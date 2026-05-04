"""GECO2 model runner.

Two implementations:

- `Geco2RunnerStub` — Plan 1 stub. `is_loaded=False`, raises on predict.
- `Geco2Runner` — Real implementation (Plan 3 / GECO2 wire-up).
  Lazy-imports torch + the vendored GECO2 source. Only constructs cleanly
  when `weights_path` exists. The vendored repo (`jerpelhan/GECO2`) plus
  SAM2 + Deformable-DETR submodules are added to sys.path on `.load()`.

The Deformable-DETR custom CUDA op `MultiScaleDeformableAttention` is
replaced at import time with the pure-PyTorch fallback
`ms_deform_attn_core_pytorch` so the model runs on CPU/MPS too. The
trade-off is slower inference; for the MVP this is acceptable.

Real GECO2 needs `CNTQG_multitrain_ca44.pth` (~335 MB) — download via
`scripts/download_geco2_weights.sh`.
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from echobox_ml.adapters import bbox_to_geco2_exemplar, geco2_outputs_to_predictions
from echobox_ml.device import DeviceName, resolve_device


@dataclass
class Prediction:
    bbox: tuple[int, int, int, int]
    score: float


class Geco2RunnerStub:
    """Stub that reports model_loaded=False. Useful in tests + when GECO2 weights absent."""

    def __init__(self, weights_path: Path | None = None, device: str = "auto") -> None:
        self.weights_path = weights_path
        self.device = device
        self.is_loaded = False

    def load(self) -> None:
        self.is_loaded = False

    def predict_similar(
        self,
        image_path: Path,
        exemplar_bbox: tuple[int, int, int, int],
        max_predictions: int = 200,
        score_threshold: float = 0.25,
    ) -> tuple[list[Prediction], tuple[int, int], int]:
        raise NotImplementedError(
            "Geco2RunnerStub: real GECO2 not wired. "
            "Set ECHOBOX_ML_GECO2_WEIGHTS to point at CNTQG_multitrain_ca44.pth and "
            "ml_backend will swap to Geco2Runner."
        )


# ---------------------------------------------------------------------------
# Real implementation
# ---------------------------------------------------------------------------


_VENDOR_DIR = Path(__file__).parent / "geco2_vendor"


def _patch_msdeformattn_to_pytorch() -> None:
    """Install a pure-PyTorch MSDeformAttn fallback in place of the CUDA op.

    GECO2 imports `MultiScaleDeformableAttention as MSDA` (a compiled C++
    extension built by `Deformable-DETR/models/ops/setup.py`). On macOS /
    CPU-only environments the extension isn't built, so the import would
    fail. We pre-register a stub module that delegates to the existing
    `ms_deform_attn_core_pytorch` helper bundled in the same package.

    Idempotent — safe to call multiple times.
    """
    if "MultiScaleDeformableAttention" in sys.modules:
        return

    import types

    fake = types.ModuleType("MultiScaleDeformableAttention")

    def ms_deform_attn_forward(  # type: ignore[no-untyped-def]
        value,
        value_spatial_shapes,
        value_level_start_index,
        sampling_locations,
        attention_weights,
        im2col_step,
    ):
        # Reshape inputs to call the bundled pure-PyTorch core.
        from models.ops.functions.ms_deform_attn_func import (  # type: ignore[import-not-found] # noqa: PLC0415
            ms_deform_attn_core_pytorch,
        )

        return ms_deform_attn_core_pytorch(
            value,
            value_spatial_shapes,
            sampling_locations,
            attention_weights,
        )

    def ms_deform_attn_backward(*args: Any, **kwargs: Any) -> tuple[Any, ...]:  # noqa: ARG001
        # Inference only — backward not supported in this fallback.
        raise NotImplementedError(
            "MSDeformAttn backward not available in PyTorch fallback. "
            "Compile Deformable-DETR/models/ops via setup.py for training."
        )

    fake.ms_deform_attn_forward = ms_deform_attn_forward  # type: ignore[attr-defined]
    fake.ms_deform_attn_backward = ms_deform_attn_backward  # type: ignore[attr-defined]
    sys.modules["MultiScaleDeformableAttention"] = fake


def _add_vendor_to_syspath() -> None:
    """Prepend GECO2 vendored paths to sys.path so its imports resolve.

    GECO2's code uses bare imports like `from models.counter_infer import ...`,
    `from sam2.sam2.modeling.sam.mask_decoder import ...`, and
    `from utils.data import ...`. We add only the vendor root so all those
    package names resolve to subdirs of geco2_vendor/.
    """
    p = str(_VENDOR_DIR)
    if p not in sys.path:
        sys.path.insert(0, p)


def _ensure_vendor_layout() -> None:
    """Idempotent fixups inside the GECO2 submodule (we don't modify upstream files).

    1. Mirror Deformable-DETR/models/ops into models/ops so `from models.ops.functions...`
       resolves. The upstream install.sh does this with `cp -r`.
    2. Add an empty sam2/__init__.py so `import sam2` finds the outer dir
       (rather than failing because sam2/ has no init).

    Both are no-ops if already present.
    """
    import shutil

    ops_src = _VENDOR_DIR / "Deformable-DETR" / "models" / "ops"
    ops_dst = _VENDOR_DIR / "models" / "ops"
    if ops_src.exists() and not ops_dst.exists():
        shutil.copytree(ops_src, ops_dst)

    sam2_init = _VENDOR_DIR / "sam2" / "__init__.py"
    if (_VENDOR_DIR / "sam2").exists() and not sam2_init.exists():
        sam2_init.touch()


class _MinimalArgs:
    """Minimal duck-typed args object matching what GECO2's build_model expects."""

    image_size: int = 1024
    num_objects: int = 3
    emb_dim: int = 256
    kernel_dim: int = 3
    reduction: int = 16
    zero_shot: bool = True
    training: bool = False


class Geco2Runner:
    def __init__(
        self,
        weights_path: Path | None,
        sam2_weights_path: Path | None = None,
        device: str = "auto",
    ) -> None:
        self.weights_path = weights_path
        self.sam2_weights_path = sam2_weights_path
        self.device: DeviceName = resolve_device(device)
        self.is_loaded: bool = False
        self._model: Any | None = None

    def load(self) -> None:
        if self.is_loaded:
            return
        if self.weights_path is None or not self.weights_path.exists():
            raise RuntimeError(
                "GECO2 weights file not found. Set ECHOBOX_ML_GECO2_WEIGHTS or run "
                "scripts/download_geco2_weights.sh"
            )

        import torch

        _ensure_vendor_layout()
        _patch_msdeformattn_to_pytorch()
        _add_vendor_to_syspath()

        # GECO2's `models/__init__.py` calls `initialize_config_module("configs", ...)`
        # at import time. We must NOT pre-initialize Hydra; just clear any previous
        # init so GECO2's bootstrap runs cleanly.
        from hydra.core.global_hydra import GlobalHydra  # noqa: PLC0415

        if GlobalHydra.instance().is_initialized():
            GlobalHydra.instance().clear()

        # Now import models — this triggers their Hydra init via configs/ package.
        try:
            from models.counter_infer import (
                build_model,  # type: ignore[import-not-found] # noqa: PLC0415
            )
        except ImportError as e:
            raise RuntimeError(
                f"failed to import GECO2 models from {_VENDOR_DIR}: {e}. "
                "Ensure 'git submodule update --init --recursive' was run."
            ) from e

        args = _MinimalArgs()
        model = build_model(args)
        # Load weights — handle DataParallel-wrapped checkpoint keys.
        ckpt = torch.load(self.weights_path, map_location=self.device, weights_only=False)
        state_dict = ckpt.get("model", ckpt)
        # Strip any "module." prefix from DataParallel checkpoints.
        cleaned = {k.replace("module.", "", 1): v for k, v in state_dict.items()}
        missing, unexpected = model.load_state_dict(cleaned, strict=False)
        if missing or unexpected:
            # Log but don't fail — GECO2's checkpoint can have aux keys.
            os.environ.setdefault(
                "ECHOBOX_ML_LOAD_INFO", f"missing={len(missing)} unexpected={len(unexpected)}"
            )

        model.to(self.device)
        model.eval()
        self._model = model
        self.is_loaded = True

    def predict_similar(
        self,
        image_path: Path,
        exemplar_bbox: tuple[int, int, int, int],
        max_predictions: int = 200,
        score_threshold: float = 0.25,
    ) -> tuple[list[Prediction], tuple[int, int], int]:
        if not self.is_loaded:
            self.load()
        assert self._model is not None

        if not image_path.exists():
            raise FileNotFoundError(f"image not found: {image_path}")

        import torch
        import torchvision.ops as tvops  # type: ignore[import-untyped]
        from PIL import Image
        from torchvision import transforms as T  # noqa: N812
        from utils.data import resize_and_pad  # type: ignore[import-not-found] # noqa: PLC0415

        with Image.open(image_path) as _raw_file:
            raw = _raw_file.convert("RGB")
            orig_w, orig_h = raw.size
            tensor = T.ToTensor()(raw)

        normalize = T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        tensor = normalize(tensor).to(self.device)

        x1, y1, x2, y2 = exemplar_bbox
        bb = torch.tensor([[x1, y1, x2, y2]], dtype=torch.float32, device=self.device)

        img_padded, bb_scaled, scale = resize_and_pad(tensor, bb, size=1024.0, zero_shot=True)
        img_in = img_padded.unsqueeze(0).to(self.device)
        bb_in = bb_scaled.unsqueeze(0).to(self.device)

        start = time.perf_counter()
        with torch.inference_mode():
            outputs, _ref, _x1, _x2, _masks = self._model(img_in, bb_in)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        # Process outputs[0] — single batch.
        out0 = outputs[0]
        pred_boxes = out0["pred_boxes"]
        if pred_boxes.dim() == 3 and pred_boxes.size(0) == 1:
            pred_boxes = pred_boxes[0]
        box_v = out0["box_v"]
        if box_v.dim() == 2 and box_v.size(0) == 1:
            box_v = box_v[0]

        if box_v.numel() == 0:
            return [], (orig_w, orig_h), elapsed_ms

        thr_inv = 1.0 / 0.33
        sel = box_v > (box_v.max() / thr_inv)
        if sel.sum().item() == 0:
            return [], (orig_w, orig_h), elapsed_ms

        keep = tvops.nms(pred_boxes[sel], box_v[sel], 0.5)
        boxes = torch.clamp(pred_boxes[sel][keep], 0, 1)
        scores = box_v[sel][keep]

        # Boxes are normalized 0..1 over the padded 1024x1024 image. Project back to original.
        boxes_in_padded = boxes * 1024.0
        boxes_in_orig = boxes_in_padded / scale
        # Clamp to original image dims.
        boxes_in_orig[:, 0::2].clamp_(0, orig_w)
        boxes_in_orig[:, 1::2].clamp_(0, orig_h)

        pairs = []
        for i in range(boxes_in_orig.shape[0]):
            bx = boxes_in_orig[i].tolist()
            pairs.append(
                (
                    (int(round(bx[0])), int(round(bx[1])), int(round(bx[2])), int(round(bx[3]))),
                    max(0.0, min(1.0, float(scores[i].item()))),
                )
            )

        adapted = geco2_outputs_to_predictions(
            [list(p[0]) for p in pairs],
            [p[1] for p in pairs],
            (orig_w, orig_h),
        )
        # Threshold + cap.
        filtered = [(b, s) for (b, s) in adapted if s >= score_threshold][:max_predictions]
        # Touch the unused-import to silence linter (already used in load()).
        _ = bbox_to_geco2_exemplar
        return [Prediction(bbox=b, score=s) for (b, s) in filtered], (orig_w, orig_h), elapsed_ms

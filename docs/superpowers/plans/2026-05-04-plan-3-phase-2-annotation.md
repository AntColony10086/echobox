# Plan 3 — Phase 2 Annotation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** End-to-end interactive annotation. After this plan, a user (post-Plan-2 finalize) can: open `/annotate?project_id=N` → see image list / canvas / class picker → pick a class → draw an exemplar bbox → see GECO2 return N similar boxes → adjust (drag/resize/delete/accept) → real-time auto-save with toast → navigate to next image.

**Architecture:**
- ml_backend: vendor GECO2 + load real model + serve `POST /predict_similar`
- app: Annotation REST (CRUD + bulk + predict-similar forward)
- Frontend: react-konva canvas, three-pane AnnotatePage, save state machine, keyboard shortcuts

**Tech Stack (added on top of Plans 1+2):**
- torch ≥2.1, sam2 (Meta SAM 2 package), GECO2 (vendored repo)
- react-konva 18, konva 9
- canvas (npm) for image loading
- react-hot-toast (or our own minimal toast)

**Spec reference:** sections 5 (Phase 2), 6.2 (annotations DB) of `docs/superpowers/specs/2026-05-04-multimodal-annotation-agent-design.md`

**Prerequisite:** Plans 1 + 2 complete.

---

## File Structure (created in this plan)

```
packages/ml_backend/
├── src/echobox_ml/
│   ├── geco2_vendor/                # cloned/submoduled jerpelhan/GECO2
│   ├── geco2_runner.py              # replaces stub from Plan 1
│   ├── device.py                    # auto cuda/mps/cpu selection
│   ├── schemas.py                   # PredictRequest / PredictResponse
│   ├── adapters.py                  # exemplar/box format conversion
│   └── main.py                      # extended with POST /predict_similar
└── tests/
    ├── test_device.py
    ├── test_runner_smoke.py         # uses real model only when ECHOBOX_ML_TEST_REAL=1
    └── test_predict_endpoint.py     # mocked runner

packages/app/src/echobox_app/
├── ml_client/
│   ├── __init__.py
│   └── client.py                    # AsyncClient wrapper for ml_backend
├── api/
│   ├── images.py                    # GET list, GET single
│   └── annotations.py               # POST predict-similar, PUT, DELETE, PATCH bulk
└── domain/
    └── annotations.py               # AnnotationDTO

frontend/src/
├── api/
│   ├── images.ts
│   └── annotations.ts
├── types/
│   └── annotation.ts
├── hooks/
│   ├── useAnnotations.ts
│   └── useSaveState.ts
├── components/
│   ├── canvas/
│   │   ├── ImageCanvas.tsx
│   │   ├── BBoxLayer.tsx
│   │   ├── BBoxItem.tsx
│   │   └── ExemplarTool.tsx
│   ├── annotate/
│   │   ├── ClassPicker.tsx
│   │   ├── ImageList.tsx
│   │   ├── Toolbar.tsx
│   │   └── SaveIndicator.tsx
│   └── ui/
│       └── Toast.tsx
└── pages/
    └── AnnotatePage.tsx
```

---

## Task 1: ml_backend — vendor GECO2 + add deps

**Files:**
- Create: `packages/ml_backend/src/echobox_ml/geco2_vendor/.gitkeep`
- Modify: `packages/ml_backend/pyproject.toml`
- Create: `scripts/download_geco2_weights.sh`
- Modify: `Makefile` (extend `setup` target)

- [ ] **Step 1: Add GECO2 as a git submodule**

Run from repo root:
```bash
git submodule add https://github.com/jerpelhan/GECO2.git packages/ml_backend/src/echobox_ml/geco2_vendor
git submodule update --init --recursive
```
Expected: `geco2_vendor/` populated with the GECO2 source tree.

- [ ] **Step 2: Add GPU deps to ml_backend pyproject.toml**

Edit `packages/ml_backend/pyproject.toml`. Add to dependencies:
```
"torch>=2.1",
"torchvision>=0.16",
"numpy>=1.24",
"opencv-python-headless>=4.9",
```

GECO2 itself uses local imports from `geco2_vendor/`; we don't pip-install it. SAM2 weights load via the GECO2 wrapper.

Run `uv sync --dev`.

- [ ] **Step 3: Create scripts/download_geco2_weights.sh**

```bash
#!/usr/bin/env bash
# Download GECO2 (and SAM2) pretrained weights into .data/weights/
set -euo pipefail

WEIGHTS_DIR="${ARIS_WEIGHTS_DIR:-./.data/weights}"
mkdir -p "$WEIGHTS_DIR"

GECO2_URL="${ARIS_GECO2_WEIGHTS_URL:-https://github.com/jerpelhan/GECO2/releases/download/v1.0/geco2.pth}"
SAM2_URL="${ARIS_SAM2_WEIGHTS_URL:-https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_tiny.pt}"

GECO2_FILE="$WEIGHTS_DIR/geco2.pth"
SAM2_FILE="$WEIGHTS_DIR/sam2_hiera_tiny.pt"

download() {
  local url="$1"
  local dest="$2"
  if [ -f "$dest" ]; then
    echo "==> already exists: $dest"
    return
  fi
  echo "==> downloading $url -> $dest"
  curl -L --fail -o "$dest.tmp" "$url" && mv "$dest.tmp" "$dest"
}

download "$SAM2_URL" "$SAM2_FILE"
download "$GECO2_URL" "$GECO2_FILE"

echo ""
echo "Weights ready in $WEIGHTS_DIR/"
echo "Set in your .env:"
echo "  ECHOBOX_ML_GECO2_WEIGHTS=$GECO2_FILE"
echo "  ECHOBOX_ML_SAM2_WEIGHTS=$SAM2_FILE"
```

- [ ] **Step 4: Make script executable**

Run: `chmod +x scripts/download_geco2_weights.sh`

- [ ] **Step 5: Extend Makefile setup target**

Edit `Makefile`. Replace the existing `setup:` target with:
```makefile
setup:
	uv sync --dev
	npm --prefix frontend install
	mkdir -p .data
	@echo ""
	@echo "==> If using GPU/CPU inference, also run:"
	@echo "       bash scripts/download_geco2_weights.sh"
	@echo ""
	@echo "Setup complete. Next steps:"
	@echo "  1. cp .env.example .env  # then fill ECHOBOX_APP_LLM_API_KEY"
	@echo "  2. make db-upgrade"
	@echo "  3. make dev"
```

- [ ] **Step 6: Add to .env.example**

Append to `.env.example`:
```
# ml_backend (Plan 3)
ECHOBOX_ML_SAM2_WEIGHTS=./.data/weights/sam2_hiera_tiny.pt
```

- [ ] **Step 7: Verify uv sync works with new deps**

Run: `uv sync --dev`
Expected: success (torch/torchvision install).

- [ ] **Step 8: Commit**

```bash
git add .gitmodules packages/ml_backend/src/echobox_ml/geco2_vendor packages/ml_backend/pyproject.toml \
        scripts/download_geco2_weights.sh Makefile .env.example uv.lock
git commit -m "chore(ml_backend): vendor GECO2 + add torch deps + weights download script"
```

---

## Task 2: ml_backend — device selection helper

**Files:**
- Create: `packages/ml_backend/src/echobox_ml/device.py`
- Create: `packages/ml_backend/tests/test_device.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/ml_backend/tests/test_device.py
from unittest.mock import patch

import pytest

from echobox_ml.device import resolve_device


def test_explicit_cpu_returns_cpu() -> None:
    assert resolve_device("cpu") == "cpu"


def test_explicit_cuda_returns_cuda_if_available() -> None:
    with patch("echobox_ml.device._has_cuda", return_value=True):
        assert resolve_device("cuda") == "cuda"


def test_explicit_cuda_falls_back_to_cpu_if_unavailable() -> None:
    with patch("echobox_ml.device._has_cuda", return_value=False):
        with patch("echobox_ml.device._has_mps", return_value=False):
            assert resolve_device("cuda") == "cpu"


def test_auto_picks_cuda_first() -> None:
    with patch("echobox_ml.device._has_cuda", return_value=True):
        with patch("echobox_ml.device._has_mps", return_value=True):
            assert resolve_device("auto") == "cuda"


def test_auto_picks_mps_when_no_cuda() -> None:
    with patch("echobox_ml.device._has_cuda", return_value=False):
        with patch("echobox_ml.device._has_mps", return_value=True):
            assert resolve_device("auto") == "mps"


def test_auto_falls_back_to_cpu() -> None:
    with patch("echobox_ml.device._has_cuda", return_value=False):
        with patch("echobox_ml.device._has_mps", return_value=False):
            assert resolve_device("auto") == "cpu"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/ml_backend/tests/test_device.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement device.py**

```python
# packages/ml_backend/src/echobox_ml/device.py
"""Auto-select the best available torch device (cuda > mps > cpu)."""
from typing import Literal

DeviceName = Literal["cuda", "mps", "cpu"]


def _has_cuda() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except ImportError:
        return False


def _has_mps() -> bool:
    try:
        import torch

        return bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
    except ImportError:
        return False


def resolve_device(requested: str) -> DeviceName:
    if requested == "cpu":
        return "cpu"
    if requested == "cuda":
        return "cuda" if _has_cuda() else ("mps" if _has_mps() else "cpu")
    if requested == "mps":
        return "mps" if _has_mps() else "cpu"
    # auto
    if _has_cuda():
        return "cuda"
    if _has_mps():
        return "mps"
    return "cpu"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/ml_backend/tests/test_device.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/ml_backend/src/echobox_ml/device.py packages/ml_backend/tests/test_device.py
git commit -m "feat(ml_backend): add resolve_device helper (auto-selects cuda/mps/cpu)"
```

---

## Task 3: ml_backend — Pydantic schemas

**Files:**
- Create: `packages/ml_backend/src/echobox_ml/schemas.py`
- Create: `packages/ml_backend/tests/test_schemas.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/ml_backend/tests/test_schemas.py
import pytest

from echobox_ml.schemas import PredictRequest, PredictResponse, Prediction


def test_predict_request_valid() -> None:
    req = PredictRequest(
        image_path="/abs/img.jpg",
        exemplar_bbox=[10, 20, 100, 200],
    )
    assert req.exemplar_bbox == (10, 20, 100, 200)
    assert req.max_predictions == 200
    assert req.score_threshold == 0.25


def test_predict_request_overrides() -> None:
    req = PredictRequest(
        image_path="/abs/img.jpg",
        exemplar_bbox=[1, 2, 3, 4],
        max_predictions=50,
        score_threshold=0.5,
    )
    assert req.max_predictions == 50
    assert req.score_threshold == 0.5


def test_predict_request_rejects_bbox_with_wrong_arity() -> None:
    with pytest.raises(ValueError):
        PredictRequest(image_path="/x", exemplar_bbox=[1, 2, 3])


def test_predict_request_rejects_inverted_bbox() -> None:
    with pytest.raises(ValueError):
        PredictRequest(image_path="/x", exemplar_bbox=[100, 100, 50, 50])


def test_prediction_serialization() -> None:
    p = Prediction(bbox=(10, 20, 100, 200), score=0.9)
    d = p.model_dump()
    assert d == {"bbox": [10, 20, 100, 200], "score": 0.9}


def test_predict_response_envelope() -> None:
    r = PredictResponse(
        predictions=[Prediction(bbox=(1, 2, 3, 4), score=0.5)],
        exemplar_count=1,
        image_size=(100, 200),
        elapsed_ms=42,
    )
    assert len(r.predictions) == 1
    assert r.elapsed_ms == 42
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/ml_backend/tests/test_schemas.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement schemas.py**

```python
# packages/ml_backend/src/echobox_ml/schemas.py
"""Pydantic request/response schemas for /predict_similar."""
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class PredictRequest(BaseModel):
    image_path: str
    exemplar_bbox: Annotated[list[int], Field(min_length=4, max_length=4)]
    max_predictions: int = Field(default=200, ge=1, le=10_000)
    score_threshold: float = Field(default=0.25, ge=0.0, le=1.0)

    @field_validator("exemplar_bbox")
    @classmethod
    def _validate_bbox(cls, v: list[int]) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = v
        if x1 >= x2 or y1 >= y2:
            raise ValueError(f"invalid bbox: x2 must be > x1 and y2 > y1; got {v}")
        if any(c < 0 for c in (x1, y1, x2, y2)):
            raise ValueError(f"bbox coords must be >= 0; got {v}")
        return (x1, y1, x2, y2)


class Prediction(BaseModel):
    bbox: tuple[int, int, int, int]
    score: float = Field(ge=0.0, le=1.0)


class PredictResponse(BaseModel):
    predictions: list[Prediction]
    exemplar_count: int
    image_size: tuple[int, int]
    elapsed_ms: int


class PredictError(BaseModel):
    error: str
    detail: str = ""
    elapsed_ms: int = 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/ml_backend/tests/test_schemas.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/ml_backend/src/echobox_ml/schemas.py packages/ml_backend/tests/test_schemas.py
git commit -m "feat(ml_backend): add Pydantic schemas for predict_similar"
```

---

## Task 4: ml_backend — Geco2Runner (real)

**Files:**
- Modify: `packages/ml_backend/src/echobox_ml/runner.py` (replace stub with real implementation)
- Create: `packages/ml_backend/src/echobox_ml/adapters.py`
- Create: `packages/ml_backend/tests/test_runner_real.py`

NOTE: Real GECO2 model loading requires SAM2 weights + GPU. Tests run only when `ECHOBOX_ML_TEST_REAL=1` env var is set. CI defaults to skip.

- [ ] **Step 1: Implement adapters.py**

```python
# packages/ml_backend/src/echobox_ml/adapters.py
"""Convert between our (x1,y1,x2,y2) tuple bbox and GECO2's exemplar/output formats."""
from typing import Any


def bbox_to_geco2_exemplar(bbox: tuple[int, int, int, int]) -> dict[str, Any]:
    """GECO2 expects an exemplar dict with 'bbox': [x1,y1,x2,y2] in pixel coords."""
    return {"bbox": [int(c) for c in bbox]}


def geco2_outputs_to_predictions(
    raw_boxes: Any,            # array-like, [N, 4] (x1,y1,x2,y2)
    raw_scores: Any | None,    # array-like, [N] floats; may be None
    image_size: tuple[int, int],
) -> list[tuple[tuple[int, int, int, int], float]]:
    """Normalize GECO2 raw output into a list of (bbox_tuple, score) pairs."""
    width, height = image_size
    out: list[tuple[tuple[int, int, int, int], float]] = []
    for idx, box in enumerate(raw_boxes):
        x1, y1, x2, y2 = (float(box[0]), float(box[1]), float(box[2]), float(box[3]))
        # clip into image
        x1 = max(0.0, min(x1, width - 1))
        y1 = max(0.0, min(y1, height - 1))
        x2 = max(0.0, min(x2, width - 1))
        y2 = max(0.0, min(y2, height - 1))
        if x2 - x1 < 1 or y2 - y1 < 1:
            continue
        score = float(raw_scores[idx]) if raw_scores is not None else 1.0
        out.append(((int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))), score))
    return out
```

- [ ] **Step 2: Test adapters**

```python
# packages/ml_backend/tests/test_adapters.py
from echobox_ml.adapters import bbox_to_geco2_exemplar, geco2_outputs_to_predictions


def test_bbox_to_exemplar() -> None:
    out = bbox_to_geco2_exemplar((10, 20, 100, 200))
    assert out == {"bbox": [10, 20, 100, 200]}


def test_outputs_clip_into_image() -> None:
    boxes = [[10, 20, 50, 60], [-5, -5, 200, 200]]
    scores = [0.9, 0.5]
    res = geco2_outputs_to_predictions(boxes, scores, image_size=(100, 100))

    assert res[0] == ((10, 20, 50, 60), 0.9)
    assert res[1] == ((0, 0, 99, 99), 0.5)


def test_outputs_skip_zero_area() -> None:
    boxes = [[10, 10, 10, 10]]
    res = geco2_outputs_to_predictions(boxes, [0.9], image_size=(100, 100))

    assert res == []


def test_outputs_default_score_when_none() -> None:
    boxes = [[10, 20, 30, 40]]
    res = geco2_outputs_to_predictions(boxes, None, image_size=(100, 100))

    assert res[0][1] == 1.0
```

Run: `uv run pytest packages/ml_backend/tests/test_adapters.py -v`
Expected: PASS (4 tests).

- [ ] **Step 3: Replace stub with real Geco2Runner**

Replace contents of `packages/ml_backend/src/echobox_ml/runner.py`:

```python
# packages/ml_backend/src/echobox_ml/runner.py
"""GECO2 model runner. Wraps the vendored jerpelhan/GECO2 implementation.

Lazy loading: model is constructed on first predict() call (avoids slow
healthz at startup). To eager-load, call .load() explicitly.
"""
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from echobox_ml.adapters import bbox_to_geco2_exemplar, geco2_outputs_to_predictions
from echobox_ml.device import DeviceName, resolve_device


@dataclass
class Prediction:
    bbox: tuple[int, int, int, int]
    score: float


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
        if self.weights_path is None:
            raise RuntimeError(
                "GECO2 weights path not set. "
                "Set ECHOBOX_ML_GECO2_WEIGHTS or run scripts/download_geco2_weights.sh"
            )
        if not self.weights_path.exists():
            raise RuntimeError(f"GECO2 weights file not found: {self.weights_path}")

        # Add vendored GECO2 to sys.path
        vendor = Path(__file__).parent / "geco2_vendor"
        if str(vendor) not in sys.path:
            sys.path.insert(0, str(vendor))

        try:
            # GECO2's public entry: importlib of its model module.
            # The exact import path depends on jerpelhan/GECO2 layout.
            # Adjust here once the repo is inspected; placeholder uses module name `geco2`.
            import torch
            from geco2.model import GECO2  # noqa: PLC0415
        except ImportError as e:
            raise RuntimeError(
                f"failed to import GECO2 from vendored repo at {vendor}: {e}. "
                "Ensure 'git submodule update --init --recursive' was run."
            ) from e

        model = GECO2(
            sam_checkpoint=str(self.sam2_weights_path) if self.sam2_weights_path else None,
        )
        ckpt = torch.load(self.weights_path, map_location=self.device)
        model.load_state_dict(ckpt.get("model", ckpt), strict=False)
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
        """Returns (predictions, image_size, elapsed_ms)."""
        if not self.is_loaded:
            self.load()
        assert self._model is not None

        if not image_path.exists():
            raise FileNotFoundError(f"image not found: {image_path}")

        with Image.open(image_path) as img:
            img = img.convert("RGB")
            width, height = img.size

        import torch
        start = time.perf_counter()
        with torch.inference_mode():
            raw_boxes, raw_scores = self._model.predict(
                image_path=str(image_path),
                exemplar=bbox_to_geco2_exemplar(exemplar_bbox),
            )

        pairs = geco2_outputs_to_predictions(raw_boxes, raw_scores, (width, height))
        # filter by threshold + cap
        filtered = [(b, s) for (b, s) in pairs if s >= score_threshold][:max_predictions]
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return [Prediction(bbox=b, score=s) for (b, s) in filtered], (width, height), elapsed_ms
```

NOTE: The exact GECO2 model class and predict signature MAY differ in `jerpelhan/GECO2`. The implementer must:
1. Inspect `geco2_vendor/` after submodule update
2. Adjust the `from geco2.model import GECO2` import + the `model.predict(...)` call to match
3. The adapter contract (input: image path + exemplar bbox; output: boxes + scores) stays stable

- [ ] **Step 4: Test runner with mocked model (no real GECO2 needed)**

```python
# packages/ml_backend/tests/test_runner_mock.py
from pathlib import Path
from unittest.mock import MagicMock

from PIL import Image

from echobox_ml.runner import Geco2Runner


def test_runner_load_lazily(tmp_path: Path) -> None:
    weights = tmp_path / "geco2.pth"
    weights.write_bytes(b"fake")
    runner = Geco2Runner(weights_path=weights, device="cpu")

    assert runner.is_loaded is False
    assert runner.weights_path == weights


def test_runner_predict_with_mocked_model(monkeypatch, tmp_path: Path) -> None:
    weights = tmp_path / "geco2.pth"
    weights.write_bytes(b"fake")
    img_path = tmp_path / "img.jpg"
    Image.new("RGB", (200, 100)).save(img_path, "JPEG")

    runner = Geco2Runner(weights_path=weights, device="cpu")
    fake_model = MagicMock()
    fake_model.predict = MagicMock(return_value=(
        [[10, 20, 50, 60], [70, 30, 110, 80]],
        [0.9, 0.4],
    ))
    runner._model = fake_model
    runner.is_loaded = True

    preds, size, elapsed = runner.predict_similar(
        img_path, exemplar_bbox=(0, 0, 100, 50),
        max_predictions=10, score_threshold=0.5,
    )

    # 0.4 < 0.5 threshold, only 1 prediction kept
    assert len(preds) == 1
    assert preds[0].bbox == (10, 20, 50, 60)
    assert preds[0].score == 0.9
    assert size == (200, 100)
    assert elapsed >= 0
```

Run: `uv run pytest packages/ml_backend/tests/test_runner_mock.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Update main.py to use Geco2Runner (not stub)**

Edit `packages/ml_backend/src/echobox_ml/main.py`. Replace the line `from echobox_ml.runner import Geco2RunnerStub` with `from echobox_ml.runner import Geco2Runner`.

Replace `runner = Geco2RunnerStub(...)` with:
```python
runner = Geco2Runner(
    weights_path=settings.geco2_weights,
    sam2_weights_path=getattr(settings, "sam2_weights", None),
    device=settings.device,
)
```

Add `sam2_weights` to `MLSettings` in `packages/ml_backend/src/echobox_ml/config.py`:
```python
sam2_weights: Path | None = None
```

- [ ] **Step 6: Verify healthz still passes (lazy load means model_loaded=False)**

Run: `uv run pytest packages/ml_backend/tests/test_healthz.py -v`
Expected: PASS — model_loaded is False because we don't call .load() at startup.

- [ ] **Step 7: Commit**

```bash
git add packages/ml_backend/src/echobox_ml/runner.py packages/ml_backend/src/echobox_ml/adapters.py \
        packages/ml_backend/src/echobox_ml/main.py packages/ml_backend/src/echobox_ml/config.py \
        packages/ml_backend/tests/test_runner_mock.py packages/ml_backend/tests/test_adapters.py
git commit -m "feat(ml_backend): replace GECO2 stub with real lazy-loading runner + adapters"
```

---

## Task 5: ml_backend — POST /predict_similar endpoint

**Files:**
- Modify: `packages/ml_backend/src/echobox_ml/main.py`
- Create: `packages/ml_backend/tests/test_predict_endpoint.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/ml_backend/tests/test_predict_endpoint.py
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture
def client_with_fake_runner(monkeypatch, tmp_path: Path) -> TestClient:
    from echobox_ml.main import create_app
    from echobox_ml.runner import Geco2Runner, Prediction

    fake = MagicMock(spec=Geco2Runner)
    fake.is_loaded = True
    fake.device = "cpu"
    fake.predict_similar = MagicMock(return_value=(
        [Prediction(bbox=(10, 20, 50, 60), score=0.9)],
        (200, 100),
        42,
    ))

    monkeypatch.setattr(
        "echobox_ml.main.Geco2Runner",
        lambda **kwargs: fake,
    )
    return TestClient(create_app())


def test_predict_returns_200(client_with_fake_runner, tmp_path: Path) -> None:
    img = tmp_path / "img.jpg"
    Image.new("RGB", (200, 100)).save(img, "JPEG")

    resp = client_with_fake_runner.post("/predict_similar", json={
        "image_path": str(img),
        "exemplar_bbox": [0, 0, 100, 50],
    })

    assert resp.status_code == 200
    body = resp.json()
    assert body["predictions"][0]["bbox"] == [10, 20, 50, 60]
    assert body["predictions"][0]["score"] == 0.9
    assert body["image_size"] == [200, 100]
    assert body["elapsed_ms"] == 42


def test_predict_invalid_bbox_400(client_with_fake_runner) -> None:
    resp = client_with_fake_runner.post("/predict_similar", json={
        "image_path": "/x.jpg",
        "exemplar_bbox": [100, 100, 50, 50],
    })

    assert resp.status_code == 422


def test_predict_image_not_found_404(client_with_fake_runner) -> None:
    client_with_fake_runner.app.state.runner.predict_similar = MagicMock(
        side_effect=FileNotFoundError("nope")
    )

    resp = client_with_fake_runner.post("/predict_similar", json={
        "image_path": "/does/not/exist.jpg",
        "exemplar_bbox": [0, 0, 100, 50],
    })

    assert resp.status_code == 404
    assert resp.json()["error"] == "image_not_found"


def test_predict_inference_failure_500(client_with_fake_runner) -> None:
    client_with_fake_runner.app.state.runner.predict_similar = MagicMock(
        side_effect=RuntimeError("oom")
    )

    resp = client_with_fake_runner.post("/predict_similar", json={
        "image_path": "/x.jpg",
        "exemplar_bbox": [0, 0, 100, 50],
    })

    assert resp.status_code == 500
    assert resp.json()["error"] == "inference_failed"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/ml_backend/tests/test_predict_endpoint.py -v`
Expected: FAIL.

- [ ] **Step 3: Add /predict_similar to ml_backend main.py**

Edit `packages/ml_backend/src/echobox_ml/main.py`. After the `/healthz` route, add:

```python
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from echobox_ml.schemas import PredictRequest, PredictResponse, Prediction as PredOut


    @app.post("/predict_similar")
    def predict_similar(payload: PredictRequest) -> PredictResponse | JSONResponse:
        try:
            preds, image_size, elapsed = runner.predict_similar(
                Path(payload.image_path),
                payload.exemplar_bbox,
                max_predictions=payload.max_predictions,
                score_threshold=payload.score_threshold,
            )
        except FileNotFoundError as e:
            return JSONResponse(
                status_code=404,
                content={"error": "image_not_found", "detail": str(e), "elapsed_ms": 0},
            )
        except RuntimeError as e:
            return JSONResponse(
                status_code=500,
                content={"error": "inference_failed", "detail": str(e), "elapsed_ms": 0},
            )

        return PredictResponse(
            predictions=[PredOut(bbox=p.bbox, score=p.score) for p in preds],
            exemplar_count=1,
            image_size=image_size,
            elapsed_ms=elapsed,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/ml_backend/tests/test_predict_endpoint.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/ml_backend/src/echobox_ml/main.py packages/ml_backend/tests/test_predict_endpoint.py
git commit -m "feat(ml_backend): add POST /predict_similar with FileNotFound + RuntimeError handlers"
```

---

## Task 6: app — ml_client (HTTP wrapper for ml_backend)

**Files:**
- Create: `packages/app/src/echobox_app/ml_client/__init__.py`
- Create: `packages/app/src/echobox_app/ml_client/client.py`
- Create: `packages/app/tests/test_ml_client.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_ml_client.py
import httpx
import pytest

from echobox_app.ml_client.client import MLBackendClient


@pytest.mark.asyncio
async def test_predict_similar_returns_parsed_response() -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(
        200,
        json={
            "predictions": [{"bbox": [1, 2, 3, 4], "score": 0.9}],
            "exemplar_count": 1,
            "image_size": [100, 200],
            "elapsed_ms": 50,
        },
    ))
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as ac:
        client = MLBackendClient(http=ac)

        result = await client.predict_similar("/img.jpg", (0, 0, 50, 50))

    assert result["predictions"][0]["bbox"] == [1, 2, 3, 4]
    assert result["elapsed_ms"] == 50


@pytest.mark.asyncio
async def test_predict_similar_503_raises_unavailable() -> None:
    from echobox_app.errors import MLBackendUnavailable

    transport = httpx.MockTransport(lambda req: httpx.Response(503))
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as ac:
        client = MLBackendClient(http=ac)
        with pytest.raises(MLBackendUnavailable):
            await client.predict_similar("/img.jpg", (0, 0, 1, 1))


@pytest.mark.asyncio
async def test_predict_similar_404_raises_image_not_found() -> None:
    from echobox_app.errors import ImageNotFound

    transport = httpx.MockTransport(lambda req: httpx.Response(
        404, json={"error": "image_not_found", "detail": "nope"}
    ))
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as ac:
        client = MLBackendClient(http=ac)
        with pytest.raises(ImageNotFound):
            await client.predict_similar("/img.jpg", (0, 0, 1, 1))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_ml_client.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement ml_client/__init__.py and client.py**

```python
# packages/app/src/echobox_app/ml_client/__init__.py
"""HTTP client for the ml_backend service."""
```

```python
# packages/app/src/echobox_app/ml_client/client.py
"""Async HTTP client for ml_backend POST /predict_similar."""
from typing import Any

import httpx

from echobox_app.errors import ImageNotFound, MLBackendUnavailable


class MLBackendClient:
    def __init__(
        self,
        http: httpx.AsyncClient | None = None,
        base_url: str = "http://localhost:9090",
        timeout_s: float = 30.0,
    ) -> None:
        self._http = http or httpx.AsyncClient(base_url=base_url, timeout=timeout_s)
        self._owns_http = http is None

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def predict_similar(
        self,
        image_path: str,
        exemplar_bbox: tuple[int, int, int, int],
        max_predictions: int = 200,
        score_threshold: float = 0.25,
    ) -> dict[str, Any]:
        try:
            resp = await self._http.post("/predict_similar", json={
                "image_path": image_path,
                "exemplar_bbox": list(exemplar_bbox),
                "max_predictions": max_predictions,
                "score_threshold": score_threshold,
            })
        except httpx.RequestError as e:
            raise MLBackendUnavailable(
                f"ml_backend request failed: {e}",
                detail={"image_path": image_path},
            )

        if resp.status_code == 404:
            body = resp.json()
            raise ImageNotFound(
                body.get("detail", "image not found"),
                detail={"image_path": image_path},
            )
        if resp.status_code >= 500 or resp.status_code == 503:
            raise MLBackendUnavailable(
                f"ml_backend returned {resp.status_code}",
                detail={"body": resp.text[:500]},
            )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_ml_client.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/ml_client/ packages/app/tests/test_ml_client.py
git commit -m "feat(app): add MLBackendClient (httpx async) with typed error mapping"
```

---

## Task 7: app domain — AnnotationDTO

**Files:**
- Create: `packages/app/src/echobox_app/domain/annotations.py`
- Create: `packages/app/tests/test_domain_annotations.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_domain_annotations.py
from echobox_app.domain.annotations import AnnotationDTO


def test_dto_to_dict() -> None:
    dto = AnnotationDTO(
        id=42, image_id=1, label_id=2, label_name="crack", label_color="#000",
        x1=10, y1=20, x2=30, y2=40, score=0.9,
        source="geco2_accepted", version=1,
    )
    d = dto.to_dict()
    assert d["id"] == 42
    assert d["bbox"] == [10, 20, 30, 40]
    assert d["score"] == 0.9
    assert d["source"] == "geco2_accepted"
    assert d["label"] == {"id": 2, "name": "crack", "color": "#000"}


def test_dto_from_db_model() -> None:
    from echobox_app.db.models import Annotation, Label
    from datetime import datetime

    label = Label(id=2, project_id=1, name="crack", color="#000",
                  created_at=datetime.now())
    ann = Annotation(
        id=42, image_id=1, label_id=2,
        x1=10, y1=20, x2=30, y2=40,
        score=0.9, source="user", version=1,
        created_at=datetime.now(), updated_at=datetime.now(),
    )
    ann.label = label

    dto = AnnotationDTO.from_db(ann)

    assert dto.id == 42
    assert dto.label_name == "crack"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_domain_annotations.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement domain/annotations.py**

```python
# packages/app/src/echobox_app/domain/annotations.py
"""Annotation DTO for API responses."""
from dataclasses import dataclass
from typing import Any

from echobox_app.db.models import Annotation as DBAnnotation


@dataclass
class AnnotationDTO:
    id: int
    image_id: int
    label_id: int
    label_name: str
    label_color: str
    x1: int
    y1: int
    x2: int
    y2: int
    score: float | None
    source: str
    version: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "image_id": self.image_id,
            "label": {"id": self.label_id, "name": self.label_name, "color": self.label_color},
            "bbox": [self.x1, self.y1, self.x2, self.y2],
            "score": self.score,
            "source": self.source,
            "version": self.version,
        }

    @classmethod
    def from_db(cls, ann: DBAnnotation) -> "AnnotationDTO":
        return cls(
            id=ann.id, image_id=ann.image_id, label_id=ann.label_id,
            label_name=ann.label.name, label_color=ann.label.color,
            x1=ann.x1, y1=ann.y1, x2=ann.x2, y2=ann.y2,
            score=ann.score, source=ann.source, version=ann.version,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_domain_annotations.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/domain/annotations.py packages/app/tests/test_domain_annotations.py
git commit -m "feat(app): add AnnotationDTO with to_dict + from_db"
```

---

## Task 8: REST — GET images endpoints

**Files:**
- Create: `packages/app/src/echobox_app/api/images.py`
- Modify: `packages/app/src/echobox_app/main.py` (include router)
- Create: `packages/app/tests/test_api_images.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_api_images.py
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_images(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path))
    from echobox_app.db.models import Base, Image, Project
    from echobox_app.db.session import make_engine, make_session_factory
    from echobox_app.main import create_app

    app = create_app()
    Base.metadata.create_all(make_engine(f"sqlite:///{tmp_path}/db"))
    sf = make_session_factory(make_engine(f"sqlite:///{tmp_path}/db"))
    with sf() as s:
        p = Project(name="x", workspace_path=str(tmp_path), source_folder="x", status="ready")
        s.add(p)
        s.flush()
        for i in range(3):
            split = ["train", "val", "test"][i]
            s.add(Image(
                project_id=p.id, filename=f"{i+1:05d}.jpg",
                abs_path=f"/x/{i+1:05d}.jpg",
                width=10, height=10, split=split,
                index_in_project=i, source_path=f"/orig/{i}.jpg",
            ))
        s.commit()
        pid = p.id
    return TestClient(app), pid


def test_list_images_with_progress(client_with_images) -> None:
    client, pid = client_with_images

    resp = client.get(f"/api/projects/{pid}/images")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert body["progress"]["train"]["total"] == 1
    assert body["progress"]["train"]["annotated"] == 0


def test_get_single_image(client_with_images) -> None:
    client, pid = client_with_images
    img_id = client.get(f"/api/projects/{pid}/images").json()["items"][0]["id"]

    resp = client.get(f"/api/images/{img_id}")

    assert resp.status_code == 200
    assert resp.json()["filename"] == "00001.jpg"


def test_list_images_filter_by_split(client_with_images) -> None:
    client, pid = client_with_images

    resp = client.get(f"/api/projects/{pid}/images?split=val")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["split"] == "val"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_api_images.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement api/images.py**

```python
# packages/app/src/echobox_app/api/images.py
"""Image REST endpoints."""
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from echobox_app.api.deps import session_dep
from echobox_app.db.models import Annotation, Image, Project
from echobox_app.errors import ImageNotFound, ProjectNotFound

router = APIRouter(tags=["images"])


@router.get("/api/projects/{pid}/images")
def list_images(
    pid: int,
    session: Annotated[Session, Depends(session_dep)],
    split: Literal["train", "val", "test"] | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=10_000),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    project = session.get(Project, pid)
    if project is None:
        raise ProjectNotFound(f"project {pid} not found")

    q = select(Image).where(Image.project_id == pid)
    if split is not None:
        q = q.where(Image.split == split)
    q = q.order_by(Image.index_in_project).limit(limit).offset(offset)
    images = session.scalars(q).all()

    # Per-image annotation count
    counts = dict(session.execute(
        select(Annotation.image_id, func.count(Annotation.id))
        .join(Image, Image.id == Annotation.image_id)
        .where(Image.project_id == pid)
        .where(Annotation.source != "geco2_pending")
        .group_by(Annotation.image_id)
    ).all())

    items = [{
        "id": img.id, "filename": img.filename, "abs_path": img.abs_path,
        "width": img.width, "height": img.height, "split": img.split,
        "index_in_project": img.index_in_project,
        "annotation_count": counts.get(img.id, 0),
    } for img in images]

    progress = _compute_progress(session, pid)
    total_q = select(func.count(Image.id)).where(Image.project_id == pid)
    if split is not None:
        total_q = total_q.where(Image.split == split)
    total = session.scalar(total_q) or 0

    return {"total": total, "items": items, "progress": progress}


@router.get("/api/images/{iid}")
def get_image(
    iid: int,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    img = session.get(Image, iid)
    if img is None:
        raise ImageNotFound(f"image {iid} not found")
    return {
        "id": img.id, "project_id": img.project_id,
        "filename": img.filename, "abs_path": img.abs_path,
        "width": img.width, "height": img.height, "split": img.split,
        "index_in_project": img.index_in_project,
    }


def _compute_progress(session: Session, pid: int) -> dict[str, dict[str, int]]:
    rows = session.execute(
        select(Image.split, func.count(Image.id)).where(Image.project_id == pid)
        .group_by(Image.split)
    ).all()
    totals = {split: count for split, count in rows}

    annotated_rows = session.execute(
        select(Image.split, func.count(func.distinct(Image.id)))
        .join(Annotation, Annotation.image_id == Image.id)
        .where(Image.project_id == pid)
        .where(Annotation.source != "geco2_pending")
        .group_by(Image.split)
    ).all()
    annotated = {split: count for split, count in annotated_rows}

    return {
        split: {"total": totals.get(split, 0), "annotated": annotated.get(split, 0)}
        for split in ("train", "val", "test")
    }
```

- [ ] **Step 4: Modify main.py**

Edit `packages/app/src/echobox_app/main.py`. After `app.include_router(chat_router)`, add:

```python
    from echobox_app.api.images import router as images_router
    app.include_router(images_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_api_images.py -v`
Expected: PASS (3 tests).

- [ ] **Step 6: Commit**

```bash
git add packages/app/src/echobox_app/api/images.py packages/app/src/echobox_app/main.py \
        packages/app/tests/test_api_images.py
git commit -m "feat(app): add GET /images list (with progress) + GET /images/{iid}"
```

---

## Task 9: REST — POST predict-similar (forward + persist pending)

**Files:**
- Create: `packages/app/src/echobox_app/api/annotations.py`
- Modify: `packages/app/src/echobox_app/main.py`
- Create: `packages/app/tests/test_api_predict.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_api_predict.py
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PILImage


@pytest.fixture
def system_with_image(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path))

    from echobox_app.db.models import Base, Image, Label, Project
    from echobox_app.db.session import make_engine, make_session_factory

    engine = make_engine(f"sqlite:///{tmp_path}/db")
    Base.metadata.create_all(engine)
    sf = make_session_factory(engine)

    img_path = tmp_path / "img.jpg"
    PILImage.new("RGB", (200, 100)).save(img_path, "JPEG")

    with sf() as s:
        p = Project(name="x", workspace_path=str(tmp_path), source_folder="/orig",
                    status="annotating")
        s.add(p)
        s.flush()
        s.add(Label(project_id=p.id, name="crack", color="#000"))
        s.add(Image(
            project_id=p.id, filename="img.jpg", abs_path=str(img_path),
            width=200, height=100, split="train",
            index_in_project=0, source_path="/orig/img.jpg",
        ))
        s.commit()
        ids = (p.id, p.images[0].id, p.labels[0].id)

    fake_ml = AsyncMock()
    fake_ml.predict_similar = AsyncMock(return_value={
        "predictions": [{"bbox": [10, 20, 50, 60], "score": 0.9},
                        {"bbox": [70, 30, 110, 80], "score": 0.7}],
        "exemplar_count": 1,
        "image_size": [200, 100],
        "elapsed_ms": 30,
    })

    from echobox_app.main import create_app
    app = create_app()

    def _override_ml() -> object:
        return fake_ml

    from echobox_app.api import annotations as ann_mod
    app.dependency_overrides[ann_mod.ml_client_dep] = _override_ml

    return TestClient(app), ids, fake_ml


def test_predict_similar_persists_pending(system_with_image, tmp_path: Path) -> None:
    client, (pid, iid, lid), fake_ml = system_with_image

    resp = client.post(
        f"/api/projects/{pid}/images/{iid}/predict-similar",
        json={"label_id": lid, "exemplar_bbox": [0, 0, 100, 50]},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert len(body["created"]) == 2
    assert body["created"][0]["source"] == "geco2_pending"

    # Verify they're in DB
    list_resp = client.get(f"/api/images/{iid}/annotations")
    annotations = list_resp.json()["items"]
    assert len(annotations) == 2


def test_predict_similar_replaces_old_pending(system_with_image) -> None:
    client, (pid, iid, lid), fake_ml = system_with_image

    client.post(f"/api/projects/{pid}/images/{iid}/predict-similar",
                json={"label_id": lid, "exemplar_bbox": [0, 0, 100, 50]})
    # second call should clear the prior pending and add new
    fake_ml.predict_similar = AsyncMock(return_value={
        "predictions": [{"bbox": [50, 50, 99, 99], "score": 0.6}],
        "exemplar_count": 1,
        "image_size": [200, 100],
        "elapsed_ms": 20,
    })
    resp2 = client.post(f"/api/projects/{pid}/images/{iid}/predict-similar",
                         json={"label_id": lid, "exemplar_bbox": [0, 0, 100, 50]})

    body = resp2.json()
    assert len(body["created"]) == 1

    list_resp = client.get(f"/api/images/{iid}/annotations")
    annotations = list_resp.json()["items"]
    pending = [a for a in annotations if a["source"] == "geco2_pending"]
    assert len(pending) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_api_predict.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement api/annotations.py**

```python
# packages/app/src/echobox_app/api/annotations.py
"""Annotation REST endpoints: list, predict-similar, PUT/DELETE/PATCH."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from echobox_app.api.deps import session_dep, settings_dep
from echobox_app.config import AppSettings
from echobox_app.db.models import Annotation, Image, Label, PredictionRun, Project
from echobox_app.domain.annotations import AnnotationDTO
from echobox_app.errors import ImageNotFound, ProjectNotFound, ValidationError
from echobox_app.ml_client.client import MLBackendClient

router = APIRouter(tags=["annotations"])


def ml_client_dep(request: Request) -> MLBackendClient:
    """Dependency provider — overrideable in tests."""
    settings: AppSettings = request.app.state.settings
    return MLBackendClient(
        base_url=settings.ml_backend_url,
        timeout_s=settings.ml_backend_timeout_s,
    )


class PredictSimilarPayload(BaseModel):
    label_id: int
    exemplar_bbox: list[int] = Field(min_length=4, max_length=4)
    max_predictions: int = 200
    score_threshold: float = 0.25


@router.get("/api/images/{iid}/annotations")
def list_image_annotations(
    iid: int,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    img = session.get(Image, iid)
    if img is None:
        raise ImageNotFound(f"image {iid} not found")
    annotations = session.scalars(
        select(Annotation).where(Annotation.image_id == iid)
        .order_by(Annotation.created_at)
    ).all()
    return {"items": [AnnotationDTO.from_db(a).to_dict() for a in annotations]}


@router.post(
    "/api/projects/{pid}/images/{iid}/predict-similar",
    status_code=status.HTTP_201_CREATED,
)
async def predict_similar(
    pid: int,
    iid: int,
    payload: PredictSimilarPayload,
    session: Annotated[Session, Depends(session_dep)],
    ml_client: Annotated[MLBackendClient, Depends(ml_client_dep)],
) -> dict[str, Any]:
    project = session.get(Project, pid)
    if project is None:
        raise ProjectNotFound(f"project {pid} not found")
    img = session.get(Image, iid)
    if img is None or img.project_id != pid:
        raise ImageNotFound(f"image {iid} not in project {pid}")
    label = session.get(Label, payload.label_id)
    if label is None or label.project_id != pid:
        raise ValidationError(f"label {payload.label_id} not in project {pid}")

    x1, y1, x2, y2 = payload.exemplar_bbox
    if x1 >= x2 or y1 >= y2:
        raise ValidationError(
            f"invalid exemplar bbox: {payload.exemplar_bbox}",
            detail={"bbox": payload.exemplar_bbox},
        )

    # Clear prior pending for this image+label
    session.execute(
        delete(Annotation).where(
            Annotation.image_id == iid,
            Annotation.label_id == payload.label_id,
            Annotation.source == "geco2_pending",
        )
    )

    response = await ml_client.predict_similar(
        image_path=img.abs_path,
        exemplar_bbox=(x1, y1, x2, y2),
        max_predictions=payload.max_predictions,
        score_threshold=payload.score_threshold,
    )

    created: list[Annotation] = []
    for pred in response["predictions"]:
        bx1, by1, bx2, by2 = pred["bbox"]
        ann = Annotation(
            image_id=iid, label_id=payload.label_id,
            x1=bx1, y1=by1, x2=bx2, y2=by2,
            score=pred["score"], source="geco2_pending", version=1,
        )
        session.add(ann)
        created.append(ann)

    session.add(PredictionRun(
        project_id=pid, image_id=iid, label_id=payload.label_id,
        exemplar_x1=x1, exemplar_y1=y1, exemplar_x2=x2, exemplar_y2=y2,
        n_predictions=len(created), elapsed_ms=int(response["elapsed_ms"]),
    ))
    session.commit()
    for a in created:
        session.refresh(a)

    return {
        "created": [AnnotationDTO.from_db(a).to_dict() for a in created],
        "elapsed_ms": int(response["elapsed_ms"]),
    }
```

- [ ] **Step 4: Modify main.py**

Edit `packages/app/src/echobox_app/main.py`. After `app.include_router(images_router)`:

```python
    from echobox_app.api.annotations import router as annotations_router
    app.include_router(annotations_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_api_predict.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add packages/app/src/echobox_app/api/annotations.py packages/app/src/echobox_app/main.py \
        packages/app/tests/test_api_predict.py
git commit -m "feat(app): add POST /predict-similar (forward + persist + replace pending)"
```

---

## Task 10: REST — PUT / DELETE / PATCH bulk for annotations

**Files:**
- Modify: `packages/app/src/echobox_app/api/annotations.py`
- Create: `packages/app/tests/test_api_annotations_crud.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_api_annotations_crud.py
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_annotation(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path))

    from echobox_app.db.models import Annotation, Base, Image, Label, Project
    from echobox_app.db.session import make_engine, make_session_factory
    from echobox_app.main import create_app

    engine = make_engine(f"sqlite:///{tmp_path}/db")
    Base.metadata.create_all(engine)
    sf = make_session_factory(engine)
    with sf() as s:
        p = Project(name="x", workspace_path=str(tmp_path), source_folder="/o",
                    status="annotating")
        s.add(p)
        s.flush()
        l = Label(project_id=p.id, name="crack", color="#000")
        s.add(l)
        img = Image(project_id=p.id, filename="i.jpg", abs_path="/x.jpg",
                    width=10, height=10, split="train", index_in_project=0,
                    source_path="/o/i.jpg")
        s.add(img)
        s.flush()
        ann = Annotation(image_id=img.id, label_id=l.id,
                         x1=10, y1=20, x2=50, y2=60,
                         score=0.9, source="geco2_pending", version=1)
        s.add(ann)
        s.commit()
        ids = (p.id, img.id, l.id, ann.id, ann.version)
    return TestClient(create_app()), ids


def test_put_updates_bbox_and_bumps_version(client_with_annotation) -> None:
    client, (pid, iid, lid, aid, ver) = client_with_annotation

    resp = client.put(f"/api/annotations/{aid}", json={
        "x1": 15, "y1": 25, "x2": 55, "y2": 65,
        "version": ver,
    })

    assert resp.status_code == 200
    body = resp.json()
    assert body["bbox"] == [15, 25, 55, 65]
    assert body["version"] == ver + 1
    assert body["source"] == "user_edited"


def test_put_with_stale_version_409(client_with_annotation) -> None:
    client, (pid, iid, lid, aid, ver) = client_with_annotation

    resp = client.put(f"/api/annotations/{aid}", json={
        "x1": 1, "y1": 2, "x2": 3, "y2": 4,
        "version": ver + 99,
    })

    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "version_conflict"


def test_put_can_change_source_to_accepted(client_with_annotation) -> None:
    client, (pid, iid, lid, aid, ver) = client_with_annotation

    resp = client.put(f"/api/annotations/{aid}", json={
        "source": "geco2_accepted", "version": ver,
    })

    assert resp.status_code == 200
    assert resp.json()["source"] == "geco2_accepted"


def test_delete(client_with_annotation) -> None:
    client, (pid, iid, lid, aid, ver) = client_with_annotation

    resp = client.delete(f"/api/annotations/{aid}")
    assert resp.status_code == 204

    list_resp = client.get(f"/api/images/{iid}/annotations")
    assert list_resp.json()["items"] == []


def test_bulk_accept_all(client_with_annotation) -> None:
    client, (pid, iid, lid, aid, ver) = client_with_annotation

    resp = client.patch(
        f"/api/projects/{pid}/images/{iid}/annotations/bulk",
        json={"action": "accept_all"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["affected"] == 1

    list_resp = client.get(f"/api/images/{iid}/annotations")
    assert list_resp.json()["items"][0]["source"] == "geco2_accepted"


def test_bulk_reject_all_deletes_pending(client_with_annotation) -> None:
    client, (pid, iid, lid, aid, ver) = client_with_annotation

    resp = client.patch(
        f"/api/projects/{pid}/images/{iid}/annotations/bulk",
        json={"action": "reject_all"},
    )

    assert resp.status_code == 200
    list_resp = client.get(f"/api/images/{iid}/annotations")
    assert list_resp.json()["items"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_api_annotations_crud.py -v`
Expected: FAIL.

- [ ] **Step 3: Add CRUD routes to api/annotations.py**

Append to `packages/app/src/echobox_app/api/annotations.py`:

```python
from typing import Literal

from echobox_app.errors import AnnotationNotFound, VersionConflict


class PutAnnotation(BaseModel):
    x1: int | None = None
    y1: int | None = None
    x2: int | None = None
    y2: int | None = None
    label_id: int | None = None
    source: Literal["user", "geco2_accepted", "user_edited"] | None = None
    version: int


class BulkAction(BaseModel):
    action: Literal["accept_all", "reject_all"]


@router.put("/api/annotations/{aid}")
def put_annotation(
    aid: int,
    payload: PutAnnotation,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    ann = session.get(Annotation, aid)
    if ann is None:
        raise AnnotationNotFound(f"annotation {aid} not found")
    if ann.version != payload.version:
        raise VersionConflict(
            f"version mismatch: have {ann.version}, sent {payload.version}",
            detail={"current_version": ann.version},
        )

    bbox_changed = False
    if payload.x1 is not None:
        ann.x1 = payload.x1
        bbox_changed = True
    if payload.y1 is not None:
        ann.y1 = payload.y1
        bbox_changed = True
    if payload.x2 is not None:
        ann.x2 = payload.x2
        bbox_changed = True
    if payload.y2 is not None:
        ann.y2 = payload.y2
        bbox_changed = True
    if ann.x1 >= ann.x2 or ann.y1 >= ann.y2:
        raise ValidationError(
            "invalid bbox after edit",
            detail={"bbox": [ann.x1, ann.y1, ann.x2, ann.y2]},
        )
    if payload.label_id is not None:
        ann.label_id = payload.label_id
    if payload.source is not None:
        ann.source = payload.source
    elif bbox_changed and ann.source.startswith("geco2"):
        ann.source = "user_edited"

    ann.version += 1
    session.commit()
    session.refresh(ann)
    return AnnotationDTO.from_db(ann).to_dict()


@router.delete("/api/annotations/{aid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_annotation(
    aid: int,
    session: Annotated[Session, Depends(session_dep)],
) -> None:
    ann = session.get(Annotation, aid)
    if ann is None:
        raise AnnotationNotFound(f"annotation {aid} not found")
    session.delete(ann)
    session.commit()


@router.patch("/api/projects/{pid}/images/{iid}/annotations/bulk")
def bulk_action(
    pid: int,
    iid: int,
    payload: BulkAction,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    img = session.get(Image, iid)
    if img is None or img.project_id != pid:
        raise ImageNotFound(f"image {iid} not in project {pid}")

    pending = session.scalars(
        select(Annotation).where(
            Annotation.image_id == iid,
            Annotation.source == "geco2_pending",
        )
    ).all()

    if payload.action == "accept_all":
        for a in pending:
            a.source = "geco2_accepted"
            a.version += 1
        session.commit()
        return {"affected": len(pending), "action": "accept_all"}

    # reject_all
    for a in pending:
        session.delete(a)
    session.commit()
    return {"affected": len(pending), "action": "reject_all"}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_api_annotations_crud.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/api/annotations.py \
        packages/app/tests/test_api_annotations_crud.py
git commit -m "feat(app): add PUT (with optimistic lock) + DELETE + PATCH bulk annotations"
```

---

## Task 11: REST — Image static file serving

**Files:**
- Modify: `packages/app/src/echobox_app/api/images.py`
- Create: `packages/app/tests/test_api_image_file.py`

The frontend canvas needs to load image bytes via HTTP. Add a route that serves them.

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_api_image_file.py
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PILImage


@pytest.fixture
def client_with_real_image(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path))

    img_path = tmp_path / "test.jpg"
    PILImage.new("RGB", (50, 50), color=(123, 45, 67)).save(img_path, "JPEG")

    from echobox_app.db.models import Base, Image, Project
    from echobox_app.db.session import make_engine, make_session_factory
    from echobox_app.main import create_app

    engine = make_engine(f"sqlite:///{tmp_path}/db")
    Base.metadata.create_all(engine)
    sf = make_session_factory(engine)
    with sf() as s:
        p = Project(name="x", workspace_path=str(tmp_path), source_folder="/o",
                    status="annotating")
        s.add(p)
        s.flush()
        s.add(Image(
            project_id=p.id, filename="test.jpg", abs_path=str(img_path),
            width=50, height=50, split="train",
            index_in_project=0, source_path="/o/t.jpg",
        ))
        s.commit()
        iid = p.images[0].id
    return TestClient(create_app()), iid


def test_get_image_file_returns_bytes(client_with_real_image) -> None:
    client, iid = client_with_real_image

    resp = client.get(f"/api/images/{iid}/file")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/")
    assert len(resp.content) > 100


def test_get_image_file_404_when_missing(client_with_real_image, tmp_path: Path) -> None:
    client, iid = client_with_real_image
    # Delete the underlying file
    Path(client.get(f"/api/images/{iid}").json()["abs_path"]).unlink()

    resp = client.get(f"/api/images/{iid}/file")

    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_api_image_file.py -v`
Expected: FAIL.

- [ ] **Step 3: Add /file route to api/images.py**

Append:

```python
from pathlib import Path

from fastapi.responses import FileResponse


@router.get("/api/images/{iid}/file")
def get_image_file(
    iid: int,
    session: Annotated[Session, Depends(session_dep)],
) -> FileResponse:
    img = session.get(Image, iid)
    if img is None:
        raise ImageNotFound(f"image {iid} not found")
    p = Path(img.abs_path)
    if not p.exists():
        raise ImageNotFound(f"file missing on disk: {p}")
    return FileResponse(p, media_type=_guess_media_type(p))


def _guess_media_type(p: Path) -> str:
    return {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".bmp": "image/bmp", ".tiff": "image/tiff", ".tif": "image/tiff",
    }.get(p.suffix.lower(), "application/octet-stream")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_api_image_file.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/api/images.py packages/app/tests/test_api_image_file.py
git commit -m "feat(app): add GET /api/images/{iid}/file for canvas image loading"
```

---

## Task 12: Frontend — Annotation types + API

**Files:**
- Create: `frontend/src/types/annotation.ts`
- Create: `frontend/src/api/images.ts`
- Create: `frontend/src/api/annotations.ts`

- [ ] **Step 1: Add react-konva**

Edit `frontend/package.json`, add to dependencies:
```json
{
  "dependencies": {
    "konva": "^9.3.14",
    "react-konva": "^18.2.10",
    "react-hot-toast": "^2.4.1"
  }
}
```
Then `cd frontend && npm install`.

- [ ] **Step 2: Create types/annotation.ts**

```typescript
// frontend/src/types/annotation.ts
import type { Label, SplitName } from "./project";

export type AnnotationSource =
  | "user"
  | "geco2_pending"
  | "geco2_accepted"
  | "user_edited";

export interface Annotation {
  id: number;
  image_id: number;
  label: Label & { id: number };
  bbox: [number, number, number, number]; // x1, y1, x2, y2 pixels
  score: number | null;
  source: AnnotationSource;
  version: number;
}

export interface ImageItem {
  id: number;
  filename: string;
  abs_path: string;
  width: number;
  height: number;
  split: SplitName;
  index_in_project: number;
  annotation_count: number;
}

export interface ImageListResponse {
  total: number;
  items: ImageItem[];
  progress: Record<SplitName, { total: number; annotated: number }>;
}

export interface PredictSimilarResponse {
  created: Annotation[];
  elapsed_ms: number;
}
```

- [ ] **Step 3: Create api/images.ts**

```typescript
// frontend/src/api/images.ts
import { apiClient } from "./client";
import type { ImageItem, ImageListResponse } from "../types/annotation";
import type { SplitName } from "../types/project";

export async function listImages(
  pid: number,
  split?: SplitName,
): Promise<ImageListResponse> {
  const params = split ? { split } : {};
  const { data } = await apiClient.get<ImageListResponse>(
    `/projects/${pid}/images`,
    { params },
  );
  return data;
}

export async function getImage(iid: number): Promise<ImageItem & { project_id: number }> {
  const { data } = await apiClient.get(`/images/${iid}`);
  return data;
}

export function imageFileUrl(iid: number): string {
  return `/api/images/${iid}/file`;
}
```

- [ ] **Step 4: Create api/annotations.ts**

```typescript
// frontend/src/api/annotations.ts
import { apiClient } from "./client";
import type {
  Annotation,
  AnnotationSource,
  PredictSimilarResponse,
} from "../types/annotation";

export async function listAnnotations(iid: number): Promise<Annotation[]> {
  const { data } = await apiClient.get<{ items: Annotation[] }>(
    `/images/${iid}/annotations`,
  );
  return data.items;
}

export async function predictSimilar(
  pid: number,
  iid: number,
  labelId: number,
  exemplarBbox: [number, number, number, number],
  maxPredictions = 200,
  scoreThreshold = 0.25,
): Promise<PredictSimilarResponse> {
  const { data } = await apiClient.post<PredictSimilarResponse>(
    `/projects/${pid}/images/${iid}/predict-similar`,
    {
      label_id: labelId,
      exemplar_bbox: exemplarBbox,
      max_predictions: maxPredictions,
      score_threshold: scoreThreshold,
    },
  );
  return data;
}

export async function updateAnnotation(
  aid: number,
  changes: Partial<{ x1: number; y1: number; x2: number; y2: number; label_id: number; source: AnnotationSource }>,
  version: number,
): Promise<Annotation> {
  const { data } = await apiClient.put<Annotation>(`/annotations/${aid}`, {
    ...changes,
    version,
  });
  return data;
}

export async function deleteAnnotation(aid: number): Promise<void> {
  await apiClient.delete(`/annotations/${aid}`);
}

export async function bulkAnnotations(
  pid: number,
  iid: number,
  action: "accept_all" | "reject_all",
): Promise<{ affected: number; action: string }> {
  const { data } = await apiClient.patch(
    `/projects/${pid}/images/${iid}/annotations/bulk`,
    { action },
  );
  return data;
}
```

- [ ] **Step 5: Verify TypeScript compiles**

Run: `cd frontend && npm run build`
Expected: passes.

- [ ] **Step 6: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/types/annotation.ts \
        frontend/src/api/images.ts frontend/src/api/annotations.ts
git commit -m "feat(frontend): add annotation/image types + API clients + react-konva dep"
```

---

## Task 13: Frontend — ImageCanvas (react-konva, just image + transform)

**Files:**
- Create: `frontend/src/components/canvas/ImageCanvas.tsx`
- Create: `frontend/src/hooks/useImageElement.ts`

- [ ] **Step 1: Create useImageElement.ts**

```typescript
// frontend/src/hooks/useImageElement.ts
import { useEffect, useState } from "react";

export function useImageElement(src: string): HTMLImageElement | null {
  const [img, setImg] = useState<HTMLImageElement | null>(null);

  useEffect(() => {
    setImg(null);
    const el = new window.Image();
    el.onload = () => setImg(el);
    el.onerror = () => setImg(null);
    el.src = src;
    return () => {
      el.onload = null;
      el.onerror = null;
    };
  }, [src]);

  return img;
}
```

- [ ] **Step 2: Create ImageCanvas.tsx**

```tsx
// frontend/src/components/canvas/ImageCanvas.tsx
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Layer, Stage, Image as KImage } from "react-konva";

import { useImageElement } from "../../hooks/useImageElement";

interface Props {
  src: string;
  imageWidth: number;
  imageHeight: number;
  containerWidth: number;
  containerHeight: number;
  children?: (ctx: { scale: number; offsetX: number; offsetY: number }) => ReactNode;
}

export function ImageCanvas({
  src, imageWidth, imageHeight, containerWidth, containerHeight, children,
}: Props): JSX.Element {
  const img = useImageElement(src);
  const stageRef = useRef<any>(null);

  // Fit-to-container scale
  const scale = Math.min(
    containerWidth / imageWidth,
    containerHeight / imageHeight,
    1,
  );
  const displayW = imageWidth * scale;
  const displayH = imageHeight * scale;
  const offsetX = (containerWidth - displayW) / 2;
  const offsetY = (containerHeight - displayH) / 2;

  return (
    <Stage
      ref={stageRef}
      width={containerWidth}
      height={containerHeight}
      style={{ background: "#1a202c" }}
    >
      <Layer>
        {img && (
          <KImage
            image={img}
            x={offsetX}
            y={offsetY}
            width={displayW}
            height={displayH}
          />
        )}
      </Layer>
      {children && children({ scale, offsetX, offsetY })}
    </Stage>
  );
}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: passes.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/canvas/ImageCanvas.tsx frontend/src/hooks/useImageElement.ts
git commit -m "feat(frontend): add ImageCanvas (react-konva) with fit-to-container scaling"
```

---

## Task 14: Frontend — BBoxLayer + BBoxItem (render boxes)

**Files:**
- Create: `frontend/src/components/canvas/BBoxItem.tsx`
- Create: `frontend/src/components/canvas/BBoxLayer.tsx`

- [ ] **Step 1: Create BBoxItem.tsx**

```tsx
// frontend/src/components/canvas/BBoxItem.tsx
import { Group, Rect, Text } from "react-konva";

import type { Annotation } from "../../types/annotation";

interface Props {
  ann: Annotation;
  scale: number;
  offsetX: number;
  offsetY: number;
  selected: boolean;
  onSelect: () => void;
  onChange: (bbox: [number, number, number, number]) => void;
}

export function BBoxItem({
  ann, scale, offsetX, offsetY, selected, onSelect, onChange,
}: Props): JSX.Element {
  const [x1, y1, x2, y2] = ann.bbox;
  const dx = offsetX + x1 * scale;
  const dy = offsetY + y1 * scale;
  const dw = (x2 - x1) * scale;
  const dh = (y2 - y1) * scale;
  const isPending = ann.source === "geco2_pending";
  const stroke = ann.label.color;
  const fade = isPending ? 0.5 : 1.0;
  const lowConfidence = ann.score !== null && ann.score < 0.5;

  return (
    <Group
      x={dx}
      y={dy}
      draggable={selected}
      onClick={onSelect}
      onTap={onSelect}
      onDragEnd={(e) => {
        const newX = e.target.x();
        const newY = e.target.y();
        const ix = Math.round((newX - offsetX) / scale);
        const iy = Math.round((newY - offsetY) / scale);
        onChange([ix, iy, ix + Math.round(dw / scale), iy + Math.round(dh / scale)]);
      }}
    >
      <Rect
        width={dw}
        height={dh}
        stroke={stroke}
        strokeWidth={selected ? 3 : 2}
        dash={isPending ? [6, 4] : undefined}
        opacity={fade * (lowConfidence ? 0.7 : 1.0)}
        fill={selected ? `${stroke}33` : undefined}
      />
      <Text
        text={`${ann.label.name}${ann.score !== null ? ` ${ann.score.toFixed(2)}` : ""}`}
        fontSize={11}
        fill="white"
        x={2}
        y={-14}
        padding={2}
        background="black"
      />
    </Group>
  );
}
```

- [ ] **Step 2: Create BBoxLayer.tsx**

```tsx
// frontend/src/components/canvas/BBoxLayer.tsx
import { Layer } from "react-konva";

import type { Annotation } from "../../types/annotation";

import { BBoxItem } from "./BBoxItem";

interface Props {
  annotations: Annotation[];
  selectedId: number | null;
  scale: number;
  offsetX: number;
  offsetY: number;
  onSelect: (id: number | null) => void;
  onChange: (id: number, bbox: [number, number, number, number]) => void;
}

export function BBoxLayer({
  annotations, selectedId, scale, offsetX, offsetY, onSelect, onChange,
}: Props): JSX.Element {
  return (
    <Layer>
      {annotations.map((ann) => (
        <BBoxItem
          key={ann.id}
          ann={ann}
          scale={scale}
          offsetX={offsetX}
          offsetY={offsetY}
          selected={selectedId === ann.id}
          onSelect={() => onSelect(ann.id)}
          onChange={(b) => onChange(ann.id, b)}
        />
      ))}
    </Layer>
  );
}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: passes.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/canvas/BBoxItem.tsx frontend/src/components/canvas/BBoxLayer.tsx
git commit -m "feat(frontend): add BBoxLayer + BBoxItem (drag-to-move, dashed for pending)"
```

---

## Task 15: Frontend — ExemplarTool (drag to draw new bbox)

**Files:**
- Create: `frontend/src/components/canvas/ExemplarTool.tsx`

- [ ] **Step 1: Create ExemplarTool.tsx**

```tsx
// frontend/src/components/canvas/ExemplarTool.tsx
import { useState } from "react";
import { Layer, Rect } from "react-konva";

interface Props {
  active: boolean;
  scale: number;
  offsetX: number;
  offsetY: number;
  onDrawn: (bbox: [number, number, number, number]) => void;
}

export function ExemplarTool({
  active, scale, offsetX, offsetY, onDrawn,
}: Props): JSX.Element | null {
  const [start, setStart] = useState<{ x: number; y: number } | null>(null);
  const [end, setEnd] = useState<{ x: number; y: number } | null>(null);

  if (!active) return null;

  const onMouseDown = (e: any): void => {
    const stage = e.target.getStage();
    const pos = stage.getPointerPosition();
    if (!pos) return;
    setStart(pos);
    setEnd(pos);
  };

  const onMouseMove = (e: any): void => {
    if (!start) return;
    const stage = e.target.getStage();
    const pos = stage.getPointerPosition();
    if (!pos) return;
    setEnd(pos);
  };

  const onMouseUp = (): void => {
    if (!start || !end) {
      setStart(null);
      setEnd(null);
      return;
    }
    const x1 = Math.round((Math.min(start.x, end.x) - offsetX) / scale);
    const y1 = Math.round((Math.min(start.y, end.y) - offsetY) / scale);
    const x2 = Math.round((Math.max(start.x, end.x) - offsetX) / scale);
    const y2 = Math.round((Math.max(start.y, end.y) - offsetY) / scale);
    if (x2 - x1 >= 4 && y2 - y1 >= 4) {
      onDrawn([x1, y1, x2, y2]);
    }
    setStart(null);
    setEnd(null);
  };

  return (
    <Layer
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onTouchStart={onMouseDown}
      onTouchMove={onMouseMove}
      onTouchEnd={onMouseUp}
    >
      {/* Invisible full-stage hit area */}
      <Rect x={0} y={0} width={9999} height={9999} fill="rgba(0,0,0,0.01)" />
      {start && end && (
        <Rect
          x={Math.min(start.x, end.x)}
          y={Math.min(start.y, end.y)}
          width={Math.abs(end.x - start.x)}
          height={Math.abs(end.y - start.y)}
          stroke="#fbbf24"
          strokeWidth={2}
          dash={[8, 4]}
          fill="rgba(251,191,36,0.15)"
        />
      )}
    </Layer>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/canvas/ExemplarTool.tsx
git commit -m "feat(frontend): add ExemplarTool layer for drag-to-draw new bbox"
```

---

## Task 16: Frontend — annotate sub-components (ClassPicker / Toolbar / SaveIndicator / ImageList)

**Files:**
- Create: `frontend/src/components/annotate/ClassPicker.tsx`
- Create: `frontend/src/components/annotate/Toolbar.tsx`
- Create: `frontend/src/components/annotate/SaveIndicator.tsx`
- Create: `frontend/src/components/annotate/ImageList.tsx`

- [ ] **Step 1: Create ClassPicker.tsx**

```tsx
// frontend/src/components/annotate/ClassPicker.tsx
import { useState } from "react";

import { addLabel } from "../../api/projects";
import type { Label } from "../../types/project";

interface Props {
  pid: number;
  labels: (Label & { id: number })[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onLabelsChanged: () => void;
}

export function ClassPicker({
  pid, labels, selectedId, onSelect, onLabelsChanged,
}: Props): JSX.Element {
  const [newName, setNewName] = useState("");
  const [busy, setBusy] = useState(false);

  const add = async (): Promise<void> => {
    if (!newName) return;
    setBusy(true);
    try {
      await addLabel(pid, newName);
      setNewName("");
      onLabelsChanged();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <h4 style={{ margin: "0 0 6px 0", fontSize: 12, color: "#a0aec0" }}>
        当前类别
      </h4>
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {labels.map((l) => (
          <button
            key={l.id}
            onClick={() => onSelect(l.id)}
            style={{
              padding: "6px 10px",
              border: `2px solid ${selectedId === l.id ? l.color : "#2d3748"}`,
              borderRadius: 4,
              background: selectedId === l.id ? `${l.color}33` : "#1a202c",
              color: "white",
              textAlign: "left",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <span
              style={{
                width: 12, height: 12, borderRadius: 2, background: l.color,
              }}
            />
            {l.name}
          </button>
        ))}
      </div>
      <div style={{ marginTop: 8, display: "flex", gap: 4 }}>
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder="+ 加新标签"
          disabled={busy}
          style={{ flex: 1, padding: 4, fontSize: 12 }}
        />
        <button onClick={add} disabled={busy || !newName}>+</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create Toolbar.tsx**

```tsx
// frontend/src/components/annotate/Toolbar.tsx
type Mode = "select" | "exemplar";

interface Props {
  mode: Mode;
  onModeChange: (m: Mode) => void;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  onDelete: () => void;
  hasSelection: boolean;
  hasPending: boolean;
  predictBusy: boolean;
}

export function Toolbar({
  mode, onModeChange, onAcceptAll, onRejectAll, onDelete,
  hasSelection, hasPending, predictBusy,
}: Props): JSX.Element {
  return (
    <div style={{ marginTop: 16 }}>
      <h4 style={{ margin: "0 0 6px 0", fontSize: 12, color: "#a0aec0" }}>模式</h4>
      <div style={{ display: "flex", gap: 4 }}>
        {(["exemplar", "select"] as const).map((m) => (
          <button
            key={m}
            onClick={() => onModeChange(m)}
            disabled={predictBusy}
            style={{
              flex: 1,
              padding: 6,
              background: mode === m ? "#3182ce" : "#2d3748",
              color: "white",
              border: "none",
              borderRadius: 4,
              cursor: "pointer",
              fontSize: 12,
            }}
          >
            {m === "exemplar" ? "画 exemplar (E)" : "选择/编辑 (V)"}
          </button>
        ))}
      </div>
      <h4 style={{ margin: "16px 0 6px 0", fontSize: 12, color: "#a0aec0" }}>操作</h4>
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <button onClick={onAcceptAll} disabled={!hasPending}>✓ 全部接受</button>
        <button onClick={onRejectAll} disabled={!hasPending}>✗ 全部拒绝</button>
        <button onClick={onDelete} disabled={!hasSelection}>⌫ 删除选中 (Del)</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create SaveIndicator.tsx**

```tsx
// frontend/src/components/annotate/SaveIndicator.tsx
import { useEffect, useState } from "react";

interface Props {
  state: "idle" | "saving" | "saved" | "error";
  lastError?: string | null;
  lastElapsedMs?: number | null;
}

export function SaveIndicator({ state, lastError, lastElapsedMs }: Props): JSX.Element {
  const [pulse, setPulse] = useState(false);

  useEffect(() => {
    if (state === "saved") {
      setPulse(true);
      const t = setTimeout(() => setPulse(false), 1500);
      return () => clearTimeout(t);
    }
  }, [state]);

  const colors = {
    idle: "#a0aec0",
    saving: "#ecc94b",
    saved: pulse ? "#48bb78" : "#a0aec0",
    error: "#e53e3e",
  };
  const labels = {
    idle: "待编辑",
    saving: "保存中…",
    saved: "已保存",
    error: lastError ?? "保存失败",
  };

  return (
    <div style={{ marginTop: 16, fontSize: 12 }}>
      <span style={{ color: colors[state] }}>● {labels[state]}</span>
      {lastElapsedMs != null && (
        <span style={{ color: "#718096", marginLeft: 8 }}>
          GECO2 {lastElapsedMs}ms
        </span>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Create ImageList.tsx**

```tsx
// frontend/src/components/annotate/ImageList.tsx
import type { ImageListResponse, ImageItem } from "../../types/annotation";

interface Props {
  data: ImageListResponse;
  currentId: number | null;
  onSelect: (img: ImageItem) => void;
}

export function ImageList({ data, currentId, onSelect }: Props): JSX.Element {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ flex: 1, overflowY: "auto" }}>
        {data.items.map((img) => {
          const active = img.id === currentId;
          return (
            <div
              key={img.id}
              onClick={() => onSelect(img)}
              style={{
                padding: "6px 8px",
                background: active ? "#2d3748" : "transparent",
                color: "white",
                cursor: "pointer",
                borderLeft: `4px solid ${
                  img.annotation_count > 0 ? "#48bb78" : "transparent"
                }`,
                display: "flex",
                justifyContent: "space-between",
                fontSize: 12,
              }}
            >
              <span>{img.filename}</span>
              <span style={{ color: "#718096" }}>{img.annotation_count}</span>
            </div>
          );
        })}
      </div>
      <div style={{ padding: 8, borderTop: "1px solid #2d3748", fontSize: 11, color: "#a0aec0" }}>
        {(["train", "val", "test"] as const).map((s) => (
          <div key={s}>
            {s}: {data.progress[s].annotated} / {data.progress[s].total}
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Verify build**

Run: `cd frontend && npm run build`
Expected: passes.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/annotate/
git commit -m "feat(frontend): add ClassPicker, Toolbar, SaveIndicator, ImageList components"
```

---

## Task 17: Frontend — useAnnotations + useSaveState hooks

**Files:**
- Create: `frontend/src/hooks/useSaveState.ts`
- Create: `frontend/src/hooks/useAnnotations.ts`

- [ ] **Step 1: Create useSaveState.ts**

```typescript
// frontend/src/hooks/useSaveState.ts
import { useCallback, useState } from "react";

export type SaveState = "idle" | "saving" | "saved" | "error";

export function useSaveState() {
  const [state, setState] = useState<SaveState>("idle");
  const [error, setError] = useState<string | null>(null);

  const wrap = useCallback(async <T,>(fn: () => Promise<T>): Promise<T | null> => {
    setState("saving");
    setError(null);
    try {
      const result = await fn();
      setState("saved");
      return result;
    } catch (e) {
      setError(String(e));
      setState("error");
      return null;
    }
  }, []);

  return { state, error, wrap };
}
```

- [ ] **Step 2: Create useAnnotations.ts**

```typescript
// frontend/src/hooks/useAnnotations.ts
import { useCallback, useEffect, useState } from "react";

import {
  bulkAnnotations,
  deleteAnnotation,
  listAnnotations,
  predictSimilar,
  updateAnnotation,
} from "../api/annotations";
import type { Annotation } from "../types/annotation";

export function useAnnotations(pid: number, iid: number | null) {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [lastElapsedMs, setLastElapsedMs] = useState<number | null>(null);
  const [predictBusy, setPredictBusy] = useState(false);

  const refetch = useCallback(async (): Promise<void> => {
    if (iid == null) return;
    const items = await listAnnotations(iid);
    setAnnotations(items);
  }, [iid]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  const drawExemplar = useCallback(
    async (labelId: number, bbox: [number, number, number, number]): Promise<void> => {
      if (iid == null) return;
      setPredictBusy(true);
      try {
        const res = await predictSimilar(pid, iid, labelId, bbox);
        setLastElapsedMs(res.elapsed_ms);
        await refetch();
      } finally {
        setPredictBusy(false);
      }
    },
    [pid, iid, refetch],
  );

  const updateBbox = useCallback(
    async (aid: number, bbox: [number, number, number, number], version: number): Promise<void> => {
      const updated = await updateAnnotation(
        aid,
        { x1: bbox[0], y1: bbox[1], x2: bbox[2], y2: bbox[3] },
        version,
      );
      setAnnotations((prev) => prev.map((a) => (a.id === aid ? updated : a)));
    },
    [],
  );

  const accept = useCallback(
    async (aid: number, version: number): Promise<void> => {
      const updated = await updateAnnotation(aid, { source: "geco2_accepted" }, version);
      setAnnotations((prev) => prev.map((a) => (a.id === aid ? updated : a)));
    },
    [],
  );

  const remove = useCallback(
    async (aid: number): Promise<void> => {
      await deleteAnnotation(aid);
      setAnnotations((prev) => prev.filter((a) => a.id !== aid));
    },
    [],
  );

  const acceptAll = useCallback(async (): Promise<void> => {
    if (iid == null) return;
    await bulkAnnotations(pid, iid, "accept_all");
    await refetch();
  }, [pid, iid, refetch]);

  const rejectAll = useCallback(async (): Promise<void> => {
    if (iid == null) return;
    await bulkAnnotations(pid, iid, "reject_all");
    await refetch();
  }, [pid, iid, refetch]);

  return {
    annotations,
    predictBusy,
    lastElapsedMs,
    drawExemplar,
    updateBbox,
    accept,
    remove,
    acceptAll,
    rejectAll,
    refetch,
  };
}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: passes.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/useSaveState.ts frontend/src/hooks/useAnnotations.ts
git commit -m "feat(frontend): add useSaveState + useAnnotations hooks"
```

---

## Task 18: Frontend — AnnotatePage assembly

**Files:**
- Create: `frontend/src/pages/AnnotatePage.tsx`
- Modify: `frontend/src/App.tsx` (add route)

- [ ] **Step 1: Create AnnotatePage.tsx**

```tsx
// frontend/src/pages/AnnotatePage.tsx
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { listImages, imageFileUrl } from "../api/images";
import { getProject } from "../api/projects";
import { BBoxLayer } from "../components/canvas/BBoxLayer";
import { ExemplarTool } from "../components/canvas/ExemplarTool";
import { ImageCanvas } from "../components/canvas/ImageCanvas";
import { ClassPicker } from "../components/annotate/ClassPicker";
import { ImageList } from "../components/annotate/ImageList";
import { SaveIndicator } from "../components/annotate/SaveIndicator";
import { Toolbar } from "../components/annotate/Toolbar";
import { useAnnotations } from "../hooks/useAnnotations";
import { useSaveState } from "../hooks/useSaveState";
import type { ImageItem, ImageListResponse } from "../types/annotation";
import type { Project } from "../types/project";

type Mode = "select" | "exemplar";

export function AnnotatePage(): JSX.Element {
  const [searchParams] = useSearchParams();
  const pid = Number(searchParams.get("project_id"));

  const [project, setProject] = useState<Project | null>(null);
  const [imageList, setImageList] = useState<ImageListResponse | null>(null);
  const [currentImage, setCurrentImage] = useState<ImageItem | null>(null);
  const [selectedLabelId, setSelectedLabelId] = useState<number | null>(null);
  const [selectedAnnId, setSelectedAnnId] = useState<number | null>(null);
  const [mode, setMode] = useState<Mode>("exemplar");

  const containerRef = useRef<HTMLDivElement>(null);
  const [containerSize, setContainerSize] = useState({ w: 800, h: 600 });

  const ann = useAnnotations(pid, currentImage?.id ?? null);
  const save = useSaveState();

  // Load project + image list
  useEffect(() => {
    if (!pid) return;
    getProject(pid).then((p) => {
      setProject(p);
      if (p.labels.length > 0 && selectedLabelId == null) {
        setSelectedLabelId((p.labels as { id: number; name: string; color: string }[])[0].id);
      }
    });
    listImages(pid).then((data) => {
      setImageList(data);
      if (data.items.length > 0 && !currentImage) {
        setCurrentImage(data.items[0]);
      }
    });
  }, [pid]);

  // Resize observer
  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver((entries) => {
      const r = entries[0].contentRect;
      setContainerSize({ w: r.width, h: r.height });
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent): void => {
      if ((e.target as HTMLElement).tagName === "INPUT") return;
      if (e.key === "e" || e.key === "E") setMode("exemplar");
      else if (e.key === "v" || e.key === "V") setMode("select");
      else if ((e.key === "Delete" || e.key === "d" || e.key === "D") && selectedAnnId) {
        save.wrap(() => ann.remove(selectedAnnId));
        setSelectedAnnId(null);
      } else if ((e.key === "a" || e.key === "A") && selectedAnnId) {
        const a = ann.annotations.find((x) => x.id === selectedAnnId);
        if (a) save.wrap(() => ann.accept(a.id, a.version));
      } else if (e.key === "ArrowRight") {
        navigateImage(+1);
      } else if (e.key === "ArrowLeft") {
        navigateImage(-1);
      } else if (project && /^[1-9]$/.test(e.key)) {
        const idx = parseInt(e.key, 10) - 1;
        const labels = project.labels as { id: number; name: string; color: string }[];
        if (idx < labels.length) setSelectedLabelId(labels[idx].id);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  });

  const navigateImage = (delta: number): void => {
    if (!imageList || !currentImage) return;
    const i = imageList.items.findIndex((x) => x.id === currentImage.id);
    const next = imageList.items[Math.max(0, Math.min(imageList.items.length - 1, i + delta))];
    if (next) setCurrentImage(next);
  };

  const onExemplarDrawn = async (bbox: [number, number, number, number]): Promise<void> => {
    if (!selectedLabelId) {
      alert("先选一个类别");
      return;
    }
    await save.wrap(() => ann.drawExemplar(selectedLabelId, bbox));
    setMode("select");
  };

  const onBboxChange = async (id: number, bbox: [number, number, number, number]): Promise<void> => {
    const a = ann.annotations.find((x) => x.id === id);
    if (!a) return;
    await save.wrap(() => ann.updateBbox(id, bbox, a.version));
  };

  const refetchImages = (): void => {
    listImages(pid).then(setImageList);
  };

  if (!pid) return <div style={{ padding: 24 }}>missing project_id</div>;
  if (!project || !imageList) return <div style={{ padding: 24 }}>loading…</div>;

  const hasPending = ann.annotations.some((a) => a.source === "geco2_pending");
  const hasSelection = selectedAnnId != null;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "220px 1fr 280px", height: "100vh" }}>
      {/* Left: image list */}
      <aside style={{ background: "#171923", color: "white" }}>
        <ImageList
          data={imageList}
          currentId={currentImage?.id ?? null}
          onSelect={setCurrentImage}
        />
      </aside>

      {/* Center: canvas */}
      <main ref={containerRef} style={{ position: "relative", overflow: "hidden", background: "#1a202c" }}>
        {currentImage && (
          <ImageCanvas
            src={imageFileUrl(currentImage.id)}
            imageWidth={currentImage.width}
            imageHeight={currentImage.height}
            containerWidth={containerSize.w}
            containerHeight={containerSize.h - 40}
          >
            {(ctx) => (
              <>
                <BBoxLayer
                  annotations={ann.annotations}
                  selectedId={selectedAnnId}
                  scale={ctx.scale}
                  offsetX={ctx.offsetX}
                  offsetY={ctx.offsetY}
                  onSelect={(id) => setSelectedAnnId(id)}
                  onChange={(id, bbox) => onBboxChange(id, bbox)}
                />
                <ExemplarTool
                  active={mode === "exemplar"}
                  scale={ctx.scale}
                  offsetX={ctx.offsetX}
                  offsetY={ctx.offsetY}
                  onDrawn={onExemplarDrawn}
                />
              </>
            )}
          </ImageCanvas>
        )}
        {/* Bottom nav */}
        <div style={{
          position: "absolute", bottom: 0, left: 0, right: 0,
          height: 40, background: "#0f1419", display: "flex",
          alignItems: "center", justifyContent: "center", gap: 12, color: "white",
        }}>
          <button onClick={() => navigateImage(-1)}>← 上一张</button>
          <span>{currentImage?.filename ?? "-"}</span>
          <button onClick={() => navigateImage(+1)}>下一张 →</button>
        </div>
      </main>

      {/* Right: tools */}
      <aside style={{ background: "#171923", color: "white", padding: 16, overflowY: "auto" }}>
        <ClassPicker
          pid={pid}
          labels={project.labels as { id: number; name: string; color: string }[]}
          selectedId={selectedLabelId}
          onSelect={setSelectedLabelId}
          onLabelsChanged={() => getProject(pid).then(setProject)}
        />
        <Toolbar
          mode={mode}
          onModeChange={setMode}
          onAcceptAll={() => save.wrap(ann.acceptAll).then(refetchImages)}
          onRejectAll={() => save.wrap(ann.rejectAll).then(refetchImages)}
          onDelete={() => {
            if (selectedAnnId) {
              save.wrap(() => ann.remove(selectedAnnId)).then(refetchImages);
              setSelectedAnnId(null);
            }
          }}
          hasSelection={hasSelection}
          hasPending={hasPending}
          predictBusy={ann.predictBusy}
        />
        <SaveIndicator
          state={save.state}
          lastError={save.error}
          lastElapsedMs={ann.lastElapsedMs}
        />
      </aside>
    </div>
  );
}
```

- [ ] **Step 2: Add route in App.tsx**

Edit `frontend/src/App.tsx`:

```tsx
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { HomePage } from "./pages/HomePage";
import { AnnotatePage } from "./pages/AnnotatePage";
import { SetupPage } from "./pages/SetupPage";

export default function App(): JSX.Element {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/setup" element={<SetupPage />} />
        <Route path="/annotate" element={<AnnotatePage />} />
        <Route path="*" element={<div style={{ padding: 24 }}>404</div>} />
      </Routes>
    </BrowserRouter>
  );
}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: passes.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/AnnotatePage.tsx frontend/src/App.tsx
git commit -m "feat(frontend): add AnnotatePage (3-pane layout) + keyboard shortcuts + route"
```

---

## Task 19: End-to-end smoke test for annotation loop

**Files:**
- Create: `tests/e2e/test_phase2_annotation.py`

- [ ] **Step 1: Write the test**

```python
# tests/e2e/test_phase2_annotation.py
"""E2E Phase 2: image present → predict-similar → adjust → accept.

Mocks ml_backend (no GECO2 needed). Verifies REST integration end-to-end.
"""
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PILImage


@pytest.fixture
def client(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path))

    img_path = tmp_path / "img.jpg"
    PILImage.new("RGB", (200, 100)).save(img_path, "JPEG")

    from echobox_app.db.models import Base, Image, Label, Project
    from echobox_app.db.session import make_engine, make_session_factory
    from echobox_app.main import create_app

    engine = make_engine(f"sqlite:///{tmp_path}/db")
    Base.metadata.create_all(engine)
    sf = make_session_factory(engine)
    with sf() as s:
        p = Project(name="x", workspace_path=str(tmp_path), source_folder="/o",
                    status="annotating")
        s.add(p)
        s.flush()
        s.add(Label(project_id=p.id, name="crack", color="#000"))
        s.add(Image(
            project_id=p.id, filename="img.jpg", abs_path=str(img_path),
            width=200, height=100, split="train",
            index_in_project=0, source_path="/o/img.jpg",
        ))
        s.commit()
        ids = (p.id, p.images[0].id, p.labels[0].id)

    fake_ml = AsyncMock()
    fake_ml.predict_similar = AsyncMock(return_value={
        "predictions": [
            {"bbox": [10, 20, 50, 60], "score": 0.9},
            {"bbox": [70, 30, 110, 80], "score": 0.4},
        ],
        "exemplar_count": 1,
        "image_size": [200, 100],
        "elapsed_ms": 30,
    })

    app = create_app()
    from echobox_app.api import annotations as ann_mod
    app.dependency_overrides[ann_mod.ml_client_dep] = lambda: fake_ml
    return TestClient(app), ids


def test_full_annotation_loop(client) -> None:
    c, (pid, iid, lid) = client

    # 1. Predict similar
    r = c.post(f"/api/projects/{pid}/images/{iid}/predict-similar",
               json={"label_id": lid, "exemplar_bbox": [0, 0, 100, 50]})
    assert r.status_code == 201
    created = r.json()["created"]
    assert len(created) == 2

    # 2. Accept all
    r = c.patch(f"/api/projects/{pid}/images/{iid}/annotations/bulk",
                json={"action": "accept_all"})
    assert r.json()["affected"] == 2

    # 3. Verify state
    annotations = c.get(f"/api/images/{iid}/annotations").json()["items"]
    assert all(a["source"] == "geco2_accepted" for a in annotations)

    # 4. Edit one
    a = annotations[0]
    r = c.put(f"/api/annotations/{a['id']}",
              json={"x1": 5, "y1": 5, "x2": 60, "y2": 70, "version": a["version"]})
    assert r.status_code == 200
    assert r.json()["bbox"] == [5, 5, 60, 70]
    assert r.json()["source"] == "user_edited"

    # 5. Delete one
    r = c.delete(f"/api/annotations/{annotations[1]['id']}")
    assert r.status_code == 204

    # 6. Image list shows progress
    list_resp = c.get(f"/api/projects/{pid}/images").json()
    assert list_resp["progress"]["train"]["annotated"] == 1
```

- [ ] **Step 2: Run test**

Run: `uv run pytest tests/e2e/test_phase2_annotation.py -v`
Expected: PASS.

- [ ] **Step 3: Run full suite**

Run: `make test`
Expected: all tests across all packages pass.

- [ ] **Step 4: Commit + tag**

```bash
git add tests/e2e/test_phase2_annotation.py
git commit -m "test(e2e): add Phase 2 annotation loop end-to-end test (mocked ml_backend)"
git tag -a v0.0.3-phase2 -m "Plan 3 complete: Phase 2 annotation end-to-end (with mocked GECO2 in CI)"
git log --oneline | head -10
```

---

## Done Criteria

After all 19 tasks:

- [x] ml_backend loads real GECO2 (or fails gracefully) + serves `/predict_similar`
- [x] app `/api/images`, `/api/annotations`, `/api/.../predict-similar` all work
- [x] Frontend AnnotatePage: image canvas + draw exemplar + render bboxes + edit + save
- [x] Keyboard shortcuts (A, D, E, V, 1-9, ←→) work
- [x] Real-time save with toast/indicator
- [x] `make test` all green
- [x] Git tag `v0.0.3-phase2`

## What's NOT in this plan (defer to Plan 4)

- Exporters (COCO, YOLO, VOC, ls_json)
- MCP server's 3 real tools
- README quick-start, demo GIF
- CI workflows
- CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, CHANGELOG.md
- Architecture docs

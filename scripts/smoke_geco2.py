"""Real GECO2 model smoke: load + run a single prediction on a tiny test image.

Run from repo root:
    ECHOBOX_ML_GECO2_WEIGHTS=./.data/weights/CNTQG_multitrain_ca44.pth \
        uv run --package echobox-ml python scripts/smoke_geco2.py

Skips gracefully if weights missing or torch unavailable.
"""

import os
import sys
import tempfile
from pathlib import Path


def main() -> int:
    weights = os.environ.get(
        "ECHOBOX_ML_GECO2_WEIGHTS", "./.data/weights/CNTQG_multitrain_ca44.pth"
    )
    weights_path = Path(weights)
    if not weights_path.exists():
        print(f"SKIP: weights not at {weights_path}")
        return 0

    try:
        from echobox_ml.runner import Geco2Runner
        from PIL import Image
    except ImportError as e:
        print(f"SKIP: missing dep {e}")
        return 0

    runner = Geco2Runner(weights_path=weights_path, device="auto")
    print(f"==> resolved device: {runner.device}")
    print("==> loading model (first run downloads SAM2 backbone weights from facebook URL)…")
    try:
        runner.load()
        print("==> model loaded.")
    except Exception as e:
        print(f"FAIL: load: {type(e).__name__}: {e}")
        return 1

    with tempfile.TemporaryDirectory() as td:
        img_path = Path(td) / "test.jpg"
        Image.new("RGB", (256, 256), color=(123, 80, 50)).save(img_path, "JPEG")
        print(f"==> running predict_similar on {img_path}…")
        try:
            preds, size, ms = runner.predict_similar(
                image_path=img_path,
                exemplar_bbox=(40, 40, 120, 120),
                max_predictions=10,
                score_threshold=0.05,
            )
        except Exception as e:
            print(f"FAIL: predict: {type(e).__name__}: {e}")
            return 2

    print(f"==> {len(preds)} predictions, image_size={size}, elapsed_ms={ms}")
    for i, p in enumerate(preds[:5]):
        print(f"    [{i}] bbox={p.bbox} score={p.score:.3f}")
    print("OK: GECO2 smoke complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

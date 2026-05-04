"""FastAPI app entry point for ml_backend."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from echobox_ml import __version__
from echobox_ml.config import MLSettings
from echobox_ml.runner import Geco2Runner, Geco2RunnerStub
from echobox_ml.schemas import Prediction as PredOut
from echobox_ml.schemas import PredictRequest, PredictResponse


def create_app(settings: MLSettings | None = None) -> FastAPI:
    settings = settings or MLSettings()
    app = FastAPI(title="echobox-ml", version=__version__)
    # Use real Geco2Runner when weights file exists; fall back to stub otherwise.
    use_real = settings.geco2_weights is not None and settings.geco2_weights.exists()
    runner: Geco2Runner | Geco2RunnerStub = (
        Geco2Runner(
            weights_path=settings.geco2_weights,
            sam2_weights_path=settings.sam2_weights,
            device=settings.device,
        )
        if use_real
        else Geco2RunnerStub(weights_path=settings.geco2_weights, device=settings.device)
    )
    app.state.settings = settings
    app.state.runner = runner

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "echobox-ml",
            "version": __version__,
            "model_loaded": runner.is_loaded,
            "device": runner.device,
        }

    @app.post("/predict_similar", response_model=None)
    def predict_similar(payload: PredictRequest) -> PredictResponse | JSONResponse:
        try:
            preds, image_size, elapsed = runner.predict_similar(
                Path(payload.image_path),
                tuple(payload.exemplar_bbox),  # type: ignore[arg-type]
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

    return app


def run() -> None:
    """Entry point for `echobox-ml` console script."""
    import uvicorn

    settings = MLSettings()
    uvicorn.run(
        "echobox_ml.main:create_app",
        host=settings.host,
        port=settings.port,
        factory=True,
        reload=False,
    )

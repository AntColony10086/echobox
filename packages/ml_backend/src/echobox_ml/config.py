"""ML backend configuration."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class MLSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ECHOBOX_ML_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 9090

    device: Literal["auto", "cuda", "mps", "cpu"] = "auto"
    geco2_weights: Path | None = None  # required when actually loading model in Plan 3
    sam2_weights: Path | None = None

    max_predictions_default: int = 200
    score_threshold_default: float = 0.25
    inference_timeout_s: float = 30.0

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "pretty"] = "pretty"

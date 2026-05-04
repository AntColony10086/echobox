"""Application configuration loaded from environment / .env file."""

from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ECHOBOX_APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 8000

    db_url: str = "sqlite:///.data/projects.db"
    data_dir: Path = Path(".data")

    ml_backend_url: str = "http://localhost:9090"
    ml_backend_timeout_s: float = 30.0

    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_api_key: SecretStr
    llm_model: str = "qwen-plus"
    llm_timeout_s: float = 60.0

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "pretty"] = "pretty"

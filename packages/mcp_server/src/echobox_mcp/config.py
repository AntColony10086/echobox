"""MCP server configuration."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ECHOBOX_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_url: str = "http://localhost:8000"
    app_request_timeout_s: float = 60.0

    transport: Literal["stdio", "sse"] = "stdio"
    sse_port: int = 9100

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "pretty"] = "pretty"

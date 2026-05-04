"""FastAPI dependencies."""

from collections.abc import Generator
from pathlib import Path

from fastapi import FastAPI, Request
from sqlalchemy.orm import Session

from echobox_app.config import AppSettings


def get_settings(app: FastAPI) -> AppSettings:
    settings: AppSettings = app.state.settings
    return settings


def get_workspace_root(settings: AppSettings) -> Path:
    return settings.data_dir / "projects"


def session_dep(request: Request) -> Generator[Session, None, None]:
    factory = request.app.state.session_factory
    s = factory()
    try:
        yield s
    finally:
        s.close()


def settings_dep(request: Request) -> AppSettings:
    return get_settings(request.app)

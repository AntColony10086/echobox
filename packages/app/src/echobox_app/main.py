"""FastAPI app entry point."""

from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from echobox_app import __version__
from echobox_app.config import AppSettings
from echobox_app.db.session import make_engine, make_session_factory
from echobox_app.errors import ArisError
from echobox_app.logging import configure_logging


def create_app(settings: AppSettings | None = None) -> FastAPI:
    settings = settings or AppSettings()  # type: ignore[call-arg]
    configure_logging(level=settings.log_level, fmt=settings.log_format)

    app = FastAPI(title="echobox-app", version=__version__)
    engine = make_engine(settings.db_url)
    session_factory = make_session_factory(engine)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory

    from echobox_app.api.projects import router as projects_router

    app.include_router(projects_router)

    from echobox_app.api.chat import router as chat_router

    app.include_router(chat_router)

    from echobox_app.api.images import router as images_router

    app.include_router(images_router)

    from echobox_app.api.annotations import router as annotations_router

    app.include_router(annotations_router)

    from echobox_app.api.exports import router as exports_router

    app.include_router(exports_router)

    @app.exception_handler(ArisError)
    async def _aris_error_handler(request: Any, exc: ArisError) -> JSONResponse:  # noqa: ARG001
        return JSONResponse(status_code=exc.http_status, content=exc.to_dict())

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        db_status = "ok"
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception:
            db_status = "unreachable"
        return {
            "status": "ok",
            "service": "echobox-app",
            "version": __version__,
            "db": db_status,
        }

    return app


def run() -> None:
    """Entry point for `echobox-app` console script."""
    import uvicorn

    settings = AppSettings()  # type: ignore[call-arg]
    uvicorn.run(
        "echobox_app.main:create_app",
        host=settings.host,
        port=settings.port,
        factory=True,
        reload=False,
    )

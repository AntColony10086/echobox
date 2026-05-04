"""POST /api/projects/{pid}/exports — produce a dataset export folder."""

import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from echobox_app.api.deps import session_dep, settings_dep
from echobox_app.config import AppSettings
from echobox_app.db.models import Annotation, Image, Project
from echobox_app.errors import ProjectNotFound, ValidationError
from echobox_app.exporters.base import ExportContext
from echobox_app.exporters.registry import EXPORTERS, get_exporter

router = APIRouter(tags=["exports"])


@router.get("/api/projects/{pid}/exports/default-dir")
def get_default_export_dir(
    pid: int,
    session: Annotated[Session, Depends(session_dep)],
    settings: Annotated[AppSettings, Depends(settings_dep)],
) -> dict[str, Any]:
    """Return the default export base dir (frontend uses as placeholder)."""
    project = session.get(Project, pid)
    if project is None:
        raise ProjectNotFound(f"project {pid} not found")
    default = (settings.data_dir / "projects" / str(pid) / "exports").resolve()
    return {"default_output_dir": str(default)}


class ExportRequest(BaseModel):
    format: str | None = None
    include_pending: bool = False
    splits: list[Literal["train", "val", "test"]] | None = None
    # Optional override. If provided, exports go to {output_dir}/{timestamp}-{fmt}/
    # Else default to <workspace>/exports/{timestamp}-{fmt}/
    # Supports ~ expansion. Must be absolute after expansion.
    output_dir: str | None = None


@router.post("/api/projects/{pid}/exports")
def create_export(
    pid: int,
    payload: ExportRequest,
    session: Annotated[Session, Depends(session_dep)],
    settings: Annotated[AppSettings, Depends(settings_dep)],
) -> dict[str, Any]:
    project = session.get(Project, pid)
    if project is None:
        raise ProjectNotFound(f"project {pid} not found")

    fmt = payload.format or project.export_format
    if fmt is None:
        raise ValidationError("no format specified and project has no default")
    if fmt not in EXPORTERS:
        raise ValidationError(f"unknown format: {fmt}")

    splits = tuple(payload.splits or ("train", "val", "test"))

    images = list(
        session.scalars(
            select(Image).where(Image.project_id == pid).order_by(Image.index_in_project)
        )
    )
    annotations_by_image: dict[int, list[Annotation]] = {}
    for img in images:
        annotations_by_image[img.id] = list(
            session.scalars(select(Annotation).where(Annotation.image_id == img.id))
        )

    if not images:
        raise ValidationError("no images to export")
    total_anns = sum(
        1
        for img in images
        for a in annotations_by_image[img.id]
        if payload.include_pending or a.source != "geco2_pending"
    )
    if total_anns == 0:
        raise ValidationError("no annotations to export")

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    export_id = f"{timestamp}-{fmt}"
    workspace_path = settings.data_dir / "projects" / str(pid)

    if payload.output_dir:
        base = Path(payload.output_dir).expanduser()
        if not base.is_absolute():
            raise ValidationError(
                f"output_dir must be an absolute path (got {payload.output_dir!r})",
                detail={"output_dir": payload.output_dir},
            )
        try:
            base.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ValidationError(
                f"cannot create output_dir {base}: {e}",
                detail={"output_dir": str(base), "error": str(e)},
            ) from e
        export_dir = base / export_id
    else:
        export_dir = workspace_path / "exports" / export_id

    ctx = ExportContext(
        project_id=pid,
        project_name=project.name,
        workspace_path=workspace_path,
        export_dir=export_dir,
        labels=[(lbl.name, lbl.color) for lbl in project.labels],
        images=images,
        annotations_by_image=annotations_by_image,
        include_pending=payload.include_pending,
        splits=splits,
    )

    start = time.perf_counter()
    stats = get_exporter(fmt).export(ctx)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    return {
        "export_id": export_id,
        "format": fmt,
        "output_dir": str(export_dir.resolve()),
        "files": sorted(p.name for p in export_dir.iterdir()),
        "stats": {
            "total_images": stats.total_images,
            "total_annotations": stats.total_annotations,
            "by_split": {k: dict(v) for k, v in stats.by_split.items()},
        },
        "elapsed_ms": elapsed_ms,
    }

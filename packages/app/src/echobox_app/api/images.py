"""Image REST endpoints."""

from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
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

    counts: dict[int, int] = dict(
        session.execute(  # type: ignore[arg-type]
            select(Annotation.image_id, func.count(Annotation.id))
            .join(Image, Image.id == Annotation.image_id)
            .where(Image.project_id == pid)
            .where(Annotation.source != "geco2_pending")
            .group_by(Annotation.image_id)
        ).all()
    )

    items = [
        {
            "id": img.id,
            "filename": img.filename,
            "abs_path": img.abs_path,
            "width": img.width,
            "height": img.height,
            "split": img.split,
            "index_in_project": img.index_in_project,
            "annotation_count": counts.get(img.id, 0),
        }
        for img in images
    ]

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
        "id": img.id,
        "project_id": img.project_id,
        "filename": img.filename,
        "abs_path": img.abs_path,
        "width": img.width,
        "height": img.height,
        "split": img.split,
        "index_in_project": img.index_in_project,
    }


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
        # Fallbacks for projects created with old buggy WorkspaceManager paths
        # (double-`projects/` or workspace_path drift):
        candidates = [
            # legacy: data_dir/projects/projects/{pid}/data/image/<file>
            p.parent.parent.parent.parent
            / "projects"
            / p.parent.parent.parent.name
            / "data"
            / "image"
            / p.name,
            # legacy strip: data_dir/projects/{pid}/data/image/<file> when DB has the
            # double-prefix variant (rare, but covers the symmetric case)
        ]
        # Also try project source_folder (in case organize_images never ran but the
        # original source file exists)
        if img.source_path:
            candidates.append(Path(img.source_path))
        for cand in candidates:
            if cand.exists():
                # Self-heal: update the DB so subsequent requests are direct.
                img.abs_path = str(cand.resolve())
                session.commit()
                return FileResponse(cand, media_type=_guess_media_type(cand))
        raise ImageNotFound(f"file missing on disk: {p} (also checked {len(candidates)} fallbacks)")
    return FileResponse(p, media_type=_guess_media_type(p))


def _guess_media_type(p: Path) -> str:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }.get(p.suffix.lower(), "application/octet-stream")


def _compute_progress(session: Session, pid: int) -> dict[str, dict[str, int]]:
    rows = session.execute(
        select(Image.split, func.count(Image.id))
        .where(Image.project_id == pid)
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

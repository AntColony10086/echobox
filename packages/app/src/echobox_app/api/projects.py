"""Project REST endpoints (POST/GET; PATCH/POST labels/finalize in later tasks)."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from echobox_app.api.deps import session_dep, settings_dep
from echobox_app.config import AppSettings
from echobox_app.db.models import Label, Project
from echobox_app.errors import ArisError, LabelConflict, ProjectNotFound, ValidationError
from echobox_app.tools.labels import validate_label_name

router = APIRouter(prefix="/api/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    source_folder: str = Field(min_length=1)
    name: str | None = None
    initial_labels: list[str] | None = None
    train_val_test: tuple[float, float, float] | None = None
    export_format: str | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest,
    session: Annotated[Session, Depends(session_dep)],
    settings: Annotated[AppSettings, Depends(settings_dep)],
) -> dict[str, Any]:
    if payload.train_val_test is not None:
        s = sum(payload.train_val_test)
        if abs(s - 1.0) > 1e-6:
            raise ValidationError(
                f"train_val_test ratios must sum to 1.0 (got {s})",
                detail={"ratios": list(payload.train_val_test)},
            )
        train, val, test = payload.train_val_test
    else:
        train, val, test = 0.7, 0.15, 0.15

    if payload.export_format and payload.export_format not in {"coco", "yolo", "voc", "ls_json"}:
        raise ValidationError(f"unknown export_format: {payload.export_format}")

    name = payload.name or _default_name(payload.source_folder)
    project = Project(
        name=name,
        workspace_path="",
        source_folder=payload.source_folder,
        status="draft",
        export_format=payload.export_format,
        train_ratio=train,
        val_ratio=val,
        test_ratio=test,
    )
    session.add(project)
    session.flush()

    project.workspace_path = str((settings.data_dir / "projects" / str(project.id)).resolve())
    if payload.initial_labels:
        for lname in payload.initial_labels:
            session.add(
                Label(project_id=project.id, name=lname, color=_assign_color(len(project.labels)))
            )
    session.commit()
    session.refresh(project)

    return _project_to_dict(project, include_state=False)


@router.get("")
def list_projects(
    session: Annotated[Session, Depends(session_dep)],
) -> list[dict[str, Any]]:
    """List all projects (most recently updated first), without chat history."""
    projects = session.query(Project).order_by(Project.updated_at.desc()).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "source_folder": p.source_folder,
            "status": p.status,
            "image_count": len(p.images),
            "label_count": len(p.labels),
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in projects
    ]


@router.get("/{pid}")
def get_project(
    pid: int,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    project = session.get(Project, pid)
    if project is None:
        raise ProjectNotFound(f"project {pid} not found", detail={"project_id": pid})
    return _project_to_dict(project, include_state=True)


@router.delete("/{pid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    pid: int,
    session: Annotated[Session, Depends(session_dep)],
) -> None:
    """Delete a project: cascades to images/labels/annotations/chat in DB,
    and removes the workspace directory on disk if it exists."""
    import shutil

    project = session.get(Project, pid)
    if project is None:
        raise ProjectNotFound(f"project {pid} not found", detail={"project_id": pid})
    workspace = project.workspace_path
    session.delete(project)
    session.commit()
    if workspace:
        ws_path = Path(workspace)
        if ws_path.exists() and ws_path.is_dir():
            shutil.rmtree(ws_path, ignore_errors=True)


def _default_name(source_folder: str) -> str:
    base = Path(source_folder).name or "project"
    today = datetime.now(UTC).strftime("%Y%m%d")
    return f"{base}-{today}"


_PALETTE = [
    "#e63946",
    "#457b9d",
    "#2a9d8f",
    "#f4a261",
    "#264653",
    "#9b5de5",
    "#f15bb5",
    "#00bbf9",
    "#00f5d4",
    "#fee440",
]


def _assign_color(index: int) -> str:
    return _PALETTE[index % len(_PALETTE)]


class PatchFolder(BaseModel):
    folder: str = Field(min_length=1)


class PatchSplits(BaseModel):
    train: float
    val: float
    test: float


class PatchFormat(BaseModel):
    format: str


@router.patch("/{pid}/folder")
def patch_folder(
    pid: int,
    payload: PatchFolder,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    project = _get_or_404(session, pid)
    project.source_folder = payload.folder
    session.commit()
    session.refresh(project)
    return _project_to_dict(project, include_state=False)


@router.patch("/{pid}/splits")
def patch_splits(
    pid: int,
    payload: PatchSplits,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    if abs(payload.train + payload.val + payload.test - 1.0) > 1e-6:
        raise ValidationError(
            "train+val+test must sum to 1.0",
            detail={"train": payload.train, "val": payload.val, "test": payload.test},
        )
    project = _get_or_404(session, pid)
    project.train_ratio = payload.train
    project.val_ratio = payload.val
    project.test_ratio = payload.test
    session.commit()
    session.refresh(project)
    return _project_to_dict(project, include_state=False)


@router.patch("/{pid}/format")
def patch_format(
    pid: int,
    payload: PatchFormat,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    if payload.format not in {"coco", "yolo", "voc", "ls_json"}:
        raise ValidationError(f"unknown format: {payload.format}")
    project = _get_or_404(session, pid)
    project.export_format = payload.format  # type: ignore[assignment]
    session.commit()
    session.refresh(project)
    return _project_to_dict(project, include_state=False)


def _get_or_404(session: Session, pid: int) -> Project:
    project = session.get(Project, pid)
    if project is None:
        raise ProjectNotFound(f"project {pid} not found", detail={"project_id": pid})
    return project


def _project_to_dict(project: Project, *, include_state: bool) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": project.id,
        "name": project.name,
        "source_folder": project.source_folder,
        "workspace_path": project.workspace_path,
        "status": project.status,
        "export_format": project.export_format,
        "train_ratio": project.train_ratio,
        "val_ratio": project.val_ratio,
        "test_ratio": project.test_ratio,
        "labels": [{"id": lbl.id, "name": lbl.name, "color": lbl.color} for lbl in project.labels],
        "image_count": len(project.images),
    }
    if include_state:
        out["messages"] = [
            {
                "role": m.role,
                "content": m.content,
                "tool_call_id": m.tool_call_id,
                "tool_name": m.tool_name,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in project.chat_messages
        ]
    return out


class CreateLabel(BaseModel):
    name: str
    color: str | None = None


@router.post("/{pid}/labels", status_code=status.HTTP_201_CREATED)
def add_label(
    pid: int,
    payload: CreateLabel,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    project = _get_or_404(session, pid)
    if not validate_label_name(payload.name):
        raise ValidationError(
            f"invalid label name: {payload.name!r}",
            detail={"rule": "^[a-zA-Z0-9_-]+$"},
        )
    color = payload.color or _assign_color(len(project.labels))
    label = Label(project_id=project.id, name=payload.name, color=color)
    session.add(label)
    try:
        session.commit()
    except IntegrityError as err:
        session.rollback()
        raise LabelConflict(
            f"label {payload.name!r} already exists",
            detail={"name": payload.name},
        ) from err
    return {"id": label.id, "name": label.name, "color": label.color}


@router.delete("/{pid}/labels/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_label(
    pid: int,
    name: str,
    session: Annotated[Session, Depends(session_dep)],
    cascade: bool = False,
) -> None:
    """Delete a label.

    Default behavior (no cascade): only allowed in `draft` status; blocked in
    `annotating`/`ready` if any annotations reference the label.

    With `?cascade=true`: also delete every annotation of this label and remove
    the label regardless of project status. Use this from the annotate page when
    the user wants to remove a class entirely.
    """
    from sqlalchemy import delete as sql_delete

    from echobox_app.db.models import Annotation

    project = _get_or_404(session, pid)
    lbl = next((lbl for lbl in project.labels if lbl.name == name), None)
    if lbl is None:
        raise ProjectNotFound(f"label {name!r} not found in project {pid}")

    if cascade:
        session.execute(sql_delete(Annotation).where(Annotation.label_id == lbl.id))
        session.delete(lbl)
        session.commit()
        return

    # Non-cascade: original draft-only gate
    if project.status != "draft":
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "label_immutable",
                    "message": (
                        f"labels cannot be deleted in status={project.status} "
                        "(use ?cascade=true to also drop its annotations)"
                    ),
                }
            },
        )
    session.delete(lbl)
    session.commit()


class _FinalizeError(ArisError):
    code = "critic_failed"
    http_status = 400


@router.post("/{pid}/finalize")
def finalize(
    pid: int,
    session: Annotated[Session, Depends(session_dep)],
    settings: Annotated[AppSettings, Depends(settings_dep)],
) -> dict[str, Any]:
    project = _get_or_404(session, pid)

    # Auto-organize fallback: agents sometimes call scan_folder but skip
    # organize_images, leaving DB without Image rows. Run a one-shot scan +
    # organize here so finalize is idempotent and bulletproof.
    if not project.images and project.source_folder:
        _auto_scan_and_organize(session, project, settings)

    errors: list[str] = []
    if not project.labels:
        errors.append("label set empty")
    if not project.export_format:
        errors.append("export format not chosen")
    if not project.images:
        errors.append(f"no images found in source_folder {project.source_folder!r}")
    if abs(project.train_ratio + project.val_ratio + project.test_ratio - 1.0) > 1e-6:
        errors.append("split ratios do not sum to 1.0")

    if errors:
        raise _FinalizeError("critic failed", detail={"errors": errors})

    project.status = "ready"
    session.commit()
    session.refresh(project)
    return {"status": project.status, "id": project.id}


def _auto_scan_and_organize(session: Session, project: Project, settings: AppSettings) -> None:
    """One-shot scan + organize when finalize finds no Image rows.

    Mirrors what the agent's organize_images tool would do, but bypasses the
    LLM. Writes Image rows + mapping.json + splits.json to the workspace.
    """
    from pathlib import Path as _Path  # avoid clobbering top-level Path

    from echobox_app.tools.filesystem import organize_images, scan_folder
    from echobox_app.tools.splits import propose_split
    from echobox_app.workspace.manager import WorkspaceManager

    src = _Path(project.source_folder)
    if not src.exists() or not src.is_dir():
        return

    # WorkspaceManager appends "projects/{id}" to root internally, so root is just data_dir.
    workspace = WorkspaceManager(root=settings.data_dir, project_id=project.id)
    workspace.init_directories()
    if not project.workspace_path:
        project.workspace_path = str(workspace.project_dir.resolve())

    try:
        scan = scan_folder(src)
        organize = organize_images(scan, workspace)
    except ValidationError:
        # Empty / unreadable folder — let the critic surface a clearer error.
        return

    # Compute split assignments based on the project's current ratios.
    split_cfg = propose_split(
        [e.canonical for e in organize.entries],
        train=project.train_ratio,
        val=project.val_ratio,
        test=project.test_ratio,
        seed=project.split_seed,
    )
    workspace.write_splits(split_cfg)

    from echobox_app.db.models import Image as _Image

    for idx, entry in enumerate(organize.entries):
        split = split_cfg.assignments.get(entry.canonical, "train")
        session.add(
            _Image(
                project_id=project.id,
                filename=entry.canonical,
                abs_path=str(workspace.image_dir / entry.canonical),
                width=entry.width,
                height=entry.height,
                split=split,
                index_in_project=idx,
                source_path=str(entry.source),
            )
        )
    session.flush()  # so project.images shows the new rows immediately

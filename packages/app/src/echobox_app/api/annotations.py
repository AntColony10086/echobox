"""Annotation REST endpoints: list, predict-similar, PUT/DELETE/PATCH."""

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from echobox_app.api.deps import session_dep
from echobox_app.config import AppSettings
from echobox_app.db.models import Annotation, Image, Label, PredictionRun, Project
from echobox_app.domain.annotations import AnnotationDTO
from echobox_app.errors import (
    AnnotationNotFound,
    ImageNotFound,
    ProjectNotFound,
    ValidationError,
    VersionConflict,
)
from echobox_app.ml_client.client import MLBackendClient

router = APIRouter(tags=["annotations"])


def ml_client_dep(request: Request) -> MLBackendClient:
    """Dependency provider — overrideable in tests."""
    settings: AppSettings = request.app.state.settings
    return MLBackendClient(
        base_url=settings.ml_backend_url,
        timeout_s=settings.ml_backend_timeout_s,
    )


class PredictSimilarPayload(BaseModel):
    label_id: int
    exemplar_bbox: list[int] = Field(min_length=4, max_length=4)
    max_predictions: int = 200
    score_threshold: float = 0.25


@router.get("/api/images/{iid}/annotations")
def list_image_annotations(
    iid: int,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    img = session.get(Image, iid)
    if img is None:
        raise ImageNotFound(f"image {iid} not found")
    annotations = session.scalars(
        select(Annotation).where(Annotation.image_id == iid).order_by(Annotation.created_at)
    ).all()
    return {"items": [AnnotationDTO.from_db(a).to_dict() for a in annotations]}


@router.post(
    "/api/projects/{pid}/images/{iid}/predict-similar",
    status_code=status.HTTP_201_CREATED,
)
async def predict_similar(
    pid: int,
    iid: int,
    payload: PredictSimilarPayload,
    session: Annotated[Session, Depends(session_dep)],
    ml_client: Annotated[MLBackendClient, Depends(ml_client_dep)],
) -> dict[str, Any]:
    project = session.get(Project, pid)
    if project is None:
        raise ProjectNotFound(f"project {pid} not found")
    img = session.get(Image, iid)
    if img is None or img.project_id != pid:
        raise ImageNotFound(f"image {iid} not in project {pid}")
    label = session.get(Label, payload.label_id)
    if label is None or label.project_id != pid:
        raise ValidationError(f"label {payload.label_id} not in project {pid}")

    x1, y1, x2, y2 = payload.exemplar_bbox
    if x1 >= x2 or y1 >= y2:
        raise ValidationError(
            f"invalid exemplar bbox: {payload.exemplar_bbox}",
            detail={"bbox": payload.exemplar_bbox},
        )

    session.execute(
        delete(Annotation).where(
            Annotation.image_id == iid,
            Annotation.label_id == payload.label_id,
            Annotation.source == "geco2_pending",
        )
    )

    response = await ml_client.predict_similar(
        image_path=img.abs_path,
        exemplar_bbox=(x1, y1, x2, y2),
        max_predictions=payload.max_predictions,
        score_threshold=payload.score_threshold,
    )

    created: list[Annotation] = []
    for pred in response["predictions"]:
        bx1, by1, bx2, by2 = pred["bbox"]
        ann = Annotation(
            image_id=iid,
            label_id=payload.label_id,
            x1=bx1,
            y1=by1,
            x2=bx2,
            y2=by2,
            score=pred["score"],
            source="geco2_pending",
            version=1,
        )
        session.add(ann)
        created.append(ann)

    session.add(
        PredictionRun(
            project_id=pid,
            image_id=iid,
            label_id=payload.label_id,
            exemplar_x1=x1,
            exemplar_y1=y1,
            exemplar_x2=x2,
            exemplar_y2=y2,
            n_predictions=len(created),
            elapsed_ms=int(response["elapsed_ms"]),
        )
    )
    session.commit()
    for a in created:
        session.refresh(a)

    return {
        "created": [AnnotationDTO.from_db(a).to_dict() for a in created],
        "elapsed_ms": int(response["elapsed_ms"]),
    }


class PutAnnotation(BaseModel):
    x1: int | None = None
    y1: int | None = None
    x2: int | None = None
    y2: int | None = None
    label_id: int | None = None
    source: Literal["user", "geco2_accepted", "user_edited"] | None = None
    version: int


class BulkAction(BaseModel):
    action: Literal["accept_all", "reject_all"]


@router.put("/api/annotations/{aid}")
def put_annotation(
    aid: int,
    payload: PutAnnotation,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    ann = session.get(Annotation, aid)
    if ann is None:
        raise AnnotationNotFound(f"annotation {aid} not found")
    if ann.version != payload.version:
        raise VersionConflict(
            f"version mismatch: have {ann.version}, sent {payload.version}",
            detail={"current_version": ann.version},
        )

    bbox_changed = False
    if payload.x1 is not None:
        ann.x1 = payload.x1
        bbox_changed = True
    if payload.y1 is not None:
        ann.y1 = payload.y1
        bbox_changed = True
    if payload.x2 is not None:
        ann.x2 = payload.x2
        bbox_changed = True
    if payload.y2 is not None:
        ann.y2 = payload.y2
        bbox_changed = True
    if ann.x1 >= ann.x2 or ann.y1 >= ann.y2:
        raise ValidationError(
            "invalid bbox after edit",
            detail={"bbox": [ann.x1, ann.y1, ann.x2, ann.y2]},
        )
    if payload.label_id is not None:
        ann.label_id = payload.label_id
    if payload.source is not None:
        ann.source = payload.source
    elif bbox_changed and ann.source.startswith("geco2"):
        ann.source = "user_edited"

    ann.version += 1
    session.commit()
    session.refresh(ann)
    return AnnotationDTO.from_db(ann).to_dict()


@router.delete("/api/annotations/{aid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_annotation(
    aid: int,
    session: Annotated[Session, Depends(session_dep)],
) -> None:
    ann = session.get(Annotation, aid)
    if ann is None:
        raise AnnotationNotFound(f"annotation {aid} not found")
    session.delete(ann)
    session.commit()


@router.patch("/api/projects/{pid}/images/{iid}/annotations/bulk")
def bulk_action(
    pid: int,
    iid: int,
    payload: BulkAction,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    img = session.get(Image, iid)
    if img is None or img.project_id != pid:
        raise ImageNotFound(f"image {iid} not in project {pid}")

    pending = session.scalars(
        select(Annotation).where(
            Annotation.image_id == iid,
            Annotation.source == "geco2_pending",
        )
    ).all()

    if payload.action == "accept_all":
        for a in pending:
            a.source = "geco2_accepted"
            a.version += 1
        session.commit()
        return {"affected": len(pending), "action": "accept_all"}

    for a in pending:
        session.delete(a)
    session.commit()
    return {"affected": len(pending), "action": "reject_all"}

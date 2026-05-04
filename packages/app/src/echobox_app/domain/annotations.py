"""Annotation DTO for API responses."""

from dataclasses import dataclass
from typing import Any

from echobox_app.db.models import Annotation as DBAnnotation


@dataclass
class AnnotationDTO:
    id: int
    image_id: int
    label_id: int
    label_name: str
    label_color: str
    x1: int
    y1: int
    x2: int
    y2: int
    score: float | None
    source: str
    version: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "image_id": self.image_id,
            "label": {"id": self.label_id, "name": self.label_name, "color": self.label_color},
            "bbox": [self.x1, self.y1, self.x2, self.y2],
            "score": self.score,
            "source": self.source,
            "version": self.version,
        }

    @classmethod
    def from_db(cls, ann: DBAnnotation) -> "AnnotationDTO":
        return cls(
            id=ann.id,
            image_id=ann.image_id,
            label_id=ann.label_id,
            label_name=ann.label.name,
            label_color=ann.label.color,
            x1=ann.x1,
            y1=ann.y1,
            x2=ann.x2,
            y2=ann.y2,
            score=ann.score,
            source=ann.source,
            version=ann.version,
        )

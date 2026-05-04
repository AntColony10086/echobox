"""Pydantic request/response schemas for /predict_similar."""

from typing import Annotated

from pydantic import BaseModel, Field, field_serializer, field_validator


class PredictRequest(BaseModel):
    image_path: str
    exemplar_bbox: Annotated[list[int], Field(min_length=4, max_length=4)]
    max_predictions: int = Field(default=200, ge=1, le=10_000)
    score_threshold: float = Field(default=0.25, ge=0.0, le=1.0)

    @field_validator("exemplar_bbox")
    @classmethod
    def _validate_bbox(cls, v: list[int]) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = v
        if x1 >= x2 or y1 >= y2:
            raise ValueError(f"invalid bbox: x2 must be > x1 and y2 > y1; got {v}")
        if any(c < 0 for c in (x1, y1, x2, y2)):
            raise ValueError(f"bbox coords must be >= 0; got {v}")
        return (x1, y1, x2, y2)


class Prediction(BaseModel):
    bbox: tuple[int, int, int, int]
    score: float = Field(ge=0.0, le=1.0)

    @field_serializer("bbox")
    def serialize_bbox(self, value: tuple[int, int, int, int]) -> list[int]:
        return list(value)


class PredictResponse(BaseModel):
    predictions: list[Prediction]
    exemplar_count: int
    image_size: tuple[int, int]
    elapsed_ms: int


class PredictError(BaseModel):
    error: str
    detail: str = ""
    elapsed_ms: int = 0

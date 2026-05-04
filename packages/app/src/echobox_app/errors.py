"""Typed exceptions for the app domain.

Boundary handlers (FastAPI exception handlers, LangGraph tool wrappers)
convert these to user-facing responses.
"""

from typing import Any


class ArisError(Exception):
    code: str = "internal_error"
    http_status: int = 500

    def __init__(self, message: str = "", *, detail: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "detail": self.detail,
            }
        }


class ValidationError(ArisError):
    code = "validation_failed"
    http_status = 400


class ProjectNotFound(ArisError):
    code = "project_not_found"
    http_status = 404


class ImageNotFound(ArisError):
    code = "image_not_found"
    http_status = 404


class AnnotationNotFound(ArisError):
    code = "annotation_not_found"
    http_status = 404


class LabelConflict(ArisError):
    code = "label_conflict"
    http_status = 409


class VersionConflict(ArisError):
    code = "version_conflict"
    http_status = 409


class MLBackendUnavailable(ArisError):
    code = "ml_backend_unavailable"
    http_status = 503


class LLMUnavailable(ArisError):
    code = "llm_unavailable"
    http_status = 503

"""Project finalization: format selection, critic validation."""

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from echobox_app.errors import ValidationError

ExportFormat = Literal["coco", "yolo", "voc", "ls_json"]
_VALID_FORMATS = {"coco", "yolo", "voc", "ls_json"}


class _StateLike(Protocol):
    inventory: Any
    canonical_images: Any
    splits: Any
    labels: Any
    export_format: Any


@dataclass
class FinalizeResult:
    success: bool
    errors: list[str] = field(default_factory=list)


def set_export_format(fmt: str) -> ExportFormat:
    if fmt not in _VALID_FORMATS:
        raise ValidationError(
            f"unknown export format: {fmt!r}",
            detail={"format": fmt, "valid": sorted(_VALID_FORMATS)},
        )
    return fmt  # type: ignore[return-value]


def critic_check(state: _StateLike) -> list[str]:
    """Validate state is finalize-ready. Returns list of human-readable errors."""
    errors: list[str] = []
    inv = state.inventory
    if inv is None or getattr(inv, "valid_count", 0) <= 0:
        errors.append("inventory is empty (run scan_folder)")

    if not state.canonical_images:
        errors.append("no canonical images (run organize_images)")

    splits = state.splits
    if splits is None:
        errors.append("split config not set (run propose_split)")
    elif not splits.is_valid():
        errors.append(f"split ratios invalid: {splits.train}+{splits.val}+{splits.test} != 1.0")
    elif state.canonical_images and len(splits.assignments) != len(state.canonical_images):
        errors.append(
            f"split assignments missing for "
            f"{len(state.canonical_images) - len(splits.assignments)} images"
        )

    if not state.labels:
        errors.append("label set empty (run set_labels)")

    if not state.export_format:
        errors.append("export format not chosen (run set_export_format)")

    return errors


def finalize_setup(state: _StateLike) -> FinalizeResult:
    """Run critic; return success/errors. Caller updates DB on success."""
    errors = critic_check(state)
    return FinalizeResult(success=len(errors) == 0, errors=errors)

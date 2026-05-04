"""Label-set tools: validate, set, propose."""

import re
from pathlib import Path

from echobox_app.errors import ValidationError

_VALID = re.compile(r"^[a-zA-Z0-9_\-]+$")


def validate_label_name(name: str) -> bool:
    return bool(name) and bool(_VALID.fullmatch(name))


def set_labels(labels: list[str]) -> list[str]:
    if not labels:
        raise ValidationError("label set cannot be empty")
    seen: dict[str, None] = {}
    for label in labels:
        if not validate_label_name(label):
            raise ValidationError(
                f"invalid label name: {label!r}",
                detail={"name": label, "rule": "^[a-zA-Z0-9_-]+$"},
            )
        if label not in seen:
            seen[label] = None
    return list(seen.keys())


def propose_labels(folder: Path) -> list[str]:
    """Heuristic: if `folder` contains class-named subdirs (each with images),
    return them as suggested labels; else empty."""
    if not folder.exists() or not folder.is_dir():
        return []

    suggestions: list[str] = []
    for child in sorted(folder.iterdir()):
        if not child.is_dir():
            continue
        if not validate_label_name(child.name):
            continue
        if any(p.is_file() for p in child.iterdir()):
            suggestions.append(child.name)
    return suggestions

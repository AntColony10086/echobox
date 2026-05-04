"""Result of copying source images to canonical workspace layout."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ImageEntry:
    canonical: str
    source: Path
    sha256: str
    bytes: int
    width: int
    height: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical": self.canonical,
            "source": str(self.source),
            "sha256": self.sha256,
            "bytes": self.bytes,
            "width": self.width,
            "height": self.height,
        }


@dataclass
class OrganizeResult:
    copied_count: int
    entries: list[ImageEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "copied_count": self.copied_count,
            "entries": [e.to_dict() for e in self.entries],
        }

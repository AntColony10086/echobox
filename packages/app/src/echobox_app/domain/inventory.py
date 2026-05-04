"""Image inventory after scanning a folder."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ImageInventory:
    total_files: int
    valid_count: int
    invalid_count: int
    formats: dict[str, int]
    sample_paths: list[Path]
    invalid_paths: list[Path] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_files": self.total_files,
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count,
            "formats": self.formats,
            "sample_paths": [str(p) for p in self.sample_paths],
            "invalid_paths": [str(p) for p in self.invalid_paths],
        }


@dataclass
class ScanResult:
    folder: Path
    inventory: ImageInventory

    def to_dict(self) -> dict[str, Any]:
        return {"folder": str(self.folder), "inventory": self.inventory.to_dict()}

"""Exporter ABC + shared types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from echobox_app.db.models import Annotation, Image

SplitName = Literal["train", "val", "test"]


@dataclass
class ExportContext:
    project_id: int
    project_name: str
    workspace_path: Path
    export_dir: Path
    labels: list[tuple[str, str]]
    images: list[Image]
    annotations_by_image: dict[int, list[Annotation]]
    include_pending: bool
    splits: tuple[SplitName, ...]

    @property
    def symlink_image_dir(self) -> Path:
        return self.export_dir / "images"


@dataclass
class ExportStats:
    by_split: dict[str, dict[str, int]] = field(
        default_factory=lambda: {
            "train": {"images": 0, "annotations": 0},
            "val": {"images": 0, "annotations": 0},
            "test": {"images": 0, "annotations": 0},
        }
    )

    def add_image(self, split: str, n_annotations: int) -> None:
        self.by_split[split]["images"] += 1
        self.by_split[split]["annotations"] += n_annotations

    @property
    def total_images(self) -> int:
        return sum(s["images"] for s in self.by_split.values())

    @property
    def total_annotations(self) -> int:
        return sum(s["annotations"] for s in self.by_split.values())


class Exporter(ABC):
    name: str

    @abstractmethod
    def export(self, ctx: ExportContext) -> ExportStats: ...


def make_image_symlink(image: Image, target_dir: Path) -> Path:
    """Create a symlink (fallback to copy on Windows or symlink failure)."""
    import shutil

    target_dir.mkdir(parents=True, exist_ok=True)
    dst = target_dir / image.filename
    if dst.exists():
        return dst
    src = Path(image.abs_path)
    try:
        dst.symlink_to(src)
    except (OSError, NotImplementedError):
        shutil.copy2(src, dst)
    return dst


def filter_annotations(
    annotations: list[Annotation],
    include_pending: bool,
) -> list[Annotation]:
    if include_pending:
        return list(annotations)
    return [a for a in annotations if a.source != "geco2_pending"]

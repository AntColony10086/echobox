"""Agent state — the single source of truth across LangGraph nodes."""

from dataclasses import dataclass, field
from typing import Any, Literal

from echobox_app.domain.inventory import ImageInventory
from echobox_app.domain.messages import Message
from echobox_app.domain.organize import ImageEntry
from echobox_app.domain.splits import SplitConfig

ProjectStatus = Literal["draft", "ready", "annotating"]
ExportFormat = Literal["coco", "yolo", "voc", "ls_json"]


@dataclass
class AgentState:
    project_id: int
    messages: list[Message] = field(default_factory=list)
    folder_path: str | None = None
    inventory: ImageInventory | None = None
    canonical_images: list[ImageEntry] = field(default_factory=list)
    splits: SplitConfig | None = None
    labels: list[str] = field(default_factory=list)
    export_format: ExportFormat | None = None
    status: ProjectStatus = "draft"
    last_critic_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "messages": [m.to_dict() for m in self.messages],
            "folder_path": self.folder_path,
            "inventory": self.inventory.to_dict() if self.inventory else None,
            "canonical_images": [e.to_dict() for e in self.canonical_images],
            "splits": self.splits.to_dict() if self.splits else None,
            "labels": list(self.labels),
            "export_format": self.export_format,
            "status": self.status,
            "last_critic_errors": list(self.last_critic_errors),
        }

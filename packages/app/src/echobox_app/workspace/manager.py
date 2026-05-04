"""On-disk workspace layout manager (per spec section 6.1)."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from echobox_app.domain.organize import OrganizeResult
from echobox_app.domain.splits import SplitConfig


class WorkspaceManager:
    def __init__(self, root: Path, project_id: int) -> None:
        self.root = root
        self.project_id = project_id
        self.project_dir = root / "projects" / str(project_id)
        self.data_dir = self.project_dir / "data"
        self.image_dir = self.data_dir / "image"
        self.exports_dir = self.project_dir / "exports"
        self.chat_dir = self.project_dir / "chat"

    def init_directories(self) -> None:
        for d in (self.image_dir, self.exports_dir, self.chat_dir):
            d.mkdir(parents=True, exist_ok=True)

    def write_mapping(self, result: OrganizeResult) -> Path:
        path = self.data_dir / "mapping.json"
        payload = {
            "version": 1,
            "created_at": datetime.now(UTC).isoformat(),
            "entries": [e.to_dict() for e in result.entries],
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        return path

    def write_splits(self, config: SplitConfig) -> Path:
        path = self.data_dir / "splits.json"
        payload = {
            "version": 1,
            "seed": config.seed,
            "ratios": {"train": config.train, "val": config.val, "test": config.test},
            "assignments": dict(config.assignments),
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        return path

    def write_project_meta(self, meta: dict[str, Any]) -> Path:
        path = self.project_dir / "project.json"
        payload = dict(meta)
        payload.setdefault("updated_at", datetime.now(UTC).isoformat())
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        return path

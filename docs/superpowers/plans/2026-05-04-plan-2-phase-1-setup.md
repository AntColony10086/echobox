# Plan 2 — Phase 1 Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** End-to-end conversational dataset setup. After this plan, a user can: open `/setup` in browser → give a folder path → chat with the LangGraph agent → see structured cards update (folder / inventory / split / labels / format) → click "开始标注" → project transitions to `status="ready"`.

**Architecture:** LangGraph Planner+Critic loop with 7 deterministic tools that mutate `AgentState`. OpenAI-compatible LLM via DashScope. FastAPI REST endpoints (REST cards + SSE chat). React frontend with 5 cards + chat sidebar.

**Tech Stack (added on top of Plan 1):**
- LangGraph 0.2+, LangChain Core 0.3+, langchain-openai
- Pillow (image validation)
- httpx-sse (server-sent events)
- React Router 6 (frontend routing)
- TanStack Query (frontend data fetching)
- Zustand (frontend state, lightweight)

**Spec reference:** sections 4 (Phase 1 setup), 6 (data model), 8 (cross-cutting) of `docs/superpowers/specs/2026-05-04-multimodal-annotation-agent-design.md`

**Prerequisite:** Plan 1 complete (4-process scaffold + DB schema migrated).

---

## File Structure (created in this plan)

```
packages/app/src/echobox_app/
├── domain/
│   ├── __init__.py
│   ├── inventory.py             # ScanResult, ImageInventory
│   ├── organize.py              # OrganizeResult, ImageEntry
│   ├── splits.py                # SplitConfig, SplitResult
│   └── messages.py              # Message dataclass for agent
├── workspace/
│   ├── __init__.py
│   └── manager.py               # WorkspaceManager (mkdir, JSON writers)
├── tools/
│   ├── __init__.py
│   ├── filesystem.py            # scan_folder, organize_images
│   ├── splits.py                # propose_split
│   ├── labels.py                # set_labels, propose_labels
│   └── project.py               # set_export_format, finalize_setup, critic
├── llm/
│   ├── __init__.py
│   └── factory.py               # OpenAI-compatible LLM factory
├── agent/
│   ├── __init__.py
│   ├── state.py                 # AgentState
│   ├── nodes.py                 # planner, tool_executor, critic
│   └── graph.py                 # build_graph()
├── api/
│   ├── __init__.py
│   ├── projects.py              # POST/GET/PATCH/finalize
│   ├── chat.py                  # SSE
│   └── deps.py                  # Depends() for session/settings
└── main.py                      # extended with router includes

frontend/src/
├── api/
│   ├── client.ts                # axios instance
│   ├── projects.ts              # project endpoints
│   └── chat.ts                  # SSE consumer
├── types/
│   └── project.ts
├── hooks/
│   ├── useProject.ts
│   └── useChat.ts
├── components/
│   ├── cards/
│   │   ├── FolderCard.tsx
│   │   ├── ImageInventoryCard.tsx
│   │   ├── SplitCard.tsx
│   │   ├── LabelsCard.tsx
│   │   └── FormatCard.tsx
│   └── ChatPanel.tsx
└── pages/
    └── SetupPage.tsx
```

---

## Task 1: Domain dataclasses (inventory, organize, splits, messages)

**Files:**
- Create: `packages/app/src/echobox_app/domain/__init__.py`
- Create: `packages/app/src/echobox_app/domain/inventory.py`
- Create: `packages/app/src/echobox_app/domain/organize.py`
- Create: `packages/app/src/echobox_app/domain/splits.py`
- Create: `packages/app/src/echobox_app/domain/messages.py`
- Create: `packages/app/tests/test_domain.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_domain.py
from pathlib import Path

import pytest

from echobox_app.domain.inventory import ImageInventory, ScanResult
from echobox_app.domain.messages import Message
from echobox_app.domain.organize import ImageEntry, OrganizeResult
from echobox_app.domain.splits import SplitConfig


def test_image_inventory_counts() -> None:
    inv = ImageInventory(
        total_files=10,
        valid_count=8,
        invalid_count=2,
        formats={".jpg": 6, ".png": 2},
        sample_paths=[Path("/a.jpg"), Path("/b.jpg")],
        invalid_paths=[Path("/x.txt"), Path("/y.gif")],
    )
    assert inv.total_files == 10
    assert inv.valid_count == 8
    assert inv.invalid_count == 2


def test_scan_result_serialization() -> None:
    sr = ScanResult(folder=Path("/data"), inventory=ImageInventory(
        total_files=2, valid_count=2, invalid_count=0,
        formats={".jpg": 2}, sample_paths=[], invalid_paths=[]
    ))
    d = sr.to_dict()
    assert d["folder"] == "/data"
    assert d["inventory"]["valid_count"] == 2


def test_split_config_validates_ratios() -> None:
    sc = SplitConfig(train=0.7, val=0.15, test=0.15, seed=42)
    assert sc.is_valid()

    bad = SplitConfig(train=0.5, val=0.3, test=0.3, seed=42)
    assert not bad.is_valid()


def test_split_config_assignment() -> None:
    sc = SplitConfig(train=0.7, val=0.15, test=0.15, seed=42)
    sc.assignments = {"00001.jpg": "train", "00002.jpg": "val"}
    assert sc.assignments["00001.jpg"] == "train"


def test_organize_result_with_entries() -> None:
    res = OrganizeResult(
        copied_count=2,
        entries=[
            ImageEntry(canonical="00001.jpg", source=Path("/orig/a.jpg"),
                       sha256="abc", bytes=100, width=10, height=10),
            ImageEntry(canonical="00002.jpg", source=Path("/orig/b.jpg"),
                       sha256="def", bytes=200, width=20, height=20),
        ],
    )
    assert res.copied_count == 2
    assert res.entries[0].canonical == "00001.jpg"


def test_message_roles() -> None:
    m = Message(role="user", content="hello")
    assert m.role == "user"

    with pytest.raises(ValueError):
        Message(role="invalid", content="x")  # type: ignore[arg-type]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_domain.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement domain/__init__.py**

```python
# packages/app/src/echobox_app/domain/__init__.py
"""Business domain dataclasses (no DB / no IO)."""
```

- [ ] **Step 4: Implement domain/inventory.py**

```python
# packages/app/src/echobox_app/domain/inventory.py
"""Image inventory after scanning a folder."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ImageInventory:
    total_files: int
    valid_count: int
    invalid_count: int
    formats: dict[str, int]                   # {".jpg": 100, ".png": 20}
    sample_paths: list[Path]                  # first ~5
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
```

- [ ] **Step 5: Implement domain/organize.py**

```python
# packages/app/src/echobox_app/domain/organize.py
"""Result of copying source images to canonical workspace layout."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ImageEntry:
    canonical: str       # "00001.jpg"
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
```

- [ ] **Step 6: Implement domain/splits.py**

```python
# packages/app/src/echobox_app/domain/splits.py
"""Train/val/test split configuration and assignment."""
from dataclasses import dataclass, field
from typing import Any, Literal

SplitName = Literal["train", "val", "test"]


@dataclass
class SplitConfig:
    train: float
    val: float
    test: float
    seed: int = 42
    assignments: dict[str, SplitName] = field(default_factory=dict)

    def is_valid(self, tol: float = 1e-6) -> bool:
        total = self.train + self.val + self.test
        return abs(total - 1.0) < tol and all(r >= 0 for r in (self.train, self.val, self.test))

    def to_dict(self) -> dict[str, Any]:
        return {
            "train": self.train,
            "val": self.val,
            "test": self.test,
            "seed": self.seed,
            "assignments": dict(self.assignments),
        }


@dataclass
class SplitResult:
    config: SplitConfig

    def to_dict(self) -> dict[str, Any]:
        return self.config.to_dict()
```

- [ ] **Step 7: Implement domain/messages.py**

```python
# packages/app/src/echobox_app/domain/messages.py
"""Agent chat message representation."""
from dataclasses import dataclass, field
from typing import Any, Literal

MessageRole = Literal["user", "assistant", "tool", "system"]
_VALID_ROLES = {"user", "assistant", "tool", "system"}


@dataclass
class Message:
    role: MessageRole
    content: str
    tool_call_id: str | None = None
    tool_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.role not in _VALID_ROLES:
            raise ValueError(f"invalid role: {self.role}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "tool_call_id": self.tool_call_id,
            "tool_name": self.tool_name,
            "metadata": dict(self.metadata),
        }
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_domain.py -v`
Expected: PASS (6 tests).

- [ ] **Step 9: Commit**

```bash
git add packages/app/src/echobox_app/domain/ packages/app/tests/test_domain.py
git commit -m "feat(app): add domain dataclasses for inventory, organize, splits, messages"
```

---

## Task 2: WorkspaceManager (paths, JSON writers)

**Files:**
- Create: `packages/app/src/echobox_app/workspace/__init__.py`
- Create: `packages/app/src/echobox_app/workspace/manager.py`
- Create: `packages/app/tests/test_workspace.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_workspace.py
import json
from pathlib import Path

from echobox_app.domain.inventory import ImageInventory
from echobox_app.domain.organize import ImageEntry, OrganizeResult
from echobox_app.domain.splits import SplitConfig
from echobox_app.workspace.manager import WorkspaceManager


def test_workspace_paths(tmp_path: Path) -> None:
    wm = WorkspaceManager(root=tmp_path, project_id=7)

    assert wm.project_dir == tmp_path / "projects" / "7"
    assert wm.image_dir == tmp_path / "projects" / "7" / "data" / "image"
    assert wm.exports_dir == tmp_path / "projects" / "7" / "exports"
    assert wm.chat_dir == tmp_path / "projects" / "7" / "chat"


def test_init_creates_directories(tmp_path: Path) -> None:
    wm = WorkspaceManager(root=tmp_path, project_id=7)
    wm.init_directories()

    assert wm.image_dir.is_dir()
    assert wm.exports_dir.is_dir()
    assert wm.chat_dir.is_dir()


def test_write_mapping_json(tmp_path: Path) -> None:
    wm = WorkspaceManager(root=tmp_path, project_id=7)
    wm.init_directories()
    res = OrganizeResult(
        copied_count=1,
        entries=[ImageEntry(canonical="00001.jpg", source=Path("/orig/a.jpg"),
                            sha256="abc", bytes=100, width=10, height=10)],
    )
    wm.write_mapping(res)

    mapping = json.loads((wm.data_dir / "mapping.json").read_text())
    assert mapping["version"] == 1
    assert len(mapping["entries"]) == 1
    assert mapping["entries"][0]["canonical"] == "00001.jpg"


def test_write_splits_json(tmp_path: Path) -> None:
    wm = WorkspaceManager(root=tmp_path, project_id=7)
    wm.init_directories()
    sc = SplitConfig(train=0.7, val=0.15, test=0.15, seed=42)
    sc.assignments = {"00001.jpg": "train"}
    wm.write_splits(sc)

    splits = json.loads((wm.data_dir / "splits.json").read_text())
    assert splits["seed"] == 42
    assert splits["assignments"]["00001.jpg"] == "train"


def test_write_project_json(tmp_path: Path) -> None:
    wm = WorkspaceManager(root=tmp_path, project_id=7)
    wm.init_directories()
    wm.write_project_meta({
        "id": 7, "name": "test", "status": "draft",
        "labels": [{"name": "crack", "color": "#000"}],
    })

    meta = json.loads((wm.project_dir / "project.json").read_text())
    assert meta["id"] == 7
    assert meta["name"] == "test"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_workspace.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement workspace/__init__.py**

```python
# packages/app/src/echobox_app/workspace/__init__.py
"""Workspace filesystem layout management."""
```

- [ ] **Step 4: Implement workspace/manager.py**

```python
# packages/app/src/echobox_app/workspace/manager.py
"""On-disk workspace layout manager (per spec section 6.1)."""
import json
from datetime import datetime, timezone
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
            "created_at": datetime.now(timezone.utc).isoformat(),
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
        payload.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        return path
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_workspace.py -v`
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add packages/app/src/echobox_app/workspace/ packages/app/tests/test_workspace.py
git commit -m "feat(app): add WorkspaceManager for project on-disk layout"
```

---

## Task 3: Tool — scan_folder

**Files:**
- Create: `packages/app/src/echobox_app/tools/__init__.py`
- Create: `packages/app/src/echobox_app/tools/filesystem.py`
- Create: `packages/app/tests/test_tool_scan.py`
- Create: `packages/app/tests/fixtures/__init__.py`

Add `pillow` to `packages/app/pyproject.toml` dependencies.

- [ ] **Step 1: Add Pillow to app dependencies**

Edit `packages/app/pyproject.toml` and add `"pillow>=10.3"` to the `dependencies` list. Then run `uv sync --dev`.

- [ ] **Step 2: Write the failing test**

```python
# packages/app/tests/test_tool_scan.py
from pathlib import Path

import pytest
from PIL import Image

from echobox_app.tools.filesystem import scan_folder


def _make_image(path: Path, fmt: str = "JPEG", size: tuple[int, int] = (10, 10)) -> None:
    Image.new("RGB", size, color=(255, 0, 0)).save(path, fmt)


def test_scan_empty_folder_raises(tmp_path: Path) -> None:
    from echobox_app.errors import ValidationError

    with pytest.raises(ValidationError):
        scan_folder(tmp_path)


def test_scan_finds_images(tmp_path: Path) -> None:
    _make_image(tmp_path / "a.jpg")
    _make_image(tmp_path / "b.png", fmt="PNG")
    (tmp_path / "readme.txt").write_text("ignore me")

    res = scan_folder(tmp_path)

    assert res.folder == tmp_path
    assert res.inventory.valid_count == 2
    assert res.inventory.invalid_count == 0      # .txt is skipped, not "invalid image"
    assert res.inventory.total_files == 2
    assert res.inventory.formats[".jpg"] == 1
    assert res.inventory.formats[".png"] == 1


def test_scan_recursive(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    _make_image(tmp_path / "a.jpg")
    _make_image(sub / "b.jpg")

    res = scan_folder(tmp_path)

    assert res.inventory.valid_count == 2


def test_scan_detects_corrupted_image(tmp_path: Path) -> None:
    (tmp_path / "broken.jpg").write_text("not a real image")
    _make_image(tmp_path / "good.jpg")

    res = scan_folder(tmp_path)

    assert res.inventory.valid_count == 1
    assert res.inventory.invalid_count == 1
    assert res.inventory.invalid_paths[0].name == "broken.jpg"


def test_scan_nonexistent_folder_raises(tmp_path: Path) -> None:
    from echobox_app.errors import ValidationError

    with pytest.raises(ValidationError):
        scan_folder(tmp_path / "nope")
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_tool_scan.py -v`
Expected: FAIL.

- [ ] **Step 4: Implement tools/__init__.py**

```python
# packages/app/src/echobox_app/tools/__init__.py
"""Agent tools: deterministic, pure-ish functions invoked by LangGraph executor."""
```

- [ ] **Step 5: Implement tools/filesystem.py (scan_folder only for now)**

```python
# packages/app/src/echobox_app/tools/filesystem.py
"""Filesystem tools: scan_folder, organize_images."""
from collections import Counter
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from echobox_app.domain.inventory import ImageInventory, ScanResult
from echobox_app.errors import ValidationError

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
MAX_SAMPLE = 5


def scan_folder(folder: Path) -> ScanResult:
    """Recursively scan `folder` for image files, validate each via PIL."""
    if not folder.exists():
        raise ValidationError(
            f"folder not found: {folder}",
            detail={"folder": str(folder)},
        )
    if not folder.is_dir():
        raise ValidationError(
            f"path is not a directory: {folder}",
            detail={"folder": str(folder)},
        )

    valid: list[Path] = []
    invalid: list[Path] = []
    formats: Counter[str] = Counter()

    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTS:
            continue
        try:
            with Image.open(path) as img:
                img.verify()
            valid.append(path)
            formats[ext] += 1
        except (UnidentifiedImageError, OSError, SyntaxError):
            invalid.append(path)

    if not valid:
        raise ValidationError(
            f"no valid images found in {folder}",
            detail={"folder": str(folder), "invalid_count": len(invalid)},
        )

    inventory = ImageInventory(
        total_files=len(valid),
        valid_count=len(valid),
        invalid_count=len(invalid),
        formats=dict(formats),
        sample_paths=valid[:MAX_SAMPLE],
        invalid_paths=invalid,
    )
    return ScanResult(folder=folder, inventory=inventory)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_tool_scan.py -v`
Expected: PASS (5 tests).

- [ ] **Step 7: Commit**

```bash
git add packages/app/pyproject.toml packages/app/src/echobox_app/tools/ \
        packages/app/tests/test_tool_scan.py packages/app/tests/fixtures/ uv.lock
git commit -m "feat(app): add scan_folder tool with PIL validation + recursive scan"
```

---

## Task 4: Tool — organize_images

**Files:**
- Modify: `packages/app/src/echobox_app/tools/filesystem.py` (add `organize_images`)
- Create: `packages/app/tests/test_tool_organize.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_tool_organize.py
from pathlib import Path

from PIL import Image

from echobox_app.domain.inventory import ImageInventory, ScanResult
from echobox_app.tools.filesystem import organize_images
from echobox_app.workspace.manager import WorkspaceManager


def _make_image(path: Path, size: tuple[int, int] = (10, 20)) -> None:
    Image.new("RGB", size, color=(0, 255, 0)).save(path, "JPEG")


def test_organize_copies_files_with_canonical_names(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    _make_image(src / "a.jpg")
    _make_image(src / "b.jpg")

    inv = ImageInventory(
        total_files=2, valid_count=2, invalid_count=0,
        formats={".jpg": 2},
        sample_paths=[src / "a.jpg", src / "b.jpg"],
    )
    sr = ScanResult(folder=src, inventory=inv)
    wm = WorkspaceManager(root=tmp_path / "data", project_id=1)
    wm.init_directories()

    res = organize_images(sr, wm)

    assert res.copied_count == 2
    assert (wm.image_dir / "00001.jpg").exists()
    assert (wm.image_dir / "00002.jpg").exists()
    # source not deleted
    assert (src / "a.jpg").exists()
    assert res.entries[0].width == 10
    assert res.entries[0].height == 20
    assert res.entries[0].canonical == "00001.jpg"
    assert len(res.entries[0].sha256) == 64


def test_organize_preserves_extension(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    Image.new("RGB", (5, 5)).save(src / "x.png", "PNG")

    inv = ImageInventory(
        total_files=1, valid_count=1, invalid_count=0,
        formats={".png": 1}, sample_paths=[src / "x.png"],
    )
    sr = ScanResult(folder=src, inventory=inv)
    wm = WorkspaceManager(root=tmp_path / "data", project_id=2)
    wm.init_directories()

    res = organize_images(sr, wm)

    assert (wm.image_dir / "00001.png").exists()


def test_organize_writes_mapping_json(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    _make_image(src / "a.jpg")

    inv = ImageInventory(
        total_files=1, valid_count=1, invalid_count=0,
        formats={".jpg": 1}, sample_paths=[src / "a.jpg"],
    )
    sr = ScanResult(folder=src, inventory=inv)
    wm = WorkspaceManager(root=tmp_path / "data", project_id=3)
    wm.init_directories()

    organize_images(sr, wm)

    assert (wm.data_dir / "mapping.json").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_tool_organize.py -v`
Expected: FAIL.

- [ ] **Step 3: Add organize_images to tools/filesystem.py**

Append to existing `packages/app/src/echobox_app/tools/filesystem.py`:

```python
import hashlib
import shutil

from echobox_app.domain.organize import ImageEntry, OrganizeResult
from echobox_app.workspace.manager import WorkspaceManager


def _sha256_of_file(path: Path, chunk: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            data = f.read(chunk)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def organize_images(scan: ScanResult, workspace: WorkspaceManager) -> OrganizeResult:
    """Copy valid images from scan into workspace.image_dir as 00001.<ext> ..."""
    workspace.init_directories()
    entries: list[ImageEntry] = []

    valid_paths: list[Path] = []
    for p in sorted(scan.folder.rglob("*")):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            try:
                with Image.open(p) as img:
                    img.verify()
                valid_paths.append(p)
            except (UnidentifiedImageError, OSError, SyntaxError):
                continue

    for idx, src_path in enumerate(valid_paths, start=1):
        ext = src_path.suffix.lower()
        canonical = f"{idx:05d}{ext}"
        dst = workspace.image_dir / canonical
        shutil.copy2(src_path, dst)

        with Image.open(dst) as img:
            width, height = img.size
        sha = _sha256_of_file(dst)
        entries.append(ImageEntry(
            canonical=canonical,
            source=src_path,
            sha256=sha,
            bytes=dst.stat().st_size,
            width=width,
            height=height,
        ))

    result = OrganizeResult(copied_count=len(entries), entries=entries)
    workspace.write_mapping(result)
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_tool_organize.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/tools/filesystem.py packages/app/tests/test_tool_organize.py
git commit -m "feat(app): add organize_images tool with sha256 + mapping.json"
```

---

## Task 5: Tool — propose_split (deterministic)

**Files:**
- Create: `packages/app/src/echobox_app/tools/splits.py`
- Create: `packages/app/tests/test_tool_splits.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_tool_splits.py
import pytest

from echobox_app.tools.splits import propose_split


def test_split_assigns_all_images() -> None:
    images = [f"{i:05d}.jpg" for i in range(1, 11)]

    sc = propose_split(images, train=0.7, val=0.15, test=0.15, seed=42)

    assert len(sc.assignments) == 10
    assert all(s in {"train", "val", "test"} for s in sc.assignments.values())


def test_split_deterministic_seed() -> None:
    images = [f"{i:05d}.jpg" for i in range(1, 21)]

    a = propose_split(images, train=0.6, val=0.2, test=0.2, seed=42)
    b = propose_split(images, train=0.6, val=0.2, test=0.2, seed=42)

    assert a.assignments == b.assignments


def test_split_different_seed_different_result() -> None:
    images = [f"{i:05d}.jpg" for i in range(1, 21)]

    a = propose_split(images, train=0.5, val=0.25, test=0.25, seed=1)
    b = propose_split(images, train=0.5, val=0.25, test=0.25, seed=2)

    assert a.assignments != b.assignments


def test_split_proportions_approx() -> None:
    images = [f"{i:05d}.jpg" for i in range(1, 1001)]

    sc = propose_split(images, train=0.7, val=0.15, test=0.15, seed=42)
    counts = {"train": 0, "val": 0, "test": 0}
    for s in sc.assignments.values():
        counts[s] += 1

    assert abs(counts["train"] - 700) <= 10
    assert abs(counts["val"] - 150) <= 10
    assert abs(counts["test"] - 150) <= 10


def test_split_invalid_ratios_raise() -> None:
    from echobox_app.errors import ValidationError

    with pytest.raises(ValidationError):
        propose_split(["a.jpg"], train=0.5, val=0.3, test=0.3, seed=42)


def test_split_empty_images_raises() -> None:
    from echobox_app.errors import ValidationError

    with pytest.raises(ValidationError):
        propose_split([], train=0.7, val=0.15, test=0.15, seed=42)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_tool_splits.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement tools/splits.py**

```python
# packages/app/src/echobox_app/tools/splits.py
"""Deterministic train/val/test split."""
import random
from typing import cast

from echobox_app.domain.splits import SplitConfig, SplitName
from echobox_app.errors import ValidationError


def propose_split(
    image_filenames: list[str],
    train: float = 0.7,
    val: float = 0.15,
    test: float = 0.15,
    seed: int = 42,
) -> SplitConfig:
    if not image_filenames:
        raise ValidationError("cannot split empty image list")

    cfg = SplitConfig(train=train, val=val, test=test, seed=seed)
    if not cfg.is_valid():
        raise ValidationError(
            f"split ratios must sum to 1.0 (got {train + val + test})",
            detail={"train": train, "val": val, "test": test},
        )

    n = len(image_filenames)
    n_train = int(n * train)
    n_val = int(n * val)
    # rest -> test (avoids floor rounding losing images)

    shuffled = list(image_filenames)
    rng = random.Random(seed)
    rng.shuffle(shuffled)

    assignments: dict[str, SplitName] = {}
    for i, fname in enumerate(shuffled):
        if i < n_train:
            assignments[fname] = cast(SplitName, "train")
        elif i < n_train + n_val:
            assignments[fname] = cast(SplitName, "val")
        else:
            assignments[fname] = cast(SplitName, "test")

    cfg.assignments = assignments
    return cfg
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_tool_splits.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/tools/splits.py packages/app/tests/test_tool_splits.py
git commit -m "feat(app): add propose_split tool with deterministic seeded shuffle"
```

---

## Task 6: Tool — labels (set_labels, propose_labels)

**Files:**
- Create: `packages/app/src/echobox_app/tools/labels.py`
- Create: `packages/app/tests/test_tool_labels.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_tool_labels.py
from pathlib import Path

import pytest

from echobox_app.tools.labels import propose_labels, set_labels, validate_label_name


def test_set_labels_dedups_and_validates() -> None:
    out = set_labels(["crack", "rust", "crack", "no_crack"])

    assert out == ["crack", "rust", "no_crack"]


def test_set_labels_rejects_invalid_name() -> None:
    from echobox_app.errors import ValidationError

    with pytest.raises(ValidationError):
        set_labels(["crack", "bad name with space"])


def test_set_labels_rejects_empty() -> None:
    from echobox_app.errors import ValidationError

    with pytest.raises(ValidationError):
        set_labels([])


def test_validate_label_name() -> None:
    assert validate_label_name("crack")
    assert validate_label_name("no_crack")
    assert validate_label_name("class-1")
    assert not validate_label_name("")
    assert not validate_label_name("with space")
    assert not validate_label_name("emoji-🚀")


def test_propose_labels_from_class_subdirs(tmp_path: Path) -> None:
    (tmp_path / "positive").mkdir()
    (tmp_path / "positive" / "img.jpg").write_text("x")
    (tmp_path / "negative").mkdir()
    (tmp_path / "negative" / "img.jpg").write_text("x")

    suggestions = propose_labels(tmp_path)

    assert sorted(suggestions) == ["negative", "positive"]


def test_propose_labels_returns_empty_when_no_subdirs(tmp_path: Path) -> None:
    (tmp_path / "a.jpg").write_text("x")

    suggestions = propose_labels(tmp_path)

    assert suggestions == []


def test_propose_labels_skips_invalid_dir_names(tmp_path: Path) -> None:
    (tmp_path / "good_class").mkdir()
    (tmp_path / "good_class" / "i.jpg").write_text("x")
    (tmp_path / "bad name with space").mkdir()
    (tmp_path / "bad name with space" / "i.jpg").write_text("x")

    suggestions = propose_labels(tmp_path)

    assert suggestions == ["good_class"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_tool_labels.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement tools/labels.py**

```python
# packages/app/src/echobox_app/tools/labels.py
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
        # Only suggest if subdir actually contains files
        if any(p.is_file() for p in child.iterdir()):
            suggestions.append(child.name)
    return suggestions
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_tool_labels.py -v`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/tools/labels.py packages/app/tests/test_tool_labels.py
git commit -m "feat(app): add set_labels + propose_labels (heuristic from subdirs)"
```

---

## Task 7: Tool — project (set_export_format, finalize_setup, critic)

**Files:**
- Create: `packages/app/src/echobox_app/tools/project.py`
- Create: `packages/app/tests/test_tool_project.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_tool_project.py
from dataclasses import dataclass

import pytest

from echobox_app.domain.inventory import ImageInventory
from echobox_app.domain.organize import ImageEntry
from echobox_app.domain.splits import SplitConfig
from echobox_app.errors import ValidationError
from echobox_app.tools.project import (
    FinalizeResult,
    critic_check,
    set_export_format,
)


@dataclass
class _State:
    inventory: ImageInventory | None = None
    canonical_images: list[ImageEntry] | None = None
    splits: SplitConfig | None = None
    labels: list[str] | None = None
    export_format: str | None = None


def test_set_export_format_accepts_known() -> None:
    for fmt in ("coco", "yolo", "voc", "ls_json"):
        assert set_export_format(fmt) == fmt


def test_set_export_format_rejects_unknown() -> None:
    with pytest.raises(ValidationError):
        set_export_format("kaggle")


def _ready_state() -> _State:
    sc = SplitConfig(train=0.7, val=0.15, test=0.15, seed=42)
    sc.assignments = {"00001.jpg": "train"}
    return _State(
        inventory=ImageInventory(
            total_files=1, valid_count=1, invalid_count=0,
            formats={".jpg": 1}, sample_paths=[],
        ),
        canonical_images=[ImageEntry(
            canonical="00001.jpg", source=__import__("pathlib").Path("/x"),
            sha256="a", bytes=1, width=1, height=1,
        )],
        splits=sc,
        labels=["crack"],
        export_format="coco",
    )


def test_critic_passes_on_complete_state() -> None:
    errs = critic_check(_ready_state())

    assert errs == []


def test_critic_flags_missing_inventory() -> None:
    state = _ready_state()
    state.inventory = None
    errs = critic_check(state)

    assert any("inventory" in e for e in errs)


def test_critic_flags_no_canonical_images() -> None:
    state = _ready_state()
    state.canonical_images = []
    errs = critic_check(state)

    assert any("canonical" in e or "organize" in e for e in errs)


def test_critic_flags_invalid_split() -> None:
    state = _ready_state()
    state.splits = SplitConfig(train=0.5, val=0.3, test=0.3, seed=42)
    errs = critic_check(state)

    assert any("split" in e for e in errs)


def test_critic_flags_missing_labels() -> None:
    state = _ready_state()
    state.labels = []
    errs = critic_check(state)

    assert any("label" in e for e in errs)


def test_critic_flags_missing_format() -> None:
    state = _ready_state()
    state.export_format = None
    errs = critic_check(state)

    assert any("format" in e for e in errs)


def test_finalize_result_dataclass() -> None:
    r = FinalizeResult(success=True, errors=[])
    assert r.success
    assert r.errors == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_tool_project.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement tools/project.py**

```python
# packages/app/src/echobox_app/tools/project.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_tool_project.py -v`
Expected: PASS (10 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/tools/project.py packages/app/tests/test_tool_project.py
git commit -m "feat(app): add set_export_format, critic_check, finalize_setup tools"
```

---

## Task 8: LLM factory (OpenAI-compatible)

**Files:**
- Create: `packages/app/src/echobox_app/llm/__init__.py`
- Create: `packages/app/src/echobox_app/llm/factory.py`
- Create: `packages/app/tests/test_llm_factory.py`

- [ ] **Step 1: Add langchain deps**

Edit `packages/app/pyproject.toml`, add to dependencies:
```
"langchain-core>=0.3",
"langchain-openai>=0.2",
"langgraph>=0.2",
```
Then `uv sync --dev`.

- [ ] **Step 2: Write the failing test**

```python
# packages/app/tests/test_llm_factory.py
from langchain_openai import ChatOpenAI

from echobox_app.config import AppSettings
from echobox_app.llm.factory import build_chat_model


def test_build_chat_model_returns_chat_openai(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "sk-stub")
    settings = AppSettings(_env_file=None)

    model = build_chat_model(settings)

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "qwen-plus"


def test_build_chat_model_overrides(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "sk-x")
    monkeypatch.setenv("ECHOBOX_APP_LLM_MODEL", "qwen-max")
    monkeypatch.setenv("ECHOBOX_APP_LLM_BASE_URL", "https://example.com/v1")
    settings = AppSettings(_env_file=None)

    model = build_chat_model(settings)

    assert model.model_name == "qwen-max"
    assert str(model.openai_api_base) == "https://example.com/v1"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_llm_factory.py -v`
Expected: FAIL.

- [ ] **Step 4: Implement llm/__init__.py and llm/factory.py**

```python
# packages/app/src/echobox_app/llm/__init__.py
"""LLM provider factory."""
```

```python
# packages/app/src/echobox_app/llm/factory.py
"""OpenAI-compatible chat model factory.

Default uses DashScope (qwen-plus). Override via:
- ECHOBOX_APP_LLM_BASE_URL  (e.g. OpenAI, DeepSeek, local vLLM)
- ECHOBOX_APP_LLM_MODEL
- ECHOBOX_APP_LLM_API_KEY
"""
from langchain_openai import ChatOpenAI

from echobox_app.config import AppSettings


def build_chat_model(settings: AppSettings) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=settings.llm_timeout_s,
        max_retries=1,
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_llm_factory.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add packages/app/pyproject.toml packages/app/src/echobox_app/llm/ \
        packages/app/tests/test_llm_factory.py uv.lock
git commit -m "feat(app): add OpenAI-compatible LLM factory (default DashScope qwen-plus)"
```

---

## Task 9: AgentState dataclass

**Files:**
- Create: `packages/app/src/echobox_app/agent/__init__.py`
- Create: `packages/app/src/echobox_app/agent/state.py`
- Create: `packages/app/tests/test_agent_state.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_agent_state.py
from echobox_app.agent.state import AgentState
from echobox_app.domain.messages import Message


def test_agent_state_defaults() -> None:
    state = AgentState(project_id=7)

    assert state.project_id == 7
    assert state.messages == []
    assert state.folder_path is None
    assert state.inventory is None
    assert state.canonical_images == []
    assert state.splits is None
    assert state.labels == []
    assert state.export_format is None
    assert state.status == "draft"
    assert state.last_critic_errors == []


def test_agent_state_append_message() -> None:
    state = AgentState(project_id=1)
    state.messages.append(Message(role="user", content="hi"))

    assert len(state.messages) == 1
    assert state.messages[0].content == "hi"


def test_agent_state_to_dict_for_frontend() -> None:
    state = AgentState(project_id=2, labels=["crack"], export_format="coco")
    state.messages.append(Message(role="user", content="hi"))

    d = state.to_dict()

    assert d["project_id"] == 2
    assert d["labels"] == ["crack"]
    assert d["export_format"] == "coco"
    assert d["status"] == "draft"
    assert d["messages"] == [{"role": "user", "content": "hi", "tool_call_id": None,
                              "tool_name": None, "metadata": {}}]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_agent_state.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement agent/__init__.py and agent/state.py**

```python
# packages/app/src/echobox_app/agent/__init__.py
"""LangGraph agent module."""
```

```python
# packages/app/src/echobox_app/agent/state.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_agent_state.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/agent/ packages/app/tests/test_agent_state.py
git commit -m "feat(app): add AgentState dataclass with to_dict for frontend sync"
```

---

## Task 10: Agent tool wrappers (LangChain Tool schemas)

**Files:**
- Create: `packages/app/src/echobox_app/agent/tool_specs.py`
- Create: `packages/app/tests/test_tool_specs.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_tool_specs.py
from echobox_app.agent.tool_specs import TOOL_SPECS


def test_all_tools_present() -> None:
    names = {t.name for t in TOOL_SPECS}
    assert names == {
        "scan_folder",
        "organize_images",
        "propose_split",
        "set_labels",
        "propose_labels",
        "set_export_format",
        "finalize_setup",
    }


def test_each_tool_has_description_and_args_schema() -> None:
    for spec in TOOL_SPECS:
        assert spec.description, f"{spec.name} missing description"
        assert spec.args_schema is not None or spec.args == {}, f"{spec.name} missing schema"


def test_scan_folder_signature() -> None:
    spec = next(t for t in TOOL_SPECS if t.name == "scan_folder")
    assert "path" in spec.args
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/app/tests/test_tool_specs.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement agent/tool_specs.py**

```python
# packages/app/src/echobox_app/agent/tool_specs.py
"""Tool specifications for LangGraph planner.

These wrap the deterministic tools in `echobox_app.tools` with metadata
the LLM uses to decide when/how to call them.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolSpec:
    name: str
    description: str
    args: dict[str, dict[str, Any]] = field(default_factory=dict)
    args_schema: dict[str, Any] | None = None


_SCAN_FOLDER = ToolSpec(
    name="scan_folder",
    description=(
        "Recursively scan a folder for image files. Returns counts, format "
        "distribution, and sample paths. Call this first when the user gives "
        "a folder path."
    ),
    args={"path": {"type": "string", "description": "absolute folder path"}},
)

_ORGANIZE_IMAGES = ToolSpec(
    name="organize_images",
    description=(
        "Copy valid images to the project workspace as 00001.<ext>, "
        "00002.<ext>, ... Writes mapping.json. Call after scan_folder succeeded."
    ),
    args={},
)

_PROPOSE_SPLIT = ToolSpec(
    name="propose_split",
    description=(
        "Deterministically split organized images into train/val/test by ratios. "
        "Default 0.7/0.15/0.15 with seed 42."
    ),
    args={
        "train": {"type": "number", "description": "train ratio 0..1"},
        "val": {"type": "number", "description": "val ratio 0..1"},
        "test": {"type": "number", "description": "test ratio 0..1"},
        "seed": {"type": "integer", "description": "random seed"},
    },
)

_SET_LABELS = ToolSpec(
    name="set_labels",
    description="Set the project label set. Names must match ^[a-zA-Z0-9_-]+$.",
    args={
        "labels": {
            "type": "array",
            "items": {"type": "string"},
            "description": "label names",
        }
    },
)

_PROPOSE_LABELS = ToolSpec(
    name="propose_labels",
    description=(
        "Heuristic: if source folder has class-named subdirectories (e.g. "
        "source/positive/, source/negative/), suggest those names as labels. "
        "Otherwise returns empty and you should ask the user."
    ),
    args={},
)

_SET_EXPORT_FORMAT = ToolSpec(
    name="set_export_format",
    description="Lock the export format. One of: coco, yolo, voc, ls_json.",
    args={"fmt": {"type": "string", "enum": ["coco", "yolo", "voc", "ls_json"]}},
)

_FINALIZE_SETUP = ToolSpec(
    name="finalize_setup",
    description=(
        "Run critic validation. If all required state is set, transitions "
        "project to status=ready. Otherwise returns error list — fix and retry."
    ),
    args={},
)

TOOL_SPECS: list[ToolSpec] = [
    _SCAN_FOLDER,
    _ORGANIZE_IMAGES,
    _PROPOSE_SPLIT,
    _SET_LABELS,
    _PROPOSE_LABELS,
    _SET_EXPORT_FORMAT,
    _FINALIZE_SETUP,
]


def to_openai_function_specs() -> list[dict[str, Any]]:
    """Convert to OpenAI function-calling spec format."""
    out: list[dict[str, Any]] = []
    for spec in TOOL_SPECS:
        properties = {k: {kk: vv for kk, vv in v.items() if kk != "description"}
                      for k, v in spec.args.items()}
        descriptions = {k: v.get("description", "") for k, v in spec.args.items()}
        for k, prop in properties.items():
            if descriptions[k]:
                prop["description"] = descriptions[k]
        out.append({
            "type": "function",
            "function": {
                "name": spec.name,
                "description": spec.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": list(spec.args.keys()),
                },
            },
        })
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest packages/app/tests/test_tool_specs.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/agent/tool_specs.py packages/app/tests/test_tool_specs.py
git commit -m "feat(app): add tool specifications for LangGraph planner"
```

---

## Task 11: Agent tool executor (dispatches tool calls to mutate state)

**Files:**
- Create: `packages/app/src/echobox_app/agent/executor.py`
- Create: `packages/app/tests/test_agent_executor.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_agent_executor.py
from pathlib import Path

import pytest
from PIL import Image

from echobox_app.agent.executor import execute_tool
from echobox_app.agent.state import AgentState
from echobox_app.workspace.manager import WorkspaceManager


@pytest.fixture
def state_with_workspace(tmp_path: Path) -> tuple[AgentState, WorkspaceManager]:
    state = AgentState(project_id=1)
    wm = WorkspaceManager(root=tmp_path / "data", project_id=1)
    wm.init_directories()
    return state, wm


def test_execute_scan_folder(state_with_workspace, tmp_path) -> None:
    state, wm = state_with_workspace
    src = tmp_path / "src"
    src.mkdir()
    Image.new("RGB", (10, 10)).save(src / "a.jpg", "JPEG")

    result = execute_tool(state, wm, "scan_folder", {"path": str(src)})

    assert result["ok"] is True
    assert state.folder_path == str(src)
    assert state.inventory is not None
    assert state.inventory.valid_count == 1


def test_execute_organize_images(state_with_workspace, tmp_path) -> None:
    state, wm = state_with_workspace
    src = tmp_path / "src"
    src.mkdir()
    Image.new("RGB", (10, 10)).save(src / "a.jpg", "JPEG")
    execute_tool(state, wm, "scan_folder", {"path": str(src)})

    result = execute_tool(state, wm, "organize_images", {})

    assert result["ok"] is True
    assert len(state.canonical_images) == 1
    assert state.canonical_images[0].canonical == "00001.jpg"


def test_execute_propose_split_after_organize(state_with_workspace, tmp_path) -> None:
    state, wm = state_with_workspace
    src = tmp_path / "src"
    src.mkdir()
    for i in range(10):
        Image.new("RGB", (10, 10)).save(src / f"img{i}.jpg", "JPEG")
    execute_tool(state, wm, "scan_folder", {"path": str(src)})
    execute_tool(state, wm, "organize_images", {})

    result = execute_tool(state, wm, "propose_split",
                          {"train": 0.7, "val": 0.15, "test": 0.15, "seed": 42})

    assert result["ok"] is True
    assert state.splits is not None
    assert len(state.splits.assignments) == 10


def test_execute_set_labels(state_with_workspace) -> None:
    state, wm = state_with_workspace

    result = execute_tool(state, wm, "set_labels", {"labels": ["crack", "rust"]})

    assert result["ok"] is True
    assert state.labels == ["crack", "rust"]


def test_execute_set_export_format(state_with_workspace) -> None:
    state, wm = state_with_workspace

    result = execute_tool(state, wm, "set_export_format", {"fmt": "yolo"})

    assert result["ok"] is True
    assert state.export_format == "yolo"


def test_execute_unknown_tool_returns_error(state_with_workspace) -> None:
    state, wm = state_with_workspace

    result = execute_tool(state, wm, "made_up", {})

    assert result["ok"] is False
    assert "unknown" in result["error"].lower()


def test_execute_validation_error_captured(state_with_workspace) -> None:
    state, wm = state_with_workspace

    result = execute_tool(state, wm, "set_labels", {"labels": []})

    assert result["ok"] is False
    assert "code" in result
    assert result["code"] == "validation_failed"


def test_execute_finalize_setup_with_complete_state(state_with_workspace, tmp_path) -> None:
    state, wm = state_with_workspace
    src = tmp_path / "src"
    src.mkdir()
    Image.new("RGB", (10, 10)).save(src / "a.jpg", "JPEG")
    execute_tool(state, wm, "scan_folder", {"path": str(src)})
    execute_tool(state, wm, "organize_images", {})
    execute_tool(state, wm, "propose_split",
                 {"train": 1.0, "val": 0.0, "test": 0.0, "seed": 42})
    execute_tool(state, wm, "set_labels", {"labels": ["crack"]})
    execute_tool(state, wm, "set_export_format", {"fmt": "coco"})

    result = execute_tool(state, wm, "finalize_setup", {})

    assert result["ok"] is True
    assert state.status == "ready"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_agent_executor.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement agent/executor.py**

```python
# packages/app/src/echobox_app/agent/executor.py
"""Dispatch a single tool call: validate inputs, run the tool, mutate AgentState."""
from pathlib import Path
from typing import Any

from echobox_app.agent.state import AgentState
from echobox_app.errors import ArisError, ValidationError
from echobox_app.tools.filesystem import organize_images, scan_folder
from echobox_app.tools.labels import propose_labels, set_labels
from echobox_app.tools.project import finalize_setup, set_export_format
from echobox_app.tools.splits import propose_split
from echobox_app.workspace.manager import WorkspaceManager


def execute_tool(
    state: AgentState,
    workspace: WorkspaceManager,
    name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    try:
        if name == "scan_folder":
            return _do_scan(state, arguments)
        if name == "organize_images":
            return _do_organize(state, workspace)
        if name == "propose_split":
            return _do_propose_split(state, arguments)
        if name == "set_labels":
            return _do_set_labels(state, arguments)
        if name == "propose_labels":
            return _do_propose_labels(state)
        if name == "set_export_format":
            return _do_set_export_format(state, arguments)
        if name == "finalize_setup":
            return _do_finalize(state, workspace)
        return {"ok": False, "error": f"unknown tool: {name}", "code": "unknown_tool"}
    except ArisError as e:
        return {"ok": False, "error": e.message, "code": e.code, "detail": e.detail}


def _do_scan(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    path = args.get("path")
    if not path:
        raise ValidationError("path argument required")
    res = scan_folder(Path(path))
    state.folder_path = str(res.folder)
    state.inventory = res.inventory
    return {"ok": True, "data": res.to_dict()}


def _do_organize(state: AgentState, workspace: WorkspaceManager) -> dict[str, Any]:
    if state.inventory is None or state.folder_path is None:
        raise ValidationError("call scan_folder first")
    from echobox_app.domain.inventory import ScanResult
    sr = ScanResult(folder=Path(state.folder_path), inventory=state.inventory)
    res = organize_images(sr, workspace)
    state.canonical_images = list(res.entries)
    return {"ok": True, "data": {"copied_count": res.copied_count}}


def _do_propose_split(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    if not state.canonical_images:
        raise ValidationError("call organize_images first")
    cfg = propose_split(
        [e.canonical for e in state.canonical_images],
        train=float(args.get("train", 0.7)),
        val=float(args.get("val", 0.15)),
        test=float(args.get("test", 0.15)),
        seed=int(args.get("seed", 42)),
    )
    state.splits = cfg
    return {"ok": True, "data": cfg.to_dict()}


def _do_set_labels(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    labels = args.get("labels")
    if not isinstance(labels, list):
        raise ValidationError("labels must be a list of strings")
    out = set_labels(labels)
    state.labels = out
    return {"ok": True, "data": {"labels": out}}


def _do_propose_labels(state: AgentState) -> dict[str, Any]:
    if state.folder_path is None:
        raise ValidationError("call scan_folder first")
    suggestions = propose_labels(Path(state.folder_path))
    return {"ok": True, "data": {"suggestions": suggestions}}


def _do_set_export_format(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    fmt = args.get("fmt")
    if not isinstance(fmt, str):
        raise ValidationError("fmt argument required")
    state.export_format = set_export_format(fmt)  # type: ignore[assignment]
    return {"ok": True, "data": {"fmt": state.export_format}}


def _do_finalize(state: AgentState, workspace: WorkspaceManager) -> dict[str, Any]:
    res = finalize_setup(state)
    state.last_critic_errors = list(res.errors)
    if res.success:
        state.status = "ready"
        # Persist project.json snapshot
        if state.splits is not None and state.inventory is not None:
            workspace.write_splits(state.splits)
            workspace.write_project_meta({
                "id": state.project_id,
                "status": "ready",
                "labels": state.labels,
                "export_format": state.export_format,
                "splits": {
                    "train": state.splits.train,
                    "val": state.splits.val,
                    "test": state.splits.test,
                    "seed": state.splits.seed,
                },
                "image_count": len(state.canonical_images),
            })
        return {"ok": True, "data": {"status": "ready"}}
    return {"ok": False, "error": "critic failed", "code": "critic_failed",
            "detail": {"errors": res.errors}}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_agent_executor.py -v`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/agent/executor.py packages/app/tests/test_agent_executor.py
git commit -m "feat(app): add agent tool executor that dispatches tool calls + mutates state"
```

---

## Task 12: LangGraph planner + graph

**Files:**
- Create: `packages/app/src/echobox_app/agent/graph.py`
- Create: `packages/app/tests/test_agent_graph.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_agent_graph.py
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, ToolMessage
from PIL import Image

from echobox_app.agent.graph import build_graph
from echobox_app.agent.state import AgentState
from echobox_app.domain.messages import Message
from echobox_app.workspace.manager import WorkspaceManager


def _fake_llm_returning(messages: list) -> MagicMock:
    """Make a fake ChatOpenAI that returns given messages in sequence."""
    llm = MagicMock()
    llm.bind_tools = MagicMock(return_value=llm)
    llm.invoke = MagicMock(side_effect=messages)
    return llm


def test_graph_handles_plain_reply(tmp_path: Path) -> None:
    state = AgentState(project_id=1)
    state.messages.append(Message(role="user", content="hi"))
    wm = WorkspaceManager(root=tmp_path, project_id=1)
    wm.init_directories()

    llm = _fake_llm_returning([AIMessage(content="Hello! Give me a folder path.")])
    graph = build_graph(llm)

    out = graph.invoke({"state": state, "workspace": wm})

    assert out["state"].messages[-1].role == "assistant"
    assert "folder" in out["state"].messages[-1].content


def test_graph_invokes_tool_then_replies(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    Image.new("RGB", (10, 10)).save(src / "a.jpg", "JPEG")

    state = AgentState(project_id=1)
    state.messages.append(Message(role="user", content=f"scan {src}"))
    wm = WorkspaceManager(root=tmp_path / "ws", project_id=1)
    wm.init_directories()

    tool_call = AIMessage(
        content="",
        tool_calls=[{"name": "scan_folder", "args": {"path": str(src)}, "id": "call_1"}],
    )
    final_reply = AIMessage(content="Found 1 image.")
    llm = _fake_llm_returning([tool_call, final_reply])
    graph = build_graph(llm)

    out = graph.invoke({"state": state, "workspace": wm})

    assert out["state"].inventory is not None
    assert out["state"].inventory.valid_count == 1
    assert out["state"].messages[-1].content == "Found 1 image."


def test_graph_caps_iterations(tmp_path: Path) -> None:
    """LLM keeps calling tools forever — graph should bail out."""
    state = AgentState(project_id=1)
    state.messages.append(Message(role="user", content="loop"))
    wm = WorkspaceManager(root=tmp_path, project_id=1)
    wm.init_directories()

    infinite_call = AIMessage(
        content="",
        tool_calls=[{"name": "propose_labels", "args": {}, "id": f"c{i}"}],
    )
    # Provide many copies so the side_effect never runs out
    llm = _fake_llm_returning([infinite_call] * 50)
    graph = build_graph(llm, max_iterations=5)

    out = graph.invoke({"state": state, "workspace": wm})

    # The last message should be a system "iteration limit reached"
    assert any("iteration" in m.content.lower() for m in out["state"].messages[-3:])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_agent_graph.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement agent/graph.py**

```python
# packages/app/src/echobox_app/agent/graph.py
"""LangGraph wiring: planner LLM + tool executor loop, with iteration cap.

For v1 we use a hand-rolled state machine (not langgraph.StateGraph) because:
- The graph is linear (planner -> executor -> planner)
- Direct loop is easier to test deterministically
- We can swap to StateGraph later without API changes

Public API: build_graph(llm) -> object with .invoke({state, workspace}) -> dict.
"""
from dataclasses import dataclass
from typing import Any, Callable, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.messages import ToolMessage as LCToolMessage

from echobox_app.agent.executor import execute_tool
from echobox_app.agent.state import AgentState
from echobox_app.agent.tool_specs import to_openai_function_specs
from echobox_app.domain.messages import Message
from echobox_app.workspace.manager import WorkspaceManager

_SYSTEM_PROMPT = """You are an annotation project setup assistant.
Your job: help the user prepare a dataset for annotation.

You have these tools:
- scan_folder(path): scan a folder for image files
- organize_images(): copy valid images into the project workspace
- propose_split(train, val, test, seed): assign train/val/test splits
- set_labels(labels): set the label set
- propose_labels(): suggest labels from source folder structure
- set_export_format(fmt): pick coco/yolo/voc/ls_json
- finalize_setup(): validate and lock the project as ready

The user can also edit cards directly (you'll see SystemMessages reflecting their edits).

Be concise. Ask one thing at a time. Confirm before destructive actions.
When everything is set, call finalize_setup."""


class _Inputs(TypedDict):
    state: AgentState
    workspace: WorkspaceManager


@dataclass
class _CompiledGraph:
    llm: Any
    max_iterations: int

    def invoke(self, inputs: _Inputs) -> dict[str, Any]:
        state = inputs["state"]
        workspace = inputs["workspace"]
        bound_llm = self.llm.bind_tools(to_openai_function_specs())

        for iteration in range(self.max_iterations):
            lc_messages = _to_lc_messages(state.messages)
            response: AIMessage = bound_llm.invoke(lc_messages)

            tool_calls = getattr(response, "tool_calls", []) or []
            if not tool_calls:
                state.messages.append(Message(role="assistant", content=response.content or ""))
                return {"state": state}

            # Append the assistant's tool-call announcement
            state.messages.append(Message(
                role="assistant",
                content=response.content or "",
                metadata={"tool_calls": [
                    {"id": tc["id"], "name": tc["name"], "args": tc["args"]}
                    for tc in tool_calls
                ]},
            ))

            for tc in tool_calls:
                result = execute_tool(state, workspace, tc["name"], tc["args"])
                state.messages.append(Message(
                    role="tool",
                    content=str(result),
                    tool_call_id=tc["id"],
                    tool_name=tc["name"],
                ))

        state.messages.append(Message(
            role="system",
            content=f"iteration limit reached ({self.max_iterations})",
        ))
        return {"state": state}


def build_graph(llm: Any, max_iterations: int = 8) -> _CompiledGraph:
    return _CompiledGraph(llm=llm, max_iterations=max_iterations)


def _to_lc_messages(messages: list[Message]) -> list[BaseMessage]:
    out: list[BaseMessage] = [SystemMessage(content=_SYSTEM_PROMPT)]
    for m in messages:
        if m.role == "user":
            out.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            out.append(AIMessage(content=m.content))
        elif m.role == "tool":
            out.append(LCToolMessage(
                content=m.content,
                tool_call_id=m.tool_call_id or "",
            ))
        elif m.role == "system":
            out.append(SystemMessage(content=m.content))
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_agent_graph.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/agent/graph.py packages/app/tests/test_agent_graph.py
git commit -m "feat(app): add LangGraph-style agent loop with planner + tool executor + iteration cap"
```

---

## Task 13: API dependencies (Depends factories for session/workspace/llm)

**Files:**
- Create: `packages/app/src/echobox_app/api/__init__.py`
- Create: `packages/app/src/echobox_app/api/deps.py`
- Create: `packages/app/tests/test_api_deps.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_api_deps.py
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from echobox_app.api.deps import get_settings, get_workspace_root


def test_get_settings_from_app(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    from echobox_app.main import create_app

    app = create_app()
    settings = get_settings(app)

    assert settings.llm_model == "qwen-plus"


def test_get_workspace_root_uses_data_dir(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path))
    from echobox_app.config import AppSettings
    settings = AppSettings(_env_file=None)

    root = get_workspace_root(settings)

    assert root == tmp_path / "projects"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_api_deps.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement api/__init__.py and api/deps.py**

```python
# packages/app/src/echobox_app/api/__init__.py
"""HTTP API routers."""
```

```python
# packages/app/src/echobox_app/api/deps.py
"""FastAPI dependencies."""
from collections.abc import Generator
from pathlib import Path

from fastapi import FastAPI, Request
from sqlalchemy.orm import Session

from echobox_app.config import AppSettings


def get_settings(app: FastAPI) -> AppSettings:
    settings: AppSettings = app.state.settings
    return settings


def get_workspace_root(settings: AppSettings) -> Path:
    return settings.data_dir / "projects"


def session_dep(request: Request) -> Generator[Session, None, None]:
    factory = request.app.state.session_factory
    s = factory()
    try:
        yield s
    finally:
        s.close()


def settings_dep(request: Request) -> AppSettings:
    return get_settings(request.app)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_api_deps.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/api/ packages/app/tests/test_api_deps.py
git commit -m "feat(app): add FastAPI dependency factories (settings, session, workspace)"
```

---

## Task 14: REST — POST /api/projects (create) + GET /api/projects/{pid}

**Files:**
- Create: `packages/app/src/echobox_app/api/projects.py`
- Create: `packages/app/tests/test_api_projects.py`
- Modify: `packages/app/src/echobox_app/main.py` (include router)

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_api_projects.py
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/test.db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path / "data"))
    from echobox_app.db.models import Base
    from echobox_app.db.session import make_engine
    from echobox_app.main import create_app

    app = create_app()
    Base.metadata.create_all(make_engine(f"sqlite:///{tmp_path}/test.db"))
    return TestClient(app)


def test_create_project(client: TestClient, tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    resp = client.post("/api/projects", json={"source_folder": str(src)})

    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] >= 1
    assert body["source_folder"] == str(src)
    assert body["status"] == "draft"


def test_create_project_with_initial_config(client: TestClient, tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    resp = client.post("/api/projects", json={
        "source_folder": str(src),
        "name": "my-project",
        "initial_labels": ["crack", "rust"],
        "train_val_test": [0.6, 0.2, 0.2],
        "export_format": "yolo",
    })

    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "my-project"
    assert body["train_ratio"] == 0.6
    assert body["val_ratio"] == 0.2
    assert body["test_ratio"] == 0.2
    assert body["export_format"] == "yolo"


def test_create_project_rejects_invalid_split(client: TestClient, tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    resp = client.post("/api/projects", json={
        "source_folder": str(src),
        "train_val_test": [0.5, 0.3, 0.3],  # sum 1.1
    })

    assert resp.status_code == 400


def test_get_project(client: TestClient, tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    pid = client.post("/api/projects", json={"source_folder": str(src)}).json()["id"]

    resp = client.get(f"/api/projects/{pid}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == pid
    assert body["status"] == "draft"
    assert body["labels"] == []
    assert body["messages"] == []


def test_get_missing_project_404(client: TestClient) -> None:
    resp = client.get("/api/projects/9999")

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "project_not_found"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_api_projects.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement api/projects.py**

```python
# packages/app/src/echobox_app/api/projects.py
"""Project REST endpoints (POST/GET; PATCH/POST labels/finalize in later tasks)."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from echobox_app.api.deps import session_dep, settings_dep
from echobox_app.config import AppSettings
from echobox_app.db.models import Label, Project
from echobox_app.errors import ProjectNotFound, ValidationError

router = APIRouter(prefix="/api/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    source_folder: str = Field(min_length=1)
    name: str | None = None
    initial_labels: list[str] | None = None
    train_val_test: tuple[float, float, float] | None = None
    export_format: str | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest,
    session: Annotated[Session, Depends(session_dep)],
    settings: Annotated[AppSettings, Depends(settings_dep)],
) -> dict[str, Any]:
    if payload.train_val_test is not None:
        s = sum(payload.train_val_test)
        if abs(s - 1.0) > 1e-6:
            raise ValidationError(
                f"train_val_test ratios must sum to 1.0 (got {s})",
                detail={"ratios": list(payload.train_val_test)},
            )
        train, val, test = payload.train_val_test
    else:
        train, val, test = 0.7, 0.15, 0.15

    if payload.export_format and payload.export_format not in {"coco", "yolo", "voc", "ls_json"}:
        raise ValidationError(f"unknown export_format: {payload.export_format}")

    name = payload.name or _default_name(payload.source_folder)
    project = Project(
        name=name,
        workspace_path="",  # set after id is known
        source_folder=payload.source_folder,
        status="draft",
        export_format=payload.export_format,
        train_ratio=train,
        val_ratio=val,
        test_ratio=test,
    )
    session.add(project)
    session.flush()

    project.workspace_path = str((settings.data_dir / "projects" / str(project.id)).resolve())
    if payload.initial_labels:
        for lname in payload.initial_labels:
            session.add(Label(project_id=project.id, name=lname, color=_assign_color(len(project.labels))))
    session.commit()
    session.refresh(project)

    return _project_to_dict(project, include_state=False)


@router.get("/{pid}")
def get_project(
    pid: int,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    project = session.get(Project, pid)
    if project is None:
        raise ProjectNotFound(f"project {pid} not found", detail={"project_id": pid})
    return _project_to_dict(project, include_state=True)


def _default_name(source_folder: str) -> str:
    base = Path(source_folder).name or "project"
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{base}-{today}"


_PALETTE = ["#e63946", "#457b9d", "#2a9d8f", "#f4a261", "#264653",
            "#9b5de5", "#f15bb5", "#00bbf9", "#00f5d4", "#fee440"]


def _assign_color(index: int) -> str:
    return _PALETTE[index % len(_PALETTE)]


def _project_to_dict(project: Project, *, include_state: bool) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": project.id,
        "name": project.name,
        "source_folder": project.source_folder,
        "workspace_path": project.workspace_path,
        "status": project.status,
        "export_format": project.export_format,
        "train_ratio": project.train_ratio,
        "val_ratio": project.val_ratio,
        "test_ratio": project.test_ratio,
        "labels": [{"name": l.name, "color": l.color} for l in project.labels],
        "image_count": len(project.images),
    }
    if include_state:
        out["messages"] = [
            {"role": m.role, "content": m.content,
             "tool_call_id": m.tool_call_id, "tool_name": m.tool_name,
             "created_at": m.created_at.isoformat() if m.created_at else None}
            for m in project.chat_messages
        ]
    return out
```

- [ ] **Step 4: Modify main.py to include the router**

Edit `packages/app/src/echobox_app/main.py`. After the line `app.state.session_factory = session_factory`, add:

```python
    from echobox_app.api.projects import router as projects_router
    app.include_router(projects_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_api_projects.py -v`
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add packages/app/src/echobox_app/api/projects.py packages/app/src/echobox_app/main.py \
        packages/app/tests/test_api_projects.py
git commit -m "feat(app): add POST /api/projects + GET /api/projects/{pid}"
```

---

## Task 15: REST — PATCH endpoints (folder, splits, format)

**Files:**
- Modify: `packages/app/src/echobox_app/api/projects.py` (add PATCH routes)
- Create: `packages/app/tests/test_api_projects_patch.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_api_projects_patch.py
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture
def client_with_project(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path / "data"))
    from echobox_app.db.models import Base
    from echobox_app.db.session import make_engine
    from echobox_app.main import create_app

    app = create_app()
    Base.metadata.create_all(make_engine(f"sqlite:///{tmp_path}/db"))
    client = TestClient(app)
    src = tmp_path / "src"
    src.mkdir()
    Image.new("RGB", (10, 10)).save(src / "a.jpg", "JPEG")
    pid = client.post("/api/projects", json={"source_folder": str(src)}).json()["id"]
    return client, pid, src


def test_patch_folder(client_with_project, tmp_path: Path) -> None:
    client, pid, _ = client_with_project
    src2 = tmp_path / "src2"
    src2.mkdir()
    Image.new("RGB", (10, 10)).save(src2 / "b.jpg", "JPEG")

    resp = client.patch(f"/api/projects/{pid}/folder", json={"folder": str(src2)})

    assert resp.status_code == 200
    assert resp.json()["source_folder"] == str(src2)


def test_patch_splits(client_with_project) -> None:
    client, pid, _ = client_with_project

    resp = client.patch(f"/api/projects/{pid}/splits", json={
        "train": 0.6, "val": 0.2, "test": 0.2,
    })

    assert resp.status_code == 200
    body = resp.json()
    assert body["train_ratio"] == 0.6
    assert body["val_ratio"] == 0.2


def test_patch_splits_rejects_bad_sum(client_with_project) -> None:
    client, pid, _ = client_with_project

    resp = client.patch(f"/api/projects/{pid}/splits", json={
        "train": 0.5, "val": 0.3, "test": 0.3,
    })

    assert resp.status_code == 400


def test_patch_format(client_with_project) -> None:
    client, pid, _ = client_with_project

    resp = client.patch(f"/api/projects/{pid}/format", json={"format": "yolo"})

    assert resp.status_code == 200
    assert resp.json()["export_format"] == "yolo"


def test_patch_format_rejects_unknown(client_with_project) -> None:
    client, pid, _ = client_with_project

    resp = client.patch(f"/api/projects/{pid}/format", json={"format": "kaggle"})

    assert resp.status_code == 400
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_api_projects_patch.py -v`
Expected: FAIL.

- [ ] **Step 3: Add PATCH routes to api/projects.py**

Append to `packages/app/src/echobox_app/api/projects.py`:

```python
class PatchFolder(BaseModel):
    folder: str = Field(min_length=1)


class PatchSplits(BaseModel):
    train: float
    val: float
    test: float


class PatchFormat(BaseModel):
    format: str


@router.patch("/{pid}/folder")
def patch_folder(
    pid: int,
    payload: PatchFolder,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    project = _get_or_404(session, pid)
    project.source_folder = payload.folder
    session.commit()
    session.refresh(project)
    return _project_to_dict(project, include_state=False)


@router.patch("/{pid}/splits")
def patch_splits(
    pid: int,
    payload: PatchSplits,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    if abs(payload.train + payload.val + payload.test - 1.0) > 1e-6:
        raise ValidationError(
            "train+val+test must sum to 1.0",
            detail={"train": payload.train, "val": payload.val, "test": payload.test},
        )
    project = _get_or_404(session, pid)
    project.train_ratio = payload.train
    project.val_ratio = payload.val
    project.test_ratio = payload.test
    session.commit()
    session.refresh(project)
    return _project_to_dict(project, include_state=False)


@router.patch("/{pid}/format")
def patch_format(
    pid: int,
    payload: PatchFormat,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    if payload.format not in {"coco", "yolo", "voc", "ls_json"}:
        raise ValidationError(f"unknown format: {payload.format}")
    project = _get_or_404(session, pid)
    project.export_format = payload.format  # type: ignore[assignment]
    session.commit()
    session.refresh(project)
    return _project_to_dict(project, include_state=False)


def _get_or_404(session: Session, pid: int) -> Project:
    project = session.get(Project, pid)
    if project is None:
        raise ProjectNotFound(f"project {pid} not found", detail={"project_id": pid})
    return project
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_api_projects_patch.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/api/projects.py packages/app/tests/test_api_projects_patch.py
git commit -m "feat(app): add PATCH /folder, /splits, /format endpoints"
```

---

## Task 16: REST — Labels (POST add, DELETE)

**Files:**
- Modify: `packages/app/src/echobox_app/api/projects.py`
- Create: `packages/app/tests/test_api_labels.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_api_labels.py
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_project(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path / "data"))
    from echobox_app.db.models import Base
    from echobox_app.db.session import make_engine
    from echobox_app.main import create_app

    app = create_app()
    Base.metadata.create_all(make_engine(f"sqlite:///{tmp_path}/db"))
    client = TestClient(app)
    src = tmp_path / "src"
    src.mkdir()
    pid = client.post("/api/projects", json={"source_folder": str(src)}).json()["id"]
    return client, pid


def test_add_label(client_with_project) -> None:
    client, pid = client_with_project

    resp = client.post(f"/api/projects/{pid}/labels", json={"name": "crack"})

    assert resp.status_code == 201
    assert resp.json()["name"] == "crack"
    assert resp.json()["color"].startswith("#")


def test_add_label_with_explicit_color(client_with_project) -> None:
    client, pid = client_with_project

    resp = client.post(f"/api/projects/{pid}/labels",
                       json={"name": "rust", "color": "#ff0000"})

    assert resp.json()["color"] == "#ff0000"


def test_add_duplicate_label_409(client_with_project) -> None:
    client, pid = client_with_project
    client.post(f"/api/projects/{pid}/labels", json={"name": "crack"})

    resp = client.post(f"/api/projects/{pid}/labels", json={"name": "crack"})

    assert resp.status_code == 409


def test_add_invalid_label_name_400(client_with_project) -> None:
    client, pid = client_with_project

    resp = client.post(f"/api/projects/{pid}/labels", json={"name": "with space"})

    assert resp.status_code == 400


def test_delete_label_in_draft(client_with_project) -> None:
    client, pid = client_with_project
    client.post(f"/api/projects/{pid}/labels", json={"name": "crack"})

    resp = client.delete(f"/api/projects/{pid}/labels/crack")

    assert resp.status_code == 204


def test_delete_label_after_ready_403(client_with_project, monkeypatch, tmp_path) -> None:
    client, pid = client_with_project
    client.post(f"/api/projects/{pid}/labels", json={"name": "crack"})
    # Manually flip status to ready via DB to test gate
    from echobox_app.db.session import make_engine, make_session_factory
    engine = make_engine(f"sqlite:///{tmp_path}/db")
    sf = make_session_factory(engine)
    with sf() as s:
        from echobox_app.db.models import Project
        p = s.get(Project, pid)
        assert p is not None
        p.status = "ready"
        s.commit()

    resp = client.delete(f"/api/projects/{pid}/labels/crack")

    assert resp.status_code == 403
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_api_labels.py -v`
Expected: FAIL.

- [ ] **Step 3: Add label routes to api/projects.py**

Append:

```python
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from echobox_app.errors import LabelConflict
from echobox_app.tools.labels import validate_label_name


class CreateLabel(BaseModel):
    name: str
    color: str | None = None


@router.post("/{pid}/labels", status_code=status.HTTP_201_CREATED)
def add_label(
    pid: int,
    payload: CreateLabel,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    project = _get_or_404(session, pid)
    if not validate_label_name(payload.name):
        raise ValidationError(
            f"invalid label name: {payload.name!r}",
            detail={"rule": "^[a-zA-Z0-9_-]+$"},
        )
    color = payload.color or _assign_color(len(project.labels))
    label = Label(project_id=project.id, name=payload.name, color=color)
    session.add(label)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise LabelConflict(
            f"label {payload.name!r} already exists",
            detail={"name": payload.name},
        )
    return {"id": label.id, "name": label.name, "color": label.color}


@router.delete("/{pid}/labels/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_label(
    pid: int,
    name: str,
    session: Annotated[Session, Depends(session_dep)],
) -> None:
    project = _get_or_404(session, pid)
    if project.status != "draft":
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "label_immutable",
                              "message": f"labels cannot be deleted in status={project.status}"}},
        )
    label = next((l for l in project.labels if l.name == name), None)
    if label is None:
        raise ProjectNotFound(f"label {name!r} not found in project {pid}")
    session.delete(label)
    session.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_api_labels.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/api/projects.py packages/app/tests/test_api_labels.py
git commit -m "feat(app): add POST /labels (with conflict 409) + DELETE /labels (draft-only)"
```

---

## Task 17: REST — POST /finalize

**Files:**
- Modify: `packages/app/src/echobox_app/api/projects.py`
- Create: `packages/app/tests/test_api_finalize.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_api_finalize.py
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture
def client_ready_to_finalize(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path / "data"))
    from echobox_app.db.models import Base
    from echobox_app.db.session import make_engine
    from echobox_app.main import create_app

    app = create_app()
    Base.metadata.create_all(make_engine(f"sqlite:///{tmp_path}/db"))
    client = TestClient(app)

    src = tmp_path / "src"
    src.mkdir()
    Image.new("RGB", (10, 10)).save(src / "a.jpg", "JPEG")
    pid = client.post("/api/projects", json={
        "source_folder": str(src),
        "initial_labels": ["crack"],
        "export_format": "coco",
    }).json()["id"]

    # Manually pre-populate canonical_images via direct DB write to fake "organize done"
    from echobox_app.db.models import Image as DBImage
    from echobox_app.db.session import make_engine, make_session_factory
    engine = make_engine(f"sqlite:///{tmp_path}/db")
    sf = make_session_factory(engine)
    with sf() as s:
        s.add(DBImage(
            project_id=pid, filename="00001.jpg",
            abs_path=str(tmp_path / "00001.jpg"),
            width=10, height=10, split="train",
            index_in_project=0, source_path=str(src / "a.jpg"),
        ))
        s.commit()
    return client, pid


def test_finalize_succeeds(client_ready_to_finalize) -> None:
    client, pid = client_ready_to_finalize

    resp = client.post(f"/api/projects/{pid}/finalize")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"


def test_finalize_fails_without_labels(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path / "data"))
    from echobox_app.db.models import Base
    from echobox_app.db.session import make_engine
    from echobox_app.main import create_app

    app = create_app()
    Base.metadata.create_all(make_engine(f"sqlite:///{tmp_path}/db"))
    client = TestClient(app)
    src = tmp_path / "src"
    src.mkdir()
    pid = client.post("/api/projects", json={
        "source_folder": str(src),
        "export_format": "coco",
    }).json()["id"]

    resp = client.post(f"/api/projects/{pid}/finalize")

    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "critic_failed"
    assert any("label" in e.lower() for e in body["error"]["detail"]["errors"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_api_finalize.py -v`
Expected: FAIL.

- [ ] **Step 3: Add finalize route to api/projects.py**

Append:

```python
from echobox_app.errors import ArisError


class _FinalizeError(ArisError):
    code = "critic_failed"
    http_status = 400


@router.post("/{pid}/finalize")
def finalize(
    pid: int,
    session: Annotated[Session, Depends(session_dep)],
) -> dict[str, Any]:
    project = _get_or_404(session, pid)

    errors: list[str] = []
    if not project.labels:
        errors.append("label set empty")
    if not project.export_format:
        errors.append("export format not chosen")
    if not project.images:
        errors.append("no images organized (run agent setup)")
    if abs(project.train_ratio + project.val_ratio + project.test_ratio - 1.0) > 1e-6:
        errors.append("split ratios do not sum to 1.0")

    if errors:
        raise _FinalizeError("critic failed", detail={"errors": errors})

    project.status = "ready"
    session.commit()
    session.refresh(project)
    return {"status": project.status, "id": project.id}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_api_finalize.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/api/projects.py packages/app/tests/test_api_finalize.py
git commit -m "feat(app): add POST /finalize with critic gate"
```

---

## Task 18: REST — POST /api/projects/{pid}/chat (SSE)

**Files:**
- Create: `packages/app/src/echobox_app/api/chat.py`
- Modify: `packages/app/src/echobox_app/main.py` (include router)
- Create: `packages/app/tests/test_api_chat.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_api_chat.py
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage


@pytest.fixture
def client_with_fake_llm(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path / "data"))

    fake_llm = MagicMock()
    fake_llm.bind_tools = MagicMock(return_value=fake_llm)
    fake_llm.invoke = MagicMock(return_value=AIMessage(content="hello back"))

    from echobox_app import llm as llm_mod
    monkeypatch.setattr(llm_mod.factory, "build_chat_model", lambda settings: fake_llm)

    from echobox_app.db.models import Base
    from echobox_app.db.session import make_engine
    from echobox_app.main import create_app

    app = create_app()
    Base.metadata.create_all(make_engine(f"sqlite:///{tmp_path}/db"))
    client = TestClient(app)

    src = tmp_path / "src"
    src.mkdir()
    pid = client.post("/api/projects", json={"source_folder": str(src)}).json()["id"]
    return client, pid


def test_chat_returns_sse_stream_with_assistant_reply(client_with_fake_llm) -> None:
    client, pid = client_with_fake_llm

    with client.stream("POST", f"/api/projects/{pid}/chat",
                        json={"content": "hi"}) as resp:
        assert resp.status_code == 200
        events = [line for line in resp.iter_lines() if line]

    assert any("hello back" in e for e in events)


def test_chat_persists_messages(client_with_fake_llm) -> None:
    client, pid = client_with_fake_llm

    with client.stream("POST", f"/api/projects/{pid}/chat",
                        json={"content": "hi"}) as resp:
        list(resp.iter_lines())

    proj = client.get(f"/api/projects/{pid}").json()
    roles = [m["role"] for m in proj["messages"]]
    assert "user" in roles
    assert "assistant" in roles
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_api_chat.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement api/chat.py**

```python
# packages/app/src/echobox_app/api/chat.py
"""SSE chat endpoint that drives LangGraph one turn per user message."""
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from echobox_app.agent.graph import build_graph
from echobox_app.agent.state import AgentState
from echobox_app.api.deps import session_dep, settings_dep
from echobox_app.config import AppSettings
from echobox_app.db.models import ChatMessage, Project
from echobox_app.domain.messages import Message
from echobox_app.errors import ProjectNotFound
from echobox_app.llm.factory import build_chat_model
from echobox_app.workspace.manager import WorkspaceManager

router = APIRouter(prefix="/api/projects", tags=["chat"])


class ChatPayload(BaseModel):
    content: str = Field(min_length=1)


@router.post("/{pid}/chat")
def chat(
    pid: int,
    payload: ChatPayload,
    session: Annotated[Session, Depends(session_dep)],
    settings: Annotated[AppSettings, Depends(settings_dep)],
) -> StreamingResponse:
    project = session.get(Project, pid)
    if project is None:
        raise ProjectNotFound(f"project {pid} not found", detail={"project_id": pid})

    # Build state from DB
    db_messages = list(project.chat_messages)
    state = AgentState(
        project_id=pid,
        messages=[Message(role=m.role, content=m.content,
                          tool_call_id=m.tool_call_id, tool_name=m.tool_name)
                  for m in db_messages],
        labels=[l.name for l in project.labels],
        export_format=project.export_format,
        status=project.status,  # type: ignore[arg-type]
    )
    state.messages.append(Message(role="user", content=payload.content))

    workspace = WorkspaceManager(root=settings.data_dir / "projects", project_id=pid)
    workspace.init_directories()
    llm = build_chat_model(settings)
    graph = build_graph(llm)

    async def _stream() -> AsyncIterator[bytes]:
        # Invoke graph (synchronous; we yield results after)
        result = graph.invoke({"state": state, "workspace": workspace})
        out_state: AgentState = result["state"]

        # Persist NEW messages to DB
        old_count = len(db_messages)
        new_messages = out_state.messages[old_count:]
        for m in new_messages:
            session.add(ChatMessage(
                project_id=pid, role=m.role, content=m.content,
                tool_call_id=m.tool_call_id, tool_name=m.tool_name,
            ))
        session.commit()

        # Stream them out
        for m in new_messages:
            event = {"type": "message", "data": m.to_dict()}
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode("utf-8")
        yield b"data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")
```

- [ ] **Step 4: Modify main.py**

Edit `packages/app/src/echobox_app/main.py` and add after `app.include_router(projects_router)`:

```python
    from echobox_app.api.chat import router as chat_router
    app.include_router(chat_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_api_chat.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add packages/app/src/echobox_app/api/chat.py packages/app/src/echobox_app/main.py \
        packages/app/tests/test_api_chat.py
git commit -m "feat(app): add POST /chat SSE endpoint that drives LangGraph + persists messages"
```

---

## Task 19: Frontend — API client + types

**Files:**
- Create: `frontend/src/types/project.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/projects.ts`
- Create: `frontend/src/api/chat.ts`

- [ ] **Step 1: Add deps**

Edit `frontend/package.json`, add:
```json
{
  "dependencies": {
    "react-router-dom": "^6.24.0",
    "@tanstack/react-query": "^5.50.0",
    "zustand": "^4.5.4",
    "axios": "^1.7.2"
  }
}
```
Then `cd frontend && npm install`.

- [ ] **Step 2: Create types/project.ts**

```typescript
// frontend/src/types/project.ts
export type ProjectStatus = "draft" | "ready" | "annotating" | "exported";
export type ExportFormat = "coco" | "yolo" | "voc" | "ls_json";
export type SplitName = "train" | "val" | "test";
export type MessageRole = "user" | "assistant" | "tool" | "system";

export interface Label {
  name: string;
  color: string;
}

export interface ChatMessage {
  role: MessageRole;
  content: string;
  tool_call_id: string | null;
  tool_name: string | null;
  created_at?: string;
}

export interface Project {
  id: number;
  name: string;
  source_folder: string;
  workspace_path: string;
  status: ProjectStatus;
  export_format: ExportFormat | null;
  train_ratio: number;
  val_ratio: number;
  test_ratio: number;
  labels: Label[];
  image_count: number;
  messages?: ChatMessage[];
}

export interface CreateProjectRequest {
  source_folder: string;
  name?: string;
  initial_labels?: string[];
  train_val_test?: [number, number, number];
  export_format?: ExportFormat;
}
```

- [ ] **Step 3: Create api/client.ts**

```typescript
// frontend/src/api/client.ts
import axios, { AxiosError } from "axios";

export const apiClient = axios.create({
  baseURL: "/api",
  timeout: 60_000,
});

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    detail?: Record<string, unknown>;
  };
}

export function unwrapError(err: unknown): { code: string; message: string } {
  if (err instanceof AxiosError && err.response?.data) {
    const body = err.response.data as ApiErrorBody;
    if (body.error) return { code: body.error.code, message: body.error.message };
  }
  return { code: "unknown", message: String(err) };
}
```

- [ ] **Step 4: Create api/projects.ts**

```typescript
// frontend/src/api/projects.ts
import { apiClient } from "./client";
import type { CreateProjectRequest, ExportFormat, Project } from "../types/project";

export async function createProject(req: CreateProjectRequest): Promise<Project> {
  const { data } = await apiClient.post<Project>("/projects", req);
  return data;
}

export async function getProject(pid: number): Promise<Project> {
  const { data } = await apiClient.get<Project>(`/projects/${pid}`);
  return data;
}

export async function patchFolder(pid: number, folder: string): Promise<Project> {
  const { data } = await apiClient.patch<Project>(`/projects/${pid}/folder`, { folder });
  return data;
}

export async function patchSplits(
  pid: number,
  train: number,
  val: number,
  test: number,
): Promise<Project> {
  const { data } = await apiClient.patch<Project>(`/projects/${pid}/splits`,
    { train, val, test });
  return data;
}

export async function patchFormat(pid: number, format: ExportFormat): Promise<Project> {
  const { data } = await apiClient.patch<Project>(`/projects/${pid}/format`, { format });
  return data;
}

export async function addLabel(
  pid: number,
  name: string,
  color?: string,
): Promise<{ id: number; name: string; color: string }> {
  const { data } = await apiClient.post(`/projects/${pid}/labels`, { name, color });
  return data;
}

export async function deleteLabel(pid: number, name: string): Promise<void> {
  await apiClient.delete(`/projects/${pid}/labels/${encodeURIComponent(name)}`);
}

export async function finalizeProject(pid: number): Promise<{ status: string; id: number }> {
  const { data } = await apiClient.post(`/projects/${pid}/finalize`);
  return data;
}
```

- [ ] **Step 5: Create api/chat.ts (SSE consumer)**

```typescript
// frontend/src/api/chat.ts
import type { ChatMessage } from "../types/project";

export type ChatEvent =
  | { type: "message"; data: ChatMessage }
  | { type: "done" };

export async function* streamChat(
  pid: number,
  content: string,
): AsyncGenerator<ChatEvent, void, unknown> {
  const resp = await fetch(`/api/projects/${pid}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!resp.ok || !resp.body) {
    throw new Error(`chat failed: ${resp.status}`);
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const chunk = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const line = chunk.trim();
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      try {
        const event = JSON.parse(payload) as ChatEvent;
        yield event;
        if (event.type === "done") return;
      } catch {
        // skip malformed
      }
    }
  }
}
```

- [ ] **Step 6: Verify TypeScript builds**

Run: `cd frontend && npm run build`
Expected: clean build with no type errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/types/ frontend/src/api/
git commit -m "feat(frontend): add types + axios client + SSE chat consumer"
```

---

## Task 20: Frontend — Card components (5)

**Files:**
- Create: `frontend/src/components/cards/FolderCard.tsx`
- Create: `frontend/src/components/cards/ImageInventoryCard.tsx`
- Create: `frontend/src/components/cards/SplitCard.tsx`
- Create: `frontend/src/components/cards/LabelsCard.tsx`
- Create: `frontend/src/components/cards/FormatCard.tsx`
- Create: `frontend/src/components/ui/Card.tsx`

- [ ] **Step 1: Create components/ui/Card.tsx (shared shell)**

```tsx
// frontend/src/components/ui/Card.tsx
import type { ReactNode } from "react";

interface Props {
  title: string;
  status?: "empty" | "filled" | "error";
  children: ReactNode;
}

export function Card({ title, status = "empty", children }: Props): JSX.Element {
  const borderColor = {
    empty: "#cbd5e0",
    filled: "#48bb78",
    error: "#e53e3e",
  }[status];
  return (
    <div
      style={{
        border: `1px solid ${borderColor}`,
        borderRadius: 8,
        padding: 16,
        marginBottom: 12,
        background: "white",
      }}
    >
      <h3 style={{ margin: "0 0 8px 0", fontSize: 14, fontWeight: 600 }}>{title}</h3>
      {children}
    </div>
  );
}
```

- [ ] **Step 2: Create FolderCard.tsx**

```tsx
// frontend/src/components/cards/FolderCard.tsx
import { useState } from "react";

import { patchFolder } from "../../api/projects";
import type { Project } from "../../types/project";
import { Card } from "../ui/Card";

interface Props {
  project: Project;
  onUpdated: (p: Project) => void;
}

export function FolderCard({ project, onUpdated }: Props): JSX.Element {
  const [value, setValue] = useState(project.source_folder);
  const [busy, setBusy] = useState(false);

  const status = project.source_folder ? "filled" : "empty";

  const submit = async (): Promise<void> => {
    if (!value || value === project.source_folder) return;
    setBusy(true);
    try {
      const updated = await patchFolder(project.id, value);
      onUpdated(updated);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title="源文件夹" status={status}>
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onBlur={submit}
        placeholder="/abs/path/to/images"
        disabled={busy}
        style={{ width: "100%", padding: 6, fontFamily: "monospace" }}
      />
    </Card>
  );
}
```

- [ ] **Step 3: Create ImageInventoryCard.tsx**

```tsx
// frontend/src/components/cards/ImageInventoryCard.tsx
import type { Project } from "../../types/project";
import { Card } from "../ui/Card";

interface Props {
  project: Project;
}

export function ImageInventoryCard({ project }: Props): JSX.Element {
  const status = project.image_count > 0 ? "filled" : "empty";
  return (
    <Card title="图像清单" status={status}>
      <div style={{ fontSize: 14 }}>
        总图像数：<b>{project.image_count}</b>
        <div style={{ marginTop: 4, color: "#718096", fontSize: 12 }}>
          扫描和整理由 Agent 执行 —— 在聊天里说"扫描这个文件夹"。
        </div>
      </div>
    </Card>
  );
}
```

- [ ] **Step 4: Create SplitCard.tsx**

```tsx
// frontend/src/components/cards/SplitCard.tsx
import { useState } from "react";

import { patchSplits } from "../../api/projects";
import type { Project } from "../../types/project";
import { Card } from "../ui/Card";

interface Props {
  project: Project;
  onUpdated: (p: Project) => void;
}

export function SplitCard({ project, onUpdated }: Props): JSX.Element {
  const [train, setTrain] = useState(project.train_ratio);
  const [val, setVal] = useState(project.val_ratio);
  const [test, setTest] = useState(project.test_ratio);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sum = train + val + test;
  const valid = Math.abs(sum - 1.0) < 1e-6;
  const status = valid ? "filled" : "error";

  const submit = async (): Promise<void> => {
    if (!valid || busy) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await patchSplits(project.id, train, val, test);
      onUpdated(updated);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title={`Train / Val / Test 切分 (sum=${sum.toFixed(3)})`} status={status}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
        {[
          { label: "train", value: train, set: setTrain },
          { label: "val", value: val, set: setVal },
          { label: "test", value: test, set: setTest },
        ].map(({ label, value, set }) => (
          <label key={label} style={{ fontSize: 12 }}>
            {label}
            <input
              type="number"
              step="0.05"
              min="0"
              max="1"
              value={value}
              onChange={(e) => set(parseFloat(e.target.value) || 0)}
              onBlur={submit}
              style={{ width: "100%", padding: 4 }}
            />
          </label>
        ))}
      </div>
      {error && <div style={{ color: "#e53e3e", fontSize: 12, marginTop: 4 }}>{error}</div>}
    </Card>
  );
}
```

- [ ] **Step 5: Create LabelsCard.tsx**

```tsx
// frontend/src/components/cards/LabelsCard.tsx
import { useState } from "react";

import { addLabel, deleteLabel } from "../../api/projects";
import type { Project } from "../../types/project";
import { Card } from "../ui/Card";

interface Props {
  project: Project;
  onUpdated: () => void; // refetch project
}

export function LabelsCard({ project, onUpdated }: Props): JSX.Element {
  const [newName, setNewName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const status = project.labels.length > 0 ? "filled" : "empty";
  const canDelete = project.status === "draft";

  const add = async (): Promise<void> => {
    if (!newName) return;
    setBusy(true);
    setError(null);
    try {
      await addLabel(project.id, newName);
      setNewName("");
      onUpdated();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (name: string): Promise<void> => {
    setBusy(true);
    try {
      await deleteLabel(project.id, name);
      onUpdated();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title={`标签集（${project.labels.length}）`} status={status}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {project.labels.map((l) => (
          <span
            key={l.name}
            style={{
              padding: "2px 8px",
              borderRadius: 12,
              background: l.color,
              color: "white",
              fontSize: 12,
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
            }}
          >
            {l.name}
            {canDelete && (
              <button
                onClick={() => remove(l.name)}
                disabled={busy}
                style={{
                  border: "none",
                  background: "rgba(0,0,0,0.2)",
                  color: "white",
                  borderRadius: 8,
                  width: 16,
                  height: 16,
                  cursor: "pointer",
                  fontSize: 10,
                }}
              >
                ×
              </button>
            )}
          </span>
        ))}
      </div>
      <div style={{ marginTop: 8, display: "flex", gap: 4 }}>
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") add();
          }}
          placeholder="加新标签 (按 Enter)"
          disabled={busy}
          style={{ flex: 1, padding: 4 }}
        />
        <button onClick={add} disabled={busy || !newName} style={{ padding: "4px 8px" }}>
          +
        </button>
      </div>
      {error && <div style={{ color: "#e53e3e", fontSize: 12, marginTop: 4 }}>{error}</div>}
    </Card>
  );
}
```

- [ ] **Step 6: Create FormatCard.tsx**

```tsx
// frontend/src/components/cards/FormatCard.tsx
import { patchFormat } from "../../api/projects";
import type { ExportFormat, Project } from "../../types/project";
import { Card } from "../ui/Card";

const FORMATS: ExportFormat[] = ["coco", "yolo", "voc", "ls_json"];

interface Props {
  project: Project;
  onUpdated: (p: Project) => void;
}

export function FormatCard({ project, onUpdated }: Props): JSX.Element {
  const status = project.export_format ? "filled" : "empty";
  const select = async (fmt: ExportFormat): Promise<void> => {
    const updated = await patchFormat(project.id, fmt);
    onUpdated(updated);
  };
  return (
    <Card title="导出格式" status={status}>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {FORMATS.map((fmt) => (
          <button
            key={fmt}
            onClick={() => select(fmt)}
            style={{
              padding: "4px 10px",
              border: "1px solid #cbd5e0",
              borderRadius: 4,
              background: project.export_format === fmt ? "#3182ce" : "white",
              color: project.export_format === fmt ? "white" : "#2d3748",
              cursor: "pointer",
            }}
          >
            {fmt.toUpperCase()}
          </button>
        ))}
      </div>
    </Card>
  );
}
```

- [ ] **Step 7: Verify build**

Run: `cd frontend && npm run build`
Expected: passes.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/cards/ frontend/src/components/ui/
git commit -m "feat(frontend): add 5 setup cards + Card shell component"
```

---

## Task 21: Frontend — ChatPanel + SSE consumer hook

**Files:**
- Create: `frontend/src/hooks/useChat.ts`
- Create: `frontend/src/components/ChatPanel.tsx`

- [ ] **Step 1: Create hooks/useChat.ts**

```typescript
// frontend/src/hooks/useChat.ts
import { useCallback, useState } from "react";

import { streamChat } from "../api/chat";
import type { ChatMessage } from "../types/project";

export function useChat(pid: number, initial: ChatMessage[]) {
  const [messages, setMessages] = useState<ChatMessage[]>(initial);
  const [sending, setSending] = useState(false);

  const send = useCallback(
    async (content: string): Promise<void> => {
      setMessages((prev) => [
        ...prev,
        { role: "user", content, tool_call_id: null, tool_name: null },
      ]);
      setSending(true);
      try {
        for await (const event of streamChat(pid, content)) {
          if (event.type === "message") {
            setMessages((prev) => [...prev, event.data]);
          } else if (event.type === "done") {
            break;
          }
        }
      } finally {
        setSending(false);
      }
    },
    [pid],
  );

  return { messages, sending, send, setMessages };
}
```

- [ ] **Step 2: Create components/ChatPanel.tsx**

```tsx
// frontend/src/components/ChatPanel.tsx
import { useEffect, useRef, useState } from "react";

import type { ChatMessage } from "../types/project";

interface Props {
  messages: ChatMessage[];
  sending: boolean;
  onSend: (content: string) => void;
}

export function ChatPanel({ messages, sending, onSend }: Props): JSX.Element {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const submit = (): void => {
    if (!input.trim() || sending) return;
    onSend(input.trim());
    setInput("");
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: "#f7fafc",
        borderLeft: "1px solid #e2e8f0",
      }}
    >
      <div
        ref={scrollRef}
        style={{ flex: 1, overflowY: "auto", padding: 12, fontSize: 13 }}
      >
        {messages.length === 0 && (
          <div style={{ color: "#a0aec0" }}>
            和 Agent 对话开始你的项目。试试："扫描 /path/to/images"
          </div>
        )}
        {messages.map((m, i) => (
          <ChatBubble key={i} m={m} />
        ))}
        {sending && (
          <div style={{ color: "#718096", fontStyle: "italic" }}>Agent 思考中…</div>
        )}
      </div>
      <div style={{ padding: 8, borderTop: "1px solid #e2e8f0", display: "flex", gap: 6 }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="对 Agent 说话…"
          disabled={sending}
          style={{ flex: 1, padding: 6 }}
        />
        <button onClick={submit} disabled={sending || !input.trim()}>
          发送
        </button>
      </div>
    </div>
  );
}

function ChatBubble({ m }: { m: ChatMessage }): JSX.Element {
  const colors = {
    user: { bg: "#3182ce", fg: "white", align: "flex-end" },
    assistant: { bg: "#e2e8f0", fg: "#2d3748", align: "flex-start" },
    tool: { bg: "#fefcbf", fg: "#5a4307", align: "flex-start" },
    system: { bg: "transparent", fg: "#a0aec0", align: "center" },
  } as const;
  const c = colors[m.role];
  return (
    <div style={{ display: "flex", justifyContent: c.align, marginBottom: 8 }}>
      <div
        style={{
          background: c.bg,
          color: c.fg,
          padding: "6px 10px",
          borderRadius: 8,
          maxWidth: "85%",
          fontFamily: m.role === "tool" ? "monospace" : "inherit",
          fontSize: m.role === "tool" ? 11 : 13,
          whiteSpace: "pre-wrap",
        }}
      >
        {m.role === "tool" && m.tool_name && (
          <div style={{ fontWeight: 700, opacity: 0.8 }}>{m.tool_name}</div>
        )}
        {m.content || (m.role === "assistant" ? "(调用工具中…)" : "")}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: passes.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/ frontend/src/components/ChatPanel.tsx
git commit -m "feat(frontend): add useChat SSE hook + ChatPanel component"
```

---

## Task 22: Frontend — SetupPage + routing + project creation entry

**Files:**
- Create: `frontend/src/pages/SetupPage.tsx`
- Create: `frontend/src/pages/HomePage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Create HomePage.tsx (entry to create a project)**

```tsx
// frontend/src/pages/HomePage.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { createProject } from "../api/projects";

export function HomePage(): JSX.Element {
  const [folder, setFolder] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const submit = async (): Promise<void> => {
    if (!folder.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const project = await createProject({ source_folder: folder.trim() });
      navigate(`/setup?project_id=${project.id}`);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "80px auto", padding: 24, fontFamily: "system-ui" }}>
      <h1>Echobox</h1>
      <p style={{ color: "#4a5568" }}>多模态智能标注 Agent 平台</p>
      <h2 style={{ fontSize: 16, marginTop: 32 }}>新建标注项目</h2>
      <input
        type="text"
        value={folder}
        onChange={(e) => setFolder(e.target.value)}
        placeholder="图片文件夹绝对路径"
        style={{ width: "100%", padding: 8, fontFamily: "monospace" }}
      />
      <button
        onClick={submit}
        disabled={busy || !folder.trim()}
        style={{ marginTop: 8, padding: "8px 16px" }}
      >
        {busy ? "创建中…" : "创建项目"}
      </button>
      {error && <div style={{ color: "#e53e3e", marginTop: 8 }}>{error}</div>}
    </div>
  );
}
```

- [ ] **Step 2: Create SetupPage.tsx**

```tsx
// frontend/src/pages/SetupPage.tsx
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { finalizeProject, getProject } from "../api/projects";
import { ChatPanel } from "../components/ChatPanel";
import { FolderCard } from "../components/cards/FolderCard";
import { FormatCard } from "../components/cards/FormatCard";
import { ImageInventoryCard } from "../components/cards/ImageInventoryCard";
import { LabelsCard } from "../components/cards/LabelsCard";
import { SplitCard } from "../components/cards/SplitCard";
import { useChat } from "../hooks/useChat";
import type { Project } from "../types/project";

export function SetupPage(): JSX.Element {
  const [searchParams] = useSearchParams();
  const pid = Number(searchParams.get("project_id"));
  const [project, setProject] = useState<Project | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [finalizeError, setFinalizeError] = useState<string | null>(null);

  const refetch = async (): Promise<void> => {
    if (!pid) return;
    try {
      const p = await getProject(pid);
      setProject(p);
    } catch (e) {
      setError(String(e));
    }
  };

  useEffect(() => {
    refetch();
  }, [pid]);

  const chat = useChat(pid, project?.messages ?? []);
  useEffect(() => {
    // Refetch project after each agent reply to sync cards
    if (chat.messages.length > 0 && !chat.sending) {
      refetch();
    }
  }, [chat.messages.length, chat.sending]);

  const finalize = async (): Promise<void> => {
    setFinalizeError(null);
    try {
      const res = await finalizeProject(pid);
      if (res.status === "ready") {
        window.location.href = `/annotate?project_id=${pid}`;
      }
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: { detail?: { errors?: string[] } } } } })
        .response?.data?.error?.detail?.errors?.join("; ") ?? String(e);
      setFinalizeError(msg);
    }
  };

  if (!pid) return <div style={{ padding: 24 }}>missing project_id</div>;
  if (error) return <div style={{ padding: 24, color: "#e53e3e" }}>{error}</div>;
  if (!project) return <div style={{ padding: 24 }}>loading…</div>;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", height: "100vh" }}>
      <div style={{ overflowY: "auto", padding: 24 }}>
        <header style={{ marginBottom: 16 }}>
          <h1 style={{ margin: 0, fontSize: 20 }}>{project.name}</h1>
          <span style={{ fontSize: 12, color: "#718096" }}>
            project_id={project.id} · status={project.status}
          </span>
        </header>
        <FolderCard project={project} onUpdated={setProject} />
        <ImageInventoryCard project={project} />
        <SplitCard project={project} onUpdated={setProject} />
        <LabelsCard project={project} onUpdated={refetch} />
        <FormatCard project={project} onUpdated={setProject} />
        <button
          onClick={finalize}
          disabled={project.status !== "draft"}
          style={{
            marginTop: 16,
            padding: "10px 20px",
            background: "#48bb78",
            color: "white",
            border: "none",
            borderRadius: 6,
            cursor: project.status === "draft" ? "pointer" : "not-allowed",
            fontSize: 14,
          }}
        >
          ▶ 开始标注
        </button>
        {finalizeError && (
          <div style={{ color: "#e53e3e", marginTop: 8 }}>{finalizeError}</div>
        )}
      </div>
      <ChatPanel messages={chat.messages} sending={chat.sending} onSend={chat.send} />
    </div>
  );
}
```

- [ ] **Step 3: Modify App.tsx with routing**

```tsx
// frontend/src/App.tsx
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { HomePage } from "./pages/HomePage";
import { SetupPage } from "./pages/SetupPage";

export default function App(): JSX.Element {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/setup" element={<SetupPage />} />
        <Route path="*" element={<div style={{ padding: 24 }}>404</div>} />
      </Routes>
    </BrowserRouter>
  );
}
```

- [ ] **Step 4: Verify build**

Run: `cd frontend && npm run build`
Expected: passes.

- [ ] **Step 5: Manual smoke test**

In one terminal: `make dev`
In browser: <http://127.0.0.1:5173/>
- See HomePage
- Type a folder path → click 创建 → redirected to /setup?project_id=N
- See 5 cards
- Type "scan this folder" in chat → see Agent reply (will fail without real API key but UI should render gracefully)

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/ frontend/src/App.tsx
git commit -m "feat(frontend): add HomePage + SetupPage + routing (cards + chat)"
```

---

## Task 23: End-to-end Phase 1 smoke test (recorded LLM)

**Files:**
- Create: `tests/e2e/test_phase1_setup.py`
- Create: `tests/e2e/__init__.py`

- [ ] **Step 1: Create tests/e2e/__init__.py**

```python
```

- [ ] **Step 2: Write the failing test**

```python
# tests/e2e/test_phase1_setup.py
"""End-to-end Phase 1: create project → drive setup via chat → finalize.

Uses a scripted fake LLM. No DashScope API call. No browser."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from PIL import Image


@pytest.fixture
def system(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path / "data"))

    src = tmp_path / "src"
    (src / "positive").mkdir(parents=True)
    (src / "negative").mkdir()
    for i in range(5):
        Image.new("RGB", (10, 10)).save(src / "positive" / f"p{i}.jpg", "JPEG")
        Image.new("RGB", (10, 10)).save(src / "negative" / f"n{i}.jpg", "JPEG")

    # Scripted LLM responses driving the full setup flow
    llm = MagicMock()
    llm.bind_tools = MagicMock(return_value=llm)
    llm.invoke = MagicMock(side_effect=[
        AIMessage(content="", tool_calls=[
            {"name": "scan_folder", "args": {"path": str(src)}, "id": "c1"}
        ]),
        AIMessage(content="", tool_calls=[
            {"name": "organize_images", "args": {}, "id": "c2"}
        ]),
        AIMessage(content="", tool_calls=[
            {"name": "propose_split",
             "args": {"train": 0.7, "val": 0.15, "test": 0.15, "seed": 42},
             "id": "c3"}
        ]),
        AIMessage(content="", tool_calls=[
            {"name": "set_labels", "args": {"labels": ["positive", "negative"]}, "id": "c4"}
        ]),
        AIMessage(content="", tool_calls=[
            {"name": "set_export_format", "args": {"fmt": "coco"}, "id": "c5"}
        ]),
        AIMessage(content="Setup complete. Click 开始标注."),
    ])

    from echobox_app import llm as llm_mod
    monkeypatch.setattr(llm_mod.factory, "build_chat_model", lambda settings: llm)

    from echobox_app.db.models import Base
    from echobox_app.db.session import make_engine
    from echobox_app.main import create_app

    app = create_app()
    Base.metadata.create_all(make_engine(f"sqlite:///{tmp_path}/db"))
    return TestClient(app), src, tmp_path


def test_full_phase1_flow(system) -> None:
    client, src, tmp_path = system
    pid = client.post("/api/projects", json={"source_folder": str(src)}).json()["id"]

    with client.stream("POST", f"/api/projects/{pid}/chat",
                        json={"content": f"scan {src} and set up everything"}) as resp:
        events = [line for line in resp.iter_lines() if line]

    # Verify all tool calls happened
    last = client.get(f"/api/projects/{pid}").json()
    tool_names = [m["tool_name"] for m in last["messages"] if m["role"] == "tool"]
    assert "scan_folder" in tool_names
    assert "organize_images" in tool_names
    assert "propose_split" in tool_names
    assert "set_labels" in tool_names
    assert "set_export_format" in tool_names

    # Workspace files written
    assert (tmp_path / "data" / "projects" / str(pid) / "data" / "image" / "00001.jpg").exists()
    assert (tmp_path / "data" / "projects" / str(pid) / "data" / "mapping.json").exists()
```

- [ ] **Step 3: Run test**

Run: `uv run pytest tests/e2e/test_phase1_setup.py -v`
Expected: PASS.

- [ ] **Step 4: Run full test suite**

Run: `make test`
Expected: all tests pass across all packages.

- [ ] **Step 5: Commit + tag**

```bash
git add tests/e2e/
git commit -m "test(e2e): add Phase 1 setup end-to-end test (scripted LLM, real workspace)"
git tag -a v0.0.2-phase1 -m "Plan 2 complete: Phase 1 conversational setup end-to-end"
git log --oneline | head -10
```

---

## Done Criteria

After all 23 tasks:

- [x] All 7 agent tools implemented + tested
- [x] LangGraph planner+executor loop with iteration cap
- [x] LLM factory (OpenAI-compatible)
- [x] REST: POST/GET projects, PATCH folder/splits/format, POST/DELETE labels, POST finalize, POST chat (SSE)
- [x] Frontend: HomePage + SetupPage with 5 cards + chat panel + finalize button
- [x] End-to-end test: chat-driven setup → workspace files written → finalize succeeds
- [x] `make test` all green
- [x] Git tag `v0.0.2-phase1`

## What's NOT in this plan (defer to Plan 3/4)

- Real GECO2 model loading (Plan 3)
- /predict_similar endpoint (Plan 3)
- AnnotatePage + react-konva canvas (Plan 3)
- Image / Annotation REST endpoints (Plan 3)
- Exporters (Plan 4)
- MCP server real tools (Plan 4)

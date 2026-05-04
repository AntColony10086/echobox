import json
from pathlib import Path

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
        entries=[
            ImageEntry(
                canonical="00001.jpg",
                source=Path("/orig/a.jpg"),
                sha256="abc",
                bytes=100,
                width=10,
                height=10,
            )
        ],
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
    wm.write_project_meta(
        {
            "id": 7,
            "name": "test",
            "status": "draft",
            "labels": [{"name": "crack", "color": "#000"}],
        }
    )

    meta = json.loads((wm.project_dir / "project.json").read_text())
    assert meta["id"] == 7
    assert meta["name"] == "test"

from pathlib import Path

import pytest
from echobox_app.agent.executor import execute_tool
from echobox_app.agent.state import AgentState
from echobox_app.workspace.manager import WorkspaceManager
from PIL import Image


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

    result = execute_tool(
        state, wm, "propose_split", {"train": 0.7, "val": 0.15, "test": 0.15, "seed": 42}
    )

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
    execute_tool(state, wm, "propose_split", {"train": 1.0, "val": 0.0, "test": 0.0, "seed": 42})
    execute_tool(state, wm, "set_labels", {"labels": ["crack"]})
    execute_tool(state, wm, "set_export_format", {"fmt": "coco"})

    result = execute_tool(state, wm, "finalize_setup", {})

    assert result["ok"] is True
    assert state.status == "ready"

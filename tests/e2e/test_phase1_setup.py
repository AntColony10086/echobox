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

    llm = MagicMock()
    llm.bind_tools = MagicMock(return_value=llm)
    llm.invoke = MagicMock(
        side_effect=[
            AIMessage(
                content="",
                tool_calls=[{"name": "scan_folder", "args": {"path": str(src)}, "id": "c1"}],
            ),
            AIMessage(content="", tool_calls=[{"name": "organize_images", "args": {}, "id": "c2"}]),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "propose_split",
                        "args": {"train": 0.7, "val": 0.15, "test": 0.15, "seed": 42},
                        "id": "c3",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "set_labels", "args": {"labels": ["positive", "negative"]}, "id": "c4"}
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[{"name": "set_export_format", "args": {"fmt": "coco"}, "id": "c5"}],
            ),
            AIMessage(content="Setup complete. Click 开始标注."),
        ]
    )

    import echobox_app.api.chat as chat_mod
    from echobox_app import llm as llm_mod

    monkeypatch.setattr(llm_mod.factory, "build_chat_model", lambda settings: llm)
    monkeypatch.setattr(chat_mod, "build_chat_model", lambda settings: llm)

    from echobox_app.db.models import Base
    from echobox_app.db.session import make_engine
    from echobox_app.main import create_app

    app = create_app()
    Base.metadata.create_all(make_engine(f"sqlite:///{tmp_path}/db"))
    return TestClient(app), src, tmp_path


def test_full_phase1_flow(system) -> None:
    client, src, tmp_path = system
    pid = client.post("/api/projects", json={"source_folder": str(src)}).json()["id"]

    with client.stream(
        "POST", f"/api/projects/{pid}/chat", json={"content": f"scan {src} and set up everything"}
    ) as resp:
        list(resp.iter_lines())

    last = client.get(f"/api/projects/{pid}").json()
    tool_names = [m["tool_name"] for m in last["messages"] if m["role"] == "tool"]
    assert "scan_folder" in tool_names
    assert "organize_images" in tool_names
    assert "propose_split" in tool_names
    assert "set_labels" in tool_names
    assert "set_export_format" in tool_names

    # WorkspaceManager appends "projects/{pid}" to its root, so chat.py now
    # passes root=settings.data_dir → workspace_dir = data_dir/projects/{pid}/...
    data_dir = tmp_path / "data"
    workspace_image_dir = data_dir / "projects" / str(pid) / "data" / "image"
    assert (workspace_image_dir / "00001.jpg").exists()
    mapping = data_dir / "projects" / str(pid) / "data" / "mapping.json"
    assert mapping.exists()

from pathlib import Path
from unittest.mock import MagicMock

from echobox_app.agent.graph import build_graph
from echobox_app.agent.state import AgentState
from echobox_app.domain.messages import Message
from echobox_app.workspace.manager import WorkspaceManager
from langchain_core.messages import AIMessage
from PIL import Image


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

    llm = _fake_llm_returning(
        [
            AIMessage(
                content="",
                tool_calls=[{"name": "propose_labels", "args": {}, "id": f"c{i}"}],
            )
            for i in range(50)
        ]
    )
    graph = build_graph(llm, max_iterations=5)

    out = graph.invoke({"state": state, "workspace": wm})

    assert any("iteration" in m.content.lower() for m in out["state"].messages[-3:])

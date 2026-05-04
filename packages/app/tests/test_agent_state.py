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
    assert d["messages"] == [
        {"role": "user", "content": "hi", "tool_call_id": None, "tool_name": None, "metadata": {}}
    ]

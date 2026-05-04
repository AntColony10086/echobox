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
    from echobox_app.api import chat as chat_mod

    monkeypatch.setattr(llm_mod.factory, "build_chat_model", lambda settings: fake_llm)
    monkeypatch.setattr(chat_mod, "build_chat_model", lambda settings: fake_llm)

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

    with client.stream("POST", f"/api/projects/{pid}/chat", json={"content": "hi"}) as resp:
        assert resp.status_code == 200
        events = [line for line in resp.iter_lines() if line]

    assert any("hello back" in e for e in events)


def test_chat_persists_messages(client_with_fake_llm) -> None:
    client, pid = client_with_fake_llm

    with client.stream("POST", f"/api/projects/{pid}/chat", json={"content": "hi"}) as resp:
        list(resp.iter_lines())

    proj = client.get(f"/api/projects/{pid}").json()
    roles = [m["role"] for m in proj["messages"]]
    assert "user" in roles
    assert "assistant" in roles

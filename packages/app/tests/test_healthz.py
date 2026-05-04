import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    from echobox_app.main import create_app

    return TestClient(create_app())


def test_healthz_returns_200_with_version(client: TestClient) -> None:
    resp = client.get("/healthz")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "echobox-app"
    assert body["version"] == "0.0.1"


def test_healthz_includes_db_check(client: TestClient) -> None:
    resp = client.get("/healthz")
    body = resp.json()

    assert "db" in body
    assert body["db"] in {"ok", "unreachable"}

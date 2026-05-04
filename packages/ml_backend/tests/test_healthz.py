import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    from echobox_ml.main import create_app

    return TestClient(create_app())


def test_healthz_returns_200(client: TestClient) -> None:
    resp = client.get("/healthz")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "echobox-ml"
    assert body["version"] == "0.0.1"
    assert body["model_loaded"] is False  # Plan 1 uses stub; Plan 3 wires real GECO2
    assert body["device"] in {"auto", "cuda", "mps", "cpu"}

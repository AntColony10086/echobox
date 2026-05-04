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
    resp = client.post(
        "/api/projects",
        json={
            "source_folder": str(src),
            "name": "my-project",
            "initial_labels": ["crack", "rust"],
            "train_val_test": [0.6, 0.2, 0.2],
            "export_format": "yolo",
        },
    )

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
    resp = client.post(
        "/api/projects",
        json={
            "source_folder": str(src),
            "train_val_test": [0.5, 0.3, 0.3],
        },
    )

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

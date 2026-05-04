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

    resp = client.patch(
        f"/api/projects/{pid}/splits",
        json={
            "train": 0.6,
            "val": 0.2,
            "test": 0.2,
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["train_ratio"] == 0.6
    assert body["val_ratio"] == 0.2


def test_patch_splits_rejects_bad_sum(client_with_project) -> None:
    client, pid, _ = client_with_project

    resp = client.patch(
        f"/api/projects/{pid}/splits",
        json={
            "train": 0.5,
            "val": 0.3,
            "test": 0.3,
        },
    )

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

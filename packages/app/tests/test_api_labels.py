from pathlib import Path

import pytest
from fastapi.testclient import TestClient


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
    pid = client.post("/api/projects", json={"source_folder": str(src)}).json()["id"]
    return client, pid


def test_add_label(client_with_project) -> None:
    client, pid = client_with_project

    resp = client.post(f"/api/projects/{pid}/labels", json={"name": "crack"})

    assert resp.status_code == 201
    assert resp.json()["name"] == "crack"
    assert resp.json()["color"].startswith("#")


def test_add_label_with_explicit_color(client_with_project) -> None:
    client, pid = client_with_project

    resp = client.post(f"/api/projects/{pid}/labels", json={"name": "rust", "color": "#ff0000"})

    assert resp.json()["color"] == "#ff0000"


def test_add_duplicate_label_409(client_with_project) -> None:
    client, pid = client_with_project
    client.post(f"/api/projects/{pid}/labels", json={"name": "crack"})

    resp = client.post(f"/api/projects/{pid}/labels", json={"name": "crack"})

    assert resp.status_code == 409


def test_add_invalid_label_name_400(client_with_project) -> None:
    client, pid = client_with_project

    resp = client.post(f"/api/projects/{pid}/labels", json={"name": "with space"})

    assert resp.status_code == 400


def test_delete_label_in_draft(client_with_project) -> None:
    client, pid = client_with_project
    client.post(f"/api/projects/{pid}/labels", json={"name": "crack"})

    resp = client.delete(f"/api/projects/{pid}/labels/crack")

    assert resp.status_code == 204


def test_delete_label_after_ready_403(client_with_project, monkeypatch, tmp_path) -> None:
    client, pid = client_with_project
    client.post(f"/api/projects/{pid}/labels", json={"name": "crack"})
    from echobox_app.db.session import make_engine, make_session_factory

    engine = make_engine(f"sqlite:///{tmp_path}/db")
    sf = make_session_factory(engine)
    with sf() as s:
        from echobox_app.db.models import Project

        p = s.get(Project, pid)
        assert p is not None
        p.status = "ready"
        s.commit()

    resp = client.delete(f"/api/projects/{pid}/labels/crack")

    assert resp.status_code == 403

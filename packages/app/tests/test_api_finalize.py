from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture
def client_ready_to_finalize(monkeypatch, tmp_path: Path):
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
    pid = client.post(
        "/api/projects",
        json={
            "source_folder": str(src),
            "initial_labels": ["crack"],
            "export_format": "coco",
        },
    ).json()["id"]

    from echobox_app.db.models import Image as DBImage
    from echobox_app.db.session import make_engine, make_session_factory

    engine = make_engine(f"sqlite:///{tmp_path}/db")
    sf = make_session_factory(engine)
    with sf() as s:
        s.add(
            DBImage(
                project_id=pid,
                filename="00001.jpg",
                abs_path=str(tmp_path / "00001.jpg"),
                width=10,
                height=10,
                split="train",
                index_in_project=0,
                source_path=str(src / "a.jpg"),
            )
        )
        s.commit()
    return client, pid


def test_finalize_succeeds(client_ready_to_finalize) -> None:
    client, pid = client_ready_to_finalize

    resp = client.post(f"/api/projects/{pid}/finalize")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"


def test_finalize_fails_without_labels(monkeypatch, tmp_path: Path) -> None:
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
    pid = client.post(
        "/api/projects",
        json={
            "source_folder": str(src),
            "export_format": "coco",
        },
    ).json()["id"]

    resp = client.post(f"/api/projects/{pid}/finalize")

    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "critic_failed"
    assert any("label" in e.lower() for e in body["error"]["detail"]["errors"])

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_images(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path))
    from echobox_app.db.models import Base, Image, Project
    from echobox_app.db.session import make_engine, make_session_factory
    from echobox_app.main import create_app

    app = create_app()
    Base.metadata.create_all(make_engine(f"sqlite:///{tmp_path}/db"))
    sf = make_session_factory(make_engine(f"sqlite:///{tmp_path}/db"))
    with sf() as s:
        p = Project(name="x", workspace_path=str(tmp_path), source_folder="x", status="ready")
        s.add(p)
        s.flush()
        for i in range(3):
            split = ["train", "val", "test"][i]
            s.add(
                Image(
                    project_id=p.id,
                    filename=f"{i + 1:05d}.jpg",
                    abs_path=f"/x/{i + 1:05d}.jpg",
                    width=10,
                    height=10,
                    split=split,
                    index_in_project=i,
                    source_path=f"/orig/{i}.jpg",
                )
            )
        s.commit()
        pid = p.id
    return TestClient(app), pid


def test_list_images_with_progress(client_with_images) -> None:
    client, pid = client_with_images

    resp = client.get(f"/api/projects/{pid}/images")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert body["progress"]["train"]["total"] == 1
    assert body["progress"]["train"]["annotated"] == 0


def test_get_single_image(client_with_images) -> None:
    client, pid = client_with_images
    img_id = client.get(f"/api/projects/{pid}/images").json()["items"][0]["id"]

    resp = client.get(f"/api/images/{img_id}")

    assert resp.status_code == 200
    assert resp.json()["filename"] == "00001.jpg"


def test_list_images_filter_by_split(client_with_images) -> None:
    client, pid = client_with_images

    resp = client.get(f"/api/projects/{pid}/images?split=val")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["split"] == "val"

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PILImage


@pytest.fixture
def client_with_real_image(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path))

    img_path = tmp_path / "test.jpg"
    PILImage.new("RGB", (50, 50), color=(123, 45, 67)).save(img_path, "JPEG")

    from echobox_app.db.models import Base, Image, Project
    from echobox_app.db.session import make_engine, make_session_factory
    from echobox_app.main import create_app

    engine = make_engine(f"sqlite:///{tmp_path}/db")
    Base.metadata.create_all(engine)
    sf = make_session_factory(engine)
    with sf() as s:
        p = Project(name="x", workspace_path=str(tmp_path), source_folder="/o", status="annotating")
        s.add(p)
        s.flush()
        s.add(
            Image(
                project_id=p.id,
                filename="test.jpg",
                abs_path=str(img_path),
                width=50,
                height=50,
                split="train",
                index_in_project=0,
                source_path="/o/t.jpg",
            )
        )
        s.commit()
        iid = p.images[0].id
    return TestClient(create_app()), iid


def test_get_image_file_returns_bytes(client_with_real_image) -> None:
    client, iid = client_with_real_image

    resp = client.get(f"/api/images/{iid}/file")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/")
    assert len(resp.content) > 100


def test_get_image_file_404_when_missing(client_with_real_image, tmp_path: Path) -> None:
    client, iid = client_with_real_image
    Path(client.get(f"/api/images/{iid}").json()["abs_path"]).unlink()

    resp = client.get(f"/api/images/{iid}/file")

    assert resp.status_code == 404

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PILImage


@pytest.fixture
def client_with_data(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path))

    img_path = tmp_path / "00001.jpg"
    PILImage.new("RGB", (100, 200)).save(img_path, "JPEG")

    from echobox_app.db.models import Annotation, Base, Image, Label, Project
    from echobox_app.db.session import make_engine, make_session_factory
    from echobox_app.main import create_app

    engine = make_engine(f"sqlite:///{tmp_path}/db")
    Base.metadata.create_all(engine)
    sf = make_session_factory(engine)
    with sf() as s:
        p = Project(
            name="proj",
            workspace_path=str(tmp_path / "ws"),
            source_folder="/orig",
            status="annotating",
            export_format="coco",
        )
        s.add(p)
        s.flush()
        lbl = Label(project_id=p.id, name="crack", color="#000")
        s.add(lbl)
        img = Image(
            project_id=p.id,
            filename="00001.jpg",
            abs_path=str(img_path),
            width=100,
            height=200,
            split="train",
            index_in_project=0,
            source_path="/orig/x.jpg",
        )
        s.add(img)
        s.flush()
        s.add(
            Annotation(
                image_id=img.id,
                label_id=lbl.id,
                x1=10,
                y1=20,
                x2=50,
                y2=60,
                score=0.9,
                source="user",
                version=1,
            )
        )
        s.commit()
        pid = p.id
    return TestClient(create_app()), pid


def test_export_creates_dir(client_with_data, tmp_path: Path) -> None:
    client, pid = client_with_data

    resp = client.post(f"/api/projects/{pid}/exports", json={"format": "coco"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["format"] == "coco"
    assert "output_dir" in body
    assert body["stats"]["total_images"] == 1
    assert Path(body["output_dir"]).exists()
    assert (Path(body["output_dir"]) / "train.json").exists()


def test_export_uses_project_default_format(client_with_data) -> None:
    client, pid = client_with_data

    resp = client.post(f"/api/projects/{pid}/exports", json={})

    assert resp.status_code == 200
    assert resp.json()["format"] == "coco"


def test_export_unknown_format_400(client_with_data) -> None:
    client, pid = client_with_data

    resp = client.post(f"/api/projects/{pid}/exports", json={"format": "kaggle"})

    assert resp.status_code == 400

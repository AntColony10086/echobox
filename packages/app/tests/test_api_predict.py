from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PILImage


@pytest.fixture
def system_with_image(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path))

    from echobox_app.db.models import Base, Image, Label, Project
    from echobox_app.db.session import make_engine, make_session_factory

    engine = make_engine(f"sqlite:///{tmp_path}/db")
    Base.metadata.create_all(engine)
    sf = make_session_factory(engine)

    img_path = tmp_path / "img.jpg"
    PILImage.new("RGB", (200, 100)).save(img_path, "JPEG")

    with sf() as s:
        p = Project(
            name="x", workspace_path=str(tmp_path), source_folder="/orig", status="annotating"
        )
        s.add(p)
        s.flush()
        s.add(Label(project_id=p.id, name="crack", color="#000"))
        s.add(
            Image(
                project_id=p.id,
                filename="img.jpg",
                abs_path=str(img_path),
                width=200,
                height=100,
                split="train",
                index_in_project=0,
                source_path="/orig/img.jpg",
            )
        )
        s.commit()
        ids = (p.id, p.images[0].id, p.labels[0].id)

    fake_ml = AsyncMock()
    fake_ml.predict_similar = AsyncMock(
        return_value={
            "predictions": [
                {"bbox": [10, 20, 50, 60], "score": 0.9},
                {"bbox": [70, 30, 110, 80], "score": 0.7},
            ],
            "exemplar_count": 1,
            "image_size": [200, 100],
            "elapsed_ms": 30,
        }
    )

    from echobox_app.main import create_app

    app = create_app()

    def _override_ml() -> object:
        return fake_ml

    from echobox_app.api import annotations as ann_mod

    app.dependency_overrides[ann_mod.ml_client_dep] = _override_ml

    return TestClient(app), ids, fake_ml


def test_predict_similar_persists_pending(system_with_image, tmp_path: Path) -> None:
    client, (pid, iid, lid), fake_ml = system_with_image

    resp = client.post(
        f"/api/projects/{pid}/images/{iid}/predict-similar",
        json={"label_id": lid, "exemplar_bbox": [0, 0, 100, 50]},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert len(body["created"]) == 2
    assert body["created"][0]["source"] == "geco2_pending"

    list_resp = client.get(f"/api/images/{iid}/annotations")
    annotations = list_resp.json()["items"]
    assert len(annotations) == 2


def test_predict_similar_replaces_old_pending(system_with_image) -> None:
    client, (pid, iid, lid), fake_ml = system_with_image

    client.post(
        f"/api/projects/{pid}/images/{iid}/predict-similar",
        json={"label_id": lid, "exemplar_bbox": [0, 0, 100, 50]},
    )
    fake_ml.predict_similar = AsyncMock(
        return_value={
            "predictions": [{"bbox": [50, 50, 99, 99], "score": 0.6}],
            "exemplar_count": 1,
            "image_size": [200, 100],
            "elapsed_ms": 20,
        }
    )
    resp2 = client.post(
        f"/api/projects/{pid}/images/{iid}/predict-similar",
        json={"label_id": lid, "exemplar_bbox": [0, 0, 100, 50]},
    )

    body = resp2.json()
    assert len(body["created"]) == 1

    list_resp = client.get(f"/api/images/{iid}/annotations")
    annotations = list_resp.json()["items"]
    pending = [a for a in annotations if a["source"] == "geco2_pending"]
    assert len(pending) == 1

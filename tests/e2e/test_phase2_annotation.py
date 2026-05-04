"""E2E Phase 2: image present → predict-similar → adjust → accept.

Mocks ml_backend (no GECO2 needed). Verifies REST integration end-to-end.
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PILImage


@pytest.fixture
def client(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path))

    img_path = tmp_path / "img.jpg"
    PILImage.new("RGB", (200, 100)).save(img_path, "JPEG")

    from echobox_app.db.models import Base, Image, Label, Project
    from echobox_app.db.session import make_engine, make_session_factory
    from echobox_app.main import create_app

    engine = make_engine(f"sqlite:///{tmp_path}/db")
    Base.metadata.create_all(engine)
    sf = make_session_factory(engine)
    with sf() as s:
        p = Project(name="x", workspace_path=str(tmp_path), source_folder="/o", status="annotating")
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
                source_path="/o/img.jpg",
            )
        )
        s.commit()
        ids = (p.id, p.images[0].id, p.labels[0].id)

    fake_ml = AsyncMock()
    fake_ml.predict_similar = AsyncMock(
        return_value={
            "predictions": [
                {"bbox": [10, 20, 50, 60], "score": 0.9},
                {"bbox": [70, 30, 110, 80], "score": 0.4},
            ],
            "exemplar_count": 1,
            "image_size": [200, 100],
            "elapsed_ms": 30,
        }
    )

    app = create_app()
    from echobox_app.api import annotations as ann_mod

    app.dependency_overrides[ann_mod.ml_client_dep] = lambda: fake_ml
    return TestClient(app), ids


def test_full_annotation_loop(client) -> None:
    c, (pid, iid, lid) = client

    r = c.post(
        f"/api/projects/{pid}/images/{iid}/predict-similar",
        json={"label_id": lid, "exemplar_bbox": [0, 0, 100, 50]},
    )
    assert r.status_code == 201
    created = r.json()["created"]
    assert len(created) == 2

    r = c.patch(f"/api/projects/{pid}/images/{iid}/annotations/bulk", json={"action": "accept_all"})
    assert r.json()["affected"] == 2

    annotations = c.get(f"/api/images/{iid}/annotations").json()["items"]
    assert all(a["source"] == "geco2_accepted" for a in annotations)

    a = annotations[0]
    r = c.put(
        f"/api/annotations/{a['id']}",
        json={"x1": 5, "y1": 5, "x2": 60, "y2": 70, "version": a["version"]},
    )
    assert r.status_code == 200
    assert r.json()["bbox"] == [5, 5, 60, 70]
    assert r.json()["source"] == "user_edited"

    r = c.delete(f"/api/annotations/{annotations[1]['id']}")
    assert r.status_code == 204

    list_resp = c.get(f"/api/projects/{pid}/images").json()
    assert list_resp["progress"]["train"]["annotated"] == 1

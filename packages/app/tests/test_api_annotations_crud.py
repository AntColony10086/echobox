from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_annotation(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path))

    from echobox_app.db.models import Annotation, Base, Image, Label, Project
    from echobox_app.db.session import make_engine, make_session_factory
    from echobox_app.main import create_app

    engine = make_engine(f"sqlite:///{tmp_path}/db")
    Base.metadata.create_all(engine)
    sf = make_session_factory(engine)
    with sf() as s:
        p = Project(name="x", workspace_path=str(tmp_path), source_folder="/o", status="annotating")
        s.add(p)
        s.flush()
        lbl = Label(project_id=p.id, name="crack", color="#000")
        s.add(lbl)
        img = Image(
            project_id=p.id,
            filename="i.jpg",
            abs_path="/x.jpg",
            width=10,
            height=10,
            split="train",
            index_in_project=0,
            source_path="/o/i.jpg",
        )
        s.add(img)
        s.flush()
        ann = Annotation(
            image_id=img.id,
            label_id=lbl.id,
            x1=10,
            y1=20,
            x2=50,
            y2=60,
            score=0.9,
            source="geco2_pending",
            version=1,
        )
        s.add(ann)
        s.commit()
        ids = (p.id, img.id, lbl.id, ann.id, ann.version)
    return TestClient(create_app()), ids


def test_put_updates_bbox_and_bumps_version(client_with_annotation) -> None:
    client, (pid, iid, lid, aid, ver) = client_with_annotation

    resp = client.put(
        f"/api/annotations/{aid}",
        json={
            "x1": 15,
            "y1": 25,
            "x2": 55,
            "y2": 65,
            "version": ver,
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["bbox"] == [15, 25, 55, 65]
    assert body["version"] == ver + 1
    assert body["source"] == "user_edited"


def test_put_with_stale_version_409(client_with_annotation) -> None:
    client, (pid, iid, lid, aid, ver) = client_with_annotation

    resp = client.put(
        f"/api/annotations/{aid}",
        json={
            "x1": 1,
            "y1": 2,
            "x2": 3,
            "y2": 4,
            "version": ver + 99,
        },
    )

    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "version_conflict"


def test_put_can_change_source_to_accepted(client_with_annotation) -> None:
    client, (pid, iid, lid, aid, ver) = client_with_annotation

    resp = client.put(
        f"/api/annotations/{aid}",
        json={
            "source": "geco2_accepted",
            "version": ver,
        },
    )

    assert resp.status_code == 200
    assert resp.json()["source"] == "geco2_accepted"


def test_delete(client_with_annotation) -> None:
    client, (pid, iid, lid, aid, ver) = client_with_annotation

    resp = client.delete(f"/api/annotations/{aid}")
    assert resp.status_code == 204

    list_resp = client.get(f"/api/images/{iid}/annotations")
    assert list_resp.json()["items"] == []


def test_bulk_accept_all(client_with_annotation) -> None:
    client, (pid, iid, lid, aid, ver) = client_with_annotation

    resp = client.patch(
        f"/api/projects/{pid}/images/{iid}/annotations/bulk",
        json={"action": "accept_all"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["affected"] == 1

    list_resp = client.get(f"/api/images/{iid}/annotations")
    assert list_resp.json()["items"][0]["source"] == "geco2_accepted"


def test_bulk_reject_all_deletes_pending(client_with_annotation) -> None:
    client, (pid, iid, lid, aid, ver) = client_with_annotation

    resp = client.patch(
        f"/api/projects/{pid}/images/{iid}/annotations/bulk",
        json={"action": "reject_all"},
    )

    assert resp.status_code == 200
    list_resp = client.get(f"/api/images/{iid}/annotations")
    assert list_resp.json()["items"] == []

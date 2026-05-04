from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture
def client_with_fake_runner(monkeypatch, tmp_path: Path) -> TestClient:
    # Clear weights env so create_app picks the stub branch (we override it below).
    monkeypatch.delenv("ECHOBOX_ML_GECO2_WEIGHTS", raising=False)

    from echobox_ml.main import create_app
    from echobox_ml.runner import Geco2RunnerStub, Prediction

    fake = MagicMock(spec=Geco2RunnerStub)
    fake.is_loaded = True
    fake.device = "cpu"
    fake.predict_similar = MagicMock(
        return_value=(
            [Prediction(bbox=(10, 20, 50, 60), score=0.9)],
            (200, 100),
            42,
        )
    )

    # Patch BOTH classes — main.py picks Geco2Runner when weights exist, Stub otherwise.
    monkeypatch.setattr("echobox_ml.main.Geco2RunnerStub", lambda **kwargs: fake)
    monkeypatch.setattr("echobox_ml.main.Geco2Runner", lambda **kwargs: fake)
    return TestClient(create_app())


def test_predict_returns_200(client_with_fake_runner, tmp_path: Path) -> None:
    img = tmp_path / "img.jpg"
    Image.new("RGB", (200, 100)).save(img, "JPEG")

    resp = client_with_fake_runner.post(
        "/predict_similar",
        json={
            "image_path": str(img),
            "exemplar_bbox": [0, 0, 100, 50],
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["predictions"][0]["bbox"] == [10, 20, 50, 60]
    assert body["predictions"][0]["score"] == 0.9
    assert body["image_size"] == [200, 100]
    assert body["elapsed_ms"] == 42


def test_predict_invalid_bbox_400(client_with_fake_runner) -> None:
    resp = client_with_fake_runner.post(
        "/predict_similar",
        json={
            "image_path": "/x.jpg",
            "exemplar_bbox": [100, 100, 50, 50],
        },
    )

    assert resp.status_code == 422


def test_predict_image_not_found_404(client_with_fake_runner) -> None:
    client_with_fake_runner.app.state.runner.predict_similar = MagicMock(
        side_effect=FileNotFoundError("nope")
    )

    resp = client_with_fake_runner.post(
        "/predict_similar",
        json={
            "image_path": "/does/not/exist.jpg",
            "exemplar_bbox": [0, 0, 100, 50],
        },
    )

    assert resp.status_code == 404
    assert resp.json()["error"] == "image_not_found"


def test_predict_inference_failure_500(client_with_fake_runner) -> None:
    client_with_fake_runner.app.state.runner.predict_similar = MagicMock(
        side_effect=RuntimeError("oom")
    )

    resp = client_with_fake_runner.post(
        "/predict_similar",
        json={
            "image_path": "/x.jpg",
            "exemplar_bbox": [0, 0, 100, 50],
        },
    )

    assert resp.status_code == 500
    assert resp.json()["error"] == "inference_failed"

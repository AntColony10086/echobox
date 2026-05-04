import pytest
from echobox_ml.schemas import Prediction, PredictRequest, PredictResponse


def test_predict_request_valid() -> None:
    req = PredictRequest(
        image_path="/abs/img.jpg",
        exemplar_bbox=[10, 20, 100, 200],
    )
    assert req.exemplar_bbox == (10, 20, 100, 200)
    assert req.max_predictions == 200
    assert req.score_threshold == 0.25


def test_predict_request_overrides() -> None:
    req = PredictRequest(
        image_path="/abs/img.jpg",
        exemplar_bbox=[1, 2, 3, 4],
        max_predictions=50,
        score_threshold=0.5,
    )
    assert req.max_predictions == 50
    assert req.score_threshold == 0.5


def test_predict_request_rejects_bbox_with_wrong_arity() -> None:
    with pytest.raises(ValueError):
        PredictRequest(image_path="/x", exemplar_bbox=[1, 2, 3])


def test_predict_request_rejects_inverted_bbox() -> None:
    with pytest.raises(ValueError):
        PredictRequest(image_path="/x", exemplar_bbox=[100, 100, 50, 50])


def test_prediction_serialization() -> None:
    p = Prediction(bbox=(10, 20, 100, 200), score=0.9)
    d = p.model_dump()
    assert d == {"bbox": [10, 20, 100, 200], "score": 0.9}


def test_predict_response_envelope() -> None:
    r = PredictResponse(
        predictions=[Prediction(bbox=(1, 2, 3, 4), score=0.5)],
        exemplar_count=1,
        image_size=(100, 200),
        elapsed_ms=42,
    )
    assert len(r.predictions) == 1
    assert r.elapsed_ms == 42

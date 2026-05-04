from echobox_ml.adapters import bbox_to_geco2_exemplar, geco2_outputs_to_predictions


def test_bbox_to_exemplar() -> None:
    out = bbox_to_geco2_exemplar((10, 20, 100, 200))
    assert out == {"bbox": [10, 20, 100, 200]}


def test_outputs_clip_into_image() -> None:
    boxes = [[10, 20, 50, 60], [-5, -5, 200, 200]]
    scores = [0.9, 0.5]
    res = geco2_outputs_to_predictions(boxes, scores, image_size=(100, 100))

    assert res[0] == ((10, 20, 50, 60), 0.9)
    assert res[1] == ((0, 0, 99, 99), 0.5)


def test_outputs_skip_zero_area() -> None:
    boxes = [[10, 10, 10, 10]]
    res = geco2_outputs_to_predictions(boxes, [0.9], image_size=(100, 100))

    assert res == []


def test_outputs_default_score_when_none() -> None:
    boxes = [[10, 20, 30, 40]]
    res = geco2_outputs_to_predictions(boxes, None, image_size=(100, 100))

    assert res[0][1] == 1.0

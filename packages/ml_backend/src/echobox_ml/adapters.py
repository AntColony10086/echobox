"""Convert between our (x1,y1,x2,y2) tuple bbox and GECO2's exemplar/output formats."""

from typing import Any


def bbox_to_geco2_exemplar(bbox: tuple[int, int, int, int]) -> dict[str, Any]:
    """GECO2 expects an exemplar dict with 'bbox': [x1,y1,x2,y2] in pixel coords."""
    return {"bbox": [int(c) for c in bbox]}


def geco2_outputs_to_predictions(
    raw_boxes: Any,
    raw_scores: Any | None,
    image_size: tuple[int, int],
) -> list[tuple[tuple[int, int, int, int], float]]:
    """Normalize GECO2 raw output into a list of (bbox_tuple, score) pairs."""
    width, height = image_size
    out: list[tuple[tuple[int, int, int, int], float]] = []
    for idx, box in enumerate(raw_boxes):
        x1, y1, x2, y2 = (float(box[0]), float(box[1]), float(box[2]), float(box[3]))
        x1 = max(0.0, min(x1, width - 1))
        y1 = max(0.0, min(y1, height - 1))
        x2 = max(0.0, min(x2, width - 1))
        y2 = max(0.0, min(y2, height - 1))
        if x2 - x1 < 1 or y2 - y1 < 1:
            continue
        score = float(raw_scores[idx]) if raw_scores is not None else 1.0
        out.append(((int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))), score))
    return out

import json
from datetime import datetime
from pathlib import Path

from echobox_app.db.models import Annotation, Image, Label
from echobox_app.exporters.base import ExportContext
from echobox_app.exporters.ls_json import LSJsonExporter


def _img(i: int, split: str) -> Image:
    return Image(
        id=i,
        project_id=1,
        filename=f"{i:05d}.jpg",
        abs_path=f"/x/{i:05d}.jpg",
        width=100,
        height=200,
        split=split,
        index_in_project=i - 1,
        source_path=f"/o/{i}.jpg",
    )


def test_ls_json_envelope(tmp_path: Path) -> None:
    crack = Label(id=1, project_id=1, name="crack", color="#000", created_at=datetime.now())
    img = _img(1, "train")
    ann = Annotation(
        id=10,
        image_id=1,
        label_id=1,
        x1=10,
        y1=20,
        x2=50,
        y2=60,
        score=0.9,
        source="user",
        version=1,
    )
    ann.label = crack

    ctx = ExportContext(
        project_id=1,
        project_name="t",
        workspace_path=tmp_path,
        export_dir=tmp_path / "out",
        labels=[("crack", "#000")],
        images=[img],
        annotations_by_image={1: [ann]},
        include_pending=False,
        splits=("train", "val", "test"),
    )

    LSJsonExporter().export(ctx)

    payload = json.loads((tmp_path / "out" / "train.json").read_text())
    assert len(payload) == 1
    task = payload[0]
    assert task["data"]["image"].endswith("00001.jpg")
    pred = task["annotations"][0]["result"][0]
    assert pred["type"] == "rectanglelabels"
    assert abs(pred["value"]["x"] - 10.0) < 0.1
    assert abs(pred["value"]["y"] - 10.0) < 0.1
    assert abs(pred["value"]["width"] - 40.0) < 0.1
    assert abs(pred["value"]["height"] - 20.0) < 0.1
    assert pred["value"]["rectanglelabels"] == ["crack"]

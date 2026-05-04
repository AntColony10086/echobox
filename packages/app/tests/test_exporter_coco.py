import json
from datetime import datetime
from pathlib import Path

from echobox_app.db.models import Annotation, Image, Label
from echobox_app.exporters.base import ExportContext
from echobox_app.exporters.coco import COCOExporter


def _make_image(iid: int, filename: str, split: str, w: int = 100, h: int = 100) -> Image:
    return Image(
        id=iid,
        project_id=1,
        filename=filename,
        abs_path=f"/x/{filename}",
        width=w,
        height=h,
        split=split,
        index_in_project=iid - 1,
        source_path=f"/o/{filename}",
    )


def _make_label(iid: int, name: str) -> Label:
    return Label(id=iid, project_id=1, name=name, color="#000", created_at=datetime.now())


def _make_ann(iid: int, image_id: int, label: Label, bbox: tuple[int, int, int, int]) -> Annotation:
    a = Annotation(
        id=iid,
        image_id=image_id,
        label_id=label.id,
        x1=bbox[0],
        y1=bbox[1],
        x2=bbox[2],
        y2=bbox[3],
        score=0.9,
        source="user",
        version=1,
    )
    a.label = label
    return a


def test_coco_writes_split_jsons(tmp_path: Path) -> None:
    label = _make_label(1, "crack")
    img1 = _make_image(1, "00001.jpg", "train")
    img2 = _make_image(2, "00002.jpg", "val")
    ann1 = _make_ann(10, 1, label, (10, 20, 50, 60))
    ann2 = _make_ann(11, 1, label, (60, 60, 90, 90))

    ctx = ExportContext(
        project_id=1,
        project_name="t",
        workspace_path=tmp_path,
        export_dir=tmp_path / "out",
        labels=[("crack", "#000")],
        images=[img1, img2],
        annotations_by_image={1: [ann1, ann2], 2: []},
        include_pending=False,
        splits=("train", "val", "test"),
    )

    stats = COCOExporter().export(ctx)

    train_json = json.loads((tmp_path / "out" / "train.json").read_text())
    assert len(train_json["images"]) == 1
    assert len(train_json["annotations"]) == 2
    assert train_json["categories"][0]["name"] == "crack"
    assert train_json["annotations"][0]["bbox"] == [10, 20, 40, 40]
    assert train_json["annotations"][0]["area"] == 1600

    val_json = json.loads((tmp_path / "out" / "val.json").read_text())
    assert len(val_json["images"]) == 1
    assert len(val_json["annotations"]) == 0

    assert stats.total_images == 2
    assert stats.total_annotations == 2
    assert stats.by_split["train"]["annotations"] == 2


def test_coco_skips_pending_when_excluded(tmp_path: Path) -> None:
    label = _make_label(1, "crack")
    img = _make_image(1, "00001.jpg", "train")
    a1 = _make_ann(10, 1, label, (1, 1, 5, 5))
    a1.source = "geco2_pending"
    a2 = _make_ann(11, 1, label, (10, 10, 30, 30))
    a2.source = "user"

    ctx = ExportContext(
        project_id=1,
        project_name="t",
        workspace_path=tmp_path,
        export_dir=tmp_path / "out",
        labels=[("crack", "#000")],
        images=[img],
        annotations_by_image={1: [a1, a2]},
        include_pending=False,
        splits=("train", "val", "test"),
    )

    COCOExporter().export(ctx)

    train_json = json.loads((tmp_path / "out" / "train.json").read_text())
    assert len(train_json["annotations"]) == 1

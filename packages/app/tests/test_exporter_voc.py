from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: N817

from echobox_app.db.models import Annotation, Image, Label
from echobox_app.exporters.base import ExportContext
from echobox_app.exporters.voc import VOCExporter


def _img(i: int, split: str, w: int = 100, h: int = 200) -> Image:
    return Image(
        id=i,
        project_id=1,
        filename=f"{i:05d}.jpg",
        abs_path=f"/x/{i:05d}.jpg",
        width=w,
        height=h,
        split=split,
        index_in_project=i - 1,
        source_path=f"/o/{i}.jpg",
    )


def _lbl(i: int, name: str) -> Label:
    return Label(id=i, project_id=1, name=name, color="#000", created_at=datetime.now())


def _ann(i: int, img_id: int, lbl: Label, bbox: tuple[int, int, int, int]) -> Annotation:
    a = Annotation(
        id=i,
        image_id=img_id,
        label_id=lbl.id,
        x1=bbox[0],
        y1=bbox[1],
        x2=bbox[2],
        y2=bbox[3],
        score=0.9,
        source="user",
        version=1,
    )
    a.label = lbl
    return a


def test_voc_writes_imagesets_and_xml(tmp_path: Path) -> None:
    label = _lbl(1, "crack")
    img1 = _img(1, "train")
    img2 = _img(2, "val")
    ann1 = _ann(10, 1, label, (10, 20, 50, 60))

    ctx = ExportContext(
        project_id=1,
        project_name="t",
        workspace_path=tmp_path,
        export_dir=tmp_path / "out",
        labels=[("crack", "#000")],
        images=[img1, img2],
        annotations_by_image={1: [ann1], 2: []},
        include_pending=False,
        splits=("train", "val", "test"),
    )

    VOCExporter().export(ctx)

    train_list = (tmp_path / "out" / "ImageSets" / "Main" / "train.txt").read_text().splitlines()
    assert train_list == ["00001"]
    val_list = (tmp_path / "out" / "ImageSets" / "Main" / "val.txt").read_text().splitlines()
    assert val_list == ["00002"]

    labels = (tmp_path / "out" / "labels.txt").read_text().splitlines()
    assert labels == ["crack"]

    xml = ET.parse(tmp_path / "out" / "Annotations" / "00001.xml").getroot()
    assert xml.findtext("filename") == "00001.jpg"
    assert xml.findtext("size/width") == "100"
    assert xml.findtext("size/height") == "200"
    obj = xml.find("object")
    assert obj is not None
    assert obj.findtext("name") == "crack"
    bb = obj.find("bndbox")
    assert bb is not None
    assert bb.findtext("xmin") == "10"
    assert bb.findtext("ymin") == "20"
    assert bb.findtext("xmax") == "50"
    assert bb.findtext("ymax") == "60"

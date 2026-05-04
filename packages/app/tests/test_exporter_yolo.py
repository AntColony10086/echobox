from datetime import datetime
from pathlib import Path

from echobox_app.db.models import Annotation, Image, Label
from echobox_app.exporters.base import ExportContext
from echobox_app.exporters.yolo import YOLOExporter


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


def test_yolo_writes_classes_and_split_dirs(tmp_path: Path) -> None:
    crack = _lbl(1, "crack")
    rust = _lbl(2, "rust")
    img1 = _img(1, "train")
    img2 = _img(2, "val")
    ann1 = _ann(10, 1, crack, (10, 20, 50, 60))
    ann2 = _ann(11, 1, rust, (60, 80, 80, 100))

    ctx = ExportContext(
        project_id=1,
        project_name="t",
        workspace_path=tmp_path,
        export_dir=tmp_path / "out",
        labels=[("crack", "#000"), ("rust", "#fff")],
        images=[img1, img2],
        annotations_by_image={1: [ann1, ann2], 2: []},
        include_pending=False,
        splits=("train", "val", "test"),
    )

    YOLOExporter().export(ctx)

    classes = (tmp_path / "out" / "classes.txt").read_text().splitlines()
    assert classes == ["crack", "rust"]

    label_file = (tmp_path / "out" / "train" / "labels" / "00001.txt").read_text().strip()
    lines = label_file.splitlines()
    assert len(lines) == 2
    parts = lines[0].split()
    assert parts[0] == "0"
    assert abs(float(parts[1]) - 30 / 100) < 1e-3
    assert abs(float(parts[2]) - 40 / 200) < 1e-3
    assert abs(float(parts[3]) - 40 / 100) < 1e-3
    assert abs(float(parts[4]) - 40 / 200) < 1e-3

    parts2 = lines[1].split()
    assert parts2[0] == "1"


def test_yolo_creates_image_symlinks(tmp_path: Path) -> None:
    img = _img(1, "train")
    img.abs_path = str(tmp_path / "src" / "00001.jpg")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "00001.jpg").write_bytes(b"fake")

    ctx = ExportContext(
        project_id=1,
        project_name="t",
        workspace_path=tmp_path,
        export_dir=tmp_path / "out",
        labels=[("crack", "#000")],
        images=[img],
        annotations_by_image={1: []},
        include_pending=False,
        splits=("train", "val", "test"),
    )

    YOLOExporter().export(ctx)

    assert (tmp_path / "out" / "train" / "images" / "00001.jpg").exists()

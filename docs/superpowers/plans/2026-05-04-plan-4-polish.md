# Plan 4 — Polish (Exporters, MCP, OSS Hygiene) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the platform OSS-publishable. After this plan: 4 export formats work end-to-end, MCP server exposes 3 real tools, README is polished, CI is green on every PR, and the v0.1.0 tag can be published.

**Architecture:** No new services. Adds exporters as pure-function modules in `app`, replaces MCP stub with 3 typed tools, fills out documentation, sets up GitHub Actions.

**Spec reference:** sections 6.4 (export formats), 7 (MCP), 8.5 (OSS hygiene) of `docs/superpowers/specs/2026-05-04-multimodal-annotation-agent-design.md`

**Prerequisite:** Plans 1 + 2 + 3 complete.

---

## File Structure (created in this plan)

```
packages/app/src/echobox_app/
├── exporters/
│   ├── __init__.py
│   ├── base.py                  # Exporter ABC + ExportContext
│   ├── coco.py
│   ├── yolo.py
│   ├── voc.py
│   ├── ls_json.py
│   └── registry.py              # name -> Exporter
└── api/
    └── exports.py               # POST /api/projects/{pid}/exports

packages/mcp_server/src/echobox_mcp/
├── tools/
│   ├── __init__.py
│   ├── start_project.py
│   ├── search_annotations.py
│   └── export_dataset.py
└── server.py                    # extended

# OSS hygiene additions:
README.md                        # full content
README_zh.md                     # full content
CONTRIBUTING.md
CODE_OF_CONDUCT.md
SECURITY.md
CHANGELOG.md
docs/architecture.md
docs/development.md
docs/api.md
docs/extending.md
.github/workflows/ci.yml
.github/workflows/release.yml
.github/ISSUE_TEMPLATE/bug_report.md
.github/ISSUE_TEMPLATE/feature_request.md
.github/PULL_REQUEST_TEMPLATE.md
```

---

## Task 1: Exporter base interface

**Files:**
- Create: `packages/app/src/echobox_app/exporters/__init__.py`
- Create: `packages/app/src/echobox_app/exporters/base.py`
- Create: `packages/app/tests/test_exporter_base.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_exporter_base.py
from pathlib import Path

from echobox_app.exporters.base import ExportContext, ExportStats, Exporter


def test_export_context_path_helpers(tmp_path: Path) -> None:
    ctx = ExportContext(
        project_id=7, project_name="test", workspace_path=tmp_path,
        export_dir=tmp_path / "exports" / "ts-coco",
        labels=[("crack", "#000")],
        images=[],
        annotations_by_image={},
        include_pending=False,
        splits=("train", "val", "test"),
    )
    assert ctx.symlink_image_dir.parent == ctx.export_dir


def test_export_stats_aggregation() -> None:
    s = ExportStats()
    s.add_image("train", 3)
    s.add_image("train", 5)
    s.add_image("val", 2)
    assert s.total_images == 3
    assert s.total_annotations == 10
    assert s.by_split["train"]["images"] == 2
    assert s.by_split["train"]["annotations"] == 8
```

- [ ] **Step 2: Run test, verify fail**

Run: `uv run pytest packages/app/tests/test_exporter_base.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement base.py**

```python
# packages/app/src/echobox_app/exporters/__init__.py
"""Dataset exporters for COCO/YOLO/VOC/Label Studio JSON."""
```

```python
# packages/app/src/echobox_app/exporters/base.py
"""Exporter ABC + shared types."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from echobox_app.db.models import Annotation, Image

SplitName = Literal["train", "val", "test"]


@dataclass
class ExportContext:
    project_id: int
    project_name: str
    workspace_path: Path
    export_dir: Path
    labels: list[tuple[str, str]]                          # [(name, color), ...]
    images: list[Image]
    annotations_by_image: dict[int, list[Annotation]]
    include_pending: bool
    splits: tuple[SplitName, ...]

    @property
    def symlink_image_dir(self) -> Path:
        return self.export_dir / "images"


@dataclass
class ExportStats:
    by_split: dict[str, dict[str, int]] = field(
        default_factory=lambda: {
            "train": {"images": 0, "annotations": 0},
            "val": {"images": 0, "annotations": 0},
            "test": {"images": 0, "annotations": 0},
        }
    )

    def add_image(self, split: str, n_annotations: int) -> None:
        self.by_split[split]["images"] += 1
        self.by_split[split]["annotations"] += n_annotations

    @property
    def total_images(self) -> int:
        return sum(s["images"] for s in self.by_split.values())

    @property
    def total_annotations(self) -> int:
        return sum(s["annotations"] for s in self.by_split.values())


class Exporter(ABC):
    name: str

    @abstractmethod
    def export(self, ctx: ExportContext) -> ExportStats: ...


def make_image_symlink(image: Image, target_dir: Path) -> Path:
    """Create a symlink (fallback to copy on Windows or symlink failure).

    Returns the destination path.
    """
    import shutil
    target_dir.mkdir(parents=True, exist_ok=True)
    dst = target_dir / image.filename
    if dst.exists():
        return dst
    src = Path(image.abs_path)
    try:
        dst.symlink_to(src)
    except (OSError, NotImplementedError):
        shutil.copy2(src, dst)
    return dst


def filter_annotations(
    annotations: list[Annotation],
    include_pending: bool,
) -> list[Annotation]:
    if include_pending:
        return list(annotations)
    return [a for a in annotations if a.source != "geco2_pending"]
```

- [ ] **Step 4: Run test, verify pass**

Run: `uv run pytest packages/app/tests/test_exporter_base.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/exporters/__init__.py \
        packages/app/src/echobox_app/exporters/base.py \
        packages/app/tests/test_exporter_base.py
git commit -m "feat(app): add Exporter ABC + ExportContext/ExportStats + symlink helper"
```

---

## Task 2: COCO exporter

**Files:**
- Create: `packages/app/src/echobox_app/exporters/coco.py`
- Create: `packages/app/tests/test_exporter_coco.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_exporter_coco.py
import json
from datetime import datetime
from pathlib import Path

from echobox_app.db.models import Annotation, Image, Label
from echobox_app.exporters.base import ExportContext
from echobox_app.exporters.coco import COCOExporter


def _make_image(id: int, filename: str, split: str, w: int = 100, h: int = 100) -> Image:
    return Image(
        id=id, project_id=1, filename=filename, abs_path=f"/x/{filename}",
        width=w, height=h, split=split, index_in_project=id - 1,
        source_path=f"/o/{filename}",
    )


def _make_label(id: int, name: str) -> Label:
    return Label(id=id, project_id=1, name=name, color="#000",
                 created_at=datetime.now())


def _make_ann(id: int, image_id: int, label: Label, bbox: tuple[int, int, int, int]) -> Annotation:
    a = Annotation(
        id=id, image_id=image_id, label_id=label.id,
        x1=bbox[0], y1=bbox[1], x2=bbox[2], y2=bbox[3],
        score=0.9, source="user", version=1,
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
        project_id=1, project_name="t", workspace_path=tmp_path,
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
    # COCO bbox is [x, y, w, h]
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
        project_id=1, project_name="t", workspace_path=tmp_path,
        export_dir=tmp_path / "out",
        labels=[("crack", "#000")], images=[img],
        annotations_by_image={1: [a1, a2]},
        include_pending=False,
        splits=("train", "val", "test"),
    )

    COCOExporter().export(ctx)

    train_json = json.loads((tmp_path / "out" / "train.json").read_text())
    assert len(train_json["annotations"]) == 1
```

- [ ] **Step 2: Run test, verify fail**

Run: `uv run pytest packages/app/tests/test_exporter_coco.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement coco.py**

```python
# packages/app/src/echobox_app/exporters/coco.py
"""Standard COCO instances format exporter."""
import json
from datetime import datetime, timezone
from typing import Any

from echobox_app.exporters.base import (
    ExportContext,
    ExportStats,
    Exporter,
    filter_annotations,
    make_image_symlink,
)


class COCOExporter(Exporter):
    name = "coco"

    def export(self, ctx: ExportContext) -> ExportStats:
        ctx.export_dir.mkdir(parents=True, exist_ok=True)
        stats = ExportStats()

        # Pre-build category list
        categories = [
            {"id": idx + 1, "name": name, "supercategory": "object"}
            for idx, (name, _color) in enumerate(ctx.labels)
        ]
        label_to_id = {name: idx + 1 for idx, (name, _) in enumerate(ctx.labels)}

        for split in ctx.splits:
            split_images = [img for img in ctx.images if img.split == split]
            payload: dict[str, Any] = {
                "info": {
                    "description": f"Echobox export for project {ctx.project_id}",
                    "date_created": datetime.now(timezone.utc).isoformat(),
                },
                "licenses": [{"id": 1, "name": "Apache-2.0"}],
                "images": [],
                "annotations": [],
                "categories": categories,
            }

            ann_id_seq = 1
            for img in split_images:
                make_image_symlink(img, ctx.symlink_image_dir)
                payload["images"].append({
                    "id": img.id,
                    "file_name": img.filename,
                    "width": img.width,
                    "height": img.height,
                    "license": 1,
                })
                anns = filter_annotations(
                    ctx.annotations_by_image.get(img.id, []),
                    ctx.include_pending,
                )
                for ann in anns:
                    w = ann.x2 - ann.x1
                    h = ann.y2 - ann.y1
                    payload["annotations"].append({
                        "id": ann_id_seq,
                        "image_id": img.id,
                        "category_id": label_to_id[ann.label.name],
                        "bbox": [ann.x1, ann.y1, w, h],
                        "area": w * h,
                        "iscrowd": 0,
                        "score": ann.score,
                        "_source": ann.source,
                    })
                    ann_id_seq += 1
                stats.add_image(split, len(anns))

            (ctx.export_dir / f"{split}.json").write_text(
                json.dumps(payload, indent=2, ensure_ascii=False)
            )

        return stats
```

- [ ] **Step 4: Run test, verify pass**

Run: `uv run pytest packages/app/tests/test_exporter_coco.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/exporters/coco.py packages/app/tests/test_exporter_coco.py
git commit -m "feat(app): add COCO exporter (per-split JSON + symlinked images)"
```

---

## Task 3: YOLO exporter

**Files:**
- Create: `packages/app/src/echobox_app/exporters/yolo.py`
- Create: `packages/app/tests/test_exporter_yolo.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_exporter_yolo.py
from datetime import datetime
from pathlib import Path

from echobox_app.db.models import Annotation, Image, Label
from echobox_app.exporters.base import ExportContext
from echobox_app.exporters.yolo import YOLOExporter


def _img(i: int, split: str) -> Image:
    return Image(id=i, project_id=1, filename=f"{i:05d}.jpg",
                 abs_path=f"/x/{i:05d}.jpg",
                 width=100, height=200, split=split, index_in_project=i - 1,
                 source_path=f"/o/{i}.jpg")


def _lbl(i: int, name: str) -> Label:
    return Label(id=i, project_id=1, name=name, color="#000",
                 created_at=datetime.now())


def _ann(i: int, img_id: int, lbl: Label, bbox: tuple[int, int, int, int]) -> Annotation:
    a = Annotation(
        id=i, image_id=img_id, label_id=lbl.id,
        x1=bbox[0], y1=bbox[1], x2=bbox[2], y2=bbox[3],
        score=0.9, source="user", version=1,
    )
    a.label = lbl
    return a


def test_yolo_writes_classes_and_split_dirs(tmp_path: Path) -> None:
    crack = _lbl(1, "crack")
    rust = _lbl(2, "rust")
    img1 = _img(1, "train")
    img2 = _img(2, "val")
    ann1 = _ann(10, 1, crack, (10, 20, 50, 60))   # cx=30 cy=40 w=40 h=40
    ann2 = _ann(11, 1, rust, (60, 80, 80, 100))   # cx=70 cy=90 w=20 h=20

    ctx = ExportContext(
        project_id=1, project_name="t", workspace_path=tmp_path,
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
    # YOLO: <cls_id> <cx_norm> <cy_norm> <w_norm> <h_norm>
    parts = lines[0].split()
    assert parts[0] == "0"  # crack
    assert abs(float(parts[1]) - 30 / 100) < 1e-3  # cx / W
    assert abs(float(parts[2]) - 40 / 200) < 1e-3  # cy / H
    assert abs(float(parts[3]) - 40 / 100) < 1e-3
    assert abs(float(parts[4]) - 40 / 200) < 1e-3

    parts2 = lines[1].split()
    assert parts2[0] == "1"  # rust


def test_yolo_creates_image_symlinks(tmp_path: Path) -> None:
    img = _img(1, "train")
    img.abs_path = str(tmp_path / "src" / "00001.jpg")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "00001.jpg").write_bytes(b"fake")

    ctx = ExportContext(
        project_id=1, project_name="t", workspace_path=tmp_path,
        export_dir=tmp_path / "out",
        labels=[("crack", "#000")], images=[img],
        annotations_by_image={1: []},
        include_pending=False,
        splits=("train", "val", "test"),
    )

    YOLOExporter().export(ctx)

    assert (tmp_path / "out" / "train" / "images" / "00001.jpg").exists()
```

- [ ] **Step 2: Run test, verify fail**

Run: `uv run pytest packages/app/tests/test_exporter_yolo.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement yolo.py**

```python
# packages/app/src/echobox_app/exporters/yolo.py
"""YOLO format exporter (per-image .txt files, normalized cx/cy/w/h)."""
from echobox_app.exporters.base import (
    ExportContext,
    ExportStats,
    Exporter,
    filter_annotations,
    make_image_symlink,
)


class YOLOExporter(Exporter):
    name = "yolo"

    def export(self, ctx: ExportContext) -> ExportStats:
        ctx.export_dir.mkdir(parents=True, exist_ok=True)
        stats = ExportStats()

        label_to_idx = {name: idx for idx, (name, _) in enumerate(ctx.labels)}
        (ctx.export_dir / "classes.txt").write_text(
            "\n".join(name for name, _ in ctx.labels) + "\n"
        )

        for split in ctx.splits:
            split_dir = ctx.export_dir / split
            (split_dir / "images").mkdir(parents=True, exist_ok=True)
            (split_dir / "labels").mkdir(parents=True, exist_ok=True)

            split_images = [img for img in ctx.images if img.split == split]
            for img in split_images:
                make_image_symlink(img, split_dir / "images")
                anns = filter_annotations(
                    ctx.annotations_by_image.get(img.id, []),
                    ctx.include_pending,
                )
                lines: list[str] = []
                for ann in anns:
                    cls_idx = label_to_idx[ann.label.name]
                    cx = (ann.x1 + ann.x2) / 2.0 / img.width
                    cy = (ann.y1 + ann.y2) / 2.0 / img.height
                    w = (ann.x2 - ann.x1) / img.width
                    h = (ann.y2 - ann.y1) / img.height
                    lines.append(f"{cls_idx} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
                txt_name = img.filename.rsplit(".", 1)[0] + ".txt"
                (split_dir / "labels" / txt_name).write_text("\n".join(lines))
                stats.add_image(split, len(anns))

        return stats
```

- [ ] **Step 4: Run test, verify pass**

Run: `uv run pytest packages/app/tests/test_exporter_yolo.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/exporters/yolo.py packages/app/tests/test_exporter_yolo.py
git commit -m "feat(app): add YOLO exporter (per-image .txt + classes.txt + symlinks)"
```

---

## Task 4: VOC exporter

**Files:**
- Create: `packages/app/src/echobox_app/exporters/voc.py`
- Create: `packages/app/tests/test_exporter_voc.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_exporter_voc.py
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from echobox_app.db.models import Annotation, Image, Label
from echobox_app.exporters.base import ExportContext
from echobox_app.exporters.voc import VOCExporter


def _img(i: int, split: str, w: int = 100, h: int = 200) -> Image:
    return Image(id=i, project_id=1, filename=f"{i:05d}.jpg",
                 abs_path=f"/x/{i:05d}.jpg",
                 width=w, height=h, split=split, index_in_project=i - 1,
                 source_path=f"/o/{i}.jpg")


def _lbl(i: int, name: str) -> Label:
    return Label(id=i, project_id=1, name=name, color="#000",
                 created_at=datetime.now())


def _ann(i: int, img_id: int, lbl: Label, bbox: tuple[int, int, int, int]) -> Annotation:
    a = Annotation(
        id=i, image_id=img_id, label_id=lbl.id,
        x1=bbox[0], y1=bbox[1], x2=bbox[2], y2=bbox[3],
        score=0.9, source="user", version=1,
    )
    a.label = lbl
    return a


def test_voc_writes_imagesets_and_xml(tmp_path: Path) -> None:
    label = _lbl(1, "crack")
    img1 = _img(1, "train")
    img2 = _img(2, "val")
    ann1 = _ann(10, 1, label, (10, 20, 50, 60))

    ctx = ExportContext(
        project_id=1, project_name="t", workspace_path=tmp_path,
        export_dir=tmp_path / "out",
        labels=[("crack", "#000")], images=[img1, img2],
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
```

- [ ] **Step 2: Run test, verify fail**

Run: `uv run pytest packages/app/tests/test_exporter_voc.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement voc.py**

```python
# packages/app/src/echobox_app/exporters/voc.py
"""Pascal VOC format exporter (per-image XML + ImageSets/Main split lists)."""
from xml.etree import ElementTree as ET

from echobox_app.exporters.base import (
    ExportContext,
    ExportStats,
    Exporter,
    filter_annotations,
    make_image_symlink,
)


class VOCExporter(Exporter):
    name = "voc"

    def export(self, ctx: ExportContext) -> ExportStats:
        ctx.export_dir.mkdir(parents=True, exist_ok=True)
        (ctx.export_dir / "Annotations").mkdir(exist_ok=True)
        (ctx.export_dir / "JPEGImages").mkdir(exist_ok=True)
        sets_dir = ctx.export_dir / "ImageSets" / "Main"
        sets_dir.mkdir(parents=True, exist_ok=True)

        (ctx.export_dir / "labels.txt").write_text(
            "\n".join(name for name, _ in ctx.labels) + "\n"
        )

        stats = ExportStats()
        for split in ctx.splits:
            split_images = [img for img in ctx.images if img.split == split]
            stem_list: list[str] = []
            for img in split_images:
                make_image_symlink(img, ctx.export_dir / "JPEGImages")
                stem = img.filename.rsplit(".", 1)[0]
                stem_list.append(stem)
                anns = filter_annotations(
                    ctx.annotations_by_image.get(img.id, []),
                    ctx.include_pending,
                )
                _write_voc_xml(ctx.export_dir / "Annotations" / f"{stem}.xml",
                               img, anns)
                stats.add_image(split, len(anns))
            (sets_dir / f"{split}.txt").write_text("\n".join(stem_list) + "\n" if stem_list else "")

        return stats


def _write_voc_xml(path, image, annotations) -> None:  # type: ignore[no-untyped-def]
    root = ET.Element("annotation")
    ET.SubElement(root, "filename").text = image.filename
    sz = ET.SubElement(root, "size")
    ET.SubElement(sz, "width").text = str(image.width)
    ET.SubElement(sz, "height").text = str(image.height)
    ET.SubElement(sz, "depth").text = "3"
    for ann in annotations:
        obj = ET.SubElement(root, "object")
        ET.SubElement(obj, "name").text = ann.label.name
        ET.SubElement(obj, "difficult").text = "0"
        bb = ET.SubElement(obj, "bndbox")
        ET.SubElement(bb, "xmin").text = str(ann.x1)
        ET.SubElement(bb, "ymin").text = str(ann.y1)
        ET.SubElement(bb, "xmax").text = str(ann.x2)
        ET.SubElement(bb, "ymax").text = str(ann.y2)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
```

- [ ] **Step 4: Run test, verify pass**

Run: `uv run pytest packages/app/tests/test_exporter_voc.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/exporters/voc.py packages/app/tests/test_exporter_voc.py
git commit -m "feat(app): add Pascal VOC exporter"
```

---

## Task 5: ls_json exporter (Label Studio JSON)

**Files:**
- Create: `packages/app/src/echobox_app/exporters/ls_json.py`
- Create: `packages/app/tests/test_exporter_ls_json.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_exporter_ls_json.py
import json
from datetime import datetime
from pathlib import Path

from echobox_app.db.models import Annotation, Image, Label
from echobox_app.exporters.base import ExportContext
from echobox_app.exporters.ls_json import LSJsonExporter


def _img(i: int, split: str) -> Image:
    return Image(id=i, project_id=1, filename=f"{i:05d}.jpg",
                 abs_path=f"/x/{i:05d}.jpg",
                 width=100, height=200, split=split, index_in_project=i - 1,
                 source_path=f"/o/{i}.jpg")


def test_ls_json_envelope(tmp_path: Path) -> None:
    crack = Label(id=1, project_id=1, name="crack", color="#000", created_at=datetime.now())
    img = _img(1, "train")
    ann = Annotation(id=10, image_id=1, label_id=1,
                     x1=10, y1=20, x2=50, y2=60,
                     score=0.9, source="user", version=1)
    ann.label = crack

    ctx = ExportContext(
        project_id=1, project_name="t", workspace_path=tmp_path,
        export_dir=tmp_path / "out",
        labels=[("crack", "#000")], images=[img],
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
    # LS uses percentage-based coords
    assert abs(pred["value"]["x"] - 10.0) < 0.1     # 10/100 * 100 = 10
    assert abs(pred["value"]["y"] - 10.0) < 0.1     # 20/200 * 100 = 10
    assert abs(pred["value"]["width"] - 40.0) < 0.1
    assert abs(pred["value"]["height"] - 20.0) < 0.1
    assert pred["value"]["rectanglelabels"] == ["crack"]
```

- [ ] **Step 2: Run test, verify fail**

Run: `uv run pytest packages/app/tests/test_exporter_ls_json.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement ls_json.py**

```python
# packages/app/src/echobox_app/exporters/ls_json.py
"""Label Studio JSON export (rectanglelabels with percent coords)."""
import json
import uuid

from echobox_app.exporters.base import (
    ExportContext,
    ExportStats,
    Exporter,
    filter_annotations,
    make_image_symlink,
)


class LSJsonExporter(Exporter):
    name = "ls_json"

    def export(self, ctx: ExportContext) -> ExportStats:
        ctx.export_dir.mkdir(parents=True, exist_ok=True)
        stats = ExportStats()

        for split in ctx.splits:
            tasks: list[dict[str, object]] = []
            split_images = [img for img in ctx.images if img.split == split]
            for img in split_images:
                make_image_symlink(img, ctx.symlink_image_dir)
                anns = filter_annotations(
                    ctx.annotations_by_image.get(img.id, []),
                    ctx.include_pending,
                )
                results = [
                    {
                        "id": str(uuid.uuid4())[:8],
                        "type": "rectanglelabels",
                        "from_name": "label",
                        "to_name": "image",
                        "image_rotation": 0,
                        "original_width": img.width,
                        "original_height": img.height,
                        "value": {
                            "x": (ann.x1 / img.width) * 100,
                            "y": (ann.y1 / img.height) * 100,
                            "width": ((ann.x2 - ann.x1) / img.width) * 100,
                            "height": ((ann.y2 - ann.y1) / img.height) * 100,
                            "rotation": 0,
                            "rectanglelabels": [ann.label.name],
                        },
                    }
                    for ann in anns
                ]
                tasks.append({
                    "data": {"image": f"images/{img.filename}"},
                    "annotations": [{"result": results}] if results else [],
                })
                stats.add_image(split, len(anns))
            (ctx.export_dir / f"{split}.json").write_text(
                json.dumps(tasks, indent=2, ensure_ascii=False)
            )
        return stats
```

- [ ] **Step 4: Run test, verify pass**

Run: `uv run pytest packages/app/tests/test_exporter_ls_json.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/exporters/ls_json.py \
        packages/app/tests/test_exporter_ls_json.py
git commit -m "feat(app): add Label Studio JSON exporter (rectanglelabels with %coords)"
```

---

## Task 6: Exporter registry

**Files:**
- Create: `packages/app/src/echobox_app/exporters/registry.py`
- Create: `packages/app/tests/test_exporter_registry.py`

- [ ] **Step 1: Write failing test**

```python
# packages/app/tests/test_exporter_registry.py
import pytest

from echobox_app.exporters.coco import COCOExporter
from echobox_app.exporters.registry import EXPORTERS, get_exporter


def test_all_4_registered() -> None:
    assert set(EXPORTERS.keys()) == {"coco", "yolo", "voc", "ls_json"}


def test_get_exporter_returns_instance() -> None:
    e = get_exporter("coco")
    assert isinstance(e, COCOExporter)


def test_get_unknown_raises() -> None:
    with pytest.raises(ValueError):
        get_exporter("kaggle")
```

- [ ] **Step 2: Run, verify fail.** `uv run pytest packages/app/tests/test_exporter_registry.py -v`

- [ ] **Step 3: Implement registry.py**

```python
# packages/app/src/echobox_app/exporters/registry.py
from echobox_app.exporters.base import Exporter
from echobox_app.exporters.coco import COCOExporter
from echobox_app.exporters.ls_json import LSJsonExporter
from echobox_app.exporters.voc import VOCExporter
from echobox_app.exporters.yolo import YOLOExporter

EXPORTERS: dict[str, type[Exporter]] = {
    "coco": COCOExporter,
    "yolo": YOLOExporter,
    "voc": VOCExporter,
    "ls_json": LSJsonExporter,
}


def get_exporter(name: str) -> Exporter:
    if name not in EXPORTERS:
        raise ValueError(f"unknown exporter: {name!r} (valid: {sorted(EXPORTERS)})")
    return EXPORTERS[name]()
```

- [ ] **Step 4: Run, verify pass.**

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/exporters/registry.py packages/app/tests/test_exporter_registry.py
git commit -m "feat(app): add exporter registry (name -> Exporter)"
```

---

## Task 7: REST — POST /api/projects/{pid}/exports

**Files:**
- Create: `packages/app/src/echobox_app/api/exports.py`
- Modify: `packages/app/src/echobox_app/main.py`
- Create: `packages/app/tests/test_api_exports.py`

- [ ] **Step 1: Write failing test**

```python
# packages/app/tests/test_api_exports.py
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PILImage


@pytest.fixture
def client_with_data(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DB_URL", f"sqlite:///{tmp_path}/db")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path))

    img_path = tmp_path / "00001.jpg"
    PILImage.new("RGB", (100, 200)).save(img_path, "JPEG")

    from echobox_app.db.models import Annotation, Base, Image, Label, Project
    from echobox_app.db.session import make_engine, make_session_factory
    from echobox_app.main import create_app

    engine = make_engine(f"sqlite:///{tmp_path}/db")
    Base.metadata.create_all(engine)
    sf = make_session_factory(engine)
    with sf() as s:
        p = Project(name="proj", workspace_path=str(tmp_path / "ws"),
                    source_folder="/orig", status="annotating",
                    export_format="coco")
        s.add(p)
        s.flush()
        l = Label(project_id=p.id, name="crack", color="#000")
        s.add(l)
        img = Image(project_id=p.id, filename="00001.jpg",
                    abs_path=str(img_path), width=100, height=200,
                    split="train", index_in_project=0, source_path="/orig/x.jpg")
        s.add(img)
        s.flush()
        s.add(Annotation(image_id=img.id, label_id=l.id,
                         x1=10, y1=20, x2=50, y2=60,
                         score=0.9, source="user", version=1))
        s.commit()
        pid = p.id
    return TestClient(create_app()), pid


def test_export_creates_dir(client_with_data, tmp_path: Path) -> None:
    client, pid = client_with_data

    resp = client.post(f"/api/projects/{pid}/exports", json={"format": "coco"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["format"] == "coco"
    assert "output_dir" in body
    assert body["stats"]["total_images"] == 1
    assert Path(body["output_dir"]).exists()
    assert (Path(body["output_dir"]) / "train.json").exists()


def test_export_uses_project_default_format(client_with_data) -> None:
    client, pid = client_with_data

    resp = client.post(f"/api/projects/{pid}/exports", json={})

    assert resp.status_code == 200
    assert resp.json()["format"] == "coco"


def test_export_unknown_format_400(client_with_data) -> None:
    client, pid = client_with_data

    resp = client.post(f"/api/projects/{pid}/exports", json={"format": "kaggle"})

    assert resp.status_code == 400
```

- [ ] **Step 2: Run, verify fail.** `uv run pytest packages/app/tests/test_api_exports.py -v`

- [ ] **Step 3: Implement api/exports.py**

```python
# packages/app/src/echobox_app/api/exports.py
"""POST /api/projects/{pid}/exports — produce a dataset export folder."""
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from echobox_app.api.deps import session_dep, settings_dep
from echobox_app.config import AppSettings
from echobox_app.db.models import Annotation, Image, Project
from echobox_app.errors import ProjectNotFound, ValidationError
from echobox_app.exporters.base import ExportContext
from echobox_app.exporters.registry import EXPORTERS, get_exporter

router = APIRouter(tags=["exports"])


class ExportRequest(BaseModel):
    format: Literal["coco", "yolo", "voc", "ls_json"] | None = None
    include_pending: bool = False
    splits: list[Literal["train", "val", "test"]] | None = None


@router.post("/api/projects/{pid}/exports")
def create_export(
    pid: int,
    payload: ExportRequest,
    session: Annotated[Session, Depends(session_dep)],
    settings: Annotated[AppSettings, Depends(settings_dep)],
) -> dict[str, Any]:
    project = session.get(Project, pid)
    if project is None:
        raise ProjectNotFound(f"project {pid} not found")

    fmt = payload.format or project.export_format
    if fmt is None:
        raise ValidationError("no format specified and project has no default")
    if fmt not in EXPORTERS:
        raise ValidationError(f"unknown format: {fmt}")

    splits = tuple(payload.splits or ("train", "val", "test"))

    images = list(session.scalars(
        select(Image).where(Image.project_id == pid).order_by(Image.index_in_project)
    ))
    annotations_by_image: dict[int, list[Annotation]] = {}
    for img in images:
        annotations_by_image[img.id] = list(session.scalars(
            select(Annotation).where(Annotation.image_id == img.id)
        ))

    if not images:
        raise ValidationError("no images to export")
    total_anns = sum(
        1 for img in images for a in annotations_by_image[img.id]
        if payload.include_pending or a.source != "geco2_pending"
    )
    if total_anns == 0:
        raise ValidationError("no annotations to export")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    export_id = f"{timestamp}-{fmt}"
    workspace_path = settings.data_dir / "projects" / str(pid)
    export_dir = workspace_path / "exports" / export_id

    ctx = ExportContext(
        project_id=pid,
        project_name=project.name,
        workspace_path=workspace_path,
        export_dir=export_dir,
        labels=[(l.name, l.color) for l in project.labels],
        images=images,
        annotations_by_image=annotations_by_image,
        include_pending=payload.include_pending,
        splits=splits,  # type: ignore[arg-type]
    )

    start = time.perf_counter()
    stats = get_exporter(fmt).export(ctx)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    return {
        "export_id": export_id,
        "format": fmt,
        "output_dir": str(export_dir.resolve()),
        "files": sorted(p.name for p in export_dir.iterdir()),
        "stats": {
            "total_images": stats.total_images,
            "total_annotations": stats.total_annotations,
            "by_split": {k: dict(v) for k, v in stats.by_split.items()},
        },
        "elapsed_ms": elapsed_ms,
    }
```

- [ ] **Step 4: Modify main.py**

After `app.include_router(annotations_router)`, add:
```python
    from echobox_app.api.exports import router as exports_router
    app.include_router(exports_router)
```

- [ ] **Step 5: Run, verify pass.**

- [ ] **Step 6: Commit**

```bash
git add packages/app/src/echobox_app/api/exports.py packages/app/src/echobox_app/main.py \
        packages/app/tests/test_api_exports.py
git commit -m "feat(app): add POST /api/projects/{pid}/exports (timestamped output dirs)"
```

---

## Task 8: MCP — AppClient real methods

**Files:**
- Modify: `packages/mcp_server/src/echobox_mcp/client.py`
- Create: `packages/mcp_server/tests/test_client.py`

- [ ] **Step 1: Write failing test**

```python
# packages/mcp_server/tests/test_client.py
import httpx
import pytest

from echobox_mcp.client import AppClient


@pytest.mark.asyncio
async def test_create_project_calls_app() -> None:
    captured: dict[str, object] = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["url"] = str(req.url)
        captured["body"] = req.content
        return httpx.Response(201, json={"id": 7, "name": "x", "status": "draft",
                                         "source_folder": "/orig",
                                         "workspace_path": "/ws"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as ac:
        client = AppClient(http=ac)
        result = await client.create_project(folder="/orig", name="x")

    assert result["id"] == 7
    assert "/api/projects" in captured["url"]


@pytest.mark.asyncio
async def test_list_annotations_with_filters() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"items": [{"id": 1}, {"id": 2}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as ac:
        client = AppClient(http=ac)
        result = await client.list_annotations(pid=7)

    assert len(result["items"]) == 2


@pytest.mark.asyncio
async def test_create_export() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "export_id": "ts-coco", "format": "coco", "output_dir": "/x",
            "files": ["train.json"], "stats": {"total_images": 1, "total_annotations": 1, "by_split": {}},
            "elapsed_ms": 5,
        })

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as ac:
        client = AppClient(http=ac)
        result = await client.create_export(pid=7, fmt="coco")

    assert result["format"] == "coco"
```

- [ ] **Step 2: Run, verify fail.** `uv run pytest packages/mcp_server/tests/test_client.py -v`

- [ ] **Step 3: Implement client.py (replace earlier stub)**

```python
# packages/mcp_server/src/echobox_mcp/client.py
"""HTTP client wrapping the app's REST API."""
from typing import Any

import httpx


class AppClient:
    def __init__(
        self,
        http: httpx.AsyncClient | None = None,
        base_url: str = "http://localhost:8000",
        timeout_s: float = 60.0,
    ) -> None:
        self._http = http or httpx.AsyncClient(base_url=base_url, timeout=timeout_s)
        self._owns = http is None

    async def aclose(self) -> None:
        if self._owns:
            await self._http.aclose()

    async def healthz(self) -> dict[str, Any]:
        r = await self._http.get("/healthz")
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]

    async def create_project(
        self,
        folder: str,
        name: str | None = None,
        initial_labels: list[str] | None = None,
        train_val_test: tuple[float, float, float] | None = None,
        export_format: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"source_folder": folder}
        if name is not None:
            body["name"] = name
        if initial_labels is not None:
            body["initial_labels"] = initial_labels
        if train_val_test is not None:
            body["train_val_test"] = list(train_val_test)
        if export_format is not None:
            body["export_format"] = export_format
        r = await self._http.post("/api/projects", json=body)
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]

    async def get_project(self, pid: int) -> dict[str, Any]:
        r = await self._http.get(f"/api/projects/{pid}")
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]

    async def list_annotations(
        self,
        pid: int,
        label: str | None = None,
        source: str | None = None,
        split: str | None = None,
        min_score: float | None = None,
        image_filename_glob: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        # Aggregates across all images of the project (this is a small API helper
        # implemented client-side for convenience; future: dedicated endpoint).
        proj = await self.get_project(pid)
        images = await self._http.get(f"/api/projects/{pid}/images")
        images.raise_for_status()
        all_imgs = images.json()["items"]
        items: list[dict[str, Any]] = []
        for img in all_imgs:
            if split and split != "any" and img["split"] != split:
                continue
            if image_filename_glob:
                from fnmatch import fnmatch
                if not fnmatch(img["filename"], image_filename_glob):
                    continue
            anns_resp = await self._http.get(f"/api/images/{img['id']}/annotations")
            anns_resp.raise_for_status()
            for a in anns_resp.json()["items"]:
                if label and a["label"]["name"] != label:
                    continue
                if source and source != "any" and a["source"] != source:
                    continue
                if min_score is not None and (a["score"] or 0.0) < min_score:
                    continue
                items.append({
                    "annotation_id": a["id"], "image_id": img["id"],
                    "image_filename": img["filename"], "image_abs_path": img["abs_path"],
                    "image_split": img["split"],
                    "label": a["label"]["name"],
                    "bbox": a["bbox"], "score": a["score"], "source": a["source"],
                })
        # Facets
        facets = {
            "by_label": {}, "by_split": {}, "by_source": {},
        }
        for it in items:
            for k, v in (("by_label", it["label"]), ("by_split", it["image_split"]),
                         ("by_source", it["source"])):
                facets[k][v] = facets[k].get(v, 0) + 1
        total = len(items)
        return {
            "total": total,
            "returned": min(limit, total - offset),
            "items": items[offset:offset + limit],
            "facets": facets,
        }

    async def create_export(
        self,
        pid: int,
        fmt: str | None = None,
        include_pending: bool = False,
        splits: list[str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"include_pending": include_pending}
        if fmt is not None:
            body["format"] = fmt
        if splits is not None:
            body["splits"] = splits
        r = await self._http.post(f"/api/projects/{pid}/exports", json=body)
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]
```

- [ ] **Step 4: Run, verify pass.**

- [ ] **Step 5: Commit**

```bash
git add packages/mcp_server/src/echobox_mcp/client.py packages/mcp_server/tests/test_client.py
git commit -m "feat(mcp_server): implement AppClient with create/list/search/export methods"
```

---

## Task 9: MCP — start_annotation_project tool

**Files:**
- Create: `packages/mcp_server/src/echobox_mcp/tools/__init__.py`
- Create: `packages/mcp_server/src/echobox_mcp/tools/start_project.py`
- Create: `packages/mcp_server/tests/test_tool_start_project.py`

- [ ] **Step 1: Write failing test**

```python
# packages/mcp_server/tests/test_tool_start_project.py
from unittest.mock import AsyncMock

import pytest

from echobox_mcp.tools.start_project import START_PROJECT_TOOL, handle_start_project


@pytest.mark.asyncio
async def test_start_project_returns_setup_url(tmp_path) -> None:  # type: ignore[no-untyped-def]
    folder = tmp_path / "imgs"
    folder.mkdir()
    (folder / "a.jpg").write_text("x")

    fake_client = AsyncMock()
    fake_client.create_project = AsyncMock(return_value={
        "id": 7, "name": "imgs-20260504", "status": "draft",
        "source_folder": str(folder), "workspace_path": str(tmp_path / "ws"),
    })

    result = await handle_start_project(fake_client, {"folder": str(folder)})

    assert result["project_id"] == 7
    assert "setup_url" in result
    assert "5173" in result["setup_url"]
    assert "project_id=7" in result["setup_url"]
    fake_client.create_project.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_project_passes_through_optional_args(tmp_path) -> None:  # type: ignore[no-untyped-def]
    folder = tmp_path / "imgs"
    folder.mkdir()

    fake_client = AsyncMock()
    fake_client.create_project = AsyncMock(return_value={
        "id": 1, "name": "x", "status": "draft", "source_folder": str(folder),
        "workspace_path": "/x",
    })

    await handle_start_project(fake_client, {
        "folder": str(folder),
        "name": "myproj",
        "initial_labels": ["crack"],
        "train_val_test": [0.8, 0.1, 0.1],
        "export_format": "yolo",
    })

    call_args = fake_client.create_project.call_args.kwargs
    assert call_args["name"] == "myproj"
    assert call_args["initial_labels"] == ["crack"]
    assert call_args["train_val_test"] == (0.8, 0.1, 0.1)
    assert call_args["export_format"] == "yolo"


@pytest.mark.asyncio
async def test_start_project_folder_not_found(tmp_path) -> None:  # type: ignore[no-untyped-def]
    fake_client = AsyncMock()

    result = await handle_start_project(fake_client, {"folder": str(tmp_path / "nope")})

    assert result["error"] == "folder_not_found"


def test_tool_schema_has_required_field() -> None:
    assert START_PROJECT_TOOL.name == "start_annotation_project"
    schema = START_PROJECT_TOOL.inputSchema
    assert "folder" in schema["properties"]
    assert "folder" in schema["required"]
```

- [ ] **Step 2: Run, verify fail.** `uv run pytest packages/mcp_server/tests/test_tool_start_project.py -v`

- [ ] **Step 3: Implement tools/__init__.py and start_project.py**

```python
# packages/mcp_server/src/echobox_mcp/tools/__init__.py
"""MCP tool implementations."""
```

```python
# packages/mcp_server/src/echobox_mcp/tools/start_project.py
"""MCP tool: start_annotation_project."""
from pathlib import Path
from typing import Any

from mcp.types import Tool

from echobox_mcp.client import AppClient

START_PROJECT_TOOL = Tool(
    name="start_annotation_project",
    description=(
        "Create a new annotation project from a folder of images. "
        "Returns a setup URL the user opens in a browser to complete "
        "interactive (chat-driven) configuration. Optional parameters "
        "pre-populate the setup cards (user can still edit before clicking 'Start')."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "folder": {
                "type": "string",
                "description": "Absolute path to the folder containing images.",
            },
            "name": {"type": "string", "description": "Project name (defaults to <folder>-<date>)."},
            "initial_labels": {
                "type": "array", "items": {"type": "string"},
                "description": "Pre-fill the label set.",
            },
            "train_val_test": {
                "type": "array", "items": {"type": "number"},
                "minItems": 3, "maxItems": 3,
                "description": "Train/val/test ratios that sum to 1.0.",
            },
            "export_format": {
                "type": "string", "enum": ["coco", "yolo", "voc", "ls_json"],
                "description": "Export format (defaults to 'coco').",
            },
        },
        "required": ["folder"],
    },
)


async def handle_start_project(client: AppClient, args: dict[str, Any]) -> dict[str, Any]:
    folder = args.get("folder")
    if not folder:
        return {"error": "validation_failed", "detail": "folder required"}
    if not Path(folder).exists():
        return {"error": "folder_not_found", "detail": str(folder)}
    if not Path(folder).is_dir():
        return {"error": "folder_not_readable", "detail": f"{folder} is not a directory"}

    train_val_test_arg = args.get("train_val_test")
    train_val_test: tuple[float, float, float] | None = None
    if train_val_test_arg is not None:
        train_val_test = (
            float(train_val_test_arg[0]),
            float(train_val_test_arg[1]),
            float(train_val_test_arg[2]),
        )

    project = await client.create_project(
        folder=folder,
        name=args.get("name"),
        initial_labels=args.get("initial_labels"),
        train_val_test=train_val_test,
        export_format=args.get("export_format"),
    )

    return {
        "project_id": project["id"],
        "name": project["name"],
        "setup_url": f"http://localhost:5173/setup?project_id={project['id']}",
        "status": project["status"],
        "image_count_pending_scan": None,
        "message": (
            "Project created. Open setup_url in a browser to drive the conversational "
            "setup (scan/organize/split/labels/format). When ready click '开始标注' to "
            "transition to status='annotating'."
        ),
    }
```

- [ ] **Step 4: Run, verify pass.**

- [ ] **Step 5: Commit**

```bash
git add packages/mcp_server/src/echobox_mcp/tools/__init__.py \
        packages/mcp_server/src/echobox_mcp/tools/start_project.py \
        packages/mcp_server/tests/test_tool_start_project.py
git commit -m "feat(mcp_server): add start_annotation_project tool"
```

---

## Task 10: MCP — search_annotations tool

**Files:**
- Create: `packages/mcp_server/src/echobox_mcp/tools/search_annotations.py`
- Create: `packages/mcp_server/tests/test_tool_search.py`

- [ ] **Step 1: Write failing test**

```python
# packages/mcp_server/tests/test_tool_search.py
from unittest.mock import AsyncMock

import pytest

from echobox_mcp.tools.search_annotations import (
    SEARCH_ANNOTATIONS_TOOL,
    handle_search_annotations,
)


@pytest.mark.asyncio
async def test_search_passes_filters_and_returns_envelope() -> None:
    fake_client = AsyncMock()
    fake_client.list_annotations = AsyncMock(return_value={
        "total": 5, "returned": 5,
        "items": [
            {"annotation_id": 1, "image_id": 10, "label": "crack",
             "image_split": "train", "score": 0.9, "source": "user"},
        ],
        "facets": {"by_label": {"crack": 5}, "by_split": {"train": 5}, "by_source": {"user": 5}},
    })

    result = await handle_search_annotations(fake_client, {
        "project_id": 7,
        "label": "crack",
        "split": "train",
    })

    assert result["total"] == 5
    fake_client.list_annotations.assert_awaited_with(
        pid=7, label="crack", source="any", split="train",
        min_score=None, image_filename_glob=None, limit=100, offset=0,
    )


def test_tool_schema_includes_facets_in_description() -> None:
    assert SEARCH_ANNOTATIONS_TOOL.name == "search_annotations"
    assert "project_id" in SEARCH_ANNOTATIONS_TOOL.inputSchema["properties"]
```

- [ ] **Step 2: Run, verify fail.**

- [ ] **Step 3: Implement search_annotations.py**

```python
# packages/mcp_server/src/echobox_mcp/tools/search_annotations.py
"""MCP tool: search_annotations."""
from typing import Any

from mcp.types import Tool

from echobox_mcp.client import AppClient

SEARCH_ANNOTATIONS_TOOL = Tool(
    name="search_annotations",
    description=(
        "Search annotations across an annotation project. Returns matching "
        "annotations with their image context, plus aggregated facets "
        "(by_label, by_split, by_source) for analysis."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {"type": "integer"},
            "label": {"type": "string", "description": "Exact label name to filter."},
            "source": {
                "type": "string",
                "enum": ["user", "geco2_accepted", "user_edited", "any"],
                "description": "Annotation source filter (default 'any').",
            },
            "split": {
                "type": "string",
                "enum": ["train", "val", "test", "any"],
                "description": "Train/val/test filter (default 'any').",
            },
            "min_score": {"type": "number", "description": "Min GECO2 score (0..1)."},
            "image_filename_glob": {"type": "string", "description": "Like '*.jpg'."},
            "limit": {"type": "integer", "minimum": 1, "maximum": 1000},
            "offset": {"type": "integer", "minimum": 0},
        },
        "required": ["project_id"],
    },
)


async def handle_search_annotations(
    client: AppClient,
    args: dict[str, Any],
) -> dict[str, Any]:
    return await client.list_annotations(
        pid=int(args["project_id"]),
        label=args.get("label"),
        source=args.get("source", "any"),
        split=args.get("split", "any"),
        min_score=args.get("min_score"),
        image_filename_glob=args.get("image_filename_glob"),
        limit=int(args.get("limit", 100)),
        offset=int(args.get("offset", 0)),
    )
```

- [ ] **Step 4: Run, verify pass.**

- [ ] **Step 5: Commit**

```bash
git add packages/mcp_server/src/echobox_mcp/tools/search_annotations.py \
        packages/mcp_server/tests/test_tool_search.py
git commit -m "feat(mcp_server): add search_annotations tool"
```

---

## Task 11: MCP — export_dataset tool + wire into server

**Files:**
- Create: `packages/mcp_server/src/echobox_mcp/tools/export_dataset.py`
- Modify: `packages/mcp_server/src/echobox_mcp/server.py`
- Create: `packages/mcp_server/tests/test_tool_export.py`

- [ ] **Step 1: Write failing test**

```python
# packages/mcp_server/tests/test_tool_export.py
from unittest.mock import AsyncMock

import pytest

from echobox_mcp.tools.export_dataset import EXPORT_DATASET_TOOL, handle_export_dataset


@pytest.mark.asyncio
async def test_export_passes_format_and_includes() -> None:
    fake_client = AsyncMock()
    fake_client.create_export = AsyncMock(return_value={
        "export_id": "ts-coco", "format": "coco", "output_dir": "/x",
        "files": ["train.json"], "stats": {"total_images": 1, "total_annotations": 5,
                                            "by_split": {}}, "elapsed_ms": 12,
    })

    result = await handle_export_dataset(fake_client, {
        "project_id": 7,
        "format": "coco",
        "include_pending": True,
    })

    assert result["format"] == "coco"
    assert result["stats"]["total_annotations"] == 5
    fake_client.create_export.assert_awaited_with(
        pid=7, fmt="coco", include_pending=True, splits=None,
    )


def test_tool_required_field() -> None:
    assert EXPORT_DATASET_TOOL.name == "export_dataset"
    assert "project_id" in EXPORT_DATASET_TOOL.inputSchema["required"]
```

- [ ] **Step 2: Run, verify fail.**

- [ ] **Step 3: Implement export_dataset.py**

```python
# packages/mcp_server/src/echobox_mcp/tools/export_dataset.py
"""MCP tool: export_dataset."""
from typing import Any

from mcp.types import Tool

from echobox_mcp.client import AppClient

EXPORT_DATASET_TOOL = Tool(
    name="export_dataset",
    description=(
        "Export a project's annotations to disk in the chosen format. "
        "Output is in <workspace>/exports/<timestamp>-<format>/. "
        "Returns the absolute output path + per-split statistics."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {"type": "integer"},
            "format": {
                "type": "string",
                "enum": ["coco", "yolo", "voc", "ls_json"],
                "description": "Export format. Defaults to project's saved choice.",
            },
            "include_pending": {
                "type": "boolean",
                "description": "Include GECO2 pending boxes (default false).",
            },
            "splits": {
                "type": "array",
                "items": {"type": "string", "enum": ["train", "val", "test"]},
                "description": "Subset of splits to export (default all).",
            },
        },
        "required": ["project_id"],
    },
)


async def handle_export_dataset(
    client: AppClient,
    args: dict[str, Any],
) -> dict[str, Any]:
    return await client.create_export(
        pid=int(args["project_id"]),
        fmt=args.get("format"),
        include_pending=bool(args.get("include_pending", False)),
        splits=args.get("splits"),
    )
```

- [ ] **Step 4: Wire all 3 tools into server.py**

Replace `packages/mcp_server/src/echobox_mcp/server.py`:

```python
# packages/mcp_server/src/echobox_mcp/server.py
"""MCP server: registers 3 tools (start_project, search, export)."""
import json
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from echobox_mcp.client import AppClient
from echobox_mcp.config import MCPSettings
from echobox_mcp.tools.export_dataset import (
    EXPORT_DATASET_TOOL,
    handle_export_dataset,
)
from echobox_mcp.tools.search_annotations import (
    SEARCH_ANNOTATIONS_TOOL,
    handle_search_annotations,
)
from echobox_mcp.tools.start_project import (
    START_PROJECT_TOOL,
    handle_start_project,
)

ALL_TOOLS: list[Tool] = [
    START_PROJECT_TOOL,
    SEARCH_ANNOTATIONS_TOOL,
    EXPORT_DATASET_TOOL,
]


def build_server(settings: MCPSettings | None = None) -> Server:
    settings = settings or MCPSettings()
    server = Server("echobox")
    client = AppClient(base_url=settings.app_url, timeout_s=settings.app_request_timeout_s)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return ALL_TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if name == "start_annotation_project":
            result = await handle_start_project(client, arguments)
        elif name == "search_annotations":
            result = await handle_search_annotations(client, arguments)
        elif name == "export_dataset":
            result = await handle_export_dataset(client, arguments)
        else:
            result = {"error": "unknown_tool", "detail": f"no tool named {name!r}"}

        is_error = "error" in result
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    return server


def run() -> None:
    """Entry point for `echobox-mcp` console script."""
    import asyncio

    from mcp.server.stdio import stdio_server

    settings = MCPSettings()
    server = build_server(settings)

    async def _serve() -> None:
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    asyncio.run(_serve())
```

- [ ] **Step 5: Update existing test to expect 3 tools**

Edit `packages/mcp_server/tests/test_server_stub.py` and rename it to test the real 3 tools. Replace contents:

```python
import pytest

from echobox_mcp.server import ALL_TOOLS, build_server


def test_server_lists_3_tools() -> None:
    server = build_server()
    assert server.name == "echobox"
    assert len(ALL_TOOLS) == 3
    names = {t.name for t in ALL_TOOLS}
    assert names == {
        "start_annotation_project",
        "search_annotations",
        "export_dataset",
    }
```

- [ ] **Step 6: Run all mcp tests, verify pass**

Run: `uv run pytest packages/mcp_server/tests/ -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/mcp_server/src/echobox_mcp/tools/export_dataset.py \
        packages/mcp_server/src/echobox_mcp/server.py \
        packages/mcp_server/tests/test_server_stub.py \
        packages/mcp_server/tests/test_tool_export.py
git commit -m "feat(mcp_server): wire all 3 tools (start/search/export) into server"
```

---

## Task 12: README.md (full English)

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace README.md content**

```markdown
# Echobox

> Multimodal intelligent annotation agent platform — pre-annotate images with one click via SAM2-backed exemplar detection, supervised by an LLM agent.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-pre--alpha-orange)

## What it does

- **Conversational setup**: Tell the agent your folder; it scans, splits (train/val/test), proposes labels, and prepares a project — by chatting in your browser.
- **Exemplar-based annotation**: Draw one bounding box on an image; [GECO2](https://github.com/jerpelhan/GECO2) returns every similar object. You adjust, accept, save — instantly.
- **Multi-format export**: COCO, YOLO, Pascal VOC, and Label Studio JSON, all from one source.
- **Reusable as MCP tools**: External agents (Claude Code, Cursor, …) can call `start_annotation_project`, `search_annotations`, `export_dataset` over the Model Context Protocol.

## Architecture

4 processes, all run locally — no Docker required.

```
Browser ──▶ frontend (Vite, port 5173)
                │
                ▼
          app (FastAPI, port 8000) ──▶ ml_backend (FastAPI + GPU, port 9090)
                │                              │
                │                              └─▶ GECO2 / SAM2 inference
                │
                ├─▶ DashScope (Qwen) for LangGraph agent
                └─▶ SQLite + filesystem workspace

mcp_server (stdio) ──▶ app HTTP — for Claude Code / Cursor consumers
```

See [`docs/superpowers/specs/2026-05-04-multimodal-annotation-agent-design.md`](docs/superpowers/specs/2026-05-04-multimodal-annotation-agent-design.md) for the full design.

## Quick start

### Prerequisites
- Python 3.11+ ([install via uv](https://docs.astral.sh/uv/getting-started/installation/))
- Node 20+
- A DashScope API key (free tier available) — or any OpenAI-compatible endpoint

### Install

```bash
git clone --recurse-submodules https://github.com/<your-org>/echobox
cd echobox
make setup                                      # installs Python + frontend deps
bash scripts/download_geco2_weights.sh          # SAM2 + GECO2 weights (~500MB)
cp .env.example .env                            # then edit ECHOBOX_APP_LLM_API_KEY
make db-upgrade                                 # creates .data/projects.db
make dev                                        # boots all 4 processes via honcho
```

Open <http://127.0.0.1:5173> and create your first project.

### Verify health

```bash
bash scripts/verify_healthz.sh
```

## Usage

1. **Home page** → enter a folder of images → "创建项目"
2. **Setup page** → chat with the agent ("scan and split 70/15/15") → review cards → "开始标注"
3. **Annotate page** → pick a class → drag an exemplar bbox → review GECO2 predictions → save → next image
4. **Export** → use the MCP `export_dataset` tool, or `POST /api/projects/{pid}/exports`

## Use as MCP server

In Claude Desktop's `mcpServers` config:
```json
{
  "echobox": {
    "command": "uv",
    "args": ["run", "--package", "echobox-mcp", "echobox-mcp"],
    "env": {"ECHOBOX_APP_URL": "http://localhost:8000"}
  }
}
```

Then ask: *"Start an annotation project for `/path/to/images`."*

## Documentation

- [Architecture](docs/architecture.md) — process topology, data model
- [Development](docs/development.md) — local dev setup, testing, code style
- [API](docs/api.md) — REST + MCP reference
- [Extending](docs/extending.md) — add new exporters or model backends
- [中文 README](README_zh.md)

## Testing

```bash
make test           # unit + integration
make typecheck      # mypy + tsc
make lint           # ruff + eslint
```

## License

[Apache-2.0](LICENSE)

## Acknowledgments

- [GECO2](https://github.com/jerpelhan/GECO2) — exemplar-based detection on SAM2
- [Segment Anything 2](https://github.com/facebookresearch/segment-anything-2)
- [LangGraph](https://github.com/langchain-ai/langgraph)
```

- [ ] **Step 2: Verify file**

Run: `head -30 README.md`
Expected: see the project intro.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: write full English README with architecture, quick-start, MCP usage"
```

---

## Task 13: README_zh.md (Chinese)

**Files:**
- Modify: `README_zh.md`

- [ ] **Step 1: Replace content**

```markdown
# Echobox

> 多模态智能标注 Agent 平台 —— 用 LangGraph 编排的对话式 setup + GECO2/SAM2 的 exemplar 检测，让"画一个框出多个框"变成主要交互。

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-pre--alpha-orange)

## 核心能力

- **对话式建项**：告诉 Agent 你的文件夹，它会扫描、切分 train/val/test、建议标签集、准备好项目 —— 全程浏览器聊天搞定。
- **示例驱动的标注**：在图上画一个示例框，[GECO2](https://github.com/jerpelhan/GECO2) 自动返回所有"长得像"的目标。你只需调整、接受、保存。
- **4 种导出格式**：COCO / YOLO / VOC / Label Studio JSON。
- **MCP 工具复用**：通过 Model Context Protocol 暴露 3 个工具，Claude Code / Cursor 等 Agent 可直接调用。

## 架构

4 个本地进程，**不需要 Docker**。

```
浏览器 ──▶ frontend (Vite, 5173)
              │
              ▼
        app (FastAPI, 8000) ──▶ ml_backend (FastAPI + GPU, 9090)
              │                          │
              │                          └─▶ GECO2 / SAM2 推理
              │
              ├─▶ DashScope (Qwen) 给 LangGraph 当大脑
              └─▶ SQLite + 文件系统 workspace

mcp_server (stdio) ──▶ app HTTP — 给 Claude Code / Cursor 用
```

完整设计见 [`docs/superpowers/specs/2026-05-04-multimodal-annotation-agent-design.md`](docs/superpowers/specs/2026-05-04-multimodal-annotation-agent-design.md)。

## 快速开始

### 前置
- Python 3.11+ ([用 uv 安装](https://docs.astral.sh/uv/getting-started/installation/))
- Node 20+
- 一个 DashScope API key（有免费额度）—— 或任何 OpenAI 兼容端点

### 安装

```bash
git clone --recurse-submodules https://github.com/<your-org>/echobox
cd echobox
make setup                                      # 装 Python + 前端依赖
bash scripts/download_geco2_weights.sh          # 下载 SAM2 + GECO2 权重 (~500MB)
cp .env.example .env                            # 编辑填入 ECHOBOX_APP_LLM_API_KEY
make db-upgrade                                 # 创建 .data/projects.db
make dev                                        # honcho 启动 4 进程
```

浏览器打开 <http://127.0.0.1:5173>，创建你的第一个项目。

### 检查健康

```bash
bash scripts/verify_healthz.sh
```

## 使用流程

1. **首页**：输入图片文件夹路径 → 创建项目
2. **Setup 页**：和 Agent 对话（如"扫描并 70/15/15 切分"）→ 检查卡片 → 开始标注
3. **标注页**：选类别 → 画示例框 → 审核 GECO2 返回的所有相似框 → 保存 → 下一张
4. **导出**：用 MCP `export_dataset` 工具或 `POST /api/projects/{pid}/exports`

## 作为 MCP 服务

Claude Desktop 的 `mcpServers` 配置：
```json
{
  "echobox": {
    "command": "uv",
    "args": ["run", "--package", "echobox-mcp", "echobox-mcp"],
    "env": {"ECHOBOX_APP_URL": "http://localhost:8000"}
  }
}
```

然后说：*"给 `/path/to/images` 启动一个标注项目。"*

## 文档

- [架构](docs/architecture.md) —— 进程拓扑、数据模型
- [开发](docs/development.md) —— 本地开发、测试、代码风格
- [API](docs/api.md) —— REST + MCP 参考
- [扩展](docs/extending.md) —— 加新 exporter / 新模型后端
- [English README](README.md)

## 测试

```bash
make test           # 单元 + 集成
make typecheck      # mypy + tsc
make lint           # ruff + eslint
```

## 协议

[Apache-2.0](LICENSE)

## 致谢

- [GECO2](https://github.com/jerpelhan/GECO2) —— 基于 SAM2 的 exemplar 检测
- [Segment Anything 2](https://github.com/facebookresearch/segment-anything-2)
- [LangGraph](https://github.com/langchain-ai/langgraph)
```

- [ ] **Step 2: Commit**

```bash
git add README_zh.md
git commit -m "docs: write full Chinese README"
```

---

## Task 14: CONTRIBUTING.md + CODE_OF_CONDUCT.md + SECURITY.md + CHANGELOG.md

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `CODE_OF_CONDUCT.md`
- Create: `SECURITY.md`
- Create: `CHANGELOG.md`

- [ ] **Step 1: Create CONTRIBUTING.md**

```markdown
# Contributing to Echobox

Thanks for your interest in contributing!

## Quick links
- [Open an issue](https://github.com/<your-org>/echobox/issues/new/choose)
- [Open a PR](https://github.com/<your-org>/echobox/pulls)
- [Read the architecture doc](docs/architecture.md)

## Local setup

```bash
git clone --recurse-submodules https://github.com/<your-org>/echobox
cd echobox
make setup
cp .env.example .env  # add your DashScope key
make db-upgrade
make dev
```

## Workflow

1. Fork + clone
2. Create a branch: `git checkout -b feature/short-description`
3. Make changes — follow the **TDD discipline** documented in `docs/superpowers/plans/`:
   - Write a failing test first
   - Implement minimal code to make it pass
   - Commit small, frequent
4. Run `make test && make lint && make typecheck` — must all pass
5. Push and open a PR

## Code style

- Python: `ruff format` + `ruff check`; strict mypy. Line width 100.
- TypeScript: `prettier` + `eslint`. Line width 100.
- Pre-commit hooks auto-format on commit (`pre-commit install` once).

## Architecture rules

- Don't import across packages directly. `app` ↔ `ml_backend` ↔ `mcp_server` go via HTTP.
- DB ownership lives in `app` only. The other packages are stateless.
- New tools or exporters: drop in their respective directory + register; no other files should change.

## Tests

- Place tests next to their package (`packages/<pkg>/tests/`).
- E2E tests in `tests/e2e/`. They mock LLM and ml_backend.
- Aim for 80% line coverage; 90%+ on `domain/`, `tools/`, `exporters/`.

## Asking questions

Open a [GitHub Discussion](https://github.com/<your-org>/echobox/discussions) or an issue.

## License of contributions

By contributing, you agree your code is licensed under [Apache-2.0](LICENSE).
```

- [ ] **Step 2: Create CODE_OF_CONDUCT.md**

```markdown
# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our community a harassment-free experience for everyone, regardless of age, body size, visible or invisible disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

## Our Standards

Examples of behavior that contributes to a positive environment:

- Demonstrating empathy and kindness
- Being respectful of differing opinions
- Giving and gracefully accepting constructive feedback
- Accepting responsibility for mistakes
- Focusing on what is best for the community

Examples of unacceptable behavior:

- Trolling, insulting/derogatory comments, personal/political attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

## Enforcement

Instances of abusive behavior may be reported to the maintainers at the email in [SECURITY.md](SECURITY.md). All complaints will be reviewed and investigated promptly and fairly.

## Attribution

Adapted from the [Contributor Covenant v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct.html).
```

- [ ] **Step 3: Create SECURITY.md**

```markdown
# Security Policy

## Reporting a Vulnerability

Please do **not** open a public GitHub issue for security vulnerabilities.

Email the maintainers at: `security@<your-domain>`

We will acknowledge within 5 business days and aim to provide a fix within 30 days for high-severity issues.

## Supported Versions

Echobox is in pre-alpha. Only the `main` branch is currently supported. Once we tag `v1.0.0`, we will document a support matrix here.

## Scope

In scope:
- The Python packages in `packages/`
- The frontend in `frontend/`
- Default deployment configurations

Out of scope (file with upstream):
- Vulnerabilities in vendored GECO2 (`packages/ml_backend/src/echobox_ml/geco2_vendor/`) — report to <https://github.com/jerpelhan/GECO2>
- Vulnerabilities in Python deps — report to PyPI / project maintainers
```

- [ ] **Step 4: Create CHANGELOG.md**

```markdown
# Changelog

All notable changes are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-XX-XX

### Added
- 4-process scaffold (app, ml_backend, mcp_server, frontend)
- LangGraph-based conversational setup with 7 deterministic tools
- GECO2 + SAM2 integration for exemplar-based detection
- React + react-konva annotation canvas
- 4 export formats (COCO, YOLO, Pascal VOC, Label Studio JSON)
- MCP server with 3 tools (start_project, search_annotations, export_dataset)
- SQLite persistence with Alembic migrations
- Honcho-based dev orchestration
- CI workflows for lint + type + test
- Bilingual documentation (English + 中文)
```

- [ ] **Step 5: Commit**

```bash
git add CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md CHANGELOG.md
git commit -m "docs: add CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG"
```

---

## Task 15: docs/architecture.md + docs/development.md

**Files:**
- Create: `docs/architecture.md`
- Create: `docs/development.md`

- [ ] **Step 1: Create docs/architecture.md**

```markdown
# Architecture

This document is a slim, navigable view of the system. The full design — every decision, every tradeoff — lives in [`superpowers/specs/2026-05-04-multimodal-annotation-agent-design.md`](superpowers/specs/2026-05-04-multimodal-annotation-agent-design.md).

## Process topology

| Process | Port | Tech | Role |
|---------|------|------|------|
| `app` | 8000 | FastAPI | LangGraph chat agent, setup orchestration, REST API, DB writes |
| `ml_backend` | 9090 | FastAPI + GPU | GECO2 / SAM2 inference (`POST /predict_similar`) |
| `mcp_server` | stdio | MCP SDK | Exposes 3 tools to external agents |
| `frontend` | 5173 | Vite + React + Konva | Setup page (cards + chat) + Annotate page (canvas) |

All inter-process communication is HTTP. `app` is the only process with persistent state (SQLite + on-disk workspace).

## Data flow

### Phase 1 — Setup
```
User chat ──▶ app POST /chat (SSE)
                 ↓
              LangGraph (Planner + Critic)
                 ↓
         tool execution → mutate AgentState
                 ↓
              SSE events back to frontend
                 ↓
         Cards re-render, user clicks 开始标注
                 ↓
         POST /finalize → status=ready → /annotate
```

### Phase 2 — Annotation
```
User draws exemplar ──▶ app POST /predict-similar
                            ↓
                       ml_backend POST /predict_similar
                            ↓
                       GECO2 returns N boxes
                            ↓
                       app persists with source=geco2_pending
                            ↓
                       SSE / response → frontend renders dashed boxes
                            ↓
                       User adjusts → PUT/PATCH/DELETE → DB
```

## Workspace layout (per-project)

```
.data/projects/<id>/
├── project.json         # metadata snapshot
├── data/
│   ├── image/00001.jpg ...   # canonical-named copies
│   ├── mapping.json          # canonical → source path
│   └── splits.json           # canonical → train/val/test
├── exports/<timestamp>-<format>/
└── chat/history.jsonl
```

## Database tables (overview)

- `projects` — top-level project (status, ratios, format)
- `images` — per-image metadata + split assignment
- `labels` — class names + UI colors
- `annotations` — bbox + label + source + version
- `chat_messages` — Phase 1 LangGraph history
- `prediction_runs` — GECO2 invocation log

Full schema: see the spec section 6.2.

## Where to look for what

| Want to ... | File |
|-------------|------|
| Add a new agent tool | `packages/app/src/echobox_app/tools/` + `agent/tool_specs.py` |
| Add a new exporter | `packages/app/src/echobox_app/exporters/` + register in `registry.py` |
| Add a new MCP tool | `packages/mcp_server/src/echobox_mcp/tools/` + register in `server.py` |
| Add a frontend card | `frontend/src/components/cards/` |
| Change the chat agent prompt | `packages/app/src/echobox_app/agent/graph.py:_SYSTEM_PROMPT` |
| Swap LLM provider | Set `ECHOBOX_APP_LLM_BASE_URL` (any OpenAI-compatible endpoint) |
| Swap exemplar detector | Replace `Geco2Runner` in `packages/ml_backend/src/echobox_ml/runner.py` |
```

- [ ] **Step 2: Create docs/development.md**

```markdown
# Development

## One-time setup

```bash
git clone --recurse-submodules https://github.com/<your-org>/echobox
cd echobox
make setup
cp .env.example .env             # then fill ECHOBOX_APP_LLM_API_KEY
make db-upgrade
uv run pre-commit install        # auto-format on commit
```

GPU/inference setup (only if you want real GECO2):
```bash
bash scripts/download_geco2_weights.sh
# Then in .env: ECHOBOX_ML_GECO2_WEIGHTS=./.data/weights/geco2.pth
#               ECHOBOX_ML_SAM2_WEIGHTS=./.data/weights/sam2_hiera_tiny.pt
```

## Daily workflow

```bash
make dev          # start all 4 processes
make test         # full test suite
make lint         # ruff + eslint
make typecheck    # mypy + tsc
```

To run a single process in its own terminal:
```bash
make app          # FastAPI app on 8000 (with --reload)
make ml           # ml_backend on 9090
make mcp          # MCP stdio server
make web          # Vite dev server on 5173
```

## Project layout

```
packages/         # 3 Python packages (uv workspace)
├── app/         # the main FastAPI service
├── ml_backend/  # GECO2 inference
└── mcp_server/  # MCP tools

frontend/        # React + TypeScript + Vite

tests/
├── e2e/         # cross-process tests (mocked LLM + ml_backend)
└── fixtures/    # tiny images, recorded LLM responses

docs/            # architecture, dev, api, extending
scripts/         # setup, dev, weight download
```

## Testing strategy

- **Unit** (~80% coverage): tools, exporters, domain dataclasses, db models
- **Integration** (~20 tests): FastAPI TestClient + temp SQLite + mocked LLM/ml_client
- **E2E** (2-3 tests): full Phase 1 / Phase 2 flows

LLM responses in tests are scripted (no real API call). Real GECO2 inference tests are gated by `ECHOBOX_ML_TEST_REAL=1`.

## Adding a feature

1. Read the relevant section in `docs/superpowers/specs/`
2. Find or write a plan in `docs/superpowers/plans/`
3. Follow TDD: write failing test → implement → pass → commit
4. Update CHANGELOG.md under `[Unreleased]`
5. Open PR
```

- [ ] **Step 3: Commit**

```bash
git add docs/architecture.md docs/development.md
git commit -m "docs: add architecture overview + development workflow guide"
```

---

## Task 16: docs/api.md + docs/extending.md

**Files:**
- Create: `docs/api.md`
- Create: `docs/extending.md`

- [ ] **Step 1: Create docs/api.md**

```markdown
# API Reference

## REST API (app, port 8000)

### Projects

| Method | Path | Body | Returns |
|--------|------|------|---------|
| POST | `/api/projects` | `{source_folder, name?, initial_labels?, train_val_test?, export_format?}` | Project (201) |
| GET | `/api/projects/{pid}` | — | Project + AgentState |
| POST | `/api/projects/{pid}/chat` | `{content}` | SSE stream of agent events |
| PATCH | `/api/projects/{pid}/folder` | `{folder}` | Project |
| PATCH | `/api/projects/{pid}/splits` | `{train, val, test}` | Project |
| PATCH | `/api/projects/{pid}/format` | `{format}` | Project |
| POST | `/api/projects/{pid}/labels` | `{name, color?}` | Label (201, 409 on dup) |
| DELETE | `/api/projects/{pid}/labels/{name}` | — | 204 (403 if status≠draft) |
| POST | `/api/projects/{pid}/finalize` | — | `{status, id}` (400 if critic fails) |

### Images

| Method | Path | Returns |
|--------|------|---------|
| GET | `/api/projects/{pid}/images?split=...` | List + per-split progress |
| GET | `/api/images/{iid}` | Image |
| GET | `/api/images/{iid}/file` | Image bytes |
| GET | `/api/images/{iid}/annotations` | List of annotations |

### Annotations

| Method | Path | Body |
|--------|------|------|
| POST | `/api/projects/{pid}/images/{iid}/predict-similar` | `{label_id, exemplar_bbox, max_predictions?, score_threshold?}` |
| PUT | `/api/annotations/{aid}` | `{x1?, y1?, x2?, y2?, label_id?, source?, version}` |
| DELETE | `/api/annotations/{aid}` | — |
| PATCH | `/api/projects/{pid}/images/{iid}/annotations/bulk` | `{action: "accept_all" \| "reject_all"}` |

### Exports

| Method | Path | Body |
|--------|------|------|
| POST | `/api/projects/{pid}/exports` | `{format?, include_pending?, splits?}` |

## Error envelope

All errors share this shape:
```json
{
  "error": {
    "code": "project_not_found",
    "message": "project 99 not found",
    "detail": {"project_id": 99}
  }
}
```

Common codes: `validation_failed` (400), `project_not_found` / `image_not_found` / `annotation_not_found` (404), `label_conflict` / `version_conflict` (409), `ml_backend_unavailable` / `llm_unavailable` (503), `internal_error` (500).

## ml_backend (port 9090)

| Method | Path | Body | Returns |
|--------|------|------|---------|
| GET | `/healthz` | — | `{status, service, version, model_loaded, device}` |
| POST | `/predict_similar` | `{image_path, exemplar_bbox, max_predictions?, score_threshold?}` | `{predictions, exemplar_count, image_size, elapsed_ms}` |

## MCP server (stdio or SSE)

3 tools — see [`docs/superpowers/specs/...`](superpowers/specs/2026-05-04-multimodal-annotation-agent-design.md) section 7 for full schemas.

| Tool | Args | Returns |
|------|------|---------|
| `start_annotation_project` | `{folder, name?, initial_labels?, train_val_test?, export_format?}` | `{project_id, name, setup_url, status, message}` |
| `search_annotations` | `{project_id, label?, source?, split?, min_score?, image_filename_glob?, limit?, offset?}` | `{total, returned, items, facets}` |
| `export_dataset` | `{project_id, format?, include_pending?, splits?}` | `{export_id, format, output_dir, files, stats, elapsed_ms}` |
```

- [ ] **Step 2: Create docs/extending.md**

```markdown
# Extending Echobox

## Adding a new export format

1. Create `packages/app/src/echobox_app/exporters/<name>.py` implementing `Exporter`:

```python
from echobox_app.exporters.base import ExportContext, ExportStats, Exporter

class MyExporter(Exporter):
    name = "myfmt"

    def export(self, ctx: ExportContext) -> ExportStats:
        ctx.export_dir.mkdir(parents=True, exist_ok=True)
        stats = ExportStats()
        # ... write files into ctx.export_dir
        return stats
```

2. Register in `packages/app/src/echobox_app/exporters/registry.py`:

```python
from echobox_app.exporters.myfmt import MyExporter

EXPORTERS["myfmt"] = MyExporter
```

3. Add `"myfmt"` to the `ExportRequest.format` Literal in `packages/app/src/echobox_app/api/exports.py`.

4. Add a test in `packages/app/tests/test_exporter_myfmt.py` following the COCO test pattern.

That's it — `POST /api/projects/{pid}/exports` and the MCP `export_dataset` tool both pick up your new format automatically.

## Adding a new agent tool

1. Implement the deterministic logic in `packages/app/src/echobox_app/tools/<topic>.py` (pure function, no LLM).
2. Add a `ToolSpec` in `packages/app/src/echobox_app/agent/tool_specs.py`:

```python
_MY_TOOL = ToolSpec(
    name="my_tool",
    description="What it does — written for the LLM to read.",
    args={"arg1": {"type": "string", "description": "..."}},
)
TOOL_SPECS.append(_MY_TOOL)
```

3. Wire it in `packages/app/src/echobox_app/agent/executor.py:execute_tool`:

```python
if name == "my_tool":
    return _do_my_tool(state, args)
```

4. Test the tool in isolation + add to e2e setup test if it should be part of the canonical flow.

## Swapping the exemplar detector

`Geco2Runner` is a class, not a global. To swap:

1. Implement an alternative class with the same `predict_similar(image_path, exemplar_bbox, max_predictions, score_threshold) -> (list[Prediction], (w, h), elapsed_ms)` signature.
2. In `packages/ml_backend/src/echobox_ml/main.py`, swap the constructor.
3. Optional: turn `Geco2Runner` into a config-driven factory if you want hot-swap.

## Swapping the LLM provider

The chat agent uses LangChain's `ChatOpenAI` — anything OpenAI-compatible works. Just set `ECHOBOX_APP_LLM_BASE_URL` and `ECHOBOX_APP_LLM_MODEL`.

For non-OpenAI APIs (e.g., Anthropic native), modify `packages/app/src/echobox_app/llm/factory.py:build_chat_model` to dispatch on a config flag.

## Adding a frontend page

1. Create `frontend/src/pages/<NewPage>.tsx`.
2. Add a route in `frontend/src/App.tsx`.
3. (Optional) Add API client in `frontend/src/api/`.

## Building a custom MCP tool

In `packages/mcp_server/src/echobox_mcp/tools/<my_tool>.py`:

```python
from mcp.types import Tool
from echobox_mcp.client import AppClient

MY_TOOL = Tool(name="my_tool", description="...", inputSchema={...})

async def handle_my_tool(client: AppClient, args: dict) -> dict:
    # call client.<some_method>(...)
    return {...}
```

Then in `packages/mcp_server/src/echobox_mcp/server.py`, append `MY_TOOL` to `ALL_TOOLS` and add a branch in `call_tool()`.
```

- [ ] **Step 3: Commit**

```bash
git add docs/api.md docs/extending.md
git commit -m "docs: add API reference + extending guide"
```

---

## Task 17: GitHub workflows — CI

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/ISSUE_TEMPLATE/bug_report.md`
- Create: `.github/ISSUE_TEMPLATE/feature_request.md`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`

- [ ] **Step 1: Create .github/workflows/ci.yml**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  python:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: latest

      - name: Set up Python
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --dev

      - name: Lint (ruff)
        run: uv run ruff check packages/

      - name: Format check (ruff)
        run: uv run ruff format --check packages/

      - name: Type check (mypy)
        run: |
          uv run mypy packages/app/src
          uv run mypy packages/ml_backend/src
          uv run mypy packages/mcp_server/src

      - name: Tests
        env:
          ECHOBOX_APP_LLM_API_KEY: stub
        run: uv run pytest --cov=packages --cov-report=term-missing

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install
        run: npm --prefix frontend ci

      - name: Lint
        run: npm --prefix frontend run lint

      - name: Type check + build
        run: npm --prefix frontend run build
```

- [ ] **Step 2: Create issue templates**

`.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug report
about: Something is broken
labels: bug
---

**Describe the bug**
A clear and concise description.

**To Reproduce**
Steps:
1. ...

**Expected behavior**

**Environment**
- OS:
- Python version:
- Node version:
- echobox version / commit:

**Logs / screenshots**
```

`.github/ISSUE_TEMPLATE/feature_request.md`:

```markdown
---
name: Feature request
about: Suggest an idea
labels: enhancement
---

**The problem you're trying to solve**

**The solution you'd like**

**Alternatives you've considered**
```

- [ ] **Step 3: Create .github/PULL_REQUEST_TEMPLATE.md**

```markdown
## Summary

## Test plan
- [ ] `make test` passes
- [ ] `make lint` passes
- [ ] `make typecheck` passes
- [ ] Manual smoke test (describe)

## Related
Closes #
```

- [ ] **Step 4: Verify workflow YAML syntax**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`
Expected: no error.

- [ ] **Step 5: Commit**

```bash
git add .github/
git commit -m "chore: add GitHub Actions CI workflow + issue/PR templates"
```

---

## Task 18: GitHub release workflow

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Create .github/workflows/release.yml**

```yaml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
          fetch-depth: 0

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Set up Python
        run: uv python install 3.11

      - name: Build wheels
        run: |
          mkdir -p dist
          for pkg in app ml_backend mcp_server; do
            uv build --package aris-${pkg/_/-} --wheel --out-dir dist
          done

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Build frontend
        run: |
          cd frontend
          npm ci
          npm run build
          tar czf ../dist/frontend-${{ github.ref_name }}.tar.gz dist

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
          files: |
            dist/*.whl
            dist/frontend-${{ github.ref_name }}.tar.gz
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "chore: add GitHub Actions release workflow (wheels + frontend tarball)"
```

---

## Task 19: Final smoke + tag v0.1.0

- [ ] **Step 1: Run full test suite one more time**

Run: `make test`
Expected: all tests pass.

- [ ] **Step 2: Run lint + typecheck**

Run: `make lint && make typecheck`
Expected: green.

- [ ] **Step 3: Run pre-commit on all files**

Run: `uv run pre-commit run --all-files`
Expected: passes (or auto-fixes; re-stage and re-run).

- [ ] **Step 4: Verify dev still boots**

Run: `make dev` in one terminal; `bash scripts/verify_healthz.sh` in another.
Expected: all 3 web services healthy.
Cleanup.

- [ ] **Step 5: Verify export end-to-end (manual integration sanity)**

In one terminal: `make dev`
In a second terminal:
```bash
curl -X POST http://127.0.0.1:8000/api/projects \
  -H 'Content-Type: application/json' \
  -d '{"source_folder": "tests/fixtures/images", "initial_labels": ["x"], "export_format": "coco"}'
```
Expected: 201 with project body.

- [ ] **Step 6: Update CHANGELOG.md**

Edit `CHANGELOG.md`. Replace the `[Unreleased]` section header with `[0.1.0] - <today's date>`. Move existing notes under it.

- [ ] **Step 7: Commit + tag**

```bash
git add CHANGELOG.md
git commit -m "chore: release v0.1.0"
git tag -a v0.1.0 -m "v0.1.0 — first OSS-publishable release"
git log --oneline | head -20
```

- [ ] **Step 8: (When ready) Push tag to trigger release workflow**

When you're ready to publish:
```bash
git push origin main
git push origin v0.1.0
```

---

## Done Criteria

After all 19 tasks:

- [x] 4 export formats implemented + tested (COCO, YOLO, VOC, ls_json)
- [x] `POST /api/projects/{pid}/exports` works end-to-end
- [x] MCP server exposes all 3 real tools
- [x] README + README_zh + CONTRIBUTING + CODE_OF_CONDUCT + SECURITY + CHANGELOG
- [x] `docs/architecture.md` + `docs/development.md` + `docs/api.md` + `docs/extending.md`
- [x] CI workflow runs lint + type + test on push/PR
- [x] Release workflow builds wheels + frontend tarball on tag
- [x] Issue + PR templates
- [x] `make test && make lint && make typecheck` all green
- [x] Git tag `v0.1.0` exists

## What's NOT in this plan (deferred to v2)

- Qwen-VL integration (zero-shot bbox suggestions)
- Mask / polygon annotations
- Undo/redo
- Multi-user / OIDC auth
- Active learning sampling
- Real demo GIF (manual recording task)

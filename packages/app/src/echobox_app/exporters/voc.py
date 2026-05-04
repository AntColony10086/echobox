"""Pascal VOC format exporter (per-image XML + ImageSets/Main split lists)."""

from xml.etree import ElementTree as ET  # noqa: N817

from echobox_app.exporters.base import (
    ExportContext,
    Exporter,
    ExportStats,
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

        (ctx.export_dir / "labels.txt").write_text("\n".join(name for name, _ in ctx.labels) + "\n")

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
                _write_voc_xml(ctx.export_dir / "Annotations" / f"{stem}.xml", img, anns)
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

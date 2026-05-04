"""YOLO format exporter (per-image .txt files, normalized cx/cy/w/h)."""

from echobox_app.exporters.base import (
    ExportContext,
    Exporter,
    ExportStats,
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

"""Label Studio JSON export (rectanglelabels with percent coords)."""

import json
import uuid

from echobox_app.exporters.base import (
    ExportContext,
    Exporter,
    ExportStats,
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
                tasks.append(
                    {
                        "data": {"image": f"images/{img.filename}"},
                        "annotations": [{"result": results}] if results else [],
                    }
                )
                stats.add_image(split, len(anns))
            (ctx.export_dir / f"{split}.json").write_text(
                json.dumps(tasks, indent=2, ensure_ascii=False)
            )
        return stats

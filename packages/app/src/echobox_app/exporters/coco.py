"""Standard COCO instances format exporter."""

import json
from datetime import UTC, datetime
from typing import Any

from echobox_app.exporters.base import (
    ExportContext,
    Exporter,
    ExportStats,
    filter_annotations,
    make_image_symlink,
)


class COCOExporter(Exporter):
    name = "coco"

    def export(self, ctx: ExportContext) -> ExportStats:
        ctx.export_dir.mkdir(parents=True, exist_ok=True)
        stats = ExportStats()

        categories = [
            {"id": idx + 1, "name": name, "supercategory": "object"}
            for idx, (name, _color) in enumerate(ctx.labels)
        ]
        label_to_id = {name: idx + 1 for idx, (name, _) in enumerate(ctx.labels)}

        for split in ctx.splits:
            split_images = [img for img in ctx.images if img.split == split]
            payload: dict[str, Any] = {
                "info": {
                    "description": f"echobox export for project {ctx.project_id}",
                    "date_created": datetime.now(UTC).isoformat(),
                },
                "licenses": [{"id": 1, "name": "Apache-2.0"}],
                "images": [],
                "annotations": [],
                "categories": categories,
            }

            ann_id_seq = 1
            for img in split_images:
                make_image_symlink(img, ctx.symlink_image_dir)
                payload["images"].append(
                    {
                        "id": img.id,
                        "file_name": img.filename,
                        "width": img.width,
                        "height": img.height,
                        "license": 1,
                    }
                )
                anns = filter_annotations(
                    ctx.annotations_by_image.get(img.id, []),
                    ctx.include_pending,
                )
                for ann in anns:
                    w = ann.x2 - ann.x1
                    h = ann.y2 - ann.y1
                    payload["annotations"].append(
                        {
                            "id": ann_id_seq,
                            "image_id": img.id,
                            "category_id": label_to_id[ann.label.name],
                            "bbox": [ann.x1, ann.y1, w, h],
                            "area": w * h,
                            "iscrowd": 0,
                            "score": ann.score,
                            "_source": ann.source,
                        }
                    )
                    ann_id_seq += 1
                stats.add_image(split, len(anns))

            (ctx.export_dir / f"{split}.json").write_text(
                json.dumps(payload, indent=2, ensure_ascii=False)
            )

        return stats

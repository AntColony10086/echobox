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

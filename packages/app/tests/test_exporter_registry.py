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

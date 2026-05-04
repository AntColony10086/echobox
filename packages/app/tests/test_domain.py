from pathlib import Path

import pytest
from echobox_app.domain.inventory import ImageInventory, ScanResult
from echobox_app.domain.messages import Message
from echobox_app.domain.organize import ImageEntry, OrganizeResult
from echobox_app.domain.splits import SplitConfig


def test_image_inventory_counts() -> None:
    inv = ImageInventory(
        total_files=10,
        valid_count=8,
        invalid_count=2,
        formats={".jpg": 6, ".png": 2},
        sample_paths=[Path("/a.jpg"), Path("/b.jpg")],
        invalid_paths=[Path("/x.txt"), Path("/y.gif")],
    )
    assert inv.total_files == 10
    assert inv.valid_count == 8
    assert inv.invalid_count == 2


def test_scan_result_serialization() -> None:
    sr = ScanResult(
        folder=Path("/data"),
        inventory=ImageInventory(
            total_files=2,
            valid_count=2,
            invalid_count=0,
            formats={".jpg": 2},
            sample_paths=[],
            invalid_paths=[],
        ),
    )
    d = sr.to_dict()
    assert d["folder"] == "/data"
    assert d["inventory"]["valid_count"] == 2


def test_split_config_validates_ratios() -> None:
    sc = SplitConfig(train=0.7, val=0.15, test=0.15, seed=42)
    assert sc.is_valid()

    bad = SplitConfig(train=0.5, val=0.3, test=0.3, seed=42)
    assert not bad.is_valid()


def test_split_config_assignment() -> None:
    sc = SplitConfig(train=0.7, val=0.15, test=0.15, seed=42)
    sc.assignments = {"00001.jpg": "train", "00002.jpg": "val"}
    assert sc.assignments["00001.jpg"] == "train"


def test_organize_result_with_entries() -> None:
    res = OrganizeResult(
        copied_count=2,
        entries=[
            ImageEntry(
                canonical="00001.jpg",
                source=Path("/orig/a.jpg"),
                sha256="abc",
                bytes=100,
                width=10,
                height=10,
            ),
            ImageEntry(
                canonical="00002.jpg",
                source=Path("/orig/b.jpg"),
                sha256="def",
                bytes=200,
                width=20,
                height=20,
            ),
        ],
    )
    assert res.copied_count == 2
    assert res.entries[0].canonical == "00001.jpg"


def test_message_roles() -> None:
    m = Message(role="user", content="hello")
    assert m.role == "user"

    with pytest.raises(ValueError):
        Message(role="invalid", content="x")  # type: ignore[arg-type]

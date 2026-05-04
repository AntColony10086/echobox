from dataclasses import dataclass

import pytest
from echobox_app.domain.inventory import ImageInventory
from echobox_app.domain.organize import ImageEntry
from echobox_app.domain.splits import SplitConfig
from echobox_app.errors import ValidationError
from echobox_app.tools.project import (
    FinalizeResult,
    critic_check,
    set_export_format,
)


@dataclass
class _State:
    inventory: ImageInventory | None = None
    canonical_images: list[ImageEntry] | None = None
    splits: SplitConfig | None = None
    labels: list[str] | None = None
    export_format: str | None = None


def test_set_export_format_accepts_known() -> None:
    for fmt in ("coco", "yolo", "voc", "ls_json"):
        assert set_export_format(fmt) == fmt


def test_set_export_format_rejects_unknown() -> None:
    with pytest.raises(ValidationError):
        set_export_format("kaggle")


def _ready_state() -> _State:
    sc = SplitConfig(train=0.7, val=0.15, test=0.15, seed=42)
    sc.assignments = {"00001.jpg": "train"}
    return _State(
        inventory=ImageInventory(
            total_files=1,
            valid_count=1,
            invalid_count=0,
            formats={".jpg": 1},
            sample_paths=[],
        ),
        canonical_images=[
            ImageEntry(
                canonical="00001.jpg",
                source=__import__("pathlib").Path("/x"),
                sha256="a",
                bytes=1,
                width=1,
                height=1,
            )
        ],
        splits=sc,
        labels=["crack"],
        export_format="coco",
    )


def test_critic_passes_on_complete_state() -> None:
    errs = critic_check(_ready_state())

    assert errs == []


def test_critic_flags_missing_inventory() -> None:
    state = _ready_state()
    state.inventory = None
    errs = critic_check(state)

    assert any("inventory" in e for e in errs)


def test_critic_flags_no_canonical_images() -> None:
    state = _ready_state()
    state.canonical_images = []
    errs = critic_check(state)

    assert any("canonical" in e or "organize" in e for e in errs)


def test_critic_flags_invalid_split() -> None:
    state = _ready_state()
    state.splits = SplitConfig(train=0.5, val=0.3, test=0.3, seed=42)
    errs = critic_check(state)

    assert any("split" in e for e in errs)


def test_critic_flags_missing_labels() -> None:
    state = _ready_state()
    state.labels = []
    errs = critic_check(state)

    assert any("label" in e for e in errs)


def test_critic_flags_missing_format() -> None:
    state = _ready_state()
    state.export_format = None
    errs = critic_check(state)

    assert any("format" in e for e in errs)


def test_finalize_result_dataclass() -> None:
    r = FinalizeResult(success=True, errors=[])
    assert r.success
    assert r.errors == []

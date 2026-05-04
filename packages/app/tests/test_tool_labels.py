from pathlib import Path

import pytest
from echobox_app.tools.labels import propose_labels, set_labels, validate_label_name


def test_set_labels_dedups_and_validates() -> None:
    out = set_labels(["crack", "rust", "crack", "no_crack"])

    assert out == ["crack", "rust", "no_crack"]


def test_set_labels_rejects_invalid_name() -> None:
    from echobox_app.errors import ValidationError

    with pytest.raises(ValidationError):
        set_labels(["crack", "bad name with space"])


def test_set_labels_rejects_empty() -> None:
    from echobox_app.errors import ValidationError

    with pytest.raises(ValidationError):
        set_labels([])


def test_validate_label_name() -> None:
    assert validate_label_name("crack")
    assert validate_label_name("no_crack")
    assert validate_label_name("class-1")
    assert not validate_label_name("")
    assert not validate_label_name("with space")
    assert not validate_label_name("emoji-🚀")


def test_propose_labels_from_class_subdirs(tmp_path: Path) -> None:
    (tmp_path / "positive").mkdir()
    (tmp_path / "positive" / "img.jpg").write_text("x")
    (tmp_path / "negative").mkdir()
    (tmp_path / "negative" / "img.jpg").write_text("x")

    suggestions = propose_labels(tmp_path)

    assert sorted(suggestions) == ["negative", "positive"]


def test_propose_labels_returns_empty_when_no_subdirs(tmp_path: Path) -> None:
    (tmp_path / "a.jpg").write_text("x")

    suggestions = propose_labels(tmp_path)

    assert suggestions == []


def test_propose_labels_skips_invalid_dir_names(tmp_path: Path) -> None:
    (tmp_path / "good_class").mkdir()
    (tmp_path / "good_class" / "i.jpg").write_text("x")
    (tmp_path / "bad name with space").mkdir()
    (tmp_path / "bad name with space" / "i.jpg").write_text("x")

    suggestions = propose_labels(tmp_path)

    assert suggestions == ["good_class"]

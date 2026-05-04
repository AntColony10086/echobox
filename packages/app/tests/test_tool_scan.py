from pathlib import Path

import pytest
from echobox_app.tools.filesystem import scan_folder
from PIL import Image


def _make_image(path: Path, fmt: str = "JPEG", size: tuple[int, int] = (10, 10)) -> None:
    Image.new("RGB", size, color=(255, 0, 0)).save(path, fmt)


def test_scan_empty_folder_raises(tmp_path: Path) -> None:
    from echobox_app.errors import ValidationError

    with pytest.raises(ValidationError):
        scan_folder(tmp_path)


def test_scan_finds_images(tmp_path: Path) -> None:
    _make_image(tmp_path / "a.jpg")
    _make_image(tmp_path / "b.png", fmt="PNG")
    (tmp_path / "readme.txt").write_text("ignore me")

    res = scan_folder(tmp_path)

    assert res.folder == tmp_path
    assert res.inventory.valid_count == 2
    assert res.inventory.invalid_count == 0
    assert res.inventory.total_files == 2
    assert res.inventory.formats[".jpg"] == 1
    assert res.inventory.formats[".png"] == 1


def test_scan_recursive(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    _make_image(tmp_path / "a.jpg")
    _make_image(sub / "b.jpg")

    res = scan_folder(tmp_path)

    assert res.inventory.valid_count == 2


def test_scan_detects_corrupted_image(tmp_path: Path) -> None:
    (tmp_path / "broken.jpg").write_text("not a real image")
    _make_image(tmp_path / "good.jpg")

    res = scan_folder(tmp_path)

    assert res.inventory.valid_count == 1
    assert res.inventory.invalid_count == 1
    assert res.inventory.invalid_paths[0].name == "broken.jpg"


def test_scan_nonexistent_folder_raises(tmp_path: Path) -> None:
    from echobox_app.errors import ValidationError

    with pytest.raises(ValidationError):
        scan_folder(tmp_path / "nope")

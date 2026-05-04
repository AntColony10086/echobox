from pathlib import Path

from echobox_app.domain.inventory import ImageInventory, ScanResult
from echobox_app.tools.filesystem import organize_images
from echobox_app.workspace.manager import WorkspaceManager
from PIL import Image


def _make_image(path: Path, size: tuple[int, int] = (10, 20)) -> None:
    Image.new("RGB", size, color=(0, 255, 0)).save(path, "JPEG")


def test_organize_copies_files_with_canonical_names(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    _make_image(src / "a.jpg")
    _make_image(src / "b.jpg")

    inv = ImageInventory(
        total_files=2,
        valid_count=2,
        invalid_count=0,
        formats={".jpg": 2},
        sample_paths=[src / "a.jpg", src / "b.jpg"],
    )
    sr = ScanResult(folder=src, inventory=inv)
    wm = WorkspaceManager(root=tmp_path / "data", project_id=1)
    wm.init_directories()

    res = organize_images(sr, wm)

    assert res.copied_count == 2
    assert (wm.image_dir / "00001.jpg").exists()
    assert (wm.image_dir / "00002.jpg").exists()
    assert (src / "a.jpg").exists()
    assert res.entries[0].width == 10
    assert res.entries[0].height == 20
    assert res.entries[0].canonical == "00001.jpg"
    assert len(res.entries[0].sha256) == 64


def test_organize_preserves_extension(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    Image.new("RGB", (5, 5)).save(src / "x.png", "PNG")

    inv = ImageInventory(
        total_files=1,
        valid_count=1,
        invalid_count=0,
        formats={".png": 1},
        sample_paths=[src / "x.png"],
    )
    sr = ScanResult(folder=src, inventory=inv)
    wm = WorkspaceManager(root=tmp_path / "data", project_id=2)
    wm.init_directories()

    organize_images(sr, wm)

    assert (wm.image_dir / "00001.png").exists()


def test_organize_writes_mapping_json(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    _make_image(src / "a.jpg")

    inv = ImageInventory(
        total_files=1,
        valid_count=1,
        invalid_count=0,
        formats={".jpg": 1},
        sample_paths=[src / "a.jpg"],
    )
    sr = ScanResult(folder=src, inventory=inv)
    wm = WorkspaceManager(root=tmp_path / "data", project_id=3)
    wm.init_directories()

    organize_images(sr, wm)

    assert (wm.data_dir / "mapping.json").exists()

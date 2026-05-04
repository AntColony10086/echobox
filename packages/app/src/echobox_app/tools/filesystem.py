"""Filesystem tools: scan_folder, organize_images."""

import hashlib
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from echobox_app.domain.inventory import ImageInventory, ScanResult
from echobox_app.domain.organize import ImageEntry, OrganizeResult
from echobox_app.errors import ValidationError
from echobox_app.workspace.manager import WorkspaceManager

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
MAX_SAMPLE = 5


def scan_folder(folder: Path) -> ScanResult:
    """Recursively scan `folder` for image files, validate each via PIL."""
    if not folder.exists():
        raise ValidationError(
            f"folder not found: {folder}",
            detail={"folder": str(folder)},
        )
    if not folder.is_dir():
        raise ValidationError(
            f"path is not a directory: {folder}",
            detail={"folder": str(folder)},
        )

    valid: list[Path] = []
    invalid: list[Path] = []
    formats: Counter[str] = Counter()

    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTS:
            continue
        try:
            with Image.open(path) as img:
                img.verify()
            valid.append(path)
            formats[ext] += 1
        except (UnidentifiedImageError, OSError, SyntaxError):
            invalid.append(path)

    if not valid:
        raise ValidationError(
            f"no valid images found in {folder}",
            detail={"folder": str(folder), "invalid_count": len(invalid)},
        )

    inventory = ImageInventory(
        total_files=len(valid),
        valid_count=len(valid),
        invalid_count=len(invalid),
        formats=dict(formats),
        sample_paths=valid[:MAX_SAMPLE],
        invalid_paths=invalid,
    )
    return ScanResult(folder=folder, inventory=inventory)


def _sha256_of_file(path: Path, chunk: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            data = f.read(chunk)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def organize_images(scan: ScanResult, workspace: WorkspaceManager) -> OrganizeResult:
    """Copy valid images from scan into workspace.image_dir as 00001.<ext> ..."""
    workspace.init_directories()
    entries: list[ImageEntry] = []

    valid_paths: list[Path] = []
    for p in sorted(scan.folder.rglob("*")):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            try:
                with Image.open(p) as img:
                    img.verify()
                valid_paths.append(p)
            except (UnidentifiedImageError, OSError, SyntaxError):
                continue

    for idx, src_path in enumerate(valid_paths, start=1):
        ext = src_path.suffix.lower()
        canonical = f"{idx:05d}{ext}"
        dst = workspace.image_dir / canonical
        shutil.copy2(src_path, dst)

        with Image.open(dst) as img:
            width, height = img.size
        sha = _sha256_of_file(dst)
        entries.append(
            ImageEntry(
                canonical=canonical,
                source=src_path,
                sha256=sha,
                bytes=dst.stat().st_size,
                width=width,
                height=height,
            )
        )

    result = OrganizeResult(copied_count=len(entries), entries=entries)
    workspace.write_mapping(result)
    return result

from pathlib import Path

from echobox_app.exporters.base import ExportContext, ExportStats


def test_export_context_path_helpers(tmp_path: Path) -> None:
    ctx = ExportContext(
        project_id=7,
        project_name="test",
        workspace_path=tmp_path,
        export_dir=tmp_path / "exports" / "ts-coco",
        labels=[("crack", "#000")],
        images=[],
        annotations_by_image={},
        include_pending=False,
        splits=("train", "val", "test"),
    )
    assert ctx.symlink_image_dir.parent == ctx.export_dir


def test_export_stats_aggregation() -> None:
    s = ExportStats()
    s.add_image("train", 3)
    s.add_image("train", 5)
    s.add_image("val", 2)
    assert s.total_images == 3
    assert s.total_annotations == 10
    assert s.by_split["train"]["images"] == 2
    assert s.by_split["train"]["annotations"] == 8

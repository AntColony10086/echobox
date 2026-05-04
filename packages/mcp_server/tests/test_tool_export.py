from unittest.mock import AsyncMock

import pytest
from echobox_mcp.tools.export_dataset import EXPORT_DATASET_TOOL, handle_export_dataset


@pytest.mark.asyncio
async def test_export_passes_format_and_includes() -> None:
    fake_client = AsyncMock()
    fake_client.create_export = AsyncMock(
        return_value={
            "export_id": "ts-coco",
            "format": "coco",
            "output_dir": "/x",
            "files": ["train.json"],
            "stats": {"total_images": 1, "total_annotations": 5, "by_split": {}},
            "elapsed_ms": 12,
        }
    )

    result = await handle_export_dataset(
        fake_client,
        {
            "project_id": 7,
            "format": "coco",
            "include_pending": True,
        },
    )

    assert result["format"] == "coco"
    assert result["stats"]["total_annotations"] == 5
    fake_client.create_export.assert_awaited_with(
        pid=7,
        fmt="coco",
        include_pending=True,
        splits=None,
    )


def test_tool_required_field() -> None:
    assert EXPORT_DATASET_TOOL.name == "export_dataset"
    assert "project_id" in EXPORT_DATASET_TOOL.inputSchema["required"]

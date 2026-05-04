from unittest.mock import AsyncMock

import pytest
from echobox_mcp.tools.search_annotations import (
    SEARCH_ANNOTATIONS_TOOL,
    handle_search_annotations,
)


@pytest.mark.asyncio
async def test_search_passes_filters_and_returns_envelope() -> None:
    fake_client = AsyncMock()
    fake_client.list_annotations = AsyncMock(
        return_value={
            "total": 5,
            "returned": 5,
            "items": [],
            "facets": {
                "by_label": {"crack": 5},
                "by_split": {"train": 5},
                "by_source": {"user": 5},
            },
        }
    )

    result = await handle_search_annotations(
        fake_client,
        {
            "project_id": 7,
            "label": "crack",
            "split": "train",
        },
    )

    assert result["total"] == 5
    fake_client.list_annotations.assert_awaited_with(
        pid=7,
        label="crack",
        source="any",
        split="train",
        min_score=None,
        image_filename_glob=None,
        limit=100,
        offset=0,
    )


def test_tool_schema_includes_facets_in_description() -> None:
    assert SEARCH_ANNOTATIONS_TOOL.name == "search_annotations"
    assert "project_id" in SEARCH_ANNOTATIONS_TOOL.inputSchema["properties"]

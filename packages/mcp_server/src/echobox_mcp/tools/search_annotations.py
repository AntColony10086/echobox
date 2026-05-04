"""MCP tool: search_annotations."""

from typing import Any

from mcp.types import Tool

from echobox_mcp.client import AppClient

SEARCH_ANNOTATIONS_TOOL = Tool(
    name="search_annotations",
    description=(
        "Search annotations across an annotation project. Returns matching "
        "annotations with their image context, plus aggregated facets "
        "(by_label, by_split, by_source) for analysis."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {"type": "integer"},
            "label": {"type": "string", "description": "Exact label name to filter."},
            "source": {
                "type": "string",
                "enum": ["user", "geco2_accepted", "user_edited", "any"],
                "description": "Annotation source filter (default 'any').",
            },
            "split": {
                "type": "string",
                "enum": ["train", "val", "test", "any"],
                "description": "Train/val/test filter (default 'any').",
            },
            "min_score": {"type": "number", "description": "Min GECO2 score (0..1)."},
            "image_filename_glob": {"type": "string", "description": "Like '*.jpg'."},
            "limit": {"type": "integer", "minimum": 1, "maximum": 1000},
            "offset": {"type": "integer", "minimum": 0},
        },
        "required": ["project_id"],
    },
)


async def handle_search_annotations(
    client: AppClient,
    args: dict[str, Any],
) -> dict[str, Any]:
    return await client.list_annotations(
        pid=int(args["project_id"]),
        label=args.get("label"),
        source=args.get("source", "any"),
        split=args.get("split", "any"),
        min_score=args.get("min_score"),
        image_filename_glob=args.get("image_filename_glob"),
        limit=int(args.get("limit", 100)),
        offset=int(args.get("offset", 0)),
    )

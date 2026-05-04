"""MCP tool: export_dataset."""

from typing import Any

from mcp.types import Tool

from echobox_mcp.client import AppClient

EXPORT_DATASET_TOOL = Tool(
    name="export_dataset",
    description=(
        "Export a project's annotations to disk in the chosen format. "
        "Output is in <workspace>/exports/<timestamp>-<format>/. "
        "Returns the absolute output path + per-split statistics."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {"type": "integer"},
            "format": {
                "type": "string",
                "enum": ["coco", "yolo", "voc", "ls_json"],
                "description": "Export format. Defaults to project's saved choice.",
            },
            "include_pending": {
                "type": "boolean",
                "description": "Include GECO2 pending boxes (default false).",
            },
            "splits": {
                "type": "array",
                "items": {"type": "string", "enum": ["train", "val", "test"]},
                "description": "Subset of splits to export (default all).",
            },
        },
        "required": ["project_id"],
    },
)


async def handle_export_dataset(
    client: AppClient,
    args: dict[str, Any],
) -> dict[str, Any]:
    return await client.create_export(
        pid=int(args["project_id"]),
        fmt=args.get("format"),
        include_pending=bool(args.get("include_pending", False)),
        splits=args.get("splits"),
    )

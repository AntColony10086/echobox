"""MCP tool: start_annotation_project."""

from pathlib import Path
from typing import Any

from mcp.types import Tool

from echobox_mcp.client import AppClient

START_PROJECT_TOOL = Tool(
    name="start_annotation_project",
    description=(
        "Create a new annotation project from a folder of images. "
        "Returns a setup URL the user opens in a browser to complete "
        "interactive (chat-driven) configuration. Optional parameters "
        "pre-populate the setup cards (user can still edit before clicking 'Start')."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "folder": {
                "type": "string",
                "description": "Absolute path to the folder containing images.",
            },
            "name": {
                "type": "string",
                "description": "Project name (defaults to <folder>-<date>).",
            },
            "initial_labels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Pre-fill the label set.",
            },
            "train_val_test": {
                "type": "array",
                "items": {"type": "number"},
                "minItems": 3,
                "maxItems": 3,
                "description": "Train/val/test ratios that sum to 1.0.",
            },
            "export_format": {
                "type": "string",
                "enum": ["coco", "yolo", "voc", "ls_json"],
                "description": "Export format (defaults to 'coco').",
            },
        },
        "required": ["folder"],
    },
)


async def handle_start_project(client: AppClient, args: dict[str, Any]) -> dict[str, Any]:
    folder = args.get("folder")
    if not folder:
        return {"error": "validation_failed", "detail": "folder required"}
    if not Path(folder).exists():  # noqa: ASYNC240
        return {"error": "folder_not_found", "detail": str(folder)}
    if not Path(folder).is_dir():  # noqa: ASYNC240
        return {"error": "folder_not_readable", "detail": f"{folder} is not a directory"}

    train_val_test_arg = args.get("train_val_test")
    train_val_test: tuple[float, float, float] | None = None
    if train_val_test_arg is not None:
        train_val_test = (
            float(train_val_test_arg[0]),
            float(train_val_test_arg[1]),
            float(train_val_test_arg[2]),
        )

    project = await client.create_project(
        folder=folder,
        name=args.get("name"),
        initial_labels=args.get("initial_labels"),
        train_val_test=train_val_test,
        export_format=args.get("export_format"),
    )

    return {
        "project_id": project["id"],
        "name": project["name"],
        "setup_url": f"http://localhost:5173/setup?project_id={project['id']}",
        "status": project["status"],
        "image_count_pending_scan": None,
        "message": (
            "Project created. Open setup_url in a browser to drive the conversational "
            "setup (scan/organize/split/labels/format). When ready click '开始标注' to "
            "transition to status='annotating'."
        ),
    }

"""MCP server: registers 3 tools (start_project, search, export)."""

import json
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from echobox_mcp.client import AppClient
from echobox_mcp.config import MCPSettings
from echobox_mcp.tools.export_dataset import (
    EXPORT_DATASET_TOOL,
    handle_export_dataset,
)
from echobox_mcp.tools.search_annotations import (
    SEARCH_ANNOTATIONS_TOOL,
    handle_search_annotations,
)
from echobox_mcp.tools.start_project import (
    START_PROJECT_TOOL,
    handle_start_project,
)

ALL_TOOLS: list[Tool] = [
    START_PROJECT_TOOL,
    SEARCH_ANNOTATIONS_TOOL,
    EXPORT_DATASET_TOOL,
]


def build_server(settings: MCPSettings | None = None) -> Server:
    settings = settings or MCPSettings()
    server = Server("echobox")
    client = AppClient(base_url=settings.app_url, timeout_s=settings.app_request_timeout_s)

    @server.list_tools()  # type: ignore[no-untyped-call,untyped-decorator]
    async def list_tools() -> list[Tool]:
        return ALL_TOOLS

    @server.call_tool()  # type: ignore[untyped-decorator]
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if name == "start_annotation_project":
            result = await handle_start_project(client, arguments)
        elif name == "search_annotations":
            result = await handle_search_annotations(client, arguments)
        elif name == "export_dataset":
            result = await handle_export_dataset(client, arguments)
        else:
            result = {"error": "unknown_tool", "detail": f"no tool named {name!r}"}

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    return server


def run() -> None:
    """Entry point for `echobox-mcp` console script."""
    import asyncio

    from mcp.server.stdio import stdio_server

    settings = MCPSettings()
    server = build_server(settings)

    async def _serve() -> None:
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    asyncio.run(_serve())

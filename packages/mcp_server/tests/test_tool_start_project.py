from unittest.mock import AsyncMock

import pytest
from echobox_mcp.tools.start_project import START_PROJECT_TOOL, handle_start_project


@pytest.mark.asyncio
async def test_start_project_returns_setup_url(tmp_path) -> None:  # type: ignore[no-untyped-def]
    folder = tmp_path / "imgs"
    folder.mkdir()
    (folder / "a.jpg").write_text("x")

    fake_client = AsyncMock()
    fake_client.create_project = AsyncMock(
        return_value={
            "id": 7,
            "name": "imgs-20260504",
            "status": "draft",
            "source_folder": str(folder),
            "workspace_path": str(tmp_path / "ws"),
        }
    )

    result = await handle_start_project(fake_client, {"folder": str(folder)})

    assert result["project_id"] == 7
    assert "setup_url" in result
    assert "5173" in result["setup_url"]
    assert "project_id=7" in result["setup_url"]
    fake_client.create_project.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_project_passes_through_optional_args(tmp_path) -> None:  # type: ignore[no-untyped-def]
    folder = tmp_path / "imgs"
    folder.mkdir()

    fake_client = AsyncMock()
    fake_client.create_project = AsyncMock(
        return_value={
            "id": 1,
            "name": "x",
            "status": "draft",
            "source_folder": str(folder),
            "workspace_path": "/x",
        }
    )

    await handle_start_project(
        fake_client,
        {
            "folder": str(folder),
            "name": "myproj",
            "initial_labels": ["crack"],
            "train_val_test": [0.8, 0.1, 0.1],
            "export_format": "yolo",
        },
    )

    call_args = fake_client.create_project.call_args.kwargs
    assert call_args["name"] == "myproj"
    assert call_args["initial_labels"] == ["crack"]
    assert call_args["train_val_test"] == (0.8, 0.1, 0.1)
    assert call_args["export_format"] == "yolo"


@pytest.mark.asyncio
async def test_start_project_folder_not_found(tmp_path) -> None:  # type: ignore[no-untyped-def]
    fake_client = AsyncMock()

    result = await handle_start_project(fake_client, {"folder": str(tmp_path / "nope")})

    assert result["error"] == "folder_not_found"


def test_tool_schema_has_required_field() -> None:
    assert START_PROJECT_TOOL.name == "start_annotation_project"
    schema = START_PROJECT_TOOL.inputSchema
    assert "folder" in schema["properties"]
    assert "folder" in schema["required"]

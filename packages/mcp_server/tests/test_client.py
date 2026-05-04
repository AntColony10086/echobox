import httpx
import pytest
from echobox_mcp.client import AppClient


@pytest.mark.asyncio
async def test_create_project_calls_app() -> None:
    captured: dict[str, object] = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["url"] = str(req.url)
        captured["body"] = req.content
        return httpx.Response(
            201,
            json={
                "id": 7,
                "name": "x",
                "status": "draft",
                "source_folder": "/orig",
                "workspace_path": "/ws",
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as ac:
        client = AppClient(http=ac)
        result = await client.create_project(folder="/orig", name="x")

    assert result["id"] == 7
    assert "/api/projects" in captured["url"]


@pytest.mark.asyncio
async def test_list_annotations_with_filters() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        path = req.url.path
        if path == "/api/projects/7":
            return httpx.Response(200, json={"id": 7, "labels": []})
        if path == "/api/projects/7/images":
            return httpx.Response(
                200,
                json={
                    "items": [
                        {"id": 1, "filename": "a.jpg", "split": "train", "abs_path": "/a.jpg"},
                        {"id": 2, "filename": "b.jpg", "split": "train", "abs_path": "/b.jpg"},
                    ]
                },
            )
        if path.endswith("/annotations"):
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "id": 100,
                            "label": {"name": "crack"},
                            "bbox": [1, 2, 3, 4],
                            "score": 0.9,
                            "source": "user",
                        },
                    ]
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as ac:
        client = AppClient(http=ac)
        result = await client.list_annotations(pid=7)

    # 2 images each with 1 annotation = 2 total annotations
    assert len(result["items"]) == 2


@pytest.mark.asyncio
async def test_create_export() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "export_id": "ts-coco",
                "format": "coco",
                "output_dir": "/x",
                "files": ["train.json"],
                "stats": {"total_images": 1, "total_annotations": 1, "by_split": {}},
                "elapsed_ms": 5,
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as ac:
        client = AppClient(http=ac)
        result = await client.create_export(pid=7, fmt="coco")

    assert result["format"] == "coco"

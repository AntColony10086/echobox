import httpx
import pytest
from echobox_app.ml_client.client import MLBackendClient


@pytest.mark.asyncio
async def test_predict_similar_returns_parsed_response() -> None:
    transport = httpx.MockTransport(
        lambda req: httpx.Response(
            200,
            json={
                "predictions": [{"bbox": [1, 2, 3, 4], "score": 0.9}],
                "exemplar_count": 1,
                "image_size": [100, 200],
                "elapsed_ms": 50,
            },
        )
    )
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as ac:
        client = MLBackendClient(http=ac)

        result = await client.predict_similar("/img.jpg", (0, 0, 50, 50))

    assert result["predictions"][0]["bbox"] == [1, 2, 3, 4]
    assert result["elapsed_ms"] == 50


@pytest.mark.asyncio
async def test_predict_similar_503_raises_unavailable() -> None:
    from echobox_app.errors import MLBackendUnavailable

    transport = httpx.MockTransport(lambda req: httpx.Response(503))
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as ac:
        client = MLBackendClient(http=ac)
        with pytest.raises(MLBackendUnavailable):
            await client.predict_similar("/img.jpg", (0, 0, 1, 1))


@pytest.mark.asyncio
async def test_predict_similar_404_raises_image_not_found() -> None:
    from echobox_app.errors import ImageNotFound

    transport = httpx.MockTransport(
        lambda req: httpx.Response(404, json={"error": "image_not_found", "detail": "nope"})
    )
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as ac:
        client = MLBackendClient(http=ac)
        with pytest.raises(ImageNotFound):
            await client.predict_similar("/img.jpg", (0, 0, 1, 1))

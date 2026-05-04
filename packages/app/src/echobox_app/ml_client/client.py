"""Async HTTP client for ml_backend POST /predict_similar."""

from typing import Any

import httpx

from echobox_app.errors import ImageNotFound, MLBackendUnavailable


class MLBackendClient:
    def __init__(
        self,
        http: httpx.AsyncClient | None = None,
        base_url: str = "http://localhost:9090",
        timeout_s: float = 30.0,
    ) -> None:
        self._http = http or httpx.AsyncClient(base_url=base_url, timeout=timeout_s)
        self._owns_http = http is None

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def predict_similar(
        self,
        image_path: str,
        exemplar_bbox: tuple[int, int, int, int],
        max_predictions: int = 200,
        score_threshold: float = 0.25,
    ) -> dict[str, Any]:
        try:
            resp = await self._http.post(
                "/predict_similar",
                json={
                    "image_path": image_path,
                    "exemplar_bbox": list(exemplar_bbox),
                    "max_predictions": max_predictions,
                    "score_threshold": score_threshold,
                },
            )
        except httpx.RequestError as e:
            raise MLBackendUnavailable(
                f"ml_backend request failed: {e}",
                detail={"image_path": image_path},
            ) from e

        if resp.status_code == 404:
            body = resp.json()
            raise ImageNotFound(
                body.get("detail", "image not found"),
                detail={"image_path": image_path},
            )
        if resp.status_code >= 500 or resp.status_code == 503:
            raise MLBackendUnavailable(
                f"ml_backend returned {resp.status_code}",
                detail={"body": resp.text[:500]},
            )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

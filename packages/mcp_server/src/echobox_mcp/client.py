"""HTTP client wrapping the app's REST API."""

from typing import Any

import httpx


class AppClient:
    def __init__(
        self,
        http: httpx.AsyncClient | None = None,
        base_url: str = "http://localhost:8000",
        timeout_s: float = 60.0,
    ) -> None:
        self._http = http or httpx.AsyncClient(base_url=base_url, timeout=timeout_s)
        self._owns = http is None

    async def aclose(self) -> None:
        if self._owns:
            await self._http.aclose()

    async def healthz(self) -> dict[str, Any]:
        r = await self._http.get("/healthz")
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]

    async def create_project(
        self,
        folder: str,
        name: str | None = None,
        initial_labels: list[str] | None = None,
        train_val_test: tuple[float, float, float] | None = None,
        export_format: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"source_folder": folder}
        if name is not None:
            body["name"] = name
        if initial_labels is not None:
            body["initial_labels"] = initial_labels
        if train_val_test is not None:
            body["train_val_test"] = list(train_val_test)
        if export_format is not None:
            body["export_format"] = export_format
        r = await self._http.post("/api/projects", json=body)
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]

    async def get_project(self, pid: int) -> dict[str, Any]:
        r = await self._http.get(f"/api/projects/{pid}")
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]

    async def list_annotations(
        self,
        pid: int,
        label: str | None = None,
        source: str | None = None,
        split: str | None = None,
        min_score: float | None = None,
        image_filename_glob: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        # Aggregates across all images of the project (client-side helper).
        await self.get_project(pid)
        images = await self._http.get(f"/api/projects/{pid}/images")
        images.raise_for_status()
        all_imgs = images.json().get("items", [])
        items: list[dict[str, Any]] = []
        for img in all_imgs:
            if split and split != "any" and img["split"] != split:
                continue
            if image_filename_glob:
                from fnmatch import fnmatch

                if not fnmatch(img["filename"], image_filename_glob):
                    continue
            anns_resp = await self._http.get(f"/api/images/{img['id']}/annotations")
            anns_resp.raise_for_status()
            for a in anns_resp.json().get("items", []):
                if label and a["label"]["name"] != label:
                    continue
                if source and source != "any" and a["source"] != source:
                    continue
                if min_score is not None and (a["score"] or 0.0) < min_score:
                    continue
                items.append(
                    {
                        "annotation_id": a["id"],
                        "image_id": img["id"],
                        "image_filename": img["filename"],
                        "image_abs_path": img["abs_path"],
                        "image_split": img["split"],
                        "label": a["label"]["name"],
                        "bbox": a["bbox"],
                        "score": a["score"],
                        "source": a["source"],
                    }
                )
        facets: dict[str, dict[str, int]] = {
            "by_label": {},
            "by_split": {},
            "by_source": {},
        }
        for it in items:
            for k, v in (
                ("by_label", it["label"]),
                ("by_split", it["image_split"]),
                ("by_source", it["source"]),
            ):
                facets[k][v] = facets[k].get(v, 0) + 1
        total = len(items)
        return {
            "total": total,
            "returned": min(limit, total - offset),
            "items": items[offset : offset + limit],
            "facets": facets,
        }

    async def create_export(
        self,
        pid: int,
        fmt: str | None = None,
        include_pending: bool = False,
        splits: list[str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"include_pending": include_pending}
        if fmt is not None:
            body["format"] = fmt
        if splits is not None:
            body["splits"] = splits
        r = await self._http.post(f"/api/projects/{pid}/exports", json=body)
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]

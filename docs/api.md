# API Reference

## REST API (app, port 8000)

### Projects

| Method | Path | Body | Returns |
|--------|------|------|---------|
| POST | `/api/projects` | `{source_folder, name?, initial_labels?, train_val_test?, export_format?}` | Project (201) |
| GET | `/api/projects/{pid}` | — | Project + AgentState |
| POST | `/api/projects/{pid}/chat` | `{content}` | SSE stream of agent events |
| PATCH | `/api/projects/{pid}/folder` | `{folder}` | Project |
| PATCH | `/api/projects/{pid}/splits` | `{train, val, test}` | Project |
| PATCH | `/api/projects/{pid}/format` | `{format}` | Project |
| POST | `/api/projects/{pid}/labels` | `{name, color?}` | Label (201, 409 on dup) |
| DELETE | `/api/projects/{pid}/labels/{name}` | — | 204 (403 if status≠draft) |
| POST | `/api/projects/{pid}/finalize` | — | `{status, id}` (400 if critic fails) |

### Images

| Method | Path | Returns |
|--------|------|---------|
| GET | `/api/projects/{pid}/images?split=...` | List + per-split progress |
| GET | `/api/images/{iid}` | Image |
| GET | `/api/images/{iid}/file` | Image bytes |
| GET | `/api/images/{iid}/annotations` | List of annotations |

### Annotations

| Method | Path | Body |
|--------|------|------|
| POST | `/api/projects/{pid}/images/{iid}/predict-similar` | `{label_id, exemplar_bbox, max_predictions?, score_threshold?}` |
| PUT | `/api/annotations/{aid}` | `{x1?, y1?, x2?, y2?, label_id?, source?, version}` |
| DELETE | `/api/annotations/{aid}` | — |
| PATCH | `/api/projects/{pid}/images/{iid}/annotations/bulk` | `{action: "accept_all" \| "reject_all"}` |

### Exports

| Method | Path | Body |
|--------|------|------|
| POST | `/api/projects/{pid}/exports` | `{format?, include_pending?, splits?}` |

## Error envelope

All errors share this shape:
```json
{
  "error": {
    "code": "project_not_found",
    "message": "project 99 not found",
    "detail": {"project_id": 99}
  }
}
```

Common codes: `validation_failed` (400), `project_not_found` / `image_not_found` / `annotation_not_found` (404), `label_conflict` / `version_conflict` (409), `ml_backend_unavailable` / `llm_unavailable` (503), `internal_error` (500).

## ml_backend (port 9090)

| Method | Path | Body | Returns |
|--------|------|------|---------|
| GET | `/healthz` | — | `{status, service, version, model_loaded, device}` |
| POST | `/predict_similar` | `{image_path, exemplar_bbox, max_predictions?, score_threshold?}` | `{predictions, exemplar_count, image_size, elapsed_ms}` |

## MCP server (stdio or SSE)

3 tools — see [`docs/superpowers/specs/...`](superpowers/specs/2026-05-04-multimodal-annotation-agent-design.md) section 7 for full schemas.

| Tool | Args | Returns |
|------|------|---------|
| `start_annotation_project` | `{folder, name?, initial_labels?, train_val_test?, export_format?}` | `{project_id, name, setup_url, status, message}` |
| `search_annotations` | `{project_id, label?, source?, split?, min_score?, image_filename_glob?, limit?, offset?}` | `{total, returned, items, facets}` |
| `export_dataset` | `{project_id, format?, include_pending?, splits?}` | `{export_id, format, output_dir, files, stats, elapsed_ms}` |

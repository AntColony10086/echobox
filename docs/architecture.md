# Architecture

This document is a slim, navigable view of the system. The full design — every decision, every tradeoff — lives in [`superpowers/specs/2026-05-04-multimodal-annotation-agent-design.md`](superpowers/specs/2026-05-04-multimodal-annotation-agent-design.md).

## Process topology

| Process | Port | Tech | Role |
|---------|------|------|------|
| `app` | 8000 | FastAPI | LangGraph chat agent, setup orchestration, REST API, DB writes |
| `ml_backend` | 9090 | FastAPI + GPU | GECO2 / SAM2 inference (`POST /predict_similar`) |
| `mcp_server` | stdio | MCP SDK | Exposes 3 tools to external agents |
| `frontend` | 5173 | Vite + React + Konva | Setup page (cards + chat) + Annotate page (canvas) |

All inter-process communication is HTTP. `app` is the only process with persistent state (SQLite + on-disk workspace).

## Data flow

### Phase 1 — Setup
```
User chat ──▶ app POST /chat (SSE)
                 ↓
              LangGraph (Planner + Critic)
                 ↓
         tool execution → mutate AgentState
                 ↓
              SSE events back to frontend
                 ↓
         Cards re-render, user clicks 开始标注
                 ↓
         POST /finalize → status=ready → /annotate
```

### Phase 2 — Annotation
```
User draws exemplar ──▶ app POST /predict-similar
                            ↓
                       ml_backend POST /predict_similar
                            ↓
                       GECO2 returns N boxes
                            ↓
                       app persists with source=geco2_pending
                            ↓
                       SSE / response → frontend renders dashed boxes
                            ↓
                       User adjusts → PUT/PATCH/DELETE → DB
```

## Workspace layout (per-project)

```
.data/projects/<id>/
├── project.json         # metadata snapshot
├── data/
│   ├── image/00001.jpg ...   # canonical-named copies
│   ├── mapping.json          # canonical → source path
│   └── splits.json           # canonical → train/val/test
├── exports/<timestamp>-<format>/
└── chat/history.jsonl
```

## Database tables (overview)

- `projects` — top-level project (status, ratios, format)
- `images` — per-image metadata + split assignment
- `labels` — class names + UI colors
- `annotations` — bbox + label + source + version
- `chat_messages` — Phase 1 LangGraph history
- `prediction_runs` — GECO2 invocation log

Full schema: see the spec section 6.2.

## Where to look for what

| Want to ... | File |
|-------------|------|
| Add a new agent tool | `packages/app/src/echobox_app/tools/` + `agent/tool_specs.py` |
| Add a new exporter | `packages/app/src/echobox_app/exporters/` + register in `registry.py` |
| Add a new MCP tool | `packages/mcp_server/src/echobox_mcp/tools/` + register in `server.py` |
| Add a frontend card | `frontend/src/components/cards/` |
| Change the chat agent prompt | `packages/app/src/echobox_app/agent/graph.py:_SYSTEM_PROMPT` |
| Swap LLM provider | Set `ECHOBOX_APP_LLM_BASE_URL` (any OpenAI-compatible endpoint) |
| Swap exemplar detector | Replace `Geco2Runner` in `packages/ml_backend/src/echobox_ml/runner.py` |

# Extending Echobox

## Adding a new export format

1. Create `packages/app/src/echobox_app/exporters/<name>.py` implementing `Exporter`:

```python
from echobox_app.exporters.base import ExportContext, ExportStats, Exporter

class MyExporter(Exporter):
    name = "myfmt"

    def export(self, ctx: ExportContext) -> ExportStats:
        ctx.export_dir.mkdir(parents=True, exist_ok=True)
        stats = ExportStats()
        # ... write files into ctx.export_dir
        return stats
```

2. Register in `packages/app/src/echobox_app/exporters/registry.py`:

```python
from echobox_app.exporters.myfmt import MyExporter

EXPORTERS["myfmt"] = MyExporter
```

3. Add `"myfmt"` to the `ExportRequest.format` Literal in `packages/app/src/echobox_app/api/exports.py`.

4. Add a test in `packages/app/tests/test_exporter_myfmt.py` following the COCO test pattern.

That's it — `POST /api/projects/{pid}/exports` and the MCP `export_dataset` tool both pick up your new format automatically.

## Adding a new agent tool

1. Implement the deterministic logic in `packages/app/src/echobox_app/tools/<topic>.py` (pure function, no LLM).
2. Add a `ToolSpec` in `packages/app/src/echobox_app/agent/tool_specs.py`:

```python
_MY_TOOL = ToolSpec(
    name="my_tool",
    description="What it does — written for the LLM to read.",
    args={"arg1": {"type": "string", "description": "..."}},
)
TOOL_SPECS.append(_MY_TOOL)
```

3. Wire it in `packages/app/src/echobox_app/agent/executor.py:execute_tool`:

```python
if name == "my_tool":
    return _do_my_tool(state, args)
```

4. Test the tool in isolation + add to e2e setup test if it should be part of the canonical flow.

## Swapping the exemplar detector

`Geco2Runner` is a class, not a global. To swap:

1. Implement an alternative class with the same `predict_similar(image_path, exemplar_bbox, max_predictions, score_threshold) -> (list[Prediction], (w, h), elapsed_ms)` signature.
2. In `packages/ml_backend/src/echobox_ml/main.py`, swap the constructor.
3. Optional: turn `Geco2Runner` into a config-driven factory if you want hot-swap.

## Swapping the LLM provider

The chat agent uses LangChain's `ChatOpenAI` — anything OpenAI-compatible works. Just set `ECHOBOX_APP_LLM_BASE_URL` and `ECHOBOX_APP_LLM_MODEL`.

For non-OpenAI APIs (e.g., Anthropic native), modify `packages/app/src/echobox_app/llm/factory.py:build_chat_model` to dispatch on a config flag.

## Adding a frontend page

1. Create `frontend/src/pages/<NewPage>.tsx`.
2. Add a route in `frontend/src/App.tsx`.
3. (Optional) Add API client in `frontend/src/api/`.

## Building a custom MCP tool

In `packages/mcp_server/src/echobox_mcp/tools/<my_tool>.py`:

```python
from mcp.types import Tool
from echobox_mcp.client import AppClient

MY_TOOL = Tool(name="my_tool", description="...", inputSchema={...})

async def handle_my_tool(client: AppClient, args: dict) -> dict:
    # call client.<some_method>(...)
    return {...}
```

Then in `packages/mcp_server/src/echobox_mcp/server.py`, append `MY_TOOL` to `ALL_TOOLS` and add a branch in `call_tool()`.

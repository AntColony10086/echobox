# Development

## One-time setup

```bash
git clone --recurse-submodules https://github.com/AntColony10086/echobox
cd echobox
make setup
cp .env.example .env             # then fill ECHOBOX_APP_LLM_API_KEY
make db-upgrade
uv run pre-commit install        # auto-format on commit
```

GPU/inference setup (only if you want real GECO2):
```bash
bash scripts/download_geco2_weights.sh
# Then in .env: ECHOBOX_ML_GECO2_WEIGHTS=./.data/weights/geco2.pth
#               ECHOBOX_ML_SAM2_WEIGHTS=./.data/weights/sam2_hiera_tiny.pt
```

## Daily workflow

```bash
make dev          # start all 4 processes
make test         # full test suite
make lint         # ruff + eslint
make typecheck    # mypy + tsc
```

To run a single process in its own terminal:
```bash
make app          # FastAPI app on 8000 (with --reload)
make ml           # ml_backend on 9090
make mcp          # MCP stdio server
make web          # Vite dev server on 5173
```

## Project layout

```
packages/         # 3 Python packages (uv workspace)
├── app/         # the main FastAPI service
├── ml_backend/  # GECO2 inference
└── mcp_server/  # MCP tools

frontend/        # React + TypeScript + Vite

tests/
├── e2e/         # cross-process tests (mocked LLM + ml_backend)
└── fixtures/    # tiny images, recorded LLM responses

docs/            # architecture, dev, api, extending
scripts/         # setup, dev, weight download
```

## Testing strategy

- **Unit** (~80% coverage): tools, exporters, domain dataclasses, db models
- **Integration** (~20 tests): FastAPI TestClient + temp SQLite + mocked LLM/ml_client
- **E2E** (2-3 tests): full Phase 1 / Phase 2 flows

LLM responses in tests are scripted (no real API call). Real GECO2 inference tests are gated by `ECHOBOX_ML_TEST_REAL=1`.

## Adding a feature

1. Read the relevant section in `docs/superpowers/specs/`
2. Find or write a plan in `docs/superpowers/plans/`
3. Follow TDD: write failing test → implement → pass → commit
4. Update CHANGELOG.md under `[Unreleased]`
5. Open PR

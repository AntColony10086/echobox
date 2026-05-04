# Open Source Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename `echobox` → `echobox`, finish OSS-readiness work, push v0.1.0 to `https://github.com/AntColony10086/echobox`.

**Architecture:** Three workstreams in sequence. **W1** is a mechanical rename (modules, env-var prefixes, package metadata) plus config/docs hygiene (NOTICE, .env.example, path scrub, bilingual README). **W2** is a Codex hand-off brief — Codex (running GPT-5.5 high) returns logo + screenshots into `assets/`. **W3** scrubs git history with `git filter-repo`, then `gh repo create --push` and `gh release create v0.1.0`. Phases 1–4 land on the live tree (mechanical work + brief). Phase 5 merges Codex returns. Phase 6 happens in a throwaway `/tmp/echobox-clean` clone so the original tree stays as backup.

**Tech Stack:** uv workspace · pydantic-settings · alembic · honcho · vite · git-filter-repo · gh CLI

**Spec:** `docs/superpowers/specs/2026-05-04-open-source-readiness-design.md`

---

## File map

### Renamed (W1.1)

| From | To |
|---|---|
| `packages/app/src/echobox_app/` (dir, recursive) | `packages/app/src/echobox_app/` |
| `packages/ml_backend/src/echobox_ml/` (dir, recursive) | `packages/ml_backend/src/echobox_ml/` |
| `packages/mcp_server/src/echobox_mcp/` (dir, recursive) | `packages/mcp_server/src/echobox_mcp/` |

### Modified — package metadata (W1.1)

- `pyproject.toml` — name, sources keys, authors note
- `packages/app/pyproject.toml` — name, scripts entry
- `packages/ml_backend/pyproject.toml` — name, scripts entry
- `packages/mcp_server/pyproject.toml` — name, scripts entry
- `frontend/package.json` — name field

### Modified — runtime config (W1.1)

- All Python files containing `from echobox_app`, `from echobox_ml`, `from echobox_mcp` (≈100 files)
- All Python files containing `ECHOBOX_APP_`, `ECHOBOX_ML_`, `ECHOBOX_MCP_` env-var lookups
- `packages/app/alembic.ini` — `script_location` path
- `Procfile` — package + module + env-var refs
- `Makefile` — same

### Modified — docs / config (W1.2–W1.4)

- `.env.example` — provider-agnostic rewrite
- `CONTRIBUTING.md` — `<your-org>` → `AntColony10086`
- `CHANGELOG.md` — name change line
- `docs/superpowers/plans/2026-05-04-plan-1-execution-summary.md` — `~/...` scrub
- `docs/superpowers/plans/2026-05-04-overnight-execution-summary.md` — same

### Created (W1.3, W1.6, W2)

- `NOTICE` — Apache-2.0 third-party attribution
- `README.md` — bilingual rewrite (overwrites existing)
- `assets/README.md` — index for `assets/`
- `assets/logo/.gitkeep` — placeholder until Codex delivers
- `assets/screenshots/.gitkeep` — placeholder until Codex delivers
- `docs/codex-brief.md` — visual deliverables prompt for Codex

### Final push artifacts (W3)

- `/tmp/echobox.git` (mirror clone, throwaway)
- `/tmp/echobox-clean/` (working clone of rewritten mirror, used to push)

---

## Phase 1 — Internal rename + tests green

### Task 1: Backup current state, snapshot test count

**Files:**
- Read-only: `packages/`

- [ ] **Step 1: Confirm clean working tree**

```bash
cd .
git status -s
```

Expected: empty output (or only untracked submodule content). If anything else, stop and surface to user.

- [ ] **Step 2: Snapshot baseline test count**

```bash
uv run pytest packages -q 2>&1 | tail -3
```

Expected: `174 passed` (or whatever current count is; record the exact number — it must match after rename).

- [ ] **Step 3: Snapshot frontend build success**

```bash
cd frontend && npm run build 2>&1 | tail -3 && cd ..
```

Expected: `✓ built in <N>ms`.

- [ ] **Step 4: Stop dev server if running**

```bash
lsof -ti:5173,8000,9090 | xargs kill 2>/dev/null || true
```

(No commit — this task is verification only.)

---

### Task 2: Rename Python module directories

**Files:**
- Move: `packages/app/src/echobox_app/` → `packages/app/src/echobox_app/`
- Move: `packages/ml_backend/src/echobox_ml/` → `packages/ml_backend/src/echobox_ml/`
- Move: `packages/mcp_server/src/echobox_mcp/` → `packages/mcp_server/src/echobox_mcp/`

- [ ] **Step 1: Move three module directories with `git mv` (preserves history)**

```bash
cd .
git mv packages/app/src/echobox_app packages/app/src/echobox_app
git mv packages/ml_backend/src/echobox_ml packages/ml_backend/src/echobox_ml
git mv packages/mcp_server/src/echobox_mcp packages/mcp_server/src/echobox_mcp
```

- [ ] **Step 2: Verify directories exist at new paths and not at old**

```bash
test -d packages/app/src/echobox_app && \
  test -d packages/ml_backend/src/echobox_ml && \
  test -d packages/mcp_server/src/echobox_mcp && \
  test ! -d packages/app/src/echobox_app && \
  test ! -d packages/ml_backend/src/echobox_ml && \
  test ! -d packages/mcp_server/src/echobox_mcp && \
  echo OK
```

Expected: `OK`.

- [ ] **Step 3: Tests are now broken (imports stale) — confirm**

```bash
uv run pytest packages -q 2>&1 | tail -5
```

Expected: import errors mentioning `echobox_app`, `echobox_ml`, or `echobox_mcp` — proves we have something to fix in next task.

- [ ] **Step 4: Stage and commit (working tree intentionally broken)**

```bash
git add -A
git commit -m "refactor(rename): move Python module dirs to echobox_*"
```

(Tests will pass after Task 3 fixes imports.)

---

### Task 3: Rewrite Python imports + env-var prefixes

**Files:**
- All `*.py` files under `packages/`
- `packages/app/alembic.ini`
- `pyproject.toml` (root)
- `packages/*/pyproject.toml`

- [ ] **Step 1: Sed-replace module imports across all Python files**

```bash
find packages -name "*.py" -print0 | xargs -0 sed -i '' \
  -e 's/echobox_app/echobox_app/g' \
  -e 's/echobox_ml/echobox_ml/g' \
  -e 's/echobox_mcp/echobox_mcp/g'
```

(macOS `sed` requires `-i ''`; Linux is `-i`.)

- [ ] **Step 2: Sed-replace env-var prefixes across all Python files**

```bash
find packages -name "*.py" -print0 | xargs -0 sed -i '' \
  -e 's/ECHOBOX_APP_/ECHOBOX_APP_/g' \
  -e 's/ECHOBOX_ML_/ECHOBOX_ML_/g' \
  -e 's/ECHOBOX_MCP_/ECHOBOX_MCP_/g'
```

- [ ] **Step 3: Update alembic.ini script_location**

```bash
sed -i '' 's|src/echobox_app/|src/echobox_app/|g' packages/app/alembic.ini
```

- [ ] **Step 4: Update root pyproject.toml workspace sources keys**

Open `pyproject.toml` and change:

```toml
[tool.uv.sources]
echobox-app = { workspace = true }
echobox-ml = { workspace = true }
echobox-mcp = { workspace = true }
```

to:

```toml
[tool.uv.sources]
echobox-app = { workspace = true }
echobox-ml = { workspace = true }
echobox-mcp = { workspace = true }
```

Also change:

```toml
name = "echobox"
description = "Multimodal intelligent annotation agent platform"
authors = [{name = "Echobox Contributors"}]
```

to:

```toml
name = "echobox"
description = "Multimodal annotation agent — one box, all the boxes"
authors = [{name = "echobox contributors"}]
```

- [ ] **Step 5: Update each package pyproject.toml**

`packages/app/pyproject.toml`:

```toml
[project]
name = "echobox-app"
version = "0.0.1"
description = "echobox main app: chat agent + setup orchestration + REST API"
# ... (rest unchanged)

[project.scripts]
echobox-app = "echobox_app.main:run"
```

`packages/ml_backend/pyproject.toml`:

```toml
[project]
name = "echobox-ml"
# ... rest similar pattern
[project.scripts]
echobox-ml = "echobox_ml.main:run"
```

(Open and edit; the file has only one `[project.scripts]` block — replace the `aris-*` entry with `echobox-*` and update `name`/`description`.)

`packages/mcp_server/pyproject.toml`:

```toml
[project]
name = "echobox-mcp"
[project.scripts]
echobox-mcp = "echobox_mcp.server:main"
```

(Verify the actual entry point string `<module>:<function>` from the existing file — the part before the colon changes from `echobox_mcp` to `echobox_mcp`; the function name stays.)

- [ ] **Step 6: Re-sync uv workspace (regenerates lock file references)**

```bash
uv sync --reinstall-package echobox-app --reinstall-package echobox-ml --reinstall-package echobox-mcp 2>&1 | tail -5
```

If it complains about missing old packages, run `uv sync --refresh` instead.

- [ ] **Step 7: Run all tests to verify imports + env vars wired correctly**

```bash
uv run pytest packages -q 2>&1 | tail -3
```

Expected: same passing count as Task 1 baseline (e.g. `174 passed`).

- [ ] **Step 8: Verify no lingering aris references in Python**

```bash
grep -rEn "echobox_app|echobox_ml|echobox_mcp|ARIS_APP|ARIS_ML|ARIS_MCP" packages --include="*.py" --include="*.toml" --include="*.ini"
```

Expected: no output.

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "refactor(rename): aris_* → echobox_* (modules + env vars + pyproject)"
```

---

### Task 4: Rename Procfile, Makefile, frontend package.json, .env files

**Files:**
- `Procfile`
- `Makefile`
- `frontend/package.json`
- `.env.example`
- `.env` (local, gitignored — but our local needs updating to keep dev working)

- [ ] **Step 1: Rewrite Procfile**

Replace contents with:

```
app: ECHOBOX_APP_DB_URL=sqlite:///.data/echobox.db uv run --package echobox-app uvicorn echobox_app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
ml:  uv run --package echobox-ml uvicorn echobox_ml.main:create_app --factory --host 127.0.0.1 --port 9090
mcp: tail -f /dev/null | uv run --package echobox-mcp echobox-mcp
web: npm --prefix frontend run dev
```

- [ ] **Step 2: Sed-replace in Makefile**

```bash
sed -i '' \
  -e 's/echobox-app/echobox-app/g' \
  -e 's/echobox-ml/echobox-ml/g' \
  -e 's/echobox-mcp/echobox-mcp/g' \
  -e 's/echobox_app/echobox_app/g' \
  -e 's/echobox_ml/echobox_ml/g' \
  -e 's/echobox_mcp/echobox_mcp/g' \
  -e 's/ECHOBOX_APP_LLM_API_KEY/ECHOBOX_APP_LLM_API_KEY/g' \
  -e 's/ECHOBOX_APP_/ECHOBOX_APP_/g' \
  -e 's/ECHOBOX_ML_/ECHOBOX_ML_/g' \
  -e 's/ECHOBOX_MCP_/ECHOBOX_MCP_/g' \
  -e 's|projects.db|echobox.db|g' \
  Makefile
```

- [ ] **Step 3: Update frontend/package.json name**

Open `frontend/package.json` and change `"name": "echobox-frontend"` to `"name": "echobox-frontend"`.

- [ ] **Step 4: Sed-replace in .env (local) so dev server keeps working**

```bash
sed -i '' \
  -e 's/ECHOBOX_APP_/ECHOBOX_APP_/g' \
  -e 's/ECHOBOX_ML_/ECHOBOX_ML_/g' \
  -e 's/ECHOBOX_MCP_/ECHOBOX_MCP_/g' \
  .env
```

- [ ] **Step 5: Smoke-start the dev server**

```bash
uv run honcho start &
HONCHO_PID=$!
sleep 8
curl -sf http://127.0.0.1:8000/api/projects > /dev/null && echo "app OK"
curl -sf http://127.0.0.1:9090/healthz > /dev/null && echo "ml OK"
curl -sf http://127.0.0.1:5173/ > /dev/null && echo "web OK"
kill $HONCHO_PID 2>/dev/null
```

Expected: three "OK" lines.

- [ ] **Step 6: Verify no aris-* package refs left in run config**

```bash
grep -E "echobox-app|echobox-ml|echobox-mcp|echobox_app|echobox_ml|echobox_mcp|ARIS_APP|ARIS_ML|ARIS_MCP|echobox-frontend" Procfile Makefile frontend/package.json
```

Expected: no output.

- [ ] **Step 7: Commit**

```bash
git add Procfile Makefile frontend/package.json .env.example
# Note: .env stays gitignored — we mutated it locally for dev, not tracked.
git commit -m "refactor(rename): Procfile/Makefile/frontend pkg → echobox"
```

---

### Task 5: Rename in docs (existing docs only — README rewrite is later)

**Files:**
- `docs/architecture.md`
- `docs/api.md`
- `docs/development.md`
- `docs/extending.md`
- `CHANGELOG.md`
- `CODE_OF_CONDUCT.md`
- `README.md` (placeholder rename only — full bilingual rewrite is Task 13)
- `docs/superpowers/specs/*.md` and `docs/superpowers/plans/*.md` (text only — keep filenames)

- [ ] **Step 1: Sed-replace in docs and CHANGELOG/CODE_OF_CONDUCT**

```bash
find docs CHANGELOG.md CODE_OF_CONDUCT.md README.md -type f \( -name "*.md" \) -print0 | \
  xargs -0 sed -i '' \
  -e 's/echobox/echobox/g' \
  -e 's/Echobox/Echobox/g' \
  -e 's/echobox_app/echobox_app/g' \
  -e 's/echobox_ml/echobox_ml/g' \
  -e 's/echobox_mcp/echobox_mcp/g' \
  -e 's/echobox-app/echobox-app/g' \
  -e 's/echobox-ml/echobox-ml/g' \
  -e 's/echobox-mcp/echobox-mcp/g' \
  -e 's/ECHOBOX_APP_/ECHOBOX_APP_/g' \
  -e 's/ECHOBOX_ML_/ECHOBOX_ML_/g' \
  -e 's/ECHOBOX_MCP_/ECHOBOX_MCP_/g'
```

- [ ] **Step 2: Verify no aris references in docs**

```bash
grep -rEn "echobox|Echobox|echobox_app|echobox_ml|echobox_mcp|echobox-app|echobox-ml|echobox-mcp|ARIS_APP|ARIS_ML|ARIS_MCP" docs CHANGELOG.md CODE_OF_CONDUCT.md README.md
```

Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "refactor(rename): docs/CHANGELOG/CODE_OF_CONDUCT/README → echobox"
```

---

### Task 6: Phase-1 final verification — full test suite + frontend build

**Files:** none modified

- [ ] **Step 1: Full test suite passes**

```bash
uv run pytest packages -q 2>&1 | tail -3
```

Expected: same baseline count from Task 1, e.g. `174 passed`.

- [ ] **Step 2: Frontend build still clean**

```bash
cd frontend && npm run build 2>&1 | tail -3 && cd ..
```

Expected: `✓ built in <N>ms`.

- [ ] **Step 3: Pre-commit hooks pass on a no-op commit (validate config still works)**

```bash
pre-commit run --all-files 2>&1 | tail -10
```

Expected: all hooks pass (or only auto-fixed formatting; if so re-stage and amend).

- [ ] **Step 4: Verify NO aris-* anywhere except this plan and the spec**

```bash
grep -rEln "echobox_app|echobox_ml|echobox_mcp|ECHOBOX_APP_|ECHOBOX_ML_|ECHOBOX_MCP_|echobox-app|echobox-ml|echobox-mcp|echobox" \
  --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=.git \
  --exclude-dir=geco2_vendor --exclude-dir=__pycache__ \
  packages frontend Makefile Procfile pyproject.toml .env.example
```

Expected: no output.

(No commit — verification only. If anything fails, fix and amend the relevant rename commit.)

---

## Phase 2 — Config + NOTICE + path scrub + CONTRIBUTING

### Task 7: Provider-agnostic `.env.example`

**Files:**
- Modify: `.env.example` (full rewrite)

- [ ] **Step 1: Overwrite `.env.example`**

Replace entire contents with:

```env
# === LLM provider (any OpenAI-compatible endpoint) ===
# Examples:
#   - DashScope (Aliyun): https://dashscope.aliyuncs.com/compatible-mode/v1 + qwen-plus
#   - MiniMax:            https://api.minimaxi.com/v1 + MiniMax-M2.7
#   - OpenAI:             https://api.openai.com/v1 + gpt-4o-mini
#   - Together:           https://api.together.xyz/v1 + meta-llama/Llama-3-70b-chat-hf
ECHOBOX_APP_LLM_API_KEY=your-key-here
ECHOBOX_APP_LLM_BASE_URL=https://api.openai.com/v1
ECHOBOX_APP_LLM_MODEL=gpt-4o-mini

# === GECO2 weights (required for real inference; otherwise stub mode) ===
# Download CNTQG_multitrain_ca44.pth from https://github.com/jerpelhan/GECO2/releases
ECHOBOX_ML_GECO2_WEIGHTS=./.data/weights/CNTQG_multitrain_ca44.pth
ECHOBOX_ML_DEVICE=auto

# === Optional overrides (defaults shown) ===
# ECHOBOX_APP_HOST=127.0.0.1
# ECHOBOX_APP_PORT=8000
# ECHOBOX_APP_DB_URL=sqlite:///.data/echobox.db
# ECHOBOX_APP_LOG_LEVEL=INFO
# ECHOBOX_ML_HOST=127.0.0.1
# ECHOBOX_ML_PORT=9090
# ECHOBOX_MCP_APP_URL=http://localhost:8000
```

- [ ] **Step 2: Verify file parses (no shell special-char issues)**

```bash
set -a && . ./.env.example && set +a && echo "loaded OK"
```

Expected: `loaded OK`.

- [ ] **Step 3: Commit**

```bash
git add .env.example
git commit -m "docs(env): provider-agnostic .env.example with 4 examples"
```

---

### Task 8: Create `NOTICE` file

**Files:**
- Create: `NOTICE`

- [ ] **Step 1: Create `NOTICE` with full content**

```
echobox
Copyright 2026 The echobox contributors

This product includes software developed by:

== Vendored / submoduled ==

GECO2 — exemplar-based detector
  https://github.com/jerpelhan/GECO2
  Copyright (c) 2025 jerpelhan
  License: MIT

SAM2 — Segment Anything Model 2 (used inside GECO2)
  https://github.com/facebookresearch/sam2
  Copyright (c) Meta Platforms, Inc. and affiliates.
  License: Apache-2.0

Deformable-DETR — used inside GECO2 (models/ops)
  https://github.com/fundamentalvision/Deformable-DETR
  Copyright (c) 2020 SenseTime
  License: Apache-2.0

== Runtime dependencies (key ones) ==

FastAPI                 https://github.com/tiangolo/fastapi      MIT
Uvicorn                 https://github.com/encode/uvicorn        BSD-3-Clause
Pydantic                https://github.com/pydantic/pydantic     MIT
SQLAlchemy              https://github.com/sqlalchemy/sqlalchemy MIT
Alembic                 https://github.com/sqlalchemy/alembic    MIT
LangChain & LangGraph   https://github.com/langchain-ai          MIT
React                   https://github.com/facebook/react        MIT
Vite                    https://github.com/vitejs/vite           MIT
react-konva             https://github.com/konvajs/react-konva   MIT

See respective package metadata for full license texts.
```

- [ ] **Step 2: Sanity check — file exists and is non-empty**

```bash
test -s NOTICE && wc -l NOTICE
```

Expected: `40` (give or take a couple lines).

- [ ] **Step 3: Commit**

```bash
git add NOTICE
git commit -m "docs(notice): NOTICE file for Apache-2.0 third-party attribution"
```

---

### Task 9: Scrub `~/...` from execution-summary docs

**Files:**
- Modify: `docs/superpowers/plans/2026-05-04-plan-1-execution-summary.md`
- Modify: `docs/superpowers/plans/2026-05-04-overnight-execution-summary.md`

- [ ] **Step 1: Sed-replace user-specific paths**

```bash
sed -i '' 's|.|.|g' \
  docs/superpowers/plans/2026-05-04-plan-1-execution-summary.md \
  docs/superpowers/plans/2026-05-04-overnight-execution-summary.md
```

- [ ] **Step 2: Verify no ~ references survive in tracked files**

```bash
git ls-files -z | xargs -0 grep -lE "~" 2>/dev/null
```

Expected: empty output. If any files surface, sed-fix them too.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-05-04-plan-1-execution-summary.md \
        docs/superpowers/plans/2026-05-04-overnight-execution-summary.md
git commit -m "docs(scrub): replace ~/... with relative paths in plan summaries"
```

---

### Task 10: Fill `<your-org>` in `CONTRIBUTING.md` (and check elsewhere)

**Files:**
- Modify: `CONTRIBUTING.md`

- [ ] **Step 1: Sed-replace org placeholder**

```bash
sed -i '' 's|<your-org>|AntColony10086|g' CONTRIBUTING.md
```

- [ ] **Step 2: Search for any other `<placeholder>` patterns in tracked text**

```bash
git ls-files -z '*.md' '*.yml' '*.yaml' | xargs -0 grep -nE "<your-[a-z]+>|<placeholder>|<TBD>|<TODO>" 2>/dev/null
```

Expected: no output (or, if anything surfaces, fix it now).

- [ ] **Step 3: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs(contrib): fill <your-org> placeholder → AntColony10086"
```

---

## Phase 3 — Bilingual README rewrite

### Task 11: Bilingual `README.md` (with placeholders for logo / screenshots)

**Files:**
- Modify: `README.md` (full overwrite)

- [ ] **Step 1: Overwrite `README.md`**

Replace entire contents with:

```markdown
<p align="center">
  <img src="assets/logo/logo.svg" alt="echobox" width="320">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License"></a>
  <a href="https://github.com/AntColony10086/echobox/actions"><img src="https://github.com/AntColony10086/echobox/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/AntColony10086/echobox/stargazers"><img src="https://img.shields.io/github/stars/AntColony10086/echobox?style=social" alt="Stars"></a>
</p>

<p align="center"><b>One box → all the boxes.</b> · <b>画一框，框出全图。</b></p>

<p align="center">
  <img src="assets/screenshots/03-annotate.png" alt="annotation page" width="900">
</p>

---

## What it does · 核心能力

**EN.** Echobox is a multimodal annotation agent. Draw one bounding box; an LLM-supervised
exemplar detector ([GECO2](https://github.com/jerpelhan/GECO2), backed by Meta's
[SAM2](https://github.com/facebookresearch/sam2)) returns every similar object in the image.
You adjust, accept, save. A LangGraph agent handles the boring parts — folder scanning,
train/val/test split, label suggestions, and dataset export to COCO / YOLO / Pascal VOC /
Label Studio JSON. The same tools are exposed as MCP, so other agents (Claude Code, Cursor,
…) can drive annotation programmatically.

**中文.** Echobox 是一个多模态智能标注 Agent。你只需画一个 bbox，LLM 监督下的 exemplar 检测器
（[GECO2](https://github.com/jerpelhan/GECO2)，底层用 Meta 的
[SAM2](https://github.com/facebookresearch/sam2)）就把图里所有相似目标都框出来。
你确认、调整、保存。LangGraph agent 负责扫描文件夹、切分 train/val/test、推荐标签、导出
COCO / YOLO / Pascal VOC / Label Studio JSON。同一套工具暴露为 MCP，其它 agent
（Claude Code、Cursor 等）也可以编程方式调用。

## Architecture · 架构

4 processes, all run locally — no Docker required. · 4 个进程纯本地运行，不需要 Docker。

```
Browser ──▶ frontend (Vite, port 5173)
                │
                ▼
          app (FastAPI, port 8000) ──▶ ml_backend (FastAPI + GPU, port 9090)
                │                              │
                │                              └─▶ GECO2 / SAM2 inference
                │
                ├─▶ OpenAI-compatible LLM (DashScope / MiniMax / OpenAI / …)
                └─▶ SQLite + filesystem workspace

mcp_server (stdio) ──▶ app HTTP — for Claude Code / Cursor consumers
```

## Quick start · 快速开始

```bash
# 1. Clone (with GECO2 submodule)
git clone --recurse-submodules https://github.com/AntColony10086/echobox
cd echobox

# 2. Configure your LLM (any OpenAI-compatible)
cp .env.example .env
# Edit .env — set ECHOBOX_APP_LLM_API_KEY, _BASE_URL, _MODEL

# 3. Install (uv handles Python; npm handles JS)
make setup

# 4. Get GECO2 weights
mkdir -p .data/weights
curl -L https://github.com/jerpelhan/GECO2/releases/download/v1.0/CNTQG_multitrain_ca44.pth \
  -o .data/weights/CNTQG_multitrain_ca44.pth

# 5. Initialize the database
make db-upgrade

# 6. Start everything (4 processes via honcho) and open the browser
make dev
# open http://localhost:5173
```

> **EN.** Need help on step 4? See [GECO2 releases](https://github.com/jerpelhan/GECO2/releases) for the latest weight URL and SHA256.
>
> **中文.** 第 4 步遇到问题，去 [GECO2 releases](https://github.com/jerpelhan/GECO2/releases) 查最新权重链接和 SHA256。

## Screenshots · 界面预览

| Home · 首页 | Setup · 配置 |
|---|---|
| ![home](assets/screenshots/01-home.png) | ![setup](assets/screenshots/02-setup-modal.png) |
| **Annotate · 标注** | **Chat · 对话** |
| ![annotate](assets/screenshots/03-annotate.png) | ![chat](assets/screenshots/04-chat.png) |

## MCP integration · MCP 集成

**EN.** Add this to your Claude Code / Cursor MCP config to call echobox tools from another agent:

```json
{
  "mcpServers": {
    "echobox": {
      "command": "uv",
      "args": ["run", "--package", "echobox-mcp", "echobox-mcp"],
      "cwd": "/path/to/echobox",
      "env": {
        "ECHOBOX_MCP_APP_URL": "http://localhost:8000"
      }
    }
  }
}
```

Available tools: `start_annotation_project`, `search_annotations`, `export_dataset`, plus all setup tools.

**中文.** 添加上面 JSON 到你的 Claude Code / Cursor MCP 配置即可让其它 agent 调用 echobox 工具。
工具清单：`start_annotation_project`、`search_annotations`、`export_dataset`，以及全部 setup 工具。

## How GECO2 works · GECO2 原理

**EN.** GECO2 (Generalist Exemplar-based COunting and detection) takes one user-drawn
exemplar and uses SAM2's image embedding to find every similar object. We use it as a
detector (not a counter): the predicted heatmap is binarised and converted to bboxes.
[Paper · jerpelhan/GECO2](https://github.com/jerpelhan/GECO2)

**中文.** GECO2 用一个用户画的 exemplar，借助 SAM2 的 image embedding，找出所有相似目标。
我们把它当作检测器用（不是计数器）：把预测的热力图二值化转成 bbox。
[论文 · jerpelhan/GECO2](https://github.com/jerpelhan/GECO2)

## Project layout · 工程结构

```
echobox/
├─ packages/
│  ├─ app/          (FastAPI + LangGraph agent + REST API)
│  ├─ ml_backend/   (FastAPI + GECO2/SAM2 inference)
│  └─ mcp_server/   (MCP stdio server, calls app HTTP)
├─ frontend/        (React + Vite + react-konva)
├─ docs/            (architecture, API, dev, extending)
├─ assets/          (logo, screenshots, social card)
├─ Procfile         (honcho config: 4 processes)
├─ Makefile         (dev shortcuts)
└─ .env.example
```

## Acknowledgements · 致谢

Echobox stands on the shoulders of these projects — credit and copyright belong to their
authors. · Echobox 完全基于以下项目，版权与归属归原作者所有：

- **GECO2** — [jerpelhan/GECO2](https://github.com/jerpelhan/GECO2) — exemplar-based detector
- **SAM2** — [facebookresearch/sam2](https://github.com/facebookresearch/sam2) — Meta AI
- **Deformable-DETR** — [fundamentalvision/Deformable-DETR](https://github.com/fundamentalvision/Deformable-DETR)
- **LangGraph** — [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)
- **FastAPI** — [tiangolo/fastapi](https://github.com/tiangolo/fastapi)

See [`NOTICE`](NOTICE) for the full attribution list.

## License · 许可

Apache-2.0 — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

## Contributing · 参与开发

PRs welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md). · PR 欢迎，详见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

## Citation

If echobox helps your research, a citation is appreciated:

```bibtex
@software{echobox2026,
  title  = {echobox: Multimodal annotation agent with exemplar-based detection},
  author = {The echobox contributors},
  year   = {2026},
  url    = {https://github.com/AntColony10086/echobox}
}
```
```

- [ ] **Step 2: Verify markdown sanity (no broken refs to non-existent files yet — assets/ is added next task)**

```bash
grep -E "assets/(logo|screenshots)" README.md | head -5
```

Expected: 5 lines referencing `assets/logo/logo.svg` and `assets/screenshots/*.png`. (These files don't exist yet — they arrive from Codex in Phase 5.)

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs(readme): bilingual rewrite with logo/screenshot placeholders"
```

---

### Task 12: Create `assets/` skeleton (placeholders)

**Files:**
- Create: `assets/README.md`
- Create: `assets/logo/.gitkeep`
- Create: `assets/screenshots/.gitkeep`

- [ ] **Step 1: Create directory skeleton**

```bash
mkdir -p assets/logo assets/screenshots
touch assets/logo/.gitkeep assets/screenshots/.gitkeep
```

- [ ] **Step 2: Create `assets/README.md`**

```markdown
# Assets

Visual assets for the project.

## logo/

Wordmark + mark variants. Used in README header, GitHub social card, and favicon.

| File | Use |
|---|---|
| `logo.svg` | Full wordmark (vector, scales) — README header |
| `logo-mark.svg` | Mark-only (no text) — favicon, social card |
| `logo.png` | 1024×256 PNG — fallback for renderers without SVG support |
| `logo-dark.png` | Dark theme variant |
| `logo-light.png` | Light theme variant |
| `favicon.svg` | Browser tab icon (vector) |
| `favicon.ico` | Legacy 16/32/48 ico bundle |

## screenshots/

UI captures used in README. All 1600px wide, light browser-chrome frame, soft drop shadow.

| File | Scene |
|---|---|
| `01-home.png` | Project list home page |
| `02-setup-modal.png` | Setup modal with all 5 cards filled |
| `03-annotate.png` | Annotation page with bboxes drawn (mix of accepted + pending) |
| `04-chat.png` | Chat modal with user + assistant + tool messages |
| `05-export.png` | Export panel showing successful result |
| `06-image-list-detail.png` | (optional) Close-up of left image list |

## social-card.png

1200×630 Open Graph card. Logo + tagline + screenshot thumbnail.
```

- [ ] **Step 3: Commit**

```bash
git add assets/
git commit -m "docs(assets): create assets/ skeleton with README index"
```

---

## Phase 4 — Codex brief

### Task 13: Write `docs/codex-brief.md`

**Files:**
- Create: `docs/codex-brief.md`

- [ ] **Step 1: Write the brief**

```markdown
# Codex visual deliverables — echobox

> **REQUIRED MODEL: GPT-5.5 high (high-reasoning tier).** Do not switch to a smaller / faster model — visual quality is the priority.

This brief defines the visual assets Codex needs to produce for the echobox open-source release. Drop deliverables into the paths shown; the rest of the project (README, CI, push) is already wired up to consume them at those exact paths.

## Project context (read first)

- **Name:** echobox (lowercase, one word)
- **Tagline (en):** "One box → all the boxes."
- **Tagline (zh):** "画一框，框出全图。"
- **What it is:** Multimodal annotation agent. User draws one bounding box on an image; a LangGraph agent + GECO2 exemplar detector returns every similar object. Tool for ML / dataset prep.
- **Primary brand color:** `#3182ce` (blue, matches in-app accent)
- **Secondary palette:** neutral grays — `#2d3748` (dark text), `#718096` (mid), `#e2e8f0` (light)
- **Aesthetic:** clean, technical, restrained. Vercel / Linear / Resend tier — not playful, not corporate.

## Deliverable 1 — Logo

A wordmark designed as **letter transformation of "echobox"**. Concept: the inner "o" (or "b") morphs into a box-with-echo motif — concentric squares fading outward, evoking "one box → many boxes / echoes". All lowercase.

Drop into `assets/logo/`:

| File | Format | Size | Notes |
|---|---|---|---|
| `logo.svg` | SVG | scales | Full wordmark with mark embedded |
| `logo-mark.svg` | SVG | scales | Just the box-echo glyph, no text |
| `logo.png` | PNG | 1024×256 transparent | README header fallback |
| `logo-dark.png` | PNG | 1024×256 | For light backgrounds — colored or black wordmark |
| `logo-light.png` | PNG | 1024×256 | For dark backgrounds — white wordmark |
| `favicon.svg` | SVG | square | Browser tab |
| `favicon.ico` | ICO | bundles 16, 32, 48 | Legacy support |

Color spec: monochrome variants in pure `#1a202c` (near-black) and pure white. Color variant uses `#3182ce` for the box-echo glyph and `#1a202c` for the rest of the wordmark.

## Deliverable 2 — UI screenshots

Take the raw screenshots Claude provides (one per scene listed below) and beautify each:

- Wrap in a **light browser chrome frame** (no real OS chrome — a stylized minimal frame: 3 colored dots top-left, address bar showing `localhost:5173`, single-pixel border)
- Add a **soft drop shadow** (offset 0 12, blur 32, opacity 12%)
- Place on a **white background**, output 1600px wide

Drop into `assets/screenshots/`:

| File | Scene description |
|---|---|
| `01-home.png` | Project list home page with at least 3 sample projects, "+ 新建项目" button visible |
| `02-setup-modal.png` | SetupModal open showing all 5 setup cards filled in |
| `03-annotate.png` | Annotation page with image loaded, several bboxes drawn (mix of accepted solid + pending dashed), class picker on right showing 2 classes |
| `04-chat.png` | Chat modal mid-conversation with user + assistant + tool messages |
| `05-export.png` | Export panel inside SetupModal showing successful export result |
| `06-image-list-detail.png` (optional) | Close-up of left ImageList showing per-row index + split dot + filename |

## Deliverable 3 — Social card

`assets/social-card.png` — 1200×630 PNG (Open Graph + Twitter card spec).

Layout: logo center-left at ~280px wide, tagline below logo ("One box → all the boxes."), one screenshot thumbnail (use `03-annotate.png`) center-right at ~600px wide, soft shadow. White background with a subtle blue gradient strip on the left edge.

## Constraints

- **No emoji**, no "AI" buzzwords in the visuals
- **Don't invent screenshots** — use the source captures Claude provides; only beautify (frame + shadow)
- **Vector-first** for the logo — PNG exports are derived from the SVG, not redrawn
- **Maintain consistency** — all screenshots use the same browser chrome and shadow

## Drop-off

Place files at exactly the paths above and commit with message `assets: logo + screenshots + social card`. Claude will pick them up in Phase 5 of the open-source-readiness plan.
```

- [ ] **Step 2: Verify the file exists and parses as markdown**

```bash
test -s docs/codex-brief.md && head -3 docs/codex-brief.md
```

Expected: file exists; first 3 lines are the H1 + blockquote.

- [ ] **Step 3: Commit**

```bash
git add docs/codex-brief.md
git commit -m "docs(codex): visual deliverables brief (logo, screenshots, social card)"
```

---

### Task 14: Hand off Codex brief to user

**Files:** none modified

- [ ] **Step 1: Print Codex hand-off instructions for user**

Output (to user, in chat):

> Codex brief is ready at `docs/codex-brief.md`. Open Codex with **GPT-5.5 high** model selected, paste the contents of that file as the prompt. Tell Codex to drop assets at the listed paths and commit them. When Codex's commit lands, ping me and I'll continue with Phase 5.

(No commit — this is a coordination step, not a code change. Engineer should literally execute the message above.)

---

## Phase 5 — Merge Codex deliverables

### Task 15: Verify Codex assets landed correctly

**Files:** none modified (verification only)

- [ ] **Step 1: Confirm all required assets exist**

```bash
test -f assets/logo/logo.svg && \
  test -f assets/logo/logo-mark.svg && \
  test -f assets/logo/logo.png && \
  test -f assets/logo/favicon.ico && \
  test -f assets/screenshots/01-home.png && \
  test -f assets/screenshots/02-setup-modal.png && \
  test -f assets/screenshots/03-annotate.png && \
  test -f assets/screenshots/04-chat.png && \
  test -f assets/screenshots/05-export.png && \
  test -f assets/social-card.png && \
  echo "all assets present"
```

Expected: `all assets present`. If any missing, surface to user — do not proceed.

- [ ] **Step 2: Spot-check screenshot dimensions (1600px wide)**

```bash
for f in assets/screenshots/*.png; do
  identify -format "%w %f\n" "$f"
done
```

Expected: all widths near 1600 (allow ±50px). Requires `imagemagick` (`brew install imagemagick`) — if unavailable, skip.

- [ ] **Step 3: Spot-check social card dimensions (1200×630)**

```bash
identify -format "%w %h" assets/social-card.png 2>/dev/null && echo
```

Expected: `1200 630`. (Skip if imagemagick unavailable.)

- [ ] **Step 4: Sanity-check logo SVG isn't empty**

```bash
wc -c assets/logo/logo.svg
```

Expected: at least 1000 bytes (an SVG with any meaningful detail is well over 1KB).

(No commit — verification only.)

---

### Task 16: Wire favicon into frontend

**Files:**
- Modify: `frontend/index.html`
- Copy/link: `assets/logo/favicon.svg` and `assets/logo/favicon.ico` into `frontend/public/`

- [ ] **Step 1: Copy favicons into frontend public dir**

```bash
mkdir -p frontend/public
cp assets/logo/favicon.svg frontend/public/favicon.svg
cp assets/logo/favicon.ico frontend/public/favicon.ico
```

- [ ] **Step 2: Update `frontend/index.html` head**

Replace the entire file contents with:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link rel="alternate icon" href="/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>echobox</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

(Was previously `Echobox` title with `/vite.svg` favicon.)

- [ ] **Step 3: Verify build picks up the favicon**

```bash
cd frontend && npm run build && cd ..
test -f frontend/dist/favicon.svg && echo "favicon shipped"
```

Expected: `favicon shipped`.

- [ ] **Step 4: Commit**

```bash
git add frontend/public/ frontend/index.html
git commit -m "feat(frontend): wire echobox favicon + title"
```

---

## Phase 6 — Pre-flight, history rewrite, push, release

### Task 17: Pre-push verification

**Files:** none modified

- [ ] **Step 1: Test suite passes**

```bash
uv run pytest packages -q 2>&1 | tail -3
```

Expected: same passing count as Task 1 baseline.

- [ ] **Step 2: Frontend build clean**

```bash
cd frontend && npm run build 2>&1 | tail -3 && cd ..
```

Expected: `✓ built in <N>ms`.

- [ ] **Step 3: Smoke-test dev server end-to-end**

```bash
uv run honcho start &
HONCHO_PID=$!
sleep 8
curl -sf http://127.0.0.1:8000/api/projects > /dev/null && echo "app OK"
curl -sf http://127.0.0.1:9090/healthz > /dev/null && echo "ml OK"
curl -sf http://127.0.0.1:5173/ > /dev/null && echo "web OK"
kill $HONCHO_PID 2>/dev/null
wait 2>/dev/null
```

Expected: three "OK" lines. Optionally manual-test in browser: create project → annotate one box → export.

- [ ] **Step 4: Secret scan — no API keys in tracked files**

```bash
git ls-files -z | xargs -0 grep -lE "sk-[A-Za-z0-9_\-]{20,}" 2>/dev/null
```

Expected: empty output.

- [ ] **Step 5: Path scan — no ~ in tracked files**

```bash
git ls-files -z | xargs -0 grep -lE "~" 2>/dev/null
```

Expected: empty output. (If anything surfaces, fix and amend in the appropriate phase commit.)

- [ ] **Step 6: Aris-* scan — no leftover old name in tracked files (excluding spec/plan, which mention old name in history context)**

```bash
git ls-files -z | xargs -0 grep -lE "echobox_app|echobox_ml|echobox_mcp|ECHOBOX_APP_|ECHOBOX_ML_|ECHOBOX_MCP_|echobox-app|echobox-ml|echobox-mcp|echobox|Echobox" 2>/dev/null | grep -vE "docs/superpowers/(specs|plans)/"
```

Expected: empty output. (The two plan/spec docs intentionally retain old names for historical reference — that's fine, the OSS audience won't grep them.)

(No commit — verification only.)

---

### Task 18: History rewrite via `git filter-repo`

**Files:** clone to `/tmp/echobox.git` (mirror) → `/tmp/echobox-clean/` (working)

- [ ] **Step 1: Install `git-filter-repo` if not already**

```bash
pipx list 2>/dev/null | grep -q git-filter-repo || pipx install git-filter-repo
```

Expected: command succeeds (or already installed).

- [ ] **Step 2: Mirror-clone the local repo**

```bash
rm -rf /tmp/echobox.git /tmp/echobox-clean
git clone --no-local --mirror . /tmp/echobox.git
cd /tmp/echobox.git
```

Expected: clone succeeds (single line output, no errors).

- [ ] **Step 3: Write the scrub rules**

```bash
cat > /tmp/scrub.txt <<'EOF'
.==>.
~==>~
EOF
```

- [ ] **Step 4: Run filter-repo (destructive — but only on the mirror, not on live tree)**

```bash
git filter-repo --replace-text /tmp/scrub.txt --force
```

Expected: progress output ending with `Completed successfully`.

- [ ] **Step 5: Verify scrub worked — no ~ in any commit**

```bash
git log -p --all 2>/dev/null | grep -E "~" | head -5
```

Expected: empty output.

- [ ] **Step 6: Clone the rewritten mirror into a normal working tree**

```bash
git clone /tmp/echobox.git /tmp/echobox-clean
cd /tmp/echobox-clean
```

Expected: clone succeeds; `git log --oneline | head -3` shows recent commits with **new SHAs**.

(No commit — this task produces `/tmp/echobox-clean/` as the source-of-truth tree for Tasks 19+.)

---

### Task 19: Create GitHub repo + push

**Files:** working from `/tmp/echobox-clean/`

- [ ] **Step 1: Confirm gh authenticated as AntColony10086**

```bash
cd /tmp/echobox-clean
gh auth status 2>&1 | grep AntColony10086
```

Expected: line containing `Logged in to github.com account AntColony10086`.

- [ ] **Step 2: Create the public repo and push in one shot**

```bash
gh repo create AntColony10086/echobox \
  --public \
  --description "One box → all the boxes. Multimodal annotation agent with SAM2-backed exemplar detection." \
  --source=. \
  --remote=origin \
  --push
```

Expected: output ending with the repo URL and push success.

- [ ] **Step 3: Open the repo URL and confirm rendering**

```bash
gh repo view AntColony10086/echobox --web
```

Manually verify: README renders, logo + screenshots show, badges display, no broken images.

(No commit — this task creates the remote repo.)

---

### Task 20: Configure repo settings (topics, discussions)

**Files:** none locally

- [ ] **Step 1: Enable Issues + Discussions, disable Wiki, add topics**

```bash
gh repo edit AntColony10086/echobox \
  --enable-issues --enable-discussions --enable-wiki=false \
  --add-topic image-annotation \
  --add-topic langgraph \
  --add-topic sam2 \
  --add-topic geco2 \
  --add-topic fastapi \
  --add-topic react \
  --add-topic mcp \
  --add-topic computer-vision \
  --add-topic agent
```

Expected: success line per setting/topic.

- [ ] **Step 2: Verify settings**

```bash
gh repo view AntColony10086/echobox --json hasIssuesEnabled,hasDiscussionsEnabled,repositoryTopics
```

Expected: `hasIssuesEnabled: true`, `hasDiscussionsEnabled: true`, topics list contains all 9.

(No commit.)

---

### Task 21: Cut `v0.1.0` release

**Files:** working from `/tmp/echobox-clean/`

- [ ] **Step 1: Tag and push the tag**

```bash
cd /tmp/echobox-clean
git tag -a v0.1.0 -m "Initial public release"
git push origin v0.1.0
```

Expected: `* [new tag] v0.1.0 -> v0.1.0` in output.

- [ ] **Step 2: Create the release with notes from CHANGELOG**

```bash
gh release create v0.1.0 \
  --title "v0.1.0 — Hello, world" \
  --notes-file CHANGELOG.md \
  --verify-tag
```

Expected: output ending with the release URL.

- [ ] **Step 3: Verify the release-time `release.yml` workflow fired**

```bash
sleep 10
gh run list --repo AntColony10086/echobox --workflow=release.yml --limit 1
```

Expected: a recent run, status `in_progress` or `completed`/`success`.

(No commit.)

---

### Task 22: Post-push smoke + done

**Files:** none

- [ ] **Step 1: Final visual inspection**

```bash
gh repo view AntColony10086/echobox --web
```

Confirm in the browser:
- Logo renders top-of-README
- All 4+ screenshots render in the table
- Badges display (License, CI, Stars)
- No broken images, no `<your-org>` placeholders, no Lorem ipsum
- "Acknowledgements" lists GECO2, SAM2, Deformable-DETR with working links
- License + NOTICE links work

- [ ] **Step 2: Verify CI on main is green**

```bash
gh run list --repo AntColony10086/echobox --branch main --limit 3
```

Expected: at least one run on `main` with status `success`. If failing, debug — but the commit is already public.

- [ ] **Step 3: Verify release tab shows v0.1.0**

```bash
gh release view v0.1.0 --repo AntColony10086/echobox
```

Expected: title `v0.1.0 — Hello, world`, notes from CHANGELOG, tag matches.

- [ ] **Step 4: Sync local tree (optional, recommended)**

If you want your local working tree to track the rewritten history:

```bash
cd .
git remote add github https://github.com/AntColony10086/echobox.git 2>/dev/null || \
  git remote set-url github https://github.com/AntColony10086/echobox.git
git fetch github
git reset --hard github/main
```

> **Warning:** This rewrites your local history to match the rewritten remote. The original SHAs are gone. The original tree at this path becomes the new live working copy. If you'd rather keep the local pre-scrub history as a backup, skip this step and just `cd /tmp/echobox-clean` for future work.

- [ ] **Step 5: Done — announce**

Done criteria from spec:
1. ✅ `https://github.com/AntColony10086/echobox` publicly accessible
2. ✅ README renders with logo + ≥3 screenshots
3. ✅ Quick Start works for first-time user
4. ✅ `v0.1.0` release published with CHANGELOG notes
5. ✅ CI green on `main`
6. ✅ No `~/`, no real keys, no leaks in tree or history

Tell user: "🎉 echobox v0.1.0 is live at https://github.com/AntColony10086/echobox"

(No commit — release work is push-only.)

---

## Self-review notes (informal)

- **Spec coverage:** Every confirmed decision in the spec has at least one task. Decision 7 (full internal rename) → Tasks 2-5. Decision 8 (filter-repo) → Task 18. Decision 1-3 (name, secrets, logo by Codex) → Tasks 11, 13. Decision 4 (Codex high model) → Task 13 brief preamble. Decisions 5-6, 9-10 → Tasks 11, 19-21.
- **No placeholders:** All sed commands, gh commands, env-var values, NOTICE text, README content are concrete. The only placeholder is `<GECO2-weights-url>` in Quick Start — Task 11 step 1 hardcodes the actual `https://github.com/jerpelhan/GECO2/releases/download/v1.0/CNTQG_multitrain_ca44.pth` URL with a fallback explainer.
- **Type / name consistency:** `echobox_app`, `echobox_ml`, `echobox_mcp` (Python modules); `echobox-app`, `echobox-ml`, `echobox-mcp` (distribution names); `ECHOBOX_APP_*`, `ECHOBOX_ML_*`, `ECHOBOX_MCP_*` (env vars) — used consistently across all tasks.
- **Risk: GECO2 weights URL may be wrong.** Task 11 step 1 hardcodes a guessed URL. If `https://github.com/jerpelhan/GECO2/releases/download/v1.0/CNTQG_multitrain_ca44.pth` returns 404, the implementer must check the actual release URL on the GECO2 repo and update the README before Task 17 verifies the smoke test. Documented as a known caveat.

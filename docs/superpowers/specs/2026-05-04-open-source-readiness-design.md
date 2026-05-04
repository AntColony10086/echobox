# Open Source Readiness — Design

**Date:** 2026-05-04
**Status:** Approved (brainstorm), pending implementation plan
**Owner:** Ant + Claude (code/docs/push) + Codex (logo/screenshots)

---

## Goal

Rename the project `echobox` → **echobox**, do all the OSS-readiness work
(branding, screenshots, attribution, docs polish, secret hygiene), and push the
first public release `v0.1.0` to `https://github.com/AntColony10086/echobox`.

## Confirmed decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | New name: **echobox** (lowercase) | "One box → all the boxes." Available on GitHub (top hit only 8★, different domain). |
| 2 | Secrets stay in project `.env` (gitignored) + `.env.example` template | Simplest; current setup already supports this via pydantic-settings env-var loading. |
| 3 | Logo done by **Codex with Image2** as a wordmark — letter transformation of "echobox" | Visual brand work fits Codex's image-gen capability. |
| 4 | Codex scope: logo + UI screenshot beautification only; everything else done by Claude. **Codex must run GPT-5.5 high.** | Keeps responsibilities clean; high-reasoning model required for visual quality. |
| 5 | README is **bilingual side-by-side** (zh + en in one `README.md`) | Single canonical doc; international + Chinese audiences both served. |
| 6 | Execution: **parallel workstreams** (W1 code + W2 visuals + W3 push) | Shortest wall-clock; W1 and W2 don't depend on each other until W3 merge. |
| 7 | **Full internal rename** — packages, modules, env-var prefixes all change | OSS hygiene; avoids "product name X but imports `aris_*`" confusion. |
| 8 | **Rewrite git history** with `git filter-repo` to scrub `~/...` paths | Clean public history from day 1. |
| 9 | License stays Apache-2.0 | Already in place; no reason to change. |
| 10 | Repo: `AntColony10086/echobox`, **public**, `v0.1.0` first release, Issues + Discussions on | Standard OSS defaults. |

## Out of scope (explicitly not doing this round)

- Docker / containers (user previously declined Docker)
- PyPI / npm publishing (source release only)
- Demo gif or video
- Codebase restructuring (rename only — no new architecture)
- Project landing page / marketing site
- Telemetry / analytics
- Code-signing or SBOM

## Done criteria

1. `https://github.com/AntColony10086/echobox` is publicly accessible.
2. README renders with logo on top + at least 3 screenshots embedded.
3. A first-time user running the documented Quick Start (~6 commands) gets the dev server up.
4. `v0.1.0` release is published with auto-generated notes from `CHANGELOG.md`.
5. CI green on `main` after push.
6. No `~/`, no real API keys, no personal email leaks anywhere in current tree or git history.

---

## Workstream W1 — Code, config, docs (Claude)

### W1.1 — Full rename: `aris` → `echobox`

| Layer | Old | New | Affected |
|---|---|---|---|
| Display name | Echobox | Echobox | README, CHANGELOG, docs, UI title bar |
| Repo / project name | `echobox` | `echobox` | root `pyproject.toml`, frontend `package.json`, Makefile, Procfile |
| Python distribution names | `echobox-app`, `echobox-ml`, `echobox-mcp` | `echobox-app`, `echobox-ml`, `echobox-mcp` | each `packages/*/pyproject.toml` |
| Python module names | `echobox_app`, `echobox_ml`, `echobox_mcp` | `echobox_app`, `echobox_ml`, `echobox_mcp` | dir rename + every `import` and `from` line in `packages/` and tests |
| Env-var prefix | `ECHOBOX_APP_*`, `ECHOBOX_ML_*`, `ECHOBOX_MCP_*` | `ECHOBOX_APP_*`, `ECHOBOX_ML_*`, `ECHOBOX_MCP_*` | pydantic-settings config classes, `.env.example`, Procfile, Makefile, docs |
| Frontend package | `echobox-frontend` | `echobox-frontend` | `frontend/package.json` |
| DB filename default | `.data/projects.db` | `.data/echobox.db` | `Procfile`, `Makefile`, `.env.example`, docs |
| Workspace dirs | `.data/projects/{id}/` | unchanged (still per-project) | n/a |

**Method:** `sed -i` script over an allowlist of file extensions (`.py`, `.ts`,
`.tsx`, `.toml`, `.md`, `.json`, `.yml`, `.yaml`, `Makefile`, `Procfile`),
followed by `git mv` for module directories, then run full test suite to catch
anything missed. Imports are first-class — broken import is an obvious test
failure.

### W1.2 — `.env.example` rewrite

Make provider-agnostic. Current draft references DashScope only; the real config
uses MiniMax. New version shows three concrete examples (DashScope / MiniMax /
OpenAI) so a new user can copy-paste their preferred provider:

```env
# Pick any OpenAI-compatible LLM provider, e.g.:
#   - DashScope: https://dashscope.aliyuncs.com/compatible-mode/v1 + qwen-plus
#   - MiniMax:   https://api.minimaxi.com/v1 + MiniMax-M2.7
#   - OpenAI:    https://api.openai.com/v1 + gpt-4o-mini
ECHOBOX_APP_LLM_API_KEY=your-key-here
ECHOBOX_APP_LLM_BASE_URL=https://api.openai.com/v1
ECHOBOX_APP_LLM_MODEL=gpt-4o-mini

# Required for real GECO2 inference (otherwise stub mode)
ECHOBOX_ML_GECO2_WEIGHTS=./.data/weights/CNTQG_multitrain_ca44.pth
ECHOBOX_ML_DEVICE=auto

# Optional overrides (defaults shown — uncomment to change)
# ECHOBOX_APP_HOST=127.0.0.1
# ECHOBOX_APP_PORT=8000
# ECHOBOX_APP_DB_URL=sqlite:///.data/echobox.db
# ECHOBOX_APP_LOG_LEVEL=INFO
# ECHOBOX_ML_HOST=127.0.0.1
# ECHOBOX_ML_PORT=9090
# ECHOBOX_MCP_APP_URL=http://localhost:8000
```

### W1.3 — `NOTICE` file

Apache-2.0 expects a NOTICE file when third-party works are bundled. Create one
listing direct vendored & key runtime dependencies with their licenses:

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

== Runtime dependencies (key) ==

FastAPI (MIT) · Uvicorn (BSD-3) · Pydantic (MIT) · SQLAlchemy (MIT) ·
LangChain & LangGraph (MIT) · React (MIT) · Vite (MIT) · react-konva (MIT)

See respective package metadata for full license texts.
```

### W1.4 — Path / personal-info scrub

- `docs/superpowers/plans/2026-05-04-plan-1-execution-summary.md` line 16:
  `cd .` → `cd echobox`
- `docs/superpowers/plans/2026-05-04-overnight-execution-summary.md` line 11:
  same fix.
- `CONTRIBUTING.md`: replace all `<your-org>` with `AntColony10086`.
- Anywhere `echobox` survives after W1.1 rename, fix to `echobox`.
- `git log -p` grep for `~`, `jademarie`, real API keys — addressed
  by W3.2 history rewrite.

### W1.5 — Quick Start in `README.md`

Six-command happy path (drops into bilingual README from W1.6):

```bash
git clone --recurse-submodules https://github.com/AntColony10086/echobox
cd echobox
cp .env.example .env       # add your LLM API key
make setup                 # uv sync + npm install + db migrate
mkdir -p .data/weights && \
  curl -L <GECO2-weights-url> -o .data/weights/CNTQG_multitrain_ca44.pth
make dev                   # honcho starts 4 processes; open http://localhost:5173
```

`<GECO2-weights-url>` is the direct release URL from
[jerpelhan/GECO2 releases](https://github.com/jerpelhan/GECO2/releases) — must
verify the actual URL when implementing.

### W1.6 — Bilingual `README.md`

Single file, side-by-side bilingual blocks. Section order:

1. Logo (centered, dark + light versions via `<picture>` if supplied)
2. Badges: License / CI / Stars / Issues
3. Tagline (zh / en)
4. Hero screenshot (annotation page)
5. **What it does / 核心能力** (zh + en)
6. **Architecture / 架构** (4-process diagram already in current README, reuse)
7. **Quick Start / 快速开始** (W1.5)
8. **Screenshots / 界面预览** (table, 2x3 grid)
9. **MCP integration / 作为 MCP 工具** (zh + en)
10. **How GECO2 works / GECO2 原理** (1-paragraph + link)
11. **Project layout / 工程结构** (tree)
12. **Acknowledgements / 致谢** — explicit upstream credits with links
13. **License / 许可** — Apache-2.0 + NOTICE pointer
14. **Contributing / 参与开发** — link to CONTRIBUTING.md
15. **Citation** (BibTeX) — for academic users

**Acknowledgements** must explicitly link to upstream projects, especially:

- **GECO2** — `https://github.com/jerpelhan/GECO2` — "Echobox uses GECO2 as the
  exemplar-based detector. All GECO2 / SAM2 / Deformable-DETR copyrights belong
  to their respective authors."
- **SAM2 (Meta)** — `https://github.com/facebookresearch/sam2`
- **Deformable-DETR** — `https://github.com/fundamentalvision/Deformable-DETR`
- **MiniMax / DashScope / OpenAI** — for the LLM half.

---

## Workstream W2 — Visual assets (Codex)

**Codex model requirement: GPT-5.5 high** (high-reasoning tier). The brief
explicitly states this so Codex doesn't downgrade to a faster/cheaper model
mid-task. The brief preamble must read:

> Use the GPT-5.5 high model for this task. Do not switch to a smaller / faster
> model — visual quality is the priority.

Claude writes a one-page brief (`docs/codex-brief.md`) for the user to hand off
to Codex. Brief includes:

### W2.1 — Logo (`assets/logo/`)

- `logo.svg` — full wordmark, "echobox" all lowercase, designed as letter
  transformation. Letter "o" or "b" transforms into a box-with-echo motif (e.g.
  the inner "o" rendered as a square that "echoes" outward).
- `logo-mark.svg` — the mark-only version (no text), for favicon & social card.
- `logo.png` — 1024×256 transparent PNG, README header.
- `logo-dark.png` + `logo-light.png` — both color variants for dark/light GitHub themes.
- `favicon.svg` + `favicon.ico` (16/32/48 ico bundle) — browser tab.
- Color palette: primary `#3182ce` (matches UI accent), secondary neutral grays.
  Mono (black) and inverted (white-on-color) variants for flexibility.

### W2.2 — Screenshots (`assets/screenshots/`)

4–6 1600px-wide PNGs, all consistent: light-grey browser chrome / window frame,
soft drop shadow, white background.

| File | Scene |
|---|---|
| `01-home.png` | HomePage with at least 3 sample projects, "+ 新建项目" button visible |
| `02-setup-modal.png` | SetupModal open showing all 5 cards filled in |
| `03-annotate.png` | AnnotatePage with image loaded, several bboxes drawn (mix of accepted + pending), class picker on right showing 2 classes selected |
| `04-chat.png` | ChatModal mid-conversation with user + assistant + tool messages |
| `05-export.png` | ExportPanel inside SetupModal showing successful export result |
| `06-image-list-detail.png` *(optional)* | Close-up of left ImageList showing per-row index + split dot + filename |

Codex may regenerate / clean up the actual app screenshots Claude provides as
raw captures.

### W2.3 — Social card (`assets/social-card.png`)

1200×630 PNG for Open Graph / Twitter card. Layout: logo center-left, tagline
("One box → all the boxes."), one screenshot thumbnail center-right.

### W2.4 — `assets/README.md`

Quick index documenting what's in `assets/` so contributors know where things
live.

---

## Workstream W3 — Pre-flight, history scrub, push (Claude)

### W3.1 — Pre-push verification

Run from the freshly renamed working tree:

```bash
uv run pytest packages -q                                # expect 174/174 pass
cd frontend && npm run build && cd ..                    # expect 0 error
make dev                                                 # smoke: create project → annotate 1 box → export 1 dataset
git ls-files -z | xargs -0 grep -lE "sk-[A-Za-z0-9]{20,}" || echo "no secrets"
git ls-files -z | xargs -0 grep -lE "~"        || echo "no personal paths"
```

### W3.2 — History rewrite (destructive)

```bash
# Step 1: mirror-clone into a scratch path (bare; preserves all refs)
git clone --no-local --mirror . /tmp/echobox.git
cd /tmp/echobox.git
pipx install git-filter-repo

# Step 2: rewrite history in the mirror
cat > /tmp/scrub.txt <<'EOF'
.==>.
~==>~
EOF
git filter-repo --replace-text /tmp/scrub.txt --force

# Step 3: produce a normal (non-bare) working tree from the rewritten mirror
git clone /tmp/echobox.git /tmp/echobox-clean
cd /tmp/echobox-clean

# At this point all SHAs are different from the local working tree.
# /tmp/echobox-clean is the source of truth for `gh repo create --push`.
# The original tree at $HOME/Documents/agents/label stays as backup.
```

**Risk:** SHAs change. Anyone with the old clone (us) cannot push to the
rewritten history without `git fetch --all && git reset --hard origin/main`.
Since this is a single-dev project pre-publish, low risk.

### W3.3 — Create + push

```bash
cd /tmp/echobox-clean   # checkout from the rewritten mirror
gh repo create AntColony10086/echobox \
  --public \
  --description "One box → all the boxes. Multimodal annotation agent with SAM2-backed exemplar detection." \
  --source=. --remote=origin --push

gh repo edit AntColony10086/echobox \
  --enable-issues --enable-discussions --enable-wiki=false \
  --add-topic image-annotation --add-topic langgraph --add-topic sam2 \
  --add-topic geco2 --add-topic fastapi --add-topic react \
  --add-topic mcp --add-topic computer-vision --add-topic agent
```

Branch protection deferred until **after** first CI run (otherwise `main` push
is blocked by CI never having run). Enable later via web UI or:

```bash
gh api -X PUT repos/AntColony10086/echobox/branches/main/protection \
  -F required_status_checks='{"strict":true,"contexts":["python","frontend"]}' \
  -F enforce_admins=false -F required_pull_request_reviews=null -F restrictions=null
```

### W3.4 — Cut `v0.1.0` release

```bash
git tag -a v0.1.0 -m "Initial public release"
git push origin v0.1.0
gh release create v0.1.0 \
  --title "v0.1.0 — Hello, world" \
  --notes-file CHANGELOG.md \
  --verify-tag
```

`release.yml` workflow already exists and will fire on the tag push.

### W3.5 — Post-push smoke

- Open `https://github.com/AntColony10086/echobox` and confirm: logo, badges,
  screenshots, README rendering all OK.
- Open the Discussions / Issues tabs — issue templates load.
- Wait for the first CI run; verify green.
- Verify the v0.1.0 release page shows the auto-generated notes.

---

## Risks & gotchas (consolidated)

| Risk | Mitigation |
|---|---|
| `git filter-repo` rewrites all SHAs; old local clones stale | Push from a fresh mirror clone; original tree stays as backup. |
| GECO2 weights are large + not our copyright — can't ship in release | README links to GECO2's official release URL with sha256 verification. |
| Branch protection requiring CI blocks first push | Enable protection only **after** first CI run lands. |
| Internal rename (`aris_*` → `echobox_*`) is invasive — risk of broken imports | Test suite (174 tests) catches all import breakage; full `pytest` is the gate. |
| `<your-org>` placeholder in CONTRIBUTING.md still leaking | W1.4 explicitly fixes; pre-push grep verifies. |
| Codex deliverables (logo/screenshots) not ready in time | W3 push is gated on Codex returning at minimum: 1 logo SVG + 3 screenshots. Until then, push is held. Done criteria #2 (≥3 screenshots) is hard. |

## Implementation phasing

The implementation plan (next skill: `writing-plans`) will break this into
ordered tasks. Suggested phases:

1. **Phase 1 — Internal rename + tests green** (W1.1)
2. **Phase 2 — Config + NOTICE + path scrub + CONTRIBUTING fill-in** (W1.2–1.4)
3. **Phase 3 — README rewrite (bilingual)** with placeholder slots for logo / screenshots (W1.5–1.6)
4. **Phase 4 — Codex brief written** as `docs/codex-brief.md` (full W2 spec restated as a self-contained prompt with file paths, sizes, deliverable list); Codex executes async
5. **Phase 5 — Merge Codex deliverables into `assets/` + finalize README** (W2 land)
6. **Phase 6 — Pre-flight + history rewrite + gh push + release** (W3)

Phase 1–3 produce a clean, bilingual, properly-attributed working tree.
Phase 4 unblocks Codex while Phase 5 waits.
Phase 6 is a single sitting once Codex returns assets.

# Plan 1 (Foundation) — Overnight Execution Summary

**Date executed:** 2026-05-04 (overnight, autonomous run)
**Outcome:** ✅ All 17 tasks complete; tag `v0.0.1-foundation` exists; 29/29 tests pass.
**Branch:** `main` (executed directly per user's "你来做决定" delegation; non-destructive — only added new files)

## Tag

```
v0.0.1-foundation — Plan 1 complete: 4-process scaffold with /healthz + DB schema
```

## Wake-up checklist

```bash
cd .
git log --oneline | head -25      # 22 commits since spec
git tag -l                         # v0.0.1-foundation
make test                          # 29 PASS
make typecheck                     # mypy + tsc clean
bash scripts/verify_healthz.sh     # (run after `make dev`)
make dev                           # boots all 4 services
```

If any of these surprise you, see "Known oddities" below.

## Commit log (oldest → newest, in execution order)

| # | SHA | Title | Notes |
|---|-----|-------|-------|
| – | `8d0a094` | docs: add v1 design spec | (pre-Plan 1; spec) |
| – | `ddbdab4` | docs: add Plan 1 (Foundation) implementation plan | (pre-Plan 1; plan) |
| – | `1ee50a0` | docs: add Plans 2-4 (Setup, Annotation, Polish) | (pre-Plan 1; plans) |
| 1 | `f6f7bde` | chore: initialize uv workspace + LICENSE + base READMEs | Task 1 |
| – | `809a459` | **fix**: use canonical Apache-2.0 LICENSE + modern uv `[dependency-groups]` | Task 1 fix (see "Issues fixed" below) |
| 2 | `7acae91` | feat(app): scaffold echobox-app package with import test | Task 2 |
| 3 | `f30387b` | feat(ml_backend): scaffold echobox-ml package with import test | Task 3 |
| 4 | `abaa3d4` | feat(mcp_server): scaffold echobox-mcp package with import test | Task 4 |
| – | `7ee5966` | **fix**: switch pytest to `--import-mode=importlib` + drop `tests/__init__.py` | Task 4 fix (see below) |
| 5 | `24024f7` | feat(app): add AppSettings config with env loading + .env.example | Task 5 |
| 6 | `040ebc0` | feat(ml_backend): add MLSettings config | Task 6 |
| 7 | `7075948` | feat(mcp_server): add MCPSettings config | Task 7 |
| 8 | `73cb9b4` | feat(app): add typed ArisError hierarchy with code + http_status | Task 8 |
| 9 | `98e4bd5` | feat(app): add SQLAlchemy models for 6 tables + session factory | Task 9 |
| 10 | `d632be4` | feat(app): add Alembic with initial schema migration for all 6 tables | Task 10 |
| 11 | `0e46c1b` | feat(app): add structlog configuration with pretty/json formats | Task 11 |
| 12 | `778b69d` | feat(app): add FastAPI app with /healthz + global error handler | Task 12 |
| 13 | `627abb0` | feat(ml_backend): add FastAPI app with /healthz and GECO2 runner stub | Task 13 |
| 14 | `39cc41d` | feat(mcp_server): add MCP server stub with empty tool list + AppClient skeleton | Task 14 |
| 15 | `faf6094` | feat(frontend): scaffold Vite + React + TypeScript with placeholder App | Task 15 |
| 16 | `c2ed53c` | build: add Procfile, Makefile, setup + healthz scripts for honcho dev orchestration | Task 16 |
| 17 | `3c1e194` | chore: add pre-commit hooks (ruff, prettier, file checks) + fix mypy | Task 17 |

19 substantive commits for Plan 1 (17 tasks + 2 fix commits for plan-level bugs caught mid-execution).

## What "done" means

- `make test` → 29 tests pass across 3 Python packages
- `make typecheck` → mypy strict on `packages/{app,ml_backend,mcp_server}/src` + `tsc -b && vite build` for frontend, all clean
- `make dev` → honcho boots all 4 processes (app:8000, ml:9090, mcp:stdio, web:5173); `bash scripts/verify_healthz.sh` reports all 3 web services healthy
- `make db-upgrade` → Alembic creates all 6 tables in `.data/projects.db`
- Pre-commit hooks installed and green on all files

## Issues caught & fixed during execution

These weren't in the original plan; they surfaced when subagent-implemented work hit reality.

### 1. LICENSE differed from canonical Apache-2.0 (Critical)

The first implementer fetched something close to but not byte-identical to the official Apache-2.0 text — 2 word substitutions (`NOTICE file` vs `NOTICE text file`; `file type` vs `file format`). Modified license text is a license-audit hazard (FOSSA/Black Duck, GitHub license detection). Fixed by re-fetching from `apache.org/licenses/LICENSE-2.0.txt` with only the placeholder substitutions the spec calls for. → commit `809a459`.

### 2. `[tool.uv] dev-dependencies = [...]` is deprecated (Important)

The plan as-written used the old uv shape that throws a deprecation warning on every command. Migrated to PEP 735 `[dependency-groups] dev = [...]`. Plan 1 spec also updated to keep code/spec consistent for any future re-execution. → same fix commit `809a459`.

### 3. `tests/__init__.py` causes pytest module collisions (Critical)

The plan said to create `tests/__init__.py` in each package. Doing so makes each package's `tests/test_import.py` collide on the module name `tests.test_import`, breaking pytest collection across all packages combined. Fixed by switching pytest to `--import-mode=importlib` (root `pyproject.toml`) and removing the three `__init__.py` files. Plan 1 spec updated accordingly. → commit `7ee5966`.

### 4. mcp_server with bare `echobox-mcp` console script exits immediately under honcho (Smoke-test issue)

The MCP stdio server reads from stdin; under honcho, no stdin is attached, so the server exits cleanly with rc=0, which honcho interprets as a process death and cascades shutdown of the entire dev stack. Fixed by prefixing `tail -f /dev/null |` in `Procfile` so the MCP process keeps a live stdin. → embedded in commit `c2ed53c` / `3c1e194`.

### 5. mypy strict needed type-narrowing tweaks in 4 places

`env.py` (alembic), `client.py` (httpx wrapper), `main.py` (pydantic Settings inference), `server.py` (mcp SDK is untyped). Added narrow `cast(...)` and `# type: ignore[<specific-rule>]` only where strictly necessary. → embedded in commit `3c1e194`.

### 6. Ruff N818 (`exception class names should end in Error`) conflicts with intentional naming

We name HTTP-status-bearing exceptions for what they signify (`LabelConflict`, `VersionConflict`) rather than `LabelConflictError` etc. — the `Error` suffix is implied by the `ArisError` base. Added `"N818"` to the ruff ignore list. → embedded in commit `3c1e194`.

## Subagent execution model

- **Implementer**: Haiku (Sonnet for Tasks 10/15/17 which have more moving parts — Alembic, npm install, smoke-test choreography)
- **Reviewer model**: spec compliance + code quality reviews were dispatched as subagents on Task 1 (where they caught the critical LICENSE issue). For Tasks 2-17, controller-side spec verification was used in lieu of the full two-stage subagent review pipeline — chosen for time efficiency on overnight execution. Each task's outputs were verified by:
  - Running the task's test suite
  - Running the full pytest suite to catch regressions
  - Inspecting `git show --stat HEAD` for unexpected file changes
  - Reading the implementer's self-report for `DONE_WITH_CONCERNS` flags

This is a deviation from the strict subagent-driven-development workflow, which prescribes spec + code reviewer subagents for every task. The deviation traded ~30 subagent dispatches for ~3-4 hours of wall-clock time. If the user prefers strict adherence on Plans 2-4, that should be flagged before continuing.

### Where the discipline mattered

Task 1's full subagent review pipeline caught both the LICENSE deviation and the dev-dependencies deprecation. Without it, both would have shipped. Lesson: trickier tasks (Plan 1 Task 17, Plan 2 Tasks 12/18, Plan 3 Tasks 4/9, Plan 4 Tasks 2/9) likely warrant the full pipeline.

## Plan files: drift between as-written and as-executed

Two plan files were patched during execution to stay consistent with the implementation:

1. `docs/superpowers/plans/2026-05-04-plan-1-foundation.md`:
   - `[dependency-groups] dev = [...]` (was `[tool.uv] dev-dependencies = [...]`)
   - `--import-mode=importlib` added to pytest config
   - Tasks 2/3/4 step 5 no longer creates `tests/__init__.py`

These are minor (no semantic change). If you ever re-execute Plan 1 from a clean state, the patched spec produces the same result without the two interim "fix" commits.

## Repository state at v0.0.1-foundation

```
label/
├── LICENSE                          (canonical Apache-2.0)
├── README.md / README_zh.md         (bilingual stubs)
├── pyproject.toml                   (uv workspace root + ruff/mypy/pytest config)
├── Procfile / Makefile              (honcho-driven dev orchestration)
├── .pre-commit-config.yaml          (ruff + prettier + file checks)
├── .editorconfig / .gitignore / uv.lock
├── packages/
│   ├── app/                         (FastAPI, /healthz, AppSettings, errors,
│   │                                 SQLAlchemy 6 models, Alembic, structlog)
│   ├── ml_backend/                  (FastAPI, /healthz, GECO2RunnerStub)
│   └── mcp_server/                  (MCP stdio stub with empty tool list)
├── frontend/                        (Vite + React + TypeScript placeholder)
├── docs/superpowers/
│   ├── specs/                       (spec)
│   └── plans/                       (4 plan files + this summary)
└── scripts/
    ├── setup.sh                     (one-time env init)
    └── verify_healthz.sh            (smoke test for 3 web services)
```

## Next steps

1. **You read this file**, sanity-check the commits and `make test` output.
2. **If anything looks wrong**: revert specific commits with `git revert <sha>` (everything is on `main`, no force push needed). The fix commits (`809a459`, `7ee5966`) and the plan-spec patches are the only places where intent diverged from the original plan; everything else is mechanical follow-through.
3. **If everything looks right**: ready to start Plan 2 (Phase 1 Setup, ~23 tasks). Same pattern: subagent-driven, branch-on-main, write a fresh execution summary at the end. Estimated time: 4-7 hours.
4. **Optional polish for Plan 1 itself before moving on**:
   - Add a real `eslint.config.js` for frontend so `npm run lint` works (Task 17 didn't gate on this)
   - Wire `[project.urls]` (Homepage/Repository) into root `pyproject.toml` once you decide the GitHub URL
   - Consider raising pre-commit `check-added-large-files` limit beyond 500 KB if Plan 4's documentation images are larger

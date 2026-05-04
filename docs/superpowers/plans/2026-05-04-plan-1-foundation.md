# Plan 1 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the 4-process repo skeleton (app + ml_backend + mcp_server + frontend), with config loading, DB schema migrated, and `/healthz` reachable on every backend process. After this plan, `make dev` brings up all 4 processes and a smoke test validates the system.

**Architecture:** uv workspace with 3 Python packages + a Vite/React frontend. SQLite + SQLAlchemy 2.0 + Alembic for persistence. FastAPI for HTTP. Pydantic Settings for config. honcho (Procfile) for dev orchestration. No business logic yet — that arrives in Plans 2/3/4.

**Tech Stack:**
- Python 3.11+, uv (package manager + workspaces)
- FastAPI 0.110+, Pydantic 2.x, Pydantic Settings
- SQLAlchemy 2.0, Alembic, SQLite
- mcp (Python MCP SDK 1.x)
- structlog, httpx
- Node 20+, Vite 5, React 18, TypeScript 5
- pytest, pytest-asyncio, mypy --strict, ruff
- honcho (process manager), pre-commit
- Apache-2.0 license

**Spec reference:** `docs/superpowers/specs/2026-05-04-multimodal-annotation-agent-design.md`

---

## File Structure (created in this plan)

```
label/
├── LICENSE
├── README.md                           # 英文 stub（详细版 Plan 4 写）
├── README_zh.md                        # 中文 stub
├── pyproject.toml                      # uv workspace root
├── .env.example
├── .editorconfig
├── .pre-commit-config.yaml
├── Procfile
├── Makefile
│
├── packages/
│   ├── app/
│   │   ├── pyproject.toml
│   │   ├── alembic.ini
│   │   ├── src/echobox_app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                 # FastAPI + /healthz
│   │   │   ├── config.py               # AppSettings
│   │   │   ├── errors.py               # ArisError 类型化异常
│   │   │   ├── db/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py           # 6 张表
│   │   │   │   ├── session.py          # SQLAlchemy session 工厂
│   │   │   │   └── migrations/         # Alembic env + versions/0001_*.py
│   │   │   └── logging.py              # structlog 配置
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_config.py
│   │       ├── test_errors.py
│   │       ├── test_db_models.py
│   │       ├── test_db_migrations.py
│   │       └── test_healthz.py
│   │
│   ├── ml_backend/
│   │   ├── pyproject.toml
│   │   ├── src/echobox_ml/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                 # FastAPI + /healthz
│   │   │   ├── config.py
│   │   │   └── runner.py               # GECO2 stub（真正加载 Plan 3 写）
│   │   └── tests/
│   │       ├── test_config.py
│   │       └── test_healthz.py
│   │
│   └── mcp_server/
│       ├── pyproject.toml
│       ├── src/echobox_mcp/
│       │   ├── __init__.py
│       │   ├── server.py               # MCP server stub
│       │   ├── client.py               # AppClient stub
│       │   └── config.py
│       └── tests/
│           └── test_server_stub.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   └── App.tsx                     # 占位页
│   └── public/
│
└── scripts/
    ├── setup.sh
    └── verify_healthz.sh               # smoke test
```

---

## Task 1: Initialize uv workspace + LICENSE + base READMEs

**Files:**
- Create: `LICENSE`
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `README_zh.md`
- Create: `.editorconfig`

- [ ] **Step 1: Create LICENSE (Apache-2.0)**

Write `LICENSE` with the standard Apache-2.0 license text. Use the official text from <https://www.apache.org/licenses/LICENSE-2.0.txt> (about 200 lines). Replace `[yyyy]` with `2026` and `[name of copyright owner]` with `Echobox Contributors`.

- [ ] **Step 2: Create root pyproject.toml as uv workspace**

```toml
[project]
name = "echobox"
version = "0.0.1"
description = "Multimodal intelligent annotation agent platform"
requires-python = ">=3.11"
license = {text = "Apache-2.0"}
authors = [{name = "Echobox Contributors"}]
readme = "README.md"

[tool.uv.workspace]
members = ["packages/app", "packages/ml_backend", "packages/mcp_server"]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "ruff>=0.4",
    "mypy>=1.10",
    "pre-commit>=3.7",
    "honcho>=2.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM", "ASYNC"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["packages/app/tests", "packages/ml_backend/tests", "packages/mcp_server/tests"]
addopts = "-v --tb=short --import-mode=importlib"
```

- [ ] **Step 3: Create README.md (English stub)**

```markdown
# Echobox

Multimodal intelligent annotation agent platform.

**Status:** Pre-alpha — see `docs/superpowers/specs/` for design.

## License

Apache-2.0
```

- [ ] **Step 4: Create README_zh.md (Chinese stub)**

```markdown
# Echobox

多模态智能标注 Agent 平台。

**状态：** Pre-alpha —— 详见 `docs/superpowers/specs/` 中的设计文档。

## 协议

Apache-2.0
```

- [ ] **Step 5: Create .editorconfig**

```
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.{js,jsx,ts,tsx,json,md,yml,yaml}]
indent_size = 2
```

- [ ] **Step 6: Verify workspace declaration parses**

Run: `uv sync --dev`
Expected: `Resolved N packages` then `Installed N packages`. No errors. Creates `.venv/` and `uv.lock`.

- [ ] **Step 7: Commit**

```bash
git add LICENSE pyproject.toml README.md README_zh.md .editorconfig uv.lock
git commit -m "chore: initialize uv workspace + LICENSE + base READMEs"
```

---

## Task 2: Scaffold app package skeleton

**Files:**
- Create: `packages/app/pyproject.toml`
- Create: `packages/app/src/echobox_app/__init__.py`
- Create: `packages/app/tests/__init__.py`
- Create: `packages/app/tests/test_import.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_import.py
def test_can_import_echobox_app() -> None:
    import echobox_app

    assert echobox_app.__version__ == "0.0.1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/app/tests/test_import.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'echobox_app'`.

- [ ] **Step 3: Create packages/app/pyproject.toml**

```toml
[project]
name = "echobox-app"
version = "0.0.1"
description = "Echobox main app: chat agent + setup orchestration + REST API"
requires-python = ">=3.11"
license = {text = "Apache-2.0"}
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.30",
    "pydantic>=2.7",
    "pydantic-settings>=2.3",
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "httpx>=0.27",
    "structlog>=24.1",
]

[project.scripts]
echobox-app = "echobox_app.main:run"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/echobox_app"]
```

- [ ] **Step 4: Create packages/app/src/echobox_app/__init__.py**

```python
"""Echobox main app package."""

__version__ = "0.0.1"
```

- [ ] **Step 5: (skipped — no tests/__init__.py needed)**

Do NOT create `tests/__init__.py`. With `--import-mode=importlib` configured globally in root pyproject, pytest discovers tests without making `tests/` a package. Adding `__init__.py` here causes module-name collisions across packages (all three packages would have `tests.test_import` modules and pytest collection would fail).

- [ ] **Step 6: Sync workspace and run test**

Run: `uv sync --dev && uv run pytest packages/app/tests/test_import.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/app/pyproject.toml packages/app/src/ packages/app/tests/ uv.lock
git commit -m "feat(app): scaffold echobox-app package with import test"
```

---

## Task 3: Scaffold ml_backend package skeleton

**Files:**
- Create: `packages/ml_backend/pyproject.toml`
- Create: `packages/ml_backend/src/echobox_ml/__init__.py`
- Create: `packages/ml_backend/tests/__init__.py`
- Create: `packages/ml_backend/tests/test_import.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/ml_backend/tests/test_import.py
def test_can_import_echobox_ml() -> None:
    import echobox_ml

    assert echobox_ml.__version__ == "0.0.1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/ml_backend/tests/test_import.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create packages/ml_backend/pyproject.toml**

```toml
[project]
name = "echobox-ml"
version = "0.0.1"
description = "Echobox ML backend: GECO2 exemplar detector inference service"
requires-python = ">=3.11"
license = {text = "Apache-2.0"}
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.30",
    "pydantic>=2.7",
    "pydantic-settings>=2.3",
    "structlog>=24.1",
    "pillow>=10.3",
]

[project.scripts]
echobox-ml = "echobox_ml.main:run"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/echobox_ml"]
```

(`torch`, `sam2`, `geco2_vendor` deps are added in Plan 3 when we wire actual inference.)

- [ ] **Step 4: Create packages/ml_backend/src/echobox_ml/__init__.py**

```python
"""Echobox ML backend package."""

__version__ = "0.0.1"
```

- [ ] **Step 5: Create empty tests/__init__.py**

```python
```

- [ ] **Step 6: Sync and run test**

Run: `uv sync --dev && uv run pytest packages/ml_backend/tests/test_import.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/ml_backend/ uv.lock
git commit -m "feat(ml_backend): scaffold echobox-ml package with import test"
```

---

## Task 4: Scaffold mcp_server package skeleton

**Files:**
- Create: `packages/mcp_server/pyproject.toml`
- Create: `packages/mcp_server/src/echobox_mcp/__init__.py`
- Create: `packages/mcp_server/tests/__init__.py`
- Create: `packages/mcp_server/tests/test_import.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/mcp_server/tests/test_import.py
def test_can_import_echobox_mcp() -> None:
    import echobox_mcp

    assert echobox_mcp.__version__ == "0.0.1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/mcp_server/tests/test_import.py -v`
Expected: FAIL.

- [ ] **Step 3: Create packages/mcp_server/pyproject.toml**

```toml
[project]
name = "echobox-mcp"
version = "0.0.1"
description = "Echobox MCP server: exposes annotation tools to external agents"
requires-python = ">=3.11"
license = {text = "Apache-2.0"}
dependencies = [
    "mcp>=1.0",
    "pydantic>=2.7",
    "pydantic-settings>=2.3",
    "httpx>=0.27",
    "structlog>=24.1",
]

[project.scripts]
echobox-mcp = "echobox_mcp.server:run"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/echobox_mcp"]
```

- [ ] **Step 4: Create packages/mcp_server/src/echobox_mcp/__init__.py**

```python
"""Echobox MCP server package."""

__version__ = "0.0.1"
```

- [ ] **Step 5: Create empty tests/__init__.py**

```python
```

- [ ] **Step 6: Sync and run test**

Run: `uv sync --dev && uv run pytest packages/mcp_server/tests/test_import.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/mcp_server/ uv.lock
git commit -m "feat(mcp_server): scaffold echobox-mcp package with import test"
```

---

## Task 5: app config (AppSettings)

**Files:**
- Create: `packages/app/src/echobox_app/config.py`
- Create: `packages/app/tests/test_config.py`
- Create: `.env.example`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_config.py
import pytest
from pydantic import SecretStr

from echobox_app.config import AppSettings


def test_settings_load_required_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "sk-test-123")

    settings = AppSettings(_env_file=None)

    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.db_url == "sqlite:///.data/projects.db"
    assert settings.llm_model == "qwen-plus"
    assert isinstance(settings.llm_api_key, SecretStr)
    assert settings.llm_api_key.get_secret_value() == "sk-test-123"


def test_settings_missing_api_key_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ECHOBOX_APP_LLM_API_KEY", raising=False)

    with pytest.raises(ValueError):
        AppSettings(_env_file=None)


def test_settings_overrides_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "sk-x")
    monkeypatch.setenv("ECHOBOX_APP_PORT", "9000")
    monkeypatch.setenv("ECHOBOX_APP_LLM_MODEL", "qwen-max")

    settings = AppSettings(_env_file=None)

    assert settings.port == 9000
    assert settings.llm_model == "qwen-max"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_config.py -v`
Expected: FAIL with `ImportError: cannot import name 'AppSettings'`.

- [ ] **Step 3: Implement config.py**

```python
# packages/app/src/echobox_app/config.py
"""Application configuration loaded from environment / .env file."""
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ECHOBOX_APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 8000

    db_url: str = "sqlite:///.data/projects.db"
    data_dir: Path = Path(".data")

    ml_backend_url: str = "http://localhost:9090"
    ml_backend_timeout_s: float = 30.0

    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_api_key: SecretStr
    llm_model: str = "qwen-plus"
    llm_timeout_s: float = 60.0

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "pretty"] = "pretty"
```

- [ ] **Step 4: Create .env.example at repo root**

```
# Required
ECHOBOX_APP_LLM_API_KEY=sk-your-dashscope-key

# Optional overrides (defaults shown)
# ECHOBOX_APP_HOST=127.0.0.1
# ECHOBOX_APP_PORT=8000
# ECHOBOX_APP_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# ECHOBOX_APP_LLM_MODEL=qwen-plus
# ECHOBOX_APP_DB_URL=sqlite:///.data/projects.db
# ECHOBOX_APP_LOG_LEVEL=INFO

# ml_backend
# ECHOBOX_ML_HOST=127.0.0.1
# ECHOBOX_ML_PORT=9090
# ECHOBOX_ML_GECO2_WEIGHTS=./.data/weights/geco2.pth
# ECHOBOX_ML_DEVICE=auto

# mcp_server
# ECHOBOX_MCP_APP_URL=http://localhost:8000
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_config.py -v`
Expected: PASS (3 tests).

- [ ] **Step 6: Commit**

```bash
git add packages/app/src/echobox_app/config.py packages/app/tests/test_config.py .env.example
git commit -m "feat(app): add AppSettings config with env loading + .env.example"
```

---

## Task 6: ml_backend config (MLSettings)

**Files:**
- Create: `packages/ml_backend/src/echobox_ml/config.py`
- Create: `packages/ml_backend/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/ml_backend/tests/test_config.py
import pytest

from echobox_ml.config import MLSettings


def test_ml_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ECHOBOX_ML_GECO2_WEIGHTS", raising=False)

    settings = MLSettings(_env_file=None)

    assert settings.host == "127.0.0.1"
    assert settings.port == 9090
    assert settings.device == "auto"
    assert settings.geco2_weights is None  # Plan 3 will require it
    assert settings.max_predictions_default == 200
    assert settings.score_threshold_default == 0.25


def test_ml_settings_device_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ECHOBOX_ML_DEVICE", "cpu")

    settings = MLSettings(_env_file=None)

    assert settings.device == "cpu"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/ml_backend/tests/test_config.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement config.py**

```python
# packages/ml_backend/src/echobox_ml/config.py
"""ML backend configuration."""
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class MLSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ECHOBOX_ML_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 9090

    device: Literal["auto", "cuda", "mps", "cpu"] = "auto"
    geco2_weights: Path | None = None  # required when actually loading model in Plan 3

    max_predictions_default: int = 200
    score_threshold_default: float = 0.25
    inference_timeout_s: float = 30.0

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "pretty"] = "pretty"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/ml_backend/tests/test_config.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/ml_backend/src/echobox_ml/config.py packages/ml_backend/tests/test_config.py
git commit -m "feat(ml_backend): add MLSettings config"
```

---

## Task 7: mcp_server config (MCPSettings)

**Files:**
- Create: `packages/mcp_server/src/echobox_mcp/config.py`
- Create: `packages/mcp_server/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/mcp_server/tests/test_config.py
from echobox_mcp.config import MCPSettings


def test_mcp_settings_defaults() -> None:
    settings = MCPSettings(_env_file=None)

    assert settings.app_url == "http://localhost:8000"
    assert settings.app_request_timeout_s == 60.0
    assert settings.transport == "stdio"
    assert settings.sse_port == 9100
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/mcp_server/tests/test_config.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement config.py**

```python
# packages/mcp_server/src/echobox_mcp/config.py
"""MCP server configuration."""
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ECHOBOX_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_url: str = "http://localhost:8000"
    app_request_timeout_s: float = 60.0

    transport: Literal["stdio", "sse"] = "stdio"
    sse_port: int = 9100

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "pretty"] = "pretty"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest packages/mcp_server/tests/test_config.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/mcp_server/src/echobox_mcp/config.py packages/mcp_server/tests/test_config.py
git commit -m "feat(mcp_server): add MCPSettings config"
```

---

## Task 8: app errors module (typed exceptions)

**Files:**
- Create: `packages/app/src/echobox_app/errors.py`
- Create: `packages/app/tests/test_errors.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_errors.py
import pytest

from echobox_app.errors import (
    ArisError,
    LLMUnavailable,
    MLBackendUnavailable,
    ProjectNotFound,
    ValidationError,
)


def test_base_error_has_code_and_status() -> None:
    err = ArisError("something broke")

    assert err.code == "internal_error"
    assert err.http_status == 500
    assert str(err) == "something broke"


def test_project_not_found_404() -> None:
    err = ProjectNotFound("project 7 missing")

    assert err.code == "project_not_found"
    assert err.http_status == 404


def test_ml_backend_unavailable_503() -> None:
    err = MLBackendUnavailable("ml_backend down")

    assert err.code == "ml_backend_unavailable"
    assert err.http_status == 503


def test_llm_unavailable_503() -> None:
    err = LLMUnavailable("dashscope timed out")

    assert err.code == "llm_unavailable"
    assert err.http_status == 503


def test_validation_error_400() -> None:
    err = ValidationError("bad bbox")

    assert err.code == "validation_failed"
    assert err.http_status == 400


def test_can_attach_detail() -> None:
    err = ProjectNotFound("not found", detail={"project_id": 99})

    assert err.detail == {"project_id": 99}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_errors.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement errors.py**

```python
# packages/app/src/echobox_app/errors.py
"""Typed exceptions for the app domain.

Boundary handlers (FastAPI exception handlers, LangGraph tool wrappers)
convert these to user-facing responses.
"""
from typing import Any


class ArisError(Exception):
    code: str = "internal_error"
    http_status: int = 500

    def __init__(self, message: str = "", *, detail: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "detail": self.detail,
            }
        }


class ValidationError(ArisError):
    code = "validation_failed"
    http_status = 400


class ProjectNotFound(ArisError):
    code = "project_not_found"
    http_status = 404


class ImageNotFound(ArisError):
    code = "image_not_found"
    http_status = 404


class AnnotationNotFound(ArisError):
    code = "annotation_not_found"
    http_status = 404


class LabelConflict(ArisError):
    code = "label_conflict"
    http_status = 409


class VersionConflict(ArisError):
    code = "version_conflict"
    http_status = 409


class MLBackendUnavailable(ArisError):
    code = "ml_backend_unavailable"
    http_status = 503


class LLMUnavailable(ArisError):
    code = "llm_unavailable"
    http_status = 503
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_errors.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/errors.py packages/app/tests/test_errors.py
git commit -m "feat(app): add typed ArisError hierarchy with code + http_status"
```

---

## Task 9: app DB models (6 SQLAlchemy tables)

**Files:**
- Create: `packages/app/src/echobox_app/db/__init__.py`
- Create: `packages/app/src/echobox_app/db/models.py`
- Create: `packages/app/src/echobox_app/db/session.py`
- Create: `packages/app/tests/test_db_models.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_db_models.py
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from echobox_app.db.models import (
    Annotation,
    Base,
    ChatMessage,
    Image,
    Label,
    PredictionRun,
    Project,
)


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_create_project(session: Session) -> None:
    p = Project(
        name="test-proj",
        workspace_path=".data/projects/1",
        source_folder="/orig",
        status="draft",
    )
    session.add(p)
    session.commit()

    assert p.id is not None
    assert p.train_ratio == 0.7
    assert p.val_ratio == 0.15
    assert p.test_ratio == 0.15
    assert p.split_seed == 42


def test_image_belongs_to_project(session: Session) -> None:
    p = Project(name="x", workspace_path="x", source_folder="x", status="draft")
    session.add(p)
    session.flush()
    img = Image(
        project_id=p.id,
        filename="00001.jpg",
        abs_path="/abs/00001.jpg",
        width=640,
        height=480,
        split="train",
        index_in_project=0,
        source_path="/orig/img1.jpg",
    )
    session.add(img)
    session.commit()

    assert img.project_id == p.id
    assert img.project.name == "x"
    assert p.images[0].filename == "00001.jpg"


def test_label_unique_per_project(session: Session) -> None:
    from sqlalchemy.exc import IntegrityError

    p = Project(name="x", workspace_path="x", source_folder="x", status="draft")
    session.add(p)
    session.flush()
    session.add(Label(project_id=p.id, name="crack", color="#e63946"))
    session.commit()

    session.add(Label(project_id=p.id, name="crack", color="#000000"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_annotation_with_label(session: Session) -> None:
    p = Project(name="x", workspace_path="x", source_folder="x", status="draft")
    session.add(p)
    session.flush()
    img = Image(
        project_id=p.id, filename="00001.jpg", abs_path="/x", width=10, height=10,
        split="train", index_in_project=0, source_path="/orig",
    )
    label = Label(project_id=p.id, name="crack", color="#000")
    session.add_all([img, label])
    session.flush()
    ann = Annotation(
        image_id=img.id, label_id=label.id,
        x1=10, y1=20, x2=30, y2=40,
        source="user", version=1,
    )
    session.add(ann)
    session.commit()

    assert ann.id is not None
    assert ann.score is None
    assert ann.image.filename == "00001.jpg"
    assert ann.label.name == "crack"


def test_chat_message(session: Session) -> None:
    p = Project(name="x", workspace_path="x", source_folder="x", status="draft")
    session.add(p)
    session.flush()
    msg = ChatMessage(project_id=p.id, role="user", content="hello")
    session.add(msg)
    session.commit()

    assert msg.id is not None


def test_prediction_run(session: Session) -> None:
    p = Project(name="x", workspace_path="x", source_folder="x", status="draft")
    session.add(p)
    session.flush()
    img = Image(
        project_id=p.id, filename="00001.jpg", abs_path="/x", width=10, height=10,
        split="train", index_in_project=0, source_path="/orig",
    )
    label = Label(project_id=p.id, name="crack", color="#000")
    session.add_all([img, label])
    session.flush()
    run = PredictionRun(
        project_id=p.id, image_id=img.id, label_id=label.id,
        exemplar_x1=1, exemplar_y1=2, exemplar_x2=3, exemplar_y2=4,
        n_predictions=5, elapsed_ms=123,
    )
    session.add(run)
    session.commit()

    assert run.id is not None
    assert run.error is None


def test_cascade_delete_project(session: Session) -> None:
    p = Project(name="x", workspace_path="x", source_folder="x", status="draft")
    session.add(p)
    session.flush()
    img = Image(
        project_id=p.id, filename="00001.jpg", abs_path="/x", width=10, height=10,
        split="train", index_in_project=0, source_path="/orig",
    )
    session.add(img)
    session.commit()
    session.delete(p)
    session.commit()

    assert session.query(Image).count() == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_db_models.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Create db/__init__.py**

```python
# packages/app/src/echobox_app/db/__init__.py
"""Database layer: SQLAlchemy models, session factory, migrations."""
```

- [ ] **Step 4: Implement db/models.py**

```python
# packages/app/src/echobox_app/db/models.py
"""SQLAlchemy 2.0 ORM models for all 6 tables (per spec section 6.2)."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


ProjectStatus = Literal["draft", "ready", "annotating", "exported"]
ExportFormat = Literal["coco", "yolo", "voc", "ls_json"]
SplitName = Literal["train", "val", "test"]
AnnotationSource = Literal["user", "geco2_pending", "geco2_accepted", "user_edited"]
ChatRole = Literal["user", "assistant", "tool", "system"]


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    workspace_path: Mapped[str] = mapped_column(String, nullable=False)
    source_folder: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(String, nullable=False)
    export_format: Mapped[ExportFormat | None] = mapped_column(String, nullable=True)
    train_ratio: Mapped[float] = mapped_column(default=0.7)
    val_ratio: Mapped[float] = mapped_column(default=0.15)
    test_ratio: Mapped[float] = mapped_column(default=0.15)
    split_seed: Mapped[int] = mapped_column(Integer, default=42)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    images: Mapped[list[Image]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    labels: Mapped[list[Label]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','ready','annotating','exported')",
            name="ck_project_status",
        ),
    )


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String, nullable=False)
    abs_path: Mapped[str] = mapped_column(String, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    split: Mapped[SplitName] = mapped_column(String, nullable=False)
    index_in_project: Mapped[int] = mapped_column(Integer, nullable=False)
    source_path: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="images")
    annotations: Mapped[list[Annotation]] = relationship(
        back_populates="image", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("split IN ('train','val','test')", name="ck_image_split"),
        Index("ix_image_project_index", "project_id", "index_in_project"),
        Index("ix_image_project_split", "project_id", "split"),
    )


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    color: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="labels")
    annotations: Mapped[list[Annotation]] = relationship(back_populates="label")

    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_label_project_name"),)


class Annotation(Base):
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image_id: Mapped[int] = mapped_column(
        ForeignKey("images.id", ondelete="CASCADE"), nullable=False
    )
    label_id: Mapped[int] = mapped_column(
        ForeignKey("labels.id", ondelete="RESTRICT"), nullable=False
    )
    x1: Mapped[int] = mapped_column(Integer, nullable=False)
    y1: Mapped[int] = mapped_column(Integer, nullable=False)
    x2: Mapped[int] = mapped_column(Integer, nullable=False)
    y2: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float | None] = mapped_column(nullable=True)
    source: Mapped[AnnotationSource] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    image: Mapped[Image] = relationship(back_populates="annotations")
    label: Mapped[Label] = relationship(back_populates="annotations")

    __table_args__ = (
        CheckConstraint(
            "source IN ('user','geco2_pending','geco2_accepted','user_edited')",
            name="ck_annotation_source",
        ),
        Index("ix_annotation_image", "image_id"),
        Index("ix_annotation_label", "label_id"),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[ChatRole] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    tool_call_id: Mapped[str | None] = mapped_column(String, nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="chat_messages")

    __table_args__ = (
        CheckConstraint(
            "role IN ('user','assistant','tool','system')",
            name="ck_chat_role",
        ),
        Index("ix_chat_project_created", "project_id", "created_at"),
    )


class PredictionRun(Base):
    __tablename__ = "prediction_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    image_id: Mapped[int] = mapped_column(
        ForeignKey("images.id", ondelete="CASCADE"), nullable=False
    )
    label_id: Mapped[int] = mapped_column(
        ForeignKey("labels.id", ondelete="CASCADE"), nullable=False
    )
    exemplar_x1: Mapped[int] = mapped_column(Integer, nullable=False)
    exemplar_y1: Mapped[int] = mapped_column(Integer, nullable=False)
    exemplar_x2: Mapped[int] = mapped_column(Integer, nullable=False)
    exemplar_y2: Mapped[int] = mapped_column(Integer, nullable=False)
    n_predictions: Mapped[int] = mapped_column(Integer, nullable=False)
    elapsed_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_pred_project_created", "project_id", "created_at"),
    )
```

- [ ] **Step 5: Implement db/session.py**

```python
# packages/app/src/echobox_app/db/session.py
"""SQLAlchemy engine + session factory."""
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def make_engine(db_url: str) -> Engine:
    engine = create_engine(db_url, echo=False, future=True)
    if db_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _enable_fk(dbapi_conn, _conn_record):  # type: ignore[no-untyped-def]
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def get_session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    s = session_factory()
    try:
        yield s
    finally:
        s.close()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_db_models.py -v`
Expected: PASS (7 tests).

- [ ] **Step 7: Commit**

```bash
git add packages/app/src/echobox_app/db/ packages/app/tests/test_db_models.py
git commit -m "feat(app): add SQLAlchemy models for 6 tables + session factory"
```

---

## Task 10: Alembic init + first migration

**Files:**
- Create: `packages/app/alembic.ini`
- Create: `packages/app/src/echobox_app/db/migrations/env.py`
- Create: `packages/app/src/echobox_app/db/migrations/script.py.mako`
- Create: `packages/app/src/echobox_app/db/migrations/versions/0001_initial_schema.py`
- Create: `packages/app/tests/test_db_migrations.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_db_migrations.py
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def tmp_db(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path}/test.db"


def test_migration_upgrade_creates_all_tables(tmp_db: str, tmp_path: Path) -> None:
    pkg_dir = Path(__file__).parents[1]  # packages/app/
    env = {"ECHOBOX_APP_DB_URL": tmp_db, "ECHOBOX_APP_LLM_API_KEY": "stub", "PATH": ""}
    import os
    env["PATH"] = os.environ.get("PATH", "")
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=pkg_dir,
        env={**os.environ, **env},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"alembic stderr: {result.stderr}"

    import sqlite3
    db_path = tmp_db.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {row[0] for row in cur.fetchall()}
    conn.close()

    expected = {
        "alembic_version",
        "annotations",
        "chat_messages",
        "images",
        "labels",
        "prediction_runs",
        "projects",
    }
    assert expected.issubset(tables), f"missing tables: {expected - tables}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/app/tests/test_db_migrations.py -v`
Expected: FAIL (alembic not configured).

- [ ] **Step 3: Add alembic to app dependencies (already done in Task 2)**

Confirm `packages/app/pyproject.toml` already has `alembic>=1.13` in dependencies. If yes, skip. If not, add.

- [ ] **Step 4: Create packages/app/alembic.ini**

```ini
[alembic]
script_location = src/echobox_app/db/migrations
prepend_sys_path = src
version_path_separator = os
sqlalchemy.url = sqlite:///.data/projects.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 5: Create migrations/env.py**

```python
# packages/app/src/echobox_app/db/migrations/env.py
"""Alembic environment: reads DB URL from ECHOBOX_APP_DB_URL env var."""
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from echobox_app.db.models import Base

config = context.config
db_url = os.environ.get("ECHOBOX_APP_DB_URL", config.get_main_option("sqlalchemy.url"))
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite-friendly ALTER
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 6: Create migrations/script.py.mako**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 7: Generate the initial migration via autogenerate**

Run from repo root:
```bash
mkdir -p packages/app/src/echobox_app/db/migrations/versions
ECHOBOX_APP_LLM_API_KEY=stub ECHOBOX_APP_DB_URL="sqlite:///.data/.alembic_init.db" \
  uv run --directory packages/app alembic revision --autogenerate -m "initial schema"
```
Expected: creates `packages/app/src/echobox_app/db/migrations/versions/<hash>_initial_schema.py`. Rename it to `0001_initial_schema.py` and update the `revision` field inside the file to `"0001"` and `down_revision` to `None`.

- [ ] **Step 8: Verify the generated migration contains all 6 tables**

Run: `grep -E "create_table" packages/app/src/echobox_app/db/migrations/versions/0001_initial_schema.py | sort`
Expected: 6 lines containing `create_table('annotations'`, `create_table('chat_messages'`, `create_table('images'`, `create_table('labels'`, `create_table('prediction_runs'`, `create_table('projects'`. If any missing, regenerate.

Then delete the temp init DB: `rm -f .data/.alembic_init.db`.

- [ ] **Step 9: Run migration test**

Run: `uv run pytest packages/app/tests/test_db_migrations.py -v`
Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add packages/app/alembic.ini packages/app/src/echobox_app/db/migrations/ \
        packages/app/tests/test_db_migrations.py
git commit -m "feat(app): add Alembic with initial schema migration for all 6 tables"
```

---

## Task 11: app structlog logging setup

**Files:**
- Create: `packages/app/src/echobox_app/logging.py`
- Create: `packages/app/tests/test_logging.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_logging.py
import json
import logging

import structlog

from echobox_app.logging import configure_logging


def test_configure_pretty_does_not_raise() -> None:
    configure_logging(level="INFO", fmt="pretty")
    log = structlog.get_logger("test")
    log.info("hello", foo="bar")  # should not raise


def test_configure_json_emits_json(capsys) -> None:  # type: ignore[no-untyped-def]
    configure_logging(level="DEBUG", fmt="json")
    log = structlog.get_logger("test")
    log.info("hello", foo="bar")
    captured = capsys.readouterr()
    line = captured.out.strip().splitlines()[-1]
    payload = json.loads(line)
    assert payload["event"] == "hello"
    assert payload["foo"] == "bar"
    assert payload["level"] == "info"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_logging.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement logging.py**

```python
# packages/app/src/echobox_app/logging.py
"""structlog configuration for the app."""
import logging
import sys
from typing import Literal

import structlog


def configure_logging(level: str = "INFO", fmt: Literal["json", "pretty"] = "pretty") -> None:
    """Configure structlog. Idempotent — safe to call multiple times."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
        force=True,
    )

    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if fmt == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper())),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_logging.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/app/src/echobox_app/logging.py packages/app/tests/test_logging.py
git commit -m "feat(app): add structlog configuration with pretty/json formats"
```

---

## Task 12: app FastAPI main with /healthz

**Files:**
- Create: `packages/app/src/echobox_app/main.py`
- Create: `packages/app/tests/test_healthz.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/app/tests/test_healthz.py
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    from echobox_app.main import create_app

    return TestClient(create_app())


def test_healthz_returns_200_with_version(client: TestClient) -> None:
    resp = client.get("/healthz")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "echobox-app"
    assert body["version"] == "0.0.1"


def test_healthz_includes_db_check(client: TestClient) -> None:
    resp = client.get("/healthz")
    body = resp.json()

    assert "db" in body
    assert body["db"] in {"ok", "unreachable"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/app/tests/test_healthz.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement main.py**

```python
# packages/app/src/echobox_app/main.py
"""FastAPI app entry point."""
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from echobox_app import __version__
from echobox_app.config import AppSettings
from echobox_app.db.session import make_engine, make_session_factory
from echobox_app.errors import ArisError
from echobox_app.logging import configure_logging


def create_app(settings: AppSettings | None = None) -> FastAPI:
    settings = settings or AppSettings()
    configure_logging(level=settings.log_level, fmt=settings.log_format)

    app = FastAPI(title="echobox-app", version=__version__)
    engine = make_engine(settings.db_url)
    session_factory = make_session_factory(engine)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory

    @app.exception_handler(ArisError)
    async def _aris_error_handler(request: Any, exc: ArisError) -> JSONResponse:  # noqa: ARG001
        return JSONResponse(status_code=exc.http_status, content=exc.to_dict())

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        db_status = "ok"
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception:
            db_status = "unreachable"
        return {
            "status": "ok",
            "service": "echobox-app",
            "version": __version__,
            "db": db_status,
        }

    return app


def run() -> None:
    """Entry point for `echobox-app` console script."""
    import uvicorn

    settings = AppSettings()
    uvicorn.run(
        "echobox_app.main:create_app",
        host=settings.host,
        port=settings.port,
        factory=True,
        reload=False,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/app/tests/test_healthz.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Manual smoke test**

Run (background): `ECHOBOX_APP_LLM_API_KEY=stub uv run uvicorn echobox_app.main:create_app --factory --port 8000 &`
Then: `curl -s http://localhost:8000/healthz | python -m json.tool`
Expected: JSON with `"status": "ok"`, `"version": "0.0.1"`, `"db": "ok"` (or `"unreachable"` if no migration run yet — both acceptable).
Cleanup: `kill %1`.

- [ ] **Step 6: Commit**

```bash
git add packages/app/src/echobox_app/main.py packages/app/tests/test_healthz.py
git commit -m "feat(app): add FastAPI app with /healthz + global error handler"
```

---

## Task 13: ml_backend FastAPI main with /healthz + GECO2 stub

**Files:**
- Create: `packages/ml_backend/src/echobox_ml/runner.py`
- Create: `packages/ml_backend/src/echobox_ml/main.py`
- Create: `packages/ml_backend/tests/test_healthz.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/ml_backend/tests/test_healthz.py
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    from echobox_ml.main import create_app

    return TestClient(create_app())


def test_healthz_returns_200(client: TestClient) -> None:
    resp = client.get("/healthz")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "echobox-ml"
    assert body["version"] == "0.0.1"
    assert body["model_loaded"] is False  # Plan 1 uses stub; Plan 3 wires real GECO2
    assert body["device"] in {"auto", "cuda", "mps", "cpu"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/ml_backend/tests/test_healthz.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement runner.py (stub)**

```python
# packages/ml_backend/src/echobox_ml/runner.py
"""GECO2 model runner. v1 stub — real loading wired in Plan 3.

Plan 3 will replace `Geco2RunnerStub` with `Geco2Runner` that:
- Imports vendored GECO2 from `geco2_vendor/`
- Loads SAM2 weights from settings.geco2_weights
- Implements `predict_similar(image_path, exemplar_bbox, ...)`
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Prediction:
    bbox: tuple[int, int, int, int]
    score: float


class Geco2RunnerStub:
    """Stub that reports model_loaded=False. Real impl in Plan 3."""

    def __init__(self, weights_path: Path | None = None, device: str = "auto") -> None:
        self.weights_path = weights_path
        self.device = device
        self.is_loaded = False

    def load(self) -> None:
        # Plan 3 wires real loading.
        self.is_loaded = False

    def predict_similar(
        self,
        image_path: Path,  # noqa: ARG002
        exemplar_bbox: tuple[int, int, int, int],  # noqa: ARG002
        max_predictions: int = 200,  # noqa: ARG002
        score_threshold: float = 0.25,  # noqa: ARG002
    ) -> list[Prediction]:
        raise NotImplementedError("GECO2 runner is a stub in Plan 1; Plan 3 implements this.")
```

- [ ] **Step 4: Implement main.py**

```python
# packages/ml_backend/src/echobox_ml/main.py
"""FastAPI app entry point for ml_backend."""
from typing import Any

from fastapi import FastAPI

from echobox_ml import __version__
from echobox_ml.config import MLSettings
from echobox_ml.runner import Geco2RunnerStub


def create_app(settings: MLSettings | None = None) -> FastAPI:
    settings = settings or MLSettings()
    app = FastAPI(title="echobox-ml", version=__version__)
    runner = Geco2RunnerStub(weights_path=settings.geco2_weights, device=settings.device)
    app.state.settings = settings
    app.state.runner = runner

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "echobox-ml",
            "version": __version__,
            "model_loaded": runner.is_loaded,
            "device": runner.device,
        }

    return app


def run() -> None:
    """Entry point for `echobox-ml` console script."""
    import uvicorn

    settings = MLSettings()
    uvicorn.run(
        "echobox_ml.main:create_app",
        host=settings.host,
        port=settings.port,
        factory=True,
        reload=False,
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest packages/ml_backend/tests/test_healthz.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/ml_backend/src/echobox_ml/runner.py packages/ml_backend/src/echobox_ml/main.py \
        packages/ml_backend/tests/test_healthz.py
git commit -m "feat(ml_backend): add FastAPI app with /healthz and GECO2 runner stub"
```

---

## Task 14: mcp_server stub with empty tool list

**Files:**
- Create: `packages/mcp_server/src/echobox_mcp/client.py`
- Create: `packages/mcp_server/src/echobox_mcp/server.py`
- Create: `packages/mcp_server/tests/test_server_stub.py`

- [ ] **Step 1: Write the failing test**

```python
# packages/mcp_server/tests/test_server_stub.py
import pytest

from echobox_mcp.server import build_server


@pytest.mark.asyncio
async def test_server_lists_no_tools_yet() -> None:
    server = build_server()
    # The MCP Server's internal handler is registered via decorators;
    # for v1 stub we just verify the server constructs and exposes its name.
    assert server.name == "echobox"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/mcp_server/tests/test_server_stub.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement client.py (HTTP client stub)**

```python
# packages/mcp_server/src/echobox_mcp/client.py
"""HTTP client wrapping the app's REST API. Plan 4 fills in concrete methods."""
from typing import Any

import httpx


class AppClient:
    def __init__(self, base_url: str, timeout_s: float = 60.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout_s)

    async def healthz(self) -> dict[str, Any]:
        resp = await self._client.get("/healthz")
        resp.raise_for_status()
        return resp.json()

    async def aclose(self) -> None:
        await self._client.aclose()
```

- [ ] **Step 4: Implement server.py**

```python
# packages/mcp_server/src/echobox_mcp/server.py
"""MCP server stub. Plan 4 registers the 3 real tools."""
from typing import Any

from mcp.server import Server
from mcp.types import Tool

from echobox_mcp.config import MCPSettings


def build_server(settings: MCPSettings | None = None) -> Server:
    settings = settings or MCPSettings()
    server = Server("echobox")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        # Plan 4 registers: start_annotation_project, search_annotations, export_dataset
        return []

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[Any]:  # noqa: ARG001
        raise ValueError(f"unknown tool: {name}")

    return server


def run() -> None:
    """Entry point for `echobox-mcp` console script."""
    import asyncio

    from mcp.server.stdio import stdio_server

    settings = MCPSettings()
    server = build_server(settings)

    async def _serve() -> None:
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    asyncio.run(_serve())
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest packages/mcp_server/tests/test_server_stub.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/mcp_server/src/echobox_mcp/client.py packages/mcp_server/src/echobox_mcp/server.py \
        packages/mcp_server/tests/test_server_stub.py
git commit -m "feat(mcp_server): add MCP server stub with empty tool list + AppClient skeleton"
```

---

## Task 15: Frontend scaffold (Vite + React + TypeScript)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/.gitignore`

- [ ] **Step 1: Create frontend/ directory and package.json**

```json
{
  "name": "echobox-frontend",
  "private": true,
  "version": "0.0.1",
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1 --port 5173",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\"",
    "preview": "vite preview --port 5173"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@typescript-eslint/eslint-plugin": "^7.13.0",
    "@typescript-eslint/parser": "^7.13.0",
    "@vitejs/plugin-react": "^4.3.1",
    "eslint": "^8.57.0",
    "prettier": "^3.3.2",
    "typescript": "^5.4.5",
    "vite": "^5.3.0"
  }
}
```

- [ ] **Step 2: Create frontend/vite.config.ts**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "127.0.0.1",
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
```

- [ ] **Step 3: Create frontend/tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 4: Create frontend/tsconfig.node.json**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 5: Create frontend/index.html**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Echobox</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Create frontend/src/main.tsx**

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 7: Create frontend/src/App.tsx (placeholder)**

```tsx
export default function App(): JSX.Element {
  return (
    <div style={{ fontFamily: "system-ui", padding: 24 }}>
      <h1>Echobox</h1>
      <p>多模态智能标注 Agent 平台 — Pre-alpha</p>
      <p>
        Plan 1 (Foundation) 完成 — Setup / Annotate 页面在 Plan 2 / Plan 3 实现。
      </p>
    </div>
  );
}
```

- [ ] **Step 8: Create frontend/.gitignore**

```
node_modules
dist
.vite
*.log
```

- [ ] **Step 9: Install dependencies**

Run from repo root: `cd frontend && npm install`
Expected: `added N packages` with no errors.

- [ ] **Step 10: Verify dev server starts**

Run (background): `cd frontend && npm run dev &`
Wait 3 seconds, then: `curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5173/`
Expected: `200`.
Cleanup: `kill %1`.

- [ ] **Step 11: Verify build works**

Run: `cd frontend && npm run build`
Expected: `dist/` created without errors.

- [ ] **Step 12: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vite.config.ts \
        frontend/tsconfig.json frontend/tsconfig.node.json frontend/index.html \
        frontend/src/ frontend/.gitignore
git commit -m "feat(frontend): scaffold Vite + React + TypeScript with placeholder App"
```

---

## Task 16: Procfile + Makefile + setup script

**Files:**
- Create: `Procfile`
- Create: `Makefile`
- Create: `scripts/setup.sh`
- Create: `scripts/verify_healthz.sh`

- [ ] **Step 1: Create Procfile**

```
app: ECHOBOX_APP_DB_URL=sqlite:///.data/projects.db uv run --package echobox-app uvicorn echobox_app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
ml:  uv run --package echobox-ml uvicorn echobox_ml.main:create_app --factory --host 127.0.0.1 --port 9090
mcp: uv run --package echobox-mcp echobox-mcp
web: npm --prefix frontend run dev
```

- [ ] **Step 2: Create Makefile**

```makefile
.PHONY: setup dev test lint typecheck app ml mcp web db-upgrade clean help

help:
	@echo "Available targets:"
	@echo "  make setup         一次性环境初始化 (uv sync + npm install)"
	@echo "  make dev           启动全部 4 进程 (honcho)"
	@echo "  make app           单独跑 app (port 8000)"
	@echo "  make ml            单独跑 ml_backend (port 9090)"
	@echo "  make mcp           单独跑 mcp_server"
	@echo "  make web           单独跑 frontend (port 5173)"
	@echo "  make test          跑全部 pytest 测试"
	@echo "  make lint          ruff + eslint"
	@echo "  make typecheck     mypy + tsc"
	@echo "  make db-upgrade    跑 alembic upgrade head"
	@echo "  make clean         清理缓存与构建产物"

setup:
	uv sync --dev
	npm --prefix frontend install
	mkdir -p .data
	@echo ""
	@echo "Setup complete. Next steps:"
	@echo "  1. cp .env.example .env  # then fill ECHOBOX_APP_LLM_API_KEY"
	@echo "  2. make db-upgrade"
	@echo "  3. make dev"

dev:
	@if [ ! -f .env ]; then echo "ERROR: .env missing. cp .env.example .env"; exit 1; fi
	uv run honcho start

app:
	uv run --package echobox-app uvicorn echobox_app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload

ml:
	uv run --package echobox-ml uvicorn echobox_ml.main:create_app --factory --host 127.0.0.1 --port 9090

mcp:
	uv run --package echobox-mcp echobox-mcp

web:
	npm --prefix frontend run dev

test:
	uv run pytest

lint:
	uv run ruff check packages/
	npm --prefix frontend run lint

typecheck:
	uv run mypy packages/app/src packages/ml_backend/src packages/mcp_server/src
	npm --prefix frontend run build

db-upgrade:
	cd packages/app && uv run alembic upgrade head

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	find . -type d -name .mypy_cache -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +
	rm -rf frontend/dist frontend/.vite
```

- [ ] **Step 3: Create scripts/setup.sh**

```bash
#!/usr/bin/env bash
# One-time environment initialization for Echobox.
set -euo pipefail

# Check uv
if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

# Check Node
if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node not found. Install Node 20+."
  exit 1
fi

NODE_MAJOR=$(node -p 'process.versions.node.split(".")[0]')
if [ "$NODE_MAJOR" -lt 20 ]; then
  echo "ERROR: Node 20+ required (found $NODE_MAJOR)."
  exit 1
fi

echo "==> Installing Python dependencies (uv sync --dev)"
uv sync --dev

echo "==> Installing frontend dependencies (npm install)"
npm --prefix frontend install

echo "==> Creating .data/ directory"
mkdir -p .data

if [ ! -f .env ]; then
  echo "==> Copying .env.example -> .env"
  cp .env.example .env
  echo "    Edit .env to fill ECHOBOX_APP_LLM_API_KEY before running 'make dev'."
fi

echo ""
echo "Setup complete. Next steps:"
echo "  1. Edit .env and set ECHOBOX_APP_LLM_API_KEY"
echo "  2. make db-upgrade"
echo "  3. make dev"
```

- [ ] **Step 4: Create scripts/verify_healthz.sh (smoke test)**

```bash
#!/usr/bin/env bash
# Verify all backend processes respond to /healthz. Run after `make dev` is up.
set -euo pipefail

echo "==> Checking app /healthz (port 8000)"
APP=$(curl -fsS http://127.0.0.1:8000/healthz)
echo "    $APP"
echo "$APP" | grep -q '"service":"echobox-app"' || (echo "FAIL: app healthz" && exit 1)

echo "==> Checking ml_backend /healthz (port 9090)"
ML=$(curl -fsS http://127.0.0.1:9090/healthz)
echo "    $ML"
echo "$ML" | grep -q '"service":"echobox-ml"' || (echo "FAIL: ml_backend healthz" && exit 1)

echo "==> Checking frontend (port 5173)"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5173/)
echo "    HTTP $HTTP"
[ "$HTTP" = "200" ] || (echo "FAIL: frontend not responding 200" && exit 1)

echo ""
echo "All 3 web services healthy. (mcp_server uses stdio — verify separately via Claude Desktop config.)"
```

- [ ] **Step 5: Make scripts executable**

Run: `chmod +x scripts/setup.sh scripts/verify_healthz.sh`

- [ ] **Step 6: Verify make help works**

Run: `make help`
Expected: prints the list of available targets.

- [ ] **Step 7: Run the full test suite to ensure nothing is broken**

Run: `uv run pytest`
Expected: all tests pass (covers app + ml_backend + mcp_server).

- [ ] **Step 8: Commit**

```bash
git add Procfile Makefile scripts/setup.sh scripts/verify_healthz.sh
git commit -m "build: add Procfile, Makefile, setup + healthz scripts for honcho dev orchestration"
```

---

## Task 17: Pre-commit hooks + final smoke test

**Files:**
- Create: `.pre-commit-config.yaml`

- [ ] **Step 1: Create .pre-commit-config.yaml**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-merge-conflict
      - id: check-added-large-files
        args: ["--maxkb=500"]

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.10
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: prettier
        name: prettier (frontend)
        entry: bash -c 'cd frontend && npx prettier --write "$@"' --
        language: system
        files: ^frontend/.*\.(ts|tsx|css|json|md)$
        pass_filenames: true
```

- [ ] **Step 2: Install pre-commit hooks**

Run: `uv run pre-commit install`
Expected: `pre-commit installed at .git/hooks/pre-commit`.

- [ ] **Step 3: Run all hooks on all files**

Run: `uv run pre-commit run --all-files`
Expected: passes (or auto-fixes formatting; if so, re-stage and re-run until green).

- [ ] **Step 4: Run final full test suite**

Run: `make test`
Expected: all tests across app + ml_backend + mcp_server pass.

- [ ] **Step 5: Run typecheck**

Run: `make typecheck`
Expected: mypy passes for all 3 packages; tsc passes for frontend.

- [ ] **Step 6: Run db-upgrade end-to-end**

Run: `ECHOBOX_APP_LLM_API_KEY=stub make db-upgrade`
Expected: `INFO  [alembic.runtime.migration] Running upgrade  -> 0001`. File `.data/projects.db` exists.

- [ ] **Step 7: Ensure .env exists for honcho**

Run:
```bash
if [ ! -f .env ]; then cp .env.example .env; fi
grep -q "^ECHOBOX_APP_LLM_API_KEY=" .env || echo "ECHOBOX_APP_LLM_API_KEY=stub" >> .env
```
Expected: `.env` exists and contains a non-empty `ECHOBOX_APP_LLM_API_KEY`. Honcho will load this when `make dev` runs.

- [ ] **Step 8: End-to-end smoke (honcho dev)**

Run terminal A: `make dev`
Wait ~5 seconds, then in terminal B: `bash scripts/verify_healthz.sh`
Expected: all 3 services report healthy.
Cleanup: Ctrl-C in terminal A.

- [ ] **Step 9: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "chore: add pre-commit hooks (ruff, prettier, file checks)"
```

- [ ] **Step 10: Final tag**

```bash
git tag -a v0.0.1-foundation -m "Plan 1 complete: 4-process scaffold with /healthz + DB schema"
git log --oneline | head -20
```
Expected: see ~17 commits from Plan 1, last tagged `v0.0.1-foundation`.

---

## Done Criteria

After all 17 tasks:

- [x] `uv sync --dev` installs all 3 Python packages
- [x] `npm --prefix frontend install` installs frontend deps
- [x] `make db-upgrade` creates `.data/projects.db` with all 6 tables
- [x] `make dev` brings up app:8000, ml_backend:9090, mcp_server (stdio), frontend:5173
- [x] `bash scripts/verify_healthz.sh` reports all 3 web services healthy
- [x] `make test` — all pytest tests pass (~17+ tests)
- [x] `make typecheck` — mypy + tsc pass
- [x] `make lint` — ruff + eslint pass
- [x] Pre-commit hooks installed and passing on all files
- [x] Git tag `v0.0.1-foundation` exists

## What's NOT in this plan (defer to Plan 2/3/4)

- LangGraph chat agent + tools (Plan 2)
- Project / Image / Annotation REST endpoints (Plan 2 for Phase 1 surfaces, Plan 3 for Phase 2)
- Real GECO2 model loading + `/predict_similar` (Plan 3)
- Frontend Setup page (Plan 2) and Annotate page (Plan 3)
- Exporters: COCO/YOLO/VOC/ls_json (Plan 4)
- MCP server's 3 actual tools (Plan 4)
- README quick-start, demo GIF, CONTRIBUTING.md, CHANGELOG.md, CI workflows (Plan 4)

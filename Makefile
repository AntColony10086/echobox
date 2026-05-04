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

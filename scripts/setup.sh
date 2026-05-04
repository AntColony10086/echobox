#!/usr/bin/env bash
# One-time environment initialization for echobox.
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

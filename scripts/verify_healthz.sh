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

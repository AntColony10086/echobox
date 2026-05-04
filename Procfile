app: ECHOBOX_APP_DB_URL=sqlite:///.data/echobox.db uv run --package echobox-app uvicorn echobox_app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
ml:  uv run --package echobox-ml uvicorn echobox_ml.main:create_app --factory --host 127.0.0.1 --port 9090
mcp: tail -f /dev/null | uv run --package echobox-mcp echobox-mcp
web: npm --prefix frontend run dev

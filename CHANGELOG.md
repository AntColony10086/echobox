# Changelog

All notable changes are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-05-04

### Added
- 4-process scaffold (app, ml_backend, mcp_server, frontend)
- LangGraph-based conversational setup with 7 deterministic tools
- GECO2 + SAM2 integration for exemplar-based detection (placeholder; real model wiring deferred)
- React + react-konva annotation canvas
- 4 export formats (COCO, YOLO, Pascal VOC, Label Studio JSON)
- MCP server with 3 tools (start_project, search_annotations, export_dataset)
- SQLite persistence with Alembic migrations
- Honcho-based dev orchestration
- CI workflows for lint + type + test
- Bilingual documentation (English + 中文)

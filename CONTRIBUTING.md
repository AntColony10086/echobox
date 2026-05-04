# Contributing to echobox

Thanks for your interest in contributing!

## Quick links
- [Open an issue](https://github.com/AntColony10086/echobox/issues/new/choose)
- [Open a PR](https://github.com/AntColony10086/echobox/pulls)
- [Read the architecture doc](docs/architecture.md)

## Local setup

```bash
git clone --recurse-submodules https://github.com/AntColony10086/echobox
cd echobox
make setup
cp .env.example .env  # add your DashScope key
make db-upgrade
make dev
```

## Workflow

1. Fork + clone
2. Create a branch: `git checkout -b feature/short-description`
3. Make changes — follow the **TDD discipline** documented in `docs/superpowers/plans/`:
   - Write a failing test first
   - Implement minimal code to make it pass
   - Commit small, frequent
4. Run `make test && make lint && make typecheck` — must all pass
5. Push and open a PR

## Code style

- Python: `ruff format` + `ruff check`; strict mypy. Line width 100.
- TypeScript: `prettier` + `eslint`. Line width 100.
- Pre-commit hooks auto-format on commit (`pre-commit install` once).

## Architecture rules

- Don't import across packages directly. `app` ↔ `ml_backend` ↔ `mcp_server` go via HTTP.
- DB ownership lives in `app` only. The other packages are stateless.
- New tools or exporters: drop in their respective directory + register; no other files should change.

## Tests

- Place tests next to their package (`packages/<pkg>/tests/`).
- E2E tests in `tests/e2e/`. They mock LLM and ml_backend.
- Aim for 80% line coverage; 90%+ on `domain/`, `tools/`, `exporters/`.

## Asking questions

Open a [GitHub Discussion](https://github.com/AntColony10086/echobox/discussions) or an issue.

## License of contributions

By contributing, you agree your code is licensed under [Apache-2.0](LICENSE).

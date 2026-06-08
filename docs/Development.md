# Development

This page covers working on the SDK itself — setting up a development
environment, running the tests, linting, and building. The project uses
[uv](https://docs.astral.sh/uv/) for dependency management and a `src/` layout.

## Get the source

```bash
git clone https://github.com/dagsdags212/loyverse_sdk.git
cd loyverse_sdk
```

## Set up the environment

Dev dependencies live in the `[dependency-groups] dev` group and the MCP server
behind the `mcp` optional extra. Install both with `uv sync`:

```bash
uv sync --extra mcp
```

This creates a virtualenv with the runtime deps, the dev tools (pytest, respx,
coverage, anyio), and the MCP server.

## Project layout

The package lives under `src/loyverse_sdk/`:

| Module | Responsibility |
|---|---|
| `client.py` | The `LoyverseClient` and its export convenience methods |
| `endpoints/` | Endpoint classes using the mixin CRUD pattern |
| `models/` | Pydantic request/response and query models |
| `exporters/` | Flat-file (CSV / Parquet) export |
| `db/` | DuckDB export pipeline |
| `cli/` | Typer-based command-line interface |
| `mcp/` | FastMCP server with read-only tools |
| `core/` | Configuration, logging, utilities |
| `auth.py` | Token-based authentication |

See [[Home]] for the feature map and links into each area.

## Run the tests

Tests live under `tests/` and are split by marker — `unit` and `integration`:

```bash
# Run everything
uv run python -m pytest

# Unit tests only
uv run python -m pytest -m unit

# Integration tests only
uv run python -m pytest -m integration
```

Integration tests hit the live Loyverse API and require a token — set
`LOYVERSE_API_TOKEN` in your environment before running them (see
[[Configuration]]).

## Lint and format

The project uses [ruff](https://docs.astral.sh/ruff/); its configuration is in
`[tool.ruff]` in `pyproject.toml` (target `py312`, line length 88):

```bash
uvx ruff check .       # lint
uvx ruff format .      # format
```

## Build

Build the wheel and sdist with uv (the `Makefile` wraps the same command):

```bash
uv build       # or: make build
```

Artifacts land in `dist/`. Run `make clean` to remove build output.

## See also

- [[Home]] — the feature map and module overview
- [[Installation]] — installing the released package
- [[Configuration]] — the token integration tests need
- [[CLI]] — the command surface under `cli/`
- [[MCP-Server]] — the server behind the `mcp` extra

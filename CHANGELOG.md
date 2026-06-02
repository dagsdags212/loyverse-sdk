# Changelog

## [0.4.0] — 2026-05-31

### Added
- `LOYVERSE_DB_PATH` config setting (default: `loyverse.db`) for automatic database path resolution
- `loyverse init` now prompts for database path in addition to API token
- `--by-month` flag on `loyverse analytics revenue` and `loyverse_analytics_total_revenue` MCP tool

### Changed
- `--db-path`/`-d` is now optional on all `loyverse analytics` and `loyverse export` commands — falls back to `LOYVERSE_DB_PATH` config
- MCP server uses `Config` class instead of raw `os.environ` for database path

## [0.3.0] — 2026-05-31

### Added
- **CLI** — Typer-based `loyverse` command with 8 subcommands: `init`, `list`, `create`, `update`, `delete`, `get`, `endpoints`, `export`
- CLI `get` subcommand for retrieving single resource records by ID
- CLI `export` subcommand for DuckDB data warehousing export
- CLI helper modules: `_async` (client lifecycle), `_dates` (date normalization), `_display` (Rich tables), `_metadata` (dynamic resource discovery)
- Parquet binary TTY guard — warns when writing binary Parquet to terminal
- 71 new CLI tests across 12 test files

### Changed
- Refactored CLI from 914-line monolith into modular `cli/commands/` sub-package
- Dynamic resource capability discovery via mixin introspection (replaces 6 hardcoded data structures)
- Simplified async client lifecycle via shared `run_async()` utility (eliminates 4 copies of boilerplate)

### Fixed
- `PaymentTypeListReponse` → `PaymentTypeListResponse` typo in `models/receipt.py`, `models/__init__.py`, `endpoints/payment_types.py`

## [0.2.2] — 2026-05-30

### Added
- Flat-file exporter: `export_to_csv()` and `export_to_parquet()` convenience methods on `LoyverseClient`
- Exporters module with `export_csv()` and `export_parquet()` functions

## [0.2.1] — 2026-05-29

### Added
- DuckDB export pipeline for local data warehousing
- 16 typed API endpoints with full CRUD support
- Pydantic v2 models for all API responses
- Async/await interface via httpx
- Cursor-based pagination with `iter_all()` async generator

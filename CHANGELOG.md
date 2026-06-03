# Changelog

## [0.4.2] - 2026-06-03

### Added
- **Profitability analytics** (`loyverse analytics profitability`) — gross profit, margins, and COGS tracking:
  - `gross_profit` — daily revenue, cost, gross profit, and margin %
  - `profit_margins` — item-level margins sortable by gross profit, margin %, or revenue
  - `profit_by_category` — margins broken down by product category
  - `margin_trend` — daily margin % trend with period-over-period change
  - `overall_margin` — single-period overall margin % (scalar)
  - `items_without_cost` — items sold without COGS data to identify setup gaps
- **Inventory analytics** (`loyverse analytics inventory`) — turnover, stock value, and low-stock alerts:
  - `turnover` — units sold ÷ current stock with days-to-sell estimate
  - `stock_value` — per-variant stock × unit cost
  - `total_inventory_value` — total tied-up capital (scalar)
  - `stock_value_by_store` — value breakdown per store location
  - `low_stock` — items at/below threshold, respecting `variant_store.low_stock_threshold`
  - `items_never_sold` — dead stock — items on hand that haven't sold in the period
- **`fmt` parameter** on all 29 analytics methods — returns `"dataframe"` (default), `"json"`, or `"csv"` for UNIX pipeline composability
- Test fixture extended with `variants`, `inventory`, and `variant_store` tables with cost data
- 24 new tests for profitability and inventory modules

### Changed
- **CLI analytics commands reorganized** with full docstrings, example blocks, and consistent flag naming across all 8 subcommands
- New CLI flags surfaced: `--refunds` (revenue), `--dod` (time-series), `--new-vs-returning`/`--visit-distribution` (customers), `--daily` (employees)
- MCP analytics tools now pass `fmt="json"` directly to analytics methods instead of wrapping DataFrames
- `_base.py` shared layer expanded with `format` param, `_serialize()`, `_scalar_to_output()`, and `_dict_to_output()` helpers

### Fixed
- Date-boundary test failures — analytics tests used `days=30` against seed data from early May, which filtered out all records after June 3. Bumped to `days=90` across all affected tests

## [0.4.1] - 2026-06-03

### Added
- Centralized config directory at `~/.loyverse` (override with `LOYVERSE_CONFIG_DIR`):
  - API token and settings stored in `<config-dir>/.loyverse.env`
  - Exported databases stored under `<config-dir>/db/`
  - New `loyverse_sdk.core.paths` module with `config_dir`, `env_file`, `db_dir`, `resolve_db_path`, pointer-file helpers, and legacy migration
- `loyverse init` now configures the **config directory location** (default `~/.loyverse`), API token, and database name:
  - New `--config-dir`/`-c` and `--api-token`/`-t` options (alongside `--db-path`/`-d`); each skips its prompt when supplied, enabling non-interactive setup
  - A non-default config directory is recorded in a pointer file (`~/.config/loyverse/config_dir`) so later commands discover it automatically — no env var to export
- Config directory resolution order: `LOYVERSE_CONFIG_DIR` env var → pointer file → default `~/.loyverse`
- Automatic migration: a `.env` in the working directory is copied into the config dir on first run when no config exists yet
- **Incremental sync** — `loyverse export` now syncs incrementally by default, fetching only records updated since the last export. Use `--force`/`-f` for a full re-export
- MCP CRUD tools now query the local DuckDB database first when available and fresh (receipts within 2 days), falling back to the API only when the DB is missing or stale

### Changed
- `loyverse init` writes to `<config-dir>/.loyverse.env` instead of a `.env` in the current directory
- Bare database names (e.g. `mydata.duckdb`) resolve under `<config-dir>/db/`; explicit/absolute paths are used as-is
- Config is loaded from the resolved config directory's `.loyverse.env` rather than the working-directory `.env`
- **`loyverse export` now syncs incrementally by default** — use `--force`/`-f` for a full export
- `loyverse export --sync` flag removed; incremental is the default, `--force` replaces the old full-export default

### Fixed
- Timestamps from the Loyverse API (UTC) were not converted to local timezone when timezone-aware. The validator now unconditionally converts all `created_at`, `updated_at`, and `deleted_at` fields to the configured `TIMEZONE` (default `Asia/Manila`). Previously, only naive datetimes were adjusted — UTC-aware timestamps from the API passed through unchanged.

## [0.4.0] — 2026-06-02

### Added
- **MCP server** (`loyverse-mcp`) — FastMCP stdio server exposing the Loyverse SDK via the Model Context Protocol
  - 18 CRUD tools: `list_*` and `get_*` for receipts, items, customers, categories, employees, shifts, stores, payment types, inventory, and merchant
  - 12 analytics tools: daily revenue, total revenue, revenue by store/category/employee, top items, RFM analysis, top customers, unique customers, peak hours, peak days, monthly summary
  - Pydantic input models with pagination, date filtering, store/category/email filters
  - All tools read-only (`readOnlyHint=True`, `destructiveHint=False`)
  - Lifespan-managed client and analytics engine with automatic cleanup
  - Available as `mcp` optional dependency (`pip install loyverse-sdk[mcp]`)
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

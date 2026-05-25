# Loyverse Data Toolkit

## What This Is

An async Python SDK for the Loyverse POS API with local DuckDB data warehousing. Provides 14 typed endpoint wrappers (categories, customers, receipts, etc.), cursor-based pagination, and a streaming export pipeline into DuckDB for local analytics.

## Core Value

Data can be reliably pulled from the Loyverse API into local storage for analysis, with correct typing and error handling throughout.

## Requirements

### Validated

- ✓ Code cleanup complete — v1.0 (removed dead code: shift.py, schemas.py, logging.py, utils.py functions)
- ✓ Tax model fixed (duplicate name field removed, max_length=40 preserved) — v1.0
- ✓ MerchantEndpoint.retrieve() fixed (parameterless, singleton /merchant URL) — v1.0
- ✓ Exception handling tightened (13 bare except blocks replaced with specific types) — v1.0
- ✓ All 8 test file imports fixed (loyverse_api → loyverse_sdk) — v1.0
- ✓ surcharge typo fixed — v1.0
- ✓ Receipt/LineItem test payloads fixed (required fields added) — v1.0
- ✓ All 25 model tests now pass — v1.0

### Active

- [ ] **TST-01**: Fix all 8 test model imports (COMPLETED — moved to Validated)
- [ ] **TST-02**: Fix `surchage` typo → `surcharge` (COMPLETED — moved to Validated)
- [ ] **BUG-01**: Remove duplicate `name` field in Tax model (COMPLETED — moved to Validated)
- [ ] **BUG-02**: Fix `MerchantEndpoint.retrieve(id)` — (COMPLETED — moved to Validated)
- [ ] **CLN-01**: Remove orphaned `models/shift.py` (COMPLETED — moved to Validated)
- [ ] **CLN-02**: Remove dead `utils.py` functions (COMPLETED — moved to Validated)
- [ ] **CLN-03**: Remove dead `db/schemas.py` (COMPLETED — moved to Validated)
- [ ] **CLN-04**: Remove dead `core/logging.py` stub (COMPLETED — moved to Validated)
- [ ] **QLT-01**: Replace 11+ bare `except Exception:` blocks in `db/exporter.py` (COMPLETED — moved to Validated)
- [ ] **QLT-02**: Replace 2 bare `except Exception:` blocks in `client.py` (COMPLETED — moved to Validated)
- [ ] **VER-01**: All existing tests pass (COMPLETED — moved to Validated)

### Out of Scope

| Feature | Reason |
|---------|--------|
| New endpoint classes or features | Cleanup/bugfix only — no new functionality |
| New test coverage for endpoints/client/auth | Deferred — focus on fixing existing tests |
| Replace `pytz` with `zoneinfo` | Nice-to-have, not part of cleanup |
| Remove `sqlmodel` or `polars` dependencies | Risk reduction, not cleanup |
| Add retry/rate-limit logic | New feature, not bugfix |
| Replace `db/schema_builder.py` raw SQL | Refactor, not cleanup |

## Context

**Shipped v1.0 Initial Cleanup** with 106 files changed, ~11K LOC affected.
The codebase now has a clean, working state — all tests pass (25 model tests), dead code removed, exception handling tightened, and type errors fixed.

**Tech Stack:**
- Python 3.12+, httpx, Pydantic v2, DuckDB, Polars, SQLModel
- 14 endpoint classes with cursor-based pagination
- Streaming export pipeline into DuckDB

**User Feedback:** N/A — internal cleanup milestone

**Known Issues:** None

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Cleanup-first scope | Codebase map revealed concrete bugs and dead code that block reliable development | ✓ All cleanup items completed in v1.0 |
| Singleton endpoint pattern | MerchantEndpoint.retrieve() without id, using _get(self.path) directly | ✓ Works correctly for singleton /merchant resource |
| Two-tier insertion strategy (D-04) | pl.exceptions.PolarsError with duckdb.Error fallback in _batch_insert | ✓ Robust error handling for mixed DataFrame/DB operations |
| Pipeline catch-and-wrap (D-01) | ExportError catch in export loop wraps duckdb.Error before re-raise | ✓ Consistent exception hierarchy |
| Narrow rollback handler (WR-02) | connection.py transaction() rollback only catches duckdb.Error/ExportError | ✓ Non-DB exceptions now propagate correctly |

---

*Last updated: 2026-05-25 after v1.0 milestone*
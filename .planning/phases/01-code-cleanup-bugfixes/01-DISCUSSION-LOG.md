# Phase 1: Code Cleanup & Bugfixes - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-25
**Phase:** 01-code-cleanup-bugfixes
**Areas discussed:** Exception specificity, Verification strategy, Dead code import cleanup, Execution order

---

## Exception Specificity

| Option | Description | Selected |
|--------|-------------|----------|
| DuckDB + ExportError | Use `duckdb.Error` for DB ops, `ExportError` for pipeline errors | ✓ |
| Broad Exception (keep) | Keep `except Exception` for catch-and-wrap patterns | |
| httpx + duckdb + Exception | Chain catch for API, DB, then generic | |

**User's choice:** DuckDB + ExportError
**Notes:** Also chose `pl.exceptions.PolarsError` for the Polars DataFrame block (line 371) and `json.JSONDecodeError` for client.py JSON parsing.

## Verification Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Import smoke tests | `python -c "from loyverse_sdk import LoyverseClient"` + `pytest --collect-only` | ✓ |
| Try running exporter tests | Run DB tests that don't have broken imports | |
| Both | Import smoke test AND DB unit tests | |

**User's choice:** Import smoke tests

## Dead Code Import Cleanup

| Option | Description | Selected |
|--------|-------------|----------|
| Leave other imports | utils.py keeps `standardize_datetime_str`, remove dead functions only | |
| Full import audit | Check imports for files being deleted entirely | ✓ |

**User's choice:** Full import audit
**Notes:** Confirmed no imports in `__init__.py` reference the files being deleted.

## Execution Order

| Option | Description | Selected |
|--------|-------------|----------|
| Dead code → Bugs → Exceptions | Remove dead code first, fix bugs, then tighten exceptions | ✓ |
| Exceptions → Bugs → Dead code | Tighten exceptions first, then fix bugs, remove dead code last | |
| Order doesn't matter | All changes are independent | |

**User's choice:** Dead code → Bugs → Exceptions

## the agent's Discretion

- Merchant endpoint `retrieve` signature (removing `id` param) — clear-cut, no discussion needed
- Tax model duplicate `name` fix — clear-cut, no discussion needed

## Deferred Ideas

None — discussion stayed within phase scope

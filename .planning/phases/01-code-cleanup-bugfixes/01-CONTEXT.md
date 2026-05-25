# Phase 1: Code Cleanup & Bugfixes - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix code-level bugs (Tax model duplicate name, Merchant singleton retrieve), remove orphaned/dead code (shift.py, schemas.py, logging.py, dead utils.py functions), and replace bare exception blocks with specific exception handling throughout the codebase. Phase 2 handles test fixes separately.

</domain>

<decisions>
## Implementation Decisions

### Exception Specificity
- **D-01:** Use `ExportError` for pipeline-level catch-and-wrap blocks in `exporter.py` (lines 151, 271, 325) — these already re-raise as `ExportError`, making the catch type consistent with the raise type
- **D-02:** Use `duckdb.Error` for DuckDB-only operations in `exporter.py` (lines 161, 425, 460, 484, 489) — index creation, sync metadata, table count queries
- **D-03:** Use `json.JSONDecodeError` for the two JSON parse points in `client.py` (lines 130, 156) — both catch `resp.json()` failures
- **D-04:** Use `pl.exceptions.PolarsError` for the Polars DataFrame creation catch in `exporter.py` (line 371) — the DuckDB fallback at line 389 uses `duckdb.Error`
- **D-05:** Replace `raise Exception(...)` on `exporter.py` line 390 with `raise ExportError(...)` — consistent with the export pipeline's exception pattern

### Verification Strategy
- **D-06:** Use import smoke tests for verification during Phase 1: run `python -c "from loyverse_sdk import LoyverseClient"` plus `uv run pytest --collect-only` after each change
- **D-07:** This catches `ModuleNotFoundError` and `AttributeError` from removed/renamed code without requiring the test suite to pass

### Dead Code Import Cleanup
- **D-08:** `utils.py` keeps `standardize_datetime_str` (still used by `mixins.py:5`) — only remove `convert_response` and `use_model` functions
- **D-09:** Full import audit for files being deleted entirely (`shift.py`, `schemas.py`, `logging.py`) — confirmed no imports in `__init__.py` or other modules reference them, so deletion is self-contained

### Execution Order
- **D-10:** Dead code removal first, then bug fixes, then exception tightening — prevents dead code removal from interfering with other changes

### the agent's Discretion
- Exact `MerchantEndpoint.retrieve` method signature (remove `id` param, call `_get` directly) — sufficiently clear-cut
- `Tax` model fix (remove the duplicate `name: str` line, preserve `max_length=40`) — straightforward
- Exact `except` clause ordering for multi-catch blocks

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source code — locations of changes
- `src/loyverse_sdk/db/exporter.py` — 10 bare `except Exception:` blocks (lines 151, 161, 271, 325, 371, 389, 390, 425, 460, 484, 489)
- `src/loyverse_sdk/client.py` — 2 bare `except Exception:` blocks (lines 130, 156)
- `src/loyverse_sdk/models/tax.py` — duplicate `name` field (line 88 overwrites line 77's `max_length=40`)
- `src/loyverse_sdk/endpoints/merchant.py` — `retrieve(self, id: str)` uses unused `id` parameter
- `src/loyverse_sdk/models/shift.py` — orphaned file for deletion
- `src/loyverse_sdk/utils.py` — keep `standardize_datetime_str`, remove `convert_response` and `use_model`
- `src/loyverse_sdk/db/schemas.py` — dead file for deletion
- `src/loyverse_sdk/core/logging.py` — dead file for deletion
- `src/loyverse_sdk/db/__init__.py` — no imports from `schemas.py` (confirmed)
- `src/loyverse_sdk/models/__init__.py` — no imports from `shift.py` (confirmed)

### Codebase maps
- `.planning/codebase/CONCERNS.md` — Full detail on each bug, dead code location, and exception issue
- `.planning/codebase/STRUCTURE.md` — File layout and integration points
- `.planning/REQUIREMENTS.md` — Requirement traceability (BUG-01, BUG-02, CLN-01 through CLN-04, QLT-01, QLT-02)

</canonical_refs>

<code_context>
## Existing Code Insights

### Patterns
- Exception hierarchy already exists in `src/loyverse_sdk/exceptions.py` with specific types (`ExportError`, `duckdb.Error`, etc.) — reuse these rather than defining new ones
- `exporter.py` already imports `duckdb` and `ExportError` — no new imports needed for exception changes
- `client.py` already imports `json` implicitly via `resp.json()` — no new import needed for `json.JSONDecodeError`

### Integration Points
- Changes to `exporter.py` exception handling affect only the export pipeline — no external API changes
- Removal of `shift.py`, `schemas.py`, `logging.py` is self-contained (no cross-references in imports)
- `utils.py` cleanup preserves `standardize_datetime_str` which is imported by `mixins.py`

</code_context>

<specifics>
## Specific Ideas

No specific requirements — all items are well-defined in REQUIREMENTS.md and CONCERNS.md with clear fix approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-code-cleanup-bugfixes*
*Context gathered: 2026-05-25*

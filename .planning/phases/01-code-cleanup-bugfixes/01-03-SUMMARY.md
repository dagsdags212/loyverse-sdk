---
phase: 01-code-cleanup-bugfixes
plan: 03
subsystem: db, client
tags: [exception-handling, cleanup, exporter, client, duckdb]

# Dependency graph
requires:
  - phase: 01-01
    provides: "Dead code removal (utils.py, schemas.py, shift.py, logging.py)"
  - phase: 01-02
    provides: "Tax model fix, merchant endpoint fix"
provides:
  - "11 bare except Exception blocks in exporter.py replaced with ExportError, duckdb.Error, pl.exceptions.PolarsError"
  - "2 bare except Exception blocks in client.py replaced with json.JSONDecodeError"
  - "1 raise Exception in exporter.py replaced with raise ExportError"
affects: [error-propagation, debugging, security]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Catch-and-wrap: except ExportError → re-raise as ExportError (pipeline pattern D-01)"
    - "DuckDB-only operations: except duckdb.Error (non-critical failure pattern D-02)"
    - "Polars operations: except pl.exceptions.PolarsError (with fallback pattern D-04)"
    - "JSON parse: except json.JSONDecodeError (let non-parse exceptions propagate)"

key-files:
  modified:
    - src/loyverse_sdk/db/exporter.py
    - src/loyverse_sdk/client.py

key-decisions:
  - "ExportError catch at lines 151, 271, 325 uses pipeline catch-and-wrap (D-01) — operations within those blocks only produce ExportError"
  - "duckdb.Error for non-critical DuckDB operations (index creation, sync metadata) — failures are silent warnings, not export blockers (D-02)"
  - "pl.exceptions.PolarsError at line 371 with duckdb.Error fallback at line 389 — two-tier insertion strategy (D-04)"
  - "raise Exception → raise ExportError at line 390 consistent with pipeline exception hierarchy (D-05)"
  - "json.JSONDecodeError replaces bare Exception — critical errors like MemoryError/KeyboardInterrupt now propagate correctly (D-06, D-07)"

requirements-completed: [QLT-01, QLT-02]

# Metrics
duration: 3min
completed: 2026-05-25
---

# Phase 01 Plan 03: Tighten Exception Handling Summary

**Replaced all 13 bare `except Exception:` blocks across `exporter.py` (11 blocks + 1 `raise Exception`) and `client.py` (2 blocks) with specific exception types aligned to the project's error hierarchy.**

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Replace 11 bare except Exception blocks in exporter.py + replace raise Exception | 85f2839 | src/loyverse_sdk/db/exporter.py |
| 2 | Replace 2 bare except Exception blocks in client.py | a89189b | src/loyverse_sdk/client.py |

## Deviations from Plan

None — plan executed exactly as written.

## Details

### Task 1: exporter.py Exception Tightening

**12 changes applied to `src/loyverse_sdk/db/exporter.py`:**

| # | Line | Change | Type |
|---|------|--------|------|
| 1 | 151 | `except Exception` → `except ExportError` | Catch-and-wrap pipeline (D-01) |
| 2 | 161 | `except Exception` → `except duckdb.Error` | DuckDB index creation (D-02) |
| 3 | 271 | `except Exception` → `except ExportError` | Catch-and-wrap merchant (D-01) |
| 4 | 325 | `except Exception` → `except ExportError` | Catch-and-wrap batch insert (D-01) |
| 5 | 371 | `except Exception` → `except pl.exceptions.PolarsError` | Polars DataFrame (D-04) |
| 6 | 389 | `except Exception` → `except duckdb.Error` | DuckDB fallback insert (D-04) |
| 7 | 390 | `raise Exception` → `raise ExportError` | Consistent hierarchy (D-05) |
| 8 | 425 | `except Exception` → `except duckdb.Error` | Sync metadata update (D-02) |
| 9 | 460 | `except Exception` → `except duckdb.Error` | Sync metadata query (D-02) |
| 10 | 484 | `except Exception` → `except duckdb.Error` | Per-table count (D-02) |
| 11 | 489 | `except Exception` → `except duckdb.Error` | Overall table count (D-02) |

No new imports needed — `duckdb`, `pl`, and `ExportError` already in scope.

**Verification results:**
- ✅ `except ExportError as e:` count: 3
- ✅ `except duckdb.Error` count: 6
- ✅ `except pl.exceptions.PolarsError` count: 1
- ✅ `raise ExportError` count: 6 (≥4 target)
- ✅ No bare `except Exception` remaining
- ✅ No bare `raise Exception` remaining
- ✅ Syntax check passes

### Task 2: client.py Exception Tightening

**3 changes applied to `src/loyverse_sdk/client.py`:**

1. Added `import json` to stdlib imports (line 1)
2. Line ~131: `except Exception` → `except json.JSONDecodeError` (error response JSON parse)
3. Line ~157: `except Exception` → `except json.JSONDecodeError` (success response JSON parse)

**Verification results:**
- ✅ `import json` present at line 1
- ✅ `except json.JSONDecodeError` count: 2
- ✅ No bare `except Exception` remaining
- ✅ Syntax check passes

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: mitigated | exporter.py | Previously, bare `except Exception` blocks could silently swallow MemoryError/KeyboardInterrupt during exports. Replaced with specific types (ExportError, duckdb.Error, PolarsError) — critical errors now propagate correctly. |
| threat_flag: mitigated | client.py | Previously, bare `except Exception` in JSON parse could silently swallow MemoryError/KeyboardInterrupt. Replaced with `json.JSONDecodeError` — only JSON parse failures are handled, critical errors propagate. |

## Known Stubs

None.

## Self-Check

All verification criteria from the plan met:
- [x] ExportError catches: 3 ✓
- [x] duckdb.Error catches: 6 ✓
- [x] PolarsError catches: 1 ✓
- [x] raise ExportError: ≥4 ✓
- [x] No bare except Exception in exporter.py ✓
- [x] No bare raise Exception in exporter.py ✓
- [x] import json in client.py ✓
- [x] json.JSONDecodeError catches: 2 ✓
- [x] No bare except Exception in client.py ✓
- [x] Syntax OK for both files ✓

---
phase: 06-export-to-flat-files
plan: 01
subsystem: exporters
tags: [export, csv, parquet, polars, pydantic]
dependency_graph:
  requires: []
tech_stack:
  added: []
  patterns:
    - "Stateless exporter class delegating to Polars DataFrame I/O"
    - "model_dump(mode='json') for JSON-safe serialization before Polars ingestion"
key_files:
  created:
    - src/loyverse_sdk/exporters/__init__.py
    - src/loyverse_sdk/exporters/exporter.py
    - tests/unit/exporters/__init__.py
    - tests/unit/exporters/test_exporter.py
  modified: []
decisions:
  - "Uses model_dump(mode='json') for Pydantic→Polars conversion to avoid Object dtype errors"
metrics:
  duration: "short"  # single-task plan
  completed_date: "2026-05-27"
---

# Phase 06 Plan 01: FlatFileExporter — CSV & Parquet Export via Polars

**One-liner:** Created `exporters/` package with a stateless `FlatFileExporter` class that converts lists of Pydantic model instances into CSV and Parquet files using Polars, with comprehensive TDD unit tests.

## Task Summary

| # | Task | Type | Status | Commit |
|---|------|------|--------|--------|
| 1 | Create exporters package and FlatFileExporter class | auto (tdd) | ✓ Complete | `eba50ab` |

### TDD Cycle

| Phase | Commit | Description |
|-------|--------|-------------|
| RED | `5459063` | `test(06-01): add failing tests for FlatFileExporter CSV/Parquet export` — 17 unit tests |
| GREEN | `eba50ab` | `feat(06-01): implement FlatFileExporter for CSV/Parquet export` — 213 LOC, all tests pass |

## What Was Built

### `src/loyverse_sdk/exporters/` package

**`FlatFileExporter`** — Stateless exporter class with two public methods:

- **`export_csv(data, filepath)`** — Writes Pydantic models to CSV using Polars defaults (comma delimiter, double-quote quoting, UTF-8, headers included)
- **`export_parquet(data, filepath)`** — Writes Pydantic models to Parquet with Snappy compression

**Module-level convenience functions:**
- `export_csv(data, filepath)` — delegates to `FlatFileExporter().export_csv()`
- `export_parquet(data, filepath)` — delegates to `FlatFileExporter().export_parquet()`

**Key implementation details:**
- Uses `model.model_dump(mode="json")` to convert Pydantic models to JSON-safe types (UUID→str, datetime→ISO str, etc.) before creating Polars DataFrames — essential because Polars CSV/Parquet writers don't support Object dtype
- Empty input: prints warning via `print()` and writes empty file (matching existing project logging patterns)
- Invalid paths: wraps Polars exceptions in `ExportError(message=..., resource_name="file_export")` (consistent with `DuckDBExporter` error pattern)
- Accepts `str | Path` for filepath parameter
- Accepts `Sequence[BaseModel]` for data parameter

### Test Coverage (17 tests)

| Test | Covers |
|------|--------|
| `test_exporter_instantiation` | FlatFileExporter can be created |
| `test_exporter_has_export_csv_method` | Method exists and is callable |
| `test_exporter_has_export_parquet_method` | Method exists and is callable |
| `test_export_csv_basic` | Single model → valid CSV file |
| `test_export_csv_has_correct_headers` | Header row contains all model fields |
| `test_export_csv_multiple_records` | 5 models → 5 data rows |
| `test_export_csv_commas_in_string` | Comma-containing fields are double-quoted |
| `test_export_csv_empty_list` | Empty list → warning + empty file (no crash) |
| `test_export_csv_invalid_path` | Invalid path → ExportError |
| `test_export_csv_pathlib` | Accepts pathlib.Path |
| `test_export_parquet_basic` | Single model → valid Parquet file |
| `test_export_parquet_readable` | Parquet readable by `pl.read_parquet()` |
| `test_export_parquet_type_preservation` | Int→Int64, Float→Float64, Str→Utf8, Bool→Boolean |
| `test_export_parquet_empty_list` | Empty list → no crash |
| `test_export_parquet_invalid_path` | Invalid path → ExportError |
| `test_convenience_export_csv` | Module-level `export_csv()` works |
| `test_convenience_export_parquet` | Module-level `export_parquet()` works |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Polars Object dtype error in Pydantic→DataFrame conversion**
- **Found during:** Task 1 GREEN phase
- **Issue:** `model.model_dump()` produces UUID objects and other Python types that Polars stores as "Object" dtype, which `write_csv()` and `write_parquet()` cannot serialize
- **Fix:** Changed `model.model_dump()` to `model.model_dump(mode="json")` which converts all types to JSON-safe representations (UUID→str, datetime→ISO str, etc.)
- **Files modified:** `src/loyverse_sdk/exporters/exporter.py`
- **Commit:** `eba50ab`

**2. [Rule 1 - Bug] Fixed pytest collection warnings for Pydantic test model classes**
- **Found during:** Task 1 RED phase
- **Issue:** Test model classes named `TestModel`, `CommaModel`, `TypeModel` triggered Pydantic's `__init__` constructor collection warning in pytest
- **Fix:** Renamed to `SampleExportModel`, `CommaSampleModel`, `TypeSampleModel` to avoid pytest's "Test" prefix collection heuristic
- **Files modified:** `tests/unit/exporters/test_exporter.py`
- **Commit:** `5459063` (applied before RED phase commit)

## Known Stubs

None.

## Threat Flags

None. All threats in the plan's threat model (T-06-01, T-06-02, T-06-03, T-06-SC) are `accept` disposition — no new security surface.

## Verification

- [x] `grep -n "class FlatFileExporter" src/loyverse_sdk/exporters/exporter.py` → line 18
- [x] `grep -n "def export_csv\|def export_parquet" src/loyverse_sdk/exporters/exporter.py` → 4 matches (2 class, 2 module-level)
- [x] `grep -n "ExportError" src/loyverse_sdk/exporters/exporter.py` → in try/except block (lines 152-155)
- [x] `grep -n "write_csv\|write_parquet" src/loyverse_sdk/exporters/exporter.py` → 3 matches
- [x] `grep -c "def test_" tests/unit/exporters/test_exporter.py` → 17 (≥10)
- [x] `python -m pytest tests/unit/exporters/ -v --tb=short` → 17 passed
- [x] Full test suite: 237 passed, 0 failed

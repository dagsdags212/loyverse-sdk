---
status: partial
phase: 01-code-cleanup-bugfixes
source: [01-VERIFICATION.md]
started: 2026-05-25
updated: 2026-05-25
---

## Current Test

[awaiting human testing]

## Tests

### 1. CR-01: export_all loop catch width — exporter.py:151
expected: Decide whether `except ExportError` is acceptable (plan's D-01 decision) or should be broadened to catch `duckdb.Error`/other exceptions and wrap them in ExportError (reviewer's recommendation).
result: [pending]

### 2. CR-02: _batch_insert catch width — exporter.py:318
expected: Same decision — narrow `except ExportError` vs broader `except (ExportError, duckdb.Error)` as reviewer recommends.
result: [pending]

### 3. CR-03: _export_merchant catch width — exporter.py:268
expected: Same decision — narrow `except ExportError` vs broader catch that wraps with merchant context.
result: [pending]

### 4. CR-04: _insert_records_to_table coverage — exporter.py:343-383
expected: Confirm path where `conn.execute()` and `conn.unregister()` outside the Polars try/except are covered by upstream catches, or add a `duckdb.Error` guard.
result: [pending]

### 5. WR-02: connection.py:118 bare except Exception in transaction rollback
expected: Acknowledge as pre-existing or decide to fix. This `except Exception` in rollback interacts with now-narrower exporter catches.
result: [pending]

## Summary

total: 5
passed: 0
issues: 0
pending: 5
skipped: 0
blocked: 0

## Gaps

# Requirements: Loyverse Data Toolkit

**Defined:** 2026-05-25
**Core Value:** Data can be reliably pulled from the Loyverse API into local storage for analysis, with correct typing and error handling throughout.

## v1 Requirements

### Test Bugs

- [ ] **TST-01**: Fix all 8 test model imports from `loyverse_api` to `loyverse_sdk`
- [ ] **TST-02**: Fix `surchage` typo to `surcharge` in receipt model test

### Code Bugs

- [x] **BUG-01**: Remove duplicate `name` field in Tax model (second overwrites `max_length=40`)
- [x] **BUG-02**: Fix `MerchantEndpoint.retrieve(id)` — remove unused `id` parameter, construct correct URL for singleton resource

### Dead Code Removal

- [ ] **CLN-01**: Remove orphaned `models/shift.py` (no endpoint, no client integration, no tests)
- [ ] **CLN-02**: Remove dead `utils.py` functions (`convert_response`, `use_model`)
- [ ] **CLN-03**: Remove dead `db/schemas.py` (unused SQLModel schema)
- [ ] **CLN-04**: Remove dead `core/logging.py` stub

### Code Quality

- [x] **QLT-01**: Replace 11+ bare `except Exception:` blocks in `db/exporter.py` with specific exception handling
- [x] **QLT-02**: Replace 2 bare `except Exception:` blocks in `client.py` with specific exception handling

### Verification

- [ ] **VER-01**: All existing tests pass after fixes

## v2 Requirements

None — this is a single cleanup phase.

## Out of Scope

| Feature | Reason |
|---------|--------|
| New endpoint classes or features | Cleanup/bugfix only — no new functionality |
| New test coverage for endpoints/client/auth | Deferred — focus on fixing existing tests |
| Replace `pytz` with `zoneinfo` | Nice-to-have, not part of cleanup |
| Remove `sqlmodel` or `polars` dependencies | Risk reduction, not cleanup |
| Add retry/rate-limit logic | New feature, not bugfix |
| Replace `db/schema_builder.py` raw SQL | Refactor, not cleanup |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TST-01 | Phase 2 | Pending |
| TST-02 | Phase 2 | Pending |
| BUG-01 | Phase 1 | Complete |
| BUG-02 | Phase 1 | Complete |
| CLN-01 | Phase 1 | Pending |
| CLN-02 | Phase 1 | Pending |
| CLN-03 | Phase 1 | Pending |
| CLN-04 | Phase 1 | Pending |
| QLT-01 | Phase 1 | Complete |
| QLT-02 | Phase 1 | Complete |
| VER-01 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 11 total
- Mapped to phases: 11 ✓
  - Phase 1: 8 requirements
  - Phase 2: 3 requirements
- Unmapped: 0 ✓

---

*Requirements defined: 2026-05-25*
*Last updated: 2026-05-25 after initial definition*

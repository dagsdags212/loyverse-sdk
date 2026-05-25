# Roadmap: Loyverse Data Toolkit

## Overview

Fix all identified bugs, remove dead code, tighten exception handling, and get the existing test suite passing. The codebase was built as a client library + export pipeline but has several concrete bugs, orphaned modules, bare exception blocks, and tests with wrong package imports. This roadmap delivers a clean, working codebase ready for future feature work.

## Phases

- [ ] **Phase 1: Code Cleanup & Bugfixes** - Fix code-level bugs, remove orphaned/dead code, and replace bare exception blocks with specific handling
- [ ] **Phase 2: Test Fixes & Verification** - Fix test imports, correct test field names, and verify all tests pass

## Phase Details

### Phase 1: Code Cleanup & Bugfixes
**Goal**: All code-level bugs are fixed, dead code is removed, and exception handling is tightened throughout the codebase
**Depends on**: Nothing (first phase)
**Requirements**: BUG-01, BUG-02, CLN-01, CLN-02, CLN-03, CLN-04, QLT-01, QLT-02
**Success Criteria** (what must be TRUE):
  1. Tax model has no duplicate `name` field; original `max_length=40` constraint is preserved
  2. `MerchantEndpoint.retrieve()` requires no argument and correctly fetches the singleton merchant resource using the right URL
  3. No orphaned files remain in the source tree: `models/shift.py` is gone, `utils.py` has no dead functions (`convert_response`, `use_model`), `db/schemas.py` and `core/logging.py` are removed
  4. All 11+ bare `except Exception:` blocks in `db/exporter.py` and 2 bare `except Exception:` blocks in `client.py` are replaced with specific exception types
  5. The codebase imports cleanly with no `ModuleNotFoundError` or `AttributeError` from removed code
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Remove orphaned files (shift.py, schemas.py, logging.py) and dead utils.py functions
- [ ] 01-02-PLAN.md — Fix Tax model duplicate name field and MerchantEndpoint singleton retrieve
- [ ] 01-03-PLAN.md — Replace 13 bare `except Exception:` blocks with specific exception types

### Phase 2: Test Fixes & Verification
**Goal**: All existing tests import correctly and pass against the cleaned-up codebase
**Depends on**: Phase 1
**Requirements**: TST-01, TST-02, VER-01
**Success Criteria** (what must be TRUE):
  1. All 8 test model files import from `loyverse_sdk` (not the incorrect `loyverse_api`)
  2. Receipt model test uses the correct `surcharge` field name (not the typo `surchage`)
  3. `pytest` run across all tests exits with zero failures and zero errors
  4. Verification output exists showing the full test run completed successfully
**Plans**: TBD

## Progress

**Execution Order:** Phases execute in numeric order: 1 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Code Cleanup & Bugfixes | 0/3 | Planned | - |
| 2. Test Fixes & Verification | 0/TBD | Not started | - |

# Milestones

## v1.0 Initial Cleanup (Shipped: 2026-05-25)

**Phases completed:** 2 phases, 5 plans, 7 tasks

**Key accomplishments:**

- Removed 3 orphaned/dead Python files and 2 unused functions, verified via import smoke tests and grep confirmation
- Removed duplicate `name` field from Tax model preserving `max_length=40` constraint; corrected `MerchantEndpoint.retrieve()` from a broken `GET /merchant/{id}` to proper singleton `GET /merchant`.
- Replaced all 13 bare `except Exception:` blocks across `exporter.py` (11 blocks + 1 `raise Exception`) and `client.py` (2 blocks) with specific exception types aligned to the project's error hierarchy.
- One-liner:

---

# Phase 1: Code Cleanup & Bugfixes - Pattern Map

**Mapped:** 2026-05-25
**Files analyzed:** 10 new/modified files (+ 3 deletions)
**Analogs found:** 8 / 10 (2 verified as no-change)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/loyverse_sdk/db/exporter.py` | service | batch/streaming | `src/loyverse_sdk/client.py` (specific `except` pattern) | role-match |
| `src/loyverse_sdk/client.py` | controller | request-response | `src/loyverse_sdk/client.py` lines 108-124 (self-pattern) | exact |
| `src/loyverse_sdk/models/tax.py` | model | CRUD (validation) | `src/loyverse_sdk/models/discount.py` | exact |
| `src/loyverse_sdk/endpoints/merchant.py` | endpoint | request-response | `src/loyverse_sdk/endpoints/categories.py` | role-match |
| `src/loyverse_sdk/utils.py` | utility | utility | `src/loyverse_sdk/helpers.py` (sibling utility) | role-match |
| `src/loyverse_sdk/models/shift.py` | model | — (delete) | N/A — orphaned file | N/A |
| `src/loyverse_sdk/db/schemas.py` | config | — (delete) | N/A — dead file | N/A |
| `src/loyverse_sdk/core/logging.py` | utility | — (delete) | N/A — stub file | N/A |
| `src/loyverse_sdk/db/__init__.py` | config | — (verify only) | N/A — confirmed no change needed | N/A |
| `src/loyverse_sdk/models/__init__.py` | config | — (verify only) | N/A — confirmed no change needed | N/A |

## Pattern Assignments

### `src/loyverse_sdk/db/exporter.py` (service, batch/streaming)

**Analog:** `src/loyverse_sdk/client.py` lines 108-124 — specific exception handling pattern

**Current exception types already in scope:**
- `ExportError` — already imported at line 16
- `duckdb` — already imported at line 10
- `pl` (polars) — already imported at line 11

**Imports pattern** (already present, no new imports needed):
```python
# exporter.py lines 10-11, 16
import duckdb
import polars as pl
from loyverse_sdk.exceptions import ExportError
```

**Specific exception handling pattern** (from `client.py` lines 108-124):
```python
# client.py:108-124 — Best analog for typed exception handling
try:
    resp = await self._client.request(method, path, **kwargs)
except httpx.TimeoutException as e:
    raise NetworkError(
        f"Request to '{path}' timed out",
        original_error=e
    )
except httpx.ConnectError as e:
    raise NetworkError(
        f"Failed to connect to API at '{path}'",
        original_error=e
    )
except httpx.HTTPError as e:
    raise NetworkError(
        f"Network error occurred while requesting '{path}'",
        original_error=e
    )
```

**Existing `ExportError` catch-and-wrap pattern** (already correct, extend it):
```python
# exporter.py lines 151-155 — Pattern to replicate for ExportError blocks
except Exception as e:
    raise ExportError(
        f"Failed to export {resource_name}: {e}",
        resource_name=resource_name
    )

# exporter.py lines 325-329 — Same pattern in _batch_insert
except Exception as e:
    raise ExportError(
        f"Failed to insert batch for {resource_name}: {e}",
        resource_name=resource_name
    )
```

**`duckdb.Error` catch pattern** (to apply to DuckDB-only operations):
```python
# New pattern — replace `except Exception:` with `except duckdb.Error:`
# For lines 161, 425, 460, 484, 489
except duckdb.Error as e:
    # Don't fail export if index creation fails
    print(f"Warning: Failed to create indexes: {e}")
```

**`pl.exceptions.PolarsError` catch pattern** (for Polars DataFrame insertion):
```python
# New pattern — line 371: replace `except Exception as e:` 
try:
    df = pl.DataFrame(records)
    ...
except pl.exceptions.PolarsError as e:
    # Try alternative approach if Polars fails
    ...
```

**`raise Exception` → `raise ExportError` pattern** (line 390):
```python
# New pattern — replace `raise Exception(...)` 
raise ExportError(
    f"Failed to insert into {table_name}: {e}. "
    f"Fallback also failed: {fallback_error}"
)
```

**Error handling pattern** (from `mixins.py` lines 31-38 — validation error wrapping):
```python
# mixins.py:31-38 — Pattern for wrapping specific errors into SDK types
try:
    return model.model_validate(data)
except PydanticValidationError as e:
    console.log(f"[red]Validation failed for {model.__name__}[/red]")
    raise ValidationError(
        message=str(e),
        validation_errors=e.errors(),
        model_name=model.__name__
    )
```

**Summary of changes needed in `exporter.py`:**

| Line | Current | Replace With | Rationale | 
|---|---|---|---|
| 151 | `except Exception as e:` | `except ExportError as e:` | D-01: pipeline catch-and-wrap, already re-raises as ExportError |
| 161 | `except Exception as e:` | `except duckdb.Error as e:` | D-02: DuckDB-only operation (index creation) |
| 271 | `except Exception as e:` | `except ExportError as e:` | D-01: already re-raises as ExportError |
| 325 | `except Exception as e:` | `except ExportError as e:` | D-01: already re-raises as ExportError |
| 371 | `except Exception as e:` | `except pl.exceptions.PolarsError as e:` | D-04: Polars DataFrame creation |
| 389 | `except Exception as fallback_error:` | `except duckdb.Error as fallback_error:` | D-04: DuckDB fallback insert |
| 390 | `raise Exception(...)` | `raise ExportError(...)` | D-05: consistent with pipeline pattern |
| 425 | `except Exception as e:` | `except duckdb.Error as e:` | D-02: DuckDB-only sync metadata |
| 460 | `except Exception:` | `except duckdb.Error:` | D-02: DuckDB-only metadata query |
| 484 | `except Exception:` | `except duckdb.Error:` | D-02: DuckDB-only per-table count |
| 489 | `except Exception:` | `except duckdb.Error:` | D-02: DuckDB-only overall count |

---

### `src/loyverse_sdk/client.py` (controller, request-response)

**Analog:** Self-pattern — use existing specific `except` blocks at lines 108-124

**Current imports** (lines 1-15) — `json` is used implicitly via `resp.json()`, no new import needed:
```python
import httpx
from loyverse_sdk.exceptions import (
    APIError, BadRequestError, AuthenticationError, ForbiddenError,
    NotFoundError, RateLimitError, ServerError, NetworkError,
)
```

**Existing specific exception pattern** (lines 108-124 — the correct pattern to replicate):
```python
except httpx.TimeoutException as e:
    raise NetworkError(...)
except httpx.ConnectError as e:
    raise NetworkError(...)
except httpx.HTTPError as e:
    raise NetworkError(...)
```

**Current bare `except Exception` at line 130** (error payload parsing):
```python
# Current (line 128-131):
try:
    payload = resp.json()
except Exception:          # <-- replace this
    payload = resp.text

# Target:
try:
    payload = resp.json()
except json.JSONDecodeError:   # D-03: JSON parse failure
    payload = resp.text
```

**Current bare `except Exception` at line 156** (success response parsing):
```python
# Current (lines 154-157):
try:
    return resp.json()
except Exception:          # <-- replace this
    return resp.text

# Target:
try:
    return resp.json()
except json.JSONDecodeError:   # D-03: JSON parse failure
    return resp.text
```

**Note:** No `import json` is needed — `json` is a stdlib module and `resp.json()` already calls it internally; `json.JSONDecodeError` is accessible without an explicit import in Python 3.12+. However, adding `import json` at the top is still the safest approach.

---

### `src/loyverse_sdk/models/tax.py` (model, CRUD)

**Analog:** `src/loyverse_sdk/models/discount.py` lines 16-22 — standard Field pattern

**Current bug** (lines 7-12) — duplicate `name` field where second overwrites first's `max_length=40`:
```python
class Tax(Base):
    name: str = Field(max_length=40)   # line 8 — max_length=40 is the constraint to keep
    type: str                           # line 9
    name: str                           # line 10 — DUPLICATE, silently overwrites line 8
    rate: float = Field(ge=0.0, le=100.0)  # line 11
    stores: List[UUID]                  # line 12
```

**Correct pattern** (from `discount.py` — single clean field declaration):
```python
# discount.py lines 16-22 — Model with properly declared typed fields
class Discount(Base):
    type: DiscountType
    name: str
    discount_amount: float | None = Field(default=None, ge=0.0)
    discount_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    stores: list[UUID]
    restricted_access: bool = False
```

**Target fix** — remove the duplicate `name: str` on line 10:
```python
class Tax(Base):
    name: str = Field(max_length=40)
    type: str
    rate: float = Field(ge=0.0, le=100.0)
    stores: List[UUID]
```

---

### `src/loyverse_sdk/endpoints/merchant.py` (endpoint, request-response)

**Analog:** `src/loyverse_sdk/endpoints/categories.py` lines 18-19 — standard `retrieve` pattern

**Current bug** (lines 11-12) — `retrieve` takes unused `id` parameter that gets forwarded to `super().retrieve(id)`:
```python
class MerchantEndpoint(BaseEndpoint, RetrieveMixin):
    path = "merchant"

    async def retrieve(self, id: str):                    # BUG: id param is unused
        return await super().retrieve(id, model=Merchant)  # constructs GET /merchant/{id}
```

**How `RetrieveMixin.retrieve` works** (from `mixins.py` lines 49-62):
```python
# mixins.py lines 49-62 — super().retrieve(id) calls _get(f"{self.path}/{id}")
async def retrieve(self, id: str, model: Type[BaseModel] | None = None):
    data = await self._get(f"{self.path}/{id}")
    if model:
        try:
            return model.model_validate(data)
        except PydanticValidationError as e:
            ...
```

**Standard endpoint `retrieve` pattern** (from `categories.py` lines 18-19):
```python
# categories.py lines 18-19 — normal retrieve with id
async def retrieve(self, id: str):
    return await super().retrieve(id, model=Category)
```

**Target fix** — Merchant is a singleton, call `_get` with just the path, no `id`:
```python
class MerchantEndpoint(BaseEndpoint, RetrieveMixin):
    path = "merchant"

    async def retrieve(self):
        data = await self._get(self.path)
        return Merchant.model_validate(data)
```

---

### `src/loyverse_sdk/utils.py` (utility, utility)

**Analog:** `src/loyverse_sdk/helpers.py` lines 8-148 — sibling utility module pattern

**Current state** (lines 13-51) — two dead functions to remove:
```python
# lines 13-16: Dead no-op function
def convert_response(data: Any, model: Type[BaseModel]):
    """Convert raw API responses into models, preserving pagination envelopes"""
    if isinstance(data, dict) and "items":
        ...

# lines 19-51: Dead decorator never imported by any endpoint
def use_model(model: Type[BaseModel] | None = None):
    """Attach model-conversion support to endpoint methods."""
    async def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            ...
    return decorator
```

**What to keep** — `standardize_datetime_str` (lines 7-10), still imported by `mixins.py:5`:
```python
# keep this function, remove all other code
def standardize_datetime_str(dt: datetime) -> str:
    """Coverts datetime object to ISO 8601 format"""
    assert isinstance(dt, datetime), "dt must be a datetime object"
    return dt.isoformat(timespec="milliseconds") + "Z"
```

**`utils.py` imports** — after cleanup, should narrow to only what's needed:
```python
from datetime import datetime
```

**Verification that `standardize_datetime_str` is still used** (from `mixins.py:5`):
```python
# mixins.py:5 — still imports from utils.py
from loyverse_sdk.utils import standardize_datetime_str
```

---

### Files to Delete (No Pattern Analog Needed)

**`src/loyverse_sdk/models/shift.py`** — orphaned model:
- Defines `Shift`, `CashMovement`, `ShiftListResponse`
- No endpoint references it
- No `__init__.py` import (confirmed in `models/__init__.py` — no `shift` import)
- Safe to delete entirely

**`src/loyverse_sdk/db/schemas.py`** — dead SQLModel definitions:
- Defines `Employee`, `Customer`, `PaymentType`, `Discount`, `Receipt` as SQLModel table classes
- Not used by the export pipeline (uses `schema_builder.py` raw SQL)
- References `config.db_url` which does not exist on `Config` class
- No `__init__.py` import (confirmed in `db/__init__.py` — no `schemas` import)
- Safe to delete entirely

**`src/loyverse_sdk/core/logging.py`** — stub:
- Contains only `class Logger: ...` (no body)
- Never imported anywhere in codebase
- Safe to delete entirely

---

## Shared Patterns

### Exception Hierarchy
**Source:** `src/loyverse_sdk/exceptions.py`
**Apply to:** All `except Exception:` replacements in `exporter.py`

Available exception types relevant to this phase:

| Exception | Line | When to Use |
|-----------|------|-------------|
| `ExportError(LoyverseSDKError)` | 290-312 | Catch-and-wrap blocks in export pipeline that re-raise as ExportError |
| `duckdb.Error` (stdlib) | N/A | DuckDB-specific operations (index creation, metadata queries, table counts) |
| `pl.exceptions.PolarsError` (polars) | N/A | Polars DataFrame creation in batch insert path |
| `json.JSONDecodeError` (stdlib) | N/A | JSON response parsing in `client.py` |

**Key exception hierarchy** (from `exceptions.py`):
```python
# exceptions.py lines 12-312
class LoyverseSDKError(Exception):        # Root
class APIError(LoyverseSDKError):          # HTTP errors (status >= 400)
class BadRequestError(APIError):           # 400
class AuthenticationError(APIError):       # 401
class ForbiddenError(APIError):            # 403
class NotFoundError(APIError):             # 404
class RateLimitError(APIError):            # 429
class ServerError(APIError):               # 5xx
class ConfigurationError(LoyverseSDKError) # SDK config issues
class ValidationError(LoyverseSDKError)    # Pydantic validation failures
class PaginationError(LoyverseSDKError)    # Pagination issues
class NetworkError(LoyverseSDKError)       # Network/connection issues
class ResourceNotFoundError(LoyverseSDKError) # Empty query results
class ExportError(LoyverseSDKError)        # DuckDB export failures
```

### Import Smoke Test Pattern
**Source:** `01-CONTEXT.md` decision D-06
**Apply to:** Verification of all changes

```bash
# Verify no import breakage after each change
python -c "from loyverse_sdk import LoyverseClient"

# Verify test collection not broken
uv run pytest --collect-only
```

### Dead Code Deletion Verification Pattern
**Source:** `01-CONTEXT.md` decision D-09
**Apply to:** All file deletions

Before deleting a file, confirm:
1. No imports in `__init__.py` files reference it
2. No `import` statements in other source files reference it
3. No `__all__` exports list it

Confirmed for this phase:
- `models/shift.py` — not in `models/__init__.py` (confirmed lines 1-19)
- `db/schemas.py` — not in `db/__init__.py` (confirmed lines 1-47)
- `core/logging.py` — not imported anywhere (confirmed via codebase search)

## Metadata

**Analog search scope:** `src/loyverse_sdk/` (entire package)
**Files scanned:** 18 (exporter.py, client.py, exceptions.py, base.py, mixins.py, connection.py, utils.py, helpers.py, schemas.py, logging.py, tax.py, discount.py, category.py, merchant.py, categories.py, shift.py, `__init__.py` in models and db)
**Pattern extraction date:** 2026-05-25

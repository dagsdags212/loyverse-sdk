# Error Handling

All exceptions raised by the SDK derive from a single base class,
`LoyverseSDKError`, so you can catch everything the library throws with one
`except`. Import them from `loyverse_sdk.exceptions`:

```python
from loyverse_sdk.exceptions import (
    LoyverseSDKError,
    APIError,
    AuthenticationError,
    RateLimitError,
    NetworkError,
    ValidationError,
    ExportError,
)
```

(The `exceptions` module is also re-exported as `loyverse_sdk.exceptions`.)

## Hierarchy

```
LoyverseSDKError                  base for everything
├── APIError                      HTTP error responses (status_code, payload, endpoint)
│   ├── BadRequestError           400
│   ├── AuthenticationError       401 — missing/invalid token
│   ├── ForbiddenError            403 — token lacks permission
│   ├── NotFoundError             404 — resource/path not found
│   ├── RateLimitError            429 — includes retry_after (seconds) when provided
│   └── ServerError               5xx — Loyverse-side error
├── ConfigurationError            bad/missing config (e.g. no API token)
├── ValidationError               response/query failed model validation
├── PaginationError               malformed pagination response
├── NetworkError                  timeout / connection failure (original_error)
├── ResourceNotFoundError         a helper found no matching records
└── ExportError                   a DuckDB export/sync failed (resource_name)
```

## Handling API errors

```python
from loyverse_sdk.exceptions import (
    AuthenticationError, RateLimitError, APIError, NetworkError,
)

try:
    response = await client.customers.list()
except AuthenticationError:
    print("Check your API token — run `loyverse init`.")
except RateLimitError as e:
    print(f"Rate limited; retry after {e.retry_after}s")
except APIError as e:
    print(f"API returned {e.status_code} for {e.endpoint}")
except NetworkError as e:
    print(f"Network problem: {e.original_error}")
```

Catch the broadest class that makes sense — `APIError` covers every HTTP status,
and `LoyverseSDKError` covers everything including config, validation, and export
errors.

## Rate limits

When the API responds with HTTP 429, the SDK raises `RateLimitError`. If the
response includes a `Retry-After` header, its value (in seconds) is available on
`e.retry_after`. The SDK does not retry automatically — implement backoff in your
caller for long-running jobs:

```python
import asyncio
from loyverse_sdk.exceptions import RateLimitError

while True:
    try:
        return await client.receipts.list(query)
    except RateLimitError as e:
        await asyncio.sleep(e.retry_after or 5)
```

## Validation errors

[[Query-Models]] validate their inputs before any request is sent — for example,
`created_at_min` must be `<= created_at_max` and `limit` must be between 1 and
250. Invalid input raises `ValidationError` with a descriptive message and the
underlying field errors.

## See also

- [[Client]] — where authentication and network errors originate
- [[Query-Models]] — input validation rules
- [[Helpers]] — raise `ResourceNotFoundError` / `ConfigurationError`
- [[DuckDB-Export]] — raises `ExportError` on failure

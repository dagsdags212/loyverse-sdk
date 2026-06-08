# Quickstart

This page gets you from a fresh install to your first results — once in Python
and once from the terminal. If you haven't already, work through
[[Installation]] and [[Configuration]] first.

## Python

Instantiate a [[Client]], make a call, and close it when done.
The client is asynchronous, so run it inside an event loop:

```python
import asyncio
from loyverse_sdk import LoyverseClient

async def main():
    client = LoyverseClient()

    # List customers (uses the default limit from config)
    response = await client.customers.list()
    print(f"Found {len(response.items)} customers")

    await client.close()

asyncio.run(main())
```

With no `api_token` argument, the client reads your token from the configuration
written by `loyverse init` (see [[Configuration]]). Every resource hangs off the
client as an attribute and shares the same CRUD + pagination interface — see
[[Endpoints]].

## CLI

The `loyverse` command gives you the same access without writing Python. Set up
your token once, then list a resource:

```bash
loyverse init                      # store token + database (one time)
loyverse api list customers        # list records
loyverse api list customers --limit 10 --format table
```

Resource commands live under the `api` subgroup (`loyverse api list`,
`loyverse api get`, …). See [[CLI]] for the full command reference.

## Where to go next

- [[Endpoints]] — every resource and the CRUD + pagination pattern
- [[CLI]] — the complete `loyverse` command reference
- [[Configuration]] — token, config directory, and resolution order
- [[Error-Handling]] — what to catch when a call fails

## See also

- [[Installation]] — install the SDK and console scripts
- [[Client]] — construct and configure the client
- [[Endpoints]] — call the API in Python
- [[CLI]] — call the API from the terminal
- [[Query-Models]] — filter and paginate list requests

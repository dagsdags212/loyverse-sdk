# Loyverse SDK

Asynchronous Python SDK, CLI, and MCP server for the
[Loyverse API](https://developer.loyverse.com/docs/) — a point-of-sale (POS)
platform for managing sales, inventory, and customers.

## Features

- **Async/await** client built on `httpx` for non-blocking API calls
- **Type-safe** request/response models powered by Pydantic
- **Automatic pagination** with cursor-based `iter_all()` iteration
- **Full CRUD** across 16 endpoints
- **`loyverse` CLI** — list, create, update, delete, export, and analyze from the terminal
- **`loyverse-mcp` server** — 18 read-only tools exposing your POS data to LLM clients (Claude Desktop, etc.)
- **DuckDB export** — a local relational warehouse for SQL analytics
- **Flat-file export** — write any query straight to CSV or Parquet
- **Analytics engine** — revenue, products, customers, profitability, inventory, and more

## Install

```bash
uv add loyverse_sdk          # core SDK
uv add "loyverse_sdk[mcp]"   # with the MCP server
```

See [Installation](docs/Installation.md) for pip, GitHub, and extras.

## Quickstart

```python
import asyncio
from loyverse_sdk import LoyverseClient

async def main():
    client = LoyverseClient()                 # reads your token from ~/.loyverse
    response = await client.customers.list()
    print(f"Found {len(response.items)} customers")
    await client.close()

asyncio.run(main())
```

Run `loyverse init` once to store your API token. See
[Configuration](docs/Configuration.md) and [Quickstart](docs/Quickstart.md) to
get going.

## Documentation

Full documentation lives in the [**`docs/`** wiki](docs/Home.md) — start at
[Home](docs/Home.md). Highlights:

- **Getting started:** [Installation](docs/Installation.md) · [Configuration](docs/Configuration.md) · [Quickstart](docs/Quickstart.md)
- **Python SDK:** [Client](docs/Client.md) · [Endpoints](docs/Endpoints.md) · [Query Models](docs/Query-Models.md) · [Models](docs/Models.md) · [Helpers](docs/Helpers.md) · [Error Handling](docs/Error-Handling.md)
- **Export & analytics:** [DuckDB Export](docs/DuckDB-Export.md) · [Flat-File Export](docs/Flat-File-Export.md) · [Analytics](docs/Analytics.md)
- **Tools:** [CLI](docs/CLI.md) · [MCP Server](docs/MCP-Server.md)
- **Project:** [Development](docs/Development.md)

> The pages under `docs/` use `[[wikilink]]` syntax so they render as a connected
> [GitHub Wiki](https://docs.github.com/en/communities/documenting-your-project-with-wikis).
> When browsing them in the repo, use the relative links above.

## License

MIT — see [LICENSE](LICENSE).

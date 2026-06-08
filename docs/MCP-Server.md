# MCP Server

`loyverse-mcp` is a [Model Context Protocol](https://modelcontextprotocol.io/)
stdio server that exposes your Loyverse data as MCP tools. Connect it to an LLM
client like [Claude Desktop](https://claude.ai/download) and ask about your POS
data in natural language — no code required.

## Installation

The server ships in the optional `mcp` extra — see [[Installation]]:

```bash
# Global install
pip install "loyverse_sdk[mcp]"

# uv-managed project
uv add "loyverse_sdk[mcp]"
```

## Client setup

`loyverse-mcp` communicates over stdio. How you reference it in a client config
depends on how it's installed:

**Globally installed** — the script is on your `PATH`:

```json
"command": "loyverse-mcp"
```

**uv-managed project** — use `uv run` (works anywhere inside the project):

```json
"command": "uv",
"args": ["run", "loyverse-mcp"]
```

**uv-managed project (explicit venv path)** — point straight at the virtualenv:

```json
"command": "/path/to/project/.venv/bin/loyverse-mcp"
```

## Claude Desktop

Add the server to `~/.config/claude/claude_desktop_config.json` (macOS:
`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "loyverse": {
      "command": "uv",
      "args": ["run", "loyverse-mcp"],
      "env": {
        "LOYVERSE_API_TOKEN": "your_api_token_here",
        "LOYVERSE_DB_PATH": "loyverse.db"
      }
    }
  }
}
```

If you installed globally, replace `command` with `"loyverse-mcp"` and drop
`args`. The token and database path follow the same rules as the rest of the SDK
— see [[Configuration]]. Restart Claude Desktop; a hammer icon in the chat
toolbar confirms the tools loaded.

## Available tools

The server registers **18 read-only tools**:

| Tool | Description |
|---|---|
| `loyverse_list_receipts` | List sales receipts with date, store, and receipt-number filters |
| `loyverse_get_receipt` | Retrieve a single receipt by UUID |
| `loyverse_list_items` | List catalog items, filterable by store, category, or IDs |
| `loyverse_get_item` | Retrieve a single item by UUID |
| `loyverse_list_customers` | List customers, searchable by email or IDs |
| `loyverse_get_customer` | Retrieve a single customer by UUID |
| `loyverse_list_categories` | List all item categories |
| `loyverse_get_category` | Retrieve a single category by UUID |
| `loyverse_list_employees` | List all employees |
| `loyverse_get_employee` | Retrieve a single employee by UUID |
| `loyverse_list_shifts` | List employee work shifts |
| `loyverse_get_shift` | Retrieve a single shift by UUID |
| `loyverse_list_stores` | List all store locations |
| `loyverse_get_store` | Retrieve a single store by UUID |
| `loyverse_list_inventory` | List inventory levels, filterable by store or variant |
| `loyverse_list_payment_types` | List configured payment methods |
| `loyverse_get_payment_type` | Retrieve a single payment type by ID |
| `loyverse_get_merchant` | Retrieve the merchant account profile |

All list tools support cursor-based pagination via `limit` and `cursor`, and most
support date-range filtering (`created_at_min`, `created_at_max`,
`updated_at_min`, `updated_at_max`).

## Example prompts

Once connected, you can ask the LLM things like:

```
"Show me all receipts from this week"
"Which items are in the Drinks category?"
"How many customers do we have?"
"What payment methods are configured?"
"List all stores and their details"
"Find receipts from store <UUID> in January 2024"
"Get the details for receipt R-1042"
"Show me the current inventory for store <UUID>"
```

The client calls the appropriate tools, paginates through results as needed, and
summarizes the data in plain language.

## Running standalone

You can run the server outside Claude Desktop — to connect another MCP client or
to test it:

```bash
LOYVERSE_API_TOKEN=your_token loyverse-mcp
```

To enable analytics-backed tools, also point it at a database:

```bash
LOYVERSE_API_TOKEN=your_token LOYVERSE_DB_PATH=loyverse.db loyverse-mcp
```

Or run it as a Python module:

```bash
LOYVERSE_API_TOKEN=your_token python -m loyverse_sdk.mcp
```

The server speaks the MCP protocol over stdio.

## See also

- [[Installation]] — install the `[mcp]` extra
- [[Configuration]] — the API token and `LOYVERSE_DB_PATH` the server reads
- [[CLI]] — the same data from the terminal (`loyverse api ...`)
- [[DuckDB-Export]] — build the database the analytics tools query
- [[Endpoints]] — the underlying resources the tools expose

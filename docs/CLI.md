# CLI

The `loyverse` command gives you terminal access to the API without writing
Python. Install the package (see [[Installation]]) and run `loyverse init` once
to store your token (see [[Configuration]]).

```
loyverse
├── init                 Set up config directory, API token, and database
├── api                  Send API requests to the Loyverse server
│   ├── list             List records for a resource
│   ├── get              Retrieve a single record by ID
│   ├── create           Create a record
│   ├── update           Update a record by ID
│   ├── delete           Delete a record by ID
│   └── endpoints        Show available resources
├── export               Export API data to a local DuckDB database
└── analytics            Business analytics on exported data
    ├── revenue          products      customers   employees
    └── operations       profitability inventory   time-series
```

> **Note:** the resource commands live under the **`api`** subgroup —
> e.g. `loyverse api list customers`, not `loyverse list customers`.

Run any command with `--help` for its full options.

## Setup

```bash
loyverse init                       # interactive prompts
loyverse init -t YOUR_TOKEN -d mydata.duckdb   # skip prompts with flags
```

See [[Configuration]] for the config directory, env file, and resolution order.

## `loyverse api` — resource operations

```bash
# List (supports output formats and filters)
loyverse api list customers --limit 10
loyverse api list receipts --created-at-min 2024-01-01 --format table
loyverse api list customers --format csv > customers.csv

# Retrieve a single record
loyverse api get customers <ID>
loyverse api get receipts <ID> --format table

# Create
loyverse api create categories --name "Drinks" --color GREEN
loyverse api create customers --name "Jane" --email jane@acme.com

# Update and delete
loyverse api update categories <ID> --name "New Name"
loyverse api delete categories <ID> --yes

# Discover resources and their required/optional fields
loyverse api endpoints
```

`list`, `create`, and `update` accept resource-specific options as
`--field value` pairs; run `loyverse api endpoints` to see which fields each
resource supports. Output formats include `table` (default for terminals),
`json`, and `csv`.

## `loyverse export` — DuckDB export

The `export` command syncs **incrementally by default** (only records changed
since the last run); use `--force`/`-f` for a full re-export. The database path
is optional and defaults to `LOYVERSE_DB_PATH` (or `loyverse.db`).

```bash
loyverse export                              # incremental sync, default DB
loyverse export --force                      # full re-export
loyverse export mydata.duckdb --resource receipts
loyverse export --created-at-min 2024-01-01  # date-bounded full export
```

Full details, options, and the resulting schema are in [[DuckDB-Export]].

## `loyverse analytics` — business analytics

Runs SQL analytics over the exported DuckDB warehouse. No `--db-path` is needed
if `LOYVERSE_DB_PATH` is set.

```bash
loyverse analytics revenue --days 30
loyverse analytics revenue --by-month --days 365
loyverse analytics products --top-n 10
loyverse analytics customers --rfm
loyverse analytics operations --payments
loyverse analytics profitability --margins
loyverse analytics inventory --low-stock
loyverse analytics time-series --monthly
```

Every analytics command also has a Python equivalent — see [[Analytics]] for the
full `AnalyticsEngine` API and the complete list of metrics. Most commands accept
`--format json` / `--format csv` for piping into other tools.

## See also

- [[Configuration]] — token and database setup the CLI relies on
- [[DuckDB-Export]] — what `loyverse export` produces
- [[Analytics]] — the metrics behind `loyverse analytics`
- [[Endpoints]] — the Python equivalent of `loyverse api ...`
- [[MCP-Server]] — expose the same data to LLM clients

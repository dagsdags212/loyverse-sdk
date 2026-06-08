# Configuration

Configuration lives in `~/.loyverse` by default, so the CLI and SDK work from
any directory without you exporting environment variables. The quickest way to
set everything up is `loyverse init`.

## `loyverse init`

Run the interactive setup once after [[Installation]]. It prompts for the config
directory (default `~/.loyverse`), your Loyverse API token, and a database name
(default `loyverse.db`):

```bash
loyverse init
```

Supply any value as a flag to skip its prompt — handy for scripts:

```bash
loyverse init --config-dir ~/work/loyverse \   # -c  where config + databases live
              --api-token YOUR_TOKEN \          # -t  your Loyverse API key
              --db-path mydata.duckdb           # -d  database name (or a path)
```

| Flag | Short | Default | Meaning |
|---|---|---|---|
| `--config-dir` | `-c` | `~/.loyverse` | Where config and databases live |
| `--api-token` | `-t` | _(prompted)_ | Your Loyverse API key |
| `--db-path` | `-d` | `loyverse.db` | Database name or an explicit path |

`init` writes `<config-dir>/.loyverse.env`. If you pick a non-default config
directory, the location is recorded in a small pointer file
(`~/.config/loyverse/config_dir`) so every later command finds it automatically
— no environment variable to export.

## Directory layout

```
~/.loyverse/
├── .loyverse.env       # API token and settings
└── db/
    └── loyverse.db     # exported DuckDB database(s)
```

## The `.loyverse.env` file

You can edit the env file directly instead of re-running `init`:

```env
LOYVERSE_API_TOKEN=your_api_token
LOYVERSE_DB_PATH=loyverse.db                 # optional, defaults to loyverse.db
```

| Variable | Purpose |
|---|---|
| `LOYVERSE_API_TOKEN` | The token used to authenticate every API call |
| `LOYVERSE_DB_PATH` | Default database for `export` and `analytics` |

Environment variables set in your shell still take precedence over values in the
env file.

## Config-directory resolution

The config directory is resolved in this order:

1. The `LOYVERSE_CONFIG_DIR` environment variable
2. The pointer file written by `init` (`~/.config/loyverse/config_dir`)
3. The default `~/.loyverse`

## Database-path resolution

`LOYVERSE_DB_PATH` (and the `--db-path` argument) accept either:

- a **bare name** — e.g. `loyverse.db` — which is stored under `<config-dir>/db/`, or
- an **explicit path** (absolute, or one containing a directory) — which is used as-is.

## Migrating from an older version

> If a `.env` exists in your working directory and `~/.loyverse` does not yet
> exist, its values are copied into `~/.loyverse/.loyverse.env` automatically on
> first run.

## See also

- [[Installation]] — install the package and console scripts
- [[Quickstart]] — make your first call once configured
- [[CLI]] — the commands that read this configuration
- [[Client]] — how the SDK picks up your token
- [[MCP-Server]] — passing the token and DB path to LLM clients

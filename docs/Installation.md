# Installation

The Loyverse SDK is a Python package that ships the `loyverse` CLI, the
`loyverse-mcp` server, and the `LoyverseClient` library. It targets
**Python 3.12+**.

## Install the core SDK

```bash
# pip
pip install loyverse_sdk

# uv — add as a project dependency
uv add loyverse_sdk
```

That gives you the client, the endpoints, the export tools, and the `loyverse`
CLI.

## Install with the MCP server

The `loyverse-mcp` server lives behind the optional `[mcp]` extra. Add it when
you want to expose your POS data to LLM clients (see [[MCP-Server]]):

```bash
# pip
pip install "loyverse_sdk[mcp]"

# uv
uv add "loyverse_sdk[mcp]"
```

## Install from GitHub

To install the latest unreleased code (or a fork):

```bash
pip install git+https://github.com/dagsdags212/loyverse_sdk.git
```

## What you get

After installation two console scripts are on your PATH:

| Command | Purpose |
|---|---|
| `loyverse` | The command-line interface — see [[CLI]] |
| `loyverse-mcp` | The MCP stdio server (requires the `[mcp]` extra) — see [[MCP-Server]] |

## Next steps

Run `loyverse init` once to store your API token and database location, then
make your first call. See [[Configuration]] and [[Quickstart]].

## See also

- [[Configuration]] — set up your API token and config directory
- [[Quickstart]] — your first call in Python and from the CLI
- [[MCP-Server]] — what the `[mcp]` extra unlocks
- [[Development]] — install from source for contributing

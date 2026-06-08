# Loyverse SDK Wiki

Asynchronous Python SDK, command-line interface, and MCP server for the
[Loyverse API](https://developer.loyverse.com/docs/) — a point-of-sale (POS)
platform for managing sales, inventory, and customers.

This wiki is organized by theme. New here? Follow **Getting Started** in order,
then dip into the **Python SDK** and **Export & Analytics** sections as needed.

## Getting Started

- [[Installation]] — install the SDK, the MCP extra, or from source
- [[Configuration]] — `loyverse init`, the `~/.loyverse` config directory, and environment variables
- [[Quickstart]] — your first API call in Python and from the CLI

## Python SDK

- [[Client]] — the `LoyverseClient`: construction, authentication, and lifecycle
- [[Endpoints]] — the 16 resource endpoints and the CRUD + pagination pattern
- [[Query-Models]] — filter, paginate, and validate list requests
- [[Models]] — the Pydantic response models and list-response shape
- [[Helpers]] — convenience functions for common receipt workflows
- [[Error-Handling]] — the exception hierarchy and how to handle failures

## Export & Analytics

- [[DuckDB-Export]] — build a local relational warehouse for SQL analytics
- [[Flat-File-Export]] — write query results directly to CSV or Parquet
- [[Analytics]] — the analytics engine (Python API) and `loyverse analytics` CLI

## Tools

- [[CLI]] — the full `loyverse` command-line reference
- [[MCP-Server]] — expose your POS data to LLM clients with `loyverse-mcp`

## Project

- [[Development]] — set up the project, run the test suite, and contribute

---

## At a glance

| Capability | Entry point | Page |
|---|---|---|
| Call the API | `LoyverseClient().customers.list()` | [[Endpoints]] |
| Filter & paginate | `CustomerListQuery(...)` | [[Query-Models]] |
| Export to a database | `client.export_to_duckdb(...)` | [[DuckDB-Export]] |
| Export to files | `client.export_to_csv(...)` | [[Flat-File-Export]] |
| Analyze the warehouse | `AnalyticsEngine(db).revenue.daily_revenue()` | [[Analytics]] |
| Work from the terminal | `loyverse api list customers` | [[CLI]] |
| Connect an LLM | `loyverse-mcp` | [[MCP-Server]] |

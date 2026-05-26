# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-05-27

### Added
- **Flat-file export (CSV + Parquet)** — `FlatFileExporter` class in new `loyverse_sdk.exporters` package for writing Pydantic model instances directly to CSV and Parquet files using Polars
- **`export_csv()` and `export_parquet()`** — Module-level convenience functions for one-shot flat-file exports without instantiating an exporter
- **`LoyverseClient.export_to_csv()` and `export_to_parquet()`** — Client convenience methods that delegate to the exporters package with lazy Polars import
- **`examples/export_flat_files.py`** — End-to-end example demonstrating query→filter→export workflows (customers by date range → CSV, all items → Parquet, latest receipts → CSV)
- **21 new unit and integration tests** — 17 exporter tests (CSV headers, Parquet type preservation, empty input handling, invalid paths) + 4 client delegation tests

## [0.2.0] - 2025-05-27

### Added
- **Typed query models for all list endpoints** — 15 `FooListQuery` classes (e.g. `CustomerListQuery`, `ReceiptListQuery`, `InventoryListQuery`) each with endpoint-specific filter fields and validation
- **`BaseListQuery`** — Base class providing `limit` (1–250), `cursor`, `created_at_min/max`, `updated_at_min/max` with `model_validator` enforcing `min <= max` date ranges and `limit` bounds
- **`to_params()` serialization** — All query models expose `to_params()` which serializes datetime fields to ISO 8601 strings and excludes `None` values; `show_deleted` serializes as lowercase `"true"` string for API compatibility
- **Webhook query model** — `WebhookListQuery` with typed `type` (`WebhookType` enum) and `status` (`WebhookStatus` enum) fields that serialize to their `.value` strings; `merchant_id` maps to `merchant_it` per Loyverse API spec
- **84 new unit tests** covering all query model classes, `BaseListQuery` validators, and `to_params()` serialization

### Changed
- **All 14 list endpoint signatures** — `list(query: FooListQuery | None = None)` and `iter_all(query: FooListQuery | None = None)` replace the previous `list(limit=..., cursor=..., **kwargs)` pattern; endpoints with endpoint-specific filters (inventory, receipts, customers, items) no longer need manual `params` dict building
- **`ListMixin.list()`** — Now accepts `model` + `**params` instead of hardcoded `limit`/`cursor` kwargs; params passed directly to `_get()`
- **`PaginationMixin.list_paginated()` and `iter_all()`** — No longer hardcode `created_at_min/max`/`updated_at_min/max`; accept `**params` and pass through to `_get()`; datetime standardization now handled at query model call site via `to_params()`
- **Endpoint-specific filter fields** — Store ID, variant IDs, receipt number ranges, order direction, and all ID-filter parameters now live on their respective query models instead of being manually forwarded via kwargs in endpoint methods

### Fixed
- **`PaginationMixin.iter_all()`** — Previously hardcoded date filters meant `DuckDBExporter.export_resource()` passed `created_at_min/max` to endpoints that don't support them (e.g. `pos_devices`); now all params flow from query model so only relevant fields reach each endpoint

## [0.1.0] - 2025-05-26

### Added
- **16 API endpoints**: categories, customers, discounts, devices, employees, inventory, items, merchant, modifiers, receipts, shifts, stores, suppliers, taxes, variants, webhooks
- Async/await interface using httpx for non-blocking API calls
- Pydantic models for type-safe request/response validation
- Cursor-based pagination with `iter_all()` async generator
- Full CRUD operations for all supported endpoints
- DuckDB export pipeline with 15 main tables, 8 junction tables, and 2 child tables
- Streaming export with batch inserts, progress tracking, and UPSERT support
- Timezone-aware datetime conversion (UTC to local via pytz)
- UUID serialization for consistent ID handling across models
- Custom exception hierarchy for error handling

### Fixed
- Inventory endpoint filter parameters (store_id, variant_ids)
- Items and Modifiers endpoints now correctly inherit update mixin
- MerchantEndpoint.retrieve for singleton resource handling
- Tax model duplicate name field removed
- Receipt model surcharge typo corrected
- FK constraint violations in batch insert tests

### Changed
- Default page limit of 250 for API pagination
- Replaced bare `except Exception` blocks with specific exception types

### Removed
- Dead code: convert_response, use_model utils, db/schemas.py, core/logging.py
- Orphaned models and duplicate test files

## [0.0.0] - 2025-02-14

### Added
- Initial project setup with LoyverseClient class
- Auth class for API token handling
- Config class with environment variable support
- Custom exceptions for API and SDK errors

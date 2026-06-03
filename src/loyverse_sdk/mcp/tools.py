"""Read-only MCP tools that wrap Loyverse SDK list and retrieve endpoints."""

import json
from typing import Optional

from mcp.server.fastmcp import Context
from pydantic import BaseModel, ConfigDict, Field

from loyverse_sdk.exceptions import LoyverseSDKError
from loyverse_sdk.mcp.db_queries import get_from_db, is_db_fresh, list_from_db
from loyverse_sdk.models import (
    CategoryListQuery,
    CustomerListQuery,
    EmployeeListQuery,
    InventoryListQuery,
    ItemListQuery,
    PaymentTypeListQuery,
    ReceiptListQuery,
    ShiftListQuery,
    StoreListQuery,
)
from loyverse_sdk.mcp.server import mcp


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_BASE_PARAM_KEYS = frozenset(
    {"limit", "cursor", "created_at_min", "created_at_max", "updated_at_min", "updated_at_max"}
)


def _client(ctx: Context):
    return ctx.request_context.lifespan_context["client"]


def _db_path(ctx: Context) -> str | None:
    return ctx.request_context.lifespan_context.get("db_path")


def _json(obj) -> str:
    return json.dumps(obj, indent=2, default=str)


def _serialize_list(response) -> str:
    data = response.model_dump(mode="json")
    data["count"] = len(data.get("items", []))
    return _json(data)


def _handle_error(e: Exception) -> str:
    if isinstance(e, LoyverseSDKError):
        return f"Error: {e}"
    return f"Error: Unexpected error — {type(e).__name__}: {e}"


def _try_db_list(ctx: Context, table: str, params: BaseModel) -> str | None:
    """Attempt to serve a list request from the local DuckDB.

    Returns a JSON string on success, or None to fall through to the API.
    Skips the DB when resource-specific filters are present.
    """
    dbp = _db_path(ctx)
    if not dbp or not is_db_fresh(dbp):
        return None
    raw = params.model_dump(exclude_none=True)
    if any(k not in _BASE_PARAM_KEYS for k in raw):
        return None
    return list_from_db(
        dbp,
        table,
        limit=raw.get("limit", 50),
        created_at_min=raw.get("created_at_min"),
        created_at_max=raw.get("created_at_max"),
        updated_at_min=raw.get("updated_at_min"),
        updated_at_max=raw.get("updated_at_max"),
    )


def _try_db_get(ctx: Context, table: str, resource_id: str) -> str | None:
    """Attempt to retrieve a single record from the local DuckDB.

    Returns a JSON string on success, or None to fall through to the API.
    """
    dbp = _db_path(ctx)
    if not dbp or not is_db_fresh(dbp):
        return None
    return get_from_db(dbp, table, resource_id)


# ---------------------------------------------------------------------------
# Shared base input model
# ---------------------------------------------------------------------------


class _BaseListInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    limit: Optional[int] = Field(
        default=50, ge=1, le=250, description="Number of records to return (1–250)"
    )
    cursor: Optional[str] = Field(
        default=None, description="Pagination cursor from a previous response"
    )
    created_at_min: Optional[str] = Field(
        default=None,
        description="ISO 8601 lower bound on created_at, e.g. 2024-01-01T00:00:00Z",
    )
    created_at_max: Optional[str] = Field(
        default=None, description="ISO 8601 upper bound on created_at"
    )
    updated_at_min: Optional[str] = Field(
        default=None, description="ISO 8601 lower bound on updated_at"
    )
    updated_at_max: Optional[str] = Field(
        default=None, description="ISO 8601 upper bound on updated_at"
    )


def _base_params(params: _BaseListInput) -> dict:
    return params.model_dump(exclude_none=True)


# ---------------------------------------------------------------------------
# Receipts
# ---------------------------------------------------------------------------


class ListReceiptsInput(_BaseListInput):
    receipt_numbers: Optional[str] = Field(
        default=None,
        description="Comma-separated receipt numbers to fetch, e.g. 'R-1001,R-1002'",
    )
    since_receipt_number: Optional[str] = Field(
        default=None, description="Return receipts with receipt_number > this value"
    )
    before_receipt_number: Optional[str] = Field(
        default=None, description="Return receipts with receipt_number < this value"
    )
    store_id: Optional[str] = Field(
        default=None, description="UUID of the store to filter receipts by"
    )
    sort_order: Optional[str] = Field(
        default=None, description="Sort direction: 'asc' or 'desc'"
    )


class GetReceiptInput(BaseModel):
    receipt_id: str = Field(description="UUID of the receipt to retrieve")


@mcp.tool(
    name="loyverse_list_receipts",
    annotations={
        "title": "List Loyverse Receipts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_list_receipts(params: ListReceiptsInput, ctx: Context) -> str:
    """List sales receipts from the Loyverse POS, with optional date, store, and receipt-number filters.

    Supports cursor-based pagination via the returned `next_cursor` field.

    Args:
        params (ListReceiptsInput): Filter and pagination options.

    Returns:
        str: JSON with keys `items` (list of receipts), `next_cursor`, and `count`.

    Error response:
        "Error: <message>" on API or configuration failures.
    """
    db_result = _try_db_list(ctx, "receipts", params)
    if db_result is not None:
        return db_result
    try:
        query = ReceiptListQuery(**_base_params(params))
        response = await _client(ctx).receipts.list(query)
        return _serialize_list(response)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_get_receipt",
    annotations={
        "title": "Get Loyverse Receipt",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_get_receipt(params: GetReceiptInput, ctx: Context) -> str:
    """Retrieve a single receipt by its UUID.

    Args:
        params (GetReceiptInput): Receipt UUID.

    Returns:
        str: JSON representation of the receipt.

    Error response:
        "Error: <message>" on not-found or API failures.
    """
    db_result = _try_db_get(ctx, "receipts", params.receipt_id)
    if db_result is not None:
        return db_result
    try:
        receipt = await _client(ctx).receipts.retrieve(params.receipt_id)
        return _json(receipt.model_dump(mode="json"))
    except Exception as e:
        return _handle_error(e)


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------


class ListItemsInput(_BaseListInput):
    item_ids: Optional[str] = Field(
        default=None, description="Comma-separated item UUIDs to fetch"
    )
    store_id: Optional[str] = Field(
        default=None, description="UUID of the store to filter items by"
    )
    category_id: Optional[str] = Field(
        default=None, description="UUID of the category to filter items by"
    )
    show_deleted: Optional[bool] = Field(
        default=False, description="Include soft-deleted items"
    )


class GetItemInput(BaseModel):
    item_id: str = Field(description="UUID of the item to retrieve")


@mcp.tool(
    name="loyverse_list_items",
    annotations={
        "title": "List Loyverse Items",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_list_items(params: ListItemsInput, ctx: Context) -> str:
    """List menu/product items from the Loyverse catalog.

    Filterable by store, category, or specific item IDs. Supports cursor pagination.

    Args:
        params (ListItemsInput): Filter and pagination options.

    Returns:
        str: JSON with keys `items`, `next_cursor`, and `count`.
    """
    db_result = _try_db_list(ctx, "items", params)
    if db_result is not None:
        return db_result
    try:
        query = ItemListQuery(**_base_params(params))
        response = await _client(ctx).items.list(query)
        return _serialize_list(response)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_get_item",
    annotations={
        "title": "Get Loyverse Item",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_get_item(params: GetItemInput, ctx: Context) -> str:
    """Retrieve a single catalog item by its UUID.

    Args:
        params (GetItemInput): Item UUID.

    Returns:
        str: JSON representation of the item.
    """
    db_result = _try_db_get(ctx, "items", params.item_id)
    if db_result is not None:
        return db_result
    try:
        item = await _client(ctx).items.retrieve(params.item_id)
        return _json(item.model_dump(mode="json"))
    except Exception as e:
        return _handle_error(e)


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------


class ListCustomersInput(_BaseListInput):
    customer_ids: Optional[str] = Field(
        default=None, description="Comma-separated customer UUIDs to fetch"
    )
    email: Optional[str] = Field(
        default=None, description="Filter by exact customer email address"
    )


class GetCustomerInput(BaseModel):
    customer_id: str = Field(description="UUID of the customer to retrieve")


@mcp.tool(
    name="loyverse_list_customers",
    annotations={
        "title": "List Loyverse Customers",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_list_customers(params: ListCustomersInput, ctx: Context) -> str:
    """List customers registered in the Loyverse loyalty program.

    Searchable by email or specific customer IDs. Supports cursor pagination.

    Args:
        params (ListCustomersInput): Filter and pagination options.

    Returns:
        str: JSON with keys `items`, `next_cursor`, and `count`.
    """
    db_result = _try_db_list(ctx, "customers", params)
    if db_result is not None:
        return db_result
    try:
        query = CustomerListQuery(**_base_params(params))
        response = await _client(ctx).customers.list(query)
        return _serialize_list(response)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_get_customer",
    annotations={
        "title": "Get Loyverse Customer",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_get_customer(params: GetCustomerInput, ctx: Context) -> str:
    """Retrieve a single customer by their UUID.

    Args:
        params (GetCustomerInput): Customer UUID.

    Returns:
        str: JSON representation of the customer.
    """
    db_result = _try_db_get(ctx, "customers", params.customer_id)
    if db_result is not None:
        return db_result
    try:
        customer = await _client(ctx).customers.retrieve(params.customer_id)
        return _json(customer.model_dump(mode="json"))
    except Exception as e:
        return _handle_error(e)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


class GetCategoryInput(BaseModel):
    category_id: str = Field(description="UUID of the category to retrieve")


@mcp.tool(
    name="loyverse_list_categories",
    annotations={
        "title": "List Loyverse Categories",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_list_categories(params: _BaseListInput, ctx: Context) -> str:
    """List all item categories in the Loyverse catalog.

    Args:
        params (_BaseListInput): Pagination and date-range options.

    Returns:
        str: JSON with keys `items`, `next_cursor`, and `count`.
    """
    db_result = _try_db_list(ctx, "categories", params)
    if db_result is not None:
        return db_result
    try:
        query = CategoryListQuery(**_base_params(params))
        response = await _client(ctx).categories.list(query)
        return _serialize_list(response)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_get_category",
    annotations={
        "title": "Get Loyverse Category",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_get_category(params: GetCategoryInput, ctx: Context) -> str:
    """Retrieve a single item category by its UUID.

    Args:
        params (GetCategoryInput): Category UUID.

    Returns:
        str: JSON representation of the category.
    """
    db_result = _try_db_get(ctx, "categories", params.category_id)
    if db_result is not None:
        return db_result
    try:
        category = await _client(ctx).categories.retrieve(params.category_id)
        return _json(category.model_dump(mode="json"))
    except Exception as e:
        return _handle_error(e)


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------


class GetEmployeeInput(BaseModel):
    employee_id: str = Field(description="UUID of the employee to retrieve")


@mcp.tool(
    name="loyverse_list_employees",
    annotations={
        "title": "List Loyverse Employees",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_list_employees(params: _BaseListInput, ctx: Context) -> str:
    """List all employees configured in Loyverse.

    Args:
        params (_BaseListInput): Pagination and date-range options.

    Returns:
        str: JSON with keys `items`, `next_cursor`, and `count`.
    """
    db_result = _try_db_list(ctx, "employees", params)
    if db_result is not None:
        return db_result
    try:
        query = EmployeeListQuery(**_base_params(params))
        response = await _client(ctx).employees.list(query)
        return _serialize_list(response)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_get_employee",
    annotations={
        "title": "Get Loyverse Employee",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_get_employee(params: GetEmployeeInput, ctx: Context) -> str:
    """Retrieve a single employee record by their UUID.

    Args:
        params (GetEmployeeInput): Employee UUID.

    Returns:
        str: JSON representation of the employee.
    """
    db_result = _try_db_get(ctx, "employees", params.employee_id)
    if db_result is not None:
        return db_result
    try:
        employee = await _client(ctx).employees.retrieve(params.employee_id)
        return _json(employee.model_dump(mode="json"))
    except Exception as e:
        return _handle_error(e)


# ---------------------------------------------------------------------------
# Shifts
# ---------------------------------------------------------------------------


class GetShiftInput(BaseModel):
    shift_id: str = Field(description="UUID of the shift to retrieve")


@mcp.tool(
    name="loyverse_list_shifts",
    annotations={
        "title": "List Loyverse Shifts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_list_shifts(params: _BaseListInput, ctx: Context) -> str:
    """List employee work shifts recorded in Loyverse POS.

    Each shift includes cash movements, payments, and sales totals.

    Args:
        params (_BaseListInput): Pagination and date-range options.

    Returns:
        str: JSON with keys `items`, `next_cursor`, and `count`.
    """
    db_result = _try_db_list(ctx, "shifts", params)
    if db_result is not None:
        return db_result
    try:
        query = ShiftListQuery(**_base_params(params))
        response = await _client(ctx).shifts.list(query)
        data = response.model_dump(mode="json")
        normalized = {
            "items": data.get("shifts", []),
            "count": len(data.get("shifts", [])),
        }
        return _json(normalized)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_get_shift",
    annotations={
        "title": "Get Loyverse Shift",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_get_shift(params: GetShiftInput, ctx: Context) -> str:
    """Retrieve a single employee work shift by its UUID.

    Args:
        params (GetShiftInput): Shift UUID.

    Returns:
        str: JSON representation of the shift including cash movements and payment summaries.
    """
    db_result = _try_db_get(ctx, "shifts", params.shift_id)
    if db_result is not None:
        return db_result
    try:
        shift = await _client(ctx).shifts.retrieve(params.shift_id)
        return _json(shift.model_dump(mode="json"))
    except Exception as e:
        return _handle_error(e)


# ---------------------------------------------------------------------------
# Stores
# ---------------------------------------------------------------------------


class GetStoreInput(BaseModel):
    store_id: str = Field(description="UUID of the store to retrieve")


@mcp.tool(
    name="loyverse_list_stores",
    annotations={
        "title": "List Loyverse Stores",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_list_stores(params: _BaseListInput, ctx: Context) -> str:
    """List all physical store locations configured in Loyverse.

    Args:
        params (_BaseListInput): Pagination and date-range options.

    Returns:
        str: JSON with keys `items`, `next_cursor`, and `count`.
    """
    db_result = _try_db_list(ctx, "stores", params)
    if db_result is not None:
        return db_result
    try:
        query = StoreListQuery(**_base_params(params))
        response = await _client(ctx).stores.list(query)
        return _serialize_list(response)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_get_store",
    annotations={
        "title": "Get Loyverse Store",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_get_store(params: GetStoreInput, ctx: Context) -> str:
    """Retrieve a single store location by its UUID.

    Args:
        params (GetStoreInput): Store UUID.

    Returns:
        str: JSON representation of the store.
    """
    db_result = _try_db_get(ctx, "stores", params.store_id)
    if db_result is not None:
        return db_result
    try:
        store = await _client(ctx).stores.retrieve(params.store_id)
        return _json(store.model_dump(mode="json"))
    except Exception as e:
        return _handle_error(e)


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


class ListInventoryInput(_BaseListInput):
    store_ids: Optional[str] = Field(
        default=None, description="Comma-separated store UUIDs to filter inventory by"
    )
    variant_ids: Optional[str] = Field(
        default=None, description="Comma-separated variant UUIDs to filter inventory by"
    )


@mcp.tool(
    name="loyverse_list_inventory",
    annotations={
        "title": "List Loyverse Inventory",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_list_inventory(params: ListInventoryInput, ctx: Context) -> str:
    """List current inventory levels across stores and variants.

    Filterable by store or specific variant IDs.

    Args:
        params (ListInventoryInput): Filter and pagination options.

    Returns:
        str: JSON with keys `items`, `next_cursor`, and `count`.
    """
    db_result = _try_db_list(ctx, "inventory", params)
    if db_result is not None:
        return db_result
    try:
        query = InventoryListQuery(**_base_params(params))
        response = await _client(ctx).inventory.list(query)
        return _serialize_list(response)
    except Exception as e:
        return _handle_error(e)


# ---------------------------------------------------------------------------
# Payment Types
# ---------------------------------------------------------------------------


class ListPaymentTypesInput(_BaseListInput):
    payment_type_ids: Optional[str] = Field(
        default=None, description="Comma-separated payment type IDs to fetch"
    )
    show_deleted: Optional[bool] = Field(
        default=False, description="Include soft-deleted payment types"
    )


class GetPaymentTypeInput(BaseModel):
    payment_type_id: str = Field(description="ID of the payment type to retrieve")


@mcp.tool(
    name="loyverse_list_payment_types",
    annotations={
        "title": "List Loyverse Payment Types",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_list_payment_types(
    params: ListPaymentTypesInput, ctx: Context
) -> str:
    """List payment methods configured in Loyverse (cash, card, etc.).

    Args:
        params (ListPaymentTypesInput): Filter and pagination options.

    Returns:
        str: JSON with keys `items`, `next_cursor`, and `count`.
    """
    db_result = _try_db_list(ctx, "payment_types", params)
    if db_result is not None:
        return db_result
    try:
        query = PaymentTypeListQuery(**_base_params(params))
        response = await _client(ctx).payment_types.list(query)
        return _serialize_list(response)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_get_payment_type",
    annotations={
        "title": "Get Loyverse Payment Type",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_get_payment_type(params: GetPaymentTypeInput, ctx: Context) -> str:
    """Retrieve a single payment type by its ID.

    Args:
        params (GetPaymentTypeInput): Payment type ID.

    Returns:
        str: JSON representation of the payment type.
    """
    db_result = _try_db_get(ctx, "payment_types", params.payment_type_id)
    if db_result is not None:
        return db_result
    try:
        pt = await _client(ctx).payment_types.retrieve(params.payment_type_id)
        return _json(pt.model_dump(mode="json"))
    except Exception as e:
        return _handle_error(e)


# ---------------------------------------------------------------------------
# Merchant
# ---------------------------------------------------------------------------


@mcp.tool(
    name="loyverse_get_merchant",
    annotations={
        "title": "Get Loyverse Merchant",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_get_merchant(ctx: Context) -> str:
    """Retrieve the merchant account profile for the authenticated Loyverse account.

    Returns:
        str: JSON representation of the merchant including business name, address, and currency.
    """
    try:
        merchant = await _client(ctx).merchant.retrieve()
        return _json(merchant.model_dump(mode="json"))
    except Exception as e:
        return _handle_error(e)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


def _engine(ctx: Context):
    engine = ctx.request_context.lifespan_context.get("engine")
    if engine is None:
        raise RuntimeError(
            "Analytics engine is not available. "
            "Export data first with `loyverse export` "
            "and set LOYVERSE_DB_PATH to the database path "
            "(defaults to loyverse.db)."
        )
    return engine


def _format_analytics(df) -> str:
    return df if isinstance(df, str) else _json(df.to_dicts())


class _AnalyticsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Number of past days to analyze (1–365, default 30)",
    )
    store_id: Optional[str] = Field(
        default=None,
        description="Optional store UUID to filter by",
    )
    date_start: Optional[str] = Field(
        default=None,
        description="Optional ISO-8601 start date, e.g. 2024-01-01",
    )
    date_end: Optional[str] = Field(
        default=None,
        description="Optional ISO-8601 end date, e.g. 2024-12-31",
    )
    by_month: bool = Field(
        default=False,
        description="Aggregate results by month instead of returning a single total",
    )


@mcp.tool(
    name="loyverse_analytics_daily_revenue",
    annotations={
        "title": "Daily Revenue Analytics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_analytics_daily_revenue(
    params: _AnalyticsInput, ctx: Context
) -> str:
    """Daily revenue, transaction count, and average ticket.

    Returns a table with one row per calendar day showing total revenue,
    number of transactions, and average transaction value.

    Args:
        params (_AnalyticsInput): days (default 30), optional store_id, date range.

    Returns:
        str: JSON array of daily records with keys date, revenue, tx_count, avg_ticket.
    """
    try:
        engine = _engine(ctx)
        result = engine.revenue.daily_revenue(
            days=params.days,
            store_id=params.store_id,
            date_start=params.date_start,
            date_end=params.date_end,
            fmt="json",
        )
        return result
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_analytics_total_revenue",
    annotations={
        "title": "Total Revenue Analytics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_analytics_total_revenue(
    params: _AnalyticsInput, ctx: Context
) -> str:
    """Total revenue as a single value for the period, or aggregated by month.

    Args:
        params (_AnalyticsInput): days (default 30), optional store_id, date range,
            and by_month flag to break results down by month.

    Returns:
        str: JSON object with key 'total_revenue' containing the sum, or
             JSON array of monthly records with keys month, revenue, tx_count, avg_ticket
             when --by-month is set.
    """
    try:
        engine = _engine(ctx)
        if params.by_month:
            result = engine.revenue.total_revenue_by_month(
                days=params.days,
                store_id=params.store_id,
                date_start=params.date_start,
                date_end=params.date_end,
                fmt="json",
            )
            return result
        result = engine.revenue.total_revenue(
            days=params.days,
            store_id=params.store_id,
            date_start=params.date_start,
            date_end=params.date_end,
            fmt="json",
        )
        return result
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_analytics_revenue_by_store",
    annotations={
        "title": "Revenue by Store Analytics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_analytics_revenue_by_store(
    params: _AnalyticsInput, ctx: Context
) -> str:
    """Revenue and transaction count broken down by store location.

    Args:
        params (_AnalyticsInput): days (default 30), optional date range.

    Returns:
        str: JSON array with keys store_name, tx_count, revenue, avg_ticket.
    """
    try:
        engine = _engine(ctx)
        result = engine.revenue.revenue_by_store(
            days=params.days,
            date_start=params.date_start,
            date_end=params.date_end,
            fmt="json",
        )
        return result
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_analytics_top_items",
    annotations={
        "title": "Top-Selling Items Analytics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_analytics_top_items(params: _AnalyticsInput, ctx: Context) -> str:
    """Top N items by total revenue and quantity sold.

    Returns items ranked by revenue, showing quantity sold and transaction count.

    Args:
        params (_AnalyticsInput): days (default 30), optional store_id, date range.
            The limit field doubles as the top-N count here.

    Returns:
        str: JSON array with keys item, total_qty, total_revenue, tx_count.
    """
    try:
        engine = _engine(ctx)
        result = engine.products.top_items(
            days=params.days,
            store_id=params.store_id,
            date_start=params.date_start,
            date_end=params.date_end,
            n=10,
            fmt="json",
        )
        return result
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_analytics_revenue_by_category",
    annotations={
        "title": "Revenue by Category Analytics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_analytics_revenue_by_category(
    params: _AnalyticsInput, ctx: Context
) -> str:
    """Revenue breakdown by product category with percentage share.

    Shows how much each category contributes to total revenue.

    Args:
        params (_AnalyticsInput): days (default 30), optional store_id, date range.

    Returns:
        str: JSON array with keys category, tx_count, revenue, units_sold, pct_share.
    """
    try:
        engine = _engine(ctx)
        result = engine.products.revenue_by_category(
            days=params.days,
            store_id=params.store_id,
            date_start=params.date_start,
            date_end=params.date_end,
            fmt="json",
        )
        return result
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_analytics_rfm_analysis",
    annotations={
        "title": "RFM Customer Segmentation",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_analytics_rfm_analysis(ctx: Context) -> str:
    """RFM (Recency, Frequency, Monetary) customer segmentation.

    Scores every customer on 1–5 quintiles for recency, visit frequency,
    and total spend. Assigns segments like Champions, Loyal, At Risk, Lost.

    Returns:
        str: JSON array with keys customer_id, name, recency_days, frequency,
             monetary, r_score, f_score, m_score, segment.
    """
    try:
        engine = _engine(ctx)
        result = engine.customers.rfm_analysis(fmt="json")
        return result
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_analytics_top_customers",
    annotations={
        "title": "Top Customers by Spend",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_analytics_top_customers(
    params: _AnalyticsInput, ctx: Context
) -> str:
    """Top N customers ranked by total spend in the period.

    Args:
        params (_AnalyticsInput): days (default 30), optional store_id, date range.

    Returns:
        str: JSON array with keys customer_id, name, visits, total_spent, avg_ticket.
    """
    try:
        engine = _engine(ctx)
        result = engine.customers.top_customers(
            days=params.days,
            store_id=params.store_id,
            date_start=params.date_start,
            date_end=params.date_end,
            n=10,
            fmt="json",
        )
        return result
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_analytics_unique_customers",
    annotations={
        "title": "Unique Customer Count",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_analytics_unique_customers(
    params: _AnalyticsInput, ctx: Context
) -> str:
    """Count of distinct customers who made purchases in the period.

    Args:
        params (_AnalyticsInput): days (default 30), optional store_id, date range.

    Returns:
        str: JSON object with key 'unique_customers' containing the count.
    """
    try:
        engine = _engine(ctx)
        result = engine.customers.unique_customers(
            days=params.days,
            store_id=params.store_id,
            date_start=params.date_start,
            date_end=params.date_end,
            fmt="json",
        )
        return result
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_analytics_revenue_by_employee",
    annotations={
        "title": "Revenue by Employee Analytics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_analytics_revenue_by_employee(
    params: _AnalyticsInput, ctx: Context
) -> str:
    """Revenue, transaction count, and average ticket per employee.

    Args:
        params (_AnalyticsInput): days (default 30), optional store_id, date range.

    Returns:
        str: JSON array with keys employee, tx_count, revenue, avg_ticket, total_tips.
    """
    try:
        engine = _engine(ctx)
        result = engine.employees.revenue_by_employee(
            days=params.days,
            store_id=params.store_id,
            date_start=params.date_start,
            date_end=params.date_end,
            fmt="json",
        )
        return result
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_analytics_peak_hours",
    annotations={
        "title": "Peak Hours Analytics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_analytics_peak_hours(params: _AnalyticsInput, ctx: Context) -> str:
    """Transaction count and revenue by hour of day.

    Identifies peak business hours to help with staffing and operations.

    Args:
        params (_AnalyticsInput): days (default 30), optional store_id, date range.

    Returns:
        str: JSON array with keys hour, tx_count, revenue, pct_of_day.
    """
    try:
        engine = _engine(ctx)
        result = engine.operations.peak_hours(
            days=params.days,
            store_id=params.store_id,
            date_start=params.date_start,
            date_end=params.date_end,
            fmt="json",
        )
        return result
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_analytics_peak_days",
    annotations={
        "title": "Peak Days Analytics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_analytics_peak_days(params: _AnalyticsInput, ctx: Context) -> str:
    """Transaction count by day of week (Monday–Sunday).

    Identifies the busiest days for capacity planning.

    Args:
        params (_AnalyticsInput): days (default 30), optional store_id, date range.

    Returns:
        str: JSON array with keys day_name, tx_count, revenue, avg_ticket.
    """
    try:
        engine = _engine(ctx)
        result = engine.operations.peak_days(
            days=params.days,
            store_id=params.store_id,
            date_start=params.date_start,
            date_end=params.date_end,
            fmt="json",
        )
        return result
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="loyverse_analytics_monthly_summary",
    annotations={
        "title": "Monthly Revenue Summary",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def loyverse_analytics_monthly_summary(ctx: Context) -> str:
    """Monthly revenue, transaction count, unique customers, and month-over-month growth.

    Returns:
        str: JSON array with keys month, revenue, tx_count, unique_customers,
             avg_ticket, prev_month_revenue, mom_change_pct.
    """
    try:
        engine = _engine(ctx)
        result = engine.time_series.monthly_summary(months=12, fmt="json")
        return result
    except Exception as e:
        return _handle_error(e)

"""
Data conversion utilities for transforming Pydantic models to DuckDB-ready data.

This module handles:
- UUID to TEXT conversion
- Nested array extraction into junction/child tables
- Resource-specific data transformations
"""

from datetime import datetime
from typing import Any
from uuid import UUID


def pydantic_to_sql_dict(
    model_instance: Any, exclude_fields: set[str] | None = None
) -> dict[str, Any]:
    """
    Convert Pydantic model instance to SQL-ready dictionary.

    Handles:
    - UUID → TEXT conversion
    - Datetime preservation
    - Field exclusion
    - None value handling

    Args:
        model_instance: Pydantic model instance or dict
        exclude_fields: Set of field names to exclude

    Returns:
        Dictionary with SQL-compatible types

    Example:
        from loyverse_sdk.models import Category

        category = Category(id=uuid4(), name="Beverages", color="BLUE")
        sql_dict = pydantic_to_sql_dict(category, exclude_fields={"color"})
        # Returns: {"id": "abc-123-...", "name": "Beverages", ...}
    """
    # Handle dict input
    if isinstance(model_instance, dict):
        data = model_instance.copy()
    else:
        # Handle Pydantic model
        data = (
            model_instance.model_dump()
            if hasattr(model_instance, "model_dump")
            else dict(model_instance)
        )

    # Remove excluded fields
    if exclude_fields:
        for field in exclude_fields:
            data.pop(field, None)

    # Convert UUIDs to TEXT
    for key, value in list(data.items()):
        if isinstance(value, UUID):
            data[key] = str(value)
        elif isinstance(value, list) and value and isinstance(value[0], UUID):
            data[key] = [str(v) for v in value]
        elif value is None:
            # Keep None as None
            pass
        elif isinstance(value, datetime):
            # Keep datetime objects as-is (DuckDB handles them)
            pass

    return data


def split_nested_data(
    resource_name: str, data: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, list[dict]], dict[str, list[dict]]]:
    """
    Split a record into main table data, junction table data, and child table data.

    Args:
        resource_name: Name of the resource (e.g., "items", "receipts", "employees")
        data: Record data as dictionary

    Returns:
        Tuple of (main_record, junction_records, child_records)
        - main_record: Data for the main table
        - junction_records: Dict mapping junction table names to lists of records
        - child_records: Dict mapping child table names to lists of records

    Example:
        item_data = {"id": "123", "name": "Coffee", "tax_ids": ["tax1", "tax2"]}
        main, junction, child = split_nested_data("items", item_data)
        # main = {"id": "123", "name": "Coffee"}
        # junction = {"item_tax": [{"item_id": "123", "tax_id": "tax1"}, ...]}
        # child = {}
    """
    main_record = data.copy()
    junction_records = {}
    child_records = {}

    # Handle resource-specific nested data
    if resource_name == "items":
        main_record, junction_records = _split_items(main_record)

    elif resource_name == "employees":
        main_record, junction_records = _split_employees(main_record)

    elif resource_name == "receipts":
        main_record, child_records = _split_receipts(main_record)

    elif resource_name == "modifiers":
        main_record, junction_records, child_records = _split_modifiers(main_record)

    elif resource_name == "taxes":
        main_record, junction_records = _split_taxes(main_record)

    elif resource_name == "discounts":
        main_record, junction_records = _split_discounts(main_record)

    elif resource_name == "payment_types":
        main_record, junction_records = _split_payment_types(main_record)

    elif resource_name == "variants":
        main_record, junction_records = _split_variants(main_record)

    elif resource_name == "shifts":
        main_record, junction_records, child_records = _split_shifts(main_record)

    elif resource_name == "inventory":
        # No nested data to split - inventory has no arrays
        pass

    # Other resources (categories, stores, suppliers, customers, pos_devices, merchant)
    # have no nested data to split

    return main_record, junction_records, child_records


# ============================================================================
# RESOURCE-SPECIFIC SPLITTING FUNCTIONS
# ============================================================================


def _split_items(data: dict) -> tuple[dict, dict[str, list[dict]]]:
    """
    Split item data into main record and junction records.

    Extracts:
    - tax_ids → item_tax junction table
    - modifier_ids → item_modifier junction table
    - variants (removed, handled by variants endpoint)
    - components (removed, complex nested data)
    """
    main_record = data.copy()
    junction_records = {}

    # Extract tax_ids
    tax_ids = main_record.pop("tax_ids", [])
    if tax_ids:
        junction_records["item_tax"] = [
            {"item_id": str(main_record["id"]), "tax_id": str(tax_id)}
            for tax_id in tax_ids
        ]

    # Extract modifier_ids
    modifier_ids = main_record.pop("modifier_ids", [])
    if modifier_ids:
        junction_records["item_modifier"] = [
            {"item_id": str(main_record["id"]), "modifier_id": str(modifier_id)}
            for modifier_id in modifier_ids
        ]

    # Remove variants (handled by variants endpoint)
    main_record.pop("variants", None)

    # Remove components (complex nested data, not in schema)
    main_record.pop("components", None)

    return main_record, junction_records


def _split_employees(data: dict) -> tuple[dict, dict[str, list[dict]]]:
    """
    Split employee data into main record and junction records.

    Extracts:
    - stores → employee_store junction table
    """
    main_record = data.copy()
    junction_records = {}

    # Extract stores
    store_ids = main_record.pop("stores", [])
    if store_ids:
        junction_records["employee_store"] = [
            {"employee_id": str(main_record["id"]), "store_id": str(store_id)}
            for store_id in store_ids
        ]

    return main_record, junction_records


def _split_receipts(data: dict) -> tuple[dict, dict[str, list[dict]]]:
    """
    Split receipt data into main record and child records.
    Extracts:
    - line_items -> receipt_line_items child table
    - total_discounts (removed, complex nested array)
    - total_taxes (removed, complex nested array)
    - payments (removed, complex nested array)
    """
    main_record = data.copy()
    child_records = {}

    # Extract line_items
    line_items = main_record.pop("line_items", [])
    if line_items:
        child_records["receipt_line_items"] = []
        receipt_number = main_record.get("receipt_number")
        for item in line_items:
            line_item_record = {
                "id": str(item.get("id")) if item.get("id") else None,
                "receipt_id": receipt_number,
                "item_id": str(item.get("item_id")) if item.get("item_id") else None,
                "variant_id": str(item.get("variant_id"))
                if item.get("variant_id")
                else None,
                "item_name": item.get("item_name"),
                "variant_name": item.get("variant_name"),
                "sku": item.get("sku"),
                "quantity": item.get("quantity"),
                "price": item.get("price"),
                "gross_total_money": item.get("gross_total_money", 0.0),
                "total_money": item.get("total_money"),
                "cost": item.get("cost"),
                "cost_total": item.get("cost_total"),
                "line_note": item.get("line_note"),
                "total_discount": item.get("total_discount", 0.0),
            }
            child_records["receipt_line_items"].append(line_item_record)

    # Remove complex nested arrays
    main_record.pop("total_discounts", None)
    main_record.pop("total_taxes", None)
    main_record.pop("payments", None)

    return main_record, child_records


def _split_modifiers(
    data: dict,
) -> tuple[dict, dict[str, list[dict]], dict[str, list[dict]]]:
    """
    Split modifier data into main record, junction records, and child records.

    Extracts:
    - modifier_options → modifier_options child table
    - stores → modifier_store junction table
    """
    main_record = data.copy()
    junction_records = {}
    child_records = {}

    # Extract modifier_options
    options = main_record.pop("modifier_options", [])
    if options:
        child_records["modifier_options"] = []
        for option in options:
            # Convert UUIDs to strings
            option_record = {
                "id": str(option.get("id")),
                "modifier_id": str(main_record["id"]),
                "name": option.get("name"),
                "price": option.get("price", 0.0),
                "position": option.get("position", 0),
                "created_at": option.get("created_at"),
                "updated_at": option.get("updated_at"),
                "deleted_at": option.get("deleted_at"),
            }
            child_records["modifier_options"].append(option_record)

    # Extract stores
    store_ids = main_record.pop("stores", [])
    if store_ids:
        junction_records["modifier_store"] = [
            {"modifier_id": str(main_record["id"]), "store_id": str(store_id)}
            for store_id in store_ids
        ]

    return main_record, junction_records, child_records


def _split_taxes(data: dict) -> tuple[dict, dict[str, list[dict]]]:
    """
    Split tax data into main record and junction records.

    Extracts:
    - stores → tax_store junction table
    """
    main_record = data.copy()
    junction_records = {}

    # Extract stores
    store_ids = main_record.pop("stores", [])
    if store_ids:
        junction_records["tax_store"] = [
            {"tax_id": str(main_record["id"]), "store_id": str(store_id)}
            for store_id in store_ids
        ]

    return main_record, junction_records


def _split_discounts(data: dict) -> tuple[dict, dict[str, list[dict]]]:
    """
    Split discount data into main record and junction records.

    Extracts:
    - stores → discount_store junction table
    """
    main_record = data.copy()
    junction_records = {}

    # Extract stores
    store_ids = main_record.pop("stores", [])
    if store_ids:
        junction_records["discount_store"] = [
            {"discount_id": str(main_record["id"]), "store_id": str(store_id)}
            for store_id in store_ids
        ]

    return main_record, junction_records


def _split_payment_types(data: dict) -> tuple[dict, dict[str, list[dict]]]:
    """
    Split payment type data into main record and junction records.

    Extracts:
    - stores → payment_type_store junction table
    """
    main_record = data.copy()
    junction_records = {}

    # Extract stores
    store_ids = main_record.pop("stores", [])
    if store_ids:
        junction_records["payment_type_store"] = [
            {"payment_type_id": str(main_record["id"]), "store_id": str(store_id)}
            for store_id in store_ids
        ]

    return main_record, junction_records


def _split_variants(data: dict) -> tuple[dict, dict[str, list[dict]]]:
    """
    Split variant data into main record and junction records.

    Extracts:
    - stores → variant_store junction table (with additional fields)
    """
    main_record = data.copy()
    junction_records = {}

    # Extract stores (with additional store-specific data)
    stores = main_record.pop("stores", [])
    if stores:
        junction_records["variant_store"] = []
        for store in stores:
            # Handle both dict and UUID formats
            if isinstance(store, dict):
                variant_store_record = {
                    "variant_id": str(main_record["id"]),
                    "store_id": str(store.get("store_id")),
                    "available_for_sale": store.get("available_for_sale", True),
                    "optimal_stock": store.get("optimal_stock"),
                    "low_stock_threshold": store.get("low_stock_threshold"),
                }
            else:
                # Simple store_id (UUID)
                variant_store_record = {
                    "variant_id": str(main_record["id"]),
                    "store_id": str(store),
                    "available_for_sale": True,
                    "optimal_stock": None,
                    "low_stock_threshold": None,
                }
            junction_records["variant_store"].append(variant_store_record)

    return main_record, junction_records


def _split_shifts(
    data: dict,
) -> tuple[dict, dict[str, list[dict]], dict[str, list[dict]]]:
    """
    Split shift data into main record, junction records, and child records.

    Extracts:
    - taxes → shift_taxes child table
    - payments → shift_payments child table
    - cash_movements → shift_cash_movements child table
    """
    main_record = data.copy()
    junction_records = {}
    child_records = {}

    # Extract taxes
    taxes = main_record.pop("taxes", [])
    if taxes:
        child_records["shift_taxes"] = []
        for tax in taxes:
            child_records["shift_taxes"].append(
                {
                    "id": str(tax.get("id")),
                    "shift_id": str(main_record["id"]),
                    "name": tax.get("name"),
                    "rate": tax.get("rate", 0.0),
                    "amount": tax.get("amount", 0.0),
                }
            )

    # Extract payments
    payments = main_record.pop("payments", [])
    if payments:
        child_records["shift_payments"] = []
        for payment in payments:
            child_records["shift_payments"].append(
                {
                    "id": str(payment.get("id")),
                    "shift_id": str(main_record["id"]),
                    "name": payment.get("name"),
                    "amount": payment.get("amount", 0.0),
                }
            )

    # Extract cash_movements
    cash_movements = main_record.pop("cash_movements", [])
    if cash_movements:
        child_records["shift_cash_movements"] = []
        for movement in cash_movements:
            child_records["shift_cash_movements"].append(
                {
                    "id": str(movement.get("id")),
                    "shift_id": str(main_record["id"]),
                    "time": movement.get("time"),
                    "amount": movement.get("amount", 0.0),
                    "note": movement.get("note"),
                }
            )

    return main_record, junction_records, child_records


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def convert_uuid_fields(data: dict) -> dict:
    """
    Convert all UUID fields in a dictionary to strings.

    Args:
        data: Dictionary that may contain UUID values

    Returns:
        Dictionary with UUIDs converted to strings

    Example:
        data = {"id": UUID("abc-123"), "name": "Test"}
        result = convert_uuid_fields(data)
        # result = {"id": "abc-123", "name": "Test"}
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, list) and value and isinstance(value[0], UUID):
            result[key] = [str(v) for v in value]
        elif isinstance(value, dict):
            result[key] = convert_uuid_fields(value)
        else:
            result[key] = value
    return result


def extract_id(value: Any) -> str | None:
    """
    Extract string ID from various formats (UUID, string, dict with id).

    Args:
        value: Value that may contain an ID

    Returns:
        String ID or None

    Example:
        extract_id(UUID("abc-123"))  # "abc-123"
        extract_id("abc-123")         # "abc-123"
        extract_id({"id": "abc-123"}) # "abc-123"
        extract_id(None)              # None
    """
    if value is None:
        return None
    elif isinstance(value, UUID):
        return str(value)
    elif isinstance(value, str):
        return value
    elif isinstance(value, dict) and "id" in value:
        return str(value["id"])
    else:
        return str(value)


def validate_required_fields(data: dict, required_fields: list[str]) -> None:
    """
    Validate that required fields are present and non-null.

    Args:
        data: Dictionary to validate
        required_fields: List of required field names

    Raises:
        ValueError: If any required field is missing or None

    Example:
        validate_required_fields(
            {"id": "123", "name": "Test"},
            ["id", "name"]
        )  # OK

        validate_required_fields(
            {"id": "123"},
            ["id", "name"]
        )  # Raises ValueError
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)

    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


def get_resource_required_fields(resource_name: str) -> list[str]:
    """
    Get list of required fields for a resource.

    Args:
        resource_name: Name of the resource

    Returns:
        List of required field names

    Example:
        fields = get_resource_required_fields("receipts")
        # Returns: ["id", "receipt_number", "receipt_type", "receipt_date", ...]
    """
    required_fields_map = {
        "categories": ["id", "name", "color", "created_at", "updated_at"],
        "stores": ["id", "name", "created_at", "updated_at"],
        "suppliers": ["id", "name", "created_at", "updated_at"],
        "taxes": ["id", "name", "type", "rate", "created_at", "updated_at"],
        "modifiers": ["id", "name", "position", "created_at", "updated_at"],
        "discounts": ["id", "type", "name", "created_at", "updated_at"],
        "employees": ["id", "name", "created_at", "updated_at"],
        "inventory": ["variant_id", "store_id", "in_stock", "updated_at"],
        "customers": ["id", "name", "created_at", "updated_at"],
        "pos_devices": ["id", "name", "store_id"],
        "payment_types": ["id", "name", "type", "created_at", "updated_at"],
        "items": ["id", "name", "created_at", "updated_at"],
        "variants": ["id", "item_id", "sku", "created_at", "updated_at"],
        "receipts": [
            "id",
            "receipt_number",
            "receipt_type",
            "receipt_date",
            "total_amount",
            "employee_id",
            "store_id",
            "pos_device_id",
            "created_at",
            "updated_at",
        ],
        "merchant": ["id", "business_name", "currency", "created_at"],
    }

    return required_fields_map.get(resource_name, ["id"])


def prepare_record_for_insert(
    resource_name: str, record: dict, validate: bool = True
) -> dict:
    """
    Prepare a record for database insertion.

    Performs:
    - UUID to string conversion
    - Field validation (if enabled)
    - None value handling

    Args:
        resource_name: Name of the resource
        record: Record dictionary
        validate: If True, validates required fields

    Returns:
        Prepared record ready for insertion

    Raises:
        ValueError: If validation fails

    Example:
        record = {"id": UUID("abc"), "name": "Test", "color": "RED"}
        prepared = prepare_record_for_insert("categories", record)
        # All UUIDs converted to strings, validated
    """
    # Convert UUIDs
    prepared = convert_uuid_fields(record)

    # Validate if requested
    if validate:
        required_fields = get_resource_required_fields(resource_name)
        validate_required_fields(prepared, required_fields)

    return prepared

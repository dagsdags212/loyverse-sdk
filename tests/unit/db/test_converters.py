"""
Unit tests for loyverse_sdk.db.converters module.

Tests Pydantic model conversion, UUID handling, and nested data splitting.
"""

import pytest
from datetime import datetime
from uuid import uuid4, UUID

from loyverse_sdk.db.converters import (
    pydantic_to_sql_dict,
    split_nested_data,
    convert_uuid_fields,
    extract_id,
    validate_required_fields,
    get_resource_required_fields,
    prepare_record_for_insert,
    _split_items,
    _split_employees,
    _split_receipts,
    _split_modifiers,
    _split_taxes,
    _split_discounts,
    _split_payment_types,
    _split_variants,
)


class TestPydanticToSqlDict:
    """Test pydantic_to_sql_dict function."""

    def test_converts_dict_input(self):
        """Test conversion of dict input."""
        data = {"id": "test123", "name": "Test", "value": 42}
        result = pydantic_to_sql_dict(data)

        assert result == data
        assert result is not data  # Should be a copy

    def test_converts_uuid_to_string(self):
        """Test that UUID values are converted to strings."""
        test_uuid = uuid4()
        data = {"id": test_uuid, "name": "Test"}

        result = pydantic_to_sql_dict(data)

        assert isinstance(result["id"], str)
        assert result["id"] == str(test_uuid)
        assert result["name"] == "Test"

    def test_converts_uuid_list_to_string_list(self):
        """Test that list of UUIDs are converted to strings."""
        uuid1 = uuid4()
        uuid2 = uuid4()
        data = {"id": "test", "tax_ids": [uuid1, uuid2]}

        result = pydantic_to_sql_dict(data)

        assert isinstance(result["tax_ids"], list)
        assert len(result["tax_ids"]) == 2
        assert all(isinstance(id, str) for id in result["tax_ids"])
        assert result["tax_ids"] == [str(uuid1), str(uuid2)]

    def test_preserves_datetime_objects(self):
        """Test that datetime objects are preserved."""
        now = datetime.now()
        data = {"id": "test", "created_at": now}

        result = pydantic_to_sql_dict(data)

        assert result["created_at"] == now
        assert isinstance(result["created_at"], datetime)

    def test_preserves_none_values(self):
        """Test that None values are preserved."""
        data = {"id": "test", "optional_field": None}

        result = pydantic_to_sql_dict(data)

        assert "optional_field" in result
        assert result["optional_field"] is None

    def test_excludes_specified_fields(self):
        """Test that excluded fields are removed."""
        data = {"id": "test", "name": "Test", "internal_field": "secret"}

        result = pydantic_to_sql_dict(data, exclude_fields={"internal_field"})

        assert "id" in result
        assert "name" in result
        assert "internal_field" not in result

    def test_handles_pydantic_model_with_model_dump(self):
        """Test conversion of Pydantic model with model_dump method."""
        # Create a simple mock Pydantic-like object
        class MockModel:
            def model_dump(self):
                return {"id": "test", "name": "Mock"}

        model = MockModel()
        result = pydantic_to_sql_dict(model)

        assert result == {"id": "test", "name": "Mock"}


class TestSplitNestedData:
    """Test split_nested_data function for all resource types."""

    def test_split_items_extracts_tax_ids(self):
        """Test that item tax_ids are extracted to junction table."""
        data = {
            "id": "item1",
            "name": "Coffee",
            "tax_ids": ["tax1", "tax2"],
            "modifier_ids": [],
        }

        main, junction, child = split_nested_data("items", data)

        # Main record should not have tax_ids
        assert "tax_ids" not in main
        assert main["id"] == "item1"
        assert main["name"] == "Coffee"

        # Junction records should have item_tax entries
        assert "item_tax" in junction
        assert len(junction["item_tax"]) == 2
        assert junction["item_tax"][0] == {"item_id": "item1", "tax_id": "tax1"}
        assert junction["item_tax"][1] == {"item_id": "item1", "tax_id": "tax2"}

    def test_split_items_extracts_modifier_ids(self):
        """Test that item modifier_ids are extracted to junction table."""
        data = {
            "id": "item1",
            "name": "Coffee",
            "tax_ids": [],
            "modifier_ids": ["mod1", "mod2"],
        }

        main, junction, child = split_nested_data("items", data)

        # Junction records should have item_modifier entries
        assert "item_modifier" in junction
        assert len(junction["item_modifier"]) == 2
        assert junction["item_modifier"][0] == {"item_id": "item1", "modifier_id": "mod1"}

    def test_split_items_removes_variants_field(self):
        """Test that variants field is removed (handled by variants endpoint)."""
        data = {
            "id": "item1",
            "name": "Coffee",
            "variants": [{"id": "var1"}, {"id": "var2"}],
        }

        main, junction, child = split_nested_data("items", data)

        assert "variants" not in main

    def test_split_employees_extracts_stores(self):
        """Test that employee stores are extracted to junction table."""
        data = {
            "id": "emp1",
            "name": "John Doe",
            "stores": ["store1", "store2"],
        }

        main, junction, child = split_nested_data("employees", data)

        assert "stores" not in main
        assert "employee_store" in junction
        assert len(junction["employee_store"]) == 2
        assert junction["employee_store"][0] == {"employee_id": "emp1", "store_id": "store1"}

    def test_split_receipts_extracts_line_items(self):
        """Test that receipt line_items are extracted to child table."""
        data = {
            "receipt_number": "001",
            "line_items": [
                {
                    "id": "line1",
                    "item_id": "item1",
                    "item_name": "Coffee",
                    "sku": "COF001",
                    "quantity": 2,
                    "price": 5.0,
                },
                {
                    "id": "line2",
                    "item_id": "item2",
                    "item_name": "Tea",
                    "sku": "TEA001",
                    "quantity": 1,
                    "price": 3.0,
                },
            ],
        }

        main, junction, child = split_nested_data("receipts", data)

        assert "line_items" not in main
        assert "receipt_line_items" in child
        assert len(child["receipt_line_items"]) == 2

        # Verify line item structure
        line1 = child["receipt_line_items"][0]
        assert line1["id"] == "line1"
        assert line1["receipt_id"] == "001"
        assert line1["item_id"] == "item1"
        assert line1["item_name"] == "Coffee"
        assert line1["quantity"] == 2
        assert line1["price"] == 5.0

    def test_split_receipts_removes_total_discounts_and_taxes(self):
        """Test that complex nested arrays are removed from receipts."""
        data = {
            "id": "rec1",
            "receipt_number": "001",
            "total_discounts": [{"amount": 10}],
            "total_taxes": [{"amount": 5}],
        }

        main, junction, child = split_nested_data("receipts", data)

        assert "total_discounts" not in main
        assert "total_taxes" not in main

    def test_split_modifiers_extracts_options(self):
        """Test that modifier options are extracted to child table."""
        data = {
            "id": "mod1",
            "name": "Size",
            "modifier_options": [
                {
                    "id": "opt1",
                    "name": "Small",
                    "price": 0.0,
                    "position": 1,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "deleted_at": None,
                },
                {
                    "id": "opt2",
                    "name": "Large",
                    "price": 2.0,
                    "position": 2,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "deleted_at": None,
                },
            ],
            "stores": [],
        }

        main, junction, child = split_nested_data("modifiers", data)

        assert "modifier_options" not in main
        assert "modifier_options" in child
        assert len(child["modifier_options"]) == 2

        opt1 = child["modifier_options"][0]
        assert opt1["id"] == "opt1"
        assert opt1["modifier_id"] == "mod1"
        assert opt1["name"] == "Small"

    def test_split_modifiers_extracts_stores(self):
        """Test that modifier stores are extracted to junction table."""
        data = {
            "id": "mod1",
            "name": "Size",
            "modifier_options": [],
            "stores": ["store1", "store2"],
        }

        main, junction, child = split_nested_data("modifiers", data)

        assert "stores" not in main
        assert "modifier_store" in junction
        assert len(junction["modifier_store"]) == 2

    def test_split_taxes_extracts_stores(self):
        """Test that tax stores are extracted to junction table."""
        data = {
            "id": "tax1",
            "name": "VAT",
            "stores": ["store1"],
        }

        main, junction, child = split_nested_data("taxes", data)

        assert "stores" not in main
        assert "tax_store" in junction
        assert len(junction["tax_store"]) == 1
        assert junction["tax_store"][0] == {"tax_id": "tax1", "store_id": "store1"}

    def test_split_discounts_extracts_stores(self):
        """Test that discount stores are extracted to junction table."""
        data = {
            "id": "disc1",
            "name": "10% Off",
            "stores": ["store1"],
        }

        main, junction, child = split_nested_data("discounts", data)

        assert "discount_store" in junction

    def test_split_payment_types_extracts_stores(self):
        """Test that payment type stores are extracted to junction table."""
        data = {
            "id": "pay1",
            "name": "Cash",
            "stores": ["store1"],
        }

        main, junction, child = split_nested_data("payment_types", data)

        assert "payment_type_store" in junction

    def test_split_variants_extracts_stores_with_details(self):
        """Test that variant stores are extracted with additional fields."""
        data = {
            "id": "var1",
            "item_id": "item1",
            "stores": [
                {
                    "store_id": "store1",
                    "available_for_sale": True,
                    "optimal_stock": 100,
                    "low_stock_threshold": 10,
                },
                {
                    "store_id": "store2",
                    "available_for_sale": False,
                    "optimal_stock": None,
                    "low_stock_threshold": None,
                },
            ],
        }

        main, junction, child = split_nested_data("variants", data)

        assert "stores" not in main
        assert "variant_store" in junction
        assert len(junction["variant_store"]) == 2

        store1 = junction["variant_store"][0]
        assert store1["variant_id"] == "var1"
        assert store1["store_id"] == "store1"
        assert store1["available_for_sale"] is True
        assert store1["optimal_stock"] == 100

    def test_split_variants_handles_simple_store_ids(self):
        """Test that variant stores can be simple UUID list."""
        data = {
            "id": "var1",
            "item_id": "item1",
            "stores": ["store1", "store2"],
        }

        main, junction, child = split_nested_data("variants", data)

        assert "variant_store" in junction
        assert len(junction["variant_store"]) == 2
        assert junction["variant_store"][0]["available_for_sale"] is True
        assert junction["variant_store"][0]["optimal_stock"] is None

    def test_split_categories_no_nested_data(self):
        """Test that categories (no nested data) return empty junction/child."""
        data = {
            "id": "cat1",
            "name": "Beverages",
            "color": "BLUE",
        }

        main, junction, child = split_nested_data("categories", data)

        assert main == data
        assert junction == {}
        assert child == {}


class TestConvertUuidFields:
    """Test convert_uuid_fields function."""

    def test_converts_single_uuid(self):
        """Test converting single UUID field."""
        test_uuid = uuid4()
        data = {"id": test_uuid, "name": "Test"}

        result = convert_uuid_fields(data)

        assert isinstance(result["id"], str)
        assert result["id"] == str(test_uuid)

    def test_converts_uuid_list(self):
        """Test converting list of UUIDs."""
        uuid1 = uuid4()
        uuid2 = uuid4()
        data = {"ids": [uuid1, uuid2]}

        result = convert_uuid_fields(data)

        assert all(isinstance(id, str) for id in result["ids"])

    def test_converts_nested_dict_uuids(self):
        """Test converting UUIDs in nested dictionaries."""
        test_uuid = uuid4()
        data = {
            "id": "test",
            "nested": {
                "uuid_field": test_uuid,
            },
        }

        result = convert_uuid_fields(data)

        assert isinstance(result["nested"]["uuid_field"], str)

    def test_preserves_non_uuid_values(self):
        """Test that non-UUID values are preserved."""
        data = {
            "id": "string_id",
            "count": 42,
            "flag": True,
            "value": None,
        }

        result = convert_uuid_fields(data)

        assert result == data


class TestExtractId:
    """Test extract_id function."""

    def test_extract_from_uuid(self):
        """Test extracting ID from UUID object."""
        test_uuid = uuid4()
        result = extract_id(test_uuid)

        assert isinstance(result, str)
        assert result == str(test_uuid)

    def test_extract_from_string(self):
        """Test extracting ID from string."""
        result = extract_id("test123")
        assert result == "test123"

    def test_extract_from_dict(self):
        """Test extracting ID from dict with id field."""
        result = extract_id({"id": "test123", "name": "Test"})
        assert result == "test123"

    def test_extract_from_none(self):
        """Test extracting ID from None."""
        result = extract_id(None)
        assert result is None

    def test_extract_from_other_types(self):
        """Test extracting ID from other types converts to string."""
        result = extract_id(42)
        assert result == "42"


class TestValidateRequiredFields:
    """Test validate_required_fields function."""

    def test_validates_present_fields(self):
        """Test validation passes when all required fields present."""
        data = {"id": "test", "name": "Test", "value": 42}

        # Should not raise
        validate_required_fields(data, ["id", "name"])

    def test_raises_on_missing_field(self):
        """Test validation raises when required field missing."""
        data = {"id": "test"}

        with pytest.raises(ValueError, match="Missing required fields: name"):
            validate_required_fields(data, ["id", "name"])

    def test_raises_on_none_value(self):
        """Test validation raises when required field is None."""
        data = {"id": "test", "name": None}

        with pytest.raises(ValueError, match="Missing required fields: name"):
            validate_required_fields(data, ["id", "name"])

    def test_raises_on_multiple_missing_fields(self):
        """Test validation raises with multiple missing fields."""
        data = {"id": "test"}

        with pytest.raises(ValueError, match="name, value"):
            validate_required_fields(data, ["id", "name", "value"])


class TestGetResourceRequiredFields:
    """Test get_resource_required_fields function."""

    def test_returns_fields_for_categories(self):
        """Test returns required fields for categories."""
        fields = get_resource_required_fields("categories")

        assert "id" in fields
        assert "name" in fields
        assert "color" in fields
        assert "created_at" in fields
        assert "updated_at" in fields

    def test_returns_fields_for_receipts(self):
        """Test returns required fields for receipts."""
        fields = get_resource_required_fields("receipts")

        assert "id" in fields
        assert "receipt_number" in fields
        assert "receipt_type" in fields
        assert "receipt_date" in fields
        assert "employee_id" in fields

    def test_returns_default_for_unknown_resource(self):
        """Test returns default fields for unknown resource."""
        fields = get_resource_required_fields("unknown_resource")

        assert fields == ["id"]


class TestPrepareRecordForInsert:
    """Test prepare_record_for_insert function."""

    def test_prepares_record_with_validation(self):
        """Test preparing record with validation enabled."""
        test_uuid = uuid4()
        record = {
            "id": test_uuid,
            "name": "Test Category",
            "color": "RED",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        result = prepare_record_for_insert("categories", record, validate=True)

        assert isinstance(result["id"], str)
        assert result["name"] == "Test Category"

    def test_prepares_record_without_validation(self):
        """Test preparing record with validation disabled."""
        record = {
            "id": uuid4(),
            "name": "Test",
        }

        # Should not raise even though required fields missing
        result = prepare_record_for_insert("categories", record, validate=False)

        assert isinstance(result["id"], str)

    def test_raises_on_validation_failure(self):
        """Test that validation failure raises error."""
        record = {
            "id": uuid4(),
            # Missing required fields
        }

        with pytest.raises(ValueError, match="Missing required fields"):
            prepare_record_for_insert("categories", record, validate=True)


class TestResourceSpecificSplitters:
    """Test resource-specific splitting functions directly."""

    def test_split_items_function(self):
        """Test _split_items function."""
        data = {
            "id": "item1",
            "name": "Coffee",
            "tax_ids": ["tax1"],
            "modifier_ids": ["mod1"],
            "variants": [{"id": "var1"}],
            "components": [{"id": "comp1"}],
        }

        main, junction = _split_items(data)

        assert "tax_ids" not in main
        assert "modifier_ids" not in main
        assert "variants" not in main
        assert "components" not in main

        assert "item_tax" in junction
        assert "item_modifier" in junction

    def test_split_employees_function(self):
        """Test _split_employees function."""
        data = {
            "id": "emp1",
            "name": "John",
            "stores": ["store1"],
        }

        main, junction = _split_employees(data)

        assert "stores" not in main
        assert "employee_store" in junction

    def test_split_receipts_function(self):
        """Test _split_receipts function."""
        data = {
            "id": "rec1",
            "line_items": [{"id": "line1", "item_id": "item1", "variant_id": "var1", "name": "Test", "quantity": 1, "price": 10.0, "cost": 5.0}],
        }

        main, child = _split_receipts(data)

        assert "line_items" not in main
        assert "receipt_line_items" in child

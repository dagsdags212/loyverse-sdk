from loyverse_sdk.cli._metadata import (
    get_creatable_resources,
    get_deletable_resources,
    get_endpoint_classes,
    get_item_model,
    get_listable_resources,
    get_required_fields,
    get_response_model,
    get_updatable_resources,
    make_create_epilog,
)


class TestResourceDiscovery:
    def test_listable_includes_customers(self):
        assert "customers" in get_listable_resources()

    def test_listable_excludes_merchant(self):
        assert "merchant" not in get_listable_resources()

    def test_creatable_does_not_include_merchant(self):
        assert "merchant" not in get_creatable_resources()

    def test_creatable_includes_categories(self):
        assert "categories" in get_creatable_resources()

    def test_updatable_includes_items(self):
        assert "items" in get_updatable_resources()

    def test_deletable_includes_discounts(self):
        assert "discounts" in get_deletable_resources()

    def test_deletable_excludes_employees(self):
        assert "employees" not in get_deletable_resources()

    def test_all_resources_have_model_map(self):
        for name in get_listable_resources():
            assert get_response_model(name) is not None
            assert get_item_model(name) is not None

    def test_endpoint_classes_returns_all(self):
        classes = get_endpoint_classes()
        assert "categories" in classes
        assert "receipts" in classes
        assert "merchant" in classes
        assert len(classes) >= 17


class TestRequiredFields:
    def test_categories_requires_name(self):
        assert "name" in get_required_fields("categories")

    def test_receipts_requires_store_id(self):
        assert "store_id" in get_required_fields("receipts")

    def test_unknown_resource_returns_empty(self):
        assert get_required_fields("nonexistent") == []


class TestCreateEpilog:
    def test_epilog_includes_known_resources(self):
        epilog = make_create_epilog()
        assert "categories" in epilog
        assert "customers" in epilog
        assert "--name" in epilog

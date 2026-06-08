import json

from pydantic import BaseModel

from loyverse_sdk.cli._display import build_table, flatten_for_export, items_key


class _FakeModel(BaseModel):
    id: str = ""
    name: str = ""
    count: int = 0
    tags: list[str] = []


class _FakeEndpoint:
    path = "items"
    items_key = "records"


class TestItemsKey:
    def test_returns_items_key_when_present(self):
        ep = _FakeEndpoint()
        assert items_key(ep) == "records"

    def test_falls_back_to_path(self):
        class Ep:
            path = "categories"

        assert items_key(Ep()) == "categories"

    def test_handles_empty_string_items_key(self):
        class Ep:
            path = "inventory"
            items_key = ""

        assert items_key(Ep()) == "inventory"

    def test_handles_none_items_key(self):
        class Ep:
            path = "receipts"
            items_key = None

        assert items_key(Ep()) == "receipts"


class TestFlattenForExport:
    def test_flattens_list_fields_to_json(self):
        items = [
            _FakeModel(id="1", name="A", count=10, tags=["x", "y"]),
            _FakeModel(id="2", name="B", count=20, tags=["z"]),
        ]
        flat = flatten_for_export(items)
        assert len(flat) == 2
        assert json.loads(flat[0]["tags"]) == ["x", "y"]
        assert json.loads(flat[1]["tags"]) == ["z"]
        assert flat[0]["name"] == "A"

    def test_handles_empty_list(self):
        assert flatten_for_export([]) == []


class TestBuildTable:
    def test_empty_items_returns_empty_table(self):
        table = build_table([])
        assert "(empty)" in table.title

    def test_builds_table_with_columns(self):
        items = [
            _FakeModel(id="abc", name="Test", count=5, tags=["a"]),
            _FakeModel(id="def", name="Other", count=3, tags=[]),
        ]
        table = build_table(items)
        assert "abc" in str(table.columns)
        assert "Test" in str(table.columns)

    def test_excludes_list_and_dict_fields(self):
        items = [_FakeModel(id="1", name="X", count=1, tags=["a"])]
        table = build_table(items)
        column_names = [col.header for col in table.columns]
        assert "id" in column_names
        assert "name" in column_names
        assert "count" in column_names
        assert "tags" not in column_names

from uuid import uuid4, UUID
from datetime import datetime
import pytest
from pydantic import ValidationError

from loyverse_sdk.models import Item


class TestItemModel:
    """Simulates ingesting and instatiating data from /items"""

    def generate_valid_payload(self):
        payload = dict(
            id=uuid4(),
            item_name="Soap",
            handle="Joy",
            reference_id=None,
            description="For washing dishes",
            track_stock=True,
            sold_by_weight=False,
            is_composite=False,
            use_production=False,
            category_id=uuid4(),
            components=[],
            primary_supplier_id=uuid4(),
            tax_ids=[uuid4()],
            modifier_ids=[uuid4()],
            form="CIRCLE",
            color="BLUE",
            image_url="soap.jpg",
            variants=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            deleted_at=None,
        )
        return payload

    def test_valid_payload(self):
        payload = self.generate_valid_payload()
        r = Item(**payload)

        assert r.id is not None
        assert r.name is not None
        assert r.handle.istitle()
        assert isinstance(r.track_stock, bool)
        assert isinstance(r.sold_by_weight, bool)
        assert isinstance(r.is_composite, bool)
        assert isinstance(r.use_production, bool)
        assert isinstance(r.components, list)
        assert isinstance(r.tax_ids, list)
        assert isinstance(r.modifier_ids, list)
        if r.variants is not None:
            assert isinstance(r.variants, list)
        assert isinstance(r.primary_supplier_id, UUID)

    def test_missing_required_values(self):
        payload = self.generate_valid_payload()
        del payload["item_name"]

        with pytest.raises(ValidationError):
            Item(**payload)

    def test_default_handle(self):
        payload = dict(item_name="Soap")
        r = Item(**payload)

        assert r.handle == r.name

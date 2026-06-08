from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from loyverse_sdk.models import PosDevice


class TestPosDeviceModel:
    """Simulates ingesting and instatiating data from /pos_devices"""

    def generate_valid_payload(self):
        payload = dict(
            id=uuid4(), name="Cash", store_id=uuid4(), activated=True, deleted_at=None
        )
        return payload

    def test_valid_payload(self):
        payload = self.generate_valid_payload()
        r = PosDevice(**payload)

        assert r.id is not None
        assert isinstance(r.id, UUID)
        assert r.name is not None
        assert r.store_id is not None
        assert isinstance(r.store_id, UUID)
        assert isinstance(r.activated, bool)

    def test_missing_required_values(self):
        payload = self.generate_valid_payload()
        del payload["id"]

        with pytest.raises(ValidationError):
            PosDevice(**payload)

        payload = self.generate_valid_payload()
        del payload["name"]

        with pytest.raises(ValidationError):
            PosDevice(**payload)

        payload = self.generate_valid_payload()
        del payload["store_id"]

        with pytest.raises(ValidationError):
            PosDevice(**payload)

    def test_default_handle(self):
        payload = dict(
            id=uuid4(),
            name="Primary POS",
            store_id=uuid4(),
        )
        r = PosDevice(**payload)

        assert r.activated is True
        assert r.deleted_at is None

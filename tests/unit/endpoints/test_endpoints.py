"""Unit tests for the concrete endpoint classes.

Each endpoint composes ``BaseEndpoint`` + mixins and overrides the CRUD /
pagination methods to inject a specific pydantic ``model=``. These tests
instantiate every endpoint with a mock client whose ``.request`` is an
``AsyncMock`` and exercise the overridden methods with a realistic API
payload, asserting the right HTTP verb/path is issued and the right model
type is returned.

The endpoints are described declaratively in ``ENDPOINT_SPECS`` so the same
parametrized tests cover all of them with minimal duplication.
"""

from dataclasses import dataclass, field
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from loyverse_sdk.endpoints import (
    CategoriesEndpoint,
    CustomersEndpoint,
    DiscountsEndpoint,
    EmployeesEndpoint,
    ItemsEndpoint,
    ModifiersEndpoint,
    PaymentTypesEndpoint,
    PosDevicesEndpoints,
    ReceiptsEndpoint,
    ShiftsEndpoint,
    StoresEndpoint,
    SuppliersEndpoint,
    TaxesEndpoint,
    VariantsEndpoint,
    WebhooksEndpoint,
)
from loyverse_sdk.models import (
    Category,
    Customer,
    Discount,
    Employee,
    Item,
    Modifier,
    PaymentType,
    PosDevice,
    Receipt,
    Shift,
    Store,
    Supplier,
    Tax,
    Variant,
    Webhook,
)

STORE_ID = str(uuid4())


def _record(endpoint: str) -> dict:
    """Return a single realistic API record for the given endpoint path."""
    records: dict[str, dict] = {
        "categories": {"id": str(uuid4()), "name": "Drinks", "color": "RED"},
        "customers": {"id": str(uuid4()), "name": "john doe", "email": "a@b.com"},
        "pos_devices": {
            "id": str(uuid4()),
            "name": "Till 1",
            "store_id": STORE_ID,
        },
        "discounts": {
            "id": str(uuid4()),
            "type": "FIXED_AMOUNT",
            "name": "Loyalty",
            "discount_amount": 5.0,
            "stores": [STORE_ID],
        },
        "employees": {"id": str(uuid4()), "name": "jane", "stores": [STORE_ID]},
        "items": {"id": str(uuid4()), "item_name": "Coffee"},
        "modifiers": {
            "id": str(uuid4()),
            "name": "Size",
            "position": 1,
            "stores": [STORE_ID],
        },
        "payment_types": {"id": str(uuid4()), "name": "Cash", "type": "CASH"},
        "receipts": {
            "receipt_number": "R-1",
            "receipt_type": "SALE",
            "total_money": 10.0,
        },
        "shifts": {
            "id": str(uuid4()),
            "store_id": STORE_ID,
            "pos_device_id": str(uuid4()),
            "opened_at": "2024-01-01T00:00:00Z",
            "opened_by_employee": "emp-1",
        },
        "stores": {"id": str(uuid4()), "name": "Main"},
        "suppliers": {"id": str(uuid4()), "name": "Acme", "contact": "Bob"},
        "taxes": {
            "id": str(uuid4()),
            "name": "VAT",
            "type": "INCLUDED",
            "rate": 12.0,
            "stores": [STORE_ID],
        },
        "variants": {
            "variant_id": str(uuid4()),
            "item_id": str(uuid4()),
            "sku": "SKU-1",
            "stores": [],
        },
        "webhooks": {
            "id": str(uuid4()),
            "merchant_id": str(uuid4()),
            "url": "https://example.com/hook",
            "type": "items.update",
        },
    }
    return records[endpoint]


@dataclass
class EndpointSpec:
    cls: type
    path: str
    items_key: str
    model: type
    # which CRUD methods the endpoint overrides
    has_create: bool = False
    has_update: bool = False
    has_retrieve: bool = True
    has_delete: bool = False
    # extra id field used for retrieve/update/delete
    id_value: str = field(default_factory=lambda: str(uuid4()))

    def list_response(self) -> dict:
        return {self.items_key: [_record(self.path)], "cursor": None}


ENDPOINT_SPECS: list[EndpointSpec] = [
    EndpointSpec(
        CategoriesEndpoint, "categories", "categories", Category,
        has_create=True, has_update=True, has_delete=True,
    ),
    EndpointSpec(
        CustomersEndpoint, "customers", "customers", Customer,
        has_create=True, has_update=True, has_delete=True,
    ),
    EndpointSpec(
        PosDevicesEndpoints, "pos_devices", "pos_devices", PosDevice,
        has_create=True, has_update=True, has_delete=True,
    ),
    EndpointSpec(
        DiscountsEndpoint, "discounts", "discounts", Discount,
        has_create=True, has_update=True, has_delete=True,
    ),
    EndpointSpec(
        EmployeesEndpoint, "employees", "employees", Employee,
    ),
    EndpointSpec(
        ItemsEndpoint, "items", "items", Item,
        has_create=True, has_update=True,
    ),
    EndpointSpec(
        ModifiersEndpoint, "modifiers", "modifiers", Modifier,
        has_create=True, has_update=True,
    ),
    EndpointSpec(
        PaymentTypesEndpoint, "payment_types", "payment_types", PaymentType,
    ),
    EndpointSpec(
        ReceiptsEndpoint, "receipts", "receipts", Receipt,
        has_create=True, has_update=True, has_delete=True,
    ),
    EndpointSpec(
        ShiftsEndpoint, "shifts", "shifts", Shift,
    ),
    EndpointSpec(
        StoresEndpoint, "stores", "stores", Store,
    ),
    EndpointSpec(
        SuppliersEndpoint, "suppliers", "suppliers", Supplier,
        has_create=True, has_update=True, has_delete=True,
    ),
    EndpointSpec(
        TaxesEndpoint, "taxes", "taxes", Tax,
        has_create=True, has_update=True, has_delete=True,
    ),
    EndpointSpec(
        VariantsEndpoint, "variants", "variants", Variant,
        has_create=True, has_update=True, has_delete=True,
    ),
    EndpointSpec(
        WebhooksEndpoint, "webhooks", "webhooks", Webhook,
        has_delete=True,
    ),
]

SPEC_IDS = [s.cls.__name__ for s in ENDPOINT_SPECS]


def make_endpoint(spec: EndpointSpec, return_value=None, *, side_effect=None):
    client = Mock()
    client.request = AsyncMock(return_value=return_value, side_effect=side_effect)
    return spec.cls(client), client


@pytest.mark.parametrize("spec", ENDPOINT_SPECS, ids=SPEC_IDS)
def test_path_and_items_key(spec: EndpointSpec):
    ep, _ = make_endpoint(spec)
    assert ep.path == spec.path


@pytest.mark.parametrize("spec", ENDPOINT_SPECS, ids=SPEC_IDS)
@pytest.mark.asyncio
async def test_list_returns_response_model(spec: EndpointSpec):
    ep, client = make_endpoint(spec, return_value=spec.list_response())
    result = await ep.list()

    # Verb/path
    args, kwargs = client.request.await_args
    assert args[0] == "GET"
    assert args[1] == spec.path
    assert "params" in kwargs

    # The list response is validated into the endpoint's response model and
    # contains the parsed records as model instances.
    records = result.shifts if spec.path == "shifts" else result.items
    assert len(records) == 1
    assert isinstance(records[0], spec.model)


@pytest.mark.parametrize("spec", ENDPOINT_SPECS, ids=SPEC_IDS)
@pytest.mark.asyncio
async def test_retrieve_returns_model(spec: EndpointSpec):
    if not spec.has_retrieve:
        pytest.skip(f"{spec.cls.__name__} has no retrieve()")
    record = _record(spec.path)
    ep, client = make_endpoint(spec, return_value=record)
    result = await ep.retrieve(spec.id_value)

    args, _ = client.request.await_args
    assert args[0] == "GET"
    assert args[1] == f"{spec.path}/{spec.id_value}"
    assert isinstance(result, spec.model)


@pytest.mark.parametrize("spec", ENDPOINT_SPECS, ids=SPEC_IDS)
@pytest.mark.asyncio
async def test_create_returns_model(spec: EndpointSpec):
    if not spec.has_create:
        pytest.skip(f"{spec.cls.__name__} has no create()")
    record = _record(spec.path)
    ep, client = make_endpoint(spec, return_value=record)
    result = await ep.create(dict(record))

    args, kwargs = client.request.await_args
    assert args[0] == "POST"
    assert args[1] == spec.path
    assert kwargs["json"] == record
    assert isinstance(result, spec.model)


@pytest.mark.parametrize("spec", ENDPOINT_SPECS, ids=SPEC_IDS)
@pytest.mark.asyncio
async def test_update_returns_model(spec: EndpointSpec):
    if not spec.has_update:
        pytest.skip(f"{spec.cls.__name__} has no update()")
    record = _record(spec.path)
    ep, client = make_endpoint(spec, return_value=record)
    result = await ep.update(spec.id_value, {"name": "Updated"})

    args, kwargs = client.request.await_args
    assert args[0] == "POST"
    assert args[1] == spec.path
    # update() injects the id into the payload before sending.
    assert kwargs["json"]["id"] == spec.id_value
    assert isinstance(result, spec.model)


@pytest.mark.parametrize("spec", ENDPOINT_SPECS, ids=SPEC_IDS)
@pytest.mark.asyncio
async def test_delete_calls_delete_verb(spec: EndpointSpec):
    if not spec.has_delete:
        pytest.skip(f"{spec.cls.__name__} has no delete()")
    ep, client = make_endpoint(spec, return_value={})
    await ep.delete(spec.id_value)

    args, _ = client.request.await_args
    assert args[0] == "DELETE"
    assert args[1] == f"{spec.path}/{spec.id_value}"


@pytest.mark.parametrize("spec", ENDPOINT_SPECS, ids=SPEC_IDS)
@pytest.mark.asyncio
async def test_iter_all_yields_model_instances(spec: EndpointSpec):
    page = {spec.items_key: [_record(spec.path)], "cursor": None}
    ep, client = make_endpoint(spec, side_effect=[page])

    items = [item async for item in ep.iter_all()]

    assert len(items) == 1
    assert isinstance(items[0], spec.model)
    # iter_all paginates via GET on the collection path.
    args, _ = client.request.await_args
    assert args[0] == "GET"
    assert args[1] == spec.path

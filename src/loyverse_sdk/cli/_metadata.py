from loyverse_sdk.endpoints import (
    CategoriesEndpoint,
    CustomersEndpoint,
    DiscountsEndpoint,
    EmployeesEndpoint,
    InventoryEndpoint,
    ItemsEndpoint,
    MerchantEndpoint,
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
from loyverse_sdk.endpoints.mixins import (
    CreateMixin,
    DeleteMixin,
    ListMixin,
    UpdateMixin,
)
from loyverse_sdk.models import (
    Category,
    CategoryListResponse,
    Customer,
    CustomerListResponse,
    Discount,
    DiscountListResponse,
    Employee,
    EmployeeListResponse,
    Inventory,
    InventoryListResponse,
    Item,
    ItemListResponse,
    Modifier,
    ModifierListResponse,
    PaymentType,
    PaymentTypeListResponse,
    PosDevice,
    PosDeviceListResponse,
    Receipt,
    ReceiptListResponse,
    Shift,
    ShiftListResponse,
    Store,
    StoreListResponse,
    Supplier,
    SupplierListResponse,
    Tax,
    TaxListResponse,
    Variant,
    VariantListResponse,
    Webhook,
    WebhookListResponse,
)

_ENDPOINT_CLASSES: dict[str, type] = {
    "categories": CategoriesEndpoint,
    "customers": CustomersEndpoint,
    "discounts": DiscountsEndpoint,
    "employees": EmployeesEndpoint,
    "inventory": InventoryEndpoint,
    "items": ItemsEndpoint,
    "merchant": MerchantEndpoint,
    "modifiers": ModifiersEndpoint,
    "payment_types": PaymentTypesEndpoint,
    "pos_devices": PosDevicesEndpoints,
    "receipts": ReceiptsEndpoint,
    "shifts": ShiftsEndpoint,
    "stores": StoresEndpoint,
    "suppliers": SuppliersEndpoint,
    "taxes": TaxesEndpoint,
    "webhooks": WebhooksEndpoint,
    "variants": VariantsEndpoint,
}

_MODEL_MAP: dict[str, tuple[type, type]] = {
    "categories": (CategoryListResponse, Category),
    "customers": (CustomerListResponse, Customer),
    "discounts": (DiscountListResponse, Discount),
    "employees": (EmployeeListResponse, Employee),
    "inventory": (InventoryListResponse, Inventory),
    "items": (ItemListResponse, Item),
    "modifiers": (ModifierListResponse, Modifier),
    "payment_types": (PaymentTypeListResponse, PaymentType),
    "pos_devices": (PosDeviceListResponse, PosDevice),
    "receipts": (ReceiptListResponse, Receipt),
    "shifts": (ShiftListResponse, Shift),
    "stores": (StoreListResponse, Store),
    "suppliers": (SupplierListResponse, Supplier),
    "taxes": (TaxListResponse, Tax),
    "webhooks": (WebhookListResponse, Webhook),
    "variants": (VariantListResponse, Variant),
}

_CREATE_REQUIRED: dict[str, list[str]] = {
    "categories": ["name"],
    "customers": ["name"],
    "discounts": ["type", "name"],
    "items": ["item_name"],
    "pos_devices": ["name", "store_id"],
    "receipts": ["store_id"],
    "suppliers": ["name"],
    "taxes": ["type", "name", "rate"],
    "webhooks": ["url", "type"],
    "variants": ["item_id"],
}

_CREATE_OPTIONAL: dict[str, list[str]] = {
    "categories": ["color (GREY,RED,PINK,ORANGE,GREEN,BLUE,PURPLE,LIME)"],
    "customers": [
        "email",
        "phone_number",
        "address",
        "city",
        "region",
        "postal_code",
        "country_code",
        "note",
        "customer_code",
    ],
    "discounts": ["amount", "percent", "stores"],
    "items": [
        "description",
        "category_id",
        "tax_ids",
        "modifier_ids",
        "image_url",
        "option1_name",
        "option2_name",
        "option3_name",
    ],
    "pos_devices": [],
    "receipts": ["customer_id", "employee_id", "line_items"],
    "suppliers": [
        "contact",
        "email",
        "phone_number",
        "website",
        "address_1",
        "address_2",
        "city",
        "region",
        "postal_code",
        "country_code",
        "note",
    ],
    "taxes": ["stores"],
    "webhooks": [],
    "variants": [
        "sku",
        "cost",
        "price",
        "option1_value",
        "option2_value",
        "option3_value",
        "barcode",
        "default_pricing_type",
    ],
}


def get_listable_resources() -> frozenset[str]:
    return frozenset(
        name for name, cls in _ENDPOINT_CLASSES.items() if issubclass(cls, ListMixin)
    )


def get_creatable_resources() -> frozenset[str]:
    return frozenset(
        name for name, cls in _ENDPOINT_CLASSES.items() if issubclass(cls, CreateMixin)
    )


def get_updatable_resources() -> frozenset[str]:
    return frozenset(
        name for name, cls in _ENDPOINT_CLASSES.items() if issubclass(cls, UpdateMixin)
    )


def get_deletable_resources() -> frozenset[str]:
    return frozenset(
        name for name, cls in _ENDPOINT_CLASSES.items() if issubclass(cls, DeleteMixin)
    )


def get_response_model(resource: str) -> type:
    return _MODEL_MAP[resource][0]


def get_item_model(resource: str) -> type:
    return _MODEL_MAP[resource][1]


def get_required_fields(resource: str) -> list[str]:
    return _CREATE_REQUIRED.get(resource, [])


def get_optional_fields(resource: str) -> list[str]:
    return _CREATE_OPTIONAL.get(resource, [])


def get_endpoint_classes() -> dict[str, type]:
    return dict(_ENDPOINT_CLASSES)


def make_create_epilog() -> str:
    parts: list[str] = ["Required fields per resource:"]
    for resource, required in sorted(_CREATE_REQUIRED.items()):
        req = " ".join(f"--{f}" for f in required)
        opt_list = _CREATE_OPTIONAL.get(resource, [])
        opt = f"  [{', '.join(f'--{f}' for f in opt_list)}]" if opt_list else ""
        parts.append(f"  {resource:15} {req}{opt}")
    return "\n".join(parts)

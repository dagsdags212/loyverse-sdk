import httpx
from loyverse_sdk.auth import Auth
from loyverse_sdk.core.config import config
from loyverse_sdk.exceptions import APIError
from loyverse_sdk.endpoints import (
    CategoriesEndpoint,
    CustomersEndpoint,
    DiscountsEndpoint,
    EmployeesEndpoint,
    ItemsEndpoint,
    MerchantEndpoint,
    ModifiersEndpoint,
    PosDevicesEndpoints,
    ReceiptsEndpoint,
    StoresEndpoint,
    SuppliersEndpoint,
    TaxesEndpoint,
    WebhooksEndpoint,
    VariantsEndpoint,
)


class LoyverseClient:
    """Base class for sending HTTP requests to the Loyverse REST API"""

    def __init__(
        self,
        api_token: str | None = None,
        base_url: str = config.BASE_URL,
        timeout: float = 15.0,
    ):
        self.auth = Auth(api_token)

        # Shared asynchronous client
        self._client = httpx.AsyncClient(
            base_url=base_url, headers=self.auth.headers, timeout=10.0
        )

        self.categories = CategoriesEndpoint(self)
        self.customers = CustomersEndpoint(self)
        self.discounts = DiscountsEndpoint(self)
        self.devices = PosDevicesEndpoints(self)
        self.employees = EmployeesEndpoint(self)
        self.items = ItemsEndpoint(self)
        self.merchant = MerchantEndpoint(self)
        self.modifiers = ModifiersEndpoint(self)
        self.receipts = ReceiptsEndpoint(self)
        self.stores = StoresEndpoint(self)
        self.suppliers = SuppliersEndpoint(self)
        self.taxes = TaxesEndpoint(self)
        self.webhooks = WebhooksEndpoint(self)
        self.variants = VariantsEndpoint(self)

    async def request(self, method: str, path: str, **kwargs) -> dict:
        """Send an HTTP request from the client to the endpoint"""
        resp = await self._client.request(method, path, **kwargs)
        if resp.status_code >= 400:
            try:
                payload = resp.json()
            except Exception:
                payload = resp.text
            raise APIError(resp.status_code, payload)

        try:
            return resp.json()
        except Exception:
            return resp.text

    async def close(self):
        """Close the client instance"""
        await self._client.aclose()

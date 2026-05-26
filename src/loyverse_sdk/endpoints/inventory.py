from loyverse_sdk.core.config import config
from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.endpoints.mixins import (
    ListMixin,
    PaginationMixin,
)
from loyverse_sdk.models import Inventory, InventoryListResponse


class InventoryEndpoint(BaseEndpoint, ListMixin, PaginationMixin):
    path = "inventory"
    items_key = "inventory_levels"

    async def list(
        self,
        *,
        limit: int = config.PAGE_LIMIT,
        cursor: str | None = None,
        store_id: str | None = None,
        variant_ids: str | None = None,
    ):
        params = {}
        if store_id is not None:
            params["store_id"] = store_id
        if variant_ids is not None:
            params["variant_ids"] = variant_ids
        return await super().list(
            limit=limit, cursor=cursor, model=InventoryListResponse, **params
        )

    async def iter_all(self, **kwargs):
        async for item in super().iter_all(**kwargs):
            yield Inventory.model_validate(item)

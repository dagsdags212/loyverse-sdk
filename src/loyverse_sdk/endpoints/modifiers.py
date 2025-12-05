from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.core.config import config
from loyverse_sdk.endpoints.mixins import (
    ListMixin,
    RetrieveMixin,
    PaginationMixin,
)
from loyverse_sdk.models import Modifier, ModifierListResponse


class ModifiersEndpoint(BaseEndpoint, ListMixin, RetrieveMixin, PaginationMixin):
    path = "modifiers"

    async def create(self, payload: dict):
        return await super().create(payload=payload, model=Modifier)

    async def retrieve(self, id: str):
        return await super().retrieve(id, model=Modifier)

    async def update(self, id: str, payload: dict):
        return await super().update(id=id, payload=payload, model=Modifier)

    async def list(self, limit: int = config.PAGE_LIMIT, cursor: str | None = None):
        return await super().list(
            limit=limit, cursor=cursor, model=ModifierListResponse
        )

    async def iter_all(self, **kwargs):
        async for item in super().iter_all(**kwargs):
            yield Modifier.model_validate(item)

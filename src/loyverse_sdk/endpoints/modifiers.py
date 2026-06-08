from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.endpoints.mixins import (
    CreateMixin,
    ListMixin,
    PaginationMixin,
    RetrieveMixin,
    UpdateMixin,
)
from loyverse_sdk.models import Modifier, ModifierListQuery, ModifierListResponse


class ModifiersEndpoint(
    BaseEndpoint, ListMixin, RetrieveMixin, PaginationMixin, CreateMixin, UpdateMixin
):
    path = "modifiers"

    async def create(self, payload: dict):
        return await super().create(payload=payload, model=Modifier)

    async def retrieve(self, id: str):
        return await super().retrieve(id, model=Modifier)

    async def update(self, id: str, payload: dict):
        return await super().update(id=id, payload=payload, model=Modifier)

    async def list(self, query: ModifierListQuery | None = None):
        query = query or ModifierListQuery()
        return await super().list(model=ModifierListResponse, **query.to_params())

    async def iter_all(self, query: ModifierListQuery | None = None):
        query = query or ModifierListQuery()
        async for item in super().iter_all(**query.to_params()):
            yield Modifier.model_validate(item)

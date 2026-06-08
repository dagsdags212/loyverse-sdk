from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.endpoints.mixins import (
    ListMixin,
    PaginationMixin,
    RetrieveMixin,
)
from loyverse_sdk.models import (
    PaymentType,
    PaymentTypeListQuery,
    PaymentTypeListResponse,
)


class PaymentTypesEndpoint(BaseEndpoint, RetrieveMixin, ListMixin, PaginationMixin):
    path = "payment_types"

    async def retrieve(self, id: str):
        return await super().retrieve(id, model=PaymentType)

    async def list(self, query: PaymentTypeListQuery | None = None):
        query = query or PaymentTypeListQuery()
        return await super().list(model=PaymentTypeListResponse, **query.to_params())

    async def iter_all(self, query: PaymentTypeListQuery | None = None):
        query = query or PaymentTypeListQuery()
        async for item in super().iter_all(**query.to_params()):
            yield PaymentType.model_validate(item)

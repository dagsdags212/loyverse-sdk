from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.endpoints.mixins import (
    RetrieveMixin,
)
from loyverse_sdk.models import Merchant


class MerchantEndpoint(BaseEndpoint, RetrieveMixin):
    path = "merchant"

    async def retrieve(self, id: str):
        return await super().retrieve(id, model=Merchant)

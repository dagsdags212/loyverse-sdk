from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.endpoints.mixins import (
    ListMixin,
    PaginationMixin,
    RetrieveMixin,
)
from loyverse_sdk.models import Employee, EmployeeListQuery, EmployeeListResponse


class EmployeesEndpoint(BaseEndpoint, RetrieveMixin, ListMixin, PaginationMixin):
    path = "employees"

    async def retrieve(self, id: str):
        return await super().retrieve(id, model=Employee)

    async def list(self, query: EmployeeListQuery | None = None):
        query = query or EmployeeListQuery()
        return await super().list(model=EmployeeListResponse, **query.to_params())

    async def iter_all(self, query: EmployeeListQuery | None = None):
        query = query or EmployeeListQuery()
        async for item in super().iter_all(**query.to_params()):
            yield Employee.model_validate(item)

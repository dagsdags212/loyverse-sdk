from typing import AsyncGenerator, Type, TypeVar, Generic
from pydantic import BaseModel
from pydantic import ValidationError
from loyverse_api.core.console import console


T = TypeVar("T")


class ListMixin:
    """Mixin for retrieving a single page of records"""

    path: str

    async def list(
        self,
        limit: int = 50,
        cursor: str | None = None,
        model: Type[BaseModel] | None = None,
    ) -> dict:
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        data = await self._get(self.path, params=params)
        if model:
            try:
                return model.model_validate(data)
            except ValidationError:
                console.log("Validation failed, cannot instantiate model")
        return data


class RetrieveMixin:
    """Mixin for retrieving a single record using an id"""

    path: str

    async def retrieve(self, id: str, model: Type[BaseModel] | None = None):
        data = await self._get(f"{self.path}/{id}")
        if model:
            try:
                return model.model_validate(data)
            except ValidationError:
                console.log("Validation failed, cannot instantiate model")

        return data


class CreateMixin:
    """Mixin for creating a new record from the client"""

    path: str

    async def create(
        self, payload: dict | Type[BaseModel], model: Type[BaseModel] | None = None
    ):
        json = payload.model_dump() if isinstance(payload, BaseModel) else payload
        data = await self._post(f"{self.path}", json=json)
        if model:
            return model.model_validate(data)

        return data


class UpdateMixin:
    """Mixin for updating a record from the client"""

    path: str

    async def update(
        self, id: str, payload: dict, model: Type[BaseModel] | None = None
    ):
        payload["id"] = id
        data = await self._post(f"{self.path}", json=payload)
        if model:
            return model.model_validate(data)
        return data


class DeleteMixin:
    """Mixin for deleting a record from the client"""

    path: str

    async def delete(self, id: str) -> list[str]:
        return await self._delete(f"{self.path}/{id}")


class PaginationMixin(Generic[T]):
    """Mixin for retrieving records across multiple pages"""

    path: str

    async def list_paginated(
        self,
        limit: int = 250,
        cursor: str | None = None,
    ) -> dict:
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        return await self._get(self.path, params=params)

    async def iter_all(self, limit: int = 250) -> AsyncGenerator[T, None]:
        """Async generator to iterate over all items across all pages"""
        cursor = None
        while True:
            resp = await self.list_paginated(cursor=cursor, limit=limit)
            records = resp.get(self.path)
            for item in records:
                yield item

            cursor = resp.get("cursor")

            if not cursor:
                break


class CrudMixin(CreateMixin, RetrieveMixin, UpdateMixin, DeleteMixin):
    """Composed mixin for performing CRUD operation from the client"""

    ...

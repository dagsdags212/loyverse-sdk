from collections.abc import AsyncGenerator

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from loyverse_sdk.core.console import console
from loyverse_sdk.exceptions import PaginationError, ValidationError


class ListMixin:
    """Mixin for retrieving a single page of records."""

    path: str

    async def list(
        self,
        model: type[BaseModel] | None = None,
        **params: object,
    ) -> dict:
        data = await self._get(self.path, params=params)
        if model:
            try:
                return model.model_validate(data)
            except PydanticValidationError as e:
                console.log(f"[red]Validation failed for {model.__name__}[/red]")
                raise ValidationError(
                    message=str(e),
                    validation_errors=e.errors(),
                    model_name=model.__name__,
                ) from e

        return data


class RetrieveMixin:
    """Mixin for retrieving a single record using an id"""

    path: str

    async def retrieve(self, id: str, model: type[BaseModel] | None = None):
        data = await self._get(f"{self.path}/{id}")
        if model:
            try:
                return model.model_validate(data)
            except PydanticValidationError as e:
                console.log(f"[red]Validation failed for {model.__name__}[/red]")
                raise ValidationError(
                    message=str(e),
                    validation_errors=e.errors(),
                    model_name=model.__name__,
                ) from e

        return data


class CreateMixin:
    """Mixin for creating a new record from the client"""

    path: str

    async def create(
        self, payload: dict | BaseModel, model: type[BaseModel] | None = None
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
        self, id: str, payload: dict, model: type[BaseModel] | None = None
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


class PaginationMixin[T]:
    """Mixin for retrieving records across multiple pages."""

    path: str

    async def list_paginated(
        self,
        limit: int = 250,
        **params: object,
    ) -> dict:
        default_params = {"limit": limit}
        if params:
            default_params.update(params)
        return await self._get(self.path, params=default_params)

    async def iter_all(
        self,
        limit: int = 250,
        **params: object,
    ) -> AsyncGenerator[T, None]:
        """
        Async generator to iterate over all items across all pages.

        Yields individual items from paginated API responses, automatically
        handling cursor-based pagination until all pages are consumed.

        Raises:
            PaginationError: If pagination metadata is missing or invalid
        """
        cursor = None
        seen_cursors: set[str] = set()

        while True:
            call_params: dict[str, object] = {"limit": limit, **params}
            if cursor:
                call_params["cursor"] = cursor

            resp = await self.list_paginated(**call_params)

            # Validate response structure
            if not isinstance(resp, dict):
                raise PaginationError(
                    f"Expected dict response for pagination, got {type(resp).__name__}"
                )

            items_key = getattr(self, "items_key", None) or self.path
            records = resp.get(items_key)
            if records is None:
                raise PaginationError(
                    f"Response missing expected key '{items_key}' for records"
                )

            if not isinstance(records, list):
                raise PaginationError(
                    f"Expected list of records, got {type(records).__name__}"
                )

            # Yield each record
            for item in records:
                yield item

            # Get next cursor
            cursor = resp.get("cursor")

            # Check for pagination loop (cursor we've seen before)
            if cursor and cursor in seen_cursors:
                raise PaginationError(
                    f"Pagination loop detected - cursor '{cursor}' seen multiple times"
                )

            if cursor:
                seen_cursors.add(cursor)
            else:
                # No more pages
                break


class CrudMixin(CreateMixin, RetrieveMixin, UpdateMixin, DeleteMixin):
    """Composed mixin for performing CRUD operation from the client"""

    ...

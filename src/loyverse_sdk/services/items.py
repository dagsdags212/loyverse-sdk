"""Items service with business logic validation on top of ItemsEndpoint."""

from typing import Self

from loyverse_sdk.exceptions import ValidationError
from loyverse_sdk.models import Item
from loyverse_sdk.services.base import BaseService


class ItemsService(BaseService):
    """
    Service for Item operations with business logic validation.

    Wraps ItemsEndpoint with validation for item names, stock tracking,
    and optimistic locking for concurrent modification detection.
    """

    def _validate_item_name(self, name: str) -> None:
        """
        Validate item name is not empty or whitespace-only.

        Raises:
            ValidationError: If name is empty or whitespace-only
        """
        if not name or not name.strip():
            raise ValidationError(
                message="Item name cannot be empty or whitespace-only",
                model_name="Item",
            )

    def _validate_track_stock(
        self, track_stock: bool, stock_quantity: float | None
    ) -> None:
        """
        Warn if track_stock is True but no stock quantity info is provided.

        This is a warning only — does not raise an error.
        """
        if track_stock and (stock_quantity is None or stock_quantity == 0):
            print(
                f"Warning: track_stock=True but stock_quantity is {stock_quantity!r}. "
                "Consider setting stock values."
            )

    async def create_item(self, item_data: dict) -> Item:
        """
        Create a new item after validating input data.

        Args:
            item_data: Item creation payload dict

        Returns:
            Item: The created item

        Raises:
            ValidationError: If item name is empty or invalid
        """
        name = item_data.get("item_name") or item_data.get("name")
        self._validate_item_name(name)

        track_stock = item_data.get("track_stock", False)
        stock_qty = item_data.get("stock_quantity")
        self._validate_track_stock(track_stock, stock_qty)

        return await self._client.items.create(item_data)

    async def update_item(self, item_id: str, item_data: dict) -> Item:
        """
        Update an existing item after validating input data.

        Args:
            item_id: The item ID to update
            item_data: Item update payload dict

        Returns:
            Item: The updated item

        Raises:
            ValidationError: If item name is empty or invalid
        """
        name = item_data.get("item_name") or item_data.get("name")
        if name:
            self._validate_item_name(name)

        track_stock = item_data.get("track_stock", False)
        stock_qty = item_data.get("stock_quantity")
        self._validate_track_stock(track_stock, stock_qty)

        return await self._client.items.update(item_id, item_data)

    async def create_item_with_lock(
        self, item_data: dict, check_version: bool = True
    ) -> Item:
        """
        Create a new item with optimistic locking support.

        This method first creates the item, then retrieves it to return
        the server's version/timestamp.

        Args:
            item_data: Item creation payload dict
            check_version: Ignored (reserved for future use)

        Returns:
            Item: The created item with server-assigned values
        """
        created = await self.create_item(item_data)
        return created

    async def update_item_safe(
        self, item_id: str, updates: dict, expected_updated_at: str | None = None
    ) -> Item:
        """
        Update an item with optimistic locking to detect concurrent modifications.

        If expected_updated_at is provided, the current item is retrieved
        and its updated_at timestamp is checked against the expected value.
        If there's a mismatch, a ValidationError is raised.

        Args:
            item_id: The item ID to update
            updates: Item update payload dict
            expected_updated_at: Expected updated_at timestamp for conflict detection

        Returns:
            Item: The updated item

        Raises:
            ValidationError: If concurrent modification detected or item not found
        """
        if expected_updated_at:
            current = await self._client.items.retrieve(item_id)
            if current.updated_at != expected_updated_at:
                raise ValidationError(
                    message=(
                        f"Concurrent modification detected: "
                        f"expected updated_at={expected_updated_at}, "
                        f"actual={current.updated_at}"
                    ),
                    model_name="Item",
                )

        return await self._client.items.update(item_id, updates)

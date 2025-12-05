from typing import TypeVar
from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class BaseEndpoint:
    path: str
    client: "LoyverseClient"

    def __init__(self, client: "LoyverseClient") -> None:
        self.client = client

    async def _get(self, path: str, **kwargs):
        """Send a GET request from the client"""
        return await self.client.request("GET", path, **kwargs)

    async def _post(self, path: str, **kwargs):
        return await self.client.request("POST", path, **kwargs)

    async def _patch(self, path: str, **kwargs):
        return await self.client.request("PATCH", path, **kwargs)

    async def _put(self, path: str, **kwargs):
        return await self.client.request("PUT", path, **kwargs)

    async def _delete(self, path: str, **kwargs):
        return await self.client.request("DELETE", path, **kwargs)

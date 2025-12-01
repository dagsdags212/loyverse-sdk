from uuid import UUID
from typing import Optional, Hashable, Any
import httpx
from pydantic import BaseModel
from loyverse_api.core.config import config
from loyverse_api.core.console import console


class BaseEndpoint(BaseModel):
    endpoint: str
    base_url: str
    api_key: Optional[str] = None
    headers: dict = {}
    params: dict = {"limit": config.limit}
    data: dict = {}
    debug: bool = False

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        if self.api_key is None:
            raise Exception(
                "API key not found, provide it as an named parameter or in a .env file"
            )

        self.headers["Authorization"] = f"Bearer {self.api_key}"

    @property
    def url(self) -> str:
        return f"{self.base_url}/{self.endpoint}"

    def set_limit(self, limit: int, debug: bool = False) -> None:
        """Update the `limit` parameter to the specified value"""
        assert limit > 0, "limit should be a positive integer"
        if debug:
            console.log(f"limit set to {limit}")
        self.params["limit"] = limit

    def get(self, cursor: str | None = None) -> tuple[dict, str | None] | None:
        """Send a GET request to the endpoint"""
        if self.api_key is None:
            raise ValueError("API key not provided")

        if cursor:
            self.params["cursor"] = cursor

        try:
            resp = httpx.get(self.url, params=self.params, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()

            return data.get(self.endpoint, []), data.get("cursor")

        except httpx.HTTPStatusError as exc:
            console.print(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}"
            )
            return

    def post(self, data: dict[Hashable, Any]) -> dict[Hashable, Any]:
        """Send a POST request to the endpoint, passing in the data"""
        try:
            resp = httpx.post(self.url, json=data, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            console.print(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}"
            )
            return {"success": False}

    def put(self, id: UUID | str, data: dict[Hashable, Any]) -> None:
        """Send a PUT request to the endpoint, returning the updated record"""
        raise NotImplementedError

    def delete(self, id: UUID | str) -> dict[Hashable, Any]:
        """Send a DELETE request to the endpoint, returning the deleted record"""
        try:
            url = f"{self.url}/{id}"
            resp = httpx.delete(url, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            console.print(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}"
            )
            return {"success": False}

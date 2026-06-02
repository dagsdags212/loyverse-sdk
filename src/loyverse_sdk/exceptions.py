"""
Comprehensive exception classes for the Loyverse SDK.

This module provides a hierarchy of exceptions that map to common API error scenarios,
network issues, and SDK-specific errors. Using specific exception types allows for
better error handling and more meaningful error messages.
"""

from typing import Any


class LoyverseSDKError(Exception):
    """
    Base exception for all Loyverse SDK errors.

    All custom exceptions in the SDK inherit from this class,
    making it easy to catch any SDK-related error.
    """

    pass


class APIError(LoyverseSDKError):
    """
    Base exception for HTTP API errors from the Loyverse API.

    This exception is raised when the API returns an HTTP error status code (>= 400).
    More specific exceptions inherit from this class for common HTTP status codes.

    Attributes:
        status_code (int): The HTTP status code returned by the API
        payload (Any): The response body, typically a dict with error details or a string
        message (str): A descriptive error message
        endpoint (str): The API endpoint that was called (optional)
    """

    def __init__(
        self,
        status_code: int,
        payload: Any,
        message: str | None = None,
        endpoint: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.payload = payload
        self.endpoint = endpoint

        # Build a comprehensive error message
        if message:
            error_msg = message
        else:
            error_msg = f"Loyverse API returned {status_code} error"

        if endpoint:
            error_msg = f"{error_msg} for endpoint '{endpoint}'"

        # Add payload details if available
        if isinstance(payload, dict):
            if "message" in payload:
                error_msg = f"{error_msg}: {payload['message']}"
            elif "detail" in payload:
                error_msg = f"{error_msg}: {payload['detail']}"
            elif "error" in payload:
                error_msg = f"{error_msg}: {payload['error']}"
        elif isinstance(payload, str) and payload:
            error_msg = f"{error_msg}: {payload}"

        self.message = error_msg
        super().__init__(error_msg)


class BadRequestError(APIError):
    """
    Exception raised for HTTP 400 Bad Request errors.

    Indicates that the request was malformed or contained invalid parameters.
    Check the payload for details about what was invalid.
    """

    def __init__(self, payload: Any, endpoint: str | None = None) -> None:
        super().__init__(
            status_code=400,
            payload=payload,
            message="Bad request - invalid parameters or malformed request",
            endpoint=endpoint,
        )


class AuthenticationError(APIError):
    """
    Exception raised for HTTP 401 Unauthorized errors.

    Indicates that the API token is missing, invalid, or expired.
    Verify that your LOYVERSE_API_TOKEN is correct and has not expired.
    """

    def __init__(self, payload: Any, endpoint: str | None = None) -> None:
        super().__init__(
            status_code=401,
            payload=payload,
            message="Authentication failed - invalid or missing API token",
            endpoint=endpoint,
        )


class ForbiddenError(APIError):
    """
    Exception raised for HTTP 403 Forbidden errors.

    Indicates that authentication succeeded but the token does not have
    permission to access the requested resource or perform the operation.
    """

    def __init__(self, payload: Any, endpoint: str | None = None) -> None:
        super().__init__(
            status_code=403,
            payload=payload,
            message="Access forbidden - insufficient permissions",
            endpoint=endpoint,
        )


class NotFoundError(APIError):
    """
    Exception raised for HTTP 404 Not Found errors.

    Indicates that the requested resource (e.g., receipt, customer, item) does not exist.
    Verify that the ID or parameters you're using are correct.
    """

    def __init__(
        self, payload: Any, endpoint: str | None = None, resource_id: str | None = None
    ) -> None:
        message = "Resource not found"
        if resource_id:
            message = f"Resource with ID '{resource_id}' not found"

        super().__init__(
            status_code=404, payload=payload, message=message, endpoint=endpoint
        )
        self.resource_id = resource_id


class RateLimitError(APIError):
    """
    Exception raised for HTTP 429 Too Many Requests errors.

    Indicates that you've exceeded the API rate limits.
    Implement exponential backoff or reduce request frequency.

    Attributes:
        retry_after (int | None): Seconds to wait before retrying (from Retry-After header)
    """

    def __init__(
        self, payload: Any, endpoint: str | None = None, retry_after: int | None = None
    ) -> None:
        message = "Rate limit exceeded"
        if retry_after:
            message = f"{message} - retry after {retry_after} seconds"

        super().__init__(
            status_code=429, payload=payload, message=message, endpoint=endpoint
        )
        self.retry_after = retry_after


class ServerError(APIError):
    """
    Exception raised for HTTP 5xx server errors.

    Indicates an internal error on the Loyverse API server.
    These errors are typically temporary - retry the request after a delay.
    """

    def __init__(
        self, status_code: int, payload: Any, endpoint: str | None = None
    ) -> None:
        super().__init__(
            status_code=status_code,
            payload=payload,
            message=f"Server error ({status_code}) - the API is experiencing issues",
            endpoint=endpoint,
        )


class ConfigurationError(LoyverseSDKError):
    """
    Exception raised for SDK configuration issues.

    Examples:
    - Missing API token
    - Invalid base URL
    - Missing required environment variables
    """

    pass


class ValidationError(LoyverseSDKError):
    """
    Exception raised when response data fails Pydantic validation.

    This indicates a mismatch between the expected data structure
    and what the API actually returned. This could mean:
    - The API response format changed
    - The SDK models are out of date
    - The API returned unexpected data

    Attributes:
        validation_errors (Any): The original Pydantic validation errors
        model_name (str | None): The name of the model that failed validation
    """

    def __init__(
        self, message: str, validation_errors: Any = None, model_name: str | None = None
    ) -> None:
        self.validation_errors = validation_errors
        self.model_name = model_name

        error_msg = f"Data validation failed: {message}"
        if model_name:
            error_msg = f"Data validation failed for {model_name}: {message}"

        super().__init__(error_msg)


class PaginationError(LoyverseSDKError):
    """
    Exception raised when pagination fails or produces invalid results.

    Examples:
    - Invalid cursor
    - Pagination loop detected
    - Missing pagination metadata
    """

    pass


class NetworkError(LoyverseSDKError):
    """
    Exception raised for network-related issues.

    This wraps underlying network errors like:
    - Connection timeouts
    - DNS resolution failures
    - Connection refused
    - SSL/TLS errors

    Attributes:
        original_error (Exception): The underlying exception that caused this error
    """

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        self.original_error = original_error

        error_msg = f"Network error: {message}"
        if original_error:
            error_msg = f"{error_msg} (caused by {type(original_error).__name__}: {original_error})"

        super().__init__(error_msg)


class ResourceNotFoundError(LoyverseSDKError):
    """
    Exception raised when a query returns empty results unexpectedly.

    This is different from NotFoundError (404) - this is used when a valid API
    request succeeds but returns no data when data was expected.

    Example: Fetching the latest receipt but no receipts exist in the system.
    """

    def __init__(self, message: str, resource_type: str | None = None) -> None:
        self.resource_type = resource_type

        error_msg = f"No data found: {message}"
        if resource_type:
            error_msg = f"No {resource_type} found: {message}"

        super().__init__(error_msg)


class ExportError(LoyverseSDKError):
    """
    Exception raised when database export operations fail.

    This exception is raised during DuckDB export operations when:
    - Database connection fails
    - Table creation fails
    - Data insertion fails
    - Batch processing encounters errors
    - Schema initialization fails

    Attributes:
        resource_name (str | None): Name of the resource being exported when error occurred
    """

    def __init__(self, message: str, resource_name: str | None = None) -> None:
        self.resource_name = resource_name

        error_msg = message
        if resource_name:
            error_msg = f"Export error for '{resource_name}': {message}"

        super().__init__(error_msg)

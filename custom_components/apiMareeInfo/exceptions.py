"""Custom exceptions for apiMareeInfo."""


class ApiError(Exception):
    """Base exception for API errors (HTTP 4xx/5xx)."""

    def __init__(
        self,
        message: str,
        url: str = "",
        source_name: str = "unknown",
        status_code: int | None = None,
    ) -> None:
        self.url = url
        self.source_name = source_name
        self.status_code = status_code
        super().__init__(message)


class RateLimitError(ApiError):
    """Raised when API returns HTTP 429 (Too Many Requests)."""


class NotFoundError(ApiError):
    """Raised when API returns HTTP 404 (Not Found)."""


class NetworkError(ApiError):
    """Raised on connection/timeout/DNS errors (no HTTP status code)."""

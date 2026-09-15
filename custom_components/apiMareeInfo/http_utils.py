"""Shared HTTP utilities for apiMareeInfo."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import ApiError, NetworkError, NotFoundError, RateLimitError

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
DEFAULT_SSL = False
DEFAULT_MAX_RETRIES = 3

DEFAULT_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "fr,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
}


def _classify_error(
    error: aiohttp.ClientError,
    url: str,
    source_name: str,
) -> ApiError:
    """Classify an aiohttp.ClientError into a specific exception type."""
    if isinstance(error, aiohttp.ClientResponseError):
        status = error.status
        if status == 429:
            return RateLimitError(
                f"Rate limited by {source_name}",
                url=url,
                source_name=source_name,
                status_code=status,
            )
        if status == 404:
            return NotFoundError(
                f"Resource not found: {source_name}",
                url=url,
                source_name=source_name,
                status_code=status,
            )
        if 400 <= status < 500:
            return ApiError(
                f"Client error {status} from {source_name}",
                url=url,
                source_name=source_name,
                status_code=status,
            )
        if 500 <= status < 600:
            return ApiError(
                f"Server error {status} from {source_name}",
                url=url,
                source_name=source_name,
                status_code=status,
            )
    return NetworkError(
        f"Network error from {source_name}: {error}",
        url=url,
        source_name=source_name,
    )


def _is_retriable(exc: Exception) -> bool:
    """Return True if the exception is worth retrying."""
    if isinstance(exc, NetworkError):
        return True
    if isinstance(exc, ApiError) and exc.status_code is not None:
        return exc.status_code == 429 or exc.status_code >= 500
    return False


async def async_fetch_json(
    url: str,
    session: aiohttp.ClientSession | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    ssl: bool = DEFAULT_SSL,
    source_name: str = "unknown",
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> dict[str, Any]:
    """Fetch JSON from a URL with retry and structured error handling.

    Args:
        url: The URL to fetch.
        session: Optional aiohttp session. If None, a new session is created.
        params: Optional query parameters.
        headers: Optional HTTP headers. Defaults to browser-like headers.
        timeout: Request timeout in seconds.
        ssl: Whether to verify SSL certificates.
        source_name: Name of the source for logging purposes.
        max_retries: Maximum number of retry attempts (default 3).

    Returns:
        Parsed JSON response.

    Raises:
        RateLimitError: On HTTP 429 after retries exhausted.
        NotFoundError: On HTTP 404 (no retry).
        ApiError: On other HTTP errors after retries exhausted.
        NetworkError: On connection/timeout errors after retries exhausted.
    """
    if headers is None:
        headers = DEFAULT_HEADERS

    @retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception(_is_retriable),
        reraise=True,
    )
    async def _fetch(s: aiohttp.ClientSession) -> dict[str, Any]:
        try:
            async with s.get(
                url, params=params, headers=headers, timeout=timeout, ssl=ssl
            ) as response:
                response.raise_for_status()
                return await response.json(content_type=None)
        except aiohttp.ClientError as error:
            classified = _classify_error(error, url, source_name)
            if _is_retriable(classified):
                _LOGGER.warning(
                    "[%s] GET %s -> %s (retriable)",
                    source_name,
                    url,
                    classified,
                )
            raise classified from error

    if session:
        return await _fetch(session)
    else:
        async with aiohttp.ClientSession() as local_session:
            return await _fetch(local_session)

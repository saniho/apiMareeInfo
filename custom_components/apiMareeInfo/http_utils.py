"""Shared HTTP utilities for apiMareeInfo."""

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
DEFAULT_SSL = False

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


async def async_fetch_json(
    url: str,
    session: aiohttp.ClientSession | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    ssl: bool = DEFAULT_SSL,
    error_return: dict[str, Any] | None = None,
    source_name: str = "unknown",
) -> dict[str, Any]:
    """Fetch JSON from a URL with standardized error handling.

    Args:
        url: The URL to fetch.
        session: Optional aiohttp session. If None, a new session is created.
        params: Optional query parameters.
        headers: Optional HTTP headers. Defaults to browser-like headers.
        timeout: Request timeout in seconds.
        ssl: Whether to verify SSL certificates.
        error_return: Value to return on error. Defaults to {"error": "UNKERROR_001"}.
        source_name: Name of the source for logging purposes.

    Returns:
        Parsed JSON response, or error dict on failure.
    """
    if headers is None:
        headers = DEFAULT_HEADERS

    if error_return is None:
        error_return = {"error": "UNKERROR_001"}

    async def _fetch(s: aiohttp.ClientSession) -> dict[str, Any]:
        try:
            async with s.get(
                url, params=params, headers=headers, timeout=timeout, ssl=ssl
            ) as response:
                response.raise_for_status()
                return await response.json(content_type=None)
        except aiohttp.ClientError as error:
            _LOGGER.error("Error getting data from %s (%s): %s", source_name, url, error)
            return error_return

    if session:
        return await _fetch(session)
    else:
        async with aiohttp.ClientSession() as local_session:
            return await _fetch(local_session)

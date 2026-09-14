"""Tests for http_utils module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.apiMareeInfo.http_utils import (
    DEFAULT_HEADERS,
    DEFAULT_TIMEOUT,
    DEFAULT_SSL,
    async_fetch_json,
)


class TestDefaultConstants:
    """Test default constant values."""

    def test_default_timeout(self):
        assert DEFAULT_TIMEOUT == 30

    def test_default_ssl(self):
        assert DEFAULT_SSL is False

    def test_default_headers_contain_user_agent(self):
        assert "user-agent" in DEFAULT_HEADERS
        assert "Chrome" in DEFAULT_HEADERS["user-agent"]

    def test_default_headers_contain_accept(self):
        assert "accept" in DEFAULT_HEADERS

    def test_default_headers_contain_cache_control(self):
        assert DEFAULT_HEADERS["cache-control"] == "no-cache"


class TestAsyncFetchJson:
    """Test async_fetch_json function."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful JSON fetch."""
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={"key": "value"})
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        result = await async_fetch_json(
            "http://example.com/api",
            session=mock_session,
            source_name="test",
        )

        assert result == {"key": "value"}
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_with_params(self):
        """Test fetch with query parameters."""
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={"result": "ok"})
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        params = {"lat": "48.5", "lon": "-2.0"}
        await async_fetch_json(
            "http://example.com/api",
            session=mock_session,
            params=params,
            source_name="test",
        )

        call_kwargs = mock_session.get.call_args
        assert call_kwargs[1]["params"] == params

    @pytest.mark.asyncio
    async def test_fetch_with_custom_headers(self):
        """Test fetch with custom headers."""
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={})
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        custom_headers = {"Authorization": "Bearer token123"}
        await async_fetch_json(
            "http://example.com/api",
            session=mock_session,
            headers=custom_headers,
            source_name="test",
        )

        call_kwargs = mock_session.get.call_args
        assert call_kwargs[1]["headers"] == custom_headers

    @pytest.mark.asyncio
    async def test_fetch_with_custom_timeout(self):
        """Test fetch with custom timeout."""
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={})
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        await async_fetch_json(
            "http://example.com/api",
            session=mock_session,
            timeout=60,
            source_name="test",
        )

        call_kwargs = mock_session.get.call_args
        assert call_kwargs[1]["timeout"] == 60

    @pytest.mark.asyncio
    async def test_fetch_client_error_returns_default(self):
        """Test that client errors return default error dict."""
        import aiohttp

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Connection failed"))

        result = await async_fetch_json(
            "http://example.com/api",
            session=mock_session,
            source_name="test",
        )

        assert result == {"error": "UNKERROR_001"}

    @pytest.mark.asyncio
    async def test_fetch_client_error_returns_custom_error(self):
        """Test that client errors return custom error dict."""
        import aiohttp

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Timeout"))

        custom_error = {"errors": {"key": "Communication error"}}
        result = await async_fetch_json(
            "http://example.com/api",
            session=mock_session,
            error_return=custom_error,
            source_name="test",
        )

        assert result == custom_error

    @pytest.mark.asyncio
    async def test_fetch_creates_session_if_none(self):
        """Test that a new session is created if none provided."""
        with patch("custom_components.apiMareeInfo.http_utils.aiohttp.ClientSession") as mock_cls:
            mock_session = MagicMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={"test": True})
            mock_response.raise_for_status = MagicMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=False)
            mock_session.get = MagicMock(return_value=mock_response)

            result = await async_fetch_json(
                "http://example.com/api",
                source_name="test",
            )

            assert result == {"test": True}
            mock_cls.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_uses_default_headers_when_none(self):
        """Test that default headers are used when none provided."""
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={})
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        await async_fetch_json(
            "http://example.com/api",
            session=mock_session,
            source_name="test",
        )

        call_kwargs = mock_session.get.call_args
        assert call_kwargs[1]["headers"] == DEFAULT_HEADERS

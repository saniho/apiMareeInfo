"""Tests for http_utils module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp

from custom_components.apiMareeInfo.http_utils import (
    DEFAULT_HEADERS,
    DEFAULT_TIMEOUT,
    DEFAULT_SSL,
    DEFAULT_MAX_RETRIES,
    async_fetch_json,
    _classify_error,
    _is_retriable,
)
from custom_components.apiMareeInfo.exceptions import (
    ApiError,
    NetworkError,
    NotFoundError,
    RateLimitError,
)


class TestDefaultConstants:
    """Test default constant values."""

    def test_default_timeout(self):
        assert DEFAULT_TIMEOUT == 30

    def test_default_ssl(self):
        assert DEFAULT_SSL is False

    def test_default_max_retries(self):
        assert DEFAULT_MAX_RETRIES == 3

    def test_default_headers_contain_user_agent(self):
        assert "user-agent" in DEFAULT_HEADERS
        assert "Chrome" in DEFAULT_HEADERS["user-agent"]

    def test_default_headers_contain_accept(self):
        assert "accept" in DEFAULT_HEADERS

    def test_default_headers_contain_cache_control(self):
        assert DEFAULT_HEADERS["cache-control"] == "no-cache"


class TestClassifyError:
    """Test _classify_error function."""

    def test_429_returns_rate_limit_error(self):
        error = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=429
        )
        result = _classify_error(error, "http://test.com", "test")
        assert isinstance(result, RateLimitError)
        assert result.status_code == 429
        assert result.url == "http://test.com"
        assert result.source_name == "test"

    def test_404_returns_not_found_error(self):
        error = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=404
        )
        result = _classify_error(error, "http://test.com", "test")
        assert isinstance(result, NotFoundError)
        assert result.status_code == 404

    def test_400_returns_api_error(self):
        error = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=400
        )
        result = _classify_error(error, "http://test.com", "test")
        assert isinstance(result, ApiError)
        assert result.status_code == 400
        assert not isinstance(result, NotFoundError)
        assert not isinstance(result, RateLimitError)

    def test_500_returns_api_error(self):
        error = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=500
        )
        result = _classify_error(error, "http://test.com", "test")
        assert isinstance(result, ApiError)
        assert result.status_code == 500

    def test_503_returns_api_error(self):
        error = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=503
        )
        result = _classify_error(error, "http://test.com", "test")
        assert isinstance(result, ApiError)
        assert result.status_code == 503

    def test_connection_error_returns_network_error(self):
        error = aiohttp.ClientError("Connection refused")
        result = _classify_error(error, "http://test.com", "test")
        assert isinstance(result, NetworkError)
        assert result.status_code is None

    def test_timeout_returns_network_error(self):
        error = aiohttp.ServerTimeoutError("Request timed out")
        result = _classify_error(error, "http://test.com", "test")
        assert isinstance(result, NetworkError)
        assert result.status_code is None


class TestIsRetriable:
    """Test _is_retriable function."""

    def test_network_error_is_retriable(self):
        assert _is_retriable(NetworkError("test")) is True

    def test_rate_limit_is_retriable(self):
        assert _is_retriable(RateLimitError("test", status_code=429)) is True

    def test_server_error_is_retriable(self):
        assert _is_retriable(ApiError("test", status_code=500)) is True

    def test_503_is_retriable(self):
        assert _is_retriable(ApiError("test", status_code=503)) is True

    def test_400_is_not_retriable(self):
        assert _is_retriable(ApiError("test", status_code=400)) is False

    def test_404_is_not_retriable(self):
        assert _is_retriable(NotFoundError("test", status_code=404)) is False

    def test_generic_api_error_is_not_retriable(self):
        assert _is_retriable(ApiError("test")) is False

    def test_generic_exception_is_not_retriable(self):
        assert _is_retriable(ValueError("test")) is False


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
    async def test_fetch_raises_network_error(self):
        """Test that connection errors raise NetworkError."""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Connection failed"))

        with pytest.raises(NetworkError):
            await async_fetch_json(
                "http://example.com/api",
                session=mock_session,
                source_name="test",
                max_retries=1,
            )

    @pytest.mark.asyncio
    async def test_fetch_raises_rate_limit_error(self):
        """Test that HTTP 429 raises RateLimitError."""
        mock_session = MagicMock()
        mock_session.get = MagicMock(
            side_effect=aiohttp.ClientResponseError(
                request_info=MagicMock(), history=(), status=429
            )
        )

        with pytest.raises(RateLimitError) as exc_info:
            await async_fetch_json(
                "http://example.com/api",
                session=mock_session,
                source_name="test",
                max_retries=1,
            )
        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_fetch_raises_not_found_error(self):
        """Test that HTTP 404 raises NotFoundError (no retry)."""
        mock_session = MagicMock()
        mock_session.get = MagicMock(
            side_effect=aiohttp.ClientResponseError(
                request_info=MagicMock(), history=(), status=404
            )
        )

        with pytest.raises(NotFoundError):
            await async_fetch_json(
                "http://example.com/api",
                session=mock_session,
                source_name="test",
                max_retries=3,
            )
        # 404 is not retriable, should only be called once
        assert mock_session.get.call_count == 1

    @pytest.mark.asyncio
    async def test_fetch_raises_api_error_on_500(self):
        """Test that HTTP 500 raises ApiError after retries."""
        mock_session = MagicMock()
        mock_session.get = MagicMock(
            side_effect=aiohttp.ClientResponseError(
                request_info=MagicMock(), history=(), status=500
            )
        )

        with pytest.raises(ApiError) as exc_info:
            await async_fetch_json(
                "http://example.com/api",
                session=mock_session,
                source_name="test",
                max_retries=3,
            )
        assert exc_info.value.status_code == 500
        # 500 is retriable, should be called 3 times
        assert mock_session.get.call_count == 3

    @pytest.mark.asyncio
    async def test_fetch_retries_on_network_error(self):
        """Test that network errors are retried."""
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={"key": "value"})
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        # Fail twice, then succeed
        mock_session.get = MagicMock(
            side_effect=[
                aiohttp.ClientError("Connection failed"),
                aiohttp.ClientError("Connection failed"),
                mock_response,
            ]
        )

        result = await async_fetch_json(
            "http://example.com/api",
            session=mock_session,
            source_name="test",
            max_retries=3,
        )

        assert result == {"key": "value"}
        assert mock_session.get.call_count == 3

    @pytest.mark.asyncio
    async def test_fetch_retries_on_500_then_succeeds(self):
        """Test that 500 errors are retried then succeed."""
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={"key": "value"})
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(
            side_effect=[
                aiohttp.ClientResponseError(
                    request_info=MagicMock(), history=(), status=500
                ),
                mock_response,
            ]
        )

        result = await async_fetch_json(
            "http://example.com/api",
            session=mock_session,
            source_name="test",
            max_retries=3,
        )

        assert result == {"key": "value"}
        assert mock_session.get.call_count == 2

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

    @pytest.mark.asyncio
    async def test_fetch_no_retry_on_400(self):
        """Test that 400 errors are not retried."""
        mock_session = MagicMock()
        mock_session.get = MagicMock(
            side_effect=aiohttp.ClientResponseError(
                request_info=MagicMock(), history=(), status=400
            )
        )

        with pytest.raises(ApiError):
            await async_fetch_json(
                "http://example.com/api",
                session=mock_session,
                source_name="test",
                max_retries=3,
            )
        # 400 is not retriable, should only be called once
        assert mock_session.get.call_count == 1

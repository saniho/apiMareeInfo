"""Tests for apiMareeInfo __init__ (async_setup_entry / async_unload_entry)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.apiMareeInfo.const import DOMAIN


@pytest.fixture
def mock_config_entry():
    """Mock a ConfigEntry with minimal data."""
    entry = MagicMock()
    entry.entry_id = "test_entry_123"
    entry.unique_id = "test_unique_123"
    entry.data = {
        "latitude": 48.649,
        "longitude": -2.008,
        "MAX_HOURS": 6,
    }
    entry.options = {}
    entry.async_on_unload = MagicMock()
    entry.add_update_listener = MagicMock(return_value=MagicMock())
    return entry


@pytest.fixture
def mock_hass():
    """Mock HomeAssistant instance."""
    hass = MagicMock()
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.config_entries.async_reload = AsyncMock()
    return hass


@pytest.mark.asyncio
async def test_async_setup_entry_stores_coordinator(mock_hass, mock_config_entry):
    """async_setup_entry should store coordinator in hass.data[DOMAIN]."""
    from custom_components.apiMareeInfo import async_setup_entry

    mock_api = MagicMock()
    mock_api.getinformationport = AsyncMock()
    mock_api.has_error.return_value = False

    with (
        patch("custom_components.apiMareeInfo.apiMareeInfo.ApiMareeInfo", return_value=mock_api),
        patch("custom_components.apiMareeInfo.async_get_clientsession"),
        patch("custom_components.apiMareeInfo.DataUpdateCoordinator") as mock_coord_cls,
    ):
        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coord_cls.return_value = mock_coordinator

        result = await async_setup_entry(mock_hass, mock_config_entry)

    assert result is True
    assert DOMAIN in mock_hass.data
    assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
    mock_hass.config_entries.async_forward_entry_setups.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_setup_entry_returns_true(mock_hass, mock_config_entry):
    """async_setup_entry should always return True on success."""
    from custom_components.apiMareeInfo import async_setup_entry

    mock_api = MagicMock()
    mock_api.getinformationport = AsyncMock()
    mock_api.has_error.return_value = False

    with (
        patch("custom_components.apiMareeInfo.apiMareeInfo.ApiMareeInfo", return_value=mock_api),
        patch("custom_components.apiMareeInfo.async_get_clientsession"),
        patch("custom_components.apiMareeInfo.DataUpdateCoordinator") as mock_coord_cls,
    ):
        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coord_cls.return_value = mock_coordinator

        result = await async_setup_entry(mock_hass, mock_config_entry)

    assert result is True


@pytest.mark.asyncio
async def test_async_setup_entry_registers_update_listener(mock_hass, mock_config_entry):
    """async_setup_entry should register update_listener."""
    from custom_components.apiMareeInfo import async_setup_entry

    mock_api = MagicMock()
    mock_api.getinformationport = AsyncMock()
    mock_api.has_error.return_value = False

    with (
        patch("custom_components.apiMareeInfo.apiMareeInfo.ApiMareeInfo", return_value=mock_api),
        patch("custom_components.apiMareeInfo.async_get_clientsession"),
        patch("custom_components.apiMareeInfo.DataUpdateCoordinator") as mock_coord_cls,
    ):
        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coord_cls.return_value = mock_coordinator

        await async_setup_entry(mock_hass, mock_config_entry)

    mock_config_entry.async_on_unload.assert_called_once()
    mock_config_entry.add_update_listener.assert_called_once()


@pytest.mark.asyncio
async def test_async_unload_entry_removes_coordinator(mock_hass, mock_config_entry):
    """async_unload_entry should remove coordinator from hass.data."""
    from custom_components.apiMareeInfo import async_unload_entry

    mock_hass.data[DOMAIN] = {mock_config_entry.entry_id: MagicMock()}

    result = await async_unload_entry(mock_hass, mock_config_entry)

    assert result is True
    assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]
    mock_hass.config_entries.async_unload_platforms.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_unload_entry_keeps_data_on_failure(mock_hass, mock_config_entry):
    """async_unload_entry should keep data if unload fails."""
    from custom_components.apiMareeInfo import async_unload_entry

    mock_hass.data[DOMAIN] = {mock_config_entry.entry_id: MagicMock()}
    mock_hass.config_entries.async_unload_platforms.return_value = False

    result = await async_unload_entry(mock_hass, mock_config_entry)

    assert result is False
    assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]

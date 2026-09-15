"""Tests for the MareeWeather entity."""
import sys
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from enum import IntFlag

# Patch WeatherEntityFeature if missing (older HA versions)
import homeassistant.components.weather as _weather_mod

if not hasattr(_weather_mod, "WeatherEntityFeature"):

    class _WeatherEntityFeature(IntFlag):
        FORECAST_HOURLY = 1

    _weather_mod.WeatherEntityFeature = _WeatherEntityFeature
    sys.modules["homeassistant.components.weather"].WeatherEntityFeature = (
        _WeatherEntityFeature
    )

from custom_components.apiMareeInfo.weather import MareeWeather, CONDITION_MAP
from custom_components.apiMareeInfo.const import DOMAIN


@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.data = MagicMock()
    coordinator.data.get_port_name.return_value = "Saint-Malo"
    coordinator.data.getcopyright.return_value = "©SHOM"
    coordinator.data.get_current_live_data.return_value = None
    coordinator.data.get_forecast_data.return_value = {}
    return coordinator


@pytest.fixture
def weather(mock_coordinator):
    return MareeWeather(mock_coordinator, "port_123")


# --- basic properties ---


def test_unique_id(weather):
    assert weather.unique_id == "port_123_weather"


def test_name(weather):
    assert weather.name == "Météo"


def test_attribution(weather):
    assert weather.attribution == "Data provided by apiMareeInfo"


def test_humidity(weather):
    assert weather.humidity is None


def test_device_info(weather, mock_coordinator):
    info = weather.device_info
    assert info["identifiers"] == {(DOMAIN, "port_123")}
    assert info["name"] == "Maree Saint-Malo"
    assert info["manufacturer"] == "apiMareeInfo"
    assert info["model"] == "©SHOM"
    assert info["entry_type"] == "service"


# --- _get_current_data ---


def test_get_current_data_live(weather, mock_coordinator):
    mock_coordinator.data.get_current_live_data.return_value = {
        "tempe": 15.2,
        "wind_speed": 20,
        "wind_direction": 180,
        "pressure": 1013,
        "weather_icon": "c0000",
        "visibility": 10,
    }
    data = weather._get_current_data()
    assert data["t"] == 15.2
    assert data["forcevnds"] == 20
    assert data["dirvdegres"] == 180
    assert data["pressure"] == 1013
    assert data["nebu"] == "c0000"
    assert data["visibility"] == 10


def test_get_current_data_forecast_fallback(weather, mock_coordinator):
    mock_coordinator.data.get_current_live_data.return_value = None
    now = datetime.now()
    past = {now: {"t": 12.0, "forcevnds": 10, "dirvdegres": 90, "nebu": "c0030", "pressure": 1010}}
    mock_coordinator.data.get_forecast_data.return_value = past
    data = weather._get_current_data()
    assert data["t"] == 12.0


def test_get_current_data_forecast_no_past(weather, mock_coordinator):
    mock_coordinator.data.get_current_live_data.return_value = None
    future = datetime(2099, 1, 1)
    mock_coordinator.data.get_forecast_data.return_value = {future: {"t": 8.0}}
    data = weather._get_current_data()
    assert data["t"] == 8.0


def test_get_current_data_empty(weather, mock_coordinator):
    mock_coordinator.data.get_current_live_data.return_value = None
    mock_coordinator.data.get_forecast_data.return_value = {}
    assert weather._get_current_data() is None


# --- properties with live data ---


def test_native_temperature_live(weather, mock_coordinator):
    mock_coordinator.data.get_current_live_data.return_value = {"tempe": 18.5}
    assert weather.native_temperature == 18.5


def test_native_wind_speed_live(weather, mock_coordinator):
    mock_coordinator.data.get_current_live_data.return_value = {"wind_speed": 25}
    assert weather.native_wind_speed == 25


def test_wind_bearing_live(weather, mock_coordinator):
    mock_coordinator.data.get_current_live_data.return_value = {"wind_direction": 270}
    assert weather.wind_bearing == 270


def test_cloud_coverage_live(weather, mock_coordinator):
    mock_coordinator.data.get_current_live_data.return_value = {
        "tempe": 15.0,
        "weather_icon": "c0000",
    }
    assert weather.cloud_coverage is None


def test_cloud_coverage_from_forecast(weather, mock_coordinator):
    mock_coordinator.data.get_current_live_data.return_value = None
    now = datetime.now()
    mock_coordinator.data.get_forecast_data.return_value = {
        now: {"t": 12.0, "nuagecouverture": 75}
    }
    assert weather.cloud_coverage == 75


def test_native_pressure_live(weather, mock_coordinator):
    mock_coordinator.data.get_current_live_data.return_value = {"pressure": 1015}
    assert weather.native_pressure == 1015


# --- properties with no data ---


def test_native_temperature_none(weather):
    assert weather.native_temperature is None


def test_native_wind_speed_none(weather):
    assert weather.native_wind_speed is None


def test_wind_bearing_none(weather):
    assert weather.wind_bearing is None


def test_cloud_coverage_none(weather):
    assert weather.cloud_coverage is None


def test_native_pressure_none(weather):
    assert weather.native_pressure is None


# --- _map_condition ---


def test_map_condition_sunny(weather):
    with patch.object(weather, "hass") as mock_hass:
        mock_hass.states.get.return_value = MagicMock(state="above_horizon")
        assert weather._map_condition("c0000") == "sunny"


def test_map_condition_clear_night(weather):
    with patch.object(weather, "hass") as mock_hass:
        mock_hass.states.get.return_value = MagicMock(state="below_horizon")
        assert weather._map_condition("c0000") == "clear-night"


def test_map_condition_partly_cloudy(weather):
    assert weather._map_condition("c0020") == "partlycloudy"
    assert weather._map_condition("c0023") == "partlycloudy"
    assert weather._map_condition("c0025") == "partlycloudy"


def test_map_condition_cloudy(weather):
    for code in ("c0030", "c0043", "c0050", "c0055", "c0060", "c0061", "c0070", "c0080"):
        assert weather._map_condition(code) == "cloudy"


def test_map_condition_rainy(weather):
    for code in ("p0010", "p0020", "p0030", "p0050", "p0060"):
        assert weather._map_condition(code) == "rainy"


def test_map_condition_snowy(weather):
    for code in ("x3050", "x3060", "x7060", "x8030"):
        assert weather._map_condition(code) == "snowy"


def test_map_condition_unknown_defaults_cloudy(weather):
    assert weather._map_condition("unknown_code") == "cloudy"
    assert weather._map_condition("") == "cloudy"


def test_map_condition_sunny_night_forecast(weather):
    night = datetime(2026, 1, 15, 3, 0)
    assert weather._map_condition("c0000", night) == "clear-night"


def test_map_condition_sunny_day_forecast(weather):
    day = datetime(2026, 1, 15, 12, 0)
    assert weather._map_condition("c0000", day) == "sunny"


# --- condition property ---


def test_condition_live_data(weather, mock_coordinator):
    mock_coordinator.data.get_current_live_data.return_value = {"weather_icon": "p0010"}
    with patch.object(weather, "hass") as mock_hass:
        mock_hass.states.get.return_value = MagicMock(state="above_horizon")
        assert weather.condition == "rainy"


def test_condition_forecast_fallback(weather, mock_coordinator):
    mock_coordinator.data.get_current_live_data.return_value = None
    now = datetime.now()
    mock_coordinator.data.get_forecast_data.return_value = {
        now: {"nebu": "x3050"}
    }
    assert weather.condition == "snowy"


def test_condition_no_data(weather, mock_coordinator):
    mock_coordinator.data.get_current_live_data.return_value = None
    mock_coordinator.data.get_forecast_data.return_value = {}
    assert weather.condition == "cloudy"


# --- async_forecast_hourly ---


@pytest.mark.asyncio
async def test_async_forecast_hourly(weather, mock_coordinator):
    now = datetime.now()
    future1 = now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)
    future2 = now.replace(hour=now.hour + 2, minute=0, second=0, microsecond=0)
    mock_coordinator.data.get_forecast_data.return_value = {
        future1: {
            "t": 14.0,
            "forcevnds": 15,
            "dirvdegres": 200,
            "precipitation": 2.5,
            "pressure": 1008,
            "nebu": "p0010",
            "nuagecouverture": 80,
        },
        future2: {
            "t": 13.0,
            "forcevnds": 18,
            "dirvdegres": 210,
            "precipitation": 0.0,
            "pressure": 1010,
            "nebu": "c0000",
            "nuagecouverture": 20,
        },
    }
    with patch.object(weather, "hass") as mock_hass:
        mock_hass.states.get.return_value = MagicMock(state="above_horizon")
        forecasts = await weather.async_forecast_hourly()

    assert len(forecasts) == 2
    assert forecasts[0]["native_temperature"] == 14.0
    assert forecasts[0]["native_wind_speed"] == 15
    assert forecasts[0]["wind_bearing"] == 200
    assert forecasts[0]["native_precipitation"] == 2.5
    assert forecasts[0]["native_pressure"] == 1008
    assert forecasts[0]["condition"] == "rainy"
    assert forecasts[0]["cloud_coverage"] == 80

    assert forecasts[1]["native_temperature"] == 13.0
    assert forecasts[1]["condition"] == "sunny"


@pytest.mark.asyncio
async def test_async_forecast_hourly_skips_past(weather, mock_coordinator):
    now = datetime.now()
    past = now.replace(hour=now.hour - 2)
    future = now.replace(hour=now.hour + 1)
    mock_coordinator.data.get_forecast_data.return_value = {
        past: {"t": 10.0, "nebu": "c0030"},
        future: {"t": 12.0, "nebu": "c0000"},
    }
    with patch.object(weather, "hass") as mock_hass:
        mock_hass.states.get.return_value = MagicMock(state="above_horizon")
        forecasts = await weather.async_forecast_hourly()

    assert len(forecasts) == 1
    assert forecasts[0]["native_temperature"] == 12.0


@pytest.mark.asyncio
async def test_async_forecast_hourly_empty(weather, mock_coordinator):
    mock_coordinator.data.get_forecast_data.return_value = {}
    forecasts = await weather.async_forecast_hourly()
    assert forecasts == []


# --- CONDITION_MAP coverage ---


def test_condition_map_sunny_keys():
    for code in ("c0000", "c0010"):
        assert CONDITION_MAP[code] == "sunny"


def test_condition_map_partlycloudy_keys():
    for code in ("c0020", "c0023", "c0025"):
        assert CONDITION_MAP[code] == "partlycloudy"


def test_condition_map_cloudy_keys():
    for code in ("c0030", "c0043", "c0050", "c0055", "c0060", "c0061", "c0070", "c0080"):
        assert CONDITION_MAP[code] == "cloudy"


def test_condition_map_rainy_keys():
    for code in ("p0010", "p0020", "p0030", "p0050", "p0060"):
        assert CONDITION_MAP[code] == "rainy"


def test_condition_map_snowy_keys():
    for code in ("x3050", "x3060", "x7060", "x8030"):
        assert CONDITION_MAP[code] == "snowy"

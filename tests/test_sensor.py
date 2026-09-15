"""Tests for apiMareeInfo sensor entities."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from custom_components.apiMareeInfo.sensor import (
    BaseMareeSensor,
    infoMareeSensor,
    infoMareeHauteSensor,
    infoMareeBasseSensor,
    infoMareeTEauSensor,
    MareeNextRainForecastSensor,
    MareeRainChanceSensor,
    MareeCloudCoverSensor,
    MareeWeatherAlertSensor,
    MareePressureSensor,
    MareeNextRainTimeSensor,
    MareeFreezeChanceSensor,
    MareeSnowChanceSensor,
    MareeUVSensor,
    MareeWaveSensor,
    MareeWindSensor,
    MareeAirTempSensor,
    MareeVisibilitySensor,
    MareeWaterLevelSensor,
    MareeProchaineGrandeMareeSensor,
)
from custom_components.apiMareeInfo.const import DOMAIN, __VERSION__


@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.data = MagicMock()
    coordinator.data.get_port_name.return_value = "Saint-Malo"
    coordinator.data.getcopyright.return_value = "©SHOM"
    return coordinator


def _make_sensor(sensor_class, coordinator, id_port="test_id"):
    """Helper: create a sensor with a mocked SensorStateManager."""
    with patch("custom_components.apiMareeInfo.sensor.sensorApiMaree.SensorStateManager"):
        sensor = sensor_class(coordinator, id_port)
    return sensor


def _make_sensor_with_manager(sensor_class, coordinator, id_port="test_id"):
    """Helper: create a sensor and return (sensor, mock_manager)."""
    with patch("custom_components.apiMareeInfo.sensor.sensorApiMaree.SensorStateManager") as MockSM:
        sensor = sensor_class(coordinator, id_port)
    return sensor, sensor._sensor_manager


# ---------------------------------------------------------------------------
# BaseMareeSensor
# ---------------------------------------------------------------------------


class TestBaseMareeSensor:
    def test_device_info(self, mock_coordinator):
        sensor = _make_sensor(BaseMareeSensor, mock_coordinator, "port123")
        info = sensor.device_info
        assert info["identifiers"] == {(DOMAIN, "port123")}
        assert info["name"] == "Maree Saint-Malo"
        assert info["manufacturer"] == "apiMareeInfo"
        assert info["model"] == "©SHOM"
        assert info["sw_version"] == __VERSION__
        assert info["entry_type"] == "service"

    def test_has_entity_name(self, mock_coordinator):
        sensor = _make_sensor(BaseMareeSensor, mock_coordinator)
        assert BaseMareeSensor._attr_has_entity_name is True


# ---------------------------------------------------------------------------
# infoMareeSensor
# ---------------------------------------------------------------------------


class TestInfoMareeSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(infoMareeSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_maree_du_jour"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(infoMareeSensor, mock_coordinator)
        assert sensor.name == "Maree du jour"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(infoMareeSensor, mock_coordinator)
        assert sensor.icon == "mdi:waves"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(infoMareeSensor, mock_coordinator)
        manager.getstatus.return_value = ("12:45", {"key": "val"})
        assert sensor.state == "12:45"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(infoMareeSensor, mock_coordinator)
        manager.getstatus.return_value = ("12:45", {"key": "val"})
        assert sensor.extra_state_attributes == {"key": "val"}


# ---------------------------------------------------------------------------
# infoMareeHauteSensor
# ---------------------------------------------------------------------------


class TestInfoMareeHauteSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(infoMareeHauteSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_maree_haute"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(infoMareeHauteSensor, mock_coordinator)
        assert sensor.name == "Maree Haute"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(infoMareeHauteSensor, mock_coordinator)
        assert sensor.icon == "mdi:waves-arrow-up"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(infoMareeHauteSensor, mock_coordinator)
        manager.get_next_tide_state.return_value = ("14:30", {"coeff": 95})
        assert sensor.state == "14:30"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(infoMareeHauteSensor, mock_coordinator)
        manager.get_next_tide_state.return_value = ("14:30", {"coeff": 95})
        assert sensor.extra_state_attributes == {"coeff": 95}

    def test_calls_pm(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(infoMareeHauteSensor, mock_coordinator)
        manager.get_next_tide_state.return_value = ("14:30", {})
        _ = sensor.state
        manager.get_next_tide_state.assert_called_with("PM")


# ---------------------------------------------------------------------------
# infoMareeBasseSensor
# ---------------------------------------------------------------------------


class TestInfoMareeBasseSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(infoMareeBasseSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_maree_basse"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(infoMareeBasseSensor, mock_coordinator)
        assert sensor.name == "Maree Basse"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(infoMareeBasseSensor, mock_coordinator)
        assert sensor.icon == "mdi:waves-arrow-down"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(infoMareeBasseSensor, mock_coordinator)
        manager.get_next_tide_state.return_value = ("08:15", {"coeff": 25})
        assert sensor.state == "08:15"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(infoMareeBasseSensor, mock_coordinator)
        manager.get_next_tide_state.return_value = ("08:15", {"coeff": 25})
        assert sensor.extra_state_attributes == {"coeff": 25}

    def test_calls_bm(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(infoMareeBasseSensor, mock_coordinator)
        manager.get_next_tide_state.return_value = ("08:15", {})
        _ = sensor.state
        manager.get_next_tide_state.assert_called_with("BM")


# ---------------------------------------------------------------------------
# infoMareeTEauSensor
# ---------------------------------------------------------------------------


class TestInfoMareeTEauSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(infoMareeTEauSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_temperature_eau"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(infoMareeTEauSensor, mock_coordinator)
        assert sensor.name == "Temperature Eau"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(infoMareeTEauSensor, mock_coordinator)
        assert sensor.icon == "mdi:thermometer-water"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = _make_sensor(infoMareeTEauSensor, mock_coordinator)
        assert sensor.unit_of_measurement == "°C"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(infoMareeTEauSensor, mock_coordinator)
        manager.get_water_temp_status.return_value = ("18.5", {"trend": "up"})
        assert sensor.state == "18.5"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(infoMareeTEauSensor, mock_coordinator)
        manager.get_water_temp_status.return_value = ("18.5", {"trend": "up"})
        assert sensor.extra_state_attributes == {"trend": "up"}


# ---------------------------------------------------------------------------
# MareeNextRainForecastSensor
# ---------------------------------------------------------------------------


class TestMareeNextRainForecastSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareeNextRainForecastSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_next_rain"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareeNextRainForecastSensor, mock_coordinator)
        assert sensor.name == "Next rain"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareeNextRainForecastSensor, mock_coordinator)
        assert sensor.icon == "mdi:weather-rainy"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeNextRainForecastSensor, mock_coordinator)
        manager.get_weather_status.return_value = ("Dans 2h", {"source": "MF"})
        assert sensor.state == "Dans 2h"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeNextRainForecastSensor, mock_coordinator)
        manager.get_weather_status.return_value = ("Dans 2h", {"source": "MF"})
        assert sensor.extra_state_attributes == {"source": "MF"}


# ---------------------------------------------------------------------------
# MareeRainChanceSensor
# ---------------------------------------------------------------------------


class TestMareeRainChanceSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareeRainChanceSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_rain_chance"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareeRainChanceSensor, mock_coordinator)
        assert sensor.name == "Rain chance"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareeRainChanceSensor, mock_coordinator)
        assert sensor.icon == "mdi:weather-rainy"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = _make_sensor(MareeRainChanceSensor, mock_coordinator)
        assert sensor.unit_of_measurement == "%"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeRainChanceSensor, mock_coordinator)
        manager.get_rain_chance_status.return_value = (42, {"hours": 3})
        assert sensor.state == 42

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeRainChanceSensor, mock_coordinator)
        manager.get_rain_chance_status.return_value = (42, {"hours": 3})
        assert sensor.extra_state_attributes == {"hours": 3}


# ---------------------------------------------------------------------------
# MareeCloudCoverSensor
# ---------------------------------------------------------------------------


class TestMareeCloudCoverSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareeCloudCoverSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_cloud_cover"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareeCloudCoverSensor, mock_coordinator)
        assert sensor.name == "Cloud cover"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareeCloudCoverSensor, mock_coordinator)
        assert sensor.icon == "mdi:cloud-percent"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = _make_sensor(MareeCloudCoverSensor, mock_coordinator)
        assert sensor.unit_of_measurement == "%"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeCloudCoverSensor, mock_coordinator)
        manager.get_cloud_cover_status.return_value = (75, {"oktas": 6})
        assert sensor.state == 75

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeCloudCoverSensor, mock_coordinator)
        manager.get_cloud_cover_status.return_value = (75, {"oktas": 6})
        assert sensor.extra_state_attributes == {"oktas": 6}


# ---------------------------------------------------------------------------
# MareeWeatherAlertSensor
# ---------------------------------------------------------------------------


class TestMareeWeatherAlertSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareeWeatherAlertSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_weather_alert"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareeWeatherAlertSensor, mock_coordinator)
        assert sensor.name == "Weather alert"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareeWeatherAlertSensor, mock_coordinator)
        assert sensor.icon == "mdi:alert"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeWeatherAlertSensor, mock_coordinator)
        manager.get_weather_alert_status.return_value = ("Vert", {"color": "green"})
        assert sensor.state == "Vert"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeWeatherAlertSensor, mock_coordinator)
        manager.get_weather_alert_status.return_value = ("Vert", {"color": "green"})
        assert sensor.extra_state_attributes == {"color": "green"}


# ---------------------------------------------------------------------------
# MareePressureSensor
# ---------------------------------------------------------------------------


class TestMareePressureSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareePressureSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_pressure"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareePressureSensor, mock_coordinator)
        assert sensor.name == "Pressure"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareePressureSensor, mock_coordinator)
        assert sensor.icon == "mdi:gauge"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = _make_sensor(MareePressureSensor, mock_coordinator)
        assert sensor.unit_of_measurement == "hPa"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareePressureSensor, mock_coordinator)
        manager.get_pressure_status.return_value = (1013, {"trend": "stable"})
        assert sensor.state == 1013

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareePressureSensor, mock_coordinator)
        manager.get_pressure_status.return_value = (1013, {"trend": "stable"})
        assert sensor.extra_state_attributes == {"trend": "stable"}


# ---------------------------------------------------------------------------
# MareeNextRainTimeSensor
# ---------------------------------------------------------------------------


class TestMareeNextRainTimeSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareeNextRainTimeSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_next_rain_time"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareeNextRainTimeSensor, mock_coordinator)
        assert sensor.name == "Next rain time"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareeNextRainTimeSensor, mock_coordinator)
        assert sensor.icon == "mdi:weather-pouring"

    def test_state_string(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeNextRainTimeSensor, mock_coordinator)
        manager.get_next_rain_status.return_value = ("Dans 45min", {})
        assert sensor.state == "Dans 45min"

    def test_state_datetime_formatted(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeNextRainTimeSensor, mock_coordinator)
        dt = datetime(2025, 7, 15, 14, 30)
        manager.get_next_rain_status.return_value = (dt, {})
        assert sensor.state == "15/07 14:30"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeNextRainTimeSensor, mock_coordinator)
        manager.get_next_rain_status.return_value = ("Dans 45min", {"minutes": 45})
        assert sensor.extra_state_attributes == {"minutes": 45}


# ---------------------------------------------------------------------------
# MareeFreezeChanceSensor
# ---------------------------------------------------------------------------


class TestMareeFreezeChanceSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareeFreezeChanceSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_freeze_chance"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareeFreezeChanceSensor, mock_coordinator)
        assert sensor.name == "Freeze chance"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareeFreezeChanceSensor, mock_coordinator)
        assert sensor.icon == "mdi:snowflake"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = _make_sensor(MareeFreezeChanceSensor, mock_coordinator)
        assert sensor.unit_of_measurement == "%"

    def test_state(self, mock_coordinator):
        sensor = _make_sensor(MareeFreezeChanceSensor, mock_coordinator)
        assert sensor.state == 0

    def test_extra_state_attributes(self, mock_coordinator):
        sensor = _make_sensor(MareeFreezeChanceSensor, mock_coordinator)
        assert sensor.extra_state_attributes == {"attribution": "Data provided by apiMareeInfo"}


# ---------------------------------------------------------------------------
# MareeSnowChanceSensor
# ---------------------------------------------------------------------------


class TestMareeSnowChanceSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareeSnowChanceSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_snow_chance"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareeSnowChanceSensor, mock_coordinator)
        assert sensor.name == "Snow chance"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareeSnowChanceSensor, mock_coordinator)
        assert sensor.icon == "mdi:weather-snowy"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = _make_sensor(MareeSnowChanceSensor, mock_coordinator)
        assert sensor.unit_of_measurement == "%"

    def test_state(self, mock_coordinator):
        sensor = _make_sensor(MareeSnowChanceSensor, mock_coordinator)
        assert sensor.state == 0

    def test_extra_state_attributes(self, mock_coordinator):
        sensor = _make_sensor(MareeSnowChanceSensor, mock_coordinator)
        assert sensor.extra_state_attributes == {"attribution": "Data provided by apiMareeInfo"}


# ---------------------------------------------------------------------------
# MareeUVSensor
# ---------------------------------------------------------------------------


class TestMareeUVSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareeUVSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_uv"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareeUVSensor, mock_coordinator)
        assert sensor.name == "UV"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareeUVSensor, mock_coordinator)
        assert sensor.icon == "mdi:weather-sunny-alert"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = _make_sensor(MareeUVSensor, mock_coordinator)
        assert sensor.unit_of_measurement == "index"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeUVSensor, mock_coordinator)
        manager.get_uv_status.return_value = (6, {"max": 11})
        assert sensor.state == 6

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeUVSensor, mock_coordinator)
        manager.get_uv_status.return_value = (6, {"max": 11})
        assert sensor.extra_state_attributes == {"max": 11}


# ---------------------------------------------------------------------------
# MareeWaveSensor
# ---------------------------------------------------------------------------


class TestMareeWaveSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareeWaveSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_waves"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareeWaveSensor, mock_coordinator)
        assert sensor.name == "Waves"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareeWaveSensor, mock_coordinator)
        assert sensor.icon == "mdi:waves"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = _make_sensor(MareeWaveSensor, mock_coordinator)
        assert sensor.unit_of_measurement == "m"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeWaveSensor, mock_coordinator)
        manager.get_wave_status.return_value = ("1.2", {"period": "8s"})
        assert sensor.state == "1.2"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeWaveSensor, mock_coordinator)
        manager.get_wave_status.return_value = ("1.2", {"period": "8s"})
        assert sensor.extra_state_attributes == {"period": "8s"}


# ---------------------------------------------------------------------------
# MareeWindSensor
# ---------------------------------------------------------------------------


class TestMareeWindSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareeWindSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_wind_live"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareeWindSensor, mock_coordinator)
        assert sensor.name == "Wind Live"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareeWindSensor, mock_coordinator)
        assert sensor.icon == "mdi:wind"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = _make_sensor(MareeWindSensor, mock_coordinator)
        assert sensor.unit_of_measurement == "km/h"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeWindSensor, mock_coordinator)
        manager.get_wind_status.return_value = ("25", {"direction": "NW"})
        assert sensor.state == "25"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeWindSensor, mock_coordinator)
        manager.get_wind_status.return_value = ("25", {"direction": "NW"})
        assert sensor.extra_state_attributes == {"direction": "NW"}


# ---------------------------------------------------------------------------
# MareeAirTempSensor
# ---------------------------------------------------------------------------


class TestMareeAirTempSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareeAirTempSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_air_temp"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareeAirTempSensor, mock_coordinator)
        assert sensor.name == "Air Temperature"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareeAirTempSensor, mock_coordinator)
        assert sensor.icon == "mdi:thermometer"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = _make_sensor(MareeAirTempSensor, mock_coordinator)
        assert sensor.unit_of_measurement == "°C"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeAirTempSensor, mock_coordinator)
        manager.get_air_temp_status.return_value = ("22.3", {"feels_like": "21"})
        assert sensor.state == "22.3"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeAirTempSensor, mock_coordinator)
        manager.get_air_temp_status.return_value = ("22.3", {"feels_like": "21"})
        assert sensor.extra_state_attributes == {"feels_like": "21"}


# ---------------------------------------------------------------------------
# MareeVisibilitySensor
# ---------------------------------------------------------------------------


class TestMareeVisibilitySensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareeVisibilitySensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_visibility"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareeVisibilitySensor, mock_coordinator)
        assert sensor.name == "Visibility"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareeVisibilitySensor, mock_coordinator)
        assert sensor.icon == "mdi:eye"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = _make_sensor(MareeVisibilitySensor, mock_coordinator)
        assert sensor.unit_of_measurement == "m"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeVisibilitySensor, mock_coordinator)
        manager.get_visibility_status.return_value = ("10000", {"condition": "good"})
        assert sensor.state == "10000"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeVisibilitySensor, mock_coordinator)
        manager.get_visibility_status.return_value = ("10000", {"condition": "good"})
        assert sensor.extra_state_attributes == {"condition": "good"}


# ---------------------------------------------------------------------------
# MareeWaterLevelSensor
# ---------------------------------------------------------------------------


class TestMareeWaterLevelSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareeWaterLevelSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_water_level"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareeWaterLevelSensor, mock_coordinator)
        assert sensor.name == "Water Level"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareeWaterLevelSensor, mock_coordinator)
        assert sensor.icon == "mdi:water-percent"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = _make_sensor(MareeWaterLevelSensor, mock_coordinator)
        assert sensor.unit_of_measurement == "m"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeWaterLevelSensor, mock_coordinator)
        manager.get_water_level_status.return_value = ("3.5", {"ref": "maregraphe"})
        assert sensor.state == "3.5"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(MareeWaterLevelSensor, mock_coordinator)
        manager.get_water_level_status.return_value = ("3.5", {"ref": "maregraphe"})
        assert sensor.extra_state_attributes == {"ref": "maregraphe"}


# ---------------------------------------------------------------------------
# MareeProchaineGrandeMareeSensor
# ---------------------------------------------------------------------------


class TestMareeProchaineGrandeMareeSensor:
    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(MareeProchaineGrandeMareeSensor, mock_coordinator, "abc")
        assert sensor.unique_id == "abc_prochaine_grande_maree"

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(MareeProchaineGrandeMareeSensor, mock_coordinator)
        assert sensor.name == "Prochaine grande maree"

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(MareeProchaineGrandeMareeSensor, mock_coordinator)
        assert sensor.icon == "mdi:waves-arrow-up"

    def test_state(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(
            MareeProchaineGrandeMareeSensor, mock_coordinator
        )
        manager.get_prochaine_grande_maree_status.return_value = (
            "15/07 11:22",
            {"coefficient": 110},
        )
        assert sensor.state == "15/07 11:22"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = _make_sensor_with_manager(
            MareeProchaineGrandeMareeSensor, mock_coordinator
        )
        manager.get_prochaine_grande_maree_status.return_value = (
            "15/07 11:22",
            {"coefficient": 110},
        )
        assert sensor.extra_state_attributes == {"coefficient": 110}

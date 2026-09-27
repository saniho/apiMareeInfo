"""Tests for apiMareeInfo sensor entities."""

from __future__ import annotations

from datetime import datetime

from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)

from custom_components.apiMareeInfo.sensor import MareeSensor
from custom_components.apiMareeInfo.const import DOMAIN, __VERSION__

from .conftest import make_sensor, make_sensor_with_manager


# ---------------------------------------------------------------------------
# Base sensor (device_info, has_entity_name)
# ---------------------------------------------------------------------------


class TestMareeSensorBase:
    def test_device_info(self, mock_coordinator):
        sensor = make_sensor("maree_du_jour", mock_coordinator, "port123")
        info = sensor.device_info
        assert info["identifiers"] == {(DOMAIN, "port123")}
        assert info["name"] == "Maree Saint-Malo"
        assert info["manufacturer"] == "apiMareeInfo"
        assert info["model"] == "\u00a9SHOM"
        assert info["sw_version"] == __VERSION__
        assert info["entry_type"] == "service"

    def test_has_entity_name(self, mock_coordinator):
        make_sensor("maree_du_jour", mock_coordinator)
        assert MareeSensor._attr_has_entity_name is True


# ---------------------------------------------------------------------------
# maree_du_jour (main tide)
# ---------------------------------------------------------------------------


class TestMareeDuJour:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("maree_du_jour", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_maree_du_jour"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("maree_du_jour", mock_coordinator)
        assert sensor.entity_description.name == "Maree du jour"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("maree_du_jour", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:waves"

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("maree_du_jour", mock_coordinator)
        manager.getstatus.return_value = ("12:45", {"key": "val"})
        assert sensor.native_value == "12:45"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("maree_du_jour", mock_coordinator)
        manager.getstatus.return_value = ("12:45", {"key": "val"})
        assert sensor.extra_state_attributes == {"key": "val"}


# ---------------------------------------------------------------------------
# maree_haute
# ---------------------------------------------------------------------------


class TestMareeHaute:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("maree_haute", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_maree_haute"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("maree_haute", mock_coordinator)
        assert sensor.entity_description.name == "Maree Haute"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("maree_haute", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:waves-arrow-up"

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("maree_haute", mock_coordinator)
        manager.get_next_tide_state.return_value = ("14:30", {"coeff": 95})
        assert sensor.native_value == "14:30"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("maree_haute", mock_coordinator)
        manager.get_next_tide_state.return_value = ("14:30", {"coeff": 95})
        assert sensor.extra_state_attributes == {"coeff": 95}

    def test_calls_pm(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("maree_haute", mock_coordinator)
        manager.get_next_tide_state.return_value = ("14:30", {})
        _ = sensor.native_value
        manager.get_next_tide_state.assert_called_with("PM")


# ---------------------------------------------------------------------------
# maree_basse
# ---------------------------------------------------------------------------


class TestMareeBasse:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("maree_basse", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_maree_basse"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("maree_basse", mock_coordinator)
        assert sensor.entity_description.name == "Maree Basse"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("maree_basse", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:waves-arrow-down"

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("maree_basse", mock_coordinator)
        manager.get_next_tide_state.return_value = ("08:15", {"coeff": 25})
        assert sensor.native_value == "08:15"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("maree_basse", mock_coordinator)
        manager.get_next_tide_state.return_value = ("08:15", {"coeff": 25})
        assert sensor.extra_state_attributes == {"coeff": 25}

    def test_calls_bm(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("maree_basse", mock_coordinator)
        manager.get_next_tide_state.return_value = ("08:15", {})
        _ = sensor.native_value
        manager.get_next_tide_state.assert_called_with("BM")


# ---------------------------------------------------------------------------
# temperature_eau
# ---------------------------------------------------------------------------


class TestTemperatureEau:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("temperature_eau", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_temperature_eau"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("temperature_eau", mock_coordinator)
        assert sensor.entity_description.name == "Temperature Eau"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("temperature_eau", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:thermometer-water"

    def test_device_class(self, mock_coordinator):
        from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
        sensor = make_sensor("temperature_eau", mock_coordinator)
        assert sensor.entity_description.device_class == SensorDeviceClass.TEMPERATURE
        assert sensor.entity_description.state_class == SensorStateClass.MEASUREMENT
        assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("temperature_eau", mock_coordinator)
        manager.get_water_temp_status.return_value = ("18.5", {"trend": "up"})
        assert sensor.native_value == "18.5"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("temperature_eau", mock_coordinator)
        manager.get_water_temp_status.return_value = ("18.5", {"trend": "up"})
        assert sensor.extra_state_attributes == {"trend": "up"}


# ---------------------------------------------------------------------------
# next_rain
# ---------------------------------------------------------------------------


class TestNextRain:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("next_rain", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_next_rain"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("next_rain", mock_coordinator)
        assert sensor.entity_description.name == "Next rain"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("next_rain", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:weather-rainy"

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("next_rain", mock_coordinator)
        manager.get_weather_status.return_value = ("Dans 2h", {"source": "MF"})
        assert sensor.native_value == "Dans 2h"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("next_rain", mock_coordinator)
        manager.get_weather_status.return_value = ("Dans 2h", {"source": "MF"})
        assert sensor.extra_state_attributes == {"source": "MF"}


# ---------------------------------------------------------------------------
# rain_chance
# ---------------------------------------------------------------------------


class TestRainChance:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("rain_chance", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_rain_chance"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("rain_chance", mock_coordinator)
        assert sensor.entity_description.name == "Rain chance"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("rain_chance", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:weather-rainy"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = make_sensor("rain_chance", mock_coordinator)
        assert sensor.native_unit_of_measurement == PERCENTAGE

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("rain_chance", mock_coordinator)
        manager.get_rain_chance_status.return_value = (42, {"hours": 3})
        assert sensor.native_value == 42

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("rain_chance", mock_coordinator)
        manager.get_rain_chance_status.return_value = (42, {"hours": 3})
        assert sensor.extra_state_attributes == {"hours": 3}


# ---------------------------------------------------------------------------
# cloud_cover
# ---------------------------------------------------------------------------


class TestCloudCover:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("cloud_cover", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_cloud_cover"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("cloud_cover", mock_coordinator)
        assert sensor.entity_description.name == "Cloud cover"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("cloud_cover", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:cloud-percent"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = make_sensor("cloud_cover", mock_coordinator)
        assert sensor.native_unit_of_measurement == PERCENTAGE

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("cloud_cover", mock_coordinator)
        manager.get_cloud_cover_status.return_value = (75, {"oktas": 6})
        assert sensor.native_value == 75

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("cloud_cover", mock_coordinator)
        manager.get_cloud_cover_status.return_value = (75, {"oktas": 6})
        assert sensor.extra_state_attributes == {"oktas": 6}


# ---------------------------------------------------------------------------
# weather_alert
# ---------------------------------------------------------------------------


class TestWeatherAlert:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("weather_alert", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_weather_alert"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("weather_alert", mock_coordinator)
        assert sensor.entity_description.name == "Weather alert"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("weather_alert", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:alert"

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("weather_alert", mock_coordinator)
        manager.get_weather_alert_status.return_value = ("Vert", {"color": "green"})
        assert sensor.native_value == "Vert"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("weather_alert", mock_coordinator)
        manager.get_weather_alert_status.return_value = ("Vert", {"color": "green"})
        assert sensor.extra_state_attributes == {"color": "green"}


# ---------------------------------------------------------------------------
# pressure
# ---------------------------------------------------------------------------


class TestPressure:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("pressure", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_pressure"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("pressure", mock_coordinator)
        assert sensor.entity_description.name == "Pressure"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("pressure", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:gauge"

    def test_device_class(self, mock_coordinator):
        from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
        sensor = make_sensor("pressure", mock_coordinator)
        assert sensor.entity_description.device_class == SensorDeviceClass.PRESSURE
        assert sensor.entity_description.state_class == SensorStateClass.MEASUREMENT
        assert sensor.native_unit_of_measurement == UnitOfPressure.HPA

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("pressure", mock_coordinator)
        manager.get_pressure_status.return_value = (1013, {"trend": "stable"})
        assert sensor.native_value == 1013

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("pressure", mock_coordinator)
        manager.get_pressure_status.return_value = (1013, {"trend": "stable"})
        assert sensor.extra_state_attributes == {"trend": "stable"}


# ---------------------------------------------------------------------------
# next_rain_time
# ---------------------------------------------------------------------------


class TestNextRainTime:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("next_rain_time", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_next_rain_time"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("next_rain_time", mock_coordinator)
        assert sensor.entity_description.name == "Next rain time"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("next_rain_time", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:weather-pouring"

    def test_state_string(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("next_rain_time", mock_coordinator)
        manager.get_next_rain_status.return_value = ("Dans 45min", {})
        assert sensor.native_value == "Dans 45min"

    def test_state_datetime_formatted(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("next_rain_time", mock_coordinator)
        dt = datetime(2025, 7, 15, 14, 30)
        manager.get_next_rain_status.return_value = (dt, {})
        assert sensor.native_value == "15/07 14:30"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("next_rain_time", mock_coordinator)
        manager.get_next_rain_status.return_value = ("Dans 45min", {"minutes": 45})
        assert sensor.extra_state_attributes == {"minutes": 45}


# ---------------------------------------------------------------------------
# freeze_chance (dummy)
# ---------------------------------------------------------------------------


class TestFreezeChance:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("freeze_chance", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_freeze_chance"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("freeze_chance", mock_coordinator)
        assert sensor.entity_description.name == "Freeze chance"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("freeze_chance", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:snowflake"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = make_sensor("freeze_chance", mock_coordinator)
        assert sensor.native_unit_of_measurement == PERCENTAGE

    def test_state(self, mock_coordinator):
        sensor = make_sensor("freeze_chance", mock_coordinator)
        assert sensor.native_value == 0

    def test_extra_state_attributes(self, mock_coordinator):
        sensor = make_sensor("freeze_chance", mock_coordinator)
        assert sensor.extra_state_attributes == {"attribution": "Data provided by apiMareeInfo"}


# ---------------------------------------------------------------------------
# snow_chance (dummy)
# ---------------------------------------------------------------------------


class TestSnowChance:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("snow_chance", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_snow_chance"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("snow_chance", mock_coordinator)
        assert sensor.entity_description.name == "Snow chance"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("snow_chance", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:weather-snowy"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = make_sensor("snow_chance", mock_coordinator)
        assert sensor.native_unit_of_measurement == PERCENTAGE

    def test_state(self, mock_coordinator):
        sensor = make_sensor("snow_chance", mock_coordinator)
        assert sensor.native_value == 0

    def test_extra_state_attributes(self, mock_coordinator):
        sensor = make_sensor("snow_chance", mock_coordinator)
        assert sensor.extra_state_attributes == {"attribution": "Data provided by apiMareeInfo"}


# ---------------------------------------------------------------------------
# uv
# ---------------------------------------------------------------------------


class TestUV:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("uv", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_uv"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("uv", mock_coordinator)
        assert sensor.entity_description.name == "UV"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("uv", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:weather-sunny-alert"

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("uv", mock_coordinator)
        manager.get_uv_status.return_value = (6, {"max": 11})
        assert sensor.native_value == 6

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("uv", mock_coordinator)
        manager.get_uv_status.return_value = (6, {"max": 11})
        assert sensor.extra_state_attributes == {"max": 11}


# ---------------------------------------------------------------------------
# waves
# ---------------------------------------------------------------------------


class TestWaves:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("waves", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_waves"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("waves", mock_coordinator)
        assert sensor.entity_description.name == "Waves"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("waves", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:waves"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = make_sensor("waves", mock_coordinator)
        assert sensor.native_unit_of_measurement == UnitOfLength.METERS

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("waves", mock_coordinator)
        manager.get_wave_status.return_value = ("1.2", {"period": "8s"})
        assert sensor.native_value == "1.2"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("waves", mock_coordinator)
        manager.get_wave_status.return_value = ("1.2", {"period": "8s"})
        assert sensor.extra_state_attributes == {"period": "8s"}


# ---------------------------------------------------------------------------
# wind_live
# ---------------------------------------------------------------------------


class TestWindLive:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("wind_live", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_wind_live"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("wind_live", mock_coordinator)
        assert sensor.entity_description.name == "Wind Live"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("wind_live", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:wind"

    def test_device_class(self, mock_coordinator):
        from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
        sensor = make_sensor("wind_live", mock_coordinator)
        assert sensor.entity_description.device_class == SensorDeviceClass.WIND_SPEED
        assert sensor.entity_description.state_class == SensorStateClass.MEASUREMENT
        assert sensor.native_unit_of_measurement == UnitOfSpeed.KILOMETERS_PER_HOUR

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("wind_live", mock_coordinator)
        manager.get_wind_status.return_value = ("25", {"direction": "NW"})
        assert sensor.native_value == "25"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("wind_live", mock_coordinator)
        manager.get_wind_status.return_value = ("25", {"direction": "NW"})
        assert sensor.extra_state_attributes == {"direction": "NW"}


# ---------------------------------------------------------------------------
# air_temp
# ---------------------------------------------------------------------------


class TestAirTemp:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("air_temp", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_air_temp"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("air_temp", mock_coordinator)
        assert sensor.entity_description.name == "Air Temperature"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("air_temp", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:thermometer"

    def test_device_class(self, mock_coordinator):
        from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
        sensor = make_sensor("air_temp", mock_coordinator)
        assert sensor.entity_description.device_class == SensorDeviceClass.TEMPERATURE
        assert sensor.entity_description.state_class == SensorStateClass.MEASUREMENT
        assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("air_temp", mock_coordinator)
        manager.get_air_temp_status.return_value = ("22.3", {"feels_like": "21"})
        assert sensor.native_value == "22.3"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("air_temp", mock_coordinator)
        manager.get_air_temp_status.return_value = ("22.3", {"feels_like": "21"})
        assert sensor.extra_state_attributes == {"feels_like": "21"}


# ---------------------------------------------------------------------------
# visibility
# ---------------------------------------------------------------------------


class TestVisibility:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("visibility", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_visibility"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("visibility", mock_coordinator)
        assert sensor.entity_description.name == "Visibility"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("visibility", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:eye"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = make_sensor("visibility", mock_coordinator)
        assert sensor.native_unit_of_measurement == UnitOfLength.METERS

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("visibility", mock_coordinator)
        manager.get_visibility_status.return_value = ("10000", {"condition": "good"})
        assert sensor.native_value == "10000"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("visibility", mock_coordinator)
        manager.get_visibility_status.return_value = ("10000", {"condition": "good"})
        assert sensor.extra_state_attributes == {"condition": "good"}


# ---------------------------------------------------------------------------
# water_level
# ---------------------------------------------------------------------------


class TestWaterLevel:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("water_level", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_water_level"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("water_level", mock_coordinator)
        assert sensor.entity_description.name == "Water Level"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("water_level", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:water-percent"

    def test_unit_of_measurement(self, mock_coordinator):
        sensor = make_sensor("water_level", mock_coordinator)
        assert sensor.native_unit_of_measurement == UnitOfLength.METERS

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("water_level", mock_coordinator)
        manager.get_water_level_status.return_value = ("3.5", {"ref": "maregraphe"})
        assert sensor.native_value == "3.5"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("water_level", mock_coordinator)
        manager.get_water_level_status.return_value = ("3.5", {"ref": "maregraphe"})
        assert sensor.extra_state_attributes == {"ref": "maregraphe"}


# ---------------------------------------------------------------------------
# prochaine_grande_maree
# ---------------------------------------------------------------------------


class TestProchaineGrandeMaree:
    def test_unique_id(self, mock_coordinator):
        sensor = make_sensor("prochaine_grande_maree", mock_coordinator, "abc")
        assert sensor.unique_id == "abc_prochaine_grande_maree"

    def test_name(self, mock_coordinator):
        sensor = make_sensor("prochaine_grande_maree", mock_coordinator)
        assert sensor.entity_description.name == "Prochaine grande maree"

    def test_icon(self, mock_coordinator):
        sensor = make_sensor("prochaine_grande_maree", mock_coordinator)
        assert sensor.entity_description.icon == "mdi:waves-arrow-up"

    def test_state(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("prochaine_grande_maree", mock_coordinator)
        manager.get_prochaine_grande_maree_status.return_value = (
            "15/07 11:22",
            {"coefficient": 110},
        )
        assert sensor.native_value == "15/07 11:22"

    def test_extra_state_attributes(self, mock_coordinator):
        sensor, manager = make_sensor_with_manager("prochaine_grande_maree", mock_coordinator)
        manager.get_prochaine_grande_maree_status.return_value = (
            "15/07 11:22",
            {"coefficient": 110},
        )
        assert sensor.extra_state_attributes == {"coefficient": 110}

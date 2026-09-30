"""Sensor for apiMareeInfo."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    __VERSION__,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class MareeSensorEntityDescription(SensorEntityDescription):
    """Describe a Maree sensor."""

    status_method: str
    status_args: tuple[Any, ...] = ()
    state_transform: Callable[[Any], Any] | None = None
    static_state: Any = None


def _format_next_rain_time(state: Any) -> str:
    """Format datetime to DD/MM HH:MM."""
    if isinstance(state, datetime):
        return state.strftime("%d/%m %H:%M")
    return state


SENSOR_DESCRIPTIONS: tuple[MareeSensorEntityDescription, ...] = (
    MareeSensorEntityDescription(
        key="maree_du_jour",
        name="Maree du jour",
        icon="mdi:waves",
        status_method="getstatus",
    ),
    MareeSensorEntityDescription(
        key="maree_haute",
        name="Maree Haute",
        translation_key="maree_haute",
        icon="mdi:waves-arrow-up",
        status_method="get_next_tide_state",
        status_args=("PM",),
    ),
    MareeSensorEntityDescription(
        key="maree_basse",
        name="Maree Basse",
        translation_key="maree_basse",
        icon="mdi:waves-arrow-down",
        status_method="get_next_tide_state",
        status_args=("BM",),
    ),
    MareeSensorEntityDescription(
        key="temperature_eau",
        name="Temperature Eau",
        translation_key="temperature_eau",
        icon="mdi:thermometer-water",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        status_method="get_water_temp_status",
    ),
    MareeSensorEntityDescription(
        key="next_rain",
        name="Next rain",
        translation_key="next_rain",
        icon="mdi:weather-rainy",
        status_method="get_weather_status",
    ),
    MareeSensorEntityDescription(
        key="rain_chance",
        name="Rain chance",
        icon="mdi:weather-rainy",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        status_method="get_rain_chance_status",
    ),
    MareeSensorEntityDescription(
        key="cloud_cover",
        name="Cloud cover",
        icon="mdi:cloud-percent",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        status_method="get_cloud_cover_status",
    ),
    MareeSensorEntityDescription(
        key="weather_alert",
        name="Weather alert",
        icon="mdi:alert",
        status_method="get_weather_alert_status",
    ),
    MareeSensorEntityDescription(
        key="pressure",
        name="Pressure",
        icon="mdi:gauge",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.HPA,
        status_method="get_pressure_status",
    ),
    MareeSensorEntityDescription(
        key="next_rain_time",
        name="Next rain time",
        icon="mdi:weather-pouring",
        status_method="get_next_rain_status",
        state_transform=_format_next_rain_time,
    ),
    MareeSensorEntityDescription(
        key="freeze_chance",
        name="Freeze chance",
        icon="mdi:snowflake",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        static_state=0,
        status_method="getstatus",
    ),
    MareeSensorEntityDescription(
        key="snow_chance",
        name="Snow chance",
        icon="mdi:weather-snowy",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        static_state=0,
        status_method="getstatus",
    ),
    MareeSensorEntityDescription(
        key="uv",
        name="UV",
        icon="mdi:weather-sunny-alert",
        state_class=SensorStateClass.MEASUREMENT,
        status_method="get_uv_status",
    ),
    MareeSensorEntityDescription(
        key="waves",
        name="Waves",
        icon="mdi:waves",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.METERS,
        status_method="get_wave_status",
    ),
    MareeSensorEntityDescription(
        key="wind_live",
        name="Wind Live",
        icon="mdi:wind",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        status_method="get_wind_status",
    ),
    MareeSensorEntityDescription(
        key="air_temp",
        name="Air Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        status_method="get_air_temp_status",
    ),
    MareeSensorEntityDescription(
        key="visibility",
        name="Visibility",
        icon="mdi:eye",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.METERS,
        status_method="get_visibility_status",
    ),
    MareeSensorEntityDescription(
        key="water_level",
        name="Water Level",
        icon="mdi:water-percent",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.METERS,
        status_method="get_water_level_status",
    ),
    MareeSensorEntityDescription(
        key="prochaine_grande_maree",
        name="Prochaine grande maree",
        icon="mdi:waves-arrow-up",
        status_method="get_prochaine_grande_maree_status",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    id_port = entry.entry_id

    if coordinator.data.has_error():
        _LOGGER.error(
            "Could not fetch initial data for %s: %s",
            id_port,
            coordinator.data.get_error_message(),
        )

    entities = [
        MareeSensor(coordinator, id_port, description)
        for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities, True)


class MareeSensor(CoordinatorEntity, SensorEntity):
    """Generic Maree sensor using SensorEntityDescription."""

    _attr_has_entity_name = True
    entity_description: MareeSensorEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        id_port: str,
        description: MareeSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._id_port = id_port
        self._attr_unique_id = f"{id_port}_{description.key}"
        self._cached_result: tuple[Any, dict[str, Any]] | None = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._id_port)},
            name=f"Maree {self.coordinator.data.get_port_name()}",
            manufacturer="apiMareeInfo",
            model=self.coordinator.data.getcopyright(),
            sw_version=__VERSION__,
            entry_type="service",
        )

    def _get_status(self) -> tuple[Any, dict[str, Any]]:
        """Call status method once per update cycle, cache the result."""
        if self._cached_result is not None:
            return self._cached_result
        method = getattr(
            self.coordinator.data, self.entity_description.status_method
        )
        self._cached_result = method(*self.entity_description.status_args)
        return self._cached_result

    def _handle_coordinator_update(self) -> None:
        """Invalidate cache on coordinator update."""
        self._cached_result = None
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> Any:
        """Return the sensor state."""
        if self.entity_description.static_state is not None:
            return self.entity_description.static_state

        state, _ = self._get_status()

        if self.entity_description.state_transform is not None:
            return self.entity_description.state_transform(state)
        return state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.entity_description.static_state is not None:
            return {"attribution": "Data provided by apiMareeInfo"}

        _, attributes = self._get_status()
        return attributes

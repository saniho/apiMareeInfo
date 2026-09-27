"""Sensor for apiMareeInfo."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

import async_timeout

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from . import apiMareeInfo
from .const import (
    __VERSION__,
    CONF_ID,
    CONF_MAXHOURS,
    CONF_STORM_KEY,
    DEFAULT_MAX_HOURS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .exceptions import ApiError, NetworkError

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
        icon="mdi:waves-arrow-up",
        status_method="get_next_tide_state",
        status_args=("PM",),
    ),
    MareeSensorEntityDescription(
        key="maree_basse",
        name="Maree Basse",
        icon="mdi:waves-arrow-down",
        status_method="get_next_tide_state",
        status_args=("BM",),
    ),
    MareeSensorEntityDescription(
        key="temperature_eau",
        name="Temperature Eau",
        icon="mdi:thermometer-water",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        status_method="get_water_temp_status",
    ),
    MareeSensorEntityDescription(
        key="next_rain",
        name="Next rain",
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
    config = entry.data
    options = entry.options

    lat = config[CONF_LATITUDE]
    lng = config[CONF_LONGITUDE]
    stormkey = options.get(CONF_STORM_KEY, config.get(CONF_STORM_KEY))
    maxhours = options.get(CONF_MAXHOURS, config.get(CONF_MAXHOURS, DEFAULT_MAX_HOURS))

    id_port = entry.entry_id

    session = async_get_clientsession(hass)

    maree_api = apiMareeInfo.ApiMareeInfo(version=__VERSION__)
    maree_api.setport(lat, lng)
    maree_api.setid(config.get(CONF_ID))
    maree_api.setmaxhours(maxhours)

    origine = "stormio" if stormkey else "MeteoMarine"
    info = {"stormkey": stormkey} if stormkey else None

    async def async_update_data() -> apiMareeInfo.ApiMareeInfo:
        """Fetch data from API endpoint."""
        try:
            async with async_timeout.timeout(30):
                await maree_api.getinformationport(
                    origine=origine, info=info, session=session
                )
                return maree_api
        except (ApiError, NetworkError) as err:
            raise UpdateFailed(f"API error: {err}")
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}-{id_port}",
        update_method=async_update_data,
        update_interval=DEFAULT_SCAN_INTERVAL,
    )

    await coordinator.async_refresh()

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

    @property
    def native_value(self) -> Any:
        """Return the sensor state."""
        if self.entity_description.static_state is not None:
            return self.entity_description.static_state

        method = getattr(
            self.coordinator.data, self.entity_description.status_method
        )
        state, _ = method(*self.entity_description.status_args)

        if self.entity_description.state_transform is not None:
            return self.entity_description.state_transform(state)
        return state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.entity_description.static_state is not None:
            return {"attribution": "Data provided by apiMareeInfo"}

        method = getattr(
            self.coordinator.data, self.entity_description.status_method
        )
        _, attributes = method(*self.entity_description.status_args)
        return attributes

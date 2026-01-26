"""Sensor for apiMareeInfo."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import (
    CONF_LATITUDE, # Gardé si besoin pour debug, sinon peut être retiré
    CONF_LONGITUDE,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    __VERSION__,
    DOMAIN,
)
from . import sensorApiMaree

_LOGGER = logging.getLogger(__name__)
ICON = "mdi:waves"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the sensor platform."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    id_port = entry.unique_id

    entities = [
        infoMareeSensor(coordinator, id_port),
        infoMareeHauteSensor(coordinator, id_port),
        infoMareeBasseSensor(coordinator, id_port),
        infoMareeTEauSensor(coordinator, id_port),
    ]
    async_add_entities(entities, True)


class BaseMareeSensor(CoordinatorEntity, SensorEntity):
    """Base class for maree sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator, id_port: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._id_port = id_port
        self._sAM = sensorApiMaree.manageSensorState()
        self._sAM.init(self.coordinator.data, _LOGGER, __VERSION__)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._id_port)},
            name=f"Maree {self.coordinator.data.getnomduport()}",
            manufacturer="apiMareeInfo",
            model=self.coordinator.data.getcopyright(),
            sw_version=__VERSION__,
        )


class infoMareeSensor(BaseMareeSensor):
    """Representation of the main tide sensor."""

    def __init__(self, coordinator, id_port):
        super().__init__(coordinator, id_port)
        self._attr_unique_id = f"myPort.{self._id_port}.MareeDuJour"
        self._attr_name = None  # Le capteur principal porte le nom de l'appareil
        self._attr_icon = ICON

    @property
    def state(self):
        """Return the state of the sensor."""
        state, _ = self._sAM.getstatus()
        return state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        _, attributes = self._sAM.getstatus()
        attributes["lat"] = self.coordinator.data.getlat()
        attributes["long"] = self.coordinator.data.getlng()
        return attributes


class infoMareeHauteSensor(BaseMareeSensor):
    """Representation of the next high tide sensor."""

    def __init__(self, coordinator, id_port):
        super().__init__(coordinator, id_port)
        self._attr_unique_id = f"myPort.{self._id_port}.MareeProchaine.Haute"
        self._attr_translation_key = "next_high_tide"
        self._attr_icon = "mdi:waves-arrow-up"

    @property
    def state(self):
        """Return the state of the sensor."""
        state, _ = self._sAM.getStateNextMaree("PM")
        return state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        _, attributes = self._sAM.getStateNextMaree("PM")
        return attributes


class infoMareeBasseSensor(BaseMareeSensor):
    """Representation of the next low tide sensor."""

    def __init__(self, coordinator, id_port):
        super().__init__(coordinator, id_port)
        self._attr_unique_id = f"myPort.{self._id_port}.MareeProchaine.Basse"
        self._attr_translation_key = "next_low_tide"
        self._attr_icon = "mdi:waves-arrow-down"

    @property
    def state(self):
        """Return the state of the sensor."""
        state, _ = self._sAM.getStateNextMaree("BM")
        return state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        _, attributes = self._sAM.getStateNextMaree("BM")
        return attributes


class infoMareeTEauSensor(BaseMareeSensor):
    """Representation of the water temperature sensor."""

    def __init__(self, coordinator, id_port):
        super().__init__(coordinator, id_port)
        self._attr_unique_id = f"myPort.{self._id_port}.TEau"
        self._attr_translation_key = "water_temp"
        self._attr_native_unit_of_measurement = "°C"
        self._attr_icon = "mdi:thermometer-water"

    @property
    def state(self):
        """Return the state of the sensor."""
        state, _ = self._sAM.getstatusTemperatureEau()
        return state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        _, attributes = self._sAM.getstatusTemperatureEau()
        return attributes

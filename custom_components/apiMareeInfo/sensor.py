"""Sensor for apiMareeInfo."""

import logging
from datetime import timedelta
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    __name__,
    __VERSION__,
    CONF_MAXHOURS,
    DOMAIN,
)
from . import apiMareeInfo, sensorApiMaree

_LOGGER = logging.getLogger(__name__)
ICON = "mdi:waves"
DEFAULT_SCAN_INTERVAL = timedelta(hours=3)

CONF_STORM_KEY = "stormio_key"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the sensor platform."""
    config = entry.data
    options = entry.options

    lat = config[CONF_LATITUDE]
    lng = config[CONF_LONGITUDE]
    stormkey = options.get(CONF_STORM_KEY, config.get(CONF_STORM_KEY))
    maxhours = options.get(CONF_MAXHOURS, config.get(CONF_MAXHOURS, 6))

    idDuPort = entry.unique_id or f"{lat}-{lng}"

    session = async_get_clientsession(hass)

    maree_api = apiMareeInfo.ApiMareeInfo()
    maree_api.setport(lat, lng)
    maree_api.setmaxhours(maxhours)

    origine = "stormio" if stormkey else "MeteoMarine"
    info = {"stormkey": stormkey} if stormkey else None

    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            async with async_timeout.timeout(30):
                await maree_api.getinformationport(
                    origine=origine, info=info, session=session
                )
                return maree_api
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}-{idDuPort}",
        update_method=async_update_data,
        update_interval=DEFAULT_SCAN_INTERVAL,
    )

    await coordinator.async_refresh()

    if coordinator.data.getError():
        _LOGGER.error(
            "Could not fetch initial data for %s: %s",
            idDuPort,
            coordinator.data.getErrorMessage(),
        )
        return

    entities = [
        infoMareeSensor(coordinator, idDuPort),
        infoMareeHauteSensor(coordinator, idDuPort),
        infoMareeBasseSensor(coordinator, idDuPort),
        infoMareeTEauSensor(coordinator, idDuPort),
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
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._id_port)},
            "name": f"Maree {self.coordinator.data.getnomduport()}",
            "manufacturer": "apiMareeInfo",
            "model": self.coordinator.data.getcopyright(),
            "sw_version": __VERSION__,
            "entry_type": "service",
        }


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
        return attributes


class infoMareeHauteSensor(BaseMareeSensor):
    """Representation of the next high tide sensor."""

    def __init__(self, coordinator, id_port):
        super().__init__(coordinator, id_port)
        self._attr_unique_id = f"myPort.{self._id_port}.MareeProchaine.Haute"
        self._attr_name = "Prochaine Haute"
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
        self._attr_name = "Prochaine Basse"
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
        self._attr_name = "Temperature Eau"
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

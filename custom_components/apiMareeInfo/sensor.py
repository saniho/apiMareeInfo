"""Sensor for apiMareeInfo."""
import logging
from datetime import timedelta
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
    CONF_METEOFRANCE_ENTITY_ID,
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
    meteofrance_entity_id = options.get(CONF_METEOFRANCE_ENTITY_ID, config.get(CONF_METEOFRANCE_ENTITY_ID))
    
    # Use entry_id as the base for unique IDs to ensure uniqueness per config entry
    idDuPort = entry.entry_id

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
                
                # Fetch Météo-France data if entity_id is provided
                if meteofrance_entity_id:
                    state = hass.states.get(meteofrance_entity_id)
                    if state and state.state not in ["unknown", "unavailable"]:
                        try:
                            value = float(state.state)
                            maree_api.set_meteofrance_precipitation(value)
                        except (ValueError, TypeError):
                            _LOGGER.warning("Could not parse Météo-France precipitation value: %s", state.state)
                
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
        # We don't return here to allow the entities to be created even if initial fetch failed
        # They will just be unavailable until the next successful update

    entities = [
        infoMareeSensor(coordinator, idDuPort),
        infoMareeHauteSensor(coordinator, idDuPort),
        infoMareeBasseSensor(coordinator, idDuPort),
        infoMareeTEauSensor(coordinator, idDuPort),
    ]
    if meteofrance_entity_id:
        entities.append(infoMareePluieMeteoFranceSensor(coordinator, idDuPort))
        
    async_add_entities(entities, True)


class BaseMareeSensor(CoordinatorEntity):
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

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return f"{self._id_port}_maree_du_jour"

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Maree du jour"

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

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return ICON


class infoMareeHauteSensor(BaseMareeSensor):
    """Representation of the next high tide sensor."""

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return f"{self._id_port}_maree_haute"

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Maree Haute"

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

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return "mdi:waves-arrow-up"


class infoMareeBasseSensor(BaseMareeSensor):
    """Representation of the next low tide sensor."""

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return f"{self._id_port}_maree_basse"

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Maree Basse"

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

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return "mdi:waves-arrow-down"


class infoMareeTEauSensor(BaseMareeSensor):
    """Representation of the water temperature sensor."""

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return f"{self._id_port}_temperature_eau"

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Temperature Eau"

    @property
    def state(self):
        """Return the state of the sensor."""
        state, _ = self._sAM.getstatusTemperatureEau()
        return state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return "°C"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        _, attributes = self._sAM.getstatusTemperatureEau()
        return attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return "mdi:thermometer-water"


class infoMareePluieMeteoFranceSensor(BaseMareeSensor):
    """Representation of the 1h precipitation sensor from Météo-France."""

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return f"{self._id_port}_precipitation_meteofrance"

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Précipitations 1h (Météo-France)"

    @property
    def state(self):
        """Return the state of the sensor."""
        state, _ = self._sAM.getstatusMeteoFrance()
        return state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return "mm"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        _, attributes = self._sAM.getstatusMeteoFrance()
        return attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return "mdi:weather-rainy"

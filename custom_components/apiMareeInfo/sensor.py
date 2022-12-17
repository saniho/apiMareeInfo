"""Sensor for my first"""
import logging
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (  # isort:skip
    CONF_CODE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    ATTR_ATTRIBUTION,
    CONF_SCAN_INTERVAL,
)
CONF_STORM_KEY = "stormio_key"
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

from .const import (  # isort:skip
    __name__,
    # CONF_SCAN_INTERVAL_HTTP,
)

_LOGGER = logging.getLogger(__name__)
DOMAIN = "saniho"
ICON = "mdi:package-variant-closed"
SCAN_INTERVAL = timedelta(seconds=60 * 60 * 3)
SCAN_INTERVAL_http = timedelta(seconds=60 * 60 * 3)
CONF_SCAN_INTERVAL_HTTP = SCAN_INTERVAL_http
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_CODE): cv.string,
        vol.Required(CONF_LATITUDE): cv.string,
        vol.Required(CONF_LONGITUDE): cv.string,
        vol.Optional(CONF_STORM_KEY): cv.string,
    }
)

from . import apiMareeInfo, sensorApiMaree


class myMareeInfo:
    def __init__(self, idDuPort, lat, lng, stormkey, _update_interval):
        self._lastSynchro = None
        self._update_interval = _update_interval
        self._idDuPort = idDuPort
        self._lat = lat
        self._lng = lng
        self._origine = "MeteoMarine"
        self._stormkey = stormkey
        self._myMaree = apiMareeInfo.ApiMareeInfo()
        pass

    def update(self, ):
        import datetime
        courant = datetime.datetime.now()
        if (self._lastSynchro is None) or \
                ((self._lastSynchro + self._update_interval) < courant):
            _LOGGER.warning("-update possible- on lance")
            self._myMaree.setport(self._lat, self._lng)
            if self._origine == "MeteoMarine":
                self._myMaree.getinformationport(origine=self._origine)
            else:
                self._myMaree.getinformationport(origine="stormio", info={"stormkey": self._stormkey})
            self._lastSynchro = datetime.datetime.now()

    def getIdPort(self):
        return self._idDuPort

    def getmyMaree(self):
        return self._myMaree

    def getDateCourante(self):
        return self._myMaree.getdatecourante()


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the platform."""
    name = config.get(CONF_NAME)
    update_interval = config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)
    update_interval_http = config.get(CONF_SCAN_INTERVAL_HTTP, SCAN_INTERVAL_http)
    try:
        idDuPort = config.get(CONF_CODE)
        lat = config.get(CONF_LATITUDE)
        lng = config.get(CONF_LONGITUDE)
        stormkey = config.get(CONF_STORM_KEY)
        session = []
    except:
        _LOGGER.exception("Could not run my apiMaree Extension miss argument ?")
        return False
    myPort = myMareeInfo(idDuPort, lat, lng, stormkey, update_interval_http)
    myPort.update()
    add_entities([infoMareeSensor(session, name, update_interval, myPort)], True)
    # add_entities([infoMareePluieSensor(session, name, update_interval, myPort)], True)


class infoMareeSensor(Entity):
    """."""

    def __init__(self, session, name, interval, myPort):
        """Initialize the sensor."""
        self._session = session
        self._name = name
        self._myPort = myPort
        self._attributes = None
        self._state = None
        self.update = Throttle(interval)(self._update)
        self._sAM = sensorApiMaree.manageSensorState()
        self._sAM.init(self._myPort.getmyMaree())

    @property
    def unique_id(self):
        "Return a unique_id for this entity."
        return "myPort.%s.MareeDuJour" % self._myPort.getIdPort()

    @property
    def name(self):
        """Return the name of the sensor."""
        return "myPort.%s.MareeDuJour" % self._myPort.getIdPort()

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return ""

    def _update(self):
        """Update device state."""
        self._attributes = {ATTR_ATTRIBUTION: ""}
        self._state = "unavailable"
        self._myPort.update()
        try:
            state, status_counts = self._sAM.getstatus()
        except:
            return
        self._attributes = {ATTR_ATTRIBUTION: ""}
        self._attributes.update(status_counts)
        self._state = state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""


class infoMareePluieSensor(Entity):
    """."""

    def __init__(self, session, name, interval, myPort):
        """Initialize the sensor."""
        self._session = session
        self._name = name
        self._myPort = myPort
        self._attributes = None
        self._state = None
        self.update = Throttle(interval)(self._update)
        self._sAM = sensorApiMaree.manageSensorState()
        self._sAM.init(self._myPort.getmyMaree())

    @property
    def unique_id(self):
        "Return a unique_id for this entity."
        return "myPort.%s.ProchainePluie" % self._myPort.getIdPort()

    @property
    def name(self):
        """Return the name of the sensor."""
        return "myPort.%s.ProchainePluie" % self._myPort.getIdPort()

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return ""

    def _update(self):
        """Update device state."""
        self._attributes = {ATTR_ATTRIBUTION: ""}
        self._state = "unavailable"
        self._myPort.update()
        try:
            state, status_counts = self._sAM.getstatusProchainePluie()
        except:
            return
        self._attributes = {ATTR_ATTRIBUTION: ""}
        self._attributes.update(status_counts)
        self._state = state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""

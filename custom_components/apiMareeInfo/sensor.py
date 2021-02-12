"""Sensor for my first"""
import logging
from collections import defaultdict
from datetime import timedelta, datetime

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_CODE,
    CONF_NAME,
    ATTR_ATTRIBUTION,
    CONF_SCAN_INTERVAL,
)

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.util import slugify
from homeassistant.util.dt import now, parse_date


from .const import (
    DOMAIN,
    __VERSION__,
    __name__,
    SCAN_INTERVAL_http,
)

_LOGGER = logging.getLogger(__name__)
DOMAIN = "saniho"
ICON = "mdi:package-variant-closed"
SCAN_INTERVAL = timedelta(seconds=1800)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_CODE): cv.string,
    }
)

from . import apiMareeInfo, sensorApiMaree

class myMareeInfo:
    def __init__(self, idDuPort, _update_interval):
        self._lastSynchro = None
        self._update_interval = _update_interval
        self._idDuPort = idDuPort
        self._myMaree = apiMareeInfo.apiMareeInfo()
        pass


    def update(self,):
        import datetime

        courant = datetime.datetime.now()
        #_LOGGER.warning("-update possible- ?")
        if ( self._lastSynchro == None ) or \
            ( (self._lastSynchro + self._update_interval) < courant ):
            _LOGGER.warning("-update possible- on lance")
            self._myMaree.getInformationPort(self._idDuPort)
            self._lastSynchro = datetime.datetime.now()

    def getIdPort(self):
        return self._idDuPort
    # revoir recupearation valeur
    def getmyMaree(self):
        return self._myMaree
    def getDateCourante(self):
        return self._myMaree.getDateCourante()


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the platform."""
    name = config.get(CONF_NAME)
    update_interval = config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)
    update_interval_http = SCAN_INTERVAL_http
    idDuPort = config.get(CONF_CODE)
    try:
        session = []
    except :
        _LOGGER.exception("Could not run my First Extension")
        return False
    myPort = myMareeInfo( idDuPort, update_interval )
    myPort.update()
    add_entities([infoMareeSensor(session, name, update_interval, myPort )], True)

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
        self._sAM.init( self._myPort.getmyMaree() )

    @property
    def name(self):
        """Return the name of the sensor."""
        return "myPort.%s.MareeDuJour" %self._myPort.getIdPort()

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
        self._myPort.update()
        self._state, self._attributes = self._sAM.getStatus()

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return ICON
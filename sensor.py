"""Sensor for my first"""
import logging
from collections import defaultdict
from datetime import timedelta

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

_LOGGER = logging.getLogger(__name__)
DOMAIN = "saniho"
ICON = "mdi:package-variant-closed"
SCAN_INTERVAL = timedelta(seconds=1800)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_CODE): cv.string,
    }
)

from . import apiMareeInfo

class myMareeInfo:
    def __init__(self, nomDuPort, _update_interval):
        self._lastSynchro = None
        self._update_interval = _update_interval
        self._nomDuPort = nomDuPort
        self._myMaree = apiMareeInfo.apiMareeInfo()
        pass


    def update(self,):
        import json
        import datetime

        courant = datetime.datetime.now()
        _LOGGER.warning("-update possible-")
        if ( self._lastSynchro == None ) or \
            ( (self._lastSynchro + self._update_interval) < courant ):
            #_LOGGER.info("--------------")
            #_LOGGER.info("tente un update  ? ... %s" %(self._lastSynchro))

            self._myMaree.getInformationPort(self._nomDuPort)
            self._infoPort = self._myMaree.getInfo()
            self._lastSynchro = datetime.datetime.now()
            _LOGGER.info("update fait, last synchro ... %s " %(self._lastSynchro))
            _LOGGER.info("update fait, last synchro(info port) ... %s " %(self._infoPort))

    def getInfoPort(self):
        return self._infoPort
    def getNomPort(self):
        return self._nomDuPort


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the platform."""
    name = config.get(CONF_NAME)
    update_interval = config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)
    nomDuPort = config.get(CONF_CODE)
    try:
        session = []
    except :
        _LOGGER.exception("Could not run my First Extension")
        return False
    myPort = myMareeInfo( nomDuPort, update_interval )
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

    @property
    def name(self):
        """Return the name of the sensor."""
        return "myPort.%s.MareeDuJour" %self._myPort.getNomPort()

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
        status_counts = defaultdict(int)
        self._myPort.update()
        infoPort = self._myPort.getInfoPort()
        _LOGGER.info("tente un update  infoPort? ... %s" % (infoPort))
        _LOGGER.info("tente un update  infoPort? ... %s" % (infoPort.keys()))
        niemeHoraire = 0
        self._attributes = {}
        for n in range(2):
            self._attributes["horaire_%s_4"%n] = ""
            self._attributes["coeff_%s_4"%n] = ""
            self._attributes["etat_%s_4"%n] = ""
            self._attributes["hauteur_%s_4"%n] = ""

        #probleme mauvaise variable
        #self._attributes["nomPort"] = self._myPort.getNomDuPort()
        #self._attributes["dateCourante"] = self._myPort.getDateCourante()

        for horaireMaree in infoPort.keys():
            niemeHoraire += 1
            info = infoPort[horaireMaree]
            nieme = info["nieme"]
            jour = info["jour"]
            self._attributes["horaire_%s_%s" %(jour, nieme)] = "%s" %(info['horaire'])
            self._attributes["coeff_%s_%s" %(jour, nieme)] = "%s" %(info['coeff'])
            self._attributes["etat_%s_%s" %(jour, nieme)] = "%s" %(info['etat'])
            self._attributes["hauteur_%s_%s" %(jour, nieme)] = "%s" %(info['hauteur'])
        self._attributes.update(status_counts)
        self._state = ""

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return ICON
"""Config flow for apiMareeInfo."""

import logging
from typing import Any, Dict

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .apiMareeInfo import ListePorts
from .const import (
    DOMAIN,
    CONF_MAXHOURS,
    CONF_PROVIDER,
    DEFAULT_PROVIDER,
)

_LOGGER = logging.getLogger(__name__)

CONF_PORT_SEARCH = "port_search"
CONF_PORT_SELECT = "port_select"


class ApiMareeInfoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for apiMareeInfo."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self.data = {}
        self.ports = {}

    async def async_step_user(self, user_input: Dict[str, Any] = None):
        """Step 1: Ask user for a port name to search."""
        errors = {}
        if user_input is not None:
            search_term = user_input[CONF_PORT_SEARCH]
            session = async_get_clientsession(self.hass)
            api = ListePorts()

            try:
                found_ports = await api.getlisteport(search_term, session)
                if (
                    not found_ports
                    or "contenu" not in found_ports
                    or not found_ports["contenu"]
                ):
                    errors["base"] = "no_ports_found"
                else:
                    self.ports = {
                        f"{port['ville']} ({port['departement']})": {
                            "lat": port["latitude"],
                            "lon": port["longitude"],
                        }
                        for port in found_ports["contenu"]
                    }
                    return await self.async_step_select_port()
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Failed to search for ports")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_PORT_SEARCH): str}),
            errors=errors,
        )

    async def async_step_select_port(self, user_input: Dict[str, Any] = None):
        """Step 2: Show found ports and ask for final details."""
        errors = {}
        if user_input is not None:
            selected_port_name = user_input[CONF_PORT_SELECT]
            port_details = self.ports[selected_port_name]

            lat = port_details["lat"]
            lon = port_details["lon"]

            await self.async_set_unique_id(f"{DEFAULT_PROVIDER}-{lat}-{lon}")
            self._abort_if_unique_id_configured()

            data = {
                CONF_PROVIDER: DEFAULT_PROVIDER,
                CONF_LATITUDE: lat,
                CONF_LONGITUDE: lon,
                CONF_NAME: user_input.get(CONF_NAME, selected_port_name),
                CONF_MAXHOURS: user_input[CONF_MAXHOURS],
            }

            return self.async_create_entry(
                title=data[CONF_NAME],
                data=data,
            )

        return self.async_show_form(
            step_id="select_port",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PORT_SELECT): vol.In(list(self.ports.keys())),
                    vol.Optional(CONF_NAME): str,
                    vol.Optional(CONF_MAXHOURS, default=6): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for apiMareeInfo."""

    async def async_step_init(self, user_input: Dict[str, Any] = None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_max_hours = self.config_entry.options.get(
            CONF_MAXHOURS, self.config_entry.data.get(CONF_MAXHOURS, 6)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_MAXHOURS, default=current_max_hours): int,
                }
            ),
        )

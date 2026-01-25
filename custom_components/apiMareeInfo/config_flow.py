"""Config flow for apiMareeInfo."""
import logging
from typing import Any, Dict

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_CODE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
)
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_MAXHOURS,
    CONF_PROVIDER,
    DEFAULT_PROVIDER,
    PROVIDERS,
    PROVIDER_STORMGLASS,
)
from . import apiMareeInfo

_LOGGER = logging.getLogger(__name__)

CONF_STORM_KEY = "stormio_key"


class ApiMareeInfoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for apiMareeInfo."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input: Dict[str, Any] = None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                # You might want to validate the input here, e.g., by making an API call
                lat = user_input[CONF_LATITUDE]
                lon = user_input[CONF_LONGITUDE]
                provider = user_input[CONF_PROVIDER]
                
                # A simple check for valid coordinates
                if user_input[CONF_PROVIDER] == PROVIDER_STORMGLASS and not user_input.get(CONF_STORM_KEY):
                    errors["base"] = "storm_key_required"
                elif not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    errors["base"] = "invalid_coords"
                else:
                    # Unique ID based on coordinates to prevent duplicate entries
                    await self.async_set_unique_id(f"{provider}-{lat}-{lon}")
                    self._abort_if_unique_id_configured()

                    # Clean up data: remove storm key if not stormglass provider
                    data = user_input.copy()
                    if data[CONF_PROVIDER] != PROVIDER_STORMGLASS:
                        data.pop(CONF_STORM_KEY, None)

                    return self.async_create_entry(
                        title=user_input.get(
                            CONF_NAME, f"Maree {provider} {lat}, {lon}"
                        ),
                        data=data,
                    )

            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME, default=self.hass.config.get(CONF_NAME, "")
                    ): str,
                    vol.Required(CONF_PROVIDER, default=DEFAULT_PROVIDER): vol.In(
                        PROVIDERS
                    ),
                    vol.Required(CONF_LATITUDE): vol.All(
                        vol.Coerce(float), vol.Range(min=-90, max=90)
                    ),
                    vol.Required(CONF_LONGITUDE): vol.All(
                        vol.Coerce(float), vol.Range(min=-180, max=180)
                    ),
                    vol.Optional(CONF_STORM_KEY, default=""): str,
                    vol.Optional(CONF_MAXHOURS, default=6): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for apiMareeInfo."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Dict[str, Any] = None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current values from options or data for defaults
        current_storm_key = self.config_entry.options.get(
            CONF_STORM_KEY, self.config_entry.data.get(CONF_STORM_KEY, "")
        )
        current_max_hours = self.config_entry.options.get(
            CONF_MAXHOURS, self.config_entry.data.get(CONF_MAXHOURS, 6)
        )

        schema_dict = {
            vol.Optional(CONF_MAXHOURS, default=current_max_hours): int,
        }

        # Show storm key field only if stormglass provider is selected for this entry
        provider = self.config_entry.data.get(CONF_PROVIDER, DEFAULT_PROVIDER)
        if provider == PROVIDER_STORMGLASS:
            schema_dict[vol.Optional(CONF_STORM_KEY, default=current_storm_key)] = str

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
        )

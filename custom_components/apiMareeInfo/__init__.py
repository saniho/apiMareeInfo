"""The apiMareeInfo component."""
import logging

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_MAXHOURS,
    CONF_ID,
    CONF_STORM_KEY,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_MAX_HOURS,
    __VERSION__,
)

from . import apiMareeInfo
from .exceptions import ApiError, NetworkError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up apiMareeInfo from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    config = entry.data
    options = entry.options

    lat = config[CONF_LATITUDE]
    lng = config[CONF_LONGITUDE]
    stormkey = options.get(CONF_STORM_KEY, config.get(CONF_STORM_KEY))
    maxhours = options.get(CONF_MAXHOURS, config.get(CONF_MAXHOURS, DEFAULT_MAX_HOURS))

    id_port = entry.entry_id

    maree_api = apiMareeInfo.ApiMareeInfo(version=__VERSION__)
    maree_api.setport(lat, lng)
    maree_api.setid(config.get(CONF_ID))
    maree_api.setmaxhours(maxhours)

    origine = "stormio" if stormkey else "MeteoMarine"
    info = {"stormkey": stormkey} if stormkey else None

    session = async_get_clientsession(hass)

    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            async with async_timeout.timeout(30):
                await maree_api.getinformationport(
                    origine=origine, info=info, session=session
                )
                if maree_api.has_error():
                    raise UpdateFailed(f"API Error: {maree_api.get_error_message()}")
                return maree_api
        except (ApiError, NetworkError) as err:
            raise UpdateFailed(f"API error: {err}") from err
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}-{id_port}",
        update_method=async_update_data,
        update_interval=DEFAULT_SCAN_INTERVAL,
        config_entry=entry,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

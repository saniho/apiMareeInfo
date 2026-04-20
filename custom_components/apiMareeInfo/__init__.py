"""The apiMareeInfo component."""
import logging

# Importation optionnelle de homeassistant pour supportez l'utilisation sans homeassistant installé
try:
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
        CONF_SCAN_INTERVAL_HTTP,
    )
    _HOMEASSISTANT_AVAILABLE = True
except ImportError:
    _HOMEASSISTANT_AVAILABLE = False

from . import apiMareeInfo

_LOGGER = logging.getLogger(__name__)


if _HOMEASSISTANT_AVAILABLE:
    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
        """Set up apiMareeInfo from a config entry."""
        hass.data.setdefault(DOMAIN, {})

        config = entry.data
        options = entry.options

        lat = config[CONF_LATITUDE]
        lng = config[CONF_LONGITUDE]

        # Gestion de la compatibilité ou surcharge par les options
        maxhours = options.get(CONF_MAXHOURS, config.get(CONF_MAXHOURS, 6))

        maree_api = apiMareeInfo.ApiMareeInfo()
        maree_api.setport(lat, lng)
        maree_api.setmaxhours(maxhours)

        session = async_get_clientsession(hass)

        async def async_update_data():
            """Fetch data from API endpoint."""
            try:
                async with async_timeout.timeout(30):
                    await maree_api.getinformationport(
                        origine="MeteoMarine", info=None, session=session
                    )
                    if maree_api.getError():
                        raise UpdateFailed(f"API Error: {maree_api.getErrorMessage()}")
                    return maree_api
            except Exception as err:
                raise UpdateFailed(f"Error communicating with API: {err}") from err

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{entry.unique_id}",
            update_method=async_update_data,
            update_interval=CONF_SCAN_INTERVAL_HTTP,
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

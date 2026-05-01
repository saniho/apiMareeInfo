"""Weather platform for apiMareeInfo."""
import logging
from datetime import datetime

from homeassistant.components.weather import (
    WeatherEntity,
    Forecast,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfSpeed, UnitOfPrecipitationDepth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, __VERSION__

_LOGGER = logging.getLogger(__name__)

CONDITION_MAP = {
    "c0000": "clear-night",
    "c0010": "sunny",
    "c0020": "partlycloudy",
    "c0023": "partlycloudy",
    "c0025": "partlycloudy",
    "c0030": "cloudy",
    "c0043": "cloudy",
    "c0050": "cloudy",
    "c0055": "cloudy",
    "c0060": "cloudy",
    "c0061": "cloudy",
    "c0070": "cloudy",
    "c0080": "cloudy",
    "p0010": "rainy",
    "p0020": "rainy",
    "p0030": "rainy",
    "p0050": "rainy",
    "p0060": "rainy",
    "x3050": "snowy",
    "x3060": "snowy",
    "x7060": "snowy",
    "x8030": "snowy",
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the weather platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    id_port = entry.entry_id
    async_add_entities([MareeWeather(coordinator, id_port)], True)


class MareeWeather(CoordinatorEntity, WeatherEntity):
    """Representation of a weather entity."""

    _attr_has_entity_name = True
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS

    def __init__(self, coordinator: DataUpdateCoordinator, id_port: str):
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._id_port = id_port
        self._attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY

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

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return f"{self._id_port}_weather"

    @property
    def name(self):
        """Return the name of the entity."""
        return "Météo"

    def _get_current_data(self):
        """Get the current weather data."""
        previs = self.coordinator.data.getprevis()
        if not previs:
            return None
        
        now = datetime.now()
        # Find the closest forecast in the past or now
        closest_dt = None
        for dt in sorted(previs.keys()):
            if dt <= now:
                closest_dt = dt
            else:
                break
        
        if closest_dt:
            return previs[closest_dt]
        return list(previs.values())[0] if previs else None

    @property
    def native_temperature(self):
        """Return the temperature."""
        data = self._get_current_data()
        if data:
            return data.get("t")
        return None

    @property
    def native_wind_speed(self):
        """Return the wind speed."""
        data = self._get_current_data()
        if data:
            return data.get("forcevnds")
        return None

    @property
    def wind_bearing(self):
        """Return the wind bearing."""
        data = self._get_current_data()
        if data:
            return data.get("dirvdegres")
        return None

    @property
    def humidity(self):
        """Return the humidity."""
        # Not available in current API?
        return None

    @property
    def cloud_coverage(self):
        """Return the cloud coverage."""
        data = self._get_current_data()
        if data:
            return data.get("nuagecouverture")
        return None

    @property
    def condition(self):
        """Return the current condition."""
        data = self._get_current_data()
        if data:
            nebu = data.get("nebu")
            return CONDITION_MAP.get(nebu, "cloudy")
        return "cloudy"

    async def async_forecast_hourly(self) -> list[Forecast]:
        """Return the hourly forecast."""
        previs = self.coordinator.data.getprevis()
        forecasts = []
        now = datetime.now()
        for dt, data in previs.items():
            if dt < now:
                continue
            
            forecast = Forecast(
                datetime=dt.isoformat(),
                native_temperature=data.get("t"),
                native_wind_speed=data.get("forcevnds"),
                wind_bearing=data.get("dirvdegres"),
                native_precipitation=data.get("precipitation"),
                condition=CONDITION_MAP.get(data.get("nebu"), "cloudy"),
                cloud_coverage=data.get("nuagecouverture"),
            )
            forecasts.append(forecast)
        return forecasts

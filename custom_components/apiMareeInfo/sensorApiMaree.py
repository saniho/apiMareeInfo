"""Gestion de l'état des capteurs marée/météo."""

from __future__ import annotations

import datetime
import logging
from typing import Any

from .apiMareeInfo import ApiMareeInfo
from .types import ForecastData, LiveForecastItemRaw, TideData


class SensorStateManager:
    """Gestionnaire d'état pour les capteurs marée/météo."""

    def __init__(self) -> None:
        self._myPort: ApiMareeInfo | None = None
        self._LOGGER: logging.Logger = logging.getLogger(__name__)
        self.version: str | None = None

    def init(
        self,
        _myPort: ApiMareeInfo,
        _LOGGER: logging.Logger | None = None,
        version: str | None = None,
    ) -> None:
        self._myPort = _myPort
        if _LOGGER is None:
            _LOGGER = logging.getLogger(__name__)
        self._LOGGER = _LOGGER
        self.version = version

    # ------------------------------------------------------------------
    # Helpers to reduce duplication across getstatus* methods
    # ------------------------------------------------------------------

    def _init_status(self, with_http_update: bool = False) -> dict[str, Any]:
        """Build the common status dict shared by every getstatus* method."""
        sc: dict[str, Any] = {
            "version": self.version,
            "attribution": "Data provided by apiMareeInfo",
            "last_update": datetime.datetime.now(),
        }
        if with_http_update:
            sc["last_http_update"] = self._myPort.get_http_request_time()
        return sc

    def _get_data_source(self) -> str:
        """Return the data source label based on live vs forecast availability."""
        return (
            "MeteoConsult Live"
            if self._myPort._donneesPrevisLive
            else "MeteoConsult Forecast (Hourly)"
        )

    def _get_live_or_forecast(
        self,
    ) -> tuple[LiveForecastItemRaw | ForecastData | None, str | None]:
        """Common pattern: try live data first, fall back to next hourly forecast.

        Returns (data_dict_or_None, source_label_or_None).
        """
        data = self._myPort.get_current_live_data()
        if data:
            return data, "MeteoConsult Live"

        date_courante = datetime.datetime.now()
        for x in sorted(self._myPort.get_forecast_data().keys()):
            if x > date_courante:
                return self._myPort.get_forecast_data()[x], "MeteoConsult Forecast (Hourly)"
        return None, None

    # ------------------------------------------------------------------
    # Tide helpers
    # ------------------------------------------------------------------

    def getnextmaree(
        self, indice: int = 1, maintenant: datetime.datetime | None = None
    ) -> TideData | None:
        i = 1
        if maintenant is None:
            maintenant = datetime.datetime.now()

        sorted_marees = sorted(
            self._myPort.get_tide_data().values(), key=lambda x: x["dateComplete"]
        )

        for maree in sorted_marees:
            if maintenant < maree["dateComplete"]:
                if indice == i:
                    return maree
                i += 1
        return None

    # ------------------------------------------------------------------
    # getstatus (main tide status – unique logic, kept as-is)
    # ------------------------------------------------------------------

    def getstatus(self) -> tuple[str, dict[str, Any]]:
        status_counts: dict[str, Any] = {}
        status_counts["version"] = self.version

        if self._myPort.has_error():
            status_counts["message"] = self._myPort.get_error_message()
            return "unavailable", status_counts

        status_counts["nomPort"] = self._myPort.get_port_name()
        status_counts["idPort"] = self._myPort.getid()
        status_counts["Copyright"] = self._myPort.getcopyright()
        status_counts["dateCourante"] = self._myPort.get_current_date()

        for info in self._myPort.get_tide_data().values():
            jour = info["jour"]
            nieme = info["nieme"]
            status_counts[f"horaire_{jour}_{nieme}"] = info["horaire"]
            status_counts[f"coeff_{jour}_{nieme}"] = info.get("coeff", "")
            status_counts[f"etat_{jour}_{nieme}"] = info["etat"]
            status_counts[f"hauteur_{jour}_{nieme}"] = info["hauteur"]
            status_counts[f"nb_maree_{jour}"] = (
                status_counts.get(f"nb_maree_{jour}", 0) + 1
            )

        for i in range(1, 3):
            pMaree = self.getnextmaree(i)
            if pMaree:
                status_counts[f"next_maree_{i}"] = pMaree["horaire"]
                status_counts[f"next_coeff_{i}"] = pMaree.get("coeff", "")
                status_counts[f"next_etat_{i}"] = pMaree["etat"]

        status_counts["timeLastCall"] = datetime.datetime.now()

        maxTime = datetime.datetime.now() + datetime.timedelta(
            hours=self._myPort.get_max_hours()
        )
        dicoPrevis = [
            previs
            for maDate, previs in self._myPort.get_forecast_data().items()
            if datetime.datetime.now() <= maDate.replace(tzinfo=None) <= maxTime
        ]
        status_counts["prevision"] = dicoPrevis

        next_maree = self.getnextmaree(1)
        if next_maree:
            status_counts["message"] = (
                f"{next_maree['horaire']} ({next_maree['etat']}/{next_maree.get('coeff', '')})"
            )
            state = next_maree["horaire"]
        else:
            state = "unavailable"

        status_counts["last_update"] = datetime.datetime.now()
        status_counts["last_http_update"] = self._myPort.get_http_request_time()

        return state, status_counts

    # ------------------------------------------------------------------
    # get_next_tide_state
    # ------------------------------------------------------------------

    def get_next_tide_state(self, pmbm: str = "") -> tuple[str, dict[str, Any]]:
        sc = self._init_status(with_http_update=True)

        next_maree = self.getnextmaree(1)
        if next_maree and next_maree["etat"] == pmbm:
            maree = next_maree
        else:
            maree = self.getnextmaree(2)

        if maree and maree["etat"] == pmbm:
            state = maree["horaire"]
            sc["coeff"] = maree.get("coeff", "")
            sc["hauteur"] = maree.get("hauteur", "")
        else:
            state = "unavailable"

        return state, sc

    # ------------------------------------------------------------------
    # get_next_rain_status
    # ------------------------------------------------------------------

    def get_next_rain_status(self) -> tuple[datetime.datetime | str, dict[str, Any]]:
        sc = self._init_status(with_http_update=True)

        dateNextPluie, precipitation = self._myPort.get_next_rain()
        if dateNextPluie:
            dateNextPluieCh = dateNextPluie.strftime("%d/%m %H:%M")
            state: datetime.datetime | str = dateNextPluie
        else:
            dateNextPluieCh = ""
            state = "unavailable"

        sc["prochainePluie"] = dateNextPluieCh
        sc["precipitation"] = precipitation
        sc["message"] = f"{dateNextPluieCh} - {precipitation} mm"

        _, forecast, _ = self._myPort.get_1h_forecast()
        sc["1_hour_forecast"] = forecast

        return state, sc

    # ------------------------------------------------------------------
    # get_water_temp_status
    # ------------------------------------------------------------------

    def get_water_temp_status(self) -> tuple[str, dict[str, Any]]:
        sc = self._init_status(with_http_update=True)

        dateTemperatureEau, teau = self._myPort.get_water_temperature()
        if dateTemperatureEau:
            state = teau
        else:
            state = "unavailable"

        sc["dateTemperatureEau"] = (
            dateTemperatureEau.strftime("%d/%m %H:%M") if dateTemperatureEau else ""
        )
        sc["teau"] = teau

        return state, sc

    # ------------------------------------------------------------------
    # get_weather_status
    # ------------------------------------------------------------------

    def get_weather_status(self) -> tuple[str, dict[str, Any]]:
        sc = self._init_status(with_http_update=True)

        forecast_time_ref, forecast, source = self._myPort.get_1h_forecast()
        state = forecast.get("0 min", "Temps sec")

        sc["forecast_time_ref"] = forecast_time_ref.isoformat()
        sc["1_hour_forecast"] = forecast
        sc["data_source"] = source

        return state, sc

    # ------------------------------------------------------------------
    # get_rain_chance_status
    # ------------------------------------------------------------------

    def get_rain_chance_status(self) -> tuple[int, dict[str, Any]]:
        sc = self._init_status()
        state = self._myPort.get_rain_chance()
        sc["data_source"] = self._get_data_source()
        return state, sc

    # ------------------------------------------------------------------
    # get_cloud_cover_status
    # ------------------------------------------------------------------

    def get_cloud_cover_status(self) -> tuple[int, dict[str, Any]]:
        sc = self._init_status()
        state = self._myPort.get_cloud_cover()
        sc["data_source"] = "MeteoConsult Forecast (Hourly)"
        return state, sc

    # ------------------------------------------------------------------
    # get_weather_alert_status
    # ------------------------------------------------------------------

    def get_weather_alert_status(self) -> tuple[str, dict[str, Any]]:
        sc = self._init_status()
        state = self._myPort.get_weather_alert()
        sc["data_source"] = "MeteoConsult"
        return state, sc

    # ------------------------------------------------------------------
    # get_pressure_status
    # ------------------------------------------------------------------

    def get_pressure_status(self) -> tuple[str | None, dict[str, Any]]:
        sc = self._init_status()
        state, forecast = self._myPort.get_pressure_forecast()
        sc["pressure_forecast"] = forecast
        sc["data_source"] = self._get_data_source()
        return state, sc

    # ------------------------------------------------------------------
    # get_wave_status
    # ------------------------------------------------------------------

    def get_wave_status(self) -> tuple[str | None, dict[str, Any]]:
        sc = self._init_status()
        data, source = self._get_live_or_forecast()
        if data:
            is_live = source == "MeteoConsult Live"
            state = data.get("wave_height" if is_live else "hauteurvague")
            sc["wave_height_max"] = data.get("wave_height_max" if is_live else "hauteurmerv")
            sc["wave_direction"] = data.get("wave_direction" if is_live else "dirhouledegres")
            sc["swell_height"] = data.get("swell_height" if is_live else "hauteurhoule")
            if is_live:
                sc["sea_code"] = data.get("sea_code")
                sc["wave_direction_deg"] = data.get("wave_direction")
            sc["data_source"] = source
        else:
            state = "unavailable"
        return state, sc

    # ------------------------------------------------------------------
    # get_wind_status
    # ------------------------------------------------------------------

    def get_wind_status(self) -> tuple[str | None, dict[str, Any]]:
        sc = self._init_status()
        data, source = self._get_live_or_forecast()
        if data:
            is_live = source == "MeteoConsult Live"
            state = data.get("wind_speed" if is_live else "forcevnds")
            sc["wind_gust"] = data.get("wind_gust" if is_live else "rafvnds")
            sc["wind_direction"] = data.get("wind_direction" if is_live else "dirvdegres")
            sc["data_source"] = source
        else:
            state = "unavailable"
        return state, sc

    # ------------------------------------------------------------------
    # get_air_temp_status
    # ------------------------------------------------------------------

    def get_air_temp_status(self) -> tuple[str | None, dict[str, Any]]:
        sc = self._init_status()
        data, source = self._get_live_or_forecast()
        if data:
            is_live = source == "MeteoConsult Live"
            state = data.get("tempe" if is_live else "t")
            if is_live:
                sc["tempe_felt"] = data.get("tempe_felt")
            sc["data_source"] = source
        else:
            state = "unavailable"
        return state, sc

    # ------------------------------------------------------------------
    # get_visibility_status
    # ------------------------------------------------------------------

    def get_visibility_status(self) -> tuple[str | None, dict[str, Any]]:
        sc = self._init_status()
        data = self._myPort.get_current_live_data()
        if data:
            state = data.get("visibility")
            sc["data_source"] = "MeteoConsult Live"
        else:
            state = "unavailable"
        return state, sc

    # ------------------------------------------------------------------
    # get_water_level_status
    # ------------------------------------------------------------------

    def get_water_level_status(self) -> tuple[float | str, dict[str, Any]]:
        sc = self._init_status()
        level, status = self._myPort.get_current_water_level()
        if level is not None:
            state: float | str = level
            sc["tide_status"] = status
            sc["data_source"] = "Calculated (Sinusoidal Interpolation)"
        else:
            state = "unavailable"
        return state, sc

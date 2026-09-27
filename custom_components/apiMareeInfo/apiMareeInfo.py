"""API client for marine weather data (MeteoConsult, StormGlass)."""

from __future__ import annotations

import datetime
import logging
import math
from typing import Any

from .http_utils import async_fetch_json
from .parsers import ParsedData, parse_meteo_marine, parse_storm_io
from .types import ForecastData, LiveForecastItemRaw, TideData

_LOGGER = logging.getLogger(__name__)


class ListePorts:
    """Recherche de ports via l'API MeteoConsult."""

    async def getjson(
        self,
        url: str,
        session: Any | None = None,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return await async_fetch_json(
            url, session=session, params=params, source_name="ListePorts"
        )

    async def getlisteport(
        self, nomport: str, session: Any | None = None
    ) -> dict[str, Any]:
        url = "https://ws.meteoconsult.fr/meteoconsultmarine/android/100/fr/v30/recherche.php"
        params = {"rech": nomport}
        return await self.getjson(url, session, params=params)


class MeteoMarine:
    """Récupération des données marées via l'API MeteoConsult."""

    def __init__(self, lat: float, lng: float) -> None:
        self._url = (
            "https://ws.meteoconsult.fr/meteoconsultmarine/androidtab/115/fr/v30/previsionsSpot.php?lat=%s&lon=%s"
            % (lat, lng)
        )

    async def getdata(self, session: Any | None = None) -> dict[str, Any]:
        return await async_fetch_json(
            self._url, session=session, source_name="MeteoMarine"
        )


class MeteoMarineLive:
    """Récupération des données live (5-min) via l'API MeteoConsult."""

    def __init__(self, id_port: str) -> None:
        self._id_port = id_port

    async def getdata(self, session: Any | None = None) -> dict[str, Any]:
        now = datetime.datetime.now()
        day = now.strftime("%Y-%m-%d")
        url = (
            "https://ws.meteoconsult.fr/meteoconsultmarine/android/100/en/v40/forecasts/live?day=%s&id=%s&limit=1&type_string=beaches"
            % (day, self._id_port)
        )
        return await async_fetch_json(
            url, session=session, source_name="MeteoMarineLive"
        )


class StormIO:
    """Récupération des données marées via l'API StormGlass."""

    def __init__(self, lat: float, lng: float, storm_key: str) -> None:
        self._lat = lat
        self._lng = lng
        self._storm_key = storm_key

    async def getdata(self, session: Any | None = None) -> dict[str, Any]:
        now = datetime.datetime.now()
        nowJ2 = now + datetime.timedelta(days=2)
        self._deb = now.strftime("%Y-%m-%d %H:%M:%S+00:00")
        self._fin = nowJ2.strftime("%Y-%m-%d %H:%M:%S+00:00")

        params = {
            "lat": self._lat,
            "lng": self._lng,
            "start": self._deb,
            "end": self._fin,
        }
        headers = {"Authorization": self._storm_key}
        url = "https://api.stormglass.io/v2/tide/extremes/point"

        return await async_fetch_json(
            url,
            session=session,
            params=params,
            headers=headers,
            timeout=600,
            source_name="StormIO",
        )


class ApiMareeInfo:
    """Classe principale d'accès aux données marées et météo."""

    def __init__(self, version: str | None = None) -> None:
        self.version = version
        self._donnees: dict[str, TideData] = {}
        self._nomDuPort: str = ""
        self._dateCourante: datetime.datetime | None = None
        self._maxhours: int | None = None
        self._lat: float | None = None
        self._lng: float | None = None
        self._id: str | None = None
        self._message: str = ""
        self._error: bool = False
        self._errorMessage: str = ""
        self._httptimerequest: datetime.datetime = datetime.datetime.now()
        self._meteofrance_precipitation: float = 0
        self._donneesPrevis: dict[datetime.datetime, ForecastData] = {}
        self._donneesPrevisLive: dict[datetime.datetime, LiveForecastItemRaw] = {}
        self._avis: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # API fetching
    # ------------------------------------------------------------------

    async def _fetch_json(
        self,
        origine: str,
        info: dict[str, str] | None = None,
        session: Any | None = None,
    ) -> dict[str, Any] | None:
        if origine == "MeteoMarine":
            api = MeteoMarine(self._lat, self._lng)  # type: ignore[arg-type]
            return await api.getdata(session)
        elif origine == "MeteoMarineLive":
            api_live = MeteoMarineLive(self._id)  # type: ignore[arg-type]
            return await api_live.getdata(session)
        elif origine == "stormio":
            api_storm = StormIO(self._lat, self._lng, info["stormkey"])  # type: ignore[arg-type, index]
            return await api_storm.getdata(session)
        return None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def setport(self, lat: float, lng: float) -> None:
        self._lat = lat
        self._lng = lng

    def setid(self, id: str) -> None:
        self._id = id

    def setmaxhours(self, maxhours: int) -> None:
        self._maxhours = maxhours

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    async def getinformationport(
        self,
        jsondata: dict[str, Any] | None = None,
        origine: str = "MeteoMarine",
        info: dict[str, str] | None = None,
        session: Any | None = None,
    ) -> None:
        self._donneesPrevisLive = {}
        self._donneesPrevis = {}
        if jsondata is None:
            jsondata = await self._fetch_json(origine, info, session)

        if origine == "MeteoMarine":
            parsed = parse_meteo_marine(jsondata or {}, self._lat, self._lng)
            self._apply_parsed(parsed)

            if self._id:
                live_jsondata = await self._fetch_json("MeteoMarineLive", session=session)
                self._donneesPrevisLive = {}
                if live_jsondata and "content" in live_jsondata and "forecasts" in live_jsondata["content"]:
                    for f in live_jsondata["content"]["forecasts"]:
                        dt = datetime.datetime.fromisoformat(f["datetime"])
                        self._donneesPrevisLive[dt.replace(tzinfo=None)] = f

        elif origine == "stormio":
            parsed = parse_storm_io(jsondata or {}, self._dateCourante)
            self._apply_parsed(parsed)
            self._dateCourante = datetime.datetime.now()
        else:
            raise RuntimeError("Data Origin unknown")

        self._httptimerequest = datetime.datetime.now()

    def _apply_parsed(self, parsed: ParsedData) -> None:
        """Apply parsed data to internal state."""
        self._nomDuPort = parsed.port_name
        self._dateCourante = parsed.date_courante
        self._avis = parsed.avis
        self._error = parsed.error
        self._errorMessage = parsed.error_message
        self._donnees = parsed.tides
        self._donneesPrevis = parsed.forecasts

    # ------------------------------------------------------------------
    # Raw data accessors
    # ------------------------------------------------------------------

    def get_port_name(self) -> str:
        if self._nomDuPort:
            return self._nomDuPort.split("©")[0].strip()
        return "Unknown"

    def getcopyright(self) -> str:
        return "©SHOM"

    def get_full_port_name(self) -> str | None:
        return self._nomDuPort or None

    def get_current_date(self) -> datetime.datetime | None:
        return self._dateCourante

    def get_max_hours(self) -> int | None:
        return self._maxhours

    def get_lat(self) -> float | None:
        return self._lat

    def get_lng(self) -> float | None:
        return self._lng

    def getid(self) -> str | None:
        return self._id

    def get_http_request_time(self) -> datetime.datetime:
        return self._httptimerequest

    def get_tide_data(self) -> dict[str, TideData]:
        return self._donnees

    def get_forecast_data(self) -> dict[datetime.datetime, ForecastData]:
        return self._donneesPrevis

    def has_error(self) -> bool:
        return self._error

    def get_error_message(self) -> str:
        return self._errorMessage

    # ------------------------------------------------------------------
    # Derived data helpers
    # ------------------------------------------------------------------

    def get_next_rain(self) -> tuple[datetime.datetime | None, float]:
        now = datetime.datetime.now()
        for dt in self._donneesPrevis.keys():
            if self._donneesPrevis[dt]["dateComplete"] > now:
                if self._donneesPrevis[dt]["precipitation"] != 0:
                    precip = self._donneesPrevis[dt]["precipitation"]
                    return self._donneesPrevis[dt]["dateComplete"], float(precip) if precip else 0.0
        return None, 0

    def get_water_temperature(self) -> tuple[datetime.datetime | None, str]:
        now = datetime.datetime.now()
        for dt in self._donneesPrevis.keys():
            if self._donneesPrevis[dt]["dateComplete"] > now:
                return self._donneesPrevis[dt]["dateComplete"], self._donneesPrevis[dt]["teau"]
        return None, ""

    def get_1h_forecast(self) -> tuple[datetime.datetime, dict[str, str], str]:
        now = datetime.datetime.now()
        forecast: dict[str, str] = {}

        if self._donneesPrevisLive:
            sorted_keys = sorted(self._donneesPrevisLive.keys())
            start_time: datetime.datetime | None = None
            for k in sorted_keys:
                if k >= now - datetime.timedelta(seconds=120):
                    start_time = k
                    break

            if start_time:
                for i in range(0, 65, 5):
                    target_dt = start_time + datetime.timedelta(minutes=i)
                    if target_dt in self._donneesPrevisLive:
                        risk = self._donneesPrevisLive[target_dt].get("precip_risk", 0)
                        forecast[f"{i} min"] = _label_risk(risk)
                    else:
                        forecast[f"{i} min"] = "Indisponible"
                return start_time, forecast, "MeteoConsult Live"

        start_time = now.replace(second=0, microsecond=0)
        start_time -= datetime.timedelta(minutes=start_time.minute % 5)

        for i in range(0, 65, 5):
            target_dt = start_time + datetime.timedelta(minutes=i)
            target_hour = target_dt.replace(minute=0, second=0, microsecond=0)
            if target_hour in self._donneesPrevis:
                mm = float(self._donneesPrevis[target_hour].get("precipitation", 0) or 0)
                forecast[f"{i} min"] = _label_rain(mm)
            else:
                forecast[f"{i} min"] = "Indisponible"

        return start_time, forecast, "MeteoConsult Forecast (Hourly Sliding)"

    def get_rain_chance(self) -> int:
        now = datetime.datetime.now()
        for x in sorted(self._donneesPrevisLive.keys()):
            if x > now:
                return self._donneesPrevisLive[x].get("precip_risk", 0)
        return 0

    def get_cloud_cover(self) -> int:
        now = datetime.datetime.now()
        for x in sorted(self._donneesPrevis.keys()):
            if x > now:
                val = self._donneesPrevis[x].get("nuagecouverture", 0)
                return int(val) if val else 0
        return 0

    def get_uv(self) -> int:
        now = datetime.datetime.now()
        for x in sorted(self._donneesPrevis.keys()):
            if x > now:
                val = self._donneesPrevis[x].get("uv", 0)
                return int(val) if val else 0
        return 0

    def get_current_live_data(self) -> LiveForecastItemRaw | None:
        if not self._donneesPrevisLive:
            return None
        now = datetime.datetime.now()
        closest_dt = min(self._donneesPrevisLive.keys(), key=lambda x: abs(x - now))
        if abs(closest_dt - now) > datetime.timedelta(minutes=15):
            return None
        return self._donneesPrevisLive[closest_dt]

    def get_current_water_level(self) -> tuple[float | None, str | None]:
        now = datetime.datetime.now()
        sorted_marees = sorted(self._donnees.values(), key=lambda x: x["dateComplete"])
        if not sorted_marees:
            return None, None

        previous_tide: TideData | None = None
        next_tide: TideData | None = None
        for maree in sorted_marees:
            if maree["dateComplete"] <= now:
                previous_tide = maree
            elif maree["dateComplete"] > now:
                next_tide = maree
                break

        if not previous_tide or not next_tide:
            return None, None

        duration = (next_tide["dateComplete"] - previous_tide["dateComplete"]).total_seconds()
        elapsed = (now - previous_tide["dateComplete"]).total_seconds()
        h_prev = float(previous_tide["hauteur"])
        h_next = float(next_tide["hauteur"])
        level = h_prev + (h_next - h_prev) * (1 - math.cos(math.pi * elapsed / duration)) / 2
        status = "Montante" if next_tide["etat"] == "PM" else "Descendante"
        return round(level, 2), status

    def get_weather_alert(self) -> str:
        if not self._avis:
            return "Aucun"
        for avis in self._avis:
            niveau = avis.get("niveau", 0)
            if isinstance(niveau, (int, float)) and niveau > 0:
                return str(avis.get("phrase", "Alerte météo"))
        return "Aucun"

    def get_pressure_forecast(self) -> tuple[str | None, dict[str, str]]:
        now = datetime.datetime.now()
        forecast: dict[str, str] = {}
        current_pressure: str | None = None

        all_data: dict[datetime.datetime, dict[str, Any]] = {k: dict(v) for k, v in self._donneesPrevis.items()}
        for dt, data in self._donneesPrevisLive.items():
            if "pressure" in data or "pression" in data:
                merged: dict[str, Any] = {**all_data.get(dt, {})}
                merged["pressure"] = data.get("pressure") or data.get("pression", "")
                all_data[dt] = merged

        sorted_keys = sorted(all_data.keys())
        for k in sorted_keys:
            val = all_data[k].get("pressure") or all_data[k].get("pression")
            if val:
                val_str = str(val)
                if k <= now:
                    current_pressure = val_str
                else:
                    forecast[k.isoformat()] = val_str

        if current_pressure is None and sorted_keys:
            fallback = all_data[sorted_keys[0]].get("pressure") or all_data[sorted_keys[0]].get("pression")
            current_pressure = str(fallback) if fallback else None

        return current_pressure, forecast

    def get_prochaine_grande_maree(self) -> TideData | None:
        """Return the next tide with coefficient >= 100, or None."""
        now = datetime.datetime.now()
        sorted_marees = sorted(self._donnees.values(), key=lambda x: x["dateComplete"])
        for maree in sorted_marees:
            coeff = maree.get("coeff", "")
            if coeff == "":
                continue
            try:
                coeff_int = int(coeff)
            except (ValueError, TypeError):
                continue
            if (
                maree["dateComplete"] > now
                and maree["etat"] == "PM"
                and coeff_int >= 100
            ):
                return maree
        return None

    def getnextmaree(
        self, indice: int = 1, maintenant: datetime.datetime | None = None
    ) -> TideData | None:
        """Return the Nth future tide."""
        i = 1
        if maintenant is None:
            maintenant = datetime.datetime.now()
        sorted_marees = sorted(self._donnees.values(), key=lambda x: x["dateComplete"])
        for maree in sorted_marees:
            if maintenant < maree["dateComplete"]:
                if indice == i:
                    return maree
                i += 1
        return None

    # ------------------------------------------------------------------
    # Status methods (return (state, attributes) for HA sensors)
    # ------------------------------------------------------------------

    def _base_attrs(self, with_http_update: bool = False) -> dict[str, Any]:
        """Build common status dict shared by every status method."""
        sc: dict[str, Any] = {
            "version": self.version,
            "attribution": "Data provided by apiMareeInfo",
            "last_update": datetime.datetime.now(),
        }
        if with_http_update:
            sc["last_http_update"] = self._httptimerequest
        return sc

    def _get_data_source(self) -> str:
        return (
            "MeteoConsult Live"
            if self._donneesPrevisLive
            else "MeteoConsult Forecast (Hourly)"
        )

    def _get_live_or_forecast(
        self,
    ) -> tuple[LiveForecastItemRaw | ForecastData | None, str | None]:
        data = self.get_current_live_data()
        if data:
            return data, "MeteoConsult Live"
        now = datetime.datetime.now()
        for x in sorted(self._donneesPrevis.keys()):
            if x > now:
                return self._donneesPrevis[x], "MeteoConsult Forecast (Hourly)"
        return None, None

    def getstatus(self) -> tuple[str, dict[str, Any]]:
        status_counts: dict[str, Any] = {}
        status_counts["version"] = self.version

        if self._error:
            status_counts["message"] = self._errorMessage
            return "unavailable", status_counts

        status_counts["nomPort"] = self.get_port_name()
        status_counts["idPort"] = self.getid()
        status_counts["Copyright"] = self.getcopyright()
        status_counts["dateCourante"] = self._dateCourante

        for info in self._donnees.values():
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
            hours=self.get_max_hours() or 6
        )
        dicoPrevis = [
            previs
            for maDate, previs in self._donneesPrevis.items()
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
        status_counts["last_http_update"] = self._httptimerequest

        return state, status_counts

    def get_next_tide_state(self, pmbm: str = "") -> tuple[str, dict[str, Any]]:
        sc = self._base_attrs(with_http_update=True)

        next_maree = self.getnextmaree(1)
        if next_maree and next_maree["etat"] == pmbm:
            maree: TideData | None = next_maree
        else:
            maree = self.getnextmaree(2)

        if maree and maree["etat"] == pmbm:
            state = maree["horaire"]
            sc["coeff"] = maree.get("coeff", "")
            sc["hauteur"] = maree.get("hauteur", "")
        else:
            state = "unavailable"

        return state, sc

    def get_next_rain_status(self) -> tuple[datetime.datetime | str, dict[str, Any]]:
        sc = self._base_attrs(with_http_update=True)

        dateNextPluie, precipitation = self.get_next_rain()
        if dateNextPluie:
            dateNextPluieCh = dateNextPluie.strftime("%d/%m %H:%M")
            state: datetime.datetime | str = dateNextPluie
        else:
            dateNextPluieCh = ""
            state = "unavailable"

        sc["prochainePluie"] = dateNextPluieCh
        sc["precipitation"] = precipitation
        sc["message"] = f"{dateNextPluieCh} - {precipitation} mm"

        _, forecast, _ = self.get_1h_forecast()
        sc["1_hour_forecast"] = forecast

        return state, sc

    def get_water_temp_status(self) -> tuple[str, dict[str, Any]]:
        sc = self._base_attrs(with_http_update=True)

        dateTemperatureEau, teau = self.get_water_temperature()
        if dateTemperatureEau:
            state = teau
        else:
            state = "unavailable"

        sc["dateTemperatureEau"] = (
            dateTemperatureEau.strftime("%d/%m %H:%M") if dateTemperatureEau else ""
        )
        sc["teau"] = teau

        return state, sc

    def get_weather_status(self) -> tuple[str, dict[str, Any]]:
        sc = self._base_attrs(with_http_update=True)

        forecast_time_ref, forecast, source = self.get_1h_forecast()
        state = forecast.get("0 min", "Temps sec")

        sc["forecast_time_ref"] = forecast_time_ref.isoformat()
        sc["1_hour_forecast"] = forecast
        sc["data_source"] = source

        return state, sc

    def get_rain_chance_status(self) -> tuple[int, dict[str, Any]]:
        sc = self._base_attrs()
        state = self.get_rain_chance()
        sc["data_source"] = self._get_data_source()
        return state, sc

    def get_cloud_cover_status(self) -> tuple[int, dict[str, Any]]:
        sc = self._base_attrs()
        state = self.get_cloud_cover()
        sc["data_source"] = "MeteoConsult Forecast (Hourly)"
        return state, sc

    def get_uv_status(self) -> tuple[int, dict[str, Any]]:
        sc = self._base_attrs()
        state = self.get_uv()
        sc["data_source"] = "MeteoConsult Forecast (Hourly)"
        return state, sc

    def get_weather_alert_status(self) -> tuple[str, dict[str, Any]]:
        sc = self._base_attrs()
        state = self.get_weather_alert()
        sc["data_source"] = "MeteoConsult"
        return state, sc

    def get_pressure_status(self) -> tuple[str | None, dict[str, Any]]:
        sc = self._base_attrs()
        state, forecast = self.get_pressure_forecast()
        sc["pressure_forecast"] = forecast
        sc["data_source"] = self._get_data_source()
        return state, sc

    def get_wave_status(self) -> tuple[str | None, dict[str, Any]]:
        sc = self._base_attrs()
        data, source = self._get_live_or_forecast()
        if data:
            is_live = source == "MeteoConsult Live"
            state = str(data.get("wave_height" if is_live else "hauteurvague", "")) or None
            sc["wave_height_max"] = str(data.get("wave_height_max" if is_live else "hauteurmerv", ""))
            sc["wave_direction"] = str(data.get("wave_direction" if is_live else "dirhouledegres", ""))
            sc["swell_height"] = str(data.get("swell_height" if is_live else "hauteurhoule", ""))
            if is_live:
                sc["sea_code"] = data.get("sea_code")
                sc["wave_direction_deg"] = data.get("wave_direction")
            sc["data_source"] = source
        else:
            state = None
        return state, sc

    def get_wind_status(self) -> tuple[str | None, dict[str, Any]]:
        sc = self._base_attrs()
        data, source = self._get_live_or_forecast()
        if data:
            is_live = source == "MeteoConsult Live"
            state = str(data.get("wind_speed" if is_live else "forcevnds", "")) or None
            sc["wind_gust"] = str(data.get("wind_gust" if is_live else "rafvnds", ""))
            sc["wind_direction"] = str(data.get("wind_direction" if is_live else "dirvdegres", ""))
            sc["data_source"] = source
        else:
            state = None
        return state, sc

    def get_air_temp_status(self) -> tuple[str | None, dict[str, Any]]:
        sc = self._base_attrs()
        data, source = self._get_live_or_forecast()
        if data:
            is_live = source == "MeteoConsult Live"
            state = str(data.get("tempe" if is_live else "t", "")) or None
            if is_live:
                sc["tempe_felt"] = data.get("tempe_felt")
            sc["data_source"] = source
        else:
            state = None
        return state, sc

    def get_visibility_status(self) -> tuple[str | None, dict[str, Any]]:
        sc = self._base_attrs()
        data = self.get_current_live_data()
        if data:
            state = data.get("visibility")
            sc["data_source"] = "MeteoConsult Live"
        else:
            state = "unavailable"
        return state, sc

    def get_water_level_status(self) -> tuple[float | str, dict[str, Any]]:
        sc = self._base_attrs()
        level, status = self.get_current_water_level()
        if level is not None:
            state: float | str = level
            sc["tide_status"] = status
            sc["data_source"] = "Calculated (Sinusoidal Interpolation)"
        else:
            state = "unavailable"
        return state, sc

    def get_prochaine_grande_maree_status(self) -> tuple[str, dict[str, Any]]:
        sc = self._base_attrs(with_http_update=True)

        if self._error:
            return "unavailable", sc

        maree = self.get_prochaine_grande_maree()
        if maree is None:
            return "unavailable", sc

        dt = maree["dateComplete"]
        now = datetime.datetime.now()
        delta = dt - now
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60
        if days > 0:
            delai = f"{days}j {hours}h {minutes}min"
        else:
            delai = f"{hours}h {minutes}min"

        state = dt.strftime("%Y-%m-%dT%H:%M:%S")
        sc["coefficient"] = maree.get("coeff", "")
        sc["type"] = "haute"
        sc["hauteur"] = maree.get("hauteur", "")
        sc["delai"] = delai
        sc["horaire"] = maree["horaire"]
        sc["data_source"] = "MeteoConsult"

        return state, sc


# ------------------------------------------------------------------
# Label helpers
# ------------------------------------------------------------------

def _label_risk(risk: int) -> str:
    if risk == 0:
        return "Temps sec"
    if risk <= 25:
        return "Pluie faible"
    if risk <= 50:
        return "Pluie modérée"
    if risk <= 75:
        return "Pluie forte"
    return "Pluie très forte"


def _label_rain(mm: float) -> str:
    if mm == 0:
        return "Temps sec"
    if mm <= 1:
        return "Pluie faible"
    if mm <= 4:
        return "Pluie modérée"
    return "Pluie forte"

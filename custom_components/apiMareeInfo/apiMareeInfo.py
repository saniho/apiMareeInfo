"""API client for marine weather data (MeteoConsult, StormGlass)."""

from __future__ import annotations

import datetime
import logging
from typing import Any

from .http_utils import async_fetch_json
from .types import (
    ForecastData,
    LiveForecastItemRaw,
    StormGlassResponse,
    TideData,
)

_LOGGER = logging.getLogger(__name__)


class ListePorts:
    """Recherche de ports via l'API MeteoConsult."""

    def __init__(self) -> None:
        pass

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


class stormIO:
    """Récupération des données marées via l'API StormGlass."""

    def __init__(self, lat: float, lng: float, storm_key: str) -> None:
        self._lat = lat
        self._lng = lng
        self._storm_key = storm_key

    async def getdata(self, session: Any | None = None) -> StormGlassResponse:
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

    def __init__(self) -> None:
        self._donnees: dict[str, TideData] = {}
        self._nomDuPort: str | None = None
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
        self._avis: list[dict[str, object]] = []

    async def getjson(
        self,
        origine: str,
        info: dict[str, str] | None = None,
        session: Any | None = None,
    ) -> dict[str, Any] | None:
        if origine == "MeteoMarine":
            mm = MeteoMarine(self._lat, self._lng)  # type: ignore[arg-type]
            return await mm.getdata(session)
        elif origine == "MeteoMarineLive":
            mm = MeteoMarineLive(self._id)  # type: ignore[arg-type]
            return await mm.getdata(session)
        elif origine == "stormio":
            mm = stormIO(self._lat, self._lng, info["stormkey"])  # type: ignore[arg-type, index]
            return await mm.getdata(session)
        return None

    def setport(self, lat: float, lng: float) -> None:
        self._lat = lat
        self._lng = lng

    def setid(self, id: str) -> None:
        self._id = id

    def setmaxhours(self, maxhours: int) -> None:
        self._maxhours = maxhours

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
            jsondata = await self.getjson(origine, info, session)

        if origine == "MeteoMarine":
            if (
                not jsondata
                or "contenu" not in jsondata
                or len(jsondata["contenu"]["marees"]) == 0
            ):
                self._error = True
                self._errorMessage = "No tide data available from MeteoMarine"
                _LOGGER.warning("MeteoMarine data error for lat=%s, lng=%s. Response: %s", self._lat, self._lng, str(jsondata)[:200])
            else:
                self._nomDuPort = jsondata["contenu"]["marees"][0]["lieu"]
                self._dateCourante = jsondata["contenu"]["marees"][0]["datetime"]
                self._error = False
                self._avis = jsondata["contenu"].get("avis", [])

            # Fetch live data if id is available
            if self._id:
                live_jsondata = await self.getjson("MeteoMarineLive", session=session)
                self._donneesPrevisLive = {}
                if live_jsondata and "content" in live_jsondata and "forecasts" in live_jsondata["content"]:
                    for f in live_jsondata["content"]["forecasts"]:
                        dt = datetime.datetime.fromisoformat(f["datetime"])
                        self._donneesPrevisLive[dt.replace(tzinfo=None)] = f

        elif origine == "stormio":
            if not jsondata or "errors" in jsondata:
                self._nomDuPort = ""
                self._errorMessage = jsondata.get("errors", {}).get("key", "Unknown error from StormIO")
                self._error = True
            elif "station" in jsondata.get("meta", {}):
                self._nomDuPort = jsondata["meta"]["station"]['name']
                self._errorMessage = ""
                self._error = False
            self._dateCourante = datetime.datetime.now()
        else:
            raise RuntimeError("Data Origin unknown")
        self._httptimerequest = datetime.datetime.now()

        myMarees: dict[str, TideData] = {}
        dicoPrevis: dict[datetime.datetime, ForecastData] = {}
        if (origine == "MeteoMarine") and (not self._error):
            j = 0
            for maree in jsondata["contenu"]["marees"]:
                i = 0
                for ele in maree["etales"]:
                    dateComplete = datetime.datetime.fromisoformat(ele["datetime"])
                    detailMaree: TideData = {
                        "coeff": ele.get("coef", ""),
                        "hauteur": ele["hauteur"],
                        "horaire": dateComplete.strftime("%H:%M"),
                        "etat": ele["type_etale"],
                        "nieme": i,
                        "jour": j,
                        "date": ele["datetime"],
                        "dateComplete": dateComplete.replace(tzinfo=None),
                    }
                    clef = "horaire_%s_%s" % (j, i)
                    myMarees[clef] = detailMaree
                    i += 1
                j += 1
            self._donnees = myMarees

            for ele in jsondata["contenu"]["previs"]["detail"]:
                dateComplete = datetime.datetime.fromisoformat(ele["datetime"])
                detailPrevis: ForecastData = {
                    "forcevnds": ele.get("forcevnds", ""),
                    "rafvnds": ele.get("rafvnds", ""),
                    "dirvdegres": ele.get("dirvdegres", ""),
                    "dateComplete": dateComplete.replace(tzinfo=None),
                    "nebu": ele.get("nebu", ""),
                    "nuagecouverture": ele.get("nuagecouverture", ""),
                    "precipitation": ele.get("precipitation", ""),
                    "pressure": ele.get("pressure") or ele.get("pression", ""),
                    "teau": ele.get("teau", ""),
                    "t": ele.get("t", ""),
                    "risqueorage": ele.get("risqueorage", ""),
                    "dirhouledegres": ele.get("dirhouledegres", ""),
                    "hauteurhoule": ele.get("hauteurhoule", ""),
                    "periodehoule": ele.get("periodehoule", ""),
                    "hauteurmerv": ele.get("hauteurmerv", ""),
                    "periodemerv": ele.get("periodemerv", ""),
                    "hauteurvague": ele.get("hauteurvague", ""),
                    "uv": ele.get("uv", ""),
                }
                clef = dateComplete.replace(tzinfo=None)
                dicoPrevis[clef] = detailPrevis
        elif (origine == "stormio") and (not self._error):
            j = 0
            dateCompletePrevious = self._dateCourante
            for maree in jsondata["data"][:6]:
                i = 0
                dateComplete = datetime.datetime.fromisoformat(maree["time"])
                detailMaree: TideData = {
                    "coeff": maree.get("coef", ""),
                    "hauteur": maree.get("height", ""),
                    "horaire": dateComplete.strftime("%H:%M"),
                    "etat": maree["type"],
                    "nieme": i,
                    "jour": j,
                    "date": maree["time"],
                    "dateComplete": dateComplete.replace(tzinfo=None),
                }
                clef = "horaire_%s_%s" % (j, i)
                myMarees[clef] = detailMaree
                i += 1
                if (dateComplete.date() != dateCompletePrevious.date()):
                    j += 1
                dateCompletePrevious = dateComplete
            self._donnees = myMarees

        self._donneesPrevis = dicoPrevis

    def get_port_name(self) -> str:
        if self._nomDuPort:
            return self._nomDuPort.split("©")[0].strip()
        return "Unknown"

    def getcopyright(self) -> str:
        return "©SHOM"

    def get_full_port_name(self) -> str | None:
        return self._nomDuPort

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

    def get_next_rain(self) -> tuple[datetime.datetime | None, float]:
        dateCourante = datetime.datetime.now()
        for x in self._donneesPrevis.keys():
            if self._donneesPrevis[x]["dateComplete"] > dateCourante:
                if self._donneesPrevis[x]["precipitation"] != 0:
                    return self._donneesPrevis[x]["dateComplete"], self._donneesPrevis[
                        x
                    ]["precipitation"]
        return None, 0

    def get_water_temperature(self) -> tuple[datetime.datetime | None, str]:
        dateCourante = datetime.datetime.now()
        for x in self._donneesPrevis.keys():
            if self._donneesPrevis[x]["dateComplete"] > dateCourante:
                return self._donneesPrevis[x]["dateComplete"], self._donneesPrevis[x][
                    "teau"
                ]
        return None, 0  # type: ignore[return-value]

    def get_1h_forecast(
        self,
    ) -> tuple[datetime.datetime, dict[str, str], str]:
        dateCourante = datetime.datetime.now()
        forecast: dict[str, str] = {}

        if self._donneesPrevisLive:
            def get_label_risk(risk: int) -> str:
                if risk == 0: return "Temps sec"
                if risk <= 25: return "Pluie faible"
                if risk <= 50: return "Pluie modérée"
                if risk <= 75: return "Pluie forte"
                return "Pluie très forte"

            # Use live data (5-min steps)
            # Find the starting point (closest available data around now)
            sorted_keys = sorted(self._donneesPrevisLive.keys())
            start_time: datetime.datetime | None = None
            # We look for the first data point that is not older than 2 minutes
            for k in sorted_keys:
                if k >= dateCourante - datetime.timedelta(seconds=120):
                    start_time = k
                    break

            if start_time:
                for i in range(0, 65, 5):
                    target_dt = start_time + datetime.timedelta(minutes=i)
                    if target_dt in self._donneesPrevisLive:
                        risk = self._donneesPrevisLive[target_dt].get("precip_risk", 0)
                        forecast[f"{i} min"] = get_label_risk(risk)
                    else:
                        forecast[f"{i} min"] = "Indisponible"

                return start_time, forecast, "MeteoConsult Live"

        # Fallback to hourly data if live data not available
        # On cherche la prévision pour l'heure en cours et les suivantes de manière glissante
        start_time = dateCourante.replace(second=0, microsecond=0)
        start_time -= datetime.timedelta(minutes=start_time.minute % 5)

        def get_label(mm: float) -> str:
            if mm == 0: return "Temps sec"
            if mm <= 1: return "Pluie faible"
            if mm <= 4: return "Pluie modérée"
            return "Pluie forte"

        for i in range(0, 65, 5):
            target_dt = start_time + datetime.timedelta(minutes=i)
            target_hour = target_dt.replace(minute=0, second=0, microsecond=0)

            if target_hour in self._donneesPrevis:
                mm = self._donneesPrevis[target_hour].get("precipitation", 0)
                forecast[f"{i} min"] = get_label(mm)
            else:
                forecast[f"{i} min"] = "Indisponible"

        return start_time, forecast, "MeteoConsult Forecast (Hourly Sliding)"

    def get_rain_chance(self) -> int:
        dateCourante = datetime.datetime.now()
        # On cherche la prévision la plus proche dans le futur
        for x in sorted(self._donneesPrevisLive.keys()):
            if x > dateCourante:
                return self._donneesPrevisLive[x].get("precip_risk", 0)
        return 0

    def get_cloud_cover(self) -> int:
        dateCourante = datetime.datetime.now()
        # Try live data first if available (though cloud cover might not be in live data,
        # checking based on the provided JSON it's not there, but for consistency...)
        for x in sorted(self._donneesPrevis.keys()):
            if x > dateCourante:
                return self._donneesPrevis[x].get("nuagecouverture", 0)
        return 0

    def get_uv(self) -> int:
        dateCourante = datetime.datetime.now()
        for x in sorted(self._donneesPrevis.keys()):
            if x > dateCourante:
                return self._donneesPrevis[x].get("uv", 0)
        return 0

    def get_current_live_data(self) -> LiveForecastItemRaw | None:
        if not self._donneesPrevisLive:
            return None
        now = datetime.datetime.now()
        # Find the closest forecast to "now"
        closest_dt = min(self._donneesPrevisLive.keys(), key=lambda x: abs(x - now))
        # Ensure the data is not too old (e.g., more than 15 minutes)
        if abs(closest_dt - now) > datetime.timedelta(minutes=15):
            return None
        return self._donneesPrevisLive[closest_dt]

    def get_current_water_level(self) -> tuple[float | None, str | None]:
        import math
        now = datetime.datetime.now()

        # Get all tides sorted by date
        sorted_marees = sorted(
            self._donnees.values(), key=lambda x: x["dateComplete"]
        )

        if not sorted_marees:
            return None, None

        # Find the tide before and after now
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

        # Calculate duration and time elapsed
        duration = (next_tide["dateComplete"] - previous_tide["dateComplete"]).total_seconds()
        elapsed = (now - previous_tide["dateComplete"]).total_seconds()

        # Heights
        h_prev = float(previous_tide["hauteur"])
        h_next = float(next_tide["hauteur"])

        # Sinusoidal interpolation
        # Height = h_prev + (h_next - h_prev) * (1 - cos(pi * elapsed / duration)) / 2
        level = h_prev + (h_next - h_prev) * (1 - math.cos(math.pi * elapsed / duration)) / 2

        status = "Montante" if next_tide["etat"] == "PM" else "Descendante"

        return round(level, 2), status

    def get_weather_alert(self) -> str:
        if not self._avis:
            return "Aucun"
        # On prend le premier avis pertinent (niveau > 0)
        for avis in self._avis:
            if avis.get("niveau", 0) > 0:
                return avis.get("phrase", "Alerte météo")
        return "Aucun"

    def get_pressure_forecast(
        self,
    ) -> tuple[str | None, dict[str, str]]:
        dateCourante = datetime.datetime.now()
        forecast: dict[str, str] = {}
        current_pressure: str | None = None

        # We combine live and hourly data for the best forecast
        all_data: dict[datetime.datetime, ForecastData] = {**self._donneesPrevis}
        for dt, data in self._donneesPrevisLive.items():
            if "pressure" in data or "pression" in data:
                all_data[dt] = {**all_data.get(dt, {}), "pressure": data.get("pressure") or data.get("pression")}

        sorted_keys = sorted(all_data.keys())
        for k in sorted_keys:
            val = all_data[k].get("pressure") or all_data[k].get("pression")
            if val:
                if k <= dateCourante:
                    current_pressure = val
                else:
                    forecast[k.isoformat()] = val

        if current_pressure is None and sorted_keys:
             current_pressure = all_data[sorted_keys[0]].get("pressure") or all_data[sorted_keys[0]].get("pression")

        return current_pressure, forecast

    def get_prochaine_grande_maree(
        self,
    ) -> TideData | None:
        """Return the next tide with coefficient >= 100, or None."""
        now = datetime.datetime.now()
        sorted_marees = sorted(
            self._donnees.values(), key=lambda x: x["dateComplete"]
        )
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

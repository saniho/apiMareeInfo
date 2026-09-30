"""API client classes for MeteoMarine, MeteoMarineLive, and StormGlass."""

from __future__ import annotations

import datetime
from typing import Any

from .http_utils import async_fetch_json


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
        now = datetime.datetime.now(tz=datetime.timezone.utc)
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
        now = datetime.datetime.now(tz=datetime.timezone.utc)
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

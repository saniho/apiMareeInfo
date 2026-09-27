"""API response parsers for MeteoMarine and StormGlass."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any

from .types import ForecastData, TideData


@dataclass
class ParsedData:
    """Result of parsing an API response."""

    port_name: str
    date_courante: datetime.datetime
    avis: list[dict[str, Any]]
    tides: dict[str, TideData]
    forecasts: dict[datetime.datetime, ForecastData]
    error: bool = False
    error_message: str = ""


def parse_meteo_marine(jsondata: dict[str, Any], lat: float | None, lng: float | None) -> ParsedData:
    """Parse MeteoMarine API response into ParsedData."""
    if (
        not jsondata
        or "contenu" not in jsondata
        or len(jsondata["contenu"]["marees"]) == 0
    ):
        return ParsedData(
            port_name="",
            date_courante=datetime.datetime.now(),
            avis=[],
            tides={},
            forecasts={},
            error=True,
            error_message="No tide data available from MeteoMarine",
        )

    contenu = jsondata["contenu"]

    tides = _parse_meteo_marine_tides(contenu["marees"])
    forecasts = _parse_meteo_marine_forecasts(contenu["previs"]["detail"])

    return ParsedData(
        port_name=contenu["marees"][0]["lieu"],
        date_courante=contenu["marees"][0]["datetime"],
        avis=contenu.get("avis", []),
        tides=tides,
        forecasts=forecasts,
    )


def _parse_meteo_marine_tides(marees: list[dict[str, Any]]) -> dict[str, TideData]:
    """Parse tide data from MeteoMarine response."""
    result: dict[str, TideData] = {}
    for jour_idx, maree in enumerate(marees):
        for nieme_idx, ele in enumerate(maree["etales"]):
            date_complete = datetime.datetime.fromisoformat(ele["datetime"])
            result[f"horaire_{jour_idx}_{nieme_idx}"] = TideData(
                coeff=ele.get("coef", ""),
                hauteur=ele["hauteur"],
                horaire=date_complete.strftime("%H:%M"),
                etat=ele["type_etale"],
                nieme=nieme_idx,
                jour=jour_idx,
                date=ele["datetime"],
                dateComplete=date_complete.replace(tzinfo=None),
            )
    return result


def _parse_meteo_marine_forecasts(details: list[dict[str, Any]]) -> dict[datetime.datetime, ForecastData]:
    """Parse forecast data from MeteoMarine response."""
    result: dict[datetime.datetime, ForecastData] = {}
    for ele in details:
        dt = datetime.datetime.fromisoformat(ele["datetime"])
        result[dt.replace(tzinfo=None)] = ForecastData(
            forcevnds=ele.get("forcevnds", ""),
            rafvnds=ele.get("rafvnds", ""),
            dirvdegres=ele.get("dirvdegres", ""),
            dateComplete=dt.replace(tzinfo=None),
            nebu=ele.get("nebu", ""),
            nuagecouverture=ele.get("nuagecouverture", ""),
            precipitation=ele.get("precipitation", ""),
            pressure=ele.get("pressure") or ele.get("pression", ""),
            teau=ele.get("teau", ""),
            t=ele.get("t", ""),
            risqueorage=ele.get("risqueorage", ""),
            dirhouledegres=ele.get("dirhouledegres", ""),
            hauteurhoule=ele.get("hauteurhoule", ""),
            periodehoule=ele.get("periodehoule", ""),
            hauteurmerv=ele.get("hauteurmerv", ""),
            periodemerv=ele.get("periodemerv", ""),
            hauteurvague=ele.get("hauteurvague", ""),
            uv=ele.get("uv", ""),
        )
    return result


def parse_storm_io(jsondata: dict[str, Any], previous_date: datetime.datetime | None) -> ParsedData:
    """Parse StormGlass API response into ParsedData."""
    if not jsondata or "errors" in jsondata:
        errors_dict = jsondata.get("errors", {}) if jsondata else {}
        return ParsedData(
            port_name="",
            date_courante=datetime.datetime.now(),
            avis=[],
            tides={},
            forecasts={},
            error=True,
            error_message=errors_dict.get("key", "Unknown error from StormIO"),
        )

    station_name = jsondata.get("meta", {}).get("station", {}).get("name", "")

    tides = _parse_storm_io_tides(jsondata.get("data", [])[:6], previous_date)

    return ParsedData(
        port_name=station_name,
        date_courante=datetime.datetime.now(),
        avis=[],
        tides=tides,
        forecasts={},
    )


def _parse_storm_io_tides(
    data: list[dict[str, Any]],
    previous_date: datetime.datetime | None,
) -> dict[str, TideData]:
    """Parse tide data from StormGlass response."""
    result: dict[str, TideData] = {}
    jour = 0
    date_previous = previous_date

    for nieme, item in enumerate(data):
        dt = datetime.datetime.fromisoformat(item["time"])
        result[f"horaire_{jour}_{nieme}"] = TideData(
            coeff=item.get("coef", ""),
            hauteur=item.get("height", ""),
            horaire=dt.strftime("%H:%M"),
            etat=item["type"],
            nieme=nieme,
            jour=jour,
            date=item["time"],
            dateComplete=dt.replace(tzinfo=None),
        )
        if date_previous is not None and dt.date() != date_previous.date():
            jour += 1
        date_previous = dt

    return result

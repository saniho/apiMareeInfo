"""Type definitions for apiMareeInfo."""

from datetime import datetime
from typing import TypedDict


class TideData(TypedDict):
    """Structure d'une donnée de marée."""

    coeff: str
    hauteur: str
    horaire: str
    etat: str  # "PM" (pleine mer) ou "BM" (basse mer)
    nieme: int
    jour: int
    date: str
    dateComplete: datetime


class ForecastData(TypedDict):
    """Structure d'une prévision météo (MeteoConsult hourly)."""

    forcevnds: str
    rafvnds: str
    dirvdegres: str
    dateComplete: datetime
    nebu: str
    nuagecouverture: str
    precipitation: str
    pressure: str
    teau: str
    t: str
    risqueorage: str
    dirhouledegres: str
    hauteurhoule: str
    periodehoule: str
    hauteurmerv: str
    periodemerv: str
    hauteurvague: str


class LiveForecastData(TypedDict, total=False):
    """Structure d'une prévision en temps réel (MeteoConsult Live, 5-min steps)."""

    datetime: str
    precip_risk: int
    wind_speed: str
    wind_gust: str
    wind_direction: str
    tempe: str
    tempe_felt: str
    pressure: str
    weather_icon: str
    visibility: str
    wave_height: str
    wave_height_max: str
    wave_direction: str
    swell_height: str
    sea_code: str
    nebu: str
    nuagecouverture: str
    precipitation: str
    teau: str
    t: str


class TideRawItem(TypedDict):
    """Élément brut d'une marée dans la réponse API MeteoMarine."""

    coef: str
    hauteur: str
    datetime: str
    type_etale: str


class TideEtoleRaw(TypedDict):
    """Marée brute depuis la réponse MeteoMarine (champ 'etales')."""

    coef: str
    hauteur: str
    datetime: str
    type_etale: str


class MareeRaw(TypedDict):
    """Structure brute d'une marée dans la réponse API MeteoMarine."""

    lieu: str
    datetime: str
    etales: list[TideEtoleRaw]


class PrevisDetailRaw(TypedDict):
    """Élément brut d'une prévision dans la réponse API MeteoMarine."""

    forcevnds: str
    rafvnds: str
    dirvdegres: str
    datetime: str
    nebu: str
    nuagecouverture: str
    precipitation: str
    pressure: str
    pression: str
    teau: str
    t: str
    risqueorage: str
    dirhouledegres: str
    hauteurhoule: str
    periodehoule: str
    hauteurmerv: str
    periodemerv: str
    hauteurvague: str


class ContenuMarees(TypedDict):
    """Champ 'contenu' de la réponse API MeteoMarine."""

    marees: list[MareeRaw]
    previs: "PrevisMarees"
    avis: list[dict[str, object]]


class PrevisMarees(TypedDict):
    """Champ 'previs' de la réponse API MeteoMarine."""

    detail: list[PrevisDetailRaw]


class MeteoMarineResponse(TypedDict):
    """Réponse brute de l'API MeteoMarine."""

    contenu: ContenuMarees


class StormGlassDataItem(TypedDict):
    """Élément brut d'une marée dans la réponse StormGlass."""

    time: str
    height: float
    type: str
    coef: str


class StormGlassMeta(TypedDict, total=False):
    """Métadonnées de la réponse StormGlass."""

    station: dict[str, str]


class StormGlassResponse(TypedDict, total=False):
    """Réponse brute de l'API StormGlass."""

    data: list[StormGlassDataItem]
    meta: StormGlassMeta
    errors: dict[str, str]


class LiveForecastItemRaw(TypedDict):
    """Élément brut d'une prévision live dans la réponse MeteoMarineLive."""

    datetime: str
    precip_risk: int
    wind_speed: str
    wind_gust: str
    wind_direction: str
    tempe: str
    tempe_felt: str
    pressure: str
    weather_icon: str
    visibility: str
    wave_height: str
    wave_height_max: str
    wave_direction: str
    swell_height: str
    sea_code: str


class LiveForecastContent(TypedDict):
    """Champ 'content' de la réponse MeteoMarineLive."""

    forecasts: list[LiveForecastItemRaw]


class MeteoMarineLiveResponse(TypedDict):
    """Réponse brute de l'API MeteoMarineLive."""

    content: LiveForecastContent


class PortSearchItem(TypedDict):
    """Élément brut d'un port dans la réponse de recherche."""

    nom: str
    pays: str
    departement: str
    lat: str
    lon: str
    id: str


class PortSearchResponse(TypedDict):
    """Réponse brute de la recherche de ports."""

    contenu: list[PortSearchItem]

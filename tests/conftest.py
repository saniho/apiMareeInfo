"""Shared test fixtures for apiMareeInfo tests."""

import datetime
import json
import pathlib

import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "json"


@pytest.fixture
def sjm_meteomarine_data():
    """Load Saint-Malo MeteoMarine fixture data."""
    with open(FIXTURES_DIR / "meteomarine" / "SJM.json") as f:
        return json.load(f)


@pytest.fixture
def sjm_stormglass_data():
    """Load Saint-Malo StormGlass fixture data."""
    with open(FIXTURES_DIR / "stormglass.io" / "sjm_20221214.json") as f:
        return json.load(f)


@pytest.fixture
def empty_meteomarine_data():
    """Return empty/invalid MeteoMarine data for error testing."""
    return {"contenu": {"marees": [], "previs": {"detail": []}, "avis": []}}


@pytest.fixture
def error_meteomarine_data():
    """Return error response from MeteoMarine."""
    return {"error": "UNKERROR_001"}


@pytest.fixture
def error_stormglass_data():
    """Return error response from StormGlass."""
    return {"errors": {"key": "Invalid API key"}}


@pytest.fixture
def live_forecast_data():
    """Return mock live forecast data for MeteoMarineLive."""
    now = datetime.datetime.now()
    forecasts = []
    for i in range(0, 65, 5):
        dt = now + datetime.timedelta(minutes=i)
        forecasts.append({
            "datetime": dt.isoformat(),
            "precip_risk": (i * 2) % 100,
            "wind_speed": 10 + i,
            "wind_gust": 15 + i,
            "wind_direction": 180,
            "tempe": 18.5,
            "wave_height": 1.2,
        })
    return {"content": {"forecasts": forecasts}}


@pytest.fixture
def sample_marees():
    """Return sample tide data for unit testing."""
    now = datetime.datetime.now()
    return {
        "horaire_0_0": {
            "coeff": 85,
            "hauteur": 5.5,
            "horaire": "06:30",
            "etat": "PM",
            "nieme": 0,
            "jour": 0,
            "date": "2024-01-15T06:30:00",
            "dateComplete": now - datetime.timedelta(hours=2),
        },
        "horaire_0_1": {
            "coeff": 30,
            "hauteur": 1.2,
            "horaire": "12:45",
            "etat": "BM",
            "nieme": 1,
            "jour": 0,
            "date": "2024-01-15T12:45:00",
            "dateComplete": now + datetime.timedelta(hours=4),
        },
        "horaire_1_0": {
            "coeff": 90,
            "hauteur": 5.8,
            "horaire": "18:55",
            "etat": "PM",
            "nieme": 0,
            "jour": 1,
            "date": "2024-01-15T18:55:00",
            "dateComplete": now + datetime.timedelta(hours=10),
        },
    }


@pytest.fixture
def sample_previs():
    """Return sample forecast data for unit testing."""
    now = datetime.datetime.now()
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    return {
        current_hour: {
            "forcevnds": "15",
            "rafvnds": "25",
            "dirvdegres": "180",
            "dateComplete": current_hour,
            "nebu": "c0030",
            "nuagecouverture": 60,
            "precipitation": 0,
            "pressure": "1013",
            "teau": "16.5",
            "t": "18.2",
            "risqueorage": 0,
            "dirhouledegres": "270",
            "hauteurhoule": "1.5",
            "periodehoule": "8",
            "hauteurmerv": "2.0",
            "periodemerv": "10",
            "hauteurvague": "1.8",
        },
        current_hour + datetime.timedelta(hours=1): {
            "forcevnds": "20",
            "rafvnds": "30",
            "dirvdegres": "190",
            "dateComplete": current_hour + datetime.timedelta(hours=1),
            "nebu": "p0010",
            "nuagecouverture": 80,
            "precipitation": 2,
            "pressure": "1012",
            "teau": "16.4",
            "t": "17.8",
            "risqueorage": 10,
            "dirhouledegres": "275",
            "hauteurhoule": "1.6",
            "periodehoule": "9",
            "hauteurmerv": "2.1",
            "periodemerv": "11",
            "hauteurvague": "1.9",
        },
    }

"""Tests for ApiMareeInfo status methods (formerly in sensorApiMaree)."""

import datetime

from custom_components.apiMareeInfo.apiMareeInfo import ApiMareeInfo


# ============================================================
# Helpers
# ============================================================
def _make_maree(horaire, etat, jour, nieme, coeff=85, hauteur=5.5, hours_offset=0):
    """Create a tide entry dict."""
    now = datetime.datetime.now(tz=datetime.timezone.utc).replace(tzinfo=None)
    return {
        "horaire": horaire,
        "etat": etat,
        "jour": jour,
        "nieme": nieme,
        "coeff": coeff,
        "hauteur": hauteur,
        "dateComplete": now + datetime.timedelta(hours=hours_offset),
    }


def _make_previs(hours_offset=0, **overrides):
    """Create a forecast entry dict."""
    now = datetime.datetime.now(tz=datetime.timezone.utc).replace(minute=0, second=0, microsecond=0, tzinfo=None) + datetime.timedelta(hours=hours_offset)
    base = {
        "forcevnds": "15",
        "rafvnds": "25",
        "dirvdegres": "180",
        "dateComplete": now,
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
        "uv": 0,
    }
    base.update(overrides)
    return now, base


def _make_api(
    error=False,
    error_msg="",
    tide_data=None,
    previs=None,
    avis=None,
    live_data=None,
    version="1.0.0",
):
    """Create an ApiMareeInfo instance with pre-configured internal state."""
    api = ApiMareeInfo(version=version)
    api._error = error
    api._errorMessage = error_msg
    api._nomDuPort = "Saint-Malo"
    api._id = "12345"
    api._donnees = tide_data or {}
    api._donneesPrevis = previs or {}
    api._donneesPrevisLive = live_data or {}
    api._avis = avis or []
    api._httptimerequest = datetime.datetime.now(tz=datetime.timezone.utc).replace(tzinfo=None)
    return api


# ============================================================
# _base_attrs tests
# ============================================================
class TestBaseAttrs:
    """Tests for _base_attrs helper."""

    def test_returns_common_fields(self):
        api = _make_api(version="2.0.0")
        sc = api._base_attrs()
        assert sc["version"] == "2.0.0"
        assert sc["attribution"] == "Data provided by apiMareeInfo"
        assert isinstance(sc["last_update"], datetime.datetime)
        assert "last_http_update" not in sc

    def test_with_http_update(self):
        api = _make_api()
        sc = api._base_attrs(with_http_update=True)
        assert "last_http_update" in sc

    def test_without_http_update_by_default(self):
        api = _make_api()
        sc = api._base_attrs()
        assert "last_http_update" not in sc


# ============================================================
# getnextmaree tests
# ============================================================
class TestGetnextmaree:
    """Tests for getnextmaree method."""

    def test_returns_first_future_maree(self):
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, hours_offset=-2),
            "0_1": _make_maree("12:45", "BM", 0, 1, hours_offset=4),
        }
        api = _make_api(tide_data=marees)
        result = api.getnextmaree(indice=1)
        assert result is not None
        assert result["horaire"] == "12:45"

    def test_returns_second_future_maree(self):
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, hours_offset=-2),
            "0_1": _make_maree("12:45", "BM", 0, 1, hours_offset=4),
            "1_0": _make_maree("18:55", "PM", 1, 0, hours_offset=10),
        }
        api = _make_api(tide_data=marees)
        result = api.getnextmaree(indice=2)
        assert result is not None
        assert result["horaire"] == "18:55"

    def test_returns_none_when_no_future_maree(self):
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, hours_offset=-10),
        }
        api = _make_api(tide_data=marees)
        result = api.getnextmaree(indice=1)
        assert result is None

    def test_with_custom_maintenant(self):
        base = datetime.datetime(2024, 1, 15, 10, 0)
        marees = {
            "0_0": {"dateComplete": datetime.datetime(2024, 1, 15, 6, 30), "horaire": "06:30", "etat": "PM", "jour": 0, "nieme": 0, "coeff": "85", "hauteur": "5.5"},
            "0_1": {"dateComplete": datetime.datetime(2024, 1, 15, 12, 45), "horaire": "12:45", "etat": "BM", "jour": 0, "nieme": 1, "coeff": "30", "hauteur": "1.2"},
        }
        api = _make_api(tide_data=marees)
        result = api.getnextmaree(indice=1, maintenant=base)
        assert result["horaire"] == "12:45"


# ============================================================
# getstatus tests
# ============================================================
class TestGetstatus:
    """Tests for getstatus method."""

    def test_returns_unavailable_on_error(self):
        api = _make_api(error=True, error_msg="Connection failed", version="1.0.0")
        state, attrs = api.getstatus()
        assert state == "unavailable"
        assert attrs["message"] == "Connection failed"
        assert attrs["version"] == "1.0.0"

    def test_returns_tide_time_when_valid(self):
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, hours_offset=-2),
            "0_1": _make_maree("12:45", "BM", 0, 1, hours_offset=4),
        }
        api = _make_api(tide_data=marees, version="2.0.0")
        state, attrs = api.getstatus()
        assert state == "12:45"
        assert attrs["nomPort"] == "Saint-Malo"
        assert attrs["idPort"] == "12345"
        assert attrs["version"] == "2.0.0"

    def test_status_includes_tide_data(self):
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, coeff=85, hauteur=5.5, hours_offset=-2),
            "0_1": _make_maree("12:45", "BM", 0, 1, coeff=30, hauteur=1.2, hours_offset=4),
        }
        api = _make_api(tide_data=marees)
        state, attrs = api.getstatus()
        assert "horaire_0_0" in attrs
        assert attrs["horaire_0_0"] == "06:30"
        assert attrs["coeff_0_0"] == 85
        assert attrs["etat_0_0"] == "PM"
        assert attrs["hauteur_0_0"] == 5.5
        assert attrs["nb_maree_0"] == 2

    def test_status_includes_next_maree(self):
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, hours_offset=-2),
            "0_1": _make_maree("12:45", "BM", 0, 1, hours_offset=4),
            "1_0": _make_maree("18:55", "PM", 1, 0, hours_offset=10),
        }
        api = _make_api(tide_data=marees)
        state, attrs = api.getstatus()
        assert "next_maree_1" in attrs
        assert attrs["next_maree_1"] == "12:45"
        assert "next_coeff_1" in attrs
        assert "next_etat_1" in attrs


# ============================================================
# get_next_tide_state tests
# ============================================================
class TestGetNextTideState:
    """Tests for get_next_tide_state method."""

    def test_returns_next_high_tide(self):
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, coeff=85, hours_offset=-2),
            "0_1": _make_maree("12:45", "BM", 0, 1, hours_offset=4),
            "1_0": _make_maree("18:55", "PM", 1, 0, coeff=90, hours_offset=10),
        }
        api = _make_api(tide_data=marees)
        state, attrs = api.get_next_tide_state(pmbm="PM")
        assert state == "18:55"
        assert attrs["coeff"] == 90

    def test_returns_unavailable_when_no_matching_tide(self):
        marees = {
            "0_0": _make_maree("12:45", "BM", 0, 1, hours_offset=4),
        }
        api = _make_api(tide_data=marees)
        state, attrs = api.get_next_tide_state(pmbm="PM")
        assert state == "unavailable"

    def test_skips_first_if_wrong_type(self):
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, hours_offset=-2),
            "0_1": _make_maree("12:45", "BM", 0, 1, hours_offset=4),
            "1_0": _make_maree("18:55", "PM", 1, 0, hours_offset=10),
        }
        api = _make_api(tide_data=marees)
        state, attrs = api.get_next_tide_state(pmbm="PM")
        assert state == "18:55"


# ============================================================
# get_next_rain_status tests
# ============================================================
class TestGetNextRainStatus:
    """Tests for get_next_rain_status method."""

    def test_returns_unavailable_when_no_rain(self):
        api = _make_api()
        api.get_next_rain = lambda: (None, 0)
        api.get_1h_forecast = lambda: (datetime.datetime.now(tz=datetime.timezone.utc).replace(tzinfo=None), {}, "")
        state, attrs = api.get_next_rain_status()
        assert state == "unavailable"
        assert attrs["precipitation"] == 0

    def test_returns_date_when_rain_forecast(self):
        rain_date = datetime.datetime.now(tz=datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=3)
        api = _make_api()
        api.get_next_rain = lambda: (rain_date, 2.5)
        api.get_1h_forecast = lambda: (datetime.datetime.now(tz=datetime.timezone.utc).replace(tzinfo=None), {}, "")
        state, attrs = api.get_next_rain_status()
        assert state == rain_date
        assert attrs["precipitation"] == 2.5
        assert "1_hour_forecast" in attrs


# ============================================================
# get_water_temp_status tests
# ============================================================
class TestGetWaterTempStatus:
    """Tests for get_water_temp_status method."""

    def test_returns_unavailable_when_no_data(self):
        api = _make_api()
        api.get_water_temperature = lambda: (None, "")
        state, attrs = api.get_water_temp_status()
        assert state == "unavailable"

    def test_returns_temp_when_data(self):
        temp_date = datetime.datetime.now(tz=datetime.timezone.utc).replace(tzinfo=None)
        api = _make_api()
        api.get_water_temperature = lambda: (temp_date, "16.5")
        state, attrs = api.get_water_temp_status()
        assert state == "16.5"
        assert attrs["teau"] == "16.5"


# ============================================================
# get_weather_status tests
# ============================================================
class TestGetWeatherStatus:
    """Tests for get_weather_status method."""

    def test_returns_forecast_state(self):
        forecast_ref = datetime.datetime.now(tz=datetime.timezone.utc).replace(tzinfo=None)
        forecast = {"0 min": "Pluie légère", "30 min": "Sec"}
        api = _make_api()
        api.get_1h_forecast = lambda: (forecast_ref, forecast, "MeteoConsult Live")
        state, attrs = api.get_weather_status()
        assert state == "Pluie légère"
        assert attrs["data_source"] == "MeteoConsult Live"
        assert "forecast_time_ref" in attrs


# ============================================================
# get_rain_chance_status tests
# ============================================================
class TestGetRainChanceStatus:
    """Tests for get_rain_chance_status method."""

    def test_returns_zero_when_no_rain(self):
        api = _make_api()
        api.get_rain_chance = lambda: 0
        state, attrs = api.get_rain_chance_status()
        assert state == 0
        assert attrs["version"] == "1.0.0"

    def test_returns_percentage_with_live_data(self):
        api = _make_api(live_data={"rain_chance": 75})
        api.get_rain_chance = lambda: 75
        state, attrs = api.get_rain_chance_status()
        assert state == 75
        assert attrs["data_source"] == "MeteoConsult Live"

    def test_returns_percentage_without_live_data(self):
        api = _make_api()
        api.get_rain_chance = lambda: 30
        state, attrs = api.get_rain_chance_status()
        assert state == 30
        assert attrs["data_source"] == "MeteoConsult Forecast (Hourly)"


# ============================================================
# get_cloud_cover_status tests
# ============================================================
class TestGetCloudCoverStatus:
    """Tests for get_cloud_cover_status method."""

    def test_returns_cloud_cover(self):
        api = _make_api()
        api.get_cloud_cover = lambda: 60
        state, attrs = api.get_cloud_cover_status()
        assert state == 60
        assert attrs["data_source"] == "MeteoConsult Forecast (Hourly)"


# ============================================================
# get_weather_alert_status tests
# ============================================================
class TestGetWeatherAlertStatus:
    """Tests for get_weather_alert_status method."""

    def test_returns_no_alert(self):
        api = _make_api()
        state, attrs = api.get_weather_alert_status()
        assert state == "Aucun"
        assert attrs["data_source"] == "MeteoConsult"

    def test_returns_alert_phrase(self):
        api = _make_api(avis=[{"niveau": 2, "phrase": "Vent violent"}])
        state, attrs = api.get_weather_alert_status()
        assert state == "Vent violent"


# ============================================================
# get_pressure_status tests
# ============================================================
class TestGetPressureStatus:
    """Tests for get_pressure_status method."""

    def test_returns_pressure_with_live(self):
        api = _make_api(live_data={"pressure": "1013"})
        api.get_pressure_forecast = lambda: ("1013", {"trend": "stable"})
        state, attrs = api.get_pressure_status()
        assert state == "1013"
        assert attrs["data_source"] == "MeteoConsult Live"

    def test_returns_pressure_without_live(self):
        api = _make_api()
        api.get_pressure_forecast = lambda: ("1012", {})
        state, attrs = api.get_pressure_status()
        assert state == "1012"
        assert attrs["data_source"] == "MeteoConsult Forecast (Hourly)"


# ============================================================
# get_wave_status tests
# ============================================================
class TestGetWaveStatus:
    """Tests for get_wave_status method."""

    def test_returns_unavailable_when_no_data(self):
        api = _make_api()
        state, attrs = api.get_wave_status()
        assert state is None

    def test_returns_live_wave_data(self):
        live_data = {datetime.datetime.now(tz=datetime.timezone.utc).replace(tzinfo=None): {"wave_height": 1.5, "wave_height_max": 2.0, "wave_direction": 270, "swell_height": 1.2, "sea_code": "moderate"}}
        api = _make_api(live_data=live_data)
        state, attrs = api.get_wave_status()
        assert state == "1.5"
        assert attrs["wave_height_max"] == "2.0"
        assert attrs["data_source"] == "MeteoConsult Live"

    def test_fallback_to_forecast(self):
        now, previs_data = _make_previs(hours_offset=1, hauteurvague="2.2", hauteurmerv="2.5", dirhouledegres="280", hauteurhoule="1.8")
        api = _make_api(previs={now: previs_data})
        state, attrs = api.get_wave_status()
        assert state == "2.2"
        assert attrs["data_source"] == "MeteoConsult Forecast (Hourly)"


# ============================================================
# get_wind_status tests
# ============================================================
class TestGetWindStatus:
    """Tests for get_wind_status method."""

    def test_returns_live_wind_data(self):
        live_data = {datetime.datetime.now(tz=datetime.timezone.utc).replace(tzinfo=None): {"wind_speed": 20, "wind_gust": 30, "wind_direction": 180}}
        api = _make_api(live_data=live_data)
        state, attrs = api.get_wind_status()
        assert state == "20"
        assert attrs["wind_gust"] == "30"
        assert attrs["data_source"] == "MeteoConsult Live"

    def test_fallback_to_forecast(self):
        now, previs_data = _make_previs(hours_offset=1, forcevnds="25", rafvnds="35", dirvdegres="190")
        api = _make_api(previs={now: previs_data})
        state, attrs = api.get_wind_status()
        assert state == "25"
        assert attrs["data_source"] == "MeteoConsult Forecast (Hourly)"

    def test_unavailable_when_no_data(self):
        api = _make_api()
        state, attrs = api.get_wind_status()
        assert state is None


# ============================================================
# get_air_temp_status tests
# ============================================================
class TestGetAirTempStatus:
    """Tests for get_air_temp_status method."""

    def test_returns_live_temp(self):
        live_data = {datetime.datetime.now(tz=datetime.timezone.utc).replace(tzinfo=None): {"tempe": 18.5, "tempe_felt": 17.0}}
        api = _make_api(live_data=live_data)
        state, attrs = api.get_air_temp_status()
        assert state == "18.5"
        assert attrs["tempe_felt"] == 17.0
        assert attrs["data_source"] == "MeteoConsult Live"

    def test_fallback_to_forecast(self):
        now, previs_data = _make_previs(hours_offset=1, t="19.0")
        api = _make_api(previs={now: previs_data})
        state, attrs = api.get_air_temp_status()
        assert state == "19.0"


# ============================================================
# get_visibility_status tests
# ============================================================
class TestGetVisibilityStatus:
    """Tests for get_visibility_status method."""

    def test_returns_live_visibility(self):
        live_data = {datetime.datetime.now(tz=datetime.timezone.utc).replace(tzinfo=None): {"visibility": 10000}}
        api = _make_api(live_data=live_data)
        state, attrs = api.get_visibility_status()
        assert state == 10000
        assert attrs["data_source"] == "MeteoConsult Live"

    def test_unavailable_without_live(self):
        api = _make_api()
        state, attrs = api.get_visibility_status()
        assert state is None


# ============================================================
# get_water_level_status tests
# ============================================================
class TestGetWaterLevelStatus:
    """Tests for get_water_level_status method."""

    def test_returns_unavailable_when_no_data(self):
        api = _make_api()
        state, attrs = api.get_water_level_status()
        assert state == "unavailable"

    def test_returns_level_and_status(self):
        api = _make_api()
        api.get_current_water_level = lambda: (3.5, "Montante")
        state, attrs = api.get_water_level_status()
        assert state == 3.5
        assert attrs["tide_status"] == "Montante"
        assert attrs["data_source"] == "Calculated (Sinusoidal Interpolation)"


# ============================================================
# get_uv_status tests
# ============================================================
class TestGetUVStatus:
    """Tests for get_uv_status method."""

    def test_returns_uv_value(self):
        api = _make_api()
        api.get_uv = lambda: 5
        state, attrs = api.get_uv_status()
        assert state == 5
        assert attrs["data_source"] == "MeteoConsult Forecast (Hourly)"

    def test_returns_zero_when_no_data(self):
        api = _make_api()
        api.get_uv = lambda: 0
        state, attrs = api.get_uv_status()
        assert state == 0

    def test_returns_high_uv(self):
        api = _make_api()
        api.get_uv = lambda: 11
        state, attrs = api.get_uv_status()
        assert state == 11

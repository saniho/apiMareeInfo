"""Comprehensive tests for sensorApiMaree module."""

import datetime
import logging
from unittest.mock import MagicMock

from custom_components.apiMareeInfo.sensorApiMaree import SensorStateManager


# ============================================================
# Helpers
# ============================================================
def _make_maree(horaire, etat, jour, nieme, coeff=85, hauteur=5.5, hours_offset=0):
    """Create a mock tide entry."""
    now = datetime.datetime.now()
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
    """Create a mock forecast entry."""
    now = datetime.datetime.now().replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=hours_offset)
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


def _make_port(error=False, error_msg="", info=None, previs=None, avis=None, live_data=None):
    """Create a mock ApiMareeInfo port object."""
    port = MagicMock()
    port.has_error.return_value = error
    port.get_error_message.return_value = error_msg
    port.get_port_name.return_value = "Saint-Malo"
    port.getid.return_value = "12345"
    port.getcopyright.return_value = "©SHOM"
    port.get_current_date.return_value = datetime.datetime.now()
    port.get_http_request_time.return_value = datetime.datetime.now()
    port.get_max_hours.return_value = 6
    port.get_tide_data.return_value = info or {}
    port.get_forecast_data.return_value = previs or {}
    port.get_next_rain.return_value = (None, 0)
    port.get_water_temperature.return_value = (None, 0)
    port.get_rain_chance.return_value = 0
    port.get_cloud_cover.return_value = 0
    port.get_weather_alert.return_value = "Aucun"
    port.get_pressure_forecast.return_value = (None, {})
    port.get_current_water_level.return_value = (None, None)
    port.get_current_live_data.return_value = live_data
    port.get_1h_forecast.return_value = (datetime.datetime.now(), {}, "")
    port._donneesPrevisLive = live_data
    return port


# ============================================================
# _init_status tests
# ============================================================
class TestInitStatus:
    """Tests for _init_status helper method."""

    def test_returns_common_fields(self):
        """Test that version, attribution, and last_update are present."""
        port = _make_port()
        mss = SensorStateManager()
        mss.init(port, version="2.0.0")

        sc = mss._init_status()
        assert sc["version"] == "2.0.0"
        assert sc["attribution"] == "Data provided by apiMareeInfo"
        assert isinstance(sc["last_update"], datetime.datetime)
        assert "last_http_update" not in sc

    def test_with_http_update(self):
        """Test that last_http_update is included when requested."""
        port = _make_port()
        mss = SensorStateManager()
        mss.init(port, version="1.0.0")

        sc = mss._init_status(with_http_update=True)
        assert "last_http_update" in sc
        assert isinstance(sc["last_http_update"], datetime.datetime)

    def test_without_http_update_by_default(self):
        """Test that last_http_update is absent by default."""
        port = _make_port()
        mss = SensorStateManager()
        mss.init(port)

        sc = mss._init_status()
        assert "last_http_update" not in sc


# ============================================================
# _get_data_source tests
# ============================================================
class TestGetDataSource:
    """Tests for _get_data_source helper method."""

    def test_returns_live_when_live_data(self):
        """Test live source when _donneesPrevisLive is truthy."""
        port = _make_port(live_data={"key": "val"})
        mss = SensorStateManager()
        mss.init(port)

        assert mss._get_data_source() == "MeteoConsult Live"

    def test_returns_forecast_when_no_live_data(self):
        """Test forecast source when _donneesPrevisLive is falsy."""
        port = _make_port()
        port._donneesPrevisLive = None
        mss = SensorStateManager()
        mss.init(port)

        assert mss._get_data_source() == "MeteoConsult Forecast (Hourly)"


# ============================================================
# _get_live_or_forecast tests
# ============================================================
class TestGetLiveOrForecast:
    """Tests for _get_live_or_forecast helper method."""

    def test_returns_live_data_first(self):
        """Test that live data is returned when available."""
        live_data = {"wind_speed": 15, "tempe": 20}
        port = _make_port(live_data=live_data)
        mss = SensorStateManager()
        mss.init(port)

        data, source = mss._get_live_or_forecast()
        assert data == live_data
        assert source == "MeteoConsult Live"

    def test_falls_back_to_forecast(self):
        """Test fallback to next hourly forecast when no live data."""
        now, previs_data = _make_previs(hours_offset=1)
        port = _make_port(previs={now: previs_data})
        port.get_current_live_data.return_value = None
        mss = SensorStateManager()
        mss.init(port)

        data, source = mss._get_live_or_forecast()
        assert data == previs_data
        assert source == "MeteoConsult Forecast (Hourly)"

    def test_returns_none_when_no_data(self):
        """Test None return when neither live nor forecast available."""
        port = _make_port()
        port.get_current_live_data.return_value = None
        port.get_forecast_data.return_value = {}
        mss = SensorStateManager()
        mss.init(port)

        data, source = mss._get_live_or_forecast()
        assert data is None
        assert source is None

    def test_skips_past_forecast_entries(self):
        """Test that past forecast entries are skipped."""
        past, past_data = _make_previs(hours_offset=-2)
        future, future_data = _make_previs(hours_offset=2)
        port = _make_port(previs={past: past_data, future: future_data})
        port.get_current_live_data.return_value = None
        mss = SensorStateManager()
        mss.init(port)

        data, source = mss._get_live_or_forecast()
        assert data == future_data
        assert source == "MeteoConsult Forecast (Hourly)"


# ============================================================
# init tests
# ============================================================
class TestManageSensorStateInit:
    """Tests for SensorStateManager initialization."""

    def test_init_defaults(self):
        """Test default init values."""
        mss = SensorStateManager()
        assert mss._myPort is None
        assert mss.version is None

    def test_init_with_params(self):
        """Test init with parameters."""
        port = _make_port()
        mss = SensorStateManager()
        mss.init(port, version="1.0.0")
        assert mss._myPort == port
        assert mss.version == "1.0.0"

    def test_init_creates_logger(self):
        """Test that init creates a logger when none passed."""
        mss = SensorStateManager()
        mss.init(_make_port())
        assert mss._LOGGER is not None

    def test_init_uses_provided_logger(self):
        """Test that init uses provided logger."""
        custom_logger = logging.getLogger("test_logger")
        mss = SensorStateManager()
        mss.init(_make_port(), _LOGGER=custom_logger)
        assert mss._LOGGER is custom_logger


# ============================================================
# getnextmaree tests
# ============================================================
class TestGetnextmaree:
    """Tests for getnextmaree method."""

    def test_returns_first_future_maree(self):
        """Test that first future tide is returned."""
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, hours_offset=-2),
            "0_1": _make_maree("12:45", "BM", 0, 1, hours_offset=4),
        }
        port = _make_port(info=marees)
        mss = SensorStateManager()
        mss.init(port)

        result = mss.getnextmaree(indice=1)
        assert result is not None
        assert result["horaire"] == "12:45"

    def test_returns_second_future_maree(self):
        """Test that second future tide is returned."""
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, hours_offset=-2),
            "0_1": _make_maree("12:45", "BM", 0, 1, hours_offset=4),
            "1_0": _make_maree("18:55", "PM", 1, 0, hours_offset=10),
        }
        port = _make_port(info=marees)
        mss = SensorStateManager()
        mss.init(port)

        result = mss.getnextmaree(indice=2)
        assert result is not None
        assert result["horaire"] == "18:55"

    def test_returns_none_when_no_future_maree(self):
        """Test None when no future tide exists."""
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, hours_offset=-10),
        }
        port = _make_port(info=marees)
        mss = SensorStateManager()
        mss.init(port)

        result = mss.getnextmaree(indice=1)
        assert result is None

    def test_with_custom_maintenant(self):
        """Test with custom reference time."""
        base = datetime.datetime(2024, 1, 15, 10, 0)
        marees = {
            "0_0": {"dateComplete": datetime.datetime(2024, 1, 15, 6, 30), "horaire": "06:30", "etat": "PM", "jour": 0, "nieme": 0, "coeff": 85, "hauteur": 5.5},
            "0_1": {"dateComplete": datetime.datetime(2024, 1, 15, 12, 45), "horaire": "12:45", "etat": "BM", "jour": 0, "nieme": 1, "coeff": 30, "hauteur": 1.2},
        }
        port = _make_port(info=marees)
        mss = SensorStateManager()
        mss.init(port)

        result = mss.getnextmaree(indice=1, maintenant=base)
        assert result["horaire"] == "12:45"


# ============================================================
# getstatus tests
# ============================================================
class TestGetstatus:
    """Tests for getstatus method."""

    def test_returns_unavailable_on_error(self):
        """Test unavailable state when port has error."""
        port = _make_port(error=True, error_msg="Connection failed")
        mss = SensorStateManager()
        mss.init(port, version="1.0.0")

        state, attrs = mss.getstatus()
        assert state == "unavailable"
        assert attrs["message"] == "Connection failed"
        assert attrs["version"] == "1.0.0"

    def test_returns_tide_time_when_valid(self):
        """Test that tide time is returned when valid data exists."""
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, hours_offset=-2),
            "0_1": _make_maree("12:45", "BM", 0, 1, hours_offset=4),
        }
        previs = {}
        port = _make_port(info=marees, previs=previs)
        mss = SensorStateManager()
        mss.init(port, version="2.0.0")

        state, attrs = mss.getstatus()
        assert state == "12:45"
        assert attrs["nomPort"] == "Saint-Malo"
        assert attrs["idPort"] == "12345"
        assert attrs["Copyright"] == "©SHOM"
        assert attrs["version"] == "2.0.0"

    def test_status_includes_tide_data(self):
        """Test that status includes tide attributes."""
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, coeff=85, hauteur=5.5, hours_offset=-2),
            "0_1": _make_maree("12:45", "BM", 0, 1, coeff=30, hauteur=1.2, hours_offset=4),
        }
        port = _make_port(info=marees)
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.getstatus()
        assert "horaire_0_0" in attrs
        assert attrs["horaire_0_0"] == "06:30"
        assert attrs["coeff_0_0"] == 85
        assert attrs["etat_0_0"] == "PM"
        assert attrs["hauteur_0_0"] == 5.5
        assert attrs["nb_maree_0"] == 2

    def test_status_includes_next_maree(self):
        """Test that status includes next tide info."""
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, hours_offset=-2),
            "0_1": _make_maree("12:45", "BM", 0, 1, hours_offset=4),
            "1_0": _make_maree("18:55", "PM", 1, 0, hours_offset=10),
        }
        port = _make_port(info=marees)
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.getstatus()
        assert "next_maree_1" in attrs
        assert attrs["next_maree_1"] == "12:45"
        assert "next_coeff_1" in attrs
        assert "next_etat_1" in attrs

    def test_status_includes_previs(self):
        """Test that forecast data is included."""
        now, previs_data = _make_previs(hours_offset=1)
        marees = {"0_0": _make_maree("06:30", "PM", 0, 0, hours_offset=-2)}
        port = _make_port(info=marees, previs={now: previs_data})
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.getstatus()
        assert "prevision" in attrs


# ============================================================
# get_next_tide_state tests (was getStateNextMaree)
# ============================================================
class TestGetNextTideState:
    """Tests for get_next_tide_state method."""

    def test_returns_next_high_tide(self):
        """Test that next high tide is returned."""
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, coeff=85, hours_offset=-2),
            "0_1": _make_maree("12:45", "BM", 0, 1, hours_offset=4),
            "1_0": _make_maree("18:55", "PM", 1, 0, coeff=90, hours_offset=10),
        }
        port = _make_port(info=marees)
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_next_tide_state(pmbm="PM")
        assert state == "18:55"
        assert attrs["coeff"] == 90

    def test_returns_unavailable_when_no_matching_tide(self):
        """Test unavailable when no matching tide type."""
        marees = {
            "0_0": _make_maree("12:45", "BM", 0, 1, hours_offset=4),
        }
        port = _make_port(info=marees)
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_next_tide_state(pmbm="PM")
        assert state == "unavailable"

    def test_skips_first_if_wrong_type(self):
        """Test that first tide is skipped if wrong type."""
        marees = {
            "0_0": _make_maree("06:30", "PM", 0, 0, hours_offset=-2),
            "0_1": _make_maree("12:45", "BM", 0, 1, hours_offset=4),
            "1_0": _make_maree("18:55", "PM", 1, 0, hours_offset=10),
        }
        port = _make_port(info=marees)
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_next_tide_state(pmbm="PM")
        # First next is BM, so it skips to second which is PM
        assert state == "18:55"


# ============================================================
# get_next_rain_status tests (was getstatusProchainePluie)
# ============================================================
class TestGetNextRainStatus:
    """Tests for get_next_rain_status method."""

    def test_returns_unavailable_when_no_rain(self):
        """Test unavailable when no rain forecast."""
        port = _make_port()
        port.get_next_rain.return_value = (None, 0)
        mss = SensorStateManager()
        mss.init(port, version="1.0.0")

        state, attrs = mss.get_next_rain_status()
        assert state == "unavailable"
        assert attrs["precipitation"] == 0

    def test_returns_date_when_rain_forecast(self):
        """Test that rain date is returned."""
        rain_date = datetime.datetime.now() + datetime.timedelta(hours=3)
        port = _make_port()
        port.get_next_rain.return_value = (rain_date, 2.5)
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_next_rain_status()
        assert state == rain_date
        assert attrs["precipitation"] == 2.5
        assert "1_hour_forecast" in attrs


# ============================================================
# get_water_temp_status tests (was getstatusTemperatureEau)
# ============================================================
class TestGetWaterTempStatus:
    """Tests for get_water_temp_status method."""

    def test_returns_unavailable_when_no_data(self):
        """Test unavailable when no water temp."""
        port = _make_port()
        port.get_water_temperature.return_value = (None, 0)
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_water_temp_status()
        assert state == "unavailable"

    def test_returns_temp_when_data(self):
        """Test water temp is returned."""
        temp_date = datetime.datetime.now()
        port = _make_port()
        port.get_water_temperature.return_value = (temp_date, 16.5)
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_water_temp_status()
        assert state == 16.5
        assert attrs["teau"] == 16.5


# ============================================================
# get_weather_status tests (was getstatusMeteoFrance)
# ============================================================
class TestGetWeatherStatus:
    """Tests for get_weather_status method."""

    def test_returns_forecast_state(self):
        """Test that forecast state is returned."""
        forecast_ref = datetime.datetime.now()
        forecast = {"0 min": "Pluie légère", "30 min": "Sec"}
        port = _make_port()
        port.get_1h_forecast.return_value = (forecast_ref, forecast, "MeteoConsult Live")
        mss = SensorStateManager()
        mss.init(port, version="1.0.0")

        state, attrs = mss.get_weather_status()
        assert state == "Pluie légère"
        assert attrs["data_source"] == "MeteoConsult Live"
        assert "forecast_time_ref" in attrs


# ============================================================
# get_rain_chance_status tests (was getstatusRainChance)
# ============================================================
class TestGetRainChanceStatus:
    """Tests for get_rain_chance_status method."""

    def test_returns_zero_when_no_rain(self):
        """Test zero rain chance."""
        port = _make_port()
        port.get_rain_chance.return_value = 0
        mss = SensorStateManager()
        mss.init(port, version="1.0.0")

        state, attrs = mss.get_rain_chance_status()
        assert state == 0
        assert attrs["version"] == "1.0.0"

    def test_returns_percentage_with_live_data(self):
        """Test rain chance with live data source."""
        port = _make_port(live_data={"rain_chance": 75})
        port.get_rain_chance.return_value = 75
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_rain_chance_status()
        assert state == 75
        assert attrs["data_source"] == "MeteoConsult Live"

    def test_returns_percentage_without_live_data(self):
        """Test rain chance without live data."""
        port = _make_port()
        port.get_rain_chance.return_value = 30
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_rain_chance_status()
        assert state == 30
        assert attrs["data_source"] == "MeteoConsult Forecast (Hourly)"


# ============================================================
# get_cloud_cover_status tests (was getstatusCloudCover)
# ============================================================
class TestGetCloudCoverStatus:
    """Tests for get_cloud_cover_status method."""

    def test_returns_cloud_cover(self):
        """Test cloud cover is returned."""
        port = _make_port()
        port.get_cloud_cover.return_value = 60
        mss = SensorStateManager()
        mss.init(port, version="1.0.0")

        state, attrs = mss.get_cloud_cover_status()
        assert state == 60
        assert attrs["data_source"] == "MeteoConsult Forecast (Hourly)"


# ============================================================
# get_weather_alert_status tests (was getstatusWeatherAlert)
# ============================================================
class TestGetWeatherAlertStatus:
    """Tests for get_weather_alert_status method."""

    def test_returns_no_alert(self):
        """Test Aucun alert."""
        port = _make_port()
        port.get_weather_alert.return_value = "Aucun"
        mss = SensorStateManager()
        mss.init(port, version="1.0.0")

        state, attrs = mss.get_weather_alert_status()
        assert state == "Aucun"
        assert attrs["data_source"] == "MeteoConsult"

    def test_returns_alert_phrase(self):
        """Test alert phrase is returned."""
        port = _make_port()
        port.get_weather_alert.return_value = "Vent violent"
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_weather_alert_status()
        assert state == "Vent violent"


# ============================================================
# get_pressure_status tests (was getstatusPressure)
# ============================================================
class TestGetPressureStatus:
    """Tests for get_pressure_status method."""

    def test_returns_pressure_with_live(self):
        """Test pressure with live data."""
        port = _make_port(live_data={"pressure": "1013"})
        port.get_pressure_forecast.return_value = ("1013", {"trend": "stable"})
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_pressure_status()
        assert state == "1013"
        assert attrs["data_source"] == "MeteoConsult Live"

    def test_returns_pressure_without_live(self):
        """Test pressure without live data."""
        port = _make_port()
        port.get_pressure_forecast.return_value = ("1012", {})
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_pressure_status()
        assert state == "1012"
        assert attrs["data_source"] == "MeteoConsult Forecast (Hourly)"


# ============================================================
# get_wave_status tests (was getstatusVagues)
# ============================================================
class TestGetWaveStatus:
    """Tests for get_wave_status method."""

    def test_returns_unavailable_when_no_data(self):
        """Test unavailable when no wave data."""
        port = _make_port()
        port.get_current_live_data.return_value = None
        port.get_forecast_data.return_value = {}
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_wave_status()
        assert state == "unavailable"

    def test_returns_live_wave_data(self):
        """Test live wave data is returned."""
        live_data = {"wave_height": 1.5, "wave_height_max": 2.0, "wave_direction": 270, "swell_height": 1.2, "sea_code": "moderate"}
        port = _make_port(live_data=live_data)
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_wave_status()
        assert state == 1.5
        assert attrs["wave_height_max"] == 2.0
        assert attrs["data_source"] == "MeteoConsult Live"

    def test_fallback_to_forecast(self):
        """Test fallback to hourly forecast."""
        now, previs_data = _make_previs(hours_offset=1, hauteurvague="2.2", hauteurmerv="2.5", dirhouledegres="280", hauteurhoule="1.8")
        port = _make_port(previs={now: previs_data})
        port.get_current_live_data.return_value = None
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_wave_status()
        assert state == "2.2"
        assert attrs["data_source"] == "MeteoConsult Forecast (Hourly)"


# ============================================================
# get_wind_status tests (was getstatusVentLive)
# ============================================================
class TestGetWindStatus:
    """Tests for get_wind_status method."""

    def test_returns_live_wind_data(self):
        """Test live wind data is returned."""
        live_data = {"wind_speed": 20, "wind_gust": 30, "wind_direction": 180}
        port = _make_port(live_data=live_data)
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_wind_status()
        assert state == 20
        assert attrs["wind_gust"] == 30
        assert attrs["data_source"] == "MeteoConsult Live"

    def test_fallback_to_forecast(self):
        """Test fallback to hourly forecast."""
        now, previs_data = _make_previs(hours_offset=1, forcevnds="25", rafvnds="35", dirvdegres="190")
        port = _make_port(previs={now: previs_data})
        port.get_current_live_data.return_value = None
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_wind_status()
        assert state == "25"
        assert attrs["data_source"] == "MeteoConsult Forecast (Hourly)"

    def test_unavailable_when_no_data(self):
        """Test unavailable when no wind data."""
        port = _make_port()
        port.get_current_live_data.return_value = None
        port.get_forecast_data.return_value = {}
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_wind_status()
        assert state == "unavailable"


# ============================================================
# get_air_temp_status tests (was getstatusAirTemp)
# ============================================================
class TestGetAirTempStatus:
    """Tests for get_air_temp_status method."""

    def test_returns_live_temp(self):
        """Test live air temp is returned."""
        live_data = {"tempe": 18.5, "tempe_felt": 17.0}
        port = _make_port(live_data=live_data)
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_air_temp_status()
        assert state == 18.5
        assert attrs["tempe_felt"] == 17.0
        assert attrs["data_source"] == "MeteoConsult Live"

    def test_fallback_to_forecast(self):
        """Test fallback to hourly forecast."""
        now, previs_data = _make_previs(hours_offset=1, t="19.0")
        port = _make_port(previs={now: previs_data})
        port.get_current_live_data.return_value = None
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_air_temp_status()
        assert state == "19.0"


# ============================================================
# get_visibility_status tests (was getstatusVisibility)
# ============================================================
class TestGetVisibilityStatus:
    """Tests for get_visibility_status method."""

    def test_returns_live_visibility(self):
        """Test live visibility is returned."""
        live_data = {"visibility": 10000}
        port = _make_port(live_data=live_data)
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_visibility_status()
        assert state == 10000
        assert attrs["data_source"] == "MeteoConsult Live"

    def test_unavailable_without_live(self):
        """Test unavailable without live data."""
        port = _make_port()
        port.get_current_live_data.return_value = None
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_visibility_status()
        assert state == "unavailable"


# ============================================================
# get_water_level_status tests (was getstatusWaterLevel)
# ============================================================
class TestGetWaterLevelStatus:
    """Tests for get_water_level_status method."""

    def test_returns_unavailable_when_no_data(self):
        """Test unavailable when no water level."""
        port = _make_port()
        port.get_current_water_level.return_value = (None, None)
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_water_level_status()
        assert state == "unavailable"

    def test_returns_level_and_status(self):
        """Test water level is returned."""
        port = _make_port()
        port.get_current_water_level.return_value = (3.5, "Montante")
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_water_level_status()
        assert state == 3.5
        assert attrs["tide_status"] == "Montante"
        assert attrs["data_source"] == "Calculated (Sinusoidal Interpolation)"


# ============================================================
# get_uv_status tests
# ============================================================
class TestGetstatusUV:
    """Tests for get_uv_status method."""

    def test_returns_uv_value(self):
        """Test UV value is returned."""
        port = _make_port()
        port.get_uv.return_value = 5
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_uv_status()
        assert state == 5
        assert attrs["data_source"] == "MeteoConsult Forecast (Hourly)"

    def test_returns_zero_when_no_data(self):
        """Test zero UV when no data available."""
        port = _make_port()
        port.get_uv.return_value = 0
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_uv_status()
        assert state == 0

    def test_returns_high_uv(self):
        """Test high UV value is returned."""
        port = _make_port()
        port.get_uv.return_value = 11
        mss = SensorStateManager()
        mss.init(port)

        state, attrs = mss.get_uv_status()
        assert state == 11

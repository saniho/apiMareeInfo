"""Comprehensive tests for apiMareeInfo module."""

import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.apiMareeInfo.apiMareeInfo import (
    ApiMareeInfo,
    ListePorts,
    MeteoMarine,
    MeteoMarineLive,
    stormIO,
)


# ============================================================
# ListePorts tests
# ============================================================
class TestListePorts:
    """Tests for ListePorts class."""

    @pytest.mark.asyncio
    async def test_getjson_calls_async_fetch(self):
        """Test that getjson delegates to async_fetch_json."""
        with patch("custom_components.apiMareeInfo.apiMareeInfo.async_fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"contenu": []}
            lp = ListePorts()
            result = await lp.getjson("http://example.com", params={"q": "test"})

            mock_fetch.assert_called_once_with(
                "http://example.com",
                session=None,
                params={"q": "test"},
                source_name="ListePorts",
            )
            assert result == {"contenu": []}

    @pytest.mark.asyncio
    async def test_getlisteport_builds_correct_url_and_params(self):
        """Test that getlisteport builds correct URL and params."""
        with patch("custom_components.apiMareeInfo.apiMareeInfo.async_fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"contenu": [{"nom": "Saint-Malo"}]}
            lp = ListePorts()
            result = await lp.getlisteport("Saint-Malo")

            call_args = mock_fetch.call_args
            assert "recherche.php" in call_args[0][0]
            assert call_args[1]["params"] == {"rech": "Saint-Malo"}

    @pytest.mark.asyncio
    async def test_getlisteport_passes_session(self):
        """Test that getlisteport passes session to async_fetch_json."""
        with patch("custom_components.apiMareeInfo.apiMareeInfo.async_fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"contenu": []}
            lp = ListePorts()
            mock_session = MagicMock()
            await lp.getlisteport("test", session=mock_session)

            assert mock_fetch.call_args[1]["session"] == mock_session


# ============================================================
# MeteoMarine tests
# ============================================================
class TestMeteoMarine:
    """Tests for MeteoMarine class."""

    def test_init_builds_correct_url(self):
        """Test that URL is built correctly from lat/lng."""
        mm = MeteoMarine("48.5", "-2.0")
        assert "lat=48.5" in mm._url
        assert "lon=-2.0" in mm._url
        assert "previsionsSpot.php" in mm._url

    @pytest.mark.asyncio
    async def test_getdata_calls_async_fetch(self):
        """Test that getdata delegates to async_fetch_json."""
        with patch("custom_components.apiMareeInfo.apiMareeInfo.async_fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"contenu": {"marees": []}}
            mm = MeteoMarine("48.5", "-2.0")
            result = await mm.getdata()

            mock_fetch.assert_called_once()
            assert "48.5" in mock_fetch.call_args[0][0]

    @pytest.mark.asyncio
    async def test_getdata_passes_session(self):
        """Test that getdata passes session correctly."""
        with patch("custom_components.apiMareeInfo.apiMareeInfo.async_fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {}
            mm = MeteoMarine("48.5", "-2.0")
            mock_session = MagicMock()
            await mm.getdata(session=mock_session)

            assert mock_fetch.call_args[1]["session"] == mock_session


# ============================================================
# MeteoMarineLive tests
# ============================================================
class TestMeteoMarineLive:
    """Tests for MeteoMarineLive class."""

    def test_init_stores_id_port(self):
        """Test that id_port is stored."""
        mml = MeteoMarineLive("12345")
        assert mml._id_port == "12345"

    @pytest.mark.asyncio
    async def test_getdata_builds_url_with_today(self):
        """Test that URL contains today's date."""
        with patch("custom_components.apiMareeInfo.apiMareeInfo.async_fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"content": {"forecasts": []}}
            mml = MeteoMarineLive("12345")
            await mml.getdata()

            url = mock_fetch.call_args[0][0]
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            assert today in url
            assert "12345" in url


# ============================================================
# stormIO tests
# ============================================================
class TestStormIO:
    """Tests for stormIO class."""

    def test_init_stores_credentials(self):
        """Test that credentials are stored."""
        sio = stormIO("48.5", "-2.0", "key123")
        assert sio._lat == "48.5"
        assert sio._lng == "-2.0"
        assert sio._storm_key == "key123"

    @pytest.mark.asyncio
    async def test_getdata_sends_auth_header(self):
        """Test that Authorization header is sent."""
        with patch("custom_components.apiMareeInfo.apiMareeInfo.async_fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"data": []}
            sio = stormIO("48.5", "-2.0", "key123")
            await sio.getdata()

            headers = mock_fetch.call_args[1]["headers"]
            assert headers == {"Authorization": "key123"}

    @pytest.mark.asyncio
    async def test_getdata_uses_600s_timeout(self):
        """Test that StormIO uses 600s timeout."""
        with patch("custom_components.apiMareeInfo.apiMareeInfo.async_fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"data": []}
            sio = stormIO("48.5", "-2.0", "key123")
            await sio.getdata()

            assert mock_fetch.call_args[1]["timeout"] == 600

    @pytest.mark.asyncio
    async def test_getdata_includes_date_range(self):
        """Test that start/end params include 2-day range."""
        with patch("custom_components.apiMareeInfo.apiMareeInfo.async_fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"data": []}
            sio = stormIO("48.5", "-2.0", "key123")
            await sio.getdata()

            params = mock_fetch.call_args[1]["params"]
            assert "lat" in params
            assert "lng" in params
            assert "start" in params
            assert "end" in params

    @pytest.mark.asyncio
    async def test_getdata_custom_error_return(self):
        """Test that StormIO has custom error return."""
        with patch("custom_components.apiMareeInfo.apiMareeInfo.async_fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"errors": {"key": "Communication error"}}
            sio = stormIO("48.5", "-2.0", "key123")
            result = await sio.getdata()

            error_return = mock_fetch.call_args[1]["error_return"]
            assert "errors" in error_return


# ============================================================
# ApiMareeInfo tests
# ============================================================
class TestApiMareeInfo:
    """Tests for ApiMareeInfo main class."""

    def test_init_defaults(self):
        """Test default initialization values."""
        api = ApiMareeInfo()
        assert api._donnees == {}
        assert api._nomDuPort is None
        assert api._error is False
        assert api._errorMessage == ""
        assert api._donneesPrevis == {}
        assert api._donneesPrevisLive == {}

    def test_setport(self):
        """Test setport stores lat/lng."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)
        assert api.get_lat() == 48.5
        assert api.get_lng() == -2.0

    def test_setid(self):
        """Test setid stores id."""
        api = ApiMareeInfo()
        api.setid("12345")
        assert api.getid() == "12345"

    def test_setmaxhours(self):
        """Test setmaxhours stores value."""
        api = ApiMareeInfo()
        api.setmaxhours(12)
        assert api.get_max_hours() == 12

    def test_get_port_name_returns_clean_name(self):
        """Test that port name strips copyright."""
        api = ApiMareeInfo()
        api._nomDuPort = "Saint-Malo©SHOM"
        assert api.get_port_name() == "Saint-Malo"

    def test_get_port_name_returns_unknown_when_none(self):
        """Test that Unknown is returned when no port name."""
        api = ApiMareeInfo()
        assert api.get_port_name() == "Unknown"

    def test_getcopyright(self):
        """Test copyright returns SHOM."""
        api = ApiMareeInfo()
        assert api.getcopyright() == "©SHOM"

    def test_get_full_port_name(self):
        """Test full port name is returned as-is."""
        api = ApiMareeInfo()
        api._nomDuPort = "Saint-Malo©SHOM"
        assert api.get_full_port_name() == "Saint-Malo©SHOM"

    def test_has_error_and_get_error_message(self):
        """Test error state getters."""
        api = ApiMareeInfo()
        assert api.has_error() is False
        assert api.get_error_message() == ""

        api._error = True
        api._errorMessage = "Test error"
        assert api.has_error() is True
        assert api.get_error_message() == "Test error"

    def test_get_http_request_time(self):
        """Test that HTTP request time is set."""
        api = ApiMareeInfo()
        before = datetime.datetime.now()
        api._httptimerequest = before
        after = datetime.datetime.now()
        assert before <= api.get_http_request_time() <= after

    def test_get_tide_data_returns_donnees(self):
        """Test that get_tide_data returns _donnees."""
        api = ApiMareeInfo()
        api._donnees = {"test": "data"}
        assert api.get_tide_data() == {"test": "data"}

    def test_get_forecast_data_returns_previsions(self):
        """Test that get_forecast_data returns _donneesPrevis."""
        api = ApiMareeInfo()
        api._donneesPrevis = {"test": "forecast"}
        assert api.get_forecast_data() == {"test": "forecast"}


class TestApiMareeInfoGetJson:
    """Tests for ApiMareeInfo.getjson routing."""

    @pytest.mark.asyncio
    async def test_getjson_meteomarine(self):
        """Test getjson routes to MeteoMarine."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)

        with patch("custom_components.apiMareeInfo.apiMareeInfo.MeteoMarine") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.getdata = AsyncMock(return_value={"data": "test"})
            mock_cls.return_value = mock_instance

            result = await api.getjson("MeteoMarine")
            assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_getjson_meteomarinelive(self):
        """Test getjson routes to MeteoMarineLive."""
        api = ApiMareeInfo()
        api.setid("12345")

        with patch("custom_components.apiMareeInfo.apiMareeInfo.MeteoMarineLive") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.getdata = AsyncMock(return_value={"content": {}})
            mock_cls.return_value = mock_instance

            result = await api.getjson("MeteoMarineLive")
            assert result == {"content": {}}

    @pytest.mark.asyncio
    async def test_getjson_stormio(self):
        """Test getjson routes to stormIO."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)

        with patch("custom_components.apiMareeInfo.apiMareeInfo.stormIO") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.getdata = AsyncMock(return_value={"data": []})
            mock_cls.return_value = mock_instance

            result = await api.getjson("stormio", info={"stormkey": "key123"})
            assert result == {"data": []}


class TestApiMareeInfoGetInformationPort:
    """Tests for getinformationport parsing."""

    @pytest.mark.asyncio
    async def test_parse_meteomarine_data(self, sjm_meteomarine_data):
        """Test parsing of real MeteoMarine data."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)
        api.setmaxhours(6)
        await api.getinformationport(jsondata=sjm_meteomarine_data, origine="MeteoMarine")

        assert api.has_error() is False
        assert api.get_port_name() != "Unknown"
        assert len(api.get_tide_data()) > 0
        assert len(api.get_forecast_data()) > 0

    @pytest.mark.asyncio
    async def test_parse_meteomarine_empty_marees(self, empty_meteomarine_data):
        """Test handling of empty tide data."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)
        await api.getinformationport(jsondata=empty_meteomarine_data, origine="MeteoMarine")

        assert api.has_error() is True
        assert "No tide data" in api.get_error_message()

    @pytest.mark.asyncio
    async def test_parse_meteomarine_error_data(self, error_meteomarine_data):
        """Test handling of error response."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)
        await api.getinformationport(jsondata=error_meteomarine_data, origine="MeteoMarine")

        assert api.has_error() is True

    @pytest.mark.asyncio
    async def test_parse_stormio_data(self, sjm_stormglass_data):
        """Test parsing of StormGlass data."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)
        api.setmaxhours(6)
        await api.getinformationport(jsondata=sjm_stormglass_data, origine="stormio")

        assert api.has_error() is False
        assert len(api.get_tide_data()) > 0

    @pytest.mark.asyncio
    async def test_parse_stormio_error(self, error_stormglass_data):
        """Test handling of StormGlass error."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)
        await api.getinformationport(jsondata=error_stormglass_data, origine="stormio")

        assert api.has_error() is True
        assert "Invalid API key" in api.get_error_message()

    @pytest.mark.asyncio
    async def test_unknown_origine_raises(self):
        """Test that unknown origine raises RuntimeError."""
        api = ApiMareeInfo()
        with pytest.raises(RuntimeError, match="Data Origin unknown"):
            await api.getinformationport(jsondata={}, origine="unknown")

    @pytest.mark.asyncio
    async def test_meteomarine_parses_tide_structure(self, sjm_meteomarine_data):
        """Test that tide data is parsed into correct structure."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)
        api.setmaxhours(6)
        await api.getinformationport(jsondata=sjm_meteomarine_data, origine="MeteoMarine")

        info = api.get_tide_data()
        for key, maree in info.items():
            assert "coeff" in maree
            assert "hauteur" in maree
            assert "horaire" in maree
            assert "etat" in maree
            assert "dateComplete" in maree
            assert maree["etat"] in ("PM", "BM")

    @pytest.mark.asyncio
    async def test_meteomarine_parses_forecast_structure(self, sjm_meteomarine_data):
        """Test that forecast data is parsed into correct structure."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)
        api.setmaxhours(6)
        await api.getinformationport(jsondata=sjm_meteomarine_data, origine="MeteoMarine")

        previs = api.get_forecast_data()
        for dt, data in previs.items():
            assert isinstance(dt, datetime.datetime)
            assert "forcevnds" in data
            assert "t" in data
            assert "precipitation" in data
            assert "pressure" in data or "pression" in data


class TestApiMareeInfoGetters:
    """Tests for ApiMareeInfo data getter methods."""

    @pytest.mark.asyncio
    async def test_get_next_rain_with_rain(self, sjm_meteomarine_data):
        """Test get_next_rain finds next rain."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)
        api.setmaxhours(24)
        await api.getinformationport(jsondata=sjm_meteomarine_data, origine="MeteoMarine")

        date, precipitation = api.get_next_rain()
        # Result depends on fixture data - either (datetime, mm) or (None, 0)
        if date is not None:
            assert isinstance(date, datetime.datetime)
            assert precipitation >= 0

    @pytest.mark.asyncio
    async def test_get_water_temperature(self, sjm_meteomarine_data):
        """Test get_water_temperature returns water temperature."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)
        api.setmaxhours(24)
        await api.getinformationport(jsondata=sjm_meteomarine_data, origine="MeteoMarine")

        date, temp = api.get_water_temperature()
        if date is not None:
            assert isinstance(date, datetime.datetime)

    @pytest.mark.asyncio
    async def test_get_cloud_cover(self, sjm_meteomarine_data):
        """Test get_cloud_cover returns a value."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)
        api.setmaxhours(24)
        await api.getinformationport(jsondata=sjm_meteomarine_data, origine="MeteoMarine")

        cover = api.get_cloud_cover()
        assert isinstance(cover, (int, float))

    @pytest.mark.asyncio
    async def test_get_weather_alert_no_avis(self):
        """Test get_weather_alert returns Aucun when no avis."""
        api = ApiMareeInfo()
        api._avis = []
        assert api.get_weather_alert() == "Aucun"

    @pytest.mark.asyncio
    async def test_get_weather_alert_with_alert(self):
        """Test get_weather_alert returns alert phrase."""
        api = ApiMareeInfo()
        api._avis = [{"niveau": 2, "phrase": "Vent violent"}]
        assert api.get_weather_alert() == "Vent violent"

    @pytest.mark.asyncio
    async def test_get_weather_alert_no_alert(self):
        """Test get_weather_alert returns Aucun when niveau=0."""
        api = ApiMareeInfo()
        api._avis = [{"niveau": 0, "phrase": "Pas de souci"}]
        assert api.get_weather_alert() == "Aucun"

    @pytest.mark.asyncio
    async def test_get_pressure_forecast(self, sjm_meteomarine_data):
        """Test get_pressure_forecast returns pressure data."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)
        api.setmaxhours(24)
        await api.getinformationport(jsondata=sjm_meteomarine_data, origine="MeteoMarine")

        current, forecast = api.get_pressure_forecast()
        # current should be a string (hPa) or None
        assert current is None or isinstance(current, str)

    @pytest.mark.asyncio
    async def test_get_rain_chance(self):
        """Test get_rain_chance returns numeric value."""
        api = ApiMareeInfo()
        api._donneesPrevisLive = {}
        chance = api.get_rain_chance()
        assert isinstance(chance, (int, float))
        assert chance == 0


class TestApiMareeInfoWaterLevel:
    """Tests for water level interpolation."""

    @pytest.mark.asyncio
    async def test_get_current_water_level_with_data(self, sjm_meteomarine_data):
        """Test water level calculation with real data."""
        api = ApiMareeInfo()
        api.setport(48.5, -2.0)
        api.setmaxhours(24)
        await api.getinformationport(jsondata=sjm_meteomarine_data, origine="MeteoMarine")

        level, status = api.get_current_water_level()
        if level is not None:
            assert isinstance(level, float)
            assert status in ("Montante", "Descendante")

    def test_get_current_water_level_no_data(self):
        """Test water level with no tide data."""
        api = ApiMareeInfo()
        api._donnees = {}
        level, status = api.get_current_water_level()
        assert level is None
        assert status is None


class TestGetProchaineGrandeMaree:
    """Tests for get_prochaine_grande_maree method."""

    def test_returns_grande_maree_when_available(self):
        """Test that it finds next tide with coef >= 100."""
        api = ApiMareeInfo()
        now = datetime.datetime.now()
        api._donnees = {
            "horaire_0_0": {
                "coeff": 85,
                "hauteur": 5.5,
                "horaire": "06:30",
                "etat": "PM",
                "nieme": 0,
                "jour": 0,
                "date": "2024-01-15T06:30:00",
                "dateComplete": now + datetime.timedelta(hours=2),
            },
            "horaire_1_0": {
                "coeff": 105,
                "hauteur": 6.8,
                "horaire": "18:55",
                "etat": "PM",
                "nieme": 0,
                "jour": 1,
                "date": "2024-01-16T18:55:00",
                "dateComplete": now + datetime.timedelta(days=1, hours=6),
            },
        }
        result = api.get_prochaine_grande_maree()
        assert result is not None
        assert result["coeff"] == 105
        assert result["etat"] == "PM"

    def test_returns_none_when_no_grande_maree(self):
        """Test that it returns None when no coef >= 100."""
        api = ApiMareeInfo()
        now = datetime.datetime.now()
        api._donnees = {
            "horaire_0_0": {
                "coeff": 85,
                "hauteur": 5.5,
                "horaire": "06:30",
                "etat": "PM",
                "nieme": 0,
                "jour": 0,
                "date": "2024-01-15T06:30:00",
                "dateComplete": now + datetime.timedelta(hours=2),
            },
        }
        result = api.get_prochaine_grande_maree()
        assert result is None

    def test_skips_past_tides(self):
        """Test that it ignores tides in the past."""
        api = ApiMareeInfo()
        now = datetime.datetime.now()
        api._donnees = {
            "horaire_0_0": {
                "coeff": 110,
                "hauteur": 7.0,
                "horaire": "06:30",
                "etat": "PM",
                "nieme": 0,
                "jour": 0,
                "date": "2024-01-15T06:30:00",
                "dateComplete": now - datetime.timedelta(hours=2),
            },
        }
        result = api.get_prochaine_grande_maree()
        assert result is None

    def test_skips_low_tide(self):
        """Test that it ignores BM even with high coef."""
        api = ApiMareeInfo()
        now = datetime.datetime.now()
        api._donnees = {
            "horaire_0_0": {
                "coeff": 105,
                "hauteur": 1.2,
                "horaire": "12:45",
                "etat": "BM",
                "nieme": 0,
                "jour": 0,
                "date": "2024-01-15T12:45:00",
                "dateComplete": now + datetime.timedelta(hours=4),
            },
        }
        result = api.get_prochaine_grande_maree()
        assert result is None

    def test_returns_first_grande_maree(self):
        """Test that it returns the chronologically first grande marée."""
        api = ApiMareeInfo()
        now = datetime.datetime.now()
        api._donnees = {
            "horaire_0_0": {
                "coeff": 102,
                "hauteur": 6.5,
                "horaire": "06:30",
                "etat": "PM",
                "nieme": 0,
                "jour": 0,
                "date": "2024-01-15T06:30:00",
                "dateComplete": now + datetime.timedelta(days=3),
            },
            "horaire_1_0": {
                "coeff": 110,
                "hauteur": 7.0,
                "horaire": "18:55",
                "etat": "PM",
                "nieme": 0,
                "jour": 1,
                "date": "2024-01-16T18:55:00",
                "dateComplete": now + datetime.timedelta(days=10),
            },
        }
        result = api.get_prochaine_grande_maree()
        assert result is not None
        assert result["coeff"] == 102

    def test_handles_coef_as_string(self):
        """Test that it handles coef stored as string."""
        api = ApiMareeInfo()
        now = datetime.datetime.now()
        api._donnees = {
            "horaire_0_0": {
                "coeff": "105",
                "hauteur": 6.8,
                "horaire": "18:55",
                "etat": "PM",
                "nieme": 0,
                "jour": 0,
                "date": "2024-01-16T18:55:00",
                "dateComplete": now + datetime.timedelta(days=1),
            },
        }
        result = api.get_prochaine_grande_maree()
        assert result is not None
        assert result["coeff"] == "105"

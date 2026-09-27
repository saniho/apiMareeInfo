"""Tests for parsers module."""

import datetime

from custom_components.apiMareeInfo.parsers import (
    parse_meteo_marine,
    parse_storm_io,
)


# ============================================================
# parse_meteo_marine tests
# ============================================================
class TestParseMeteoMarine:
    """Tests for parse_meteo_marine function."""

    def _make_response(self, marees=None, previs_detail=None, avis=None):
        """Build a minimal MeteoMarine API response."""
        if marees is None:
            marees = [
                {
                    "lieu": "Saint-Malo",
                    "datetime": "2024-06-15T06:30:00",
                    "etales": [
                        {"coef": "85", "hauteur": "5.5", "datetime": "2024-06-15T06:30:00", "type_etale": "PM"},
                        {"coef": "30", "hauteur": "1.2", "datetime": "2024-06-15T12:45:00", "type_etale": "BM"},
                    ],
                }
            ]
        if previs_detail is None:
            previs_detail = [
                {
                    "forcevnds": "15",
                    "rafvnds": "25",
                    "dirvdegres": "180",
                    "datetime": "2024-06-15T13:00:00",
                    "nebu": "c0030",
                    "nuagecouverture": "60",
                    "precipitation": "0",
                    "pression": "1013",
                    "teau": "16.5",
                    "t": "18.2",
                    "risqueorage": "0",
                    "dirhouledegres": "270",
                    "hauteurhoule": "1.5",
                    "periodehoule": "8",
                    "hauteurmerv": "2.0",
                    "periodemerv": "10",
                    "hauteurvague": "1.8",
                    "uv": "3",
                }
            ]
        if avis is None:
            avis = []
        return {
            "contenu": {
                "marees": marees,
                "previs": {"detail": previs_detail},
                "avis": avis,
            }
        }

    def test_parse_valid_response(self):
        """Test parsing a valid response."""
        resp = self._make_response()
        result = parse_meteo_marine(resp, lat=48.6, lng=-2.0)

        assert result.error is False
        assert result.port_name == "Saint-Malo"
        assert len(result.tides) == 2
        assert len(result.forecasts) == 1

    def test_parse_tide_fields(self):
        """Test tide data is correctly parsed."""
        resp = self._make_response()
        result = parse_meteo_marine(resp, lat=48.6, lng=-2.0)

        tide = result.tides["horaire_0_0"]
        assert tide["horaire"] == "06:30"
        assert tide["etat"] == "PM"
        assert tide["coeff"] == "85"
        assert tide["hauteur"] == "5.5"
        assert tide["jour"] == 0
        assert tide["nieme"] == 0

    def test_parse_forecast_fields(self):
        """Test forecast data is correctly parsed."""
        resp = self._make_response()
        result = parse_meteo_marine(resp, lat=48.6, lng=-2.0)

        dt = datetime.datetime(2024, 6, 15, 13, 0)
        fc = result.forecasts[dt]
        assert fc["forcevnds"] == "15"
        assert fc["t"] == "18.2"
        assert fc["teau"] == "16.5"
        assert fc["pressure"] == "1013"

    def test_parse_avis(self):
        """Test avis (weather alerts) are parsed."""
        avis = [{"niveau": 2, "phrase": "Vent violent"}]
        resp = self._make_response(avis=avis)
        result = parse_meteo_marine(resp, lat=48.6, lng=-2.0)

        assert len(result.avis) == 1
        assert result.avis[0]["niveau"] == 2

    def test_empty_marees_returns_error(self):
        """Test error on empty marees."""
        resp = self._make_response(marees=[])
        result = parse_meteo_marine(resp, lat=48.6, lng=-2.0)

        assert result.error is True
        assert "No tide data" in result.error_message

    def test_missing_contenu_returns_error(self):
        """Test error on missing contenu key."""
        result = parse_meteo_marine({}, lat=48.6, lng=-2.0)

        assert result.error is True

    def test_none_input_returns_error(self):
        """Test error on None input."""
        result = parse_meteo_marine({}, lat=48.6, lng=-2.0)
        assert result.error is True


# ============================================================
# parse_storm_io tests
# ============================================================
class TestParseStormIO:
    """Tests for parse_storm_io function."""

    def _make_response(self, data=None, station_name="Brest"):
        """Build a minimal StormGlass API response."""
        if data is None:
            data = [
                {"time": "2024-06-15T06:30:00+00:00", "height": 5.5, "type": "PM", "coef": "85"},
                {"time": "2024-06-15T12:45:00+00:00", "height": 1.2, "type": "BM", "coef": "30"},
            ]
        return {
            "data": data,
            "meta": {"station": {"name": station_name}},
        }

    def test_parse_valid_response(self):
        """Test parsing a valid StormGlass response."""
        resp = self._make_response()
        result = parse_storm_io(resp, previous_date=None)

        assert result.error is False
        assert result.port_name == "Brest"
        assert len(result.tides) == 2

    def test_parse_tide_fields(self):
        """Test tide data is correctly parsed."""
        resp = self._make_response()
        result = parse_storm_io(resp, previous_date=None)

        tide = result.tides["horaire_0_0"]
        assert tide["horaire"] == "06:30"
        assert tide["etat"] == "PM"
        assert tide["coeff"] == "85"
        assert tide["hauteur"] == 5.5

    def test_day_increment(self):
        """Test jour increments when date changes."""
        data = [
            {"time": "2024-06-15T06:30:00+00:00", "height": 5.5, "type": "PM", "coef": "85"},
            {"time": "2024-06-16T12:45:00+00:00", "height": 1.2, "type": "BM", "coef": "30"},
        ]
        prev = datetime.datetime(2024, 6, 14, 12, 0)
        resp = self._make_response(data=data)
        result = parse_storm_io(resp, previous_date=prev)

        assert result.tides["horaire_0_0"]["jour"] == 0
        assert result.tides["horaire_1_1"]["jour"] == 1

    def test_errors_returns_error(self):
        """Test error response."""
        resp = {"errors": {"key": "Invalid API key"}}
        result = parse_storm_io(resp, previous_date=None)

        assert result.error is True
        assert result.error_message == "Invalid API key"

    def test_empty_data_returns_error(self):
        """Test empty response."""
        result = parse_storm_io({}, previous_date=None)
        assert result.error is True

    def test_no_forecasts(self):
        """StormGlass doesn't provide weather forecasts."""
        resp = self._make_response()
        result = parse_storm_io(resp, previous_date=None)
        assert result.forecasts == {}

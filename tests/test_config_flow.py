"""Comprehensive tests for the apiMareeInfo config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME

from custom_components.apiMareeInfo.config_flow import (
    CONF_PORT_SEARCH,
    CONF_PORT_SELECT,
    ApiMareeInfoConfigFlow,
    OptionsFlowHandler,
)
from custom_components.apiMareeInfo.const import (
    CONF_ID,
    CONF_MAXHOURS,
    CONF_PROVIDER,
    DEFAULT_PROVIDER,
    DOMAIN,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_hass():
    """Return a minimal mock hass object."""
    hass = MagicMock()
    hass.data = {}
    return hass


@pytest.fixture
def flow(mock_hass):
    """Return a fresh config flow with mock hass and mutable context."""
    f = ApiMareeInfoConfigFlow()
    f.hass = mock_hass
    f.context = {}
    return f


SAMPLE_PORTS_RESPONSE = {
    "contenu": [
        {
            "nom": "Saint-Malo",
            "pays": "France",
            "lat": 48.6493,
            "lon": -2.0257,
            "id": 123,
        },
        {
            "nom": "Dinard",
            "pays": "France",
            "lat": 48.6313,
            "lon": -2.0782,
            "id": 456,
        },
    ]
}


SAMPLE_PORT_KEY = "Saint-Malo (France)"


# ---------------------------------------------------------------------------
# ApiMareeInfoConfigFlow – async_step_user
# ---------------------------------------------------------------------------
class TestStepUser:
    """Tests for the 'user' step."""

    @pytest.mark.asyncio
    async def test_shows_form_when_no_input(self, flow):
        """Form is returned when user_input is None."""
        result = await flow.async_step_user(None)

        assert result["type"] == "form"
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    @pytest.mark.asyncio
    async def test_search_returns_ports_moves_to_select(self, flow):
        """Successful search transitions to the select_port step."""
        mock_api = MagicMock()
        mock_api.getlisteport = AsyncMock(return_value=SAMPLE_PORTS_RESPONSE)

        with patch(
            "custom_components.apiMareeInfo.config_flow.ListePorts",
            return_value=mock_api,
        ), patch(
            "custom_components.apiMareeInfo.config_flow.async_get_clientsession",
        ):
            result = await flow.async_step_user({CONF_PORT_SEARCH: "Saint-Malo"})

        # Ports dict is populated
        assert len(flow.ports) == 2
        assert SAMPLE_PORT_KEY in flow.ports

        # Should return the select_port form
        assert result["type"] == "form"
        assert result["step_id"] == "select_port"

    @pytest.mark.asyncio
    async def test_search_empty_response_shows_no_ports_found(self, flow):
        """Empty 'contenu' from the API surfaces 'no_ports_found' error."""
        mock_api = MagicMock()
        mock_api.getlisteport = AsyncMock(return_value={"contenu": []})

        with patch(
            "custom_components.apiMareeInfo.config_flow.ListePorts",
            return_value=mock_api,
        ), patch(
            "custom_components.apiMareeInfo.config_flow.async_get_clientsession",
        ):
            result = await flow.async_step_user({CONF_PORT_SEARCH: "nowhere"})

        assert result["type"] == "form"
        assert result["step_id"] == "user"
        assert result["errors"]["base"] == "no_ports_found"

    @pytest.mark.asyncio
    async def test_search_missing_contenu_key_shows_no_ports_found(self, flow):
        """Response without 'contenu' key surfaces 'no_ports_found'."""
        mock_api = MagicMock()
        mock_api.getlisteport = AsyncMock(return_value={"error": "some error"})

        with patch(
            "custom_components.apiMareeInfo.config_flow.ListePorts",
            return_value=mock_api,
        ), patch(
            "custom_components.apiMareeInfo.config_flow.async_get_clientsession",
        ):
            result = await flow.async_step_user({CONF_PORT_SEARCH: "fail"})

        assert result["errors"]["base"] == "no_ports_found"

    @pytest.mark.asyncio
    async def test_search_exception_shows_cannot_connect(self, flow):
        """An exception during the API call surfaces 'cannot_connect'."""
        mock_api = MagicMock()
        mock_api.getlisteport = AsyncMock(side_effect=RuntimeError("timeout"))

        with patch(
            "custom_components.apiMareeInfo.config_flow.ListePorts",
            return_value=mock_api,
        ), patch(
            "custom_components.apiMareeInfo.config_flow.async_get_clientsession",
        ):
            result = await flow.async_step_user({CONF_PORT_SEARCH: "test"})

        assert result["type"] == "form"
        assert result["step_id"] == "user"
        assert result["errors"]["base"] == "cannot_connect"

    @pytest.mark.asyncio
    async def test_search_builds_port_keys_with_pays(self, flow):
        """Port keys include country (pays) when available."""
        mock_api = MagicMock()
        mock_api.getlisteport = AsyncMock(return_value=SAMPLE_PORTS_RESPONSE)

        with patch(
            "custom_components.apiMareeInfo.config_flow.ListePorts",
            return_value=mock_api,
        ), patch(
            "custom_components.apiMareeInfo.config_flow.async_get_clientsession",
        ):
            await flow.async_step_user({CONF_PORT_SEARCH: "test"})

        assert "Saint-Malo (France)" in flow.ports
        assert "Dinard (France)" in flow.ports

    @pytest.mark.asyncio
    async def test_search_falls_back_to_departement_when_no_pays(self, flow):
        """Port keys fall back to 'departement' when 'pays' is absent."""
        response = {
            "contenu": [
                {
                    "nom": "Brest",
                    "departement": "Finistere",
                    "lat": 48.39,
                    "lon": -4.49,
                    "id": 789,
                }
            ]
        }
        mock_api = MagicMock()
        mock_api.getlisteport = AsyncMock(return_value=response)

        with patch(
            "custom_components.apiMareeInfo.config_flow.ListePorts",
            return_value=mock_api,
        ), patch(
            "custom_components.apiMareeInfo.config_flow.async_get_clientsession",
        ):
            await flow.async_step_user({CONF_PORT_SEARCH: "test"})

        assert "Brest (Finistere)" in flow.ports

    @pytest.mark.asyncio
    async def test_search_falls_back_to_unknown_when_no_geo_info(self, flow):
        """Port keys fall back to 'Inconnu' when neither pays nor departement."""
        response = {
            "contenu": [
                {
                    "nom": "GhostPort",
                    "lat": 0.0,
                    "lon": 0.0,
                }
            ]
        }
        mock_api = MagicMock()
        mock_api.getlisteport = AsyncMock(return_value=response)

        with patch(
            "custom_components.apiMareeInfo.config_flow.ListePorts",
            return_value=mock_api,
        ), patch(
            "custom_components.apiMareeInfo.config_flow.async_get_clientsession",
        ):
            await flow.async_step_user({CONF_PORT_SEARCH: "test"})

        assert "GhostPort (Inconnu)" in flow.ports

    @pytest.mark.asyncio
    async def test_search_stores_lat_lon_id_for_each_port(self, flow):
        """Port details dict includes lat, lon, and id."""
        mock_api = MagicMock()
        mock_api.getlisteport = AsyncMock(return_value=SAMPLE_PORTS_RESPONSE)

        with patch(
            "custom_components.apiMareeInfo.config_flow.ListePorts",
            return_value=mock_api,
        ), patch(
            "custom_components.apiMareeInfo.config_flow.async_get_clientsession",
        ):
            await flow.async_step_user({CONF_PORT_SEARCH: "test"})

        details = flow.ports[SAMPLE_PORT_KEY]
        assert details["lat"] == 48.6493
        assert details["lon"] == -2.0257
        assert details["id"] == 123


# ---------------------------------------------------------------------------
# ApiMareeInfoConfigFlow – async_step_select_port
# ---------------------------------------------------------------------------
class TestStepSelectPort:
    """Tests for the 'select_port' step."""

    @pytest.fixture
    def flow_with_ports(self, flow):
        """Flow pre-populated with sample port data."""
        flow.ports = {
            SAMPLE_PORT_KEY: {"lat": 48.6493, "lon": -2.0257, "id": 123},
        }
        return flow

    @pytest.mark.asyncio
    async def test_shows_form_when_no_input(self, flow_with_ports):
        """Form is returned when user_input is None."""
        result = await flow_with_ports.async_step_select_port(None)

        assert result["type"] == "form"
        assert result["step_id"] == "select_port"
        assert result["errors"] == {}

    @pytest.mark.asyncio
    async def test_creates_entry_on_success(self, flow_with_ports):
        """Valid selection creates a config entry with correct data."""
        user_input = {
            CONF_PORT_SELECT: SAMPLE_PORT_KEY,
            CONF_NAME: "Custom Name",
            CONF_MAXHOURS: 12,
        }
        result = await flow_with_ports.async_step_select_port(user_input)

        assert result["type"] == "create_entry"
        assert result["title"] == "Custom Name"
        assert result["data"][CONF_PROVIDER] == DEFAULT_PROVIDER
        assert result["data"][CONF_LATITUDE] == 48.6493
        assert result["data"][CONF_LONGITUDE] == -2.0257
        assert result["data"][CONF_ID] == 123
        assert result["data"][CONF_MAXHOURS] == 12
        assert result["data"][CONF_NAME] == "Custom Name"

    @pytest.mark.asyncio
    async def test_uses_port_name_as_title_when_no_name_provided(self, flow_with_ports):
        """When CONF_NAME is omitted, the selected port key becomes the title."""
        user_input = {
            CONF_PORT_SELECT: SAMPLE_PORT_KEY,
            CONF_MAXHOURS: 6,
        }
        result = await flow_with_ports.async_step_select_port(user_input)

        assert result["title"] == SAMPLE_PORT_KEY
        assert result["data"][CONF_NAME] == SAMPLE_PORT_KEY

    @pytest.mark.asyncio
    async def test_unique_id_set_from_provider_lat_lon(self, flow_with_ports):
        """Unique ID is formed from provider, lat, and lon."""
        user_input = {
            CONF_PORT_SELECT: SAMPLE_PORT_KEY,
            CONF_MAXHOURS: 6,
        }
        await flow_with_ports.async_step_select_port(user_input)

        expected_unique_id = f"{DEFAULT_PROVIDER}-48.6493--2.0257"
        assert flow_with_ports.unique_id == expected_unique_id

    @pytest.mark.asyncio
    async def test_aborts_if_unique_id_already_configured(self, flow_with_ports):
        """Flow aborts when the unique ID matches an existing entry."""
        from homeassistant.data_entry_flow import AbortFlow

        # Make _abort_if_unique_id_configured raise an abort (simulating duplicate)
        flow_with_ports._abort_if_unique_id_configured = MagicMock(
            side_effect=AbortFlow("already_configured")
        )

        user_input = {
            CONF_PORT_SELECT: SAMPLE_PORT_KEY,
            CONF_MAXHOURS: 6,
        }
        with pytest.raises(AbortFlow):
            await flow_with_ports.async_step_select_port(user_input)

    @pytest.mark.asyncio
    async def test_select_port_with_default_maxhours(self, flow_with_ports):
        """Default maxhours value (6) is used when not explicitly provided."""
        user_input = {
            CONF_PORT_SELECT: SAMPLE_PORT_KEY,
            CONF_MAXHOURS: 6,
        }
        result = await flow_with_ports.async_step_select_port(user_input)

        assert result["data"][CONF_MAXHOURS] == 6

    @pytest.mark.asyncio
    async def test_select_port_optional_name_not_provided(self, flow_with_ports):
        """When name is not in input, port key is used."""
        user_input = {
            CONF_PORT_SELECT: SAMPLE_PORT_KEY,
            CONF_MAXHOURS: 8,
        }
        result = await flow_with_ports.async_step_select_port(user_input)

        # get(CONF_NAME, selected_port_name) => selected_port_name
        assert result["data"][CONF_NAME] == SAMPLE_PORT_KEY

    @pytest.mark.asyncio
    async def test_select_port_schema_includes_available_ports(self, flow_with_ports):
        """The form schema lists all available port keys."""
        result = await flow_with_ports.async_step_select_port(None)

        assert result["type"] == "form"
        assert result["step_id"] == "select_port"


# ---------------------------------------------------------------------------
# async_get_options_flow
# ---------------------------------------------------------------------------
class TestAsyncGetOptionsFlow:
    """Tests for the static options flow factory."""

    def test_returns_options_flow_handler(self):
        """async_get_options_flow returns an OptionsFlowHandler instance."""
        handler = ApiMareeInfoConfigFlow.async_get_options_flow(MagicMock())
        assert isinstance(handler, OptionsFlowHandler)


# ---------------------------------------------------------------------------
# OptionsFlowHandler
# ---------------------------------------------------------------------------
class TestOptionsFlowHandler:
    """Tests for the OptionsFlowHandler."""

    @pytest.fixture
    def handler(self):
        """Return an OptionsFlowHandler with mock config_entry."""
        h = OptionsFlowHandler()
        entry = MagicMock()
        entry.options = {CONF_MAXHOURS: 6}
        entry.data = {CONF_MAXHOURS: 6}
        h.config_entry = entry
        return h

    @pytest.mark.asyncio
    async def test_shows_form_when_no_input(self, handler):
        """Form is returned when user_input is None."""
        result = await handler.async_step_init(None)

        assert result["type"] == "form"
        assert result["step_id"] == "init"

    @pytest.mark.asyncio
    async def test_form_defaults_to_options_value(self, handler):
        """Default value comes from config_entry.options[CONF_MAXHOURS]."""
        handler.config_entry.options = {CONF_MAXHOURS: 12}

        result = await handler.async_step_init(None)

        assert result["type"] == "form"
        assert result["step_id"] == "init"

    @pytest.mark.asyncio
    async def test_form_falls_back_to_data_when_no_options(self, handler):
        """When options is empty, default falls back to config_entry.data."""
        handler.config_entry.options = {}
        handler.config_entry.data = {CONF_MAXHOURS: 10}

        result = await handler.async_step_init(None)

        assert result["type"] == "form"
        assert result["step_id"] == "init"

    @pytest.mark.asyncio
    async def test_form_defaults_to_six_when_neither_present(self, handler):
        """When neither options nor data has MAXHOURS, default is 6."""
        handler.config_entry.options = {}
        handler.config_entry.data = {}

        result = await handler.async_step_init(None)

        assert result["type"] == "form"
        assert result["step_id"] == "init"

    @pytest.mark.asyncio
    async def test_creates_entry_on_submit(self, handler):
        """Submitting the form creates an entry with the new data."""
        result = await handler.async_step_init({CONF_MAXHOURS: 24})

        assert result["type"] == "create_entry"
        assert result["data"] == {CONF_MAXHOURS: 24}

    @pytest.mark.asyncio
    async def test_submit_preserves_all_user_input_keys(self, handler):
        """All keys from user_input are passed to the entry data."""
        user_input = {CONF_MAXHOURS: 3}
        result = await handler.async_step_init(user_input)

        assert result["data"] == user_input

    @pytest.mark.asyncio
    async def test_submit_with_zero_maxhours(self, handler):
        """Zero is accepted as a valid maxhours value."""
        result = await handler.async_step_init({CONF_MAXHOURS: 0})

        assert result["type"] == "create_entry"
        assert result["data"][CONF_MAXHOURS] == 0

    @pytest.mark.asyncio
    async def test_submit_with_large_maxhours(self, handler):
        """Large values are accepted."""
        result = await handler.async_step_init({CONF_MAXHOURS: 9999})

        assert result["type"] == "create_entry"
        assert result["data"][CONF_MAXHOURS] == 9999


# ---------------------------------------------------------------------------
# Integration-style: full two-step config flow
# ---------------------------------------------------------------------------
class TestFullConfigFlow:
    """End-to-end test: user step -> select_port step -> entry created."""

    @pytest.mark.asyncio
    async def test_full_flow_creates_entry(self, mock_hass):
        """Walk through the entire config flow from start to entry creation."""
        flow = ApiMareeInfoConfigFlow()
        flow.hass = mock_hass
        flow.context = {}

        mock_api = MagicMock()
        mock_api.getlisteport = AsyncMock(return_value=SAMPLE_PORTS_RESPONSE)

        with patch(
            "custom_components.apiMareeInfo.config_flow.ListePorts",
            return_value=mock_api,
        ), patch(
            "custom_components.apiMareeInfo.config_flow.async_get_clientsession",
        ):
            # Step 1: user searches for a port
            result1 = await flow.async_step_user({CONF_PORT_SEARCH: "Saint"})
            assert result1["type"] == "form"
            assert result1["step_id"] == "select_port"

            # Step 2: user selects a port and submits
            result2 = await flow.async_step_select_port(
                {
                    CONF_PORT_SELECT: SAMPLE_PORT_KEY,
                    CONF_NAME: "Saint-Malo Port",
                    CONF_MAXHOURS: 8,
                }
            )

        assert result2["type"] == "create_entry"
        assert result2["title"] == "Saint-Malo Port"
        assert result2["data"][CONF_LATITUDE] == 48.6493
        assert result2["data"][CONF_LONGITUDE] == -2.0257
        assert result2["data"][CONF_MAXHOURS] == 8
        assert result2["data"][CONF_PROVIDER] == DEFAULT_PROVIDER

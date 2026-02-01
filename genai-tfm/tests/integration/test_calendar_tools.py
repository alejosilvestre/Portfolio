"""
===========================================================
TEST CALENDAR TOOLS - Tests para backend/calendar_tools.py
===========================================================

Tests de integración para las herramientas de calendario.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import os


class TestIsCalendarConfigured:
    """Tests para is_calendar_configured."""

    @patch("backend.calendar_tools.os.path.exists")
    @patch("backend.calendar_tools.Credentials")
    def test_is_calendar_configured_with_valid_token(self, mock_credentials, mock_exists):
        """Verifica configuración con token válido."""
        mock_exists.return_value = True
        mock_creds = Mock()
        mock_creds.valid = True
        mock_credentials.from_authorized_user_file.return_value = mock_creds

        from backend.calendar_tools import is_calendar_configured

        result = is_calendar_configured()

        assert result is True

    @patch("backend.calendar_tools.os.path.exists")
    @patch("backend.calendar_tools.Credentials")
    @patch("backend.calendar_tools.Request")
    def test_is_calendar_configured_refreshes_expired_token(
        self, mock_request, mock_credentials, mock_exists
    ):
        """Verifica refresh de token expirado."""
        mock_exists.return_value = True
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token"
        mock_creds.to_json.return_value = "{}"
        mock_credentials.from_authorized_user_file.return_value = mock_creds

        mock_file = MagicMock()
        with patch("builtins.open", MagicMock(return_value=mock_file)):
            from backend.calendar_tools import is_calendar_configured

            result = is_calendar_configured()

            assert result is True
            mock_creds.refresh.assert_called_once()

    @patch("backend.calendar_tools.os.path.exists")
    @patch("backend.calendar_tools.InstalledAppFlow")
    @patch("backend.calendar_tools.GOOGLE_CREDENTIALS", "credentials.json")
    def test_is_calendar_configured_runs_oauth_flow(self, mock_flow, mock_exists):
        """Verifica que ejecuta OAuth flow cuando no hay token."""
        mock_exists.return_value = False
        mock_creds = Mock()
        mock_creds.to_json.return_value = "{}"
        mock_flow.from_client_secrets_file.return_value.run_local_server.return_value = mock_creds

        mock_file = MagicMock()
        with patch("builtins.open", MagicMock(return_value=mock_file)):
            from backend.calendar_tools import is_calendar_configured

            result = is_calendar_configured()

            assert result is True


class TestInitCalendar:
    """Tests para init_calendar."""

    @patch("backend.calendar_tools.is_calendar_configured")
    @patch("backend.calendar_tools.CalendarToolkit")
    def test_init_calendar_returns_tools(self, mock_toolkit, mock_is_configured):
        """Verifica que retorna herramientas del calendario."""
        # Reset del estado de inicialización
        import backend.calendar_tools as cal_module
        cal_module._initialized = False
        cal_module._calendar_tools = []

        mock_is_configured.return_value = True
        mock_tools = [Mock(name="create_event"), Mock(name="get_events")]
        mock_toolkit.return_value.get_tools.return_value = mock_tools

        from backend.calendar_tools import init_calendar

        result = init_calendar()

        assert len(result) == 2
        assert cal_module._initialized is True

    @patch("backend.calendar_tools.is_calendar_configured")
    def test_init_calendar_returns_empty_when_not_configured(self, mock_is_configured):
        """Verifica que retorna lista vacía si no está configurado."""
        import backend.calendar_tools as cal_module
        cal_module._initialized = False
        cal_module._calendar_tools = []

        mock_is_configured.return_value = False

        from backend.calendar_tools import init_calendar

        result = init_calendar()

        assert result == []
        assert cal_module._initialized is True

    @patch("backend.calendar_tools.is_calendar_configured")
    @patch("backend.calendar_tools.CalendarToolkit")
    def test_init_calendar_caches_tools(self, mock_toolkit, mock_is_configured):
        """Verifica que cachea las herramientas."""
        import backend.calendar_tools as cal_module
        cal_module._initialized = False
        cal_module._calendar_tools = []

        mock_is_configured.return_value = True
        mock_tools = [Mock(name="tool1")]
        mock_toolkit.return_value.get_tools.return_value = mock_tools

        from backend.calendar_tools import init_calendar

        # Primera llamada
        result1 = init_calendar()

        # Segunda llamada - debería usar caché
        result2 = init_calendar()

        # CalendarToolkit solo debería instanciarse una vez
        assert mock_toolkit.call_count == 1
        assert result1 == result2

    @patch("backend.calendar_tools.is_calendar_configured")
    @patch("backend.calendar_tools.CalendarToolkit")
    def test_init_calendar_handles_import_error(self, mock_toolkit, mock_is_configured):
        """Verifica manejo de ImportError."""
        import backend.calendar_tools as cal_module
        cal_module._initialized = False
        cal_module._calendar_tools = []

        mock_is_configured.return_value = True
        mock_toolkit.side_effect = ImportError("langchain-google-community not installed")

        from backend.calendar_tools import init_calendar

        result = init_calendar()

        assert result == []

    @patch("backend.calendar_tools.is_calendar_configured")
    @patch("backend.calendar_tools.CalendarToolkit")
    def test_init_calendar_handles_exception(self, mock_toolkit, mock_is_configured):
        """Verifica manejo de excepciones generales."""
        import backend.calendar_tools as cal_module
        cal_module._initialized = False
        cal_module._calendar_tools = []

        mock_is_configured.return_value = True
        mock_toolkit.side_effect = Exception("Error inesperado")

        from backend.calendar_tools import init_calendar

        result = init_calendar()

        assert result == []


class TestGetCalendarTools:
    """Tests para get_calendar_tools."""

    @patch("backend.calendar_tools.init_calendar")
    def test_get_calendar_tools_initializes_if_needed(self, mock_init):
        """Verifica que inicializa si es necesario."""
        import backend.calendar_tools as cal_module
        cal_module._initialized = False
        cal_module._calendar_tools = []

        mock_init.return_value = [Mock(name="tool1")]

        from backend.calendar_tools import get_calendar_tools

        result = get_calendar_tools()

        mock_init.assert_called_once()

    def test_get_calendar_tools_returns_cached(self):
        """Verifica que retorna herramientas cacheadas."""
        import backend.calendar_tools as cal_module

        mock_tools = [Mock(name="cached_tool")]
        cal_module._initialized = True
        cal_module._calendar_tools = mock_tools

        from backend.calendar_tools import get_calendar_tools

        result = get_calendar_tools()

        assert result == mock_tools


class TestCalendarToolsScopes:
    """Tests para los scopes de Google Calendar."""

    def test_scopes_are_defined(self):
        """Verifica que los scopes están definidos."""
        from backend.calendar_tools import SCOPES

        assert len(SCOPES) > 0
        assert any("calendar" in scope for scope in SCOPES)

    def test_scopes_include_readonly(self):
        """Verifica que incluye scope de solo lectura."""
        from backend.calendar_tools import SCOPES

        assert "https://www.googleapis.com/auth/calendar.readonly" in SCOPES

    def test_scopes_include_events(self):
        """Verifica que incluye scope de eventos."""
        from backend.calendar_tools import SCOPES

        assert "https://www.googleapis.com/auth/calendar.events.owned" in SCOPES

    def test_scopes_include_freebusy(self):
        """Verifica que incluye scope de free/busy."""
        from backend.calendar_tools import SCOPES

        assert "https://www.googleapis.com/auth/calendar.freebusy" in SCOPES

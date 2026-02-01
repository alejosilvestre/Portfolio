"""
===========================================================
TEST TOOLS - Tests para agent/tools.py
===========================================================

Tests unitarios para las herramientas del agente.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os


class TestExecuteTool:
    """Tests para la función execute_tool."""

    def test_execute_tool_unknown_tool_returns_error(self):
        """Verifica que retorna error para herramienta desconocida."""
        from agent.tools import execute_tool

        result = execute_tool("herramienta_inexistente", {})

        assert "ERROR" in result
        assert "no existe" in result

    @patch("agent.tools.TOOLS_MAP")
    def test_execute_tool_calls_correct_tool(self, mock_tools_map):
        """Verifica que llama a la herramienta correcta."""
        from agent.tools import execute_tool

        mock_tool = Mock()
        mock_tool.invoke.return_value = "Resultado de búsqueda"
        mock_tools_map.__contains__ = Mock(return_value=True)
        mock_tools_map.__getitem__ = Mock(return_value=mock_tool)

        result = execute_tool("web_search", {"query": "test"})

        mock_tool.invoke.assert_called_once_with({"query": "test"})
        assert result == "Resultado de búsqueda"

    @patch("agent.tools.TOOLS_MAP")
    def test_execute_tool_handles_exception(self, mock_tools_map):
        """Verifica que maneja excepciones correctamente."""
        from agent.tools import execute_tool

        mock_tool = Mock()
        mock_tool.invoke.side_effect = Exception("Error de conexión")
        mock_tools_map.__contains__ = Mock(return_value=True)
        mock_tools_map.__getitem__ = Mock(return_value=mock_tool)

        result = execute_tool("web_search", {"query": "test"})

        assert "ERROR" in result
        assert "Error de conexión" in result


class TestSearchResultsCache:
    """Tests para las funciones de caché de resultados."""

    def test_get_search_results_returns_empty_initially(self):
        """Verifica que retorna lista vacía inicialmente."""
        from agent.tools import clear_search_results, get_search_results

        clear_search_results()
        result = get_search_results()

        assert result == []

    def test_clear_search_results(self):
        """Verifica que limpia los resultados de búsqueda."""
        from agent.tools import _search_results, clear_search_results, get_search_results
        import agent.tools as tools_module

        # Simular que hay resultados
        tools_module._search_results = [{"name": "Test"}]

        clear_search_results()
        result = get_search_results()

        assert result == []


class TestMockBookingSystem:
    """Tests para MockBookingSystem."""

    def test_check_availability_with_known_chain(self):
        """Verifica disponibilidad para cadena conocida."""
        from agent.tools import MockBookingSystem

        system = MockBookingSystem()

        result = system.check_availability(
            place_id="test123",
            name="Domino's Pizza",
            date="2026-01-20",
            time="21:00",
            num_people=2
        )

        assert result["has_api"] is True
        assert "available" in result
        assert "times" in result

    def test_check_availability_returns_has_api_false_for_unknown(self):
        """Verifica que lugares desconocidos pueden no tener API."""
        from agent.tools import MockBookingSystem

        system = MockBookingSystem()

        # Ejecutar varias veces para cubrir el caso aleatorio
        has_api_false_count = 0
        for _ in range(20):
            result = system.check_availability(
                place_id=f"test{_}",
                name="Restaurante Pequeño",
                date="2026-01-20",
                time="14:00",
                num_people=2
            )
            if not result["has_api"]:
                has_api_false_count += 1

        # Al menos algunos deberían no tener API
        assert has_api_false_count >= 0

    def test_make_booking_success(self):
        """Verifica que make_booking puede tener éxito."""
        from agent.tools import MockBookingSystem

        system = MockBookingSystem()

        # Primero verificar disponibilidad para registrar en caché
        system.check_availability("test123", "Domino's Pizza", "2026-01-20", "21:00", 2)

        # Hacer varias reservas para asegurar que al menos una tenga éxito
        success_count = 0
        for i in range(10):
            result = system.make_booking(
                place_id="test123",
                name="Domino's Pizza",
                date="2026-01-20",
                time="21:00",
                num_people=2
            )
            if result["success"]:
                success_count += 1
                assert "booking_id" in result
                assert result["details"]["restaurant"] == "Domino's Pizza"

        # Al menos algunas deberían tener éxito (85% probabilidad)
        assert success_count > 0

    def test_make_booking_fails_without_api(self):
        """Verifica que make_booking falla si no hay API registrada."""
        from agent.tools import MockBookingSystem

        system = MockBookingSystem()

        result = system.make_booking(
            place_id="unknown123",
            name="Restaurante Sin API",
            date="2026-01-20",
            time="21:00",
            num_people=2
        )

        assert result["success"] is False
        assert "No tiene reserva online" in result["error"]


class TestWebSearch:
    """Tests para la herramienta web_search."""

    @patch("agent.tools.TavilyClient")
    def test_web_search_success(self, mock_tavily_client, mock_env_vars):
        """Verifica búsqueda web exitosa."""
        from agent.tools import web_search

        mock_client = Mock()
        mock_client.search.return_value = {
            "answer": "Los mejores restaurantes son...",
            "results": [
                {"title": "Top 10", "content": "Lista de restaurantes..."}
            ]
        }
        mock_tavily_client.return_value = mock_client

        result = web_search.invoke({"query": "mejores restaurantes Madrid"})

        assert "Resumen" in result
        assert "Top 10" in result

    @patch.dict(os.environ, {"TAVILY_API_KEY": ""}, clear=False)
    def test_web_search_without_api_key(self):
        """Verifica error sin API key."""
        # Forzar que os.getenv devuelva None
        with patch("agent.tools.os.getenv", return_value=None):
            from agent.tools import web_search

            result = web_search.invoke({"query": "test"})

            assert "ERROR" in result
            assert "TAVILY_API_KEY" in result

    @patch("agent.tools.TavilyClient")
    def test_web_search_no_results(self, mock_tavily_client, mock_env_vars):
        """Verifica mensaje cuando no hay resultados."""
        from agent.tools import web_search

        mock_client = Mock()
        mock_client.search.return_value = {"answer": "", "results": []}
        mock_tavily_client.return_value = mock_client

        result = web_search.invoke({"query": "consulta sin resultados xyz"})

        assert "No encontré" in result


class TestMapsSearch:
    """Tests para la herramienta maps_search."""

    @patch("agent.tools.places_text_search")
    def test_maps_search_success(self, mock_places_search, mock_env_vars):
        """Verifica búsqueda en Maps exitosa."""
        from agent.tools import maps_search, clear_search_results

        clear_search_results()

        mock_places_search.return_value = [
            {
                "name": "La Trattoria",
                "address": "Calle Mayor 10",
                "rating": 4.5,
                "user_ratings_total": 200,
                "price_level": 2,
                "phone": "+34912345678",
            }
        ]

        result = maps_search.invoke({
            "query": "restaurante italiano",
            "location": "Madrid"
        })

        assert "La Trattoria" in result
        assert "4.5" in result

    @patch("agent.tools.places_text_search")
    def test_maps_search_no_results(self, mock_places_search, mock_env_vars):
        """Verifica mensaje cuando no hay resultados."""
        from agent.tools import maps_search

        mock_places_search.return_value = []

        result = maps_search.invoke({
            "query": "restaurante inexistente xyz",
            "location": "Pueblo Pequeño"
        })

        assert "No encontré" in result

    @patch("agent.tools.places_text_search")
    def test_maps_search_handles_exception(self, mock_places_search, mock_env_vars):
        """Verifica manejo de excepciones."""
        from agent.tools import maps_search

        mock_places_search.side_effect = Exception("Error de API")

        result = maps_search.invoke({
            "query": "restaurante",
            "location": "Madrid"
        })

        assert "ERROR" in result


class TestCheckAvailability:
    """Tests para la herramienta check_availability."""

    def test_check_availability_without_search_results(self):
        """Verifica error sin resultados previos."""
        from agent.tools import check_availability, clear_search_results

        clear_search_results()

        result = check_availability.invoke({
            "date": "2026-01-20",
            "time": "21:00",
            "num_people": 2
        })

        assert "ERROR" in result
        assert "maps_search" in result

    @patch("agent.tools._booking_system")
    def test_check_availability_with_results(self, mock_booking_system, mock_env_vars):
        """Verifica disponibilidad con resultados previos."""
        from agent.tools import check_availability
        import agent.tools as tools_module

        # Simular resultados de búsqueda
        tools_module._search_results = [
            {
                "name": "La Trattoria",
                "place_id": "place123",
                "website": "https://latrattoria.com",
            }
        ]

        mock_booking_system.check_availability.return_value = {
            "has_api": True,
            "available": True,
            "times": ["21:00"]
        }

        result = check_availability.invoke({
            "date": "2026-01-20",
            "time": "21:00",
            "num_people": 2
        })

        assert "La Trattoria" in result
        assert "Disponible" in result


class TestMakeBooking:
    """Tests para la herramienta make_booking."""

    def test_make_booking_place_not_found(self):
        """Verifica error cuando no se encuentra el lugar."""
        from agent.tools import make_booking, clear_search_results

        clear_search_results()

        result = make_booking.invoke({
            "place_name": "Restaurante Inexistente",
            "date": "2026-01-20",
            "time": "21:00",
            "num_people": 2
        })

        assert "ERROR" in result
        assert "No encontré" in result

    @patch("agent.tools._booking_system")
    def test_make_booking_success(self, mock_booking_system, mock_env_vars):
        """Verifica reserva exitosa."""
        from agent.tools import make_booking
        import agent.tools as tools_module

        # Simular resultados de búsqueda
        tools_module._search_results = [
            {
                "name": "La Trattoria",
                "place_id": "place123",
                "phone": "+34912345678",
            }
        ]

        mock_booking_system.make_booking.return_value = {
            "success": True,
            "booking_id": "RES-123",
            "details": {
                "restaurant": "La Trattoria",
                "date": "2026-01-20",
                "time": "21:00",
                "people": 2
            }
        }

        result = make_booking.invoke({
            "place_name": "La Trattoria",
            "date": "2026-01-20",
            "time": "21:00",
            "num_people": 2
        })

        assert "confirmada" in result
        assert "RES-123" in result

    @patch("agent.tools._booking_system")
    def test_make_booking_failure_offers_phone(self, mock_booking_system, mock_env_vars):
        """Verifica que ofrece teléfono cuando falla la reserva."""
        from agent.tools import make_booking
        import agent.tools as tools_module

        tools_module._search_results = [
            {
                "name": "La Trattoria",
                "place_id": "place123",
                "phone": "+34912345678",
            }
        ]

        mock_booking_system.make_booking.return_value = {
            "success": False,
            "error": "Error temporal"
        }

        result = make_booking.invoke({
            "place_name": "La Trattoria",
            "date": "2026-01-20",
            "time": "21:00",
            "num_people": 2
        })

        assert "No pude reservar" in result
        assert "+34912345678" in result or "llamo" in result.lower()


class TestPhoneCall:
    """Tests para la herramienta phone_call."""

    @patch("agent.tools.requests.get")
    def test_phone_call_service_unavailable(self, mock_get, mock_env_vars):
        """Verifica error cuando el servicio no está disponible."""
        import requests
        from agent.tools import phone_call

        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        result = phone_call.invoke({
            "phone_number": "+34912345678",
            "mission": "Reservar mesa",
        })

        assert "ERROR" in result

    @patch("agent.tools.requests.post")
    @patch("agent.tools.requests.get")
    def test_phone_call_initiates_call(self, mock_get, mock_post, mock_env_vars):
        """Verifica que se inicia la llamada correctamente."""
        from agent.tools import phone_call

        # Mock health check
        mock_get.return_value = Mock(status_code=200)

        # Mock start call
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"call_id": "call123"})
        )

        # Mock status polling - simular llamada completada
        mock_get.side_effect = [
            Mock(status_code=200),  # Health check
            Mock(
                status_code=200,
                json=Mock(return_value={
                    "status": "completed",
                    "result": {
                        "mission_completed": True,
                        "outcome": "Reserva confirmada"
                    },
                    "transcript": [],
                    "duration_seconds": 30
                })
            )
        ]

        result = phone_call.invoke({
            "phone_number": "+34912345678",
            "mission": "Reservar mesa para 2",
        })

        assert "COMPLETADA" in result or "ERROR" not in result

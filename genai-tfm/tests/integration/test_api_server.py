"""
===========================================================
TEST API SERVER - Tests para FastAPI/api_server.py
===========================================================

Tests de integración para el servidor FastAPI.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from fastapi.testclient import TestClient
import os


@pytest.fixture
def api_client(mock_env_vars):
    """Cliente de test para FastAPI."""
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "test-key",
        "GOOGLE_MAPS_API_KEY": "test-key",
        "TAVILY_API_KEY": "test-key",
    }):
        with patch("FastAPI.api_server.run_agent") as mock_agent:
            mock_agent.return_value = {
                "response": "Test response",
                "messages": [],
                "knowledge": {}
            }
            from FastAPI.api_server import app
            yield TestClient(app)


class TestHealthEndpoint:
    """Tests para el endpoint de health check."""

    def test_health_returns_ok(self, api_client):
        """Verifica que /health retorna ok."""
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_root_returns_service_info(self, api_client):
        """Verifica que / retorna información del servicio."""
        response = api_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "ReserveHub" in data["service"]
        assert "version" in data
        assert data["status"] == "running"


class TestReservationRequestEndpoint:
    """Tests para el endpoint de reservation-requests."""

    def test_reservation_request_valid_input(self, mock_env_vars):
        """Verifica request válido."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            with patch("FastAPI.api_server.run_agent") as mock_agent:
                mock_agent.return_value = {
                    "response": "He encontrado varios restaurantes",
                    "messages": [],
                    "knowledge": {
                        "places": [{"name": "La Trattoria", "rating": 4.5}]
                    }
                }
                from FastAPI.api_server import app
                client = TestClient(app)

                response = client.post(
                    "/api/reservation-requests",
                    json={
                        "session_id": "test-123",
                        "user_id": "user-1",
                        "messages": [
                            {"role": "user", "content": "Busco restaurante italiano"}
                        ]
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert "restaurantes" in data["message"] or "encontrado" in data["message"]
                assert data["restaurants"] is not None

    def test_reservation_request_empty_messages(self, mock_env_vars):
        """Verifica request con mensajes vacíos."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            with patch("FastAPI.api_server.run_agent") as mock_agent:
                mock_agent.return_value = {
                    "response": "¿En qué puedo ayudarte?",
                    "messages": [],
                    "knowledge": {}
                }
                from FastAPI.api_server import app
                client = TestClient(app)

                response = client.post(
                    "/api/reservation-requests",
                    json={
                        "messages": []
                    }
                )

                assert response.status_code == 200

    def test_reservation_request_generates_session_id(self, mock_env_vars):
        """Verifica que se genera session_id si no se proporciona."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            with patch("FastAPI.api_server.run_agent") as mock_agent:
                mock_agent.return_value = {
                    "response": "Test",
                    "messages": [],
                    "knowledge": {}
                }
                from FastAPI.api_server import app
                client = TestClient(app)

                response = client.post(
                    "/api/reservation-requests",
                    json={
                        "messages": [{"role": "user", "content": "Hola"}]
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["session_id"] is not None
                assert "session_" in data["session_id"]


class TestExtractRestaurantsFromKnowledge:
    """Tests para extract_restaurants_from_knowledge."""

    def test_extract_restaurants_with_places(self):
        """Verifica extracción con lugares."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            from FastAPI.api_server import extract_restaurants_from_knowledge

            knowledge = {
                "places": [
                    {
                        "name": "La Trattoria",
                        "address": "Calle Mayor 10",
                        "rating": 4.5,
                        "phone": "+34912345678",
                        "available": True,
                    },
                    {
                        "name": "Pizzería Milano",
                        "address": "Gran Vía 20",
                        "rating": 4.2,
                        "phone": "+34987654321",
                        "available": False,
                        "available_times": ["20:30", "21:00"]
                    }
                ]
            }

            result = extract_restaurants_from_knowledge(knowledge)

            assert len(result) == 2
            assert result[0]["name"] == "La Trattoria"
            assert result[0]["available"] is True
            assert result[1]["available_times"] == ["20:30", "21:00"]

    def test_extract_restaurants_empty_knowledge(self):
        """Verifica extracción con knowledge vacío."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            from FastAPI.api_server import extract_restaurants_from_knowledge

            result = extract_restaurants_from_knowledge({})

            assert result == []

    def test_extract_restaurants_no_places(self):
        """Verifica extracción sin places en knowledge."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            from FastAPI.api_server import extract_restaurants_from_knowledge

            knowledge = {"web_search": {"query": "test"}}

            result = extract_restaurants_from_knowledge(knowledge)

            assert result == []


class TestDetermineStatus:
    """Tests para determine_status."""

    def test_determine_status_completed_with_booking(self):
        """Verifica status completed con reserva."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            from FastAPI.api_server import determine_status

            knowledge = {"booking": {"place_name": "La Trattoria"}}

            result = determine_status("Tu reserva está confirmada", knowledge)

            assert result == "completed"

    def test_determine_status_success_with_places(self):
        """Verifica status success con lugares."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            from FastAPI.api_server import determine_status

            knowledge = {"places": [{"name": "Test"}]}

            result = determine_status("He encontrado restaurantes", knowledge)

            assert result == "success"

    def test_determine_status_needs_input_with_question(self):
        """Verifica status needs_input con pregunta."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            from FastAPI.api_server import determine_status

            result = determine_status("¿Dónde te gustaría comer?", {})

            assert result == "needs_input"

    def test_determine_status_needs_input_with_keywords(self):
        """Verifica status needs_input con keywords de pregunta."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            from FastAPI.api_server import determine_status

            result = determine_status("¿Cuántos sois para la cena?", {})

            assert result == "needs_input"


class TestContinueConversationEndpoint:
    """Tests para el endpoint /api/agent/continue."""

    def test_continue_conversation_is_alias(self, mock_env_vars):
        """Verifica que es un alias de reservation-requests."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            with patch("FastAPI.api_server.run_agent") as mock_agent:
                mock_agent.return_value = {
                    "response": "Test",
                    "messages": [],
                    "knowledge": {}
                }
                from FastAPI.api_server import app
                client = TestClient(app)

                response = client.post(
                    "/api/agent/continue",
                    json={
                        "messages": [{"role": "user", "content": "Hola"}]
                    }
                )

                assert response.status_code == 200


class TestPhotoEndpoint:
    """Tests para el endpoint de fotos."""

    def test_photo_endpoint_missing_api_key(self, mock_env_vars, monkeypatch):
        """Verifica error cuando falta API key."""
        monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)

        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "",
            "TAVILY_API_KEY": "test-key",
        }):
            from FastAPI.api_server import app
            client = TestClient(app)

            response = client.get("/api/photo/places/test/photos/photo123")

            assert response.status_code == 500

    @patch("FastAPI.api_server.requests.get")
    def test_photo_endpoint_success(self, mock_get, mock_env_vars):
        """Verifica obtención de foto exitosa."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"fake_image_data"
        mock_response.headers = {"Content-Type": "image/jpeg"}
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            from FastAPI.api_server import app
            client = TestClient(app)

            response = client.get("/api/photo/places/test/photos/photo123")

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/jpeg"

    @patch("FastAPI.api_server.requests.get")
    def test_photo_endpoint_google_error(self, mock_get, mock_env_vars):
        """Verifica manejo de error de Google."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Photo not found"
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            from FastAPI.api_server import app
            client = TestClient(app, raise_server_exceptions=False)

            response = client.get("/api/photo/places/test/photos/invalid")

            # El endpoint propaga el status code de Google (404) o 500 si hay error interno
            assert response.status_code in [404, 500]
            assert response.status_code != 200

    @patch("FastAPI.api_server.requests.get")
    def test_photo_endpoint_timeout(self, mock_get, mock_env_vars):
        """Verifica manejo de timeout."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout()

        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            from FastAPI.api_server import app
            client = TestClient(app)

            response = client.get("/api/photo/places/test/photos/photo123")

            assert response.status_code == 504


class TestAgentErrorHandling:
    """Tests para manejo de errores del agente."""

    def test_agent_exception_returns_error_status(self, mock_env_vars):
        """Verifica que excepciones del agente retornan error."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GOOGLE_MAPS_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
        }):
            with patch("FastAPI.api_server.run_agent") as mock_agent:
                mock_agent.side_effect = Exception("Error del agente")
                from FastAPI.api_server import app
                client = TestClient(app)

                response = client.post(
                    "/api/reservation-requests",
                    json={
                        "messages": [{"role": "user", "content": "Test"}]
                    }
                )

                assert response.status_code == 200  # La API maneja el error
                data = response.json()
                assert data["status"] == "error"
                assert "Error" in data["message"]

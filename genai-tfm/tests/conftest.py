"""
===========================================================
CONFTEST - Fixtures compartidos para todos los tests
===========================================================

Contiene fixtures reutilizables para mocking de APIs externas,
estado del agente, y configuración de tests.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ===========================================================
# FIXTURES DE CONFIGURACIÓN
# ===========================================================

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Configura variables de entorno para tests."""
    env_vars = {
        "OPENAI_API_KEY": "test-openai-key",
        "GOOGLE_MAPS_API_KEY": "test-google-maps-key",
        "TAVILY_API_KEY": "test-tavily-key",
        "TWILIO_ACCOUNT_SID": "test-twilio-sid",
        "TWILIO_AUTH_TOKEN": "test-twilio-token",
        "FROM_TWILIO_PHONE_NUMBER": "+34600000000",
        "TO_PHONE_NUMBER": "+34611111111",
        "ELEVENLABS_API_KEY": "test-elevenlabs-key",
        "ELEVENLABS_VOICE_ID": "test-voice-id",
        "NGROK_AUTH_TOKEN": "test-ngrok-token",
        "CALL_SERVICE_PORT": "8080",
        "MODEL_NAME": "gpt-4o-mini",
        "TEMPERATURE": "0.3",
        "LANGSMITH_TRACING": "false",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.fixture
def mock_config():
    """Retorna configuración mock para tests."""
    return {
        "OPENAI_API_KEY": "test-openai-key",
        "MODEL_NAME": "gpt-4o-mini",
        "TEMPERATURE": 0.3,
        "GOOGLE_MAPS_API_KEY": "test-google-maps-key",
        "TAVILY_API_KEY": "test-tavily-key",
        "LANGSMITH_API_KEY": "",
        "LANGSMITH_TRACING": False,
        "DATA_DIR": "/tmp/data",
    }


# ===========================================================
# FIXTURES DE ESTADO DEL AGENTE
# ===========================================================

@pytest.fixture
def empty_agent_state():
    """Estado inicial vacío del agente."""
    return {
        "messages": [],
        "knowledge": {},
        "next_tool": None,
        "tool_args": None,
        "last_observation": None,
        "status": "thinking",
        "iterations": 0
    }


@pytest.fixture
def agent_state_with_messages():
    """Estado del agente con mensajes de ejemplo."""
    from langchain_core.messages import HumanMessage, AIMessage
    return {
        "messages": [
            HumanMessage(content="Busco un restaurante italiano en Madrid"),
            AIMessage(content="Voy a buscar restaurantes italianos en Madrid."),
        ],
        "knowledge": {},
        "next_tool": None,
        "tool_args": None,
        "last_observation": None,
        "status": "thinking",
        "iterations": 1
    }


@pytest.fixture
def agent_state_with_places():
    """Estado del agente con lugares encontrados."""
    return {
        "messages": [],
        "knowledge": {
            "places": [
                {
                    "name": "La Trattoria",
                    "address": "Calle Mayor 10, Madrid",
                    "place_id": "place123",
                    "rating": 4.5,
                    "user_ratings_total": 200,
                    "phone": "+34912345678",
                    "website": "https://latrattoria.com",
                    "available": True,
                    "has_api": True,
                },
                {
                    "name": "Pizzería Milano",
                    "address": "Gran Vía 20, Madrid",
                    "place_id": "place456",
                    "rating": 4.2,
                    "user_ratings_total": 150,
                    "phone": "+34987654321",
                    "website": None,
                    "available": False,
                    "has_api": False,
                    "available_times": ["20:30", "21:00", "21:30"],
                },
            ]
        },
        "next_tool": None,
        "tool_args": None,
        "last_observation": None,
        "status": "thinking",
        "iterations": 2
    }


@pytest.fixture
def agent_state_with_booking():
    """Estado del agente con reserva confirmada."""
    return {
        "messages": [],
        "knowledge": {
            "places": [
                {
                    "name": "La Trattoria",
                    "address": "Calle Mayor 10, Madrid",
                    "place_id": "place123",
                    "rating": 4.5,
                }
            ],
            "booking": {
                "confirmed": True,
                "place_name": "La Trattoria",
                "date": "2026-01-20",
                "time": "21:00",
                "num_people": 2,
                "result_text": "Reserva confirmada",
            }
        },
        "next_tool": None,
        "tool_args": None,
        "last_observation": None,
        "status": "thinking",
        "iterations": 3
    }


# ===========================================================
# FIXTURES DE RESPUESTAS MOCK DE APIs
# ===========================================================

@pytest.fixture
def mock_places_response():
    """Respuesta mock de Google Places API."""
    return {
        "places": [
            {
                "id": "ChIJ123abc",
                "displayName": {"text": "Restaurante El Buen Sabor"},
                "formattedAddress": "Calle Principal 123, Madrid",
                "location": {"latitude": 40.4168, "longitude": -3.7038},
                "rating": 4.5,
                "userRatingCount": 250,
                "priceLevel": "PRICE_LEVEL_2",
                "types": ["restaurant", "food"],
                "nationalPhoneNumber": "912 345 678",
                "websiteUri": "https://elbuensabor.com",
                "regularOpeningHours": {
                    "openNow": True,
                    "weekdayDescriptions": [
                        "Monday: 12:00 PM - 11:00 PM",
                        "Tuesday: 12:00 PM - 11:00 PM",
                    ]
                },
                "photos": [{"name": "places/ChIJ123abc/photos/photo123"}]
            }
        ]
    }


@pytest.fixture
def mock_geocode_response():
    """Respuesta mock de Geocoding API."""
    return {
        "results": [
            {
                "geometry": {
                    "location": {
                        "lat": 40.4168,
                        "lng": -3.7038
                    }
                }
            }
        ],
        "status": "OK"
    }


@pytest.fixture
def mock_tavily_response():
    """Respuesta mock de Tavily Search API."""
    return {
        "answer": "Los mejores restaurantes italianos en Madrid incluyen...",
        "results": [
            {
                "title": "Top 10 Restaurantes Italianos",
                "content": "Una guía completa de los mejores restaurantes italianos...",
                "url": "https://example.com/restaurantes"
            }
        ]
    }


@pytest.fixture
def mock_openai_response():
    """Respuesta mock de OpenAI API."""
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content="THOUGHT: Voy a buscar restaurantes.\nACTION: maps_search\nACTION_INPUT: {\"query\": \"restaurante italiano\", \"location\": \"Madrid\"}"))
    ]
    return mock_response


@pytest.fixture
def mock_openai_respond_response():
    """Respuesta mock de OpenAI cuando debe responder."""
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content="THOUGHT: Ya tengo la información.\nACTION: respond\nACTION_INPUT: {\"message\": \"He encontrado varios restaurantes italianos en Madrid.\"}"))
    ]
    return mock_response


# ===========================================================
# FIXTURES DE TRANSCRIPCIONES
# ===========================================================

@pytest.fixture
def mock_call_transcript_success():
    """Transcripción mock de una llamada exitosa."""
    return [
        {"speaker": "self", "message": "Hola, buenas tardes. Quería hacer una reserva para mañana."},
        {"speaker": "other", "message": "Hola, claro. ¿Para cuántas personas?"},
        {"speaker": "self", "message": "Para 2 personas a las 21:00."},
        {"speaker": "other", "message": "Perfecto, tenemos mesa disponible. ¿A nombre de quién?"},
        {"speaker": "self", "message": "A nombre de Ana García."},
        {"speaker": "other", "message": "Anotado. Reserva confirmada para mañana a las 21:00 para 2 personas."},
        {"speaker": "self", "message": "Muchas gracias. Hasta mañana."},
    ]


@pytest.fixture
def mock_call_transcript_failed():
    """Transcripción mock de una llamada fallida."""
    return [
        {"speaker": "self", "message": "Hola, buenas tardes. Quería hacer una reserva para mañana."},
        {"speaker": "other", "message": "Lo siento, mañana estamos completos."},
        {"speaker": "self", "message": "¿Y pasado mañana?"},
        {"speaker": "other", "message": "También estamos llenos. Lo siento."},
    ]


# ===========================================================
# FIXTURES DE MOCKS PARA SERVICIOS EXTERNOS
# ===========================================================

@pytest.fixture
def mock_requests_get(monkeypatch):
    """Mock para requests.get."""
    mock = Mock()
    mock.return_value.status_code = 200
    mock.return_value.json.return_value = {}
    mock.return_value.raise_for_status = Mock()
    monkeypatch.setattr("requests.get", mock)
    return mock


@pytest.fixture
def mock_requests_post(monkeypatch):
    """Mock para requests.post."""
    mock = Mock()
    mock.return_value.status_code = 200
    mock.return_value.json.return_value = {}
    mock.return_value.raise_for_status = Mock()
    monkeypatch.setattr("requests.post", mock)
    return mock


@pytest.fixture
def mock_openai_client():
    """Mock del cliente OpenAI."""
    mock = Mock()
    mock.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Test response"))]
    )
    return mock


@pytest.fixture
def mock_twilio_client():
    """Mock del cliente Twilio."""
    mock = Mock()
    mock.calls.create.return_value = Mock(sid="CA123456789")
    mock.incoming_phone_numbers.list.return_value = [Mock(sid="PN123456789")]
    return mock


# ===========================================================
# FIXTURES PARA FASTAPI
# ===========================================================

@pytest.fixture
def test_client():
    """Cliente de test para FastAPI."""
    from fastapi.testclient import TestClient

    # Importamos después de configurar mocks
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "test-key",
        "GOOGLE_MAPS_API_KEY": "test-key",
        "TAVILY_API_KEY": "test-key",
    }):
        from FastAPI.api_server import app
        return TestClient(app)


# ===========================================================
# FIXTURES DE MENSAJES
# ===========================================================

@pytest.fixture
def sample_messages():
    """Mensajes de ejemplo para tests."""
    return [
        {"role": "user", "content": "Busco un restaurante italiano en Madrid"},
        {"role": "assistant", "content": "Voy a buscar restaurantes italianos en Madrid."},
        {"role": "user", "content": "Quiero reservar para 2 personas mañana a las 21:00"},
    ]


@pytest.fixture
def sample_agent_request():
    """Request de ejemplo para la API."""
    return {
        "session_id": "test-session-123",
        "user_id": "test-user",
        "messages": [
            {"role": "user", "content": "Busco un restaurante italiano en Madrid"}
        ],
        "session_context": {}
    }

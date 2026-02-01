"""
===========================================================
TEST CALL SERVICE - Tests para backend/call_service.py
===========================================================

Tests de integración para el servicio de llamadas telefónicas.
"""

import pytest
import json
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime


class TestGenerateCallScript:
    """Tests para generate_call_script."""

    def test_generate_call_script_formats_correctly(self):
        """Verifica que genera el script correctamente."""
        with patch("backend.call_service._load_prompt_from_file") as mock_load:
            mock_load.return_value = """
Persona: {persona_name}
Misión: {mission}
Contexto: {context}
Teléfono: {phone_formatted}
"""
            from backend.call_service import generate_call_script

            result = generate_call_script(
                mission="Reservar mesa para 2",
                context="Restaurante La Trattoria",
                persona_name="Ana García",
                persona_phone="612345678"
            )

            assert "Ana García" in result
            assert "Reservar mesa para 2" in result

    def test_generate_call_script_formats_phone_with_pauses(self):
        """Verifica que formatea el teléfono con pausas SSML."""
        with patch("backend.call_service._load_prompt_from_file") as mock_load:
            mock_load.return_value = "Teléfono: {phone_formatted}"

            from backend.call_service import generate_call_script

            result = generate_call_script(
                mission="Test",
                context="",
                persona_name="Test",
                persona_phone="612345678"
            )

            # Debe contener las palabras de los dígitos
            assert "seis" in result
            assert "uno" in result
            assert "dos" in result
            # Debe contener pausas SSML
            assert "break" in result

    def test_generate_call_script_digits_spoken_individually(self):
        """Verifica que los dígitos se dictan individualmente."""
        with patch("backend.call_service._load_prompt_from_file") as mock_load:
            mock_load.return_value = "{phone_formatted}"

            from backend.call_service import generate_call_script

            result = generate_call_script(
                mission="",
                context="",
                persona_name="",
                persona_phone="123"
            )

            assert "uno" in result
            assert "dos" in result
            assert "tres" in result


class TestAnalyzeCallResult:
    """Tests para analyze_call_result."""

    @patch("backend.call_service.openai_client")
    def test_analyze_call_result_success(self, mock_openai, mock_call_transcript_success):
        """Verifica análisis exitoso."""
        mock_openai.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content=json.dumps({
                "mission_completed": True,
                "outcome": "Reserva confirmada para mañana a las 21:00",
                "notes": ["A nombre de Ana García"]
            })))]
        )

        from backend.call_service import analyze_call_result

        result = analyze_call_result(
            mission="Reservar mesa para 2",
            transcript=mock_call_transcript_success
        )

        assert result["mission_completed"] is True
        assert "confirmada" in result["outcome"]

    @patch("backend.call_service.openai_client")
    def test_analyze_call_result_failure(self, mock_openai, mock_call_transcript_failed):
        """Verifica análisis de llamada fallida."""
        mock_openai.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content=json.dumps({
                "mission_completed": False,
                "outcome": "No hay disponibilidad",
                "notes": ["Sugerir otra fecha"]
            })))]
        )

        from backend.call_service import analyze_call_result

        result = analyze_call_result(
            mission="Reservar mesa para 2",
            transcript=mock_call_transcript_failed
        )

        assert result["mission_completed"] is False

    def test_analyze_call_result_empty_transcript(self):
        """Verifica análisis con transcripción vacía."""
        from backend.call_service import analyze_call_result

        result = analyze_call_result(
            mission="Reservar mesa",
            transcript=[]
        )

        assert result["mission_completed"] is False
        assert "No hubo conversación" in result["outcome"]

    @patch("backend.call_service.openai_client")
    def test_analyze_call_result_fallback_on_error(self, mock_openai):
        """Verifica fallback cuando falla el análisis."""
        mock_openai.chat.completions.create.side_effect = Exception("Error de API")

        from backend.call_service import analyze_call_result

        transcript = [
            {"speaker": "other", "message": "Perfecto, reserva confirmada"}
        ]

        result = analyze_call_result(
            mission="Reservar mesa",
            transcript=transcript
        )

        # Debería usar análisis básico de fallback
        assert result["mission_completed"] is True  # "confirmada" está en el texto


class TestFlaskEndpoints:
    """Tests para los endpoints Flask."""

    @pytest.fixture
    def flask_client(self, mock_env_vars):
        """Cliente de test Flask."""
        with patch("backend.call_service._load_prompt_from_file") as mock_load:
            mock_load.return_value = "Test prompt {mission} {context} {persona_name} {phone_formatted}"

            from backend.call_service import app
            app.config["TESTING"] = True
            with app.test_client() as client:
                yield client

    def test_health_endpoint(self, flask_client):
        """Verifica endpoint de health check."""
        response = flask_client.get("/")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "running"
        assert "Call Service" in data["service"]

    def test_start_call_missing_phone(self, flask_client):
        """Verifica error cuando falta phone_number."""
        response = flask_client.post(
            "/start-call",
            json={"mission": "Reservar mesa"},
            content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "phone_number" in data["error"]

    def test_start_call_missing_mission(self, flask_client):
        """Verifica error cuando falta mission."""
        response = flask_client.post(
            "/start-call",
            json={"phone_number": "+34612345678"},
            content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "mission" in data["error"]

    def test_start_call_no_data(self, flask_client):
        """Verifica error cuando no hay datos."""
        response = flask_client.post(
            "/start-call",
            content_type="application/json"
        )

        assert response.status_code == 400

    @patch("backend.call_service.threading.Thread")
    def test_start_call_success(self, mock_thread, flask_client):
        """Verifica inicio de llamada exitoso."""
        mock_thread.return_value = Mock()

        response = flask_client.post(
            "/start-call",
            json={
                "phone_number": "+34612345678",
                "mission": "Reservar mesa para 2",
                "context": "La Trattoria",
                "persona_name": "Ana García",
                "persona_phone": "612345678"
            },
            content_type="application/json"
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "call_id" in data
        assert data["status"] == "initiating"

    def test_call_status_not_found(self, flask_client):
        """Verifica error para call_id inexistente."""
        response = flask_client.get("/call-status/nonexistent123")

        assert response.status_code == 404
        data = response.get_json()
        assert "not found" in data["error"]


class TestCallStatusTracking:
    """Tests para el seguimiento de estado de llamadas."""

    def test_call_status_stores_call_data(self, mock_env_vars):
        """Verifica que se almacenan los datos de la llamada."""
        with patch("backend.call_service._load_prompt_from_file") as mock_load:
            mock_load.return_value = "{mission} {context} {persona_name} {phone_formatted}"

            from backend.call_service import calls_db, generate_call_script
            import uuid

            call_id = str(uuid.uuid4())[:8]
            mission = "Reservar mesa"
            script = generate_call_script(mission, "", "Ana", "612345678")

            calls_db[call_id] = {
                "id": call_id,
                "status": "initiating",
                "phone_number": "+34612345678",
                "mission": mission,
                "script": script,
                "transcript": [],
                "result": None,
            }

            assert call_id in calls_db
            assert calls_db[call_id]["status"] == "initiating"
            assert calls_db[call_id]["mission"] == mission

    def test_call_status_transitions(self, mock_env_vars):
        """Verifica transiciones de estado."""
        with patch("backend.call_service._load_prompt_from_file") as mock_load:
            mock_load.return_value = ""

            from backend.call_service import calls_db

            call_id = "test123"
            calls_db[call_id] = {"status": "initiating"}

            # Transición a calling
            calls_db[call_id]["status"] = "calling"
            assert calls_db[call_id]["status"] == "calling"

            # Transición a in_progress
            calls_db[call_id]["status"] = "in_progress"
            assert calls_db[call_id]["status"] == "in_progress"

            # Transición a analyzing
            calls_db[call_id]["status"] = "analyzing"
            assert calls_db[call_id]["status"] == "analyzing"

            # Transición a completed
            calls_db[call_id]["status"] = "completed"
            assert calls_db[call_id]["status"] == "completed"


class TestTwilioWebhooks:
    """Tests para webhooks de Twilio."""

    @pytest.fixture
    def flask_client(self, mock_env_vars):
        """Cliente de test Flask."""
        with patch("backend.call_service._load_prompt_from_file") as mock_load:
            mock_load.return_value = ""

            from backend.call_service import app, calls_db
            app.config["TESTING"] = True

            # Crear una llamada de prueba
            calls_db["test123"] = {
                "id": "test123",
                "status": "calling",
                "mission": "Test",
                "transcript": [],
                "result": None,
                "start_time": datetime.now(),
            }

            with app.test_client() as client:
                yield client

    def test_twilio_status_completed(self, flask_client):
        """Verifica manejo de estado completed."""
        with patch("backend.call_service.threading.Thread") as mock_thread:
            mock_thread.return_value = Mock()

            response = flask_client.post(
                "/twilio-status/test123",
                data={"CallStatus": "completed"}
            )

            assert response.status_code == 200

    def test_twilio_status_failed(self, flask_client):
        """Verifica manejo de estado failed."""
        from backend.call_service import calls_db

        response = flask_client.post(
            "/twilio-status/test123",
            data={"CallStatus": "failed"}
        )

        assert response.status_code == 200
        assert calls_db["test123"]["status"] == "failed"
        assert calls_db["test123"]["result"]["mission_completed"] is False

    def test_twilio_status_busy(self, flask_client):
        """Verifica manejo de estado busy."""
        from backend.call_service import calls_db

        response = flask_client.post(
            "/twilio-status/test123",
            data={"CallStatus": "busy"}
        )

        assert response.status_code == 200
        assert calls_db["test123"]["status"] == "failed"
        assert "ocupada" in calls_db["test123"]["result"]["outcome"]

    def test_twilio_status_no_answer(self, flask_client):
        """Verifica manejo de estado no-answer."""
        from backend.call_service import calls_db

        response = flask_client.post(
            "/twilio-status/test123",
            data={"CallStatus": "no-answer"}
        )

        assert response.status_code == 200
        assert calls_db["test123"]["status"] == "failed"
        assert "contestaron" in calls_db["test123"]["result"]["outcome"]

    def test_twilio_status_unknown_call(self, flask_client):
        """Verifica manejo de llamada desconocida."""
        response = flask_client.post(
            "/twilio-status/unknown123",
            data={"CallStatus": "completed"}
        )

        assert response.status_code == 200


class TestVoiceWebhook:
    """Tests para el webhook de voz."""

    @pytest.fixture
    def flask_client(self, mock_env_vars):
        """Cliente de test Flask."""
        with patch("backend.call_service._load_prompt_from_file") as mock_load:
            mock_load.return_value = ""

            from backend.call_service import app, calls_db
            app.config["TESTING"] = True

            calls_db["test123"] = {
                "id": "test123",
                "status": "calling",
                "mission": "Test",
                "script": "Test script",
                "transcript": [],
            }

            with app.test_client() as client:
                yield client

    def test_voice_webhook_returns_twiml(self, flask_client):
        """Verifica que devuelve TwiML válido."""
        response = flask_client.post("/voice/test123")

        assert response.status_code == 200
        assert response.content_type == "application/xml"
        data = response.get_data(as_text=True)
        assert "<Response>" in data
        assert "ConversationRelay" in data

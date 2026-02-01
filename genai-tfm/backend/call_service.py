"""
===========================================================
CALL SERVICE - Servicio de Llamadas Telefónicas Generalista
===========================================================

Servicio Flask que permite al agente realizar llamadas telefónicas
para cumplir cualquier misión: reservas, consultas, citas, etc.

Features:
- Misión dinámica definida por el agente
- Trazabilidad completa en LangSmith
- Extracción automática de notas importantes
- Feedback estructurado al agente

Endpoints:
- POST /start-call: Inicia una llamada con misión
- GET /call-status/<call_id>: Consulta estado
- GET /health: Health check
"""

import os
import json
import uuid
import threading
import time as time_module
from datetime import datetime
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_sock import Sock
from pyngrok import ngrok
import logging
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect
from openai import OpenAI
from langsmith import traceable
from langsmith.run_trees import RunTree

load_dotenv()

# ===========================================================
# PROMPT LOADING
# ===========================================================


def _load_prompt_from_file(filename: str) -> str:
    """Load a prompt from a markdown file in the prompts directory."""
    from pathlib import Path

    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_path = prompts_dir / filename

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


# Load prompts from files
_CALL_SCRIPT_TEMPLATE = _load_prompt_from_file("call_script_generation.md")
_CALL_ANALYSIS_TEMPLATE = _load_prompt_from_file("call_result_analysis.md")

# ===========================================================
# CONFIGURACIÓN
# ===========================================================

app = Flask(__name__)
sock = Sock(app)

# Silenciar logs de Werkzeug (Flask)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("FROM_TWILIO_PHONE_NUMBER")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ElevenLabs
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

# LangSmith
LANGSMITH_ENABLED = os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"

# Límites
MAX_CALL_DURATION = 120  # 2 minutos
MAX_TURNS = 20  # Máximo de intercambios en la conversación

# Clientes
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Estado de llamadas
calls_db: Dict[str, Dict[str, Any]] = {}
conversation_sessions: Dict[str, dict] = {}

# URL pública de ngrok
PUBLIC_URL: Optional[str] = None


# ===========================================================
# GENERADOR DE SCRIPT DINÁMICO
# ===========================================================


def generate_call_script(
    mission: str, context: str, persona_name: str, persona_phone: str
) -> str:
    """Genera el script para la llamada basado en la misión."""

    # Limpiar el teléfono y formatear como palabras con pausas SSML
    # 0.5s entre dígitos, 1s cada 3 dígitos
    digit_words = {
        "0": "cero",
        "1": "uno",
        "2": "dos",
        "3": "tres",
        "4": "cuatro",
        "5": "cinco",
        "6": "seis",
        "7": "siete",
        "8": "ocho",
        "9": "nueve",
    }
    phone_clean = persona_phone.replace(" ", "").replace("-", "")
    phone_parts = []
    for i, digit in enumerate(phone_clean):
        phone_parts.append(digit_words[digit])
        if i + 1 < len(phone_clean):
            if (i + 1) % 3 == 0:
                phone_parts.append('<break time="0.3s" />')
            else:
                phone_parts.append('<break time="0.1s" />')
    phone_formatted = " ".join(phone_parts)

    # Format the template with variables
    return _CALL_SCRIPT_TEMPLATE.format(
        persona_name=persona_name,
        mission=mission,
        context=context if context else "Sin contexto adicional",
        phone_formatted=phone_formatted,
    )


# ===========================================================
# ANÁLISIS DE RESULTADO CON LLM
# ===========================================================


@traceable(name="analyze_call_result", run_type="chain")
def analyze_call_result(
    mission: str, transcript: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analiza la transcripción para extraer resultado y notas importantes."""

    if not transcript:
        return {
            "mission_completed": False,
            "outcome": "No hubo conversación",
            "notes": [],
        }

    # Formatear transcripción para el análisis
    transcript_text = "\n".join(
        [
            f"{'Restaurante' if t['speaker'] == 'other' else 'Bot'}: {t['message']}"
            for t in transcript
        ]
    )

    # Format the analysis template
    analysis_prompt = _CALL_ANALYSIS_TEMPLATE.format(
        mission=mission, transcript_text=transcript_text
    )

    try:
        response = openai_client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=float(os.getenv("TEMPERATURE", 0)),
            max_tokens=500,
        )

        result_text = response.choices[0].message.content.strip()

        # Limpiar posibles marcadores de código
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        result_text = result_text.strip()

        result = json.loads(result_text)

        return {
            "mission_completed": result.get("mission_completed", False),
            "outcome": result.get("outcome", "Resultado no determinado"),
            "notes": result.get("notes", []),
        }

    except Exception as e:
        print(f"   ⚠️ Error analizando resultado: {e}")

        # Análisis básico de fallback
        full_text = transcript_text.lower()

        completed = any(
            word in full_text
            for word in [
                "confirmado",
                "confirmada",
                "perfecto",
                "anotado",
                "reservado",
                "reservada",
                "de acuerdo",
                "hecho",
            ]
        )

        return {
            "mission_completed": completed,
            "outcome": (
                "Llamada completada"
                if completed
                else "Resultado incierto - revisar transcripción"
            ),
            "notes": [],
        }


# ===========================================================
# ENDPOINTS REST
# ===========================================================


@app.route("/", methods=["GET"])
def health():
    """Health check"""
    return jsonify(
        {
            "service": "Call Service (Generalista)",
            "status": "running",
            "public_url": PUBLIC_URL,
            "langsmith_enabled": LANGSMITH_ENABLED,
        }
    )


@app.route("/start-call", methods=["POST"])
def start_call():
    """
    Inicia una llamada con misión dinámica.

    Body JSON:
    {
        "phone_number": "+34612345678",
        "mission": "Reservar mesa para 2 personas mañana a las 21:00",
        "context": "Restaurante: Pizzería Tío Miguel. Usuario prefiere terraza.",
        "persona_name": "Ana García",
        "persona_phone": "612345678"
    }
    """
    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    phone_number = data.get("phone_number")
    mission = data.get("mission")

    if not phone_number:
        return jsonify({"error": "phone_number is required"}), 400
    if not mission:
        return jsonify({"error": "mission is required"}), 400

    # Generar ID único de llamada
    call_id = str(uuid.uuid4())[:8]

    # Extraer parámetros
    context = data.get("context", "")
    persona_name = data.get("persona_name")
    persona_phone = data.get("persona_phone")

    # Generar script
    script = generate_call_script(mission, context, persona_name, persona_phone)

    # Guardar en DB
    calls_db[call_id] = {
        "id": call_id,
        "status": "initiating",
        "phone_number": phone_number,
        "mission": mission,
        "context": context,
        "persona_name": persona_name,
        "persona_phone": persona_phone,
        "script": script,
        "transcript": [],
        "result": None,
        "twilio_call_sid": None,
        "start_time": None,
        "end_time": None,
        "created_at": datetime.now().isoformat(),
    }

    # Iniciar llamada en background
    thread = threading.Thread(
        target=_make_call_async, args=(call_id, phone_number), daemon=True
    )
    thread.start()

    print(f"\n📞 [CALL {call_id}] Iniciando llamada")
    print(f"   📱 Teléfono: {phone_number}")
    print(f"   🎯 Misión: {mission[:50]}...")

    return jsonify(
        {
            "call_id": call_id,
            "status": "initiating",
            "message": "Llamada iniciándose...",
        }
    )


@app.route("/call-status/<call_id>", methods=["GET"])
def call_status(call_id: str):
    """Consulta el estado de una llamada."""

    if call_id not in calls_db:
        return jsonify({"error": "Call not found"}), 404

    call = calls_db[call_id]

    # Calcular duración si está en curso o completada
    duration = None
    if call.get("start_time"):
        end = call.get("end_time") or datetime.now()
        if isinstance(end, str):
            end = datetime.fromisoformat(end)
        start = call["start_time"]
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        duration = (end - start).total_seconds()

    return jsonify(
        {
            "call_id": call_id,
            "status": call["status"],
            "mission": call["mission"],
            "transcript": call["transcript"],
            "result": call["result"],
            "duration_seconds": duration,
            "created_at": call["created_at"],
        }
    )


def _make_call_async(call_id: str, phone_number: str):
    """Realiza la llamada de forma asíncrona."""
    try:
        if not PUBLIC_URL:
            calls_db[call_id]["status"] = "failed"
            calls_db[call_id]["result"] = {
                "mission_completed": False,
                "outcome": "Servicio no inicializado (ngrok no disponible)",
                "notes": [],
            }
            return

        voice_url = f"{PUBLIC_URL}/voice/{call_id}"
        status_url = f"{PUBLIC_URL}/twilio-status/{call_id}"

        call = twilio_client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE,
            url=voice_url,
            status_callback=status_url,
            status_callback_method="POST",
        )

        calls_db[call_id]["twilio_call_sid"] = call.sid
        calls_db[call_id]["status"] = "calling"
        calls_db[call_id]["start_time"] = datetime.now()

        print(f"   ✓ Llamada Twilio iniciada: {call.sid}")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        calls_db[call_id]["status"] = "failed"
        calls_db[call_id]["result"] = {
            "mission_completed": False,
            "outcome": f"Error al iniciar llamada: {str(e)}",
            "notes": [],
        }


# ===========================================================
# WEBHOOKS DE TWILIO
# ===========================================================


@app.route("/voice/<call_id>", methods=["GET", "POST"])
def voice_webhook(call_id: str):
    """Webhook de Twilio para iniciar la conversación."""
    from twilio.twiml.voice_response import ConversationRelay

    response = VoiceResponse()
    connect = Connect()

    host = request.host
    conversation_relay = ConversationRelay(
        url=f"wss://{host}/conversation-ws/{call_id}",
        language="es-ES",
        tts_provider="elevenlabs",
        voice=ELEVENLABS_VOICE_ID,
        dtmf_detection=False,
    )

    connect.append(conversation_relay)
    response.append(connect)

    return str(response), 200, {"Content-Type": "application/xml"}


@app.route("/twilio-status/<call_id>", methods=["POST"])
def twilio_status_webhook(call_id: str):
    """Webhook de estado de llamada de Twilio."""

    if call_id not in calls_db:
        return "", 200

    call_status = request.values.get("CallStatus", "unknown")
    call = calls_db[call_id]

    print(f"\n📞 [STATUS {call_id}] {call_status}")

    if call_status == "completed":
        call["status"] = "analyzing"
        call["end_time"] = datetime.now()

        # Analizar resultado en background
        thread = threading.Thread(target=_finalize_call, args=(call_id,), daemon=True)
        thread.start()

    elif call_status == "failed":
        call["status"] = "failed"
        call["end_time"] = datetime.now()
        call["result"] = {
            "mission_completed": False,
            "outcome": "La llamada falló",
            "notes": [],
        }

    elif call_status == "busy":
        call["status"] = "failed"
        call["end_time"] = datetime.now()
        call["result"] = {
            "mission_completed": False,
            "outcome": "Línea ocupada",
            "notes": ["Intentar más tarde"],
        }

    elif call_status == "no-answer":
        call["status"] = "failed"
        call["end_time"] = datetime.now()
        call["result"] = {
            "mission_completed": False,
            "outcome": "No contestaron",
            "notes": ["Intentar más tarde"],
        }

    elif call_status in ["ringing", "in-progress"]:
        call["status"] = "in_progress"

    return "", 200


@traceable(name="finalize_call", run_type="chain")
def _finalize_call(call_id: str):
    """Analiza y finaliza la llamada."""
    call = calls_db[call_id]

    print(f"\n🔍 [ANALYZE {call_id}] Analizando resultado...")

    # Analizar transcripción
    result = analyze_call_result(mission=call["mission"], transcript=call["transcript"])

    call["result"] = result
    call["status"] = "completed"

    print(f"   ✓ Misión completada: {result['mission_completed']}")
    print(f"   📋 Resultado: {result['outcome']}")
    if result["notes"]:
        print(f"   📝 Notas: {result['notes']}")


# ===========================================================
# WEBSOCKET PARA CONVERSACIÓN
# ===========================================================


@sock.route("/conversation-ws/<call_id>")
def conversation_websocket(ws, call_id: str):
    """WebSocket para la conversación con Twilio ConversationRelay."""

    if call_id not in calls_db:
        print(f"   ✗ Llamada {call_id} no encontrada")
        return

    call = calls_db[call_id]

    print(f"\n🎙️ [WS {call_id}] Conversación iniciada")
    print(f"   🎯 Misión: {call['mission'][:50]}...")

    # Inicializar sesión de conversación
    conversation_sessions[call_id] = {
        "messages": [{"role": "system", "content": call["script"]}],
        "turn_count": 0,
        "start_time": time_module.time(),
    }

    try:
        while True:
            # Verificar límites
            session = conversation_sessions.get(call_id, {})
            elapsed = time_module.time() - session.get("start_time", time_module.time())

            if elapsed > MAX_CALL_DURATION:
                print(f"   ⏱️ Límite de tiempo alcanzado ({MAX_CALL_DURATION}s)")
                _send_goodbye(
                    ws,
                    "Se me ha hecho un poco tarde, ¿podría llamar en otro momento? Gracias.",
                )
                break

            if session.get("turn_count", 0) > MAX_TURNS:
                print(f"   🔄 Límite de turnos alcanzado ({MAX_TURNS})")
                _send_goodbye(ws, "Muchas gracias por su tiempo. Hasta luego.")
                break

            try:
                message_raw = ws.receive(timeout=30)
                if message_raw is None:
                    break

                message = json.loads(message_raw)
                message_type = message.get("type")

            except Exception as e:
                if "timeout" in str(e).lower():
                    continue
                break

            if message_type == "setup":
                twilio_call_sid = message.get("callSid")
                print(f"   📞 Setup: {twilio_call_sid}")

            elif message_type == "prompt":
                _handle_prompt(ws, call_id, message)

            elif message_type == "interrupt":
                print(f"   ⚡ Interrupción detectada")

            elif message_type == "error":
                print(f"   ✗ Error Twilio: {message.get('description')}")

    except Exception as e:
        print(f"   ✗ Error WS: {e}")

    finally:
        if call_id in conversation_sessions:
            del conversation_sessions[call_id]
        print(f"   ✓ WebSocket cerrado")


@traceable(name="handle_conversation_turn", run_type="llm")
def _handle_prompt(ws, call_id: str, message: dict):
    """Maneja un turno de la conversación."""

    call = calls_db[call_id]
    session = conversation_sessions[call_id]

    voice_prompt = message.get("voicePrompt", "")
    print(f"   🏪 Restaurante: {voice_prompt}")

    # Guardar en transcripción
    call["transcript"].append(
        {
            "speaker": "other",
            "message": voice_prompt,
            "timestamp": datetime.now().isoformat(),
        }
    )

    # Añadir al historial
    session["messages"].append({"role": "user", "content": voice_prompt})
    session["turn_count"] += 1

    # Llamar a OpenAI
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=session["messages"],
            temperature=0.7,
            max_tokens=150,
        )

        ai_response = response.choices[0].message.content
        if not ai_response:
            ai_response = "Perdona, no te he escuchado bien. ¿Puedes repetir?"

        print(f"   🤖 Tú: {ai_response}")

        # Guardar en transcripción
        call["transcript"].append(
            {
                "speaker": "self",
                "message": ai_response,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Añadir al historial
        session["messages"].append({"role": "assistant", "content": ai_response})

        # Enviar respuesta
        ws.send(json.dumps({"type": "text", "token": ai_response, "last": True}))

    except Exception as e:
        print(f"   ✗ Error OpenAI: {e}")
        ws.send(
            json.dumps(
                {
                    "type": "text",
                    "token": "Perdona, ha habido un problema. ¿Puedes repetir?",
                    "last": True,
                }
            )
        )


def _send_goodbye(ws, message: str):
    """Envía mensaje de despedida y cierra."""
    try:
        ws.send(json.dumps({"type": "text", "token": message, "last": True}))
    except:
        pass


# ===========================================================
# INICIALIZACIÓN
# ===========================================================


def start_service(CALL_SERVICE_PORT):
    """Inicia el servicio de llamadas telefónicas con IA."""
    global PUBLIC_URL

    # Verificar configuración
    missing = []
    if not TWILIO_ACCOUNT_SID:
        missing.append("TWILIO_ACCOUNT_SID")
    if not TWILIO_AUTH_TOKEN:
        missing.append("TWILIO_AUTH_TOKEN")
    if not TWILIO_PHONE:
        missing.append("FROM_TWILIO_PHONE_NUMBER")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")

    if missing:
        print(f"❌ Error: Faltan variables de entorno: {', '.join(missing)}")
        return None

    # Iniciar Flask
    flask_thread = threading.Thread(
        target=lambda: app.run(
            port=CALL_SERVICE_PORT, debug=False, use_reloader=False, host="0.0.0.0"
        ),
        daemon=True,
    )
    flask_thread.start()

    print(f"✅ Flask iniciado en puerto {CALL_SERVICE_PORT}")
    time_module.sleep(2)

    # Iniciar ngrok
    ngrok_token = os.getenv("NGROK_AUTH_TOKEN")
    if ngrok_token:
        try:
            ngrok.set_auth_token(ngrok_token)
            tunnel = ngrok.connect(CALL_SERVICE_PORT)
            PUBLIC_URL = str(tunnel.public_url).replace("http://", "https://")
            print(f"✅  ngrok: {PUBLIC_URL}")
        except Exception as e:
            print(f"❌ Error: Iniciando ngrok: {e}")
            PUBLIC_URL = f"http://localhost:{CALL_SERVICE_PORT}"
    else:
        print("⚠️ NGROK_AUTH_TOKEN no configurado")
        PUBLIC_URL = f"http://localhost:{CALL_SERVICE_PORT}"

    # Actualizar webhook de Twilio
    if PUBLIC_URL.startswith("https://"):
        voice_url = f"{PUBLIC_URL}/voice"
        status_url = f"{PUBLIC_URL}/status"

        print(f"📞 Voice webhook: {voice_url}")
        print(f"🔔 Status webhook: {status_url}")

        try:
            incoming_phone_numbers = twilio_client.incoming_phone_numbers.list(
                phone_number=TWILIO_PHONE
            )

            if incoming_phone_numbers:
                phone_number_sid = incoming_phone_numbers[0].sid
                if phone_number_sid:
                    twilio_client.incoming_phone_numbers(phone_number_sid).update(
                        voice_url=voice_url,
                        voice_method="POST",
                        status_callback=status_url,
                        status_callback_method="POST",
                    )
                    print(f"✅ Twilio webhook actualizado para {TWILIO_PHONE}")
                else:
                    print(f"⚠️ No se pudo obtener SID del número de teléfono")
            else:
                print(f"⚠️ Número {TWILIO_PHONE} no encontrado en tu cuenta Twilio")
        except Exception as e:
            print(f"❌ Error: actualizando webhook de Twilio: {e}")

    return flask_thread


if __name__ == "__main__":
    CALL_SERVICE_PORT = int(os.getenv("CALL_SERVICE_PORT", "8080"))
    thread = start_service(CALL_SERVICE_PORT)

    if thread:
        try:
            while True:
                time_module.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Cerrando servicio...")

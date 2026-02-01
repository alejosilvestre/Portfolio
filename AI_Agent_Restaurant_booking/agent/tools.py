"""
===========================================================
TOOLS - Herramientas del Agente
===========================================================

Herramientas definidas con @tool de LangChain.
El grafo las ejecuta según lo que decida el LLM.
"""

from typing import Optional, List, Dict
from langchain_core.tools import tool
from datetime import datetime
import os
import random
import requests
import time as time_module

# Google Places
from backend.google_places import places_text_search, PlaceSearchPayload

# Google calendar
from langchain_google_community import CalendarToolkit

# Tavily web search
from tavily import TavilyClient


# ===========================================================
# ESTADO COMPARTIDO (para tools que dependen de otras)
# ===========================================================

_search_results: List[Dict] = []


def get_search_results() -> List[Dict]:
    """Obtiene los resultados de la última búsqueda."""
    return _search_results


def clear_search_results():
    """Limpia los resultados de búsqueda."""
    global _search_results
    _search_results = []


# ===========================================================
# MOCK: Sistema de Reservas
# ===========================================================


class MockBookingSystem:
    """Mock del sistema de reservas (reemplazar con API real)."""

    def __init__(self):
        self._api_cache = {}

    def check_availability(
        self,
        place_id: str,
        name: str,
        date: str,
        time: str,
        num_people: int,
        website: str = None,
    ) -> Dict:

        # Si ya determinamos si tiene API, mantener ese valor
        if place_id in self._api_cache:
            has_api = self._api_cache[place_id]
        else:
            known_chains = ["domino", "telepizza", "foster", "burger king", "mcdonald"]
            has_api = any(chain in name.lower() for chain in known_chains) or (
                website and random.random() < 0.6
            )
            self._api_cache[place_id] = has_api

        if not has_api:
            return {"has_api": False, "available": None, "times": []}

        hour = int(time.split(":")[0]) if ":" in time else 20
        is_peak = 13 <= hour <= 15 or 20 <= hour <= 22
        available = random.random() > (0.4 if is_peak else 0.2)

        if available:
            return {"has_api": True, "available": True, "times": [time]}
        else:
            alts = [f"{hour}:{m:02d}" for m in [15, 30, 45]]
            return {"has_api": True, "available": False, "times": alts}

    def make_booking(
        self, place_id: str, name: str, date: str, time: str, num_people: int
    ) -> Dict:

        if not self._api_cache.get(place_id, False):
            return {"success": False, "error": "No tiene reserva online"}

        if random.random() < 0.95:  # 95% éxito (antes 85%)
            return {
                "success": True,
                "booking_id": f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "details": {
                    "restaurant": name,
                    "date": date,
                    "time": time,
                    "people": num_people,
                },
            }
        return {"success": False, "error": "Error temporal"}


_booking_system = MockBookingSystem()


# ===========================================================
# TOOL: web_search
# ===========================================================


@tool
def web_search(query: str) -> str:
    """Busca información en internet.

    Útil para: información actualizada, recetas, recomendaciones,
    noticias, opiniones, o cualquier cosa que no conozcas.

    Args:
        query: La consulta de búsqueda
    """

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "ERROR: TAVILY_API_KEY no configurada"

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=5, include_answer=True)

        answer = response.get("answer", "")
        results = response.get("results", [])

        if not answer and not results:
            return f"No encontré resultados para: {query}"

        lines = []
        if answer:
            lines.append(f"**Resumen:** {answer}\n")
        for i, r in enumerate(results[:3], 1):
            lines.append(f"{i}. {r.get('title')}: {r.get('content', '')[:150]}...")

        return "\n".join(lines)
    except Exception as e:
        return f"ERROR: {str(e)}"


# ===========================================================
# TOOL: maps_search
# ===========================================================


@tool
def maps_search(
    query: str,
    location: str,
    radius: int = 2000,
    price_level: Optional[int] = None,
    extras: Optional[str] = None,
    max_travel_time: Optional[int] = None,
    travel_mode: str = "walking",
) -> str:
    """Busca lugares en Google Maps/Places.

    Args:
        query: Qué buscar (ej: "pizzería", "farmacia", "hotel", "gimnasio")
        location: Dónde buscar (ej: "Navalcarnero", "Madrid centro")
        radius: Radio en metros (default: 2000)
        price_level: Nivel de precio 1-4 (solo para restaurantes)
        extras: Palabras clave adicionales (ej: "terraza", "24h")
        max_travel_time: Tiempo máximo de viaje en minutos
        travel_mode: "walking", "driving", "bicycling", "transit"
    """
    global _search_results

    try:
        payload = PlaceSearchPayload(
            query=query,
            location=location,
            radius=radius,
            price_level=price_level,
            extras=extras,
            max_travel_time=max_travel_time,
            travel_mode=travel_mode,
        )

        results = places_text_search(payload)
        places = results[:5] if isinstance(results, list) else []

        if not places:
            return f"No encontré '{query}' en {location}"

        _search_results = places

        lines = [f"Encontré {len(places)} resultados:\n"]
        for i, p in enumerate(places, 1):
            rating = f"⭐{p.get('rating')}" if p.get("rating") else ""
            reviews = (
                f"({p.get('user_ratings_total')} reseñas)"
                if p.get("user_ratings_total")
                else ""
            )
            price = "€" * (p.get("price_level") or 2) if p.get("price_level") else ""
            lines.append(f"{i}. **{p.get('name')}** {rating} {reviews} {price}")
            lines.append(f"   📍 {p.get('address')}")
            if p.get("phone"):
                lines.append(f"   📞 {p.get('phone')}")

        return "\n".join(lines)
    except Exception as e:
        return f"ERROR: {str(e)}"


# ===========================================================
# TOOL: check_availability
# ===========================================================


@tool
def check_availability(date: str, time: str, num_people: int = 2) -> str:
    """Verifica disponibilidad en los lugares encontrados.

    IMPORTANTE: Usa maps_search primero.

    Args:
        date: Fecha YYYY-MM-DD (ej: "2026-01-15")
        time: Hora HH:MM (ej: "21:00")
        num_people: Número de personas
    """
    global _search_results

    if not _search_results:
        return "ERROR: Primero busca lugares con maps_search"

    lines = [f"Disponibilidad para {date} {time} ({num_people}p):\n"]

    for p in _search_results:
        avail = _booking_system.check_availability(
            p.get("place_id", ""),
            p.get("name", ""),
            date,
            time,
            num_people,
            p.get("website"),
        )

        p["has_api"] = avail["has_api"]
        p["available"] = avail["available"]
        p["available_times"] = avail["times"]

        if avail["available"]:
            status = "✅ Disponible"
        elif avail["available"] is False:
            status = f"⚠️ Alternativas: {', '.join(avail['times'])}"
        else:
            status = "📞 Solo teléfono"

        lines.append(f"- **{p.get('name')}**: {status}")

    return "\n".join(lines)


# ===========================================================
# TOOL: make_booking
# ===========================================================


@tool
def make_booking(place_name: str, date: str, time: str, num_people: int = 2) -> str:
    """Hace una reserva en un lugar.

    IMPORTANTE: Usa check_availability primero.

    Args:
        place_name: Nombre del lugar
        date: Fecha YYYY-MM-DD
        time: Hora HH:MM
        num_people: Número de personas
    """
    global _search_results

    place = next(
        (p for p in _search_results if place_name.lower() in p.get("name", "").lower()),
        None,
    )

    if not place:
        return f"ERROR: No encontré '{place_name}'. Usa maps_search primero."

    result = _booking_system.make_booking(
        place.get("place_id", ""), place_name, date, time, num_people
    )

    if result["success"]:
        d = result["details"]
        return f"""¡Reserva confirmada! 🎉

**{d['restaurant']}**
📅 {d['date']} a las {d['time']}
👥 {d['people']} personas
🔖 Código: {result['booking_id']}"""
    else:
        phone = place.get("phone", "no disponible")
        return f"No pude reservar online. ¿Llamo al {phone}?"


# ===========================================================
# TOOL: phone_call
# ===========================================================


@tool
def phone_call(
    phone_number: str,
    mission: str,
    context: str = "",
    persona_name: str = "",
    persona_phone: str = "",
) -> str:
    """Realiza una llamada telefónica para cumplir una misión.

    Esta herramienta permite llamar por teléfono para realizar cualquier
    gestión: reservas, consultas, citas, preguntas, etc.

    USAR CUANDO:
    - El lugar solo acepta teléfono (📞)
    - El usuario pide explícitamente que llames
    - Necesitas información que solo se puede obtener por teléfono

    Args:
        phone_number: Número a llamar (formato +34XXXXXXXXX)
        mission: Qué debe conseguir la llamada. Sé específico.
                 Ej: "Reservar mesa para 2 personas mañana a las 21:00"
                 Ej: "Preguntar si aceptan perros y horario de cierre"
                 Ej: "Agendar cita para revisión de frenos esta semana"
        context: Información adicional relevante para la llamada.
                 Ej: "Restaurante: La Trattoria. Usuario prefiere terraza."
        persona_name: Nombre a usar si lo preguntan
        persona_phone: Teléfono de contacto si lo piden

    Returns:
        Resultado estructurado con: misión completada (sí/no),
        resultado, notas importantes y transcripción resumida.
    """

    # Sobreescribmos el número de teléfono del restaurante para poder hacer nuestras pruebas
    phone_number = os.getenv("TO_PHONE_NUMBER")

    # Obtener puerto del servicio de llamadas desde variable de entorno
    CALL_SERVICE_PORT = os.getenv("CALL_SERVICE_PORT", "8080")
    CALL_SERVICE_URL = f"http://localhost:{CALL_SERVICE_PORT}"

    # Verificar servicio disponible
    try:
        health = requests.get(f"{CALL_SERVICE_URL}/", timeout=5)
        if health.status_code != 200:
            return "ERROR: El servicio de llamadas no está disponible. Ejecuta: python backend/call_service.py"
    except requests.exceptions.ConnectionError:
        return f"ERROR: No se pudo conectar al servicio de llamadas en {CALL_SERVICE_URL}. ¿Está corriendo?"

    # Iniciar llamada
    print(f"   📞 Iniciando llamada...")
    print(f"   🎯 Misión: {mission[:60]}...")

    try:
        response = requests.post(
            f"{CALL_SERVICE_URL}/start-call",
            json={
                "phone_number": phone_number,
                "mission": mission,
                "context": context,
                "persona_name": persona_name,
                "persona_phone": persona_phone,
            },
            timeout=10,
        )

        if response.status_code != 200:
            return f"ERROR: No se pudo iniciar la llamada: {response.text}"

        call_id = response.json().get("call_id")

    except Exception as e:
        return f"ERROR iniciando llamada: {str(e)}"

    # Esperar resultado (polling)
    max_wait = 150  # 2.5 minutos máximo
    start_time = time_module.time()
    last_status = ""

    while time_module.time() - start_time < max_wait:
        try:
            status_response = requests.get(
                f"{CALL_SERVICE_URL}/call-status/{call_id}", timeout=5
            )

            if status_response.status_code != 200:
                time_module.sleep(3)
                continue

            data = status_response.json()
            status = data.get("status")

            # Log de progreso
            if status != last_status:
                status_emoji = {
                    "initiating": "📱",
                    "calling": "📞",
                    "in_progress": "🗣️",
                    "analyzing": "🔍",
                    "completed": "✅",
                    "failed": "❌",
                }.get(status, "⏳")
                print(f"   {status_emoji} Estado: {status}")
                last_status = status

            if status == "completed":
                result = data.get("result", {})
                transcript = data.get("transcript", [])
                duration = data.get("duration_seconds", 0)

                # Formatear respuesta
                completed = "✅ SÍ" if result.get("mission_completed") else "❌ NO"

                output = f"""📞 **LLAMADA COMPLETADA** (Duración: {int(duration)}s)
                        **Misión cumplida:** {completed}
                        **Resultado:** {result.get('outcome', 'Sin resultado')}
                        """

                # Añadir notas si las hay
                notes = result.get("notes", [])
                if notes:
                    output += "\n**📝 Notas importantes:**\n"
                    for note in notes:
                        output += f"  • {note}\n"

                # Añadir transcripción resumida
                if transcript:
                    output += "\n**Transcripción:**\n"
                    for entry in transcript[-8:]:  # Últimos 8 intercambios
                        speaker = "🏪" if entry["speaker"] == "other" else "🤖"
                        output += f"{speaker} {entry['message']}\n"

                return output

            elif status == "failed":
                result = data.get("result", {})
                outcome = result.get("outcome", "Error desconocido")
                notes = result.get("notes", [])

                output = f"❌ **LLAMADA FALLIDA**\n\n**Motivo:** {outcome}"
                if notes:
                    output += f"\n**Sugerencia:** {notes[0]}"

                return output

            # Aún en curso
            time_module.sleep(3)

        except Exception as e:
            print(f"   ⚠️ Error consultando estado: {e}")
            time_module.sleep(3)

    return (
        f"⏱️ La llamada está tardando más de lo esperado (>{max_wait}s). ID: {call_id}"
    )

    # -------------------------------------------------------

    # ... (todo tu código anterior de MockBookingSystem, web_search, maps_search, etc.) ...

# ===========================================================
# REGISTRO FINAL DE HERRAMIENTAS
# ===========================================================


# Herramientas base (siempre disponibles)
TOOLS = [web_search, maps_search, check_availability, make_booking, phone_call]

# Añadir herramientas de calendario si están configuradas
try:
    from backend.calendar_tools import is_calendar_configured, init_calendar

    if is_calendar_configured():
        calendar_tools = init_calendar()
        if calendar_tools:
            TOOLS.extend(calendar_tools)
except ImportError:
    pass  # calendar_tools no existe, continuar sin él
except Exception as e:
    print(f"⚠️  Error cargando calendario: {e}")

# Diccionario nombre -> función para ejecución
TOOLS_MAP = {t.name: t for t in TOOLS}


def execute_tool(tool_name: str, tool_args: dict) -> str:
    """Ejecuta una herramienta por nombre."""
    if tool_name not in TOOLS_MAP:
        return f"ERROR: Herramienta '{tool_name}' no existe. Disponibles: {list(TOOLS_MAP.keys())}"

    try:
        return TOOLS_MAP[tool_name].invoke(tool_args)
    except Exception as e:
        return f"ERROR ejecutando {tool_name}: {str(e)}"

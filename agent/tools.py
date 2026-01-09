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

# Google Places
from backend.google_places import places_text_search, PlaceSearchPayload

# Tavily
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False


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
    
    def check_availability(self, place_id: str, name: str, date: str, 
                          time: str, num_people: int, website: str = None) -> Dict:
        
        known_chains = ["domino", "telepizza", "foster", "burger king", "mcdonald"]
        has_api = any(chain in name.lower() for chain in known_chains) or (website and random.random() < 0.6)
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
    
    def make_booking(self,
                    place_id: str, 
                    name: str, 
                    date: str, 
                    time: str, 
                    num_people: int) -> Dict:
        import random
        if not self._api_cache.get(place_id, False):
            return {"success": False, "error": "No tiene reserva online"}
        
        if random.random() < 0.85:
            return {
                "success": True,
                "booking_id": f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "details": {"restaurant": name, "date": date, "time": time, "people": num_people}
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
    if not TAVILY_AVAILABLE:
        return "ERROR: Tavily no instalado (pip install tavily-python)"
    
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
    travel_mode: str = "walking"
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
            travel_mode=travel_mode
        )
        
        results = places_text_search(payload)
        places = results[:6] if isinstance(results, list) else []
        
        if not places:
            return f"No encontré '{query}' en {location}"
        
        _search_results = places
        
        lines = [f"Encontré {len(places)} resultados:\n"]
        for i, p in enumerate(places, 1):
            rating = f"⭐{p.get('rating')}" if p.get('rating') else ""
            reviews = f"({p.get('user_ratings_total')} reseñas)" if p.get('user_ratings_total') else ""
            price = "€" * (p.get('price_level') or 2) if p.get('price_level') else ""
            lines.append(f"{i}. **{p.get('name')}** {rating} {reviews} {price}")
            lines.append(f"   📍 {p.get('address')}")
            if p.get('phone'):
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
            p.get("place_id", ""), p.get("name", ""),
            date, time, num_people, p.get("website")
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
    
    place = next((p for p in _search_results if place_name.lower() in p.get("name", "").lower()), None)
    
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
# REGISTRO DE HERRAMIENTAS
# ===========================================================

TOOLS = [web_search, maps_search, check_availability, make_booking]

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
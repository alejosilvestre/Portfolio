"""
===========================================================
AGENT STATE - Estado compartido del Agente
===========================================================

Este módulo define el "cerebro compartido" del agente.
Cada nodo del grafo puede LEER y ESCRIBIR en este estado.

¿Por qué es importante?
-----------------------
- El agente necesita "recordar" qué ha pasado en pasos anteriores
- Permite que los nodos se comuniquen entre sí sin acoplamiento
- Facilita el debug (puedes ver el estado en cada paso)

Componentes clave:
-----------------
1. AgentState: El estado principal que fluye por todo el grafo
2. UserIntent: Clasificación de la intención del usuario
3. ReservationParams: Parámetros extraídos para la reserva
4. SearchResults: Resultados de búsqueda de restaurantes
"""

from typing import TypedDict, Literal, Optional, List, Dict, Any, Annotated
from pydantic import BaseModel, Field
from datetime import datetime
import operator


# ===========================================================
# 1. MODELOS DE DATOS
# ===========================================================

class UserIntent(BaseModel):
    """
    Clasificación de la intención del usuario.
    
    Ejemplo:
    --------
    query: "Resérvame una pizzería"
    → intent: "search_and_book"
    → confidence: 0.95
    → missing_params: ["location", "date", "time", "num_people"]
    """
    intent: Literal[
        "search_and_book",      # Buscar y reservar
        "search_only",          # Solo buscar info
        "modify_reservation",   # Modificar reserva existente
        "cancel_reservation",   # Cancelar reserva
        "unclear"               # No está claro qué quiere
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    missing_params: List[str] = Field(default_factory=list)
    reasoning: Optional[str] = None  # Explicación del LLM


class ReservationParams(BaseModel):
    """
    Parámetros necesarios para hacer una reserva.
    
    El agente irá rellenando estos campos a medida que obtiene info.
    Si falta algo crítico, preguntará al usuario.
    """
    # Parámetros de búsqueda
    query: Optional[str] = None                    # "pizzería", "comida japonesa"
    location: Optional[str] = None                 # "Navalcarnero" o "lat,lng"
    radius: Optional[int] = None                   # metros
    price_level: Optional[int] = None              # 0-4
    extras: Optional[str] = None                   # "terraza, wifi"
    max_travel_time: Optional[int] = None          # minutos
    travel_mode: Optional[str] = "walking"         # walking, driving, etc.
    
    # Parámetros de reserva
    date: Optional[str] = None                     # YYYY-MM-DD
    time: Optional[str] = None                     # HH:MM
    num_people: Optional[int] = None               # número de comensales
    
    # Preferencias del usuario (futuro: RAG)
    user_preferences: Optional[Dict[str, Any]] = None


class RestaurantCandidate(BaseModel):
    """
    Representa un restaurante candidato con toda su info.
    """
    place_id: str
    name: str
    address: str
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    price_level: Optional[int] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[Dict[str, Any]] = None
    
    # Disponibilidad (desde CoverManager)
    has_api_booking: bool = False
    available: Optional[bool] = None
    available_times: Optional[List[str]] = None
    
    # Score del agente (basado en relevancia, rating, disponibilidad)
    agent_score: Optional[float] = None
    score_reasoning: Optional[str] = None


class SearchResults(BaseModel):
    """
    Resultados de búsqueda de Google Places.
    """
    restaurants: List[RestaurantCandidate] = Field(default_factory=list)
    total_found: int = 0
    search_params_used: Optional[Dict[str, Any]] = None


# ===========================================================
# 2. ESTADO PRINCIPAL DEL AGENTE
# ===========================================================

class AgentState(TypedDict):
    """
    Estado global que fluye por todo el grafo del agente.
    
    ¿Cómo funciona?
    ---------------
    - Cada nodo recibe este estado como input
    - Cada nodo puede modificar campos y devolver el estado actualizado
    - LangGraph se encarga de mergear los cambios automáticamente
    
    Campos principales:
    -------------------
    - messages: Historial de conversación (Memoria Episódica)
    - current_step: En qué fase estamos
    - user_intent: Qué quiere hacer el usuario
    - reservation_params: Parámetros de la reserva
    - search_results: Restaurantes encontrados
    - selected_restaurant: Restaurante elegido por el usuario
    - booking_status: Estado de la reserva
    - needs_user_input: Flag para HITL
    - error: Si algo falla
    """
    
    # ========== CONVERSACIÓN ==========
    # Usamos Annotated con operator.add para que los mensajes se acumulen
    messages: Annotated[List[Dict[str, str]], operator.add]
    
    # ========== CONTROL DE FLUJO ==========
    current_step: str  # "classify", "extract", "search", "rank", "book", etc.
    iteration_count: int  # Para evitar loops infinitos
    needs_user_input: bool  # Flag para pausar y esperar al usuario
    
    # ========== INTENCIÓN Y PARÁMETROS ==========
    user_intent: Optional[UserIntent]
    reservation_params: Optional[ReservationParams]
    
    # ========== BÚSQUEDA Y SELECCIÓN ==========
    search_results: Optional[SearchResults]
    top_3_restaurants: Optional[List[RestaurantCandidate]]
    selected_restaurant: Optional[RestaurantCandidate]
    
    # ========== RESERVA ==========
    booking_status: Optional[Literal[
        "pending",           # Pendiente
        "api_success",       # Reserva exitosa por API
        "api_failed",        # API falló, intentar voz
        "voice_success",     # Reserva exitosa por voz
        "voice_failed",      # Falló también por voz
        "cancelled"          # Usuario canceló
    ]]
    booking_confirmation: Optional[Dict[str, Any]]  # Detalles de la reserva confirmada
    
    # ========== FALLBACK A VOZ ==========
    voice_call_transcript: Optional[str]  # Transcripción de la llamada
    
    # ========== ERROR HANDLING ==========
    error: Optional[str]
    
    # ========== PENSAMIENTO DEL AGENTE (ReAct) ==========
    agent_thoughts: Annotated[List[str], operator.add]  # Razonamiento interno
    agent_actions: Annotated[List[str], operator.add]   # Acciones ejecutadas
    agent_observations: Annotated[List[str], operator.add]  # Resultados observados


# ===========================================================
# 3. FUNCIONES HELPER PARA INICIALIZAR ESTADO
# ===========================================================

def create_initial_state(user_message: str) -> AgentState:
    """
    Crea el estado inicial del agente a partir del mensaje del usuario.
    
    Args:
        user_message: Primer mensaje del usuario (ej: "Resérvame una pizzería")
    
    Returns:
        AgentState inicializado
    """
    return AgentState(
        messages=[{"role": "user", "content": user_message}],
        current_step="classify_intent",
        iteration_count=0,
        needs_user_input=False,
        user_intent=None,
        reservation_params=None,
        search_results=None,
        top_3_restaurants=None,
        selected_restaurant=None,
        booking_status=None,
        booking_confirmation=None,
        voice_call_transcript=None,
        error=None,
        agent_thoughts=[],
        agent_actions=[],
        agent_observations=[]
    )


def is_state_complete_for_search(state: AgentState) -> bool:
    """
    Verifica si tenemos suficiente información para buscar restaurantes.
    
    Parámetros CRÍTICOS para búsqueda:
    - query (tipo de comida)
    - location (dónde buscar)
    
    Parámetros OPCIONALES pero útiles:
    - date, time (para verificar disponibilidad)
    - num_people (para la reserva)
    """
    if not state.get("reservation_params"):
        return False
    
    params = state["reservation_params"]
    
    # Mínimos para una búsqueda
    has_query = params.query is not None
    has_location = params.location is not None
    
    return has_query and has_location


def get_missing_critical_params(state: AgentState) -> List[str]:
    """
    Retorna una lista de parámetros críticos que faltan.
    
    Esto le dirá al agente QUÉ debe preguntar al usuario.
    """
    if not state.get("reservation_params"):
        return ["query", "location", "date", "time", "num_people"]
    
    params = state["reservation_params"]
    missing = []
    
    # Parámetros críticos
    if not params.query:
        missing.append("tipo de comida")
    if not params.location:
        missing.append("ubicación")
    if not params.date:
        missing.append("fecha")
    if not params.time:
        missing.append("hora")
    if not params.num_people:
        missing.append("número de personas")
    
    return missing


# ===========================================================
# EJEMPLO DE USO
# ===========================================================

if __name__ == "__main__":
    # Crear estado inicial
    state = create_initial_state("Resérvame una pizzería para esta noche")
    
    print("Estado inicial creado:")
    print(f"- Mensaje del usuario: {state['messages'][0]['content']}")
    print(f"- Paso actual: {state['current_step']}")
    print(f"- ¿Está completo para búsqueda?: {is_state_complete_for_search(state)}")
    print(f"- Parámetros faltantes: {get_missing_critical_params(state)}")

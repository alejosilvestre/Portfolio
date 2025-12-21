"""
===========================================================
AGENT NODES - Nodos del Grafo del Agente
===========================================================

Este módulo contiene la LÓGICA CEREBRAL del agente.
Cada nodo es una "neurona" que ejecuta una tarea específica.

¿Por qué es importante?
-----------------------
- Cada nodo tiene una responsabilidad ÚNICA (Single Responsibility)
- Los nodos son PUROS: reciben estado, devuelven estado modificado
- Facilita el testing y debugging de cada paso
- Permite reordenar el flujo sin cambiar la lógica

Arquitectura de un Nodo:
------------------------
1. Recibe el estado actual (AgentState)
2. Ejecuta su lógica (puede usar LLM, herramientas, etc.)
3. Actualiza el estado con sus hallazgos
4. Retorna el estado modificado

Nodos implementados:
-------------------
1. classify_intent_node: Clasifica la intención del usuario
2. extract_parameters_node: Extrae parámetros de la conversación
3. check_completeness_node: Verifica si hay info suficiente
4. ask_user_node: Genera preguntas para obtener info faltante
5. search_restaurants_node: Busca restaurantes con Google Places
6. rank_restaurants_node: Genera TOP 3 inteligente
7. check_availability_node: Verifica disponibilidad en cada restaurante
8. present_options_node: Presenta opciones al usuario
9. book_restaurant_node: Intenta reserva por API
10. fallback_voice_node: Reserva por llamada telefónica
11. finalize_node: Mensaje final de éxito
12. error_node: Manejo de errores
"""

from typing import Dict, Any, Optional
import json
import openai
import os
from datetime import datetime

from agent.agent_state import (
    AgentState, 
    UserIntent, 
    ReservationParams,
    RestaurantCandidate,
    SearchResults,
    get_missing_critical_params,
    is_state_complete_for_search
)
from agent.agent_prompts import (
    format_system_prompt,
    format_conversation_history,
    CLASSIFY_INTENT_PROMPT,
    EXTRACT_PARAMETERS_PROMPT,
    RANK_RESTAURANTS_PROMPT,
    ASK_USER_PROMPT,
    PROPOSE_ALTERNATIVE_PROMPT,
    format_top_3_for_user,
    SUCCESS_MESSAGE,
    FALLBACK_MESSAGE,
    ERROR_MESSAGE
)
from agent.agent_tools import ToolRegistry

# ===========================================================
# CONFIGURACIÓN
# ===========================================================

# Inicializar OpenAI (asegúrate de tener OPENAI_API_KEY en tu .env)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Inicializar herramientas
tools = ToolRegistry()

# Modelo a usar (puedes cambiarlo)
LLM_MODEL = "gpt-4o-mini"  # o "gpt-4o" para más potencia


# ===========================================================
# HELPER: LLAMADA A LLM
# ===========================================================

def call_llm(
    prompt: str, 
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    response_format: Optional[Dict[str, Any]] = None
) -> str:
    """
    Wrapper para llamadas a OpenAI.
    
    Args:
        prompt: El prompt del usuario
        system_prompt: System prompt (opcional)
        temperature: Creatividad (0.0 = determinista, 1.0 = creativo)
        response_format: Para forzar JSON output
    
    Returns:
        Respuesta del LLM como string
    """
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": prompt})
    
    kwargs = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature
    }
    
    # Si queremos forzar JSON
    if response_format:
        kwargs["response_format"] = response_format
    
    try:
        response = openai.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR LLM] {str(e)}")
        return json.dumps({"error": str(e)})


# ===========================================================
# NODO 1: CLASIFICAR INTENCIÓN
# ===========================================================

def classify_intent_node(state: AgentState) -> AgentState:
    """
    Clasifica la intención del usuario.
    
    ¿Qué hace?
    ----------
    - Analiza el mensaje del usuario
    - Determina qué quiere hacer (buscar, reservar, cancelar...)
    - Identifica qué parámetros faltan
    - Asigna un nivel de confianza
    
    Actualiza:
    ---------
    - state["user_intent"]
    - state["current_step"]
    - state["agent_thoughts"]
    """
    
    print("\n🧠 [NODO: Clasificar Intención]")
    
    # Obtener último mensaje del usuario
    last_message = state["messages"][-1]["content"]
    conversation = format_conversation_history(state["messages"])
    
    # Construir prompt
    prompt = CLASSIFY_INTENT_PROMPT.format(
        user_message=last_message,
        conversation_history=conversation
    )
    
    # Llamar al LLM
    system = format_system_prompt()
    response = call_llm(prompt, system, temperature=0.3)
    
    # Parsear respuesta (debería ser JSON)
    try:
        # Limpiar posibles markdown backticks
        response_clean = response.strip()
        if response_clean.startswith("```"):
            response_clean = response_clean.split("```")[1]
            if response_clean.startswith("json"):
                response_clean = response_clean[4:]
        
        intent_data = json.loads(response_clean)
        
        user_intent = UserIntent(
            intent=intent_data.get("intent", "unclear"),
            confidence=intent_data.get("confidence", 0.5),
            missing_params=intent_data.get("missing_params", []),
            reasoning=intent_data.get("reasoning", "")
        )
        
        # Actualizar estado
        state["user_intent"] = user_intent
        state["current_step"] = "extract_parameters"
        state["agent_thoughts"].append(
            f"THOUGHT: Usuario quiere '{user_intent.intent}' con confianza {user_intent.confidence}. "
            f"Razonamiento: {user_intent.reasoning}"
        )
        
        print(f"  ✓ Intención: {user_intent.intent} ({user_intent.confidence:.2f} confianza)")
        print(f"  ✓ Parámetros faltantes: {user_intent.missing_params}")
        
    except Exception as e:
        print(f"  ✗ Error parseando intención: {e}")
        state["error"] = f"Error clasificando intención: {str(e)}"
        state["current_step"] = "error"
    
    return state


# ===========================================================
# NODO 2: EXTRAER PARÁMETROS
# ===========================================================

def extract_parameters_node(state: AgentState) -> AgentState:
    """
    Extrae parámetros de la conversación.
    
    ¿Qué hace?
    ----------
    - Analiza todo el historial de conversación
    - Extrae parámetros (ubicación, fecha, hora, tipo de comida, etc.)
    - Interpreta lenguaje natural ("esta noche" → 20:00)
    - Mantiene parámetros existentes si no se mencionan nuevos
    
    Actualiza:
    ---------
    - state["reservation_params"]
    - state["current_step"]
    """
    
    print("\n📝 [NODO: Extraer Parámetros]")
    
    last_message = state["messages"][-1]["content"]
    conversation = format_conversation_history(state["messages"])
    current_params = state.get("reservation_params")
    
    # Construir prompt
    prompt = EXTRACT_PARAMETERS_PROMPT.format(
        user_message=last_message,
        conversation_history=conversation,
        current_params=json.dumps(current_params.dict() if current_params else {}, indent=2),
        current_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # Llamar al LLM
    system = format_system_prompt()
    response = call_llm(prompt, system, temperature=0.2)
    
    try:
        # Limpiar respuesta
        response_clean = response.strip()
        if response_clean.startswith("```"):
            response_clean = response_clean.split("```")[1]
            if response_clean.startswith("json"):
                response_clean = response_clean[4:]
        
        params_data = json.loads(response_clean)
        
        # Crear objeto ReservationParams
        reservation_params = ReservationParams(**params_data)
        
        # Actualizar estado
        state["reservation_params"] = reservation_params
        state["current_step"] = "check_completeness"
        state["agent_thoughts"].append(
            f"THOUGHT: Extraídos parámetros - "
            f"Query: {reservation_params.query}, "
            f"Location: {reservation_params.location}, "
            f"Date: {reservation_params.date}, "
            f"Time: {reservation_params.time}, "
            f"People: {reservation_params.num_people}"
        )
        
        print(f"  ✓ Query: {reservation_params.query}")
        print(f"  ✓ Ubicación: {reservation_params.location}")
        print(f"  ✓ Fecha: {reservation_params.date}")
        print(f"  ✓ Hora: {reservation_params.time}")
        print(f"  ✓ Personas: {reservation_params.num_people}")
        
    except Exception as e:
        print(f"  ✗ Error extrayendo parámetros: {e}")
        state["error"] = f"Error extrayendo parámetros: {str(e)}"
        state["current_step"] = "error"
    
    return state


# ===========================================================
# NODO 3: VERIFICAR COMPLETITUD
# ===========================================================

def check_completeness_node(state: AgentState) -> AgentState:
    """
    Verifica si tenemos suficiente información para proceder.
    
    ¿Qué hace?
    ----------
    - Verifica parámetros críticos (query, location, date, time, people)
    - Decide si puede buscar o necesita preguntar al usuario
    
    Actualiza:
    ---------
    - state["current_step"] → "search" o "ask_user"
    - state["needs_user_input"]
    """
    
    print("\n🔍 [NODO: Verificar Completitud]")
    
    # Verificar si podemos buscar
    can_search = is_state_complete_for_search(state)
    missing = get_missing_critical_params(state)
    
    if can_search and not missing:
        # Tenemos todo, podemos buscar
        state["current_step"] = "search"
        state["needs_user_input"] = False
        state["agent_thoughts"].append(
            "THOUGHT: Tengo toda la información necesaria. Procedo a buscar restaurantes."
        )
        print("  ✓ Información completa. Procediendo a búsqueda...")
    else:
        # Falta información, necesitamos preguntar
        state["current_step"] = "ask_user"
        state["needs_user_input"] = True
        state["agent_thoughts"].append(
            f"THOUGHT: Falta información crítica: {missing}. Debo preguntar al usuario."
        )
        print(f"  ⚠ Información incompleta. Falta: {missing}")
    
    return state


# ===========================================================
# NODO 4: PREGUNTAR AL USUARIO
# ===========================================================

def ask_user_node(state: AgentState) -> AgentState:
    """
    Genera una pregunta natural para obtener información faltante.
    
    ¿Qué hace?
    ----------
    - Identifica qué parámetros faltan
    - Genera UNA pregunta fluida que cubra todo
    - No usa formato de formulario, es conversacional
    
    Actualiza:
    ---------
    - state["messages"] con la pregunta del agente
    - state["current_step"] → "waiting_user"
    """
    
    print("\n💬 [NODO: Preguntar al Usuario]")
    
    missing = get_missing_critical_params(state)
    conversation = format_conversation_history(state["messages"])
    current_params = state.get("reservation_params")
    
    # Construir prompt
    prompt = ASK_USER_PROMPT.format(
        missing_params=", ".join(missing),
        conversation_history=conversation,
        current_params=json.dumps(current_params.dict() if current_params else {}, indent=2)
    )
    
    # Llamar al LLM
    system = format_system_prompt()
    question = call_llm(prompt, system, temperature=0.8)
    
    # Limpiar la respuesta (quitar posibles comillas)
    question = question.strip().strip('"').strip("'")
    
    # Añadir al historial
    state["messages"].append({
        "role": "assistant",
        "content": question
    })
    
    state["current_step"] = "waiting_user"
    state["agent_actions"].append(f"ACTION: Preguntar al usuario - {question}")
    
    print(f"  💬 Pregunta: {question}")
    print("\n⏸️  Esperando respuesta del usuario...")
    
    return state


# ===========================================================
# NODO 5: BUSCAR RESTAURANTES
# ===========================================================

def search_restaurants_node(state: AgentState) -> AgentState:
    """
    Busca restaurantes usando Google Places.
    
    ¿Qué hace?
    ----------
    - Usa los parámetros extraídos para buscar
    - Llama a la herramienta GooglePlaces
    - Normaliza y guarda los resultados
    
    Actualiza:
    ---------
    - state["search_results"]
    - state["current_step"] → "check_availability"
    """
    
    print("\n🔎 [NODO: Buscar Restaurantes]")
    
    params = state["reservation_params"]
    
    # Llamar a Google Places
    try:
        search_result = tools.google_places.run(
            query=params.query,
            location=params.location,
            radius=params.radius,
            price_level=params.price_level,
            extras=params.extras,
            max_travel_time=params.max_travel_time,
            travel_mode=params.travel_mode
        )
        
        # Convertir a RestaurantCandidate
        candidates = []
        for r in search_result["restaurants"]:
            candidate = RestaurantCandidate(
                place_id=r["place_id"],
                name=r["name"],
                address=r["address"],
                rating=r.get("rating"),
                user_ratings_total=r.get("user_ratings_total", 0),  # ✅ AÑADIDO
                price_level=r.get("price_level"),
                phone=r.get("phone"),
                website=r.get("website"),
                opening_hours=r.get("opening_hours")
            )
            candidates.append(candidate)
        
        # Guardar resultados
        state["search_results"] = SearchResults(
            restaurants=candidates,
            total_found=search_result["total_found"],
            search_params_used=search_result["search_params_used"]
        )
        
        state["current_step"] = "check_availability"
        state["agent_thoughts"].append(
            f"OBSERVATION: Encontrados {len(candidates)} restaurantes."
        )
        state["agent_actions"].append(
            f"ACTION: Búsqueda en Google Places con query='{params.query}', location='{params.location}'"
        )
        
        print(f"  ✓ Encontrados {len(candidates)} restaurantes")
        for c in candidates[:3]:
            print(f"    - {c.name} ⭐ {c.rating}")
        
    except Exception as e:
        print(f"  ✗ Error en búsqueda: {e}")
        state["error"] = f"Error buscando restaurantes: {str(e)}"
        state["current_step"] = "error"
    
    return state


# ===========================================================
# NODO 6: VERIFICAR DISPONIBILIDAD
# ===========================================================

def check_availability_node(state: AgentState) -> AgentState:
    """
    Verifica disponibilidad en los restaurantes encontrados.
    
    ¿Qué hace?
    ----------
    - Para cada restaurante, consulta CoverManager
    - Actualiza si tiene API y si está disponible
    - Guarda horarios alternativos si no hay disponibilidad
    
    Actualiza:
    ---------
    - Cada RestaurantCandidate con info de disponibilidad
    - state["current_step"] → "rank"
    """
    
    print("\n📅 [NODO: Verificar Disponibilidad]")
    
    if not state.get("search_results"):
        state["error"] = "No hay resultados de búsqueda"
        state["current_step"] = "error"
        return state
    
    params = state["reservation_params"]
    restaurants = state["search_results"].restaurants
    
    for restaurant in restaurants:
        try:
            availability = tools.cover_manager.check_availability(
                place_id=restaurant.place_id,
                date=params.date,
                time=params.time,
                num_people=params.num_people,
                restaurant_name=restaurant.name,  # ✅ NUEVO
                website=restaurant.website,        # ✅ NUEVO
                rating=restaurant.rating,          # ✅ NUEVO
                user_ratings_total=getattr(restaurant, 'user_ratings_total', 0)  # ✅ NUEVO
            )
            
            # Actualizar restaurant
            restaurant.has_api_booking = availability["has_api_booking"]
            restaurant.available = availability["available"]
            restaurant.available_times = availability["available_times"]
            
            status = "✓ Disponible" if availability["available"] else "✗ No disponible"
            api_status = "con API" if availability["has_api_booking"] else "sin API"
            print(f"  {restaurant.name}: {status} ({api_status})")
            
        except Exception as e:
            print(f"  ⚠ Error verificando {restaurant.name}: {e}")
            restaurant.has_api_booking = False
            restaurant.available = None
    
    state["current_step"] = "rank"
    state["agent_thoughts"].append(
        "OBSERVATION: Disponibilidad verificada en todos los restaurantes."
    )
    
    return state


# ===========================================================
# NODO 7: GENERAR RANKING
# ===========================================================

def rank_restaurants_node(state: AgentState) -> AgentState:
    """
    Genera un TOP 3 inteligente basado en múltiples criterios.
    
    ¿Qué hace?
    ----------
    - Usa LLM para analizar y rankear restaurantes
    - Considera: rating, reviews, disponibilidad, precio, distancia
    - Genera razonamiento de por qué cada uno es buena opción
    
    Actualiza:
    ---------
    - state["top_3_restaurants"]
    - state["current_step"] → "present_options"
    """
    
    print("\n🏆 [NODO: Generar Ranking]")
    
    restaurants = state["search_results"].restaurants
    params = state["reservation_params"]
    
    # Preparar info para el LLM
    # Preparar info para el LLM
    restaurants_json = [
        {
            "place_id": r.place_id,
            "name": r.name,
            "address": r.address,
            "rating": r.rating,
            "user_ratings_total": getattr(r, 'user_ratings_total', 0),  # ✅ CAMBIO
            "price_level": r.price_level,
            "available": r.available,
            "has_api_booking": r.has_api_booking
        }
  
        for r in restaurants
    ]
    
    prompt = RANK_RESTAURANTS_PROMPT.format(
        search_params=json.dumps(params.dict(), indent=2),
        restaurants=json.dumps(restaurants_json, indent=2),
        user_preferences=json.dumps(params.user_preferences or {})
    )
    
    system = format_system_prompt()
    response = call_llm(prompt, system, temperature=0.5)
    
    try:
        # Parsear respuesta
        response_clean = response.strip()
        if response_clean.startswith("```"):
            response_clean = response_clean.split("```")[1]
            if response_clean.startswith("json"):
                response_clean = response_clean[4:]
        
        ranking_data = json.loads(response_clean)
        top_3_ids = [r["place_id"] for r in ranking_data["top_3"]]
        
        # Obtener los restaurantes completos y añadir scores
        top_3 = []
        for rank_item in ranking_data["top_3"]:
            restaurant = next(r for r in restaurants if r.place_id == rank_item["place_id"])
            restaurant.agent_score = rank_item["agent_score"]
            restaurant.score_reasoning = rank_item["score_reasoning"]
            top_3.append(restaurant)
        
        state["top_3_restaurants"] = top_3
        state["current_step"] = "present_options"
        state["agent_thoughts"].append(
            f"THOUGHT: Generado TOP 3. Mejor opción: {top_3[0].name} (score: {top_3[0].agent_score})"
        )
        
        print(f"  🥇 {top_3[0].name} - Score: {top_3[0].agent_score}")
        print(f"  🥈 {top_3[1].name} - Score: {top_3[1].agent_score}")
        print(f"  🥉 {top_3[2].name} - Score: {top_3[2].agent_score}")
        
    except Exception as e:
        print(f"  ✗ Error generando ranking: {e}")
        # Fallback: usar los 3 primeros
        state["top_3_restaurants"] = restaurants[:3]
        state["current_step"] = "present_options"
    
    return state


# ===========================================================
# NODO 8: PRESENTAR OPCIONES
# ===========================================================

def present_options_node(state: AgentState) -> AgentState:
    """
    Presenta el TOP 3 al usuario y espera su elección.
    
    ¿Qué hace?
    ----------
    - Formatea el TOP 3 de forma atractiva
    - Pide al usuario que elija
    - Activa flag de HITL
    
    Actualiza:
    ---------
    - state["messages"] con el TOP 3
    - state["needs_user_input"] = True
    - state["current_step"] → "waiting_selection"
    """
    
    print("\n📋 [NODO: Presentar Opciones]")
    
    top_3 = state["top_3_restaurants"]
    
    # Formatear mensaje
    formatted_list = format_top_3_for_user([
        {
            "name": r.name,
            "rating": r.rating,
            "address": r.address,
            "score_reasoning": r.score_reasoning
        }
        for r in top_3
    ])
    
    message = f"¡Perfecto! He encontrado estos restaurantes que podrían interesarte:\n\n{formatted_list}\n\n¿Cuál prefieres? (responde con el número 1, 2 o 3)"
    
    state["messages"].append({
        "role": "assistant",
        "content": message
    })
    
    state["needs_user_input"] = True
    state["current_step"] = "waiting_selection"
    state["agent_actions"].append("ACTION: Presentar TOP 3 y esperar selección del usuario")
    
    print("  ✓ TOP 3 presentado al usuario")
    print("⏸️  Esperando selección del usuario...")
    
    return state


# ===========================================================
# NODO 9: RESERVAR RESTAURANTE (VIA API)
# ===========================================================

def book_restaurant_node(state: AgentState) -> AgentState:
    """
    Intenta hacer la reserva vía API.
    
    ¿Qué hace?
    ----------
    - Llama a CoverManager para hacer la reserva
    - Si tiene éxito → finaliza
    - Si falla o no tiene API → activa fallback a voz
    
    Actualiza:
    ---------
    - state["booking_status"]
    - state["booking_confirmation"]
    - state["current_step"] → "finalize" o "fallback_voice"
    """
    
    print("\n📞 [NODO: Reservar por API]")
    
    restaurant = state["selected_restaurant"]
    params = state["reservation_params"]
    
    # Verificar si el restaurante tiene API
    if not restaurant.has_api_booking:
        print(f"  ⚠ {restaurant.name} no tiene API de reservas")
        state["booking_status"] = "api_failed"
        state["current_step"] = "fallback_voice"
        state["agent_thoughts"].append(
            f"THOUGHT: {restaurant.name} no tiene API. Debo intentar por llamada telefónica."
        )
        return state
    
    # Intentar reserva
    try:
        result = tools.cover_manager.make_reservation(
            place_id=restaurant.place_id,
            restaurant_name=restaurant.name,
            date=params.date,
            time=params.time,
            num_people=params.num_people,
            user_name="Usuario",  # TODO: Obtener del contexto
            user_phone=None
        )
        
        if result["success"]:
            state["booking_status"] = "api_success"
            state["booking_confirmation"] = result["confirmation_details"]
            state["current_step"] = "finalize"
            state["agent_thoughts"].append(
                f"OBSERVATION: Reserva exitosa por API. ID: {result['booking_id']}"
            )
            print(f"  ✓ Reserva confirmada: {result['booking_id']}")
        else:
            state["booking_status"] = "api_failed"
            state["current_step"] = "fallback_voice"
            state["agent_thoughts"].append(
                f"OBSERVATION: API falló. Error: {result['error']}. Intentaré por voz."
            )
            print(f"  ✗ API falló: {result['error']}")
    
    except Exception as e:
        print(f"  ✗ Error en reserva: {e}")
        state["booking_status"] = "api_failed"
        state["current_step"] = "fallback_voice"
    
    return state


# ===========================================================
# NODO 10: FALLBACK A VOZ
# ===========================================================

def fallback_voice_node(state: AgentState) -> AgentState:
    """
    Fallback: intenta reservar por llamada telefónica.
    
    ¿Qué hace?
    ----------
    - Informa al usuario que llamará al restaurante
    - Usa Twilio + ElevenLabs para llamar
    - Analiza la transcripción para confirmar reserva
    
    Actualiza:
    ---------
    - state["voice_call_transcript"]
    - state["booking_status"]
    - state["current_step"] → "finalize"
    """
    
    print("\n📞 [NODO: Fallback a Voz]")
    
    restaurant = state["selected_restaurant"]
    params = state["reservation_params"]
    
    # Informar al usuario
    state["messages"].append({
        "role": "assistant",
        "content": FALLBACK_MESSAGE
    })
    
    print(f"  📞 Llamando a {restaurant.name}...")
    
    try:
        result = tools.twilio_voice.make_voice_reservation(
            restaurant_name=restaurant.name,
            phone=restaurant.phone,
            date=params.date,
            time=params.time,
            num_people=params.num_people
        )
        
        state["voice_call_transcript"] = result["transcript"]
        
        if result["success"] and result["confirmation"]:
            state["booking_status"] = "voice_success"
            state["booking_confirmation"] = {
                "restaurant": restaurant.name,
                "date": params.date,
                "time": params.time,
                "num_people": params.num_people,
                "phone": restaurant.phone,
                "method": "voice",
                "transcript": result["transcript"]
            }
            state["current_step"] = "finalize"
            print(f"  ✓ Reserva confirmada por teléfono")
        else:
            state["booking_status"] = "voice_failed"
            state["error"] = result["message"]
            state["current_step"] = "error"
            print(f"  ✗ Llamada falló: {result['message']}")
        
        state["agent_thoughts"].append(
            f"OBSERVATION: Llamada completada. Resultado: {result['message']}"
        )
    
    except Exception as e:
        print(f"  ✗ Error en llamada: {e}")
        state["booking_status"] = "voice_failed"
        state["error"] = str(e)
        state["current_step"] = "error"
    
    return state


# ===========================================================
# NODO 11: FINALIZAR
# ===========================================================

def finalize_node(state: AgentState) -> AgentState:
    """
    Nodo final: genera mensaje de éxito.
    
    ¿Qué hace?
    ----------
    - Confirma la reserva al usuario
    - Proporciona todos los detalles
    - Marca el proceso como completado
    
    Actualiza:
    ---------
    - state["messages"] con confirmación
    - state["current_step"] → "completed"
    """
    
    print("\n✅ [NODO: Finalizar]")
    
    confirmation = state["booking_confirmation"]
    
    message = SUCCESS_MESSAGE.format(
        restaurant_name=confirmation["restaurant"],
        date=confirmation["date"],
        time=confirmation["time"],
        num_people=confirmation["num_people"],
        phone=confirmation.get("phone", "No disponible"),
        confirmation_details=f"Método: {confirmation.get('method', 'API')}\nReferencia: {confirmation.get('booking_reference', 'N/A')}"
    )
    
    state["messages"].append({
        "role": "assistant",
        "content": message
    })
    
    state["current_step"] = "completed"
    state["agent_thoughts"].append(
        "THOUGHT: Reserva completada exitosamente. Proceso finalizado."
    )
    
    print(f"  ✅ Reserva confirmada en {confirmation['restaurant']}")
    print(f"  📅 {confirmation['date']} a las {confirmation['time']}")
    
    return state


# ===========================================================
# NODO 12: ERROR HANDLER
# ===========================================================

def error_node(state: AgentState) -> AgentState:
    """
    Maneja errores y proporciona feedback al usuario.
    
    ¿Qué hace?
    ----------
    - Muestra mensaje de error al usuario
    - Sugiere alternativas si es posible
    - Marca el proceso como completado con error
    
    Actualiza:
    ---------
    - state["messages"] con mensaje de error
    - state["current_step"] → "completed"
    """
    
    print("\n❌ [NODO: Error]")
    
    error_msg = state.get("error", "Error desconocido")
    
    message = ERROR_MESSAGE.format(
        error_details=error_msg
    )
    
    state["messages"].append({
        "role": "assistant",
        "content": message
    })
    
    state["current_step"] = "completed"
    
    print(f"  ❌ Error: {error_msg}")
    
    return state


# ===========================================================
# EJEMPLO DE USO
# ===========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST DE NODOS")
    print("=" * 60)
    
    from agent_state import create_initial_state
    
    # Crear estado inicial
    state = create_initial_state("Resérvame una pizzería en Navalcarnero para 4 personas mañana a las 21:00")
    
    # Test Nodo 1: Clasificar
    state = classify_intent_node(state)
    
    # Test Nodo 2: Extraer
    state = extract_parameters_node(state)
    
    # Test Nodo 3: Verificar completitud
    state = check_completeness_node(state)
    
    # Si está completo, buscar
    if state["current_step"] == "search":
        state = search_restaurants_node(state)
        state = check_availability_node(state)
        state = rank_restaurants_node(state)
        state = present_options_node(state)
    
    print("\n" + "=" * 60)
    print("ESTADO FINAL:")
    print("=" * 60)
    print(f"Step: {state['current_step']}")
    print(f"Needs user input: {state['needs_user_input']}")
    print(f"Thoughts: {len(state['agent_thoughts'])} pensamientos registrados")
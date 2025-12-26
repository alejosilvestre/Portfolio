"""
===========================================================
AGENT GRAPH - Grafo de Estados del Agente con LangGraph
===========================================================

Este es el CORAZÓN del agente: define cómo fluye la información
entre los nodos y cómo se toman las decisiones.

¿Por qué LangGraph?
-------------------
- Permite ciclos y reintentos (a diferencia de cadenas lineales)
- Gestión de estado automática
- Puntos de interrupción para Human-in-the-Loop
- Fácil visualización y debugging
- Escalable para añadir nuevos nodos

Arquitectura del Grafo:
-----------------------
START
  ↓
classify_intent → extract_parameters → check_completeness
                                            ↓
                                    ¿Completo?
                                    ↙        ↘
                              ask_user    search_restaurants
                                  ↓              ↓
                        (espera usuario)   check_availability
                                              ↓
                                         rank_restaurants
                                              ↓
                                      present_options
                                              ↓
                                    (espera selección)
                                              ↓
                                       book_restaurant
                                        ↙          ↘
                                   ¿Éxito?      fallback_voice
                                      ↓              ↓
                                  finalize      finalize/error
                                      ↓
                                     END

Decisiones Condicionales:
-------------------------
1. check_completeness → ask_user o search
2. book_restaurant → finalize o fallback_voice
3. Cualquier error → error_node
"""

from typing import Literal, Optional
from langgraph.graph import StateGraph, END
from agent.agent_state import AgentState
from agent.agent_nodes import (
    classify_intent_node,
    extract_parameters_node,
    check_completeness_node,
    ask_user_node,
    search_restaurants_node,
    check_availability_node,
    rank_restaurants_node,
    present_options_node,
    book_restaurant_node,
    fallback_voice_node,
    finalize_node,
    error_node
)


# ===========================================================
# FUNCIONES DE ENRUTAMIENTO (CONDITIONAL EDGES)
# ===========================================================

def route_after_completeness_check(state: AgentState) -> Literal["ask_user", "search", "error"]:
    """
    Decide qué hacer después de verificar completitud.
    
    Lógica:
    -------
    - Si hay error → error_node
    - Si falta info → ask_user_node
    - Si está completo → search_restaurants_node
    """
    if state.get("error"):
        return "error"
    
    if state.get("needs_user_input"):
        return "ask_user"
    
    return "search"


def route_after_asking_user(state: AgentState) -> Literal["waiting_user"]:
    """
    Después de preguntar, el agente SIEMPRE espera al usuario.
    
    Este es un punto de interrupción (HITL).
    El grafo se pausará aquí hasta que se añada un nuevo mensaje.
    """
    return "waiting_user"


def route_after_presenting_options(state: AgentState) -> Literal["waiting_selection"]:
    """
    Después de presentar el TOP 3, el agente espera la selección.
    
    Otro punto de interrupción (HITL).
    """
    return "waiting_selection"


def route_after_booking(state: AgentState) -> Literal["finalize", "fallback_voice", "error"]:
    """
    Decide qué hacer después de intentar la reserva por API.
    
    Lógica:
    -------
    - Si api_success → finalize
    - Si api_failed → fallback_voice
    - Si error crítico → error
    """
    booking_status = state.get("booking_status")
    
    if state.get("error") and booking_status == "voice_failed":
        return "error"
    
    if booking_status == "api_success":
        return "finalize"
    
    if booking_status == "api_failed":
        return "fallback_voice"
    
    return "error"


def route_after_voice_fallback(state: AgentState) -> Literal["finalize", "error"]:
    """
    Decide qué hacer después de intentar reserva por voz.
    
    Lógica:
    -------
    - Si voice_success → finalize
    - Si voice_failed → error
    """
    booking_status = state.get("booking_status")
    
    if booking_status == "voice_success":
        return "finalize"
    
    return "error"


def should_continue_or_end(state: AgentState) -> Literal["continue", "end"]:
    """
    Determina si el proceso ha terminado o debe continuar.
    
    Usado para detectar ciclos infinitos y forzar terminación.
    """
    iteration_count = state.get("iteration_count", 0)
    current_step = state.get("current_step", "")
    
    # Protección contra loops infinitos
    if iteration_count > 20:
        print("⚠️  ADVERTENCIA: Demasiadas iteraciones. Forzando terminación.")
        return "end"
    
    # Si llegamos a un estado terminal
    if current_step in ["completed", "error", "waiting_user", "waiting_selection"]:
        return "end"
    
    return "continue"


# ===========================================================
# CONSTRUCCIÓN DEL GRAFO
# ===========================================================

def create_agent_graph() -> StateGraph:
    """
    Construye y retorna el grafo completo del agente.
    
    Returns:
        StateGraph compilado y listo para ejecutar
    """
    
    # Inicializar el grafo con el esquema de estado
    workflow = StateGraph(AgentState)
    
    # ===========================================================
    # AÑADIR NODOS AL GRAFO
    # ===========================================================
    
    # Nodos de razonamiento
    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("extract_parameters", extract_parameters_node)
    workflow.add_node("check_completeness", check_completeness_node)
    workflow.add_node("ask_user", ask_user_node)
    
    # Nodos de búsqueda
    workflow.add_node("search", search_restaurants_node)
    workflow.add_node("check_availability", check_availability_node)
    workflow.add_node("rank", rank_restaurants_node)
    workflow.add_node("present_options", present_options_node)
    
    # Nodos de reserva
    workflow.add_node("book", book_restaurant_node)
    workflow.add_node("fallback_voice", fallback_voice_node)
    
    # Nodos finales
    workflow.add_node("finalize", finalize_node)
    workflow.add_node("error", error_node)
    
    # ===========================================================
    # DEFINIR EDGES (CONEXIONES ENTRE NODOS)
    # ===========================================================
    
    # PUNTO DE ENTRADA: Siempre empezamos clasificando la intención
    workflow.set_entry_point("classify_intent")
    
    # Flujo lineal inicial
    workflow.add_edge("classify_intent", "extract_parameters")
    workflow.add_edge("extract_parameters", "check_completeness")
    
    # DECISIÓN CONDICIONAL: ¿Tenemos toda la info?
    workflow.add_conditional_edges(
        "check_completeness",
        route_after_completeness_check,
        {
            "ask_user": "ask_user",
            "search": "search",
            "error": "error"
        }
    )
    
    # PUNTO DE INTERRUPCIÓN: Después de preguntar, esperamos al usuario
    # En producción, el grafo se pausa aquí
    workflow.add_edge("ask_user", END)
    
    # Flujo de búsqueda y ranking
    workflow.add_edge("search", "check_availability")
    workflow.add_edge("check_availability", "rank")
    workflow.add_edge("rank", "present_options")
    
    # PUNTO DE INTERRUPCIÓN: Después de presentar opciones, esperamos selección
    workflow.add_edge("present_options", END)
    
    # DECISIÓN CONDICIONAL: ¿La reserva por API funcionó?
    workflow.add_conditional_edges(
        "book",
        route_after_booking,
        {
            "finalize": "finalize",
            "fallback_voice": "fallback_voice",
            "error": "error"
        }
    )
    
    # DECISIÓN CONDICIONAL: ¿La llamada funcionó?
    workflow.add_conditional_edges(
        "fallback_voice",
        route_after_voice_fallback,
        {
            "finalize": "finalize",
            "error": "error"
        }
    )
    
    # Nodos finales van a END
    workflow.add_edge("finalize", END)
    workflow.add_edge("error", END)
    
    # Compilar el grafo
    return workflow.compile()


# ===========================================================
# FUNCIONES HELPER PARA EJECUTAR EL GRAFO
# ===========================================================

def run_agent_step(graph, state: AgentState) -> AgentState:
    """
    Ejecuta UN PASO del agente.
    
    Útil para ejecución interactiva donde el usuario puede 
    responder en cada punto de interrupción.
    
    Args:
        graph: Grafo compilado
        state: Estado actual
    
    Returns:
        Estado actualizado después de ejecutar un paso
    """
    result = graph.invoke(state)
    return result


def run_agent_until_completion(graph, state: AgentState, max_iterations: int = 10) -> AgentState:
    """
    Ejecuta el agente hasta que se complete o alcance max_iterations.
    
    Para testing o ejecución autónoma sin HITL.
    
    Args:
        graph: Grafo compilado
        state: Estado inicial
        max_iterations: Máximo de iteraciones permitidas
    
    Returns:
        Estado final
    """
    for i in range(max_iterations):
        print(f"\n{'='*60}")
        print(f"ITERACIÓN {i+1}/{max_iterations}")
        print(f"{'='*60}")
        
        # Incrementar contador de iteraciones
        state["iteration_count"] = i
        
        # Ejecutar un paso
        state = graph.invoke(state)
        
        # Verificar si necesitamos parar
        current_step = state.get("current_step", "")
        
        if current_step in ["completed", "waiting_user", "waiting_selection"]:
            print(f"\n✓ Proceso detenido en: {current_step}")
            break
        
        if state.get("error"):
            print(f"\n✗ Error detectado: {state['error']}")
            break
    
    return state


def resume_agent_after_user_input(
    graph, 
    state: AgentState, 
    user_message: str
) -> AgentState:
    """
    Reanuda el agente después de que el usuario responda.
    
    Esta función es clave para el flujo HITL (Human-in-the-Loop).
    
    Args:
        graph: Grafo compilado
        state: Estado pausado
        user_message: Nueva respuesta del usuario
    
    Returns:
        Estado actualizado después de procesar la respuesta
    """
    # Añadir el mensaje del usuario al historial
    state["messages"].append({
        "role": "user",
        "content": user_message
    })
    
    # Resetear flag de input
    state["needs_user_input"] = False
    
    # Determinar en qué punto estábamos
    current_step = state.get("current_step", "")
    
    if current_step == "waiting_user":
        # El usuario respondió a una pregunta de info faltante
        # Volvemos a extraer parámetros con la nueva info
        state["current_step"] = "extract_parameters"
        state = extract_parameters_node(state)
        state = check_completeness_node(state)
        
        # Si ahora está completo, continuar con búsqueda
        if state["current_step"] == "search":
            state = run_agent_until_completion(graph, state)
    
    elif current_step == "waiting_selection":
        # El usuario seleccionó un restaurante del TOP 3
        selection = parse_restaurant_selection(user_message, state["top_3_restaurants"])
        
        if selection:
            state["selected_restaurant"] = selection
            state["current_step"] = "book"
            
            # Continuar con la reserva
            state = book_restaurant_node(state)
            
            # Ejecutar hasta completar
            if state["current_step"] in ["finalize", "fallback_voice"]:
                state = run_agent_until_completion(graph, state)
        else:
            # No entendimos la selección, preguntar de nuevo
            state["messages"].append({
                "role": "assistant",
                "content": "No he entendido tu selección. Por favor, responde con 1, 2 o 3."
            })
            state["current_step"] = "waiting_selection"
    
    return state


def parse_restaurant_selection(message: str, top_3: list) -> Optional[object]:
    """
    Parsea la selección del usuario (1, 2, 3 o nombre del restaurante).
    
    Args:
        message: Mensaje del usuario
        top_3: Lista de RestaurantCandidate
    
    Returns:
        RestaurantCandidate seleccionado o None
    """
    message_lower = message.lower().strip()
    
    # Intenta parsear como número
    if message_lower in ["1", "primero", "primer", "uno"]:
        return top_3[0]
    elif message_lower in ["2", "segundo", "dos"]:
        return top_3[1]
    elif message_lower in ["3", "tercero", "tres"]:
        return top_3[2]
    
    # Intenta buscar por nombre
    for restaurant in top_3:
        if restaurant.name.lower() in message_lower:
            return restaurant
    
    return None


# ===========================================================
# VISUALIZACIÓN DEL GRAFO (OPCIONAL)
# ===========================================================

def visualize_graph(graph):
    """
    Genera una representación visual del grafo.
    
    Requiere: graphviz instalado
    """
    try:
        from IPython.display import Image, display
        display(Image(graph.get_graph().draw_mermaid_png()))
    except ImportError:
        print("Para visualizar el grafo, instala: pip install graphviz pygraphviz")
    except Exception as e:
        print(f"Error visualizando grafo: {e}")


# ===========================================================
# EJEMPLO DE USO
# ===========================================================

if __name__ == "__main__":
    from agent.agent_state import create_initial_state
    
    print("=" * 60)
    print("CREANDO GRAFO DEL AGENTE")
    print("=" * 60)
    
    # Crear el grafo
    agent_graph = create_agent_graph()
    print("✓ Grafo creado exitosamente")
    
    print("\n" + "=" * 60)
    print("TEST 1: FLUJO COMPLETO (con info completa)")
    print("=" * 60)
    
    # Crear estado con mensaje completo
    state = create_initial_state(
        "Resérvame una pizzería en Navalcarnero para 4 personas mañana a las 21:00"
    )
    
    # Ejecutar hasta que se pause o complete
    final_state = run_agent_until_completion(agent_graph, state, max_iterations=15)
    
    print("\n" + "=" * 60)
    print("RESULTADO:")
    print("=" * 60)
    print(f"Estado final: {final_state['current_step']}")
    print(f"Mensajes intercambiados: {len(final_state['messages'])}")
    
    if final_state.get("top_3_restaurants"):
        print(f"TOP 3 generado: {len(final_state['top_3_restaurants'])} restaurantes")
    
    if final_state.get("booking_confirmation"):
        print("✅ Reserva completada")
    
    print("\n" + "=" * 60)
    print("TEST 2: FLUJO CON INFO INCOMPLETA (HITL)")
    print("=" * 60)
    
    # Crear estado con mensaje incompleto
    state2 = create_initial_state("Resérvame una pizzería")
    
    # Ejecutar hasta que pida info
    state2 = run_agent_until_completion(agent_graph, state2, max_iterations=5)
    
    print(f"\nEstado: {state2['current_step']}")
    if state2["needs_user_input"]:
        print("✓ Agente está esperando respuesta del usuario")
        print(f"Última pregunta: {state2['messages'][-1]['content']}")
        
        # Simular respuesta del usuario
        print("\n[Simulando respuesta del usuario...]")
        state2 = resume_agent_after_user_input(
            agent_graph,
            state2,
            "En Navalcarnero, para 4 personas, mañana a las 21:00"
        )
        
        print(f"Estado después de respuesta: {state2['current_step']}")
    
    print("\n" + "=" * 60)
    print("✓ Tests completados")
    print("=" * 60)

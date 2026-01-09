"""
===========================================================
GRAPH - Grafo del Agente con LangGraph
===========================================================

Implementa el bucle ReAct con nodos explícitos:
- brain: LLM decide qué hacer
- execute: Ejecuta la herramienta
- respond: Envía respuesta al usuario
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
import json
import re

from agent.state import AgentState, create_initial_state
from agent.prompts import format_prompt
from agent.tools import execute_tool, TOOLS_MAP, get_search_results

# Config
from config.settings import load_config
config = load_config()

# Constantes
MAX_ITERATIONS = 10


# ===========================================================
# LLM
# ===========================================================

def get_llm():
    return ChatOpenAI(
        model=config["MODEL_NAME"],
        temperature=config["TEMPERATURE"],
        openai_api_key=config["OPENAI_API_KEY"]
    )


# ===========================================================
# FORMATEO DE CONTEXTO
# ===========================================================

def format_conversation(messages: list) -> str:
    """Formatea el historial de mensajes para el prompt."""
    if not messages:
        return "Sin mensajes previos"
    
    lines = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            lines.append(f"Usuario: {msg.content}")
        elif isinstance(msg, AIMessage):
            lines.append(f"Asistente: {msg.content}")
        elif isinstance(msg, dict):
            role = "Usuario" if msg.get("role") == "user" else "Asistente"
            lines.append(f"{role}: {msg.get('content', '')}")
    
    return "\n".join(lines[-10:])  # Últimos 10 mensajes


def format_knowledge(knowledge: dict) -> str:
    """Formatea el conocimiento adquirido para el prompt."""
    if not knowledge:
        return "Ninguno"
    
    lines = []
    
    # Lugares encontrados
    if "places" in knowledge:
        lines.append("**Lugares encontrados:**")
        for p in knowledge["places"]:
            status = ""
            if p.get("available") is True:
                status = "✅ Disponible"
            elif p.get("available") is False:
                times = ", ".join(p.get("available_times", []))
                status = f"⚠️ Alternativas: {times}"
            elif p.get("has_api") is False:
                status = "📞 Solo teléfono"
            
            rating = f"⭐{p.get('rating')}" if p.get('rating') else ""
            lines.append(f"  - {p.get('name')} {rating} {status}")
    
    # Reserva confirmada
    if "booking" in knowledge:
        b = knowledge["booking"]
        lines.append(f"**Reserva:** {b.get('details', {}).get('restaurant')} - {b.get('booking_id')}")
    
    # Búsqueda web
    if "web_search" in knowledge:
        ws = knowledge["web_search"]
        lines.append(f"**Búsqueda web:** {ws.get('query')}")
    
    return "\n".join(lines) if lines else "Ninguno"


# ===========================================================
# PARSEO DE RESPUESTA DEL LLM
# ===========================================================

def parse_llm_response(text: str) -> dict:
    """Parsea la respuesta del LLM en formato THOUGHT/ACTION/ACTION_INPUT."""
    result = {
        "thought": "",
        "action": "respond",
        "action_input": {"message": text}
    }
    
    # Extraer THOUGHT
    thought_match = re.search(r'THOUGHT:\s*(.+?)(?=ACTION:|$)', text, re.DOTALL | re.IGNORECASE)
    if thought_match:
        result["thought"] = thought_match.group(1).strip()
    
    # Extraer ACTION
    action_match = re.search(r'ACTION:\s*(\w+)', text, re.IGNORECASE)
    if action_match:
        result["action"] = action_match.group(1).strip().lower()
    
    # Extraer ACTION_INPUT
    input_match = re.search(r'ACTION_INPUT:\s*(\{.+\})', text, re.DOTALL | re.IGNORECASE)
    if input_match:
        try:
            json_str = input_match.group(1).strip()
            # Buscar el cierre del JSON
            brace_count = 0
            end_idx = 0
            for i, char in enumerate(json_str):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            json_str = json_str[:end_idx]
            result["action_input"] = json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    return result


# ===========================================================
# NODO: BRAIN (LLM decide)
# ===========================================================

def brain_node(state: AgentState) -> AgentState:
    """El LLM analiza la situación y decide qué hacer."""
    print(f"\n🧠 [BRAIN] Iteración {state.get('iterations', 0)}")
    
    llm = get_llm()
    
    # Formatear contexto para el prompt
    conversation = format_conversation(state.get("messages", []))
    knowledge = format_knowledge(state.get("knowledge", {}))
    last_obs = state.get("last_observation") or "Ninguna (inicio de conversación)"
    
    # Construir prompt completo
    prompt = format_prompt(conversation, knowledge, last_obs)
    
    # Llamar al LLM
    print("   Pensando...")
    response = llm.invoke([HumanMessage(content=prompt)])
    output = response.content
    
    # Parsear respuesta
    parsed = parse_llm_response(output)
    
    print(f"   💭 Thought: {parsed['thought'][:80]}..." if parsed['thought'] else "   💭 (sin thought)")
    print(f"   🎯 Action: {parsed['action']}")
    print(f"   📥 Args: {parsed['action_input']}")
    
    # Actualizar estado
    state["next_tool"] = parsed["action"]
    state["tool_args"] = parsed["action_input"]
    state["iterations"] = state.get("iterations", 0) + 1
    
    # Si es respond, ir directamente a responder (no es una herramienta real)
    if parsed["action"] == "respond":
        state["status"] = "responding"
    else:
        state["status"] = "executing"
    
    return state


# ===========================================================
# NODO: EXECUTE (Ejecuta herramienta)
# ===========================================================

def execute_node(state: AgentState) -> AgentState:
    """Ejecuta la herramienta decidida por el brain."""
    tool_name = state.get("next_tool")
    tool_args = state.get("tool_args", {})
    
    print(f"\n⚡ [EXECUTE] {tool_name}")
    
    # respond no es una herramienta real, es para responder al usuario
    if tool_name == "respond":
        # Cambiar a responding para que vaya al nodo respond
        state["status"] = "responding"
        return state
    
    # Ejecutar herramienta
    result = execute_tool(tool_name, tool_args)
    
    print(f"   📤 Resultado: {result[:100]}..." if len(str(result)) > 100 else f"   📤 Resultado: {result}")
    
    # Actualizar conocimiento según la herramienta
    knowledge = state.get("knowledge", {})
    
    if tool_name == "maps_search" and "ERROR" not in result:
        # Guardar lugares encontrados
        knowledge["places"] = get_search_results()
    
    elif tool_name == "check_availability" and "ERROR" not in result:
        # Actualizar disponibilidad en places
        knowledge["places"] = get_search_results()
    
    elif tool_name == "make_booking" and "confirmada" in result.lower():
        knowledge["booking"] = {"confirmed": True, "details": result}
    
    elif tool_name == "web_search" and "ERROR" not in result:
        knowledge["web_search"] = {"query": tool_args.get("query"), "result": result[:500]}
    
    # Actualizar estado
    state["last_observation"] = result
    state["knowledge"] = knowledge
    state["status"] = "thinking"  # Volver al brain para procesar resultado
    
    return state


# ===========================================================
# NODO: RESPOND (Responde al usuario)
# ===========================================================

def respond_node(state: AgentState) -> AgentState:
    """Envía respuesta al usuario."""
    tool_args = state.get("tool_args", {})
    message = tool_args.get("message", "¿En qué puedo ayudarte?")
    
    print(f"\n💬 [RESPOND] {message[:80]}...")
    
    # Añadir mensaje del asistente
    state["messages"] = list(state.get("messages", [])) + [AIMessage(content=message)]
    state["status"] = "finished"
    
    return state


# ===========================================================
# ROUTING: Decide el siguiente nodo
# ===========================================================

def should_continue(state: AgentState) -> Literal["execute", "respond", "brain", "end"]:
    """Decide qué nodo ejecutar a continuación."""
    status = state.get("status", "thinking")
    iterations = state.get("iterations", 0)
    
    # Límite de iteraciones
    if iterations >= MAX_ITERATIONS:
        print(f"⚠️ Límite de iteraciones alcanzado ({MAX_ITERATIONS})")
        return "respond"
    
    if status == "executing":
        return "execute"
    elif status == "responding":
        return "respond"
    elif status == "thinking":
        return "brain"
    else:  # finished
        return "end"


# ===========================================================
# CONSTRUIR GRAFO
# ===========================================================

def create_graph():
    """Crea y compila el grafo del agente."""
    
    # Crear grafo
    workflow = StateGraph(AgentState)
    
    # Añadir nodos
    workflow.add_node("brain", brain_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("respond", respond_node)
    
    # Definir flujo
    workflow.set_entry_point("brain")
    
    # Routing condicional desde brain
    workflow.add_conditional_edges(
        "brain",
        should_continue,
        {
            "execute": "execute",
            "respond": "respond",
            "brain": "brain",
            "end": END
        }
    )
    
    # Después de execute, volver a brain
    workflow.add_edge("execute", "brain")
    
    # Después de respond, terminar
    workflow.add_edge("respond", END)
    
    # Compilar
    return workflow.compile()


# ===========================================================
# FUNCIÓN PRINCIPAL
# ===========================================================

_graph = None

def get_graph():
    """Obtiene el grafo (singleton)."""
    global _graph
    if _graph is None:
        _graph = create_graph()
    return _graph


def run_agent(messages: list) -> dict:
    """
    Ejecuta el agente.
    
    Args:
        messages: Lista de mensajes [{"role": "user/assistant", "content": "..."}]
    
    Returns:
        {"response": str, "messages": list, "knowledge": dict}
    """
    graph = get_graph()
    
    # Convertir mensajes
    lc_messages = []
    for m in messages:
        if isinstance(m, dict):
            if m["role"] == "user":
                lc_messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                lc_messages.append(AIMessage(content=m["content"]))
        else:
            lc_messages.append(m)
    
    # Estado inicial
    initial_state = create_initial_state(lc_messages)
    
    # Ejecutar grafo
    print("\n" + "=" * 50)
    print("🚀 AGENTE ReAct")
    print("=" * 50)
    
    final_state = graph.invoke(initial_state)
    
    # Extraer respuesta
    response = ""
    for msg in reversed(final_state.get("messages", [])):
        if isinstance(msg, AIMessage):
            response = msg.content
            break
    
    print(f"\n{'=' * 50}")
    print("✓ Completado")
    print("=" * 50)
    
    return {
        "response": response,
        "messages": final_state.get("messages", []),
        "knowledge": final_state.get("knowledge", {})
    }
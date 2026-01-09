"""
===========================================================
STATE - Estado del Agente
===========================================================

Define el estado que fluye a través del grafo.
"""

from typing import TypedDict, Literal, Optional, List, Dict, Any, Annotated
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Estado del agente que fluye por el grafo."""
    
    # Mensajes de la conversación (se acumulan)
    messages: Annotated[List, add_messages]
    
    # Conocimiento adquirido (lugares encontrados, disponibilidad, etc.)
    knowledge: Dict[str, Any]
    
    # Próxima herramienta a ejecutar
    next_tool: Optional[str]
    tool_args: Optional[Dict[str, Any]]
    
    # Resultado de la última herramienta
    last_observation: Optional[str]
    
    # Estado del flujo
    status: Literal["thinking", "executing", "responding", "finished"]
    
    # Contador de iteraciones (evita loops infinitos)
    iterations: int


def create_initial_state(messages: List = None) -> dict:
    """Crea el estado inicial del agente."""
    return {
        "messages": messages or [],
        "knowledge": {},
        "next_tool": None,
        "tool_args": None,
        "last_observation": None,
        "status": "thinking",
        "iterations": 0
    }
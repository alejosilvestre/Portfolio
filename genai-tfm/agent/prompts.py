"""
===========================================================
PROMPTS - System Prompt del Agente
===========================================================

El cerebro del agente. Un único prompt que contiene:
- Personalidad
- Herramientas disponibles y sus requisitos
- Cómo razonar (ReAct)
- Cuándo preguntar vs cuándo actuar
"""

import os
from datetime import datetime
from pathlib import Path


def _load_prompt_from_file(filename: str) -> str:
    """Load a prompt from a markdown file in the prompts directory."""
    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_path = prompts_dir / filename

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


# Load the system prompt from file
SYSTEM_PROMPT = _load_prompt_from_file("agent_system_prompt.md")


def format_prompt(
    conversation: str,
    knowledge: str = "Ninguno",
    last_observation: str = "Ninguna (inicio de conversación)"
) -> str:
    """Formatea el prompt con el contexto actual."""
    now = datetime.now()
    return SYSTEM_PROMPT.format(
        current_datetime=now.strftime("%Y-%m-%d %H:%M:%S (%A)"),
        today=now.strftime("%Y-%m-%d"),
        conversation=conversation,
        knowledge=knowledge,
        last_observation=last_observation
    )
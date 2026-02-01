"""
===========================================================
MAIN - Punto de Entrada del Agente
===========================================================
"""

import sys
import os
from pathlib import Path

# Path setup
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from config.settings import load_config

from agent.graph import run_agent
from agent.tools import clear_search_results
from backend.call_service import PUBLIC_URL, start_service

config = load_config()

# Iniciar el servicio de llamadas
print("🔄 Iniciando servicio de llamadas...")
CALL_SERVICE_PORT = int(os.getenv("CALL_SERVICE_PORT"))
call_service_thread = start_service(CALL_SERVICE_PORT)

if not call_service_thread:
    print("❌ Error: El servicio de llamadas no pudo iniciarse")
    print("   El agente funcionará sin capacidad de llamadas telefónicas\n")
else:
    print(f"✅ Servicio de llamadas listo\n")


def main():
    """Loop interactivo."""

    print("\n" + "=" * 50)
    print("🧠 Agente de Reservas (LangGraph)")
    print("=" * 50)
    print("Comandos: 'exit', 'reset'\n")

    messages = []

    while True:
        try:
            user_input = input("👤 Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 ¡Hasta luego!")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "salir", "quit"]:
            print("\n👋 ¡Hasta luego!")
            break

        if user_input.lower() == "reset":
            messages = []
            clear_search_results()
            print("🔄 Conversación reiniciada\n")
            continue

        # Añadir mensaje del usuario
        messages.append({"role": "user", "content": user_input})

        try:
            result = run_agent(messages)
            response = result["response"]
            print(f"\n🤖 Agente: {response}\n")

            # Añadir respuesta al historial
            messages.append({"role": "assistant", "content": response})

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()
            print()


if __name__ == "__main__":
    main()

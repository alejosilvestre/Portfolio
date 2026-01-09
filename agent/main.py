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

from dotenv import load_dotenv
from config.settings import load_config

from agent.graph import run_agent
from agent.tools import clear_search_results

config= load_config()


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
        
        if user_input.lower() in ['exit', 'salir', 'quit']:
            print("\n👋 ¡Hasta luego!")
            break
        
        if user_input.lower() == 'reset':
            messages = []
            clear_search_results()
            print("🔄 Conversación reiniciada\n")
            continue
        
        # Añadir mensaje del usuario
        messages.append({"role": "user", "content": user_input})
        
        try:
            result = run(messages)
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
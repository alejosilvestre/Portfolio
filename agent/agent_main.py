"""
===========================================================
MAIN - Punto de Entrada del Agente de Reservas
===========================================================

Este es el archivo principal para ejecutar y testear el agente.

Modos de ejecución:
------------------
1. Modo Interactivo: Chat en terminal con el agente
2. Modo Test: Ejecuta casos de prueba automáticos
3. Modo API: Para integrar con FastAPI (próximo paso)

Uso:
----
    # Modo interactivo
    python main.py --mode interactive
    
    # Modo test
    python main.py --mode test
    
    # Test de un caso específico
    python main.py --test-case complete
"""

import os
import argparse
from typing import Optional
from dotenv import load_dotenv

from agent.agent_state import create_initial_state, AgentState
from agent.agent_graph import (
    create_agent_graph,
    run_agent_until_completion,
    resume_agent_after_user_input
)

# Cargar variables de entorno
load_dotenv()

# Verificar que tenemos API key
if not os.getenv("OPENAI_API_KEY"):
    print("⚠️  ADVERTENCIA: No se encontró OPENAI_API_KEY en .env")
    print("   El agente no podrá funcionar sin esta clave.")


# ===========================================================
# CLASE PRINCIPAL DEL AGENTE
# ===========================================================

class RestaurantBookingAgent:
    """
    Clase wrapper para el agente de reservas.
    
    Facilita la interacción y mantiene el estado de la conversación.
    """
    
    def __init__(self):
        """Inicializa el agente y el grafo."""
        print("🔧 Inicializando Agente de Reservas...")
        self.graph = create_agent_graph()
        self.state: Optional[AgentState] = None
        self.conversation_history = []
        print("✓ Agente inicializado correctamente\n")
    
    def start_conversation(self, user_message: str) -> str:
        """
        Inicia una nueva conversación con el agente.
        
        Args:
            user_message: Primer mensaje del usuario
        
        Returns:
            Respuesta del agente
        """
        print(f"\n{'='*60}")
        print("🎬 INICIANDO NUEVA CONVERSACIÓN")
        print(f"{'='*60}\n")
        
        # Crear estado inicial
        self.state = create_initial_state(user_message)
        
        # Ejecutar hasta punto de interrupción o completar
        self.state = run_agent_until_completion(self.graph, self.state, max_iterations=20)
        
        # Obtener última respuesta del agente
        assistant_messages = [msg for msg in self.state["messages"] if msg["role"] == "assistant"]
        
        if assistant_messages:
            return assistant_messages[-1]["content"]
        else:
            return "Lo siento, hubo un problema procesando tu solicitud."
    
    def continue_conversation(self, user_message: str) -> str:
        """
        Continúa la conversación existente.
        
        Args:
            user_message: Nuevo mensaje del usuario
        
        Returns:
            Respuesta del agente
        """
        if not self.state:
            return "Error: No hay conversación activa. Usa start_conversation() primero."
        
        print(f"\n{'='*60}")
        print("💬 CONTINUANDO CONVERSACIÓN")
        print(f"{'='*60}\n")
        
        # Reanudar con el nuevo mensaje
        self.state = resume_agent_after_user_input(self.graph, self.state, user_message)
        
        # Obtener última respuesta del agente
        assistant_messages = [msg for msg in self.state["messages"] if msg["role"] == "assistant"]
        
        if assistant_messages:
            return assistant_messages[-1]["content"]
        else:
            return "Lo siento, hubo un problema procesando tu respuesta."
    
    def get_conversation_status(self) -> dict:
        """
        Obtiene el estado actual de la conversación.
        
        Returns:
            Dict con información del estado actual
        """
        if not self.state:
            return {"status": "not_started"}
        
        return {
            "status": self.state.get("current_step", "unknown"),
            "needs_user_input": self.state.get("needs_user_input", False),
            "booking_status": self.state.get("booking_status"),
            "error": self.state.get("error"),
            "messages_count": len(self.state.get("messages", []))
        }
    
    def reset(self):
        """Resetea el agente para una nueva conversación."""
        self.state = None
        self.conversation_history = []
        print("\n🔄 Agente reseteado. Listo para nueva conversación.\n")


# ===========================================================
# MODO INTERACTIVO
# ===========================================================

def run_interactive_mode():
    """
    Modo interactivo: chat en terminal con el agente.
    """
    print("\n" + "="*60)
    print("🤖 AGENTE DE RESERVAS DE RESTAURANTES")
    print("="*60)
    print("\nModo: Interactivo")
    print("Comandos especiales:")
    print("  - 'exit' o 'salir': Terminar")
    print("  - 'reset': Nueva conversación")
    print("  - 'status': Ver estado actual")
    print("\n" + "="*60 + "\n")
    
    agent = RestaurantBookingAgent()
    conversation_started = False
    
    while True:
        # Obtener input del usuario
        if not conversation_started:
            user_input = input("👤 Tú: ")
        else:
            user_input = input("\n👤 Tú: ")
        
        # Comandos especiales
        if user_input.lower() in ['exit', 'salir', 'quit']:
            print("\n👋 ¡Hasta luego! Que tengas un buen día.\n")
            break
        
        if user_input.lower() == 'reset':
            agent.reset()
            conversation_started = False
            continue
        
        if user_input.lower() == 'status':
            status = agent.get_conversation_status()
            print(f"\n📊 Estado actual:")
            for key, value in status.items():
                print(f"  - {key}: {value}")
            continue
        
        # Procesar mensaje
        try:
            if not conversation_started:
                response = agent.start_conversation(user_input)
                conversation_started = True
            else:
                response = agent.continue_conversation(user_input)
            
            print(f"\n🤖 Agente: {response}")
            
            # Verificar si la conversación terminó
            status = agent.get_conversation_status()
            if status["status"] == "completed":
                print("\n" + "="*60)
                print("✅ Conversación completada")
                print("="*60)
                
                reset_input = input("\n¿Quieres hacer otra reserva? (s/n): ")
                if reset_input.lower() in ['s', 'si', 'sí', 'yes', 'y']:
                    agent.reset()
                    conversation_started = False
                else:
                    print("\n👋 ¡Hasta luego!\n")
                    break
        
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Intenta de nuevo o escribe 'reset' para empezar de nuevo.\n")


# ===========================================================
# MODO TEST
# ===========================================================

def run_test_mode(test_case: Optional[str] = None):
    """
    Modo test: ejecuta casos de prueba automáticos.
    """
    print("\n" + "="*60)
    print("🧪 MODO TEST - CASOS DE PRUEBA")
    print("="*60 + "\n")
    
    test_cases = {
        "complete": {
            "name": "Información Completa",
            "messages": [
                "Resérvame una pizzería en Navalcarnero para 4 personas mañana a las 21:00"
            ],
            "description": "El usuario proporciona toda la información de una vez"
        },
        "incomplete": {
            "name": "Información Incompleta (HITL)",
            "messages": [
                "Resérvame una pizzería",
                "En Navalcarnero, para 4 personas, mañana a las 21:00"
            ],
            "description": "El agente debe preguntar por la información faltante"
        },
        "selection": {
            "name": "Flujo Completo con Selección",
            "messages": [
                "Busca restaurantes japoneses en Navalcarnero para 2 personas esta noche a las 20:30",
                "El segundo"
            ],
            "description": "Flujo completo hasta selección de restaurante"
        },
        "incremental": {
            "name": "Construcción Incremental",
            "messages": [
                "Quiero cenar",
                "Una pizzería",
                "En Navalcarnero",
                "Para 4 personas",
                "Mañana a las 21:00"
            ],
            "description": "El usuario proporciona información poco a poco"
        }
    }
    
    # Si se especificó un test case, solo ejecutar ese
    if test_case:
        if test_case not in test_cases:
            print(f"❌ Test case '{test_case}' no encontrado")
            print(f"Disponibles: {', '.join(test_cases.keys())}")
            return
        cases_to_run = {test_case: test_cases[test_case]}
    else:
        cases_to_run = test_cases
    
    results = []
    
    # Ejecutar cada test case
    for case_id, case_data in cases_to_run.items():
        print(f"\n{'='*60}")
        print(f"TEST: {case_data['name']}")
        print(f"{'='*60}")
        print(f"Descripción: {case_data['description']}\n")
        
        agent = RestaurantBookingAgent()
        success = True
        error_msg = None
        
        try:
            # Primer mensaje
            response = agent.start_conversation(case_data['messages'][0])
            print(f"👤 Usuario: {case_data['messages'][0]}")
            print(f"🤖 Agente: {response}\n")
            
            # Mensajes adicionales si existen
            for i, msg in enumerate(case_data['messages'][1:], 1):
                print(f"👤 Usuario: {msg}")
                response = agent.continue_conversation(msg)
                print(f"🤖 Agente: {response}\n")
            
            # Verificar estado final
            status = agent.get_conversation_status()
            print(f"📊 Estado final: {status['status']}")
            
            if status.get('error'):
                success = False
                error_msg = status['error']
        
        except Exception as e:
            success = False
            error_msg = str(e)
            print(f"❌ Error durante el test: {error_msg}")
        
        results.append({
            "case": case_data['name'],
            "success": success,
            "error": error_msg
        })
    
    # Resumen de resultados
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS")
    print("="*60 + "\n")
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    for result in results:
        status_icon = "✅" if result['success'] else "❌"
        print(f"{status_icon} {result['case']}")
        if result['error']:
            print(f"   Error: {result['error']}")
    
    print(f"\n{'='*60}")
    print(f"Resultado: {passed}/{total} tests pasados")
    print(f"{'='*60}\n")


# ===========================================================
# MODO API (PLACEHOLDER)
# ===========================================================

def run_api_mode():
    """
    Modo API: Para integración con FastAPI.
    
    Este será el siguiente paso del desarrollo.
    """
    print("\n" + "="*60)
    print("🚀 MODO API")
    print("="*60)
    print("\nEste modo estará disponible cuando integremos con FastAPI.")
    print("Por ahora, usa el modo interactivo o test.\n")


# ===========================================================
# CLI PRINCIPAL
# ===========================================================

def main():
    """Punto de entrada principal con argumentos CLI."""
    parser = argparse.ArgumentParser(
        description="Agente de Reservas de Restaurantes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py --mode interactive
  python main.py --mode test
  python main.py --mode test --test-case complete
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["interactive", "test", "api"],
        default="interactive",
        help="Modo de ejecución (default: interactive)"
    )
    
    parser.add_argument(
        "--test-case",
        type=str,
        help="Test case específico a ejecutar (solo para mode=test)"
    )
    
    args = parser.parse_args()
    
    # Ejecutar el modo seleccionado
    if args.mode == "interactive":
        run_interactive_mode()
    elif args.mode == "test":
        run_test_mode(args.test_case)
    elif args.mode == "api":
        run_api_mode()


# ===========================================================
# EJECUCIÓN DIRECTA
# ===========================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Proceso interrumpido por el usuario. ¡Hasta luego!\n")
    except Exception as e:
        print(f"\n❌ Error fatal: {str(e)}\n")
        import traceback
        traceback.print_exc()

"""
===========================================================
RUN EVALS - Ejecutor de evaluaciones del agente
===========================================================

Script principal para ejecutar evaluaciones del agente FoodLooker
usando DeepEval y Confident AI.

Uso:
    python evals/run_evals.py                    # Ejecuta todas las evaluaciones
    python evals/run_evals.py --category search  # Solo evaluaciones de búsqueda
"""

import argparse
import atexit
import json
import os
import sys
import time as time_module
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Cargar configuración ANTES de importar deepeval
from config.settings import load_config

config = {}
try:
    config = load_config()
    # Configurar CONFIDENT_API_KEY en el entorno ANTES de importar deepeval
    if config.get("CONFIDENT_API_KEY"):
        os.environ["CONFIDENT_API_KEY"] = config["CONFIDENT_API_KEY"]
except Exception as e:
    print(f"⚠️ Error cargando configuración: {e}")

# Ahora importar deepeval (después de configurar el entorno)
from deepeval import evaluate
from deepeval.test_case import LLMTestCase, ToolCall

from evals.datasets import (
    EvalTestCase,
    get_all_test_cases,
    get_test_cases_by_category,
    get_available_categories,
)
from evals.metrics import (
    create_tool_correctness_metric,
    create_task_completion_metric,
    create_response_quality_metric,
    build_llm_test_case,
)

# ===========================================================
# GESTIÓN DEL SERVICIO DE LLAMADAS
# ===========================================================

_call_service_thread = None


def start_call_service_if_needed(categories: List[str]) -> bool:
    """
    Arranca el servicio de llamadas si es necesario para las categorías seleccionadas.

    Args:
        categories: Lista de categorías de test a ejecutar

    Returns:
        True si el servicio se arrancó correctamente o no era necesario
    """
    global _call_service_thread

    # Solo arrancar si hay tests de phone_call
    needs_call_service = "phone_call" in categories or "all" in categories

    if not needs_call_service:
        return True

    # Verificar si ya está corriendo
    import requests
    CALL_SERVICE_PORT = os.getenv("CALL_SERVICE_PORT", "8080")
    CALL_SERVICE_URL = f"http://localhost:{CALL_SERVICE_PORT}"

    try:
        health = requests.get(f"{CALL_SERVICE_URL}/", timeout=2)
        if health.status_code == 200:
            print(f"✅ Servicio de llamadas ya está corriendo en puerto {CALL_SERVICE_PORT}")
            return True
    except requests.exceptions.ConnectionError:
        pass  # No está corriendo, lo arrancaremos

    # Arrancar el servicio
    print(f"\n🚀 Arrancando servicio de llamadas en puerto {CALL_SERVICE_PORT}...")

    try:
        from backend.call_service import start_service
        _call_service_thread = start_service(int(CALL_SERVICE_PORT))

        if _call_service_thread is None:
            print("❌ No se pudo arrancar el servicio de llamadas (faltan variables de entorno)")
            return False

        # Esperar a que el servicio esté listo
        max_wait = 10
        for i in range(max_wait):
            try:
                health = requests.get(f"{CALL_SERVICE_URL}/", timeout=2)
                if health.status_code == 200:
                    print(f"✅ Servicio de llamadas listo")
                    return True
            except requests.exceptions.ConnectionError:
                pass
            time_module.sleep(1)

        print(f"⚠️ El servicio de llamadas no respondió después de {max_wait}s")
        return False

    except ImportError as e:
        print(f"❌ Error importando call_service: {e}")
        return False
    except Exception as e:
        print(f"❌ Error arrancando servicio de llamadas: {e}")
        return False


def stop_call_service():
    """Detiene el servicio de llamadas si fue arrancado por este script."""
    global _call_service_thread
    if _call_service_thread is not None:
        print("\n🛑 Deteniendo servicio de llamadas...")
        # El thread es daemon, se cerrará automáticamente
        _call_service_thread = None


# Registrar cleanup al salir
atexit.register(stop_call_service)


# Mostrar estado de configuración
if config.get("CONFIDENT_API_KEY"):
    print(f"✅ Configuración cargada")
    print(f"✅ Confident AI configurado - Los resultados se subirán al dashboard")
    print(f"   Dashboard: https://app.confident-ai.com")
else:
    print(f"✅ Configuración cargada")
    print(f"⚠️ CONFIDENT_API_KEY no encontrada - Las evaluaciones serán solo locales")


# ===========================================================
# FUNCIONES DE EJECUCIÓN
# ===========================================================


def run_agent_for_eval(user_input: str) -> Dict[str, Any]:
    """
    Ejecuta el agente real y retorna la respuesta.

    Args:
        user_input: Input del usuario

    Returns:
        Dict con 'output' y 'tools_called'
    """
    from agent.graph import run_agent

    # Preparar mensajes
    messages = [{"role": "user", "content": user_input}]

    # Ejecutar agente
    result = run_agent(messages)

    # Extraer herramientas usadas del knowledge
    tools_called = []
    knowledge = result.get("knowledge", {})

    if "places" in knowledge:
        tools_called.append("maps_search")
    if "booking" in knowledge:
        if "maps_search" not in tools_called:
            tools_called.append("maps_search")
        tools_called.append("check_availability")
        tools_called.append("make_booking")
    if "web_search" in knowledge:
        tools_called.append("web_search")
    if "phone_call_made" in knowledge:
        tools_called.append("phone_call")
    if "calendar_event_created" in knowledge:
        tools_called.append("create_calendar_event")

    return {
        "output": result.get("response", ""),
        "tools_called": tools_called,
    }


def convert_to_deepeval_case(
    eval_case: EvalTestCase,
    agent_response: Dict[str, Any],
) -> LLMTestCase:
    """
    Convierte un EvalTestCase a LLMTestCase de DeepEval.

    Args:
        eval_case: Caso de prueba interno
        agent_response: Respuesta del agente

    Returns:
        LLMTestCase para DeepEval
    """
    return build_llm_test_case(
        user_input=eval_case.user_input,
        actual_output=agent_response["output"],
        tools_called=agent_response["tools_called"],
        expected_tools=eval_case.expected_tools,
        expected_output=eval_case.expected_output,
    )


def run_evaluations(
    test_cases: List[EvalTestCase],
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Ejecuta evaluaciones sobre los casos de prueba.

    Args:
        test_cases: Lista de casos de prueba
        verbose: Si mostrar progreso detallado

    Returns:
        Resultados de la evaluación
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"🧪 Ejecutando {len(test_cases)} evaluaciones")
        print(f"{'='*60}\n")

    # Crear métricas
    metrics = [
        create_tool_correctness_metric(threshold=0.5),
        create_task_completion_metric(threshold=0.5),
        create_response_quality_metric(threshold=0.5),
    ]

    # Convertir casos de prueba
    deepeval_cases = []
    for i, eval_case in enumerate(test_cases, 1):
        if verbose:
            print(f"📝 [{i}/{len(test_cases)}] {eval_case.category}: {eval_case.user_input[:50]}...")

        # Obtener respuesta del agente
        try:
            agent_response = run_agent_for_eval(eval_case.user_input)
        except Exception as e:
            print(f"   ❌ Error ejecutando agente: {e}")
            agent_response = {
                "output": f"Error: {str(e)}",
                "tools_called": [],
            }

        # Convertir a DeepEval
        deepeval_case = convert_to_deepeval_case(eval_case, agent_response)
        deepeval_cases.append(deepeval_case)

        if verbose:
            print(f"   🔧 Tools: {agent_response['tools_called']}")
            print(f"   📤 Output: {agent_response['output'][:80]}...")
            print()

    # Ejecutar evaluación
    if verbose:
        print(f"\n{'='*60}")
        print("📊 Ejecutando métricas de DeepEval...")
        print(f"{'='*60}\n")

    try:
        evaluation_results = evaluate(
            test_cases=deepeval_cases,
            metrics=metrics,
        )

        # Confirmar subida a Confident AI
        if verbose and config.get("CONFIDENT_API_KEY"):
            print(f"\n{'='*60}")
            print("✅ Resultados subidos a Confident AI")
            print(f"{'='*60}")
            print(f"🌐 Dashboard: https://app.confident-ai.com")
            print(f"📊 Puedes ver los resultados en el dashboard")

    except Exception as e:
        print(f"❌ Error en evaluación: {e}")
        evaluation_results = None

    # Compilar resultados
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_cases": len(test_cases),
        "metrics_used": [m.__class__.__name__ for m in metrics],
        "deepeval_results": evaluation_results,
    }

    return results


def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Guarda los resultados en un archivo JSON.

    Args:
        results: Resultados de la evaluación
        output_path: Ruta del archivo de salida
    """
    # Convertir objetos no serializables
    serializable_results = {
        "timestamp": results["timestamp"],
        "total_cases": results["total_cases"],
        "metrics_used": results["metrics_used"],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Resultados guardados en: {output_path}")


# ===========================================================
# CLI
# ===========================================================


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta evaluaciones del agente FoodLooker"
    )
    parser.add_argument(
        "--category",
        type=str,
        choices=get_available_categories() + ["all"],
        default="all",
        help="Categoría de tests a ejecutar",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Modo silencioso (menos output)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Archivo de salida para resultados JSON",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Ejecutar solo localmente (sin enviar a Confident AI)",
    )

    args = parser.parse_args()

    # Si --local, desactivar Confident AI
    if args.local:
        os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "true"
        # Eliminar la API key del entorno para evitar envío
        if "CONFIDENT_API_KEY" in os.environ:
            del os.environ["CONFIDENT_API_KEY"]
        print("🔒 Modo local: Los resultados NO se enviarán a Confident AI")

    # Obtener casos de prueba
    if args.category == "all":
        test_cases = get_all_test_cases()
    else:
        test_cases = get_test_cases_by_category(args.category)

    if not test_cases:
        print(f"❌ No se encontraron casos de prueba para: {args.category}")
        sys.exit(1)

    # Arrancar servicios necesarios
    categories = [args.category] if args.category != "all" else get_available_categories()
    if not start_call_service_if_needed(categories):
        print("⚠️ Continuando sin servicio de llamadas (los tests de phone_call pueden fallar)")

    # Ejecutar evaluaciones
    results = run_evaluations(
        test_cases=test_cases,
        verbose=not args.quiet,
    )

    # Guardar resultados si se especificó archivo
    if args.output:
        save_results(results, args.output)
    elif not args.quiet:
        # Guardar por defecto en evals/results/
        output_dir = Path(__file__).parent / "results"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_results(results, str(output_file))

    print("\n✅ Evaluación completada")


if __name__ == "__main__":
    main()

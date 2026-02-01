"""
===========================================================
METRICS - Métricas de evaluación con DeepEval
===========================================================

Implementa las métricas de evaluación para el agente FoodLooker:
- Tool Correctness: Evalúa si el agente usa las herramientas correctas
- Task Completion: Evalúa si el agente completa la tarea
- Answer Relevancy: Evalúa si las respuestas son relevantes

Los thresholds se pueden configurar en .env:
- EVAL_THRESHOLD_TOOL_CORRECTNESS (default: 0.5)
- EVAL_THRESHOLD_TASK_COMPLETION (default: 0.5)
- EVAL_THRESHOLD_RESPONSE_QUALITY (default: 0.5)
- EVAL_THRESHOLD_ANSWER_RELEVANCY (default: 0.5)
"""

import os
from typing import List, Dict, Any, Optional
from deepeval import evaluate
from deepeval.test_case import LLMTestCase, ToolCall
from deepeval.metrics import (
    ToolCorrectnessMetric,
    AnswerRelevancyMetric,
    GEval,
)
from deepeval.test_case import LLMTestCaseParams


# ===========================================================
# CARGAR THRESHOLDS DESDE .ENV
# ===========================================================

def get_threshold(env_var: str, default: float = 0.5) -> float:
    """
    Obtiene un threshold desde variable de entorno.

    Args:
        env_var: Nombre de la variable de entorno
        default: Valor por defecto si no existe

    Returns:
        Threshold como float entre 0.0 y 1.0
    """
    value = os.getenv(env_var)
    if value is None:
        return default
    try:
        threshold = float(value)
        # Asegurar que está en rango válido
        return max(0.0, min(1.0, threshold))
    except ValueError:
        return default


# Thresholds configurables desde .env
THRESHOLD_TOOL_CORRECTNESS = get_threshold("EVAL_THRESHOLD_TOOL_CORRECTNESS", 0.5)
THRESHOLD_TASK_COMPLETION = get_threshold("EVAL_THRESHOLD_TASK_COMPLETION", 0.5)
THRESHOLD_RESPONSE_QUALITY = get_threshold("EVAL_THRESHOLD_RESPONSE_QUALITY", 0.5)
THRESHOLD_ANSWER_RELEVANCY = get_threshold("EVAL_THRESHOLD_ANSWER_RELEVANCY", 0.5)


# ===========================================================
# DEFINICIÓN DE HERRAMIENTAS DISPONIBLES
# ===========================================================

AVAILABLE_TOOLS = [
    {
        "name": "maps_search",
        "description": "Busca lugares en Google Maps/Places. Útil para encontrar restaurantes, bares, cafeterías por ubicación, tipo de cocina, etc.",
        "parameters": {
            "query": "Qué buscar (ej: 'pizzería', 'restaurante italiano')",
            "location": "Dónde buscar (ej: 'Madrid centro', 'Navalcarnero')",
            "radius": "Radio en metros (default: 2000)",
            "price_level": "Nivel de precio 1-4",
            "extras": "Palabras clave adicionales (ej: 'terraza', 'wifi')",
        },
    },
    {
        "name": "check_availability",
        "description": "Verifica disponibilidad en los lugares encontrados previamente con maps_search.",
        "parameters": {
            "date": "Fecha YYYY-MM-DD",
            "time": "Hora HH:MM",
            "num_people": "Número de personas",
        },
    },
    {
        "name": "make_booking",
        "description": "Hace una reserva en un lugar. Requiere haber verificado disponibilidad primero.",
        "parameters": {
            "place_name": "Nombre del lugar",
            "date": "Fecha YYYY-MM-DD",
            "time": "Hora HH:MM",
            "num_people": "Número de personas",
        },
    },
    {
        "name": "phone_call",
        "description": "Realiza una llamada telefónica para cumplir una misión: reservas, consultas, citas.",
        "parameters": {
            "phone_number": "Número a llamar (+34XXXXXXXXX)",
            "mission": "Qué debe conseguir la llamada",
            "context": "Información adicional relevante",
        },
    },
    {
        "name": "web_search",
        "description": "Busca información en internet. Útil para opiniones, recomendaciones, información actualizada.",
        "parameters": {
            "query": "La consulta de búsqueda",
        },
    },
    {
        "name": "create_calendar_event",
        "description": "Crea un evento en Google Calendar para recordar la reserva.",
        "parameters": {
            "summary": "Título del evento",
            "start_datetime": "Fecha y hora de inicio",
            "duration_minutes": "Duración en minutos",
        },
    },
]


# ===========================================================
# MÉTRICAS PERSONALIZADAS
# ===========================================================


def create_tool_correctness_metric(
    threshold: float = None,
    include_reason: bool = True,
    consider_ordering: bool = False,
) -> ToolCorrectnessMetric:
    """
    Crea métrica de Tool Correctness configurada para FoodLooker.

    Args:
        threshold: Umbral mínimo para pasar (0-1). Si None, usa EVAL_THRESHOLD_TOOL_CORRECTNESS de .env
        include_reason: Si incluir explicación del score
        consider_ordering: Si considerar el orden de las herramientas

    Returns:
        Métrica configurada
    """
    if threshold is None:
        threshold = THRESHOLD_TOOL_CORRECTNESS

    return ToolCorrectnessMetric(
        threshold=threshold,
        include_reason=include_reason,
        should_consider_ordering=consider_ordering,
    )


def create_answer_relevancy_metric(
    threshold: float = None,
    include_reason: bool = True,
) -> AnswerRelevancyMetric:
    """
    Crea métrica de Answer Relevancy configurada.

    Args:
        threshold: Umbral mínimo para pasar (0-1). Si None, usa EVAL_THRESHOLD_ANSWER_RELEVANCY de .env
        include_reason: Si incluir explicación del score

    Returns:
        Métrica configurada
    """
    if threshold is None:
        threshold = THRESHOLD_ANSWER_RELEVANCY

    return AnswerRelevancyMetric(
        threshold=threshold,
        include_reason=include_reason,
    )


def create_task_completion_metric(
    threshold: float = None,
) -> GEval:
    """
    Crea métrica de Task Completion usando G-Eval.

    Esta métrica evalúa si el agente completó exitosamente la tarea
    solicitada por el usuario.

    Args:
        threshold: Umbral mínimo para pasar (0-1). Si None, usa EVAL_THRESHOLD_TASK_COMPLETION de .env

    Returns:
        Métrica G-Eval configurada
    """
    if threshold is None:
        threshold = THRESHOLD_TASK_COMPLETION

    return GEval(
        name="TaskCompletion",
        criteria="""Evalúa si el agente de reservas completó exitosamente la tarea del usuario.

Considera los siguientes aspectos:
1. ¿El agente entendió correctamente lo que el usuario pedía?
2. ¿El agente tomó las acciones apropiadas para completar la tarea?
3. ¿El resultado final satisface la solicitud original del usuario?
4. ¿La respuesta es útil y proporciona la información/acción esperada?

Para tareas de búsqueda: ¿Encontró opciones relevantes?
Para tareas de reserva: ¿Completó o intentó completar la reserva?
Para tareas de información: ¿Proporcionó información útil y relevante?

Puntuación:
- 1.0: Tarea completada perfectamente
- 0.7-0.9: Tarea mayormente completada con pequeños fallos
- 0.4-0.6: Tarea parcialmente completada
- 0.1-0.3: Intento de completar pero sin éxito
- 0.0: No intentó o completamente fallido""",
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=threshold,
    )


def create_response_quality_metric(
    threshold: float = None,
) -> GEval:
    """
    Crea métrica de calidad de respuesta usando G-Eval.

    Evalúa la calidad general de la respuesta del agente.

    Args:
        threshold: Umbral mínimo para pasar (0-1). Si None, usa EVAL_THRESHOLD_RESPONSE_QUALITY de .env

    Returns:
        Métrica G-Eval configurada
    """
    if threshold is None:
        threshold = THRESHOLD_RESPONSE_QUALITY

    return GEval(
        name="ResponseQuality",
        criteria="""Evalúa la calidad de la respuesta del agente de reservas.

Considera:
1. Claridad: ¿La respuesta es clara y fácil de entender?
2. Completitud: ¿Incluye toda la información relevante?
3. Tono: ¿Es amable y profesional?
4. Formato: ¿Está bien estructurada?
5. Utilidad: ¿Ayuda al usuario a tomar decisiones?

Para respuestas con restaurantes:
- ¿Incluye nombre, ubicación, valoración?
- ¿Ofrece opciones variadas si las hay?

Para confirmaciones de reserva:
- ¿Incluye todos los detalles (fecha, hora, personas)?
- ¿Indica claramente si fue exitosa o no?

Puntuación:
- 1.0: Respuesta excelente, clara y completa
- 0.7-0.9: Buena respuesta con detalles menores faltantes
- 0.4-0.6: Respuesta aceptable pero mejorable
- 0.1-0.3: Respuesta pobre o confusa
- 0.0: Respuesta inapropiada o irrelevante""",
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=threshold,
    )


# ===========================================================
# FUNCIONES DE EVALUACIÓN
# ===========================================================


def build_llm_test_case(
    user_input: str,
    actual_output: str,
    tools_called: List[str],
    expected_tools: List[str],
    expected_output: Optional[str] = None,
    retrieval_context: Optional[List[str]] = None,
) -> LLMTestCase:
    """
    Construye un LLMTestCase para DeepEval.

    Args:
        user_input: Input del usuario
        actual_output: Respuesta del agente
        tools_called: Herramientas que el agente usó
        expected_tools: Herramientas que se esperaban usar
        expected_output: Respuesta esperada (opcional)
        retrieval_context: Contexto de retrieval (opcional)

    Returns:
        LLMTestCase configurado
    """
    # Convertir nombres de herramientas a ToolCall objects
    tools_called_objects = [ToolCall(name=t) for t in tools_called]
    expected_tools_objects = [ToolCall(name=t) for t in expected_tools]

    return LLMTestCase(
        input=user_input,
        actual_output=actual_output,
        expected_output=expected_output,
        tools_called=tools_called_objects,
        expected_tools=expected_tools_objects,
        retrieval_context=retrieval_context,
    )


def evaluate_single_case(
    test_case: LLMTestCase,
    metrics: List[Any],
) -> Dict[str, Any]:
    """
    Evalúa un único caso de prueba con las métricas especificadas.

    Args:
        test_case: Caso de prueba
        metrics: Lista de métricas a aplicar

    Returns:
        Resultados de la evaluación
    """
    results = {}

    for metric in metrics:
        metric.measure(test_case)
        results[metric.__class__.__name__] = {
            "score": metric.score,
            "reason": getattr(metric, "reason", None),
            "passed": metric.score >= metric.threshold,
        }

    return results


def evaluate_batch(
    test_cases: List[LLMTestCase],
    metrics: List[Any],
) -> List[Dict[str, Any]]:
    """
    Evalúa un batch de casos de prueba.

    Args:
        test_cases: Lista de casos de prueba
        metrics: Lista de métricas a aplicar

    Returns:
        Lista de resultados de evaluación
    """
    # Usar evaluate de DeepEval para batch
    evaluate(test_cases=test_cases, metrics=metrics)

    # Recopilar resultados
    results = []
    for test_case in test_cases:
        case_results = {}
        for metric in metrics:
            case_results[metric.__class__.__name__] = {
                "score": metric.score,
                "reason": getattr(metric, "reason", None),
                "passed": metric.score >= metric.threshold,
            }
        results.append(case_results)

    return results

"""
===========================================================
DATASETS - Casos de prueba para evaluación del agente
===========================================================

Define los casos de prueba (golden datasets) para evaluar
el agente de reservas FoodLooker.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class EvalTestCase:
    """Caso de prueba para evaluación."""

    # Input del usuario
    user_input: str

    # Herramientas que se esperan usar (en orden)
    expected_tools: List[str] = field(default_factory=list)

    # Respuesta esperada (para Answer Relevancy)
    expected_output: str = ""

    # ¿Se espera que complete la tarea?
    should_complete_task: bool = True

    # Contexto adicional para el evaluador
    context: str = ""

    # Categoría del test
    category: str = "general"


# ===========================================================
# DATASET: Búsqueda de restaurantes
# ===========================================================

SEARCH_TESTS = [
    EvalTestCase(
        user_input="Busco un restaurante italiano cerca de Sol, Madrid",
        expected_tools=["maps_search"],
        expected_output="Aquí tienes restaurantes italianos cerca de Sol",
        should_complete_task=True,
        context="El usuario quiere encontrar restaurantes italianos en Madrid centro",
        category="search",
    ),
    EvalTestCase(
        user_input="Recomiéndame un sitio para comer sushi en Gran Vía con terraza",
        expected_tools=["maps_search"],
        expected_output="Restaurantes de sushi con terraza en Gran Vía",
        should_complete_task=True,
        context="Búsqueda con criterios específicos: sushi + terraza",
        category="search",
    ),
    EvalTestCase(
        user_input="¿Hay algún restaurante mexicano barato cerca de Atocha?",
        expected_tools=["maps_search"],
        expected_output="Restaurantes mexicanos económicos cerca de Atocha",
        should_complete_task=True,
        context="Búsqueda con filtro de precio",
        category="search",
    ),
]

# ===========================================================
# DATASET: Información completa
# ===========================================================

COMPLETE_INFO_TESTS = [
    EvalTestCase(
        user_input="Quiero cenar pizza en Navalcarnero",
        expected_tools=["maps_search"],
        expected_output="¿A qué hora te gustaría cenar y cuántas personas asistirán?",
        should_complete_task=True,
        context="Búsqueda de pizzerías en un pueblo de Madrid",
        category="search",
    ),
    EvalTestCase(
        user_input="Reserva en La Trattoria para 2 personas el viernes a las 20:30",
        expected_tools=["maps_search", "check_availability", "make_booking"],
        expected_output="¿En qué ciudad se encuentra La Trattoria?",
        should_complete_task=True,
        context="Reserva en restaurante específico",
        category="booking",
    ),
]
# ===========================================================
# DATASET: Reservas completas
# ===========================================================

BOOKING_TESTS = [
    EvalTestCase(
        user_input="Quiero reservar mesa para 4 personas mañana a las 21:00 en un italiano en Chamberí",
        expected_tools=["maps_search", "check_availability", "make_booking"],
        expected_output="Aquí tienes la lista de restaurantes italianos en Chamberí con disponibilidad. ¿en cual quieres reservar?",
        should_complete_task=True,
        context="Flujo completo: búsqueda → disponibilidad → reserva",
        category="booking",
    ),
    EvalTestCase(
        user_input="Reserva en Tapa Tapa Montera de Madrid para 2 personas el viernes a las 20:30, a nombre de Juan Pérez, y teléfono 612345678",
        expected_tools=["maps_search", "check_availability", "make_booking"],
        expected_output="Resultado de la reserva en Tapa Tapa Montera de Madrid: confirmada, o sin disponibilidad pero propone alternativas",
        should_complete_task=True,
        context="Reserva en restaurante específico. El test es válido si se confirma la reserva O si se informa de falta de disponibilidad con horarios alternativos",
        category="booking",
    ),
]


# ===========================================================
# DATASET: Llamadas telefónicas
# ===========================================================

PHONE_CALL_TESTS = [
    EvalTestCase(
        user_input="¿Puedes llamar para reservar en el restaurante Divina Locura de Madrid para 2 personas? A nombre de María García, y teléfono 612345678",
        expected_tools=["phone_call"],
        expected_output="He llamado al restaurante para hacer la reserva",
        should_complete_task=True,
        context="El usuario pide explícitamente una llamada",
        category="phone_call",
    ),
    EvalTestCase(
        user_input="Llama a Trattoria Sant Arcangelo y pregunta si tienen menú vegetariano",
        expected_tools=["phone_call"],
        expected_output="He llamado para preguntar sobre el menú vegetariano, y  sí tiene. O:  He llamado para preguntar sobre el menú vegetariano, y no tiene",
        should_complete_task=True,
        context="Llamada para consulta, no reserva",
        category="phone_call",
    ),
]


# ===========================================================
# DATASET: Calendario
# ===========================================================

CALENDAR_TESTS = [
    EvalTestCase(
        user_input="Reserva en el restaurante Villa Capri de Madrid para 2 personas el viernes a las 20:30, a nombre de Juan Pérez, y teléfono 612345678. Añade la reserva a mi calendario de Google",
        expected_tools=["create_calendar_event"],
        expected_output="He añadido el evento a tu calendario",
        should_complete_task=True,
        context="Usuario pide crear evento en calendario después de reservar",
        category="calendar",
    ),
]


# ===========================================================
# DATASET: Búsquedas web
# ===========================================================

WEB_SEARCH_TESTS = [
    EvalTestCase(
        user_input="¿Cuáles son los mejores restaurantes con estrella Michelin en Madrid?",
        expected_tools=["web_search"],
        expected_output="Los restaurantes con estrella Michelin en Madrid son",
        should_complete_task=True,
        context="Pregunta que requiere búsqueda web, no Maps",
        category="web_search",
    ),
    EvalTestCase(
        user_input="¿Qué opinan de DiverXO? ¿Vale la pena?",
        expected_tools=["web_search"],
        expected_output="Información y opiniones sobre DiverXO",
        should_complete_task=True,
        context="Búsqueda de opiniones/reseñas",
        category="web_search",
    ),
]


# ===========================================================
# DATASET: Conversaciones multi-turno
# ===========================================================

MULTI_TURN_TESTS = [
    # Este caso simula una conversación donde el usuario primero busca
    # y luego pide reservar
    EvalTestCase(
        user_input="Busca restaurantes japoneses en Malasaña",
        expected_tools=["maps_search"],
        expected_output="Restaurantes japoneses en Malasaña",
        should_complete_task=True,
        context="Primer turno de conversación multi-turno",
        category="multi_turn",
    ),
]


# ===========================================================
# DATASET: Casos edge / errores esperados
# ===========================================================

EDGE_CASE_TESTS = [
    EvalTestCase(
        user_input="Hola, ¿qué tal?",
        expected_tools=[],  # No debería usar ninguna herramienta
        expected_output="Saludo amable y ofrecimiento de ayuda con restaurantes",
        should_complete_task=True,
        context="¡Hola! Estoy aquí para ayudarte a encontrar un restaurante y hacer una reserva. ¿Tienes algún lugar en mente o algún tipo de comida que prefieras?",
        category="edge_case",
    ),
    EvalTestCase(
        user_input="¿Cuál es la capital de Francia?",
        expected_tools=[],  # Pregunta fuera de dominio
        expected_output="Solo busco restaurantes y estaré encantado de ayudarte con tu reserva de restaurantes. ¿Te gustaría encontrar un restaurante en particular?",
        should_complete_task=True,  # El agente completa su tarea: redirigir al tema de restaurantes
        context="Pregunta fuera del dominio del agente - debe redirigir amablemente al tema de restaurantes",
        category="edge_case",
    ),
]


# ===========================================================
# DATASET COMPLETO
# ===========================================================


def get_all_test_cases() -> List[EvalTestCase]:
    """Retorna todos los casos de prueba."""
    return (
        SEARCH_TESTS
        + COMPLETE_INFO_TESTS
        + BOOKING_TESTS
        + PHONE_CALL_TESTS
        + CALENDAR_TESTS
        + WEB_SEARCH_TESTS
        + MULTI_TURN_TESTS
        + EDGE_CASE_TESTS
    )


def get_test_cases_by_category(category: str) -> List[EvalTestCase]:
    """Retorna casos de prueba filtrados por categoría."""
    all_cases = get_all_test_cases()
    return [tc for tc in all_cases if tc.category == category]


def get_available_categories() -> List[str]:
    """Retorna las categorías disponibles."""
    return [
        "search",
        "booking",
        "phone_call",
        "calendar",
        "web_search",
        "multi_turn",
        "edge_case",
    ]

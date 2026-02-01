"""
===========================================================
TEST AGENT GRAPH - Tests para agent/graph.py
===========================================================

Tests unitarios para el grafo del agente ReAct.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage


class TestParseILLMResponse:
    """Tests para la función parse_llm_response."""

    def test_parse_llm_response_extracts_thought_action_correctly(self):
        """Verifica que se extraen correctamente THOUGHT, ACTION y ACTION_INPUT."""
        from agent.graph import parse_llm_response

        text = """THOUGHT: Necesito buscar restaurantes italianos en Madrid.
ACTION: maps_search
ACTION_INPUT: {"query": "restaurante italiano", "location": "Madrid"}"""

        result = parse_llm_response(text)

        assert result["thought"] == "Necesito buscar restaurantes italianos en Madrid."
        assert result["action"] == "maps_search"
        assert result["action_input"] == {"query": "restaurante italiano", "location": "Madrid"}

    def test_parse_llm_response_handles_malformed_response(self):
        """Verifica que maneja respuestas mal formadas."""
        from agent.graph import parse_llm_response

        text = "Esta es una respuesta sin formato correcto."

        result = parse_llm_response(text)

        assert result["action"] == "respond"
        assert "message" in result["action_input"]

    def test_parse_llm_response_with_respond_action(self):
        """Verifica el parseo de la acción respond."""
        from agent.graph import parse_llm_response

        text = """THOUGHT: Ya tengo toda la información necesaria.
ACTION: respond
ACTION_INPUT: {"message": "He encontrado 3 restaurantes italianos en Madrid."}"""

        result = parse_llm_response(text)

        assert result["action"] == "respond"
        assert result["action_input"]["message"] == "He encontrado 3 restaurantes italianos en Madrid."

    def test_parse_llm_response_with_nested_json(self):
        """Verifica el parseo con JSON anidado."""
        from agent.graph import parse_llm_response

        text = """THOUGHT: Buscaré con filtros.
ACTION: maps_search
ACTION_INPUT: {"query": "pizza", "location": "Madrid", "extras": "terraza"}"""

        result = parse_llm_response(text)

        assert result["action"] == "maps_search"
        assert result["action_input"]["query"] == "pizza"
        assert result["action_input"]["extras"] == "terraza"

    def test_parse_llm_response_without_action_input(self):
        """Verifica el parseo cuando no hay ACTION_INPUT."""
        from agent.graph import parse_llm_response

        text = """THOUGHT: Necesito verificar disponibilidad.
ACTION: check_availability"""

        result = parse_llm_response(text)

        assert result["action"] == "check_availability"
        assert result["action_input"] == {}

    def test_parse_llm_response_case_insensitive(self):
        """Verifica que el parseo es case insensitive."""
        from agent.graph import parse_llm_response

        text = """thought: Pensando...
action: WEB_SEARCH
action_input: {"query": "test"}"""

        result = parse_llm_response(text)

        assert result["thought"] == "Pensando..."
        assert result["action"] == "web_search"


class TestFormatConversation:
    """Tests para la función format_conversation."""

    def test_format_conversation_with_empty_messages(self):
        """Verifica el formateo con lista vacía."""
        from agent.graph import format_conversation

        result = format_conversation([])

        assert result == "Sin mensajes previos"

    def test_format_conversation_with_human_messages(self):
        """Verifica el formateo con mensajes humanos."""
        from agent.graph import format_conversation

        messages = [
            HumanMessage(content="Hola"),
            HumanMessage(content="Busco restaurante"),
        ]

        result = format_conversation(messages)

        assert "Usuario: Hola" in result
        assert "Usuario: Busco restaurante" in result

    def test_format_conversation_with_mixed_messages(self):
        """Verifica el formateo con mensajes mixtos."""
        from agent.graph import format_conversation

        messages = [
            HumanMessage(content="Hola"),
            AIMessage(content="¡Hola! ¿En qué puedo ayudarte?"),
            HumanMessage(content="Busco restaurante"),
        ]

        result = format_conversation(messages)

        assert "Usuario: Hola" in result
        assert "Asistente: ¡Hola!" in result
        assert "Usuario: Busco restaurante" in result

    def test_format_conversation_with_dict_messages(self):
        """Verifica el formateo con mensajes en formato dict."""
        from agent.graph import format_conversation

        messages = [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "¡Hola!"},
        ]

        result = format_conversation(messages)

        assert "Usuario: Hola" in result
        assert "Asistente: ¡Hola!" in result

    def test_format_conversation_limits_to_last_10(self):
        """Verifica que solo se muestran los últimos 10 mensajes."""
        from agent.graph import format_conversation

        messages = [HumanMessage(content=f"Mensaje {i}") for i in range(15)]

        result = format_conversation(messages)

        assert "Mensaje 5" in result
        assert "Mensaje 14" in result
        # Los primeros 5 no deberían estar
        assert "Mensaje 0" not in result
        assert "Mensaje 4" not in result


class TestFormatKnowledge:
    """Tests para la función format_knowledge."""

    def test_format_knowledge_empty(self):
        """Verifica el formateo con knowledge vacío."""
        from agent.graph import format_knowledge

        result = format_knowledge({})

        assert result == "Ninguno"

    def test_format_knowledge_with_places(self, agent_state_with_places):
        """Verifica el formateo con lugares."""
        from agent.graph import format_knowledge

        result = format_knowledge(agent_state_with_places["knowledge"])

        assert "La Trattoria" in result
        assert "Pizzería Milano" in result
        assert "Disponible" in result

    def test_format_knowledge_with_booking(self, agent_state_with_booking):
        """Verifica el formateo con reserva."""
        from agent.graph import format_knowledge

        result = format_knowledge(agent_state_with_booking["knowledge"])

        assert "Reserva confirmada" in result
        assert "La Trattoria" in result

    def test_format_knowledge_with_web_search(self):
        """Verifica el formateo con búsqueda web."""
        from agent.graph import format_knowledge

        knowledge = {
            "web_search": {
                "query": "mejores pizzerías Madrid",
                "result": "Las mejores pizzerías..."
            }
        }

        result = format_knowledge(knowledge)

        assert "Búsqueda web" in result
        assert "mejores pizzerías Madrid" in result

    def test_format_knowledge_with_phone_call(self):
        """Verifica el formateo con llamada telefónica."""
        from agent.graph import format_knowledge

        knowledge = {
            "phone_call_made": {
                "phone_number": "+34912345678",
                "mission": "Reservar mesa para 2 personas",
                "result": "Reserva confirmada"
            }
        }

        result = format_knowledge(knowledge)

        assert "Llamada realizada" in result
        assert "+34912345678" in result

    def test_format_knowledge_with_calendar_event(self):
        """Verifica el formateo con evento de calendario."""
        from agent.graph import format_knowledge

        knowledge = {
            "calendar_event_created": {
                "summary": "Cena en La Trattoria",
                "start": "2026-01-20T21:00:00",
                "result": "Evento creado"
            }
        }

        result = format_knowledge(knowledge)

        assert "Evento creado" in result
        assert "Cena en La Trattoria" in result


class TestShouldContinue:
    """Tests para la función should_continue."""

    def test_should_continue_returns_execute_when_tool_selected(self):
        """Verifica que retorna 'execute' cuando hay herramienta seleccionada."""
        from agent.graph import should_continue

        state = {
            "status": "executing",
            "iterations": 1,
            "knowledge": {},
            "messages": [],
        }

        result = should_continue(state)

        assert result == "execute"

    def test_should_continue_returns_respond_when_respond_action(self):
        """Verifica que retorna 'respond' cuando status es responding."""
        from agent.graph import should_continue

        state = {
            "status": "responding",
            "iterations": 1,
            "knowledge": {},
            "messages": [],
        }

        result = should_continue(state)

        assert result == "respond"

    def test_should_continue_returns_brain_when_thinking(self):
        """Verifica que retorna 'brain' cuando status es thinking."""
        from agent.graph import should_continue

        state = {
            "status": "thinking",
            "iterations": 1,
            "knowledge": {},
            "messages": [],
        }

        result = should_continue(state)

        assert result == "brain"

    def test_should_continue_returns_end_when_finished(self):
        """Verifica que retorna 'end' cuando status es finished."""
        from agent.graph import should_continue

        state = {
            "status": "finished",
            "iterations": 1,
            "knowledge": {},
            "messages": [],
        }

        result = should_continue(state)

        assert result == "end"

    def test_should_continue_returns_respond_at_max_iterations(self):
        """Verifica que retorna 'respond' al alcanzar máximo de iteraciones."""
        from agent.graph import should_continue, MAX_ITERATIONS

        state = {
            "status": "thinking",
            "iterations": MAX_ITERATIONS,
            "knowledge": {"places": [{"name": "Test"}]},
            "messages": [HumanMessage(content="test")],
            "tool_args": {},
        }

        result = should_continue(state)

        assert result == "respond"
        assert state["status"] == "responding"

    def test_should_continue_generates_response_with_knowledge_at_max_iterations(self):
        """Verifica que genera respuesta con knowledge al máximo de iteraciones."""
        from agent.graph import should_continue, MAX_ITERATIONS

        state = {
            "status": "thinking",
            "iterations": MAX_ITERATIONS,
            "knowledge": {
                "places": [{"name": "Restaurante Test"}],
                "booking": {"place_name": "Restaurante Test"}
            },
            "messages": [HumanMessage(content="test")],
            "tool_args": {},
        }

        should_continue(state)

        assert "message" in state["tool_args"]
        assert "confirmada" in state["tool_args"]["message"]


class TestBrainNode:
    """Tests para el nodo brain."""

    @patch("agent.graph.get_llm")
    def test_brain_node_updates_state_correctly(self, mock_get_llm, mock_config):
        """Verifica que brain_node actualiza el estado correctamente."""
        from agent.graph import brain_node

        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content="THOUGHT: Test\nACTION: maps_search\nACTION_INPUT: {\"query\": \"test\"}"
        )
        mock_get_llm.return_value = mock_llm

        state = {
            "messages": [HumanMessage(content="Busco restaurante")],
            "knowledge": {},
            "next_tool": None,
            "tool_args": None,
            "last_observation": None,
            "status": "thinking",
            "iterations": 0,
        }

        with patch("agent.graph.config", mock_config):
            result = brain_node(state)

        assert result["next_tool"] == "maps_search"
        assert result["iterations"] == 1
        assert result["status"] == "executing"

    @patch("agent.graph.get_llm")
    def test_brain_node_sets_responding_for_respond_action(self, mock_get_llm, mock_config):
        """Verifica que brain_node pone status responding para acción respond."""
        from agent.graph import brain_node

        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content="THOUGHT: Ya tengo info\nACTION: respond\nACTION_INPUT: {\"message\": \"Aquí están los resultados\"}"
        )
        mock_get_llm.return_value = mock_llm

        state = {
            "messages": [HumanMessage(content="Test")],
            "knowledge": {},
            "next_tool": None,
            "tool_args": None,
            "last_observation": None,
            "status": "thinking",
            "iterations": 0,
        }

        with patch("agent.graph.config", mock_config):
            result = brain_node(state)

        assert result["next_tool"] == "respond"
        assert result["status"] == "responding"


class TestExecuteNode:
    """Tests para el nodo execute."""

    def test_execute_node_handles_respond_action(self):
        """Verifica que execute_node maneja acción respond."""
        from agent.graph import execute_node

        state = {
            "next_tool": "respond",
            "tool_args": {"message": "Test"},
            "knowledge": {},
            "status": "executing",
        }

        result = execute_node(state)

        assert result["status"] == "responding"

    @patch("agent.tools.get_search_results")
    @patch("agent.graph.execute_tool")
    def test_execute_node_updates_knowledge_for_maps_search(self, mock_execute_tool, mock_get_results):
        """Verifica que execute_node actualiza knowledge para maps_search."""
        from agent.graph import execute_node

        mock_execute_tool.return_value = "Encontré 3 restaurantes"
        mock_get_results.return_value = [{"name": "Test"}]

        state = {
            "next_tool": "maps_search",
            "tool_args": {"query": "pizza", "location": "Madrid"},
            "knowledge": {},
            "status": "executing",
            "last_observation": None,
        }

        result = execute_node(state)

        assert result["status"] == "thinking"
        assert result["last_observation"] == "Encontré 3 restaurantes"
        assert "places" in result["knowledge"]

    @patch("agent.graph.execute_tool")
    def test_execute_node_updates_knowledge_for_booking(self, mock_execute_tool):
        """Verifica que execute_node actualiza knowledge para booking."""
        from agent.graph import execute_node

        mock_execute_tool.return_value = "Reserva confirmada"

        state = {
            "next_tool": "make_booking",
            "tool_args": {
                "place_name": "La Trattoria",
                "date": "2026-01-20",
                "time": "21:00",
                "num_people": 2
            },
            "knowledge": {},
            "status": "executing",
            "last_observation": None,
        }

        result = execute_node(state)

        assert "booking" in result["knowledge"]
        assert result["knowledge"]["booking"]["confirmed"] is True
        assert result["knowledge"]["booking"]["place_name"] == "La Trattoria"


class TestRespondNode:
    """Tests para el nodo respond."""

    def test_respond_node_adds_message(self):
        """Verifica que respond_node añade mensaje al estado."""
        from agent.graph import respond_node

        state = {
            "messages": [HumanMessage(content="Hola")],
            "tool_args": {"message": "¡Hola! ¿En qué puedo ayudarte?"},
            "status": "responding",
        }

        result = respond_node(state)

        assert result["status"] == "finished"
        assert len(result["messages"]) == 2
        assert isinstance(result["messages"][-1], AIMessage)
        assert result["messages"][-1].content == "¡Hola! ¿En qué puedo ayudarte?"

    def test_respond_node_with_default_message(self):
        """Verifica que respond_node usa mensaje por defecto."""
        from agent.graph import respond_node

        state = {
            "messages": [],
            "tool_args": {},
            "status": "responding",
        }

        result = respond_node(state)

        assert result["messages"][-1].content == "¿En qué puedo ayudarte?"


class TestCreateGraph:
    """Tests para la creación del grafo."""

    def test_create_graph_returns_compiled_graph(self):
        """Verifica que create_graph retorna un grafo compilado."""
        from agent.graph import create_graph

        with patch("agent.graph.load_config", return_value={
            "OPENAI_API_KEY": "test",
            "MODEL_NAME": "gpt-4o-mini",
            "TEMPERATURE": 0.3,
            "GOOGLE_MAPS_API_KEY": "test",
            "TAVILY_API_KEY": "test",
        }):
            graph = create_graph()

        assert graph is not None
        assert hasattr(graph, "invoke")

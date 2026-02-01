"""
===========================================================
TEST STATE - Tests para agent/state.py
===========================================================

Tests unitarios para el estado del agente.
"""

import pytest
from langchain_core.messages import HumanMessage, AIMessage


class TestAgentState:
    """Tests para AgentState TypedDict."""

    def test_agent_state_initial_values(self):
        """Verifica los valores iniciales del estado."""
        from agent.state import create_initial_state

        state = create_initial_state()

        assert state["messages"] == []
        assert state["knowledge"] == {}
        assert state["next_tool"] is None
        assert state["tool_args"] is None
        assert state["last_observation"] is None
        assert state["status"] == "thinking"
        assert state["iterations"] == 0

    def test_agent_state_with_messages(self):
        """Verifica estado con mensajes iniciales."""
        from agent.state import create_initial_state

        messages = [
            HumanMessage(content="Hola"),
            AIMessage(content="¡Hola! ¿En qué puedo ayudarte?"),
        ]

        state = create_initial_state(messages)

        assert len(state["messages"]) == 2
        assert state["messages"][0].content == "Hola"
        assert state["messages"][1].content == "¡Hola! ¿En qué puedo ayudarte?"

    def test_agent_state_knowledge_accumulation(self):
        """Verifica que el knowledge se puede acumular."""
        from agent.state import create_initial_state

        state = create_initial_state()

        # Añadir lugares
        state["knowledge"]["places"] = [{"name": "La Trattoria"}]
        assert len(state["knowledge"]["places"]) == 1

        # Añadir más lugares
        state["knowledge"]["places"].append({"name": "Pizzería Milano"})
        assert len(state["knowledge"]["places"]) == 2

        # Añadir booking
        state["knowledge"]["booking"] = {
            "place_name": "La Trattoria",
            "date": "2026-01-20",
            "time": "21:00",
        }
        assert state["knowledge"]["booking"]["place_name"] == "La Trattoria"

    def test_agent_state_status_transitions(self):
        """Verifica las transiciones de status."""
        from agent.state import create_initial_state

        state = create_initial_state()

        # Transición thinking -> executing
        assert state["status"] == "thinking"
        state["status"] = "executing"
        assert state["status"] == "executing"

        # Transición executing -> thinking
        state["status"] = "thinking"
        assert state["status"] == "thinking"

        # Transición thinking -> responding
        state["status"] = "responding"
        assert state["status"] == "responding"

        # Transición responding -> finished
        state["status"] = "finished"
        assert state["status"] == "finished"

    def test_agent_state_iterations_increment(self):
        """Verifica el incremento de iteraciones."""
        from agent.state import create_initial_state

        state = create_initial_state()

        assert state["iterations"] == 0

        for i in range(5):
            state["iterations"] += 1
            assert state["iterations"] == i + 1

    def test_agent_state_next_tool_and_args(self):
        """Verifica la asignación de next_tool y tool_args."""
        from agent.state import create_initial_state

        state = create_initial_state()

        # Asignar herramienta
        state["next_tool"] = "maps_search"
        state["tool_args"] = {"query": "pizza", "location": "Madrid"}

        assert state["next_tool"] == "maps_search"
        assert state["tool_args"]["query"] == "pizza"
        assert state["tool_args"]["location"] == "Madrid"

    def test_agent_state_last_observation(self):
        """Verifica la asignación de last_observation."""
        from agent.state import create_initial_state

        state = create_initial_state()

        assert state["last_observation"] is None

        state["last_observation"] = "Encontré 5 restaurantes italianos en Madrid"

        assert "Encontré 5 restaurantes" in state["last_observation"]

    def test_agent_state_messages_append(self):
        """Verifica que se pueden añadir mensajes."""
        from agent.state import create_initial_state

        state = create_initial_state()

        state["messages"].append(HumanMessage(content="Primer mensaje"))
        assert len(state["messages"]) == 1

        state["messages"].append(AIMessage(content="Respuesta"))
        assert len(state["messages"]) == 2

        state["messages"].append(HumanMessage(content="Segundo mensaje"))
        assert len(state["messages"]) == 3

    def test_create_initial_state_is_independent(self):
        """Verifica que cada llamada crea un estado independiente."""
        from agent.state import create_initial_state

        state1 = create_initial_state()
        state2 = create_initial_state()

        # Modificar state1
        state1["knowledge"]["test"] = "value"
        state1["iterations"] = 5

        # state2 no debería estar afectado
        assert "test" not in state2["knowledge"]
        assert state2["iterations"] == 0

    def test_agent_state_complex_knowledge(self):
        """Verifica knowledge con estructura compleja."""
        from agent.state import create_initial_state

        state = create_initial_state()

        state["knowledge"] = {
            "places": [
                {
                    "name": "La Trattoria",
                    "rating": 4.5,
                    "available": True,
                    "available_times": ["20:00", "21:00"],
                }
            ],
            "booking": {
                "confirmed": True,
                "place_name": "La Trattoria",
                "date": "2026-01-20",
                "time": "21:00",
                "num_people": 2,
            },
            "web_search": {
                "query": "opiniones La Trattoria",
                "result": "Excelente restaurante..."
            },
            "calendar_event_created": {
                "summary": "Cena en La Trattoria",
                "start": "2026-01-20T21:00:00"
            },
            "phone_call_made": {
                "phone_number": "+34912345678",
                "mission": "Confirmar reserva",
                "result": "Confirmado"
            }
        }

        # Verificar cada componente
        assert len(state["knowledge"]["places"]) == 1
        assert state["knowledge"]["places"][0]["available"] is True
        assert state["knowledge"]["booking"]["confirmed"] is True
        assert state["knowledge"]["web_search"]["query"] == "opiniones La Trattoria"
        assert state["knowledge"]["calendar_event_created"]["summary"] == "Cena en La Trattoria"
        assert state["knowledge"]["phone_call_made"]["result"] == "Confirmado"

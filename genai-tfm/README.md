# 🍽️ FoodLooker

Agente Inteligente de reservas con IA
Trabajo final de Máster

---

## Ejecución del proyecto

## Pasos previos

⚠️**IMPORTANTE**: Primero crea un archivo `.env` con tus API keys (usa `.env.example` como plantilla).

**Instrucciones para generar las credenciales de Google Calendar**

1.  Crea un proyecto nuevo en https://console.cloud.google.com/
2.  Habilita la API: Ve a "APIs y servicios" > "Biblioteca", busca "Google Calendar API" y habilítala.
3.  Pantalla de Consentimiento OAuth:
    1. Ve a "APIs y servicios" > "Pantalla de consentimiento de OAuth".
    2. Selecciona el tipo de usuario (interno o externo).
    3. Configura el nombre de la aplicación, y la información de contacto.
    4. Dale permisos completos, la aplicación configurará luego los SCOPES
4.  Crea Credenciales OAuth:
    1. Ve a "APIs y servicios" > "Credenciales" > "Crear credenciales" > "ID de cliente OAuth".
    2. Elige el tipo de aplicación: Web application
    3. Añade las URIs de redireccionamiento autorizadas (donde Google devolverá el código de autorización):
       - http://localhost/8080/
       - http://127.0.0.1/8080/
    4. Guarda el ID de cliente y el Secreto de cliente ("credentials.json) que se generan, son cruciales para tu aplicación.
    5. Coloca el fichero credentials.json en el directorio raiz de tu proyecto
5.  Ve a Google Auth Platform -> Público -> Haz scroll down hasta "Usuarios de prueba"
    1.  Añade tu cuenta de google: xxxx@gmail.com que estés utilizando para correr la aplicación

**Instrucciones para habilitar Google Places API**

1. Ve a google maps platform https://console.cloud.google.com/google/maps-apis/overview
   1. Asegúrate que utilizas el mismo proyecto en que habilitaste google calendar API
   2. La primera vez te pedirá crear un clave de api, esa es la variable de entorno GOOGLE_MAPS_API_KEY
      - Debes implementar una restricción por IP, y agregar tu IP pública
      - Debes implementar una restricción de API para las siguientes APIs:
        - Distance Matrix API
        - Geocoding API
        - Places API (New)
   3. Puedes revisar, o rehacer tus credenciales en APIs y Servicios -> Credenciales -> Nueva Clave de API
2. En APIs y Servicios -> Biblioteca habilita las siguientes APIs
   - Geocoding API (necesaria para convertir direcciones a coordenadas)
   - Places API (New) o Places API (para búsqueda de lugares)
   - Distance Matrix API (para filtrado por tiempo de viaje)

---

### 💻 Ejecución desde bash (Ejecución completa con todas las APIs de terceros y streamlit)

```bash
python main.py
```

Para debugear por separado cada elemento:

1. **Agente en terminal**: `python agent/main.py` → Ejecutará el agente en terminal, podrás interactuar con el y ver el proceso de razonamiento
2. **FastAPI en terminal**: `python .\FastAPI\api_server.py`
3. **Lanzar el Frontend**: `streamlit run frontend/frontend.py`

---

### 🐋 Ejecución Rápida con Docker (No carga streamlit ni Google Calendar)

Dos Comandos - Listo para usar

```bash
# 1. Construir la imagen
docker build -t foodlooker .

# 2. Ejecutar el contenedor
docker run -p 8000:8000 -p 8501:8501 --env-file .env foodlooker
```

Acceso a la Aplicación

- 🖥️ **Frontend**: http://localhost:8501
- 📡 **Backend API**: http://localhost:8000
- 📖 **Documentación API**: http://localhost:8000/docs

---

## 📁 Project Structure

```
genai-tfm/
│
├── agent/                          # Core agent system (LangGraph + ReAct)
│   ├── graph.py                   # LangGraph orchestration and nodes
│   ├── main.py                    # Agent execution entry point (terminal)
│   ├── prompts.py                 # Prompt loader and formatter
│   ├── state.py                   # State management and data models
│   └── tools.py                   # External tools (Maps, Booking, Calendar, Phone)
│
├── backend/                        # Backend services
│   ├── calendar_tools.py          # Google Calendar integration
│   ├── call_service.py            # Twilio/ElevenLabs phone call service
│   └── google_places.py           # Google Places API integration
│
├── config/
│   └── settings.py                # Configuration loader (.env)
│
├── FastAPI/                        # API backend
│   ├── api_server.py              # FastAPI server
│   └── test_api.py                # API tests (manual)
│
├── frontend/                       # User interface
│   ├── frontend.py                # Streamlit UI
│   └── frontend_api_helpers.py    # API helper functions
│
├── prompts/                        # Prompt templates (markdown)
│   ├── agent_system_prompt.md     # Main agent system prompt
│   ├── call_script_generation.md  # Phone call script template
│   └── call_result_analysis.md    # Call result analysis template
│
├── tests/                          # Automated tests (pytest)
│   ├── conftest.py                # Shared fixtures and mocks
│   ├── unit/                      # Unit tests
│   │   ├── test_agent_graph.py   # Tests for agent graph logic
│   │   ├── test_tools.py         # Tests for agent tools
│   │   ├── test_state.py         # Tests for state management
│   │   ├── test_prompts.py       # Tests for prompt system
│   │   └── test_settings.py      # Tests for configuration
│   ├── integration/               # Integration tests
│   │   ├── test_google_places.py # Tests for Google Places API
│   │   ├── test_call_service.py  # Tests for phone call service
│   │   ├── test_calendar_tools.py# Tests for calendar integration
│   │   └── test_api_server.py    # Tests for FastAPI endpoints
│   └── fixtures/                  # Test data and mock responses
│       └── mock_responses.py     # Sample API responses for testing
│
├── evals/                          # LLM Evaluation with DeepEval
│   ├── datasets.py                # Golden test datasets for evaluation
│   ├── metrics.py                 # DeepEval metrics configuration
│   ├── run_evals.py               # Evaluation runner script
│   └── results/                   # Evaluation results output
│
├── .coveragerc                     # Coverage configuration (output to test_results/)
├── .env                            # Environment variables (API keys)
├── .env.example                    # Environment template
├── Dockerfile                      # Docker configuration
├── main.py                         # Main entry point (starts all services)
├── pytest.ini                      # Pytest configuration
├── README.md                       # Project documentation
└── requirements.txt                # Python dependencies
└── tool_description.md             # Tools available
```

---

## 🧪 Testing

El proyecto incluye tests automatizados con pytest. Los resultados se generan en `test_results/` (configurado en `.coveragerc` y `pytest.ini`).

```bash
# Instalar dependencias de testing
pip install -r requirements.txt

# Ejecutar todos los tests
pytest

# Ejecutar solo tests unitarios
pytest tests/unit/

# Ejecutar solo tests de integración
pytest tests/integration/

# Ejecutar con cobertura de código (resultados en test_results/htmlcov/)
pytest --cov

# Ejecutar un archivo específico con verbose
pytest tests/unit/test_agent_graph.py -v

# Generar reporte JUnit XML (para CI/CD)
pytest --junitxml=test_results/junit.xml
```

Los resultados se guardan en:

- `test_results/htmlcov/` - Reporte HTML de cobertura
- `test_results/.coverage` - Datos de cobertura
- `test_results/junit.xml` - Reporte JUnit (opcional)

---

## 📊 Evaluación del Agente (DeepEval)

El proyecto incluye un sistema de evaluación de calidad del agente usando [DeepEval](https://deepeval.com/) de Confident AI.

### Métricas implementadas

| Métrica              | Descripción                                                |
| -------------------- | ---------------------------------------------------------- |
| **Tool Correctness** | ¿El agente usa las herramientas correctas para cada tarea? |
| **Task Completion**  | ¿El agente completa exitosamente la tarea del usuario?     |
| **Response Quality** | ¿Las respuestas son claras, completas y útiles?            |

### Ejecutar evaluaciones

Las evaluaciones siempre ejecutan el agente real contra los casos de prueba definidos en `evals/datasets.py`.

```bash
# Ejecutar todas las evaluaciones
python evals/run_evals.py

# Ejecutar solo evaluaciones de búsqueda
python evals/run_evals.py --category search

# Ejecutar solo localmente (sin enviar a Confident AI)
python evals/run_evals.py --local

# Ejecutar en modo silencioso
python evals/run_evals.py --quiet

# Guardar resultados en archivo específico
python evals/run_evals.py --output results/mi_evaluacion.json
```

### Servicios automáticos

El sistema de evaluación arranca automáticamente los servicios necesarios:

- **Servicio de llamadas**: Se inicia automáticamente cuando se ejecutan tests de la categoría `phone_call`
- El servicio se detiene al finalizar las evaluaciones

### Categorías de evaluación

- `search` - Búsqueda de restaurantes
- `missing_info` - Falta información para reservar
- `booking` - Flujo completo de reservas
- `phone_call` - Llamadas telefónicas (requiere Twilio configurado)
- `calendar` - Eventos de calendario
- `web_search` - Búsquedas web
- `multi_turn` - Conversaciones multi-turno
- `edge_case` - Casos especiales (saludos, preguntas fuera de dominio)

### Integración con Confident AI

Para ver los resultados en el dashboard de Confident AI:

1. Configura `CONFIDENT_API_KEY` en tu archivo `.env`
2. Ejecuta las evaluaciones:

```bash
# Login (una sola vez)
deepeval login

# Ejecutar evaluaciones con tracking automático
python evals/run_evals.py
```

Los resultados se guardan localmente en `evals/results/` y se envían automáticamente al dashboard de Confident AI si está configurado.


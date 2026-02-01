"""
===========================================================
CALENDAR TOOLS - Integración con Google Calendar
===========================================================

Usa langchain_google_community.CalendarToolkit para gestionar
el calendario del usuario.

Configuración:
1. Descarga credentials.json de Google Cloud Console (OAuth credentials token)
2. Colócalo en la raíz del proyecto
3. La primera ejecución abrirá el navegador para autorizar
4. Se generará token.json automáticamente

Requiere:
- pip install langchain-google-community
"""

from typing import List, Any
from dotenv import load_dotenv
from langchain_google_community import CalendarToolkit
import datetime
import os.path
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

# ===========================================================
# CONFIGURACIÓN
# ===========================================================

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.freebusy",
    "https://www.googleapis.com/auth/calendar.events.owned",
]
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")


# Cache de herramientas
_calendar_tools: List[Any] = []
_initialized = False


def is_calendar_configured() -> bool:
    """Autentica con Google Calendar y obtiene credenciales."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    if creds != None:
        return True
    else:
        return False


def init_calendar() -> List[Any]:
    """
    Inicializa y devuelve las herramientas de Google Calendar.

    Usa CalendarToolkit de langchain-google-community que proporciona:
    - create_calendar_event: Crear eventos
    - get_calendar_events: Listar eventos
    - update_calendar_event: Modificar eventos
    - delete_calendar_event: Eliminar eventos
    - search_calendar_events: Buscar eventos

    Returns:
        Lista de herramientas de calendario
    """
    global _calendar_tools, _initialized

    # Si ya se inicializó, devolver cache
    if _initialized:
        return _calendar_tools

    # Verificar configuración
    if not is_calendar_configured():
        print(f"⚠️  Google Calendar no está correctamente configurado.")
        _initialized = True
        return []

    try:
        print("🔄 Inicializando Google Calendar...")

        # Crear toolkit (esto puede abrir el navegador la primera vez)
        toolkit = CalendarToolkit()

        # Obtener herramientas
        tools = toolkit.get_tools()

        if tools:
            print(f"✅ Google Calendar habilitado ({len(tools)} herramientas):")
            for tool in tools:
                print(f"   - {tool.name}")
            _calendar_tools = tools
        else:
            print("⚠️  CalendarToolkit no devolvió herramientas")

        _initialized = True
        return _calendar_tools

    except ImportError as e:
        print("⚠️  langchain-google-community no instalado")
        print("   Instala con: pip install langchain-google-community")
        _initialized = True
        return []

    except Exception as e:
        print(f"⚠️  Error inicializando Google Calendar: {e}")
        _initialized = True
        return []


def get_calendar_tools() -> List[Any]:
    """
    Obtiene las herramientas de calendario (inicializa si es necesario).

    Returns:
        Lista de herramientas de calendario
    """
    if not _initialized:
        return init_calendar()
    return _calendar_tools

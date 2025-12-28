"""
Helper functions para conectar el frontend de Streamlit con el API server
Estas funciones reemplazan las llamadas directas a call_llm y backend_google_places
"""
import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, date, time


# ==========================================
# CONFIGURACIÓN DEL API
# ==========================================
API_BASE_URL = "http://localhost:8000"
API_KEY = "demo-api-key"


def search_restaurants_via_agent(
    user_query: str,
    location: str,
    party_size: int = 2,
    selected_date: Optional[date] = None,
    selected_time: Optional[time] = None,
    mins: Optional[int] = None,
    travel_mode: str = "walking",
    max_distance: float = 15.0,
    price_level: int = 2,
    extras: str = ""
) -> Dict[str, Any]:
    """
    Envía la búsqueda del usuario al API server para que el agente
    busque restaurantes y gestione la disponibilidad.
    
    Args:
        user_query: Query original del usuario
        location: Ubicación de búsqueda
        party_size: Número de personas
        selected_date: Fecha seleccionada (opcional)
        selected_time: Hora seleccionada (opcional)
        mins: Minutos de espera si no hay fecha/hora específica
        travel_mode: Modo de transporte
        max_distance: Distancia máxima en km
        price_level: Nivel de precio (1-4)
        extras: Preferencias adicionales
    
    Returns:
        Diccionario con:
        - status: "success", "needs_input", "failed"
        - results: Lista de restaurantes (si success)
        - message: Mensaje del agente
        - session_id: ID de sesión para continuar conversación
    """
    
    # Preparar el contexto de la sesión
    session_context = {
        "original_query": user_query,
        "location": location,
        "party_size": party_size,
        "travel_mode": travel_mode,
        "max_distance_km": max_distance,
        "price_level": price_level,
        "extras": extras
    }
    
    # Añadir fecha/hora si están especificadas
    if selected_date:
        session_context["date"] = selected_date.isoformat()
    if selected_time:
        session_context["time"] = selected_time.isoformat()
    if mins and not selected_date:  # Solo si no hay fecha específica
        session_context["mins_to_wait"] = mins
    
    # Preparar el payload para el endpoint del agente
    payload = {
        "user_id": f"streamlit_user_{datetime.now().timestamp()}",
        "session_context": session_context,
        "ranked_restaurants": []  # Vacío porque el agente debe buscarlos
    }
    
    try:
        # Hacer la petición al API server
        print(f"📡 Enviando petición al API server: {API_BASE_URL}/api/reservation-requests")
        print(f"📦 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{API_BASE_URL}/api/reservation-requests",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY
            },
            timeout=30  # 30 segundos timeout
        )
        
        print(f"✅ Respuesta recibida: Status {response.status_code}")
        
        # Verificar si la petición fue exitosa
        response.raise_for_status()
        
        # Parsear la respuesta
        result = response.json()
        print(f"📄 Resultado: {json.dumps(result, indent=2)[:500]}...")
        
        return result
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al API server")
        return {
            "status": "failed",
            "message": "Error: No se pudo conectar al servidor. ¿Está corriendo el API server en localhost:8000?",
            "results": []
        }
    
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout esperando respuesta del API")
        return {
            "status": "failed",
            "message": "Error: El servidor tardó demasiado en responder. Intenta de nuevo.",
            "results": []
        }
    
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP: {e}")
        error_detail = "Error desconocido"
        try:
            error_detail = response.json().get("detail", str(e))
        except:
            error_detail = str(e)
        
        return {
            "status": "failed",
            "message": f"Error del servidor: {error_detail}",
            "results": []
        }
    
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "status": "failed",
            "message": f"Error inesperado: {str(e)}",
            "results": []
        }


def continue_agent_conversation(
    session_id: str,
    user_response: str
) -> Dict[str, Any]:
    """
    Continúa una conversación con el agente cuando necesita más información.
    
    Args:
        session_id: ID de la sesión anterior
        user_response: Respuesta del usuario a la pregunta del agente
    
    Returns:
        Diccionario con la nueva respuesta del agente
    """
    
    payload = {
        "session_id": session_id,
        "user_message": user_response
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/agent/continue",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY
            },
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        print(f"Error continuando conversación: {e}")
        return {
            "status": "failed",
            "message": f"Error: {str(e)}"
        }


def check_restaurant_availability(
    venue_id: str,
    reservation_date: date,
    party_size: int,
    shift_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Consulta disponibilidad directa de un restaurante específico.
    
    Args:
        venue_id: ID del restaurante en ReserveHub
        reservation_date: Fecha de la reserva
        party_size: Número de personas
        shift_id: ID del turno (opcional)
    
    Returns:
        Lista de slots disponibles
    """
    
    payload = {
        "venue_id": venue_id,
        "reservation_date": reservation_date.isoformat(),
        "party_size": party_size
    }
    
    if shift_id:
        payload["shift_id"] = shift_id
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/availability",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY
            },
            timeout=10
        )
        
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        print(f"Error consultando disponibilidad: {e}")
        return []


def create_reservation(
    venue_id: str,
    reservation_date: date,
    reservation_time: time,
    party_size: int,
    customer_name: str,
    customer_phone: str,
    customer_email: Optional[str] = None,
    notes: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Crea una reserva directa sin pasar por el agente.
    
    Returns:
        Diccionario con los datos de la reserva o None si falla
    """
    
    payload = {
        "venue_id": venue_id,
        "reservation_date": reservation_date.isoformat(),
        "reservation_time": reservation_time.isoformat(),
        "party_size": party_size,
        "name": customer_name,
        "phone": customer_phone,
        "email": customer_email,
        "notes": notes
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/reservations",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY
            },
            timeout=10
        )
        
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        print(f"Error creando reserva: {e}")
        return None


# ==========================================
# FUNCIÓN HELPER PARA PROCESAR RESPUESTA
# ==========================================

def process_agent_response_for_ui(agent_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convierte la respuesta del agente al formato que espera la UI del frontend.
    
    Args:
        agent_response: Respuesta del endpoint /api/reservation-requests
    
    Returns:
        Lista de restaurantes en formato UI:
        [
            {
                "id": 1,
                "name": "Restaurante X",
                "area": "Zona Y",
                "price": "€€",
                "rating": 4.5,
                "has_availability": True,
                "available_slots": ["20:00", "20:30", "21:00"]
            },
            ...
        ]
    """
    
    status = agent_response.get("status")
    
    # Si el agente necesita más información
    if status == "needs_input":
        return []
    
    # Si hubo un error
    if status == "failed":
        return []
    
    # Si fue exitoso, extraer los restaurantes
    if status == "success":
        # El agente debería devolver información de los restaurantes
        # que encontró en su búsqueda
        
        # TODO: Aquí necesitas adaptar según la estructura exacta
        # que devuelva tu agente. Por ahora, asumo una estructura básica:
        
        restaurants = agent_response.get("restaurants", [])
        attempts = agent_response.get("attempts", [])
        
        processed = []
        
        for idx, restaurant in enumerate(restaurants[:3]):  # Top 3
            processed.append({
                "id": idx + 1,
                "name": restaurant.get("name", "Restaurante desconocido"),
                "area": restaurant.get("neighborhood", restaurant.get("area", "N/A")),
                "price": _format_price_level(restaurant.get("price_level")),
                "rating": restaurant.get("rating", 0.0),
                "has_availability": restaurant.get("has_reservehub", False),
                "available_slots": [
                    slot.get("slot_time") 
                    for slot in restaurant.get("available_slots", [])
                ]
            })
        
        return processed
    
    return []


def _format_price_level(price_level: Optional[int]) -> str:
    """Convierte nivel de precio numérico a string de euros"""
    if price_level is None:
        return "€€"
    
    price_map = {
        1: "€",
        2: "€€",
        3: "€€€",
        4: "€€€€"
    }
    
    return price_map.get(price_level, "€€")

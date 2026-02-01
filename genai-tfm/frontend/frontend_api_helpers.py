"""
Helper functions para conectar el frontend de Streamlit con el API server

CORREGIDO:
- Recibe historial COMPLETO desde el frontend
- NO añade el mensaje actual (ya viene incluido en el historial)
- Simplificado y limpio
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
    messages: List[Dict[str, str]],
    location: str = "",
    party_size: int = 2,
    selected_date: Optional[date] = None,
    selected_time: Optional[time] = None,
    mins: Optional[int] = None,
    travel_mode: str = "walking",
    max_distance: float = 15.0,
    price_level: int = 2,
    extras: str = "",
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Envía la conversación al API server.
    
    CORREGIDO: Recibe el historial COMPLETO (incluyendo el mensaje actual)
    desde el frontend. No manipula ni añade mensajes.
    
    Args:
        messages: Historial COMPLETO de mensajes [{"role": "user/assistant", "content": "..."}]
        location: Ubicación de búsqueda (del formulario)
        party_size: Número de personas
        selected_date: Fecha seleccionada (opcional)
        selected_time: Hora seleccionada (opcional)
        mins: Minutos de espera
        travel_mode: Modo de transporte
        max_distance: Distancia máxima en km
        price_level: Nivel de precio (1-4)
        extras: Preferencias adicionales
        session_id: ID de sesión existente
    
    Returns:
        Diccionario con status, message, restaurants, etc.
    """
    
    # Generar session_id si no existe
    if not session_id:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Preparar contexto de sesión (preferencias del formulario)
    session_context = {
        "travel_mode": travel_mode,
        "max_distance_km": max_distance,
        "price_level": price_level,
    }
    
    if location and location.strip():
        session_context["location"] = location
    
    if party_size:
        session_context["party_size_hint"] = party_size
    
    if extras and extras.strip():
        session_context["extras"] = extras
    
    if selected_date:
        session_context["date"] = selected_date.isoformat()
    
    if selected_time:
        session_context["time"] = selected_time.isoformat()
    
    if mins and not selected_date:
        session_context["mins_to_wait"] = mins
    
    # Preparar payload - enviamos el historial TAL CUAL viene del frontend
    payload = {
        "session_id": session_id,
        "user_id": "streamlit_user",
        "messages": messages,  # ← Historial COMPLETO, sin modificar
        "session_context": session_context
    }
    
    try:
        print(f"\n{'='*50}")
        print(f"📡 Enviando al API: {API_BASE_URL}/api/reservation-requests")
        print(f"📨 Mensajes: {len(messages)}")
        for i, msg in enumerate(messages[-3:]):  # Solo últimos 3 para el log
            print(f"   {i+1}. [{msg['role']}]: {msg['content'][:50]}...")
        print(f"{'='*50}\n")
        
        response = requests.post(
            f"{API_BASE_URL}/api/reservation-requests",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY
            },
            timeout=360  # 6 minutos para llamadas telefónicas largas
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Asegurar session_id en respuesta
        if "session_id" not in result or result["session_id"] is None:
            result["session_id"] = session_id
        
        print(f"✅ Respuesta: status={result.get('status')}")
        
        return result
        
    except requests.exceptions.ConnectionError:
        return {
            "status": "failed",
            "message": "No se pudo conectar al servidor. ¿Está corriendo en localhost:8000?",
            "session_id": session_id
        }
    
    except requests.exceptions.Timeout:
        return {
            "status": "failed",
            "message": "El servidor tardó demasiado. Intenta de nuevo.",
            "session_id": session_id
        }
    
    except requests.exceptions.HTTPError as e:
        error_detail = "Error desconocido"
        try:
            error_detail = response.json().get("detail", str(e))
        except:
            error_detail = str(e)
        
        return {
            "status": "failed",
            "message": f"Error del servidor: {error_detail}",
            "session_id": session_id
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            "status": "failed",
            "message": f"Error inesperado: {str(e)}",
            "session_id": session_id
        }


def process_agent_response_for_ui(agent_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convierte la respuesta del agente al formato que espera la UI.
    """
    status = agent_response.get("status")
    
    if status not in ["success", "needs_input", "completed"]:
        return []
    
    restaurants = agent_response.get("restaurants", [])
    
    if not restaurants:
        return []
    
    processed = []
    
    for idx, restaurant in enumerate(restaurants[:6]):
        processed.append({
            "id": idx + 1,
            "name": restaurant.get("name", "Restaurante"),
            "area": restaurant.get("address", restaurant.get("neighborhood", "N/A")),
            "neighborhood": restaurant.get("neighborhood", "N/A"),
            "price": _format_price_level(restaurant.get("price_level")),
            "rating": restaurant.get("rating", "N/A"),
            "user_ratings_total": restaurant.get("user_ratings_total", 0),
            "has_availability": restaurant.get("has_api_booking", False),
            "available": restaurant.get("available"),
            "availability": restaurant.get("availability", ""),
            "place_id": restaurant.get("place_id"),
            "phone": restaurant.get("phone", ""),
            "opening_hours": restaurant.get("opening_hours", {}),
            "photo_name": restaurant.get("photo_name")
        })
    
    return processed


def _format_price_level(price_level: Optional[int]) -> str:
    """Convierte nivel de precio numérico a string de euros"""
    if price_level is None:
        return "€€"
    
    return {1: "€", 2: "€€", 3: "€€€", 4: "€€€€"}.get(price_level, "€€")
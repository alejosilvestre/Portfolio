# backend_reservehub.py
"""
Módulo para conectar con la API de ReserveHub (mock interno)
y verificar disponibilidad de restaurantes
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, date, time
from pydantic import BaseModel


class AvailabilityQuery(BaseModel):
    """Query para consultar disponibilidad"""
    venue_id: str
    reservation_date: date
    reservation_time: time
    party_size: int
    shift_id: Optional[str] = None


class ReservationRequest(BaseModel):
    """Request para crear una reserva"""
    venue_id: str
    reservation_date: date
    reservation_time: time
    party_size: int
    name: str
    phone: str
    email: Optional[str] = None
    notes: Optional[str] = None
    shift_id: Optional[str] = None


class ReserveHubClient:
    """Cliente para interactuar con ReserveHub API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "demo-api-key"):
        self.base_url = base_url
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
    
    def check_venue_exists(self, venue_name: str) -> Optional[Dict]:
        """
        Verifica si un restaurante existe en ReserveHub
        Retorna el venue si existe, None si no
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/venues",
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            
            venues = response.json()
            # Buscar por nombre (case insensitive)
            for venue in venues:
                if venue["name"].lower() == venue_name.lower():
                    return venue
            return None
            
        except Exception as e:
            print(f"Error verificando venue: {e}")
            return None
    
    def get_venue_shifts(self, venue_id: str) -> List[Dict]:
        """Obtiene los turnos disponibles de un restaurante"""
        try:
            response = requests.get(
                f"{self.base_url}/api/venues/{venue_id}/shifts",
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error obteniendo turnos: {e}")
            return []
    
    def check_availability(
        self,
        venue_id: str,
        reservation_date: date,
        party_size: int,
        shift_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Consulta disponibilidad de un restaurante
        Retorna lista de slots disponibles
        """
        try:
            query = {
                "venue_id": venue_id,
                "reservation_date": reservation_date.isoformat(),
                "party_size": party_size,
                "shift_id": shift_id
            }
            
            response = requests.post(
                f"{self.base_url}/api/availability",
                headers=self.headers,
                json=query,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Error consultando disponibilidad: {e}")
            return []
    
    def create_reservation(
        self,
        venue_id: str,
        reservation_date: date,
        reservation_time: time,
        party_size: int,
        customer_name: str,
        customer_phone: str,
        customer_email: Optional[str] = None,
        notes: Optional[str] = None,
        shift_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Crea una reserva en ReserveHub"""
        try:
            reservation_data = {
                "venue_id": venue_id,
                "reservation_date": reservation_date.isoformat(),
                "reservation_time": reservation_time.isoformat(),
                "party_size": party_size,
                "name": customer_name,
                "phone": customer_phone,
                "email": customer_email,
                "notes": notes,
                "shift_id": shift_id
            }
            
            response = requests.post(
                f"{self.base_url}/api/reservations",
                headers=self.headers,
                json=reservation_data,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Error creando reserva: {e}")
            return None


# Función auxiliar para enriquecer resultados de Google Places con disponibilidad
def enrich_with_availability(
    google_places_results: List[Dict],
    reservation_date: date,
    party_size: int,
    client: ReserveHubClient = None
) -> List[Dict]:
    """
    Enriquece los resultados de Google Places con datos de disponibilidad
    de ReserveHub si el restaurante existe en el sistema
    """
    if client is None:
        client = ReserveHubClient()
    
    enriched_results = []
    
    for place in google_places_results:
        result = place.copy()
        result["has_reservehub"] = False
        result["available_slots"] = []
        result["venue_id"] = None
        
        # Verificar si el restaurante está en ReserveHub
        venue = client.check_venue_exists(place.get("name", ""))
        
        if venue:
            result["has_reservehub"] = True
            result["venue_id"] = venue["id"]
            
            # Consultar disponibilidad
            slots = client.check_availability(
                venue_id=venue["id"],
                reservation_date=reservation_date,
                party_size=party_size
            )
            
            # Filtrar solo slots disponibles
            available = [s for s in slots if s.get("available", False)]
            result["available_slots"] = available
            
            # Agregar el primer slot disponible como sugerencia
            if available:
                result["suggested_time"] = available[0]["slot_time"]
            else:
                result["suggested_time"] = None
        
        enriched_results.append(result)
    
    return enriched_results
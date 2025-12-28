"""
===========================================================
AGENT TOOLS - Herramientas del Agente
===========================================================

Este módulo contiene todas las herramientas externas que el
agente puede usar para interactuar con el mundo.

¿Por qué es importante?
-----------------------
- Abstrae la complejidad de las APIs externas
- Proporciona una interfaz uniforme para el agente
- Facilita el testing con mocks
- Permite expandir sin modificar el núcleo del agente

Herramientas disponibles:
-------------------------
1. GooglePlacesTool: Búsqueda de restaurantes
2. CoverManagerTool: Verificación de disponibilidad y reserva (MOCK)
3. TwilioVoiceTool: Llamadas telefónicas para reserva (MOCK)

Arquitectura:
-------------
Cada herramienta sigue el patrón:
- __init__: Inicialización (API keys, config)
- run: Método principal de ejecución
- parse_result: Normalización de la respuesta
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import random
from datetime import datetime, timedelta
import json

# Modulo Google places API
from backend.backend_google_places import PlaceSearchPayload, places_text_search


# ===========================================================
# 1. BASE TOOL CLASS
# ===========================================================

class BaseTool:
    """
    Clase base para todas las herramientas.
    
    Proporciona estructura común y logging básico.
    """
    def __init__(self, name: str):
        self.name = name
        self.call_count = 0
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """Método principal a implementar por cada herramienta."""
        raise NotImplementedError
    
    def log_call(self, params: Dict[str, Any], result: Dict[str, Any]):
        """Log de la llamada para debugging."""
        self.call_count += 1
        print(f"[{self.name}] Call #{self.call_count}")
        print(f"  Params: {json.dumps(params, indent=2)}")
        print(f"  Result keys: {list(result.keys())}")


# ===========================================================
# 2. GOOGLE PLACES TOOL
# ===========================================================

class GooglePlacesTool(BaseTool):
    """
    Herramienta para buscar restaurantes usando Google Places API.
    
    Wrapper sobre tu función places_text_search existente.
    """
    
    def __init__(self):
        super().__init__("GooglePlaces")
    
    def run(
        self,
        query: str,
        location: Optional[str] = None,
        radius: Optional[int] = None,
        price_level: Optional[int] = None,
        extras: Optional[str] = None,
        max_travel_time: Optional[int] = None,
        travel_mode: Optional[str] = "walking"
    ) -> Dict[str, Any]:
        """
        Busca restaurantes usando Google Places.
        
        Args:
            query: Tipo de comida o nombre del restaurante
            location: Ubicación (ciudad, dirección, o "lat,lng")
            radius: Radio de búsqueda en metros
            price_level: Nivel de precio (0-4)
            extras: Palabras clave adicionales
            max_travel_time: Tiempo máximo de viaje en minutos
            travel_mode: Modo de transporte
        
        Returns:
            Dict con:
            - restaurants: Lista de restaurantes encontrados
            - total_found: Número total de resultados
            - search_params_used: Parámetros usados en la búsqueda
        """
        # Construir payload
        payload = PlaceSearchPayload(
            query=query,
            location=location,
            radius=radius,
            price_level=price_level,
            extras=extras,
            max_travel_time=max_travel_time,
            travel_mode=travel_mode
        )
        
        results = places_text_search(payload)
    
        
        result = {
            "restaurants": results,  # La lista de restaurantes
            "total_found": len(results),
            "search_params_used": {
                "query": query,
                "location": location,
                "radius": radius,
                "price_level": price_level
                }
            }
    
        self.log_call({
            "query": query,
            "location": location
        }, result)
    
        return result
    
    def _generate_mock_results(self, query: str, location: str) -> List[Dict[str, Any]]:
        """
        Genera resultados de prueba para desarrollo.
        ELIMINAR cuando integres tu API real.
        """
        mock_restaurants = [
            {
                "place_id": "ChIJ_mock_001",
                "name": f"Restaurante {query.title()} Premium",
                "address": f"Calle Principal 123, {location or 'Madrid'}",
                "rating": 4.7,
                "user_ratings_total": 520,
                "price_level": 2,
                "phone": "+34 912 345 678",
                "website": "https://example.com",
                "location": {"lat": 40.4168, "lng": -3.7038},
                "neighborhood": location or "Centro",
                "opening_hours": {
                    "open_now": True,
                    "weekday_text": ["Lunes: 13:00-23:00"] * 7
                },
                "types": ["restaurant", "food"]
            },
            {
                "place_id": "ChIJ_mock_002",
                "name": f"{query.title()} Gourmet",
                "address": f"Avenida Central 45, {location or 'Madrid'}",
                "rating": 4.5,
                "user_ratings_total": 380,
                "price_level": 3,
                "phone": "+34 913 456 789",
                "website": None,
                "location": {"lat": 40.4200, "lng": -3.7050},
                "neighborhood": location or "Centro",
                "opening_hours": {
                    "open_now": True,
                    "weekday_text": ["Martes-Domingo: 12:00-00:00"]
                },
                "types": ["restaurant", "food"]
            },
            {
                "place_id": "ChIJ_mock_003",
                "name": f"La Casa de {query.title()}",
                "address": f"Plaza Mayor 7, {location or 'Madrid'}",
                "rating": 4.8,
                "user_ratings_total": 650,
                "price_level": 2,
                "phone": "+34 914 567 890",
                "website": "https://example2.com",
                "location": {"lat": 40.4150, "lng": -3.7070},
                "neighborhood": location or "Centro",
                "opening_hours": {
                    "open_now": False,
                    "weekday_text": ["Cerrado los lunes"]
                },
                "types": ["restaurant", "food", "point_of_interest"]
            }
        ]
        
        return mock_restaurants


# ===========================================================
# 3. COVERMANAGER MOCK TOOL
# ===========================================================

class CoverManagerTool(BaseTool):
    """
    Herramienta para verificar disponibilidad y hacer reservas.
    
    NOTA: Esta es una versión MOCK para desarrollo.
    Cuando tengas acceso a CoverManager real, reemplaza la lógica interna.
    
    Mock Inteligente:
    -----------------
    - Simula qué restaurantes tienen API basándose en patrones reales
    - Determina disponibilidad según hora pico/valle
    - Genera horarios alternativos realistas
    """
    
    def __init__(self):
        super().__init__("CoverManager")
        # Cache de decisiones para mantener consistencia
        self._api_cache = {}
        self._availability_cache = {}
    
    def _has_online_booking(self, place_id: str, restaurant_name: str, 
                           website: Optional[str] = None, 
                           rating: Optional[float] = None,
                           user_ratings_total: Optional[int] = 0) -> bool:
        """
        Determina si un restaurante tiene sistema de reservas online.
        
        Usa heurísticas basadas en patrones reales:
        - Cadenas conocidas → Siempre tienen API
        - Tiene website → Mayor probabilidad
        - Popular (rating alto + muchas reviews) → Mayor probabilidad
        
        Args:
            place_id: ID único del restaurante
            restaurant_name: Nombre del restaurante
            website: URL del sitio web (si tiene)
            rating: Rating promedio
            user_ratings_total: Número de reviews
        
        Returns:
            True si tiene sistema de reservas online
        """
        # Usar cache para consistencia (mismo restaurante, misma respuesta)
        if place_id in self._api_cache:
            return self._api_cache[place_id]
        
        # ========================================
        # REGLA 1: Cadenas conocidas SIEMPRE tienen API
        # ========================================
        chain_keywords = [
            "domino", "telepizza", "pizza hut", "ginos", 
            "vips", "laterraza", "tgb", "foster", "mcdonalds",
            "burger king", "kfc", "papa john", "american royal"
        ]
        
        name_lower = restaurant_name.lower()
        for keyword in chain_keywords:
            if keyword in name_lower:
                self._api_cache[place_id] = True
                return True
        
        # ========================================
        # REGLA 2: Probabilidades basadas en características
        # ========================================
        import random
        
        # Base: 15% de probabilidad por defecto
        probability = 0.15
        
        # +45% si tiene website
        if website:
            probability += 0.45
        
        # +20% si es muy popular (>500 reviews)
        if user_ratings_total and user_ratings_total > 500:
            probability += 0.20
        
        # +15% si tiene rating excelente (>4.6)
        if rating and rating > 4.6:
            probability += 0.15
        
        # Limitar al 85% máximo (nunca 100% certeza para locales)
        probability = min(probability, 0.85)
        
        # Decisión aleatoria pero determinista por place_id
        random.seed(place_id)  # Seed para consistencia
        has_api = random.random() < probability
        
        self._api_cache[place_id] = has_api
        return has_api
    
    def _is_peak_hour(self, time: str) -> bool:
        """
        Determina si una hora es pico (más demanda).
        
        Horas pico:
        - Comida: 13:00 - 15:30
        - Cena: 20:00 - 22:30
        """
        try:
            hour = int(time.split(":")[0])
            minute = int(time.split(":")[1])
            time_decimal = hour + minute / 60
            
            # Hora de comida
            if 13.0 <= time_decimal <= 15.5:
                return True
            
            # Hora de cena
            if 20.0 <= time_decimal <= 22.5:
                return True
            
            return False
        except:
            return False
    
    def check_availability(
        self,
        place_id: str,
        date: str,
        time: str,
        num_people: int,
        restaurant_name: str = "",
        website: Optional[str] = None,
        rating: Optional[float] = None,
        user_ratings_total: Optional[int] = 0
    ) -> Dict[str, Any]:
        """
        Verifica disponibilidad en un restaurante.
        
        Args:
            place_id: ID del restaurante de Google Places
            date: Fecha en formato YYYY-MM-DD
            time: Hora en formato HH:MM
            num_people: Número de comensales
            restaurant_name: Nombre del restaurante (para detectar cadenas)
            website: URL del sitio web
            rating: Rating promedio
            user_ratings_total: Número de reviews
        
        Returns:
            Dict con:
            - has_api_booking: Si el restaurante tiene integración API
            - available: Si hay disponibilidad
            - available_times: Lista de horarios disponibles
            - message: Mensaje descriptivo
        """
        
        # ========================================
        # PASO 1: Verificar si el restaurante tiene API
        # ========================================
        has_api = self._has_online_booking(
            place_id, 
            restaurant_name, 
            website, 
            rating, 
            user_ratings_total
        )
        
        if not has_api:
            result = {
                "has_api_booking": False,
                "available": None,
                "available_times": [],
                "message": "Este restaurante no tiene sistema de reservas online. Reserva por teléfono."
            }
            self.log_call({
                "place_id": place_id, 
                "restaurant": restaurant_name,
                "date": date, 
                "time": time
            }, result)
            return result
        
        # ========================================
        # PASO 2: Simular disponibilidad realista
        # ========================================
        import random
        
        # Usar cache para consistencia
        cache_key = f"{place_id}_{date}_{time}"
        if cache_key in self._availability_cache:
            return self._availability_cache[cache_key]
        
        # Probabilidad de estar ocupado según hora
        is_peak = self._is_peak_hour(time)
        if is_peak:
            # Hora pico: 60% de probabilidad de estar ocupado
            occupied_probability = 0.60
        else:
            # Hora valle: 20% de probabilidad de estar ocupado
            occupied_probability = 0.20
        
        # Grupos grandes tienen menos disponibilidad
        if num_people >= 6:
            occupied_probability += 0.15
        elif num_people >= 4:
            occupied_probability += 0.05
        
        # Decisión determinista basada en place_id + time
        random.seed(f"{place_id}{time}")
        is_available = random.random() > occupied_probability
        
        # ========================================
        # PASO 3: Generar horarios alternativos si no hay disponibilidad
        # ========================================
        available_times = []
        if not is_available:
            # Ofrecer horarios cercanos (±15, ±30, ±45 minutos)
            for offset in [15, -15, 30, -30, 45, -45]:
                alt_time = self._calculate_time_offset(time, offset)
                available_times.append(alt_time)
        else:
            available_times = [time]
        
        # ========================================
        # PASO 4: Construir respuesta
        # ========================================
        result = {
            "has_api_booking": True,
            "available": is_available,
            "available_times": available_times,
            "message": "Disponibilidad confirmada" if is_available else f"No hay disponibilidad a las {time}, pero hay horarios cercanos"
        }
        
        self._availability_cache[cache_key] = result
        
        self.log_call({
            "place_id": place_id,
            "restaurant": restaurant_name,
            "date": date,
            "time": time,
            "num_people": num_people
        }, result)
        
        return result
    
    def make_reservation(
        self,
        place_id: str,
        restaurant_name: str,
        date: str,
        time: str,
        num_people: int,
        user_name: Optional[str] = "Cliente",
        user_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Realiza una reserva en un restaurante.
        
        Returns:
            Dict con:
            - success: Si la reserva fue exitosa
            - booking_id: ID de la reserva (si exitoso)
            - confirmation_details: Detalles de la reserva
            - error: Mensaje de error (si falló)
        """
        
        # Verifica si el restaurante tiene API
        has_api = self.restaurants_with_api.get(place_id, False)
        
        if not has_api:
            return {
                "success": False,
                "booking_id": None,
                "confirmation_details": None,
                "error": "Restaurante sin sistema de reservas online"
            }
        
        # Simula éxito/fallo
        success = random.choice([True, True, False])  # 66% de éxito
        
        if success:
            booking_id = f"COVER_{random.randint(10000, 99999)}"
            result = {
                "success": True,
                "booking_id": booking_id,
                "confirmation_details": {
                    "restaurant": restaurant_name,
                    "date": date,
                    "time": time,
                    "num_people": num_people,
                    "name": user_name,
                    "phone": user_phone,
                    "booking_reference": booking_id
                },
                "error": None
            }
        else:
            result = {
                "success": False,
                "booking_id": None,
                "confirmation_details": None,
                "error": "Error al procesar la reserva. Intente nuevamente."
            }
        
        self.log_call({
            "place_id": place_id,
            "restaurant": restaurant_name,
            "date": date,
            "time": time
        }, result)
        
        return result
    
    def _calculate_time_offset(self, time: str, minutes: int) -> str:
        """Calcula un horario con offset de minutos."""
        hour, minute = map(int, time.split(":"))
        dt = datetime(2000, 1, 1, hour, minute) + timedelta(minutes=minutes)
        return dt.strftime("%H:%M")


# ===========================================================
# 4. TWILIO VOICE MOCK TOOL
# ===========================================================

class TwilioVoiceTool(BaseTool):
    """
    Herramienta para realizar llamadas telefónicas de reserva.
    
    NOTA: Esta es una versión MOCK para desarrollo.
    Cuando implementes Twilio + ElevenLabs real, reemplaza la lógica.
    """
    
    def __init__(self):
        super().__init__("TwilioVoice")
    
    def make_voice_reservation(
        self,
        restaurant_name: str,
        phone: str,
        date: str,
        time: str,
        num_people: int
    ) -> Dict[str, Any]:
        """
        Realiza una llamada telefónica para reservar.
        
        Flujo simulado:
        1. TTS (ElevenLabs): Genera audio de la petición
        2. Twilio: Realiza la llamada
        3. STT: Transcribe la respuesta del restaurante
        4. LLM: Analiza si la reserva fue confirmada
        
        Returns:
            Dict con:
            - success: Si la llamada fue exitosa
            - transcript: Transcripción de la conversación
            - confirmation: Si el restaurante confirmó
            - message: Resumen de la llamada
        """
        
        # Simula diferentes escenarios
        scenarios = [
            {
                "success": True,
                "confirmation": True,
                "transcript": f"[Restaurante]: Sí, perfecto. Tenemos mesa para {num_people} personas el {date} a las {time}. ¿A nombre de quién?",
                "message": "Reserva confirmada por teléfono"
            },
            {
                "success": True,
                "confirmation": False,
                "transcript": f"[Restaurante]: Lo siento, estamos completos a esa hora. ¿Le vendría bien a las {self._suggest_alternative_time(time)}?",
                "message": "No hay disponibilidad a esa hora, ofrecen alternativa"
            },
            {
                "success": False,
                "confirmation": False,
                "transcript": "[Sistema]: No se pudo completar la llamada. El teléfono no responde.",
                "message": "No se pudo establecer contacto"
            }
        ]
        
        result = random.choice(scenarios)
        
        self.log_call({
            "restaurant": restaurant_name,
            "phone": phone,
            "date": date,
            "time": time,
            "num_people": num_people
        }, result)
        
        return result
    
    def _suggest_alternative_time(self, time: str) -> str:
        """Genera un horario alternativo para el mock."""
        hour, minute = map(int, time.split(":"))
        alt_hour = hour + 1 if hour < 22 else hour - 1
        return f"{alt_hour:02d}:{minute:02d}"


# ===========================================================
# 5. TOOL REGISTRY (Para facilitar acceso)
# ===========================================================

class ToolRegistry:
    """
    Registro centralizado de todas las herramientas.
    
    Facilita el acceso y la gestión de herramientas desde los nodos.
    """
    
    def __init__(self):
        self.google_places = GooglePlacesTool()
        self.cover_manager = CoverManagerTool()
        self.twilio_voice = TwilioVoiceTool()
    
    def get_tool(self, name: str) -> BaseTool:
        """Obtiene una herramienta por nombre."""
        tools = {
            "google_places": self.google_places,
            "cover_manager": self.cover_manager,
            "twilio_voice": self.twilio_voice
        }
        return tools.get(name)
    
    def list_tools(self) -> List[str]:
        """Lista todas las herramientas disponibles."""
        return ["google_places", "cover_manager", "twilio_voice"]


# ===========================================================
# EJEMPLO DE USO
# ===========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST DE HERRAMIENTAS")
    print("=" * 60)
    
    # Inicializar registro de herramientas
    tools = ToolRegistry()
    
    # Test 1: Google Places
    print("\n1. BÚSQUEDA DE RESTAURANTES:")
    print("-" * 60)
    search_result = tools.google_places.run(
        query="pizzería",
        location="Navalcarnero",
        max_travel_time=15,
        travel_mode="driving"
    )
    print(f"Encontrados: {search_result['total_found']} restaurantes")
    for r in search_result['restaurants']:
        print(f"  - {r['name']} ⭐ {r['rating']}")
    
    # Test 2: CoverManager - Verificar disponibilidad
    print("\n2. VERIFICAR DISPONIBILIDAD:")
    print("-" * 60)
    place_id = search_result['restaurants'][0]['place_id']
    availability = tools.cover_manager.check_availability(
        place_id=place_id,
        date="2025-12-21",
        time="20:30",
        num_people=4
    )
    print(f"Tiene API: {availability['has_api_booking']}")
    print(f"Disponible: {availability['available']}")
    if not availability['available']:
        print(f"Horarios alternativos: {availability['available_times']}")
    
    # Test 3: CoverManager - Hacer reserva
    print("\n3. HACER RESERVA:")
    print("-" * 60)
    reservation = tools.cover_manager.make_reservation(
        place_id=place_id,
        restaurant_name=search_result['restaurants'][0]['name'],
        date="2025-12-21",
        time="20:30",
        num_people=4,
        user_name="Juan Pérez",
        user_phone="+34 600 123 456"
    )
    print(f"Éxito: {reservation['success']}")
    if reservation['success']:
        print(f"ID Reserva: {reservation['booking_id']}")
    
    # Test 4: Twilio Voice (fallback)
    print("\n4. FALLBACK A VOZ:")
    print("-" * 60)
    voice_result = tools.twilio_voice.make_voice_reservation(
        restaurant_name=search_result['restaurants'][1]['name'],
        phone="+34 912 345 678",
        date="2025-12-21",
        time="21:00",
        num_people=2
    )
    print(f"Llamada exitosa: {voice_result['success']}")
    print(f"Confirmación: {voice_result['confirmation']}")
    print(f"Transcripción: {voice_result['transcript']}")

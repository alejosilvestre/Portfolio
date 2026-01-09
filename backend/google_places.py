"""
===========================================================
DOCUMENTACIÓN - Módulo de Búsqueda Avanzada Google Places
===========================================================

Este módulo implementa un wrapper mejorado para la API de 
Google Places, permitiendo realizar búsquedas tipo "Text Search"
con geocodificación automática de direcciones, obtención de 
detalles avanzados de cada lugar y filtrado opcional por 
tiempo máximo de viaje usando Distance Matrix.

El flujo interno del módulo es:
1) Geocodificar la ubicación si se pasa como texto.
2) Ejecutar Places Text Search.
3) Para cada sitio encontrado, obtener detalles avanzados (Place Details).
4) Normalizar los datos para facilitar su uso.
5) Filtrar resultados por tiempo máximo de viaje (opcional).
6) Devolver resultados enriquecidos y uniformes.


-----------------------------------------------------------
1. Clase principal de entrada: PlaceSearchPayload
-----------------------------------------------------------

Define todos los parámetros que puede recibir la búsqueda:

- query (str): Término(s) de búsqueda ("cafeterías", "gimnasios", etc.).
- location (str | None): Ciudad, dirección o coordenadas "lat,lng".
  Si no se especifica, usa por defecto Puerta del Sol (Madrid).
- radius (int): Radio de búsqueda en metros (default: 1500).
- price_level (int | None): Filtrado por nivel de precio de 0 a 4.
- extras (list[str]): Palabras clave adicionales para añadir a la query.
- max_travel_time (int | None): Tiempo máximo de viaje en minutos.
- travel_mode (str): walking, driving, bicycling o transit.

Esta clase es el *único input* que debe recibir la función places_text_search().


-----------------------------------------------------------
2. Función principal: places_text_search(payload)
-----------------------------------------------------------

Esta función realiza todo el proceso de búsqueda:

1) Normaliza la ubicación:
   - Si location ya es "lat,lng", la usa directamente.
   - Si no, llama a geocode_location() para convertir texto → coordenadas.

2) Construye la query combinando query + extras.

3) Llama a:
   https://maps.googleapis.com/maps/api/place/textsearch/json

4) Para cada resultado:
   - Extrae datos básicos (nombre, dirección, rating, tipos…)
   - Llama a Place Details para obtener info avanzada:
     horarios, teléfono, website, precio, barrio, etc.
   - Normaliza los datos en un diccionario uniforme.

5) Si el payload incluye max_travel_time:
   Filtra los resultados usando Distance Matrix API.

6) Devuelve un diccionario:
{
    "results": [... lista de lugares con detalles ...],
    "status": "OK",
    "total_results": X
}


-----------------------------------------------------------
3. Ejemplo de uso
-----------------------------------------------------------

from module_name import PlaceSearchPayload, places_text_search

payload = PlaceSearchPayload(
    query="cafeterías",
    location="Gran Via, Madrid",
    extras=["specialty", "wifi"],
    radius=1200,
    max_travel_time=10,
    travel_mode="walking"
)

response = places_text_search(payload)

print(response["total_results"])
for place in response["results"]:
    print(place["name"], "-", place["address"])


-----------------------------------------------------------
4. Ejemplo de output (simplificado)
-----------------------------------------------------------

 {'name': "Sofía's bar & rest",
 'address': 'n° 6, C. del Pozo del Concejo, 6, 28600 Navalcarnero, Madrid, Spain',
 'place_id': 'ChIJfSQ69BWVQQ0Ry_AG9fwvCD0',
 'types': ['establishment', 'food', 'point_of_interest', 'restaurant'],
 'rating': 4.9,
 'user_ratings_total': 297,
 'price_level': None,
 'location': {'lat': 40.2870375, 'lng': -4.014548899999999},
 'neighborhood': 'Navalcarnero',
 'phone': '919 48 86 37',
 'website': None,
 'opening_hours': {'open_now': True,
  'periods': [{'close': {'day': 1, 'time': '0000'},
    'open': {'day': 0, 'time': '0900'}},
   {'close': {'day': 3, 'time': '0000'}, 'open': {'day': 2, 'time': '0900'}},
   {'close': {'day': 4, 'time': '0000'}, 'open': {'day': 3, 'time': '0900'}},
   {'close': {'day': 5, 'time': '0000'}, 'open': {'day': 4, 'time': '0900'}},
   {'close': {'day': 6, 'time': '0000'}, 'open': {'day': 5, 'time': '0900'}},
   {'close': {'day': 0, 'time': '0000'}, 'open': {'day': 6, 'time': '0900'}}],
  'weekday_text': ['Monday: Closed',
   'Tuesday: 9:00\u202fAM\u2009–\u200912:00\u202fAM',
   'Wednesday: 9:00\u202fAM\u2009–\u200912:00\u202fAM',
   'Thursday: 9:00\u202fAM\u2009–\u200912:00\u202fAM',
   'Friday: 9:00\u202fAM\u2009–\u200912:00\u202fAM',
   'Saturday: 9:00\u202fAM\u2009–\u200912:00\u202fAM',
   'Sunday: 9:00\u202fAM\u2009–\u200912:00\u202fAM']}
   }

-----------------------------------------------------------

ESTAMOS ATOPE JEFE DE EQUIPO !!!!

===========================================================
"""
# ---------------- IMPORTS ----------------
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import requests
import os
from dotenv import load_dotenv

from config.settings import load_config
# ---------------- CARGA CONFIGURACIÓN ----------------
config = load_config()

# Carga las variables de entorno desde el .env
load_dotenv(".env")
# ---------------- API KEY ----------------
GOOGLE_MAPS_API_KEY = config["GOOGLE_MAPS_API_KEY"]
if not GOOGLE_MAPS_API_KEY:
    raise ValueError("Debes definir la variable de entorno GOOGLE_MAPS_API_KEY")

# ---------------- Payload de búsqueda ----------------
class PlaceSearchPayload(BaseModel):
    query: str
    location: Optional[str] = None  # ciudad o "lat,lng"
    radius: Optional[int] = None
    price_level: Optional[int] = None
    extras: Optional[str] = None
    max_travel_time: Optional[int] = None  # minutos máximos
    travel_mode: Optional[str] = "walking"  # "walking", "transit", "driving", "bicycling"
    col_date: Optional[str] = None  # fecha de la visita (YYYY-MM-DD)
    col_time: Optional[str] = None  # hora de la visita (HH:MM

# ---------------- Funciones auxiliares ----------------
def geocode_location(location: str) -> Optional[str]:
    """
    Convierte un string de ubicación en lat,lng usando Place Autocomplete + Place Details
    para obtener coordenadas precisas.
    
    MEJORADO: Ahora busca primero en (regions) para ciudades, y si falla, en geocode directo.
    """
    
    # ============================================================
    # MÉTODO 1: Usar Place Autocomplete con types=(regions)
    # Mejor para ciudades, pueblos, barrios
    # ============================================================
    autocomplete_url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    autocomplete_params = {
        "input": location,
        "types": "(regions)",  # ✅ CAMBIO: Ahora busca regiones (ciudades, pueblos)
        "key": GOOGLE_MAPS_API_KEY
    }
    r = requests.get(autocomplete_url, params=autocomplete_params)
    r.raise_for_status()
    data = r.json()
    
    # Si encuentra resultados con (regions)
    if data.get("predictions"):
        place_id = data["predictions"][0]["place_id"]
        
        # Obtener detalles del lugar
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        details_params = {
            "place_id": place_id,
            "fields": "geometry,formatted_address",
            "key": GOOGLE_MAPS_API_KEY
        }
        r2 = requests.get(details_url, params=details_params)
        r2.raise_for_status()
        details = r2.json()
        
        location_data = details.get("result", {}).get("geometry", {}).get("location")
        if location_data:
            coords = f"{location_data.get('lat')},{location_data.get('lng')}"

            return coords
    
    # ============================================================
    # MÉTODO 2: Fallback a Geocoding API directo
    # Si el autocomplete no encuentra nada, usar geocoding directo
    # ============================================================

    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    geocode_params = {
        "address": location,
        "key": GOOGLE_MAPS_API_KEY
    }
    r3 = requests.get(geocode_url, params=geocode_params)
    r3.raise_for_status()
    geocode_data = r3.json()
    
    if geocode_data.get("results"):
        location_data = geocode_data["results"][0]["geometry"]["location"]
        coords = f"{location_data.get('lat')},{location_data.get('lng')}"

        return coords
    
    print(f"❌ No se pudo geocodificar '{location}'")
    return None


def extract_neighborhood(address_components: List[Dict[str, Any]]) -> Optional[str]:
    for comp in address_components:
        if "neighborhood" in comp.get("types", []):
            return comp.get("long_name")
    for comp in address_components:
        if "sublocality_level_1" in comp.get("types", []):
            return comp.get("long_name")
    for comp in address_components:
        if "locality" in comp.get("types", []):
            return comp.get("long_name")
    return None

def normalize_place_details(details: Dict[str, Any]) -> Dict[str, Any]:
    result = details.get("result", {})
    return {
        "name": result.get("name"),
        "address": result.get("formatted_address"),
        "neighborhood": extract_neighborhood(result.get("address_components", [])),
        "phone": result.get("formatted_phone_number"),
        "website": result.get("website"),
        "opening_hours": result.get("opening_hours", {}),
        "place_id": result.get("place_id"),
        "types": result.get("types"),
        "rating": result.get("rating"),
        "user_ratings_total": result.get("user_ratings_total"),
        "price_level": result.get("price_level"),
        "location": result.get("geometry", {}).get("location")
    }

def get_place_details(place_id: str) -> Dict[str, Any]:
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,opening_hours,"
                  "types,rating,user_ratings_total,price_level,geometry,"
                  "address_components,place_id",
        "key": GOOGLE_MAPS_API_KEY
    }
    r = requests.get("https://maps.googleapis.com/maps/api/place/details/json", params=params)
    r.raise_for_status()
    data = r.json()
    return normalize_place_details(data)

def filter_by_travel_time(origin: str, destinations: List[str], max_time: int, mode: str = "walking") -> List[bool]:
    """
    Devuelve un booleano por cada destino: True si está dentro del tiempo máximo de viaje.
    """
    if not destinations:
        return []

    params = {
        "origins": origin,
        "destinations": "|".join(destinations),
        "mode": mode,
        "key": GOOGLE_MAPS_API_KEY
    }
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    results = []
    for elem in data.get("rows", [])[0].get("elements", []):
        if elem.get("status") == "OK":
            duration_sec = elem.get("duration", {}).get("value", 0)
            results.append(duration_sec <= max_time * 60)
        else:
            results.append(False)
    return results

import re

def is_lat_lng(value: str) -> bool:
    """
    Detecta si un string está en formato 'lat,lng', por ejemplo '42.8805533,-8.5422782'
    """
    pattern = r'^-?\d+(\.\d+)?,-?\d+(\.\d+)?$'
    return bool(re.match(pattern, value.strip()))


# ---------------- Función principal ----------------
def places_text_search_old(payload: PlaceSearchPayload) -> Dict[str, Any]:
    
    #location a default a Puerta del Sol, Madrid si no hay location
    location = payload.location if payload.location is not None else "40.4238,-3.7130"


    if location is not None and not  is_lat_lng(location):
        latlng = geocode_location(location)
        if latlng:
            location = latlng
        else:
            raise ValueError(f"No se pudo geocodificar la ubicación: {payload.location}")

    query_keywords = payload.query
    if payload.extras:
        query_keywords += " " + " ".join(payload.extras)

    params = {
        "query": query_keywords,
        "location": location,
        "radius": payload.radius,
        "key": GOOGLE_MAPS_API_KEY
    }
    if payload.price_level is not None:
        params["minprice"] = payload.price_level
        params["maxprice"] = payload.price_level

    r = requests.get("https://maps.googleapis.com/maps/api/place/textsearch/json", params=params)
    r.raise_for_status()
    data = r.json()

    results = []
    destinations = []
    for r_item in data.get("results", []):
        normalized = {
            "name": r_item.get("name"),
            "address": r_item.get("formatted_address"),
            "place_id": r_item.get("place_id"),
            "types": r_item.get("types"),
            "rating": r_item.get("rating"),
            "user_ratings_total": r_item.get("user_ratings_total"),
            "price_level": r_item.get("price_level"),
            "location": r_item.get("geometry", {}).get("location"),
            "neighborhood": extract_neighborhood(r_item.get("address_components", []))
        }
        if normalized["place_id"]:
            details = get_place_details(normalized["place_id"])
            normalized.update(details)
        results.append(normalized)
        destinations.append(f"{normalized['location']['lat']},{normalized['location']['lng']}")

    # Filtrar por tiempo de viaje si se especifica
    if payload.max_travel_time is not None:
        travel_filter = filter_by_travel_time(location, destinations, payload.max_travel_time, payload.travel_mode)
        results = [r for r, keep in zip(results, travel_filter) if keep]

    return results

def places_text_search(payload: PlaceSearchPayload) -> Dict[str, Any]:
    
    # Location a default a Puerta del Sol, Madrid si no hay location
    location = payload.location if payload.location is not None else "40.4238,-3.7130"

    if location is not None and not is_lat_lng(location):
        latlng = geocode_location(location)
        if latlng:
            location = latlng
        else:
            raise ValueError(f"No se pudo geocodificar la ubicación: {payload.location}")

    query_keywords = payload.query
    if payload.extras:
        query_keywords += " " + " ".join(payload.extras)

    # ✅ SOLUCIÓN: Si hay max_travel_time pero no radius, establecer uno razonable
    radius = payload.radius
    if radius is None:
        if payload.max_travel_time:
            # Estimación: 10 min coche ≈ 5-10 km, 10 min walking ≈ 800m
            if payload.travel_mode == "driving":
                radius = payload.max_travel_time * 833  # ~50 km/h → 833 m/min
            elif payload.travel_mode == "bicycling":
                radius = payload.max_travel_time * 250  # ~15 km/h → 250 m/min
            else:  # walking o transit
                radius = payload.max_travel_time * 80   # ~5 km/h → 80 m/min
        else:
            radius = 5000  # Default 5km si no hay ninguna info

    params = {
        "query": query_keywords,
        "location": location,
        "radius": radius,  # ✅ Ahora siempre tiene un valor
        "key": GOOGLE_MAPS_API_KEY
    }
    if payload.price_level is not None:
        params["minprice"] = payload.price_level
        params["maxprice"] = payload.price_level

    r = requests.get("https://maps.googleapis.com/maps/api/place/textsearch/json", params=params)
    r.raise_for_status()
    data = r.json()

    results = []
    destinations = []
    for r_item in data.get("results", []):
        normalized = {
            "name": r_item.get("name"),
            "address": r_item.get("formatted_address"),
            "place_id": r_item.get("place_id"),
            "types": r_item.get("types"),
            "rating": r_item.get("rating"),
            "user_ratings_total": r_item.get("user_ratings_total"),
            "price_level": r_item.get("price_level"),
            "location": r_item.get("geometry", {}).get("location"),
            "neighborhood": extract_neighborhood(r_item.get("address_components", []))
        }
        if normalized["place_id"]:
            details = get_place_details(normalized["place_id"])
            normalized.update(details)
        results.append(normalized)
        destinations.append(f"{normalized['location']['lat']},{normalized['location']['lng']}")

    # Filtrar por tiempo de viaje si se especifica
    if payload.max_travel_time is not None:
        travel_filter = filter_by_travel_time(location, destinations, payload.max_travel_time, payload.travel_mode)
        results = [r for r, keep in zip(results, travel_filter) if keep]

    return results
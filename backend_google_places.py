# ---------------- IMPORTS ----------------
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import requests
import os
from dotenv import load_dotenv

# Carga las variables de entorno desde el .env
load_dotenv(".env")
# ---------------- API KEY ----------------
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
if not GOOGLE_MAPS_API_KEY:
    raise ValueError("Debes definir la variable de entorno GOOGLE_MAPS_API_KEY")

# ---------------- Payload de búsqueda ----------------
class PlaceSearchPayload(BaseModel):
    query: str
    location: Optional[str] = None  # ciudad o "lat,lng"
    radius: Optional[int] = 1500
    price_level: Optional[int] = None
    extras: Optional[List[str]] = []
    max_travel_time: Optional[int] = None  # minutos máximos
    travel_mode: Optional[str] = "walking"  # "walking", "transit", "driving", "bicycling"

# ---------------- Funciones auxiliares ----------------
def geocode_location(location: str) -> Optional[str]:
    """
    Convierte un string de ubicación en lat,lng usando Place Autocomplete + Place Details
    para obtener coordenadas precisas.
    """
    # ---------------- Autocomplete ----------------
    autocomplete_url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    autocomplete_params = {
        "input": location,
        "types": "address",
        "key": GOOGLE_MAPS_API_KEY
    }
    r = requests.get(autocomplete_url, params=autocomplete_params)
    r.raise_for_status()
    data = r.json()

    if not data.get("predictions"):
        return None

    # Tomamos la primera predicción
    place_id = data["predictions"][0]["place_id"]

    # ---------------- Place Details ----------------
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    details_params = {
        "place_id": place_id,
        "fields": "geometry",
        "key": GOOGLE_MAPS_API_KEY
    }
    r2 = requests.get(details_url, params=details_params)
    r2.raise_for_status()
    details = r2.json()

    location_data = details.get("result", {}).get("geometry", {}).get("location")
    if location_data:
        return f"{location_data.get('lat')},{location_data.get('lng')}"
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
        "fields": "name,formatted_address,formatted_phone_number,website,opening_hours,types,rating,user_ratings_total,price_level,geometry,address_component",
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
def places_text_search(payload: PlaceSearchPayload) -> Dict[str, Any]:
    
    #location a default a Puerta del Sol, Madrid si no hay location
    location = payload.location if payload.location is not None else "40.4238,-3.7130"


    if location is not None and not  is_lat_lng(location):
        latlng = geocode_location(location)
        if latlng:
            location = latlng
        else:
            raise ValueError(f"No se pudo geocodificar la ubicación: {payload.location}")

    # if location is not None and "," not in location:
    #     latlng = geocode_location(location)
    #     if latlng:
    #         location = latlng
    #     else:
    #         raise ValueError(f"No se pudo geocodificar la ubicación: {payload.location}")

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

    return {
        "results": results,
        "status": data.get("status"),
        "total_results": len(results)
    }

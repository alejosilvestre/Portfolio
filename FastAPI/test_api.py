"""
Script de prueba para CoverManager API Mock (Versión Simple)
"""
import requests
from datetime import date, time, datetime
import json

# Configuración
BASE_URL = "http://localhost:8000"
API_KEY = "demo-api-key"
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_response(response):
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
    except:
        print(f"Response: {response.text}")

# ==================== PRUEBAS ====================

print_section("1. Health Check")
response = requests.get(f"{BASE_URL}/health")
print_response(response)

print_section("2. Listar Venues (Restaurantes)")
response = requests.get(f"{BASE_URL}/api/venues", headers=HEADERS)
print_response(response)
venues = response.json()
venue_id = venues[0]["id"] if venues else "venue-1"

print_section("3. Obtener detalles del Venue")
response = requests.get(f"{BASE_URL}/api/venues/{venue_id}", headers=HEADERS)
print_response(response)

print_section("4. Listar Turnos del Restaurante")
response = requests.get(f"{BASE_URL}/api/venues/{venue_id}/shifts", headers=HEADERS)
print_response(response)
shifts = response.json()
shift_id = shifts[0]["id"] if shifts else None

print_section("5. Consultar Disponibilidad")
today = date.today()
availability_query = {
    "venue_id": venue_id,
    "date": str(today),
    "party_size": 4,
    "shift_id": shift_id
}
response = requests.post(
    f"{BASE_URL}/api/availability",
    headers=HEADERS,
    json=availability_query
)
print_response(response)

print_section("6. Crear Reserva")
reservation_data = {
    "venue_id": venue_id,
    "date": str(today),
    "time": "20:00:00",
    "party_size": 4,
    "name": "Juan Pérez",
    "phone": "+34666111222",
    "email": "juan@example.com",
    "notes": "Mesa junto a la ventana si es posible",
    "shift_id": shift_id
}
response = requests.post(
    f"{BASE_URL}/api/reservations",
    headers=HEADERS,
    json=reservation_data
)
print_response(response)
reservation = response.json()
reservation_id = reservation["id"]

print_section("7. Obtener Detalles de la Reserva")
response = requests.get(
    f"{BASE_URL}/api/reservations/{reservation_id}",
    headers=HEADERS
)
print_response(response)

print_section("8. Listar Todas las Reservas")
response = requests.get(f"{BASE_URL}/api/reservations", headers=HEADERS)
print_response(response)

print_section("9. Listar Reservas por Fecha")
response = requests.get(
    f"{BASE_URL}/api/reservations?date={today}",
    headers=HEADERS
)
print_response(response)

print_section("10. Actualizar Estado de Reserva a 'seated'")
response = requests.put(
    f"{BASE_URL}/api/reservations/{reservation_id}?status=seated",
    headers=HEADERS
)
print_response(response)

print_section("11. Crear Segunda Reserva")
reservation_data_2 = {
    "venue_id": venue_id,
    "date": str(today),
    "time": "21:00:00",
    "party_size": 2,
    "name": "María García",
    "phone": "+34666333444",
    "email": "maria@example.com"
}
response = requests.post(
    f"{BASE_URL}/api/reservations",
    headers=HEADERS,
    json=reservation_data_2
)
print_response(response)
reservation_2 = response.json()
reservation_id_2 = reservation_2["id"]

print_section("12. Cancelar Reserva")
response = requests.delete(
    f"{BASE_URL}/api/reservations/{reservation_id_2}",
    headers=HEADERS
)
print_response(response)

print_section("13. Listar Reservas Confirmadas")
response = requests.get(
    f"{BASE_URL}/api/reservations?status=confirmed",
    headers=HEADERS
)
print_response(response)

print_section("14. Consultar Disponibilidad con más Personas")
availability_query_large = {
    "venue_id": venue_id,
    "date": str(today),
    "party_size": 8
}
response = requests.post(
    f"{BASE_URL}/api/availability",
    headers=HEADERS,
    json=availability_query_large
)
print_response(response)

print("\n" + "="*60)
print("  ✅ Pruebas Completadas")
print("="*60 + "\n")

"""
Test para ver qué devuelve Places Text Search API
"""
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

print("="*60)
print("🔍 TEST DE PLACES TEXT SEARCH API")
print("="*60)

# Parámetros de búsqueda
params = {
    "query": "restaurante japonés",
    "location": "40.4167,-3.7039",
    "radius": 15000,
    "key": GOOGLE_MAPS_API_KEY
}

print(f"\n📍 Parámetros de búsqueda:")
print(f"   Query: {params['query']}")
print(f"   Location: {params['location']}")
print(f"   Radius: {params['radius']} metros")

url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
print(f"\n🌐 Llamando a: {url}")

try:
    r = requests.get(url, params=params, timeout=10)
    print(f"\n📡 Respuesta HTTP: {r.status_code}")
    
    data = r.json()
    
    print(f"\n📊 Status: {data.get('status')}")
    
    if data.get('status') == 'REQUEST_DENIED':
        print("\n❌ REQUEST_DENIED")
        print(f"   Error: {data.get('error_message')}")
        print("\n   Esto significa que Places Text Search también usa API legacy")
        print("\n   🔧 SOLUCIONES:")
        print("   1. Habilitar 'Places API' (legacy) en Google Cloud Console")
        print("   2. O migrar a usar 'Places API (New)' con el nuevo endpoint")
        
    elif data.get('status') == 'ZERO_RESULTS':
        print("\n⚠️  ZERO_RESULTS - No se encontraron restaurantes")
        print("   Esto es extraño para Madrid...")
        
    elif data.get('status') == 'OK':
        results = data.get('results', [])
        print(f"\n✅ Resultados encontrados: {len(results)}")
        
        if results:
            print(f"\n📍 Primeros 3 restaurantes:")
            for i, place in enumerate(results[:3], 1):
                print(f"\n   {i}. {place.get('name')}")
                print(f"      Dirección: {place.get('formatted_address')}")
                print(f"      Rating: {place.get('rating', 'N/A')}")
                print(f"      Tipos: {', '.join(place.get('types', [])[:3])}")
        else:
            print("\n⚠️  OK pero sin resultados (raro)")
    
    else:
        print(f"\n❌ Status desconocido: {data.get('status')}")
    
    # Mostrar respuesta completa si hay error
    if data.get('status') != 'OK':
        print(f"\n📄 Respuesta completa:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "="*60)

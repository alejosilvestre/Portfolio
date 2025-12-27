"""
Test para verificar que Geocoding API funciona correctamente
"""
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

print("="*60)
print("🗺️  TEST DE GEOCODING API")
print("="*60)

# Test con "Madrid, Spain"
location = "Madrid, Spain"
print(f"\n📍 Geocodificando: '{location}'")

geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"
params = {
    "address": location,
    "key": GOOGLE_MAPS_API_KEY
}

try:
    r = requests.get(geocoding_url, params=params, timeout=10)
    print(f"\n📡 Respuesta HTTP: {r.status_code}")
    
    data = r.json()
    
    print(f"\n📊 Status: {data.get('status')}")
    
    if data.get('status') == 'OK':
        results = data.get('results', [])
        print(f"✅ Resultados encontrados: {len(results)}")
        
        if results:
            first = results[0]
            formatted_address = first.get('formatted_address')
            location_data = first.get('geometry', {}).get('location')
            
            print(f"\n📍 Primer resultado:")
            print(f"   Dirección: {formatted_address}")
            print(f"   Lat: {location_data.get('lat')}")
            print(f"   Lng: {location_data.get('lng')}")
            print(f"   Formato: {location_data.get('lat')},{location_data.get('lng')}")
            
            print("\n✅ ¡GEOCODING API FUNCIONA CORRECTAMENTE!")
            print("   Puedes usar esta API en lugar de Places Autocomplete")
    
    elif data.get('status') == 'REQUEST_DENIED':
        print("\n❌ REQUEST_DENIED")
        print(f"   Error: {data.get('error_message')}")
        print("\n   🔧 SOLUCIÓN:")
        print("   - Ve a: https://console.cloud.google.com/apis/library")
        print("   - Busca 'Geocoding API'")
        print("   - Habilítala si no lo está")
    
    else:
        print(f"\n⚠️  Status: {data.get('status')}")
        print(f"   Respuesta completa:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "="*60)

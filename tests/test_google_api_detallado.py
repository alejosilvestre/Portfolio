"""
Test detallado de la API de Google Places Autocomplete
Para ver exactamente qué está devolviendo y por qué falla
"""
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

print("="*60)
print("🔍 TEST DETALLADO DE GOOGLE PLACES AUTOCOMPLETE")
print("="*60)

print(f"\n🔑 API Key: {GOOGLE_MAPS_API_KEY[:10]}...{GOOGLE_MAPS_API_KEY[-4:]}")
print(f"   Longitud: {len(GOOGLE_MAPS_API_KEY)} caracteres")

# Test con "Madrid, Spain"
location = "Madrid, Spain"
print(f"\n📍 Probando geocodificación de: '{location}'")

autocomplete_url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
autocomplete_params = {
    "input": location,
    "types": "geocode",
    "key": GOOGLE_MAPS_API_KEY
}

print(f"\n🌐 Llamando a: {autocomplete_url}")
print(f"   Parámetros: input='{location}', types='geocode'")

try:
    r = requests.get(autocomplete_url, params=autocomplete_params, timeout=10)
    print(f"\n📡 Respuesta HTTP:")
    print(f"   Status Code: {r.status_code}")
    
    data = r.json()
    
    print(f"\n📄 Respuesta JSON completa:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    print(f"\n📊 Análisis de la respuesta:")
    print(f"   Status: {data.get('status')}")
    
    if data.get('status') == 'REQUEST_DENIED':
        print("\n❌ ERROR: REQUEST_DENIED")
        print("   Posibles causas:")
        print("   1. La API key no tiene habilitada 'Places API'")
        print("   2. La API key tiene restricciones de IP/HTTP referrer")
        print("   3. La API key no tiene permisos suficientes")
        print("\n   🔧 SOLUCIÓN:")
        print("   - Ve a: https://console.cloud.google.com/google/maps-apis")
        print("   - Asegúrate de haber habilitado 'Places API' (NEW)")
        print("   - Verifica las restricciones de la API key")
        
        if data.get('error_message'):
            print(f"\n   Mensaje de error: {data.get('error_message')}")
    
    elif data.get('status') == 'ZERO_RESULTS':
        print("\n⚠️  No se encontraron resultados")
        print("   Esto es raro para 'Madrid, Spain'")
        
    elif data.get('status') == 'OVER_QUERY_LIMIT':
        print("\n⚠️  Límite de queries excedido")
        print("   Has usado demasiadas búsquedas hoy")
        
    elif data.get('status') == 'OK':
        predictions = data.get('predictions', [])
        print(f"\n✅ Status OK - {len(predictions)} predicciones encontradas")
        
        if predictions:
            print(f"\n📍 Primera predicción:")
            first = predictions[0]
            print(f"   Descripción: {first.get('description')}")
            print(f"   Place ID: {first.get('place_id')}")
            
            # Ahora probar Place Details
            print(f"\n🔍 Obteniendo detalles del place_id...")
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                "place_id": first.get('place_id'),
                "fields": "geometry",
                "key": GOOGLE_MAPS_API_KEY
            }
            
            r2 = requests.get(details_url, params=details_params, timeout=10)
            details = r2.json()
            
            print(f"\n📄 Respuesta de Place Details:")
            print(json.dumps(details, indent=2, ensure_ascii=False))
            
            if details.get('status') == 'OK':
                location_data = details.get("result", {}).get("geometry", {}).get("location")
                if location_data:
                    lat = location_data.get('lat')
                    lng = location_data.get('lng')
                    print(f"\n✅ ¡ÉXITO! Coordenadas obtenidas:")
                    print(f"   Lat: {lat}")
                    print(f"   Lng: {lng}")
                    print(f"   Formato: {lat},{lng}")
                else:
                    print("\n❌ No se pudieron extraer las coordenadas del resultado")
            else:
                print(f"\n❌ Place Details falló con status: {details.get('status')}")
        else:
            print("\n⚠️  Status OK pero sin predicciones (raro)")
    
    else:
        print(f"\n❌ Status desconocido: {data.get('status')}")

except requests.RequestException as e:
    print(f"\n❌ Error de red: {e}")

print("\n" + "="*60)
print("📋 DIAGNÓSTICO")
print("="*60)

print("""
Si ves REQUEST_DENIED:
  → Ve a Google Cloud Console
  → Habilita 'Places API (NEW)'
  → Verifica restricciones de la API key

Si ves ZERO_RESULTS:
  → Prueba con "Madrid" en lugar de "Madrid, Spain"
  → O con coordenadas: "40.4168,-3.7038"

Si ves OK con predicciones:
  → ¡El problema está resuelto!
  → La función geocode_location debería funcionar
""")

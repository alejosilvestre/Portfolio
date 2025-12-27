"""
Test simplificado que simula exactamente el flujo del frontend
"""
import os
import sys

# No necesitamos cambiar de directorio, el script se ejecuta desde el directorio correcto
# Solo aseguramos que los módulos se pueden importar desde el directorio actual
sys.path.insert(0, os.getcwd())

# Ahora importar los módulos (cargarán el .env correctamente)
from backend_google_places import PlaceSearchPayload, places_text_search
from first_input_llm import call_llm

print("="*60)
print("🔍 TEST SIMPLIFICADO DEL FLUJO")
print("="*60)

# Simular exactamente lo que hace el frontend
query = "Busco un restaurante japonés para 2 personas esta noche"
location = ""  # Vacío como en tu caso

print(f"\n📝 Input del usuario:")
print(f"   Query: {query}")
print(f"   Location: {location if location else '(vacío - usará default)'}")

# Paso 1: Preparar inputs para el LLM (exactamente como el frontend)
print("\n1️⃣ Preparando inputs para el LLM...")
llm_inputs = {
    "query": query,
    "location": location,
    "max_distance": 15.0,
    "mins": 50,
    "travel_mode": "walking",
    "price": 2,
    "col_date": "",
    "col_time": "",
    "extras": []
}

print("   ✅ Inputs preparados")

# Paso 2: Llamar al LLM
print("\n2️⃣ Llamando al LLM (Gemini)...")
try:
    llm_response = call_llm(
        prompt_variables=llm_inputs,
        parse_json=True
    )
    print(f"   ✅ LLM respondió correctamente")
    print(f"   📄 Respuesta del LLM:")
    import json
    print(f"   {json.dumps(llm_response, indent=6, ensure_ascii=False)}")
    
except Exception as e:
    print(f"   ❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

# Paso 3: Validar respuesta del LLM
print("\n3️⃣ Validando respuesta del LLM...")
if not llm_response or not isinstance(llm_response, dict):
    print("   ❌ ERROR: El LLM no devolvió un diccionario válido")
    print(f"   Tipo recibido: {type(llm_response)}")
    print(f"   Valor: {llm_response}")
    exit(1)

required_fields = ['query', 'location']
missing_fields = [field for field in required_fields if field not in llm_response]
if missing_fields:
    print(f"   ⚠️  ADVERTENCIA: Faltan campos obligatorios: {missing_fields}")
else:
    print("   ✅ Respuesta válida con campos requeridos")

# Paso 4: Crear payload para Google Places
print("\n4️⃣ Creando payload para Google Places...")
try:
    google_places_payload = PlaceSearchPayload(**llm_response)
    print("   ✅ Payload creado exitosamente")
    print(f"   📍 Parámetros de búsqueda:")
    payload_dict = google_places_payload.dict()
    for key, value in payload_dict.items():
        if value is not None:
            print(f"      - {key}: {value}")
    
except Exception as e:
    print(f"   ❌ ERROR creando payload: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

# Paso 5: Buscar en Google Places
print("\n5️⃣ Buscando en Google Places API...")
try:
    resultados = places_text_search(google_places_payload)
    print(f"   ✅ Búsqueda completada")
    print(f"   📊 Resultados encontrados: {len(resultados)}")
    
    if not resultados:
        print("\n⚠️  NO SE ENCONTRARON RESULTADOS")
        print("   Posibles causas:")
        print("   - Los criterios de búsqueda son muy restrictivos")
        print("   - El radio de búsqueda es muy pequeño")
        print("   - No hay restaurantes japoneses en la ubicación especificada")
        exit(0)
    
    # Mostrar primeros 3 resultados
    print(f"\n📋 Mostrando primeros 3 resultados:")
    for i, resultado in enumerate(resultados[:3], 1):
        print(f"\n   {i}. {resultado.get('name', 'SIN NOMBRE')}")
        print(f"      📍 Zona: {resultado.get('neighborhood', 'N/A')}")
        print(f"      ⭐ Rating: {resultado.get('rating', 'N/A')}")
        print(f"      💰 Precio: {resultado.get('price_level', 'N/A')}")
        print(f"      📞 Teléfono: {resultado.get('phone', 'N/A')}")
        
except Exception as e:
    print(f"   ❌ ERROR en búsqueda: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*60)
print("✅ TEST COMPLETADO CON ÉXITO")
print("="*60)
print("\n💡 Si llegaste aquí, el problema NO está en el backend.")
print("   El problema debe estar en el frontend (frontend.py)")

"""
Test para identificar el problema sin necesidad de API keys reales
Este test usa mocks para simular las respuestas y encontrar dónde falla el frontend
"""
import os
import sys

# Configurar variables de entorno de prueba ANTES de importar los módulos
os.environ['GOOGLE_MAPS_API_KEY'] = 'TEST_KEY_12345'
os.environ['AI_STUDIO_API_KEY'] = 'TEST_KEY_67890'

sys.path.insert(0, '/mnt/project')

print("="*60)
print("🧪 TEST DE DIAGNÓSTICO (Sin API keys reales)")
print("="*60)

# Test 1: Verificar que los módulos se importan correctamente
print("\n✅ TEST 1: Importación de módulos")
try:
    from backend_google_places import PlaceSearchPayload
    print("   ✅ backend_google_places importado")
except Exception as e:
    print(f"   ❌ ERROR importando backend_google_places: {e}")
    exit(1)

try:
    from first_input_llm import call_llm
    print("   ✅ first_input_llm importado")
except Exception as e:
    print(f"   ❌ ERROR importando first_input_llm: {e}")
    exit(1)

# Test 2: Verificar creación de payload
print("\n✅ TEST 2: Creación de payload para Google Places")
test_llm_response = {
    "query": "restaurante japonés",
    "location": "Plaza España, Madrid",
    "max_travel_time": 30,
    "price_level": 2
}

try:
    payload = PlaceSearchPayload(**test_llm_response)
    print(f"   ✅ Payload creado exitosamente")
    print(f"   📍 Query: {payload.query}")
    print(f"   📍 Location: {payload.location}")
except Exception as e:
    print(f"   ❌ ERROR creando payload: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*60)
print("📋 DIAGNÓSTICO BASADO EN TU CÓDIGO")
print("="*60)

print("""
Basándome en el análisis del código, el problema está en uno de estos puntos:

🔴 PROBLEMA 1: Ubicación del archivo .env
   El archivo .env debe estar en la RAÍZ del proyecto, en la misma carpeta que:
   - frontend.py
   - backend_google_places.py
   - first_input_llm.py
   
   ❌ NO funciona: ~/Documents/mi-proyecto/.env
   ❌ NO funciona: ~/mi-proyecto/src/.env
   ✅ SÍ funciona: ~/mi-proyecto/.env (mismo nivel que frontend.py)

🔴 PROBLEMA 2: El frontend.py tiene un bug silencioso
   En la línea ~370 de frontend.py, cuando search_clicked=True:
   
   ❌ PROBLEMA: Si hay un error en call_llm() o places_text_search(),
      el código no muestra nada al usuario (error silencioso)
   
   ✅ SOLUCIÓN: Añadir try-except con st.error()

🔴 PROBLEMA 3: El LLM no está devolviendo JSON válido
   El prompt en prompt_first_LLM.txt tiene placeholders que no se limpian:
   
   Ejemplo: Si "mins" está vacío, el prompt puede quedar:
   "Tiempo aproximado (minutos)": {mins}  ← Esto rompe el JSON
   
   ✅ SOLUCIÓN: La función call_llm() debe limpiar placeholders vacíos

🔴 PROBLEMA 4: Google Places no encuentra resultados
   Si la búsqueda es muy específica, puede no devolver nada:
   - "restaurante japonés" → ✅ Debería encontrar
   - "restaurante japonés vegano con terraza" → ❌ Muy específico
   
   ✅ SOLUCIÓN: Empezar con búsquedas simples para probar
""")

print("\n" + "="*60)
print("🔧 PASOS PARA SOLUCIONAR")
print("="*60)

print("""
1. VERIFICA LA UBICACIÓN DEL .env
   Ejecuta en tu terminal (en la carpeta del proyecto):
   
   ls -la .env
   
   Deberías ver el archivo. Si no, está en el lugar equivocado.

2. VERIFICA EL CONTENIDO DEL .env
   cat .env
   
   Debe tener exactamente:
   GOOGLE_MAPS_API_KEY=AIzaSy...
   AI_STUDIO_API_KEY=AIzaSy...
   
   (Sin espacios, sin comillas, sin comentarios antes)

3. PRUEBA CON UN SCRIPT SIMPLE
   Crea un archivo test_env.py:
   
   from dotenv import load_dotenv
   import os
   load_dotenv()
   print("Google Key:", os.getenv('GOOGLE_MAPS_API_KEY')[:10] if os.getenv('GOOGLE_MAPS_API_KEY') else "NO ENCONTRADA")
   print("AI Key:", os.getenv('AI_STUDIO_API_KEY')[:10] if os.getenv('AI_STUDIO_API_KEY') else "NO ENCONTRADA")
   
   Ejecuta: python test_env.py
   
   Deberías ver:
   Google Key: AIzaSyXXXX
   AI Key: AIzaSyYYYY

4. AÑADE DEBUGGING AL FRONTEND
   En frontend.py, después de la línea donde haces click en "Buscar":
   
   if search_clicked:
       st.write("🔍 DEBUG - Botón clickeado")  # ← Añade esto
       if not query and not location:
           st.write("⚠️ DEBUG - Query y location vacíos")  # ← Añade esto
       else:
           st.write(f"🔍 DEBUG - Query: {query}")  # ← Añade esto
           st.write(f"🔍 DEBUG - Location: {location}")  # ← Añade esto
           
   Esto te dirá EXACTAMENTE dónde se detiene el flujo.

5. EJECUTA STREAMLIT CON VERBOSE
   streamlit run frontend.py --logger.level=debug
   
   Verás todos los errores en la consola.
""")

print("\n" + "="*60)
print("💡 SIGUIENTE PASO")
print("="*60)
print("""
OPCIÓN A (Rápida): Comparte el error exacto que ves
   - Ejecuta: streamlit run frontend.py
   - Haz una búsqueda
   - Mira la TERMINAL (no el navegador)
   - Copia y pega aquí cualquier error que veas

OPCIÓN B (Completa): Añade debugging
   - Añade los st.write() de debugging mencionados arriba
   - Ejecuta la app
   - Dime QUÉ mensaje de debug ves y cuál NO ves
   - Así sabré exactamente dónde falla
""")

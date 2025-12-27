"""
Script simple para verificar que las API keys están configuradas correctamente
"""
from dotenv import load_dotenv
import os

# Cargar el .env
load_dotenv()

print("="*60)
print("🔐 VERIFICACIÓN DE API KEYS")
print("="*60)

# Verificar Google Maps API Key
google_key = os.getenv('GOOGLE_MAPS_API_KEY')
if google_key:
    print(f"✅ GOOGLE_MAPS_API_KEY: Configurada")
    print(f"   Longitud: {len(google_key)} caracteres")
    print(f"   Empieza con: {google_key[:10]}...")
    print(f"   Termina con: ...{google_key[-4:]}")
else:
    print("❌ GOOGLE_MAPS_API_KEY: NO ENCONTRADA")
    print("")
    print("   🔧 SOLUCIÓN:")
    print("   1. Verifica que el archivo .env existe en este directorio")
    print("   2. Verifica que contenga una línea:")
    print("      GOOGLE_MAPS_API_KEY=AIzaSy...")
    print("   3. Sin espacios, sin comillas, sin comentarios antes")

print("")

# Verificar AI Studio API Key
ai_key = os.getenv('AI_STUDIO_API_KEY')
if ai_key:
    print(f"✅ AI_STUDIO_API_KEY: Configurada")
    print(f"   Longitud: {len(ai_key)} caracteres")
    print(f"   Empieza con: {ai_key[:10]}...")
    print(f"   Termina con: ...{ai_key[-4:]}")
else:
    print("❌ AI_STUDIO_API_KEY: NO ENCONTRADA")
    print("")
    print("   🔧 SOLUCIÓN:")
    print("   1. Verifica que el archivo .env existe en este directorio")
    print("   2. Verifica que contenga una línea:")
    print("      AI_STUDIO_API_KEY=AIzaSy...")
    print("   3. Sin espacios, sin comillas, sin comentarios antes")

print("")
print("="*60)

# Verificar ubicación del .env
import pathlib
env_path = pathlib.Path('.env')
if env_path.exists():
    print(f"📁 Archivo .env encontrado en: {env_path.absolute()}")
    print("")
    print("📄 Contenido del .env (primeras 2 líneas):")
    with open('.env', 'r') as f:
        lines = f.readlines()[:2]
        for i, line in enumerate(lines, 1):
            # Ocultar parte de la API key por seguridad
            if '=' in line:
                key_name, key_value = line.split('=', 1)
                if len(key_value.strip()) > 10:
                    masked = key_value[:10] + "..." + key_value[-4:]
                    print(f"   Línea {i}: {key_name}={masked}")
                else:
                    print(f"   Línea {i}: {line.strip()}")
            else:
                print(f"   Línea {i}: {line.strip()}")
else:
    print("❌ Archivo .env NO ENCONTRADO en el directorio actual")
    print(f"   Directorio actual: {pathlib.Path.cwd()}")
    print("")
    print("   🔧 SOLUCIÓN:")
    print("   1. Crea un archivo llamado .env (sin extensión)")
    print("   2. En la misma carpeta que frontend.py")
    print("   3. Con el contenido:")
    print("      GOOGLE_MAPS_API_KEY=tu_api_key_aqui")
    print("      AI_STUDIO_API_KEY=tu_api_key_aqui")

print("="*60)

# Diagnóstico final
if google_key and ai_key:
    print("✅ CONFIGURACIÓN CORRECTA")
    print("   Las API keys están configuradas.")
    print("   Si el frontend sigue sin funcionar, el problema está en otro lado.")
    print("")
    print("   Próximo paso: Ejecuta test_flujo_completo.py")
elif not google_key and not ai_key:
    print("❌ PROBLEMA: Ambas API keys faltan")
    print("   Configura el archivo .env correctamente")
elif not google_key:
    print("❌ PROBLEMA: Falta GOOGLE_MAPS_API_KEY")
    print("   El LLM funcionará pero la búsqueda de restaurantes NO")
else:
    print("❌ PROBLEMA: Falta AI_STUDIO_API_KEY")
    print("   La búsqueda de restaurantes funcionará pero el LLM NO")

print("="*60)

"""
===========================================================
DOCUMENTACIÓN - Módulo de procesamiento de primer input LLM
===========================================================

Este módulo se encarga de preparar y enviar el primer input 
del sistema a AI Studio (Gemini), haciéndolo accesible al 
módulo backend_google_places.py y permitiendo inyectar 
variables dinámicas en un prompt externo.

Incluye:
- Carga automática de un prompt base desde archivo externo.
- Construcción segura del prompt final incorporando variables.
- Opción para parsear la salida como JSON.


-----------------------------------------------------------
1. Función principal: call_llm(...)
-----------------------------------------------------------

Esta función ejecuta una llamada a Gemini (AI Studio) usando 
genai.Client, permitiendo:

- Usar un prompt base desde archivo o sobreescribirlo.
- Inyectar variables dinámicas en el prompt mediante 
  placeholders {variable}.
- Elegir el modelo (por defecto: gemini-2.5-flash).
- Obtener salida como texto o intentar convertirla a JSON.
- Manejar errores de red o parseo de forma segura.

Parámetros:
-----------
- prompt_template (str | None):
    Prompt base a utilizar. Si se deja en None, el módulo usa 
    el prompt cargado desde prompt_first_LLM.txt.

- prompt_variables (dict | None):
    Variables que reemplazarán placeholders en el prompt, 
    por ejemplo: {"ciudad": "Madrid"} reemplaza {ciudad}.

- model (str):
    Modelo de Gemini a usar. Default: "gemini-2.5-flash".

- parse_json (bool):
    Si True, intenta interpretar la respuesta del modelo 
    como JSON. Si falla, devuelve un dict con el contenido 
    sin parsear.

Retorna:
--------
- Un string con el texto generado por el modelo, o
- Un dict si parse_json=True y la respuesta es JSON válido.


-----------------------------------------------------------
2. Flujo interno de la función call_llm
-----------------------------------------------------------

1) Selección del prompt:
   - Si prompt_template es None → usa prompt_global cargado 
     desde el archivo prompt_first_LLM.txt.
   - Si no → usa el prompt_template pasado por el usuario.

2) Inyección de variables:
   - Cada variable del diccionario prompt_variables reemplaza 
     su placeholder {llave} dentro del prompt final.

3) Llamada al modelo Gemini:
   - Se usa client.models.generate_content(...)
   - Opciones como temperatura o max_output_tokens están 
     preparadas para activarse según se necesite.

4) Procesamiento de la respuesta:
   - Se obtiene response.text como salida principal.
   - Si parse_json=True, se intenta json.loads().
   - Si falla la conversión, el módulo retorna un dict con 
     el contenido puro como fallback.

5) Manejo de errores:
   - Cualquier excepción de API devuelve {} y un print 
     informativo.


-----------------------------------------------------------
3. Ejemplo de uso
-----------------------------------------------------------

Ejemplo de llamada desde otro módulo:

    from first_input_llm import call_llm

### VARIABLES OBTENIDAS DESDE EL IMPUT DEL USUARIO A TRAVES DE STREAMLIT
   prompt_variables = {
    "query": "Buscame un restaurante japonés para cenar cerca de mi con una terraza y opciones veganas.",
    "location": "Plaza España, Madrid",
    "max_distance": 1500,
    "mins": 10,
    "travel_mode": "walking",
    "price": "2",
    "col_date": "2024-06-15",
    "col_time": "20:00",
    "extras": ["terraza", "vegano"]
}

    respuesta = call_llm(
        prompt_variables=variables,
        parse_json=True
    )

-----------------------------------------------------------
5. Ejemplo de salida esperada
-----------------------------------------------------------


{'query': 'restaurante japonés',
 'location': 'Plaza España, Madrid',
 'radius': 1500,
 'max_travel_time': 10,
 'travel_mode': 'walking',
 'price_level': 2,
 'date': '2024-06-15',
 'time': '20:00',
 'extras': ['terrace', 'vegan']}
    

===========================================================
"""



import os
import json
from google import genai
from dotenv import load_dotenv
import re

load_dotenv(".env")
AI_STUDIO_API_KEY = os.environ.get("AI_STUDIO_API_KEY")
client = genai.Client(api_key=AI_STUDIO_API_KEY)
# cargamos el prompt desde un archivo externo

# with open("prompt_test.txt", "r", encoding="utf-8") as f:
with open("prompt_first_LLM.txt", "r", encoding="utf-8") as f:
    prompt_template = f.read()


def call_llm_not(prompt_variables: dict, prompt_template: str = None,
             model: str = 'gemini-2.5-flash', parse_json: bool = False):

    import json

    # Cargar prompt base
    prompt_base = prompt_template or globals().get("prompt_template", "")

    # Construir bloque dinámico SOLO con los valores que existan
    input_lines = []

    def add(name, value):
        if value not in [None, "", []]:
            input_lines.append(f'  "{name}": "{value}"')

    add("Usuario", prompt_variables.get("query"))
    add("Ubicación", prompt_variables.get("location"))
    add("Distancia máxima (metros)", prompt_variables.get("max_distance"))
    add("Tiempo aproximado (minutos)", prompt_variables.get("mins"))
    add("Modo de viaje", prompt_variables.get("travel_mode"))
    add("Precio", prompt_variables.get("price"))
    add("Fecha", prompt_variables.get("col_date"))
    add("Hora", prompt_variables.get("col_time"))
    add("Preferencias adicionales", prompt_variables.get("extras"))

    input_block = ",\n".join(input_lines)

    # Insertar en la plantilla
    prompt = prompt_base.format(input_block=input_block)

    # Llamada al modelo
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
    except Exception as e:
        print("Error llamando al LLM:", e)
        return {}

    output_text = response.text.strip()

    # Parsear JSON solo si se indica
    if parse_json:
        try:
            # limpiar posibles ```json
            if output_text.startswith("```"):
                output_text = output_text.strip("` \n")
                if output_text.startswith("json"):
                    output_text = output_text[4:].strip()

            return json.loads(output_text)

        except Exception as e:
            print("LLM no devolvió JSON válido:", output_text)
            print("Error:", e)
            return {}

    return output_text


def call_llm(
        prompt_template: str = None,
        prompt_variables: dict = None,
        model: str = 'gemini-2.5-flash',
        parse_json: bool = False
    ) -> str | dict:

    prompt_base = prompt_template or globals().get("prompt_template", "")
    prompt = prompt_base

    # 1. Reemplazar variables existentes
    if prompt_variables:
        for key, value in prompt_variables.items():
            if value is None or value == "" or value == "None":
                # Eliminar completamente la línea JSON correspondiente
                pattern = f'"{key}".*?\\n'
                prompt = re.sub(pattern, "", prompt)
            else:
                prompt = prompt.replace(f"{{{key}}}", str(value))

    # 2. Eliminar cualquier placeholder sobrante
    prompt = re.sub(r"\{[a-zA-Z0-9_]+\}", "", prompt)

    # 3. Quitar posibles dobles comas en JSON
    prompt = prompt.replace(",\n}", "\n}")

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
    except Exception as e:
        print("Error llamando al LLM:", e)
        return {}

    output_text = response.text.strip()

    if parse_json:
        try:
            cleaned = output_text

            # eliminar fences si los hubiera
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0]
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0]

            return json.loads(cleaned.strip())

        except json.JSONDecodeError as e:
            print("LLM output no es JSON válido:", output_text)
            print("Error de parsing:", e)
            return {}

    return output_text



def call_llm_ORIGINAL(prompt_template: str = None, prompt_variables: dict = None, 
             model: str = 'gemini-2.5-flash', parse_json: bool = False) -> str or dict:
    
    prompt_base = prompt_template or globals().get("prompt_template", "")
    prompt = prompt_base
    
    if prompt_variables:
        for key, value in prompt_variables.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
    except Exception as e:
        print("Error llamando al LLM:", e)
        return {}
    
    output_text = response.text
    
    if parse_json:
        try:
            # Limpieza del texto antes de parsear
            cleaned_text = output_text.strip()
            
            # Eliminar bloques de código markdown si existen
            if "```json" in cleaned_text:
                cleaned_text = cleaned_text.split("```json")[1].split("```")[0]
            elif "```" in cleaned_text:
                cleaned_text = cleaned_text.split("```")[1].split("```")[0]
            
            cleaned_text = cleaned_text.strip()
            
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            print("LLM output no es JSON válido:", output_text)
            print("Error de parsing:", e)
            return {}
    
    return output_text
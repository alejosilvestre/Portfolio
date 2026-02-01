# Tool Descriptions

This document contains descriptions of all available tools for the agent.

## 1. web_search

**Purpose:** Busca información en internet.

**Use Cases:**
- Información actualizada
- Recetas
- Recomendaciones
- Noticias
- Opiniones
- Cualquier dato que no conozcas

**Arguments:**
- `query`: La consulta de búsqueda (required)

**Example Usage:**
```python
web_search(query="receta auténtica de carbonara italiana")
```

---

## 2. maps_search

**Purpose:** Busca lugares en Google Maps/Places.

**Arguments:**
- `query`: Qué buscar (ej: "pizzería", "farmacia", "hotel", "gimnasio") - required
- `location`: Dónde buscar (ej: "Navalcarnero", "Madrid centro") - required
- `radius`: Radio en metros (default: 2000) - optional
- `price_level`: Nivel de precio 1-4 (solo para restaurantes) - optional
- `extras`: Palabras clave adicionales (ej: "terraza", "24h") - optional
- `max_travel_time`: Tiempo máximo de viaje en minutos - optional
- `travel_mode`: "walking", "driving", "bicycling", "transit" - optional

**Example Usage:**
```python
maps_search(
    query="pizzería",
    location="Navalcarnero",
    radius=2000,
    price_level=2,
    extras="terraza romántico"
)
```

---

## 3. check_availability

**Purpose:** Verifica disponibilidad en los lugares encontrados.

**Important:** Usa `maps_search` primero.

**Arguments:**
- `date`: Fecha YYYY-MM-DD (ej: "2026-01-15") - required
- `time`: Hora HH:MM (ej: "21:00") - required
- `num_people`: Número de personas (default: 2) - optional

**Example Usage:**
```python
check_availability(
    date="2026-01-15",
    time="21:00",
    num_people=4
)
```

---

## 4. make_booking

**Purpose:** Hace una reserva en un lugar.

**Important:** Usa `check_availability` primero.

**Arguments:**
- `place_name`: Nombre del lugar - required
- `date`: Fecha YYYY-MM-DD - required
- `time`: Hora HH:MM - required
- `num_people`: Número de personas (default: 2) - optional

**Example Usage:**
```python
make_booking(
    place_name="Pizzería Tío Miguel",
    date="2026-01-15",
    time="21:00",
    num_people=4
)
```

---

## 5. phone_call

**Purpose:** Realiza una llamada telefónica para cumplir una misión.

Esta herramienta permite llamar por teléfono para realizar cualquier gestión: reservas, consultas, citas, preguntas, etc.

**Use When:**
- El lugar solo acepta teléfono (📞)
- El usuario pide explícitamente que llames
- Necesitas información que solo se puede obtener por teléfono

**Arguments:**
- `phone_number`: Número a llamar (formato +34XXXXXXXXX) - required
- `mission`: Qué debe conseguir la llamada. Sé específico - required
  - Ej: "Reservar mesa para 2 personas mañana a las 21:00"
  - Ej: "Preguntar si aceptan perros y horario de cierre"
  - Ej: "Agendar cita para revisión de frenos esta semana"
- `context`: Información adicional relevante para la llamada - optional
  - Ej: "Restaurante: La Trattoria. Usuario prefiere terraza."
- `persona_name`: Nombre a usar si lo preguntan (default: "Ana García") - optional
- `persona_phone`: Teléfono de contacto si lo piden (default: "649122018") - optional

**Returns:**
Resultado estructurado con: misión completada (sí/no), resultado, notas importantes y transcripción resumida.

**Example Usage:**
```python
phone_call(
    phone_number="+34911197692",
    mission="Reservar mesa para 3 personas mañana a las 21:00",
    context="Restaurante: TAN-GO pizza & grill",
    persona_name="María López"
)
```

**Warning:**
⚠️ ANTES DE LLAMAR, VERIFICA:
1. Tienes el teléfono REAL del lugar (de maps_search, no inventado)
2. El usuario te ha dado su NOMBRE para la reserva
3. Si te falta alguno, PREGUNTA primero con respond

---

## 6. Google Calendar Tools

### 6.1 search_events

**Purpose:** Busca eventos en el calendario.

**Arguments:**
- `calendars_info`: Info de calendarios (usa get_calendars_info primero) - required
- `min_datetime`: Fecha/hora inicio 'YYYY-MM-DD HH:MM:SS' - required
- `max_datetime`: Fecha/hora fin 'YYYY-MM-DD HH:MM:SS' - required

**Example Usage:**
```python
search_events(
    calendars_info="[resultado de get_calendars_info]",
    min_datetime="2026-01-11 00:00:00",
    max_datetime="2026-01-11 23:59:59"
)
```

### 6.2 get_calendars_info

**Purpose:** Obtiene info de calendarios antes de search_events.

**Arguments:** None required

### 6.3 create_calendar_event

**Purpose:** Crea un nuevo evento en el calendario.

**Arguments:**
- `summary`: Título del evento - required
- `start_datetime`: Fecha/hora inicio 'YYYY-MM-DD HH:MM:SS' - required
- `end_datetime`: Fecha/hora fin 'YYYY-MM-DD HH:MM:SS' - required
- `timezone`: Zona horaria (ej: "Europe/Madrid") - required

**Example Usage:**
```python
create_calendar_event(
    summary="Reserva Restaurante",
    start_datetime="2026-01-15 21:00:00",
    end_datetime="2026-01-15 23:00:00",
    timezone="Europe/Madrid"
)
```

### 6.4 update_calendar_event

**Purpose:** Modifica un evento existente.

**Arguments:**
- `event_id`: ID del evento (búscalo con search_events primero) - required
- `summary`: Nuevo título - optional
- `start_datetime`: Nueva fecha inicio - optional
- `end_datetime`: Nueva fecha fin - optional
- `timezone`: Nueva zona horaria - optional
- `location`: Nueva ubicación - optional
- `description`: Nueva descripción - optional

### 6.5 delete_calendar_event

**Purpose:** Elimina un evento del calendario.

**Arguments:**
- `event_id`: ID del evento a borrar - required

### 6.6 get_current_datetime

**Purpose:** Obtiene la fecha/hora actual en la zona horaria del calendario.

**Arguments:**
- `calendar_id`: ID del calendario (default: "primary") - optional

---

## 7. respond

**Purpose:** Responde al usuario (para chitchat, preguntas, o pedir información).

**Arguments:**
- `message`: Tu respuesta - required

**Example Usage:**
```python
respond(message="La capital de Francia es París.")
```

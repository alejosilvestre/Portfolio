# Call Result Analysis Prompt

Analiza esta conversación telefónica y extrae información estructurada.

## MISIÓN ORIGINAL:

{mission}

## TRANSCRIPCIÓN:

{transcript_text}

Responde SOLO con un JSON válido (sin markdown, sin explicación):

```json
{{
    "mission_completed": true/false,
    "outcome": "Descripción breve del resultado (ej: 'Reserva confirmada para las 22:00 a nombre de María García', 'No fue posible realizar la reserva por falta de disponibilidad', 'No hay menú vegetariano', 'No se admiten mascotas')",
    "notes": ["Lista de información importante mencionada", "Ej: 'Llegar 10 min antes'", "Ej: 'No aceptan pago con tarjeta'"]
}}
```

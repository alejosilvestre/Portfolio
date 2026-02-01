"""
===========================================================
MOCK RESPONSES - Respuestas mock para tests
===========================================================

Datos de ejemplo para usar en los tests.
"""

# Respuesta mock de Google Places API
MOCK_PLACES_RESPONSE = {
    "places": [
        {
            "id": "ChIJ123abc",
            "displayName": {"text": "Restaurante El Buen Sabor"},
            "formattedAddress": "Calle Principal 123, 28001 Madrid",
            "location": {"latitude": 40.4168, "longitude": -3.7038},
            "rating": 4.5,
            "userRatingCount": 250,
            "priceLevel": "PRICE_LEVEL_2",
            "types": ["restaurant", "food", "point_of_interest"],
            "nationalPhoneNumber": "912 345 678",
            "websiteUri": "https://elbuensabor.com",
            "regularOpeningHours": {
                "openNow": True,
                "weekdayDescriptions": [
                    "Monday: 12:00 PM - 11:00 PM",
                    "Tuesday: 12:00 PM - 11:00 PM",
                    "Wednesday: 12:00 PM - 11:00 PM",
                    "Thursday: 12:00 PM - 11:00 PM",
                    "Friday: 12:00 PM - 12:00 AM",
                    "Saturday: 12:00 PM - 12:00 AM",
                    "Sunday: 12:00 PM - 10:00 PM"
                ],
                "periods": []
            },
            "addressComponents": [
                {"types": ["neighborhood"], "longText": "Centro"},
                {"types": ["locality"], "longText": "Madrid"}
            ],
            "photos": [{"name": "places/ChIJ123abc/photos/photo123"}]
        },
        {
            "id": "ChIJ456def",
            "displayName": {"text": "La Trattoria Italiana"},
            "formattedAddress": "Gran Vía 45, 28013 Madrid",
            "location": {"latitude": 40.4200, "longitude": -3.7050},
            "rating": 4.7,
            "userRatingCount": 180,
            "priceLevel": "PRICE_LEVEL_3",
            "types": ["restaurant", "italian_restaurant", "food"],
            "nationalPhoneNumber": "915 678 901",
            "websiteUri": "https://latrattoria.es",
            "regularOpeningHours": {
                "openNow": True,
                "weekdayDescriptions": [
                    "Monday: Closed",
                    "Tuesday: 1:00 PM - 11:30 PM",
                    "Wednesday: 1:00 PM - 11:30 PM",
                    "Thursday: 1:00 PM - 11:30 PM",
                    "Friday: 1:00 PM - 12:00 AM",
                    "Saturday: 1:00 PM - 12:00 AM",
                    "Sunday: 1:00 PM - 10:00 PM"
                ]
            },
            "addressComponents": [
                {"types": ["neighborhood"], "longText": "Gran Vía"},
                {"types": ["locality"], "longText": "Madrid"}
            ],
            "photos": [{"name": "places/ChIJ456def/photos/photo456"}]
        }
    ]
}

# Respuesta mock de Geocoding API
MOCK_GEOCODE_RESPONSE = {
    "results": [
        {
            "geometry": {
                "location": {
                    "lat": 40.4168,
                    "lng": -3.7038
                }
            },
            "formatted_address": "Madrid, Spain"
        }
    ],
    "status": "OK"
}

# Respuesta mock de Distance Matrix API
MOCK_DISTANCE_MATRIX_RESPONSE = {
    "rows": [
        {
            "elements": [
                {
                    "status": "OK",
                    "distance": {"value": 1500, "text": "1.5 km"},
                    "duration": {"value": 600, "text": "10 mins"}
                },
                {
                    "status": "OK",
                    "distance": {"value": 2000, "text": "2.0 km"},
                    "duration": {"value": 900, "text": "15 mins"}
                }
            ]
        }
    ],
    "status": "OK"
}

# Respuesta mock de Tavily Search
MOCK_TAVILY_RESPONSE = {
    "answer": "Los mejores restaurantes italianos en Madrid incluyen La Trattoria, Il Piccolo, y Ristorante Roma.",
    "results": [
        {
            "title": "Top 10 Restaurantes Italianos en Madrid 2026",
            "content": "Una guía completa de los mejores restaurantes italianos en la capital española...",
            "url": "https://example.com/restaurantes-italianos-madrid"
        },
        {
            "title": "La Trattoria - Auténtica Cocina Italiana",
            "content": "Ubicado en el corazón de Madrid, La Trattoria ofrece pasta fresca y pizzas artesanales...",
            "url": "https://latrattoria.es"
        }
    ]
}

# Respuesta mock de OpenAI para el agente
MOCK_OPENAI_AGENT_RESPONSE = """THOUGHT: El usuario quiere encontrar un restaurante italiano en Madrid. Voy a buscar opciones usando maps_search.

ACTION: maps_search
ACTION_INPUT: {"query": "restaurante italiano", "location": "Madrid"}"""

MOCK_OPENAI_RESPOND_RESPONSE = """THOUGHT: Ya tengo información sobre restaurantes italianos en Madrid. Voy a responder al usuario con las opciones encontradas.

ACTION: respond
ACTION_INPUT: {"message": "He encontrado varios restaurantes italianos en Madrid. Te recomiendo La Trattoria Italiana en Gran Vía con una puntuación de 4.7 estrellas, y El Buen Sabor en Calle Principal con 4.5 estrellas. ¿Te gustaría que verifique la disponibilidad en alguno de ellos?"}"""

# Transcripción mock de llamada exitosa
MOCK_CALL_TRANSCRIPT_SUCCESS = [
    {
        "speaker": "self",
        "message": "Hola, buenas tardes. Llamo para hacer una reserva para mañana por la noche.",
        "timestamp": "2026-01-18T15:30:00"
    },
    {
        "speaker": "other",
        "message": "Buenas tardes, claro. ¿Para cuántas personas sería la reserva?",
        "timestamp": "2026-01-18T15:30:05"
    },
    {
        "speaker": "self",
        "message": "Para 2 personas, a las 21:00 si es posible.",
        "timestamp": "2026-01-18T15:30:10"
    },
    {
        "speaker": "other",
        "message": "Perfecto, tenemos mesa disponible a esa hora. ¿A nombre de quién hago la reserva?",
        "timestamp": "2026-01-18T15:30:15"
    },
    {
        "speaker": "self",
        "message": "A nombre de Ana García.",
        "timestamp": "2026-01-18T15:30:20"
    },
    {
        "speaker": "other",
        "message": "Muy bien, Ana García. Reserva confirmada para mañana a las 21:00 para 2 personas. ¿Necesita algo más?",
        "timestamp": "2026-01-18T15:30:25"
    },
    {
        "speaker": "self",
        "message": "No, eso es todo. Muchas gracias. Hasta mañana.",
        "timestamp": "2026-01-18T15:30:30"
    },
    {
        "speaker": "other",
        "message": "Gracias a usted. Le esperamos mañana. Hasta luego.",
        "timestamp": "2026-01-18T15:30:35"
    }
]

# Transcripción mock de llamada fallida
MOCK_CALL_TRANSCRIPT_FAILED = [
    {
        "speaker": "self",
        "message": "Hola, buenas tardes. Llamo para hacer una reserva para mañana.",
        "timestamp": "2026-01-18T15:30:00"
    },
    {
        "speaker": "other",
        "message": "Buenas tardes. Lo siento mucho, pero mañana estamos completos.",
        "timestamp": "2026-01-18T15:30:05"
    },
    {
        "speaker": "self",
        "message": "¿Y pasado mañana tendría disponibilidad?",
        "timestamp": "2026-01-18T15:30:10"
    },
    {
        "speaker": "other",
        "message": "Pasado mañana también estamos llenos. Tenemos disponibilidad a partir del viernes.",
        "timestamp": "2026-01-18T15:30:15"
    },
    {
        "speaker": "self",
        "message": "Entiendo. Llamaré otro día entonces. Gracias.",
        "timestamp": "2026-01-18T15:30:20"
    },
    {
        "speaker": "other",
        "message": "De nada. Hasta luego.",
        "timestamp": "2026-01-18T15:30:25"
    }
]

# Datos de ejemplo para el estado del agente
SAMPLE_AGENT_STATE_WITH_KNOWLEDGE = {
    "messages": [],
    "knowledge": {
        "places": [
            {
                "name": "La Trattoria",
                "address": "Calle Mayor 10, Madrid",
                "place_id": "place123",
                "rating": 4.5,
                "user_ratings_total": 200,
                "price_level": 2,
                "phone": "+34912345678",
                "website": "https://latrattoria.com",
                "available": True,
                "has_api": True,
                "available_times": ["21:00"],
                "opening_hours": {"open_now": True}
            }
        ],
        "booking": {
            "confirmed": True,
            "place_name": "La Trattoria",
            "date": "2026-01-20",
            "time": "21:00",
            "num_people": 2,
            "booking_id": "RES-20260120143025"
        }
    },
    "next_tool": None,
    "tool_args": None,
    "last_observation": None,
    "status": "thinking",
    "iterations": 3
}

# Request de ejemplo para la API
SAMPLE_API_REQUEST = {
    "session_id": "test-session-123",
    "user_id": "test-user-456",
    "messages": [
        {"role": "user", "content": "Busco un restaurante italiano en Madrid para cenar mañana"},
        {"role": "assistant", "content": "Voy a buscar restaurantes italianos en Madrid. ¿Para cuántas personas sería la reserva?"},
        {"role": "user", "content": "Para 2 personas a las 21:00"}
    ],
    "session_context": {}
}

# Respuesta de ejemplo de la API
SAMPLE_API_RESPONSE = {
    "status": "success",
    "message": "He encontrado varios restaurantes italianos en Madrid. La Trattoria tiene buenas reseñas y está disponible.",
    "session_id": "test-session-123",
    "restaurants": [
        {
            "name": "La Trattoria",
            "address": "Calle Mayor 10, Madrid",
            "rating": 4.5,
            "available": True
        }
    ]
}

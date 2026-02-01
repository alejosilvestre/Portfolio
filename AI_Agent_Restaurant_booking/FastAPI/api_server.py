"""
===========================================================
FastAPI Server - API para el Agente de Reservas
===========================================================

Conecta el frontend con el agente brain_agent.

Endpoints principales:
- POST /api/reservation-requests: Procesa conversación
- GET /health: Health check
"""

import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
import requests
import os

# Path setup
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv()

# Importar el agente
from agent.graph import run_agent


# ==================== MODELOS ====================

class Message(BaseModel):
    """Mensaje de la conversación"""
    role: str = Field(..., description="user o assistant")
    content: str = Field(..., description="Contenido del mensaje")


class AgentRequest(BaseModel):
    """Request con historial completo (stateless)"""
    session_id: Optional[str] = Field(None, description="ID de sesión")
    user_id: Optional[str] = Field("anonymous", description="ID del usuario")
    messages: List[Message] = Field(..., description="Historial completo")
    session_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contexto adicional (ignorado por ahora)"
    )


class AgentResponse(BaseModel):
    """Respuesta del agente"""
    status: str = Field(..., description="success, needs_input, error")
    message: str = Field(..., description="Respuesta del agente")
    session_id: Optional[str] = None
    restaurants: Optional[List[Dict]] = Field(None, description="Restaurantes encontrados")


# ==================== APP ====================

app = FastAPI(
    title="ReserveHub API",
    description="API para el Agente de Reservas con LangGraph",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== HELPERS ====================

def extract_restaurants_from_knowledge(knowledge: Dict) -> List[Dict]:
    """Extrae restaurantes del knowledge del agente."""
    places = knowledge.get("places", [])
    
    if not places:
        return []
    
    restaurants = []
    for p in places:
        restaurants.append({
            "name": p.get("name"),
            "address": p.get("address"),
            "neighborhood": p.get("neighborhood"),
            "rating": p.get("rating"),
            "user_ratings_total": p.get("user_ratings_total"),
            "price_level": p.get("price_level"),
            "phone": p.get("phone"),
            "website": p.get("website"),
            "place_id": p.get("place_id"),
            "has_api": p.get("has_api"),
            "available": p.get("available"),
            "available_times": p.get("available_times", []),
            "availability": p.get("availability", ""),
            "opening_hours": p.get("opening_hours", {}),
            "photo_name": p.get("photo_name")
        })
    
    return restaurants


def determine_status(response: str, knowledge: Dict) -> str:
    """Determina el status basado en la respuesta y knowledge."""
    response_lower = response.lower()
    
    # Si hay reserva confirmada
    if knowledge.get("booking") or "confirmada" in response_lower or "reserva" in response_lower and "código" in response_lower:
        return "completed"
    
    # Si hay restaurantes encontrados
    if knowledge.get("places"):
        return "success"
    
    # Si parece una pregunta (necesita más input)
    if "?" in response or any(word in response_lower for word in ["dónde", "cuándo", "cuántos", "qué tipo", "cuál"]):
        return "needs_input"
    
    return "success"


# ==================== ENDPOINTS ====================

@app.post("/api/reservation-requests", response_model=AgentResponse)
async def process_request(request: AgentRequest):
    """
    Endpoint principal para interactuar con el agente.
    
    Recibe historial completo y devuelve respuesta.
    """
    
    print("\n" + "=" * 60)
    print("📦 REQUEST RECIBIDO")
    print("=" * 60)
    print(f"👤 Usuario: {request.user_id}")
    print(f"📨 Mensajes: {len(request.messages)}")
    print("=" * 60 + "\n")
    
    try:
        # Convertir mensajes al formato del agente
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Ejecutar agente
        result = run_agent(messages)
        
        response_text = result.get("response", "")
        knowledge = result.get("knowledge", {})
        
        # Extraer restaurantes si los hay
        restaurants = extract_restaurants_from_knowledge(knowledge)
        
        # Determinar status
        status = determine_status(response_text, knowledge)
        
        # Generar session_id si no existe
        session_id = request.session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\n✓ Respuesta generada")
        print(f"   Status: {status}")
        print(f"   Restaurantes: {len(restaurants)}")
        
        return AgentResponse(
            status=status,
            message=response_text,
            session_id=session_id,
            restaurants=restaurants if restaurants else None
        )
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return AgentResponse(
            status="error",
            message=f"Error procesando la solicitud: {str(e)}",
            session_id=request.session_id
        )


@app.post("/api/agent/continue", response_model=AgentResponse)
async def continue_conversation(request: AgentRequest):
    """Alias de /api/reservation-requests"""
    return await process_request(request)


@app.get("/")
async def root():
    return {
        "service": "ReserveHub API",
        "version": "3.0.0",
        "status": "running",
        "agent": "brain_agent (LangGraph)",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/photo/{path:path}")
async def get_photo(path: str):
    """
    Endpoint proxy para obtener fotos de Google Places API.

    La nueva Places API requiere autenticación con header X-Goog-Api-Key,
    por lo que no se pueden cargar directamente desde el navegador.
    Este endpoint actúa como proxy seguro.

    Args:
        path: El photo_name completo, ej: "places/ChIJ.../photos/..."

    Returns:
        La imagen en formato JPEG
    """
    try:
        # Obtener API key del entorno
        google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not google_api_key:
            raise HTTPException(status_code=500, detail="API key no configurada")

        # Construir URL de la API de Google Places
        photo_url = f"https://places.googleapis.com/v1/{path}/media"
        params = {
            "maxWidthPx": 400,
            "maxHeightPx": 300,
            "key": google_api_key
        }

        # Hacer request a Google Places API
        response = requests.get(photo_url, params=params, timeout=10)

        if response.status_code == 200:
            # Devolver la imagen con el content-type correcto
            return Response(
                content=response.content,
                media_type=response.headers.get("Content-Type", "image/jpeg")
            )
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error obteniendo foto de Google: {response.text}"
            )

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Timeout obteniendo foto")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Error de red: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 60)
    print("🚀 ReserveHub API v3.0")
    print("=" * 60)
    print("\n📚 Docs: http://localhost:8000/docs")
    print("🤖 Agente: brain_agent (LangGraph)")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
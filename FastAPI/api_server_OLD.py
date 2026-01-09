"""
===========================================================
FastAPI Server - API para el Agente de Reservas
===========================================================

Versión modificada con soporte para:
- Historial completo de conversación (stateless)
- Compatible con LangSmith (observabilidad)
- Preparado para Mem0 (memoria a largo plazo)

Endpoints principales:
- POST /api/reservation-requests: Procesa conversación con historial
- POST /api/availability: Consulta disponibilidad
- POST /api/reservations: Crea reserva directa
"""

from __future__ import annotations
import sys
from pathlib import Path as FilePath

from fastapi import FastAPI, HTTPException, Header, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any, Dict
from datetime import datetime, date, time, timedelta
import uuid
import random

ROOT_DIR = FilePath(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from agent.agent_main import RestaurantBookingAgent


# ==================== MODELOS ====================

class Message(BaseModel):
    """Mensaje de la conversación"""
    role: str = Field(..., description="user o assistant", example="user")
    content: str = Field(..., description="Contenido del mensaje")


class AgentRequest(BaseModel):
    """
    Request para el agente con historial completo.
    
    Este es el modelo principal para el modo stateless.
    El frontend envía todo el historial en cada petición.
    """
    session_id: Optional[str] = Field(None, description="ID de sesión (opcional)")
    user_id: Optional[str] = Field("anonymous", description="ID del usuario")
    messages: List[Message] = Field(..., description="Historial completo de mensajes")
    session_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contexto adicional (ubicación, preferencias, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_123",
                "user_id": "user_456",
                "messages": [
                    {"role": "user", "content": "Busco una pizzería para 3 personas"},
                    {"role": "assistant", "content": "¿Para qué día y hora?"},
                    {"role": "user", "content": "Esta noche a las 21:00 en Navalcarnero"}
                ],
                "session_context": {
                    "location": "Navalcarnero",
                    "price_level": 2
                }
            }
        }


class AgentResponse(BaseModel):
    """Respuesta del agente"""
    status: str = Field(..., description="success, needs_input, error")
    message: str = Field(..., description="Respuesta del agente")
    question: Optional[str] = Field(None, description="Pregunta si necesita más info")
    session_id: Optional[str] = Field(None, description="ID de sesión")
    restaurants: Optional[List[Dict]] = Field(None, description="Restaurantes encontrados")
    booking_confirmation: Optional[Dict] = Field(None, description="Confirmación de reserva")


# Modelos para reservas directas (sin agente)
class Venue(BaseModel):
    id: str
    name: str
    slug: str
    timezone: str = "Europe/Madrid"
    currency: str = "EUR"


class Shift(BaseModel):
    id: str
    name: str
    start_time: time
    end_time: time
    venue_id: str


class ReservationRequest(BaseModel):
    venue_id: str
    reservation_date: date
    reservation_time: time
    party_size: int = Field(..., ge=1, le=20)
    name: str = Field(..., min_length=2, max_length=100)
    phone: str
    email: Optional[EmailStr] = None
    notes: Optional[str] = None
    shift_id: Optional[str] = None


class Reservation(BaseModel):
    id: str
    venue_id: str
    reservation_date: date
    reservation_time: time
    party_size: int
    status: str
    name: str
    phone: str
    email: Optional[EmailStr] = None
    notes: Optional[str] = None
    shift_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AvailabilityQuery(BaseModel):
    venue_id: str
    reservation_date: date
    party_size: int = Field(..., ge=1, le=20)
    shift_id: Optional[str] = None


class AvailableSlot(BaseModel):
    slot_time: time
    available: bool
    shift_id: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str


# ==================== BASE DE DATOS MOCK ====================

class SimpleDB:
    def __init__(self):
        self.venues: dict[str, Venue] = {}
        self.shifts: dict[str, Shift] = {}
        self.reservations: dict[str, Reservation] = {}
        self._init_data()
    
    def _init_data(self):
        venue = Venue(
            id="venue-1",
            name="Restaurante Demo",
            slug="restaurante-demo"
        )
        self.venues[venue.id] = venue
        
        shifts_data = [
            {"id": "shift-1", "name": "Comida", "start_time": time(13, 0), "end_time": time(16, 0), "venue_id": "venue-1"},
            {"id": "shift-2", "name": "Cena", "start_time": time(20, 0), "end_time": time(23, 0), "venue_id": "venue-1"}
        ]
        
        for shift_data in shifts_data:
            shift = Shift(**shift_data)
            self.shifts[shift.id] = shift


db = SimpleDB()


# ==================== AGENTE (SINGLETON) ====================

_agent_instance: Optional[RestaurantBookingAgent] = None


def get_agent() -> RestaurantBookingAgent:
    """Obtiene o crea la instancia del agente"""
    global _agent_instance
    if _agent_instance is None:
        print("🤖 Inicializando Agente de Reservas...")
        _agent_instance = RestaurantBookingAgent()
        print("✓ Agente listo\n")
    return _agent_instance


# ==================== AUTENTICACIÓN ====================

API_KEYS = {
    "demo-api-key": "venue-1",
    "dev-api-key-67890": "venue-1"
}


def verify_api_key(x_api_key: str = Header(..., alias="x-api-key")):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return API_KEYS[x_api_key]


# ==================== APP ====================

app = FastAPI(
    title="ReserveHub API",
    description="""
## API de ReserveHub para Gestión de Reservas con IA

Sistema multi-agente para gestión inteligente de reservas en restaurantes.

### Características:
* 🤖 Agente conversacional con LangGraph
* 📊 Observabilidad con LangSmith
* 🧠 Preparado para memoria a largo plazo (Mem0)
* 🔄 Modo stateless (historial completo en cada petición)

### Autenticación:
Header `x-api-key` con API key válida.

**API Key de prueba**: `demo-api-key`
    """,
    version="2.0.0"
)

# CORS para permitir peticiones desde Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== ENDPOINTS DEL AGENTE ====================

@app.post("/api/reservation-requests",
    response_model=AgentResponse,
    tags=["Agente de Reservas"],
    summary="Procesar conversación con el agente"
)
async def process_agent_request(request: AgentRequest):
    """
    Endpoint principal para interactuar con el agente.
    
    Recibe el historial completo de la conversación y devuelve
    la respuesta del agente.
    
    Este es un endpoint STATELESS: el frontend envía todo el
    historial en cada petición y el servidor no guarda estado.
    """
    
    print("\n" + "="*60)
    print("📦 REQUEST RECIBIDO")
    print("="*60)
    print(f"👤 Usuario: {request.user_id}")
    print(f"📨 Mensajes: {len(request.messages)}")
    print(f"📋 Contexto: {request.session_context}")
    print("="*60 + "\n")
    
    try:
        # Obtener instancia del agente
        agent = get_agent()
        
        # Convertir mensajes al formato esperado
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Procesar con el agente
        result = agent.process_with_history(
            messages=messages,
            session_context=request.session_context
        )
        
        print(f"\n✓ Agente respondió con status: {result['status']}")
        
        # Construir respuesta
        response = AgentResponse(
            status=result["status"],
            message=result["response"],
            question=result["response"] if result["status"] == "needs_input" else None,
            session_id=request.session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            restaurants=result.get("top_3_restaurants"),
            booking_confirmation=result.get("booking_confirmation")
        )
        
        return response
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return AgentResponse(
            status="error",
            message=f"Error procesando la solicitud: {str(e)}",
            session_id=request.session_id
        )


@app.post("/api/agent/continue",
    response_model=AgentResponse,
    tags=["Agente de Reservas"],
    summary="Continuar conversación (alias de reservation-requests)"
)
async def continue_conversation(request: AgentRequest):
    """
    Alias de /api/reservation-requests para compatibilidad.
    
    Ambos endpoints funcionan igual: reciben historial completo
    y devuelven la respuesta del agente.
    """
    return await process_agent_request(request)


# ==================== ENDPOINTS DE SISTEMA ====================

@app.get("/",
    tags=["Sistema"],
    summary="Información del servicio"
)
async def root():
    return {
        "service": "ReserveHub API",
        "version": "2.0.0",
        "status": "running",
        "documentation": "/docs",
        "features": [
            "Agente conversacional con LangGraph",
            "Modo stateless con historial",
            "Observabilidad con LangSmith"
        ]
    }


@app.get("/health",
    tags=["Sistema"],
    summary="Health check"
)
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ==================== ENDPOINTS DE VENUES ====================

@app.get("/api/venues",
    response_model=List[Venue],
    tags=["Restaurantes"]
)
async def list_venues(x_api_key: str = Header(..., alias="x-api-key")):
    verify_api_key(x_api_key)
    return list(db.venues.values())


@app.get("/api/venues/{venue_id}",
    response_model=Venue,
    tags=["Restaurantes"]
)
async def get_venue(
    venue_id: str = Path(...),
    x_api_key: str = Header(..., alias="x-api-key")
):
    verify_api_key(x_api_key)
    if venue_id not in db.venues:
        raise HTTPException(status_code=404, detail="Venue not found")
    return db.venues[venue_id]


# ==================== ENDPOINTS DE SHIFTS ====================

@app.get("/api/venues/{venue_id}/shifts",
    response_model=List[Shift],
    tags=["Turnos"]
)
async def list_shifts(
    venue_id: str = Path(...),
    x_api_key: str = Header(..., alias="x-api-key")
):
    verify_api_key(x_api_key)
    return [s for s in db.shifts.values() if s.venue_id == venue_id]


# ==================== ENDPOINTS DE DISPONIBILIDAD ====================

@app.post("/api/availability",
    response_model=List[AvailableSlot],
    tags=["Disponibilidad"]
)
async def check_availability(
    query: AvailabilityQuery,
    x_api_key: str = Header(..., alias="x-api-key"),
    max_slots: int = Query(default=3, ge=1, le=20)
):
    verify_api_key(x_api_key)
    
    available_slots = []
    venue_shifts = [s for s in db.shifts.values() if s.venue_id == query.venue_id]
    
    if query.shift_id:
        venue_shifts = [s for s in venue_shifts if s.id == query.shift_id]
    
    for shift in venue_shifts:
        current = datetime.combine(query.reservation_date, shift.start_time)
        end = datetime.combine(query.reservation_date, shift.end_time)
        
        while current < end:
            slot_time = current.time()
            
            has_reservation = any(
                r.reservation_date == query.reservation_date and 
                r.reservation_time == slot_time and
                r.status in ["confirmed", "seated"]
                for r in db.reservations.values()
            )
            
            available_slots.append(AvailableSlot(
                slot_time=slot_time,
                available=not has_reservation,
                shift_id=shift.id
            ))
            
            current = current + timedelta(minutes=30)
    
    truly_available = [slot for slot in available_slots if slot.available]
    random_slots = random.sample(truly_available, min(max_slots, len(truly_available)))
    random_slots.sort(key=lambda slot: slot.slot_time)
    
    return random_slots


# ==================== ENDPOINTS DE RESERVAS ====================

@app.post("/api/reservations",
    response_model=Reservation,
    tags=["Reservas"]
)
async def create_reservation(
    reservation: ReservationRequest,
    x_api_key: str = Header(..., alias="x-api-key")
):
    verify_api_key(x_api_key)
    
    if reservation.venue_id not in db.venues:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    new_reservation = Reservation(
        id=str(uuid.uuid4()),
        venue_id=reservation.venue_id,
        reservation_date=reservation.reservation_date,
        reservation_time=reservation.reservation_time,
        party_size=reservation.party_size,
        status="confirmed",
        name=reservation.name,
        phone=reservation.phone,
        email=reservation.email,
        notes=reservation.notes,
        shift_id=reservation.shift_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db.reservations[new_reservation.id] = new_reservation
    return new_reservation


@app.get("/api/reservations",
    response_model=List[Reservation],
    tags=["Reservas"]
)
async def list_reservations(
    x_api_key: str = Header(..., alias="x-api-key"),
    venue_id: Optional[str] = Query(default=None),
    reservation_date: Optional[date] = Query(default=None),
    status: Optional[str] = Query(default=None)
):
    verify_api_key(x_api_key)
    
    reservations = list(db.reservations.values())
    
    if venue_id:
        reservations = [r for r in reservations if r.venue_id == venue_id]
    if reservation_date:
        reservations = [r for r in reservations if r.reservation_date == reservation_date]
    if status:
        reservations = [r for r in reservations if r.status == status]
    
    return reservations


@app.get("/api/reservations/{reservation_id}",
    response_model=Reservation,
    tags=["Reservas"]
)
async def get_reservation(
    reservation_id: str = Path(...),
    x_api_key: str = Header(..., alias="x-api-key")
):
    verify_api_key(x_api_key)
    
    if reservation_id not in db.reservations:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return db.reservations[reservation_id]


@app.delete("/api/reservations/{reservation_id}",
    tags=["Reservas"]
)
async def cancel_reservation(
    reservation_id: str = Path(...),
    x_api_key: str = Header(..., alias="x-api-key")
):
    verify_api_key(x_api_key)
    
    if reservation_id not in db.reservations:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    reservation = db.reservations[reservation_id]
    reservation.status = "cancelled"
    reservation.updated_at = datetime.now()
    
    return {"message": "Reservation cancelled", "reservation_id": reservation_id}


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 ReserveHub API v2.0 - Stateless con Historial")
    print("="*60)
    print("\n📚 Documentación: http://localhost:8000/docs")
    print("🔑 API Key: demo-api-key")
    print("\n✨ Características:")
    print("   - Agente conversacional con LangGraph")
    print("   - Modo stateless (historial completo en cada petición)")
    print("   - Compatible con LangSmith para observabilidad")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
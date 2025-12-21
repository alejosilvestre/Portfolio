"""
CoverManager API Mock - OpenAPI 3.0.3 100% Compatible
Post-procesamiento del esquema para Swagger Editor
"""
from __future__ import annotations
from fastapi import FastAPI, HTTPException, Header, Query, Path
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any, Dict
from datetime import datetime, date, time, timedelta
import uuid

# ==================== MODELOS ====================

class Venue(BaseModel):
    """Restaurante/Local"""
    id: str = Field(..., description="ID único del restaurante", example="venue-1")
    name: str = Field(..., description="Nombre del restaurante", example="Restaurante Demo")
    slug: str = Field(..., description="Slug único para URLs", example="restaurante-demo")
    timezone: str = Field(default="Europe/Madrid", description="Zona horaria", example="Europe/Madrid")
    currency: str = Field(default="EUR", description="Moneda", example="EUR")

class Shift(BaseModel):
    """Turno del restaurante"""
    id: str = Field(..., description="ID único del turno", example="shift-1")
    name: str = Field(..., description="Nombre del turno", example="Comida")
    start_time: time = Field(..., description="Hora de inicio", example="13:00:00")
    end_time: time = Field(..., description="Hora de fin", example="16:00:00")
    venue_id: str = Field(..., description="ID del restaurante", example="venue-1")

class ReservationRequest(BaseModel):
    """Petición para crear reserva"""
    venue_id: str = Field(..., description="ID del restaurante", example="venue-1")
    reservation_date: date = Field(..., description="Fecha de la reserva", example="2024-12-15")
    reservation_time: time = Field(..., description="Hora de la reserva", example="20:00:00")
    party_size: int = Field(..., description="Número de personas", example=4, ge=1, le=20)
    name: str = Field(..., description="Nombre del cliente", example="Juan Pérez", min_length=2, max_length=100)
    phone: str = Field(..., description="Teléfono del cliente", example="+34666111222")
    email: Optional[EmailStr] = Field(default=None, description="Email del cliente", example="juan@example.com")
    notes: Optional[str] = Field(default=None, description="Notas adicionales", example="Alergia a frutos secos", max_length=500)
    shift_id: Optional[str] = Field(default=None, description="ID del turno (opcional)", example="shift-2")

class Reservation(BaseModel):
    """Reserva"""
    id: str = Field(..., description="ID único de la reserva", example="550e8400-e29b-41d4-a716-446655440000")
    venue_id: str = Field(..., description="ID del restaurante", example="venue-1")
    reservation_date: date = Field(..., description="Fecha de la reserva", example="2024-12-15")
    reservation_time: time = Field(..., description="Hora de la reserva", example="20:00:00")
    party_size: int = Field(..., description="Número de personas", example=4)
    status: str = Field(..., description="Estado de la reserva", example="confirmed")
    name: str = Field(..., description="Nombre del cliente", example="Juan Pérez")
    phone: str = Field(..., description="Teléfono del cliente", example="+34666111222")
    email: Optional[EmailStr] = Field(default=None, description="Email del cliente", example="juan@example.com")
    notes: Optional[str] = Field(default=None, description="Notas adicionales", example="Alergia a frutos secos", max_length=500)
    shift_id: Optional[str] = Field(default=None, description="ID del turno (opcional)", example="shift-2")
    created_at: datetime = Field(..., description="Fecha de creación", example="2024-12-15T10:30:00")
    updated_at: datetime = Field(..., description="Fecha de última actualización", example="2024-12-15T10:30:00")

class AvailabilityQuery(BaseModel):
    """Consulta de disponibilidad"""
    venue_id: str = Field(..., description="ID del restaurante", example="venue-1")
    reservation_date: date = Field(..., description="Fecha a consultar", example="2024-12-15")
    party_size: int = Field(..., description="Número de personas", example=4, ge=1, le=20)
    shift_id: Optional[str] = Field(default=None, description="ID del turno (opcional)", example="shift-2")

class AvailableSlot(BaseModel):
    """Franja horaria disponible"""
    slot_time: time = Field(..., description="Hora del slot", example="20:00:00")
    available: bool = Field(..., description="Si está disponible", example=True)
    shift_id: Optional[str] = Field(default=None, description="ID del turno (opcional)", example="shift-2")

class ErrorResponse(BaseModel):
    """Respuesta de error estándar"""
    detail: str = Field(..., description="Descripción del error", example="Venue not found")

# ==================== BASE DE DATOS ====================

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
            slug="restaurante-demo",
            timezone="Europe/Madrid",
            currency="EUR"
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

# ==================== AUTENTICACIÓN ====================

API_KEYS = {
    "demo-api-key": "venue-1",
    "dev-api-key-67890": "venue-1"
}

def verify_api_key(x_api_key: str = Header(..., alias="x-api-key", description="API Key de autenticación")):
    """Verifica que la API key sea válida"""
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return API_KEYS[x_api_key]

# ==================== APP ====================

app = FastAPI(
    title="CoverManager API Mock",
    description="""
    ## API de CovManager para TFM
    
    Esta API proporciona funcionalidad básica de gestión de reservas para restaurantes.
    
    ### Características:
    * 🏪 Gestión de restaurantes (venues)
    * ⏰ Gestión de turnos (shifts)
    * 📅 Consulta de disponibilidad
    * 📝 CRUD completo de reservas
    
    ### Autenticación:
    Todas las peticiones requieren un header `x-api-key` con una API key válida.
    
    **API Key de prueba**: `demo-api-key`
    
    ### Estados de Reserva:
    * `confirmed` - Reserva confirmada
    * `seated` - Cliente sentado en la mesa
    * `cancelled` - Reserva cancelada
    * `no_show` - Cliente no se presentó
    """,
    version="2.0.0",
    contact={
        "name": "Soporte API",
        "email": "ebis@ebis.com"
    },
    license_info={
        "name": "MIT License",
    }
)

# ==================== POST-PROCESAMIENTO OPENAPI ====================

def convert_anyof_to_nullable(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte anyOf con type null a nullable para OpenAPI 3.0
    """
    if isinstance(schema, dict):
        # Si tiene anyOf con null, convertir a nullable
        if "anyOf" in schema:
            any_of = schema["anyOf"]
            # Buscar si hay un type null
            non_null_schemas = [s for s in any_of if s.get("type") != "null"]
            has_null = len(non_null_schemas) < len(any_of)
            
            if has_null and len(non_null_schemas) == 1:
                # Reemplazar anyOf con el schema no-null + nullable
                result = non_null_schemas[0].copy()
                result["nullable"] = True
                # Copiar otras propiedades
                for key in schema:
                    if key not in ["anyOf"]:
                        result[key] = schema[key]
                return convert_anyof_to_nullable(result)
        
        # Recursión en todos los valores
        return {k: convert_anyof_to_nullable(v) for k, v in schema.items()}
    elif isinstance(schema, list):
        return [convert_anyof_to_nullable(item) for item in schema]
    else:
        return schema

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        contact=app.contact,
        license_info=app.license_info,
    )
    
    # Forzar versión 3.0.3
    openapi_schema["openapi"] = "3.0.3"
    
    # Convertir anyOf a nullable
    openapi_schema = convert_anyof_to_nullable(openapi_schema)
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ==================== ENDPOINTS ====================

@app.get("/", 
    tags=["Sistema"],
    summary="Información del servicio"
)
async def root():
    """Endpoint raíz con información del servicio"""
    return {
        "service": "CoverManager API Mock",
        "version": "2.0.0",
        "status": "running",
        "documentation": "/docs"
    }

@app.get("/health", 
    tags=["Sistema"],
    summary="Health check"
)
async def health():
    """Verifica que el servicio esté funcionando"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# ==================== VENUES ====================

@app.get("/api/venues", 
    response_model=List[Venue],
    tags=["Restaurantes"],
    summary="Listar restaurantes",
    responses={
        200: {"description": "Lista de restaurantes"},
        401: {"model": ErrorResponse, "description": "API Key inválida"}
    }
)
async def list_venues(x_api_key: str = Header(..., alias="x-api-key")):
    """Listar todos los restaurantes disponibles"""
    verify_api_key(x_api_key)
    return list(db.venues.values())

@app.get("/api/venues/{venue_id}", 
    response_model=Venue,
    tags=["Restaurantes"],
    summary="Obtener restaurante",
    responses={
        200: {"description": "Detalles del restaurante"},
        401: {"model": ErrorResponse, "description": "API Key inválida"},
        404: {"model": ErrorResponse, "description": "Restaurante no encontrado"}
    }
)
async def get_venue(
    venue_id: str = Path(..., description="ID del restaurante"),
    x_api_key: str = Header(..., alias="x-api-key")
):
    """Obtener detalles de un restaurante específico"""
    verify_api_key(x_api_key)
    
    if venue_id not in db.venues:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    return db.venues[venue_id]

# ==================== SHIFTS ====================

@app.get("/api/venues/{venue_id}/shifts", 
    response_model=List[Shift],
    tags=["Turnos"],
    summary="Listar turnos",
    responses={
        200: {"description": "Lista de turnos"},
        401: {"model": ErrorResponse, "description": "API Key inválida"}
    }
)
async def list_shifts(
    venue_id: str = Path(..., description="ID del restaurante"),
    x_api_key: str = Header(..., alias="x-api-key")
):
    """Listar todos los turnos de un restaurante"""
    verify_api_key(x_api_key)
    
    shifts = [s for s in db.shifts.values() if s.venue_id == venue_id]
    return shifts

# ==================== DISPONIBILIDAD ====================

@app.post("/api/availability", 
    response_model=List[AvailableSlot],
    tags=["Disponibilidad"],
    summary="Consultar disponibilidad",
    responses={
        200: {"description": "Lista de franjas horarias con disponibilidad"},
        401: {"model": ErrorResponse, "description": "API Key inválida"}
    }
)
async def check_availability(
    query: AvailabilityQuery,
    x_api_key: str = Header(..., alias="x-api-key")
):
    """Consultar disponibilidad de un restaurante"""
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
    
    return available_slots

# ==================== RESERVAS ====================

@app.post("/api/reservations", 
    response_model=Reservation,
    tags=["Reservas"],
    summary="Crear reserva",
    responses={
        200: {"description": "Reserva creada exitosamente"},
        400: {"model": ErrorResponse, "description": "Datos inválidos"},
        401: {"model": ErrorResponse, "description": "API Key inválida"},
        404: {"model": ErrorResponse, "description": "Restaurante no encontrado"}
    }
)
async def create_reservation(
    reservation: ReservationRequest,
    x_api_key: str = Header(..., alias="x-api-key")
):
    """Crear una nueva reserva"""
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
    tags=["Reservas"],
    summary="Listar reservas",
    responses={
        200: {"description": "Lista de reservas"},
        401: {"model": ErrorResponse, "description": "API Key inválida"}
    }
)
async def list_reservations(
    x_api_key: str = Header(..., alias="x-api-key"),
    venue_id: Optional[str] = Query(default=None, description="Filtrar por restaurante"),
    reservation_date: Optional[date] = Query(default=None, description="Filtrar por fecha"),
    status: Optional[str] = Query(default=None, description="Filtrar por estado")
):
    """Listar reservas con filtros opcionales"""
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
    tags=["Reservas"],
    summary="Obtener reserva",
    responses={
        200: {"description": "Detalles de la reserva"},
        401: {"model": ErrorResponse, "description": "API Key inválida"},
        404: {"model": ErrorResponse, "description": "Reserva no encontrada"}
    }
)
async def get_reservation(
    reservation_id: str = Path(..., description="ID de la reserva"),
    x_api_key: str = Header(..., alias="x-api-key")
):
    """Obtener los detalles completos de una reserva"""
    verify_api_key(x_api_key)
    
    if reservation_id not in db.reservations:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return db.reservations[reservation_id]

@app.put("/api/reservations/{reservation_id}", 
    response_model=Reservation,
    tags=["Reservas"],
    summary="Actualizar estado de reserva",
    responses={
        200: {"description": "Reserva actualizada"},
        400: {"model": ErrorResponse, "description": "Estado inválido"},
        401: {"model": ErrorResponse, "description": "API Key inválida"},
        404: {"model": ErrorResponse, "description": "Reserva no encontrada"}
    }
)
async def update_reservation(
    reservation_id: str = Path(..., description="ID de la reserva"),
    status: str = Query(..., description="Nuevo estado (confirmed, seated, cancelled, no_show)"),
    x_api_key: str = Header(..., alias="x-api-key")
):
    """Actualizar el estado de una reserva"""
    verify_api_key(x_api_key)
    
    if reservation_id not in db.reservations:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    valid_statuses = ["confirmed", "cancelled", "seated", "no_show"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    reservation = db.reservations[reservation_id]
    reservation.status = status
    reservation.updated_at = datetime.now()
    
    return reservation

@app.delete("/api/reservations/{reservation_id}",
    tags=["Reservas"],
    summary="Cancelar reserva",
    responses={
        200: {"description": "Reserva cancelada"},
        401: {"model": ErrorResponse, "description": "API Key inválida"},
        404: {"model": ErrorResponse, "description": "Reserva no encontrada"}
    }
)
async def cancel_reservation(
    reservation_id: str = Path(..., description="ID de la reserva"),
    x_api_key: str = Header(..., alias="x-api-key")
):
    """Cancelar una reserva"""
    verify_api_key(x_api_key)
    
    if reservation_id not in db.reservations:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    reservation = db.reservations[reservation_id]
    reservation.status = "cancelled"
    reservation.updated_at = datetime.now()
    
    return {
        "message": "Reservation cancelled successfully",
        "reservation_id": reservation_id,
        "status": "cancelled"
    }

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 CoverManager API Mock v2.0 - OpenAPI 3.0.3")
    print("="*60)
    print("\n📚 Documentación: http://localhost:8000/docs")
    print("🔗 OpenAPI JSON:  http://localhost:8000/openapi.json")
    print("\n🔑 API Key: demo-api-key")
    print("\n✅ OpenAPI 3.0.3 100% Compatible con Swagger Editor")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
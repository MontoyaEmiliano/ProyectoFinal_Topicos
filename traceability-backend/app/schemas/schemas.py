from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.models import UserRole, PartStatus, StationType, TraceResult

##------------------------------------------------------------------------------------------
#User (usuario)

class UserBase(BaseModel):
    nombre: str
    email: EmailStr
    rol: UserRole
    activo: bool = True

class UserCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str  # contraseña en texto plano solo para crear
    rol: UserRole = UserRole.OPERADOR

class UserRead(UserBase):
    id: int
    fecha_registro: datetime

    class Config:
        orm_mode = True

#------------------------------------------------------------------------------------------
#Station (estacion)

class StationBase(BaseModel):
    nombre: str
    tipo: StationType
    linea: str

class StationCreate(StationBase):
    pass

class StationRead(StationBase):
    id: int

    class Config:
        orm_mode = True

class StationUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[StationType] = None
    linea: Optional[str] = None

#------------------------------------------------------------------------------------------
#Part (pieza)

class PartBase(BaseModel):
    tipo_pieza: str
    lote: str
    status: PartStatus = PartStatus.IN_PROCESS

class PartCreate(PartBase):
    id: str  # serial de la pieza que envía el cliente

class PartRead(PartBase):
    id: str
    fecha_creacion: datetime
    num_retrabajos: int
    tiempo_total_segundos: float
    ultima_estacion_id: Optional[int] = None

    class Config:
        orm_mode = True

class PartUpdate(BaseModel):
    tipo_pieza: Optional[str] = None
    lote: Optional[str] = None
    status: Optional[PartStatus] = None

#------------------------------------------------------------------------------------------
#TraceEvent (evento de trazabilidad)

class TraceEventBase(BaseModel):
    part_id: str
    station_id: int
    timestamp_entrada: datetime
    timestamp_salida: datetime
    resultado: TraceResult
    operador_id: Optional[int] = None
    observaciones: Optional[str] = None

class TraceEventCreate(TraceEventBase):
    pass

class TraceEventRead(TraceEventBase):
    id: int

    class Config:
        orm_mode = True

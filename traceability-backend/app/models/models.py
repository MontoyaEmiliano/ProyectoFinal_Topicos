from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Float,
    Text,
)
from sqlalchemy.orm import relationship
from app.core.database import Base  #Se importa la base declarativa de database.py


#Aqui abajito estan los enum que se usan en los modelos

class UserRole(str, Enum):
    OPERADOR = "OPERADOR"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"


class PartStatus(str, Enum):
    CREATED = "CREATED"
    IN_PROCESS = "IN_PROCESS"
    COMPLETED = "COMPLETED"
    SCRAPPED = "SCRAPPED"

class StationType(str, Enum):
    INSPECCION = "INSPECCION"
    ENSAMBLE = "ENSAMBLE"
    PRUEBA = "PRUEBA"


class TraceResult(str, Enum):
    OK = "OK"
    SCRAP = "SCRAP"
    RETRABAJO = "RETRABAJO"

#------------------------------------------------------------------------------------------
#Clase User (usuario)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(SAEnum(UserRole), nullable=False, default=UserRole.OPERADOR)
    activo = Column(Boolean, nullable=False, default=True)
    fecha_registro = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # un usuario puede registrar muchos eventos
    trace_events = relationship("TraceEvent", back_populates="operador")

#------------------------------------------------------------------------------------------
#Clase Station (estacion)

class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True, index=True)
    tipo = Column(SAEnum(StationType), nullable=False)
    linea = Column(String(100), nullable=False)

    trace_events = relationship("TraceEvent", back_populates="station")
    parts_ultima = relationship("Part", back_populates="ultima_estacion")

#------------------------------------------------------------------------------------------
#Clase Part (pieza)

class Part(Base):
    __tablename__ = "parts"

    # id de la pieza = serial
    id = Column(String(50), primary_key=True, index=True)
    tipo_pieza = Column(String(50), nullable=False, index=True)
    lote = Column(String(50), nullable=False, index=True)
    status = Column(
        SAEnum(PartStatus),
        nullable=False,
        default=PartStatus.IN_PROCESS,
        index=True,
    )
    fecha_creacion = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # campos básicos para analítica
    num_retrabajos = Column(Integer, nullable=False, default=0)
    tiempo_total_segundos = Column(Float, nullable=False, default=0.0)

    ultima_estacion_id = Column(
        Integer,
        ForeignKey("stations.id"),
        nullable=True,
    )

    trace_events = relationship("TraceEvent", back_populates="part")
    ultima_estacion = relationship("Station", back_populates="parts_ultima")

#------------------------------------------------------------------------------------------
#Clase TraceEvent (evento de trazabilidad)

class TraceEvent(Base):
    __tablename__ = "trace_events"

    id = Column(Integer, primary_key=True, index=True)

    part_id = Column(
        String(50),
        ForeignKey("parts.id"),
        nullable=False,
        index=True,
    )

    station_id = Column(
        Integer,
        ForeignKey("stations.id"),
        nullable=False,
        index=True,
    )

    timestamp_entrada = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    timestamp_salida = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    resultado = Column(
        SAEnum(TraceResult),
        nullable=False,
        index=True,
    )

    operador_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    observaciones = Column(Text, nullable=True)

    part = relationship("Part", back_populates="trace_events")
    station = relationship("Station", back_populates="trace_events")
    operador = relationship("User", back_populates="trace_events")

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.models import (
    Part,
    Station,
    TraceEvent,
    TraceResult,
    PartStatus,
    User,
)
from app.schemas.schemas import TraceEventCreate

def get_trace_event(db: Session, event_id: int) -> Optional[TraceEvent]:
    return db.query(TraceEvent).filter(TraceEvent.id == event_id).first()

def list_trace_events(
    db: Session,
    station_id: Optional[int] = None,
    resultado: Optional[TraceResult] = None,
    from_ts: Optional[datetime] = None,
    to_ts: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[TraceEvent]:
    query = db.query(TraceEvent)

    if station_id is not None:
        query = query.filter(TraceEvent.station_id == station_id)

    if resultado is not None:
        query = query.filter(TraceEvent.resultado == resultado)

    if from_ts is not None:
        query = query.filter(TraceEvent.timestamp_entrada >= from_ts)

    if to_ts is not None:
        query = query.filter(TraceEvent.timestamp_salida <= to_ts)

    return (
        query.order_by(TraceEvent.timestamp_entrada.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_trace_event(
    db: Session,
    data: TraceEventCreate,
    current_user: Optional[User],
) -> TraceEvent:

    part = db.query(Part).filter(Part.id == data.part_id).first()
    if not part:
        raise ValueError("PART_NOT_FOUND")

    station = db.query(Station).filter(Station.id == data.station_id).first()
    if not station:
        raise ValueError("STATION_NOT_FOUND")

    if data.timestamp_salida <= data.timestamp_entrada:
        raise ValueError("INVALID_TIMESTAMPS")

    event = TraceEvent(
        part_id=data.part_id,
        station_id=data.station_id,
        timestamp_entrada=data.timestamp_entrada,
        timestamp_salida=data.timestamp_salida,
        resultado=data.resultado,
        operador_id=current_user.id if current_user else data.operador_id,
        observaciones=data.observaciones,
    )
    db.add(event)

    part.ultima_estacion_id = data.station_id

    if data.resultado == TraceResult.SCRAP:
        part.status = PartStatus.SCRAPPED
    elif data.resultado == TraceResult.RETRABAJO:
        part.status = PartStatus.IN_PROCESS
        part.num_retrabajos = (part.num_retrabajos or 0) + 1
    elif data.resultado == TraceResult.OK:
        part.status = PartStatus.COMPLETED

    delta = data.timestamp_salida - data.timestamp_entrada
    part.tiempo_total_segundos = (part.tiempo_total_segundos or 0.0) + delta.total_seconds()

    db.commit()
    db.refresh(event)
    db.refresh(part)

    return event

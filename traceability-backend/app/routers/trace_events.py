from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User, UserRole, TraceResult
from app.schemas.schemas import TraceEventCreate, TraceEventRead
from app.services.auth_service import require_role
from app.services.trace_event_service import (
    get_trace_event,
    list_trace_events,
    create_trace_event,
)

router = APIRouter(prefix="/trace-events", tags=["TraceEvents"])

@router.post("/", response_model=TraceEventRead, status_code=status.HTTP_201_CREATED)
def create_trace_event_endpoint(
    data: TraceEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.OPERADOR, UserRole.SUPERVISOR, UserRole.ADMIN)
    ),
):
    try:
        event = create_trace_event(db, data, current_user)
    except ValueError as e:
        code = str(e)
        if code == "PART_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pieza no encontrada",
            )
        if code == "STATION_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estación no encontrada",
            )
        if code == "INVALID_TIMESTAMPS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="timestamp_salida debe ser mayor que timestamp_entrada",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear evento de trazabilidad",
        )

    return TraceEventRead(
        id=event.id,
        part_id=event.part_id,
        station_id=event.station_id,
        timestamp_entrada=event.timestamp_entrada,
        timestamp_salida=event.timestamp_salida,
        resultado=event.resultado,
        operador_id=event.operador_id,
        observaciones=event.observaciones,
    )


@router.get("/", response_model=List[TraceEventRead])
def list_trace_events_endpoint(
    station_id: Optional[int] = Query(default=None),
    resultado: Optional[TraceResult] = Query(default=None),
    from_ts: Optional[datetime] = Query(default=None),
    to_ts: Optional[datetime] = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SUPERVISOR, UserRole.ADMIN)
    ),
):

    events = list_trace_events(
        db=db,
        station_id=station_id,
        resultado=resultado,
        from_ts=from_ts,
        to_ts=to_ts,
        skip=skip,
        limit=limit,
    )

    return [
        TraceEventRead(
            id=e.id,
            part_id=e.part_id,
            station_id=e.station_id,
            timestamp_entrada=e.timestamp_entrada,
            timestamp_salida=e.timestamp_salida,
            resultado=e.resultado,
            operador_id=e.operador_id,
            observaciones=e.observaciones,
        )
        for e in events
    ]


@router.get("/{event_id}", response_model=TraceEventRead)
def get_trace_event_endpoint(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SUPERVISOR, UserRole.ADMIN)
    ),
):

    event = get_trace_event(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento de trazabilidad no encontrado",
        )

    return TraceEventRead(
        id=event.id,
        part_id=event.part_id,
        station_id=event.station_id,
        timestamp_entrada=event.timestamp_entrada,
        timestamp_salida=event.timestamp_salida,
        resultado=event.resultado,
        operador_id=event.operador_id,
        observaciones=event.observaciones,
    )


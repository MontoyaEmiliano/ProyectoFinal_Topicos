from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User, UserRole, PartStatus
from app.schemas.schemas import (
    PartCreate,
    PartRead,
    PartUpdate,
    TraceEventRead,
)
from app.services.auth_service import require_role
from app.services.part_service import (
    get_part,
    list_parts,
    create_part,
    update_part,
    get_part_history,
)

router = APIRouter(prefix="/parts")

@router.post("/", response_model=PartRead, status_code=status.HTTP_201_CREATED)
def create_part_endpoint(
    data: PartCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SUPERVISOR, UserRole.ADMIN)
    ),
):
    existing = get_part(db, data.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una pieza con ese id (serial)",
        )

    part = create_part(db, data)
    return PartRead(
        id=part.id,
        tipo_pieza=part.tipo_pieza,
        lote=part.lote,
        status=part.status,
        fecha_creacion=part.fecha_creacion,
        num_retrabajos=part.num_retrabajos,
        tiempo_total_segundos=part.tiempo_total_segundos,
        ultima_estacion_id=part.ultima_estacion_id,
    )

@router.get("/", response_model=List[PartRead])
def list_parts_endpoint(
    status_filter: Optional[PartStatus] = Query(default=None, alias="status"),
    tipo_pieza: Optional[str] = Query(default=None),
    lote: Optional[str] = Query(default=None),
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SUPERVISOR, UserRole.ADMIN)
    ),
):
    parts = list_parts(
        db=db,
        status_filter=status_filter,
        tipo_pieza=tipo_pieza,
        lote=lote,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )

    return [
        PartRead(
            id=p.id,
            tipo_pieza=p.tipo_pieza,
            lote=p.lote,
            status=p.status,
            fecha_creacion=p.fecha_creacion,
            num_retrabajos=p.num_retrabajos,
            tiempo_total_segundos=p.tiempo_total_segundos,
            ultima_estacion_id=p.ultima_estacion_id,
        )
        for p in parts
    ]

@router.get("/{part_id}", response_model=PartRead)
def get_part_endpoint(
    part_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SUPERVISOR, UserRole.ADMIN)
    ),
):
    part = get_part(db, part_id)
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pieza no encontrada",
        )

    return PartRead(
        id=part.id,
        tipo_pieza=part.tipo_pieza,
        lote=part.lote,
        status=part.status,
        fecha_creacion=part.fecha_creacion,
        num_retrabajos=part.num_retrabajos,
        tiempo_total_segundos=part.tiempo_total_segundos,
        ultima_estacion_id=part.ultima_estacion_id,
    )

@router.get("/{part_id}/history", response_model=List[TraceEventRead])
def get_part_history_endpoint(
    part_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SUPERVISOR, UserRole.ADMIN)
    ),
):

    part = get_part(db, part_id)
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pieza no encontrada",
        )

    events = get_part_history(db, part_id)

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


@router.patch("/{part_id}", response_model=PartRead)
def update_part_endpoint(
    part_id: str,
    data: PartUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SUPERVISOR, UserRole.ADMIN)
    ),
):
    part = get_part(db, part_id)
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pieza no encontrada",
        )

    updated = update_part(db, part, data)
    return PartRead(
        id=updated.id,
        tipo_pieza=updated.tipo_pieza,
        lote=updated.lote,
        status=updated.status,
        fecha_creacion=updated.fecha_creacion,
        num_retrabajos=updated.num_retrabajos,
        tiempo_total_segundos=updated.tiempo_total_segundos,
        ultima_estacion_id=updated.ultima_estacion_id,
    )

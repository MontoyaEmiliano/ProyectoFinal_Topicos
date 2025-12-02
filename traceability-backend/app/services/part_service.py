from datetime import date, datetime, time
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Part, PartStatus, TraceEvent
from app.schemas.schemas import PartCreate, PartUpdate

def get_part(db: Session, part_id: str) -> Optional[Part]:
    return db.query(Part).filter(Part.id == part_id).first()

def list_parts(
    db: Session,
    status_filter: Optional[PartStatus] = None,
    tipo_pieza: Optional[str] = None,
    lote: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Part]:
    query = db.query(Part)

    if status_filter is not None:
        query = query.filter(Part.status == status_filter)

    if tipo_pieza:
        query = query.filter(Part.tipo_pieza == tipo_pieza)

    if lote:
        query = query.filter(Part.lote == lote)

    if from_date:
        start_dt = datetime.combine(from_date, time.min)
        query = query.filter(Part.fecha_creacion >= start_dt)

    if to_date:
        end_dt = datetime.combine(to_date, time.max)
        query = query.filter(Part.fecha_creacion <= end_dt)

    return query.offset(skip).limit(limit).all()

def create_part(db: Session, data: PartCreate) -> Part:
    part = Part(
        id=data.id,
        tipo_pieza=data.tipo_pieza,
        lote=data.lote,
        status=data.status,
    )
    db.add(part)
    db.commit()
    db.refresh(part)
    return part

def update_part(db: Session, part: Part, data: PartUpdate) -> Part:
    if data.tipo_pieza is not None:
        part.tipo_pieza = data.tipo_pieza
    if data.lote is not None:
        part.lote = data.lote
    if data.status is not None:
        part.status = data.status
    db.commit()
    db.refresh(part)
    return part

def get_part_history(db: Session, part_id: str) -> List[TraceEvent]:
    return (
        db.query(TraceEvent)
        .filter(TraceEvent.part_id == part_id)
        .order_by(TraceEvent.timestamp_entrada.asc())
        .all()
    )

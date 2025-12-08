from datetime import date, datetime, time
from typing import List, Optional, Dict, Any
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from app.models.models import Part, PartStatus, TraceEvent, TraceResult, Station

def _date_range_to_datetimes(from_date: Optional[date], to_date: Optional[date]):
    start_dt = None
    end_dt = None
    if from_date:
        start_dt = datetime.combine(from_date, time.min)
    if to_date:
        end_dt = datetime.combine(to_date, time.max)
    return start_dt, end_dt

def get_parts_by_status(
    db: Session,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    tipo_pieza: Optional[str] = None,
) -> Dict[str, Any]:
    query = db.query(Part)

    start_dt, end_dt = _date_range_to_datetimes(from_date, to_date)
    if start_dt:
        query = query.filter(Part.fecha_creacion >= start_dt)
    if end_dt:
        query = query.filter(Part.fecha_creacion <= end_dt)

    if tipo_pieza:
        query = query.filter(Part.tipo_pieza == tipo_pieza)
    agg = (
        db.query(Part.status, func.count(Part.id))
        .select_from(query.subquery())  
        .group_by(Part.status)
        .all()
    )

    counts = [
        {"status": status.value if isinstance(status, PartStatus) else str(status), "count": count}
        for status, count in agg
    ]

    return {
        "from_date": from_date.isoformat() if from_date else None,
        "to_date": to_date.isoformat() if to_date else None,
        "tipo_pieza": tipo_pieza,
        "counts": counts,
    }

def get_throughput(
    db: Session,
    from_date: date,
    to_date: date,
    tipo_pieza: Optional[str] = None,
) -> Dict[str, Any]:
    start_dt, end_dt = _date_range_to_datetimes(from_date, to_date)

    query = db.query(Part).filter(
        Part.fecha_creacion >= start_dt,
        Part.fecha_creacion <= end_dt,
    )

    if tipo_pieza:
        query = query.filter(Part.tipo_pieza == tipo_pieza)
    agg = (
        db.query(
            func.date(Part.fecha_creacion).label("day"),
            func.count(Part.id).label("count"),
        )
        .select_from(query.subquery())
        .group_by("day")
        .order_by("day")
        .all()
    )

    throughput_per_day = [
        {"date": day.isoformat(), "count": count} for day, count in agg
    ]

    return {
        "from": from_date.isoformat(),
        "to": to_date.isoformat(),
        "tipo_pieza": tipo_pieza,
        "throughput_per_day": throughput_per_day,
    }

def get_station_cycle_time(
    db: Session,
    from_ts: Optional[datetime],
    to_ts: Optional[datetime],
    tipo_pieza: Optional[str],
):
    avg_cycle = func.avg(
        (func.julianday(TraceEvent.timestamp_salida) - func.julianday(TraceEvent.timestamp_entrada)) * 86400.0
    ).label("avg_cycle_time_seconds")

    query = (
        db.query(
            Station.id.label("station_id"),
            Station.nombre.label("station_name"),
            avg_cycle,
        )
        .join(TraceEvent, TraceEvent.station_id == Station.id)
        .join(Part, Part.id == TraceEvent.part_id)
    )

    if from_ts is not None:
        query = query.filter(TraceEvent.timestamp_entrada >= from_ts)

    if to_ts is not None:
        query = query.filter(TraceEvent.timestamp_salida <= to_ts)

    if tipo_pieza is not None:
        query = query.filter(Part.tipo_pieza == tipo_pieza)

    query = query.group_by(Station.id, Station.nombre)

    rows = query.all()

    return [
        {
            "station_id": r.station_id,
            "station_name": r.station_name,
            "avg_cycle_time_seconds": r.avg_cycle_time_seconds or 0.0,
        }
        for r in rows
    ]

def get_overview(db: Session) -> Dict[str, Any]:
    today = datetime.utcnow().date()
    start_today = datetime.combine(today, time.min)
    end_today = datetime.combine(today, time.max)

    total_parts = db.query(func.count(Part.id)).scalar() or 0
    in_process = (
        db.query(func.count(Part.id))
        .filter(Part.status == PartStatus.IN_PROCESS)
        .scalar()
        or 0
    )
    completed = (
        db.query(func.count(Part.id))
        .filter(Part.status == PartStatus.COMPLETED)
        .scalar()
        or 0
    )
    completed_today = (
        db.query(func.count(Part.id))
        .filter(
            Part.fecha_creacion >= start_today,
            Part.fecha_creacion <= end_today,
            Part.status == PartStatus.COMPLETED,
        )
        .scalar()
        or 0
    )
    scrap_today = (
        db.query(func.count(TraceEvent.id))
        .filter(
            TraceEvent.resultado == TraceResult.SCRAP,
            TraceEvent.timestamp_entrada >= start_today,
            TraceEvent.timestamp_entrada <= end_today,
        )
        .scalar()
        or 0
    )

    return {
        "date": today.isoformat(),
        "total_parts": total_parts,
        "in_process": in_process,
        "completed": completed,
        "completed_today": completed_today,
        "scrap_today": scrap_today,
    }

def get_scrap_rate(
    db: Session,
    from_ts: Optional[datetime],
    to_ts: Optional[datetime],
    station_id: Optional[int],
    tipo_pieza: Optional[str],
):
    total = func.count(TraceEvent.id).label("total")
    scrap = func.sum(
        case(
            (TraceEvent.resultado == TraceResult.SCRAP, 1),
            else_=0,
        )
    ).label("scrap_count")

    query = (
        db.query(
            Part.tipo_pieza.label("tipo_pieza"),
            Station.id.label("station_id"),
            Station.nombre.label("station_name"),
            total,
            scrap,
        )
        .join(TraceEvent, TraceEvent.part_id == Part.id)
        .join(Station, TraceEvent.station_id == Station.id)
    )

    if from_ts is not None:
        query = query.filter(TraceEvent.timestamp_entrada >= from_ts)

    if to_ts is not None:
        query = query.filter(TraceEvent.timestamp_salida <= to_ts)

    if station_id is not None:
        query = query.filter(Station.id == station_id)

    if tipo_pieza is not None:
        query = query.filter(Part.tipo_pieza == tipo_pieza)

    query = query.group_by(Part.tipo_pieza, Station.id, Station.nombre)

    rows = query.all()

    resultado = []
    for r in rows:
        total_val = r.total or 0
        scrap_val = r.scrap_count or 0
        rate = float(scrap_val) / total_val if total_val else 0.0

        resultado.append(
            {
                "tipo_pieza": r.tipo_pieza,
                "station_id": r.station_id,
                "station_name": r.station_name,
                "total": total_val,
                "scrap": scrap_val,
                "scrap_rate": rate,
            }
        )

    return resultado

def get_station_load(
    db: Session,
    from_ts: Optional[datetime],
    to_ts: Optional[datetime],
):
    query = (
        db.query(
            Station.id.label("station_id"),
            Station.nombre.label("station_name"),
            func.count(TraceEvent.id).label("events_count"),
        )
        .join(TraceEvent, TraceEvent.station_id == Station.id)
    )

    if from_ts is not None:
        query = query.filter(TraceEvent.timestamp_entrada >= from_ts)

    if to_ts is not None:
        query = query.filter(TraceEvent.timestamp_salida <= to_ts)

    query = query.group_by(Station.id, Station.nombre)

    rows = query.all()

    return [
        {
            "station_id": r.station_id,
            "station_name": r.station_name,
            "events_count": r.events_count or 0,
        }
        for r in rows
    ]

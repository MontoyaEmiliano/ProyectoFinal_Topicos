from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User, UserRole
from app.services.auth_service import require_role
from app.services.metrics_service import (
    get_parts_by_status,
    get_throughput,
    get_station_cycle_time,
    get_scrap_rate,
    get_overview,
    get_station_load,
)
router = APIRouter(prefix="/metrics", tags=["Metrics"])
MetricsUserDep = Depends(require_role(UserRole.SUPERVISOR, UserRole.ADMIN))


@router.get("/parts-by-status")
def parts_by_status(
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    tipo_pieza: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = MetricsUserDep,
):
    return get_parts_by_status(db, from_date, to_date, tipo_pieza)


@router.get("/throughput")
def throughput(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    tipo_pieza: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = MetricsUserDep,
):
    return get_throughput(db, from_date, to_date, tipo_pieza)


@router.get("/station-cycle-time")
def station_cycle_time(
    from_ts: Optional[datetime] = Query(default=None),
    to_ts: Optional[datetime] = Query(default=None),
    tipo_pieza: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = MetricsUserDep,
):
    return get_station_cycle_time(db, from_ts, to_ts, tipo_pieza)


@router.get("/scrap-rate")
def scrap_rate(
    from_ts: Optional[datetime] = Query(default=None),
    to_ts: Optional[datetime] = Query(default=None),
    station_id: Optional[int] = Query(default=None),
    tipo_pieza: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = MetricsUserDep,
):
    return get_scrap_rate(db, from_ts, to_ts, station_id, tipo_pieza)


@router.get("/overview")
def metrics_overview(
    db: Session = Depends(get_db),
    current_user: User = MetricsUserDep,
):
    return get_overview(db)


@router.get("/station-load")
def station_load(
    from_ts: Optional[datetime] = Query(default=None),
    to_ts: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = MetricsUserDep,
):
    return get_station_load(db, from_ts, to_ts)

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User, UserRole
from app.schemas.schemas import StationCreate, StationRead, StationUpdate
from app.services.auth_service import require_role
from app.services.station_service import (
    get_station,
    list_stations,
    create_station,
    update_station,
    delete_station,
)

router = APIRouter(prefix="/stations", tags=["Stations"])

@router.get("/", response_model=List[StationRead])
def get_stations(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SUPERVISOR, UserRole.ADMIN)
    ),
):
    stations = list_stations(db)
    return [
        StationRead(
            id=s.id,
            nombre=s.nombre,
            tipo=s.tipo,
            linea=s.linea,
        )
        for s in stations
    ]

@router.get("/{station_id}", response_model=StationRead)
def get_station_by_id(
    station_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SUPERVISOR, UserRole.ADMIN)
    ),
):
    station = get_station(db, station_id)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estación no encontrada",
        )

    return StationRead(
        id=station.id,
        nombre=station.nombre,
        tipo=station.tipo,
        linea=station.linea,
    )


@router.post("/", response_model=StationRead, status_code=status.HTTP_201_CREATED)
def create_station_endpoint(
    data: StationCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
):
    from app.models.models import Station
    existing = db.query(Station).filter(Station.nombre == data.nombre).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una estación con ese nombre",
        )

    station = create_station(db, data)

    return StationRead(
        id=station.id,
        nombre=station.nombre,
        tipo=station.tipo,
        linea=station.linea,
    )


@router.put("/{station_id}", response_model=StationRead)
def update_station_endpoint(
    station_id: int,
    data: StationUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
):
    station = get_station(db, station_id)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estación no encontrada",
        )
    updated = update_station(db, station, data)
    return StationRead(
        id=updated.id,
        nombre=updated.nombre,
        tipo=updated.tipo,
        linea=updated.linea,
    )

@router.delete("/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_station_endpoint(
    station_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
):
    station = get_station(db, station_id)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estación no encontrada",
        )

    delete_station(db, station)
    return

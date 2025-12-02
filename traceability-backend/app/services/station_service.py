from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Station
from app.schemas.schemas import StationCreate, StationUpdate

def get_station(db: Session, station_id: int) -> Optional[Station]:
    return db.query(Station).filter(Station.id == station_id).first()

def list_stations(db: Session) -> List[Station]:
    return db.query(Station).all()

def create_station(db: Session, data: StationCreate) -> Station:
    station = Station(
        nombre=data.nombre,
        tipo=data.tipo,
        linea=data.linea,
    )
    db.add(station)
    db.commit()
    db.refresh(station)
    return station

def update_station(db: Session, station: Station, data: StationUpdate) -> Station:
    if data.nombre is not None:
        station.nombre = data.nombre
    if data.tipo is not None:
        station.tipo = data.tipo
    if data.linea is not None:
        station.linea = data.linea

    db.commit()
    db.refresh(station)
    return station

def delete_station(db: Session, station: Station) -> None:
    db.delete(station)
    db.commit()

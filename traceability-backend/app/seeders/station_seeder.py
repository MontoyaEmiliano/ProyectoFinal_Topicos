from app.models.models import Station, StationType
from sqlalchemy.orm import Session

def seed_stations(db: Session):
    if db.query(Station).count() > 0:
        print("Stations already seeded.")
        return

    stations = [
        Station(nombre="Inspección Inicial", tipo=StationType.INSPECCION, linea="Línea 1"),
        Station(nombre="Ensamble Base", tipo=StationType.ENSAMBLE, linea="Línea 1"),
        Station(nombre="Ensamble Final", tipo=StationType.ENSAMBLE, linea="Línea 2"),
        Station(nombre="Prueba Funcional", tipo=StationType.PRUEBA, linea="Línea 2"),
        Station(nombre="Inspección Final", tipo=StationType.INSPECCION, linea="Línea 3"),
    ]

    db.add_all(stations)
    db.commit()
    print("Stations seeded successfully!")

from app.models.models import TraceEvent, TraceResult, Part, Station, User
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

def seed_trace_events(db: Session):
    if db.query(TraceEvent).count() > 0:
        print("TraceEvents already seeded.")
        return
    parts = db.query(Part).all()
    stations = db.query(Station).all()
    users = db.query(User).all()
    events = []

    for i in range(5):
        events.append(
            TraceEvent(
                part_id=parts[i].id,
                station_id=stations[i].id,
                operador_id=users[i].id,
                timestamp_entrada=datetime.utcnow() - timedelta(minutes=20*(i+1)),
                timestamp_salida=datetime.utcnow() - timedelta(minutes=10*(i+1)),
                resultado=TraceResult.OK if i % 2 == 0 else TraceResult.SCRAP,
                observaciones=f"Evento de prueba {i+1}"
            )
        )

    db.add_all(events)
    db.commit()
    print("TraceEvents seeded successfully!")

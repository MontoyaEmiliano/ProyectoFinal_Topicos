from app.core.database import SessionLocal, Base, engine
from app.seeders.user_seeder import seed_users
from app.seeders.station_seeder import seed_stations
from app.seeders.part_seeder import seed_parts
from app.seeders.trace_events_seeder import seed_trace_events

def run_all_seeders():
    db = SessionLocal()
    try:
        print("Creating tables if not exist...")
        Base.metadata.create_all(bind=engine)

        seed_users(db)
        seed_stations(db)
        seed_parts(db)
        seed_trace_events(db)

        print("ALL SEEDERS EXECUTED SUCCESSFULLY!")
    finally:
        db.close()


if __name__ == "__main__":
    run_all_seeders()

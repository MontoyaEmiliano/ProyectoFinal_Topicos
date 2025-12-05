from fastapi import FastAPI

from app.core.config import settings
from app.routers import api_router
from app.core.database import Base, engine
from app.seeders.run_seeders import run_all_seeders

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Traceability API")

@app.on_event("startup")
def startup_event():
    print("Running seeders on startup...")
    run_all_seeders()
    print("Seeders finished.")
app.include_router(api_router, prefix="/api")
@app.get("/")
def root():
    return {"message": "Traceability API running"}

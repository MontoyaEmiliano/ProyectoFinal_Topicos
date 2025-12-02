from fastapi import FastAPI
from app.routers import api_router


app = FastAPI(title="Traceability API")
app.include_router(api_router, prefix="/api")
@app.get("/")
def root():
    return {"message": "Traceability API running"}

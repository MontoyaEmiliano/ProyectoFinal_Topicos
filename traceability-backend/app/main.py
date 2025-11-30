from fastapi import FastAPI

app = FastAPI(title="Traceability API")

@app.get("/")
def root():
    return {"message": "Traceability API running"}

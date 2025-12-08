import os
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
from app.main import app
from app.core.database import Base, get_db
from app.models.models import (
    User,
    UserRole,
    Part,
    PartStatus,
    Station,
    TraceResult,
)
from app.services.auth_service import get_password_hash
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.sqlite"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

BASE_URL = "/api/trace-events"

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    admin = User(
        nombre="Administrador",
        email="admin@example.com",
        password_hash=get_password_hash("admin123"),
        rol=UserRole.ADMIN,
        activo=True,
    )

    operador = User(
        nombre="Operador 1",
        email="operador1@example.com",
        password_hash=get_password_hash("oper123"),
        rol=UserRole.OPERADOR,
        activo=True,
    )

    db.add_all([admin, operador])
    part = Part(
        id="PZA-100",
        tipo_pieza="X_TEST",
        lote="L_TEST",
        status=PartStatus.IN_PROCESS,
    )

    station = Station(
        id=1,
        nombre="Estación Trazabilidad",
        tipo="ENSAMBLE",   
        linea="Línea 1",
    )
    db.add_all([part, station])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

def get_admin_token():
    res = client.post(
        "/api/auth/login",
        data={"username": "admin@example.com", "password": "admin123"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]

def _build_valid_payload():
    now = datetime.utcnow()
    ts_in = now.isoformat()
    ts_out = (now + timedelta(minutes=5)).isoformat()
    result_enum = list(TraceResult)[0]
    result_value = result_enum.value if hasattr(result_enum, "value") else str(result_enum)

    return {
        "part_id": "PZA-100",
        "station_id": 1,
        "timestamp_entrada": ts_in,
        "timestamp_salida": ts_out,
        "resultado": result_value,
        "observaciones": "Evento de prueba",
    }

def test_create_trace_event_requires_auth():
    payload = _build_valid_payload()

    res = client.post(BASE_URL + "/", json=payload)

    assert res.status_code == 401  

def test_create_trace_event_success():
    token = get_admin_token()
    payload = _build_valid_payload()

    res = client.post(
        BASE_URL + "/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 201
    body = res.json()
    assert body["part_id"] == payload["part_id"]
    assert body["station_id"] == payload["station_id"]
    assert body["observaciones"] == payload["observaciones"]
    assert "timestamp_entrada" in body
    assert "timestamp_salida" in body
    assert "resultado" in body
    assert "operador_id" in body  

def test_create_trace_event_part_not_found():
    token = get_admin_token()
    payload = _build_valid_payload()
    payload["part_id"] = "NO-EXISTE"

    res = client.post(
        BASE_URL + "/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 404
    assert res.json()["detail"] == "Pieza no encontrada"

def test_create_trace_event_station_not_found():
    token = get_admin_token()
    payload = _build_valid_payload()
    payload["station_id"] = 999

    res = client.post(
        BASE_URL + "/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 404
    assert res.json()["detail"] == "Estación no encontrada"

def test_create_trace_event_invalid_timestamps():
    token = get_admin_token()

    now = datetime.utcnow()
    ts_in = now.isoformat()
    ts_out = (now - timedelta(minutes=5)).isoformat()  

    result_enum = list(TraceResult)[0]
    result_value = result_enum.value if hasattr(result_enum, "value") else str(result_enum)

    payload = {
        "part_id": "PZA-100",
        "station_id": 1,
        "timestamp_entrada": ts_in,
        "timestamp_salida": ts_out,
        "resultado": result_value,
        "observaciones": "Evento inválido",
    }

    res = client.post(
        BASE_URL + "/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 400
    assert res.json()["detail"] == "timestamp_salida debe ser mayor que timestamp_entrada"

def test_list_trace_events_requires_auth():
    res = client.get(BASE_URL + "/")
    assert res.status_code == 401

def test_list_trace_events_success():
    token = get_admin_token()
    payload1 = _build_valid_payload()
    payload2 = _build_valid_payload()
    payload2["observaciones"] = "Segundo evento"

    res1 = client.post(
        BASE_URL + "/",
        json=payload1,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 201

    res2 = client.post(
        BASE_URL + "/",
        json=payload2,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 201
    res_list = client.get(
        BASE_URL + "/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res_list.status_code == 200
    data = res_list.json()
    assert isinstance(data, list)
    assert len(data) >= 2

def test_get_trace_event_not_found():
    token = get_admin_token()

    res = client.get(
        f"{BASE_URL}/9999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 404
    assert res.json()["detail"] == "Evento de trazabilidad no encontrado"

def test_get_trace_event_success():
    token = get_admin_token()
    payload = _build_valid_payload()
    res_create = client.post(
        BASE_URL + "/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res_create.status_code == 201
    created = res_create.json()
    event_id = created["id"]
    res_get = client.get(
        f"{BASE_URL}/{event_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res_get.status_code == 200
    body = res_get.json()
    assert body["id"] == event_id
    assert body["part_id"] == payload["part_id"]
    assert body["station_id"] == payload["station_id"]

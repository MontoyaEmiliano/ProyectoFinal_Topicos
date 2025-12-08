import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
from app.main import app
from app.core.database import Base, get_db
from app.models.models import User, UserRole, Station
from app.services.auth_service import get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.sqlite"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
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

BASE_URL = "/api/stations"
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
    db.add(admin)
    stations = [
        Station(id=1, nombre="Estación A", tipo="ENSAMBLE", linea="Línea 1"),
        Station(id=2, nombre="Estación B", tipo="PRUEBA", linea="Línea 1"),
        Station(id=3, nombre="Estación C", tipo="INSPECCION", linea="Línea 2"),
    ]
    db.add_all(stations)

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

def test_list_stations_requires_auth():
    res = client.get(BASE_URL + "/")
    assert res.status_code == 401  


def test_list_stations_success():
    token = get_admin_token()
    res = client.get(
        BASE_URL + "/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 3

    first = data[0]
    assert "id" in first
    assert "nombre" in first
    assert "tipo" in first
    assert "linea" in first


def test_get_station_by_id_success():
    token = get_admin_token()
    res = client.get(
        f"{BASE_URL}/1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == 1
    assert body["nombre"] == "Estación A"


def test_get_station_by_id_not_found():
    token = get_admin_token()
    res = client.get(
        f"{BASE_URL}/999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 404
    body = res.json()
    assert body["detail"] == "Estación no encontrada"


def test_create_station_success():
    token = get_admin_token()
    payload = {
        "nombre": "Estación Nueva",
        "tipo": "PRUEBA",
        "linea": "Línea 3",
    }

    res = client.post(
        BASE_URL + "/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 201
    body = res.json()
    assert body["nombre"] == payload["nombre"]
    assert body["tipo"] == payload["tipo"]
    assert body["linea"] == payload["linea"]


def test_create_station_duplicate_name():
    token = get_admin_token()
    payload = {
        "nombre": "Estación A",  # ya existe por el seed
        "tipo": "PRUEBA",
        "linea": "Línea X",
    }

    res = client.post(
        BASE_URL + "/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 409
    body = res.json()
    assert body["detail"] == "Ya existe una estación con ese nombre"


def test_update_station_success():
    token = get_admin_token()
    payload = {
        "nombre": "Estación A Modificada",
        "tipo": "ENSAMBLE",
        "linea": "Línea 99",
    }

    res = client.put(
        f"{BASE_URL}/1",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == 1
    assert body["nombre"] == payload["nombre"]
    assert body["linea"] == payload["linea"]

def test_delete_station_success():
    token = get_admin_token()

    res = client.delete(
        f"{BASE_URL}/3",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 204

    res_check = client.get(
        f"{BASE_URL}/3",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_check.status_code == 404

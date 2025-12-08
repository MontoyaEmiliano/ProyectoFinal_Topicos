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
from app.models.models import User, UserRole
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

BASE_URL = "/api/users"

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    admin = User(
        id=1,
        nombre="Admin",
        email="admin@example.com",
        password_hash=get_password_hash("admin123"),
        rol=UserRole.ADMIN,
        activo=True,
    )

    supervisor = User(
        id=2,
        nombre="Supervisor Uno",
        email="sup1@example.com",
        password_hash=get_password_hash("sup123"),
        rol=UserRole.SUPERVISOR,
        activo=True,
    )

    operador = User(
        id=3,
        nombre="Operador Inactivo",
        email="op1@example.com",
        password_hash=get_password_hash("op123"),
        rol=UserRole.OPERADOR,
        activo=False,
    )

    db.add_all([admin, supervisor, operador])
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

def test_list_users_requires_auth():
    res = client.get(BASE_URL + "/")
    assert res.status_code == 401 

def test_list_users_success():
    token = get_admin_token()

    res = client.get(
        BASE_URL + "/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 3
    emails = {u["email"] for u in data}
    assert "admin@example.com" in emails
    assert "sup1@example.com" in emails
    assert "op1@example.com" in emails

def test_list_users_filter_by_role():
    token = get_admin_token()

    res = client.get(
        BASE_URL + "/?rol=SUPERVISOR",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["email"] == "sup1@example.com"
    assert data[0]["rol"] == "SUPERVISOR"

def test_list_users_filter_by_activo():
    token = get_admin_token()

    res = client.get(
        BASE_URL + "/?activo=false",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["email"] == "op1@example.com"
    assert data[0]["activo"] is False

def test_get_user_by_id_not_found():
    token = get_admin_token()

    res = client.get(
        f"{BASE_URL}/999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 404
    assert res.json()["detail"] == "Usuario no encontrado"


def test_get_user_by_id_success():
    token = get_admin_token()
    res = client.get(
        f"{BASE_URL}/2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == 2
    assert body["email"] == "sup1@example.com"
    assert body["rol"] == "SUPERVISOR"

def test_update_user_not_found():
    token = get_admin_token()

    payload = {"nombre": "No Existe"}

    res = client.patch(
        f"{BASE_URL}/999",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 404
    assert res.json()["detail"] == "Usuario no encontrado"


def test_update_user_success():
    token = get_admin_token()

    payload = {
        "nombre": "Supervisor Actualizado",
        "rol": "OPERADOR",
        "activo": False,
    }

    res = client.patch(
        f"{BASE_URL}/2",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == 2
    assert body["nombre"] == "Supervisor Actualizado"
    assert body["rol"] == "OPERADOR"
    assert body["activo"] is False

def test_delete_user_not_found():
    token = get_admin_token()

    res = client.delete(
        f"{BASE_URL}/999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 404
    assert res.json()["detail"] == "Usuario no encontrado"


def test_delete_user_success_soft_delete():
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
    assert res_check.status_code == 200
    body = res_check.json()
    assert body["id"] == 3
    assert body["activo"] is False
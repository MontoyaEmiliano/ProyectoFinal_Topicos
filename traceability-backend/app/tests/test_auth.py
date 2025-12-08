import os
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models.models import User, UserRole
from app.services.auth_service import get_password_hash

SQL_URL = "sqlite:///./test_db.sqlite"

engine = create_engine(SQL_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
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
    db.commit()
    db.close()

    yield

    # Limpiar al final de la sesión de tests
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# ----------------------------------------------------------------------------- 
# TEST: LOGIN CORRECTO
# -----------------------------------------------------------------------------
def test_login_success():
    response = client.post(
        "/api/auth/login",   # <-- ajustado
        data={"username": "admin@example.com", "password": "admin123"},
    )

    assert response.status_code == 200
    json = response.json()

    assert "access_token" in json
    assert json["user"]["email"] == "admin@example.com"


# ----------------------------------------------------------------------------- 
# TEST: LOGIN CON CREDENCIALES INVÁLIDAS
# -----------------------------------------------------------------------------
def test_login_invalid_credentials():
    response = client.post(
        "/api/auth/login",   # <-- ajustado
        data={"username": "admin@example.com", "password": "wrongpass"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Credenciales inválidas"


# ----------------------------------------------------------------------------- 
# TEST: /auth/me SIN TOKEN (debe fallar)
# -----------------------------------------------------------------------------
def test_me_unauthorized():
    res = client.get("/api/auth/me")   # <-- ajustado
    assert res.status_code == 401


# ----------------------------------------------------------------------------- 
# TEST: /auth/me CON TOKEN
# -----------------------------------------------------------------------------
def test_me_authenticated():
    # Obtener token
    login = client.post(
        "/api/auth/login",   # <-- ajustado
        data={"username": "admin@example.com", "password": "admin123"},
    )
    token = login.json()["access_token"]

    # Llamar a /me
    res = client.get(
        "/api/auth/me",      # <-- ajustado
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    assert res.json()["email"] == "admin@example.com"


# ----------------------------------------------------------------------------- 
# TEST: REGISTRO DE USUARIO NUEVO (ADMIN AUTENTICADO)
# -----------------------------------------------------------------------------
def test_register_user_success():
    # Login para obtener token de admin
    login = client.post(
        "/api/auth/login",   # <-- ajustado
        data={"username": "admin@example.com", "password": "admin123"},
    )
    token = login.json()["access_token"]

    new_user = {
        "nombre": "Supervisor 1",
        "email": "supervisor1@example.com",
        "password": "test123",
        "rol": "SUPERVISOR",
    }

    res = client.post(
        "/api/auth/register",    # <-- ajustado
        json=new_user,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    assert res.json()["email"] == "supervisor1@example.com"


# ----------------------------------------------------------------------------- 
# TEST: REGISTRO DUPLICADO → 409
# -----------------------------------------------------------------------------
def test_register_duplicate_email():
    login = client.post(
        "/api/auth/login",   # <-- ajustado
        data={"username": "admin@example.com", "password": "admin123"},
    )
    token = login.json()["access_token"]

    new_user = {
        "nombre": "Repetido",
        "email": "supervisor1@example.com",  # ya existe
        "password": "test123",
        "rol": "SUPERVISOR",
    }

    res = client.post(
        "/api/auth/register",    # <-- ajustado
        json=new_user,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 409
    assert res.json()["detail"] == "Ya existe un usuario con ese email"

import os
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
os.environ.setdefault("SECRET_KEY", "test-secret")
from app.main import app
from app.core.database import Base, get_db
from app.models.models import User, UserRole, Part, PartStatus
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

BASE_URL = "/api/parts"  

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
    parts = [
        Part(id="PZA-001", tipo_pieza="X1", lote="L001", status=PartStatus.IN_PROCESS),
        Part(id="PZA-002", tipo_pieza="X1", lote="L001", status=PartStatus.COMPLETED),
        Part(id="PZA-003", tipo_pieza="X2", lote="L002", status=PartStatus.SCRAPPED),
        Part(
            id="PZA-004",
            tipo_pieza="X2",
            lote="L002",
            status=PartStatus.IN_PROCESS,
            num_retrabajos=1,
        ),
        Part(id="PZA-005", tipo_pieza="X3", lote="L003", status=PartStatus.IN_PROCESS),
    ]
    db.add_all(parts)

    db.commit()
    db.close()

    yield  
    Base.metadata.drop_all(bind=engine)


def get_admin_token():
    """Hace login con el admin semillado y devuelve un Bearer token."""
    res = client.post(
        "/api/auth/login",
        data={"username": "admin@example.com", "password": "admin123"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]

def test_list_parts_requires_auth():
    res = client.get(BASE_URL)
    assert res.status_code == 401

def test_list_parts_ok():
    token = get_admin_token()

    res = client.get(
        BASE_URL,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    ids = {p["id"] for p in data}
    assert "PZA-001" in ids
    assert "PZA-004" in ids

def test_get_part_not_found():
    token = get_admin_token()

    res = client.get(
        f"{BASE_URL}/NO-EXISTE",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


def test_get_part_ok():
    token = get_admin_token()

    res = client.get(
        f"{BASE_URL}/PZA-001",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == "PZA-001"
    assert body["tipo_pieza"] == "X1"
    assert body["lote"] == "L001"
    assert body["status"] == PartStatus.IN_PROCESS.value

def test_create_part_conflict_when_id_exists():
    token = get_admin_token()

    payload = {
        "id": "PZA-001",  
        "tipo_pieza": "X9",
        "lote": "L999",
        "status": "IN_PROCESS",
    }

    res = client.post(
        BASE_URL + "/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 409


def test_create_part_success():
    token = get_admin_token()

    payload = {
        "id": "PZA-010",
        "tipo_pieza": "X9",
        "lote": "L999",
        "status": "IN_PROCESS",
    }

    res = client.post(
        BASE_URL + "/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 201
    body = res.json()
    assert body["id"] == "PZA-010"
    assert body["tipo_pieza"] == "X9"
    assert body["lote"] == "L999"
    assert body["status"] == "IN_PROCESS"


def test_update_part_status():
    token = get_admin_token()
    res_before = client.get(
        f"{BASE_URL}/PZA-004",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_before.status_code == 200
    body_before = res_before.json()
    original_retrabajos = body_before["num_retrabajos"]
    payload = {
        "status": "COMPLETED",
    }
    res = client.patch(
        f"{BASE_URL}/PZA-004",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == "PZA-004"
    assert body["status"] == "COMPLETED"
    assert body["num_retrabajos"] == original_retrabajos

def test_part_history_returns_list_even_if_empty():
    token = get_admin_token()

    res = client.get(
        f"{BASE_URL}/PZA-001/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, list)

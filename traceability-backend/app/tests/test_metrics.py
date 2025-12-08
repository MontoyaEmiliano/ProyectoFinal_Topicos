import os
from datetime import date
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
BASE_URL = "/api/metrics"

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    admin = User(
        nombre="Admin",
        email="admin@example.com",
        password_hash=get_password_hash("admin123"),
        rol=UserRole.ADMIN,
        activo=True,
    )
    db.add(admin)
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

def test_parts_by_status_requires_auth():
    res = client.get(f"{BASE_URL}/parts-by-status")
    assert res.status_code == 401

def test_parts_by_status_success():
    token = get_admin_token()

    res = client.get(
        f"{BASE_URL}/parts-by-status",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200

def test_throughput_requires_auth():
    today = date.today().isoformat()
    res = client.get(f"{BASE_URL}/throughput?from={today}&to={today}")
    assert res.status_code == 401

def test_throughput_success():
    token = get_admin_token()
    today = date.today().isoformat()

    res = client.get(
        f"{BASE_URL}/throughput?from={today}&to={today}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200

def test_station_cycle_time_requires_auth():
    res = client.get(f"{BASE_URL}/station-cycle-time")
    assert res.status_code == 401

def test_station_cycle_time_success():
    token = get_admin_token()

    res = client.get(
        f"{BASE_URL}/station-cycle-time",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200

def test_scrap_rate_requires_auth():
    res = client.get(f"{BASE_URL}/scrap-rate")
    assert res.status_code == 401

def test_scrap_rate_success():
    token = get_admin_token()

    res = client.get(
        f"{BASE_URL}/scrap-rate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200

def test_metrics_overview_requires_auth():
    res = client.get(f"{BASE_URL}/overview")
    assert res.status_code == 401


def test_metrics_overview_success():
    token = get_admin_token()

    res = client.get(
        f"{BASE_URL}/overview",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200

def test_station_load_requires_auth():
    res = client.get(f"{BASE_URL}/station-load")
    assert res.status_code == 401

def test_station_load_success():
    token = get_admin_token()

    res = client.get(
        f"{BASE_URL}/station-load",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200

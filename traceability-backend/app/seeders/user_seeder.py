from app.models.models import User, UserRole
from app.services.auth_service import get_password_hash
from sqlalchemy.orm import Session

def seed_users(db: Session):
    if db.query(User).count() > 0:
        print("Users already seeded.")
        return

    users = [
        User(
            nombre="Administrador",
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            rol=UserRole.ADMIN,
        ),
        User(
            nombre="Operador 1",
            email="operador1@example.com",
            password_hash=get_password_hash("password1"),
            rol=UserRole.OPERADOR,
        ),
        User(
            nombre="Operador 2",
            email="operador2@example.com",
            password_hash=get_password_hash("password2"),
            rol=UserRole.OPERADOR,
        ),
        User(
            nombre="Supervisor 1",
            email="supervisor1@example.com",
            password_hash=get_password_hash("password3"),
            rol=UserRole.SUPERVISOR,
        ),
        User(
            nombre="Supervisor 2",
            email="supervisor2@example.com",
            password_hash=get_password_hash("password4"),
            rol=UserRole.SUPERVISOR,
        ),
    ]

    db.add_all(users)
    db.commit()
    print("Users seeded successfully!")

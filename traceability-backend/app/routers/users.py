from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User, UserRole
from app.schemas.schemas import UserRead
from app.services.auth_service import require_role

router = APIRouter(prefix="/users")

class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    rol: Optional[UserRole] = None
    activo: Optional[bool] = None

@router.get("/", response_model=List[UserRead])
def list_users(
    rol: Optional[UserRole] = Query(default=None),
    activo: Optional[bool] = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
):
    query = db.query(User)

    if rol is not None:
        query = query.filter(User.rol == rol)

    if activo is not None:
        query = query.filter(User.activo == activo)

    users = query.offset(skip).limit(limit).all()

    return [
        UserRead(
            id=u.id,
            nombre=u.nombre,
            email=u.email,
            rol=u.rol,
            activo=u.activo,
            fecha_registro=u.fecha_registro,
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=UserRead)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return UserRead(
        id=user.id,
        nombre=user.nombre,
        email=user.email,
        rol=user.rol,
        activo=user.activo,
        fecha_registro=user.fecha_registro,
    )

@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    if data.nombre is not None:
        user.nombre = data.nombre

    if data.rol is not None:
        user.rol = data.rol

    if data.activo is not None:
        user.activo = data.activo

    db.commit()
    db.refresh(user)

    return UserRead(
        id=user.id,
        nombre=user.nombre,
        email=user.email,
        rol=user.rol,
        activo=user.activo,
        fecha_registro=user.fecha_registro,
    )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    user.activo = False
    db.commit()
    return

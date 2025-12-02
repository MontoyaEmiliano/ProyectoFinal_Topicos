from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User, UserRole
from app.schemas.schemas import UserCreate, UserRead
from app.services.auth_service import (
    get_password_hash,
    verify_password,
    get_user_by_email,
    create_access_token,
    get_current_user,
    require_role,
)

router = APIRouter(prefix="/auth")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead

class LoginBody(BaseModel):
    email: str
    password: str

@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user: User | None = get_user_by_email(db, form_data.username)

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credenciales inválidas",
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "rol": user.rol.value,
        },
        expires_delta=access_token_expires,
    )

    user_read = UserRead(
        id=user.id,
        nombre=user.nombre,
        email=user.email,
        rol=user.rol,
        activo=user.activo,
        fecha_registro=user.fecha_registro,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_read,
    )


@router.post("/register", response_model=UserRead)
def register_user(
    new_user: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
):
    existing = get_user_by_email(db, new_user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email",
        )

    user = User(
        nombre=new_user.nombre,
        email=new_user.email,
        password_hash=get_password_hash(new_user.password),
        rol=new_user.rol,
        activo=True,
    )

    db.add(user)
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


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Devuelve la información del usuario autenticado.
    """
    return UserRead(
        id=current_user.id,
        nombre=current_user.nombre,
        email=current_user.email,
        rol=current_user.rol,
        activo=current_user.activo,
        fecha_registro=current_user.fecha_registro,
    )

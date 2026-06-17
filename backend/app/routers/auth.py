from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.limiter import limiter
from app.services import auth_service as svc

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"email": "agente@empresa.com", "password": "mipassword123"}
    })
    email: EmailStr
    password: str


@router.post("/login", summary="Iniciar sesión")
@limiter.limit("10/minute")
async def login(request: Request, body: LoginBody, db: AsyncSession = Depends(get_db)):
    """
    Autentica al usuario y devuelve un token JWT.

    - El token debe enviarse en el header `Authorization: Bearer <token>` en todas las rutas protegidas.
    - Roles disponibles: `user`, `agent`, `admin`.
    """
    return await svc.login(db, body.email, body.password)


@router.get("/me", summary="Usuario actual")
async def me(user: dict = Depends(get_current_user)):
    """
    Devuelve los datos del usuario autenticado según el token JWT.

    Requiere header: `Authorization: Bearer <token>`
    """
    return user

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.limiter import limiter
from app.services import password_reset_service as svc

router = APIRouter(prefix="/api/reset-password", tags=["reset-password"])


class RequestBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"email": "usuario@empresa.com"}
    })
    email: EmailStr


class ValidateBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"token": "abc123xyz789"}
    })
    token: str


class ConfirmBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"token": "abc123xyz789", "new_password": "NuevaPassword456!"}
    })
    token: str
    new_password: str


@router.post("/request", summary="Solicitar reset de contraseña")
@limiter.limit("3/hour")
async def request_reset(request: Request, body: RequestBody, db: AsyncSession = Depends(get_db)):
    """
    Genera un token de reset válido por 15 minutos para el email indicado.

    - No requiere autenticación — acción pública.
    - El token se devuelve directamente en la respuesta (el email está en modo simulado).
    - Ejemplo: envía `{"email": "usuario@empresa.com"}` y obtienes el token en la respuesta.
    """
    return await svc.request_reset(db, body.email)


@router.post("/validate", summary="Validar token de reset")
async def validate_token(body: ValidateBody, db: AsyncSession = Depends(get_db)):
    """
    Verifica si un token de reset es válido y no ha expirado.

    - No requiere autenticación.
    - Devuelve `valid: true/false` y la fecha de expiración si es válido.
    """
    return await svc.validate_token(db, body.token)


@router.post("/confirm", summary="Confirmar nueva contraseña")
async def confirm_reset(body: ConfirmBody, db: AsyncSession = Depends(get_db)):
    """
    Aplica la nueva contraseña usando el token de reset.

    - No requiere autenticación.
    - El token se invalida tras usarse.
    - Flujo completo: `/request` → copiar token → `/validate` (opcional) → `/confirm`
    """
    return await svc.confirm_reset(db, body.token, body.new_password)

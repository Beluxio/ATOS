from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import require_role
from app.services import account_service as svc

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


class RegisterBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "nuevo@empresa.com",
            "username": "juanperez",
            "password": "Password123!",
            "role": "user",
        }
    })
    email: EmailStr
    username: str
    password: str
    role: Optional[str] = "user"


@router.post("/register", summary="Registrar cuenta")
async def register(body: RegisterBody, db: AsyncSession = Depends(get_db),
                   current_user: dict = Depends(require_role("admin"))):
    """
    Crea una nueva cuenta de usuario.

    - `role` puede ser `user`, `agent` o `admin` (por defecto `user`).
    - El email debe ser único en el sistema.
    """
    return await svc.register(db, body.email, body.username, body.password, body.role or "user")


@router.get("", summary="Listar cuentas")
async def list_accounts(db: AsyncSession = Depends(get_db),
                        current_user: dict = Depends(require_role("admin", "agent"))):
    """
    Devuelve todas las cuentas registradas en el sistema.

    Útil para administración y auditoría de usuarios.
    """
    return await svc.list_accounts(db)


@router.get("/{email}/status", summary="Estado de cuenta")
async def get_status(email: str, db: AsyncSession = Depends(get_db)):
    """
    Consulta el estado actual de una cuenta.

    - Devuelve si la cuenta está activa, bloqueada o pendiente de verificación.
    - Ejemplo: `GET /api/accounts/usuario@empresa.com/status`
    """
    return await svc.check_status(db, email)


@router.post("/{email}/unlock", summary="Desbloquear cuenta")
async def unlock(email: str, db: AsyncSession = Depends(get_db)):
    """
    Desbloquea una cuenta que fue bloqueada (por intentos fallidos u otro motivo).

    - Ejemplo: `POST /api/accounts/usuario@empresa.com/unlock`
    """
    return await svc.unlock(db, email)


@router.patch("/{email}/job-role", summary="Asignar job role")
async def set_job_role(
    email: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Asigna o cambia el job role de un usuario.

    - Requiere rol `admin`.
    - Valores válidos: `frontend_dev`, `backend_dev`, `data_scientist`, o `null` para quitar el rol.
    - El job role determina a qué bases de datos puede tener acceso el usuario.
    """
    return await svc.update_job_role(db, email, body.get("job_role"))


@router.post("/{email}/lock", summary="Bloquear cuenta")
async def lock(email: str, db: AsyncSession = Depends(get_db)):
    """
    Bloquea una cuenta impidiendo el acceso hasta que sea desbloqueada manualmente.

    - Ejemplo: `POST /api/accounts/usuario@empresa.com/lock`
    """
    return await svc.lock(db, email)

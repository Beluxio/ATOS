from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import require_role, get_current_user
from app.services import database_access_service as svc

router = APIRouter(prefix="/api/db-access", tags=["database-access"])

DATABASES = sorted(svc.ALLOWED_DATABASES)


class GrantBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"user_email": "carlos@dataco.com", "database_name": "DataCo Analytics", "granted_by": "admin@atos.com", "days": 30}
    })
    user_email: EmailStr
    database_name: str
    granted_by: Optional[str] = None
    days: Optional[int] = 30


@router.get("", summary="Listar todos los accesos")
async def list_all(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    Devuelve todos los registros de acceso. Revoca automáticamente los vencidos antes de responder.

    Requiere rol `admin` o `agent`.
    """
    await svc.expire_check(db)
    return await svc.list_all(db)


@router.get("/logs", summary="Historial de acciones")
async def get_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    Devuelve el historial de todas las acciones sobre accesos a BD: otorgados, revocados, expirados y resets.

    Requiere rol `admin` o `agent`.
    """
    return await svc.get_logs(db, limit)


@router.post("/expire-check", summary="Verificar accesos expirados")
async def run_expire_check(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    Revoca manualmente todos los accesos vencidos y notifica a los usuarios por email.

    Requiere rol `admin` o `agent`.
    """
    return await svc.expire_check(db)


@router.get("/my-accesses", summary="Mis accesos a bases de datos")
async def my_accesses(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Devuelve los accesos a bases de datos del usuario autenticado.

    Disponible para cualquier usuario con sesión activa — no requiere rol especial.
    """
    await svc.expire_check(db)
    return await svc.get_user_accesses(db, current_user["sub"])


@router.get("/databases", summary="Bases de datos disponibles")
async def list_databases(current_user: dict = Depends(require_role("admin", "agent"))):
    """Devuelve la lista de bases de datos gestionadas por ATOS."""
    return {"databases": DATABASES}


@router.get("/user/{email}", summary="Accesos de un usuario")
async def get_user_accesses(
    email: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """Devuelve todos los accesos a bases de datos de un usuario específico."""
    return await svc.get_user_accesses(db, email)


@router.get("/database/{name}", summary="Usuarios de una base de datos")
async def get_database_users(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """Devuelve todos los usuarios con acceso a la base de datos indicada."""
    return await svc.get_database_users(db, name)


@router.post("/grant", summary="Otorgar acceso")
async def grant_access(
    body: GrantBody,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    Otorga acceso a una base de datos y genera credenciales automáticamente.

    - El `db_username` se genera a partir del email y el nombre de la BD.
    - La `db_password` se genera aleatoriamente y se muestra solo en esta respuesta.
    - Requiere rol `admin` o `agent`.
    """
    granted_by = body.granted_by or current_user.get("sub")
    return await svc.grant_access(db, body.user_email, body.database_name, granted_by, body.days)


@router.patch("/{access_id}", summary="Editar acceso")
async def edit_access(
    access_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    Edita un acceso activo. Campos modificables: `days` (nueva vigencia desde hoy) y `notes`.

    - El cambio queda registrado en el historial con el detalle de qué se modificó.
    - Requiere rol `admin` o `agent`.
    """
    return await svc.update_access(
        db, access_id,
        days=body.get("days"),
        no_expiry=body.get("no_expiry", False),
        notes=body.get("notes"),
        performed_by=current_user.get("sub"),
    )


@router.post("/{access_id}/revoke", summary="Revocar acceso")
async def revoke_access(
    access_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    Revoca el acceso de un usuario a una base de datos por ID de registro.

    Requiere rol `admin` o `agent`.
    """
    from sqlalchemy import select
    from app.models.database_access import DatabaseAccess
    result = await db.execute(select(DatabaseAccess).where(DatabaseAccess.id == access_id))
    record = result.scalar_one_or_none()
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Registro de acceso no encontrado.")
    return await svc.revoke_access(db, record.user_email, record.database_name)


@router.post("/{access_id}/reset-password", summary="Resetear contraseña de BD")
async def reset_db_password(
    access_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    Genera una nueva contraseña de base de datos para el acceso indicado.

    - La nueva contraseña se devuelve en la respuesta — guárdala, no se vuelve a mostrar.
    - Requiere rol `admin` o `agent`.
    """
    from sqlalchemy import select
    from app.models.database_access import DatabaseAccess
    result = await db.execute(select(DatabaseAccess).where(DatabaseAccess.id == access_id))
    record = result.scalar_one_or_none()
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Registro de acceso no encontrado.")
    return await svc.reset_password(db, record.user_email, record.database_name)

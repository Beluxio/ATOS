from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import require_role
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/logs", summary="Logs de auditoría")
async def get_logs(
    limit: int = Query(50, ge=1, le=500, description="Cantidad de logs a devolver (máx. 500)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    Devuelve el historial de todas las herramientas ejecutadas por el agente, ordenadas por fecha descendente.

    - Cada entrada registra: herramienta ejecutada, parámetros usados, resultado y sesión.
    - Útil para auditoría, debugging y monitoreo del comportamiento del agente.
    - Ejemplo: `?limit=10` devuelve las últimas 10 ejecuciones.
    """
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "tool_name": log.tool_name,
            "params": log.params_json,
            "result": log.result_json,
            "session_id": log.session_id,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]

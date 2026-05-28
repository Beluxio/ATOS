from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/logs")
async def get_logs(limit: int = 50, db: AsyncSession = Depends(get_db)):
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

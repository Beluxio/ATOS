import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import require_role
from app.models.ticket import Ticket
from app.models.account import Account
from app.models.database_access import DatabaseAccess
from app.models.database_access_log import DatabaseAccessLog
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/api/export", tags=["export"])


def _csv_response(rows: list[dict], filename: str) -> StreamingResponse:
    if not rows:
        rows = [{"info": "Sin datos"}]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _ts(dt) -> str:
    if dt is None:
        return ""
    if hasattr(dt, "tzinfo") and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


@router.get("/tickets", summary="Exportar tickets a CSV")
async def export_tickets(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    rows_db = (await db.execute(select(Ticket).order_by(Ticket.created_at.desc()))).scalars().all()
    rows = [
        {
            "id": t.id,
            "titulo": t.title,
            "descripcion": t.description,
            "estado": t.status,
            "prioridad": t.priority,
            "creado_por": t.created_by,
            "asignado_a": t.assigned_to or "",
            "creado_en": _ts(t.created_at),
            "actualizado_en": _ts(t.updated_at),
        }
        for t in rows_db
    ]
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    return _csv_response(rows, f"tickets_{ts}.csv")


@router.get("/accounts", summary="Exportar cuentas a CSV")
async def export_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    rows_db = (await db.execute(select(Account).order_by(Account.created_at.desc()))).scalars().all()
    rows = [
        {
            "email": a.email,
            "username": a.username,
            "rol": a.role,
            "job_role": a.job_role or "",
            "estado": a.status,
            "intentos_fallidos": a.failed_login_attempts,
            "creado_en": _ts(a.created_at),
        }
        for a in rows_db
    ]
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    return _csv_response(rows, f"cuentas_{ts}.csv")


@router.get("/db-access", summary="Exportar accesos a BD a CSV")
async def export_db_access(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    rows_db = (await db.execute(
        select(DatabaseAccess).order_by(DatabaseAccess.created_at.desc())
    )).scalars().all()
    now = datetime.now(timezone.utc)
    rows = [
        {
            "id": a.id,
            "usuario": a.user_email,
            "base_de_datos": a.database_name,
            "usuario_bd": a.db_username,
            "estado": a.status,
            "otorgado_por": a.granted_by or "",
            "notas": a.notes or "",
            "expira_en": _ts(a.expires_at),
            "dias_restantes": max(0, (a.expires_at.replace(tzinfo=timezone.utc) - now).days) if a.expires_at else "",
            "aviso_enviado": "Sí" if a.expiry_warning_sent else "No",
            "creado_en": _ts(a.created_at),
        }
        for a in rows_db
    ]
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    return _csv_response(rows, f"accesos_bd_{ts}.csv")


@router.get("/db-access-logs", summary="Exportar historial de accesos a CSV")
async def export_db_access_logs(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    rows_db = (await db.execute(
        select(DatabaseAccessLog).order_by(DatabaseAccessLog.created_at.desc())
    )).scalars().all()
    rows = [
        {
            "id": r.id,
            "usuario": r.user_email,
            "base_de_datos": r.database_name,
            "accion": r.action,
            "realizado_por": r.performed_by or "",
            "detalles": r.details or "",
            "fecha": _ts(r.created_at),
        }
        for r in rows_db
    ]
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    return _csv_response(rows, f"historial_accesos_{ts}.csv")


@router.get("/audit-logs", summary="Exportar audit logs del agente a CSV")
async def export_audit_logs(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    rows_db = (await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc())
    )).scalars().all()
    rows = [
        {
            "id": r.id,
            "herramienta": r.tool_name,
            "usuario": r.user_email or "",
            "session_id": r.session_id or "",
            "fecha": _ts(r.created_at),
        }
        for r in rows_db
    ]
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    return _csv_response(rows, f"audit_logs_{ts}.csv")

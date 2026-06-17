from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.core.database import get_db
from app.core.auth import require_role
from app.models.ticket import Ticket
from app.models.account import Account
from app.models.database_access import DatabaseAccess
from app.models.database_access_log import DatabaseAccessLog
from app.models.incident_history import IncidentHistory
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", summary="Métricas generales del sistema")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """Devuelve estadísticas agregadas de tickets, cuentas, accesos a BD e historial."""

    # ── Tickets ──────────────────────────────────────────────────────────────
    ticket_rows = (await db.execute(
        select(Ticket.status, func.count().label("n")).group_by(Ticket.status)
    )).all()
    ticket_by_status = {r.status: r.n for r in ticket_rows}

    priority_rows = (await db.execute(
        select(Ticket.priority, func.count().label("n")).group_by(Ticket.priority)
    )).all()
    ticket_by_priority = {r.priority: r.n for r in priority_rows}

    total_tickets = sum(ticket_by_status.values())

    # ── Accounts ─────────────────────────────────────────────────────────────
    acc_rows = (await db.execute(
        select(Account.role, func.count().label("n")).group_by(Account.role)
    )).all()
    accounts_by_role = {r.role: r.n for r in acc_rows}

    job_rows = (await db.execute(
        select(Account.job_role, func.count().label("n"))
        .where(Account.job_role.isnot(None))
        .group_by(Account.job_role)
    )).all()
    accounts_by_job_role = {r.job_role: r.n for r in job_rows}

    locked_count = (await db.execute(
        select(func.count()).where(Account.status == "locked")
    )).scalar_one()

    total_accounts = sum(accounts_by_role.values())

    # ── DB Access ─────────────────────────────────────────────────────────────
    db_rows = (await db.execute(
        select(DatabaseAccess.database_name, func.count().label("n"))
        .where(DatabaseAccess.status == "active")
        .group_by(DatabaseAccess.database_name)
    )).all()
    active_access_by_db = {r.database_name: r.n for r in db_rows}

    soon = datetime.now(timezone.utc) + timedelta(days=7)
    expiring_soon = (await db.execute(
        select(func.count()).select_from(DatabaseAccess).where(
            DatabaseAccess.status == "active",
            DatabaseAccess.expires_at.isnot(None),
            DatabaseAccess.expires_at <= soon,
        )
    )).scalar_one()

    total_active_accesses = sum(active_access_by_db.values())

    db_log_rows = (await db.execute(
        select(DatabaseAccessLog.action, func.count().label("n"))
        .group_by(DatabaseAccessLog.action)
    )).all()
    db_actions = {r.action: r.n for r in db_log_rows}

    # ── Incident History ──────────────────────────────────────────────────────
    outcome_rows = (await db.execute(
        select(IncidentHistory.outcome, func.count().label("n"))
        .group_by(IncidentHistory.outcome)
    )).all()
    incidents_by_outcome = {r.outcome: r.n for r in outcome_rows}

    cat_rows = (await db.execute(
        select(IncidentHistory.category, func.count().label("n"))
        .where(IncidentHistory.category.isnot(None))
        .group_by(IncidentHistory.category)
        .order_by(func.count().desc())
        .limit(5)
    )).all()
    top_categories = [{"category": r.category, "count": r.n} for r in cat_rows]

    total_incidents = sum(incidents_by_outcome.values())

    # ── Audit Log (agent activity) ────────────────────────────────────────────
    tool_rows = (await db.execute(
        select(AuditLog.tool_name, func.count().label("n"))
        .group_by(AuditLog.tool_name)
        .order_by(func.count().desc())
        .limit(6)
    )).all()
    top_tools = [{"tool": r.tool_name, "count": r.n} for r in tool_rows]

    total_tool_calls = (await db.execute(select(func.count()).select_from(AuditLog))).scalar_one()

    # ── SLA ──────────────────────────────────────────────────────────────────
    SLA_HOURS = {"critical": 4, "high": 8, "medium": 24, "low": 72}

    resolved_tickets = (await db.execute(
        select(Ticket.priority, Ticket.created_at, Ticket.resolved_at)
        .where(Ticket.resolved_at.isnot(None))
    )).all()

    sla_by_priority: dict[str, dict] = {}
    for priority, sla_h in SLA_HOURS.items():
        rows = [r for r in resolved_tickets if r.priority == priority]
        if not rows:
            sla_by_priority[priority] = {"avg_hours": None, "within_sla": None, "total": 0}
            continue
        hours = []
        within = 0
        for r in rows:
            ca = r.created_at.replace(tzinfo=timezone.utc) if r.created_at.tzinfo is None else r.created_at
            ra = r.resolved_at.replace(tzinfo=timezone.utc) if r.resolved_at.tzinfo is None else r.resolved_at
            h = (ra - ca).total_seconds() / 3600
            hours.append(h)
            if h <= sla_h:
                within += 1
        avg = round(sum(hours) / len(hours), 1)
        sla_by_priority[priority] = {
            "avg_hours": avg,
            "within_sla": round(within / len(rows) * 100),
            "total": len(rows),
            "sla_limit_hours": sla_h,
        }

    # ── Tickets por agente asignado ───────────────────────────────────────────
    agent_rows = (await db.execute(
        select(Ticket.assigned_to, func.count().label("n"))
        .where(Ticket.assigned_to.isnot(None))
        .group_by(Ticket.assigned_to)
        .order_by(func.count().desc())
    )).all()
    tickets_by_agent = {r.assigned_to: r.n for r in agent_rows}

    return {
        "tickets": {
            "total": total_tickets,
            "by_status": ticket_by_status,
            "by_priority": ticket_by_priority,
        },
        "sla": {
            "by_priority": sla_by_priority,
            "tickets_by_agent": tickets_by_agent,
        },
        "accounts": {
            "total": total_accounts,
            "locked": locked_count,
            "by_role": accounts_by_role,
            "by_job_role": accounts_by_job_role,
        },
        "db_access": {
            "total_active": total_active_accesses,
            "expiring_soon": expiring_soon,
            "by_database": active_access_by_db,
            "actions": db_actions,
        },
        "incidents": {
            "total": total_incidents,
            "by_outcome": incidents_by_outcome,
            "top_categories": top_categories,
        },
        "agent": {
            "total_tool_calls": total_tool_calls,
            "top_tools": top_tools,
        },
    }


@router.get("/trend", summary="Tendencia semanal de tickets y accesos BD")
async def get_trend(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """Devuelve tickets y accesos BD creados por semana en las últimas 8 semanas."""
    eight_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=8)

    ticket_rows = (await db.execute(
        select(
            func.date_trunc("week", Ticket.created_at).label("week"),
            func.count().label("n"),
        )
        .where(Ticket.created_at >= eight_weeks_ago)
        .group_by(text("1"))
        .order_by(text("1"))
    )).all()

    access_rows = (await db.execute(
        select(
            func.date_trunc("week", DatabaseAccess.created_at).label("week"),
            func.count().label("n"),
        )
        .where(DatabaseAccess.created_at >= eight_weeks_ago)
        .group_by(text("1"))
        .order_by(text("1"))
    )).all()

    def _label(dt) -> str:
        if hasattr(dt, "tzinfo") and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%d/%m")

    ticket_map = {_label(r.week): r.n for r in ticket_rows}
    access_map = {_label(r.week): r.n for r in access_rows}

    all_weeks = sorted(set(ticket_map) | set(access_map))
    data = [
        {"week": w, "tickets": ticket_map.get(w, 0), "accesses": access_map.get(w, 0)}
        for w in all_weeks
    ]
    return {"weeks": data}

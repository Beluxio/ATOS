from datetime import datetime, UTC
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.ticket import Ticket, TicketResponse

# ── Auto-classification ──────────────────────────────────────

_CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("password",  ["password", "contraseña", "reset", "token", "clave"]),
    ("account",   ["account", "cuenta", "locked", "bloqueada", "acceso", "login", "sesion", "sesión"]),
    ("network",   ["network", "red", "conexión", "conexion", "internet", "dns", "timeout", "conectar"]),
    ("technical", ["error", "bug", "fallo", "crash", "instalación", "instalacion", "install", "dependencia", "excepción"]),
    ("billing",   ["pago", "factura", "billing", "suscripción", "cobro"]),
]

_PRIORITY_KEYWORDS: dict[str, list[str]] = {
    "critical": ["urgente", "crítico", "critico", "caído", "caido", "producción", "produccion", "no puedo acceder", "bloqueado", "bloqueada"],
    "high":     ["error 500", "falla", "importante", "afecta", "varios usuarios"],
    "low":      ["pregunta", "consulta", "información", "informacion", "duda", "cuando"],
}


def _classify(title: str, description: str) -> tuple[str, str, list[str]]:
    text = (title + " " + description).lower()

    category = "other"
    for cat, keywords in _CATEGORY_KEYWORDS:
        if any(kw in text for kw in keywords):
            category = cat
            break

    priority = "medium"
    for prio, keywords in _PRIORITY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            priority = prio
            break

    tags: list[str] = [category]
    if priority in ("critical", "high"):
        tags.append(priority)

    return category, priority, tags


# ── CRUD ─────────────────────────────────────────────────────

async def create_ticket(
    db: AsyncSession,
    title: str,
    description: str,
    user_email: str,
) -> dict:
    category, priority, tags = _classify(title, description)

    ticket = Ticket(
        title=title,
        description=description,
        status="open",
        priority=priority,
        category=category,
        tags=tags,
        user_email=user_email.strip().lower(),
    )
    db.add(ticket)
    await db.flush()

    auto_msg = (
        f"Ticket creado automáticamente. Categoría: {category} | Prioridad: {priority}. "
        "Un agente lo revisará pronto."
    )
    db.add(TicketResponse(ticket_id=ticket.id, content=auto_msg, author="ATOS", is_auto=True))
    await db.commit()
    await db.refresh(ticket)
    return _serialize(ticket)


async def get_ticket(db: AsyncSession, ticket_id: int) -> dict | None:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    return _serialize(ticket) if ticket else None


async def list_tickets(
    db: AsyncSession,
    user_email: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    q = select(Ticket).order_by(Ticket.created_at.desc()).limit(limit)
    if user_email:
        q = q.where(Ticket.user_email == user_email.strip().lower())
    if status:
        q = q.where(Ticket.status == status)
    if priority:
        q = q.where(Ticket.priority == priority)
    result = await db.execute(q)
    return [_serialize(t) for t in result.scalars().all()]


async def update_status(
    db: AsyncSession,
    ticket_id: int,
    new_status: str,
    note: Optional[str] = None,
    author: str = "ATOS",
) -> dict:
    valid = {"open", "in_progress", "resolved", "closed", "escalated"}
    if new_status not in valid:
        return {"status": "error", "message": f"Estado inválido. Usa: {', '.join(valid)}."}

    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        return {"status": "error", "message": f"Ticket #{ticket_id} no encontrado."}

    await db.execute(
        update(Ticket)
        .where(Ticket.id == ticket_id)
        .values(status=new_status, updated_at=datetime.now(UTC))
    )

    content = note or f"Estado actualizado a: {new_status}."
    db.add(TicketResponse(ticket_id=ticket_id, content=content, author=author, is_auto=True))
    await db.commit()
    await db.refresh(ticket)
    return _serialize(ticket)


async def escalate_ticket(
    db: AsyncSession,
    ticket_id: int,
    reason: str,
) -> dict:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        return {"status": "error", "message": f"Ticket #{ticket_id} no encontrado."}

    await db.execute(
        update(Ticket)
        .where(Ticket.id == ticket_id)
        .values(status="escalated", priority="high", updated_at=datetime.now(UTC))
    )
    note = f"Escalado a soporte humano. Motivo: {reason}"
    db.add(TicketResponse(ticket_id=ticket_id, content=note, author="ATOS", is_auto=True))
    await db.commit()
    await db.refresh(ticket)
    return _serialize(ticket)


async def add_response(
    db: AsyncSession,
    ticket_id: int,
    content: str,
    author: str = "ATOS",
    is_auto: bool = False,
) -> dict:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    if not result.scalar_one_or_none():
        return {"status": "error", "message": f"Ticket #{ticket_id} no encontrado."}

    db.add(TicketResponse(ticket_id=ticket_id, content=content, author=author, is_auto=is_auto))
    await db.commit()
    return {"status": "ok", "message": "Respuesta añadida."}


async def find_duplicates(
    db: AsyncSession,
    title: str,
    description: str,
    user_email: str,
    limit: int = 5,
) -> list[dict]:
    """Return open/in_progress tickets from the same user that share keywords with the new one."""
    text_new = (title + " " + description).lower()
    terms = [t for t in text_new.split() if len(t) > 3]

    q = select(Ticket).where(
        Ticket.user_email == user_email.strip().lower(),
        Ticket.status.in_(["open", "in_progress"]),
    ).order_by(Ticket.created_at.desc()).limit(50)
    result = await db.execute(q)
    candidates = result.scalars().all()

    scored = []
    for ticket in candidates:
        blob = (ticket.title + " " + ticket.description).lower()
        score = sum(1 for t in terms if t in blob)
        if score > 0:
            scored.append((score, ticket))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "created_at": t.created_at.isoformat(),
            "similarity_score": score,
        }
        for score, t in scored[:limit]
    ]


# ── Helpers ──────────────────────────────────────────────────

def _serialize(t: Ticket) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "priority": t.priority,
        "category": t.category,
        "tags": t.tags,
        "user_email": t.user_email,
        "assigned_to": t.assigned_to,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
        "responses": [_serialize_response(r) for r in (t.responses or [])],
    }


def _serialize_response(r: TicketResponse) -> dict:
    return {
        "id": r.id,
        "content": r.content,
        "author": r.author,
        "is_auto": r.is_auto,
        "created_at": r.created_at.isoformat(),
    }

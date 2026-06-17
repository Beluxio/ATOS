import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.auth import decode_token
from app.models.ticket import Ticket
from app.models.database_access import DatabaseAccess

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/notifications", tags=["notifications"])

POLL_INTERVAL = 15  # segundos entre cada chequeo


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _event_generator(request: Request, since: datetime):
    last_ticket_check = since
    last_access_check = since

    try:
        yield _sse("connected", {"message": "Conectado a notificaciones ATOS"})

        while True:
            if await request.is_disconnected():
                break

            now = datetime.now(timezone.utc)
            events = []

            async with AsyncSessionLocal() as db:
                # Tickets nuevos
                new_tickets = (await db.execute(
                    select(Ticket).where(Ticket.created_at > last_ticket_check)
                    .order_by(Ticket.created_at.desc())
                )).scalars().all()

                for t in new_tickets:
                    events.append(_sse("new_ticket", {
                        "id": t.id,
                        "title": t.title,
                        "priority": t.priority,
                        "created_by": t.user_email,
                    }))
                if new_tickets:
                    last_ticket_check = now

                # Accesos por vencer o recién expirados/revocados
                expiring = (await db.execute(
                    select(DatabaseAccess).where(
                        DatabaseAccess.status == "active",
                        DatabaseAccess.expires_at.isnot(None),
                        DatabaseAccess.expiry_warning_sent == True,  # noqa: E712
                        DatabaseAccess.updated_at > last_access_check,
                    )
                )).scalars().all()

                for a in expiring:
                    exp = a.expires_at.replace(tzinfo=timezone.utc) if a.expires_at.tzinfo is None else a.expires_at
                    days_left = max(0, (exp - now).days)
                    events.append(_sse("expiring_access", {
                        "user_email": a.user_email,
                        "database_name": a.database_name,
                        "days_left": days_left,
                    }))

                recently_revoked = (await db.execute(
                    select(DatabaseAccess).where(
                        DatabaseAccess.status.in_(["revoked", "expired"]),
                        DatabaseAccess.updated_at > last_access_check,
                    )
                )).scalars().all()

                for a in recently_revoked:
                    events.append(_sse("access_revoked", {
                        "user_email": a.user_email,
                        "database_name": a.database_name,
                        "status": a.status,
                    }))

                if expiring or recently_revoked:
                    last_access_check = now

            for event in events:
                yield event

            await asyncio.sleep(POLL_INTERVAL)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error("SSE error: %s", e)


@router.get("/stream", summary="Stream de notificaciones en tiempo real (SSE)")
async def notification_stream(
    request: Request,
    token: str = Query(..., description="JWT token (EventSource no soporta headers)"),
):
    """
    Abre un stream SSE que envía notificaciones en tiempo real.
    El token se pasa como query param porque `EventSource` del browser no admite headers.
    Escucha eventos: `connected`, `new_ticket`, `expiring_access`, `access_revoked`.
    """
    try:
        decode_token(token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
        )

    since = datetime.now(timezone.utc)
    return StreamingResponse(
        _event_generator(request, since),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

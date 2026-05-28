from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import ticket_service as svc

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


class CreateTicketBody(BaseModel):
    title: str
    description: str
    user_email: EmailStr


class UpdateStatusBody(BaseModel):
    new_status: str
    note: Optional[str] = None


class AddResponseBody(BaseModel):
    content: str
    author: Optional[str] = "Agente"


@router.post("")
async def create_ticket(body: CreateTicketBody, db: AsyncSession = Depends(get_db)):
    return await svc.create_ticket(db, body.title, body.description, body.user_email)


@router.get("")
async def list_tickets(
    user_email: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_tickets(db, user_email, status, priority, limit)


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    ticket = await svc.get_ticket(db, ticket_id)
    if not ticket:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Ticket no encontrado.")
    return ticket


@router.patch("/{ticket_id}/status")
async def update_status(ticket_id: int, body: UpdateStatusBody, db: AsyncSession = Depends(get_db)):
    return await svc.update_status(db, ticket_id, body.new_status, body.note, author="Panel")


@router.post("/{ticket_id}/responses")
async def add_response(ticket_id: int, body: AddResponseBody, db: AsyncSession = Depends(get_db)):
    return await svc.add_response(db, ticket_id, body.content, body.author or "Agente", is_auto=False)


@router.post("/{ticket_id}/escalate")
async def escalate(ticket_id: int, db: AsyncSession = Depends(get_db)):
    return await svc.escalate_ticket(db, ticket_id, "Escalado manualmente desde el panel.")

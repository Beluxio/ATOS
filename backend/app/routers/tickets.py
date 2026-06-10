from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import ticket_service as svc

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


class CreateTicketBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "title": "Error al instalar dependencias npm",
            "description": "Al correr `npm install` aparece el error ENOENT en node_modules.",
            "user_email": "dev@empresa.com",
        }
    })
    title: str
    description: str
    user_email: EmailStr


class UpdateStatusBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"new_status": "in_progress", "note": "Asignado al equipo de infraestructura."}
    })
    new_status: str
    note: Optional[str] = None


class AddResponseBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"content": "Se identificó el problema. Limpia la caché con `npm cache clean --force`.", "author": "Agente"}
    })
    content: str
    author: Optional[str] = "Agente"


@router.post("", summary="Crear ticket")
async def create_ticket(body: CreateTicketBody, db: AsyncSession = Depends(get_db)):
    """
    Crea un nuevo ticket de soporte.

    - El agente verifica duplicados antes de crear (recomendado usar el chat para este flujo).
    - Estados posibles tras crear: `open`.
    - Prioridades asignadas automáticamente: `low`, `medium`, `high`, `critical`.
    """
    return await svc.create_ticket(db, body.title, body.description, body.user_email)


@router.get("", summary="Listar tickets")
async def list_tickets(
    user_email: Optional[str] = Query(None, description="Filtrar por email del usuario", example="dev@empresa.com"),
    status: Optional[str] = Query(None, description="Filtrar por estado: open, in_progress, resolved, closed", example="open"),
    priority: Optional[str] = Query(None, description="Filtrar por prioridad: low, medium, high, critical", example="high"),
    limit: int = Query(50, ge=1, le=200, description="Máximo de resultados a devolver"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista tickets con filtros opcionales por email, estado y prioridad.

    - Sin filtros devuelve los últimos 50 tickets.
    - Combina filtros: `?status=open&priority=high` devuelve tickets abiertos y urgentes.
    """
    return await svc.list_tickets(db, user_email, status, priority, limit)


@router.get("/{ticket_id}", summary="Obtener ticket")
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    """
    Devuelve el detalle completo de un ticket, incluyendo sus respuestas y el historial de cambios.

    - Devuelve 404 si el ticket no existe.
    """
    ticket = await svc.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado.")
    return ticket


@router.patch("/{ticket_id}/status", summary="Actualizar estado del ticket")
async def update_status(ticket_id: int, body: UpdateStatusBody, db: AsyncSession = Depends(get_db)):
    """
    Cambia el estado de un ticket y opcionalmente agrega una nota al historial.

    - Estados válidos: `open`, `in_progress`, `resolved`, `closed`.
    - La nota queda registrada en el historial del ticket.
    """
    return await svc.update_status(db, ticket_id, body.new_status, body.note, author="Panel")


@router.post("/{ticket_id}/responses", summary="Agregar respuesta al ticket")
async def add_response(ticket_id: int, body: AddResponseBody, db: AsyncSession = Depends(get_db)):
    """
    Agrega una respuesta o comentario a un ticket existente.

    - `author` identifica quién responde (por defecto `Agente`).
    - La respuesta queda visible en el historial del ticket.
    """
    return await svc.add_response(db, ticket_id, body.content, body.author or "Agente", is_auto=False)


@router.post("/{ticket_id}/escalate", summary="Escalar ticket")
async def escalate(ticket_id: int, db: AsyncSession = Depends(get_db)):
    """
    Escala un ticket aumentando su prioridad y marcándolo para atención urgente.

    - Cambia la prioridad a `critical` y el estado a `escalated`.
    - Registra la escalación en el historial.
    """
    return await svc.escalate_ticket(db, ticket_id, "Escalado manualmente desde el panel.")

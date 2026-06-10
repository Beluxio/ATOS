import logging
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user_optional
from app.schemas.chat import ChatRequest, ChatResponse
from app.agent import agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse, summary="Enviar mensaje al agente")
async def chat_endpoint(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Envía un mensaje al agente ATOS y recibe una respuesta.

    - La autenticación es opcional — sin token el agente opera en modo anónimo con capacidades limitadas.
    - `session_id` identifica la conversación; usa el mismo valor para mantener el contexto entre mensajes.
    - `history` es la lista de mensajes previos devuelta por el agente en turnos anteriores; envíala de vuelta para que el agente recuerde el contexto.
    - Ejemplo de flujo: primer mensaje → `history: []`; siguientes mensajes → reenvía el `history` de la respuesta anterior.
    """
    user_email = current_user.get("sub") if current_user else None
    user_role = current_user.get("role") if current_user else None

    try:
        reply, updated_history = await agent.chat(
            message=body.message,
            history=body.history,
            db=db,
            session_id=body.session_id,
            user_email=user_email,
            user_role=user_role,
        )
        return ChatResponse(
            reply=reply,
            session_id=body.session_id,
            history=updated_history,
            user_email=user_email,
            user_role=user_role,
        )
    except Exception:
        logger.exception("Unexpected error in chat endpoint")
        return ChatResponse(
            reply="⚠️ Error interno del servidor. Revisa los logs con: docker logs atos-api-1",
            session_id=body.session_id,
            history=body.history,
        )

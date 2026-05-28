import logging
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from groq import APIStatusError

from app.core.database import get_db
from app.core.auth import get_current_user_optional
from app.schemas.chat import ChatRequest, ChatResponse
from app.agent import agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


def _groq_error_msg(e: APIStatusError) -> str:
    raw = str(e)
    if e.status_code == 429:
        return "⚠️ Límite de requests de Groq alcanzado. Espera unos segundos e intenta de nuevo."
    if e.status_code == 401:
        return "⚠️ GROQ_API_KEY inválida. Actualízala en .env y reinicia con: docker-compose up -d --force-recreate api"
    return f"⚠️ Error de la API de Groq ({e.status_code}): {raw[:200]}"


@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
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
    except APIStatusError as e:
        logger.error("Groq APIStatusError %s: %s", e.status_code, e)
        return ChatResponse(
            reply=_groq_error_msg(e),
            session_id=body.session_id,
            history=body.history,
        )
    except Exception:
        logger.exception("Unexpected error in chat endpoint")
        return ChatResponse(
            reply="⚠️ Error interno del servidor. Revisa los logs con: docker logs atos-api-1",
            session_id=body.session_id,
            history=body.history,
        )

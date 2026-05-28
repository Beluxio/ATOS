from pydantic import BaseModel
from typing import Any, Optional


class ChatRequest(BaseModel):
    message: str
    session_id: str
    history: list[dict[str, Any]] = []


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    history: list[dict[str, Any]]
    user_email: Optional[str] = None
    user_role: Optional[str] = None

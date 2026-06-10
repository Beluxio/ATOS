from pydantic import BaseModel, ConfigDict
from typing import Any, Optional


class ChatRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "message": "Necesito resetear la contraseña de usuario@empresa.com",
            "session_id": "sesion-001",
            "history": [],
        }
    })
    message: str
    session_id: str
    history: list[dict[str, Any]] = []


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    history: list[dict[str, Any]]
    user_email: Optional[str] = None
    user_role: Optional[str] = None

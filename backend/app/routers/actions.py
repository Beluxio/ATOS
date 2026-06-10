from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, Optional
from app.core.auth import get_current_user, require_role
from app.agent.tools.automated_actions import (
    generate_report,
    execute_allowed_action,
    ALLOWED_ACTIONS,
    ALLOWED_REPORT_TYPES,
)

router = APIRouter(prefix="/api/actions", tags=["actions"])


class GenerateReportBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "report_type": "tickets",
            "filters": {"status": "open", "priority": "high"},
        }
    })
    report_type: str = "tickets"
    filters: Optional[Dict[str, Any]] = {}


class ExecuteActionBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "action_name": "restart_session",
            "params": {"user_email": "usuario@empresa.com"},
            "confirmed": True,
        }
    })
    action_name: str
    params: Optional[Dict[str, Any]] = {}
    confirmed: bool = False


@router.get("/available", summary="Listar acciones disponibles")
async def list_available_actions(current_user: dict = Depends(get_current_user)):
    """
    Devuelve las acciones automatizadas y tipos de reporte disponibles en el sistema.

    - Requiere autenticación.
    - Útil para conocer qué se puede ejecutar antes de llamar a `/execute` o `/report`.
    """
    return {
        "actions": sorted(ALLOWED_ACTIONS),
        "report_types": sorted(ALLOWED_REPORT_TYPES),
    }


@router.post("/report", summary="Generar reporte")
async def post_generate_report(
    body: GenerateReportBody,
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    Genera un reporte del sistema según el tipo y filtros indicados.

    - Requiere rol `agent` o `admin`.
    - Tipos de reporte disponibles: ver `GET /api/actions/available`.
    - Ejemplo: tipo `tickets` con filtro `{"status": "open"}` devuelve todos los tickets abiertos.
    """
    return await generate_report({"report_type": body.report_type, "filters": body.filters or {}})


@router.post("/execute", summary="Ejecutar acción automatizada")
async def post_execute_action(
    body: ExecuteActionBody,
    current_user: dict = Depends(require_role("admin")),
):
    """
    Ejecuta una acción automatizada permitida en el sistema.

    - Requiere rol `admin`.
    - **`confirmed` debe ser `true`** para que la acción se ejecute; en `false` solo simula.
    - Acciones disponibles: ver `GET /api/actions/available`.
    - Ejemplo: `restart_session` cierra la sesión activa de un usuario.
    """
    return await execute_allowed_action({
        "action_name": body.action_name,
        "params": body.params or {},
        "confirmed": body.confirmed,
    })

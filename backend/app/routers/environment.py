from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from app.core.auth import get_current_user
from app.agent.tools.environment import (
    generate_environment_report,
    check_tool_installed,
    check_minimum_requirements,
    ALLOWED_TOOLS,
)

router = APIRouter(prefix="/api/environment", tags=["environment"])


class CheckRequirementsBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"requirements": ["node", "python", "docker", "git"]}
    })
    requirements: Optional[List[str]] = None


@router.get("/report", summary="Reporte del entorno")
async def get_environment_report(current_user: dict = Depends(get_current_user)):
    """
    Genera un reporte completo del entorno de desarrollo: herramientas instaladas, versiones y rutas.

    - Requiere autenticación.
    - Detecta: Node.js, Python, Docker, Git, npm, pip, entre otros.
    """
    return await generate_environment_report({})


@router.get("/tool/{tool_name}", summary="Verificar herramienta instalada")
async def get_tool_status(tool_name: str, current_user: dict = Depends(get_current_user)):
    """
    Verifica si una herramienta específica está instalada y devuelve su versión.

    - Requiere autenticación.
    - Herramientas soportadas: `node`, `python`, `docker`, `git`, `npm`, `pip`, `yarn`, etc.
    - Ejemplo: `GET /api/environment/tool/docker`
    """
    return await check_tool_installed({"tool_name": tool_name})


@router.post("/check-requirements", summary="Verificar requisitos mínimos")
async def post_check_requirements(
    body: CheckRequirementsBody,
    current_user: dict = Depends(get_current_user),
):
    """
    Verifica si una lista de herramientas están instaladas y cumplen los requisitos mínimos.

    - Requiere autenticación.
    - Si `requirements` se omite, verifica todas las herramientas permitidas del sistema.
    - Útil para onboarding de nuevos desarrolladores.
    """
    requirements = body.requirements or list(ALLOWED_TOOLS)
    return await check_minimum_requirements({"requirements": requirements})

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import get_current_user
from app.core.database import get_db
from app.services.memory_service import search_incidents, get_stats, save_incident

router = APIRouter(prefix="/api/history", tags=["history"])


class SaveIncidentBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "description": "Usuario no podía conectarse a VPN por conflicto de DNS.",
            "solution_used": "Se cambió el servidor DNS a 8.8.8.8 en la configuración de red.",
            "outcome": "resolved",
            "ticket_id": 42,
            "category": "red",
            "tags": ["vpn", "dns", "red"],
        }
    })
    description: str
    solution_used: str
    outcome: str = "resolved"
    ticket_id: Optional[int] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


@router.get("/stats", summary="Estadísticas del historial")
async def history_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Devuelve estadísticas globales del historial de incidencias.

    - Requiere autenticación.
    - Incluye: total de incidencias, categorías más frecuentes, tasa de resolución.
    """
    return await get_stats(db)


@router.get("/search", summary="Buscar en historial de incidencias")
async def search_history(
    q: str = Query(..., min_length=2, description="Texto a buscar en descripciones y soluciones", example="vpn dns"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Busca incidencias anteriores en el historial por texto.

    - Requiere autenticación.
    - Útil para encontrar soluciones aplicadas previamente a problemas similares.
    - Ejemplo: `?q=npm install error` devuelve incidencias relacionadas.
    """
    results = await search_incidents(db, q)
    return {"query": q, "count": len(results), "results": results}


@router.post("/save", summary="Guardar incidencia en historial")
async def save_incident_endpoint(
    body: SaveIncidentBody,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Guarda una incidencia resuelta en el historial para referencia futura.

    - Requiere autenticación.
    - `outcome` puede ser: `resolved`, `escalated`, `unresolved`.
    - `ticket_id` es opcional — vincula la incidencia a un ticket existente.
    - Los `tags` permiten búsquedas y agrupaciones más precisas.
    """
    return await save_incident(
        db,
        description=body.description,
        solution_used=body.solution_used,
        outcome=body.outcome,
        ticket_id=body.ticket_id,
        category=body.category,
        tags=body.tags,
    )

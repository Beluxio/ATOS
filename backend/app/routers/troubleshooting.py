from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import troubleshooting_service as svc

router = APIRouter(prefix="/api/troubleshooting", tags=["troubleshooting"])


@router.get("", summary="Listar flujos de troubleshooting")
async def list_flows(
    category: Optional[str] = Query(None, description="Filtrar por categoría, ej: red, docker, npm", example="docker"),
    db: AsyncSession = Depends(get_db),
):
    """
    Devuelve todos los flujos de diagnóstico disponibles, opcionalmente filtrados por categoría.

    - Cada flujo contiene pasos ordenados para resolver un tipo de problema.
    """
    return await svc.list_flows(db, category)


@router.get("/search", summary="Buscar flujos de troubleshooting")
async def search_flows(
    q: str = Query(..., min_length=2, description="Texto a buscar en los flujos", example="contenedor no inicia"),
    db: AsyncSession = Depends(get_db),
):
    """
    Busca flujos de troubleshooting por texto.

    - Ejemplo: `?q=contenedor no inicia` devuelve flujos relacionados con Docker.
    """
    return await svc.search_flows(db, q)


@router.get("/identify", summary="Identificar error")
async def identify(
    error: str = Query(..., min_length=3, description="Mensaje o código de error", example="ECONNREFUSED 127.0.0.1:5432"),
    db: AsyncSession = Depends(get_db),
):
    """
    Analiza un mensaje de error y sugiere flujos de resolución relacionados.

    - Pasa el error exacto del log o terminal para mejores resultados.
    - Ejemplo: `?error=ModuleNotFoundError: No module named 'fastapi'`
    """
    return await svc.identify_error(db, error)


@router.get("/{flow_id}", summary="Obtener flujo de troubleshooting")
async def get_flow(flow_id: int, db: AsyncSession = Depends(get_db)):
    """
    Devuelve el detalle completo de un flujo de troubleshooting por su ID, incluyendo todos sus pasos.

    - Devuelve 404 si el flujo no existe.
    """
    flow = await svc.get_flow(db, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flujo no encontrado.")
    return flow

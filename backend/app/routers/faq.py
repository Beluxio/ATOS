from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import faq_service as svc

router = APIRouter(prefix="/api/faq", tags=["faq"])


@router.get("", summary="Listar preguntas frecuentes")
async def list_faq(
    category: Optional[str] = Query(None, description="Filtrar por categoría, ej: red, software, acceso", example="red"),
    db: AsyncSession = Depends(get_db),
):
    """
    Devuelve todas las entradas del FAQ, opcionalmente filtradas por categoría.

    - Sin `category` devuelve todo el FAQ.
    - Las categorías disponibles dependen de los datos cargados en la base de datos.
    """
    return await svc.list_all(db, category)


@router.get("/search", summary="Buscar en el FAQ")
async def search_faq(
    q: str = Query(..., min_length=2, description="Texto a buscar en título y contenido", example="vpn no conecta"),
    limit: int = Query(8, ge=1, le=20, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_db),
):
    """
    Busca entradas del FAQ que coincidan con el texto indicado.

    - Busca en el título y el cuerpo del artículo.
    - Ejemplo: `?q=vpn no conecta` devuelve artículos relacionados con VPN.
    """
    return await svc.search(db, q, limit)


@router.get("/{faq_id}", summary="Obtener artículo del FAQ")
async def get_faq(faq_id: int, db: AsyncSession = Depends(get_db)):
    """
    Devuelve el contenido completo de un artículo del FAQ por su ID.

    - Devuelve 404 si el artículo no existe.
    """
    item = await svc.get_item(db, faq_id)
    if not item:
        raise HTTPException(status_code=404, detail="FAQ no encontrada.")
    return item


@router.post("/{faq_id}/helpful", summary="Marcar artículo como útil")
async def mark_helpful(faq_id: int, db: AsyncSession = Depends(get_db)):
    """
    Registra que el artículo fue útil para el usuario (incrementa el contador de votos positivos).

    - Se usa para medir la efectividad del FAQ.
    """
    return await svc.mark_helpful(db, faq_id)

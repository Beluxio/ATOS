from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import faq_service as svc

router = APIRouter(prefix="/api/faq", tags=["faq"])


@router.get("")
async def list_faq(
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_all(db, category)


@router.get("/search")
async def search_faq(
    q: str = Query(..., min_length=2),
    limit: int = Query(8, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    return await svc.search(db, q, limit)


@router.get("/{faq_id}")
async def get_faq(faq_id: int, db: AsyncSession = Depends(get_db)):
    item = await svc.get_item(db, faq_id)
    if not item:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="FAQ no encontrada.")
    return item


@router.post("/{faq_id}/helpful")
async def mark_helpful(faq_id: int, db: AsyncSession = Depends(get_db)):
    return await svc.mark_helpful(db, faq_id)

from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import troubleshooting_service as svc

router = APIRouter(prefix="/api/troubleshooting", tags=["troubleshooting"])


@router.get("")
async def list_flows(
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_flows(db, category)


@router.get("/search")
async def search_flows(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
):
    return await svc.search_flows(db, q)


@router.get("/identify")
async def identify(
    error: str = Query(..., min_length=3),
    db: AsyncSession = Depends(get_db),
):
    return await svc.identify_error(db, error)


@router.get("/{flow_id}")
async def get_flow(flow_id: int, db: AsyncSession = Depends(get_db)):
    flow = await svc.get_flow(db, flow_id)
    if not flow:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Flujo no encontrado.")
    return flow

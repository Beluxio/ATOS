from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import get_current_user
from app.core.database import get_db
from app.services.memory_service import search_incidents, get_stats, save_incident

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/stats")
async def history_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_stats(db)


@router.get("/search")
async def search_history(
    q: str = Query(..., min_length=2),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    results = await search_incidents(db, q)
    return {"query": q, "count": len(results), "results": results}


@router.post("/save")
async def save_incident_endpoint(
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await save_incident(
        db,
        description=body.get("description", ""),
        solution_used=body.get("solution_used", ""),
        outcome=body.get("outcome", "resolved"),
        ticket_id=body.get("ticket_id"),
        category=body.get("category"),
        tags=body.get("tags"),
    )

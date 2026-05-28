from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import account_service as svc

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


class RegisterBody(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: Optional[str] = "user"


@router.post("/register")
async def register(body: RegisterBody, db: AsyncSession = Depends(get_db)):
    return await svc.register(db, body.email, body.username, body.password, body.role or "user")


@router.get("")
async def list_accounts(db: AsyncSession = Depends(get_db)):
    return await svc.list_accounts(db)


@router.get("/{email}/status")
async def get_status(email: str, db: AsyncSession = Depends(get_db)):
    return await svc.check_status(db, email)


@router.post("/{email}/unlock")
async def unlock(email: str, db: AsyncSession = Depends(get_db)):
    return await svc.unlock(db, email)


@router.post("/{email}/lock")
async def lock(email: str, db: AsyncSession = Depends(get_db)):
    return await svc.lock(db, email)

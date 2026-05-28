from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import password_reset_service as svc

router = APIRouter(prefix="/api/reset-password", tags=["reset-password"])


class RequestBody(BaseModel):
    email: EmailStr


class ConfirmBody(BaseModel):
    token: str
    new_password: str


@router.post("/request")
async def request_reset(body: RequestBody, db: AsyncSession = Depends(get_db)):
    return await svc.request_reset(db, body.email)


@router.post("/validate")
async def validate_token(body: dict, db: AsyncSession = Depends(get_db)):
    return await svc.validate_token(db, body["token"])


@router.post("/confirm")
async def confirm_reset(body: ConfirmBody, db: AsyncSession = Depends(get_db)):
    return await svc.confirm_reset(db, body.token, body.new_password)

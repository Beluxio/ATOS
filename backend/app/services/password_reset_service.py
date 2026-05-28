import hashlib
import secrets
from datetime import datetime, timedelta, UTC

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.password_reset_token import PasswordResetToken

TOKEN_TTL_MINUTES = 15


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def request_reset(db: AsyncSession, email: str) -> dict:
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = datetime.now(UTC) + timedelta(minutes=TOKEN_TTL_MINUTES)

    db.add(PasswordResetToken(email=email, token_hash=token_hash, expires_at=expires_at))
    await db.commit()

    from app.core.email import send_password_reset_email
    email_sent = await send_password_reset_email(email, token, TOKEN_TTL_MINUTES)

    return {
        "status": "ok",
        "message": f"Token de reset generado para {email}. Válido por {TOKEN_TTL_MINUTES} minutos.",
        "token": token,
        "expires_at": expires_at.isoformat(),
        "email_sent": email_sent,
        "note": "Muestra este token directamente al usuario en el chat." if not email_sent else f"Email enviado a {email}.",
    }


async def validate_token(db: AsyncSession, token: str) -> dict:
    token_hash = _hash_token(token)
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    record = result.scalar_one_or_none()

    if not record:
        return {"valid": False, "reason": "Token no encontrado."}
    if record.used:
        return {"valid": False, "reason": "El token ya fue utilizado."}
    if datetime.now(UTC) > record.expires_at.replace(tzinfo=UTC):
        return {"valid": False, "reason": "El token ha expirado."}

    return {"valid": True, "email": record.email}


async def confirm_reset(db: AsyncSession, token: str, new_password: str) -> dict:
    from app.services import account_service

    validation = await validate_token(db, token)
    if not validation["valid"]:
        return {"status": "error", "message": validation["reason"]}

    if len(new_password) < 8:
        return {"status": "error", "message": "La contraseña debe tener al menos 8 caracteres."}

    token_hash = _hash_token(token)
    await db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.token_hash == token_hash)
        .values(used=True)
    )

    await account_service.update_password(db, validation["email"], new_password)
    await db.commit()

    return {
        "status": "ok",
        "message": f"Contraseña actualizada correctamente para {validation['email']}.",
    }

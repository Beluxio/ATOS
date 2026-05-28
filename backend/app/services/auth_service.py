import hashlib
from datetime import datetime, timedelta, UTC

import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.account import Account
from app.core.auth import create_access_token

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    # Support legacy sha256 hashes from before bcrypt migration
    if len(hashed) == 64 and all(c in "0123456789abcdef" for c in hashed):
        return hashlib.sha256(plain.encode()).hexdigest() == hashed
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def _norm(email: str) -> str:
    return email.strip().lower()


async def login(db: AsyncSession, email: str, password: str) -> dict:
    email = _norm(email)
    result = await db.execute(select(Account).where(Account.email == email))
    account = result.scalar_one_or_none()

    if not account:
        return {"status": "error", "message": "Email o contraseña incorrectos."}

    # Check manual lock (status field)
    if account.status == "locked":
        return {"status": "error", "message": "Esta cuenta está bloqueada. Contacta a soporte."}

    # Check rate-limit lockout
    now = datetime.now(UTC)
    if account.locked_until and account.locked_until > now:
        remaining = int((account.locked_until - now).total_seconds() / 60) + 1
        return {
            "status": "error",
            "message": f"Cuenta bloqueada temporalmente por intentos fallidos. Intenta en {remaining} min.",
        }

    # Verify password
    if not verify_password(password, account.hashed_password):
        new_attempts = account.failed_login_attempts + 1
        values: dict = {"failed_login_attempts": new_attempts, "updated_at": now}

        if new_attempts >= MAX_FAILED_ATTEMPTS:
            values["locked_until"] = now + timedelta(minutes=LOCKOUT_MINUTES)
            await db.execute(update(Account).where(Account.email == email).values(**values))
            await db.commit()
            return {
                "status": "error",
                "message": f"Demasiados intentos fallidos. Cuenta bloqueada por {LOCKOUT_MINUTES} minutos.",
            }

        await db.execute(update(Account).where(Account.email == email).values(**values))
        await db.commit()
        left = MAX_FAILED_ATTEMPTS - new_attempts
        return {"status": "error", "message": f"Email o contraseña incorrectos. Intentos restantes: {left}."}

    # Success — reset failed attempts and locked_until
    await db.execute(
        update(Account)
        .where(Account.email == email)
        .values(failed_login_attempts=0, locked_until=None, updated_at=now)
    )
    await db.commit()

    token = create_access_token(account.email, account.role)
    return {
        "status": "ok",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": account.email,
            "username": account.username,
            "role": account.role,
        },
    }

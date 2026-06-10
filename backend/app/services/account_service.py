from datetime import datetime, UTC

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.account import Account
from app.services.auth_service import hash_password, verify_password


def _norm(email: str) -> str:
    return email.strip().lower()


def _by_email(email: str):
    return Account.email == _norm(email)


async def register(db: AsyncSession, email: str, username: str, password: str, role: str = "user") -> dict:
    email = _norm(email)
    existing = await db.execute(select(Account).where(_by_email(email)))
    if existing.scalar_one_or_none():
        return {"status": "error", "message": f"Ya existe una cuenta con el email {email}."}

    if len(password) < 6:
        return {"status": "error", "message": "La contraseña debe tener al menos 6 caracteres."}

    if role not in ("user", "agent", "admin"):
        role = "user"

    account = Account(
        email=email,
        username=username,
        hashed_password=hash_password(password),
        status="active",
        role=role,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)

    return {
        "status": "ok",
        "message": f"Cuenta creada exitosamente para {username} ({email}).",
        "account": _serialize(account),
    }


async def list_accounts(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Account).order_by(Account.created_at.desc()))
    return [_serialize(a) for a in result.scalars().all()]


async def get_by_email(db: AsyncSession, email: str) -> dict | None:
    result = await db.execute(select(Account).where(_by_email(email)))
    account = result.scalar_one_or_none()
    return _serialize(account) if account else None


async def check_status(db: AsyncSession, email: str) -> dict:
    result = await db.execute(select(Account).where(_by_email(email)))
    account = result.scalar_one_or_none()
    if not account:
        return {"found": False, "message": f"No existe ninguna cuenta con el email {_norm(email)}."}
    return {"found": True, "account": _serialize(account)}


async def unlock(db: AsyncSession, email: str) -> dict:
    email = _norm(email)
    result = await db.execute(select(Account).where(_by_email(email)))
    account = result.scalar_one_or_none()
    if not account:
        return {"status": "error", "message": f"No existe cuenta con email {email}."}
    if account.status == "active" and not account.locked_until:
        return {"status": "info", "message": f"La cuenta {email} ya está activa."}

    await db.execute(
        update(Account).where(_by_email(email))
        .values(status="active", failed_login_attempts=0, locked_until=None, updated_at=datetime.now(UTC))
    )
    await db.commit()
    return {"status": "ok", "message": f"Cuenta {email} desbloqueada correctamente."}


async def lock(db: AsyncSession, email: str, reason: str = "Bloqueada por soporte") -> dict:
    email = _norm(email)
    result = await db.execute(select(Account).where(_by_email(email)))
    account = result.scalar_one_or_none()
    if not account:
        return {"status": "error", "message": f"No existe cuenta con email {email}."}

    await db.execute(
        update(Account).where(_by_email(email))
        .values(status="locked", updated_at=datetime.now(UTC))
    )
    await db.commit()
    return {"status": "ok", "message": f"Cuenta {email} bloqueada. Motivo: {reason}"}


async def update_password(db: AsyncSession, email: str, new_password: str) -> dict:
    email = _norm(email)
    result = await db.execute(select(Account).where(_by_email(email)))
    account = result.scalar_one_or_none()
    if not account:
        return {"status": "error", "message": f"No existe cuenta con email {email}."}

    await db.execute(
        update(Account).where(_by_email(email))
        .values(hashed_password=hash_password(new_password), updated_at=datetime.now(UTC))
    )
    await db.commit()
    return {"status": "ok", "message": f"Contraseña actualizada para {email}."}


async def update_job_role(db: AsyncSession, email: str, job_role: str | None) -> dict:
    from app.core.job_role_policy import JOB_ROLES
    if job_role and job_role not in JOB_ROLES:
        return {"status": "error", "message": f"Job role inválido. Opciones: {', '.join(JOB_ROLES)}"}
    email = _norm(email)
    result = await db.execute(select(Account).where(_by_email(email)))
    if not result.scalar_one_or_none():
        return {"status": "error", "message": f"No existe cuenta con email {email}."}
    await db.execute(
        update(Account).where(_by_email(email))
        .values(job_role=job_role, updated_at=datetime.now(UTC))
    )
    await db.commit()
    label = job_role or "ninguno"
    return {"status": "ok", "message": f"Job role de {email} actualizado a '{label}'."}


async def update_role(db: AsyncSession, email: str, new_role: str) -> dict:
    if new_role not in ("user", "agent", "admin"):
        return {"status": "error", "message": "Rol inválido. Usa: user, agent, admin."}
    email = _norm(email)
    result = await db.execute(select(Account).where(_by_email(email)))
    if not result.scalar_one_or_none():
        return {"status": "error", "message": f"No existe cuenta con email {email}."}

    await db.execute(
        update(Account).where(_by_email(email))
        .values(role=new_role, updated_at=datetime.now(UTC))
    )
    await db.commit()
    return {"status": "ok", "message": f"Rol de {email} cambiado a {new_role}."}


def _serialize(a: Account) -> dict:
    return {
        "id": a.id,
        "email": a.email,
        "username": a.username,
        "status": a.status,
        "role": a.role,
        "job_role": a.job_role,
        "failed_login_attempts": a.failed_login_attempts,
        "locked_until": a.locked_until.isoformat() if a.locked_until else None,
        "created_at": a.created_at.isoformat(),
        "updated_at": a.updated_at.isoformat(),
    }

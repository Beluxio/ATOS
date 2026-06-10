import secrets
import string
from datetime import datetime, timedelta, UTC

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.database_access import DatabaseAccess
from app.models.database_access_log import DatabaseAccessLog
from app.core.job_role_policy import can_access_database, get_allowed_databases, JOB_ROLE_LABELS


async def _log(db: AsyncSession, access_id: int | None, user_email: str,
               database_name: str, action: str, performed_by: str | None = None,
               details: str | None = None) -> None:
    db.add(DatabaseAccessLog(
        access_id=access_id, user_email=user_email, database_name=database_name,
        action=action, performed_by=performed_by, details=details,
    ))

ALLOWED_DATABASES = {"DataCo Analytics", "Data Warehouse", "Reporting DB"}
DEFAULT_EXPIRY_DAYS = 30
WARNING_DAYS = 7  # aviso cuando quedan menos de 7 días


def _generate_password(length: int = 14) -> str:
    chars = string.ascii_letters + string.digits + "!@#$"
    return "".join(secrets.choice(chars) for _ in range(length))


def _generate_username(user_email: str, database_name: str) -> str:
    user_part = user_email.split("@")[0].replace(".", "_").lower()
    db_part = database_name.replace(" ", "_").lower()[:6]
    return f"{user_part}_{db_part}"


def _serialize(a: DatabaseAccess) -> dict:
    now = datetime.now(UTC)
    expires_at = a.expires_at
    days_left: int | None = None
    if expires_at:
        exp = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=UTC)
        days_left = max(0, (exp - now).days)

    return {
        "id": a.id,
        "user_email": a.user_email,
        "database_name": a.database_name,
        "db_username": a.db_username,
        "db_password": a.db_password,
        "status": a.status,
        "granted_by": a.granted_by,
        "notes": a.notes,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "days_left": days_left,
        "expiring_soon": days_left is not None and 0 < days_left <= WARNING_DAYS,
        "created_at": a.created_at.isoformat(),
        "updated_at": a.updated_at.isoformat(),
    }


async def expire_check(db: AsyncSession) -> dict:
    """Revoca accesos vencidos y notifica a los usuarios. Llamar periódicamente."""
    now = datetime.now(UTC)
    result = await db.execute(
        select(DatabaseAccess).where(
            DatabaseAccess.status == "active",
            DatabaseAccess.expires_at.isnot(None),
            DatabaseAccess.expires_at <= now,
        )
    )
    expired = result.scalars().all()

    from app.core.email import send_expiry_email
    revoked = []
    for record in expired:
        await db.execute(
            update(DatabaseAccess).where(DatabaseAccess.id == record.id)
            .values(status="expired", updated_at=now)
        )
        await _log(db, record.id, record.user_email, record.database_name,
                   "expired", "sistema", "Revocado automáticamente por expiración")
        await send_expiry_email(record.user_email, record.database_name)
        revoked.append({"id": record.id, "user_email": record.user_email, "database_name": record.database_name})

    if revoked:
        await db.commit()

    return {"expired_count": len(revoked), "revoked": revoked}


async def grant_access(
    db: AsyncSession, user_email: str, database_name: str,
    granted_by: str | None = None, days: int | None = DEFAULT_EXPIRY_DAYS
) -> dict:
    if database_name not in ALLOWED_DATABASES:
        return {"status": "error", "message": f"Base de datos no válida. Opciones: {', '.join(sorted(ALLOWED_DATABASES))}"}

    # Verificar job role del usuario
    from app.models.account import Account
    acc_result = await db.execute(select(Account).where(Account.email == user_email))
    account = acc_result.scalar_one_or_none()
    if not account:
        return {"status": "error", "message": f"No existe cuenta con email {user_email}."}
    if not account.job_role:
        return {"status": "error", "message": f"{user_email} no tiene un job role asignado. Pide a un admin que lo configure."}
    if not can_access_database(account.job_role, database_name):
        allowed = sorted(get_allowed_databases(account.job_role))
        label = JOB_ROLE_LABELS.get(account.job_role, account.job_role)
        return {
            "status": "error",
            "message": (
                f"Acceso denegado por política. El rol '{label}' solo puede acceder a: "
                f"{', '.join(allowed) if allowed else 'ninguna BD'}. "
                f"'{database_name}' no está permitida para este rol."
            ),
        }

    existing = await db.execute(
        select(DatabaseAccess).where(
            DatabaseAccess.user_email == user_email,
            DatabaseAccess.database_name == database_name,
            DatabaseAccess.status == "active",
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "error", "message": f"{user_email} ya tiene acceso activo a {database_name}."}

    password = _generate_password()
    expires_at = datetime.now(UTC) + timedelta(days=days) if days is not None else None
    record = DatabaseAccess(
        user_email=user_email,
        database_name=database_name,
        db_username=_generate_username(user_email, database_name),
        db_password=password,
        status="active",
        granted_by=granted_by,
        expires_at=expires_at,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    expiry_note = f"Expira en {days} días" if days is not None else "Sin expiración"
    await _log(db, record.id, user_email, database_name, "granted", granted_by, expiry_note)

    from app.core.email import send_db_access_email
    email_sent = await send_db_access_email(
        user_email, database_name, record.db_username, password, granted_by, expires_at
    )

    expiry_msg = f"Expira en {days} días." if days is not None else "Sin fecha de expiración."
    return {
        "status": "ok",
        "message": f"Acceso otorgado a {user_email} en {database_name}. {expiry_msg}"
                   + (" Credenciales enviadas por correo." if email_sent else ""),
        "access": _serialize(record),
        "email_sent": email_sent,
    }


async def update_access(
    db: AsyncSession, access_id: int, days: int | None = None,
    no_expiry: bool = False, notes: str | None = None, performed_by: str | None = None
) -> dict:
    result = await db.execute(select(DatabaseAccess).where(DatabaseAccess.id == access_id))
    record = result.scalar_one_or_none()
    if not record:
        return {"status": "error", "message": "Registro de acceso no encontrado."}
    if record.status != "active":
        return {"status": "error", "message": "Solo se pueden editar accesos activos."}

    changes = []
    values: dict = {"updated_at": datetime.now(UTC)}

    if no_expiry:
        values["expires_at"] = None
        changes.append("expiración eliminada")
    elif days is not None:
        new_expires = datetime.now(UTC) + timedelta(days=days)
        values["expires_at"] = new_expires
        changes.append(f"expiración → {days}d")

    if notes is not None:
        values["notes"] = notes
        changes.append(f"notas actualizadas")

    if not changes:
        return {"status": "error", "message": "No se especificaron cambios."}

    await db.execute(update(DatabaseAccess).where(DatabaseAccess.id == access_id).values(**values))
    await _log(db, access_id, record.user_email, record.database_name,
               "edited", performed_by, ", ".join(changes))
    await db.commit()

    result2 = await db.execute(select(DatabaseAccess).where(DatabaseAccess.id == access_id))
    return {"status": "ok", "message": f"Acceso actualizado: {', '.join(changes)}.",
            "access": _serialize(result2.scalar_one())}


async def revoke_access(db: AsyncSession, user_email: str, database_name: str) -> dict:
    result = await db.execute(
        select(DatabaseAccess).where(
            DatabaseAccess.user_email == user_email,
            DatabaseAccess.database_name == database_name,
            DatabaseAccess.status == "active",
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        return {"status": "error", "message": f"No existe acceso activo de {user_email} a {database_name}."}

    await db.execute(
        update(DatabaseAccess).where(DatabaseAccess.id == record.id)
        .values(status="revoked", updated_at=datetime.now(UTC))
    )
    await _log(db, record.id, user_email, database_name, "revoked")
    await db.commit()
    return {"status": "ok", "message": f"Acceso de {user_email} a {database_name} revocado."}


async def reset_password(db: AsyncSession, user_email: str, database_name: str) -> dict:
    result = await db.execute(
        select(DatabaseAccess).where(
            DatabaseAccess.user_email == user_email,
            DatabaseAccess.database_name == database_name,
            DatabaseAccess.status == "active",
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        return {"status": "error", "message": f"No existe acceso activo de {user_email} a {database_name}."}

    new_password = _generate_password()
    await db.execute(
        update(DatabaseAccess).where(DatabaseAccess.id == record.id)
        .values(db_password=new_password, updated_at=datetime.now(UTC))
    )
    await db.commit()
    await _log(db, record.id, user_email, database_name, "password_reset")

    from app.core.email import send_db_access_email
    email_sent = await send_db_access_email(
        user_email, database_name, record.db_username, new_password, "ATOS (reset automático)"
    )

    return {
        "status": "ok",
        "message": f"Contraseña de BD actualizada para {user_email} en {database_name}."
                   + (" Nueva contraseña enviada por correo." if email_sent else ""),
        "db_username": record.db_username,
        "db_password": new_password,
        "email_sent": email_sent,
    }


async def get_user_accesses(db: AsyncSession, user_email: str) -> dict:
    result = await db.execute(
        select(DatabaseAccess).where(DatabaseAccess.user_email == user_email)
        .order_by(DatabaseAccess.created_at.desc())
    )
    records = result.scalars().all()
    return {
        "user_email": user_email,
        "total": len(records),
        "accesses": [_serialize(r) for r in records],
    }


async def get_database_users(db: AsyncSession, database_name: str) -> dict:
    result = await db.execute(
        select(DatabaseAccess).where(DatabaseAccess.database_name == database_name)
        .order_by(DatabaseAccess.created_at.desc())
    )
    records = result.scalars().all()
    return {
        "database_name": database_name,
        "total": len(records),
        "users": [_serialize(r) for r in records],
    }


async def get_logs(db: AsyncSession, limit: int = 100) -> list[dict]:
    result = await db.execute(
        select(DatabaseAccessLog)
        .order_by(DatabaseAccessLog.created_at.desc())
        .limit(limit)
    )
    ACTION_LABELS = {
        "granted":        ("✅", "Acceso otorgado"),
        "revoked":        ("🚫", "Acceso revocado"),
        "expired":        ("⏰", "Expirado automáticamente"),
        "password_reset": ("🔑", "Contraseña reseteada"),
        "edited":         ("✏️", "Acceso editado"),
    }
    rows = []
    for r in result.scalars().all():
        icon, label = ACTION_LABELS.get(r.action, ("•", r.action))
        rows.append({
            "id": r.id,
            "access_id": r.access_id,
            "user_email": r.user_email,
            "database_name": r.database_name,
            "action": r.action,
            "action_label": label,
            "action_icon": icon,
            "performed_by": r.performed_by,
            "details": r.details,
            "created_at": r.created_at.isoformat(),
        })
    return rows


async def list_all(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(DatabaseAccess).order_by(DatabaseAccess.created_at.desc())
    )
    return [_serialize(r) for r in result.scalars().all()]

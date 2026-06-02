from app.agent.tools.registry import register
from app.core.database import AsyncSessionLocal
from app.services import account_service as svc
from app.services import password_reset_service as reset_svc


@register({
    "type": "function",
    "function": {
        "name": "unlock_account",
        "description": (
            "Desbloquea una cuenta de usuario bloqueada (manualmente o por intentos fallidos). "
            "Requiere rol agent o admin. Úsala cuando el usuario reporta que no puede acceder a su cuenta."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email de la cuenta a desbloquear."},
            },
            "required": ["email"],
        },
    },
})
async def unlock_account(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await svc.unlock(db, args["email"])


@register({
    "type": "function",
    "function": {
        "name": "check_account_status",
        "description": (
            "Consulta el estado actual de una cuenta: si está activa o bloqueada, "
            "el rol, número de intentos fallidos y si hay bloqueo temporal activo."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email de la cuenta a consultar."},
            },
            "required": ["email"],
        },
    },
})
async def check_account_status(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await svc.check_status(db, args["email"])


@register({
    "type": "function",
    "function": {
        "name": "resend_verification",
        "description": (
            "Reenvía las credenciales de acceso a un usuario generando un nuevo token de reset "
            "de contraseña. Útil cuando el usuario no recibió su email inicial o necesita "
            "recuperar el acceso."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email de la cuenta que necesita recibir las credenciales."},
            },
            "required": ["email"],
        },
    },
})
async def resend_verification(args: dict) -> dict:
    email = args["email"].strip().lower()
    async with AsyncSessionLocal() as db:
        status = await svc.check_status(db, email)
        if not status.get("found"):
            return {"status": "error", "message": f"No existe ninguna cuenta con el email {email}."}

        result = await reset_svc.request_reset(db, email)
        result["message"] = (
            f"Token de acceso generado para {email}. "
            "El usuario puede usarlo para establecer una nueva contraseña."
        )
        return result


@register({
    "type": "function",
    "function": {
        "name": "manage_session",
        "description": (
            "Gestiona la sesión de una cuenta: limpia intentos fallidos de login, "
            "levanta bloqueos temporales por tiempo, o bloquea la cuenta manualmente. "
            "Acciones: 'clear_attempts' (resetea contador), 'clear_temp_lock' (elimina bloqueo temporal), "
            "'lock' (bloquea manualmente), 'unlock' (desbloquea completamente)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email de la cuenta a gestionar."},
                "action": {
                    "type": "string",
                    "description": "Acción a realizar: clear_attempts, clear_temp_lock, lock, unlock.",
                },
                "reason": {"type": "string", "description": "Motivo de la acción (opcional)."},
            },
            "required": ["email", "action"],
        },
    },
})
async def manage_session(args: dict) -> dict:
    email = args["email"].strip().lower()
    action = args["action"].strip().lower()
    reason = args.get("reason", "Acción de soporte")

    allowed_actions = {"clear_attempts", "clear_temp_lock", "lock", "unlock"}
    if action not in allowed_actions:
        return {
            "status": "error",
            "message": f"Acción '{action}' no válida. Usar: {', '.join(sorted(allowed_actions))}.",
        }

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, update
        from app.models.account import Account
        from datetime import datetime, UTC

        result = await db.execute(select(Account).where(Account.email == email))
        account = result.scalar_one_or_none()
        if not account:
            return {"status": "error", "message": f"No existe cuenta con email {email}."}

        if action == "clear_attempts":
            await db.execute(
                update(Account).where(Account.email == email)
                .values(failed_login_attempts=0, updated_at=datetime.now(UTC))
            )
            await db.commit()
            return {"status": "ok", "message": f"Intentos fallidos de {email} reseteados a 0."}

        elif action == "clear_temp_lock":
            await db.execute(
                update(Account).where(Account.email == email)
                .values(locked_until=None, failed_login_attempts=0, updated_at=datetime.now(UTC))
            )
            await db.commit()
            return {"status": "ok", "message": f"Bloqueo temporal de {email} eliminado."}

        elif action == "lock":
            return await svc.lock(db, email, reason)

        elif action == "unlock":
            return await svc.unlock(db, email)


@register({
    "type": "function",
    "function": {
        "name": "validate_identity",
        "description": (
            "Verifica la identidad de un usuario comprobando que la cuenta existe, "
            "está activa, y opcionalmente que el username coincide con el email dado. "
            "Úsala antes de ejecutar acciones sensibles para confirmar que estás actuando "
            "sobre la cuenta correcta."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email de la cuenta a verificar."},
                "expected_username": {
                    "type": "string",
                    "description": "Nombre de usuario esperado para confirmar identidad (opcional).",
                },
            },
            "required": ["email"],
        },
    },
})
async def validate_identity(args: dict) -> dict:
    email = args["email"].strip().lower()
    expected_username = (args.get("expected_username") or "").strip().lower()

    async with AsyncSessionLocal() as db:
        status = await svc.check_status(db, email)

    if not status.get("found"):
        return {
            "identity_confirmed": False,
            "reason": f"No existe ninguna cuenta con el email {email}.",
        }

    account = status["account"]

    if account["status"] == "locked":
        return {
            "identity_confirmed": False,
            "reason": f"La cuenta {email} está bloqueada. Desbloquéala antes de continuar.",
            "account_status": account["status"],
        }

    if expected_username and account["username"].lower() != expected_username:
        return {
            "identity_confirmed": False,
            "reason": "El nombre de usuario no coincide con el email proporcionado.",
        }

    return {
        "identity_confirmed": True,
        "email": email,
        "username": account["username"],
        "role": account["role"],
        "status": account["status"],
        "message": f"Identidad confirmada para {account['username']} ({email}).",
    }

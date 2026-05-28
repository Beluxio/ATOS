from app.agent.tools.registry import register
from app.core.database import AsyncSessionLocal
from app.services import password_reset_service as svc
from app.services import account_service as acc_svc


@register({
    "type": "function",
    "function": {
        "name": "request_password_reset",
        "description": "Solicita un reset de contraseña para un email. Genera un token válido por 15 minutos.",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email del usuario que solicita el reset."},
            },
            "required": ["email"],
        },
    },
})
async def request_password_reset(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await svc.request_reset(db, args["email"])


@register({
    "type": "function",
    "function": {
        "name": "validate_reset_token",
        "description": "Verifica si un token de reset de contraseña es válido y no ha expirado.",
        "parameters": {
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "Token de reset a validar."},
            },
            "required": ["token"],
        },
    },
})
async def validate_reset_token(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await svc.validate_token(db, args["token"])


@register({
    "type": "function",
    "function": {
        "name": "confirm_password_reset",
        "description": "Aplica el reset de contraseña usando un token válido y la nueva contraseña.",
        "parameters": {
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "Token de reset válido."},
                "new_password": {"type": "string", "description": "Nueva contraseña (mínimo 8 caracteres)."},
            },
            "required": ["token", "new_password"],
        },
    },
})
async def confirm_password_reset(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await svc.confirm_reset(db, args["token"], args["new_password"])


@register({
    "type": "function",
    "function": {
        "name": "change_account_password",
        "description": (
            "Cambia la contraseña de una cuenta directamente, sin token de reset. "
            "Úsala cuando el agente de soporte confirma la identidad del usuario y "
            "necesita cambiar su contraseña de forma inmediata."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email de la cuenta a modificar."},
                "new_password": {"type": "string", "description": "Nueva contraseña (mínimo 8 caracteres)."},
            },
            "required": ["email", "new_password"],
        },
    },
})
async def change_account_password(args: dict) -> dict:
    if len(args["new_password"]) < 8:
        return {"status": "error", "message": "La contraseña debe tener al menos 8 caracteres."}
    async with AsyncSessionLocal() as db:
        return await acc_svc.update_password(db, args["email"], args["new_password"])

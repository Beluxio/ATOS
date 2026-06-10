from app.agent.tools.registry import register
from app.core.database import AsyncSessionLocal
from app.services import database_access_service as svc
from app.services import account_service as acc_svc


@register({
    "type": "function",
    "function": {
        "name": "grant_database_access",
        "description": "Otorga acceso a una base de datos a un usuario. Genera credenciales automáticamente.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string", "description": "Email del usuario al que se le otorgará acceso."},
                "database_name": {"type": "string", "description": "Nombre de la BD. Opciones: DataCo Analytics, Data Warehouse, Reporting DB"},
                "granted_by": {"type": "string", "description": "Email del agente que otorga el acceso (opcional)."},
            },
            "required": ["user_email", "database_name"],
        },
    },
})
async def grant_database_access(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await svc.grant_access(db, args["user_email"], args["database_name"], args.get("granted_by"))


@register({
    "type": "function",
    "function": {
        "name": "revoke_database_access",
        "description": "Revoca el acceso de un usuario a una base de datos.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string", "description": "Email del usuario."},
                "database_name": {"type": "string", "description": "Nombre de la BD. Opciones: DataCo Analytics, Data Warehouse, Reporting DB"},
            },
            "required": ["user_email", "database_name"],
        },
    },
})
async def revoke_database_access(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await svc.revoke_access(db, args["user_email"], args["database_name"])


@register({
    "type": "function",
    "function": {
        "name": "reset_database_password",
        "description": "Genera una nueva contraseña de base de datos para un usuario con acceso activo.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string", "description": "Email del usuario."},
                "database_name": {"type": "string", "description": "Nombre de la BD. Opciones: DataCo Analytics, Data Warehouse, Reporting DB"},
            },
            "required": ["user_email", "database_name"],
        },
    },
})
async def reset_database_password(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await svc.reset_password(db, args["user_email"], args["database_name"])


@register({
    "type": "function",
    "function": {
        "name": "check_database_access",
        "description": "Consulta todos los accesos a bases de datos de un usuario.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string", "description": "Email del usuario."},
            },
            "required": ["user_email"],
        },
    },
})
async def check_database_access(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await svc.get_user_accesses(db, args["user_email"])


@register({
    "type": "function",
    "function": {
        "name": "assign_job_role",
        "description": "Asigna un job role a un usuario. El job role determina a qué bases de datos puede tener acceso.",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email del usuario."},
                "job_role": {
                    "type": "string",
                    "description": "Job role a asignar. Opciones: frontend_dev, backend_dev, data_scientist. Enviar null para quitar el rol.",
                },
            },
            "required": ["email", "job_role"],
        },
    },
})
async def assign_job_role(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await acc_svc.update_job_role(db, args["email"], args.get("job_role"))


@register({
    "type": "function",
    "function": {
        "name": "list_database_users",
        "description": "Lista todos los usuarios con acceso a una base de datos específica.",
        "parameters": {
            "type": "object",
            "properties": {
                "database_name": {"type": "string", "description": "Nombre de la BD. Opciones: DataCo Analytics, Data Warehouse, Reporting DB"},
            },
            "required": ["database_name"],
        },
    },
})
async def list_database_users(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await svc.get_database_users(db, args["database_name"])

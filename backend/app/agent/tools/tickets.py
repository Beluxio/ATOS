from app.agent.tools.registry import register
from app.core.database import AsyncSessionLocal
from app.services import ticket_service as svc


@register({
    "type": "function",
    "function": {
        "name": "create_ticket",
        "description": (
            "Crea un nuevo ticket de soporte. La prioridad y categoría se asignan automáticamente "
            "según el contenido. Úsala cuando el usuario reporta un problema o incidencia."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title":       {"type": "string", "description": "Título breve del problema (máx 100 chars)."},
                "description": {"type": "string", "description": "Descripción detallada del problema."},
                "user_email":  {"type": "string", "description": "Email del usuario que reporta el problema."},
            },
            "required": ["title", "description", "user_email"],
        },
    },
})
async def create_ticket(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await svc.create_ticket(db, args["title"], args["description"], args["user_email"])


@register({
    "type": "function",
    "function": {
        "name": "get_ticket",
        "description": "Obtiene los detalles completos de un ticket por su ID, incluyendo historial de respuestas.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer", "description": "ID numérico del ticket."},
            },
            "required": ["ticket_id"],
        },
    },
})
async def get_ticket(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        result = await svc.get_ticket(db, args["ticket_id"])
        return result or {"status": "error", "message": f"Ticket #{args['ticket_id']} no encontrado."}


@register({
    "type": "function",
    "function": {
        "name": "list_tickets",
        "description": "Lista tickets con filtros opcionales. Útil para ver tickets de un usuario o por estado.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string",  "description": "Filtrar por email del usuario (opcional)."},
                "status":     {"type": "string",  "description": "Filtrar por estado: open, in_progress, resolved, closed, escalated (opcional)."},
                "priority":   {"type": "string",  "description": "Filtrar por prioridad: critical, high, medium, low (opcional)."},
                "limit":      {"type": "integer", "description": "Máximo de resultados a retornar (default: 20)."},
            },
            "required": [],
        },
    },
})
async def list_tickets(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        tickets = await svc.list_tickets(
            db,
            user_email=args.get("user_email"),
            status=args.get("status"),
            priority=args.get("priority"),
            limit=args.get("limit", 20),
        )
        return {"total": len(tickets), "tickets": tickets}


@register({
    "type": "function",
    "function": {
        "name": "update_ticket_status",
        "description": "Actualiza el estado de un ticket. Estados válidos: open, in_progress, resolved, closed, escalated.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id":  {"type": "integer", "description": "ID del ticket a actualizar."},
                "new_status": {"type": "string",  "description": "Nuevo estado del ticket."},
                "note":       {"type": "string",  "description": "Nota opcional explicando el cambio de estado."},
            },
            "required": ["ticket_id", "new_status"],
        },
    },
})
async def update_ticket_status(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await svc.update_status(db, args["ticket_id"], args["new_status"], args.get("note"))


@register({
    "type": "function",
    "function": {
        "name": "escalate_ticket",
        "description": "Escala un ticket a soporte humano, marcándolo como urgente. Úsala cuando el problema supera las capacidades del agente.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer", "description": "ID del ticket a escalar."},
                "reason":    {"type": "string",  "description": "Motivo de la escalación."},
            },
            "required": ["ticket_id", "reason"],
        },
    },
})
async def escalate_ticket(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await svc.escalate_ticket(db, args["ticket_id"], args["reason"])


@register({
    "type": "function",
    "function": {
        "name": "add_ticket_response",
        "description": "Añade una respuesta o nota a un ticket existente.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer", "description": "ID del ticket."},
                "content":   {"type": "string",  "description": "Contenido de la respuesta o nota."},
                "author":    {"type": "string",  "description": "Nombre del autor (default: ATOS)."},
            },
            "required": ["ticket_id", "content"],
        },
    },
})
async def add_ticket_response(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await svc.add_response(db, args["ticket_id"], args["content"], args.get("author", "ATOS"))

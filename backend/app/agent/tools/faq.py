from app.agent.tools.registry import register
from app.core.database import AsyncSessionLocal
from app.services import faq_service as svc


@register({
    "type": "function",
    "function": {
        "name": "search_faq",
        "description": (
            "Busca en la base de conocimiento (FAQ) respuestas a preguntas frecuentes. "
            "Úsala SIEMPRE antes de responder preguntas sobre procesos, políticas o procedimientos del sistema. "
            "Retorna las entradas más relevantes con respuesta y pasos."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Pregunta o palabras clave a buscar en la FAQ."},
                "limit": {"type": "integer", "description": "Máximo de resultados (default: 5)."},
            },
            "required": ["query"],
        },
    },
})
async def search_faq(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        results = await svc.search(db, args["query"], args.get("limit", 5))
        if not results:
            return {"found": False, "message": "No se encontraron FAQs relevantes para esa consulta."}
        return {"found": True, "total": len(results), "results": results}


@register({
    "type": "function",
    "function": {
        "name": "get_faq_item",
        "description": "Obtiene el detalle completo de una FAQ por su ID, incluyendo pasos detallados.",
        "parameters": {
            "type": "object",
            "properties": {
                "faq_id": {"type": "integer", "description": "ID de la FAQ a consultar."},
            },
            "required": ["faq_id"],
        },
    },
})
async def get_faq_item(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        item = await svc.get_item(db, args["faq_id"])
        return item or {"status": "error", "message": f"FAQ #{args['faq_id']} no encontrada."}


@register({
    "type": "function",
    "function": {
        "name": "list_faq_categories",
        "description": "Lista todas las FAQs agrupadas por categoría. Útil para mostrar al usuario qué temas cubre la base de conocimiento.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Filtrar por categoría: password, account, security, tickets, admin, technical, general (opcional)."},
            },
            "required": [],
        },
    },
})
async def list_faq_categories(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        items = await svc.list_all(db, args.get("category"))
        return {"total": len(items), "items": items}

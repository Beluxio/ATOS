from app.agent.tools.registry import register
from app.core.database import AsyncSessionLocal
from app.services import memory_service as svc


@register({
    "type": "function",
    "function": {
        "name": "search_incident_history",
        "description": (
            "Busca en el historial de incidencias anteriores para encontrar soluciones probadas. "
            "Usa esto ANTES de dar una solución, para ver si ya hubo casos similares."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Descripción del problema actual para buscar similitudes.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Máximo de resultados a retornar (default: 5).",
                },
            },
            "required": ["description"],
        },
    },
})
async def search_incident_history(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        results = await svc.search_incidents(db, args["description"], args.get("limit", 5))
    if not results:
        return {
            "found": False,
            "message": "No se encontraron incidencias similares en el historial.",
            "tip": "Puedes guardar esta solución cuando la resuelvas con save_incident_to_history.",
        }
    return {
        "found": True,
        "similar_count": len(results),
        "results": results,
    }


@register({
    "type": "function",
    "function": {
        "name": "save_incident_to_history",
        "description": "Guarda una incidencia resuelta en el historial para mejorar respuestas futuras.",
        "parameters": {
            "type": "object",
            "properties": {
                "description":   {"type": "string", "description": "Descripción del problema."},
                "solution_used": {"type": "string", "description": "Comando o acción que resolvió el problema."},
                "outcome": {
                    "type": "string",
                    "description": "Resultado: resolved, escalated, unresolved.",
                },
                "ticket_id": {"type": "integer", "description": "ID del ticket relacionado (opcional)."},
                "category":  {"type": "string",  "description": "Categoría: nodejs, python, docker, git, network, permissions, environment."},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Etiquetas adicionales (opcional).",
                },
            },
            "required": ["description", "solution_used", "outcome"],
        },
    },
})
async def save_incident_to_history(args: dict) -> dict:
    outcome = args.get("outcome", "resolved").lower()
    if outcome not in {"resolved", "escalated", "unresolved"}:
        return {"status": "error", "message": "outcome debe ser: resolved, escalated, o unresolved."}

    async with AsyncSessionLocal() as db:
        saved = await svc.save_incident(
            db,
            description=args["description"].strip(),
            solution_used=args["solution_used"].strip(),
            outcome=outcome,
            ticket_id=args.get("ticket_id"),
            category=args.get("category"),
            tags=args.get("tags"),
        )
    return {
        "status": "ok",
        "saved": True,
        **saved,
        "message": "✅ Incidencia guardada en el historial. Se usará para mejorar respuestas futuras.",
    }


@register({
    "type": "function",
    "function": {
        "name": "get_frequent_issues",
        "description": "Obtiene las categorías de problemas más frecuentes y sus soluciones más efectivas.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
})
async def get_frequent_issues(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        stats = await svc.get_stats(db)
    return {
        "status": "ok",
        "frequent_categories": stats["category_distribution"],
        "total_incidents": stats["total_incidents"],
        "resolution_rate_pct": stats["resolution_rate_pct"],
    }


@register({
    "type": "function",
    "function": {
        "name": "get_solution_effectiveness",
        "description": "Obtiene métricas de efectividad para una solución específica o las top soluciones.",
        "parameters": {
            "type": "object",
            "properties": {
                "solution_name": {
                    "type": "string",
                    "description": "Nombre exacto de la solución, o vacío para obtener el top 5.",
                },
            },
            "required": [],
        },
    },
})
async def get_solution_effectiveness(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        stats = await svc.get_stats(db)

    top_solutions = stats["top_solutions"]
    name = (args.get("solution_name") or "").strip().lower()

    if name:
        match = next((s for s in top_solutions if name in s["solution"].lower()), None)
        if match:
            return {"found": True, "solution": match}
        return {"found": False, "message": f"No se encontraron métricas para '{name}'."}

    return {
        "status": "ok",
        "top_solutions": top_solutions,
    }

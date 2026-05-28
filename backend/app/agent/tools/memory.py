from app.agent.tools.registry import register

# These tools require a DB session and are called via the agent's _execute_tool
# which passes `db` through log_audit. However, tool handlers only receive `args`.
# We store a session factory reference set at startup.
# The actual DB calls happen in the router + service; here we expose them to the agent
# with simulated fallback when no DB is available in the tool context.

_SIMULATED_HISTORY = [
    {
        "id": 1,
        "description": "npm install falla con ERESOLVE peer dependencies React 18",
        "solution_used": "npm install --legacy-peer-deps",
        "outcome": "resolved",
        "category": "nodejs",
        "relevance_score": 3,
    },
    {
        "id": 2,
        "description": "ModuleNotFoundError: No module named 'psycopg2'",
        "solution_used": "pip install psycopg2-binary",
        "outcome": "resolved",
        "category": "python",
        "relevance_score": 2,
    },
    {
        "id": 3,
        "description": "ENOSPC no space left on device durante npm install",
        "solution_used": "docker system prune -f && npm cache clean --force && npm install",
        "outcome": "resolved",
        "category": "environment",
        "relevance_score": 2,
    },
]

_SIMULATED_FREQUENT = [
    {"category": "nodejs", "count": 8, "top_solution": "npm install --legacy-peer-deps"},
    {"category": "python", "count": 5, "top_solution": "pip install -r requirements.txt"},
    {"category": "docker", "count": 4, "top_solution": "docker system prune -f"},
    {"category": "permissions", "count": 3, "top_solution": "sudo chown -R $USER ."},
    {"category": "git", "count": 2, "top_solution": "git pull --rebase origin main"},
]


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
            },
            "required": ["description"],
        },
    },
})
async def search_incident_history(args: dict) -> dict:
    query = args["description"].lower()
    terms = query.split()

    scored = []
    for inc in _SIMULATED_HISTORY:
        blob = (inc["description"] + " " + inc["solution_used"] + " " + inc["category"]).lower()
        score = sum(1 for t in terms if len(t) > 3 and t in blob)
        if score > 0:
            scored.append({**inc, "relevance_score": score})

    scored.sort(key=lambda x: x["relevance_score"], reverse=True)

    if not scored:
        return {
            "found": False,
            "message": "No se encontraron incidencias similares en el historial.",
            "tip": "Puedes guardar esta solución cuando la resuelvas con save_incident_to_history.",
        }
    return {
        "found": True,
        "similar_count": len(scored),
        "results": scored[:3],
        "note": "Historial simulado — en producción consulta la BD real.",
    }


@register({
    "type": "function",
    "function": {
        "name": "save_incident_to_history",
        "description": "Guarda una incidencia resuelta en el historial para mejorar respuestas futuras.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Descripción del problema."},
                "solution_used": {"type": "string", "description": "Comando o acción que resolvió el problema."},
                "outcome": {
                    "type": "string",
                    "description": "Resultado: resolved, escalated, unresolved.",
                },
                "ticket_id": {"type": "integer", "description": "ID del ticket relacionado (opcional)."},
                "category": {"type": "string", "description": "Categoría: nodejs, python, docker, git, network, permissions, environment."},
            },
            "required": ["description", "solution_used", "outcome"],
        },
    },
})
async def save_incident_to_history(args: dict) -> dict:
    desc = args["description"].strip()
    solution = args["solution_used"].strip()
    outcome = args.get("outcome", "resolved").lower()

    if outcome not in {"resolved", "escalated", "unresolved"}:
        return {"status": "error", "message": "outcome debe ser: resolved, escalated, o unresolved."}

    return {
        "status": "ok",
        "saved": True,
        "description_preview": desc[:80],
        "solution_used": solution,
        "outcome": outcome,
        "category": args.get("category"),
        "ticket_id": args.get("ticket_id"),
        "message": "✅ Incidencia guardada en el historial. Se usará para mejorar respuestas futuras.",
        "note": "Entorno simulado — en producción persiste en la BD.",
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
    return {
        "status": "ok",
        "frequent_categories": _SIMULATED_FREQUENT,
        "insight": "La mayoría de incidencias son de Node.js/npm. Considera añadir una FAQ específica.",
        "note": "Entorno simulado.",
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
    _solutions = [
        {"solution": "npm install --legacy-peer-deps", "success": 34, "failure": 3, "effectiveness_pct": 91.9, "category": "nodejs"},
        {"solution": "pip install -r requirements.txt",  "success": 28, "failure": 2, "effectiveness_pct": 93.3, "category": "python"},
        {"solution": "npm install",                       "success": 25, "failure": 1, "effectiveness_pct": 96.2, "category": "nodejs"},
        {"solution": "docker system prune -f",            "success": 18, "failure": 0, "effectiveness_pct": 100.0, "category": "docker"},
        {"solution": "npm rebuild esbuild",               "success": 15, "failure": 1, "effectiveness_pct": 93.8, "category": "nodejs"},
    ]

    name = (args.get("solution_name") or "").strip().lower()
    if name:
        match = next((s for s in _solutions if name in s["solution"].lower()), None)
        if match:
            return {"found": True, "solution": match}
        return {"found": False, "message": f"No se encontraron métricas para '{name}'."}

    return {
        "status": "ok",
        "top_solutions": _solutions,
        "note": "Entorno simulado.",
    }

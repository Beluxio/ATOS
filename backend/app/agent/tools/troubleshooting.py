from app.agent.tools.registry import register
from app.core.database import AsyncSessionLocal
from app.services import troubleshooting_service as svc

# Simulated software versions and config values for demo purposes
_SIMULATED_VERSIONS: dict[str, str] = {
    "node": "v20.11.0", "nodejs": "v20.11.0", "npm": "10.2.4",
    "python": "3.12.0", "python3": "3.12.0", "pip": "24.0",
    "docker": "26.1.0", "git": "2.44.0",
    "vite": "6.0.1", "react": "18.3.1",
}

_SIMULATED_CONFIGS: dict[str, str] = {
    "node_env": "development", "port": "8002", "database_url": "configured",
    "groq_api_key": "configured", "resend_api_key": "configured",
    "docker_running": "yes", "tunnel_active": "yes",
}


@register({
    "type": "function",
    "function": {
        "name": "identify_error",
        "description": (
            "Analiza un mensaje de error y encuentra los flujos de troubleshooting más relevantes. "
            "Úsala cuando el usuario pega un error o describe un problema técnico."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "error_message": {"type": "string", "description": "Mensaje de error o descripción del problema del usuario."},
            },
            "required": ["error_message"],
        },
    },
})
async def identify_error(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        flows = await svc.identify_error(db, args["error_message"])
    if not flows:
        return {
            "found": False,
            "message": "No encontré un flujo específico para ese error. Describe el problema con más detalle o comparte el mensaje de error exacto.",
        }
    return {"found": True, "matching_flows": flows,
            "suggestion": f"Encontré {len(flows)} flujo(s) relevante(s). Puedo guiarte paso a paso por el más apropiado."}


@register({
    "type": "function",
    "function": {
        "name": "get_troubleshooting_flow",
        "description": "Obtiene los pasos completos de un flujo de troubleshooting por su ID para guiar al usuario.",
        "parameters": {
            "type": "object",
            "properties": {
                "flow_id": {"type": "integer", "description": "ID del flujo de troubleshooting."},
            },
            "required": ["flow_id"],
        },
    },
})
async def get_troubleshooting_flow(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        flow = await svc.get_flow(db, args["flow_id"])
    if not flow:
        return {"status": "error", "message": f"Flujo #{args['flow_id']} no encontrado."}
    return flow


@register({
    "type": "function",
    "function": {
        "name": "list_troubleshooting_flows",
        "description": "Lista todos los flujos de troubleshooting disponibles, opcionalmente filtrados por categoría.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Categoría: nodejs, python, network, permissions, docker, git, environment (opcional)."},
            },
            "required": [],
        },
    },
})
async def list_troubleshooting_flows(args: dict) -> dict:
    async with AsyncSessionLocal() as db:
        flows = await svc.list_flows(db, args.get("category"))
    return {"total": len(flows), "flows": flows}


@register({
    "type": "function",
    "function": {
        "name": "check_software_version",
        "description": "Verifica la versión instalada de una herramienta de software (simulado para demo).",
        "parameters": {
            "type": "object",
            "properties": {
                "software_name": {"type": "string", "description": "Nombre del software a verificar (node, python, docker, git, npm, etc.)."},
            },
            "required": ["software_name"],
        },
    },
})
async def check_software_version(args: dict) -> dict:
    name = args["software_name"].lower().strip()
    version = _SIMULATED_VERSIONS.get(name)
    if version:
        return {"software": name, "version": version, "status": "installed",
                "note": "Versión simulada para entorno de demo."}
    return {"software": name, "status": "unknown",
            "message": f"No tengo información sobre '{name}' en el entorno simulado."}


@register({
    "type": "function",
    "function": {
        "name": "validate_basic_config",
        "description": "Verifica si una configuración básica del entorno está presente y correcta (simulado para demo).",
        "parameters": {
            "type": "object",
            "properties": {
                "config_key": {"type": "string", "description": "Clave de configuración a validar (node_env, port, database_url, groq_api_key, docker_running, etc.)."},
            },
            "required": ["config_key"],
        },
    },
})
async def validate_basic_config(args: dict) -> dict:
    key = args["config_key"].lower().strip()
    value = _SIMULATED_CONFIGS.get(key)
    if value:
        return {"config_key": key, "value": value, "status": "ok",
                "note": "Valor simulado para entorno de demo."}
    return {"config_key": key, "status": "not_found",
            "message": f"Configuración '{key}' no encontrada en el entorno simulado."}

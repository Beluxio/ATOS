from app.agent.tools.registry import register


@register({
    "type": "function",
    "function": {
        "name": "ping",
        "description": "Verifica que el agente está operativo. Útil para pruebas.",
        "parameters": {"type": "object", "properties": {}},
    },
})
async def ping(_: dict) -> dict:
    return {"status": "ok", "agent": "ATOS"}

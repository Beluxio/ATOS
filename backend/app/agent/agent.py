import json
import logging
from typing import Any, Optional
from groq import AsyncGroq, APIStatusError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import log_audit
from app.agent.prompts.system_prompt import build_system_prompt
from app.agent.tools.registry import TOOL_REGISTRY, get_tool_declarations

import app.agent.tools.base_tools      # noqa: F401
import app.agent.tools.password_reset  # noqa: F401
import app.agent.tools.accounts        # noqa: F401
import app.agent.tools.tickets         # noqa: F401
import app.agent.tools.faq             # noqa: F401
import app.agent.tools.troubleshooting  # noqa: F401
import app.agent.tools.dependencies       # noqa: F401
import app.agent.tools.environment        # noqa: F401
import app.agent.tools.automated_actions  # noqa: F401
import app.agent.tools.memory             # noqa: F401

logger = logging.getLogger(__name__)

_client = AsyncGroq(api_key=settings.groq_api_key)
# llama3-groq-8b-8192-tool-use-preview is fine-tuned specifically for tool use
# and generates well-formed JSON arguments reliably on the free tier.
MODEL = "llama-3.3-70b-versatile"

# ── Tool routing ───────────────────────────────────────────────
# Sending all 30+ tools on every request consumes ~6k tokens of declarations.
# Instead, route: select tools relevant to the message + a small core set.

_ALWAYS_INCLUDE = {
    "search_faq", "create_ticket", "suggest_fix", "identify_error",
}

_KEYWORD_TOOLS: list[tuple[list[str], list[str]]] = [
    (
        ["password", "contraseña", "reset", "token"],
        ["request_password_reset", "validate_reset_token", "confirm_password_reset"],
    ),
    (
        ["ticket", "incidencia", "issue", "escalar", "prioridad"],
        ["get_ticket", "list_tickets", "update_ticket_status", "escalate_ticket", "detect_duplicate_tickets"],
    ),
    (
        ["faq", "pregunta", "documenta", "base de conocimiento"],
        ["get_faq_item", "list_faq_categories"],
    ),
    (
        ["npm", "pip", "yarn", "pnpm", "depend", "paquete", "package", "cache", "módulo", "module",
         "esbuild", "node_modules", "install", "reinstal"],
        ["detect_broken_dependencies", "clean_cache", "reinstall_dependency",
         "check_version_conflicts"],
    ),
    (
        ["troubleshoot", "diagnos", "flujo", "paso a paso", "guía"],
        ["get_troubleshooting_flow", "list_troubleshooting_flows",
         "check_software_version", "validate_basic_config"],
    ),
    (
        ["entorno", "environment", "herramienta", "instalad", "versión", "path",
         "node", "python", "docker", "git", "reporte del sistema", "requisito"],
        ["check_tool_installed", "validate_path",
         "check_minimum_requirements", "generate_environment_report"],
    ),
    (
        ["historial", "incidencia anterior", "solución anterior", "guardar", "memoria",
         "frecuente", "efectividad"],
        ["search_incident_history", "save_incident_to_history",
         "get_frequent_issues", "get_solution_effectiveness"],
    ),
    (
        ["reporte", "report", "acción", "notificaci", "ejecutar acción",
         "reiniciar sesión", "exportar"],
        ["execute_allowed_action", "generate_report",
         "send_notification", "restart_session"],
    ),
    (
        ["usuario", "cuenta", "bloqueado", "unlock", "verificaci", "sesión revocar",
         "credencial", "acceso", "identidad", "desbloquea", "bloquea", "estado de"],
        ["unlock_account", "check_account_status",
         "resend_verification", "manage_session", "validate_identity"],
    ),
]

# Keep last N turns to cap history tokens (1 turn = user + assistant + tool msgs)
_MAX_HISTORY_TURNS = 4


def _select_tools(message: str) -> list[dict]:
    """Return tool declarations for tools relevant to the message."""
    all_decls = {d["function"]["name"]: d for d in get_tool_declarations()}
    msg_lower = message.lower()

    selected_names: set[str] = set(_ALWAYS_INCLUDE)
    for keywords, tool_names in _KEYWORD_TOOLS:
        if any(kw in msg_lower for kw in keywords):
            selected_names.update(tool_names)

    # Fall back to all tools only when nothing matched beyond core
    if len(selected_names) == len(_ALWAYS_INCLUDE):
        # Generic message — add FAQ + troubleshooting as safe defaults
        selected_names.update([
            "get_faq_item", "list_faq_categories",
            "search_incident_history", "identify_error",
        ])

    return [decl for name, decl in all_decls.items() if name in selected_names]


def _trim_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only the last N user turns; truncate old tool results to 300 chars."""
    if not history:
        return history

    user_indices = [i for i, m in enumerate(history) if m.get("role") == "user"]
    if len(user_indices) > _MAX_HISTORY_TURNS:
        cutoff = user_indices[-_MAX_HISTORY_TURNS]
        history = history[cutoff:]

    # Truncate verbose tool results in older messages
    result = []
    total = len(history)
    for idx, msg in enumerate(history):
        if msg.get("role") == "tool" and idx < total - 4:
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > 300:
                msg = {**msg, "content": content[:300] + "…(truncated)"}
        result.append(msg)
    return result


async def chat(
    message: str,
    history: list[dict[str, Any]],
    db: AsyncSession,
    session_id: str,
    user_email: Optional[str] = None,
    user_role: Optional[str] = None,
) -> tuple[str, list[dict[str, Any]]]:
    system_prompt = build_system_prompt(user_email, user_role)
    messages = [{"role": "system", "content": system_prompt}]
    messages += _trim_history(history)
    messages.append({"role": "user", "content": message})
    tools = _select_tools(message)

    response_text = ""
    max_iterations = 6

    for _ in range(max_iterations):
        try:
            response = await _client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=1024,
            )
        except APIStatusError as e:
            body = e.body or {}
            code = body.get("error", {}).get("code", "") if isinstance(body, dict) else ""
            # Retry without tools only for tool_use_failed (malformed JSON args)
            if e.status_code == 400 and code == "tool_use_failed" and tools:
                logger.warning("tool_use_failed — retrying without tools")
                try:
                    response = await _client.chat.completions.create(
                        model=MODEL,
                        messages=messages,
                        max_tokens=1024,
                    )
                except APIStatusError as inner:
                    raise RuntimeError(f"Error de la API de Groq ({inner.status_code})") from inner
            else:
                raise RuntimeError(f"Error de la API de Groq ({e.status_code}): {e.message}") from e

        choice = response.choices[0]
        assistant_msg = choice.message

        msg_dict: dict[str, Any] = {"role": "assistant", "content": assistant_msg.content or ""}
        if assistant_msg.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in assistant_msg.tool_calls
            ]
        messages.append(msg_dict)

        if choice.finish_reason == "tool_calls" and assistant_msg.tool_calls:
            for tool_call in assistant_msg.tool_calls:
                name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                result = await _execute_tool(name, args, db, session_id)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
        else:
            response_text = assistant_msg.content or ""
            break

    updated_history = messages[1:]
    return response_text, updated_history


async def _execute_tool(name: str, args: dict, db: AsyncSession, session_id: str) -> Any:
    handler = TOOL_REGISTRY.get(name)
    if not handler:
        return {"error": f"Tool '{name}' no registrada."}
    result = await handler(args)
    await log_audit(db, name, args, result, session_id)
    return result

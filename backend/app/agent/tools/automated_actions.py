from app.agent.tools.registry import register
import datetime

# ── Whitelists ────────────────────────────────────────────────

ALLOWED_ACTIONS = {
    "clear_user_sessions",
    "generate_audit_report",
    "generate_ticket_summary",
    "send_status_notification",
    "restart_agent_session",
    "export_logs",
    "run_health_check",
}

ALLOWED_REPORT_TYPES = {"audit", "tickets", "users", "performance", "incidents"}

ALLOWED_NOTIFICATION_CHANNELS = {"slack", "email", "webhook", "dashboard"}

ALLOWED_SESSION_TYPES = {"agent", "user", "admin"}


# ── Simulated action results ───────────────────────────────────

def _simulate_action(action: str, params: dict) -> dict:
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    results = {
        "clear_user_sessions": {
            "action": action,
            "affected_sessions": params.get("count", 3),
            "timestamp": ts,
            "message": "Sesiones de usuario limpiadas correctamente.",
        },
        "generate_audit_report": {
            "action": action,
            "report_id": f"RPT-{ts[:10].replace('-', '')}-001",
            "rows": 42,
            "timestamp": ts,
            "message": "Reporte de auditoría generado.",
        },
        "generate_ticket_summary": {
            "action": action,
            "open": 12, "closed": 87, "pending": 5, "critical": 2,
            "timestamp": ts,
        },
        "send_status_notification": {
            "action": action,
            "channel": params.get("channel", "dashboard"),
            "delivered": True,
            "timestamp": ts,
        },
        "restart_agent_session": {
            "action": action,
            "session_type": params.get("session_type", "agent"),
            "timestamp": ts,
            "message": "Sesión reiniciada correctamente.",
        },
        "export_logs": {
            "action": action,
            "file": f"logs_{ts[:10]}.csv",
            "rows_exported": 256,
            "timestamp": ts,
        },
        "run_health_check": {
            "action": action,
            "services": {
                "api": "healthy",
                "database": "healthy",
                "agent": "healthy",
            },
            "timestamp": ts,
            "overall": "healthy",
        },
    }
    return results.get(action, {"action": action, "status": "executed", "timestamp": ts})


# ── Tools ──────────────────────────────────────────────────────

@register({
    "type": "function",
    "function": {
        "name": "execute_allowed_action",
        "description": (
            "Ejecuta una acción predefinida y autorizada del sistema. "
            "SIEMPRE muestra al usuario qué acción se va a ejecutar y espera confirmación "
            "para acciones destructivas (clear_sessions, restart). "
            f"Acciones disponibles: {', '.join(sorted(ALLOWED_ACTIONS))}."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action_name": {
                    "type": "string",
                    "description": f"Nombre de la acción. Permitidas: {', '.join(sorted(ALLOWED_ACTIONS))}.",
                },
                "params": {
                    "type": "object",
                    "description": "Parámetros adicionales para la acción (opcional).",
                },
                "confirmed": {
                    "type": "boolean",
                    "description": "True si el usuario ya confirmó la ejecución.",
                },
            },
            "required": ["action_name"],
        },
    },
})
async def execute_allowed_action(args: dict) -> dict:
    action = args["action_name"].lower().strip()
    if action not in ALLOWED_ACTIONS:
        return {
            "status": "error",
            "message": f"Acción '{action}' no está en la whitelist. Permitidas: {', '.join(sorted(ALLOWED_ACTIONS))}.",
        }

    params = args.get("params") or {}
    destructive = action in {"clear_user_sessions", "restart_agent_session", "export_logs"}

    if destructive and not args.get("confirmed"):
        return {
            "status": "pending_confirmation",
            "action": action,
            "params": params,
            "message": f"⚠️ La acción '{action}' es potencialmente disruptiva. ¿Confirmas la ejecución?",
        }

    result = _simulate_action(action, params)
    return {
        "status": "ok",
        "note": "Entorno simulado — en producción ejecuta la acción real.",
        **result,
    }


@register({
    "type": "function",
    "function": {
        "name": "generate_report",
        "description": "Genera un reporte del sistema en formato JSON. Tipos disponibles: audit, tickets, users, performance, incidents.",
        "parameters": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "description": f"Tipo de reporte: {', '.join(ALLOWED_REPORT_TYPES)}.",
                },
                "filters": {
                    "type": "object",
                    "description": "Filtros opcionales: date_from, date_to, status, priority.",
                },
            },
            "required": ["report_type"],
        },
    },
})
async def generate_report(args: dict) -> dict:
    rtype = args["report_type"].lower().strip()
    if rtype not in ALLOWED_REPORT_TYPES:
        return {
            "status": "error",
            "message": f"Tipo '{rtype}' no soportado. Usar: {', '.join(ALLOWED_REPORT_TYPES)}.",
        }

    filters = args.get("filters") or {}
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

    reports = {
        "audit": {
            "total_actions": 314,
            "by_tool": {"search_faq": 89, "create_ticket": 72, "check_account_status": 61, "suggest_fix": 45, "other": 47},
            "period": filters.get("date_from", "last 30 days"),
        },
        "tickets": {
            "total": 104, "open": 12, "closed": 87, "pending": 5,
            "by_priority": {"critical": 3, "high": 11, "medium": 56, "low": 34},
            "avg_resolution_hours": 4.2,
        },
        "users": {
            "total_accounts": 3, "active": 3, "locked": 0, "admins": 1, "agents": 0, "users": 2,
        },
        "performance": {
            "avg_response_ms": 312,
            "p95_response_ms": 890,
            "uptime_pct": 99.8,
            "error_rate_pct": 0.4,
        },
        "incidents": {
            "total_incidents": 28,
            "resolved": 25, "unresolved": 3,
            "top_categories": ["npm/node", "python env", "permissions"],
            "avg_resolution_steps": 3.1,
        },
    }

    return {
        "status": "ok",
        "report_type": rtype,
        "generated_at": ts,
        "filters_applied": filters,
        "data": reports[rtype],
        "note": "Entorno simulado — en producción consulta datos reales de la BD.",
    }


@register({
    "type": "function",
    "function": {
        "name": "send_notification",
        "description": "Envía una notificación a través de un canal autorizado (Slack, email, webhook, dashboard).",
        "parameters": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": f"Canal de envío: {', '.join(ALLOWED_NOTIFICATION_CHANNELS)}.",
                },
                "message": {
                    "type": "string",
                    "description": "Contenido del mensaje a enviar.",
                },
                "recipient": {
                    "type": "string",
                    "description": "Destinatario: email, canal de Slack, o URL del webhook.",
                },
            },
            "required": ["channel", "message"],
        },
    },
})
async def send_notification(args: dict) -> dict:
    channel = args["channel"].lower().strip()
    if channel not in ALLOWED_NOTIFICATION_CHANNELS:
        return {
            "status": "error",
            "message": f"Canal '{channel}' no permitido. Usar: {', '.join(ALLOWED_NOTIFICATION_CHANNELS)}.",
        }

    msg = args["message"]
    if len(msg) > 1000:
        return {"status": "error", "message": "El mensaje supera los 1000 caracteres permitidos."}

    recipient = args.get("recipient", "N/A")
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

    return {
        "status": "ok",
        "channel": channel,
        "recipient": recipient,
        "message_preview": msg[:80] + ("..." if len(msg) > 80 else ""),
        "sent_at": ts,
        "delivered": True,
        "note": "Entorno simulado — en producción envía la notificación real.",
    }


@register({
    "type": "function",
    "function": {
        "name": "restart_session",
        "description": "Reinicia una sesión del sistema (agente, usuario, o admin). Requiere confirmación del usuario.",
        "parameters": {
            "type": "object",
            "properties": {
                "session_type": {
                    "type": "string",
                    "description": f"Tipo de sesión: {', '.join(ALLOWED_SESSION_TYPES)}.",
                },
                "confirmed": {
                    "type": "boolean",
                    "description": "True si el usuario confirmó el reinicio.",
                },
            },
            "required": ["session_type"],
        },
    },
})
async def restart_session(args: dict) -> dict:
    stype = args["session_type"].lower().strip()
    if stype not in ALLOWED_SESSION_TYPES:
        return {
            "status": "error",
            "message": f"Tipo de sesión '{stype}' no válido. Usar: {', '.join(ALLOWED_SESSION_TYPES)}.",
        }

    if not args.get("confirmed"):
        return {
            "status": "pending_confirmation",
            "session_type": stype,
            "message": f"⚠️ Esto reiniciará la sesión '{stype}'. Los cambios no guardados se perderán. ¿Confirmas?",
        }

    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return {
        "status": "ok",
        "session_type": stype,
        "restarted_at": ts,
        "message": f"✅ Sesión '{stype}' reiniciada correctamente.",
        "note": "Entorno simulado.",
    }

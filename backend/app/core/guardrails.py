"""
Guardrails de contenido para el chat de ATOS.

Dos capas de protección:
  1. OpenAI Moderation API — detecta odio, acoso, violencia, contenido sexual, autolesiones.
  2. Detección de jailbreak — patrones que intentan manipular al agente fuera de sus funciones.
"""

import logging
import re
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = AsyncOpenAI(api_key=settings.openai_api_key)

# ── Políticas de contenido ────────────────────────────────────────────────────

POLICIES: dict[str, str] = {
    # Categorías de la API de Moderación de OpenAI
    "hate": (
        "🚫 Tu mensaje contiene lenguaje de odio o discriminación. "
        "ATOS no puede procesar mensajes con ese tipo de contenido. "
        "Por favor reformula tu solicitud de forma respetuosa."
    ),
    "hate/threatening": (
        "🚫 Tu mensaje contiene amenazas basadas en odio o discriminación. "
        "Este tipo de contenido no está permitido en ATOS."
    ),
    "harassment": (
        "🚫 Tu mensaje contiene lenguaje ofensivo o de acoso. "
        "ATOS requiere un trato respetuoso. Por favor reformula tu solicitud."
    ),
    "harassment/threatening": (
        "🚫 Tu mensaje contiene amenazas o lenguaje intimidatorio. "
        "Este tipo de contenido no está permitido. Contacta a soporte si tienes una urgencia."
    ),
    "sexual": (
        "🚫 Tu mensaje contiene contenido sexual inapropiado. "
        "ATOS es un sistema de soporte técnico y no puede procesar ese tipo de contenido."
    ),
    "sexual/minors": (
        "🚫 Tu mensaje contiene contenido sexual inapropiado. "
        "Este caso ha sido registrado automáticamente."
    ),
    "violence": (
        "🚫 Tu mensaje contiene contenido violento. "
        "ATOS no puede procesar ese tipo de contenido. "
        "Si estás en una situación de emergencia, contacta a los servicios de emergencia."
    ),
    "violence/graphic": (
        "🚫 Tu mensaje contiene contenido violento explícito. "
        "Este tipo de contenido no está permitido en ATOS."
    ),
    "self-harm": (
        "⚠️ Tu mensaje puede estar relacionado con autolesiones. "
        "Si estás pasando por un momento difícil, por favor comunícate con una línea de crisis. "
        "ATOS no puede ayudarte con esto, pero alguien puede hacerlo."
    ),
    "self-harm/intent": (
        "⚠️ Tu mensaje puede estar relacionado con autolesiones. "
        "Si estás pasando por un momento difícil, por favor comunícate con una línea de crisis. "
        "ATOS no puede ayudarte con esto, pero alguien puede hacerlo."
    ),
    "self-harm/instructions": (
        "🚫 Tu mensaje solicita contenido relacionado con autolesiones. "
        "Este tipo de contenido no está permitido."
    ),
    # Jailbreak / manipulación del agente
    "jailbreak": (
        "🚫 Tu mensaje intenta modificar el comportamiento de ATOS fuera de sus funciones. "
        "El agente solo puede ejecutar acciones de soporte técnico autorizadas. "
        "Si necesitas ayuda, describe tu problema técnico con normalidad."
    ),
}

# ── Detección de jailbreak ────────────────────────────────────────────────────

_JAILBREAK_PATTERNS: list[re.Pattern] = [re.compile(p, re.IGNORECASE) for p in [
    # Suplantación de identidad / cambio de rol
    r"\beres ahora\b",
    r"\bahora eres\b",
    r"\bactúa como\b",
    r"\bactua como\b",
    r"\bfinge (?:ser|que eres)\b",
    r"\bpretend(?:ing)? (?:to be|you are|you're)\b",
    r"\byou are now\b",
    r"\bact as\b",
    r"\byou're (?:now )?a\b",
    r"\bDAN\b",
    r"\bdo anything now\b",
    # Anulación de instrucciones
    r"\bignora (?:tus|las|sus) instrucciones\b",
    r"\bolvida (?:tus|las|tus) instrucciones\b",
    r"\bignore (?:your|previous|all) instructions?\b",
    r"\bforget (?:your|previous|all) instructions?\b",
    r"\bignore (?:the )?system prompt\b",
    r"\boverride (?:your )?(instructions?|rules?|guidelines?)\b",
    r"\bdisregard (?:your )?(instructions?|rules?|guidelines?)\b",
    # Extracción del system prompt
    r"\bmuéstrame (?:el|tu) (system )?prompt\b",
    r"\brepite (?:el|tu) (system )?prompt\b",
    r"\breveal (?:your|the) (system )?prompt\b",
    r"\bprint (?:your|the) (system )?prompt\b",
    r"\bwhat (?:are|were) your instructions\b",
    # Modo sin restricciones
    r"\bsin restricciones\b",
    r"\bmode? (?:sin|without|no) (restricciones?|restrictions?|limits?|filters?)\b",
    r"\bunrestricted mode\b",
    r"\bjailbreak\b",
    r"\bbypass (?:your )?(filters?|restrictions?|guidelines?|safety)\b",
    r"\bdeshabilita (?:tus|los) filtros\b",
    r"\bdisable (?:your )?(filters?|safety|restrictions?)\b",
    # Inyección de prompt
    r"</?(system|user|assistant|instruction)>",
    r"\[INST\]",
    r"<<SYS>>",
]]


def _detect_jailbreak(message: str) -> bool:
    return any(pattern.search(message) for pattern in _JAILBREAK_PATTERNS)


# ── Resultado de la verificación ──────────────────────────────────────────────

@dataclass
class GuardrailResult:
    blocked: bool
    category: str | None = None
    policy_message: str | None = None
    scores: dict | None = None


# ── Función principal ─────────────────────────────────────────────────────────

async def check_message(message: str) -> GuardrailResult:
    """
    Verifica el mensaje contra las políticas de contenido.
    Retorna GuardrailResult con blocked=True si viola alguna política.
    """
    # Capa 1: detección local de jailbreak (sin latencia de red)
    if _detect_jailbreak(message):
        logger.warning("Jailbreak detectado: %.120s", message)
        return GuardrailResult(
            blocked=True,
            category="jailbreak",
            policy_message=POLICIES["jailbreak"],
        )

    # Capa 2: OpenAI Moderation API
    try:
        response = await _client.moderations.create(
            model="omni-moderation-latest",
            input=message,
        )
        result = response.results[0]

        if result.flagged:
            # Encontrar la categoría con mayor puntuación
            scores = result.category_scores.model_dump()
            flags = result.categories.model_dump()

            # Priorizar las más graves
            priority_order = [
                "sexual/minors", "hate/threatening", "harassment/threatening",
                "violence/graphic", "self-harm/intent", "self-harm/instructions",
                "hate", "harassment", "sexual", "violence", "self-harm",
            ]
            triggered = next(
                (cat for cat in priority_order if flags.get(cat.replace("/", "_"), False)),
                next((k for k, v in flags.items() if v), None),
            )

            if triggered:
                category_key = triggered.replace("_", "/")
                policy_msg = POLICIES.get(category_key, POLICIES["harassment"])
                logger.warning(
                    "Contenido bloqueado — categoría: %s | puntuación: %.3f | mensaje: %.120s",
                    category_key,
                    scores.get(triggered, 0),
                    message,
                )
                return GuardrailResult(
                    blocked=True,
                    category=category_key,
                    policy_message=policy_msg,
                    scores=scores,
                )

    except Exception as e:
        # Si la API de moderación falla, no bloqueamos (fail open)
        logger.error("Error en Moderation API: %s — mensaje permitido por defecto", e)

    return GuardrailResult(blocked=False)

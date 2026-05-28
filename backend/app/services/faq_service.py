from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.models.faq import FAQItem

# ── Seed data ─────────────────────────────────────────────────

SEED_FAQS = [
    {
        "question": "¿Cómo reseteo mi contraseña?",
        "answer": "Puedes resetear tu contraseña mediante un token temporal válido por 15 minutos. El agente ATOS puede iniciar el proceso por ti.",
        "steps": [
            "Pídele a ATOS: 'Resetea mi contraseña para usuario@email.com'",
            "Recibirás un token de reset",
            "Usa el token junto con tu nueva contraseña para confirmar el cambio",
            "Inicia sesión con tu nueva contraseña",
        ],
        "tags": ["contraseña", "reset", "password", "olvidé"],
        "category": "password",
    },
    {
        "question": "Mi cuenta está bloqueada, ¿qué hago?",
        "answer": "Las cuentas se bloquean por múltiples intentos de login fallidos (5 intentos = 15 min de bloqueo) o por acción manual del soporte. ATOS puede desbloquearla si tienes los permisos necesarios.",
        "steps": [
            "Espera 15 minutos si fue por intentos fallidos",
            "Si persiste, pídele a ATOS: 'Desbloquea mi cuenta usuario@email.com'",
            "Un agente verificará tu identidad antes de desbloquear",
            "Si el bloqueo es manual, contacta a soporte para más información",
        ],
        "tags": ["bloqueada", "locked", "acceso", "intentos"],
        "category": "account",
    },
    {
        "question": "¿Cuántos intentos de login tengo antes de que se bloquee mi cuenta?",
        "answer": "El sistema permite 5 intentos fallidos consecutivos. Al superar este límite, la cuenta se bloquea automáticamente durante 15 minutos.",
        "steps": [],
        "tags": ["intentos", "bloqueo", "login", "límite"],
        "category": "security",
    },
    {
        "question": "¿Cómo cambio mi contraseña sin olvidarla?",
        "answer": "Si recuerdas tu contraseña actual y quieres cambiarla, ATOS puede hacerlo directamente verificando tu identidad primero.",
        "steps": [
            "Pídele a ATOS: 'Quiero cambiar mi contraseña'",
            "ATOS verificará que la solicitud viene del titular de la cuenta",
            "Proporciona tu nueva contraseña (mínimo 8 caracteres)",
            "El cambio se aplica de inmediato",
        ],
        "tags": ["cambiar contraseña", "actualizar", "nueva contraseña"],
        "category": "password",
    },
    {
        "question": "¿Cómo creo una nueva cuenta?",
        "answer": "Las cuentas se crean desde el panel de administración por un agente o administrador. Los usuarios finales no pueden auto-registrarse.",
        "steps": [
            "Contacta a tu administrador o abre un ticket de soporte",
            "Proporciona tu email y nombre de usuario deseado",
            "El administrador creará la cuenta y te enviará las credenciales",
            "Cambia tu contraseña en el primer acceso",
        ],
        "tags": ["crear cuenta", "registro", "nueva cuenta", "sign up"],
        "category": "account",
    },
    {
        "question": "¿Qué roles existen en el sistema?",
        "answer": "El sistema tiene tres roles: 'user' (acceso básico, solo puede gestionar su propia cuenta), 'agent' (puede gestionar cuentas de usuarios), y 'admin' (acceso completo incluyendo cambio de roles).",
        "steps": [],
        "tags": ["roles", "permisos", "admin", "agent", "user"],
        "category": "account",
    },
    {
        "question": "¿Cómo abro un ticket de soporte?",
        "answer": "Puedes abrir un ticket directamente desde el panel de Tickets o pidiendo a ATOS que lo cree por ti en el chat.",
        "steps": [
            "Opción 1: Ve al panel Tickets → botón 'Nuevo ticket'",
            "Opción 2: En el chat, dile a ATOS: 'Crea un ticket por [tu problema]'",
            "ATOS asignará automáticamente prioridad y categoría",
            "Recibirás el número de ticket para seguimiento",
        ],
        "tags": ["ticket", "soporte", "incidencia", "ayuda"],
        "category": "tickets",
    },
    {
        "question": "¿Cuáles son las prioridades de los tickets?",
        "answer": "Los tickets tienen 4 niveles de prioridad asignados automáticamente: critical (sistema caído, producción afectada), high (problema importante), medium (problema normal), low (consulta o duda).",
        "steps": [],
        "tags": ["prioridad", "critical", "urgente", "ticket"],
        "category": "tickets",
    },
    {
        "question": "¿Cómo escalo un ticket a soporte humano?",
        "answer": "Si ATOS no puede resolver tu problema, puede escalar el ticket a un agente humano. El ticket queda marcado como 'escalated' con alta prioridad.",
        "steps": [
            "Pídele a ATOS: 'Escala el ticket #N porque no se ha podido resolver'",
            "ATOS registrará el motivo de la escalación",
            "El ticket cambia a estado 'escalated' y prioridad 'high'",
            "Un agente humano lo atenderá lo antes posible",
        ],
        "tags": ["escalar", "escalation", "soporte humano", "agente"],
        "category": "tickets",
    },
    {
        "question": "Mi sesión expira muy rápido, ¿es normal?",
        "answer": "Los tokens de acceso tienen una duración de 8 horas. Al expirar, necesitas iniciar sesión nuevamente. Esto es por seguridad.",
        "steps": [
            "Al expirar la sesión verás la pantalla de login",
            "Ingresa tus credenciales nuevamente",
            "Si el problema persiste, verifica que tu reloj del sistema esté sincronizado",
        ],
        "tags": ["sesión", "token", "expirado", "logout automático"],
        "category": "security",
    },
    {
        "question": "¿Cómo verifico el estado de mi cuenta?",
        "answer": "ATOS puede consultar el estado de cualquier cuenta: si está activa, bloqueada, el número de intentos fallidos y cuándo fue creada.",
        "steps": [
            "Pídele a ATOS: '¿Cuál es el estado de la cuenta usuario@email.com?'",
            "ATOS mostrará: estado, rol, intentos fallidos y bloqueo temporal si existe",
        ],
        "tags": ["estado", "cuenta", "status", "verificar"],
        "category": "account",
    },
    {
        "question": "¿Qué hago si no recibo el email de reset de contraseña?",
        "answer": "El sistema puede operar en dos modos: con Resend (email real) o modo simulado (token en el chat). En modo simulado, el token aparece directamente en la conversación con ATOS.",
        "steps": [
            "Revisa si el token aparece en el chat de ATOS",
            "Revisa tu carpeta de spam o correo no deseado",
            "Verifica que el email ingresado sea correcto",
            "Si el problema persiste, pide a ATOS que regenere el token",
        ],
        "tags": ["email", "correo", "no llega", "token", "reset"],
        "category": "password",
    },
    {
        "question": "¿Cuál es la longitud mínima de la contraseña?",
        "answer": "Las contraseñas deben tener mínimo 8 caracteres para el flujo de reset. Para el registro inicial, el mínimo es 6 caracteres.",
        "steps": [],
        "tags": ["contraseña", "longitud", "requisitos", "seguridad"],
        "category": "password",
    },
    {
        "question": "¿Puedo ver el historial de acciones de ATOS?",
        "answer": "Sí. Todas las acciones ejecutadas por ATOS se registran en el Audit Log, accesible desde el panel de administración.",
        "steps": [
            "Ve al panel 'Audit Logs' en el sidebar",
            "Verás cada herramienta ejecutada, sus parámetros y el resultado",
            "Los logs incluyen timestamp y session_id para trazabilidad",
        ],
        "tags": ["audit", "logs", "historial", "acciones", "trazabilidad"],
        "category": "admin",
    },
    {
        "question": "¿Cómo funciona el bloqueo automático por intentos fallidos?",
        "answer": "El sistema registra cada intento fallido de login. Al llegar a 5 intentos consecutivos, bloquea la cuenta automáticamente durante 15 minutos. El contador se resetea al iniciar sesión correctamente.",
        "steps": [],
        "tags": ["bloqueo automático", "intentos", "rate limiting", "seguridad"],
        "category": "security",
    },
    {
        "question": "¿Qué diferencia hay entre bloqueo manual y bloqueo automático?",
        "answer": "El bloqueo manual (status='locked') lo aplica un agente o ATOS y requiere desbloqueo explícito. El bloqueo automático (locked_until) es temporal (15 min) por intentos fallidos y se libera solo.",
        "steps": [],
        "tags": ["bloqueo", "manual", "automático", "diferencia"],
        "category": "security",
    },
    {
        "question": "¿Cómo desbloqueo una cuenta de otro usuario?",
        "answer": "Solo los agentes y administradores pueden desbloquear cuentas de otros usuarios. Los usuarios con rol 'user' solo pueden gestionar su propia cuenta.",
        "steps": [
            "Necesitas rol 'agent' o 'admin'",
            "Pídele a ATOS: 'Desbloquea la cuenta usuario@email.com'",
            "ATOS verificará tus permisos antes de ejecutar",
            "La acción queda registrada en el Audit Log",
        ],
        "tags": ["desbloquear", "otra cuenta", "agente", "admin"],
        "category": "account",
    },
    {
        "question": "¿Qué pasa si ATOS no puede resolver mi problema?",
        "answer": "Si ATOS no puede resolver tu problema, escala el ticket a soporte humano automáticamente o puedes pedírselo explícitamente.",
        "steps": [
            "ATOS intentará resolver el problema con las herramientas disponibles",
            "Si no puede, te informará y ofrecerá crear/escalar un ticket",
            "Un agente humano revisará el ticket escalado",
            "Puedes también pedir: 'Escala este problema a soporte humano'",
        ],
        "tags": ["límites", "escalar", "soporte humano", "no puede resolver"],
        "category": "general",
    },
    {
        "question": "¿Cómo funciona la clasificación automática de tickets?",
        "answer": "ATOS analiza el título y descripción del ticket para asignar automáticamente categoría (password, account, technical, network, billing) y prioridad (critical, high, medium, low) usando palabras clave.",
        "steps": [],
        "tags": ["clasificación", "automática", "ticket", "prioridad", "categoría"],
        "category": "tickets",
    },
    {
        "question": "¿Cómo contacto al soporte si ATOS no responde?",
        "answer": "Si el servidor está offline (punto rojo en el sidebar) significa que Docker no está corriendo o el tunnel de Cloudflare está caído. Reinicia Docker y el tunnel.",
        "steps": [
            "Verifica el punto de estado en el sidebar (verde = online)",
            "Si está rojo: reinicia Docker con 'docker-compose up -d'",
            "Si usas Cloudflare Tunnel: reinicia cloudflared",
            "Abre un ticket para que quede registro del problema",
        ],
        "tags": ["offline", "servidor", "docker", "tunnel", "cloudflare"],
        "category": "technical",
    },
]


# ── Service functions ─────────────────────────────────────────

async def seed(db: AsyncSession) -> None:
    count = await db.execute(select(func.count()).select_from(FAQItem))
    if count.scalar() > 0:
        return
    for item in SEED_FAQS:
        db.add(FAQItem(**item))
    await db.commit()


async def search(db: AsyncSession, query: str, limit: int = 8) -> list[dict]:
    q = query.strip().lower()
    result = await db.execute(
        select(FAQItem).order_by(FAQItem.helpful_count.desc()).limit(100)
    )
    all_items = result.scalars().all()

    scored: list[tuple[int, FAQItem]] = []
    for item in all_items:
        score = 0
        text = (item.question + " " + item.answer).lower()
        for word in q.split():
            if word in text:
                score += 2
            if word in [t.lower() for t in item.tags]:
                score += 3
            if word in item.category.lower():
                score += 1
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [item for _, item in scored[:limit]]

    # increment views for top results
    for item in top:
        await db.execute(
            update(FAQItem).where(FAQItem.id == item.id).values(views=FAQItem.views + 1)
        )
    await db.commit()
    return [_serialize(i) for i in top]


async def get_item(db: AsyncSession, faq_id: int) -> dict | None:
    result = await db.execute(select(FAQItem).where(FAQItem.id == faq_id))
    item = result.scalar_one_or_none()
    if not item:
        return None
    await db.execute(update(FAQItem).where(FAQItem.id == faq_id).values(views=FAQItem.views + 1))
    await db.commit()
    return _serialize(item)


async def list_all(db: AsyncSession, category: str | None = None) -> list[dict]:
    q = select(FAQItem).order_by(FAQItem.category, FAQItem.question)
    if category:
        q = q.where(FAQItem.category == category)
    result = await db.execute(q)
    return [_serialize(i) for i in result.scalars().all()]


async def mark_helpful(db: AsyncSession, faq_id: int) -> dict:
    result = await db.execute(select(FAQItem).where(FAQItem.id == faq_id))
    if not result.scalar_one_or_none():
        return {"status": "error", "message": "FAQ no encontrada."}
    await db.execute(update(FAQItem).where(FAQItem.id == faq_id).values(helpful_count=FAQItem.helpful_count + 1))
    await db.commit()
    return {"status": "ok"}


def _serialize(i: FAQItem) -> dict:
    return {
        "id": i.id,
        "question": i.question,
        "answer": i.answer,
        "steps": i.steps,
        "tags": i.tags,
        "category": i.category,
        "views": i.views,
        "helpful_count": i.helpful_count,
    }

import asyncio
import logging
import resend
from app.core.config import settings

logger = logging.getLogger(__name__)


async def _send(params: dict) -> bool:
    """Envía un email vía Resend. Retorna True si fue enviado."""
    if not settings.resend_api_key:
        return False
    resend.api_key = settings.resend_api_key
    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info("Email enviado a %s — id: %s", params.get("to"), getattr(result, "id", result))
        return True
    except Exception as e:
        logger.error("Error enviando email a %s: %s", params.get("to"), e)
        return False


async def send_password_reset_email(to_email: str, token: str, expires_minutes: int) -> bool:
    """Envía email de reset vía Resend. Retorna True si fue enviado."""
    if not settings.resend_api_key:
        return False

    resend.api_key = settings.resend_api_key

    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 32px 24px;">
      <div style="margin-bottom: 24px;">
        <span style="font-size: 22px; font-weight: 700; color: #1f2937;">⚙️ ATOS</span>
        <span style="font-size: 14px; color: #6b7280; margin-left: 8px;">Soporte Técnico</span>
      </div>
      <h2 style="color: #111827; font-size: 18px; margin-bottom: 8px;">Reset de contraseña</h2>
      <p style="color: #374151; font-size: 14px; margin-bottom: 20px;">
        Recibimos una solicitud para restablecer tu contraseña. Usa el token de abajo:
      </p>
      <div style="background: #f9fafb; border: 1px solid #e5e7eb; padding: 20px;
                  border-radius: 8px; text-align: center; margin-bottom: 20px;">
        <code style="font-size: 20px; font-weight: bold; letter-spacing: 3px;
                     color: #111827; font-family: monospace;">{token}</code>
      </div>
      <p style="color: #6b7280; font-size: 13px;">
        Válido por <strong>{expires_minutes} minutos</strong>.<br>
        Si no solicitaste este reset, ignora este mensaje.
      </p>
    </div>
    """

    return await _send({
        "from": settings.email_from,
        "to": [to_email],
        "subject": "Token de reset de contraseña — ATOS",
        "html": html,
    })


async def send_db_access_email(
    to_email: str,
    database_name: str,
    db_username: str,
    db_password: str,
    granted_by: str | None = None,
    expires_at=None,
) -> bool:
    """Envía las credenciales de acceso a BD al usuario."""
    granter = granted_by or "un administrador"
    expiry_line = ""
    if expires_at:
        expiry_line = f"<p style='color:#f59e0b;font-size:13px;margin-top:12px;'>⚠️ Este acceso expira el <strong>{expires_at.strftime('%d/%m/%Y')}</strong>.</p>"
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 32px 24px;">
      <div style="margin-bottom: 24px;">
        <span style="font-size: 22px; font-weight: 700; color: #1f2937;">⚙️ ATOS</span>
        <span style="font-size: 14px; color: #6b7280; margin-left: 8px;">Soporte Técnico</span>
      </div>
      <h2 style="color: #111827; font-size: 18px; margin-bottom: 8px;">Acceso a base de datos otorgado</h2>
      <p style="color: #374151; font-size: 14px; margin-bottom: 20px;">
        {granter} te ha otorgado acceso a <strong>{database_name}</strong>. Aquí están tus credenciales:
      </p>
      <div style="background: #f9fafb; border: 1px solid #e5e7eb; padding: 20px;
                  border-radius: 8px; margin-bottom: 20px;">
        <div style="margin-bottom: 12px;">
          <span style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 4px;">BASE DE DATOS</span>
          <code style="font-size: 15px; font-weight: 600; color: #111827;">{database_name}</code>
        </div>
        <div style="margin-bottom: 12px;">
          <span style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 4px;">USUARIO</span>
          <code style="font-size: 15px; font-weight: 600; color: #111827;">{db_username}</code>
        </div>
        <div>
          <span style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 4px;">CONTRASEÑA</span>
          <code style="font-size: 15px; font-weight: 600; color: #111827;">{db_password}</code>
        </div>
      </div>
      {expiry_line}
      <p style="color: #6b7280; font-size: 13px; margin-top: 12px;">
        Guarda estas credenciales en un lugar seguro.<br>
        Si necesitas ayuda, contacta al soporte técnico a través de ATOS.
      </p>
    </div>
    """
    return await _send({
        "from": settings.email_from,
        "to": [to_email],
        "subject": f"Credenciales de acceso — {database_name}",
        "html": html,
    })


async def send_expiry_warning_email(to_email: str, database_name: str, days_left: int) -> bool:
    """Avisa al usuario que su acceso expira en X días."""
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 32px 24px;">
      <div style="margin-bottom: 24px;">
        <span style="font-size: 22px; font-weight: 700; color: #1f2937;">⚙️ ATOS</span>
        <span style="font-size: 14px; color: #6b7280; margin-left: 8px;">Soporte Técnico</span>
      </div>
      <h2 style="color: #d97706; font-size: 18px; margin-bottom: 8px;">⚠️ Tu acceso expira pronto</h2>
      <p style="color: #374151; font-size: 14px; margin-bottom: 20px;">
        Tu acceso a <strong>{database_name}</strong> expirará en <strong>{days_left} día{'s' if days_left != 1 else ''}</strong>.
      </p>
      <div style="background: #fffbeb; border: 1px solid #fcd34d; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
        <div style="font-size: 13px; color: #92400e;">
          🗄️ Base de datos: <strong>{database_name}</strong><br>
          ⏳ Días restantes: <strong>{days_left}</strong>
        </div>
      </div>
      <p style="color: #6b7280; font-size: 13px;">
        Si necesitas renovar tu acceso, contáctate con tu administrador o solicítalo a través del chat de ATOS antes de que expire.
      </p>
    </div>
    """
    return await _send({
        "from": settings.email_from,
        "to": [to_email],
        "subject": f"⚠️ Tu acceso a {database_name} expira en {days_left} días",
        "html": html,
    })


async def send_ticket_assigned_email(
    to_email: str,
    ticket_id: int,
    ticket_title: str,
    priority: str,
    assigned_by: str,
) -> bool:
    """Notifica al agente que le fue asignado un ticket."""
    priority_colors = {"critical": "#dc2626", "high": "#f59e0b", "medium": "#818cf8", "low": "#6b7280"}
    color = priority_colors.get(priority, "#818cf8")
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 32px 24px;">
      <div style="margin-bottom: 24px;">
        <span style="font-size: 22px; font-weight: 700; color: #1f2937;">⚙️ ATOS</span>
        <span style="font-size: 14px; color: #6b7280; margin-left: 8px;">Soporte Técnico</span>
      </div>
      <h2 style="color: #111827; font-size: 18px; margin-bottom: 8px;">🎫 Ticket asignado</h2>
      <p style="color: #374151; font-size: 14px; margin-bottom: 20px;">
        <strong>{assigned_by}</strong> te asignó el ticket <strong>#{ticket_id}</strong>:
      </p>
      <div style="background:#f9fafb; border:1px solid #e5e7eb; padding:16px;
                  border-radius:8px; margin-bottom:20px;">
        <div style="font-size:15px; font-weight:600; color:#111827; margin-bottom:8px;">
          {ticket_title}
        </div>
        <span style="display:inline-block; background:{color}22; color:{color};
              padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600;">
          {priority.upper()}
        </span>
      </div>
      <p style="color:#6b7280; font-size:13px;">
        Accede al panel de ATOS para ver el ticket completo y tomar acción.
      </p>
    </div>
    """
    return await _send({
        "from": settings.email_from,
        "to": [to_email],
        "subject": f"[ATOS] Ticket #{ticket_id} asignado — {ticket_title}",
        "html": html,
    })


async def send_ticket_comment_email(
    to_email: str,
    ticket_id: int,
    ticket_title: str,
    author: str,
    content: str,
) -> bool:
    """Notifica al creador del ticket que recibió una respuesta."""
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 32px 24px;">
      <div style="margin-bottom: 24px;">
        <span style="font-size: 22px; font-weight: 700; color: #1f2937;">⚙️ ATOS</span>
        <span style="font-size: 14px; color: #6b7280; margin-left: 8px;">Soporte Técnico</span>
      </div>
      <h2 style="color: #111827; font-size: 18px; margin-bottom: 8px;">
        Nueva respuesta en tu ticket #{ticket_id}
      </h2>
      <p style="color: #374151; font-size: 14px; margin-bottom: 4px;">
        <strong>{author}</strong> respondió en:
        <em style="color:#6b7280;">{ticket_title}</em>
      </p>
      <div style="background:#f9fafb; border:1px solid #e5e7eb; padding:16px;
                  border-radius:8px; margin: 16px 0;">
        <p style="color:#111827; font-size:14px; margin:0; line-height:1.6;">{content}</p>
      </div>
      <p style="color:#6b7280; font-size:13px;">
        Accede al panel de ATOS para ver el ticket completo y responder.
      </p>
    </div>
    """
    return await _send({
        "from": settings.email_from,
        "to": [to_email],
        "subject": f"Re: Ticket #{ticket_id} — {ticket_title}",
        "html": html,
    })


async def send_welcome_email(
    to_email: str,
    username: str,
    password: str,
    role: str,
) -> bool:
    """Email de bienvenida al crear una nueva cuenta."""
    portal_url = "https://portal.beluxio.org"
    atos_url = "https://atos.beluxio.org"
    role_label = {"user": "Usuario", "agent": "Agente de soporte", "admin": "Administrador"}.get(role, role)
    html = f"""
    <div style="font-family: sans-serif; max-width: 520px; margin: 0 auto; padding: 32px 24px;">
      <div style="margin-bottom: 24px;">
        <span style="font-size: 22px; font-weight: 700; color: #1f2937;">⚙️ ATOS</span>
        <span style="font-size: 14px; color: #6b7280; margin-left: 8px;">Soporte Técnico — DataCo Analytics</span>
      </div>
      <h2 style="color: #111827; font-size: 18px; margin-bottom: 8px;">Bienvenido/a, {username} 👋</h2>
      <p style="color: #374151; font-size: 14px; margin-bottom: 20px;">
        Se ha creado tu cuenta en el sistema ATOS de DataCo Analytics. Aquí están tus credenciales de acceso:
      </p>
      <div style="background:#f9fafb; border:1px solid #e5e7eb; padding:20px;
                  border-radius:8px; margin-bottom:20px;">
        <div style="margin-bottom:12px;">
          <span style="font-size:12px; color:#6b7280; display:block; margin-bottom:4px;">EMAIL</span>
          <code style="font-size:14px; font-weight:600; color:#111827;">{to_email}</code>
        </div>
        <div style="margin-bottom:12px;">
          <span style="font-size:12px; color:#6b7280; display:block; margin-bottom:4px;">USUARIO</span>
          <code style="font-size:14px; font-weight:600; color:#111827;">{username}</code>
        </div>
        <div style="margin-bottom:12px;">
          <span style="font-size:12px; color:#6b7280; display:block; margin-bottom:4px;">CONTRASEÑA INICIAL</span>
          <code style="font-size:14px; font-weight:600; color:#111827;">{password}</code>
        </div>
        <div>
          <span style="font-size:12px; color:#6b7280; display:block; margin-bottom:4px;">ROL</span>
          <span style="font-size:14px; font-weight:600; color:#111827;">{role_label}</span>
        </div>
      </div>
      <div style="display:flex; gap:12px; margin-bottom:24px;">
        <a href="{portal_url}" style="display:inline-block; background:#4f46e5; color:#fff;
           padding:10px 20px; border-radius:6px; text-decoration:none; font-size:14px; font-weight:600;">
          🌐 Abrir Portal DataCo
        </a>
        <a href="{atos_url}" style="display:inline-block; background:#0f172a; color:#fff;
           padding:10px 20px; border-radius:6px; text-decoration:none; font-size:14px; font-weight:600;
           border:1px solid #334155;">
          ⚙️ Panel ATOS
        </a>
      </div>
      <p style="color:#6b7280; font-size:13px;">
        Por seguridad, te recomendamos cambiar tu contraseña tras el primer inicio de sesión.<br>
        Si tienes dudas, usa el chat de ATOS o contacta al equipo de soporte.
      </p>
    </div>
    """
    return await _send({
        "from": settings.email_from,
        "to": [to_email],
        "subject": "Bienvenido/a a ATOS — DataCo Analytics",
        "html": html,
    })


async def send_expiry_email(to_email: str, database_name: str) -> bool:
    """Notifica al usuario que su acceso a una BD ha expirado."""
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 32px 24px;">
      <div style="margin-bottom: 24px;">
        <span style="font-size: 22px; font-weight: 700; color: #1f2937;">⚙️ ATOS</span>
        <span style="font-size: 14px; color: #6b7280; margin-left: 8px;">Soporte Técnico</span>
      </div>
      <h2 style="color: #dc2626; font-size: 18px; margin-bottom: 8px;">Acceso expirado</h2>
      <p style="color: #374151; font-size: 14px; margin-bottom: 20px;">
        Tu acceso a <strong>{database_name}</strong> ha expirado y ha sido revocado automáticamente.
      </p>
      <div style="background: #fef2f2; border: 1px solid #fecaca; padding: 16px;
                  border-radius: 8px; margin-bottom: 20px;">
        <div style="font-size: 13px; color: #991b1b;">
          🔒 Acceso revocado: <strong>{database_name}</strong>
        </div>
      </div>
      <p style="color: #6b7280; font-size: 13px;">
        Si necesitas renovar tu acceso, contacta a tu administrador o solicítalo a través del chat de ATOS.
      </p>
    </div>
    """
    return await _send({
        "from": settings.email_from,
        "to": [to_email],
        "subject": f"Acceso expirado — {database_name}",
        "html": html,
    })

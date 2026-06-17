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

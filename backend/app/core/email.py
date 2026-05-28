import resend
from app.core.config import settings


async def send_password_reset_email(to_email: str, token: str, expires_minutes: int) -> bool:
    """Envía email de reset. Retorna True si fue enviado, False si email no está configurado."""
    if not settings.resend_api_key:
        return False

    resend.api_key = settings.resend_api_key

    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
      <h2 style="color: #4f46e5;">⚙️ ATOS — Reset de Contraseña</h2>
      <p>Has solicitado un reset de contraseña. Usa el siguiente token:</p>
      <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; text-align: center; margin: 20px 0;">
        <code style="font-size: 18px; font-weight: bold; letter-spacing: 2px; color: #1f2937;">{token}</code>
      </div>
      <p style="color: #6b7280; font-size: 13px;">
        Este token es válido por <strong>{expires_minutes} minutos</strong>.<br>
        Si no solicitaste este reset, ignora este mensaje.
      </p>
    </div>
    """

    try:
        resend.Emails.send({
            "from": settings.email_from,
            "to": [to_email],
            "subject": "Token de reset de contraseña — ATOS",
            "html": html,
        })
        return True
    except Exception:
        return False

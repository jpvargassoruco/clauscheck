"""Envío de correo (CLAUDE.md tarea 1): backend `console` (log) o `smtp` async.

`MAIL_BACKEND=console` (por defecto) sólo registra el mensaje en el log —
útil en dev y en tests que capturan el logger. `MAIL_BACKEND=smtp` usa
`aiosmtplib`: puerto 465 → TLS implícito, 587 → STARTTLS. Un fallo de envío
NUNCA debe interrumpir el flujo de la petición: se registra y se continúa
(ver `send_mail`).
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings

logger = logging.getLogger("clauscheck.mail")
# Uvicorn/gunicorn no configuran el logger raíz por defecto (sólo sus propios
# loggers "uvicorn.*"), así que sin un handler propio los `logger.info(...)`
# del backend `console` nunca llegarían a `docker logs`: caerían al
# `lastResort` handler de la stdlib, que sólo emite WARNING o más grave.
# `propagate` se deja en True para que además sea capturable con `caplog`.
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)


async def send_mail(to: str, subject: str, text: str, html: str) -> None:
    if settings.MAIL_BACKEND != "smtp":
        logger.info(
            "MAIL[console] to=%s subject=%s\n--- texto ---\n%s\n--- html ---\n%s",
            to,
            subject,
            text,
            html,
        )
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
        msg["To"] = to
        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        implicit_tls = settings.SMTP_PORT == 465
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER or None,
            password=settings.SMTP_PASS or None,
            use_tls=implicit_tls,
            start_tls=not implicit_tls,
        )
        logger.info("MAIL[smtp] enviado to=%s subject=%s", to, subject)
    except Exception:
        logger.exception("fallo enviando correo a %s (asunto=%s)", to, subject)


def _html(titulo: str, cuerpo: str) -> str:
    return (
        '<div style="font-family:sans-serif;max-width:560px;margin:0 auto">'
        f'<h2 style="color:#1E3A8A">{titulo}</h2>'
        f"{cuerpo}"
        '<p style="color:#888;font-size:12px;margin-top:24px">'
        "ClausCheck — este es un mensaje automático, no responda a este correo."
        "</p></div>"
    )


async def send_solicitud_recibida(to: str, nombre: str) -> None:
    text = (
        f"Hola {nombre},\n\n"
        "Recibimos su solicitud de acceso a ClausCheck. Un administrador la "
        "revisará y le notificaremos por este medio la decisión.\n\n"
        "Gracias por su interés."
    )
    html = _html(
        "Solicitud recibida",
        f"<p>Hola {nombre},</p>"
        "<p>Recibimos su solicitud de acceso a ClausCheck. Un administrador la "
        "revisará y le notificaremos por este medio la decisión.</p>"
        "<p>Gracias por su interés.</p>",
    )
    await send_mail(to, "ClausCheck — Solicitud recibida", text, html)


async def send_nueva_solicitud_admin(
    to: str, nombre: str, email: str, organizacion: str, motivo: str, approve_url: str
) -> None:
    text = (
        "Nueva solicitud de acceso a ClausCheck:\n\n"
        f"Nombre: {nombre}\nEmail: {email}\nOrganización: {organizacion}\n"
        f"Motivo: {motivo}\n\nRevisar: {approve_url}"
    )
    html = _html(
        "Nueva solicitud de acceso",
        f"<p><strong>Nombre:</strong> {nombre}<br>"
        f"<strong>Email:</strong> {email}<br>"
        f"<strong>Organización:</strong> {organizacion}<br>"
        f"<strong>Motivo:</strong> {motivo}</p>"
        f'<p><a href="{approve_url}">Revisar solicitud</a></p>',
    )
    await send_mail(to, "ClausCheck — Nueva solicitud de acceso", text, html)


async def send_invitacion(to: str, token: str, org_nombre: str, role: str, accept_url: str) -> None:
    text = (
        f"Fue invitado a unirse a {org_nombre} en ClausCheck como {role}.\n\n"
        f"Complete su registro aquí (el enlace vence en 7 días): {accept_url}"
    )
    html = _html(
        "Invitación a ClausCheck",
        f"<p>Fue invitado a unirse a <strong>{org_nombre}</strong> en ClausCheck "
        f"como <strong>{role}</strong>.</p>"
        f'<p><a href="{accept_url}">Completar registro</a> (el enlace vence en 7 días).</p>',
    )
    await send_mail(to, "ClausCheck — Invitación", text, html)


async def send_solicitud_rechazada(to: str, nombre: str, motivo: str) -> None:
    motivo_txt = motivo or "no especificado"
    text = (
        f"Hola {nombre},\n\nSu solicitud de acceso a ClausCheck fue rechazada.\n"
        f"Motivo: {motivo_txt}."
    )
    html = _html(
        "Solicitud rechazada",
        f"<p>Hola {nombre},</p><p>Su solicitud de acceso a ClausCheck fue rechazada.</p>"
        f"<p><strong>Motivo:</strong> {motivo_txt}</p>",
    )
    await send_mail(to, "ClausCheck — Solicitud rechazada", text, html)


async def send_mfa_notice(to: str, accion: str) -> None:
    text = f"La autenticación en dos pasos (MFA) fue {accion} en su cuenta de ClausCheck."
    html = _html(
        "Aviso de seguridad",
        f"<p>La autenticación en dos pasos (MFA) fue <strong>{accion}</strong> "
        "en su cuenta de ClausCheck.</p>",
    )
    await send_mail(to, "ClausCheck — Aviso de seguridad (MFA)", text, html)

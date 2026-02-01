"""Email notification service."""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


def _is_configured() -> bool:
    """Check if SMTP is configured."""
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)


async def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send an email via SMTP. Returns True on success."""
    if not _is_configured():
        logger.warning("SMTP not configured, skipping email send")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email or settings.smtp_user}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False


async def notify_new_demo_request(
    clinic_name: str,
    contact_name: str,
    email: str,
    phone: str,
    clinic_size: str | None = None,
    preferred_time: str | None = None,
    message: str | None = None,
) -> bool:
    """Send notification email when a new demo request is received."""
    to = settings.notification_email
    if not to:
        logger.warning("No notification_email configured, skipping demo request notification")
        return False

    time_labels = {
        "morning": "Manana",
        "afternoon": "Tarde",
        "anytime": "Cualquier hora",
    }
    size_labels = {
        "1-2": "1-2 veterinarios",
        "3-5": "3-5 veterinarios",
        "6-10": "6-10 veterinarios",
        "10+": "Mas de 10",
    }

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #10b981; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">Nueva solicitud de demo</h2>
        </div>
        <div style="border: 1px solid #e5e7eb; border-top: none; padding: 20px; border-radius: 0 0 8px 8px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; color: #6b7280; width: 140px;">Clinica:</td>
                    <td style="padding: 8px 0; font-weight: bold;">{clinic_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Contacto:</td>
                    <td style="padding: 8px 0;">{contact_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Email:</td>
                    <td style="padding: 8px 0;"><a href="mailto:{email}">{email}</a></td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Telefono:</td>
                    <td style="padding: 8px 0;"><a href="tel:{phone}">{phone}</a></td>
                </tr>
                {"<tr><td style='padding: 8px 0; color: #6b7280;'>Tamano:</td><td style='padding: 8px 0;'>" + size_labels.get(clinic_size, clinic_size) + "</td></tr>" if clinic_size else ""}
                {"<tr><td style='padding: 8px 0; color: #6b7280;'>Horario preferido:</td><td style='padding: 8px 0;'>" + time_labels.get(preferred_time, preferred_time) + "</td></tr>" if preferred_time else ""}
            </table>
            {"<div style='margin-top: 16px; padding: 12px; background: #f9fafb; border-radius: 6px;'><strong style='color: #6b7280;'>Mensaje:</strong><p style='margin: 8px 0 0;'>" + message + "</p></div>" if message else ""}
        </div>
    </div>
    """

    return await send_email(
        to=to,
        subject=f"Nueva solicitud de demo - {clinic_name}",
        html_body=html,
    )

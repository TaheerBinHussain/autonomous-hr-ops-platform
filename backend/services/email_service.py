"""
Email Service — sends emails via SMTP to Mailpit (or production SMTP).
"""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import structlog

log = structlog.get_logger(__name__)

class EmailService:
    def __init__(self, smtp_host: str = "mailpit", smtp_port: int = 1025) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
        from_email: str = "hr@techcorp.ai",
    ) -> bool:
        """Send an email via SMTP to Mailpit or configured SMTP server."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"TechCorp HR <{from_email}>"
            msg["To"] = to_email

            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            # Try connecting to container 'mailpit', fallback to 'host.docker.internal', 'localhost'
            for host in [self.smtp_host, "host.docker.internal", "localhost", "127.0.0.1"]:
                try:
                    with smtplib.SMTP(host, self.smtp_port, timeout=3) as server:
                        server.sendmail(from_email, [to_email], msg.as_string())
                    log.info("email_service.sent", to=to_email, subject=subject, host=host)
                    return True
                except Exception as e:
                    log.warning("email_service.host_failed", host=host, error=str(e))

            log.error("email_service.all_failed", to=to_email)
            return False
        except Exception as exc:
            log.error("email_service.error", error=str(exc))
            return False

email_service = EmailService()

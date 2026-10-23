
import smtplib
from email.message import EmailMessage

from core.config import settings


class EmailProvider:

    @staticmethod
    def send_otp(to_email: str, otp: str) -> None:
        if not settings.gmail_address or not settings.gmail_app_password:
            raise RuntimeError("Gmail SMTP is not configured")

        message = EmailMessage()
        message["Subject"] = "Verify your Logsbee email"
        message["From"] = settings.gmail_address
        message["To"] = to_email

        message.set_content(
            f"""Hello,

Your Logsbee email verification code is: {otp}

This code expires in 5 minutes.
Do not share this code with anyone.

If you did not request this code, you can ignore this email.

Regards,
Logsbee Team
"""
        )

        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
                timeout=15,
            ) as smtp:
                smtp.login(
                    settings.gmail_address,
                    settings.gmail_app_password,
                )
                smtp.send_message(message)
        else:
            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=15,
            ) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(
                    settings.gmail_address,
                    settings.gmail_app_password,
                )
                smtp.send_message(message)

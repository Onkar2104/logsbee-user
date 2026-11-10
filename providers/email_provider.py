
# import smtplib
# from email.message import EmailMessage

# from core.config import settings


# class EmailProvider:

#     @staticmethod
#     def send_otp(to_email: str, otp: str) -> None:
#         if not settings.gmail_address or not settings.gmail_app_password:
#             raise RuntimeError("Gmail SMTP is not configured")

#         message = EmailMessage()
#         message["Subject"] = "Verify your Logsbee email"
#         message["From"] = settings.gmail_address
#         message["To"] = to_email

#         message.set_content(
#             f"""Hello,

# Your Logsbee email verification code is: {otp}

# This code expires in 5 minutes.
# Do not share this code with anyone.

# If you did not request this code, you can ignore this email.

# Regards,
# Logsbee Team
# """
#         )

#         if settings.smtp_port == 465:
#             with smtplib.SMTP_SSL(
#                 settings.smtp_host,
#                 settings.smtp_port,
#                 timeout=15,
#             ) as smtp:
#                 smtp.login(
#                     settings.gmail_address,
#                     settings.gmail_app_password,
#                 )
#                 smtp.send_message(message)
#         else:
#             with smtplib.SMTP(
#                 settings.smtp_host,
#                 settings.smtp_port,
#                 timeout=15,
#             ) as smtp:
#                 smtp.ehlo()
#                 smtp.starttls()
#                 smtp.ehlo()
#                 smtp.login(
#                     settings.gmail_address,
#                     settings.gmail_app_password,
#                 )
#                 smtp.send_message(message)



import smtplib
import requests
from email.message import EmailMessage

from core.config import settings


class EmailProvider:

    @staticmethod
    def send_otp(to_email: str, otp: str) -> None:
        provider = settings.email_provider.strip().lower()

        if provider == "mailjet":
            EmailProvider._send_using_mailjet(to_email, otp)
        elif provider == "smtp":
            EmailProvider._send_using_gmail(to_email, otp)
        else:
            raise RuntimeError(
                f"Unsupported email provider: {provider}"
            )

    @staticmethod
    def _send_using_mailjet(to_email: str, otp: str) -> None:
        if not all([
            settings.mailjet_apikey_public,
            settings.mailjet_apikey_private,
            settings.mailjet_sender_email,
        ]):
            raise RuntimeError("Mailjet is not fully configured")

        payload = {
            "Messages": [
                {
                    "From": {
                        "Email": settings.mailjet_sender_email,
                        "Name": "Logsbee Team",
                    },
                    "To": [
                        {
                            "Email": to_email,
                        }
                    ],
                    "Subject": "Verify your Logsbee email",
                    "TextPart": f"""Hello,

Your Logsbee email verification code is: {otp}

This code expires in 5 minutes.
Do not share this code with anyone.

If you did not request this code, you can ignore this email.

Regards,
Logsbee Team
""",
                }
            ]
        }

        try:
            response = requests.post(
                "https://api.mailjet.com/v3.1/send",
                auth=(
                    settings.mailjet_apikey_public,
                    settings.mailjet_apikey_private,
                ),
                json=payload,
                timeout=15,
            )

            response.raise_for_status()

            result = response.json()
            messages = result.get("Messages", [])

            if not messages or messages[0].get("Status") != "success":
                raise RuntimeError("Mailjet did not accept the email")

        except requests.RequestException as exc:
            raise RuntimeError("Mailjet email delivery request failed") from exc

    @staticmethod
    def _send_using_gmail(to_email: str, otp: str) -> None:
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

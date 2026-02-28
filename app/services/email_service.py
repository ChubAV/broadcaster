from email.message import EmailMessage

import aiosmtplib


async def send_verification_email(
    to_email: str,
    code: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    smtp_from: str,
    smtp_use_tls: bool = True,
) -> None:
    """Send a verification code email via SMTP."""
    msg = EmailMessage()
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg["Subject"] = f"Код подтверждения: {code}"
    msg.set_content(
        f"Ваш код подтверждения для регистрации в Broadcaster: {code}\n\n"
        f"Код действителен 10 минут.\n\n"
        f"Если вы не запрашивали этот код, проигнорируйте это письмо."
    )

    await aiosmtplib.send(
        message=msg,
        hostname=smtp_host,
        port=smtp_port,
        username=smtp_user,
        password=smtp_password,
        use_tls=smtp_use_tls,
    )

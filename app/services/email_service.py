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

    # use_tls=True → implicit SSL (port 465)
    # start_tls=True → STARTTLS (port 587)
    use_tls = smtp_use_tls and smtp_port == 465
    start_tls = smtp_use_tls and smtp_port != 465

    await aiosmtplib.send(
        msg,
        hostname=smtp_host,
        port=smtp_port,
        username=smtp_user,
        password=smtp_password,
        use_tls=use_tls,
        start_tls=start_tls,
        timeout=10,
    )


async def send_password_reset_email(
    to_email: str,
    code: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    smtp_from: str,
    smtp_use_tls: bool = True,
) -> None:
    """Send a password reset code email via SMTP."""
    msg = EmailMessage()
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg["Subject"] = f"Сброс пароля: {code}"
    msg.set_content(
        f"Код для сброса пароля в Broadcaster: {code}\n\n"
        f"Код действителен 10 минут.\n\n"
        f"Если вы не запрашивали сброс пароля, проигнорируйте это письмо."
    )

    use_tls = smtp_use_tls and smtp_port == 465
    start_tls = smtp_use_tls and smtp_port != 465

    await aiosmtplib.send(
        msg,
        hostname=smtp_host,
        port=smtp_port,
        username=smtp_user,
        password=smtp_password,
        use_tls=use_tls,
        start_tls=start_tls,
        timeout=10,
    )

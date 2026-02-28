import pytest
from unittest.mock import AsyncMock, patch

from app.services.email_service import send_verification_email, send_password_reset_email


@pytest.mark.asyncio
async def test_send_verification_email_calls_smtp():
    with patch("app.services.email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = ({}, "OK")
        await send_verification_email(
            to_email="user@example.com",
            code="123456",
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="sender@test.com",
            smtp_password="pass",
            smtp_from="noreply@test.com",
            smtp_use_tls=True,
        )
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args
        message = call_kwargs.args[0]
        assert "123456" in str(message)
        assert message["To"] == "user@example.com"
        assert message["From"] == "noreply@test.com"


@pytest.mark.asyncio
async def test_send_password_reset_email_calls_smtp():
    with patch("app.services.email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = ({}, "OK")
        await send_password_reset_email(
            to_email="user@example.com",
            code="654321",
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="sender@test.com",
            smtp_password="pass",
            smtp_from="noreply@test.com",
            smtp_use_tls=True,
        )
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args
        message = call_kwargs.args[0]
        assert "654321" in str(message)
        assert message["To"] == "user@example.com"
        assert "Сброс" in message["Subject"]

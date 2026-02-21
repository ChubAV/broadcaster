import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.messengers.telegram_bot import TelegramBotMessenger


@pytest.mark.asyncio
async def test_send_text_message():
    messenger = TelegramBotMessenger("123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
    messenger.bot = AsyncMock()
    messenger.bot.send_message = AsyncMock()

    result = await messenger.send_message("-100123", "Hello!")

    assert result["ok"] is True
    messenger.bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_with_image():
    messenger = TelegramBotMessenger("123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
    messenger.bot = AsyncMock()
    messenger.bot.send_photo = AsyncMock()

    result = await messenger.send_message("-100123", "Hello!", images=["path/to/img.jpg"])

    assert result["ok"] is True
    messenger.bot.send_photo.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_with_multiple_images():
    messenger = TelegramBotMessenger("123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
    messenger.bot = AsyncMock()
    messenger.bot.send_media_group = AsyncMock()

    result = await messenger.send_message("-100123", "Hello!", images=["img1.jpg", "img2.jpg", "img3.jpg"])

    assert result["ok"] is True
    messenger.bot.send_media_group.assert_called_once()
    media = messenger.bot.send_media_group.call_args.kwargs["media"]
    assert len(media) == 3


@pytest.mark.asyncio
async def test_send_message_error():
    messenger = TelegramBotMessenger("123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
    messenger.bot = AsyncMock()
    messenger.bot.send_message = AsyncMock(side_effect=Exception("Rate limited"))

    result = await messenger.send_message("-100123", "Hello!")

    assert result["ok"] is False
    assert "Rate limited" in result["error"]


@pytest.mark.asyncio
async def test_check_connection_success():
    messenger = TelegramBotMessenger("123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
    messenger.bot = AsyncMock()
    messenger.bot.get_me = AsyncMock()

    assert await messenger.check_connection() is True


@pytest.mark.asyncio
async def test_check_connection_failure():
    messenger = TelegramBotMessenger("123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
    messenger.bot = AsyncMock()
    messenger.bot.get_me = AsyncMock(side_effect=Exception("Invalid token"))

    assert await messenger.check_connection() is False

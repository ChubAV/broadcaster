"""Гард подлинности вебхука ЮKassa по адресу источника (T-05-01).

До этой фазы `POST /api/billing/webhook` не был защищён ничем: любой POST с
угаданным `yookassa_payment_id` проводил платёж. Тесты здесь проверяют НАСТОЯЩИЙ
путь чтения адреса — тот же заголовок, который читает боевой код, — а не
подставляют адрес в обход гарда: тест, проверяющий фикцию, зелен и при
сломанном гарде.
"""
from unittest.mock import AsyncMock, patch

import pytest

# Один из десяти боевых адресов ЮKassa (SecurityHelper.YOOKASSA_NETWORKS).
TRUSTED_IP = "77.75.156.11"
# TEST-NET-3 (RFC 5737) — адрес, зарезервированный под документацию, поэтому
# он заведомо не станет боевым адресом ЮKassa ни при каком обновлении SDK.
UNTRUSTED_IP = "203.0.113.7"

IP_HEADER = "X-Real-IP"
SUCCEEDED_BODY = {"event": "payment.succeeded", "object": {"id": "yoo_1"}}


@pytest.mark.asyncio
async def test_a_trusted_source_reaches_the_handler(client, test_settings):
    test_settings.yookassa_webhook_verify_ip = True
    test_settings.yookassa_webhook_client_ip_header = IP_HEADER

    with patch(
        "app.routes.billing.handle_webhook", new_callable=AsyncMock, return_value=True
    ) as handler:
        response = await client.post(
            "/api/billing/webhook",
            json=SUCCEEDED_BODY,
            headers={IP_HEADER: TRUSTED_IP},
        )

    assert response.status_code == 200
    handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_an_untrusted_source_is_rejected(client, test_settings):
    test_settings.yookassa_webhook_verify_ip = True
    test_settings.yookassa_webhook_client_ip_header = IP_HEADER

    with patch(
        "app.routes.billing.handle_webhook", new_callable=AsyncMock
    ) as handler:
        response = await client.post(
            "/api/billing/webhook",
            json=SUCCEEDED_BODY,
            headers={IP_HEADER: UNTRUSTED_IP},
        )

    assert response.status_code == 403
    handler.assert_not_awaited(), "недоверенный источник не должен доходить до обработки"


@pytest.mark.asyncio
async def test_the_kill_switch_lets_any_source_through(client, test_settings):
    """Аварийный выключатель: приём денег важнее проверки, если она слепа."""
    test_settings.yookassa_webhook_verify_ip = False
    test_settings.yookassa_webhook_client_ip_header = IP_HEADER

    with patch(
        "app.routes.billing.handle_webhook", new_callable=AsyncMock, return_value=True
    ) as handler:
        response = await client.post(
            "/api/billing/webhook",
            json=SUCCEEDED_BODY,
            headers={IP_HEADER: UNTRUSTED_IP},
        )

    assert response.status_code == 200
    handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_a_missing_source_address_is_untrusted(client, test_settings):
    """Заголовок настроен, но не пришёл — это ОТКАЗ, а не «доверять всем»."""
    test_settings.yookassa_webhook_verify_ip = True
    test_settings.yookassa_webhook_client_ip_header = IP_HEADER

    with patch("app.routes.billing.handle_webhook", new_callable=AsyncMock) as handler:
        response = await client.post("/api/billing/webhook", json=SUCCEEDED_BODY)

    assert response.status_code == 403
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_an_unparseable_source_address_is_untrusted(client, test_settings):
    """Мусор в заголовке — 403, а не 500 от разбора адреса."""
    test_settings.yookassa_webhook_verify_ip = True
    test_settings.yookassa_webhook_client_ip_header = IP_HEADER

    with patch("app.routes.billing.handle_webhook", new_callable=AsyncMock) as handler:
        response = await client.post(
            "/api/billing/webhook",
            json=SUCCEEDED_BODY,
            # Значение ASCII: заголовки HTTP не переносят иных байтов вовсе,
            # и мусор здесь обязан быть таким, какой реально дойдёт до кода.
            headers={IP_HEADER: "not-an-address"},
        )

    assert response.status_code == 403
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_the_body_is_not_parsed_before_the_guard_runs(client, test_settings):
    """Недоверенный источник не доходит даже до разбора тела.

    Тело намеренно НЕ является валидным JSON. Разбирайся оно до гарда,
    исключение ушло бы в `except Exception` обработчика и вернуло 500 — ответ
    403 доказывает, что гард отработал первым.
    """
    test_settings.yookassa_webhook_verify_ip = True
    test_settings.yookassa_webhook_client_ip_header = IP_HEADER

    response = await client.post(
        "/api/billing/webhook",
        content=b"{ not json at all",
        headers={IP_HEADER: UNTRUSTED_IP, "Content-Type": "application/json"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_a_forged_leftmost_element_does_not_grant_trust(client, test_settings):
    """Список адресов читается СПРАВА, а не слева.

    Заголовок со списком растёт слева направо, и левый элемент подставляет сам
    клиент — nginx лишь дописывает реальный адрес пира СПРАВА. Возьми гард
    левый элемент, любой желающий подделал бы успешный платёж, просто прислав
    доверенный адрес первым. Правый элемент — тот, который проставил свой прокси.
    """
    test_settings.yookassa_webhook_verify_ip = True
    test_settings.yookassa_webhook_client_ip_header = IP_HEADER

    with patch("app.routes.billing.handle_webhook", new_callable=AsyncMock) as handler:
        response = await client.post(
            "/api/billing/webhook",
            json=SUCCEEDED_BODY,
            headers={IP_HEADER: f"{TRUSTED_IP}, {UNTRUSTED_IP}"},
        )

    assert response.status_code == 403
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_without_a_configured_header_the_peer_address_is_used(
    client, test_settings
):
    """Пустая настройка = читать `request.client.host` напрямую.

    Так работает локальный запуск без прокси и вся суита: адрес пира тестового
    транспорта не входит в сети ЮKassa, поэтому ожидается отказ.
    """
    test_settings.yookassa_webhook_verify_ip = True
    test_settings.yookassa_webhook_client_ip_header = ""

    with patch("app.routes.billing.handle_webhook", new_callable=AsyncMock) as handler:
        response = await client.post("/api/billing/webhook", json=SUCCEEDED_BODY)

    assert response.status_code == 403
    handler.assert_not_awaited()

"""Гард источника вебхука в СБОРКЕ, идентичной боевой (гэп 1, план 05-07).

ЗАЧЕМ ЭТОТ ФАЙЛ ОТДЕЛЬНО ОТ `test_billing_webhook_source.py`. Тот проверяет
ЛОГИКУ гарда на голом приложении: как разбирается настроенный заголовок, какой
элемент списка берётся, что бывает с мусором. Этот проверяет другое — что логика
вообще ИСПОЛНЯЕТСЯ в той сборке, которая едет на бой.

Разница не академическая, она и была дырой. Суита была зелёной ровно потому, что
её транспорт до `ProxyHeadersMiddleware` не доходил: `ASGITransport` поверх
приложения оставляет `scope["client"]` тестовым адресом. Боевой uvicorn запущен с
`--forwarded-allow-ips=*` (`docker-compose.prod.yml`), и в этой сборке
`scope["client"]` — это ЛЕВЫЙ элемент `X-Forwarded-For`, то есть значение,
которое присылает сам вызывающий. Правильное чтение справа в проде не
исполнялось ни разу: до него не доходило управление, потому что пустое умолчание
имени заголовка уводило в ветку адреса пира.

Поэтому здесь приложение оборачивается НАСТОЯЩИМ `ProxyHeadersMiddleware` из
uvicorn тем же конструктором, который uvicorn вызывает по флагу
`--forwarded-allow-ips=*` (`trusted_hosts="*"` → `_TrustedHosts.always_trust`,
`get_trusted_client_host` возвращает `x_forwarded_for_hosts[0]`), и транспорт
теста ставится поверх ОБЁРТКИ, а не поверх приложения.

Оба файла нужны. Логика без сборки — доказательство о коде, который не
исполняется; сборка без логики — доказательство, что 403 приходит, но неизвестно
по какой причине.
"""
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.main import create_app

# Те же константы, что в test_billing_webhook_source.py.
# Один из десяти боевых адресов ЮKassa (SecurityHelper.YOOKASSA_NETWORKS).
TRUSTED_IP = "77.75.156.11"
# TEST-NET-3 (RFC 5737) — адрес под документацию, поэтому он заведомо не станет
# боевым адресом ЮKassa ни при каком обновлении SDK.
UNTRUSTED_IP = "203.0.113.7"

IP_HEADER = "X-Real-IP"
SUCCEEDED_BODY = {"event": "payment.succeeded", "object": {"id": "yoo_1"}}


@pytest_asyncio.fixture
async def proxied_client(db_session, test_settings):
    """Клиент, ходящий в приложение ЧЕРЕЗ ProxyHeadersMiddleware.

    Подмены зависимостей — те же, что у фикстуры `client` в `tests/conftest.py`;
    отличие ровно одно и оно и есть предмет файла: транспорт ставится поверх
    обёртки, поэтому `scope["client"]` к моменту обработчика уже переписан из
    `X-Forwarded-For`, как это происходит на бою.
    """
    app = create_app(settings=test_settings)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: test_settings
    proxied = ProxyHeadersMiddleware(app, trusted_hosts="*")
    transport = ASGITransport(app=proxied)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_a_forged_x_forwarded_for_does_not_grant_trust(
    proxied_client, test_settings
):
    """Гэп 1 целиком: подделанный `X-Forwarded-For` не проводит платёж.

    До правки этот запрос отдавал 200: middleware переписывал адрес пира левым
    элементом заголовка, пустая настройка уводила гард в ветку адреса пира, и
    подделанный адрес ЮKassa проходил проверку как настоящий.
    """
    test_settings.yookassa_webhook_verify_ip = True
    test_settings.yookassa_webhook_client_ip_header = ""

    with patch(
        "app.routes.billing.handle_webhook", new_callable=AsyncMock, return_value=True
    ) as handler:
        response = await proxied_client.post(
            "/api/billing/webhook",
            json=SUCCEEDED_BODY,
            headers={"X-Forwarded-For": TRUSTED_IP},
        )

    assert response.status_code == 403
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_forged_x_forwarded_for_list_does_not_grant_trust(
    proxied_client, test_settings
):
    """Список в `X-Forwarded-For` — та же подделка, просто длиннее.

    При доверии всем пирам uvicorn берёт ЛЕВЫЙ элемент, то есть ровно тот,
    который подставляет вызывающий.
    """
    test_settings.yookassa_webhook_verify_ip = True
    test_settings.yookassa_webhook_client_ip_header = ""

    with patch(
        "app.routes.billing.handle_webhook", new_callable=AsyncMock, return_value=True
    ) as handler:
        response = await proxied_client.post(
            "/api/billing/webhook",
            json=SUCCEEDED_BODY,
            headers={"X-Forwarded-For": f"{TRUSTED_IP}, {UNTRUSTED_IP}"},
        )

    assert response.status_code == 403
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_an_unconfigured_header_refuses_even_a_bare_request(
    proxied_client, test_settings
):
    """Пустая настройка = ОТКАЗ каждому уведомлению, а не доверие адресу пира.

    Отказ по умолчанию закрывает гард, а не открывает его: ненастроенный
    источник — это «источник не подтверждён», и подтвердить его нечем.
    """
    test_settings.yookassa_webhook_verify_ip = True
    test_settings.yookassa_webhook_client_ip_header = ""

    with patch(
        "app.routes.billing.handle_webhook", new_callable=AsyncMock, return_value=True
    ) as handler:
        response = await proxied_client.post(
            "/api/billing/webhook", json=SUCCEEDED_BODY
        )

    assert response.status_code == 403
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_an_unconfigured_header_is_reported_at_error_level(
    proxied_client, test_settings
):
    """Молча остановленный приём денег неотличим от отсутствия платежей.

    Уровень именно `error`, а не `warning`: этот отказ отвергает ВСЕ настоящие
    уведомления, и в потоке предупреждений он потерялся бы.
    """
    test_settings.yookassa_webhook_verify_ip = True
    test_settings.yookassa_webhook_client_ip_header = ""

    with patch("app.routes.billing.logger") as logger:
        await proxied_client.post("/api/billing/webhook", json=SUCCEEDED_BODY)

    assert logger.error.called, "отказ по ненастроенному заголовку обязан быть в журнале"
    keys = [call.args[0] for call in logger.error.call_args_list if call.args]
    assert "webhook_ip_header_not_configured" in keys


@pytest.mark.asyncio
async def test_the_configured_header_with_a_trusted_address_reaches_the_handler(
    proxied_client, test_settings
):
    """Гард закрыт, а не сломан: настоящее уведомление по-прежнему проходит."""
    test_settings.yookassa_webhook_verify_ip = True
    test_settings.yookassa_webhook_client_ip_header = IP_HEADER

    with patch(
        "app.routes.billing.handle_webhook", new_callable=AsyncMock, return_value=True
    ) as handler:
        response = await proxied_client.post(
            "/api/billing/webhook",
            json=SUCCEEDED_BODY,
            headers={IP_HEADER: TRUSTED_IP},
        )

    assert response.status_code == 200
    handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_only_the_configured_header_grants_trust_never_the_peer_address(
    proxied_client, test_settings
):
    """Настроенный заголовок недоверен, а подделанный `X-Forwarded-For` — доверен.

    Единственный источник доверия — заголовок, который ПЕРЕЗАПИСЫВАЕТ свой
    прокси. Адрес пира не служит источником ни при какой настройке, поэтому
    подделка обязана проиграть настроенному заголовку, а не победить его.
    """
    test_settings.yookassa_webhook_verify_ip = True
    test_settings.yookassa_webhook_client_ip_header = IP_HEADER

    with patch(
        "app.routes.billing.handle_webhook", new_callable=AsyncMock, return_value=True
    ) as handler:
        response = await proxied_client.post(
            "/api/billing/webhook",
            json=SUCCEEDED_BODY,
            headers={IP_HEADER: UNTRUSTED_IP, "X-Forwarded-For": TRUSTED_IP},
        )

    assert response.status_code == 403
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_the_configured_header_is_still_read_from_the_right(
    proxied_client, test_settings
):
    """Чтение настроенного заголовка справа налево правкой не тронуто."""
    test_settings.yookassa_webhook_verify_ip = True
    test_settings.yookassa_webhook_client_ip_header = IP_HEADER

    with patch(
        "app.routes.billing.handle_webhook", new_callable=AsyncMock, return_value=True
    ) as handler:
        response = await proxied_client.post(
            "/api/billing/webhook",
            json=SUCCEEDED_BODY,
            headers={IP_HEADER: f"{TRUSTED_IP}, {UNTRUSTED_IP}"},
        )

    assert response.status_code == 403
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_the_kill_switch_still_lets_any_source_through(
    proxied_client, test_settings
):
    """Аварийный выключатель жив и в боевой сборке.

    Он существует потому, что ошибка настройки заголовка отвергает ВСЕ настоящие
    уведомления. После смены умолчания цена такой ошибки не изменилась, поэтому
    выключатель обязан остаться единственной правкой окружения, возвращающей
    приём денег без выката кода.
    """
    test_settings.yookassa_webhook_verify_ip = False
    test_settings.yookassa_webhook_client_ip_header = ""

    with patch(
        "app.routes.billing.handle_webhook", new_callable=AsyncMock, return_value=True
    ) as handler:
        response = await proxied_client.post(
            "/api/billing/webhook",
            json=SUCCEEDED_BODY,
            headers={"X-Forwarded-For": UNTRUSTED_IP},
        )

    assert response.status_code == 200
    handler.assert_awaited_once()


def test_the_shipped_default_header_name_is_x_real_ip():
    """Умолчание закрывает гард само, без записи в окружении.

    `X-Real-IP` выбран не произвольно: nginx проекта ставит его `$remote_addr`-ом
    на КАЖДОМ location (`nginx/nginx.conf.template`), то есть затирает всё, что
    прислал клиент. Заголовок, который прокси лишь ДОПИСЫВАЕТ, такой гарантии не
    даёт, и умолчанием служить не может.

    `_env_file=None` отключает `.env` рабочего каталога; `database_url` и
    `secret_key` обязательны у модели и передаются явно — иначе конструктор
    падает на валидации ещё до того, как проверяемое умолчание будет прочитано.
    """
    settings = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test-secret-key",
    )

    assert settings.yookassa_webhook_client_ip_header == "X-Real-IP"

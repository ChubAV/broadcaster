"""Регрессия Mixed Content: страница по HTTPS не должна подключать статику по http://.

Механика дефекта. `url_for('static', …)` в Starlette отдаёт АБСОЛЮТНЫЙ адрес и
берёт схему из `scope["scheme"]`. За обратным прокси эту схему выставляет
`uvicorn.middleware.proxy_headers.ProxyHeadersMiddleware`, читая
`X-Forwarded-Proto` — но ТОЛЬКО если IP клиента входит в `--forwarded-allow-ips`.
Дефолт uvicorn — `127.0.0.1`, а в Docker nginx приходит с адреса bridge-сети
(172.x.x.x). Заголовок отбрасывается молча, схема остаётся `http`, браузер
блокирует CSS и JS.

Поэтому тесты проверяют не разметку, а СВЯЗКУ «прод-команда uvicorn → схема в
отрендеренной странице»: доверенный список читается из docker-compose.prod.yml,
и сужение флага обратно до loopback роняет поведенческие тесты.
"""

import re
import shlex
from pathlib import Path

import pytest
import pytest_asyncio
import yaml
from httpx import ASGITransport, AsyncClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.dependencies import get_db, get_settings
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]
PROD_COMPOSE = REPO_ROOT / "docker-compose.prod.yml"

# Каким uvicorn видит контейнер nginx: адрес docker-сети broadcaster, не loopback.
NGINX_CONTAINER_IP = "172.20.0.7"
PUBLIC_HOST = "broadcaster.all-torgi.ru"

UVICORN_DEFAULT_FORWARDED_ALLOW_IPS = "127.0.0.1"

# <script src> и <link href> — ровно те теги, что перечислены в отчёте о баге.
ASSET_REF_RE = re.compile(r'<(?:script|link)\b[^>]*?(?:src|href)="([^"]+)"', re.I)

# Файлы из консоли браузера: app.css, htmx.min.js, alpine.min.js.
BLOCKED_ASSETS = ("/static/css/app.css", "/static/js/htmx.min.js", "/static/js/alpine.min.js")


def _web_argv() -> list[str]:
    """argv сервиса web из прод-компоуза (строковая и списковая форма command)."""
    compose = yaml.safe_load(PROD_COMPOSE.read_text(encoding="utf-8"))
    command = compose["services"]["web"]["command"]
    return command if isinstance(command, list) else shlex.split(command)


def prod_forwarded_allow_ips() -> str:
    """Значение --forwarded-allow-ips из прод-команды, иначе дефолт uvicorn."""
    argv = _web_argv()
    for index, arg in enumerate(argv):
        if arg.startswith("--forwarded-allow-ips="):
            return arg.split("=", 1)[1]
        if arg == "--forwarded-allow-ips":
            return argv[index + 1]
    return UVICORN_DEFAULT_FORWARDED_ALLOW_IPS


def static_asset_refs(html: str) -> list[str]:
    return [ref for ref in ASSET_REF_RE.findall(html) if "/static/" in ref]


def assert_assets_use(html: str, scheme: str, label: str) -> None:
    """Все ссылки на статику идут по указанной схеме, и все три файла на месте."""
    refs = static_asset_refs(html)
    assert refs, f"{label}: на странице нет ни одной ссылки на /static/"

    wrong_scheme = "http://" if scheme == "https" else "https://"
    offenders = [ref for ref in refs if ref.startswith(wrong_scheme)]
    assert not offenders, f"{label}: ожидалась схема {scheme}://, получено {offenders}"

    for asset in BLOCKED_ASSETS:
        expected_prefix = f"{scheme}://{PUBLIC_HOST}{asset}"
        assert any(ref.startswith(expected_prefix) for ref in refs), (
            f"{label}: нет ссылки {expected_prefix} среди {refs}"
        )


@pytest_asyncio.fixture
async def behind_proxy(db_session, test_settings):
    """Фабрика клиента, повторяющего прод-стек: nginx → ProxyHeadersMiddleware → app.

    trusted_hosts по умолчанию берётся из docker-compose.prod.yml, поэтому
    поведенческие проверки привязаны к реально задеплоенной команде запуска.
    """

    clients = []

    async def _make(*, forwarded_proto: str = "https", trusted_hosts: str | None = None):
        app = create_app(settings=test_settings)
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_settings] = lambda: test_settings

        asgi = ProxyHeadersMiddleware(
            app,
            trusted_hosts=prod_forwarded_allow_ips() if trusted_hosts is None else trusted_hosts,
        )
        client = AsyncClient(
            # nginx ходит на upstream по обычному http — https знает только заголовок
            transport=ASGITransport(app=asgi, client=(NGINX_CONTAINER_IP, 51234)),
            base_url=f"http://{PUBLIC_HOST}",
            headers={
                "X-Forwarded-Proto": forwarded_proto,
                "X-Forwarded-For": "203.0.113.9",
            },
        )
        clients.append(client)
        await client.__aenter__()
        return client

    yield _make

    for client in clients:
        await client.__aexit__(None, None, None)


async def _login(client: AsyncClient) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "https@test.com", "password": "testpass123", "name": "HTTPS User"},
    )
    await client.post(
        "/login",
        data={"email": "https@test.com", "password": "testpass123"},
        follow_redirects=False,
    )


# --- Контракт деплоя ---------------------------------------------------------


def test_prod_uvicorn_is_told_to_trust_the_proxy():
    """Прод-команда uvicorn обязана расширять --forwarded-allow-ips за loopback."""
    argv = _web_argv()
    assert any(arg.startswith("--forwarded-allow-ips") for arg in argv), (
        "docker-compose.prod.yml: web.command без --forwarded-allow-ips — "
        f"uvicorn доверяет только {UVICORN_DEFAULT_FORWARDED_ALLOW_IPS} и отбросит "
        f"X-Forwarded-Proto от nginx. Текущая команда: {' '.join(argv)}"
    )
    assert prod_forwarded_allow_ips() != UVICORN_DEFAULT_FORWARDED_ALLOW_IPS, (
        "--forwarded-allow-ips сужен до loopback: контейнер nginx под это не подходит"
    )


# --- Поведение: страница за TLS-прокси --------------------------------------


@pytest.mark.asyncio
async def test_auth_page_behind_tls_proxy_emits_https_assets(behind_proxy):
    """auth_base.html: /login отдан по HTTPS → статика тоже по HTTPS."""
    client = await behind_proxy()
    response = await client.get("/login")

    assert response.status_code == 200
    assert_assets_use(response.text, "https", "/login")


@pytest.mark.asyncio
async def test_shell_page_behind_tls_proxy_emits_https_assets(behind_proxy):
    """base.html: именно /dashboard из отчёта о баге."""
    client = await behind_proxy()
    await _login(client)
    response = await client.get("/dashboard")

    assert response.status_code == 200
    assert_assets_use(response.text, "https", "/dashboard")


@pytest.mark.asyncio
async def test_no_mixed_content_on_dashboard(behind_proxy):
    """Дословная проверка симптома: ни одного http:// ресурса на HTTPS-странице."""
    client = await behind_proxy()
    await _login(client)
    html = (await client.get("/dashboard")).text

    insecure = [ref for ref in ASSET_REF_RE.findall(html) if ref.startswith("http://")]
    assert not insecure, f"Mixed Content: {insecure}"


# --- Границы: не подменять схему вслепую ------------------------------------


@pytest.mark.asyncio
async def test_plain_http_request_still_emits_http_assets(behind_proxy):
    """X-Forwarded-Proto: http → статика по http.

    Соседний случай той же ветки: схема обязана СЛЕДОВАТЬ за запросом. Если её
    просто зашить в https, ляжет доступ по HTTP (в том числе ACME-редиректы и
    локальный прогон без TLS), а тест это поймает.
    """
    client = await behind_proxy(forwarded_proto="http")
    response = await client.get("/login")

    assert response.status_code == 200
    assert_assets_use(response.text, "http", "/login по http")


# --- Инвертированный сторож: дефект остаётся проверяемым ---------------------


@pytest.mark.asyncio
async def test_loopback_only_trust_reproduces_the_defect(behind_proxy):
    """С дефолтным доверием только к 127.0.0.1 баг обязан воспроизводиться.

    Это RED-условие в постоянно проверяемой форме. Если тест однажды упадёт,
    значит uvicorn сменил дефолт (или мидлварь) — и флаг в компоузе пора
    пересматривать, а не молча тащить дальше.
    """
    client = await behind_proxy(trusted_hosts=UVICORN_DEFAULT_FORWARDED_ALLOW_IPS)
    html = (await client.get("/login")).text

    refs = static_asset_refs(html)
    assert refs
    assert all(ref.startswith("http://") for ref in refs), (
        f"Недоверенный прокси больше не понижает схему до http: {refs}"
    )

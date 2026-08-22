"""Каркас админ-панели: шесть подразделов — МАРШРУТЫ, а не состояния экрана.

Файл держит три архитектурных решения фазы, каждое из которых дороже исправить
после десяти планов, чем после одного:

1. **Подраздел есть маршрут (D-01).** Проверяется тем, что разметка вкладок не
   несёт ни атрибутов HTMX, ни обработчиков Alpine: при выключенном JS
   переключение подраздела обязано работать. HTMX в фазе применяется ВНУТРИ
   подраздела, но никогда — для его смены.
2. **Docker при рендере не зовётся (D-07).** Утверждение снимается РАЗБОРОМ
   исходника по синтаксическому дереву, а не поиском строки и не наблюдением за
   страницей: поиск строки считает вхождение и в комментарии, и в докстринге, а
   наблюдение зелено ровно до того дня, когда демон недоступен.
3. **Живость приезжает из Redis через сервис.** Подраздел «Воркеры» проверяется
   с ПОДМЕНЁННЫМ клиентом — ни один тест не требует поднятой внешней службы.

Плюс страховочная сетка сноса справочника групп (D-05): ни один шаблон и ни один
маршрут собранного приложения не ссылается на снесённый адрес.
"""
import ast
import re
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messenger_account import MessengerAccount
from app.pages.admin import ADMIN_TABS

ADMIN_PAGES_SOURCE = Path("app/pages/admin.py")
TABS_TEMPLATE = Path("app/templates/admin/includes/_tabs.html")
TEMPLATES_ROOT = Path("app/templates")

SUBSECTION_URLS = tuple(tab["href"] for tab in ADMIN_TABS)

# Признаки клиентских библиотек. Любой из них в разметке вкладок означал бы, что
# смена подраздела перестала быть переходом по ссылке.
CLIENT_LIB_MARKERS = ("hx-", "x-data", "x-on:", "@click", ":class")


async def _seed_account(
    db_session: AsyncSession, account_type: str = "wa", status: str = "active"
) -> MessengerAccount:
    """Мессенджер-аккаунт под существующим пользователем.

    Пользователя создаёт фикстура admin_client через регистрацию, поэтому
    идентификатор владельца берётся первым существующим.
    """
    from sqlalchemy import select
    from app.models.user import User

    user = (await db_session.execute(select(User))).scalars().first()
    account = MessengerAccount(
        user_id=user.id,
        type=account_type,
        credentials="{}",
        status=status,
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account


def _fake_redis(values: list):
    pipe = MagicMock()
    pipe.get = MagicMock(return_value=pipe)
    pipe.llen = MagicMock(return_value=pipe)
    pipe.execute = AsyncMock(return_value=values)
    client = MagicMock()
    client.pipeline = MagicMock(return_value=pipe)
    return client


# ---- Каркас шести подразделов ----

@pytest.mark.asyncio
async def test_six_subsections_answer_the_admin(admin_client: AsyncClient):
    """Все шесть адресов отвечают 200 администратору."""
    assert len(SUBSECTION_URLS) == 6
    for url in SUBSECTION_URLS:
        response = await admin_client.get(url)
        assert response.status_code == 200, url


@pytest.mark.asyncio
async def test_six_subsections_denied_for_regular_user(authed_client: AsyncClient):
    """Все шесть адресов отвечают 403 постороннему (T-06-01).

    Пять маршрутов заведены этим планом, и зависимость администратора на каждом
    из них — не формальность: без неё привилегированные чтения о ЧУЖИХ учётных
    записях открылись бы любому вошедшему.
    """
    for url in SUBSECTION_URLS:
        response = await authed_client.get(url)
        assert response.status_code == 403, url


@pytest.mark.asyncio
async def test_subsection_navigation_degrades_without_js(admin_client: AsyncClient):
    """Вкладки — ссылки: ни HTMX, ни Alpine в разметке переключения нет (D-01).

    Утверждение снимается и с ФАЙЛА, и с отданной страницы: атрибут, дописанный
    обработчиком в контекст, в файле бы не нашёлся.
    """
    source = TABS_TEMPLATE.read_text(encoding="utf-8")
    for marker in CLIENT_LIB_MARKERS:
        assert marker not in source, f"_tabs.html: {marker}"

    html = (await admin_client.get("/admin/workers")).text
    tabs_markup = html[html.index("<nav data-subtabs") : html.index("</nav>", html.index("<nav data-subtabs"))]
    for marker in CLIENT_LIB_MARKERS:
        assert marker not in tabs_markup, f"отданная разметка вкладок: {marker}"


@pytest.mark.asyncio
async def test_tabs_render_six_real_links(admin_client: AsyncClient):
    """Отданная разметка вкладок — ШЕСТЬ якорей с адресами подразделов.

    Проверка идёт по отданной разметке, а не по числу строк с `href` в файле:
    перечень объявлен ОДИН раз (`ADMIN_TABS`), и шаблон обходит его циклом —
    шесть выписанных в шаблоне ссылок были бы второй копией подписей и
    разъехались бы с первой молча.
    """
    html = (await admin_client.get("/admin")).text
    start = html.index("<nav data-subtabs")
    tabs_markup = html[start : html.index("</nav>", start)]

    hrefs = re.findall(r'<a class="subtab" href="([^"]+)"', tabs_markup)
    assert hrefs == list(SUBSECTION_URLS)
    for tab in ADMIN_TABS:
        assert tab["label"] in tabs_markup, tab["label"]


@pytest.mark.asyncio
async def test_active_subsection_is_marked_exactly_once(admin_client: AsyncClient):
    """Признак активной вкладки встречается на странице РОВНО один раз.

    Признак свой (`data-subtab-active`), а не признак сайдбара или нижних
    табов: переиспользование чужого сделало бы «активный подраздел»
    неотличимым от «активного раздела».
    """
    for url in SUBSECTION_URLS:
        html = (await admin_client.get(url)).text
        assert html.count("data-subtab-active") == 1, url


@pytest.mark.asyncio
async def test_admin_section_stays_highlighted_in_the_sidebar(
    admin_client: AsyncClient,
):
    """Раздел «Админ-панель» подсвечен в сайдбаре на всех шести адресах."""
    for url in SUBSECTION_URLS:
        html = (await admin_client.get(url)).text
        assert 'class="nav-item is-active"' in html, url
        assert 'href="/admin"' in html, url


def test_all_six_subsection_templates_include_the_same_tabs():
    """Одни вкладки на шесть шаблонов — вторая копия разъехалась бы молча."""
    for name in ("overview", "users", "workers", "queue", "logs", "payments"):
        template = TEMPLATES_ROOT / "admin" / f"{name}.html"
        assert template.exists(), template
        assert "admin/includes/_tabs.html" in template.read_text(encoding="utf-8"), name


# ---- Docker не трогается при рендере (D-07, T-06-03) ----

def test_no_docker_client_on_the_render_path():
    """Разбор ДЕРЕВА исходника: ни один обработчик не зовёт клиент контейнеров.

    Поиск строки считал бы вхождение и в комментарии, и в докстринге — то есть
    объяснение, ПОЧЕМУ вызова нет, роняло бы тест, утверждающий, что вызова
    нет. Поэтому проверяются имена в дереве: импорты и обращения к атрибутам.
    """
    tree = ast.parse(ADMIN_PAGES_SOURCE.read_text(encoding="utf-8"))

    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
            imported += [alias.name for alias in node.names]
    assert not [name for name in imported if "docker" in name.lower()], imported

    called: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                called.append(target.id)
            elif isinstance(target, ast.Attribute):
                called.append(target.attr)
    assert not [name for name in called if "docker" in name.lower()], called


# ---- Подраздел «Воркеры» на живых данных ----

@pytest.mark.asyncio
async def test_workers_subsection_shows_idle_account_row(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Аккаунт без heartbeat и с ПУСТОЙ очередью показан ПРОСТАИВАЮЩИМ (D-08).

    Отключённым он показан только при непустой очереди: воркер уходит сам через
    300 секунд простоя, и отсутствие контейнера здесь — норма, а не отказ.
    """
    account = await _seed_account(db_session, account_type="wa")
    stale = str(int((time.time() - 600) * 1000))

    with patch(
        "app.services.ops_state._get_redis", return_value=_fake_redis([stale, 0])
    ):
        response = await admin_client.get("/admin/workers")

    assert response.status_code == 200
    html = response.text
    assert f"#{account.id}" in html, "строка аккаунта не отрисовалась"
    assert "простаивает" in html
    # Строчная форма приходит ТОЛЬКО из колонки воркера: состояние сессии здесь
    # «Активно», а бейдж сессии пишется с прописной.
    assert "отключён" not in html


@pytest.mark.asyncio
async def test_workers_subsection_shows_offline_only_with_pending_queue(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Несвежий heartbeat при НЕПУСТОЙ очереди — «отключён»: работать некому."""
    await _seed_account(db_session, account_type="wa")
    stale = str(int((time.time() - 600) * 1000))

    with patch(
        "app.services.ops_state._get_redis", return_value=_fake_redis([stale, 5])
    ):
        html = (await admin_client.get("/admin/workers")).text

    assert "отключён" in html
    assert "простаивает" not in html


@pytest.mark.asyncio
async def test_workers_subsection_keeps_session_and_worker_apart(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Колонки «Сессия» и «Воркер» независимы и печатаются обе.

    Контейнер с мёртвой сессией остаётся ЗАПУЩЕННЫМ: один бейдж на две
    величины врал бы про обе.
    """
    await _seed_account(db_session, account_type="wa", status="disconnected")
    fresh = str(int(time.time() * 1000))

    with patch(
        "app.services.ops_state._get_redis", return_value=_fake_redis([fresh, 0])
    ):
        html = (await admin_client.get("/admin/workers")).text

    assert "Сессия" in html and "Воркер" in html
    assert "в работе" in html, "живой воркер при мёртвой сессии не показан"


@pytest.mark.asyncio
async def test_workers_subsection_survives_unavailable_redis(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Недоступный Redis не роняет подраздел: 200 и «неизвестно» (T-06-02).

    Показать здесь «отключён» значило бы сообщить об аварии воркеров, когда
    сломан наблюдатель.
    """
    await _seed_account(db_session, account_type="wa")

    with patch("app.services.ops_state._get_redis", return_value=None):
        response = await admin_client.get("/admin/workers")

    assert response.status_code == 200
    assert "неизвестно" in response.text


@pytest.mark.asyncio
async def test_telegram_row_prints_a_dash_for_the_worker_column(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """У телеграм-аккаунта отдельного воркера нет — печатается прочерк.

    Выдуманный бейдж здесь читался бы как измеренное состояние. Честную
    подпись назначает план 06-05 чекпойнтом владельца.
    """
    account = await _seed_account(db_session, account_type="tg_user")

    with patch("app.services.ops_state._get_redis", return_value=_fake_redis([])):
        html = (await admin_client.get("/admin/workers")).text

    assert f"#{account.id}" in html
    assert "величина ещё не определена" in html


@pytest.mark.asyncio
async def test_workers_subsection_uses_row_primitives(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Строка собрана существующим примитивом, а не своей вёрсткой."""
    await _seed_account(db_session, account_type="wa")

    with patch("app.services.ops_state._get_redis", return_value=None):
        html = (await admin_client.get("/admin/workers")).text

    assert "data-row" in html
    assert "data-rowhead" in html


# ---- Данные-заглушки макета не доехали ----

@pytest.mark.asyncio
async def test_no_mockup_placeholder_numbers_reached_the_subsections(
    admin_client: AsyncClient,
):
    """Ни одно нарисованное в макете число не доехало до подразделов.

    Число из макета, дожившее до прода, читается администратором как
    ИЗМЕРЕННОЕ, и в аварии он примет решение по нарисованной цифре.
    """
    forbidden = ("621 000", "18 д 4 ч", "uptime", "восстановлен после рестарта")
    for url in SUBSECTION_URLS:
        html = (await admin_client.get(url)).text
        for marker in forbidden:
            assert marker not in html, f"{url}: {marker}"

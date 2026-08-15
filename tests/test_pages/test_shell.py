"""Wave 0: покрытие UI-01, UI-02, UI-03, UI-06 для нового шелла (План 01-01)."""

import ast
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import AD_STATUS_PUBLISHED
from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.user import User
from app.pages.common import get_shell_context
from tests.conftest import seed_group


# --- UI-01: своя статика вместо CDN -----------------------------------------

@pytest.mark.asyncio
async def test_app_css_served(client: AsyncClient):
    response = await client.get("/static/css/app.css")
    assert response.status_code == 200
    body = response.text
    assert ":root" in body
    assert "--accent" in body


@pytest.mark.asyncio
async def test_static_js_served(client: AsyncClient):
    for path in ("/static/js/htmx.min.js", "/static/js/alpine.min.js"):
        response = await client.get(path)
        assert response.status_code == 200, path
        # Вендоренные рантаймы: htmx ~47.7 КБ, Alpine ~43.4 КБ
        assert len(response.content) > 10_000, path


# --- D-04 / D-17: шрифты со своего домена -----------------------------------

@pytest.mark.asyncio
async def test_fonts_served(client: AsyncClient):
    fonts_dir = Path(__file__).resolve().parents[2] / "app" / "static" / "fonts"
    files = sorted(fonts_dir.glob("*.woff2"))
    assert len(files) >= 18
    for path in files:
        response = await client.get(f"/static/fonts/{path.name}")
        assert response.status_code == 200, path.name
        assert response.content[:4] == b"wOF2", path.name


@pytest.mark.asyncio
async def test_app_css_declares_fonts(client: AsyncClient):
    body = (await client.get("/static/css/app.css")).text
    assert "@font-face" in body
    # Основная текстовая гарнитура обязана содержать кириллицу (D-17)
    assert "IBM Plex Sans" in body
    assert "IBM Plex Mono" in body
    for token in ("--font-sans", "--font-mono", "--font-display"):
        assert token in body, token
    # Внешних шрифтовых запросов не осталось
    assert "fonts.googleapis.com" not in body
    assert "fonts.gstatic.com" not in body


# --- UI-02: новый шелл на странице ------------------------------------------

@pytest.mark.asyncio
async def test_profile_renders_new_shell(authed_client: AsyncClient):
    response = await authed_client.get("/profile")
    assert response.status_code == 200
    html = response.text
    for marker in ("data-shell", "data-side", "data-nav", "data-head", "data-body", "data-tabs"):
        assert marker in html, marker


# --- План 08: сплошной обход фазы -------------------------------------------
#
# Итоговое покрытие UI-01…UI-03. Список адресов — §Smoke-test routes из
# 01-VALIDATION.md: все страницы БЕЗ path-параметров. Адреса с параметрами
# покрываются точечно тестами Планов 05-08 и в общий обход не тянутся.

# Полные страницы обычного пользователя: отдают шелл целиком.
SHELL_ROUTES = (
    "/dashboard",
    "/ads",
    "/ads/new",
    "/accounts",
    "/accounts/connect/tg_user",
    "/accounts/connect/wa",
    "/accounts/connect/max",
    "/schedules",
    "/history",
    "/billing",
    "/profile",
)

# Страницы админ-панели: тот же шелл, но нужен admin_client.
ADMIN_SHELL_ROUTES = ("/admin", "/admin/users", "/admin/groups-info")

# Партиалы бесконечной прокрутки: это ФРАГМЕНТЫ, а не страницы — шелла у них
# нет по построению, поэтому data-shell с них не спрашивается. Но внешних
# ссылок и utility-классов в них быть не должно наравне со страницами.
PARTIAL_ROUTES = (
    "/ads/partial",
    "/accounts/partial",
    "/schedules/partial",
    "/history/partial",
)

# ОГРАНИЧЕНИЕ ОБХОДА СНЯТО (Фаза 2, план 02-01). Раньше /ads/new в тестовой
# среде отдавал 500 и в обход не включался: глобал шаблонов s3_public_url
# вызывал get_settings() в обход подмены зависимостей, Settings() собирался
# заново из окружения, и без .env обязательные поля отсутствовали —
# ValidationError. Глобалы изображений теперь привязываются к настройкам
# приложения через bind_image_url_globals в create_app (D-21), поэтому
# страница вернулась в SHELL_ROUTES наравне с остальными.
#
# АДРЕС /groups И ЕГО ПАРТИАЛ УБРАНЫ ИЗ ОБХОДА планом 03-08: глобальный раздел
# «Группы» снесён целиком (D-01), и по обоим адресам теперь стоит заглушка,
# отвечающая перенаправлением. Обход требует 200 и шелла — перенаправление ни
# тем, ни другим не является. Вклад раздела в четыре проверки обхода не
# потерян: он переехал на экран групп аккаунта и живёт в
# test_account_groups_page_gets_the_full_shell_treatment ниже, а сама заглушка
# закреплена тестами раздела «снесённый раздел» в конце файла.
#
# АДРЕС /schedules/new ИЗ ОБХОДА УБРАН планом 02-06: отдельные страницы
# расписаний сняты (D-14). Страницей настройки расписаний стал редактор
# объявления, но у него есть path-параметр, и в этот перечень он по построению
# не входит — «все страницы БЕЗ path-параметров». Чтобы четыре проверки обхода
# (шелл, отсутствие сторонних ресурсов, версионирование статики, единственная
# подсветка навигации) не потерялись вместе с адресом, редактор проверяется
# отдельным тестом test_ad_editor_page_gets_the_full_shell_treatment ниже.
# `/ads/new` — тот же редактор в режиме создания — в перечне остаётся.

EXTERNAL_HOSTS = (
    "cdn.tailwindcss.com",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "unpkg.com",
    "cdn.jsdelivr.net",
    "cdnjs.cloudflare.com",
    "ajax.googleapis.com",
)

# Ссылки на подключаемые ресурсы: <script src> и <link href>
ASSET_REF_RE = re.compile(r'<(?:script|link)\b[^>]*?(?:src|href)="([^"]+)"', re.I)


def _assert_no_external_assets(html: str, label: str, own_host: str = "test") -> None:
    """Ни один подключаемый ресурс не уходит за пределы своего домена.

    Проверка идёт не только по списку известных хостов: любой script/link,
    указывающий на ЧУЖОЙ домен, — это внешний запрос, даже если хост нам
    сегодня незнаком (T-08-04).

    url_for('static', …) в Starlette отдаёт абсолютный адрес со своим хостом,
    поэтому «абсолютный» само по себе нарушением не является — нарушением
    является ЧУЖОЙ хост. Протокол-относительные (//host/…) считаются внешними
    всегда: собственных ссылок такого вида в проекте нет.
    """
    for host in EXTERNAL_HOSTS:
        assert host not in html, f"{label}: {host}"
    for ref in ASSET_REF_RE.findall(html):
        netloc = urlsplit(ref).netloc
        assert netloc in ("", own_host), f"{label}: сторонний ресурс {ref}"


@pytest.mark.asyncio
@pytest.mark.parametrize("route", SHELL_ROUTES)
async def test_all_pages_render_new_shell(authed_client: AsyncClient, route: str):
    """Ни одна страница не осталась на старом layout (D-06, UI-02).

    Это тест, доказывающий требование ЦЕЛИКОМ, а не по одному разделу:
    пропущенный шаблон виден только сплошным обходом.
    """
    response = await authed_client.get(route)
    assert response.status_code == 200, route
    html = response.text
    assert "data-shell" in html, route
    assert "data-nav" in html, route
    assert "data-tabs" in html, route


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ADMIN_SHELL_ROUTES)
async def test_admin_pages_render_new_shell(admin_client: AsyncClient, route: str):
    response = await admin_client.get(route)
    assert response.status_code == 200, route
    assert "data-shell" in response.text, route


@pytest.mark.asyncio
async def test_root_route_lands_in_shell(authed_client: AsyncClient):
    """Корень — перенаправление, а не страница: обход идёт по его цели."""
    response = await authed_client.get("/", follow_redirects=True)
    assert response.status_code == 200
    assert "data-shell" in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("route", PARTIAL_ROUTES)
async def test_partials_render_without_shell(authed_client: AsyncClient, route: str):
    """Партиал — фрагмент подмены: шелла в нём быть НЕ должно.

    Партиал, притащивший шелл целиком, вставит вторую копию навигации в
    середину списка. Утверждение на статус ответа этого не поймает.
    """
    response = await authed_client.get(route)
    assert response.status_code == 200, route
    assert "data-shell" not in response.text, route


@pytest.mark.asyncio
async def test_no_external_cdn(
    authed_client: AsyncClient, admin_client: AsyncClient, client: AsyncClient
):
    """Ни одна выдача проекта не тянет сторонний скрипт, стиль или шрифт.

    После фазы приложение загружает только свои ресурсы — это же закрывает
    весь класс supply-chain-риска (T-08-04).
    """
    for route in ADMIN_SHELL_ROUTES:
        _assert_no_external_assets((await admin_client.get(route)).text, route)
    for route in AUTH_GET_ROUTES:
        _assert_no_external_assets((await client.get(route)).text, route)


@pytest.mark.asyncio
@pytest.mark.parametrize("route", SHELL_ROUTES + PARTIAL_ROUTES)
async def test_no_external_cdn_on_user_pages(authed_client: AsyncClient, route: str):
    response = await authed_client.get(route)
    assert response.status_code == 200, route
    _assert_no_external_assets(response.text, route)


@pytest.mark.asyncio
@pytest.mark.parametrize("route", SHELL_ROUTES)
async def test_static_links_versioned(authed_client: AsyncClient, route: str):
    """Ссылки на статику несут параметр версии (T-08-05).

    На выкате у части пользователей в кэше лежит страница, тянувшая ассеты с
    внешних CDN. Без параметра версии они получат смесь старого и нового.
    Хешей в именах файлов нет и не будет — build-шаг запрещён D-02.
    """
    html = (await authed_client.get(route)).text

    static_refs = [r for r in ASSET_REF_RE.findall(html) if "/static/" in r]
    assert static_refs, f"{route}: ссылок на статику не найдено"
    for ref in static_refs:
        assert re.search(r"\?v=\S+", ref), f"{route}: ссылка без версии — {ref}"

    # Общий стиль подключён и версионирован на каждой странице
    assert any("app.css" in r for r in static_refs), route


# --- UI-03: навигация -------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("route", SHELL_ROUTES)
async def test_active_nav_highlight(authed_client: AsyncClient, route: str):
    """Текущий раздел подсвечен РОВНО один раз на каждой странице шелла.

    Ноль совпадений — пользователь не понимает, где он. Два и больше —
    подсвечены несколько разделов сразу, что не лучше.
    """
    html = (await authed_client.get(route)).text
    # Сайдбар помечает пункт is-active; нижние табы — только aria-current
    assert html.count("is-active") == 1, route


@pytest.mark.asyncio
async def test_ad_editor_page_gets_the_full_shell_treatment(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Редактор объявления — страница настройки расписаний (D-14, план 02-06).

    Заменяет вклад снятого `/schedules/new` в сплошной обход. Адрес несёт
    path-параметр и потому в SHELL_ROUTES не входит; все четыре утверждения
    обхода воспроизведены здесь на одной странице, а не потеряны вместе с ней.
    """
    user = (
        await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()
    ad = Ad(
        user_id=user.id, title="Объявление обхода", text="Текст", images=[],
        status=AD_STATUS_PUBLISHED,
    )
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)

    route = f"/ads/{ad.id}/edit"
    response = await authed_client.get(route)
    assert response.status_code == 200, route
    html = response.text

    # 1. Шелл целиком
    assert "data-shell" in html, route
    assert "data-nav" in html, route
    assert "data-tabs" in html, route
    # 2. Ни одного стороннего ресурса
    _assert_no_external_assets(html, route)
    # 3. Статика версионирована
    static_refs = [r for r in ASSET_REF_RE.findall(html) if "/static/" in r]
    assert static_refs, f"{route}: ссылок на статику не найдено"
    for ref in static_refs:
        assert re.search(r"\?v=\S+", ref), f"{route}: ссылка без версии — {ref}"
    assert any("app.css" in r for r in static_refs), route
    # 4. Подсвечен ровно один раздел
    assert html.count("is-active") == 1, route


@pytest.mark.asyncio
async def test_account_groups_page_gets_the_full_shell_treatment(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Экран групп аккаунта — замена вклада снесённого раздела в обход (03-08).

    Адрес несёт path-параметр и в SHELL_ROUTES по построению не входит — то же
    решение, что у редактора объявления взамен снятого `/schedules/new`. Все
    четыре утверждения обхода воспроизведены здесь на одной странице, а не
    потеряны вместе со строкой перечня.
    """
    user = (
        await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()
    account = MessengerAccount(
        user_id=user.id, type="wa", credentials="session", status="active"
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    await seed_group(db_session, account.id, name="Группа обхода")

    route = f"/accounts/{account.id}/groups"
    response = await authed_client.get(route)
    assert response.status_code == 200, route
    html = response.text

    # 1. Шелл целиком
    assert "data-shell" in html, route
    assert "data-nav" in html, route
    assert "data-tabs" in html, route
    # 2. Ни одного стороннего ресурса
    _assert_no_external_assets(html, route)
    # 3. Статика версионирована
    static_refs = [r for r in ASSET_REF_RE.findall(html) if "/static/" in r]
    assert static_refs, f"{route}: ссылок на статику не найдено"
    for ref in static_refs:
        assert re.search(r"\?v=\S+", ref), f"{route}: ссылка без версии — {ref}"
    assert any("app.css" in r for r in static_refs), route
    # 4. Подсвечен ровно один раздел — «Аккаунты», внутри которых живёт экран
    assert html.count("is-active") == 1, route

    # Порция прокрутки экрана — ФРАГМЕНТ: шелла в ней быть не должно. Это
    # замена вклада `/groups/partial` в PARTIAL_ROUTES: адрес порции тоже несёт
    # идентификатор аккаунта и в статический перечень не входит.
    partial = await authed_client.get(f"{route}/partial?offset=0&limit=30")
    assert partial.status_code == 200
    assert "data-shell" not in partial.text
    _assert_no_external_assets(partial.text, f"{route}/partial")


@pytest.mark.asyncio
async def test_admin_nav_hidden_for_regular_user(authed_client: AsyncClient):
    html = (await authed_client.get("/profile")).text
    assert 'href="/admin"' not in html


@pytest.mark.asyncio
async def test_admin_nav_visible_for_admin(admin_client: AsyncClient):
    html = (await admin_client.get("/profile")).text
    assert 'href="/admin"' in html


@pytest.mark.asyncio
async def test_nav_keeps_links(authed_client: AsyncClient):
    """Переходы навигации остаются ссылками, а не кнопками со скриптом."""
    html = (await authed_client.get("/profile")).text
    assert 'href="/dashboard"' in html
    assert 'href="/accounts"' in html


# --- План 03-08: снесённый глобальный раздел «Группы» (D-01) -----------------
#
# Раздел снят целиком. Оба утверждения ниже — ЯВНЫЕ и положительные по форме:
# отсутствие пункта меню не следует автоматически из того, что старый тест его
# присутствия удалён, а перенаправление старого адреса не следует из того, что
# адрес выпал из перечня обхода. Незаявленный возврат пункта или молчаливое
# исчезновение заглушки обязаны краснеть.

# Пункт рисуется в ДВУХ местах из одного списка NAV_ITEMS: в боковом меню
# (<span class="nav-label">) и в нижних табах (текст ссылки). Проверяются оба.
GROUPS_NAV_MARKERS = (
    'href="/groups"',
    '<span class="nav-label">Группы</span>',
    ">Группы</a>",
)


@pytest.mark.asyncio
@pytest.mark.parametrize("route", SHELL_ROUTES)
async def test_nav_has_no_groups_item(authed_client: AsyncClient, route: str):
    """Пункта «Группы» нет НИ НА ОДНОЙ странице — ни в меню, ни в табах.

    Обход сплошной, потому что состав навигации приходит на каждую страницу из
    одного списка: пункт, вернувшийся в него, появился бы сразу везде, а увидеть
    это на одной проверенной странице — случайность, а не гарантия.
    """
    html = (await authed_client.get(route)).text
    for marker in GROUPS_NAV_MARKERS:
        assert marker not in html, f"{route}: пункт снесённого раздела вернулся ({marker})"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "route",
    (
        "/groups",
        "/groups?account_id=1&messenger_type=wa&is_active=1",
        "/groups/partial?offset=30&limit=30",
        "/groups/42/toggle",
    ),
)
async def test_retired_groups_routes_redirect_to_accounts(
    authed_client: AsyncClient, route: str
):
    """Старый адрес и любая старая глубокая ссылка отвечают перенаправлением.

    Не 404: у пользователей остались закладки и открытые вкладки, чьи сентинелы
    всё ещё несут прежние адреса. Ответ об отсутствии страницы был бы потерей
    без нужды — перенаправление приводит человека туда, где его группы теперь
    живут (UI-SPEC E8 error, T-03-33).
    """
    response = await authed_client.get(route, follow_redirects=False)
    assert response.status_code == 302, route
    assert response.headers["location"] == "/accounts", route


@pytest.mark.asyncio
async def test_retired_groups_section_accepts_no_post(authed_client: AsyncClient):
    """Ни тумблера, ни удаления, ни массовых операций на старом префиксе нет.

    Заглушка отвечает ТОЛЬКО на переход по ссылке. Обработчик POST, оставленный
    «чтобы старые формы не ломались», означал бы второй живой путь изменения
    данных мимо проверок владения нового экрана.
    """
    for route in ("/groups/42/toggle", "/groups/42/delete", "/groups/bulk"):
        response = await authed_client.post(route, follow_redirects=False)
        assert response.status_code == 405, (
            f"{route}: снесённый раздел принял POST ({response.status_code})"
        )


# --- D-09/D-19: живые данные шелла ------------------------------------------

@pytest.mark.asyncio
async def test_shell_live_data(authed_client: AsyncClient):
    html = (await authed_client.get("/profile")).text
    # Виджет квоты
    assert "data-quota" in html
    # Индикатор сессий мессенджеров (rename-to-sessions, Задача 1)
    assert "data-sessions" in html
    assert 'data-sessions-online="0"' in html
    assert 'data-sessions-total="0"' in html
    # Счётчики пунктов меню отрисованы числами
    counts = re.findall(r'<span class="nav-count">(\d+)</span>', html)
    assert len(counts) == 4
    assert all(c.isdigit() for c in counts)


# --- UI-06: адаптив ---------------------------------------------------------

@pytest.mark.asyncio
async def test_mobile_tabs_present(authed_client: AsyncClient):
    html = (await authed_client.get("/profile")).text
    assert "data-tabs" in html


# --- D-08: auth-шелл без сайдбара (План 02) ---------------------------------

AUTH_GET_ROUTES = ("/login", "/register", "/forgot-password")


@pytest.mark.asyncio
async def test_auth_shell(client: AsyncClient):
    """7 экранов авторизации живут во ВТОРОМ шелле: ни сайдбара, ни навигации.

    До Плана 02 они переопределяли {% block body %}, чтобы обойти {% if user %}
    основного шелла. Теперь у них собственный шелл на тех же токенах.
    """
    for route in AUTH_GET_ROUTES:
        response = await client.get(route)
        assert response.status_code == 200, route
        html = response.text
        assert "data-auth-shell" in html, route
        assert "data-side" not in html, route
        assert "data-nav" not in html, route
        assert "data-tabs" not in html, route


@pytest.mark.asyncio
async def test_auth_pages_no_external_cdn(client: AsyncClient):
    for route in AUTH_GET_ROUTES:
        html = (await client.get(route)).text
        for host in (
            "fonts.googleapis.com",
            "fonts.gstatic.com",
            "cdn.tailwindcss.com",
            "unpkg.com",
            "cdn.jsdelivr.net",
            "cdnjs.cloudflare.com",
        ):
            assert host not in html, f"{route}: {host}"


@pytest.mark.asyncio
async def test_login_form_contract(client: AsyncClient):
    """Атрибуты формы входа — контракт с обработчиком: они читаются дословно."""
    html = (await client.get("/login")).text
    assert 'method="post"' in html
    assert 'action="/login"' in html
    assert 'name="email"' in html
    assert 'name="password"' in html
    assert 'type="password"' in html


@pytest.mark.asyncio
async def test_auth_pages_use_component_library(client: AsyncClient):
    """Auth-экраны собраны из библиотеки, а не из скопированной разметки."""
    html = (await client.get("/login")).text
    assert 'class="field__input' in html
    assert 'class="btn btn--primary' in html


# --- Контракт «страница → шелл» на мигрированном разделе (План 03) ----------

@pytest.mark.asyncio
async def test_ads_head_contract(authed_client: AsyncClient):
    """Заголовок и CTA раздела живут в шапке шелла, а не в теле страницы.

    Собственный заголовок страницы удалён — иначе он бы задвоился с шапкой.
    """
    html = (await authed_client.get("/ads")).text

    head = re.search(r"<header data-head>(.*?)</header>", html, re.S)
    assert head, "шапка шелла не отрисована"
    assert "Объявления" in head.group(1)
    assert 'href="/ads/new"' in head.group(1)

    # Заголовок первого уровня на странице ровно один — тот, что в шапке
    assert html.count("<h1") == 1


@pytest.mark.asyncio
async def test_auth_pages_drop_utility_classes(client: AsyncClient):
    for route in AUTH_GET_ROUTES:
        html = (await client.get(route)).text
        for utility in ("bg-gray", "text-gray", "rounded-lg", "border-gray"):
            assert utility not in html, f"{route}: {utility}"


# --- DASH-05: воркеры онлайн читаются ИЗ КОНТРАКТА ШЕЛЛА ---------------------
#
# Единственное требование Фазы 4, у которого реализация уже была: индикатор
# рисует шелл из get_shell_context (Фаза 1, D-09/D-19). Работа здесь —
# закрепляющая: не написать второй источник числа, а закрепить, что второго
# источника не появилось.
#
# Ключи sessions_online / sessions_total измеряют состояние СЕССИИ мессенджера
# (MessengerAccount.status в БД), а не живость Docker-контейнера воркера. Это
# ограничение принято осознанно (T-04-21) и здесь только фиксируется: подмена
# смысла индикатора на «контейнер жив» стоила бы синхронного Docker SDK на
# рендере КАЖДОЙ страницы, а в тестах сокет Docker недоступен вовсе.

# Модули пути рендера дашборда. Проверка «нет обращения к Docker» идёт ПО
# ИСХОДНИКУ каждого из них: тот же приём уже применяется в проекте к проверкам
# по тексту модуля (см. запрет календарных функций диалекта в тестах аналитики).
DASHBOARD_RENDER_PATH = (
    "app/pages/dashboard.py",
    "app/pages/dashboard_feed.py",
    "app/application/analytics/send_analytics.py",
    # Модуль контекста шелла входит в перечень С ФАЗЫ 4: поаккаунтное чтение
    # состояния воркеров живёт теперь здесь, то есть именно сюда потянется
    # следующий разработчик дописать «а давайте покажем, жив ли контейнер».
    # Запрет обязан стоять там, где стоит соблазн.
    "app/pages/common.py",
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SESSION_PILL_RE = re.compile(r'data-sessions-online="(\d+)"')


async def _seed_messenger_account(
    db: AsyncSession,
    user_id: int,
    status: str,
    *,
    type_: str = "wa",
    credentials: str = "creds",
    session_data: str | None = None,
) -> MessengerAccount:
    """Посеять messenger-аккаунт. Один посев на всю секцию DASH-05.

    Канал, учётные данные и строка сессии — именованные параметры с прежними
    умолчаниями: тесты индикатора, написанные до перечня, продолжают звать
    помощника тремя позиционными аргументами и не правятся.
    """
    account = MessengerAccount(
        user_id=user_id,
        type=type_,
        credentials=credentials,
        session_data=session_data,
        status=status,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def _dashboard_user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


@pytest.mark.asyncio
async def test_dashboard_shows_the_sessions_indicator(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """DASH-05: на дашборде индикатор числа онлайн-сессий присутствует."""
    response = await authed_client.get("/dashboard")

    assert response.status_code == 200
    html = response.text
    assert "data-sessions" in html, "индикатор сессий на дашборде не отрисован"
    assert "воркеров онлайн" in html, "подпись индикатора потеряна"


@pytest.mark.asyncio
async def test_dashboard_sessions_number_counts_active_accounts(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Число индикатора равно числу messenger-аккаунтов в активном статусе.

    Утверждение ПАРНОЕ по смыслу с тестом нуля ниже: одно число без второго не
    отличает «счёт работает» от «счёт всегда показывает всё, что заведено».
    """
    user = await _dashboard_user(db_session)
    await _seed_messenger_account(db_session, user.id, "active")
    await _seed_messenger_account(db_session, user.id, "active")
    await _seed_messenger_account(db_session, user.id, "sync_failed")

    html = (await authed_client.get("/dashboard")).text

    assert SESSION_PILL_RE.search(html).group(1) == "2", (
        "индикатор считает не активные сессии, а что-то другое"
    )
    assert 'data-sessions-total="3"' in html, "общее число аккаунтов разошлось"


@pytest.mark.asyncio
async def test_dashboard_sessions_number_is_zero_without_active_accounts(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Пользователь без активных аккаунтов видит НОЛЬ, а не отсутствие индикатора.

    Спрятанный индикатор читался бы как сломанная шапка, а не как «воркеров
    нет»: пользователю нужно понять, почему его рассылки не уходят.
    """
    html = (await authed_client.get("/dashboard")).text

    assert "data-sessions" in html
    assert SESSION_PILL_RE.search(html).group(1) == "0"


def _worker_rows(html: str) -> dict[int, str]:
    """{id аккаунта: значение data-worker-online} по строкам перечня воркеров.

    Разбор идёт по ТЕГУ строки целиком, а не по паре соседних атрибутов: порядок
    атрибутов в разметке — не контракт, и тест, который его закрепил бы, краснел
    бы от перестановки, ничего не сломавшей на экране.
    """
    rows: dict[int, str] = {}
    for tag in re.findall(r"<[^>]*\sdata-worker\s[^>]*>", html):
        account_id = re.search(r'data-worker-id="(\d+)"', tag)
        online = re.search(r'data-worker-online="(true|false)"', tag)
        assert account_id and online, (
            f"строка перечня без опознавательных атрибутов: {tag}"
        )
        rows[int(account_id.group(1))] = online.group(1)
    return rows


def _worker_states(html: str) -> dict[int, str]:
    """{id аккаунта: ВИДИМЫЙ текст состояния} по строкам перечня воркеров.

    Разбирается именно ТЕКСТ, а не атрибут: атрибут `data-worker-online` уже
    пинится `_worker_rows`, а расходятся между собой они — точка считается из
    булева признака контракта шелла, а слово рисовалось сравнением со строкой в
    самом макросе. Тест, читающий только атрибут, зеленел бы на серой точке
    рядом со словом «Онлайн».
    """
    states: dict[int, str] = {}
    for account_id, body in re.findall(
        r'data-worker-id="(\d+)"(.*?)</div>', html, re.S
    ):
        state = re.search(r'class="worker-row__state">\s*(.*?)\s*</span>', body, re.S)
        assert state, f"строка перечня без видимого состояния: {body}"
        states[int(account_id)] = state.group(1).strip()
    return states


@pytest.mark.asyncio
async def test_dashboard_lists_each_account_with_its_worker_state(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """DASH-05/SC-1: пользователь читает, КАКОЙ аккаунт онлайн, а не сколько.

    Одно число не отвечает на вопрос, ради которого пользователь пришёл на
    дашборд: «почему мои рассылки не уходят». Отвечает перечень, в котором
    отвалившийся канал назван по имени.
    """
    user = await _dashboard_user(db_session)
    wa = await _seed_messenger_account(db_session, user.id, "active", type_="wa")
    tg = await _seed_messenger_account(
        db_session, user.id, "disconnected", type_="tg_user"
    )
    mx = await _seed_messenger_account(db_session, user.id, "active", type_="max")

    response = await authed_client.get("/dashboard")

    assert response.status_code == 200
    html = response.text
    rows = _worker_rows(html)
    assert len(rows) == 3, "перечень показывает не все аккаунты пользователя"
    assert rows == {wa.id: "true", tg.id: "false", mx.id: "true"}, (
        "состояние строки разошлось со статусом аккаунта"
    )
    # ТОЧКА И СЛОВО ИДУТ ИЗ ОДНОГО ПРИЗНАКА. Пока слово рисовалось собственным
    # сравнением со строкой 'active', смена константы WORKER_ONLINE_STATUS дала
    # бы серую точку рядом со словом «Онлайн», и ни один тест не покраснел бы:
    # разбирался только атрибут.
    states = _worker_states(html)
    assert states == {wa.id: "Онлайн", tg.id: "Отключён", mx.id: "Онлайн"}, (
        "видимое состояние строки разошлось с булевым признаком онлайна"
    )
    for account_id, online in rows.items():
        assert (states[account_id] == "Онлайн") == (online == "true"), (
            f"точка и слово спорят об аккаунте {account_id}: "
            f"{online} против {states[account_id]!r}"
        )
    # Агрегат шапки посчитан из того же списка и разойтись с ним не может.
    assert SESSION_PILL_RE.search(html).group(1) == "2"


@pytest.mark.asyncio
async def test_worker_list_is_capped_but_the_counts_are_not(
    authed_client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    """Перечень воркеров ограничен потолком, а числа шапки — нет.

    Число messenger-аккаунтов задаёт ПОЛЬЗОВАТЕЛЬ, схема его не ограничивает, а
    контракт шелла собирается на КАЖДОМ из 26 маршрутов — в том числе на 25,
    которые перечня не читают. Выборка без потолка — выделение памяти и
    разметка, растущие вместе с числом аккаунтов, на каждом рендере продукта.

    Числа при этом обязаны остаться ТОЧНЫМИ: выведенные из обрезанного перечня,
    они показали бы пользователю за потолком меньше аккаунтов, чем у него есть,
    — молча, с исправным на вид экраном.

    Потолок подменяется, а не создаётся сотня аккаунтов: утверждение теста —
    «перечень ограничен потолком», и настоящая сотня строк проверяла бы то же
    самое, но минутой дольше.
    """
    monkeypatch.setattr("app.pages.common.WORKER_LIST_CAP", 2)

    user = await _dashboard_user(db_session)
    for _ in range(3):
        await _seed_messenger_account(db_session, user.id, "active")
    await _seed_messenger_account(db_session, user.id, "disconnected")

    context = await get_shell_context(db_session, user)

    assert len(context["sessions"]) == 2, "перечень воркеров не ограничен потолком"
    assert context["sessions_total"] == 4, (
        "счёт аккаунтов выведен из обрезанного перечня и потому занижен"
    )
    assert context["sessions_online"] == 3, (
        "счёт онлайн-аккаунтов выведен из обрезанного перечня и потому занижен"
    )
    assert context["nav_counts"]["accounts"] == 4, (
        "счётчик бокового меню выведен из обрезанного перечня"
    )
    assert context["sessions_truncated"] is True, (
        "обрезка перечня не названа — короткий список читается как «остальных "
        "каналов нет»"
    )

    html = (await authed_client.get("/dashboard")).text
    assert "data-worker-truncated" in html, (
        "пользователю не сказано, что перечень показан не целиком"
    )


@pytest.mark.asyncio
async def test_worker_list_reports_no_truncation_when_it_fits(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Умещающийся перечень обрезанным себя не называет."""
    user = await _dashboard_user(db_session)
    await _seed_messenger_account(db_session, user.id, "active")

    context = await get_shell_context(db_session, user)

    assert context["sessions_truncated"] is False
    html = (await authed_client.get("/dashboard")).text
    assert "data-worker-truncated" not in html, (
        "полный перечень объявлен обрезанным — сообщение о неполноте лжёт"
    )


@pytest.mark.asyncio
async def test_dashboard_worker_list_excludes_another_users_account(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-G1-01: чужой аккаунт не попадает ни в перечень, ни в счёт."""
    user = await _dashboard_user(db_session)
    mine = await _seed_messenger_account(db_session, user.id, "active")

    stranger = User(email="stranger@test.com", password_hash="x", name="Stranger")
    db_session.add(stranger)
    await db_session.commit()
    await db_session.refresh(stranger)
    theirs = await _seed_messenger_account(db_session, stranger.id, "active")

    html = (await authed_client.get("/dashboard")).text

    rows = _worker_rows(html)
    assert theirs.id not in rows, "в перечень попал аккаунт другого пользователя"
    assert set(rows) == {mine.id}
    assert 'data-sessions-total="1"' in html, "счёт аккаунтов считает чужие строки"


@pytest.mark.asyncio
async def test_shell_worker_list_carries_no_secrets(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-G1-02: учётные данные и строка сессии на экран не выводятся.

    `credentials` хранит строку сессии Telegram и телефон MAX/WhatsApp. Контракт
    шелла печатается в HTML на КАЖДОЙ странице, поэтому граница проверяется по
    отрендеренной разметке, а не по намерению.
    """
    user = await _dashboard_user(db_session)
    secret_credentials = f"credentials-{uuid4().hex}"
    secret_session = f"session-{uuid4().hex}"
    await _seed_messenger_account(
        db_session,
        user.id,
        "active",
        credentials=secret_credentials,
        session_data=secret_session,
    )

    html = (await authed_client.get("/dashboard")).text

    assert secret_credentials not in html, "учётные данные аккаунта попали в разметку"
    assert secret_session not in html, "строка сессии аккаунта попала в разметку"


@pytest.mark.asyncio
async def test_dashboard_worker_list_keeps_an_unrecognised_status_visible(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Аккаунт с незнакомым статусом остаётся в перечне со своим значением.

    Пользователь пришёл на дашборд узнать, почему его рассылки не уходят.
    Строка, выпавшая из перечня потому, что интерфейс не знает её статуса, —
    ровно тот ответ, которого он не получит. Проверяются ДВА незнакомых
    статуса: существующий в проекте `sync_failed` и вымышленный, которого в
    коде нет вовсе, — иначе тест доказывал бы только наличие четвёртой ветки,
    а не отсутствие обрезки по списку известных значений.
    """
    user = await _dashboard_user(db_session)
    failed = await _seed_messenger_account(db_session, user.id, "sync_failed")
    invented_status = f"status-{uuid4().hex[:8]}"
    unknown = await _seed_messenger_account(db_session, user.id, invented_status)

    html = (await authed_client.get("/dashboard")).text

    rows = _worker_rows(html)
    assert set(rows) == {failed.id, unknown.id}, "незнакомый статус выпал из перечня"
    assert rows[failed.id] == "false"
    assert rows[unknown.id] == "false", "незнакомый статус зачтён за онлайн"
    assert "sync_failed" in html, "сырое значение статуса не показано"
    assert invented_status in html, "сырое значение статуса не показано"
    assert SESSION_PILL_RE.search(html).group(1) == "0"


@pytest.mark.asyncio
async def test_dashboard_worker_list_shows_an_empty_state_without_accounts(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Без аккаунтов блок остаётся на месте и ведёт на подключение (D-39/D-40)."""
    html = (await authed_client.get("/dashboard")).text

    assert "Воркеры аккаунтов" in html, "блок перечня спрятан вместо пустого состояния"
    assert not _worker_rows(html), "строки перечня взялись из ниоткуда"

    start = html.index("Каналы не подключены")
    empty_block = html[start : html.index("</div>", start)]
    assert 'href="/accounts"' in empty_block, "пустое состояние никуда не ведёт"
    assert "Подключить аккаунт" in empty_block


def test_dashboard_worker_row_has_one_definition():
    """Разметка строки перечня объявлена РОВНО в одном месте — в макросе.

    Инвентаризационный тест в духе уже существующих в проекте: вторая копия
    строки разъехалась бы с первой при первой же правке, а страница осталась бы
    исправной с виду.
    """
    templates_dir = PROJECT_ROOT / "app" / "templates"

    owners = sorted(
        path.relative_to(templates_dir).as_posix()
        for path in templates_dir.rglob("*.html")
        if "data-worker-id" in path.read_text(encoding="utf-8")
    )
    assert owners == ["dashboard/includes/worker_row.html"], (
        f"разметка строки перечня объявлена не только в макросе: {owners}"
    )

    page = (templates_dir / "dashboard.html").read_text(encoding="utf-8")
    assert "worker_row" in page, "страница не импортирует и не зовёт макрос строки"


def _identifiers_of(source: str) -> set[str]:
    """Имена, которые модуль ИМПОРТИРУЕТ и ВЫЗЫВАЕТ — без прозы.

    Разбор синтаксическим деревом, а не поиском подстроки по тексту. Поиск по
    тексту здесь неприменим принципиально: контракт модуля аналитики ОБЪЯСНЯЕТ
    свой запрет («не вызывает Docker SDK и вообще ничего синхронно-блокирующего
    — он живёт на пути рендера страницы»), и на поиске по подстроке объяснение
    запрета само нарушало бы запрет. Такой тест заставил бы снять из докстринга
    самое ценное — причину, — и следующая правка вернула бы обращение обратно,
    не встретив ни одного возражения.

    Дерево различает УПОМИНАНИЕ и ОБРАЩЕНИЕ, а запрещено именно обращение.
    """
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Name):
            names.add(node.id)
    return names


def test_dashboard_render_path_never_touches_docker():
    """T-04-21: в пути рендера дашборда обращения к Docker нет ни в каком виде.

    Docker SDK синхронный: вызванный на рендере, он блокирует event loop на
    КАЖДОЙ странице, а в тестах сокет Docker недоступен — то есть дефект
    существовал бы только в бою и ловился бы не тестами, а пользователем.
    Индикатор измеряет статус сессии мессенджера в БД, и этого достаточно:
    подмена его смысла на «контейнер жив» — это и есть цена, которую платить
    нечем.

    Единственный владелец обращений к Docker в проекте — сервис управления
    контейнерами воркеров; его имя запрещено здесь наравне с самим SDK.

    Перечень модулей СЛЕДУЕТ ЗА ВЛАДЕЛЬЦЕМ чтения состояния воркеров: с Фазы 4
    поаккаунтное чтение живёт в модуле контекста шелла, и он входит в перечень
    наравне с тремя модулями самой страницы.
    """
    offenders = {}
    for rel in DASHBOARD_RENDER_PATH:
        path = PROJECT_ROOT / rel
        assert path.exists(), f"модуль пути рендера пропал: {rel}"
        names = _identifiers_of(path.read_text(encoding="utf-8"))
        hits = sorted(
            name
            for name in names
            if "docker" in name.lower() or "wa_container_manager" in name
        )
        if hits:
            offenders[rel] = hits

    assert not offenders, (
        f"путь рендера дашборда обращается к Docker: {offenders}"
    )


@pytest.mark.asyncio
async def test_shell_reads_worker_state_in_a_single_query(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-G1-03: перечень стоит ОДНО обращение к таблице аккаунтов, не N.

    Перечень на N строк — естественное место для запроса на строку, а контракт
    шелла висит на пути рендера КАЖДОЙ из 26 страниц: N+1 здесь обошёлся бы
    дороже того самого синхронного Docker SDK, ради отказа от которого весь
    этот перечень и построен на статусе из БД.

    Считаются РЕАЛЬНЫЕ обращения к курсору, а не вызовы прикладного кода.

    Простой пересчёт запросов, УПОМИНАЮЩИХ таблицу, здесь не годится: блок
    ближайших отправок (DASH-02) присоединяет messenger_accounts к расписаниям
    своим запросом, и таких упоминаний на рендере два независимо от перечня.
    Поэтому утверждений тоже два, и оба про перечень: собственное чтение
    состояния воркеров РОВНО ОДНО, и число обращений НЕ РАСТЁТ вместе с числом
    аккаунтов — второе и есть настоящая проверка на N+1, потому что запрос на
    строку не поймать никакой константой.

    ЧТО СЧИТАЕТСЯ СОБСТВЕННЫМ ЧТЕНИЕМ. Перечень ограничен потолком
    (WORKER_LIST_CAP), а его агрегаты считаются скалярными подзапросами В ТОМ ЖЕ
    round-trip, где считаются объявления, расписания и история, — то есть
    дополнительного обращения к базе они не стоят. Собственным чтением здесь
    называется отдельный ЗАПРОС за строками перечня, и он один.
    """
    user = await _dashboard_user(db_session)
    for _ in range(3):
        await _seed_messenger_account(db_session, user.id, "active")

    statements: list[str] = []

    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    bind = db_session.get_bind()
    engine = getattr(bind, "sync_engine", bind)
    event.listen(engine, "before_cursor_execute", record)
    try:
        first = await authed_client.get("/dashboard")
        with_three = [s for s in statements if "messenger_accounts" in s]

        for _ in range(3):
            await _seed_messenger_account(db_session, user.id, "active")
        # Посев в счёт не идёт — считается только рендер.
        statements.clear()
        second = await authed_client.get("/dashboard")
        with_six = [s for s in statements if "messenger_accounts" in s]
    finally:
        event.remove(engine, "before_cursor_execute", record)

    assert first.status_code == 200
    assert second.status_code == 200

    own_read = [
        s
        for s in with_three
        if "FROM messenger_accounts" in s and "ORDER BY messenger_accounts.id" in s
    ]
    assert len(own_read) == 1, (
        "состояние воркеров читается не одним запросом: "
        f"{len(own_read)} собственных обращений\n" + "\n".join(own_read)
    )

    # Агрегаты перечня не стоят СВОЕГО round-trip: они едут скалярными
    # подзапросами в общем запросе счётчиков — том самом, что считает
    # объявления. Отдельный запрос за ними был бы двадцать шестым обращением на
    # двадцати шести маршрутах.
    aggregate_reads = [
        s
        for s in with_three
        if "FROM messenger_accounts" in s and s not in own_read
    ]
    assert len(aggregate_reads) == 1, (
        "агрегаты аккаунтов читаются не одним запросом: "
        f"{len(aggregate_reads)}\n" + "\n".join(aggregate_reads)
    )
    assert "FROM ads" in aggregate_reads[0], (
        "агрегаты аккаунтов уехали в СВОЁ обращение к базе вместо общего "
        f"round-trip счётчиков: {aggregate_reads[0]}"
    )
    assert len(with_six) == len(with_three), (
        "число обращений к messenger_accounts выросло вместе с числом аккаунтов "
        f"({len(with_three)} на трёх, {len(with_six)} на шести) — это N+1 на "
        "пути рендера каждой страницы"
    )


@pytest.mark.asyncio
async def test_shell_aggregate_is_derived_from_the_worker_list(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Оба числа СОГЛАСНЫ С ПЕРЕЧНЕМ, пока перечень умещается целиком.

    Считаются числа агрегатами, а перечень ограничен потолком — иначе
    пользователь за потолком видел бы в шапке заниженную цифру. Разойтись им
    всё равно не на чем: предикат «онлайн» у строки и у агрегата ОДИН
    (WORKER_ONLINE_STATUS), и именно это утверждает тест — не одно вычисление,
    а одно определение. Пока строк меньше потолка, согласие наблюдаемо
    поштучно, что здесь и проверяется.
    """
    user = await _dashboard_user(db_session)
    await _seed_messenger_account(db_session, user.id, "active")
    await _seed_messenger_account(db_session, user.id, "active")
    await _seed_messenger_account(db_session, user.id, "disconnected")
    await _seed_messenger_account(db_session, user.id, "sync_failed")

    result = await get_shell_context(db_session, user)

    assert len(result["sessions"]) == 4
    assert result["sessions_total"] == len(result["sessions"])
    online = [s for s in result["sessions"] if s["is_online"]]
    assert result["sessions_online"] == len(online) == 2
    assert result["nav_counts"]["accounts"] == len(result["sessions"])


@pytest.mark.asyncio
async def test_shell_worker_entries_expose_only_the_declared_keys(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-G1-02: состав ключей контракта закреплён, секретам в нём места нет.

    Граница держится на УРОВНЕ КОНТРАКТА, а не только на отрендеренной
    разметке: словарь шелла печатается на каждой странице, и смена способа его
    сборки не должна протащить `credentials` или `session_data` следующей
    правкой.
    """
    user = await _dashboard_user(db_session)
    await _seed_messenger_account(
        db_session, user.id, "active", credentials="secret", session_data="secret"
    )

    result = await get_shell_context(db_session, user)

    assert result["sessions"], "перечень пуст — проверка стала бы вакуумной"
    for session in result["sessions"]:
        assert set(session) == {"id", "type", "status", "is_online"}, (
            f"состав ключей строки контракта изменился: {sorted(session)}"
        )


def test_dashboard_page_has_no_second_source_of_the_sessions_number():
    """Собственного запроса по messenger-аккаунтам страница дашборда не делает.

    Число уже посчитано контрактом шелла на каждом страничном маршруте
    (`load_shell_context` → `get_shell_context`). Второй запрос ради того же
    числа завёл бы ВТОРОЙ источник одного факта — ровно ту болезнь, которую
    лечит D-35, — и Фаза 6, обязанная переиспользовать тот же контракт,
    унаследовала бы расхождение.
    """
    source = (PROJECT_ROOT / "app" / "pages" / "dashboard.py").read_text(
        encoding="utf-8"
    )

    assert "MessengerAccount" not in source, (
        "страница дашборда выбирает messenger-аккаунты сама — второй источник "
        "числа воркеров онлайн"
    )
    assert "sessions_online" not in source, (
        "страница дашборда считает индикатор сама вместо чтения контракта шелла"
    )

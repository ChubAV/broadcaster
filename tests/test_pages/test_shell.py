"""Wave 0: покрытие UI-01, UI-02, UI-03, UI-06 для нового шелла (План 01-01)."""

import ast
import base64
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import normalize_utc
from app.constants import AD_STATUS_PUBLISHED
from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.subscription import Subscription
from app.models.user import User
from app.pages import notices
from app.pages.common import get_shell_context
from tests.conftest import run_node_script, seed_group


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
        # Вендоренные рантаймы: htmx ~51.2 КБ (2.0.10, план 07-01 — записанная
        # здесь прежде величина снята вместе с файлом 1.9.10, а не дополнена
        # поправкой), Alpine ~43.4 КБ.
        # Порог здесь грубый и таким остаётся: подлинность htmx утверждается не
        # им, а полным SHA-384 в test_vendored_htmx_is_the_declared_artifact.
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
#
# ЧЕТЫРЕ НОВЫХ АДРЕСА ДОПИСАНЫ ПЛАНОМ 06-01 вместе с самими подразделами.
# Подраздел, заведённый маршрутом и НЕ внесённый в обход, отвечал бы 200 и
# выглядел бы исправным, потеряв при этом шелл целиком — и заметили бы это
# только глазами.
ADMIN_SHELL_ROUTES = (
    "/admin",
    "/admin/users",
    "/admin/workers",
    "/admin/queue",
    "/admin/logs",
    "/admin/payments",
)
# АДРЕС СПРАВОЧНИКА ГРУПП УБРАН ИЗ ОБХОДА планом 06-01 вместе с самими
# экранами (D-05): у таблицы справочника нет производителя, в бою она пуста, и
# экран показывал пустоту всем, кто на него заходил. Замены в обходе у него нет
# и быть не может — поверхность снята, а не переименована; вердикт по ADMIN-02
# записан в реестре требований частичным, с датой и основанием.

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
    # Виджет доступа (план 05.1-04: был виджетом квоты сообщений)
    assert "data-access" in html
    # Индикатор сессий мессенджеров (rename-to-sessions, Задача 1)
    assert "data-sessions" in html
    assert 'data-sessions-online="0"' in html
    assert 'data-sessions-total="0"' in html
    # Счётчики пунктов меню отрисованы числами
    counts = re.findall(r'<span class="nav-count">(\d+)</span>', html)
    assert len(counts) == 4
    assert all(c.isdigit() for c in counts)


# --- 05.1-04: контракт доступа в шелле ---------------------------------------
#
# Ключ `quota` заменён ключом `access`, и это переименование при СМЕНЕ ФОРМЫ
# значения, а не при смене подписи: `{used, limit, percent, plan}` →
# `{open, expires_at, days_left}`. Имя `quota` над словарём без квоты — ровно
# та ловушка, за которую фаза 5 сняла виджет с чужой подписью (D-22).
#
# Вердикт считается ЕДИНСТВЕННЫМ предикатом проекта (`access_is_open`), а не
# вторым сравнением дат на месте: две копии одного правила разъехались бы с
# гейтом `require_access` молча — то есть виджет обещал бы доступ, в котором
# зависимость уже отказывает.


async def _access_row(db: AsyncSession, user: User) -> Subscription:
    """Активная строка подписки пользователя — её заводит регистрация."""
    return (
        await db.execute(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.is_active.is_(True),
            )
        )
    ).scalar_one()


async def _move_expiry(db: AsyncSession, user: User, delta: timedelta) -> datetime:
    """Сдвигает срок УЖЕ СУЩЕСТВУЮЩЕЙ строки, а не заводит вторую.

    Частичный уникальный индекс `uq_subscriptions_active_user` допускает у
    пользователя ровно одну активную строку, а пробный срок ему завела
    регистрация (план 05.1-01). Вторая вставка дала бы IntegrityError, то есть
    тест падал бы на посеве, а не на предмете.
    """
    row = await _access_row(db, user)
    row.expires_at = datetime.now(timezone.utc) + delta
    await db.commit()
    return row.expires_at


@pytest.mark.asyncio
async def test_the_shell_reports_an_open_period_with_its_date_and_days(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Живой срок: вердикт открыт, дата — та же, что в строке, дни — число.

    Дата сверяется через `normalize_utc`, а не оператором равенства: колонка
    объявлена `DateTime(timezone=True)`, но SQLite отдаёт её NAIVE, а
    PostgreSQL — aware. Шелл отдаёт разметке ЗНАЧЕНИЕ КОЛОНКИ как есть — ровно
    как отдавал прежний ключ, — и приведение делает глобал форматирования.
    Сравнение без приведения проверяло бы диалект, а не контракт.
    """
    user = await _dashboard_user(db_session)
    expires_at = await _move_expiry(db_session, user, timedelta(days=10))

    access = (await get_shell_context(db_session, user))["access"]

    assert access["open"] is True
    assert normalize_utc(access["expires_at"]) == normalize_utc(expires_at)
    assert isinstance(access["days_left"], int)
    assert access["days_left"] == 9  # 9 полных суток + остаток


@pytest.mark.asyncio
async def test_the_shell_reports_a_closed_period_when_the_date_has_passed(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Истёкший срок закрывает доступ, а не «почти закрывает»."""
    user = await _dashboard_user(db_session)
    await _move_expiry(db_session, user, timedelta(days=-3))

    access = (await get_shell_context(db_session, user))["access"]

    assert access["open"] is False


@pytest.mark.asyncio
async def test_a_user_without_a_subscription_row_gets_a_verdict_not_an_exception(
    db_session: AsyncSession,
):
    """Отсутствие строки — ОПРЕДЕЛЁННОЕ состояние, а не отсутствие ответа.

    Ключ `access` присутствует всегда, когда пользователь есть: подстановка
    выдуманного имени тарифа («free»), которой жил прежний ключ `quota`, снята
    вместе с ним — умолчаний у вердикта доступа нет. Ветка несущая, а не
    защитная: пользователи, заведённые до ревизии 05.1-08, строки не имеют.
    """
    user = User(email="rowless@test.com", password_hash="h", name="R")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    access = (await get_shell_context(db_session, user))["access"]

    assert access["open"] is False
    assert access["expires_at"] is None
    assert access["days_left"] is None


@pytest.mark.asyncio
async def test_the_last_day_of_access_is_reachable_through_the_shell(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Ноль полных суток при ЖИВОМ сроке достижим НА ПОВЕРХНОСТИ ШЕЛЛА.

    Правило P-6 UI-контракта требует от виджета слов «последний день» вместо
    «осталось 0 дней». Ветка имела бы право на существование только если ноль
    вообще выпадает: округление вверх сделало бы её мёртвым кодом. Здесь
    показано, что не сделало, — и показано там, где ветка живёт, а не только в
    арифметике модуля.
    """
    user = await _dashboard_user(db_session)
    await _move_expiry(db_session, user, timedelta(hours=5))

    access = (await get_shell_context(db_session, user))["access"]

    assert access["days_left"] == 0
    assert access["open"] is True, "ноль выпал на УЖЕ ЗАКРЫТОМ доступе"


@pytest.mark.asyncio
async def test_the_widget_costs_the_shell_no_query_of_its_own(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Виджет доступа стоит НОЛЬ дополнительных запросов (UI-контракт C3).

    Строку подписки шелл читал и до правки — она же несёт дату. Два чтения
    журнала сообщений (`message_balances` и `balance_transactions`) уходят и
    ничем не заменяются: это минус два обращения к базе на каждом из 26
    страничных маршрутов, а не перенос стоимости в другое место.
    """
    statements: list[str] = []

    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    bind = db_session.get_bind()
    engine = getattr(bind, "sync_engine", bind)
    event.listen(engine, "before_cursor_execute", record)
    try:
        response = await authed_client.get("/profile")
    finally:
        event.remove(engine, "before_cursor_execute", record)

    assert response.status_code == 200

    journal = [
        s
        for s in statements
        if "message_balances" in s or "balance_transactions" in s
    ]
    assert not journal, (
        "шелл по-прежнему читает журнал сообщений на рендере страницы:\n"
        + "\n".join(journal)
    )

    subscriptions = [s for s in statements if "FROM subscriptions" in s]
    assert len(subscriptions) == 1, (
        "строка подписки читается не одним запросом: "
        f"{len(subscriptions)}\n" + "\n".join(subscriptions)
    )


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


# --- DASH-05: состояние сессий читается ИЗ КОНТРАКТА ШЕЛЛА ДВУМЯ ЧИСЛАМИ -----
#
# Индикатор рисует шелл из get_shell_context (Фаза 1, D-09/D-19). Работа здесь
# закрепляющая: не написать второй источник числа, а закрепить, что второго
# источника не появилось.
#
# ПОАККАУНТНОГО ПЕРЕЧНЯ БОЛЬШЕ НЕТ (задача 260826-6jq). Карточка «Воркеры
# аккаунтов» снята с дашборда вместе со своим шаблоном строки, стилями и
# отдельным запросом за строками аккаунтов: перечень читал ОДИН маршрут из 26,
# а собирался на всех. Часть тестов ниже — положительные ЗАПРЕТЫ на его
# возврат; утверждения снятых тестов о владении и о единственном предикате
# «онлайн» никуда не делись, они переехали на числа агрегатов.
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
    # Модуль контекста шелла остаётся в перечне и ПОСЛЕ снятия поаккаунтного
    # перечня: чтение состояния аккаунтов живёт здесь по-прежнему — теперь
    # агрегатами, — то есть именно сюда потянется следующий разработчик
    # дописать «а давайте покажем, жив ли контейнер». Запрет обязан стоять там,
    # где стоит соблазн, а соблазн стоит у чтения состояния, а не у его формы.
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


@pytest.mark.asyncio
async def test_dashboard_account_count_excludes_another_users_account(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-G1-01: чужой аккаунт не попадает в числа пилюли шапки.

    Владение проверялось прежде по перечню — «чужой строки в списке нет».
    Перечня больше нет, а утверждение осталось: предикат user_id в счётных
    подзапросах — единственное, что отделяет аккаунты одного пользователя от
    другого, и потерянный он покажет владельцу двойку вместо единицы.
    """
    user = await _dashboard_user(db_session)
    await _seed_messenger_account(db_session, user.id, "active")

    stranger = User(email="stranger@test.com", password_hash="x", name="Stranger")
    db_session.add(stranger)
    await db_session.commit()
    await db_session.refresh(stranger)
    await _seed_messenger_account(db_session, stranger.id, "active")

    html = (await authed_client.get("/dashboard")).text

    assert 'data-sessions-total="1"' in html, "счёт аккаунтов считает чужие строки"
    assert SESSION_PILL_RE.search(html).group(1) == "1", (
        "счёт онлайн-аккаунтов считает чужие строки"
    )


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
async def test_shell_makes_no_own_read_of_messenger_accounts(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-G1-03: собственного запроса за строками аккаунтов на рендере НЕТ.

    Прежде их было одно — отдельный запрос за строками поаккаунтного перечня.
    Перечень снят вместе с карточкой воркеров дашборда (задача 260826-6jq), и
    вместе с ним ушло это чтение: собирался запрос на КАЖДОМ из 26 страничных
    маршрутов, а читал его результат один.

    Считаются РЕАЛЬНЫЕ обращения к курсору, а не вызовы прикладного кода.

    Простой пересчёт запросов, УПОМИНАЮЩИХ таблицу, здесь не годится: блок
    ближайших отправок (DASH-02) присоединяет messenger_accounts к расписаниям
    своим запросом, и таких упоминаний на рендере два независимо от воркеров.
    Поэтому утверждений три: собственных чтений строк НОЛЬ, агрегаты по-прежнему
    едут скалярными подзапросами в общем round-trip счётчиков, и число обращений
    НЕ РАСТЁТ вместе с числом аккаунтов — последнее и есть настоящая проверка на
    N+1, потому что запрос на строку не поймать никакой константой.

    ЧТО СЧИТАЕТСЯ СОБСТВЕННЫМ ЧТЕНИЕМ. Агрегаты считаются скалярными подзапросами
    В ТОМ ЖЕ round-trip, где считаются объявления, расписания и история, — то
    есть дополнительного обращения к базе они не стоят. Собственным чтением
    здесь называется отдельный ЗАПРОС за строками аккаунтов, и его больше нет.
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
    assert own_read == [], (
        "на путь рендера каждой из 26 страниц вернулось отдельное чтение строк "
        f"messenger-аккаунтов: {len(own_read)} собственных обращений\n"
        + "\n".join(own_read)
    )

    # Агрегаты не стоят СВОЕГО round-trip: они едут скалярными подзапросами в
    # общем запросе счётчиков — том самом, что считает объявления. Отдельный
    # запрос за ними был бы двадцать шестым обращением на двадцати шести
    # маршрутах.
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
async def test_shell_counts_accounts_and_online_accounts_by_one_predicate(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Предикат «онлайн» имеет РОВНО ОДНО объявление, и числа считает он.

    Из четырёх посеянных аккаунтов онлайном обязаны считаться ровно два:
    `active` — единственное значение, которое проходит WORKER_ONLINE_STATUS, а
    `disconnected` и `sync_failed` не проходят. Тест утверждает не согласие
    двух вычислений (второго вычисления в проекте больше нет — поаккаунтный
    перечень снят), а то, что второе ОПРЕДЕЛЕНИЕ предиката не завелось: литерал
    'active', выписанный где-то ещё, разъедется с константой молча.

    Полное число проверяется рядом: без него тест не отличил бы работающий
    предикат от предиката, считающего всё подряд.
    """
    user = await _dashboard_user(db_session)
    await _seed_messenger_account(db_session, user.id, "active")
    await _seed_messenger_account(db_session, user.id, "active")
    await _seed_messenger_account(db_session, user.id, "disconnected")
    await _seed_messenger_account(db_session, user.id, "sync_failed")

    result = await get_shell_context(db_session, user)

    assert result["sessions_total"] == 4, "счёт аккаунтов потерял строки"
    assert result["sessions_online"] == 2, (
        "предикат «онлайн» считает не то, что объявляет WORKER_ONLINE_STATUS"
    )
    assert result["nav_counts"]["accounts"] == 4, (
        "счётчик раздела аккаунтов разошёлся с числом пилюли"
    )


# --- ЗАПРЕТ НА ВОЗВРАТ ПОАККАУНТНОГО ПЕРЕЧНЯ ВОРКЕРОВ (задача 260826-6jq) ----
#
# Снятие блока ОБЪЯВЛЕНО тестами, а не молчаливо: без них следующая правка
# вернула бы карточку вместе с отдельным чтением строк аккаунтов на путь
# рендера всех 26 страниц, и ни один тест не покраснел бы. Тем же приёмом
# проект выводил `dashboard/includes/recent_send_card.html` (план 04-05).
#
# Признаки перечня перечислены ЗДЕСЬ ОДНИМ СПИСКОМ: три теста ниже проверяют
# разные поверхности (разметка, контракт, шаблоны), но предмет у них один, и
# разъехавшиеся списки признаков дали бы запрет, дырявый ровно в том месте,
# где список короче.
WORKER_LIST_MARKERS = (
    "data-worker-id",
    "worker-row",
    "worker-list",
)


@pytest.mark.asyncio
async def test_the_dashboard_carries_no_per_account_worker_block(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """На дашборде нет ни строк перечня воркеров, ни его карточки.

    Разбирается ОТРЕНДЕРЕННЫЙ ответ, а не текст шаблона: комментарии Jinja до
    разметки не доезжают, и объяснение снятия, оставленное в `dashboard.html`,
    этот тест краснить не должно.

    Пилюля шапки проверяется тем же тестом НАРОЧНО: запрет, поставленный без
    неё, прошёл бы и на индикаторе, снесённом заодно с перечнем, — а он живой,
    к дашборду не привязан и стоит на всех 26 маршрутах.
    """
    user = await _dashboard_user(db_session)
    await _seed_messenger_account(db_session, user.id, "active")
    await _seed_messenger_account(db_session, user.id, "disconnected")

    response = await authed_client.get("/dashboard")

    assert response.status_code == 200
    html = response.text
    for marker in WORKER_LIST_MARKERS:
        assert marker not in html, (
            f"поаккаунтный перечень воркеров вернулся на дашборд: {marker!r}"
        )
    assert "Воркеры аккаунтов" not in html, "карточка перечня вернулась на дашборд"
    assert "data-sessions" in html, (
        "вместе с перечнем снесена пилюля состояния сессий — она живая и стоит "
        "в шапке шелла на всех 26 маршрутах"
    )


@pytest.mark.asyncio
async def test_the_shell_contract_carries_no_per_account_list(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Контракт шелла отдаёт ДВА ЧИСЛА и ничего поаккаунтного.

    Это же утверждение закрывает границу секретов, которую держал снятый
    `test_shell_worker_list_carries_no_secrets`: словарь печатается в HTML на
    каждой из 26 страниц, и протаскивать в него `credentials` или
    `session_data` следующей правкой попросту неоткуда — перечня нет вовсе.
    """
    user = await _dashboard_user(db_session)
    await _seed_messenger_account(
        db_session,
        user.id,
        "active",
        credentials=f"credentials-{uuid4().hex}",
        session_data=f"session-{uuid4().hex}",
    )

    result = await get_shell_context(db_session, user)

    assert "sessions" not in result, (
        "поаккаунтный перечень вернулся в контракт шелла — он собирается на "
        "всех 26 маршрутах, а читает его в лучшем случае один"
    )
    assert "sessions_truncated" not in result, (
        "признак обрезки вернулся в контракт шелла вместе с перечнем"
    )
    assert result["sessions_total"] == 1
    assert result["sessions_online"] == 1


def test_the_dashboard_worker_row_template_is_gone():
    """Шаблона строки перечня нет на диске, и его разметки нет ни в одном шаблоне.

    Замена снятому `test_dashboard_worker_row_has_one_definition`: прежде он
    требовал РОВНО ОДНОГО владельца разметки строки, теперь требуется ни одного.
    Недостижимых шаблонов в проекте не оставляют.

    Проверяется каталог дашборда, а не весь `app/templates`: строка таблицы
    админки `admin/includes/worker_row.html` — ДРУГОЙ файл с тем же именем, он
    живой и потребляется `admin/includes/workers_partial.html`.
    """
    templates_dir = PROJECT_ROOT / "app" / "templates"
    dashboard_dir = templates_dir / "dashboard"

    assert not (dashboard_dir / "includes" / "worker_row.html").exists(), (
        "шаблон строки перечня воркеров дашборда вернулся на диск"
    )
    assert (templates_dir / "admin" / "includes" / "worker_row.html").exists(), (
        "снесена строка таблицы воркеров АДМИНКИ — другой файл с тем же именем"
    )

    owners = {}
    for path in dashboard_dir.rglob("*.html"):
        source = path.read_text(encoding="utf-8")
        hits = sorted(m for m in WORKER_LIST_MARKERS if m in source)
        if hits:
            owners[path.relative_to(templates_dir).as_posix()] = hits
    page = templates_dir / "dashboard.html"
    hits = sorted(m for m in WORKER_LIST_MARKERS if m in page.read_text(encoding="utf-8"))
    if hits:
        owners["dashboard.html"] = hits

    assert not owners, f"разметка перечня воркеров вернулась в шаблоны: {owners}"


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


# --- Фаза 7 / план 07-01: рантайм htmx 2.0.10 и блок его конфигурации --------
#
# Три константы ниже ВЫПИСАНЫ ЗДЕСЬ, а не выведены из проверяемого артефакта.
# Тест, считающий ожидание с того же файла, который проверяет, согласился бы с
# любой правкой — прецедент записан у GATED_ROUTERS (test_access_gate.py:41-52).

HTMX_VERSION = "2.0.10"

# ЗАПИСЬ О ТОМ, ЧТО ИМЕННО ВВЕЗЕНО.
# Файл `app/static/js/htmx.min.js` — дистрибутивный минифицированный htmx
# 2.0.10, скачанный с https://cdn.jsdelivr.net/npm/htmx.org@2.0.10/dist/htmx.min.js
# (зеркало https://unpkg.com/htmx.org@2.0.10/dist/htmx.min.js байт-идентично).
# Вытеснил собой 1.9.10 (47 755 Б) планом 07-01.
#
# Хеш стоит здесь, а НЕ атрибутом integrity на теге рантайма, и это решение
# (D-04): тот же хеш в двух местах при рассинхроне заставил бы браузер отбросить
# файл МОЛЧА — пользователь получил бы мёртвый интерфейс без единого сообщения.
# Здесь рассинхрон краснеет в суите, а не у пользователя.
#
# ПРИ СЛЕДУЮЩЕМ ОБНОВЛЕНИИ РАНТАЙМА обе константы меняются ТЕМ ЖЕ КОММИТОМ,
# что и сам файл. Подмена артефакта без правки этих строк — то, ради чего они
# написаны; правка этих строк без сверки со скачанным файлом превращает запись
# о ввезённом в запись о том, чего в репозитории нет.
HTMX_SHA384 = "H5SrcfygHmAuTDZphMHqBJLc3FhssKjG7w/CeCpFReSfwBWDTKpkzPP8c+cLsK+V"
HTMX_BYTES = 51238

# Шесть ключей ВЕРХНЕГО уровня; responseHandling — ОДИН ключ, а не пять.
# Источник — .planning/research/SUMMARY.md §«Обязательный блок конфигурации»,
# где у каждой строки выписано последствие её пропуска.
#
# Правило "422" несёт ПРИЗНАК ОШИБКИ, но НЕ несёт свопа, и это решение, а не
# небрежность. Признак ошибки добавлен, потому что в приложении сегодня нет ни
# одного маршрута, отдающего этот код с фрагментом разметки: всякий такой
# ответ — умолчание фреймворка, то есть машинное тело с внутренностями маршрута
# и параметра, и без признака ошибки оно приезжало бы в страницу МОЛЧА, не
# подняв htmx:responseError. Расхождение правила с телом ответа сервера
# стережёт tests/test_pages/test_htmx_response_contract.py.
#
# ⚠️ СВОП СНЯТ ПРАВКОЙ БЕЗОПАСНОСТИ ФАЗЫ 7 (07-SECURITY.md, 07-05/T-07-13), и
# ПРЕЖНЕЕ ОЖИДАНИЕ ЗДЕСЬ БЫЛО "swap": True. Обоснование прежней редакции — «на
# перерисовке формы с эхо-возвратом строится FORM-08, снятие свопа сделало бы
# кнопку сохранения мёртвой» — ВЕРНО, но только начиная с Фазы 8. Пока
# авторского тела у 422 нет, своп делал целью подмены DOM тело, состав которого
# приложение не выбирает и которое дословно повторяет присланное пользователем
# значение, — при allowScriptTags и allowEval, оставленных умолчаниями артефакта
# (оба true) и шестиключевым составом НЕ переопределяемых.
#
# ЭТО ОЖИДАНИЕ — ГЕЙТ НА ВОЗВРАТ СВОПА. Оно краснеет в тот момент, когда своп
# вернут в разметку, и вернуть его ПРАВОМЕРНО только одновременно с появлением
# первого маршрута, отдающего 422 с АВТОРСКИМ фрагментом. Правка этой строки
# без такого маршрута воспроизводит снятый сток — то есть красноту надлежит
# чинить маршрутом, а не строкой.
#
# СЛЕДСТВИЕ: со "swap": False правило "422" поведенчески совпадает с "[45]..",
# стоящим ниже. Порядок правил при этом остаётся несущим и утверждается ниже по
# ИНДЕКСАМ — правило, опустившееся под общее, потеряет и признак ошибки.
HTMX_CONFIG = {
    "historyRestoreAsHxRequest": False,
    "allowNestedOobSwaps": False,
    "reportValidityOfForms": True,
    "historyCacheSize": 0,
    "selfRequestsOnly": True,
    "responseHandling": [
        {"code": "204", "swap": False},
        {"code": "[23]..", "swap": True},
        {"code": "422", "swap": False, "error": True},
        {"code": "[45]..", "swap": False, "error": True},
        {"code": "...", "swap": False},
    ],
}

# Пять правил В ПОРЯДКЕ. Порядок и есть предмет: правила разбираются сверху вниз
# до первого совпадения, и "422", опустившееся ниже "[45]..", перехватывается
# общим правилом — форма с ошибкой валидации становится мёртвой кнопкой.
RESPONSE_HANDLING_CODES = ("204", "[23]..", "422", "[45]..", "...")

# Значение атрибута многострочное, поэтому re.DOTALL обязателен.
HTMX_CONFIG_RE = re.compile(
    r"""<meta\s+name=["']htmx-config["']\s+content='(.*?)'\s*/?>""",
    re.DOTALL,
)

# Путь рантайма в отрендеренном документе. url_for отдаёт АБСОЛЮТНЫЙ адрес со
# своим хостом, поэтому ищется хвост, а не вся ссылка.
HTMX_RUNTIME_REF = "/static/js/htmx.min.js"

# То же в ИСХОДНИКЕ шаблона: там стоит вызов url_for, а не готовый путь.
HTMX_RUNTIME_SOURCE_REF = "js/htmx.min.js"

# ЕДИНСТВЕННЫЙ законный владелец ссылки на рантайм среди шаблонов (D-01).
# Имя выписано здесь, а не выведено обходом: тест, назначающий владельцем того,
# кого нашёл, согласился бы с переездом тега куда угодно.
HTMX_RUNTIME_OWNER = "includes/htmx_config.html"

# Ключ, под которым ОБА рантайма складывают снимки страниц: имя ключа у 1.9.10
# и у 2.0.10 одно и то же, а вот ХРАНИЛИЩЕ у них разное, и в этом весь предмет.
#
# Отгруженный 2.0.10 держит снимки в sessionStorage. Измерено по вендоренному
# app/static/js/htmx.min.js: вхождений localStorage — НОЛЬ, вхождений
# sessionStorage — ДЕВЯТЬ. Свой store рантайм при historyCacheSize <= 0 чистит
# САМ, в функции zt(): она первым же условием делает
# sessionStorage.removeItem("htmx-history-cache") и выходит, не сохранив снимка.
#
# localStorage — хранилище ВЫБЫВШЕГО 1.9.10. 2.0.10 этого хранилища не
# наполняет и не опустошает, потому что не знает о нём вовсе, поэтому остаток,
# накопленный прежним рантаймом, не убывает сам НИКОГДА и есть предмет разовой
# миграционной очистки (единственный инлайн-скрипт проекта).
#
# ⚠️ Прежняя редакция этого комментария объявляла хранилищем localStorage и
# обосновывала выбор тем, что «снимок переживает закрытие вкладки». Утверждение
# СНЯТО как неверное для вендоренного артефакта: переживание закрытия вкладки —
# ровно то свойство, которого у sessionStorage нет. Посылка была снята с
# ВЫБЫВАЮЩЕГО рантайма (research/PITFALLS.md §9, измерение 4/7) и после
# обновления не пересчитана; поправка к §9 датирована Фазой 7.
HISTORY_CACHE_KEY = "htmx-history-cache"

# ЕДИНСТВЕННЫЙ законный владелец строки миграционной очистки среди шаблонов.
# Имя выписано здесь, а не выведено обходом, по тому же основанию, что и
# HTMX_RUNTIME_OWNER выше: тест, назначающий владельцем того, кого нашёл,
# согласился бы с переездом строки куда угодно.
LEGACY_HISTORY_CACHE_OWNER = "includes/htmx_config.html"

# Сток разметки: значение, попавшее в строку разметки, разбирается парсером
# всегда. Перечень тот же, что закрепляет редактор объявления
# (tests/test_templates/test_ads_form_security.py:49) — второго ОПРЕДЕЛЕНИЯ
# одного запрета в проекте не заводится, значение копируется дословно с
# указанием источника. Прецедент такого копирования во второй файл —
# tests/test_pages/test_history.py:820-826.
MARKUP_SINKS = ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write")

# Комментарии шаблона: Jinja-комментарий вырезается при рендере, HTML-комментарий
# доезжает до браузера, но НИ ОДИН из них не есть подключение чего-либо.
_TEMPLATE_COMMENT_RE = re.compile(r"\{#.*?#\}|<!--.*?-->", re.DOTALL)

# Тег подключения рантайма в ИСХОДНИКЕ: открывающий script с путём рантайма в
# атрибуте источника. Ищется ТЕГ, а не путь — см. _without_comments ниже.
# Путь берётся из HTMX_RUNTIME_SOURCE_REF, а не выписывается второй раз: второй
# копии одного пути в этом файле не заводится.
_HTMX_RUNTIME_TAG_RE = re.compile(
    r"<script[^>]*" + re.escape(HTMX_RUNTIME_SOURCE_REF)
)


def _without_comments(source: str) -> str:
    """Исходник шаблона без Jinja- и HTML-комментариев.

    Общий помощник ДВУХ гейтов единственности — рантайма и строки миграционной
    очистки, — и общий он нарочно: два места вырезают одно и то же, и вторая
    копия вырезания разъехалась бы с первой ровно так же, как разъехались бы два
    литеральных блока конфигурации (D-01, та же доктрина этажом ниже).

    ЗАЧЕМ ВООБЩЕ ВЫРЕЗАТЬ (07-REVIEW.md IN-02). Гейт, ищущий подстроку по всему
    исходнику, объявляет нарушителем шаблон, всего лишь УПОМЯНУВШИЙ путь или ключ
    в комментарии. В кодовой базе, где комментарии обязательны и объёмны, это
    реалистичное ложное срабатывание, а не теоретическое: включение уже несёт
    комментарий, говорящий и о рантайме, и об очистке. Гейт, краснеющий на прозу,
    учит правку удалять прозу — то есть ровно наоборот.
    """
    return _TEMPLATE_COMMENT_RE.sub("", source)


def _htmx_config_of(html: str, shell: str) -> dict:
    """Блок конфигурации, вытащенный из ОТРЕНДЕРЕННОГО документа и разобранный.

    Разбор идёт по ответу, а не по исходнику шаблона, и это несущее решение
    (D-05). Сломанное экранирование кавычек внутри значения атрибута отбросило
    бы ВСЕ шесть ключей в умолчания, оставив греп исходника зелёным: htmx не
    сообщает о нечитаемой конфигурации ничем. Ловит это только json.loads
    разобранного ответа.
    """
    match = HTMX_CONFIG_RE.search(html)
    assert match, (
        f"{shell}: блока конфигурации htmx в отрендеренном документе нет — "
        "забытый {% include %} либо съехавший атрибут content"
    )
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"{shell}: значение content= не разбирается как JSON ({exc}) — "
            "все шесть ключей молча ушли бы в умолчания:\n" + match.group(1)
        ) from exc


def _assert_config_contract(config: dict, shell: str) -> None:
    """Шесть ключей с их значениями и ПОРЯДОК пяти правил responseHandling."""
    assert set(config) == set(HTMX_CONFIG), (
        f"{shell}: состав ключей верхнего уровня разошёлся — "
        f"лишние {sorted(set(config) - set(HTMX_CONFIG))}, "
        f"недостающие {sorted(set(HTMX_CONFIG) - set(config))}"
    )

    for key, expected in HTMX_CONFIG.items():
        actual = config[key]
        # Тип сверяется отдельно от значения: в Python False == 0, и
        # historyCacheSize, съехавший в false, прошёл бы сравнение значений.
        assert type(actual) is type(expected), (
            f"{shell}: у ключа {key} тип {type(actual).__name__}, "
            f"ожидался {type(expected).__name__}"
        )
        assert actual == expected, (
            f"{shell}: у ключа {key} значение {actual!r}, ожидалось {expected!r}"
        )

    codes = tuple(rule["code"] for rule in config["responseHandling"])
    assert codes == RESPONSE_HANDLING_CODES, (
        f"{shell}: порядок правил responseHandling {codes}, "
        f"ожидался {RESPONSE_HANDLING_CODES}"
    )
    assert codes.index("422") < codes.index("[45].."), (
        f"{shell}: правило 422 опустилось НИЖЕ общего [45].. и перехватывается "
        "им — форма с ошибкой валидации стала для пользователя мёртвой кнопкой"
    )


def _assert_config_precedes_runtime(html: str, shell: str) -> None:
    """Блок стоит ВЫШЕ тега рантайма — утверждается индексами, а не наличием.

    ⚠️ ЭТА ПРОВЕРКА НЕ ЕСТЬ МЕХАНИЗМ БЕЗОПАСНОСТИ, И ПРЕЖНЕЕ УТВЕРЖДЕНИЕ О ТОМ,
    ЧТО ОНА ИМ ЯВЛЯЕТСЯ, СНЯТО. Docstring гласил: «рантайм читает конфигурацию
    один раз, при разборе собственного тега; блок, оказавшийся ниже, не
    читается вовсе». По вендоренному 2.0.10 это неверно: блок ищется
    querySelector'ом по ВСЕМУ документу, а слияние идёт на DOMContentLoaded, —
    значит блок ниже тега рантайм прочитает.

    Настоящее несущее свойство другое: блок обязан быть в ИСХОДНОМ, серверно
    отрендеренном документе; вставленный скриптом ПОСЛЕ DOMContentLoaded, он не
    читается и молчит об этом. Это свойство обеспечивает {% include %} в <head>,
    а утверждают его гейты разбора конфигурации по ответу.

    Проверка порядка сохраняется в полной силе как ЗАЩИТНАЯ ПРОВЕРКА СТИЛЯ И
    ПОРЯДКА: соседство тегов остаётся правильной практикой, и разъехавшаяся пара
    — сигнал, что <head> правили вслепую. Не ослабляется и не снимается, но
    называть её причиной, по которой конфигурация доезжает до рантайма, нельзя.
    """
    config_at = html.find("htmx-config")
    runtime_at = html.find(HTMX_RUNTIME_REF)
    assert config_at != -1, f"{shell}: блока конфигурации в документе нет"
    assert runtime_at != -1, f"{shell}: тега рантайма htmx в документе нет"
    assert config_at < runtime_at, (
        f"{shell}: блок конфигурации ({config_at}) оказался НИЖЕ тега рантайма "
        f"({runtime_at}) — htmx его не прочитает и не пожалуется"
    )


def test_vendored_htmx_is_the_declared_artifact():
    """D-04: вендоренный рантайм — ИМЕННО тот артефакт, а не «версия 2.0.10».

    Утверждений три, и ни одно не заменяет другого. Размер ловит оборванную
    загрузку. Полный SHA-384 ловит пропатченную сборку и чужой ре-минификатор —
    файл, отличающийся хотя бы одним байтом, гейт не проходит. Подстрока версии
    ловит подмену соседним релизом с сохранением размера; она несёт ЗАКРЫВАЮЩУЮ
    кавычку, поэтому ни 2.0.1, ни 2.0.101 ей не удовлетворяют.

    Читается файл с диска, а не ответ HTTP: предмет — байты в репозитории.
    Прецедент утверждения по байтам в этом же файле есть — сигнатура wOF2 у
    шрифтов (:55).
    """
    path = PROJECT_ROOT / "app" / "static" / "js" / "htmx.min.js"
    assert path.exists(), "вендоренный рантайм htmx пропал с диска"
    payload = path.read_bytes()

    assert len(payload) == HTMX_BYTES, (
        f"размер вендоренного htmx {len(payload)} Б, объявлено {HTMX_BYTES} Б"
    )

    digest = base64.b64encode(hashlib.sha384(payload).digest()).decode("ascii")
    assert digest == HTMX_SHA384, (
        "SHA-384 вендоренного htmx не равен объявленному:\n"
        f"  в репозитории: {digest}\n"
        f"  объявлено:     {HTMX_SHA384}\n"
        "Артефакт подменён либо константа правлена отдельно от файла."
    )

    assert f'version:"{HTMX_VERSION}"'.encode("utf-8") in payload, (
        f'подстроки version:"{HTMX_VERSION}" в артефакте нет'
    )


@pytest.mark.asyncio
async def test_auth_shell_carries_htmx_config(client: AsyncClient):
    """auth_base.html: блок из шести ключей приезжает на /login разобранным.

    Подпись называет ШЕЛЛ, а не адрес: предмет — второй шелл проекта, а /login
    лишь одна из семи его страниц. Забытый {% include %} в ОДНОМ из двух шеллов
    — тот самый тихий отказ, ради которого гейт читает отрендеренный HTML.
    """
    response = await client.get("/login")
    assert response.status_code == 200

    html = response.text
    _assert_config_contract(_htmx_config_of(html, "auth_base.html"), "auth_base.html")
    _assert_config_precedes_runtime(html, "auth_base.html")


@pytest.mark.asyncio
async def test_main_shell_carries_htmx_config(authed_client: AsyncClient):
    """base.html: тот же блок приезжает на /dashboard тем же ОДНИМ include.

    Тест-близнец предыдущего, и парой они обязаны быть именно парой: шеллов в
    проекте два, конфигурация одна, и утверждение, снятое с одной страницы,
    ничего не говорит о второй. Подпись называет ШЕЛЛ, а не адрес — /dashboard
    здесь представитель всех 26 страничных маршрутов под base.html.
    """
    response = await authed_client.get("/dashboard")
    assert response.status_code == 200

    html = response.text
    _assert_config_contract(_htmx_config_of(html, "base.html"), "base.html")
    _assert_config_precedes_runtime(html, "base.html")


def test_htmx_runtime_tag_has_single_source():
    """D-01: ссылка на рантайм htmx живёт в ШАБЛОНАХ ровно в одном файле.

    Машинная форма доктрины «один источник, не вторая копия». Литеральный тег,
    вернувшийся в шелл, означал бы, что конфигурация и рантайм снова могут
    разъехаться: блок остался бы в include, а рантайм подгружался бы вторым
    тегом выше него — и htmx прочитал бы умолчания, не сказав ни слова.

    Обход РЕКУРСИВНЫЙ (rglob, не glob) по образцу _all_templates()
    из test_templates/test_components.py:856-865: плоский обход не увидел бы
    файл в подкаталоге, а именно там единственный законный владелец и живёт.

    Утверждается МНОЖЕСТВО путей, а не их число: сообщение об отказе обязано
    называть файл-нарушитель, иначе оно сообщает о расхождении счёта и
    оставляет поиск виновника читателю.

    Ищется ТЕГ ПОДКЛЮЧЕНИЯ, а не путь, и ищется он в исходнике БЕЗ комментариев
    (IN-02): шаблон, упомянувший путь в комментарии, ничего не подключает и
    нарушителем не является.
    """
    templates_dir = PROJECT_ROOT / "app" / "templates"
    owners = {
        path.relative_to(templates_dir).as_posix()
        for path in sorted(templates_dir.rglob("*.html"))
        if _HTMX_RUNTIME_TAG_RE.search(
            _without_comments(path.read_text(encoding="utf-8"))
        )
    }

    assert owners == {HTMX_RUNTIME_OWNER}, (
        "ссылка на рантайм htmx перестала быть единственной в шаблонах:\n"
        f"  найдено:  {sorted(owners)}\n"
        f"  ожидался: [{HTMX_RUNTIME_OWNER}]"
    )


@pytest.mark.asyncio
async def test_auth_shell_purges_the_legacy_history_cache_once(client: AsyncClient):
    """auth_base.html: миграционная очистка приезжает на /login ровно один раз.

    QUAL-05, машинная половина. Считается ЧИСЛО вхождений, а не признак
    наличия: снятие строки будущим планом обязано ронять тест ровно так же, как
    снятие любого из шести ключей конфигурации (D-13), а вторая копия — так же,
    как второй литеральный блок.

    ЧЕГО ЭТОТ ГЕЙТ НЕ ДОКАЗЫВАЕТ. Суита не исполняет ни строчки JS: httpx
    отдаёт текст ответа, а не браузер с хранилищем. Зелёный счёт вхождений
    означает «строка ДОСТАВЛЕНА в документ», а не «остаточных данных в
    localStorage не осталось». Разница между этими двумя утверждениями и есть в
    точности предмет QUAL-05: действие проверяется глазами в DevTools по
    процедуре 07-UAT.md, WINDOWS.md #11 остаётся открытым. Называть эту
    половину покрытием требования нельзя.
    """
    response = await client.get("/login")
    assert response.status_code == 200

    assert response.text.count(HISTORY_CACHE_KEY) == 1, (
        "строка очистки ключа снимков истории в auth-шелле встречается "
        f"{response.text.count(HISTORY_CACHE_KEY)} раз(а), ожидалась ровно одна"
    )


@pytest.mark.asyncio
async def test_main_shell_purges_the_legacy_history_cache_once(
    authed_client: AsyncClient,
):
    """base.html: та же очистка приезжает и на /dashboard, тоже ровно один раз.

    ⚠️ ПРЕЖНЕЕ УТВЕРЖДЕНИЕ ЭТОЙ ФУНКЦИИ СНЯТО, И СНЯТО ИМЕННО КАК НЕВЕРНОЕ.
    Функция называлась test_main_shell_does_not_clear_history_cache и утверждала
    count == 0, читая отсутствие очистки в основном шелле как соблюдение
    доктрины «одно действие — один владелец» (клауза размещения D-11). На
    отгруженном рантайме это прочтение не работает: 2.0.10 не касается
    localStorage вовсе, поэтому нулевой размер кеша истории на ОСТАТОК прежнего
    1.9.10 не влияет никак, а очистка, срабатывающая только при рендере
    auth-шелла, означает, что пользователь, не заходящий на /login, остаток не
    теряет НИКОГДА — вместе со снимками админки, платёжных форм и экранов,
    открытых под чужим именем.

    Доктрина единственного владельца при этом не нарушена, а восстановлена:
    строка по-прежнему выписана ОДИН раз, в includes/htmx_config.html, и оба
    шелла получают её тем же include, которым получают конфигурацию. Отвергнутый
    D-11 вариант — две литеральные копии в двух шеллах — не вводится и здесь;
    это и стережёт test_legacy_history_cache_purge_has_single_source.

    ЧЕГО ЭТОТ ГЕЙТ НЕ ДОКАЗЫВАЕТ — ровно того же, чего не доказывает его
    близнец по auth-шеллу: доставки строки, а не её действия.
    """
    response = await authed_client.get("/dashboard")
    assert response.status_code == 200

    assert response.text.count(HISTORY_CACHE_KEY) == 1, (
        "строка очистки ключа снимков истории в основном шелле встречается "
        f"{response.text.count(HISTORY_CACHE_KEY)} раз(а), ожидалась ровно одна: "
        "остаток 1.9.10 обязан сниматься на КАЖДОМ шелле, а не только при "
        "заходе на экран входа"
    )


def test_legacy_history_cache_purge_has_single_source():
    """D-01: строка миграционной очистки живёт в ШАБЛОНАХ ровно в одном файле.

    Близнец test_htmx_runtime_tag_has_single_source и по форме, и по основанию.
    Инвариант «ровно один раз в ОБОИХ шеллах» держится двумя разными
    утверждениями: пара гейтов выше отвечает за ДОСТАВКУ в каждый шелл, этот —
    за ЕДИНСТВЕННОСТЬ ИСТОЧНИКА. Без него зелёная пара была бы совместима с
    двумя литеральными копиями строки в двух шеллах, то есть ровно с тем
    вариантом, который D-11 отверг.

    Обход РЕКУРСИВНЫЙ (rglob, не glob): единственный законный владелец живёт в
    подкаталоге, и плоский обход его не увидел бы.

    Утверждается МНОЖЕСТВО путей, а не их число: сообщение об отказе обязано
    называть файл-нарушитель, иначе оно сообщает о расхождении счёта и
    оставляет поиск виновника читателю.

    Комментарии из исходника вырезаются тем же общим помощником, что и у гейта
    рантайма (IN-02): шаблон, назвавший ключ в комментарии-объяснении, ничего не
    чистит и владельцем не становится.

    ЧЕГО ЭТОТ ГЕЙТ НЕ ДОКАЗЫВАЕТ. Он говорит о ШАБЛОНАХ, а не о хранилище
    браузера: единственность источника строки ничего не сообщает о том, что
    строка отработала и остаточных данных не осталось.
    """
    templates_dir = PROJECT_ROOT / "app" / "templates"
    owners = {
        path.relative_to(templates_dir).as_posix()
        for path in sorted(templates_dir.rglob("*.html"))
        if HISTORY_CACHE_KEY in _without_comments(path.read_text(encoding="utf-8"))
    }

    assert owners == {LEGACY_HISTORY_CACHE_OWNER}, (
        "строка миграционной очистки перестала быть единственной в шаблонах:\n"
        f"  найдено:  {sorted(owners)}\n"
        f"  ожидался: [{LEGACY_HISTORY_CACHE_OWNER}]"
    )


def test_history_cache_purge_touches_no_markup_sink():
    """Инлайн-скрипт очистки не зовёт ни одного стока разметки и не читает запрос.

    T-07-09/T-07-04. Реестр угроз плана 07-01 объявлял мерой «гейт по исходнику
    шелла», но такого гейта в суите НЕ СУЩЕСТВОВАЛО — расхождение реестра с
    суитой закрывается здесь. Радиус скрипта вырос с семи экранов входа до ВСЕХ
    страниц проекта, поэтому утверждение перестало быть формальностью.

    Правило вехи v2.0 «сборка узлами DOM, не строкой» здесь держится тривиально:
    скрипт зовёт ровно один метод удаления ключа. Перечень стоков — MARKUP_SINKS,
    скопированный дословно из редактора объявления.

    ЧЕГО ЭТОТ ГЕЙТ НЕ ДОКАЗЫВАЕТ. Он читает ИСХОДНИК шаблона: отсутствие стоков
    в исходнике не есть утверждение о безопасности отрендеренного документа
    целиком, и политику безопасности содержимого (CSP, T-07-11) он не заменяет.
    """
    source = (
        PROJECT_ROOT / "app" / "templates" / LEGACY_HISTORY_CACHE_OWNER
    ).read_text(encoding="utf-8")

    offenders = [sink for sink in MARKUP_SINKS if sink in source]
    assert not offenders, (
        f"{LEGACY_HISTORY_CACHE_OWNER}: появился сток разметки {offenders} — "
        "инлайн-скрипт в <head> обоих шеллов начал собирать разметку строкой"
    )

    assert "request" not in source, (
        f"{LEGACY_HISTORY_CACHE_OWNER}: появилось обращение к request — "
        "инлайн-скрипт, исполняемый на КАЖДОЙ странице, начал читать значение "
        "из запроса"
    )

    # T-07-10 (реестр 07-04). Мера объявлена ДВУМЯ частями: перехват переносится
    # вместе со строкой, И его сохранность утверждается ЭТИМ гейтом. Вторая часть
    # отсутствовала — аудит безопасности Фазы 7 нашёл, что снятый try/catch
    # оставил бы зелёными все три гейта: пара доставки считает вхождения КЛЮЧА, а
    # не вызова, а утверждения выше говорят о стоках и о запросе.
    #
    # Почему это важнее, чем выглядит: доступ к localStorage ВЫБРАСЫВАЕТ в
    # приватном режиме и при запрещённых сайтовых данных. Радиус скрипта вырос с
    # семи экранов входа до <head> КАЖДОЙ страницы, поэтому необработанное
    # исключение останавливает разбор документа целиком, а не портит один экран.
    #
    # Комментарии вырезаются: шаблон, написавший слово try в объяснении, ничего
    # не перехватывает (тот же принцип, что у гейта единственности источника).
    code = _without_comments(source)

    purge_at = code.find("removeItem")
    assert purge_at != -1, (
        f"{LEGACY_HISTORY_CACHE_OWNER}: вызов removeItem исчез из исходника — "
        "миграционная очистка снята. Если снятие СОЗНАТЕЛЬНОЕ (остаток 1.9.10 "
        "признан выбывшим), снимать надо вместе с этим гейтом и записью в "
        "WINDOWS.md, а не молча"
    )

    try_at = code.rfind("try", 0, purge_at)
    catch_at = code.find("catch", purge_at)
    assert try_at != -1 and catch_at != -1, (
        f"{LEGACY_HISTORY_CACHE_OWNER}: вызов removeItem перестал быть обёрнут в "
        "try/catch. Доступ к localStorage выбрасывает в приватном режиме и при "
        "запрещённых сайтовых данных, а скрипт исполняется в <head> КАЖДОЙ "
        "страницы — необработанное исключение останавливает разбор документа "
        "целиком. Гейты доставки этого не увидят: они считают вхождения ключа, "
        "а не вызова"
    )


# --- FOUND-06: две области уведомления в обоих шеллах ------------------------

# ЕДИНСТВЕННЫЙ законный владелец разметки областей уведомления среди шаблонов.
# Имя выписано ЗДЕСЬ, а не выведено обходом, по тому же основанию, что и
# HTMX_RUNTIME_OWNER выше: тест, назначающий владельцем того, кого нашёл,
# согласился бы с переездом областей куда угодно.
NOTICE_AREA_OWNER = "includes/notice_area.html"

# Оба шелла проекта. Перечень выписан, а не собран обходом: предмет требования —
# что канал есть у КАЖДОГО шелла, и шелл, забывший включение, обязан краснеть, а
# не молча выпадать из собранного множества.
NOTICE_AREA_SHELLS = ("base.html", "auth_base.html")

# Идентификатор области → её признак роли и её признак живости.
#
# ПАРА ПРИЗНАКОВ ПРОВЕРЯЕТСЯ ЦЕЛИКОМ, А НЕ ПО ОДНОМУ. Область с role="alert" и
# aria-live="polite" разметку проходит, а человеку даёт отказ, объявленный
# «когда будет пауза», — то есть ровно тот исход, ради которого областей две.
NOTICE_REGIONS = {
    "notice": ("status", "polite"),
    "notice-alert": ("alert", "assertive"),
}

# Включение областей в ИСХОДНИКЕ шелла. Ищется ОПЕРАТОР включения, а не имя
# файла: шаблон, назвавший файл в комментарии-объяснении, ничего не подключает.
_NOTICE_AREA_INCLUDE_RE = re.compile(
    r"\{%-?\s*include\s+[\"']" + re.escape(NOTICE_AREA_OWNER) + r"[\"']"
)


def _notice_region(html: str, region_id: str) -> str:
    """СОДЕРЖИМОЕ названной области уведомления из отрендеренного документа.

    Читается ответ, а не исходник шаблона: предмет проверки — что получил
    человек, а условие Jinja, съехавшее в другую ветку, оставило бы греп
    исходника зелёным.

    Совпадение НЕЖАДНОЕ и обрывается на первом закрывающем теге. Для пустой
    области это ровно её содержимое; для непустой — открывающий тег плашки
    вместе с её текстом, и этого довольно: утверждения ниже спрашивают наличие
    класса плашки и наличие текста записи, а не полную вложенную разметку.
    """
    match = re.search(
        rf'<div id="{re.escape(region_id)}"[^>]*>(.*?)</div>', html, re.DOTALL
    )
    assert match, (
        f"области уведомления #{region_id} в документе нет вовсе — забытое "
        "включение в одном из двух шеллов"
    )
    return match.group(1)


def _assert_both_regions_present(html: str, shell: str) -> None:
    """Обе области приехали в документ по одному разу и несут свои признаки."""
    for region_id, (role, live) in NOTICE_REGIONS.items():
        seen = html.count(f'id="{region_id}"')
        assert seen == 1, (
            f"{shell}: область #{region_id} встречается {seen} раз(а), "
            "ожидалась ровно одна — вторая копия означала бы, что внеполосная "
            "подмена целится в неизвестно какую из них"
        )
        opening = re.search(rf'<div id="{re.escape(region_id)}"[^>]*>', html)
        assert opening, f"{shell}: открывающего тега области #{region_id} нет"
        tag = opening.group(0)
        assert f'role="{role}"' in tag, (
            f"{shell}: у области #{region_id} нет признака роли {role} — {tag}"
        )
        assert f'aria-live="{live}"' in tag, (
            f"{shell}: у области #{region_id} нет признака живости {live} — {tag}"
        )


@pytest.mark.asyncio
async def test_main_shell_carries_both_notice_regions(authed_client: AsyncClient):
    """base.html: вежливая и настойчивая области приезжают на /profile.

    Подпись называет ШЕЛЛ, а не адрес: /profile здесь представитель всех 26
    страничных маршрутов под base.html. Тест-близнец по второму шеллу стоит
    ниже, и парой они обязаны быть именно парой — шеллов два, включение одно, и
    утверждение, снятое с одного, ничего не говорит о втором.
    """
    response = await authed_client.get("/profile")
    assert response.status_code == 200
    _assert_both_regions_present(response.text, "base.html")


@pytest.mark.asyncio
async def test_auth_shell_carries_both_notice_regions(client: AsyncClient):
    """auth_base.html: те же две области приезжают на /login тем же включением.

    Второй шелл получает канал НАРАВНЕ с основным, а не по остаточному
    принципу: признак смены пароля приземляется именно здесь.
    """
    response = await client.get("/login")
    assert response.status_code == 200
    _assert_both_regions_present(response.text, "auth_base.html")


@pytest.mark.asyncio
async def test_without_a_code_neither_region_draws_a_banner(
    authed_client: AsyncClient,
):
    """Нет кода — нет ПЛАШКИ, при том что узлы областей на месте (FOUND-06).

    Утверждения здесь два, и они разные. Первое: плашки нет ни в одной области —
    умолчание «показать» запрещено прямо, а пустая рамка сообщала бы о событии,
    которого не было. Второе: узлы областей всё же существуют — внеполосная
    подмена целится в них ПО ИДЕНТИФИКАТОРУ, и без стабильного узла ответ
    приехал бы в никуда, молча.
    """
    response = await authed_client.get("/profile")
    assert response.status_code == 200
    html = response.text

    _assert_both_regions_present(html, "base.html")
    for region_id in NOTICE_REGIONS:
        assert 'class="alert' not in _notice_region(html, region_id), (
            f"без кода уведомления в области #{region_id} нарисована плашка — "
            "умолчание «показать» вернулось"
        )


@pytest.mark.asyncio
async def test_a_known_code_draws_in_the_polite_region_by_its_variant(
    authed_client: AsyncClient,
):
    """Известный код НЕ аварийного варианта рисуется в вежливой области."""
    record = notices.notice_for(notices.PROFILE_SAVED)
    assert record is not None and record.variant != "error"

    response = await authed_client.get(f"/profile?notice={notices.PROFILE_SAVED}")
    assert response.status_code == 200
    html = response.text

    assert record.text in _notice_region(html, "notice"), (
        "текст записи не попал в вежливую область"
    )
    assert 'class="alert' not in _notice_region(html, "notice-alert"), (
        "запись неаварийного варианта нарисовалась в НАСТОЙЧИВОЙ области — "
        "успех сохранения перебивал бы человека посреди чтения"
    )


@pytest.mark.asyncio
async def test_a_known_error_code_draws_in_the_assertive_region(
    authed_client: AsyncClient,
):
    """Известный код аварийного варианта рисуется в настойчивой области."""
    record = notices.notice_for(notices.PAYMENT_FAILED)
    assert record is not None and record.variant == "error"

    response = await authed_client.get(f"/billing?notice={notices.PAYMENT_FAILED}")
    assert response.status_code == 200
    html = response.text

    assert record.text in _notice_region(html, "notice-alert"), (
        "текст записи не попал в настойчивую область"
    )
    assert 'class="alert' not in _notice_region(html, "notice"), (
        "отказ нарисовался в ВЕЖЛИВОЙ области — объявление ждало бы паузы в "
        "речи, а человек за это время нажал бы кнопку второй раз"
    )


@pytest.mark.asyncio
async def test_the_auth_shell_draws_a_known_code_too(client: AsyncClient):
    """/login?notice=… рисует плашку: второй шелл получил канал по-настоящему."""
    record = notices.notice_for(notices.PASSWORD_RESET_DONE)
    assert record is not None

    response = await client.get(f"/login?notice={notices.PASSWORD_RESET_DONE}")
    assert response.status_code == 200

    assert record.text in _notice_region(response.text, "notice"), (
        "экран входа не нарисовал известный код — канал во втором шелле мёртв"
    )


@pytest.mark.asyncio
async def test_an_unknown_code_draws_nothing_and_never_reaches_the_document(
    authed_client: AsyncClient,
):
    """T-08-08/T-08-12: чужое значение не рисует НИЧЕГО и в документ не уходит.

    ⚠️ ПРЯМОЕ УТВЕРЖДЕНИЕ «ПОДСТРОКИ ТЕГА СЦЕНАРИЯ В ТЕЛЕ НЕТ» ЗДЕСЬ
    НЕВЫРАЗИМО, И ЭТО СВОЙСТВО ДОКУМЕНТА, А НЕ ПОСЛАБЛЕНИЕ. Оба шелла несут
    инлайн-сценарий миграционной очистки (includes/htmx_config.html), то есть
    открывающий тег сценария без атрибутов присутствует в КАЖДОМ ответе
    независимо от адреса. Утверждение о его отсутствии было бы красным всегда —
    то есть не утверждением, а поломкой.

    Проверяемое свойство поэтому записано ТРЕМЯ утверждениями, вместе строгими:
    плашки нет ни в одной области; ЭКРАНИРОВАННОЙ формы присланного значения в
    документе нет (её появление означало бы, что значение уехало в разметку и
    спаслось лишь автоэкранированием); и число тегов сценария в ответе С
    параметром РАВНО числу в ответе БЕЗ него — присланное значение не добавило
    в документ ни одного узла. Последнее и есть недостижимость: вход в разметку
    не связан со входом из адреса.
    """
    baseline = await authed_client.get("/profile")
    assert baseline.status_code == 200

    response = await authed_client.get("/profile?notice=%3Cscript%3E")
    assert response.status_code == 200
    html = response.text

    for region_id in NOTICE_REGIONS:
        assert 'class="alert' not in _notice_region(html, region_id), (
            f"неизвестный код нарисовал плашку в области #{region_id} — реестр "
            "перестал быть закрытым, и владелец ссылки печатает пользователю "
            "сообщение от имени приложения"
        )

    assert "&lt;script&gt;" not in html, (
        "присланное значение уехало в разметку и спаслось только "
        "автоэкранированием — недостижимость подменилась экранированием"
    )

    seen = html.count("<script")
    expected = baseline.text.count("<script")
    assert seen == expected, (
        f"ответ с параметром несёт {seen} тег(ов) сценария против {expected} "
        "без него — присланное значение добавило в документ узел"
    )


def test_notice_area_has_single_source():
    """D-01: разметка областей уведомления живёт в ШАБЛОНАХ ровно в одном файле.

    Близнец test_htmx_runtime_tag_has_single_source и по форме, и по основанию.
    Инвариант «ровно один раз в ОБОИХ шеллах» держится двумя разными
    утверждениями: пара гейтов доставки выше отвечает за КАЖДЫЙ шелл, этот — за
    ЕДИНСТВЕННОСТЬ ИСТОЧНИКА. Без него зелёная пара была бы совместима с двумя
    литеральными копиями областей в двух шеллах — то есть ровно с тем вариантом,
    который D-01 отверг.

    Утверждается МНОЖЕСТВО путей, а не их число: сообщение об отказе обязано
    называть файл-нарушитель.

    Комментарии из исходника вырезаются общим помощником (IN-02): шаблон,
    назвавший идентификатор области в объяснении, ничего не рисует.
    """
    templates_dir = PROJECT_ROOT / "app" / "templates"

    owners = {
        path.relative_to(templates_dir).as_posix()
        for path in sorted(templates_dir.rglob("*.html"))
        if 'id="notice"' in _without_comments(path.read_text(encoding="utf-8"))
    }
    assert owners == {NOTICE_AREA_OWNER}, (
        "разметка областей уведомления перестала быть единственной в шаблонах:\n"
        f"  найдено:  {sorted(owners)}\n"
        f"  ожидался: [{NOTICE_AREA_OWNER}]"
    )

    found = {}
    for path in sorted(templates_dir.rglob("*.html")):
        count = len(
            _NOTICE_AREA_INCLUDE_RE.findall(
                _without_comments(path.read_text(encoding="utf-8"))
            )
        )
        if count:
            found[path.relative_to(templates_dir).as_posix()] = count

    expected = {shell: 1 for shell in NOTICE_AREA_SHELLS}
    assert found == expected, (
        "включение областей уведомления подключено не по одному разу в каждый "
        "из двух шеллов:\n"
        f"  найдено:   {found}\n"
        f"  ожидалось: {expected}"
    )


# --- G-23: плашки отказа сервера и обрыва связи (QUAL-03) --------------------
#
# ЧТО ЭТА ГРУППА ДОБАВЛЯЕТ К УЖЕ НАПИСАННОМУ В ЭТОМ ФАЙЛЕ. Версия вендоренного
# рантайма, шесть ключей блока конфигурации и порядок пяти правил
# responseHandling УЖЕ утверждены выше — test_vendored_htmx_is_the_declared_artifact,
# test_auth_shell_carries_htmx_config, test_main_shell_carries_htmx_config. Здесь
# они НЕ дублируются: второе утверждение о том же предмете не строже первого, а
# при правке расходится с ним молча. Предмет этой группы — видимость ОТКАЗА:
# заготовки плашек, два обработчика и различение ошибки заполнения формы от
# аварии сервера.
#
# ЧЕГО ГРУППА НЕ ДОКАЗЫВАЕТ. Суита не исполняет ни строчки JS: httpx отдаёт
# текст ответа, а не браузер с событиями. Зелёный гейт означает «строки
# ДОСТАВЛЕНЫ в документ» и «в исходнике включения есть то, что обязано быть», а
# не «плашка появилась при выключенной сети». Разница между этими утверждениями
# и есть пункт 8 перечня ручного UAT.

# ЕДИНСТВЕННЫЙ законный владелец заготовок и обработчиков среди шаблонов.
FAILURE_BANNER_OWNER = "includes/htmx_error_banner.html"

FAILURE_BANNER_SHELLS = ("base.html", "auth_base.html")

# Идентификаторы двух заготовок. Отказ сервера и обрыв связи — РАЗНЫЕ поводы и
# разные следующие действия человека, поэтому и плашек две.
FAILURE_BANNER_IDS = ("htmx-failure-server", "htmx-failure-network")

# Имена двух событий слоя письма. Событие отказа ОТВЕТА не возникает, когда
# ответа не было вовсе, — его место занимает событие отказа ОТПРАВКИ. С одним
# обработчиком выключенная сеть неотличима от сломанной кнопки (R-2).
FAILURE_BANNER_EVENTS = ("htmx:responseError", "htmx:sendError")

# Код ответа, по которому канал отличает ошибку ЗАПОЛНЕНИЯ ФОРМЫ от отказа
# сервера. Выписан здесь строкой, а не взят из проверяемого файла: ожидание,
# добытое из предмета проверки, согласилось бы с любой его правкой.
VALIDATION_STATUS = "422"

# Свойство ответа, которого в сценарии быть не должно: читать разрешено ТОЛЬКО
# код состояния. Тело чужого ответа, попавшее в плашку, вынесло бы наружу
# внутреннее устройство (T-08-20).
RESPONSE_BODY_READ = "responseText"

# Слова, которые ОБЯЗАНЫ стоять в тексте плашки ОБРЫВА СВЯЗИ (D-16, Фаза 9).
#
# ПОЧЕМУ ОЖИДАНИЕ ВЫПИСАНО ЗДЕСЬ, А НЕ ВЫБРАНО ИЗ ПРОВЕРЯЕМОГО ФАЙЛА. По той же
# причине, что и VALIDATION_STATUS выше: ожидание, добытое из предмета проверки,
# согласилось бы с любой его правкой — в том числе с правкой, стирающей смысл.
#
# ПОЧЕМУ ЭТО ОЖИДАНИЕ ВООБЩЕ СУЩЕСТВУЕТ. У тумблера есть изъян, которого нет у
# кнопок: браузер переключает чекбокс МГНОВЕННО, до ответа. Когда сервер ответил,
# случай закрыт — строка приезжает с сервера настоящим состоянием. Когда ответа
# не было ВОВСЕ, на экране остаётся оптимистичный результат, а веха оптимистичный
# UI прямо запрещает: «пользователь думает, что группа выключена, а объявление
# туда уходит». Единственный канал, в котором это расхождение называется словами,
# — текст этой плашки, и его содержание поэтому утверждается, а не подразумевается.
#
# ПОЧЕМУ ИМЕННО ЭТИ ЧЕТЫРЕ ОСНОВЫ, А НЕ ФРАЗА ЦЕЛИКОМ. Утверждается СМЫСЛ, а не
# редакция: где расхождение видно («экран»), с чем оно («серв»), что человеку
# сделать («обнов») и что он тогда увидит («настоящ»). Фраза целиком запретила бы
# UI-ревью поправить формулировку, не тронув смысла, — то есть охраняла бы буквы.
NETWORK_BANNER_DIVERGENCE = ("экран", "серв", "обнов", "настоящ")

# Половина, которая в тексте плашки обрыва связи УЖЕ есть. Дополнение обязано
# добавлять смысл, а не повторять сказанное: человек прочитал этот совет в первой
# половине, и второе его вхождение означало бы, что дополнение ничего не сказало.
NETWORK_BANNER_REPEATED_ADVICE = "попробуйте ещё раз"

_FAILURE_BANNER_INCLUDE_RE = re.compile(
    r"\{%-?\s*include\s+[\"']" + re.escape(FAILURE_BANNER_OWNER) + r"[\"']"
)


def _failure_banner_path() -> Path:
    """Путь настоящего включения — единственное место, где он собирается."""
    return PROJECT_ROOT / "app" / "templates" / FAILURE_BANNER_OWNER


def _failure_banner_source(path: Path) -> str:
    """Исходник включения ПО НАЗВАННОМУ ПУТИ, а не по константе модуля.

    ⚠️ ПАРАМЕТР ЗДЕСЬ И ЕСТЬ ТО, ЧТО ДЕЛАЕТ ГРУППУ КОНТРОЛЯ ВОЗМОЖНОЙ.
    Утверждения этой группы суть «строка присутствует в файле», и у таких
    утверждений есть свой способ соврать: разбор, читающий НЕ ТОТ файл или
    вырезающий комментарии слишком жадно, зеленеет на чём угодно. Функция,
    принимающая путь, позволяет подать гейту ИЗМЕНЁННУЮ копию во временном
    каталоге и потребовать красноты — то есть доказать зубы, а не объявить их.
    Читай эта функция константу, контроль был бы невыразим.
    """
    return path.read_text(encoding="utf-8")


def _failure_banner_code(path: Path) -> str:
    """То же без комментариев: комментарий ничего не исполняет.

    Вырезание обязательно и здесь, и по той же причине, что у гейтов
    единственности (IN-02): объяснение, называющее событие или код ответа,
    оставило бы гейт зелёным даже после того, как сама строка снята из
    сценария. Ровно это и проверяют два отрицательных контроля ниже.
    """
    return _without_comments(_failure_banner_source(path))


def _failure_banner_missing_events(path: Path) -> tuple[str, ...]:
    """Имена событий, которых в сценарии НЕТ. Пусто — оба обработчика на месте."""
    code = _failure_banner_code(path)
    return tuple(name for name in FAILURE_BANNER_EVENTS if name not in code)


def _failure_banner_markup_sinks(path: Path) -> tuple[str, ...]:
    """Стоки разметки, найденные в исходнике включения ЦЕЛИКОМ.

    Читается исходник С комментариями — намеренно, и это не оплошность: сток,
    «объяснённый» в комментарии, приехал бы туда же одним движением правки, а
    объяснять запрещённое собственным литералом этот проект и так не умеет
    (урок includes/htmx_config.html). Форма и перечень скопированы у
    test_history_cache_purge_touches_no_markup_sink.
    """
    source = _failure_banner_source(path)
    return tuple(sink for sink in MARKUP_SINKS if sink in source)


def _failure_banner_tells_validation_from_a_crash(path: Path) -> bool:
    """Есть ли в сценарии сравнение с кодом ответа валидации."""
    return VALIDATION_STATUS in _failure_banner_code(path)


def _network_banner_line(path: Path) -> str:
    """Строка узла заготовки ОБРЫВА СВЯЗИ, приведённая к нижнему регистру.

    Берётся ровно ОДНА строка исходника — та, что несёт идентификатор
    htmx-failure-network. Это не экономия чтения, а несущее свойство разбора:
    объяснение в докстринге файла говорит о том же расхождении теми же словами,
    и гейт, читающий файл целиком, зеленел бы от КОММЕНТАРИЯ после того, как сам
    текст плашки лишился бы смысла. Ровно этот урок оставлен в
    includes/htmx_config.html и повторён здесь.

    Соседняя заготовка (отказ сервера) в строку не попадает намеренно: у неё
    другой повод и другое следующее действие человека, и требовать от неё слов о
    расхождении экрана с сервером значило бы пересматривать QUAL-03.

    Путь параметром — по той же причине, что у _failure_banner_source: иначе
    подать гейту изменённую копию и потребовать красноты было бы невозможно.
    """
    for line in _failure_banner_source(path).splitlines():
        if f'id="{FAILURE_BANNER_IDS[1]}"' in line:
            return line.lower()
    return ""


def _scratch_banner(tmp_path, text: str) -> Path:
    """Изменённая копия включения во временном каталоге.

    Подмена идёт по-настоящему через файловую систему, а не строкой в памяти:
    так контроль проверяет ТОТ ЖЕ путь чтения, которым гейт ходит по боевому
    дереву, и не может разойтись с ним из-за кодировки или переносов строк.
    Форма скопирована из test_impersonation_gate.py.
    """
    scratch = tmp_path / Path(FAILURE_BANNER_OWNER).name
    scratch.write_text(text, encoding="utf-8")
    return scratch


# --- Число регистраций обработчиков (WR-05, план 09-19) -----------------------
#
# ⚠️ ЧТО ЗДЕСЬ ИЗМЕРЯЕТСЯ И ПОЧЕМУ ЭТО НЕ СЛЕДУЕТ ИЗ РАЗМЕТКИ. `allowScriptTags`
# в проекте остаётся умолчанием `true` (`includes/htmx_config.html:87`, и
# мета-блок конфигурации его не переопределяет), а переход `HX-Location`
# (`app/pages/htmx.py`) документ НЕ ПЕРЕЗАГРУЖАЕТ: он забирает страницу
# запросом и вклеивает её. Значит инлайн-сценарий этого включения исполняется
# ЗАНОВО на каждом таком переходе и вешает слушателей ещё раз. Оба обработчика
# идемпотентны (`removeAttribute('hidden')`), поэтому видимого отказа нет — но
# канал этот ОБЩИЙ для обеих оболочек и для всех сорока семи форм вехи, и число
# слушателей на живом узле тела документа росло бы всю сессию (T-09-19-01).
#
# ⚠️ ЧТО ПРАВИЛО ДОКАЗЫВАЕТ, А ЧТО НЕТ. Оно доказывает, что ПОВТОРНОЕ
# ИСПОЛНЕНИЕ сценария не удваивает регистраций. Оно НЕ доказывает, что узел
# тела переживает подмену в браузере: ревизия назвала эту неопределённость
# прямо, и правило шире неё не становится. Замер счётчиком регистраций в живом
# браузере остаётся человеку — проверка 4.2 плана 09-20.

# ⚠️ ЧИСЛО ИЗМЕРЕНО ПО ДЕРЕВУ, А НЕ ВЗЯТО ИЗ ПАМЯТИ (идиома SP-1,
# 09-PATTERNS.md): в сценарии включения ровно два вызова регистрации — по
# одному на каждое из имён FAILURE_BANNER_EVENTS. Без этого числа правило
# «после двух исполнений столько же, сколько после одного» зеленело бы ВАКУУМОМ
# — на сценарии, не вешающем НИЧЕГО: ноль равен нулю.
FAILURE_BANNER_HANDLERS_MEASURED = 2

# Гарнир регистраций: стаб-узел тела документа со счётчиком. Стаб неймитирующий
# ровно там, где предмет, — счётчик настоящий; всё остальное (поиск узла по
# идентификатору, снятие атрибута) предметом не является и стабится.
FAILURE_BANNER_REGISTRATION_HARNESS = """
'use strict';
const SOURCE = __SOURCE__;
const RUNS = __RUNS__;
let registrations = 0;
const body = {
  dataset: {},
  addEventListener: function () { registrations += 1; }
};
globalThis.document = {
  body: body,
  getElementById: function () { return { removeAttribute: function () {} }; }
};
const script = new Function(SOURCE);
for (let i = 0; i < RUNS; i += 1) { script(); }
process.stdout.write(JSON.stringify({ registrations: registrations }));
"""

_BANNER_SCRIPT_RE = re.compile(r"<script>(.*?)</script>", re.DOTALL)

# Узел, к которому вешаются слушатели, и узел, на котором стои́т признак
# однократности. Разбирается ПРИЁМНИК вызова, а не факт вхождения строки:
# предмет правила — совпадение двух узлов, а не наличие двух слов.
_LISTENER_HOST_RE = re.compile(r"([A-Za-z_$][\w.$]*)\.addEventListener\s*\(")
_GUARD_HOST_RE = re.compile(r"([A-Za-z_$][\w.$]*)\.dataset\s*\.\s*(\w+)")


def _failure_banner_script(path: Path) -> str:
    """Исходник инлайн-сценария включения — и ничего кроме него.

    Путь параметром — по той же причине, что у ``_failure_banner_source``:
    иначе подать гейту изменённую копию и потребовать красноты было бы
    невозможно.
    """
    found = _BANNER_SCRIPT_RE.findall(_failure_banner_source(path))
    assert len(found) == 1, (
        f"{FAILURE_BANNER_OWNER}: блоков сценария в файле {len(found)}, а не "
        "один — разборщик рассчитан на единственный, и выбор блока стал бы "
        "молчаливым"
    )
    return found[0]


def _failure_banner_registration_count(path: Path, runs: int = 2) -> int:
    """Число регистраций обработчиков после ``runs`` исполнений сценария.

    Исполняется исходник ПО НАЗВАННОМУ ПУТИ — ровно затем, чтобы контроль мог
    подать изменённую копию и потребовать удвоения.
    """
    harness = FAILURE_BANNER_REGISTRATION_HARNESS.replace(
        "__SOURCE__", json.dumps(_failure_banner_script(path))
    ).replace("__RUNS__", str(runs))
    return run_node_script(harness)["registrations"]


def _assert_both_banners_delivered(html: str, shell: str) -> None:
    """Обе заготовки приехали по одному разу и приехали СКРЫТЫМИ."""
    for banner_id in FAILURE_BANNER_IDS:
        seen = html.count(f'id="{banner_id}"')
        assert seen == 1, (
            f"{shell}: заготовка #{banner_id} встречается {seen} раз(а), "
            "ожидалась ровно одна"
        )
        opening = re.search(rf'<div id="{re.escape(banner_id)}"[^>]*>', html)
        assert opening, f"{shell}: открывающего тега заготовки #{banner_id} нет"
        assert "hidden" in opening.group(0), (
            f"{shell}: заготовка #{banner_id} приехала ВИДИМОЙ — плашка аварии "
            f"нарисована на исправной странице: {opening.group(0)}"
        )


@pytest.mark.asyncio
async def test_main_shell_carries_both_failure_banners(authed_client: AsyncClient):
    """base.html: обе заготовки приезжают на /profile и приезжают скрытыми."""
    response = await authed_client.get("/profile")
    assert response.status_code == 200
    _assert_both_banners_delivered(response.text, "base.html")


@pytest.mark.asyncio
async def test_auth_shell_carries_both_failure_banners(client: AsyncClient):
    """auth_base.html: те же две заготовки приезжают на /login.

    Второй шелл получает видимость отказа наравне с основным: форма входа ходит
    через слой письма ровно так же, как форма оплаты.
    """
    response = await client.get("/login")
    assert response.status_code == 200
    _assert_both_banners_delivered(response.text, "auth_base.html")


def test_the_failure_banner_carries_both_handlers():
    """Обработчиков ДВА, а не один (R-2).

    Без второго обработчика выключенная сеть неотличима от сломанной кнопки:
    событие отказа ответа не возникает, когда ответа не было вовсе, и человек
    жмёт кнопку в пустоту, не получая ни одного признака того, что дело в связи.
    """
    missing = _failure_banner_missing_events(_failure_banner_path())

    assert missing == (), (
        f"{FAILURE_BANNER_OWNER}: в сценарии нет обработчика(ов) {missing} — "
        "видимость отказа потеряла одну из двух своих половин"
    )


def test_the_failure_banner_registers_its_handlers_once_per_body():
    """ПОВЕДЕНЧЕСКОЕ: два исполнения сценария дают столько же регистраций.

    Переход `HX-Location` документ не перезагружает, а вклеивает страницу
    запросом — сценарий исполняется ЗАНОВО. Без признака однократности число
    слушателей на живом узле тела документа росло бы всю сессию, а канал этот
    общий для обеих оболочек и для всех сорока семи форм вехи (WR-05,
    T-09-19-01).

    ⚠️ АНТИВАКУУМНОЕ УТВЕРЖДЕНИЕ СТОИ́Т ПЕРВЫМ. Без него правило зеленело бы на
    сценарии, не вешающем НИЧЕГО: после двух исполнений ноль равен нулю после
    одного, и «регистрация однократна» было бы неотличимо от «регистрации нет».

    ⚠️ ЧЕГО ЭТО ПРАВИЛО НЕ ДОКАЗЫВАЕТ: что узел тела переживает подмену в
    БРАУЗЕРЕ. Ревизия назвала эту неопределённость прямо; замер счётчиком
    регистраций в живом браузере — проверка 4.2 плана 09-20.
    """
    path = _failure_banner_path()

    after_one = _failure_banner_registration_count(path, runs=1)
    assert after_one == FAILURE_BANNER_HANDLERS_MEASURED > 0, (
        f"{FAILURE_BANNER_OWNER}: одно исполнение сценария дало {after_one} "
        f"регистраций, а измерено {FAILURE_BANNER_HANDLERS_MEASURED} — правило "
        "об однократности проверяло бы сценарий, который вешает не то число "
        "обработчиков (или не вешает ни одного)"
    )

    after_two = _failure_banner_registration_count(path, runs=2)
    assert after_two == FAILURE_BANNER_HANDLERS_MEASURED, (
        f"{FAILURE_BANNER_OWNER}: два исполнения сценария дали {after_two} "
        f"регистраций вместо {FAILURE_BANNER_HANDLERS_MEASURED} — на каждом "
        "переходе HX-Location общий канал видимости отказа вешает слушателей "
        "ЗАНОВО, и число их растёт всю сессию"
    )


def test_the_failure_banner_guard_lives_on_the_node_it_wires():
    """Признак однократности стои́т на ТОМ ЖЕ узле, к которому вешаются слушатели.

    ⚠️ ЭТО НЕ ПЕДАНТИЗМ, А ОТДЕЛЬНАЯ УГРОЗА (T-09-19-02). Признак, поставленный
    на документ или на окно, пережил бы подмену узла тела и оставил бы НОВЫЙ
    узел без обработчиков ВОВСЕ — человек перестал бы видеть отказы, и отказ
    этот громче исходного накопления. Признак на самом узле означает: подмена
    узла снимает и признак, и регистрация происходит ровно один раз на ЖИВОЙ
    узел.

    Разбирается ПРИЁМНИК вызова, а не факт вхождения слова: предмет — совпадение
    двух узлов, а не наличие двух строк.
    """
    code = _failure_banner_code(_failure_banner_path())

    listener_hosts = _LISTENER_HOST_RE.findall(code)
    assert len(listener_hosts) == FAILURE_BANNER_HANDLERS_MEASURED, (
        f"{FAILURE_BANNER_OWNER}: вызовов регистрации в сценарии "
        f"{len(listener_hosts)}, а измерено {FAILURE_BANNER_HANDLERS_MEASURED} "
        "— правило о совпадении узлов проверяло бы не тот сценарий"
    )

    guards = _GUARD_HOST_RE.findall(code)
    assert guards, (
        f"{FAILURE_BANNER_OWNER}: признака однократности в сценарии НЕТ — "
        "обработчики вешаются заново на каждом переходе HX-Location (WR-05)"
    )

    flags = {name for _host, name in guards}
    assert len(flags) == 1, (
        f"{FAILURE_BANNER_OWNER}: признаков однократности в сценарии несколько "
        f"({sorted(flags)}) — проверка и присвоение разъехались бы молча"
    )

    guard_hosts = {host for host, _name in guards}
    assert guard_hosts == set(listener_hosts), (
        f"{FAILURE_BANNER_OWNER}: признак однократности стои́т на "
        f"{sorted(guard_hosts)}, а слушатели вешаются на "
        f"{sorted(set(listener_hosts))} — подмена узла снимет слушателей, но "
        "НЕ снимет признак, и новый узел останется без обработчиков вовсе "
        "(T-09-19-02)"
    )


def test_control_negative_an_unguarded_banner_accumulates_listeners(tmp_path):
    """ЧТО ДОКАЗЫВАЕТ: правило однократности зелено ПРИЗНАКОМ, а не вакуумом.

    Тот же замер на подставленной копии БЕЗ признака обязан дать удвоенное
    число. Без этого контроля правило выше было бы совместимо с гарниром,
    который исполняет сценарий один раз вместо двух, — и «однократность»
    доказывалась бы ошибкой замера.
    """
    original = _failure_banner_source(_failure_banner_path())

    negation = re.search(r"!\s*[A-Za-z_$][\w.$]*\.dataset\s*\.\s*\w+", original)
    assert negation, (
        "в настоящем файле нет проверки признака однократности — подставлять "
        "нечего, и контроль ничего не доказал бы"
    )

    # Двойной предохранитель подстановки: якорь встречается ровно один раз, и
    # результат отличается от исходника. Условие обращается в заведомо истинное,
    # а не вырезается вместе с телом: снятым обязан быть ПРИЗНАК, а не
    # регистрация.
    anchor = negation.group(0)
    assert original.count(anchor) == 1, (
        f"якорь замены {anchor!r} встречается не один раз — подмена задела бы "
        "чужую разметку"
    )
    unguarded = original.replace(anchor, "true")
    assert unguarded != original, "подмена не сработала — якорь замены не найден"
    assert unguarded.count("addEventListener") == FAILURE_BANNER_HANDLERS_MEASURED, (
        "из подставленной копии исчезли вызовы регистрации: контроль перестал "
        "доказывать накопление и стал доказывать пустоту"
    )

    doubled = _failure_banner_registration_count(
        _scratch_banner(tmp_path, unguarded), runs=2
    )

    assert doubled == 2 * FAILURE_BANNER_HANDLERS_MEASURED, (
        "КОПИЯ БЕЗ ПРИЗНАКА НЕ НАКОПИЛА СЛУШАТЕЛЕЙ: два исполнения дали "
        f"{doubled} регистраций вместо {2 * FAILURE_BANNER_HANDLERS_MEASURED} "
        "— значит замер не считает регистрации, и зелёное правило однократности "
        "выше не доказывает ничего"
    )


def test_the_failure_banner_touches_no_markup_sink():
    """Сценарий не собирает разметку и не читает из ответа ничего лишнего.

    T-08-18 и T-08-20. Радиус сценария — ВСЕ страницы обоих шеллов, поэтому
    утверждение не формальность: сток разметки здесь был бы стоком исполнения на
    каждом экране продукта. Перечень стоков — MARKUP_SINKS, тот же, что у
    инлайн-сценария миграционной очистки; второго ОПРЕДЕЛЕНИЯ одного запрета в
    проекте не заводится.

    Второе утверждение — сверх перечня стоков и добавлено по букве реестра
    угроз: сценарию разрешено читать из пришедшего ответа ТОЛЬКО код состояния.
    Тело чужого ответа, подставленное в плашку, вынесло бы наружу внутреннее
    устройство, а человеку не сообщило бы ничего.

    ЧЕГО ЭТОТ ГЕЙТ НЕ ДОКАЗЫВАЕТ. Он читает ИСХОДНИК шаблона: отсутствие стоков
    в исходнике не есть утверждение о безопасности отрендеренного документа
    целиком и политику безопасности содержимого не заменяет.
    """
    path = _failure_banner_path()

    offenders = _failure_banner_markup_sinks(path)
    assert offenders == (), (
        f"{FAILURE_BANNER_OWNER}: появился сток разметки {offenders} — "
        "сценарий, исполняемый на КАЖДОЙ странице, начал собирать разметку "
        "строкой"
    )

    assert RESPONSE_BODY_READ not in _failure_banner_code(path), (
        f"{FAILURE_BANNER_OWNER}: сценарий начал читать ТЕЛО пришедшего "
        "ответа — плашка отказа способна вынести наружу внутреннее устройство"
    )


def test_the_failure_banner_tells_a_validation_answer_from_a_crash():
    """Ответ 422 плашку аварии НЕ поднимает: различение идёт ПО КОДУ (T-08-19).

    Правило "422" в блоке конфигурации несёт признак ошибки — значит корректно
    перерисованная форма с ошибкой заполнения поднимает то же событие отказа
    ответа, что и настоящая авария. Без раннего выхода по коду человек получал
    бы плашку аварии на КАЖДОЙ опечатке в поле, и глаз, приученный игнорировать
    красное, перестал бы видеть настоящую аварию.

    Это прямое исполнение предписания, оставленного Фазой 7 в
    includes/htmx_config.html абзацем «ОГРАНИЧЕНИЕ ДЛЯ ТОГО, КТО БУДЕТ ПИСАТЬ
    ОБЩИЙ КАНАЛ ВИДИМОСТИ ОТКАЗОВ».
    """
    assert _failure_banner_tells_validation_from_a_crash(_failure_banner_path()), (
        f"{FAILURE_BANNER_OWNER}: сравнение с кодом ответа {VALIDATION_STATUS} "
        "исчезло из сценария — плашка аварии поднимается на каждой ошибке "
        "заполнения формы"
    )


def test_the_network_banner_names_the_screen_server_divergence():
    """Плашка обрыва связи называет РАСХОЖДЕНИЕ экрана с сервером (D-16).

    ЧТО ЭТО ЗА СЛУЧАЙ И ПОЧЕМУ ОН ОСТАЛСЯ ПОСЛЕДНИМ. Веха запрещает
    оптимистичный UI, и у кнопок запрет исполняется сам собой: пока сервер не
    ответил, на экране не меняется ничего. У тумблера иначе — браузер
    переключает чекбокс МГНОВЕННО, до ответа. Случай «сервер ответил» закрыт
    решением D-16 механически: строка приезжает с сервера НАСТОЯЩИМ состоянием,
    а не ожидаемым. Незакрытым остаётся ровно один случай — «сервер не ответил
    вовсе»: ответа нет, подменять строку нечем, а чекбокс на экране уже
    переключён. Человек уходит со страницы в уверенности, что группа выключена,
    — и объявление продолжает туда уходить.

    ПОЧЕМУ ЭТО ЗАКРЫВАЕТСЯ ТЕКСТОМ, А НЕ ОБРАБОТЧИКОМ. Клиентский откат чекбокса
    отвергнут решением: он потребовал бы ТРЕТЬЕГО встроенного обработчика
    событий в шаблонах, покрасив инвентаризацию, и против рамки «минимум нового
    JS». Остаётся единственный канал, в котором расхождение можно НАЗВАТЬ
    словами, — текст плашки, которую человек в этот момент и увидит.

    ВТОРОЕ УТВЕРЖДЕНИЕ — ЧТО ДОПОЛНЕНИЕ ДОБАВЛЯЕТ СМЫСЛ, А НЕ ПОВТОРЯЕТ. Совет
    «проверьте соединение и попробуйте ещё раз» в этой плашке уже есть. Его
    второе вхождение означало бы, что дополнение свелось к удлинению фразы, а
    расхождение так и осталось неназванным.

    ЧЕГО ЭТОТ ГЕЙТ НЕ ДОКАЗЫВАЕТ. Что плашка ПОЯВИТСЯ при выключенной сети:
    суита не исполняет ни строчки JS и утверждает ДОСТАВКУ строки в документ.
    Это пункт 8 перечня ручного UAT, и заменить его гейтом нельзя.

    ЗУБЫ ЭТОГО ГЕЙТА ДОКАЗАНЫ ИСПОЛНЕНИЕМ, А НЕ ОБЪЯВЛЕНЫ: он написан ДО правки
    шаблона и краснел на отгруженном Фазой 8 тексте — основы «экран», «обнов» и
    «настоящ» в нём отсутствовали.
    """
    line = _network_banner_line(_failure_banner_path())

    assert line, (
        f"{FAILURE_BANNER_OWNER}: строки заготовки "
        f"#{FAILURE_BANNER_IDS[1]} в исходнике нет — разбор читает не тот файл "
        "или заготовка обрыва связи снята"
    )

    missing = tuple(
        stem for stem in NETWORK_BANNER_DIVERGENCE if stem not in line
    )
    assert missing == (), (
        f"{FAILURE_BANNER_OWNER}: в тексте плашки обрыва связи нет основ "
        f"{missing} — единственный канал, называющий расхождение экрана с "
        "сервером словами, перестал его называть, а чекбокс тумблера остаётся "
        "переключённым независимо от того, дошёл ли запрос"
    )

    repeats = line.count(NETWORK_BANNER_REPEATED_ADVICE)
    assert repeats == 1, (
        f"{FAILURE_BANNER_OWNER}: совет "
        f"{NETWORK_BANNER_REPEATED_ADVICE!r} встречается в плашке обрыва связи "
        f"{repeats} раз(а), ожидался ровно один — дополнение обязано добавлять "
        "смысл, а не повторять уже прочитанное"
    )


def test_failure_banner_has_single_source():
    """D-01: заготовки и обработчики живут в ШАБЛОНАХ ровно в одном файле.

    Близнец test_notice_area_has_single_source и по форме, и по основанию. Пара
    гейтов доставки выше отвечает за КАЖДЫЙ шелл, этот — за ЕДИНСТВЕННОСТЬ
    ИСТОЧНИКА: без него зелёная пара была бы совместима с двумя литеральными
    копиями сценария в двух шеллах, то есть ровно с тем вариантом, который D-01
    отверг.

    ⚠️ ПРЕЖНЯЯ ФОРМА МЕМБЕРШИПА СУЖЕНА, А НЕ СНЯТА (план 10-35, находка `CR-01`
    седьмого круга; идиома D-30/D-32 `.planning/STATE.md`). Она объявляла
    владельцем ЛЮБОЙ шаблон, где встречается строка идентификатора заготовки, —
    то есть считала ЧИТАТЕЛЯ источником. Читатель у заготовок теперь есть и
    заведён нарочно: рычаг `components/modal.html` СНИМАЕТ обе заготовки при
    открытии панели, иначе подъём выносит поверх диалога отказ, к этому диалогу
    отношения не имеющий. Посылка прежней формы верна — двух источников быть не
    должно; неверен был её ПРИЗНАК источника. Поэтому предмет утверждается
    ПРЯМО и ДВАЖДЫ, а не по упоминанию имени: (1) РАЗМЕТКА — объявление
    `id="…"`; (2) СЦЕНАРИЙ — файл, который И называет заготовку литералом, И
    регистрирует обработчик. Литеральная копия сценария в другом шелле несёт
    обе половины и краснит гейт ровно как прежде; рычаг не несёт ни одной.
    """
    templates_dir = PROJECT_ROOT / "app" / "templates"

    sources = {
        path.relative_to(templates_dir).as_posix(): _without_comments(
            path.read_text(encoding="utf-8")
        )
        for path in sorted(templates_dir.rglob("*.html"))
    }
    assert sources, (
        "шаблонов в дереве не найдено ВОВСЕ — три утверждения ниже прошли бы по "
        "пустому перечню и объявили зелёным отсутствие проверки"
    )

    owners = {
        rel for rel, text in sources.items()
        if f'id="{FAILURE_BANNER_IDS[0]}"' in text
    }
    assert owners == {FAILURE_BANNER_OWNER}, (
        "РАЗМЕТКА заготовок плашек перестала быть единственной в шаблонах:\n"
        f"  найдено:  {sorted(owners)}\n"
        f"  ожидался: [{FAILURE_BANNER_OWNER}]"
    )

    wired = {
        rel for rel, text in sources.items()
        if "addEventListener" in text
        and any(f"'{banner_id}'" in text for banner_id in FAILURE_BANNER_IDS)
    }
    assert wired == {FAILURE_BANNER_OWNER}, (
        "СЦЕНАРИЙ заготовок плашек перестал быть единственным в шаблонах — "
        "файл называет заготовку литералом И регистрирует обработчик:\n"
        f"  найдено:  {sorted(wired)}\n"
        f"  ожидался: [{FAILURE_BANNER_OWNER}]"
    )

    found = {}
    for rel, text in sources.items():
        count = len(_FAILURE_BANNER_INCLUDE_RE.findall(text))
        if count:
            found[rel] = count

    expected = {shell: 1 for shell in FAILURE_BANNER_SHELLS}
    assert found == expected, (
        "включение заготовок подключено не по одному разу в каждый из двух "
        "шеллов:\n"
        f"  найдено:   {found}\n"
        f"  ожидалось: {expected}"
    )


def test_the_session_cookie_flag_stays_the_recorded_lax_decision():
    """Признак межсайтовой отправки cookie сессии равен `lax` — ПО ЗАПИСИ.

    Читается ЕДИНСТВЕННОЕ объявление набора атрибутов, а не заголовок ответа:
    предмет здесь — записанное решение, а не наблюдение за одним маршрутом.
    Наблюдение уже есть и живёт в test_cookie_flags.py; это утверждение
    закрепляет само решение и краснеет в момент его правки, а не в момент, когда
    правка доедет до какого-нибудь ответа.

    Место — в шелл-гейте, потому что признак есть свойство ВСЕГО продукта, а не
    одного экрана входа: он решает, уедет ли cookie с запросом, пришедшим по
    чужой ссылке.
    """
    from types import SimpleNamespace

    from app.pages.auth import _session_cookie_attrs

    attrs = _session_cookie_attrs(SimpleNamespace(cookie_secure=False))

    assert attrs["samesite"] == "lax", (
        "признак межсайтовой отправки cookie сессии изменён: "
        f"{attrs['samesite']!r} вместо 'lax'"
    )


# --- G-23, группа контроля: у гейтов выше есть зубы --------------------------
#
# ⚠️ ПОЧЕМУ ЭТА ГРУППА ОБЯЗАТЕЛЬНА, А НЕ ФОРМАЛЬНОСТЬ. G-23 — единственный гейт
# фазы, чьи утверждения суть «строка присутствует в файле». Зелёными по
# построению, как инвентарные, они быть не могут, но у них есть собственный
# способ соврать: разбор, читающий не тот файл или вырезающий комментарии
# слишком жадно, зеленеет на чём угодно. Проверка, не показавшая красного ни
# разу, охраняет ноль.
#
# ЧТО ГРУППА ДОКАЗЫВАЕТ: гейты выше УМЕЮТ КРАСНЕТЬ — на снятом обработчике, на
# снятом сравнении с кодом ответа и на добавленном стоке разметки, — и при этом
# на НАСТОЯЩЕМ файле молчат. «Ловит подмену» и «ловит ТОЛЬКО подмену» — разные
# утверждения, и доказательство зубов состоит из обоих.
#
# ЧЕГО ГРУППА НЕ ДОКАЗЫВАЕТ: что сценарий делает в браузере то, что написано.
# Суита не исполняет ни строчки JS. Это пункт 8 перечня ручного UAT, и заменить
# его контролем нельзя.


def test_control_negative_a_removed_send_error_handler_reddens_the_gate(tmp_path):
    """ЧТО ДОКАЗЫВАЕТ: гейт ловит СНЯТЫЙ второй обработчик.

    ⚠️ УПОМИНАНИЕ СОБЫТИЯ В КОММЕНТАРИИ НАМЕРЕННО ОСТАЁТСЯ. Именно так и
    выглядит настоящая потеря: объяснение, говорящее об обоих обработчиках,
    переживает удаление одного из них, файл продолжает УПОМИНАТЬ событие, и
    поиск по тексту нашёл бы его. Контроль доказывает, что гейт смотрит на
    СЦЕНАРИЙ, а не на наличие имени в файле.
    """
    original = _failure_banner_source(_failure_banner_path())
    victim = FAILURE_BANNER_EVENTS[1]

    stripped = "\n".join(
        line
        for line in original.splitlines()
        if not (victim in line and "addEventListener" in line)
    )
    assert stripped != original, (
        "подмена ничего не удалила — контроль проверял бы неизменённый исходник"
    )

    missing = _failure_banner_missing_events(_scratch_banner(tmp_path, stripped))

    assert victim in missing, (
        "ГЕЙТ НЕ ЗАМЕТИЛ СНЯТЫЙ ОБРАБОТЧИК — он зелёный по построению, и "
        "настоящая потеря видимости обрыва связи пройдёт мимо него"
    )


def test_control_negative_a_removed_validation_check_reddens_the_gate(tmp_path):
    """ЧТО ДОКАЗЫВАЕТ: гейт ловит СНЯТОЕ сравнение с кодом ответа валидации.

    Здесь вырезание комментариев несущее: объяснение, называющее код, остаётся
    в файле после того, как сама ветка снята, и гейт, читающий исходник
    целиком, согласился бы с потерей.
    """
    original = _failure_banner_source(_failure_banner_path())

    stripped = "\n".join(
        line
        for line in original.splitlines()
        if not (VALIDATION_STATUS in line and "status" in line)
    )
    assert stripped != original, (
        "подмена ничего не удалила — контроль проверял бы неизменённый исходник"
    )
    assert VALIDATION_STATUS in stripped, (
        "из подменённого исходника исчезло и УПОМИНАНИЕ кода: контроль "
        "перестал доказывать, что гейт смотрит на сценарий, а не на текст"
    )

    assert not _failure_banner_tells_validation_from_a_crash(
        _scratch_banner(tmp_path, stripped)
    ), (
        "ГЕЙТ НЕ ЗАМЕТИЛ СНЯТОЕ РАЗЛИЧЕНИЕ — плашка аварии на каждой ошибке "
        "заполнения формы прошла бы мимо него"
    )


def test_control_negative_an_added_markup_sink_reddens_the_gate(tmp_path):
    """ЧТО ДОКАЗЫВАЕТ: гейт стоков ловит сток, добавленный в сценарий."""
    original = _failure_banner_source(_failure_banner_path())
    sink = MARKUP_SINKS[0]
    assert sink not in original, (
        "сток уже есть в настоящем файле — контроль ничего не доказал бы"
    )

    poisoned = original.replace(
        "</script>",
        f"  document.getElementById('htmx-failure-server').{sink} = '<b>!</b>';\n"
        "</script>",
    )
    assert poisoned != original, "подмена не сработала — якорь замены не найден"

    offenders = _failure_banner_markup_sinks(_scratch_banner(tmp_path, poisoned))

    assert sink in offenders, (
        "ГЕЙТ СТОКОВ НЕ ЗАМЕТИЛ ДОБАВЛЕННЫЙ СТОК — сборка разметки строкой "
        "вернулась бы в <body> каждой страницы незамеченной"
    )


def test_control_positive_the_untouched_banner_keeps_the_gates_green():
    """ЧТО ДОКАЗЫВАЕТ: на НЕИЗМЕНЁННОМ файле все три гейта молчат.

    ⚠️ БЕЗ ЭТОГО КОНТРОЛЯ ВСЕ ТРИ ОТРИЦАТЕЛЬНЫХ ПРОШЛИ БЫ И У ГЕЙТА, КОТОРЫЙ
    КРАСНЕЕТ ВСЕГДА. Гейт, роняющий сборку на любом дереве, не строже, а просто
    сломан, и его сняли бы первым же коммитом.
    """
    path = _failure_banner_path()

    assert _failure_banner_missing_events(path) == (), (
        "гейт обработчиков краснеет на неизменённом файле — отрицательные "
        "контроли выше ничего не доказывают"
    )
    assert _failure_banner_markup_sinks(path) == (), (
        "гейт стоков краснеет на неизменённом файле — отрицательные контроли "
        "выше ничего не доказывают"
    )
    assert _failure_banner_tells_validation_from_a_crash(path), (
        "гейт различения краснеет на неизменённом файле — отрицательные "
        "контроли выше ничего не доказывают"
    )


# --- Слой плашки отказа при открытой панели (Р-3, обход 2026-09-09) ----------
#
# ⚠️ ЧТО ИЗМЕРЕНО ОБХОДОМ, И ЧИСЛА ЗДЕСЬ ИЗ ЗАМЕРА, А НЕ ИЗ ПАМЯТИ О НЁМ. Шаг
# 4.4 обхода 2026-09-09 (ad_id=51, sched-143, режим Offline) записал шестью
# величинами: текст плашки обрыва связи в документе ЕСТЬ и верен, но сама
# плашка лежит в обычном потоке (`position: static`, `z-index: auto`) на 322 px
# ВЫШЕ окна (`top: -322`, `bottom: -259` при `scrollY: 418`), под панелью
# (`position: fixed`, `z-index: 60`, `top: 0`, высота 1267 — во всё окно);
# верхним узлом в точке плашки стои́т `DIV.modal__overlay` внутри диалога
# `sched-del-143`, а прокрутка корня снята `overflow: hidden` — доскроллить
# до плашки НЕЛЬЗЯ. Следствие для человека названо без смягчения: он нажал
# «Удалить» без связи, панель СОЗНАТЕЛЬНО осталась открытой (D-12), кнопка
# снова нажимаема — и ни одного объяснения, почему ничего не произошло, ему не
# показано. Единственное объяснение существует в документе и недостижимо ни
# глазом, ни прокруткой.
#
# ⚠️ ЧЕГО ЭТА ГРУППА НЕ ДОКАЗЫВАЕТ, И ГРАНИЦА НАЗВАНА ЗДЕСЬ, А НЕ ОСТАВЛЕНА
# СЛЕДУЮЩЕМУ ЧИТАТЕЛЮ. Правила ниже утверждают ОБЪЯВЛЕНИЕ слоя в таблице стилей
# и ПОРЯДОК объявленных слоёв. Они НЕ утверждают, что браузер НАРИСОВАЛ плашку
# поверх панели: суита не исполняет ни строчки CSS, рантайма наложения у неё
# нет, и контекст наложения заводят правила на предках, а не эта таблица.
# Отрисовка остаётся шагу 4.4 ручного обхода `10-UAT.md`, и объявлять его
# пройденным по зелени этих правил — ошибка, названная заранее.
#
# ⚠️ РАЗБОР ТАБЛИЦЫ ИДЁТ ПО ПАРАМ «СПИСОК СЕЛЕКТОРОВ + БЛОК ОБЪЯВЛЕНИЙ», И
# ВЛОЖЕННЫЕ ПРАВИЛА МЕДИАЗАПРОСОВ РАЗБИРАЮТСЯ КАК ОБЫЧНЫЕ БЛОКИ СО СВОИМИ
# СЕЛЕКТОРАМИ. Свойство названо прямо: `@media`, `@supports` и прочие
# группирующие правила не становятся отдельной сущностью разбора — их тело
# раскрывается, и правила внутри встают в общий перечень наравне с внешними.
# Следствие принято сознательно: правило, объявленное только внутри
# медиазапроса, для разбора неотличимо от объявленного снаружи, и утверждения
# ниже говорят «в таблице объявлено», а не «объявлено безусловно».

APP_CSS_RELATIVE = ("app", "static", "css", "app.css")

# Исходник рычага панели. Нужен ровно затем, чтобы сличить с ним имя признака
# блокировки прокрутки: подъём ключáется на ТОТ ЖЕ признак, который поднимает
# сама панель, и панель, перестав его поднимать, роняет правило — а не тихо
# забирает у плашки подъём.
MODAL_LEVER_RELATIVE = ("app", "templates", "components", "modal.html")

# Селектор блока, объявляющего слой панели подтверждения. ⚠️ ЧИСЛО СЛОЯ ЗДЕСЬ НЕ
# ВЫПИСАНО И НЕ БУДЕТ — ни это, ни число слоя подъёма. Правило СЛИЧАЕТ два слоя,
# прочитанных из таблицы, и не знает наперёд ни одного из них: выписанное число
# разошлось бы с таблицей молча при первой же правке любого из двух слоёв.
MODAL_PANEL_SELECTOR = ".modal"

# Признак блокировки прокрутки, на который ключáется подъём. ЗАМЕРЕН ПО РЫЧАГУ
# (`components/modal.html`, `show()` поднимает его на корневом узле, `hide()` и
# `destroy()` снимают), а не взят из памяти, и правило сличает его с исходником
# рычага отдельным утверждением.
MODAL_SCROLL_LOCK_FLAG = "is-modal-open"

_CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def _app_css_path() -> Path:
    """Путь боевой таблицы стилей — единственное место, где он собирается."""
    return PROJECT_ROOT.joinpath(*APP_CSS_RELATIVE)


def _modal_lever_path() -> Path:
    """Путь исходника рычага панели."""
    return PROJECT_ROOT.joinpath(*MODAL_LEVER_RELATIVE)


def _stylesheet_source(path: Path) -> str:
    """Исходник таблицы стилей ПО НАЗВАННОМУ ПУТИ, а не по константе модуля.

    Параметр здесь и есть то, что делает группу контроля возможной: утверждения
    ниже суть «в таблице объявлено то-то», и у таких утверждений есть свой
    способ соврать — разбор, читающий не тот файл или раскрывающий блоки
    неверно, зеленеет на чём угодно. Функция, принимающая путь, позволяет подать
    правилу доктóренную копию во временном каталоге и потребовать красноты.
    Форма наследуется у `_failure_banner_source` выше, а не изобретается.
    """
    return path.read_text(encoding="utf-8")


def _scratch_stylesheet(tmp_path, text: str) -> Path:
    """Доктóренная копия таблицы стилей во временном каталоге.

    Подмена идёт по-настоящему через файловую систему, а не строкой в памяти:
    так контроль проверяет ТОТ ЖЕ путь чтения, которым правило ходит по боевому
    дереву. Форма скопирована у `_scratch_banner`.
    """
    scratch = tmp_path / APP_CSS_RELATIVE[-1]
    scratch.write_text(text, encoding="utf-8")
    return scratch


def _css_rules(source: str) -> tuple[tuple[str, str, str], ...]:
    """Тройки «селекторы, тело объявлений, исходный кусок» из таблицы стилей.

    Комментарии вырезаются до разбора: блок, «объявленный» в комментарии,
    зеленил бы правило после того, как настоящий блок был бы снят, — ровно тот
    урок, что оставлен помощником `_without_comments` этажом выше.

    Группирующие правила (`@media`, `@supports`) раскрываются рекурсивно: их
    тело разбирается тем же проходом, и правила внутри встают в общий перечень.
    Свойство названо и в шапке группы: следствие принято сознательно.

    Третий элемент тройки — ИСХОДНЫЙ кусок текста, дословно. Он нужен
    отрицательным контролям: доктóрить блок подстановкой по нормализованному
    селектору было бы подгонкой, а по дословному куску подмена либо срабатывает,
    либо контроль краснеет на самой подмене.
    """
    text = _CSS_COMMENT_RE.sub("", source)
    found: list[tuple[str, str, str]] = []

    def walk(chunk: str) -> None:
        depth = 0
        prelude_start = 0
        body_start = 0
        rule_start = 0
        prelude = ""
        for index, symbol in enumerate(chunk):
            if symbol == "{":
                if depth == 0:
                    rule_start = prelude_start
                    prelude = " ".join(chunk[prelude_start:index].split())
                    body_start = index + 1
                depth += 1
            elif symbol == "}":
                depth -= 1
                if depth == 0:
                    body = chunk[body_start:index]
                    if prelude.startswith("@"):
                        walk(body)
                    else:
                        found.append((prelude, body, chunk[rule_start:index + 1].strip()))
                    prelude_start = index + 1

    walk(text)
    return tuple(found)


def _css_rules_of(path: Path) -> tuple[tuple[str, str, str], ...]:
    """Правила таблицы стилей по названному пути."""
    return _css_rules(_stylesheet_source(path))


def _css_declarations(body: str) -> tuple[tuple[str, str], ...]:
    """Пары «свойство, значение» блока объявлений, приведённые к нижнему регистру.

    `!important` снимается со значения: предмет утверждений — объявленная
    величина, а не её вес в каскаде.
    """
    pairs: list[tuple[str, str]] = []
    for chunk in body.split(";"):
        if ":" not in chunk:
            continue
        name, value = chunk.split(":", 1)
        pairs.append((
            name.strip().lower(),
            value.replace("!important", "").strip().lower(),
        ))
    return tuple(pairs)


def _css_value(body: str, prop: str) -> str | None:
    """Последнее объявленное значение свойства в блоке, или None."""
    seen = None
    for name, value in _css_declarations(body):
        if name == prop:
            seen = value
    return seen


def _css_layer(body: str) -> int | None:
    """Числовой слой блока. None — слой не объявлен или объявлен не числом."""
    raw = _css_value(body, "z-index")
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _css_is_out_of_flow(body: str) -> bool:
    """Объявляет ли блок положение ВНЕ ПОТОКА по отношению к окну."""
    return _css_value(body, "position") == "fixed"


def _banner_elevation_rules(path: Path) -> tuple[tuple[str, str, str], ...]:
    """Блоки подъёма: селектор несёт И признак блокировки, И идентификатор заготовки."""
    return tuple(
        rule for rule in _css_rules_of(path)
        if MODAL_SCROLL_LOCK_FLAG in rule[0]
        and any(f"#{banner_id}" in rule[0] for banner_id in FAILURE_BANNER_IDS)
    )


def _banner_elevation_findings(path: Path) -> tuple[str, ...]:
    """Расхождения порядка слоёв. Пусто — плашка объявлена выше панели.

    ⚠️ ПОЧЕМУ НАХОДКИ СЧИТАЮТСЯ ПО-РАЗНОМУ ДЛЯ ДВУХ РОДОВ РАСХОЖДЕНИЙ. Отсутствие
    блока — расхождение НА КАЖДУЮ ЗАГОТОВКУ: заготовок две, и оставшаяся без
    подъёма остаётся недостижимой независимо от соседки. Низкий слой —
    расхождение НА БЛОК: блок один на обе, и два одинаковых сообщения о нём
    сказали бы одно и то же дважды. Оба числа слоёв называются в сообщении.
    """
    findings: list[str] = []
    rules = _css_rules_of(path)

    panel = [rule for rule in rules if rule[0] == MODAL_PANEL_SELECTOR]
    if len(panel) != 1:
        return (
            f"блоков селектора панели `{MODAL_PANEL_SELECTOR}` в таблице "
            f"{len(panel)}, а не один — сличать слой подъёма не с чем",
        )
    panel_layer = _css_layer(panel[0][1])
    if panel_layer is None:
        return (
            f"блок `{MODAL_PANEL_SELECTOR}` не объявляет числового слоя — "
            "сличать слой подъёма не с чем",
        )

    blocks: dict[str, tuple[str, list[str]]] = {}
    for banner_id in FAILURE_BANNER_IDS:
        hits = [rule for rule in rules
                if MODAL_SCROLL_LOCK_FLAG in rule[0] and f"#{banner_id}" in rule[0]]
        if len(hits) != 1:
            findings.append(
                f"#{banner_id}: блоков подъёма с признаком "
                f"`{MODAL_SCROLL_LOCK_FLAG}` в таблице {len(hits)}, а не один — "
                "заготовка остаётся в потоке под панелью, и человеку не показано "
                "ни одного объяснения отказа (Р-3, шаг 4.4)"
            )
            continue
        selector, body, _raw = hits[0]
        blocks.setdefault(selector, (body, []))[1].append(banner_id)

    for selector, (body, banner_ids) in blocks.items():
        if not _css_is_out_of_flow(body):
            findings.append(
                f"`{selector}`: блок подъёма не объявляет положения вне потока "
                f"(заготовки {', '.join(banner_ids)}) — плашка остаётся в потоке "
                "документа и уезжает выше окна вместе с ним"
            )
        layer = _css_layer(body)
        if layer is None:
            findings.append(
                f"`{selector}`: блок подъёма не объявляет числового слоя "
                f"(заготовки {', '.join(banner_ids)}) — сравнивать с панелью "
                "нечего, и плашка остаётся под ней"
            )
        elif layer <= panel_layer:
            findings.append(
                f"`{selector}`: слой подъёма {layer}, слой панели "
                f"{panel_layer} — плашка объявлена НЕ ВЫШЕ панели (заготовки "
                f"{', '.join(banner_ids)}); человек, нажавший кнопку без связи, "
                "снова не увидит объяснения отказа"
            )

    return tuple(findings)


def test_the_failure_banner_is_declared_above_the_panel_while_it_is_open():
    """Обе заготовки объявлены вне потока и слоем выше панели при её открытии.

    ⚠️ АНТИВАКУУМНАЯ ПОЛОВИНА ИДЁТ ПЕРВОЙ. Без неё правило зеленело бы на
    таблице, где слоёв нет ВОВСЕ: «подъём выше панели» неотличимо от «панели с
    её слоем в таблице нет». Поэтому сперва утверждается, что блок селектора
    панели существует ровно один, объявляет положение вне потока и ЧИСЛОВОЙ
    слой, — и только потом с этим слоем что-либо сличается.

    ⚠️ ВТОРАЯ ПОЛОВИНА АНТИВАКУУМА — КЛЮЧ ПОДЪЁМА. Имя признака блокировки
    прокрутки сличается с исходником рычага панели: подъём ключáется на ТОТ ЖЕ
    признак, который поднимает сама панель. Панель, перестав его поднимать,
    роняет ЭТО правило — а не тихо забирает у плашки подъём.

    ⚠️ НИ ОДНО ЧИСЛО СЛОЯ В ПРАВИЛЕ НЕ ВЫПИСАНО. Оба читаются из таблицы и
    сличаются между собой, поэтому правка любого из двух слоёв не может
    разойтись с правилом молча.
    """
    path = _app_css_path()
    rules = _css_rules_of(path)

    panel = [rule for rule in rules if rule[0] == MODAL_PANEL_SELECTOR]
    assert len(panel) == 1, (
        f"app.css: блоков селектора `{MODAL_PANEL_SELECTOR}` в таблице "
        f"{len(panel)}, а не один — правило о порядке слоёв сличало бы слой "
        "подъёма неизвестно с чем"
    )
    panel_body = panel[0][1]
    assert _css_is_out_of_flow(panel_body), (
        f"app.css: блок `{MODAL_PANEL_SELECTOR}` перестал объявлять положение "
        "вне потока — предмет сравнения исчез, и утверждение «плашка выше "
        "панели» стало бы утверждением ни о чём"
    )
    panel_layer = _css_layer(panel_body)
    assert panel_layer is not None, (
        f"app.css: блок `{MODAL_PANEL_SELECTOR}` не объявляет ЧИСЛОВОГО слоя — "
        "сличать слой подъёма не с чем, и правило зеленело бы вакуумом"
    )

    lever = _stylesheet_source(_modal_lever_path())
    assert MODAL_SCROLL_LOCK_FLAG in lever, (
        f"components/modal.html: рычаг перестал поднимать признак "
        f"`{MODAL_SCROLL_LOCK_FLAG}` — подъём плашки ключáется на признак, "
        "которого больше никто не ставит, и заготовки молча вернулись под "
        "панель (Р-3, шаг 4.4)"
    )

    findings = _banner_elevation_findings(path)
    assert findings == (), (
        "app.css: плашка отказа объявлена НЕ выше панели подтверждения:\n"
        + "\n".join(f"  — {line}" for line in findings)
    )


def test_control_a_banner_layer_below_the_panel_reddens(tmp_path):
    """ЧТО ДОКАЗЫВАЕТ: правило видит слой подъёма, опущенный до панели и ниже.

    ⚠️ ДОКТÓРИВАНИЙ ДВА, И ВТОРОЕ НЕ ИЗБЫТОЧНО. Первое опускает слой подъёма
    РОВНО ДО слоя панели: это граница между `<` и `<=`, и без неё правило,
    сличающее слои нестрого, зеленело бы на равенстве — а при равных слоях
    порядок отрисовки решает порядок в документе, то есть «выше» перестаёт быть
    утверждением. Второе опускает слой СТРОГО НИЖЕ: только на нём числа
    различны, и требование «отказ называет ОБА» имеет зубы.

    ⚠️ ЧИСЛА В КОНТРОЛЕ НЕ ВЫПИСАНЫ НИ ОДНО. Оба слоя читаются из настоящей
    таблицы, а подстановка выводится из прочитанного арифметикой. Выписанное
    здесь число разошлось бы с таблицей ровно так же, как выписанное в самом
    правиле.
    """
    path = _app_css_path()

    elevation = _banner_elevation_rules(path)
    assert len(elevation) == 1, (
        f"блоков подъёма в настоящей таблице {len(elevation)}, а не один — "
        "доктóрить нечего, и контроль ничего не доказал бы"
    )
    selector, body, raw = elevation[0]

    panel = [rule for rule in _css_rules_of(path) if rule[0] == MODAL_PANEL_SELECTOR]
    assert len(panel) == 1, "блока панели в настоящей таблице нет — доктóрить нечего"
    panel_layer = _css_layer(panel[0][1])
    layer = _css_layer(body)
    assert panel_layer is not None and layer is not None, (
        "один из двух слоёв в настоящей таблице не число — подстановка была бы "
        "молчаливой"
    )
    assert layer > panel_layer, (
        "в настоящей таблице слой подъёма НЕ выше слоя панели — опускать нечего, "
        "и контроль доказывал бы отсутствие того, чего и так нет"
    )

    original = _stylesheet_source(path)
    assert original.count(raw) == 1, (
        "блок подъёма встречается в исходнике не один раз — подстановка задела "
        "бы не тот блок"
    )

    for dropped in (panel_layer, panel_layer - 1):
        poisoned = original.replace(raw, raw.replace(
            f"z-index: {layer}", f"z-index: {dropped}"
        ))
        assert poisoned != original, (
            f"подмена слоя на {dropped} не сработала — якорь замены не найден"
        )

        findings = _banner_elevation_findings(_scratch_stylesheet(tmp_path, poisoned))

        assert len(findings) == 1, (
            f"ПРАВИЛО НЕ ЗАМЕТИЛО СЛОЙ ПОДЪЁМА {dropped} ПРИ СЛОЕ ПАНЕЛИ "
            f"{panel_layer} или назвало расхождение дважды: находок "
            f"{len(findings)} — {findings}"
        )
        assert selector in findings[0], (
            f"отказ не назвал селектор блока подъёма: {findings[0]}"
        )
        assert str(dropped) in findings[0] and str(panel_layer) in findings[0], (
            "отказ не назвал ОБА числа — читатель отказа не узнает, какой слой "
            f"править: {findings[0]}"
        )


def test_control_a_banner_without_an_elevation_rule_reddens(tmp_path):
    """ЧТО ДОКАЗЫВАЕТ: правило краснеет на КАЖДУЮ заготовку, лишённую подъёма.

    Снятый целиком блок подъёма возвращает обе заготовки ровно в то состояние,
    которое обход измерил на шаге 4.4, — и правило обязано назвать обе, а не
    одну: заготовка, оставшаяся без подъёма, недостижима независимо от соседки.
    """
    path = _app_css_path()

    elevation = _banner_elevation_rules(path)
    assert len(elevation) == 1, (
        f"блоков подъёма в настоящей таблице {len(elevation)}, а не один — "
        "снимать нечего, и контроль ничего не доказал бы"
    )
    raw = elevation[0][2]

    original = _stylesheet_source(path)
    assert original.count(raw) == 1, (
        "блок подъёма встречается в исходнике не один раз — снятие задело бы "
        "не тот блок"
    )
    poisoned = original.replace(raw, "")
    assert poisoned != original, "снятие не сработало — якорь замены не найден"

    findings = _banner_elevation_findings(_scratch_stylesheet(tmp_path, poisoned))

    assert len(findings) == len(FAILURE_BANNER_IDS), (
        "ПРАВИЛО НЕ ЗАМЕТИЛО СНЯТЫЙ БЛОК ПОДЪЁМА или назвало не все заготовки: "
        f"находок {len(findings)} при {len(FAILURE_BANNER_IDS)} заготовках — "
        f"{findings}"
    )
    joined = "\n".join(findings)
    for banner_id in FAILURE_BANNER_IDS:
        assert banner_id in joined, (
            f"отказ не назвал заготовку #{banner_id} — читатель отказа не "
            f"узнает, какая из двух осталась под панелью: {joined}"
        )


# --- Снятие заготовок плашки при ОТКРЫТИИ панели (CR-01 седьмого круга) ------
#
# ⚠️ ЗАЧЕМ ЭТА ГРУППА СУЩЕСТВУЕТ ОТДЕЛЬНО ОТ ПРАВИЛА ПОРЯДКА СЛОЁВ. Подъём,
# объявленный блоком выше, выносит поверх панели ЛЮБУЮ уже снятую заготовку —
# включая снятую отказом, случившимся задолго до этой панели и к ней отношения
# не имеющим. Сценарий включения снятую плашку обратно НЕ ПРЯЧЕТ (записанное
# допущение Фазы 8), поэтому последовательность «сентинель бесконечной прокрутки
# поймал обрыв связи БЕЗ единого действия человека → связь вернулась → человек
# открыл любую из 18 панелей подтверждения» ставит над кнопкой «Удалить» текст
# «Запрос не дошёл до сервера…» — ложное утверждение о ТЕКУЩЕМ действии в момент
# наивысшей цены ошибки. Правило порядка слоёв на это ЗЕЛЕНО: слой объявлен
# верно, неверен ПОВОД. Стережёт свойство только правило этой группы.

# Имя метода рычага, ОТКРЫВАЮЩЕГО панель. Замерено по рычагу
# (`components/modal.html`: атрибут `x-on:modal-open-…window` зовёт именно его),
# а не взято из памяти. Предмет правила — ИМЕННО этот метод: то же снятие,
# переехавшее в метод закрытия, даёт поведение, ОБРАТНОЕ требуемому, и правило,
# считающее файл целиком, зеленело бы на нём.
MODAL_OPEN_METHOD = "show"

# Имя метода рычага, ЗАКРЫВАЮЩЕГО панель. Нужен ровно отрицательному контролю
# границы предмета и больше нигде не читается.
MODAL_CLOSE_METHOD = "hide"

# Признак скрытости заготовки. Выписан ОДИН раз, и выражение глагола собирается
# вокруг него: правка признака разойдётся с правилом громко, а не молча.
FAILURE_BANNER_HIDDEN_ATTR = "hidden"

# Комментарий блока JS. Синтаксис совпадает с CSS-комментарием этажом выше, но
# языки разные, и одна константа на два языка связала бы два несвязанных разбора.
_JS_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)

_MODAL_OPEN_METHOD_RE = re.compile(
    r"(?<![\w$])" + re.escape(MODAL_OPEN_METHOD) + r"\s*\(\s*\)\s*\{"
)


def _lever_show_body(source: str) -> str:
    """Тело метода, ОТКРЫВАЮЩЕГО панель, из де-комментированного исходника рычага.

    ⚠️ ПОЧЕМУ ТЕЛО, А НЕ ФАЙЛ ЦЕЛИКОМ. Предмет правила — снятие заготовок ПРИ
    ОТКРЫТИИ. Идентификатор, встреченный в теле закрытия или сноса, даёт
    поведение, обратное предмету, и правило, считающее файл целиком, зеленело бы
    на нём. Скобки считаются с вложенностью, а не берётся первая закрывающая:
    тела соседних методов лежат в том же объекте `x-data`.

    ⚠️ ПОЧЕМУ ДЕ-КОММЕНТИРОВАННЫЙ (WR-08 седьмого круга, тот же урок, что у
    `_without_comments` на :1377 — `07-REVIEW.md IN-02`). Перед макросом рычага
    лежит 693 строки прозы. Утверждение по подстроке зеленело бы от УПОМИНАНИЯ
    идентификатора в комментарии, то есть учило бы правку удалять прозу. Блочный
    комментарий JS вырезается тем же проходом: он живёт ВНУТРИ значения атрибута
    `x-data` и `_without_comments` его не видит.

    ⚠️ ДВА СОБЫТИЯ ОТКАЗА НАЗЫВАЮТСЯ ОТДЕЛЬНО. «Объявление метода не найдено» и
    «тело метода не замкнуто» — разные поломки с разной починкой, и слитый отказ
    заставил бы читателя разбирать, какая из двух случилась.
    """
    text = _JS_BLOCK_COMMENT_RE.sub("", _without_comments(source))

    anchor = _MODAL_OPEN_METHOD_RE.search(text)
    if anchor is None:
        raise ValueError(
            f"components/modal.html: объявления метода `{MODAL_OPEN_METHOD}()` в "
            "де-комментированном исходнике рычага НЕТ — либо метод переименован, "
            "либо разбор читает не тот файл; в обоих случаях правило снятия "
            "заготовок зеленело бы вакуумом"
        )

    start = anchor.end() - 1
    depth = 0
    for pos in range(start, len(text)):
        char = text[pos]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:pos]

    raise ValueError(
        f"components/modal.html: тело метода `{MODAL_OPEN_METHOD}()` НЕ ЗАМКНУТО "
        "— счёт вложенности дошёл до конца исходника с ненулевой глубиной; "
        "разбор вернул бы кусок, границы которого никто не знает"
    )


def _lever_clearing_findings(path: Path) -> tuple[str, ...]:
    """Расхождения снятия заготовок при ОТКРЫТИИ панели. Пусто — снимаются обе.

    ⚠️ ПУТЬ ПРИХОДИТ ПАРАМЕТРОМ, А НЕ ЧИТАЕТСЯ КОНСТАНТОЙ МОДУЛЯ, — по той же
    причине, по какой параметр принимает `_stylesheet_source` (:2813): без него
    контроль зубов невыразим, и «правило видит возврат дефекта» пришлось бы
    ЗАЯВЛЯТЬ вместо того, чтобы ПОКАЗЫВАТЬ.

    ⚠️ РАСХОЖДЕНИЕ СЧИТАЕТСЯ НА ЗАГОТОВКУ, А НЕ НА ФАЙЛ. Заготовок две, и
    оставшаяся неснятой встаёт над панелью независимо от соседки — та же
    арифметика находок, что у `_banner_elevation_findings` (:2941), и там она
    объяснена.

    ⚠️ ПЕРЕЧЕНЬ ЧИТАЕТСЯ ИЗ `FAILURE_BANNER_IDS`, А НЕ ВЫПИСЫВАЕТСЯ ДВУМЯ
    ИМЕНАМИ: третья заготовка, добавленная в перечень и не добавленная в рычаг,
    обязана уронить правило, а не пройти мимо него.
    """
    try:
        body = _lever_show_body(_stylesheet_source(path))
    except ValueError as parse_failure:
        return (str(parse_failure),)

    verb = f"setAttribute('{FAILURE_BANNER_HIDDEN_ATTR}'"

    findings: list[str] = []
    for banner_id in FAILURE_BANNER_IDS:
        if banner_id not in body:
            findings.append(
                f"#{banner_id}: тело метода `{MODAL_OPEN_METHOD}()` рычага этой "
                "заготовки не называет — отказ, случившийся ДО открытия панели, "
                "поднимается над кнопкой необратимого удаления и утверждает о "
                "ТЕКУЩЕМ действии неправду (CR-01: сентинель прокрутки поймал "
                "обрыв без действия человека → связь вернулась → человек открыл "
                "панель подтверждения)"
            )
            continue
        if verb not in body:
            findings.append(
                f"#{banner_id}: тело метода `{MODAL_OPEN_METHOD}()` рычага "
                "заготовку называет, но признака скрытости ей обратно НЕ СТАВИТ "
                f"(`{verb}` в теле нет) — упоминание без глагола снятия оставляет "
                "устаревшую плашку поверх панели ровно так же, как его отсутствие"
            )

    return tuple(findings)


def test_the_lever_clears_both_failure_banners_when_the_panel_opens():
    """Рычаг снимает ОБЕ заготовки плашки отказа при открытии панели.

    ⚠️ АНТИВАКУУМНАЯ ПОЛОВИНА ИДЁТ ПЕРВОЙ. Без неё правило зеленело бы на пустом
    перечне заготовок, на нечитаемом исходнике рычага и на пустом теле метода —
    то есть «обе заготовки снимаются» было бы неотличимо от «снимать нечего».

    ⚠️ ЧТО ИМЕННО СТЕРЕЖЁТСЯ. Не факт отрисовки браузером — исходник рычага.
    Отрисовка остаётся шагу 4.4 ручного обхода `10-UAT.md`, и объявлять его
    пройденным по зелени этого правила НЕЛЬЗЯ.
    """
    assert FAILURE_BANNER_IDS, (
        "перечень заготовок плашки пуст — правило ниже прошло бы по нулю "
        "элементов и объявило зелёным отсутствие проверки"
    )

    source = _stylesheet_source(_modal_lever_path())
    assert source.strip(), (
        "исходник рычага `components/modal.html` пуст или не прочитан — разбор "
        "ниже вернул бы пустоту, и правило зеленело бы вакуумом"
    )

    body = _lever_show_body(source)
    assert body.strip(), (
        f"тело метода `{MODAL_OPEN_METHOD}()` рычага пусто — сличать снятие "
        "заготовок не с чем"
    )

    findings = _lever_clearing_findings(_modal_lever_path())
    assert findings == (), (
        "components/modal.html: открытие панели НЕ снимает заготовки плашки "
        "отказа, и подъём выносит поверх диалога отказ, к этому диалогу "
        "отношения не имеющий:\n"
        + "\n".join(f"  — {line}" for line in findings)
    )


# --- Чистота цепи предков точки включения (Р-3, вторая половина) -------------
#
# ⚠️ ЗАЧЕМ ЭТА ГРУППА СУЩЕСТВУЕТ ОТДЕЛЬНО ОТ ПРАВИЛА ПОРЯДКА СЛОЁВ. Подъём,
# объявленный `position: fixed`, есть подъём ДО ОКНА — но ровно до тех пор, пока
# ни один предок точки включения не порождает содержащий блок и не заводит
# собственного контекста наложения. Свойство, дописанное предку, отнимает у
# плашки окно и запирает её слой внутри предка: плашка позиционируется
# относительно предка, а не окна, и её `z-index: 70` перестаёт сравниваться со
# слоем панели вовсе. ГЛАЗОМ ЭТО НЕОТЛИЧИМО ОТ РАБОТАЮЩЕГО ПОДЪЁМА — правило
# порядка слоёв осталось бы зелёным, а человек снова не увидел бы объяснения.

# Вселенная предков точки включения В ОСНОВНОМ ШЕЛЛЕ.
#
# ⚠️ ЗАМЕРЕНА ПО ШЕЛЛУ, А НЕ ВЫВЕДЕНА ИЗ НЕГО РАЗБОРОМ, и это ПЕРВАЯ ГРАНИЦА
# правила, названная здесь, а не оставленная следующему читателю. Замер
# 2026-09-09 по `app/templates/base.html`: тело документа → `[data-shell]`
# (:79) → `[data-main]` (:209) → `[data-body]` (:232) → включение заготовок
# (:242). Липкая шапка `[data-head]` со слоем 5 — СОСЕД, а не предок: она
# закрывается на :230, а `[data-body]` открывается на :232. Следствие границы
# прямое: обёртка, вставленная в шелл между корнем и точкой включения, в эту
# константу САМА НЕ ПОПАДЁТ, и правило её не проверит.
#
# ⚠️ ЦЕПЬ ШЕЛЛА АВТОРИЗАЦИИ СЮДА НЕ ВХОДИТ, И ЭТО РЕШЕНИЕ С ОСНОВАНИЕМ, А НЕ
# ПРОПУСК — ВТОРАЯ ГРАНИЦА. Замер той цепи: тело документа →
# `[data-auth-shell]` (auth_base.html:33) → `.auth-card` (:34) → включение
# (:49); карточка несёт `animation: rise`, последний кадр которой трансформацию
# СНИМАЕТ (`transform: none`), но ВО ВРЕМЯ анимации содержащий блок существует.
# Правило, взявшее её в свою вселенную, краснело бы на живой анимации —
# то есть требовало бы снять анимацию карточки входа ради плашки, которой там
# негде появиться: панелей подтверждения в том шелле НЕТ НИ ОДНОЙ (замер
# 2026-09-09: из семи наследников `auth_base.html` рычаг `components/modal.html`
# зовут НОЛЬ, и ни один из семи не включает ничего, через что рычаг мог бы
# приехать транзитом).
FAILURE_BANNER_ANCESTORS = ("[data-shell]", "[data-main]", "[data-body]")

# ГРУППА 1 — СВОЙСТВА, ОТНИМАЮЩИЕ У ФИКСИРОВАННОГО ПОТОМКА ОКНО. Любое из них,
# объявленное предку, делает СОДЕРЖАЩИМ БЛОКОМ для `position: fixed` сам предок:
# плашка перестаёт позиционироваться по окну и начинает — по прямоугольнику
# предка, вместе с ним уезжая при прокрутке. Подъём формально остаётся
# объявленным, а достижимость теряется.
CONTAINING_BLOCK_PROPERTIES = (
    "transform", "perspective", "filter", "backdrop-filter", "contain",
    "will-change",
)

# ГРУППА 2 — СВОЙСТВА, ЗАВОДЯЩИЕ ПРЕДКУ СОБСТВЕННЫЙ КОНТЕКСТ НАЛОЖЕНИЯ. Слой
# потомка внутри такого контекста перестаёт сравниваться со слоем панели: он
# сравнивается только с братьями ВНУТРИ предка, а весь предок целиком встаёт в
# общий порядок своим собственным слоем. Плашка со слоем 70 внутри предка со
# слоем `auto` уезжает под панель — и число 70 в таблице при этом остаётся.
STACKING_CONTEXT_PROPERTIES = ("isolation", "mix-blend-mode", "opacity")

# Свойство слоя ЗАВОДИТ контекст наложения только вместе с положением, отличным
# от обычного потока. Оно вынесено из группы 2 отдельно ровно поэтому: правило,
# краснеющее на `z-index`, объявленный узлу в обычном потоке, краснело бы на
# объявление, ничего не делающее, — и учило бы правку не объявлять, а обходить.
LAYER_PROPERTY = "z-index"

_CSS_VENDOR_PREFIX_RE = re.compile(r"^-(?:webkit|moz|ms|o)-")
_CSS_COMBINATOR_RE = re.compile(r"[>+~]")


def _selector_targets(selector: str) -> tuple[str, ...]:
    """Предки из вселенной, на которые НАЦЕЛЕН блок (а не упомянуты в цепочке).

    Разбирается ПОСЛЕДНЯЯ простая часть каждого селектора списка: `[data-shell]`
    целится в предка, а `[data-shell] [data-nav]` — в потомка внутри него, и
    свойство, объявленное потомку, к цепи предков отношения не имеет. Без этого
    различения правило краснело бы на половине таблицы и научило бы читателя
    себя ослаблять.
    """
    hits: list[str] = []
    for part in selector.split(","):
        compound = _CSS_COMBINATOR_RE.sub(" ", part).split()
        if not compound:
            continue
        last = compound[-1]
        for ancestor in FAILURE_BANNER_ANCESTORS:
            if ancestor in last and ancestor not in hits:
                hits.append(ancestor)
    return tuple(hits)


def _ancestor_trap_findings(path: Path) -> tuple[str, ...]:
    """Расхождения чистоты цепи предков. Пусто — ни один предок подъём не запирает."""
    findings: list[str] = []
    consequence = (
        "поднятая плашка позиционируется внутри предка, а не по окну, и глазом "
        "это неотличимо от работающего подъёма"
    )
    for selector, body, _raw in _css_rules_of(path):
        targets = _selector_targets(selector)
        if not targets:
            continue
        position = _css_value(body, "position") or "static"
        for prop, value in _css_declarations(body):
            name = _CSS_VENDOR_PREFIX_RE.sub("", prop)
            if name in CONTAINING_BLOCK_PROPERTIES:
                findings.append(
                    f"`{selector}` (предок {', '.join(targets)}): свойство "
                    f"`{prop}: {value}` делает предка СОДЕРЖАЩИМ БЛОКОМ для "
                    f"фиксированного потомка — {consequence}"
                )
            elif name in STACKING_CONTEXT_PROPERTIES:
                findings.append(
                    f"`{selector}` (предок {', '.join(targets)}): свойство "
                    f"`{prop}: {value}` заводит предку СОБСТВЕННЫЙ КОНТЕКСТ "
                    f"НАЛОЖЕНИЯ — слой плашки перестаёт сравниваться со слоем "
                    f"панели; {consequence}"
                )
            elif name == LAYER_PROPERTY and position != "static":
                findings.append(
                    f"`{selector}` (предок {', '.join(targets)}): свойство "
                    f"`{prop}: {value}` при `position: {position}` заводит "
                    f"предку СОБСТВЕННЫЙ КОНТЕКСТ НАЛОЖЕНИЯ — {consequence}"
                )
    return tuple(findings)


def test_no_ancestor_of_the_failure_banner_traps_the_fixed_layer():
    """Ни один предок точки включения не запирает поднятый слой в себе.

    ⚠️ ПОЛОЖИТЕЛЬНАЯ ПОЛОВИНА ИДЁТ ПЕРВОЙ, И АНТИВАКУУМ ПЕРЕД НЕЙ. Предмет
    правила есть ОТСУТСТВИЕ свойства, а такое утверждение зеленеет само собой на
    пустой вселенной и на таблице, где этих селекторов нет вовсе. Поэтому сперва
    утверждается, что вселенная непуста и что КАЖДЫЙ её селектор в таблице
    действительно объявлен хотя бы одним блоком, — и только потом, что ни один из
    этих блоков запрещённых свойств не несёт.

    ⚠️ ОБЕ ГРАНИЦЫ ПРАВИЛА НАЗВАНЫ У КОНСТАНТЫ `FAILURE_BANNER_ANCESTORS`:
    вселенная ЗАМЕРЕНА по шеллу, а не выведена разбором (новая обёртка в неё сама
    не попадёт), и цепь шелла авторизации в неё не входит по замеру, а не по
    забывчивости.
    """
    assert FAILURE_BANNER_ANCESTORS, (
        "вселенная предков ПУСТА — правило об отсутствии свойства на пустой "
        "вселенной зеленеет само собой и не проверяет ничего"
    )

    path = _app_css_path()
    rules = _css_rules_of(path)

    for ancestor in FAILURE_BANNER_ANCESTORS:
        targeted = [rule for rule in rules if ancestor in _selector_targets(rule[0])]
        assert targeted, (
            f"app.css: селектор предка `{ancestor}` не объявлен в таблице ни "
            "одним блоком — либо шелл переписан и вселенная разошлась с ним, "
            "либо разбор селекторов сломан; в обоих случаях правило ниже "
            "зеленело бы вакуумом"
        )

    findings = _ancestor_trap_findings(path)
    assert findings == (), (
        "app.css: предок точки включения запирает поднятый слой в себе:\n"
        + "\n".join(f"  — {line}" for line in findings)
    )


def test_control_a_transforming_ancestor_reddens(tmp_path):
    """ЧТО ДОКАЗЫВАЕТ: правило видит свойство, дописанное предку.

    ⚠️ ПОРЯДОК ЗДЕСЬ ОБРАТЕН ПРАВИЛУ ПОРЯДКА СЛОЁВ, И ЭТО НАЗВАНО ПРЯМО.
    Предмет правила выше — ОТСУТСТВИЕ свойства, и «красного до правки» у него не
    существует: чинить нечего, сегодня ни один предок ничего запрещённого не
    объявляет. Зубы ему даёт ТОЛЬКО этот контроль — без него правило неотличимо
    от разборщика, не находящего ничего никогда.

    Предка правит доктóренная копия, а не дерево: подгонять боевую таблицу под
    правило запрещено, и настоящие предки не тронуты ни на символ.
    """
    path = _app_css_path()

    targeted = [rule for rule in _css_rules_of(path) if _selector_targets(rule[0])]
    assert targeted, "блоков предков в настоящей таблице нет — доктóрить нечего"
    selector, _body, raw = targeted[0]
    prop = CONTAINING_BLOCK_PROPERTIES[0]

    original = _stylesheet_source(path)
    assert original.count(raw) == 1, (
        f"блок предка `{selector}` встречается в исходнике не один раз — "
        "подстановка задела бы не тот блок"
    )
    assert raw.rstrip().endswith("}"), (
        "разбор вернул блок без закрывающей скобки — дописывать свойство некуда"
    )
    poisoned = original.replace(
        raw, raw.rstrip()[:-1] + f" {prop}: translateZ(0); }}"
    )
    assert poisoned != original, "подмена не сработала — якорь замены не найден"

    findings = _ancestor_trap_findings(_scratch_stylesheet(tmp_path, poisoned))

    assert len(findings) == 1, (
        f"ПРАВИЛО НЕ ЗАМЕТИЛО СВОЙСТВО `{prop}`, ДОПИСАННОЕ ПРЕДКУ "
        f"`{selector}`, или назвало расхождение дважды: находок "
        f"{len(findings)} — {findings}"
    )
    assert selector in findings[0], (
        f"отказ не назвал селектор предка: {findings[0]}"
    )
    assert prop in findings[0], (
        f"отказ не назвал свойство: {findings[0]}"
    )

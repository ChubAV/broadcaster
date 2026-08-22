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


def _fake_redis(*replies: list):
    """Двойник клиента Redis, отдающий ответы конвейера ПО ПОРЯДКУ вызовов.

    ⚠️ ОТВЕТОВ НЕСКОЛЬКО, ПОТОМУ ЧТО КОНВЕЙЕРОВ ДВА (D-52). Подраздел читает
    сперва живость инфраструктуры (три ключа), потом живость воркеров
    аккаунтов; смешать их в один ответ значило бы проверять не то, что
    отдаётся. Последний объявленный ответ повторяется на всех последующих
    вызовах — так вызовы, которым тест ничего не назначил, не падают и не
    притворяются осмысленными.
    """
    queue = list(replies) or [[]]

    async def _execute():
        return queue.pop(0) if len(queue) > 1 else queue[0]

    pipe = MagicMock()
    pipe.get = MagicMock(return_value=pipe)
    pipe.llen = MagicMock(return_value=pipe)
    pipe.execute = AsyncMock(side_effect=_execute)
    client = MagicMock()
    client.pipeline = MagicMock(return_value=pipe)
    return client


def _row_markup(html: str, account_id: int) -> str:
    """Разметка ОДНОЙ строки воркера, найденная по идентификатору аккаунта.

    Утверждать про подпись поиском подстроки по ВСЕЙ странице нельзя: на
    странице два блока и сколько угодно строк, и «в работе» из
    инфраструктурного блока прошло бы за подпись строки аккаунта. Поэтому
    утверждения адресуются ячейке, а не документу.
    """
    marker = f">#{account_id}<"
    chunks = [chunk for chunk in html.split("<div data-row")[1:] if marker in chunk]
    assert len(chunks) == 1, (
        f"строка аккаунта #{account_id} найдена {len(chunks)} раз — "
        "утверждение адресовать нечему"
    )
    # Обрезаем по ЗАКРЫВАЮЩЕМУ тегу строки, а не по началу следующей: у
    # ПОСЛЕДНЕЙ строки следующей нет, и без этой обрезки в «разметку строки»
    # попал бы весь хвост документа — вместе с закрывающими тегами шелла,
    # которых у паршала нет. Сравнение страницы с паршалом тогда падало бы на
    # разнице, к строке не относящейся. Ячейки вложенных `div` не содержат,
    # поэтому первый `</div>` и есть конец строки.
    return chunks[0][: chunks[0].index("</div>")]


def _row_cell(html: str, account_id: int, index: int) -> str:
    """Ячейка строки аккаунта по индексу колонки (0 — «Аккаунт», -1 — последняя)."""
    cells = _row_markup(html, account_id).split('<span class="cell')[1:]
    assert len(cells) == 4, f"ожидалось четыре ячейки, найдено {len(cells)}"
    return cells[index]


def _tg_worker_cell(html: str, account_id: int) -> str:
    """Ячейка колонки «Воркер» — третья по `WORKER_COLUMNS`."""
    return _row_cell(html, account_id, 2)


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
async def test_telegram_row_worker_label_changes_with_the_source_state(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 4 (D-52): подпись «Воркер» у TG-строки ВЫВЕДЕНА ИЗ СОСТОЯНИЯ.

    ⚠️ УТВЕРЖДЕНИЕ ЗДЕСЬ — НЕ «НАПЕЧАТАНА ПРАВИЛЬНАЯ СТРОКА», А «СТРОКА
    МЕНЯЕТСЯ». Прежняя редакция D-09 мандатировала константу «в пуле app»:
    она истинна безусловно, поэтому не может измениться никогда и провалить
    проверку не может тоже — величина выглядела бы измеренной, ничего не
    измеряя. Единственный способ отличить измерение от декорации — прогнать
    ОДИН И ТОТ ЖЕ экран на РАЗНЫХ состояниях источника и потребовать разной
    подписи. Источник здесь — heartbeat службы `celery-worker-telegram`,
    третий ключ инфраструктурного конвейера.
    """
    from app.services.ops_state import INFRA_SERVICE_ORDER, INFRA_WORKER_TELEGRAM

    account = await _seed_account(db_session, account_type="tg_user")
    telegram_slot = INFRA_SERVICE_ORDER.index(INFRA_WORKER_TELEGRAM)

    def _infra(telegram_age_sec: float) -> list:
        beats = [str(int((time.time() - 600) * 1000))] * len(INFRA_SERVICE_ORDER)
        beats[telegram_slot] = str(int((time.time() - telegram_age_sec) * 1000))
        return beats

    with patch(
        "app.services.ops_state._get_redis", return_value=_fake_redis(_infra(1))
    ):
        alive = (await admin_client.get("/admin/workers")).text
    with patch(
        "app.services.ops_state._get_redis", return_value=_fake_redis(_infra(600))
    ):
        dead = (await admin_client.get("/admin/workers")).text
    with patch("app.services.ops_state._get_redis", return_value=None):
        blind = (await admin_client.get("/admin/workers")).text

    for html in (alive, dead, blind):
        assert f"#{account.id}" in html, "строка telegram-аккаунта не отрисовалась"

    tg_alive = _tg_worker_cell(alive, account.id)
    tg_dead = _tg_worker_cell(dead, account.id)
    tg_blind = _tg_worker_cell(blind, account.id)

    assert "в работе" in tg_alive
    assert "отключён" in tg_dead
    assert "неизвестно" in tg_blind
    assert tg_alive != tg_dead != tg_blind, (
        "подпись колонки «Воркер» не изменилась при смене состояния источника — "
        "величина неопровержима и потому не является измерением"
    )
    # Отменённая константа не вернулась ни в одну из веток.
    for html in (alive, dead, blind):
        assert "в пуле app" not in html
        assert "величина ещё не определена" not in html


@pytest.mark.asyncio
async def test_telegram_queue_cell_names_the_cause_of_the_missing_depth(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Прочерк в «В очереди» несёт `title` с ПРИЧИНОЙ, а не с фактом неполучения.

    Правило контракта UI заострено намеренно: `title`, сообщающий, что
    величину не удалось получить, запрещён ровно так же, как отсутствие
    `title` — он пересказывает провал вместо его причины. Причина у TG-строки
    названа предметно: очередь `telegram` ОДНА на все telegram-аккаунты,
    поэтому отдельной глубины у строки не существует; общее число, повторённое
    в каждой строке, читалось бы как величина аккаунта.
    """
    account = await _seed_account(db_session, account_type="tg_user")
    fresh = str(int(time.time() * 1000))

    with patch(
        "app.services.ops_state._get_redis",
        return_value=_fake_redis([fresh, fresh, fresh]),
    ):
        html = (await admin_client.get("/admin/workers")).text

    cell = _row_cell(html, account.id, -1)
    assert "—" in cell
    assert "title=" in cell, "голый прочерк без подсказки — запрещён контрактом"
    for forbidden in ("не удалось", "не определен", "неизвестно почему"):
        assert forbidden not in cell.lower(), f"подсказка пересказывает провал: {cell}"
    assert "одна на все" in cell, f"подсказка не называет причину: {cell}"


@pytest.mark.asyncio
async def test_queue_cell_names_the_broken_observer_when_redis_is_down(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Второй случай отсутствия глубины назван СВОЕЙ причиной, а не общей.

    Две разные причины под одной подсказкой слились бы в бессодержательную:
    «глубины нет» верно в обоих случаях и не помогает ни в одном.
    """
    account = await _seed_account(db_session, account_type="wa")

    with patch("app.services.ops_state._get_redis", return_value=None):
        html = (await admin_client.get("/admin/workers")).text

    cell = _row_cell(html, account.id, -1)
    assert "title=" in cell
    assert "Redis" in cell, f"подсказка не называет сломанного наблюдателя: {cell}"


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


# ---- Два блока подраздела, опрос и паршал (D-09, D-12, D-52) ----

@pytest.mark.asyncio
async def test_workers_subsection_has_two_named_blocks(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 1: блоков ДВА, и у каждого свой заголовок (D-09).

    Без верхнего блока упавший `celery-beat` не виден НИГДЕ, кроме отсутствия
    рассылок, — а это самая частая причина «всё встало».
    """
    await _seed_account(db_session, account_type="wa")

    with patch("app.services.ops_state._get_redis", return_value=None):
        html = (await admin_client.get("/admin/workers")).text

    assert "Инфраструктура" in html
    assert "Воркеры аккаунтов" in html
    assert html.index("Инфраструктура") < html.index("Воркеры аккаунтов"), (
        "инфраструктурный блок обязан стоять сверху: в аварии сперва смотрят, "
        "жив ли планировщик"
    )


@pytest.mark.asyncio
async def test_infrastructure_block_prints_three_services_from_the_named_source(
    admin_client: AsyncClient
):
    """Тест 2: три службы, и состояние каждой взято из источника решения D-52."""
    from app.pages.admin import INFRA_SERVICES
    from app.services.ops_state import INFRA_SERVICE_ORDER

    assert len(INFRA_SERVICES) == 3
    assert [service["key"] for service in INFRA_SERVICES] == list(INFRA_SERVICE_ORDER)

    beats = [str(int((time.time() - age) * 1000)) for age in (1, 600, 1)]
    with patch(
        "app.services.ops_state._get_redis", return_value=_fake_redis(beats)
    ):
        html = (await admin_client.get("/admin/workers")).text

    for service in INFRA_SERVICES:
        assert service["label"] in html, service["label"]
        # Ключ признака напечатан: в аварии администратору нужно знать, ЧТО
        # смотреть в Redis, а не только вердикт.
        assert f"infra:heartbeat:{service['key']}" in html
    assert "в работе" in html and "отключён" in html


@pytest.mark.asyncio
async def test_infrastructure_block_says_unknown_when_the_source_is_unreachable(
    admin_client: AsyncClient
):
    """Тест 3: сломанный наблюдатель — «неизвестно» и 200, а не отказ и не 500.

    Показать «отключён» при недоступном Redis значило бы отправить
    администратора чинить исправные службы.
    """
    with patch("app.services.ops_state._get_redis", return_value=None):
        response = await admin_client.get("/admin/workers")

    assert response.status_code == 200
    assert "неизвестно" in response.text
    assert "отключён" not in response.text


@pytest.mark.asyncio
async def test_lower_block_groups_accounts_by_channel(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 5: нижний блок делит строки по каналам, каждая — в своей группе."""
    tg = await _seed_account(db_session, account_type="tg_user")
    wa = await _seed_account(db_session, account_type="wa")
    mx = await _seed_account(db_session, account_type="max")

    fresh = str(int(time.time() * 1000))
    with patch(
        "app.services.ops_state._get_redis",
        return_value=_fake_redis([fresh, fresh, fresh], [fresh, 0, fresh, 0]),
    ):
        html = (await admin_client.get("/admin/workers")).text

    for label in ("Telegram", "WhatsApp", "MAX"):
        assert label in html, label
    positions = {
        account_type: html.index(f">#{account.id}<")
        for account_type, account in (("tg", tg), ("wa", wa), ("max", mx))
    }
    for account_type, group in (("tg", "Telegram"), ("wa", "WhatsApp"), ("max", "MAX")):
        heading = html.rindex(f"{group}</h", 0, positions[account_type])
        assert heading > 0, f"строка {account_type} стоит вне группы своего канала"


@pytest.mark.asyncio
async def test_workers_partial_answers_the_admin_with_the_same_rows(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 6а: паршал отвечает администратору ТЕМИ ЖЕ строками, что страница.

    ⚠️ ОТКАЗ ПОСТОРОННЕМУ ПРОВЕРЯЕТСЯ ОТДЕЛЬНЫМ ТЕСТОМ, И ЭТО НЕ ДРОБЛЕНИЕ РАДИ
    дробления: `admin_client` и `authed_client` — ОДИН И ТОТ ЖЕ объект клиента с
    разными cookie входа, и запрошенные в одном тесте они затирают друг друга.
    Утверждение про 403 в таком тесте проверяло бы не права, а порядок фикстур.
    """
    account = await _seed_account(db_session, account_type="wa")
    fresh = str(int(time.time() * 1000))
    replies = ([fresh, fresh, fresh], [fresh, 3])

    with patch(
        "app.services.ops_state._get_redis", return_value=_fake_redis(*replies)
    ):
        page = await admin_client.get("/admin/workers")
    with patch(
        "app.services.ops_state._get_redis", return_value=_fake_redis(*replies)
    ):
        partial = await admin_client.get("/admin/workers/partial")

    assert partial.status_code == 200
    # Те же строки, что первичная отрисовка: паршал и есть первичная отрисовка.
    assert f">#{account.id}<" in partial.text
    assert _row_markup(page.text, account.id) == _row_markup(partial.text, account.id)


@pytest.mark.asyncio
async def test_workers_partial_refuses_the_stranger(authed_client: AsyncClient):
    """Тест 6б: паршал отвечает 403 постороннему (T-06-PART).

    Роутер без зависимости шелла — это роутер без зависимости ШЕЛЛА, а не
    роутер без проверки прав. Паршал живёт вне страничной сборки, поэтому
    проверку администратора он держит СВОЮ, на самом обработчике.
    """
    assert (await authed_client.get("/admin/workers/partial")).status_code == 403


@pytest.mark.asyncio
async def test_workers_partial_does_not_inherit_the_shell(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 7: в ответе паршала нет ни одного признака разметки шелла."""
    await _seed_account(db_session, account_type="wa")

    with patch("app.services.ops_state._get_redis", return_value=None):
        body = (await admin_client.get("/admin/workers/partial")).text

    for marker in ("<!DOCTYPE", "<html", "<body", "data-sidebar", "data-subtabs"):
        assert marker not in body, f"паршал притащил шелл: {marker}"
    partial_source = (TEMPLATES_ROOT / "admin/includes/workers_partial.html").read_text(
        encoding="utf-8"
    )
    assert "extends" not in partial_source


@pytest.mark.asyncio
async def test_workers_subsection_polls_without_a_stop_condition(
    admin_client: AsyncClient
):
    """Тест 8: атрибуты опроса есть, интервал — константа модуля, автостопа нет.

    Автостопа нет НАМЕРЕННО, и мотив отличается от живой ленты Фазы 4:
    администратор открывает подраздел в момент аварии, и замершее состояние
    здесь вреднее, чем на дашборде (D-12).
    """
    from app.pages.admin import WORKERS_POLL_SEC

    assert 15 <= WORKERS_POLL_SEC <= 30

    with patch("app.services.ops_state._get_redis", return_value=None):
        html = (await admin_client.get("/admin/workers")).text

    assert 'hx-get="/admin/workers/partial"' in html
    assert f'hx-trigger="every {WORKERS_POLL_SEC}s"' in html
    # Условие остановки опроса не заводится: ни `once`, ни оборванный триггер.
    poll_markup = html[html.index('hx-get="/admin/workers/partial"') :][:400]
    for stopper in ("hx-trigger=\"once", " once", "hx-swap-oob"):
        assert stopper not in poll_markup, f"в разметку опроса попал автостоп: {stopper}"

    page_source = (TEMPLATES_ROOT / "admin/workers.html").read_text(encoding="utf-8")
    assert f"every {WORKERS_POLL_SEC}s" not in page_source, (
        "интервал выписан в разметке литералом — он обязан приходить константой "
        "модуля, иначе разъедется с маршрутом молча"
    )


def test_no_docker_client_reaches_the_partial_handler_either():
    """Тест 9: разбор дерева — обращений к контейнерному API нет и в паршале.

    Утверждение повторяет `test_no_docker_client_on_the_render_path` по ДРУГОМУ
    поводу: паршал тикает каждые двадцать секунд, и вызов демона в нём стоил бы
    не одного обращения на открытие страницы, а бессрочного потока обращений.
    """
    tree = ast.parse(ADMIN_PAGES_SOURCE.read_text(encoding="utf-8"))
    handlers = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and (node.name.startswith("admin_") or node.name.startswith("_workers"))
    ]
    assert any(node.name == "admin_workers_partial" for node in handlers)

    # Обработчик формы перезапуска исключён ИМЕНЕМ, а не забыт: D-11 разрешает
    # ему ровно одно обращение к контейнерному API, и разрешение это адресное.
    # Что оно не расползлось на соседей, утверждает
    # `test_the_container_api_lives_only_in_the_restart_handler` — двусторонне.
    for handler in handlers:
        if handler.name == "admin_restart_worker":
            continue
        called = [
            node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            for node in ast.walk(handler)
            if isinstance(node, ast.Call)
            and isinstance(node.func, (ast.Name, ast.Attribute))
        ]
        assert not [name for name in called if "docker" in name.lower()], handler.name
        assert not [name for name in called if "container" in name.lower()], handler.name


# ---- Перезапуск воркера: единственное во всей фазе обращение к Docker (D-11) ----
#
# ⚠️ ЭТОТ БЛОК ПРОВЕРЯЕТ ГРАНИЦУ, А НЕ КНОПКУ. D-07 запрещает контейнерное API
# на пути ОТРИСОВКИ, а не в приложении вообще; D-11 разрешает ровно один вызов и
# ровно по нажатию. Утверждения ниже держат обе половины: вызов происходит там,
# где разрешён, и не происходит нигде больше.


def _restart_url(account_id: int) -> str:
    return f"/admin/workers/{account_id}/restart"


@pytest.mark.asyncio
async def test_restart_starts_the_container_of_the_accounts_own_channel(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 1: форма зовёт запуск контейнера НУЖНОГО канала ровно один раз.

    Канал берётся из САМОГО аккаунта, а не из поля формы: поле подделывается
    вместе с запросом, колонка в базе — нет.
    """
    account = await _seed_account(db_session, account_type="wa")

    with patch(
        "app.services.wa_container_manager.start_container", return_value="http://x"
    ) as wa_start, patch(
        "app.services.max_container_manager.start_container", return_value="http://x"
    ) as max_start:
        response = await admin_client.post(
            _restart_url(account.id), follow_redirects=False
        )

    assert response.status_code == 302
    wa_start.assert_called_once_with(account.id)
    max_start.assert_not_called()


@pytest.mark.asyncio
async def test_restart_of_a_max_account_goes_to_the_max_manager(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Второй канал ходит к СВОЕМУ менеджеру: один на два канала перепутал бы их."""
    account = await _seed_account(db_session, account_type="max")

    with patch(
        "app.services.wa_container_manager.start_container", return_value="http://x"
    ) as wa_start, patch(
        "app.services.max_container_manager.start_container", return_value="http://x"
    ) as max_start:
        await admin_client.post(_restart_url(account.id), follow_redirects=False)

    max_start.assert_called_once_with(account.id)
    wa_start.assert_not_called()


@pytest.mark.asyncio
async def test_restart_is_refused_for_a_channel_without_a_container(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """У telegram-аккаунта своего контейнера нет — перезапускать нечего.

    Молчаливый успех здесь был бы хуже отказа: администратор решил бы, что
    починил, и перестал бы искать настоящую причину.
    """
    account = await _seed_account(db_session, account_type="tg_user")

    with patch("app.services.wa_container_manager.start_container") as wa_start, patch(
        "app.services.max_container_manager.start_container"
    ) as max_start:
        response = await admin_client.post(
            _restart_url(account.id), follow_redirects=False
        )

    assert response.status_code == 302
    wa_start.assert_not_called()
    max_start.assert_not_called()
    assert "error=" in response.headers["location"]


@pytest.mark.asyncio
async def test_restart_is_denied_for_a_regular_user(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Тест 2: посторонний отвергается по правам и контейнера не трогает."""
    account = await _seed_account(db_session, account_type="wa")

    with patch("app.services.wa_container_manager.start_container") as wa_start:
        response = await authed_client.post(_restart_url(account.id))

    assert response.status_code == 403
    wa_start.assert_not_called()


@pytest.mark.asyncio
async def test_restart_is_refused_for_a_foreign_origin_before_touching_anything(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 3: чужое происхождение отвергается ДО вызова (T-06-RST2).

    Гард обязателен: аутентификация проекта идёт cookie, поэтому браузер
    приложит её к межсайтовой форме сам, и изменяющий запрос со стороннего
    сайта неотличим от своего. Новая изменяющая форма админки без гарда молча
    расширила бы принятую границу риска — сегодня его несут ровно три формы, и
    две из них денежные.
    """
    account = await _seed_account(db_session, account_type="wa")

    with patch("app.services.wa_container_manager.start_container") as wa_start:
        response = await admin_client.post(
            _restart_url(account.id),
            headers={"Sec-Fetch-Site": "cross-site"},
            follow_redirects=False,
        )

    assert response.status_code == 403
    wa_start.assert_not_called()


@pytest.mark.asyncio
async def test_restart_of_an_unknown_account_never_reaches_the_container(
    admin_client: AsyncClient,
):
    """Тест 6: неизвестный аккаунт отвергается до обращения к контейнеру."""
    with patch("app.services.wa_container_manager.start_container") as wa_start:
        response = await admin_client.post(_restart_url(999999), follow_redirects=False)

    assert response.status_code == 302
    wa_start.assert_not_called()


@pytest.mark.asyncio
async def test_unreachable_daemon_gives_named_words_and_a_log_line_not_a_500(
    admin_client: AsyncClient, db_session: AsyncSession, caplog
):
    """Тест 4: недоступный демон — названный отказ и запись в журнал, НЕ 500.

    Молча вернувшая ту же страницу кнопка читается как «кнопка сломана»
    (Pitfall 7). Текст стороннего исключения на экран при этом не выходит: он
    ничего не сообщает администратору и может нести внутренние адреса.
    """
    account = await _seed_account(db_session, account_type="wa")

    with patch(
        "app.services.wa_container_manager.start_container",
        side_effect=RuntimeError(
            "Error while fetching server API version: /var/run/whale.sock"
        ),
    ):
        with caplog.at_level("WARNING"):
            response = await admin_client.post(
                _restart_url(account.id), follow_redirects=False
            )

    assert response.status_code == 302, "отказ обязан оставаться отказом, а не 500"
    assert "worker_restart_failed" in caplog.text, (
        "отказ проглочен молча — именованной строки журнала нет"
    )
    assert str(account.id) in caplog.text

    with patch("app.services.ops_state._get_redis", return_value=None):
        page = (await admin_client.get(response.headers["location"])).text
    assert "демон контейнеров не отвечает" in page
    assert "/var/run" not in page, "текст стороннего исключения вышел на экран"


@pytest.mark.asyncio
async def test_successful_restart_leaves_a_named_trace(
    admin_client: AsyncClient, db_session: AsyncSession, caplog
):
    """Тест 5: успех уходит в журнал с идентификаторами админа, аккаунта и канала.

    Привилегированная операция над чужой сущностью обязана оставлять след, и
    форма следа в проекте уже есть (`free_access_toggled`).
    """
    account = await _seed_account(db_session, account_type="wa")

    with patch(
        "app.services.wa_container_manager.start_container", return_value="http://x"
    ):
        with caplog.at_level("INFO"):
            await admin_client.post(_restart_url(account.id), follow_redirects=False)

    assert "worker_restarted" in caplog.text
    assert str(account.id) in caplog.text
    assert "wa" in caplog.text


@pytest.mark.asyncio
async def test_no_stop_action_exists_in_markup_or_in_routes(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 7 (отрицательный): действия остановки нет ни в разметке, ни в маршрутах.

    ⚠️ ЭТО ЗАПРЕТ, ЗАКРЕПЛЁННЫЙ ТЕСТОМ, А НЕ НАМЕРЕНИЕ (D-11). Остановка
    обещает контроль, которого нет: воркер уходит сам через 300 секунд простоя
    и возвращается через 15 секунд при появлении задачи. Администратор,
    нажавший её в аварии, решит, что починил, и перестанет искать причину.
    """
    await _seed_account(db_session, account_type="wa")

    with patch("app.services.ops_state._get_redis", return_value=None):
        html = (await admin_client.get("/admin/workers")).text
    assert "Остановить" not in html
    assert "/stop" not in html

    from app.main import create_app

    paths = {route.path for route in create_app().routes if hasattr(route, "path")}
    assert not [path for path in paths if "stop" in path.lower()], sorted(paths)

    assert "stop_container" not in ADMIN_PAGES_SOURCE.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_restart_button_goes_through_the_confirmation_panel(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 8: кнопка ведёт через общую панель подтверждения, а не шлёт сразу.

    Тринадцать мест проекта уже переведены с системного диалога на панель;
    четырнадцатое не имеет права быть исключением. Перезапуск обрывает активные
    отправки этого аккаунта — откат кода тривиален, последствия нажатия нет.
    """
    account = await _seed_account(db_session, account_type="wa")

    with patch("app.services.ops_state._get_redis", return_value=None):
        html = (await admin_client.get("/admin/workers")).text

    assert "Перезапустить" in html
    assert 'role="dialog"' in html, "панель подтверждения не отрисована"
    assert f"modal-open-worker-restart-{account.id}" in html
    assert "confirm(" not in html and "onclick" not in html
    # Базовый путь без JS остаётся настоящей формой POST на тот же адрес.
    assert f'action="{_restart_url(account.id)}"' in html


def test_the_container_api_lives_only_in_the_restart_handler():
    """Разбор ДЕРЕВА: контейнерное API есть ТОЛЬКО в обработчике перезапуска.

    Утверждение двустороннее намеренно. Односторонний запрет («нигде нет»)
    выполнялся бы и пустым модулем; одностороннее разрешение («в перезапуске
    есть») не заметило бы второго вызова, уехавшего на путь отрисовки. Вместе
    они и есть граница D-07/D-11.
    """
    tree = ast.parse(ADMIN_PAGES_SOURCE.read_text(encoding="utf-8"))

    def _calls(node) -> list[str]:
        return [
            child.func.id if isinstance(child.func, ast.Name) else child.func.attr
            for child in ast.walk(node)
            if isinstance(child, ast.Call)
            and isinstance(child.func, (ast.Name, ast.Attribute))
        ]

    container_callers = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and [name for name in _calls(node) if "container" in name.lower()]
    }
    assert container_callers == {"admin_restart_worker"}, (
        "контейнерное API вызывается не только из обработчика формы перезапуска: "
        f"{sorted(container_callers)}"
    )

    assert not [
        name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for name in _calls(node)
        if "stop_container" in name
    ]


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


# ---- Страховочная сетка сноса справочника групп (D-05) ----

def test_groups_info_gone_from_templates_and_routes():
    """Ни один шаблон и ни один маршрут не ведёт на снесённый адрес (D-05).

    ⚠️ УТВЕРЖДЕНИЕ ПО ДЕРЕВУ КАТАЛОГА И ПО ПЕРЕЧНЮ МАРШРУТОВ, А НЕ ПО ОДНОМУ
    ФАЙЛУ. Ссылка, забытая в соседнем шаблоне, отдала бы администратору 404 —
    и отдала бы молча, потому что сам снос выглядел бы завершённым. Поэтому
    проверяются ВСЕ шаблоны проекта и ВСЕ маршруты собранного приложения.

    Хранилище под снос НЕ попадает: таблица `group_info`, её модель, её
    репозиторий и ревизия `0011` остаются — снос касается поверхности, и это
    отдельное намеренное решение, а не недоделка.
    """
    dead_url = "/admin/" + "groups-info"

    offenders = [
        str(path)
        for path in TEMPLATES_ROOT.rglob("*.html")
        if dead_url in path.read_text(encoding="utf-8")
    ]
    assert not offenders, f"ссылка на снесённый адрес осталась в шаблонах: {offenders}"

    assert not (TEMPLATES_ROOT / "admin" / "groups_info.html").exists()
    assert not (TEMPLATES_ROOT / "admin" / "group_info_detail.html").exists()

    from app.main import create_app
    from app.config import Settings

    app = create_app(
        settings=Settings(
            _env_file=None,
            database_url="sqlite+aiosqlite:///:memory:",
            redis_url="redis://localhost:6379/0",
            secret_key="test-secret-key",
            telegram_api_id=12345,
            telegram_api_hash="test_api_hash",
            wa_bridge_urls=["http://localhost:3000"],
            admin_email="admin@test.com",
            smtp_host="",
            smtp_port=587,
            smtp_user="",
            smtp_password="",
            smtp_from="noreply@test.com",
        )
    )
    live = [
        route.path
        for route in app.routes
        if dead_url in getattr(route, "path", "")
    ]
    assert not live, f"маршрут снесённого справочника всё ещё объявлен: {live}"


def test_groups_info_gone_but_its_storage_survived():
    """Хранилище справочника ЦЕЛО — снесена поверхность, а не данные (D-05).

    Утверждение парное к предыдущему и существует ради ассимметрии решения:
    экраны сняты, потому что у таблицы нет производителя, но таблица, её
    модель, её репозиторий и ревизия остаются — снос данных был бы необратим,
    а снос экранов откатывается из git.
    """
    assert Path("app/models/group_info.py").exists()
    assert Path("app/repositories/group_info.py").exists()
    assert list(Path("alembic/versions").glob("0011*.py"))

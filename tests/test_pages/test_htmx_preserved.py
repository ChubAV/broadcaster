"""Wave 0: страховочная сетка для живых HTMX-взаимодействий (План 01-03, UI-05).

Все тесты этого файла ЗЕЛЁНЫЕ НА ТЕКУЩЕМ КОДЕ — они фиксируют поведение до того,
как разметку начнут переверстывать, а не описывают новое поведение.

Три механизма, которые ломаются молча (страница продолжает отдавать 200, а
поведение исчезает):

1. Цепочка бесконечной прокрутки. Сентинел «Загрузка…» лежит ВНУТРИ партиала и
   заменяет сам себя, подтягивая вместе со следующей порцией новый сентинел.
   Поломка не видна на первом экране — поэтому тесты запрашивают ВТОРУЮ страницу.
2. Самоостановка опроса статуса синхронизации. Опрос прекращается тем, что
   очередной ответ приходит БЕЗ HTMX-атрибутов: они обёрнуты условием по статусу
   прямо в шаблоне. Вынос атрибутов наружу «ради единообразия» превратил бы это в
   вечный опрос каждые 5 секунд на каждой открытой вкладке.
3. Якоря подмены. Идентификаторы строки аккаунта и блоков статуса подключения —
   точки, куда приходит замена; они обязаны оставаться на ТОМ ЖЕ элементе,
   который несёт запрос.

Атрибута явной цели подмены в проекте нет нигде: все взаимодействия — это hx-get
с неявной целью (сам элемент) плюс hx-swap. Утверждать про явную цель нечего.
"""

import re
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.user import User

# Достаточно, чтобы вторая страница выдачи (offset=30, limit=30) сама имела
# продолжение: обработчики берут limit + 1 строку и ставят сентинел при has_next.
SEED_ROWS = 61
PAGE = 30

# Сентинел бесконечной прокрутки — единственный hx-get, ведущий на /partial.
# Опрос статуса аккаунта (/accounts/{id}/sync-status) под этот шаблон не попадает.
SENTINEL_RE = re.compile(r'hx-get="([^"]*/partial\?[^"]*)"')


async def _user(db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.email == "testuser@test.com"))
    return result.scalar_one()


async def _seed_account(
    db: AsyncSession, user_id: int, status: str = "active", type_: str = "wa"
) -> MessengerAccount:
    account = MessengerAccount(
        user_id=user_id, type=type_, credentials="session", status=status
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def _seed_section(db: AsyncSession, section: str) -> None:
    """Наполняет раздел так, чтобы вторая страница выдачи имела продолжение."""
    user = await _user(db)
    if section == "ads":
        db.add_all(
            [
                Ad(user_id=user.id, title=f"Объявление {i}", text=f"Текст {i}", images=[])
                for i in range(SEED_ROWS)
            ]
        )
    elif section == "accounts":
        db.add_all(
            [
                MessengerAccount(
                    user_id=user.id, type="wa", credentials=f"cred-{i}", status="active"
                )
                for i in range(SEED_ROWS)
            ]
        )
    elif section == "groups":
        account = await _seed_account(db, user.id)
        db.add_all(
            [
                Group(
                    user_id=user.id,
                    account_id=account.id,
                    messenger_type="wa",
                    group_external_id=f"ext-{i}",
                    name=f"Группа {i}",
                )
                for i in range(SEED_ROWS)
            ]
        )
    elif section == "schedules":
        ad = Ad(user_id=user.id, title="Объявление расписаний", text="Текст", images=[])
        db.add(ad)
        await db.commit()
        await db.refresh(ad)
        db.add_all(
            [
                Schedule(
                    ad_id=ad.id,
                    account_id=None,
                    group_ids=[],
                    days_of_week=[1],
                    times_of_day=["10:00"],
                    timezone="UTC",
                )
                for i in range(SEED_ROWS)
            ]
        )
    elif section == "history":
        db.add_all(
            [
                SendLog(
                    user_id=user.id,
                    ad_title=f"Отправка {i}",
                    ad_text="Текст",
                    group_name=f"Группа {i}",
                    messenger_type="wa",
                    status="ok",
                )
                for i in range(SEED_ROWS)
            ]
        )
    else:  # pragma: no cover — защита от опечатки в параметризации
        raise AssertionError(f"неизвестный раздел: {section}")
    await db.commit()


def _sentinel_urls(html: str) -> list[str]:
    return SENTINEL_RE.findall(html)


def _sentinel_offset(html: str) -> int:
    """Смещение следующего сентинела.

    Извлекается регулярным выражением по URL, а не сравнением строки целиком:
    URL меняется (из него уходит параметр компоновки), и тест обязан пережить
    это изменение. Поэтому утверждается отношение «больше», а не значение.
    """
    urls = _sentinel_urls(html)
    assert urls, f"сентинел бесконечной прокрутки не найден в ответе:\n{html[:800]}"
    match = re.search(r"offset=(\d+)", urls[-1])
    assert match, f"в URL сентинела нет смещения: {urls[-1]}"
    return int(match.group(1))


# --- UI-05: цепочка бесконечной прокрутки -----------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("section", ["ads", "groups", "schedules", "history", "accounts"])
async def test_infinite_scroll_chain(
    authed_client: AsyncClient, db_session: AsyncSession, section: str
):
    """Вторая страница выдачи несёт следующий сентинел с бо́льшим смещением.

    Проверяется именно вторая страница: разрыв цепочки невидим на первом экране,
    а на малом объёме тестовых данных прокрутки может не быть вовсе.
    """
    await _seed_section(db_session, section)

    response = await authed_client.get(
        f"/{section}/partial?offset={PAGE}&limit={PAGE}&layout=cards"
    )
    assert response.status_code == 200, section

    assert _sentinel_offset(response.text) > PAGE, section


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "section,query,expected",
    [
        ("groups", "messenger_type=wa", "messenger_type=wa"),
        ("history", "status=ok", "status=ok"),
        # Расписания получили полосу фильтров планом 02-07. Раздел дописан сюда
        # в тот же заход: фильтр, потерянный сентинелом, не роняет страницу —
        # он молча подмешивает неотфильтрованные расписания к отфильтрованным
        # на второй странице выдачи, и увидеть это можно только прокруткой.
        ("schedules", "state=active", "state=active"),
    ],
)
async def test_infinite_scroll_keeps_filters(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    section: str,
    query: str,
    expected: str,
):
    """Вторая страница выдачи не теряет фильтрацию: фильтр едет в URL сентинела."""
    await _seed_section(db_session, section)

    response = await authed_client.get(
        f"/{section}/partial?offset={PAGE}&limit={PAGE}&layout=cards&{query}"
    )
    assert response.status_code == 200, section

    urls = _sentinel_urls(response.text)
    assert urls, section
    assert expected in urls[-1], f"{section}: фильтр потерян в {urls[-1]}"


# --- UI-05: самоостановка опроса статуса синхронизации ----------------------

@pytest.mark.asyncio
async def test_sync_polling_stops(authed_client: AsyncClient, db_session: AsyncSession):
    """Ответ без hx-trigger — это и есть механизм остановки опроса.

    Если атрибуты вынести из-под условия по статусу, каждая открытая вкладка
    каждого пользователя начнёт дёргать сервер каждые 5 секунд без конца.
    """
    user = await _user(db_session)
    account = await _seed_account(db_session, user.id, status="active")

    response = await authed_client.get(f"/accounts/{account.id}/sync-status?layout=cards")
    assert response.status_code == 200
    assert "hx-trigger" not in response.text
    assert "hx-get" not in response.text


@pytest.mark.asyncio
async def test_sync_polling_continues_while_syncing(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Парный тест: без него предыдущий зеленел бы вакуумно (пустой ответ)."""
    user = await _user(db_session)
    account = await _seed_account(db_session, user.id, status="syncing")

    response = await authed_client.get(f"/accounts/{account.id}/sync-status?layout=cards")
    assert response.status_code == 200
    assert "hx-trigger" in response.text
    assert "hx-get" in response.text
    assert f'id="account-row-{account.id}"' in response.text


# --- UI-05: самоостановка опроса на экране групп аккаунта (План 03-06) ------
#
# Второй в проекте самоостанавливающийся опрос. Экран групп аккаунта добирает
# завершение ФОНОВОЙ синхронизации WA и MAX: она уходит в Celery, и без опроса
# пользователь не узнал бы о её конце, не перезагрузив страницу.
#
# Пара повторена дословно по той же причине, что и у экрана аккаунтов: тест
# присутствия в одиночку зеленеет и у вечного опроса, тест отсутствия в
# одиночку — на пустом ответе. Красить обязан каждый из двух.


async def _seed_groups_account(
    db: AsyncSession, status: str
) -> MessengerAccount:
    user = await _user(db)
    return await _seed_account(db, user.id, status=status)


@pytest.mark.asyncio
async def test_account_groups_polling_stops(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Ответ без hx-trigger — механизм остановки опроса экрана групп."""
    account = await _seed_groups_account(db_session, status="active")

    response = await authed_client.get(
        f"/accounts/{account.id}/groups/sync-status?layout=cards"
    )
    assert response.status_code == 200
    assert "hx-trigger" not in response.text
    assert "hx-get" not in response.text


@pytest.mark.asyncio
async def test_account_groups_polling_continues_while_syncing(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Парный тест: без него предыдущий зеленел бы вакуумно (пустой ответ)."""
    account = await _seed_groups_account(db_session, status="syncing")

    response = await authed_client.get(
        f"/accounts/{account.id}/groups/sync-status?layout=cards"
    )
    assert response.status_code == 200
    assert "hx-trigger" in response.text
    assert "hx-get" in response.text
    assert f'id="account-groups-sync-{account.id}"' in response.text


@pytest.mark.asyncio
async def test_account_groups_page_polls_only_while_syncing(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Сама страница объявляет опрос ровно в статусе выполнения.

    Ответ входа проверяют тесты выше; здесь проверяется ПЕРВИЧНАЯ отрисовка —
    вечный опрос, объявленный страницей, до входа статуса вообще не доходит и
    парой тестов на вход не ловится.
    """
    syncing = await _seed_groups_account(db_session, status="syncing")
    active = await _seed_groups_account(db_session, status="active")

    running = (await authed_client.get(f"/accounts/{syncing.id}/groups")).text
    finished = (await authed_client.get(f"/accounts/{active.id}/groups")).text

    assert 'hx-trigger="every' in running
    assert 'hx-trigger="every' not in finished


# --- UI-05: якоря подмены ---------------------------------------------------

@pytest.mark.asyncio
async def test_swap_anchors_present(authed_client: AsyncClient, db_session: AsyncSession):
    """Идентификаторы-якоря остаются на ТОМ ЖЕ элементе, который несёт запрос."""
    user = await _user(db_session)
    # Якорь строки аккаунта существует ровно у синхронизирующегося аккаунта —
    # именно ему приходит замена. У остальных статусов замене неоткуда взяться.
    # Тип MAX выбран намеренно: экран подключения WhatsApp ниже перенаправляет
    # на /accounts, если у пользователя уже есть активный или синхронизирующийся
    # WA-аккаунт.
    account = await _seed_account(db_session, user.id, status="syncing", type_="max")

    html = (await authed_client.get("/accounts")).text
    assert re.search(rf'id="account-row-{account.id}"[^>]*hx-get="', html), (
        "якорь строки аккаунта потерял запрос обновления"
    )

    # Экран подключения WhatsApp: якорь опроса статуса подключения.
    # Мост недоступен из тестов, поэтому мессенджер подменяется — как в
    # tests/test_routes/test_wa_sync_status.py.
    with patch("app.pages.accounts.WhatsAppMessenger") as MockWa:
        instance = MockWa.return_value
        instance.start_session = AsyncMock(return_value={"status": "ok"})
        instance.get_qr = AsyncMock(return_value={"qr": "data:image/png;base64,x"})
        wa_html = (await authed_client.get("/accounts/connect/wa")).text
    assert re.search(r'id="wa-status"[^>]*hx-get="', wa_html), (
        "якорь статуса подключения WhatsApp потерял запрос опроса"
    )

    # Экран подключения MAX: якорь появляется на шаге QR, а он достигается
    # отправкой формы с телефоном — GET отдаёт шаг ввода номера.
    with patch("app.pages.accounts.MaxMessenger") as MockMax:
        instance = MockMax.return_value
        instance.start_session = AsyncMock(side_effect=RuntimeError("bridge offline"))
        instance.get_qr = AsyncMock(return_value={})
        max_html = (
            await authed_client.post(
                "/accounts/connect/max/start", data={"phone": "+79991234567"}
            )
        ).text
    assert re.search(r'id="max-status"[^>]*hx-get="', max_html), (
        "якорь статуса подключения MAX потерял запрос опроса"
    )


# --- D-15: запрос партиала без параметра компоновки -------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("section", ["ads", "groups", "schedules", "history", "accounts"])
async def test_partial_without_layout_param_ok(
    authed_client: AsyncClient, db_session: AsyncSession, section: str
):
    """Сегодня уводит в недостижимую ветку; после схлопывания обязан работать.

    У открытых вкладок пользователей сентинелы всё ещё несут прежний URL —
    поэтому и запрос без параметра компоновки, и запрос с ним обязаны
    возвращать 200.
    """
    await _seed_section(db_session, section)

    without = await authed_client.get(f"/{section}/partial?offset=0&limit={PAGE}")
    assert without.status_code == 200, section

    legacy = await authed_client.get(
        f"/{section}/partial?offset=0&limit={PAGE}&layout=cards"
    )
    assert legacy.status_code == 200, section

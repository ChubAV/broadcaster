"""ADS-07 / ADS-08: полный цикл расписания внутри редактора объявления.

Этот файл — ГЕЙТ следующего плана. 02-06 несёт предусловие «`uv run pytest
tests/test_pages/test_editor_schedules.py -q` завершается с кодом 0» и обязан
остановиться, если файл красный или отсутствует: только зелёный новый путь даёт
02-06 право сносить `/schedules/new` и `/schedules/{id}/edit` (D-16, SC-3).

Две группы утверждений:

* **Возврат в редактор** — четыре страничных обработчика расписаний
  заканчивались редиректом на сводный список, и в редакторе это выкидывало бы
  пользователя со страницы после каждой правки (Pitfall 11). Признак
  происхождения приходит полем формы; адрес редиректа строит СЕРВЕР из
  идентификатора объявления уже проверенной на владение записи — подстановка
  значения поля как есть была бы открытым редиректом (T-02-23).
* **Неполнота и валидация** — неполное расписание сохраняется ВЫКЛЮЧЕННЫМ
  (D-08), а значения, не приводящиеся к своему типу, отбрасываются ДО разбора:
  прямой POST мимо браузера обязан давать отказ валидации, а не 500
  (T-02-24, T-02-25).
"""

from contextlib import contextmanager
from datetime import datetime, timezone

import re
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import event, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import AD_STATUS_PUBLISHED
from app.pages.common import format_datetime_for_user, templates
from app.pages.schedules import ID_MAX
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User
from tests.conftest import a_future_run_moment

FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}


@pytest_asyncio.fixture
async def owner(db_session: AsyncSession) -> User:
    return (
        await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_ad(db: AsyncSession, user_id: int, title: str = "Объявление редактора") -> Ad:
    ad = Ad(
        user_id=user_id,
        title=title,
        text="Текст объявления",
        images=[],
        status=AD_STATUS_PUBLISHED,
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


async def _seed_account(db: AsyncSession, user_id: int, type_: str = "tg_user") -> MessengerAccount:
    account = MessengerAccount(
        user_id=user_id, type=type_, credentials="creds", status="active"
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def _seed_group(
    db: AsyncSession,
    user_id: int,
    account_id: int,
    name: str = "Группа расписания",
    is_active: bool = True,
) -> Group:
    group = Group(
        user_id=user_id,
        account_id=account_id,
        messenger_type="tg_user",
        group_external_id=f"ext-{name}",
        name=name,
        is_active=is_active,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def _stranger(db: AsyncSession) -> User:
    """Второй пользователь — владелец «чужой» группы.

    Форма посева взята из tests/test_pages/test_ads_editor.py: чужая запись
    обязана принадлежать НАСТОЯЩЕМУ пользователю, иначе отсутствие группы в
    выдаче объяснялось бы отсутствием владельца, а не скоупом выборки.
    """
    user = User(email="stranger@test.com", password_hash="x", name="Stranger")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _seed_schedule(
    db: AsyncSession,
    ad_id: int,
    account_id: int | None,
    group_ids: list[int] | None = None,
    days: list[int] | None = None,
    times: list[str] | None = None,
    is_active: bool = True,
) -> Schedule:
    schedule = Schedule(
        ad_id=ad_id,
        account_id=account_id,
        group_ids=group_ids if group_ids is not None else [],
        days_of_week=days if days is not None else [0],
        times_of_day=times if times is not None else ["09:00"],
        timezone="UTC",
        is_active=is_active,
        # Момент запуска ставится ТОЛЬКО включённой строке. Схема запрещает пару
        # «включено + нет момента» (CHECK ck_schedules_active_requires_next_run),
        # а приостановленной строке он не нужен и вреден: карточка печатает
        # «следующий запуск» по одному лишь наличию значения, и выданный паузе
        # момент менял бы разметку, к предмету этих тестов отношения не имеющую.
        next_run_at=(
            a_future_run_moment() if is_active else None
        ),
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


def _form(pairs: list[tuple[str, str]]) -> str:
    return urlencode(pairs)


# populate_existing, а не expire_all: сессия теста — ТА ЖЕ, что у обработчика
# (dependency_overrides), поэтому в карте идентичности уже лежит объект,
# созданный запросом. Без принудительного заполнения часть его атрибутов
# остаётся истёкшей, и первое же обращение к ним уходит в ленивую загрузку вне
# greenlet-контекста — тест падает MissingGreenlet вместо своего утверждения.
async def _reload(db: AsyncSession, schedule_id: int) -> Schedule:
    return (
        await db.execute(
            select(Schedule)
            .where(Schedule.id == schedule_id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one()


async def _all_schedules(db: AsyncSession) -> list[Schedule]:
    return list(
        (
            await db.execute(
                select(Schedule)
                .order_by(Schedule.id)
                .execution_options(populate_existing=True)
            )
        )
        .scalars()
        .all()
    )


# --- Возврат в редактор -------------------------------------------------------


@pytest.mark.asyncio
async def test_create_from_editor_returns_to_the_editor(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Создание расписания из редактора возвращает в редактор ЭТОГО объявления."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("return_to", "editor"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith(f"/ads/{ad.id}/edit"), location
    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert f"sched={created[0].id}" in location, location


@pytest.mark.asyncio
async def test_create_without_the_editor_marker_still_goes_to_the_summary_list(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Без признака происхождения поведение прежнее — редирект на сводный список.

    Парный тест к предыдущему: без него признак мог бы игнорироваться, и оба
    пути молча вели бы в редактор.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form([("ad_id", str(ad.id)), ("account_id", str(account.id))]),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/schedules"


@pytest.mark.asyncio
async def test_schedule_create_over_htmx_appends_the_card_to_the_list(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Создание при НЕПУСТОМ списке отдаёт карточку для вставки В КОНЕЦ (FORM-07, D-05).

    Верхним узлом тела стоит САМА карточка — та же разметка, что печатает полная
    страница, — и приезжает она РАСКРЫТОЙ: сегодня путь деградации приземляет
    человека с `?sched=N`, и подмена обязана давать тот же экран. Панель
    подтверждения едет ВМЕСТЕ с ней, потому что на полной странице обе
    принадлежат контейнеру `#sched-list`: ответ, принёсший статью без панели,
    дал бы карточку, кнопка удаления которой не открывает ничего.

    ⚠️ ЛИНЕЙКА И СВОДКА СЛИЧАЮТСЯ С ПОЛНОЙ СТРАНИЦЕЙ, А НЕ С ОЖИДАЕМЫМ ТЕКСТОМ.
    Утверждение «в линейке написано „2 расписания“» зеленело бы на собственной
    копии формулировки; предмет же в том, что линейка ПОСЛЕ СОЗДАНИЯ и линейка
    ПОСЛЕ ПЕРЕЗАГРУЗКИ — одна величина, собранная одним источником разметки.
    """
    from tests.test_pages.test_confirm_delete_transport import _oob_node_ids

    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    await _seed_schedule(db_session, ad.id, account.id)

    response = await htmx_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("return_to", "editor"),
            ]
        ),
        headers=FORM_HEADERS,
    )

    assert response.status_code == 200, response.status_code
    body = response.text
    assert "<!DOCTYPE" not in body, "слою письма приехал целый документ"

    created = await _all_schedules(db_session)
    assert len(created) == 2, [s.id for s in created]
    new_id = created[-1].id

    assert body.lstrip().startswith(
        f'<article data-sched-card id="sched-{new_id}">'
    ), body[:200]
    assert f'action="/schedules/{new_id}/edit"' in body, (
        "новая карточка приехала свёрнутой — формы правки в ней нет"
    )
    assert f'id="sched-del-{new_id}"' in body, (
        "панель подтверждения новой карточки не приехала: на полной странице "
        "она принадлежит тому же контейнеру, что и статья"
    )

    oob_ids = _oob_node_ids(body)
    assert "#sched-count" in oob_ids, f"узла линейки нет среди внеполосных: {oob_ids}"
    assert "ad-summary" in oob_ids, f"узла сводки нет среди внеполосных: {oob_ids}"

    rule = re.search(
        r'<div hx-swap-oob="innerHTML:#sched-count">(.*?)</div>', body, re.S
    )
    assert rule, body[-800:]

    htmx_client.headers.pop("HX-Request")
    page = await htmx_client.get(f"/ads/{ad.id}/edit")
    assert page.status_code == 200
    page_rule = re.search(r'<div id="sched-count">(.*?)</div>', page.text, re.S)
    assert page_rule, "обёртки линейки на полной странице нет"
    assert page_rule.group(1).strip() == rule.group(1).strip(), (
        f"линейка после создания {rule.group(1)!r} разошлась с линейкой после "
        f"перезагрузки {page_rule.group(1)!r}"
    )


@pytest.mark.asyncio
async def test_the_first_schedule_over_htmx_lands_by_a_location_header(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """«Было ноль» приземляет ПЕРЕХОДОМ, а не фрагментом (D-05).

    При пустом списке контейнера в документе нет вовсе (ветка пустого
    состояния), и фрагменту некуда приземлиться: ответ уходит 204 с заголовком
    перехода на ТОТ ЖЕ адрес, что уезжает 302 без htmx. Второго механизма
    отрисовки пустого и непустого состояния фаза не заводит — идиома D-09
    Фазы 9 в обратную сторону.

    Посимвольное равенство адресов обоих транспортов утверждает пара модуля
    `tests/test_pages/test_htmx_post_pairs.py`; здесь утверждается форма ответа.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)

    response = await htmx_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("return_to", "editor"),
            ]
        ),
        headers=FORM_HEADERS,
    )

    assert response.status_code == 204, response.status_code
    created = await _all_schedules(db_session)
    assert len(created) == 1, [s.id for s in created]
    new_id = created[0].id
    assert response.headers.get("HX-Location") == (
        f"/ads/{ad.id}/edit?sched={new_id}#sched-{new_id}"
    ), response.headers.get("HX-Location")
    assert response.content == b"", "у ответа 204 появилось тело"


@pytest.mark.asyncio
async def test_update_from_editor_returns_to_the_editor(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)

    response = await authed_client.post(
        f"/schedules/{schedule.id}/edit",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("days_of_week", "1"),
                ("times_of_day", "18:30"),
                ("timezone", "UTC"),
                ("return_to", "editor"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith(f"/ads/{ad.id}/edit"), location
    assert f"sched={schedule.id}" in location, location


@pytest.mark.asyncio
async def test_schedule_edit_over_htmx_swaps_only_its_card(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Правка на транспорте htmx отвечает фрагментом СВОЕЙ карточки (FORM-03, D-02).

    Первым узлом тела стоит сама карточка — цель `outerHTML` формы правки; она
    приезжает раскрытой (раскрытие — серверное состояние, D-12(а)), и корня
    панели подтверждения удаления в теле НЕТ: панель живёт снаружи карточки, и
    подмена карточки, принёсшая вторую панель, задвоила бы её в документе.
    Путь без htmx стережёт `test_update_from_editor_returns_to_the_editor` выше.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)

    response = await htmx_client.post(
        f"/schedules/{schedule.id}/edit",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("days_of_week", "1"),
                ("times_of_day", "18:30"),
                ("timezone", "UTC"),
                ("return_to", "editor"),
            ]
        ),
        headers=FORM_HEADERS,
    )

    assert response.status_code == 200, response.status_code
    body = response.text
    assert "<!DOCTYPE" not in body, "слою письма приехал целый документ"
    assert body.lstrip().startswith(
        f'<article data-sched-card id="sched-{schedule.id}">'
    ), body[:200]
    assert f'action="/schedules/{schedule.id}/edit"' in body, (
        "форма правки отсутствует — карточка приехала свёрнутой"
    )
    assert f'id="sched-del-{schedule.id}"' not in body, (
        "корень панели подтверждения приехал в теле подмены карточки"
    )


@pytest.mark.asyncio
async def test_schedule_edit_over_htmx_refreshes_the_summary_and_the_panel_text(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Ответ правки обновляет сводку объявления и ТЕКСТ панели подтверждения.

    Панель удаления стоит снаружи подменяемой карточки и после правки осталась
    бы спрашивать про прежние дни и группы. Ответ несёт два верхнеуровневых
    внеполосных узла: `#ad-summary` (подмена узла) и подмену СОДЕРЖИМОГО абзаца
    текста панели по постоянному id `sched-del-N-text` — корень панели с
    состоянием Alpine целью не становится (D-12(б)). Текст, приехавший
    внеполосно, и текст полной страницы после перезагрузки — ОДНА величина.
    """
    from tests.test_pages.test_confirm_delete_transport import _oob_node_ids

    day_names = templates.env.get_template(
        "schedules/includes/schedule_row.html"
    ).module.DAY_NAMES
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id, days=[0])

    response = await htmx_client.post(
        f"/schedules/{schedule.id}/edit",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("days_of_week", "0"),
                ("days_of_week", "1"),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
                ("return_to", "editor"),
            ]
        ),
        headers=FORM_HEADERS,
    )

    assert response.status_code == 200, response.status_code
    body = response.text
    oob_ids = _oob_node_ids(body)
    assert "ad-summary" in oob_ids, f"узла сводки нет среди внеполосных: {oob_ids}"
    assert f"#sched-del-{schedule.id}-text" in oob_ids, (
        f"узла текста панели нет среди внеполосных: {oob_ids}"
    )
    assert f'id="sched-del-{schedule.id}"' not in body, (
        "корень панели подтверждения стал целью либо приехал в теле"
    )

    panel_node = re.search(
        rf'<div hx-swap-oob="innerHTML:#sched-del-{schedule.id}-text">(.*?)</div>',
        body,
        re.S,
    )
    assert panel_node, body[-600:]
    oob_text = panel_node.group(1)
    assert f"{day_names[0]} {day_names[1]}" in oob_text, oob_text

    htmx_client.headers.pop("HX-Request")
    page = await htmx_client.get(f"/ads/{ad.id}/edit")
    assert page.status_code == 200
    page_text = re.search(
        rf'<p class="modal__text" id="sched-del-{schedule.id}-text">(.*?)</p>',
        page.text,
        re.S,
    )
    assert page_text, "у абзаца текста панели нет постоянного id"
    assert page_text.group(1) == oob_text, (
        f"внеполосный текст {oob_text!r} разошёлся с полной страницей "
        f"{page_text.group(1)!r}"
    )


@pytest.mark.asyncio
async def test_toggle_from_editor_returns_to_the_editor(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """SCH-05: маршрут переключения не меняется, меняется только место возврата."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[group.id]
    )

    response = await authed_client.post(
        f"/schedules/{schedule.id}/toggle",
        content=_form([("return_to", "editor")]),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].startswith(f"/ads/{ad.id}/edit")
    assert (await _reload(db_session, schedule.id)).is_active is False


def _hidden_fields_of_the_toggle_form(html: str, schedule_id: int) -> list[tuple[str, str]]:
    """Скрытые поля формы тумблера ИМЕННО этой карточки — из отрендеренной разметки.

    Поля берутся со страницы, а не собираются в тесте руками: собранный вручную
    набор прошёл бы и при разметке, которая этих полей не рисует, и связка
    «шаблон ↔ обработчик» осталась бы непроверенной.
    """
    block = re.search(
        rf'<form[^>]*action="/schedules/{schedule_id}/toggle"[^>]*>(.*?)</form>',
        html,
        re.DOTALL,
    )
    assert block, f"формы тумблера расписания {schedule_id} в разметке нет"
    return [
        (m.group("name"), m.group("value"))
        for m in re.finditer(
            r'<input[^>]*type="hidden"[^>]*name="(?P<name>[^"]+)"[^>]*value="(?P<value>[^"]*)"',
            block.group(1),
        )
    ]


@pytest.mark.asyncio
async def test_the_toggle_does_not_fold_or_unfold_the_schedule_card(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Тумблер меняет состояние расписания и НЕ трогает разворот карточек.

    Разворот — состояние СЕРВЕРНОЕ: его определяет единственный параметр адреса
    `sched`, и обработчик переключения перезаписывал его идентификатором нажатой
    карточки. Пользователь читал это как «тумблер нажал кнопку СВЕРНУТЬ /
    РАЗВЕРНУТЬ»: свёрнутая карточка от нажатия разворачивалась, а развёрнутая
    соседка схлопывалась.

    Тест сквозной — он проходит путь пользователя целиком: страница, форма из
    её разметки, POST, переход по адресу ответа. Утверждение про `is_active`
    обязательно: без него тест остался бы зелёным и при тумблере, переставшем
    работать вовсе.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)
    first = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[group.id]
    )
    second = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[group.id], times=["21:00"]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={second.id}")).text
    fields = _hidden_fields_of_the_toggle_form(html, first.id)

    response = await authed_client.post(
        f"/schedules/{first.id}/toggle",
        content=_form(fields),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )
    assert response.status_code == 302

    after = (await authed_client.get(response.headers["location"])).text
    assert f'action="/schedules/{first.id}/edit"' not in after, (
        "свёрнутая карточка РАЗВЕРНУЛАСЬ от нажатия собственного тумблера"
    )
    assert f'action="/schedules/{second.id}/edit"' in after, (
        "развёрнутая карточка СХЛОПНУЛАСЬ от нажатия тумблера соседней"
    )
    assert (await _reload(db_session, first.id)).is_active is False, (
        "тумблер перестал переключать расписание"
    )


@pytest.mark.asyncio
async def test_a_toggle_without_the_expansion_field_leaves_every_card_collapsed(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Нечего разворачивать — значит, после нажатия развёрнутых карточек нет.

    Форма браузера в этом состоянии именно такова: развёрнутых карточек не было,
    поле разворота не отрисовано. Адрес возврата обязан быть чистым — иначе
    тумблер РАЗВОРАЧИВАЛ БЫ свёрнутую карточку, что пользователь и сообщил.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[group.id]
    )

    response = await authed_client.post(
        f"/schedules/{schedule.id}/toggle",
        content=_form([("return_to", "editor")]),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"] == f"/ads/{ad.id}/edit", (
        "тумблер развернул карточку, которая была свёрнута"
    )
    assert (await _reload(db_session, schedule.id)).is_active is False


@pytest.mark.asyncio
async def test_a_malformed_expansion_field_is_dropped_instead_of_crashing(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Испорченное поле разворота отбрасывается, а переключение доводится до конца.

    Разметка — не точка принуждения: POST мимо браузера обязан получить тот же
    ответ, что и форма. Значение разворота — единственная величина, приходящая
    из формы в строку адреса, и непреобразуемое к целому в неё не попадает
    (T-mwo-01).
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[group.id]
    )

    response = await authed_client.post(
        f"/schedules/{schedule.id}/toggle",
        content=_form(
            [("return_to", "editor"), ("keep_sched", "1&sched=99#hack")]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302, "мусор в поле разворота уронил обработчик"
    assert response.headers["location"] == f"/ads/{ad.id}/edit"
    assert (await _reload(db_session, schedule.id)).is_active is False


# --- Фаза 11, план 11-03: тумблер расписания на слое ответа -------------------
#
# Тумблер в редакторе на htmx отвечает КАРТОЧКОЙ `#sched-N` (D-02), и раскрытие
# в ней берётся из скрытого поля разворота, а не из идентификатора нажатой
# карточки (D-12(а)). Путь без htmx остаётся прежним перенаправлением.

HTMX_FORM_HEADERS = {**FORM_HEADERS, "HX-Request": "true"}


@pytest.mark.asyncio
async def test_schedule_toggle_over_htmx_keeps_the_expanded_neighbour(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Раскрыта A, нажат тумблер B: во фрагменте B СВЁРНУТА, путь деградации — на A.

    Фрагмент несёт ровно карточку B: A на экране не трогается (цель подмены —
    `#sched-B`), и раскрытой она остаётся потому, что её не подменяют. Свёрнутость
    B утверждается отсутствием формы сохранения — её рисует только раскрытая
    карточка.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)
    first = await _seed_schedule(db_session, ad.id, account.id, group_ids=[group.id])
    second = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[group.id], times=["21:00"]
    )
    body = _form([("return_to", "editor"), ("keep_sched", str(first.id))])

    degraded = await authed_client.post(
        f"/schedules/{second.id}/toggle",
        content=body,
        headers=FORM_HEADERS,
        follow_redirects=False,
    )
    assert degraded.status_code == 302
    assert degraded.headers["location"] == (
        f"/ads/{ad.id}/edit?sched={first.id}#sched-{first.id}"
    )
    assert (await _reload(db_session, second.id)).is_active is False

    response = await authed_client.post(
        f"/schedules/{second.id}/toggle",
        content=body,
        headers=HTMX_FORM_HEADERS,
        follow_redirects=False,
    )
    assert response.status_code == 200, (
        f"тумблер на htmx ответил {response.status_code} вместо фрагмента карточки"
    )
    assert "<!DOCTYPE" not in response.text, "слою письма приехал целый документ"
    assert f'id="sched-{second.id}"' in response.text, "во фрагменте нет карточки B"
    assert f'id="sched-{first.id}"' not in response.text, (
        "фрагмент принёс соседнюю карточку — цель подмены одна"
    )
    assert f'action="/schedules/{second.id}/edit"' not in response.text, (
        "карточка B РАЗВЕРНУЛАСЬ от нажатия собственного тумблера"
    )
    assert (await _reload(db_session, second.id)).is_active is True


@pytest.mark.asyncio
async def test_a_blocked_resume_over_htmx_returns_the_unchanged_card(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Неполное выключенное расписание: фрагмент несёт СЕРВЕРНОЕ состояние.

    Браузер переключает флажок оптимистично; ответ, не несущий флажка без
    `checked`, оставил бы на экране «включено» при выключенной строке (D-11,
    D-13/D-16 Фазы 9).
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id, is_active=False)

    response = await authed_client.post(
        f"/schedules/{schedule.id}/toggle",
        content=_form([("return_to", "editor"), ("is_active", "1")]),
        headers=HTMX_FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200, (
        f"заблокированное возобновление на htmx ответило {response.status_code} "
        "вместо карточки"
    )
    toggle_input = re.search(
        rf'<input[^>]*id="sched-toggle-{schedule.id}"[^>]*>', response.text
    )
    assert toggle_input, "во фрагменте нет флажка тумблера карточки"
    assert "checked" not in toggle_input.group(0), (
        "флажок во фрагменте включён, а расписание выключено — ответ повторил "
        "оптимистичное состояние браузера"
    )
    assert (await _reload(db_session, schedule.id)).is_active is False


@pytest.mark.asyncio
async def test_delete_from_editor_returns_to_the_editor_and_removes_the_schedule(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)

    response = await authed_client.post(
        f"/schedules/{schedule.id}/delete",
        content=_form([("return_to", "editor")]),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].startswith(f"/ads/{ad.id}/edit")
    assert await _all_schedules(db_session) == []


@pytest.mark.asyncio
async def test_an_unreadable_body_leaves_the_schedule_in_place(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """WR-07: удаление не имеет права коммититься ДО разбора тела запроса.

    `await request.form()` — единственное место, где тело вообще разбирается, и
    оно МОЖЕТ поднять исключение: негодный `multipart`, обрыв тела, превышение
    лимита частей. Пока `commit()` стоял ВЫШЕ этого разбора, человек получал 500,
    А СТРОКИ УЖЕ НЕ БЫЛО — то есть отказ, неотличимый от «ничего не произошло»,
    при уже выполненной записи.

    ⚠️ ПРЕДМЕТ ПРАВИЛА — ПОРЯДОК «РАЗБОР ТЕЛА → ЗАПИСЬ», А НЕ КОД ОТВЕТА.
    `MultipartParseError` остаётся необработанной и доезжает до общего
    обработчика приложения: разбор тела — граница фреймворка, одна на все
    маршруты проекта, и чинить её в этом обработчике значило бы завести
    частное правило там, где нужно общее. Утверждается ровно то, что обработчик
    обязан гарантировать сам: НЕУДАВШИЙСЯ запрос НЕ УДАЛИЛ строку.

    Негодность тела здесь ЗАМЕРЕНА, а не предположена: `python_multipart`
    отвечает на это тело `MultipartParseError: Expected boundary character 45,
    got 103 at index 2`.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)
    schedule_id = schedule.id

    response = await authed_client.post(
        f"/schedules/{schedule_id}/delete",
        content=b"garbage-not-multipart",
        headers={"Content-Type": "multipart/form-data; boundary=BOUND"},
        follow_redirects=False,
    )

    assert response.status_code >= 400, (
        f"запрос с нечитаемым телом объявлен УСПЕШНЫМ ({response.status_code}) — "
        "тело негодно, и правило ниже проверяло бы не то, ради чего заведено"
    )

    db_session.expire_all()
    survivors = await _all_schedules(db_session)
    assert [row.id for row in survivors] == [schedule_id], (
        "запрос с нечитаемым телом УДАЛИЛ расписание: запись прошла раньше "
        "разбора тела, и человек получил отказ над уже исчезнувшей строкой"
    )


@pytest.mark.asyncio
async def test_return_value_never_reaches_the_redirect_verbatim(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """T-02-23: поле возврата — ПРИЗНАК происхождения, а не адрес.

    Значение подконтрольно отправителю. Подставленное в редирект как есть, оно
    даёт открытый редирект: страница входа увела бы пользователя на чужой домен
    сразу после успешной аутентификации.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("return_to", "https://evil.example/steal"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["location"]
    assert "evil.example" not in location, location
    assert location.startswith("/"), location


# --- D-08: неполное расписание сохраняется выключенным -------------------------


@pytest.mark.asyncio
async def test_schedule_without_groups_is_saved_disabled(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)

    await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("days_of_week", "1"),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].is_active is False
    assert created[0].next_run_at is None


@pytest.mark.asyncio
async def test_schedule_without_days_is_saved_disabled(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)

    await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("group_ids", str(group.id)),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].is_active is False
    assert created[0].next_run_at is None


@pytest.mark.asyncio
async def test_schedule_without_times_is_saved_disabled(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)

    await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("group_ids", str(group.id)),
                ("days_of_week", "3"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].is_active is False
    assert created[0].next_run_at is None


@pytest.mark.asyncio
async def test_schedule_without_account_is_saved_disabled(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Только что добавленная карточка не несёт аккаунта — и это законно.

    При нескольких аккаунтах ни один не выбран заранее, поэтому «+ РАСПИСАНИЕ»
    обязано создать расписание БЕЗ аккаунта. Отказ формы (422) на этом месте
    лишил бы пользователя единственного способа добавить расписание в редакторе.
    """
    ad = await _seed_ad(db_session, owner.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form([("ad_id", str(ad.id)), ("return_to", "editor")]),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].account_id is None
    assert created[0].is_active is False
    assert created[0].next_run_at is None


@pytest.mark.asyncio
async def test_changing_the_account_clears_the_previously_chosen_groups(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Расписание не может нести группы другого аккаунта.

    Сервер и раньше молча отбрасывал группы, не принадлежащие выбранному
    аккаунту, — но оставлял расписание АКТИВНЫМ с нулём групп: планировщик
    выбирал бы его к отправке и ничего не отправлял (Pitfall 8).
    """
    ad = await _seed_ad(db_session, owner.id)
    first = await _seed_account(db_session, owner.id)
    second = await _seed_account(db_session, owner.id, type_="wa")
    group_of_first = await _seed_group(db_session, owner.id, first.id, "Группа первого")
    schedule = await _seed_schedule(
        db_session, ad.id, first.id, group_ids=[group_of_first.id]
    )

    response = await authed_client.post(
        f"/schedules/{schedule.id}/edit",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(second.id)),
                ("group_ids", str(group_of_first.id)),
                ("days_of_week", "1"),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
                ("return_to", "editor"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    stored = await _reload(db_session, schedule.id)
    assert stored.account_id == second.id
    assert stored.group_ids == []
    assert stored.is_active is False
    assert stored.next_run_at is None


@pytest.mark.asyncio
async def test_complete_schedule_is_saved_active_with_a_next_run(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Парный позитивный тест: без него выключение проходило бы всегда."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("group_ids", str(group.id)),
                ("days_of_week", "0"),
                ("days_of_week", "1"),
                ("days_of_week", "2"),
                ("days_of_week", "3"),
                ("days_of_week", "4"),
                ("days_of_week", "5"),
                ("days_of_week", "6"),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
                ("return_to", "editor"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].group_ids == [group.id]
    assert created[0].is_active is True
    assert created[0].next_run_at is not None


@pytest.mark.asyncio
async def test_incomplete_schedule_cannot_be_switched_on(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-08: тумблер неполного расписания не включает его.

    Тумблер размечен недоступным, но разметка — не точка принуждения: прямой
    POST на маршрут переключения обязан получить отказ так же, как и клик.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[], is_active=False
    )

    response = await authed_client.post(
        f"/schedules/{schedule.id}/toggle", follow_redirects=False
    )

    assert response.status_code == 302
    stored = await _reload(db_session, schedule.id)
    assert stored.is_active is False
    assert stored.next_run_at is None


# --- Валидация клиентских значений (Pitfall 9, D-13) ---------------------------


@pytest.mark.asyncio
async def test_malformed_time_does_not_crash_and_is_dropped(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """T-02-24: значение времени не формата ЧЧ:ММ роняло вычисление запуска.

    `int(parts[0])` бросает ValueError, `parts[1]` — IndexError. Через браузер
    сюда приходит `input type="time"`, но POST можно послать мимо браузера, и
    сегодня это давало 500 вместо отказа валидации.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("group_ids", str(group.id)),
                ("days_of_week", "1"),
                ("times_of_day", "не-время"),
                ("times_of_day", "25:00"),
                ("times_of_day", "10:61"),
                ("times_of_day", "10"),
                ("times_of_day", "09:30"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code < 500, response.status_code
    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].times_of_day == ["09:30"]


@pytest.mark.asyncio
async def test_a_time_padded_with_spaces_is_stored_trimmed(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """WR-01: сохраняется ТО, ЧТО ПРОВЕРЕНО, а не то, что пришло.

    `_clean_times` сверял `v.strip()`, а в список кладёл `v`. Значение
    `" 09:00 "` проходило проверку и ложилось в `times_of_day` С ПРОБЕЛАМИ.

    ⚠️ ПОЧЕМУ ЭТО НЕ КОСМЕТИКА. Значение печатается в разметку редактора как
    есть — `<input class="time-pill__input" type="time" value=" 09:00 ">`, — а
    `type="time"` значение с пробелами НЕ ПРИНИМАЕТ: поле показывается ПУСТЫМ, и
    при следующем сохранении время молча теряется. `compute_next_run_at` при
    этом отрабатывает (`int(" 09")` пробелы терпит), поэтому расхождение не
    поднимает НИ ОДНОГО признака — оно наблюдаемо только здесь.

    Сверх того рождались два написания одного времени, которых `TIME_OF_DAY_RE`
    избегает требованием двух цифр часа: второе определение формата.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("group_ids", str(group.id)),
                ("days_of_week", "1"),
                ("times_of_day", " 09:00 "),
                ("times_of_day", "\t18:30"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code < 500, response.status_code
    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].times_of_day == ["09:00", "18:30"], (
        "сохранено НЕОБРЕЗАННОЕ значение — редактор покажет пустое поле, и "
        f"время потеряется при следующем сохранении: {created[0].times_of_day!r}"
    )


@pytest.mark.asyncio
async def test_non_numeric_group_and_day_values_do_not_crash(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """T-02-25: `int(g)` на списках идентификаторов падал на любой строке."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("group_ids", "не-число"),
                ("group_ids", str(group.id)),
                ("days_of_week", "понедельник"),
                ("days_of_week", "2"),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code < 500, response.status_code
    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].group_ids == [group.id]
    assert created[0].days_of_week == [2]


@pytest.mark.asyncio
async def test_out_of_range_day_values_are_dropped(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """День недели вне 0..6 не отправится никогда — он не должен и храниться."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)

    await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("days_of_week", "9"),
                ("days_of_week", "-1"),
                ("days_of_week", "4"),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    created = await _all_schedules(db_session)
    assert created[0].days_of_week == [4]


@pytest.mark.asyncio
async def test_malformed_time_on_update_does_not_crash(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Тот же отказ на маршруте изменения: обход одной ветки не помогает."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)

    response = await authed_client.post(
        f"/schedules/{schedule.id}/edit",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("days_of_week", "1"),
                ("times_of_day", "24:00"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code < 500, response.status_code
    stored = await _reload(db_session, schedule.id)
    assert stored.times_of_day == []
    assert stored.is_active is False


# --- Старый путь не тронут ----------------------------------------------------


# --- Секция расписаний в разметке редактора (Задача 3) ------------------------


FORM_OPEN_RE = re.compile(r"<form\b", re.I)
FORM_CLOSE_RE = re.compile(r"</form\s*>", re.I)


def _max_form_nesting(html: str) -> int:
    """Наибольшая глубина вложенности форм в разметке.

    Вложенную форму браузер молча ОТБРАСЫВАЕТ: симптом — неработающие кнопки на
    карточках расписаний, а не ошибка. Проверка идёт по отрендеренной выдаче, а
    не по файлу: форма могла бы приехать из макроса.
    """
    depth = 0
    peak = 0
    for match in re.finditer(r"<form\b|</form\s*>", html, re.I):
        if match.group(0).startswith("</"):
            depth = max(0, depth - 1)
        else:
            depth += 1
            peak = max(peak, depth)
    return peak


@pytest.mark.asyncio
async def test_editor_without_schedules_names_the_consequence(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Пустое состояние называет ПОСЛЕДСТВИЕ, а не только отсутствие."""
    ad = await _seed_ad(db_session, owner.id)
    await _seed_account(db_session, owner.id)

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert "Расписаний пока нет — объявление не будет отправляться" in html
    assert "+ ДОБАВИТЬ ПЕРВОЕ" in html


@pytest.mark.asyncio
async def test_editor_card_renders_data(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Карточка-макрос отрисовывает РЕАЛЬНЫЕ данные, а не пустоту.

    Импортированным макросам Jinja контекст вызывающего не передаёт: ошибка в
    имени параметра оставит страницу валидной, отдаст 200 и нарисует пустую
    карточку. Утверждение на статус ответа такую поломку не ловит.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id, "Уникальная группа карточки")
    schedule = await _seed_schedule(
        db_session,
        ad.id,
        account.id,
        group_ids=[group.id],
        days=[0, 2],
        times=["09:30", "18:45"],
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert f"Telegram #{account.id}" in html, "подпись аккаунта не отрисована"
    assert "09:30" in html and "18:45" in html, "времена не отрисованы"
    assert "Уникальная группа карточки" in html, "имя группы не отрисовано"
    assert f"/schedules/{schedule.id}/edit" in html
    assert f"/schedules/{schedule.id}/toggle" in html


@pytest.mark.asyncio
async def test_editor_markup_has_no_nested_forms(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Ни одна форма не открыта внутри другой — ни в одном состоянии секции."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[group.id]
    )

    for url in (
        "/ads/new",
        f"/ads/{ad.id}/edit",
        f"/ads/{ad.id}/edit?sched={schedule.id}",
    ):
        html = (await authed_client.get(url)).text
        assert _max_form_nesting(html) == 1, f"{url}: в разметке есть вложенные формы"


@pytest.mark.asyncio
async def test_schedule_delete_is_a_real_form(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Деградация без Alpine: удаление остаётся настоящей формой с POST."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert re.search(
        rf'<form[^>]*method="post"[^>]*action="/schedules/{schedule.id}/delete"'
        rf'|<form[^>]*action="/schedules/{schedule.id}/delete"[^>]*method="post"',
        html,
    ), "путь удаления расписания перестал быть настоящей формой"
    assert "confirm(" not in html
    assert "onsubmit" not in html


@pytest.mark.asyncio
async def test_selected_schedule_is_the_expanded_one(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Параметр выбранного расписания разворачивает ИМЕННО эту карточку.

    Развёрнута одновременно одна: при многих расписаниях иначе получилась бы
    стена одновременно открытых форм.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    first = await _seed_schedule(db_session, ad.id, account.id)
    second = await _seed_schedule(db_session, ad.id, account.id, times=["21:00"])

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={second.id}")).text

    assert f'action="/schedules/{second.id}/edit"' in html, (
        "выбранная карточка не развёрнута: формы сохранения в разметке нет"
    )
    assert f'action="/schedules/{first.id}/edit"' not in html, (
        "невыбранная карточка тоже развёрнута"
    )

    collapsed = (await authed_client.get(f"/ads/{ad.id}/edit")).text
    assert f'action="/schedules/{first.id}/edit"' not in collapsed
    assert f'action="/schedules/{second.id}/edit"' not in collapsed


@pytest.mark.asyncio
async def test_the_collapsed_cards_toggle_carries_the_expanded_card_id(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Тумблер СВЁРНУТОЙ карточки несёт ЧУЖОЙ идентификатор — развёрнутой.

    Утверждение о СВЯЗКЕ шаблона и обработчика: без него оба могли бы пройти
    свои проверки по отдельности при неработающей странице — обработчик читал бы
    поле, которого разметка не рисует.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    first = await _seed_schedule(db_session, ad.id, account.id)
    second = await _seed_schedule(db_session, ad.id, account.id, times=["21:00"])

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={second.id}")).text

    assert ("keep_sched", str(second.id)) in _hidden_fields_of_the_toggle_form(
        html, first.id
    ), "свёрнутая карточка не проносит через тумблер идентификатор развёрнутой"


@pytest.mark.asyncio
async def test_user_without_accounts_is_offered_to_connect_one(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Ни одного аккаунта — подсказка со ссылкой в раздел, а не пустая полоса."""
    ad = await _seed_ad(db_session, owner.id)

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert "Сначала подключите аккаунт мессенджера" in html
    assert "Без аккаунта расписание отправлять некуда" in html
    assert 'href="/accounts"' in html


def _toggle_markup(html: str, schedule_id: int) -> str:
    """Разметка тумблера карточки — узел `label.toggle` по его `for`.

    ⚠️ ПРИБОР СМЕНЁН ПЛАНОМ 11-03, И ЭТО НЕ ПРАВКА ПОД РЕАЛИЗАЦИЮ. Прежде
    разметка бралась срезом за ПЕРВЫМ вхождением адреса маршрута. Форма
    тумблера перешла на макрос-обёртку, и адрес печатается ДВАЖДЫ подряд —
    в `action` и в атрибуте отправки слоя письма, — поэтому срез попадал
    между ними и содержал одну строку `" hx-post="`. Узел берётся по
    идентификатору тумблера: его же ищет возврат фокуса (QUAL-06).
    """
    match = re.search(
        rf'<label class="toggle" for="sched-toggle-{schedule_id}"[^>]*>.*?</label>',
        html,
        re.S,
    )
    assert match, f"тумблера карточки {schedule_id} в разметке нет"
    return match.group(0)


@pytest.mark.asyncio
async def test_account_without_groups_says_so(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Аккаунт без групп — названная причина, а не пустой блок."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    # Выключенное: недоступен тумблер именно на ВОЗОБНОВЛЕНИИ неполного (D-08),
    # а паузу активного не блокируют ни сервер, ни соседний шаблон.
    schedule = await _seed_schedule(db_session, ad.id, account.id, is_active=False)

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert "У выбранного аккаунта нет подключённых групп" in html
    # Тумблер неполного ВЫКЛЮЧЕННОГО расписания недоступен (D-08)
    assert "disabled" in _toggle_markup(html, schedule.id)


@pytest.mark.asyncio
async def test_active_incomplete_schedule_can_still_be_paused_from_the_editor(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Пауза АКТИВНОГО не зависит от заполненности — тумблер доступен.

    Определение недоступности в карточке разъехалось с двумя другими носителями
    того же правила: `schedules/includes/schedule_row.html` и обработчик
    `app/pages/schedules.py` считают блокируемым только ВОЗОБНОВЛЕНИЕ
    неполного. Карточка отключала орган управления и в состоянии «активное И
    неполное», подпись при этом врала («Включить нельзя», когда пользователь
    хочет ВЫКЛЮЧИТЬ), а выключенный флажок браузер не отправляет и события
    `change` не порождает — пути поставить расписание на паузу из редактора не
    было вовсе.

    Состояние не теоретическое: удаление единственной группы вычищает
    идентификатор из `Schedule.group_ids`, не трогая `is_active`.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[], is_active=True
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    toggle_markup = _toggle_markup(html, schedule.id)
    assert "disabled" not in toggle_markup, (
        "активное неполное расписание нельзя поставить на паузу из редактора"
    )
    assert "Приостановить" in toggle_markup, (
        "подпись обязана называть действие, которое пользователь может сделать"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "count,expected",
    [(1, "1 расписание"), (3, "3 расписания"), (5, "5 расписаний")],
)
async def test_section_caption_is_declined(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
    count: int,
    expected: str,
):
    """«1 расписаний» — заметный дефект копирайтинга; подпись СКЛОНЯЕТСЯ."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    for _ in range(count):
        await _seed_schedule(db_session, ad.id, account.id)

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert expected in html, f"подпись секции не склонена для {count}"


@pytest.mark.asyncio
async def test_add_schedule_form_preselects_a_single_account(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Единственный аккаунт выбран заранее; при нескольких — ни один.

    Заставлять выбирать из одного варианта — лишний шаг; выбирать за
    пользователя из нескольких — решать за него, куда уйдёт рассылка.
    """
    ad = await _seed_ad(db_session, owner.id)
    only = await _seed_account(db_session, owner.id)

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text
    add_form = html[html.index('action="/schedules/new"'):]
    add_form = add_form[: add_form.index("</form>")]
    assert f'name="account_id" value="{only.id}"' in add_form

    await _seed_account(db_session, owner.id, type_="wa")
    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text
    add_form = html[html.index('action="/schedules/new"'):]
    add_form = add_form[: add_form.index("</form>")]
    assert 'name="account_id"' not in add_form


@pytest.mark.asyncio
async def test_editor_schedule_section_is_a_sibling_of_the_ad_form(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Секция расписаний стоит ПОСЛЕ закрытия формы объявления.

    Проверка позиционная, а не «нет вложенных форм»: последнее верно и тогда,
    когда секция уехала выше формы и потеряла свой порядок чтения на узкой
    ширине (D-14, порядок разметки — порядок чтения).
    """
    ad = await _seed_ad(db_session, owner.id)
    await _seed_account(db_session, owner.id)

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    ad_form_close = html.index("</form>", html.index('id="ad-form"'))
    section = html.index('action="/schedules/new"')
    assert ad_form_close < section, "секция расписаний оказалась внутри формы объявления"


@pytest.mark.asyncio
async def test_summary_list_keeps_working(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Обращение НЕ из редактора обслуживается тем же способом, что и раньше."""
    ad = await _seed_ad(db_session, owner.id, title="Расписание сводного списка")
    account = await _seed_account(db_session, owner.id)
    await _seed_schedule(db_session, ad.id, account.id)

    response = await authed_client.get("/schedules")
    assert response.status_code == 200
    assert "Расписание сводного списка" in response.text

    # Отдельной страницы создания расписания больше НЕТ (D-14, план 02-06).
    # До 02-06 здесь стояло `== 200` — утверждение о сосуществовании двух путей,
    # верное ровно между планами 02-05 и 02-06. Теперь утверждение обратное и не
    # менее строгое: страница снесена, мёртвого кода не осталось.
    #
    # Код именно 405, а не 404: `POST /schedules/new` остаётся — на него ходит
    # форма добавления из редактора, — поэтому путь в приложении существует, а
    # метод GET на нём больше не обслуживается.
    legacy_form = await authed_client.get("/schedules/new")
    assert legacy_form.status_code == 405


# --- D-07: выключенные группы в списке выбора редактора ------------------------
#
# С D-05 выключенная группа перестаёт получать рассылку. Выборка редактора брала
# только активные группы, и выбранная-но-выключенная группа ИСЧЕЗАЛА из карточки:
# пользователь не мог ни узнать, почему группа молчит, ни снять её выбор, а
# подпись «выбрано N из M» начинала врать (RESEARCH Pitfall 6).
#
# Правило ровно одно и о двух половинах: выключенная группа видна ТОЛЬКО если она
# уже выбрана в расписании ЭТОГО объявления; невыбранные выключенные список не
# захламляют.

# Строка списка выбора целиком: разбор строкой — тот же приём, что уже применяют
# этот файл и tests/test_pages/test_responsive_markup.py. Отдельной зависимости
# разбора HTML ради четырёх утверждений не заводится.
GROUP_ROW_RE = re.compile(r'<label class="group-pick__row".*?</label>', re.S)
GROUP_COUNTER_RE = re.compile(r"выбрано (\d+) из (\d+)")
OFF_MARK = "отключена"
# ВИДИМАЯ подпись, а не любое вхождение слова: то же слово стоит внутри
# пояснения («Группа отключена и пропускается при рассылке»), и счёт по голой
# подстроке мерил бы два вхождения на одну пометку.
OFF_MARK_CAPTION = ">отключена<"


def _group_rows(html: str) -> list[str]:
    return GROUP_ROW_RE.findall(html)


def _row_of(html: str, group_id: int) -> str:
    """Строка выбора конкретной группы. Отсутствие — падение, а не пустая строка."""
    for row in _group_rows(html):
        if f'value="{group_id}"' in row:
            return row
    raise AssertionError(f"строки группы {group_id} в списке выбора нет")


@pytest.mark.asyncio
async def test_disabled_group_chosen_in_the_schedule_stays_visible(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Выключенная группа, уже выбранная в расписании, из карточки не исчезает."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    off = await _seed_group(
        db_session, owner.id, account.id, "Выключенная выбранная группа", is_active=False
    )
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[off.id]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert "Выключенная выбранная группа" in html, (
        "выбранная выключенная группа пропала из списка выбора"
    )
    assert "checked" in _row_of(html, off.id), "выбор с группы снялся сам"


@pytest.mark.asyncio
async def test_disabled_group_not_chosen_is_absent_from_the_picker(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Невыбранная выключенная группа список выбора не захламляет.

    Парный тест к предыдущему: без него выборка могла бы отдавать ВСЕ группы
    подряд и оба утверждения о видимости проходили бы разом.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    active = await _seed_group(db_session, owner.id, account.id, "Активная группа списка")
    await _seed_group(
        db_session, owner.id, account.id, "Выключенная невыбранная группа", is_active=False
    )
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[active.id]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert "Активная группа списка" in html
    assert "Выключенная невыбранная группа" not in html, (
        "невыбранная выключенная группа попала в список выбора"
    )


@pytest.mark.asyncio
async def test_active_group_is_present_regardless_of_schedules(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Активная группа видна и тогда, когда ни в одном расписании не выбрана."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    active = await _seed_group(db_session, owner.id, account.id, "Активная невыбранная")
    schedule = await _seed_schedule(db_session, ad.id, account.id, group_ids=[])

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert "Активная невыбранная" in html
    assert "checked" not in _row_of(html, active.id)


@pytest.mark.asyncio
async def test_disabled_group_chosen_in_another_ad_is_absent_here(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Множество выбранных строится из расписаний ИМЕННО ЭТОГО объявления.

    Иначе выключенная группа, выбранная где-то в другом объявлении, всплывала бы
    в списке выбора всех объявлений сразу.
    """
    ad = await _seed_ad(db_session, owner.id)
    other_ad = await _seed_ad(db_session, owner.id, title="Второе объявление")
    account = await _seed_account(db_session, owner.id)
    off = await _seed_group(
        db_session, owner.id, account.id, "Выключенная чужого объявления", is_active=False
    )
    await _seed_schedule(db_session, other_ad.id, account.id, group_ids=[off.id])
    schedule = await _seed_schedule(db_session, ad.id, account.id, group_ids=[])

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert "Выключенная чужого объявления" not in html


@pytest.mark.asyncio
async def test_group_of_another_user_never_reaches_the_editor(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """T-03-11: расширение выборки на выключенные не снимает скоуп по владельцу.

    Идентификатор чужой группы подставлен в СВОЁ расписание — то есть клиентское
    значение прошло весь путь до множества выбранных. Выборка обязана остаться
    ограниченной владельцем: чужое имя в карточку не попадает.
    """
    stranger = await _stranger(db_session)
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    foreign = await _seed_group(
        db_session, stranger.id, account.id, "Группа постороннего", is_active=False
    )
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[foreign.id]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert "Группа постороннего" not in html, "чужая группа попала в список выбора"


@pytest.mark.asyncio
async def test_editor_without_disabled_selections_renders_the_same_group_set(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Обычный случай — нулевой диф: набор строк ровно тот же, что и до правки."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    first = await _seed_group(db_session, owner.id, account.id, "Первая активная")
    second = await _seed_group(db_session, owner.id, account.id, "Вторая активная")
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[first.id]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    rows = _group_rows(html)
    assert len(rows) == 2, "набор строк списка выбора изменился в обычном случае"
    assert "Первая активная" in html and "Вторая активная" in html
    assert OFF_MARK not in html, "пометка появилась там, где выключенных групп нет"
    assert "checked" in _row_of(html, first.id)
    assert "checked" not in _row_of(html, second.id)


# --- D-07: пометка «отключена» и согласованный счётчик -------------------------


@pytest.mark.asyncio
async def test_disabled_chosen_row_is_marked_as_off(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Пользователь видит ПРИЧИНУ молчания группы прямо в строке выбора.

    Без пометки выключенная группа выглядит в карточке ровно как работающая, и
    единственным наблюдаемым следствием D-05 остаётся отсутствие отправок.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    off = await _seed_group(
        db_session, owner.id, account.id, "Помеченная выключенная", is_active=False
    )
    active = await _seed_group(db_session, owner.id, account.id, "Обычная активная")
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[off.id, active.id]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    off_row = _row_of(html, off.id)
    assert off_row.count(OFF_MARK_CAPTION) == 1, "пометки нет или она задвоена"
    assert "Группа отключена и пропускается при рассылке" in off_row, (
        "у пометки нет пояснения"
    )
    assert OFF_MARK not in _row_of(html, active.id), (
        "активная группа помечена отключённой"
    )


@pytest.mark.asyncio
async def test_disabled_chosen_checkbox_stays_operable(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Снять выбор с выключенной группы обязано быть возможно.

    Недоступный флажок запер бы группу в расписании навсегда: убрать её было бы
    нечем, а отправок она уже не получает.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    off = await _seed_group(
        db_session, owner.id, account.id, "Выключенная снимаемая", is_active=False
    )
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[off.id]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    off_row = _row_of(html, off.id)
    assert "checked" in off_row
    assert "disabled" not in off_row, "флажок выключенной группы стал недоступен"

    # Разметка — не точка принуждения: снятие обязано доехать до хранилища.
    await authed_client.post(
        f"/schedules/{schedule.id}/edit",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("days_of_week", "1"),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
                ("return_to", "editor"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert (await _reload(db_session, schedule.id)).group_ids == []


@pytest.mark.asyncio
async def test_group_counter_agrees_with_the_rendered_rows(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """«выбрано N из M» считает ВИДИМЫЙ набор, а не хранимый список.

    Пока выключенные-выбранные группы выпадали из выборки, знаменатель считал
    одно, а числитель — другое, и подпись противоречила списку перед глазами
    (RESEARCH Pitfall 6).
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    off = await _seed_group(
        db_session, owner.id, account.id, "Счётная выключенная", is_active=False
    )
    chosen_active = await _seed_group(
        db_session, owner.id, account.id, "Счётная выбранная"
    )
    await _seed_group(db_session, owner.id, account.id, "Счётная невыбранная")
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[off.id, chosen_active.id]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    rows = _group_rows(html)
    counter = GROUP_COUNTER_RE.search(html)
    assert counter is not None, "подписи «выбрано N из M» в карточке нет"
    chosen_shown = int(counter.group(1))
    total_shown = int(counter.group(2))

    assert total_shown == len(rows) == 3, "знаменатель разошёлся с видимым списком"
    assert chosen_shown == sum("checked" in row for row in rows) == 2, (
        "числитель разошёлся с отмеченными строками"
    )


# --- Фаза 10, план 10-01: единственный ФРАГМЕНТНЫЙ путь фазы ------------------
#
# ПОЧЕМУ ЭТОТ МАРШРУТ И ТОЛЬКО ОН (D-09). Из восьми обработчиков за панелями
# подтверждения фрагментом отвечает РОВНО ОДИН — удаление расписания из
# редактора объявления. Прокрутки в редакторе нет, `id="sched-{id}"` карточки и
# ключ панели `sched-del-{id}` собраны из ПЕРВИЧНОГО КЛЮЧА, а не из позиции
# строки, — сдвигаться нечему. Семь остальных уходят в ветку `HX-Location`, и
# основание у каждого измерено, а не предположено (D-06, D-08).
#
# ⚠️ ПАРА «БЕЗ ЗАГОЛОВКА → 302 / С ЗАГОЛОВКОМ → ФРАГМЕНТ» — НЕСУЩАЯ ФОРМА, А НЕ
# ДУБЛИРОВАНИЕ. Вторая половина утверждает ОТСУТСТВИЕ ДОКУМЕНТА в теле
# (`"<!DOCTYPE" not in response.text`): фикстура `htmx_client` идёт
# `follow_redirects=True`, поэтому обработчик, забывший путь письма и ответивший
# редиректом, приехал бы к тесту кодом 200 и телом ЧУЖОЙ СТРАНИЦЫ — и без этой
# половины тест позеленел бы на нём (GATE-01, D-16 Фазы 8).


def _editor_delete_body(ad: Ad) -> str:
    """Тело, которое шлют ОБЕ формы пути удаления расписания из редактора.

    ⚠️ СОБИРАЕТСЯ ЗДЕСЬ ОДИН РАЗ И НАМЕРЕННО: тест, пославший НЕ ТО, что шлёт
    разметка, проверяет маршрут, которым не идёт ни один пользователь. Оба поля
    — признак возврата и контекст экрана — стоят в обеих формах карточки
    расписания (`ads/includes/sched_card.html`); равенство наборов держит
    правило `test_both_editor_delete_forms_post_the_same_field_names`.
    """
    return _form([("return_to", "editor"), ("ad_id", str(ad.id))])


def _oob_top_level_tags(body: str) -> list[str]:
    """Открывающие теги ВЕРХНЕГО УРОВНЯ тела фрагментного ответа.

    Разбор нарочно грубый — по началу строки: тело фрагментного ответа обязано
    быть плоским (`allowNestedOobSwaps: false` в блоке конфигурации), и
    разборщик, умеющий во вложенность, скрыл бы ровно тот отказ, ради которого
    правило существует.
    """
    return [
        line for line in body.splitlines() if line.startswith("<") and "id=" in line
    ]


@pytest.mark.asyncio
async def test_editor_delete_degrades_without_htmx(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Путь деградации не тронут: без заголовка htmx — прежний 302 на прежний адрес.

    Перевод обработчика на слой ответа обязан оставить человека без JavaScript
    ровно там, где он был: подтверждение остаётся настоящей формой POST, а ответ
    — перенаправлением в редактор объявления.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)
    await _seed_schedule(db_session, ad.id, account.id)

    response = await authed_client.post(
        f"/schedules/{schedule.id}/delete",
        content=_editor_delete_body(ad),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"] == f"/ads/{ad.id}/edit"


@pytest.mark.asyncio
async def test_editor_delete_returns_oob_nodes(
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Ответ htmx-пути — ФРАГМЕНТ из трёх внеполосных узлов, а не документ.

    ⚠️ УЗЛОВ СТАЛО ЧЕТЫРЕ, И СТРОКА ВЫШЕ ОСТАВЛЕНА ДОСЛОВНО, А НЕ ВЫЧЕРКНУТА
    (идиома D-30/D-32). Ошибкой она не была — она верна для дерева, на котором
    писалась. ИСТОЧНИК РАСХОЖДЕНИЯ: план 10-50 добавил ЧЕТВЁРТЫЙ узел — сводку
    объявления `#ad-summary` (гэп `G-10-6`, обход `walkthrough_3` от
    2026-09-11).

    ⚠️ УЗЛОВ СНЯТИЯ ПО-ПРЕЖНЕМУ ДВА, И ЧЕТВЁРТЫЙ УЗЕЛ ИХ ЧИСЛА НЕ СДВИНУЛ —
    это утверждается ПРЯМО, а не выводится читателем из того, что правило
    зелено. Снятие есть форма подмены (`hx-swap-oob="delete"`), и узлов этой
    формы ровно два: карточка удалённого расписания и осиротевшая панель
    подтверждения. Сводка приезжает подменой УЗЛА, а не снятием.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)
    await _seed_schedule(db_session, ad.id, account.id)

    response = await htmx_client.post(
        f"/schedules/{schedule.id}/delete",
        content=_editor_delete_body(ad),
        headers=FORM_HEADERS,
    )

    assert response.status_code == 200
    assert "<!DOCTYPE" not in response.text, (
        "обработчик ответил документом — значит слой письма его не увидел и "
        "фикстура прошла по редиректу"
    )
    body = response.text
    assert f'id="sched-{schedule.id}"' in body, "узла снятия карточки в ответе нет"
    assert f'id="sched-del-{schedule.id}"' in body, "узла снятия панели в ответе нет"
    assert 'hx-swap-oob="innerHTML:#sched-count"' in body, (
        "линейка счётчика не приезжает подменой СОДЕРЖИМОГО долгоживущей области"
    )
    assert f'id="{AD_SUMMARY_NODE_ID}"' in body, (
        "узла сводки объявления в ответе нет — линейка списка и сводка "
        "предпросмотра снова разойдутся до следующей полной загрузки (G-10-6)"
    )
    removals = body.count('hx-swap-oob="delete"')
    assert removals == 2, (
        f"узлов снятия в ответе {removals}, ожидалось два (карточка и "
        f"осиротевшая панель): {body!r}"
    )
    nodes = _oob_nodes(body)
    assert len(nodes) == 4, (
        f"внеполосных узлов в ответе {len(nodes)} ({[n.identifier for n in nodes]}), "
        f"ожидалось четыре: два снятия, линейка счётчика и сводка объявления: "
        f"{body!r}"
    )
    assert [node.depth for node in nodes] == [0, 0, 0, 0], (
        f"не все узлы ответа — прямые дети тела: "
        f"{[(n.identifier, n.depth) for n in nodes]}. Вложенному узлу рантайм "
        f"МОЛЧА снимает признак внеполосной подмены "
        f"(`allowNestedOobSwaps: false`)"
    )


@pytest.mark.asyncio
async def test_the_orphaned_panel_is_removed_by_its_own_oob_node(
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Панель снимает СОБСТВЕННЫЙ узел, а не узел карточки (критерий 2 фазы).

    Панель подтверждения сознательно стоит СНАРУЖИ удаляемой карточки (T-11-04):
    внутри неё она стала бы её блоком и после первой же подмены задвоилась бы.
    Снаружи она вместе с карточкой и НЕ УЕЗЖАЕТ — без отдельного узла снятия
    после N удалений в документе копятся N узлов `role="dialog"`, каждый с живой
    ловушкой фокуса и живым обработчиком Escape, и признака отказа нет ни
    одного: ни в консоли, ни в статусе, ни в теле.

    Правило существует потому, что критерий 2 фазы — про ВТОРОЙ УЗЕЛ, а не про
    факт наличия ответа: тест на присутствие тела зеленел бы и без него.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)
    await _seed_schedule(db_session, ad.id, account.id)

    response = await htmx_client.post(
        f"/schedules/{schedule.id}/delete",
        content=_editor_delete_body(ad),
        headers=FORM_HEADERS,
    )

    tags = _oob_top_level_tags(response.text)
    card = [tag for tag in tags if f'id="sched-{schedule.id}"' in tag]
    panel = [tag for tag in tags if f'id="sched-del-{schedule.id}"' in tag]

    assert len(card) == 1, f"узел снятия карточки не один: {card}"
    assert len(panel) == 1, f"узел снятия панели не один: {panel}"
    assert card[0] != panel[0], (
        "снятие карточки и снятие панели оказались одним узлом — осиротевшая "
        "панель осталась бы в документе"
    )
    for tag in (card[0], panel[0]):
        assert 'hx-swap-oob="delete"' in tag, (
            f"узел верхнего уровня не несёт признака снятия: {tag!r}"
        )


@pytest.mark.asyncio
async def test_the_last_schedule_goes_to_location(
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Опустевший редактор закрывается ПЕРЕХОДОМ, а не второй отрисовкой (D-04).

    Второго экземпляра пустого состояния во фрагменте не заводится: ветка
    «расписаний пока нет» живёт в `ads/form.html` в ОДНОМ экземпляре, и второй
    её отрисовкой она разошлась бы с первой молча.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)

    response = await htmx_client.post(
        f"/schedules/{schedule.id}/delete",
        content=_editor_delete_body(ad),
        headers=FORM_HEADERS,
    )

    assert response.status_code == 204
    assert response.headers["HX-Location"] == f"/ads/{ad.id}/edit"
    assert response.text == "", "у ответа 204 тела нет по определению"
    assert await _all_schedules(db_session) == []


@pytest.mark.asyncio
async def test_repeated_editor_delete_is_harmless(
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Повтор БЕЗВРЕДЕН и НЕОТЛИЧИМ — и это два разных утверждения.

    Безвредность: единица записи — ОДИН commit одной строки под `WHERE` со
    связью `Ad.user_id`; второй запрос второй записи не создаёт и не удаляет
    ничего сверх.
    ⚠️ `hx-disabled-elt` СЕРВЕРНОЙ ЗАЩИТОЙ НЕ ЯВЛЯЕТСЯ и таковой здесь не
    объявляется: он блокирует кнопку в документе, а не маршрут на сервере. Два
    одновременных подтверждения дают одно удаление и один безвредный холостой
    путь, а не две записи.

    Неотличимость: тело собирается из `schedule_id` ПУТИ, а не из найденной
    строки, и ветви по факту удаления в шаблоне ответа нет. Иначе НАЛИЧИЕ узла
    стало бы признаком того, что удаление состоялось, и карту чужих
    идентификаторов можно было бы составить перебором.

    ⚠️ ЦЕНА НЕОТЛИЧИМОСТИ НАЗЫВАЕТСЯ ЧИСЛОМ, А НЕ СЛОВОМ «МОЛЧА»: холостой путь
    шлёт ДВА узла, чьих целей в документе нет, то есть ДВЕ строки
    `htmx:oobErrorNoTarget` в консоли на запрос (измерено Фазой 9 по
    вендоренному рантайму 2.0.10). Признак «200 и чистая консоль» на этом пути
    теряется; остаток наследуется перечнем `OOB_TARGET_EXCEPTIONS` с назначенной
    Фазой 15.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)
    survivor = await _seed_schedule(db_session, ad.id, account.id)

    body = _editor_delete_body(ad)
    first = await htmx_client.post(
        f"/schedules/{schedule.id}/delete", content=body, headers=FORM_HEADERS
    )
    after_first = await _all_schedules(db_session)

    second = await htmx_client.post(
        f"/schedules/{schedule.id}/delete", content=body, headers=FORM_HEADERS
    )
    after_second = await _all_schedules(db_session)

    assert second.status_code == first.status_code
    assert second.text == first.text, (
        "повторный ответ отличим от первого — по нему видно, состоялось ли "
        "удаление, и чужие идентификаторы перебираются по этому различию"
    )
    assert [s.id for s in after_first] == [survivor.id]
    assert [s.id for s in after_second] == [survivor.id], (
        "повтор тронул строки: единица записи перестала быть одним commit-ом"
    )


@pytest.mark.asyncio
async def test_editor_delete_does_not_trust_the_schedule_of_another_owner(
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Чужое расписание НЕ удаляется, и ответ на него неотличим от несуществующего.

    Неотличимость проверяется СРАВНЕНИЕМ ДВУХ ОТВЕТОВ, а не глазами: чужой
    идентификатор и заведомо несуществующий обязаны давать один и тот же ответ,
    иначе перебор по адресу составил бы карту занятых идентификаторов, не
    получив ни одной строки (T-10-01, T-10-07).
    """
    stranger = await _stranger(db_session)
    foreign_ad = await _seed_ad(db_session, stranger.id, "Чужое объявление")
    foreign_account = await _seed_account(db_session, stranger.id)
    foreign = await _seed_schedule(db_session, foreign_ad.id, foreign_account.id)

    body = _form([("return_to", "editor")])
    on_foreign = await htmx_client.post(
        f"/schedules/{foreign.id}/delete", content=body, headers=FORM_HEADERS
    )
    on_missing = await htmx_client.post(
        "/schedules/98765/delete", content=body, headers=FORM_HEADERS
    )

    assert [s.id for s in await _all_schedules(db_session)] == [foreign.id], (
        "чужая строка расписания удалена — тройной скоуп выборки перестал "
        "ограничивать её владельцем"
    )
    assert on_foreign.status_code == on_missing.status_code
    assert on_foreign.text == on_missing.text
    assert on_foreign.headers.get("HX-Location") == on_missing.headers.get(
        "HX-Location"
    ), "чужой идентификатор отличим от несуществующего по адресу приземления"


# --- Фаза 10, план 10-01, задача 3: ветка деградации и неотличимость ----------
#
# ⚠️ ПРАВИЛА НИЖЕ УТВЕРЖДАЮТ ПОВЕДЕНИЕ, А НЕ ВХОЖДЕНИЕ СТРОКИ, и это следствие
# измерения, а не вкуса. Ревизия Фазы 9 нашла ДВА расхождения (DIV-09-01 и
# DIV-09-02) ровно там, где машинные правила были зелены: разметочное правило
# зеленеет на присутствии подстроки, которую соседний путь не исполняет.

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"
SCHED_CARD_TEMPLATE = "ads/includes/sched_card.html"
SCHED_DELETE_RESPONSE_TEMPLATE = "ads/partials/sched_delete_response.html"

HIDDEN_FIELD_RE = re.compile(
    r'<input[^>]*type="hidden"[^>]*name="([^"]+)"', re.S
)
FORM_TAG_RE = re.compile(r"<form\b[^>]*>", re.S)

# Число форм-ТРИГГЕРОВ подтверждения в дереве. Значение поставлено ПРОГОНОМ, а не
# выведено: обход `x-on:submit.prevent` по всем шаблонам дал 18 — ровно столько
# же, сколько мест подтверждения насчитывает инвентарь панели (`MODAL_PLACES`).
#
# ⚠️ КОНСТАНТА ЗАВЕДЕНА ПРОТИВ ВАКУУМА, А НЕ ДЛЯ ОТЧЁТНОСТИ. Правило ниже
# утверждает ОТСУТСТВИЕ признака отправки на этих формах; разборщик, вернувший
# пустое множество, дал бы зелёный цвет, посимвольно совпадающий с зелёным
# цветом соблюдённого правила.
TRIGGER_FORMS_DECLARED = 18


def _template_text(rel: str) -> str:
    return (TEMPLATES_DIR / rel).read_text(encoding="utf-8")


def _all_template_sources() -> list[tuple[str, str]]:
    return [
        (path.relative_to(TEMPLATES_DIR).as_posix(), path.read_text(encoding="utf-8"))
        for path in sorted(TEMPLATES_DIR.rglob("*.html"))
    ]


def _delete_trigger_form(source: str) -> str:
    """Форма-ТРИГГЕР удаления расписания целиком — от открывающего тега до конца."""
    start = source.index('<form method="post" action="/schedules/{{ s.id }}/delete"')
    return source[start : source.index("</form>", start)]


def _delete_panel_slot(source: str) -> str:
    """Слот скрытых полей БЛОЧНОГО вызова панели подтверждения удаления."""
    start = source.index("{% call modal(id='sched-del-")
    return source[start : source.index("{% endcall %}", start)]


@pytest.mark.asyncio
async def test_both_editor_delete_forms_post_the_same_field_names():
    """Обе формы пути удаления шлют ОДИН И ТОТ ЖЕ набор имён полей.

    Правило существует потому, что ровно этот разъезд Фаза 9 поймала
    расхождением WR-03: поле несла только форма панели, и путь БЕЗ Alpine
    приезжал на сервер без него — обработчик считал ветку по другому состоянию,
    чем видел перед собой человек. Отказ обязан называть разошедшиеся имена, а
    не только факт расхождения: «наборы не равны» не говорит, какой путь чего
    лишился.
    """
    source = _template_text(SCHED_CARD_TEMPLATE)
    trigger = set(HIDDEN_FIELD_RE.findall(_delete_trigger_form(source)))
    panel = set(HIDDEN_FIELD_RE.findall(_delete_panel_slot(source)))

    assert trigger, "в форме-триггере удаления не нашлось ни одного скрытого поля"
    assert panel, "в слоте панели подтверждения не нашлось ни одного скрытого поля"
    assert trigger == panel, (
        "наборы полей двух форм пути удаления разошлись — путь деградации "
        "приедет на сервер с другим состоянием, чем путь htmx: "
        f"только в триггере {sorted(trigger - panel)}; "
        f"только в панели {sorted(panel - trigger)}"
    )


def test_the_trigger_form_never_carries_the_htmx_post():
    """Ни одна форма-ТРИГГЕР в дереве не несёт признака отправки htmx (D-03).

    Все места диспетчеризации остаются ЧИСТЫМ путём деградации: без Alpine форма
    уходит обычным POST-ом, с Alpine — открывает панель. Признак отправки живёт
    ТОЛЬКО на форме панели подтверждения, и это граница, а не полумера: триггер,
    получивший его, слал бы запрос ВМЕСТО открытия панели — то есть выполнял бы
    необратимое действие без подтверждения.
    """
    triggers: list[tuple[str, str]] = []
    for rel, source in _all_template_sources():
        for tag in FORM_TAG_RE.findall(source):
            if "x-on:submit.prevent" in tag:
                triggers.append((rel, tag))

    assert len(triggers) == TRIGGER_FORMS_DECLARED, (
        f"форм-триггеров подтверждения найдено {len(triggers)}, объявлено "
        f"{TRIGGER_FORMS_DECLARED} — место диспетчеризации молча исчезло или "
        f"появилось незаявленное: {sorted(rel for rel, _ in triggers)}"
    )

    carrying = [(rel, tag) for rel, tag in triggers if "hx-post" in tag]
    assert not carrying, (
        "форма-триггер несёт признак отправки htmx — подтверждённое действие "
        "ушло бы на сервер ВМЕСТО открытия панели подтверждения: "
        + "; ".join(f"{rel} -> {tag!r}" for rel, tag in carrying)
    )


@pytest.mark.asyncio
async def test_the_editor_delete_address_is_the_same_on_both_transports(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Адрес приземления ПОСИМВОЛЬНО один и тот же на обоих транспортах.

    Он же уезжает перенаправлением человеку без JavaScript, он же — заголовком
    перехода. Два независимо собранных адреса разошлись бы МОЛЧА, и путь
    деградации уводил бы на сводный список там, где путь htmx остаётся в
    редакторе. Тело формы в обоих запросах одно — иначе сравнивались бы два
    разных вопроса.

    ⚠️ ФИКСТУРА `htmx_client` ЗДЕСЬ НЕ ЗАПРАШИВАЕТСЯ, И ЭТО ВЫНУЖДЕННО, А НЕ
    НЕБРЕЖНОСТЬ. Она возвращает ТОТ ЖЕ объект клиента и ставит признак htmx на
    НЕГО — свойство несущее, оно и позволяет складывать её с фикстурами
    аутентификации. Но у пары «оба транспорта В ОДНОМ ТЕСТЕ» цена его обратная:
    запрошенная рядом, фикстура пометила бы и запрос, который обязан прийти БЕЗ
    признака, и половина деградации молча превратилась бы во вторую половину
    htmx. Поймано прогоном: запрос без JavaScript вернул 200 вместо 302.
    Поэтому признак ставится ЗДЕСЬ и ровно на один запрос из двух.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    first = await _seed_schedule(db_session, ad.id, account.id)
    second = await _seed_schedule(db_session, ad.id, account.id)
    body = _editor_delete_body(ad)

    degraded = await authed_client.post(
        f"/schedules/{first.id}/delete",
        content=body,
        headers=FORM_HEADERS,
        follow_redirects=False,
    )
    over_htmx = await authed_client.post(
        f"/schedules/{second.id}/delete",
        content=body,
        headers={**FORM_HEADERS, "HX-Request": "true"},
    )

    assert degraded.status_code == 302
    assert over_htmx.status_code == 204
    assert degraded.headers["location"] == over_htmx.headers["HX-Location"], (
        "адрес приземления разошёлся между транспортами: без JavaScript "
        f"{degraded.headers['location']!r}, через htmx "
        f"{over_htmx.headers['HX-Location']!r}"
    )


def test_control_negative_a_conditional_removal_node_reddens_the_gate():
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ безусловности узлов снятия.

    Несущее правило (`test_editor_delete_returns_oob_nodes`) утверждает, что в
    ответе есть ОБА узла снятия. Зелёным оно обязано быть потому, что узлы
    БЕЗУСЛОВНЫ, а не потому, что на счастливом пути условие сложилось удачно.
    Контроль подставляет в прочитанный исходник ветвь по факту удаления и
    требует, чтобы правило на подделке ПОКРАСНЕЛО.

    ⚠️ ДВОЙНОЙ ПРЕДОХРАНИТЕЛЬ (образец — `_xdata_with_dead_teardown`): контроль
    отдельно доказывает, что подстановка ЧТО-ТО изменила и ИМЕННО ТО. Иначе
    неудавшаяся замена дала бы «правило покраснело» на нетронутом исходнике —
    или, того хуже, зелёный цвет, неотличимый от соблюдения.
    """
    source = _template_text(SCHED_DELETE_RESPONSE_TEMPLATE)
    panel_node = '<div id="sched-del-{{ schedule_id }}" hx-swap-oob="delete"></div>'

    assert source.count(panel_node) == 1, (
        "образец узла снятия панели встречается в источнике не один раз — "
        "подстановка контроля перестала быть однозначной"
    )
    forged = source.replace(
        panel_node, "{% if deleted %}" + panel_node + "{% endif %}"
    )
    assert forged != source, "подстановка контроля ничего не изменила"

    honest = templates.env.from_string(source).render(schedule_id=7, schedules_count=2)
    faked = templates.env.from_string(forged).render(
        schedule_id=7, schedules_count=2, deleted=False
    )

    # Первый предохранитель: несущее свойство на НАСТОЯЩЕМ источнике держится.
    assert honest.count('hx-swap-oob="delete"') == 2, (
        "на настоящем источнике узлов снятия не два — контроль сравнивал бы "
        f"подделку с уже сломанным образцом: {honest!r}"
    )
    # Второй: подделка снимает ИМЕННО узел панели, а не что-нибудь ещё.
    assert 'id="sched-del-7"' not in faked, "подстановка не убрала узел панели"
    assert 'id="sched-7"' in faked, (
        "подстановка задела узел снятия карточки — контроль доказывал бы не то "
        "свойство, которое объявил"
    )
    assert faked.count('hx-swap-oob="delete"') == 1, (
        "правило присутствия обоих узлов НЕ ПОКРАСНЕЛО на подделке: ветвь по "
        "факту удаления прошла бы в дерево незамеченной, и НАЛИЧИЕ узла стало "
        "бы признаком того, что удаление состоялось"
    )


# =============================================================================
# ГРАНИЦА ВЕЛИЧИНЫ ИДЕНТИФИКАТОРА — ПЯТЬ ВХОДОВ ФАЙЛА ОДНИМ ОТОБРАЖЕНИЕМ
# (CR-01 унаследованный, CR-02 новый; отчёт верификации Фазы 10, третий круг)
# =============================================================================
#
# ПРЕДМЕТ — ТОТ ЖЕ ИНВАРИАНТ, ЧТО У T-02-24 / T-02-25, НА ОСИ ВЕЛИЧИНЫ, А НЕ
# ТИПА: «прямой POST мимо браузера обязан давать отказ валидации, а не 500»
# (шапка этого модуля). Коэрция `int` ограничивает ТИП и пропускает число любой
# величины; значение вне диапазона колонки доезжает до драйвера БД и роняет
# запрос (`OverflowError` на SQLite суиты, `DataError` вне int32 на PostgreSQL
# боевого стенда) — то есть даёт ровно ту пятисотку, которую модуль себе
# запретил.
#
# ⚠️ ПЕРЕЧНЕМ, А НЕ ПЯТЬЮ ПРАВИЛАМИ, И ЭТО НЕСУЩЕЕ РЕШЕНИЕ. Правка, закрывшая
# один вход из пяти, уже была принята за закрытие блокера — дважды. Правило с
# ранним отказом показало бы одну несогласную строку из пяти, и следующий круг
# чинил бы вход за входом, воспроизводя ровно ту форму отказа, которой фаза
# провалена третьим кругом.


class _RouteInput(NamedTuple):
    """Один вход маршрута, по которому величина идентификатора доезжает до SQL.

    `url` и `body` — ШАБЛОНЫ: `{value}` подставляется испытуемой величиной,
    `{ad_id}` — ЖИВЫМ идентификатором объявления. Живой идентификатор в теле
    обязателен там, где маршрут читает его сам: иначе случай проверял бы отказ
    по ЧУЖОМУ входу, а не по тому, который назван его именем.

    `live` называет, какая ЖИВАЯ величина подставляется в антивакууме, — без
    неё правило зеленело бы на границе, отвергающей и годное тоже.
    """

    name: str
    carrier: str
    url: str
    body: tuple[tuple[str, str], ...]
    live: str


# Величина ВНЕ диапазона колонки идентификатора. Берётся СТРОКОЙ из двадцати
# пяти девяток — тем же способом, каким её берёт обход транспортов
# (tests/test_pages/test_confirm_delete_transport.py, UNUSABLE_AD_ID_VALUES).
# Приведение к числу на стороне правила спрятало бы предмет: предмет — именно
# то, что ДО приведения на стороне приложения значение доезжает до драйвера.
OUT_OF_COLUMN_RANGE = "9" * 25

# Форма ответа на негодную величину — отказ ВАЛИДАЦИИ, то есть ровно то, что
# модуль правил редактора себе и объявил.
VALIDATION_REFUSAL = 422

# Пять входов файла `app/pages/schedules.py`, доезжающих до сравнения SQL.
# Перечень взят из отчёта верификации третьего круга ДОСЛОВНО: три
# идентификатора пути (`CR-02`) и два поля формы маршрута создания (`CR-01`,
# унаследованный незакрытым).
UNBOUNDED_ROUTE_CASES: tuple[_RouteInput, ...] = (
    _RouteInput(
        name="delete/path:schedule_id",
        carrier="адрес запроса",
        url="/schedules/{value}/delete",
        body=(),
        live="schedule",
    ),
    _RouteInput(
        name="edit/path:schedule_id",
        carrier="адрес запроса",
        url="/schedules/{value}/edit",
        body=(("ad_id", "{ad_id}"),),
        live="schedule",
    ),
    _RouteInput(
        name="toggle/path:schedule_id",
        carrier="адрес запроса",
        url="/schedules/{value}/toggle",
        body=(),
        live="schedule",
    ),
    _RouteInput(
        name="new/form:ad_id",
        carrier="тело формы",
        url="/schedules/new",
        body=(("ad_id", "{value}"),),
        live="ad",
    ),
    _RouteInput(
        name="new/form:account_id",
        carrier="тело формы",
        url="/schedules/new",
        body=(("ad_id", "{ad_id}"), ("account_id", "{value}")),
        live="account",
    ),
)


async def _post_route_input(
    client: AsyncClient, case: _RouteInput, value: str, ad_id: int, *, htmx: bool = False
):
    """Прямой POST мимо браузера по одному входу перечня.

    Тело собирается СЫРОЙ строкой (`_form`), а не отображением: величина из
    двадцати пяти девяток в отображении потребовала бы приведения, и первое же
    приведение спрятало бы предмет (записанное основание соседнего обхода).

    `htmx` ставит признак слоя письма на ЭТОТ запрос, а не на общий клиент:
    половина деградации не имеет права молча стать половиной htmx.
    """
    headers = {**FORM_HEADERS, "HX-Request": "true"} if htmx else FORM_HEADERS
    return await client.post(
        case.url.format(value=value),
        content=_form(
            [(key, tmpl.format(value=value, ad_id=ad_id)) for key, tmpl in case.body]
        ),
        headers=headers,
        follow_redirects=False,
    )


# Величины ВНЕ колонки, на которых маршрут обязан ответить веткой «записи нет».
# Три, и у каждой своё основание: соседняя с границей (`ID_MAX + 1`, до D-07 —
# отказ валидации, на SQLite суиты НЕ роняющая драйвер), двадцать пять девяток
# (прежний предмет правила) и двадцать шесть знаков (величина, роняющая сам
# драйвер, — критерий плана 11-02).
OUT_OF_COLUMN_VALUES: tuple[str, ...] = (
    str(ID_MAX + 1),
    OUT_OF_COLUMN_RANGE,
    "9" * 26,
)

# ЭТАЛОН ВЕТКИ: несуществующий идентификатор ВНУТРИ колонки. Ожидание для
# величины вне колонки формулируется СОВПАДЕНИЕМ с ответом на него, а не
# буквенным адресом: «та же ветка» (D-07) есть равенство исходов, и правило,
# знающее адрес буквой, разъехалось бы с продуктом при первой правке ветки.
MISSING_IN_COLUMN = "999999"


def _branch_shape(response) -> tuple[int, str | None, str | None]:
    """Форма исхода: код, адрес перенаправления и заголовок перехода."""
    return (
        response.status_code,
        response.headers.get("location"),
        response.headers.get("HX-Location"),
    )


@pytest.mark.asyncio
async def test_no_schedule_route_answers_with_a_handler_failure_on_an_out_of_range_identifier(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Ни один из ПЯТИ входов файла не роняет обработчик величиной вне диапазона.

    ⚠️ ПОКОЛЕНИЕ ОЖИДАНИЯ (Фаза 11, план 11-02, решение D-07). Прежде правило
    ожидало на каждом входе ОТКАЗ ВАЛИДАЦИИ (`422`): граница стояла в аннотации,
    и форму отказа выбирал фреймворк. D-07 перенёс границу внутрь обработчика, и
    величина вне колонки идёт ТОЙ ЖЕ веткой, что «записи нет / запись чужая»
    этого входа. Ожидание теперь — РАВЕНСТВО исхода исходу на несуществующем
    идентификаторе внутри колонки, на ОБОИХ транспортах: без htmx это `302` с
    адресом, с htmx — та же ветка своим транспортом. Предмет «не 500» остаётся.

    Отображение сличается ЦЕЛИКОМ, и текст отказа называет ВСЕ несогласные
    строки: правило, останавливающееся на первой, чинилось бы по одному входу
    за круг.

    ⚠️ ЭТО ПРАВИЛО НЕ ПОГЛОЩЕНО ГЕЙТОМ КАТАЛОГА И НЕ ПОГЛОЩАЕТ ЕГО. Свойство
    ПРОЕКТА — «ни один вход ни одного модуля страничного слоя не появится без
    границы» — стережёт `test_every_identifier_parameter_of_the_catalogue_carries_the_bound`
    (`tests/test_pages/test_identifier_bounds.py`, план 10-30), и вселенная у
    него весь `app/pages/`. ПРЕДМЕТ ЗДЕШНЕГО ПРАВИЛА ДРУГОЙ: оно наблюдает
    ПОВЕДЕНИЕ ПЯТИ РЕАЛЬНЫХ ЗАПРОСОВ — что запрос действительно ДОЕХАЛ до
    отказа валидации, включая порядок полей в теле, — тогда как гейт каталога
    наблюдает ОБЪЯВЛЕНИЕ в сигнатуре. Снос здешнего правила ради
    «неповторения» заменил бы НАБЛЮДЕНИЕ ОБЪЯВЛЕНИЕМ: сигнатура, объявленная
    ограниченным псевдонимом, ничего не говорит о том, что запрос по этому
    маршруту доезжает куда обещано.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)

    disagreed: list[str] = []
    rows = 0
    for case in UNBOUNDED_ROUTE_CASES:
        for htmx in (False, True):
            transport = "htmx" if htmx else "без htmx"
            reference = _branch_shape(
                await _post_route_input(
                    authed_client, case, MISSING_IN_COLUMN, ad.id, htmx=htmx
                )
            )
            for value in OUT_OF_COLUMN_VALUES:
                observed = _branch_shape(
                    await _post_route_input(authed_client, case, value, ad.id, htmx=htmx)
                )
                rows += 1
                if observed != reference or (
                    not htmx and (observed[0] != 302 or not observed[1])
                ):
                    disagreed.append(
                        f"{case.name} [{transport}] ← {value[:12]}… = {observed}, "
                        f"ветка «записи нет» = {reference}"
                    )

    assert rows == len(UNBOUNDED_ROUTE_CASES) * 2 * len(OUT_OF_COLUMN_VALUES)
    assert not disagreed, (
        "величина вне диапазона колонки НЕ ПОШЛА веткой «записи нет / запись "
        "чужая» своего входа (D-07 Фазы 11): "
        + "; ".join(disagreed)
        + ". Предмет — инвариант этого модуля в поколении D-07: прямой POST мимо "
        "браузера не роняет обработчик и не выдаёт отказом валидации, что "
        "величина лежит вне колонки (T-02-24, T-02-25, T-11-05). Несогласных "
        f"строк {len(disagreed)} из {rows}"
    )

    # АНТИВАКУУМ. Без него зелёное не значит ничего: помощник, отвергающий ВСЁ,
    # дал бы те же пять отказов валидации и объявил бы себя границей.
    alive = {}
    for case in UNBOUNDED_ROUTE_CASES:
        if case.live == "schedule":
            live_value = (await _seed_schedule(db_session, ad.id, account.id)).id
        elif case.live == "ad":
            live_value = ad.id
        else:
            live_value = account.id
        response = await _post_route_input(
            authed_client, case, str(live_value), ad.id
        )
        alive[case.name] = response.status_code

    refused_alive = {
        name: code
        for name, code in alive.items()
        if code == VALIDATION_REFUSAL or code >= 500
    }
    assert not refused_alive, (
        "граница отвергла ГОДНУЮ величину — она отвергает не то, что объявила: "
        + "; ".join(f"{name} = {code}" for name, code in sorted(refused_alive.items()))
        + f". Все снятые исходы: {sorted(alive.items())}"
    )


# --- СМЕЖНОСТЬ ГРАНИЦЫ: ОБЕ СТОРОНЫ, И ОНИ РАЗЛИЧНЫ --------------------------
#
# Ребро `adjacency` зонда покрытия по FORM-06 разрешается ЗДЕСЬ. Граница,
# проверенная только ИЗНУТРИ диапазона, зеленела бы на помощнике, не
# отвергающем ничего; проверенная только СНАРУЖИ — на помощнике, отвергающем
# всё. Замеряется ровно СТЫК: последняя допустимая величина и первая
# недопустимая.
#
# ⚠️ ВЕЛИЧИНА ЧИТАЕТСЯ ИЗ ПРИЛОЖЕНИЯ ВВОЗОМ, А НЕ ВЫПИСЫВАЕТСЯ ЛИТЕРАЛОМ.
# Вторая копия числа разошлась бы с первой молча при первой же правке, и правило
# начало бы утверждать о числе, которого в приложении нет.

# Заведомо несуществующий идентификатор ВНУТРИ диапазона. Нужен эталоном формы
# ответа: величина границы есть ЗАКОННЫЙ идентификатор, которого в базе нет, и
# ожидание для неё формулируется КАК СОВПАДЕНИЕ с ответом на такой же
# несуществующий, а не буквенным кодом. Правило, ожидающее код буквой,
# разъехалось бы с продуктом при первой правке формы ответа на отсутствующую
# запись.
MISSING_INSIDE_RANGE = 999_999

# Маршрут тумблера — самый короткий из трёх с идентификатором пути: ни тела
# формы, ни ветвления по признаку возврата.
ADJACENCY_ROUTE = "/schedules/{value}/toggle"


@contextmanager
def _schedule_statement_log(db_session: AsyncSession):
    """Операторы SQL, ищущие строку расписания ПО ИДЕНТИФИКАТОРУ, за время блока.

    Слушатель вешается на СИНХРОННЫЙ движок за асинхронным (приём
    `_statement_log`, `tests/test_pages/test_schedules_list.py`) и снимается в
    `finally`, иначе следующий тест наследовал бы чужой слушатель.

    ⚠️ ПРИЗНАК — СРАВНЕНИЕ ПО КОЛОНКЕ ИДЕНТИФИКАТОРА, А НЕ ИМЯ ТАБЛИЦЫ, И ЭТО
    ЗАМЕР. Первая редакция ловила любое вхождение слова `schedules` и поймала
    запрос счётчиков навигации (`… AS schedules`), который исполняется на ЛЮБОМ
    запросе вошедшего и величины идентификатора не касается вовсе. Предмет
    стыка — уехала ли величина операндом сравнения по колонке, и признак снят
    ровно с него.
    """
    engine = db_session.bind.sync_engine
    seen: list[str] = []

    def _before(conn, cursor, statement, parameters, context, executemany):
        if "schedules.id = " in statement:
            seen.append(statement)

    event.listen(engine, "before_cursor_execute", _before)
    try:
        yield seen
    finally:
        event.remove(engine, "before_cursor_execute", _before)


async def _response_shape(client: AsyncClient, value) -> tuple[int, str | None]:
    """ФОРМА ответа маршрута тумблера: код и адрес приземления.

    Форма — пара, а не один код: две ветви маршрута отвечают одним кодом 302 и
    различаются адресом, и утверждение по одному коду прошло бы на обеих.
    """
    response = await client.post(
        ADJACENCY_ROUTE.format(value=value),
        content=_form([]),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )
    return response.status_code, response.headers.get("location")


@pytest.mark.asyncio
async def test_the_column_bound_admits_its_own_value_and_refuses_the_next_one(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Величина границы доходит до выборки, величина на единицу больше — нет.

    ⚠️ ПОКОЛЕНИЕ (Фаза 11, план 11-02, решение D-07). Прежде внешняя сторона
    стыка утверждалась КОДОМ: `ID_MAX + 1` давал отказ валидации, и антивакуум
    требовал, чтобы две соседние величины дали РАЗНЫЕ исходы. D-07 делает исходы
    РАВНЫМИ по построению — величина вне колонки идёт веткой «записи нет», и
    различимость исхода была бы ровно тем, что T-11-05 запрещает. Стык теперь
    наблюдается там, где он и живёт: у величины границы выборка по расписаниям
    ВЫПОЛНЯЕТСЯ, у величины на единицу больше — НЕ выполняется ни одного
    оператора над таблицей расписаний.
    """
    reference = await _response_shape(authed_client, MISSING_INSIDE_RANGE)
    with _schedule_statement_log(db_session) as at_bound_statements:
        at_bound = await _response_shape(authed_client, ID_MAX)
    with _schedule_statement_log(db_session) as past_bound_statements:
        past_bound = await _response_shape(authed_client, ID_MAX + 1)

    assert at_bound == reference, (
        "величина, РАВНАЯ верхней границе колонки, отвергнута — граница "
        "отвергает годное, и «отказ валидации, а не 500» держалось бы ценой "
        f"сломанного продукта. На границе снято {at_bound}, на несуществующем "
        f"идентификаторе внутри диапазона — {reference}. Разошлась ВНУТРЕННЯЯ "
        "сторона границы"
    )
    assert past_bound == reference, (
        "величина НА ЕДИНИЦУ БОЛЬШЕ верхней границы колонки ушла НЕ веткой "
        f"«записи нет»: снято {past_bound}, ветка «записи нет» — {reference} "
        "(D-07 Фазы 11). Разошлась ВНЕШНЯЯ сторона границы"
    )

    # АНТИВАКУУМ СМЕЖНОСТИ — ПО ЗАПРОСАМ, А НЕ ПО КОДУ. Помощник, не отвергающий
    # ничего, отправил бы `ID_MAX + 1` в выборку; помощник, отвергающий всё, не
    # отправил бы в неё и `ID_MAX`.
    assert at_bound_statements, (
        "на величине границы не выполнено НИ ОДНОГО оператора над расписаниями — "
        "либо граница отвергает годное, либо журнал операторов не видит запросов "
        "приложения и правило ниже зеленело бы вакуумом"
    )
    assert not past_bound_statements, (
        "величина на единицу больше границы ДОЕХАЛА ДО ЗАПРОСА: "
        f"{past_bound_statements} — проверка стоит ниже первого использования, и "
        "на PostgreSQL этот запрос даёт `DataError` (Landmine CONTEXT Фазы 11)"
    )


# =============================================================================
# СТАТИЧЕСКИЙ ГЕЙТ СИГНАТУР: ШЕСТОЙ ВХОД ТОГО ЖЕ КЛАССА НЕ УЕЗЖАЕТ МОЛЧА
# =============================================================================
#
# ПРЕДМЕТ ШИРЕ ПЯТИ ИЗВЕСТНЫХ ВХОДОВ. Правило поведения выше стережёт РОВНО ТЕ
# пять входов, которые назвал отчёт верификации. Новый маршрут страничного
# модуля расписаний приедет с неограниченным идентификатором, и правило
# поведения останется зелёным: оно о нём не знает. Гейт читает СИГНАТУРЫ файла и
# краснеет на идентификаторе, объявленном без общей границы, — то есть В МОМЕНТ
# ВВЕДЕНИЯ, а не следующим кругом верификации.

SCHEDULES_MODULE = Path(__file__).resolve().parents[2] / "app" / "pages" / "schedules.py"

# Три псевдонима общей границы (app/pages/schedules.py). Идентификатор маршрута,
# объявленный НЕ через них, границы не несёт.
BOUND_ALIASES = ("ScheduleIdPath", "AdIdForm", "AccountIdForm")

# ВТОРАЯ ФОРМА ГРАНИЦЫ — ВСТРОЕННАЯ ЗАПИСЬ, И ЭТО ЗАМЕР, А НЕ ПОБЛАЖКА
# (Фаза 11, план 11-04).
#
# ПОЧЕМУ ФОРМ ДВЕ. Все три псевдонима выше построены на `Path()` и `Form()` —
# то есть на входах МАРШРУТА и ТЕЛА. Курсор порции есть параметр СТРОКИ ЗАПРОСА
# (`Query`), и псевдонима этой формы у проекта нет вовсе: соседний раздел
# объявляет свой курсор ровно так же, встроенной записью
# (`app/pages/account_groups.py::account_groups_partial`). Правило, знающее
# только псевдонимы, объявило бы ограниченный вход НЕограниченным и потребовало
# бы от него псевдонима, которого не существует.
#
# ⚠️ ЭТО НЕ ОСЛАБЛЕНИЕ ПРАВИЛА, И ГРАНИЦА РАЗЛИЧИЯ НАЗВАНА. Предмет модуля —
# «величина вне диапазона колонки не доедет до драйвера БД» (T-02-24, T-02-25),
# а не «в сигнатуре набрано одно из трёх имён». Встроенная запись этот предмет
# удовлетворяет ПОЛНОСТЬЮ: обе половины диапазона стоя́т на самом входе. Голое
# `int` по-прежнему краснеет, и это показано отрицательными контролями ниже —
# их ДВА: на голое целое и на ПОЛОВИНУ встроенной границы.
#
# ЭТА ЖЕ ПАРА ФОРМ УЖЕ ПРИЗНАНА ПРОЕКТОМ: `_carries_the_bound` гейта каталога
# (`tests/test_pages/test_identifier_bounds.py`) принимает псевдоним ЛИБО
# встроенную запись, и по тому же основанию — курсор постраничного вывода.
# Здешнее правило приводится к той же паре, а не заводит третью трактовку.
INLINE_BOUND_MARKS = ("ge=1", "le=ID_MAX")

# Признак идентификатора в имени параметра: `id` целиком либо хвост `_id`.
# `valid`, `paid` и прочие слова, кончающиеся на те же две буквы, признаком не
# являются — иначе гейт судил бы о параметрах, к идентификаторам отношения не
# имеющих.
_IDENTIFIER_PARAM = re.compile(r"(?:^id|_id)$")

_PY_DOCSTRING = re.compile(r'"""(?:.|\n)*?"""')
_PY_WHOLE_LINE_COMMENT = re.compile(r"(?m)^[ \t]*#.*$")

_ROUTE_HANDLER = re.compile(
    r"^@router\.(?:get|post|put|patch|delete)\([^\n]*\n"
    r"(?:@[^\n]*\n)*"
    r"async def (?P<name>\w+)\((?P<signature>.*?)\n\)\s*:",
    re.M | re.S,
)

# ПЕРЕЧЕНЬ ИЗЪЯТИЙ — ПУСТ, И ЭТО ЗАМЕР, А НЕ ПРОПУСК.
#
# Изъятию подлежит параметр, чья ВЕЛИЧИНА НЕ ПОДКОНТРОЛЬНА ОТПРАВИТЕЛЮ:
# идентификатор владельца, приходящий не запросом, а зависимостью сессии. Такой
# параметр границы на границе приложения не требует — его значение приложение
# ставит себе само, и требование границы к нему было бы требованием к
# собственному коду, а не к вводу.
#
# ЗАМЕРЕНО ПО ДЕРЕВУ: в `app/pages/schedules.py` такого параметра НЕТ НИ У
# ОДНОГО из шести маршрутов. Владелец во всех шести берётся ВНУТРИ тела
# (`get_user_from_cookie(request, db, settings)`), а не параметром сигнатуры,
# поэтому изымать сегодня нечего. Перечень заведён ПУСТЫМ, а не опущен: пустой
# перечень с записанным основанием говорит следующему читателю, ЧТО именно сюда
# кладут и почему, — опущенный не говорит ничего, и первое же изъятие уехало бы
# фильтром без обоснования. Форма перечня изъятий с основанием НА ЗАПИСЬ у
# каждого пункта принята планом 10-06.
SIGNATURE_GATE_EXEMPTIONS: dict[str, str] = {}

# Число ограниченных входов файла. ПОСТАВЛЕНО ПРОГОНОМ покрасневшего правила, а
# не посчитано в уме.
#
# ЛЕТОПИСЬ ЧИСЛА. Заведено планом 10-12 равным СЕМИ: три идентификатора пути
# (`schedules_update`, `schedules_toggle`, `schedules_delete`), два поля
# маршрута создания (`ad_id`, `account_id`) и два поля маршрута правки
# (`ad_id`, `account_id`). Маршруты `schedules_partial` и `schedules_list`
# идентификаторов в сигнатурах не несут вовсе и в счёт не входят. Рост числа
# означает НОВЫЙ вход того же класса, и решение о его границе принимается тогда,
# а не обнаруживается кругом верификации; падение — что вход исчез из сигнатуры
# и правило поведения выше стережёт величину, которой в маршруте больше нет.
#
# 7 → 8, Фаза 11, план 11-04 (решение D-11).
#
# ⚠️ ПОСЫЛКА АБЗАЦА ВЫШЕ ОПРОВЕРГНУТА И ОСТАВЛЕНА НАЗВАННОЙ, А НЕ СТЁРТОЙ
# (идиома D-30/D-32). Она гласила: «Маршруты `schedules_partial` и
# `schedules_list` идентификаторов в сигнатурах не несут вовсе и в счёт не
# входят». Это было верно ДЛЯ СВОЕГО ДЕРЕВА — плана 10-12, где порция листалась
# СМЕЩЕНИЕМ, а смещение идентификатором не является. План 11-04 перевёл курсор
# на КЛЮЧ последней отрисованной строки (CR-01 Фазы 9), и у `schedules_partial`
# впервые появился вход, чьё имя несёт признак идентификатора. `schedules_list`
# по-прежнему не несёт ни одного — половина посылки в силе.
#
# ИСТОЧНИК ДВИЖЕНИЯ, НАЗВАННЫЙ ВХОДОМ: `schedules_partial.after_id`. Границу он
# несёт ВСТРОЕННОЙ записью, а не псевдонимом, — основание записано у
# `INLINE_BOUND_MARKS`, и вход остаётся ВНУТРИ счёта, а не выводится изъятием:
# величина его подконтрольна отправителю, то есть критерию перечня изъятий он не
# удовлетворяет.
#
# ⚠️ ЧИСЛО ПОСТАВЛЕНО ПРОГОНОМ ПОКРАСНЕВШЕГО ПРАВИЛА, А НЕ СЛОЖЕНИЕМ В УМЕ:
# «ограниченных входов маршрутов 8, а объявлено 7» — и перечислило все восемь.
BOUNDED_ROUTE_INPUTS_DECLARED = 8


def _strip_comments(source: str) -> str:
    """Исходник Python без тел докстрингов и без строчных комментариев.

    ВЫРЕЗАНИЕ ЕСТЬ НЕСУЩЕЕ РЕШЕНИЕ ГЕЙТА, А НЕ УДОБСТВО РАЗБОРА. Кодовая база
    проекта комментарии-обоснования несёт объёмные — почти каждое место снабжено
    абзацем о том, почему оно устроено именно так, — и такой абзац свободно
    содержит и форму объявления параметра, и его имя. Гейт, считающий прозу,
    получает два отказа сразу: он краснеет на правку документации сообщением об
    исчезнувшем параметре и, что хуже, позволяет комментарию ЗАМЕНИТЬ СОБОЙ
    пропавшую границу, оставив вердикт верным. Основание перенесено дословно из
    `tests/test_templates/test_htmx_inventory.py:_strip_comments`, где та же
    ловушка уже стоила суите константы, знавшей текст документации наизусть.

    Порядок вырезания значим: сперва ДОКСТРИНГИ, потом строчные комментарии.
    Строка, начинающаяся с решётки, свободно лежит ВНУТРИ докстринга (этот файл
    такие несёт), и обратный порядок разорвал бы докстринг на половины, оставив
    его закрывающие кавычки без открывающих.

    Вырезаются ЦЕЛЫЕ строки комментария, а не хвост после решётки на строке
    кода, И ЭТО РЕШЕНИЕ: решётка живёт и внутри строковых литералов (адреса с
    якорем), и вырезание хвоста съело бы код. Ловушка, которую гейт закрывает, —
    именно АБЗАЦ обоснования, а такой абзац в этом проекте всегда состоит из
    целых строк.
    """
    return _PY_WHOLE_LINE_COMMENT.sub("", _PY_DOCSTRING.sub("", source))


def _route_signature_sources(source: str) -> dict[str, str]:
    """Пары «имя обработчика маршрута — текст его сигнатуры».

    ИСХОДНИК ПРИНИМАЕТСЯ ПАРАМЕТРОМ, а не читается из константы, и это несущее
    решение гейта. Группа контроля обязана подать разборщику ИЗМЕНЁННУЮ копию
    исходника; разборщик, зашитый на единственный источник, сделал бы группу
    контроля невыразимой, и зубы гейта пришлось бы ЗАЯВЛЯТЬ вместо того, чтобы
    их показывать. Приём и его основание взяты у `_all_templates(directory)`
    (tests/test_templates/test_htmx_markup_gates.py).

    Отбор ведётся по ОБЪЯВЛЕНИЮ МАРШРУТА, стоящему над функцией, а не по имени
    функции: имя — соглашение, признак маршрута — факт.
    """
    clean = _strip_comments(source)
    return {
        match.group("name"): match.group("signature")
        for match in _ROUTE_HANDLER.finditer(clean)
    }


def _identifier_inputs(signature: str) -> dict[str, str]:
    """Параметры сигнатуры, чьё имя несёт признак идентификатора.

    Разбор ведётся по запятым ВЕРХНЕГО УРОВНЯ: аннотация ограниченного
    параметра сама несёт запятые внутри скобок (`Annotated[int, Form(...)]`), и
    наивное деление по запятой разорвало бы её на два мнимых параметра.
    """
    parts: list[str] = []
    depth = 0
    current = ""
    for char in signature:
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        if char == "," and depth == 0:
            parts.append(current)
            current = ""
            continue
        current += char
    parts.append(current)

    inputs: dict[str, str] = {}
    for part in parts:
        text = part.strip()
        if not text or ":" not in text:
            continue
        name, annotation = text.split(":", 1)
        name = name.strip()
        if _IDENTIFIER_PARAM.search(name):
            inputs[name] = annotation.strip()
    return inputs


def _carries_inline_bound(annotation: str) -> bool:
    """Несёт ли объявление ВСТРОЕННУЮ границу — ОБЕ её половины сразу.

    ⚠️ ТРЕБУЮТСЯ ОБЕ ПОЛОВИНЫ, И ЭТО НЕСУЩЕЕ УСЛОВИЕ. Одна лишь нижняя граница
    (`ge=1`) не защищает ни от чего: величина ВЫШЕ диапазона колонки и есть та,
    что доезжает до драйвера и даёт пятисотку. Правило, принявшее половину,
    зеленело бы ровно на том входе, ради которого написано.
    """
    return all(mark in annotation for mark in INLINE_BOUND_MARKS)


def _bound_verdicts(source: str) -> dict[str, bool]:
    """Отображение «обработчик.параметр → несёт ли общую границу».

    Граница засчитывается в ДВУХ формах — псевдонимом либо встроенной записью
    (основание записано у `INLINE_BOUND_MARKS`).
    """
    verdicts: dict[str, bool] = {}
    for handler, signature in _route_signature_sources(source).items():
        for name, annotation in _identifier_inputs(signature).items():
            key = f"{handler}.{name}"
            if key in SIGNATURE_GATE_EXEMPTIONS:
                continue
            verdicts[key] = any(
                alias in annotation for alias in BOUND_ALIASES
            ) or _carries_inline_bound(annotation)
    return verdicts


def test_every_identifier_input_of_the_schedule_routes_carries_the_shared_bound():
    """Каждый идентификатор каждого маршрута файла объявлен через общую границу.

    Сличается ОТОБРАЖЕНИЕ ЦЕЛИКОМ, а не утверждение на каждом шаге, — по той же
    причине, по которой так собрано правило пяти маршрутов: гейт с ранним
    отказом чинился бы по одному параметру за круг.

    ⚠️ ТРИ УТВЕРЖДЕНИЯ, А НЕ ОДНО В ТРЁХ КОПИЯХ. С заведением гейта каталога
    (`test_every_identifier_parameter_of_the_catalogue_carries_the_bound`,
    `tests/test_pages/test_identifier_bounds.py`, план 10-30) над границей
    величины стоя́т ТРИ правила, и ни одно не выводится из другого:
      — правило прогона выше: ПЯТЬ РЕАЛЬНЫХ ЗАПРОСОВ доезжают до отказа
        валидации — наблюдается ПОВЕДЕНИЕ маршрута целиком;
      — ЭТО правило: ШЕСТОЙ вход ЭТОГО ФАЙЛА не появится без границы —
        стережётся ИНВАРИАНТ, объявленный шапкой ЭТОГО модуля («прямой POST
        мимо браузера обязан давать отказ валидации, а не 500», T-02-24,
        T-02-25), и вселенная у него ОДИН ФАЙЛ, объявленный числом
        `BOUNDED_ROUTE_INPUTS_DECLARED`;
      — гейт каталога: НИ ОДИН вход НИ ОДНОГО модуля страничного слоя не
        появится без границы — стережётся свойство ПРОЕКТА, и вселенная у него
        объявлена своим числом.
    ЗДЕШНЕЕ ЧИСЛО И ЧИСЛО ГЕЙТА КАТАЛОГА СЧИТАЮТ РАЗНОЕ и совпадать не обязаны:
    здешнее считает входы ОДНОГО файла, то число — параметры ВСЕГО каталога.
    Снос здешнего правила ради «неповторения» подменил бы ИНВАРИАНТ МОДУЛЯ,
    записанный его собственной шапкой, СВОЙСТВОМ ПРОЕКТА — а модуль, чей
    объявленный инвариант никем не стережётся, теряет его молча.
    """
    source = SCHEDULES_MODULE.read_text(encoding="utf-8")
    verdicts = _bound_verdicts(source)

    unbounded = sorted(key for key, carries in verdicts.items() if not carries)
    assert not unbounded, (
        "идентификаторы маршрутов объявлены БЕЗ общей границы величины: "
        + ", ".join(unbounded)
        + ". Величина вне диапазона колонки доедет по ним до драйвера БД и даст "
        "пятисотку на форменный POST (T-02-24, T-02-25, CR-01, CR-02). "
        "Объявлять через ScheduleIdPath / AdIdForm / AccountIdForm"
    )

    assert len(verdicts) == BOUNDED_ROUTE_INPUTS_DECLARED, (
        f"ограниченных входов маршрутов {len(verdicts)}, а объявлено "
        f"{BOUNDED_ROUTE_INPUTS_DECLARED}. Рост означает НОВЫЙ вход того же "
        "класса, решения о границе которого никто не принимал; падение — что "
        "вход исчез из сигнатуры и правило поведения стережёт величину, которой "
        f"в маршруте больше нет. Снятые входы: {sorted(verdicts)}"
    )

    # Изъятие, пережившее свой параметр, есть перечень того, до чего не дошли
    # руки: ключ, которого в сигнатурах больше нет, обязан краснить прогон.
    all_keys = set()
    for handler, signature in _route_signature_sources(source).items():
        all_keys.update(f"{handler}.{name}" for name in _identifier_inputs(signature))
    stale = sorted(set(SIGNATURE_GATE_EXEMPTIONS) - all_keys)
    assert not stale, (
        f"изъятия пережили свои параметры: {stale}. Изъятие без предмета — "
        "запись о том, до чего не дошли руки, а не решение"
    )


def test_control_negative_half_an_inline_bound_reddens_the_signature_gate():
    """ЗУБЫ ВТОРОЙ ФОРМЫ ГРАНИЦЫ ПОКАЗАНЫ ОТДЕЛЬНО (Фаза 11, план 11-04).

    ⚠️ БЕЗ ЭТОГО КОНТРОЛЯ ПРИЗНАНИЕ ВСТРОЕННОЙ ЗАПИСИ БЫЛО БЫ ДЫРОЙ, А НЕ
    ЗАМЕРОМ. Соседний контроль доказывает, что краснеет ГОЛОЕ целое, — но он
    ничего не говорит о том, краснеет ли встроенная запись, у которой есть
    только нижняя половина диапазона. Именно ВЕРХНЯЯ половина и защищает от
    величины, доезжающей до драйвера БД, поэтому правило, принимающее
    `Query(None, ge=1)`, зеленело бы на том самом входе, ради которого написано.

    Подделка идёт в памяти: у курсора порции снимается верхняя граница, и
    утверждается, что гейт назвал ИМЕННО этот вход. Файл дерева не правится ни
    байтом.
    """
    source = SCHEDULES_MODULE.read_text(encoding="utf-8")

    honest = _bound_verdicts(source)
    assert all(honest.values()), (
        f"на настоящем исходнике гейт уже красен: {sorted(honest.items())}"
    )

    forged_declaration = "after_id: int | None = Query(None, ge=1, le=ID_MAX)"
    assert source.count(forged_declaration) == 1, (
        "объявление курсора порции встречается в исходнике не единожды "
        f"({source.count(forged_declaration)}) — подстановка контроля перестала "
        "быть однозначной"
    )
    forged = source.replace(
        forged_declaration, "after_id: int | None = Query(None, ge=1)", 1
    )
    assert forged != source, "подстановка контроля ничего не изменила"

    broken = _bound_verdicts(forged)
    unbounded = sorted(key for key, carries in broken.items() if not carries)
    assert unbounded == ["schedules_partial.after_id"], (
        "гейт НЕ ПОКРАСНЕЛ на встроенной границе, потерявшей верхнюю половину: "
        f"{sorted(broken.items())}. Величина выше диапазона колонки прошла бы в "
        "дерево незамеченной"
    )
    assert len(broken) == len(honest), (
        "подделка изменила ЧИСЛО входов, а не только их вердикт — контроль "
        f"доказывал бы не то свойство, которое объявил: {len(broken)} против "
        f"{len(honest)}"
    )


def test_control_negative_an_unbounded_identifier_reddens_the_signature_gate():
    """ЗУБЫ ГЕЙТА ПОКАЗАНЫ, А НЕ ЗАЯВЛЕНЫ.

    Разборщику подаётся ИЗМЕНЁННАЯ КОПИЯ исходника, в которой ОДИН
    идентификатор пути возвращён к объявлению без границы. Копия собирается в
    памяти — файл дерева не правится ни байтом.
    """
    source = SCHEDULES_MODULE.read_text(encoding="utf-8")

    honest = _bound_verdicts(source)
    # Первый предохранитель: на НАСТОЯЩЕМ исходнике гейт зелен, иначе контроль
    # сравнивал бы подделку с уже сломанным образцом.
    assert all(honest.values()), (
        f"на настоящем исходнике гейт уже красен: {sorted(honest.items())}"
    )

    forged_declaration = "    schedule_id: ScheduleIdPath,"
    assert source.count(forged_declaration) == 3, (
        "образец объявления идентификатора пути встречается в исходнике не "
        f"трижды ({source.count(forged_declaration)}) — подстановка контроля "
        "перестала быть однозначной"
    )
    forged = source.replace(forged_declaration, "    schedule_id: int,", 1)
    assert forged != source, "подстановка контроля ничего не изменила"

    broken = _bound_verdicts(forged)
    unbounded = sorted(key for key, carries in broken.items() if not carries)
    assert unbounded == ["schedules_update.schedule_id"], (
        "гейт НЕ ПОКРАСНЕЛ на идентификаторе пути, возвращённом к голому целому: "
        f"{sorted(broken.items())}. Неограниченный вход прошёл бы в дерево "
        "незамеченным"
    )
    assert len(broken) == len(honest), (
        "подделка изменила ЧИСЛО входов, а не только их вердикт — контроль "
        f"доказывал бы не то свойство, которое объявил: {len(broken)} против "
        f"{len(honest)}"
    )


def test_control_the_signature_gate_does_not_read_its_own_documentation():
    """ГЕЙТ НЕ САМООТМЕНЯЕТСЯ: комментарий не заменяет собой параметр.

    В исходник добавляется СТРОКА КОММЕНТАРИЯ, дословно называющая форму
    неограниченного параметра. Вердикт гейта обязан не измениться: комментарий
    не есть параметр, и правило, читающее прозу, краснело бы на правку
    документации и зеленело бы на документацию, повторяющую искомое.
    """
    source = SCHEDULES_MODULE.read_text(encoding="utf-8")
    honest = _bound_verdicts(source)

    anchor = "async def schedules_toggle(\n"
    assert source.count(anchor) == 1, "якорь подстановки комментария неоднозначен"
    commented = source.replace(
        anchor,
        anchor + "    # ПРИМЕР ДЛЯ ЧИТАТЕЛЯ: schedule_id: int, — так объявлять НЕЛЬЗЯ\n",
        1,
    )
    assert commented != source, "подстановка комментария ничего не изменила"

    assert _bound_verdicts(commented) == honest, (
        "вердикт гейта изменился от ОДНОЙ строки комментария — гейт считает "
        f"прозу: {sorted(_bound_verdicts(commented).items())} против "
        f"{sorted(honest.items())}"
    )


# --- Фаза 10, план 10-50: сводка объявления во фрагментном ответе -------------
#
# ГЭП G-10-6, обход `walkthrough_3` от 2026-09-11, ДВА замера на разных стендах:
# линейка списка «2 расписания» при сводке предпросмотра «РАСПИСАНИЯ 3» и на
# сервере 2; линейка «1 расписание» при сводке «РАСПИСАНИЯ 2» и на сервере 1.
# Настоящая перезагрузка каждый раз возвращала сводке верное число — то есть
# расхождение живёт РОВНО до следующей полной загрузки.
#
# ⚠️ ЭТО НЕ ТО ЖЕ, ЧТО РАСХОЖДЕНИЕ ШАГА 2.8, И РАЗНИЦА НЕСУЩАЯ. Там экран
# расходится с сервером ПОТОМУ ЧТО ОТВЕТ НЕ ДОЕХАЛ, и плашка об этом честно
# предупреждает. Здесь ответ доехал, своп СОСТОЯЛСЯ и прошёл успешно — а два
# числа ОДНОГО экрана противоречат друг другу, и ни одна плашка об этом не
# говорит, потому что говорить ей не о чем: отказа не было.
#
# ⚠️ РАЗБОР ИДЁТ ПО ОБЛАСТИ ВНЕПОЛОСНОГО УЗЛА, А НЕ ПО ВХОЖДЕНИЮ ЧИСЛА В ТЕЛО.
# Счёт числа по всему телу был бы негодным прибором: в теле стоя́т
# идентификаторы вида `sched-{N}`, и первое же число пришло бы оттуда. Это тот
# же класс дефекта прибора, что расхождение Р-1 обхода (селектор шире
# предмета), и он назван здесь, а не воспроизведён.

AD_SUMMARY_NODE_ID = "ad-summary"
SCHED_COUNT_NODE_ID = "sched-count"

# Элементы, у которых закрывающего тега не бывает: уровня вложенности они не
# открывают. Без перечня скрытое поле, объявленное внеполосным блоком
# (`<input … hx-swap-oob="true">`), навсегда оставило бы всё, что стоит после
# него, «вложенным» — правило глубины краснело бы на работающем ответе (форма
# перенята у `VOID_ELEMENTS` в tests/test_templates/test_htmx_markup_gates.py).
_VOID_TAGS = frozenset(
    {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }
)

_TAG_RE = re.compile(r"<(/?)\s*([a-zA-Z][\w:-]*)((?:[^<>\"']|\"[^\"]*\"|'[^']*')*)>")
_OOB_ATTR_RE = re.compile(r'hx-swap-oob\s*=\s*"([^"]*)"')
_ID_ATTR_RE = re.compile(r'(?<![-\w])id\s*=\s*"([^"]*)"')
_KV_ROW_RE = re.compile(r'<div class="kv">(.*?)</div>', re.S)
_KV_KEY_RE = re.compile(r'<span class="kv__k">(.*?)</span>', re.S)
_KV_VALUE_RE = re.compile(r'<span class="kv__v[^"]*">(.*?)</span>', re.S)


class _OobNode(NamedTuple):
    """Внеполосный узел тела ответа: чем адресован, на какой глубине, что несёт."""

    identifier: str
    depth: int
    inner: str


def _oob_identifier(attrs: str) -> str | None:
    """Чем узел адресует свою цель, или None — если узел не внеполосный.

    Форм адресации ДВЕ, и обе живут в этом ответе: цель, названная СЕЛЕКТОРОМ
    внутри значения признака (`innerHTML:#sched-count` — линейка счётчика), и
    цель, названная СОБСТВЕННЫМ идентификатором узла (`id="ad-summary"` при
    `hx-swap-oob="true"` — подмена самого узла). Разборщик, знающий только одну
    форму, не нашёл бы половину узлов ответа и дал бы правилу вакуумную зелень.
    """
    oob = _OOB_ATTR_RE.search(attrs)
    if oob is None:
        return None
    value = oob.group(1).strip()
    if ":" in value:
        return value.split(":", 1)[1].strip().lstrip("#")
    ident = _ID_ATTR_RE.search(attrs)
    return ident.group(1) if ident else ""


def _oob_nodes(body: str) -> list[_OobNode]:
    """Все внеполосные узлы тела вместе с ГЛУБИНОЙ каждого.

    Глубина возвращается, а не отбрасывается, потому что она и есть предмет
    отдельного правила: блок конфигурации несёт `allowNestedOobSwaps: false`, и
    у ВЛОЖЕННОГО внеполосного узла рантайм МОЛЧА снимает признак — ни ошибки,
    ни предупреждения, ни отличия в статусе. Разборщик, считающий только узлы
    верхнего уровня, не отличил бы «узла нет» от «узел есть, но не свопается».
    """
    nodes: list[_OobNode] = []
    stack: list[tuple[str, str | None, int, int]] = []
    for match in _TAG_RE.finditer(body):
        closing, tag, attrs = match.group(1), match.group(2).lower(), match.group(3)
        if closing:
            if stack and stack[-1][0] == tag:
                _, identifier, depth, start = stack.pop()
                if identifier is not None:
                    nodes.append(_OobNode(identifier, depth, body[start : match.start()]))
            continue
        if tag in _VOID_TAGS or attrs.rstrip().endswith("/"):
            # У пустого элемента области нет вовсе: скрытое поле, объявленное
            # внеполосным блоком, несёт значение атрибутом, а не содержимым.
            continue
        stack.append((tag, _oob_identifier(attrs), len(stack), match.end()))
    return nodes


def _oob_node(body: str, node_id: str) -> _OobNode | None:
    """Внеполосный узел, адресующий поданный идентификатор, или None."""
    for node in _oob_nodes(body):
        if node.identifier == node_id:
            return node
    return None


def _oob_region(body: str, node_id: str) -> str | None:
    """Область внеполосного узла по идентификатору его цели, или None."""
    node = _oob_node(body, node_id)
    return None if node is None else node.inner


def _first_integer(text: str | None) -> int | None:
    """Первое число, НАПЕЧАТАННОЕ в поданной области, или None.

    Разметка вырезается до поиска: число, стоящее в атрибуте (`id="sched-7"`),
    напечатанным не является, и прибор, его засчитавший, мерил бы разметку, а
    не то, что видит человек.
    """
    if text is None:
        return None
    found = re.search(r"\d+", re.sub(r"<[^>]*>", " ", text))
    return int(found.group(0)) if found else None


def _summary_row(region: str, key: str) -> str | None:
    """Значение строки сводки «ключ — значение» по её ключу, или None.

    ⚠️ СТРОКА ВЫБИРАЕТСЯ ПО КЛЮЧУ, А НЕ ПО ПОРЯДКУ, И ЭТО РЕШЕНИЕ. Строк в
    сводке четыре, и ДВЕ из них печатают числа («Вложения» и «Расписания»);
    прибор, берущий первое число области, снял бы число ВЛОЖЕНИЙ и сличал бы с
    линейкой расписаний его. Порядок строк свойством контракта не объявлен ни
    одной записью проекта — утверждать его значило бы завести контракт, которого
    нет, и чинить перестановку строк шаблона как регресс.
    """
    for raw in _KV_ROW_RE.findall(region):
        found_key = _KV_KEY_RE.search(raw)
        found_value = _KV_VALUE_RE.search(raw)
        if found_key and found_value and found_key.group(1).strip() == key:
            return found_value.group(1).strip()
    return None


async def _server_schedule_count(db: AsyncSession, ad_id: int) -> int:
    """Счёт расписаний объявления ПРЯМЫМ запросом к тестовой базе.

    Третий счёт правила согласия. Читается ЗАПРОСОМ, а не выводится из ответа:
    ответ и есть предмет сличения, и выводить из него состояние базы значило бы
    проверять утверждение самим утверждением.
    """
    db.expire_all()
    return (
        await db.execute(
            select(func.count(Schedule.id)).where(Schedule.ad_id == ad_id)
        )
    ).scalar_one()


@pytest.mark.asyncio
async def test_the_ruler_and_the_summary_agree_after_a_fragment_delete(
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """ТРИ счёта одного экрана согласны после ФРАГМЕНТНОГО удаления.

    Сличаются число линейки списка, число сводки предпросмотра и счёт расписаний
    объявления на сервере.

    ⚠️ ТРЕТИЙ СЧЁТ НЕ ИЗБЫТОЧЕН, И ЕГО ОСНОВАНИЕ НАЗЫВАЕТСЯ ЗДЕСЬ, А НЕ
    ПОДРАЗУМЕВАЕТСЯ. Два числа, приезжающие из ОДНОЙ переменной ответа,
    СОГЛАСНЫ ВСЕГДА — в том числе когда оба неверны. Без серверного счёта
    правило утверждало бы СОГЛАСИЕ, а не ВЕРНОСТЬ, и позеленело бы на ответе,
    который печатает в обеих областях одно и то же чужое число.

    ⚠️ ДВА РОДА ОТКАЗА РАЗЛИЧАЮТСЯ ПРАВИЛОМ, А НЕ ЧИТАТЕЛЕМ. «Узла сводки в
    теле нет вовсе» и «числа в двух областях разошлись» суть РАЗНЫЕ отказы с
    разными причинами: первый означает, что ответ этой области не шлёт, второй —
    что шлёт, но из второго независимого чтения. Тексты отказов названы порознь.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)
    await _seed_schedule(db_session, ad.id, account.id)
    await _seed_schedule(db_session, ad.id, account.id)
    ad_id = ad.id

    response = await htmx_client.post(
        f"/schedules/{schedule.id}/delete",
        content=_editor_delete_body(ad),
        headers=FORM_HEADERS,
    )

    assert response.status_code == 200
    assert "<!DOCTYPE" not in response.text, (
        "обработчик ответил документом — значит слой письма его не увидел и "
        "фикстура прошла по редиректу"
    )
    body = response.text

    # --- АНТИВАКУУМ ПЕРВЫМ: ОБЕ ОБЛАСТИ НАЙДЕНЫ И В КАЖДОЙ ЕСТЬ ЧИСЛО -------
    # Область, не найденная разбором, дала бы отсутствующее равным
    # отсутствующему, и сличение трёх счётов зеленело бы на ответе, не несущем
    # ни одного из них.
    ruler_region = _oob_region(body, SCHED_COUNT_NODE_ID)
    assert ruler_region is not None, (
        f"области линейки счётчика ({SCHED_COUNT_NODE_ID}) в теле ответа НЕТ — "
        f"сличать нечего, и правило утверждало бы не о том предмете. Тело: "
        f"{body!r}"
    )
    summary_region = _oob_region(body, AD_SUMMARY_NODE_ID)
    assert summary_region is not None, (
        f"ОБЛАСТИ СВОДКИ ОБЪЯВЛЕНИЯ ({AD_SUMMARY_NODE_ID}) В ТЕЛЕ ОТВЕТА НЕТ "
        f"ВОВСЕ. Это НЕ расхождение чисел, а его причина: фрагментный ответ "
        f"удаления этой области не шлёт, и сводка остаётся такой, какой её "
        f"застала последняя полная загрузка страницы — то есть УСТАРЕВШЕЙ до "
        f"следующей перезагрузки, всё это время глядя человеку в глаза "
        f"(гэп G-10-6). Тело: {body!r}"
    )

    ruler_count = _first_integer(ruler_region)
    assert ruler_count is not None, (
        f"в области линейки счётчика не напечатано ни одного числа: "
        f"{ruler_region!r}"
    )
    summary_cell = _summary_row(summary_region, "Расписания")
    assert summary_cell is not None, (
        f"в сводке нет строки «Расписания» — число, о котором говорит гэп, в "
        f"области не напечатано вовсе: {summary_region!r}"
    )
    summary_count = _first_integer(summary_cell)
    assert summary_count is not None, (
        f"в строке «Расписания» сводки не напечатано числа: {summary_cell!r}"
    )

    # --- СЛИЧЕНИЕ ТРЁХ СЧЁТОВ ----------------------------------------------
    on_server = await _server_schedule_count(db_session, ad_id)
    assert (ruler_count, summary_count) == (on_server, on_server), (
        f"два числа ОДНОГО экрана противоречат друг другу либо серверу: "
        f"линейка списка {ruler_count}, сводка предпросмотра {summary_count}, "
        f"на сервере {on_server}. Своп СОСТОЯЛСЯ и прошёл успешно, статус "
        f"двухсотый, консоль чистая — признака отказа нет НИ ОДНОГО, и увидит "
        f"расхождение только глаз, и только если смотреть на обе области сразу"
    )


@pytest.mark.asyncio
async def test_the_summary_next_run_follows_the_delete(
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Вторая строка сводки двигается вместе с числом, а не остаётся прежней.

    ⚠️ ЗАЧЕМ ОТДЕЛЬНОЕ ПРАВИЛО. Гэп назван ЧИСЛОМ расписаний, но устаревает в
    сводке НЕ ТОЛЬКО оно: строка «Ближайший запуск» читает ТОТ ЖЕ контекст
    редактора и разошлась бы с сервером так же молча. Правило заводится сейчас
    потому, что предмет ОБЩИЙ, а не потому, что дефект наблюдён обоими глазами.

    Стенд: два расписания с РАЗНЫМИ моментами запуска; удаляется то, чей момент
    БЛИЖЕ. Сводка ответа обязана назвать момент ОСТАВШЕГОСЯ расписания.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    sooner = await _seed_schedule(db_session, ad.id, account.id)
    later = await _seed_schedule(db_session, ad.id, account.id)
    # Моменты разводятся ПРЯМОЙ правкой строк: `_seed_schedule` ставит всем
    # включённым строкам ОДИН момент, а правило о «ближайшем» на совпадающих
    # моментах не отличало бы оставшуюся строку от удалённой.
    # ⚠️ МОМЕНТ УДАЛЯЕМОЙ СТРОКИ СНИМАЕТСЯ В ИМЯ, А НЕ ВЫЧИСЛЯЕТСЯ ДВАЖДЫ
    # (WR-08). Ниже он нужен ВТОРОЙ раз — для отображения момента УДАЛЁННОЙ
    # строки, — и два независимых вызова относительного помощника разошлись бы
    # на границе минуты: отказ ПРИБОРА, редкий ровно настолько, чтобы его
    # разбирали как дефект предмета.
    removed_run_at = a_future_run_moment(1)
    sooner.next_run_at = removed_run_at
    later.next_run_at = a_future_run_moment(9)
    await db_session.commit()
    remaining_run_at = later.next_run_at

    response = await htmx_client.post(
        f"/schedules/{sooner.id}/delete",
        content=_editor_delete_body(ad),
        headers=FORM_HEADERS,
    )

    assert response.status_code == 200
    summary_region = _oob_region(response.text, AD_SUMMARY_NODE_ID)
    assert summary_region is not None, (
        f"области сводки объявления ({AD_SUMMARY_NODE_ID}) в теле ответа нет "
        f"вовсе — вторая строка сводки устаревает вместе с первой, и по тому же "
        f"основанию: ответ этой области не шлёт. Тело: {response.text!r}"
    )
    shown = _summary_row(summary_region, "Ближайший запуск")
    assert shown is not None, (
        f"в сводке нет строки «Ближайший запуск»: {summary_region!r}"
    )

    # Ожидание собирается ТЕМ ЖЕ помощником отображения времени, что и разметка:
    # литерал разошёлся бы с зоной пользователя и краснил бы правило на чужом
    # предмете (тот же приём, что `_rendered_counter_line` соседнего модуля).
    expected = format_datetime_for_user(remaining_run_at, owner, "%d.%m %H:%M")
    removed = format_datetime_for_user(removed_run_at, owner, "%d.%m %H:%M")
    assert expected != removed, (
        f"моменты удалённой и оставшейся строк отобразились ОДИНАКОВО "
        f"({expected!r}) — сличение перестало различать строки, и вердикт "
        f"правила был бы неотличим от вердикта на устаревшей сводке"
    )
    assert shown == expected, (
        f"сводка называет ближайшим запуском {shown!r}, а после удаления "
        f"ближайшей строки им стал {expected!r} (момент удалённой строки — "
        f"{removed!r}). Вторая строка сводки осталась при значении, которого на "
        f"сервере больше нет"
    )


@pytest.mark.asyncio
async def test_the_summary_node_is_a_top_level_child_of_the_response(
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Узел сводки — ПРЯМОЙ ребёнок тела ответа, а не вложенный узел.

    Блок конфигурации несёт `allowNestedOobSwaps: false`
    (`includes/htmx_config.html`): у ВЛОЖЕННОГО внеполосного узла рантайм МОЛЧА
    снимает признак и не свопает ВОВСЕ — ни ошибки, ни предупреждения, ни
    отличия в статусе. Ответ при этом остаётся двухсотым, тело — прежним, и
    отличить «сводка приехала» от «сводка приехала и была выброшена» нельзя
    ничем, кроме глаза на экране.

    ⚠️ ПРАВИЛО ЧИТАЕТ ТЕЛО ОТВЕТА, А НЕ ШАБЛОН: предмет — то, что УЕХАЛО, а не
    то, что набрано. Обёртка, появившаяся вокруг включения, в шаблоне ответа не
    видна вовсе.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)
    await _seed_schedule(db_session, ad.id, account.id)

    response = await htmx_client.post(
        f"/schedules/{schedule.id}/delete",
        content=_editor_delete_body(ad),
        headers=FORM_HEADERS,
    )

    assert response.status_code == 200
    body = response.text

    # --- АНТИВАКУУМ РАЗБОРЩИКА: ГЛУБИНА ИЗМЕРЯЕТСЯ, А НЕ ВОЗВРАЩАЕТСЯ НУЛЁМ --
    # Разборщик, отдающий ноль ВСЕГДА, зеленил бы правило на любом теле. Зубы
    # прибора показываются на СИНТЕТИКЕ: тот же узел, обёрнутый одним тегом,
    # обязан измериться глубиной один.
    wrapped = f'<div><div id="{AD_SUMMARY_NODE_ID}" hx-swap-oob="true">x</div></div>'
    wrapped_node = _oob_node(wrapped, AD_SUMMARY_NODE_ID)
    assert wrapped_node is not None and wrapped_node.depth == 1, (
        f"разборщик не измерил глубину обёрнутого узла ({wrapped_node!r}) — "
        f"его ноль на живом теле не означал бы ничего"
    )

    node = _oob_node(body, AD_SUMMARY_NODE_ID)
    assert node is not None, (
        f"узла сводки объявления ({AD_SUMMARY_NODE_ID}) в теле ответа нет "
        f"вовсе. Тело: {body!r}"
    )
    assert node.depth == 0, (
        f"узел сводки объявления стоит на глубине {node.depth}, а обязан быть "
        f"ПРЯМЫМ ребёнком тела ответа. Вложенному узлу рантайм МОЛЧА снимает "
        f"признак внеполосной подмены (`allowNestedOobSwaps: false`): ответ "
        f"остаётся двухсотым, узел в теле присутствует, а на экране не "
        f"меняется ничего. Тело: {body!r}"
    )


# --- Фаза 10, план 10-50, задача 3: зубы четвёртого узла ----------------------
#
# ⚠️ ПРАВИЛА НИЖЕ УТВЕРЖДАЮТ ПОВЕДЕНИЕ И РАЗМЕТКУ ПОРОЗНЬ, И ГРАНИЦА МЕЖДУ НИМИ
# НАЗЫВАЕТСЯ, А НЕ ПОДРАЗУМЕВАЕТСЯ. Единственность источника разметки —
# свойство ДЕРЕВА (две копии разошлись бы молча); цена пути деградации и
# неприкосновенность ветки перехода — свойства ИСПОЛНЕНИЯ, и предъявляются они
# счётом запросов и телом ответа, а не вхождением подстроки.

AD_SUMMARY_RULE_SOURCE = "ads/includes/summary.html"

# Признаков ДВА, и второй — не осторожность, а измерение. Первый — ПОДПИСЬ
# строки сводки; сама по себе она могла бы встретиться в прозе о сводке. Второй
# — ИМЯ ВЕЛИЧИНЫ, которую сводка печатает: это КОНТРАКТ с контекстом редактора,
# а не подпись, — переводу и правкам UI он не подлежит. Признаком считается
# СОВПАДЕНИЕ ОБОИХ: подпись без величины — проза о сводке, величина без подписи
# — соседний экран (`dashboard/includes/upcoming_row.html` печатает тот же
# момент запуска СВОЕЙ разметкой; это другой экран и отдельное UI-ревью, и в
# множество источников сводки объявления он НЕ ВХОДИТ).
AD_SUMMARY_RULE_MARKERS = ("Ближайший запуск", "editor.next_run_at")

# ⚠️ МЕСТ ВКЛЮЧЕНИЯ ТРИ, И ЧИСЛО ПОСТАВЛЕНО ЗАМЕРОМ ДЕРЕВА, А НЕ УНАСЛЕДОВАНО.
# План 10-50 объявлял ДВА («при двух местах включения»), и это число было верно
# ДО него в другом смысле: два места существовали до появления четвёртого узла
# (страница редактора и ответ автосохранения). Настоящий план добавил ТРЕТЬЕ, и
# перечень назван поимённо — правило, утверждающее число, которого в дереве нет,
# краснело бы на верном дереве.
AD_SUMMARY_RULE_USERS = (
    "ads/form.html",
    "ads/includes/autosave_response.html",
    "ads/partials/sched_delete_response.html",
)

AD_SUMMARY_RULE_INCLUDE = re.compile(
    r"\{%-?\s*include\s+['\"]" + re.escape(AD_SUMMARY_RULE_SOURCE) + r"['\"]"
)

JINJA_COMMENT_RE = re.compile(r"\{#.*?#\}", re.S)

# Три запроса ОТЛОЖЕННОЙ СБОРКИ фрагмента, названные СИГНАТУРОЙ СВОЕГО SQL.
#
# ⚠️ ГРАНИЦА ПРАВИЛА НАЗЫВАЕТСЯ ЗДЕСЬ ЦЕЛИКОМ: оно считает запросы ОДНОГО
# обработчика на ОДНОМ пути и не утверждает НИЧЕГО о числе запросов проекта
# вообще. Наблюдение идёт по событию исполнения ORM ТОЙ ЖЕ сессии, которую
# обработчик получает подменой зависимости, — то есть меряется ИСПОЛНЕНИЕ, а не
# исходник: чтение, тихо переехавшее наружу отложенной сборки, обязано краснить
# прогон, и обещанием `IN-03` быть перестало.
#
# ⚠️ СИГНАТУРА СЧЁТА СУЖЕНА ДО НАЧАЛА ЗАПРОСА, И ЭТО ЗАМЕР, А НЕ ОСТОРОЖНОСТЬ.
# Первая форма («в тексте встречается `count(`») краснила правило на ВЕРНОМ
# дереве: путь деградации исполняет счётчики боковой навигации шелла
# (`count(*) AS ads, … AS schedules, … AS history`), к отложенной сборке
# отношения не имеющие. Это тот же класс дефекта прибора, что расхождение Р-1
# обхода — СЕЛЕКТОР ШИРЕ ПРЕДМЕТА, — и он назван здесь, потому что был
# ИЗМЕРЕН на этом самом правиле, а не предположен.
DEFERRED_READ_SIGNATURES = {
    "счёт расписаний объявления": lambda sql: sql.startswith(
        "SELECT count(schedules.id)"
    ),
    "строка объявления владельца": lambda sql: sql.startswith("SELECT ads."),
    "ближайший момент запуска": lambda sql: sql.startswith(
        "SELECT schedules.next_run_at"
    ),
}


@contextmanager
def _observed_statements(db: AsyncSession):
    """Тексты запросов, ИСПОЛНЕННЫХ сессией внутри блока.

    Наблюдатель снимается в `finally`: переживший свой блок, он считал бы
    запросы соседнего правила и давал бы отказ, не относящийся к предмету.
    """
    seen: list[str] = []

    def _record(state) -> None:
        seen.append(str(state.statement))

    event.listen(db.sync_session, "do_orm_execute", _record)
    try:
        yield seen
    finally:
        event.remove(db.sync_session, "do_orm_execute", _record)


def _deferred_reads_in(statements: list[str]) -> set[str]:
    """Имена тех отложенных чтений, чья сигнатура нашлась среди исполненных."""
    return {
        name
        for name, matches in DEFERRED_READ_SIGNATURES.items()
        if any(matches(sql) for sql in statements)
    }


def test_the_ad_summary_markup_has_exactly_one_source() -> None:
    """Разметка сводки объявления существует РОВНО ОДНИМ источником.

    Правило из двух половин, и убрать можно только обе сразу — форма взята у
    `test_the_schedule_counter_markup_has_exactly_one_source`
    (`tests/test_templates/test_htmx_markup_gates.py`) и по тому же основанию.

    (i)  Файл, несущий разметку сводки собственным текстом, ровно один, и это
         именно файл общего источника. Две копии расходятся МОЛЧА: статус
         ответа останется двухсотым, консоль — чистой, и человек видел бы РАЗНОЕ
         в зависимости от того, перезагрузил он страницу или удалил расписание,
         — то есть РОВНО гэп `G-10-6`, только внесённый заново разметкой вместо
         контекста.
    (ii) АНТИВАКУУМНАЯ ПОЛОВИНА, И ОНА СТОИ́Т ПЕРВОЙ: включающих файлов НЕ НОЛЬ,
         и каждый назван поимённо. Без неё «источник один» зеленело бы на
         источнике, которого не включает никто: ноль копий — тоже «не больше
         одной».
    """
    sources_by_template = {
        path.relative_to(TEMPLATES_DIR).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(TEMPLATES_DIR.rglob("*.html"))
    }

    # --- АНТИВАКУУМ ПЕРВЫМ -------------------------------------------------
    assert AD_SUMMARY_RULE_USERS, (
        "перечень мест включения сводки ПУСТ — правило зелено вакуумом и "
        "перестало отличать соблюдение от поломки"
    )
    not_including = [
        user
        for user in AD_SUMMARY_RULE_USERS
        if user not in sources_by_template
        or not AD_SUMMARY_RULE_INCLUDE.search(
            JINJA_COMMENT_RE.sub("", sources_by_template[user])
        )
    ]
    assert not not_including, (
        f"место отрисовки сводки объявления не включает общий источник: "
        f"{not_including} — половина (i) правила зелена и от того, что сводку "
        f"сняли отовсюду, поэтому все точки отрисовки утверждаются поимённо"
    )

    sources = sorted(
        rel
        for rel, source in sources_by_template.items()
        if all(
            marker in JINJA_COMMENT_RE.sub("", source)
            for marker in AD_SUMMARY_RULE_MARKERS
        )
    )
    assert sources == [AD_SUMMARY_RULE_SOURCE], (
        f"разметка сводки объявления найдена в файлах {sources}, а источник "
        f"обязан быть один — {AD_SUMMARY_RULE_SOURCE!r}: пока копий больше "
        f"одной, правка формулировки или состава строк в любой из них разводит "
        f"СВОДКУ ПОСЛЕ УДАЛЕНИЯ СО СВОДКОЙ ПОСЛЕ ПЕРЕЗАГРУЗКИ, и разойдутся они "
        f"МОЛЧА"
    )


# Признак запроса от слоя письма, ПИСЬМЕННО. Литерал стои́т здесь, а не берётся
# у фикстуры `htmx_client`, по ИЗМЕРЕННОМУ основанию: фикстура ставит заголовок
# в УМОЛЧАНИЯ КЛИЕНТА и возвращает ТОТ ЖЕ объект, что `authed_client`, — то есть
# правило, запросившее обе фикстуры, получило бы признак htmx на ОБОИХ своих
# запросах, и половина деградации мерила бы путь htmx (замер 2026-09-11: путь
# «без htmx» ответил 200 с фрагментом). Форма перенята у
# `tests/test_pages/test_confirm_delete_transport.py`, где литерал стои́т по
# тому же основанию, что выписано у самой фикстуры: единственность, которую
# держит веха, — единственность ЧТЕНИЯ признака приложением; здесь признак
# ПИШЕТСЯ, и пишущая сторона — клиент.
HTMX_HEADERS = {"HX-Request": "true"}


@pytest.mark.asyncio
async def test_the_degraded_path_runs_none_of_the_deferred_reads(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Цена пути деградации предъявляется СЧЁТОМ ЗАПРОСОВ, а не обещанием (IN-03).

    Отложенная сборка фрагмента выросла с ОДНОГО запроса до ТРЁХ, и платит за
    них ТОЛЬКО путь htmx с признаком возврата в редактор. Человек без
    JavaScript получает прежнее перенаправление и не платит ни одним из трёх:
    разметка, которая ему всё равно не уедет, не собирается вовсе.

    ⚠️ ПОЛОЖИТЕЛЬНАЯ ПОЛОВИНА СТОИ́Т ПЕРВОЙ, И ОНА НЕ ГИГИЕНА. Без неё правило
    зеленело бы на сигнатурах, не совпадающих НИ С ЧЕМ: пустое пересечение с
    пустым множеством даёт зелёный цвет, посимвольно равный зелёному цвету
    соблюдённого правила. Сначала предъявляется, что все три сигнатуры НАХОДЯТ
    свои запросы, и только потом — что на соседнем пути они не находят ни
    одного.

    ⚠️ ГРАНИЦА: правило считает запросы ОДНОГО обработчика на ОДНОМ пути и не
    утверждает ничего о числе запросов проекта вообще.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    on_htmx = await _seed_schedule(db_session, ad.id, account.id)
    on_degraded = await _seed_schedule(db_session, ad.id, account.id)
    # Третья строка держит ОБА запроса на фрагментной развилке: после двух
    # удалений объявление обязано остаться непустым, иначе второй запрос ушёл бы
    # в ветку перехода и мерил бы другую ветку, а не другой транспорт.
    await _seed_schedule(db_session, ad.id, account.id)
    body = _editor_delete_body(ad)

    # --- ПОЛОЖИТЕЛЬНАЯ ПОЛОВИНА: НА ПУТИ HTMX ИСПОЛНЯЮТСЯ ВСЕ ТРИ ----------
    with _observed_statements(db_session) as on_fragment_path:
        fragment = await authed_client.post(
            f"/schedules/{on_htmx.id}/delete",
            content=body,
            headers={**FORM_HEADERS, **HTMX_HEADERS},
            follow_redirects=False,
        )

    assert fragment.status_code == 200, (
        f"путь htmx ответил {fragment.status_code} вместо 200 — отложенной "
        f"сборки не случилось, и мерить было нечего"
    )
    executed = _deferred_reads_in(on_fragment_path)
    assert executed == set(DEFERRED_READ_SIGNATURES), (
        f"на пути htmx исполнились не все чтения отложенной сборки: найдены "
        f"{sorted(executed)}, объявлены {sorted(DEFERRED_READ_SIGNATURES)}. "
        f"Сигнатура, не находящая своего запроса, делает вторую половину "
        f"правила вакуумной: она ищет то, чего не находит нигде. Исполненные "
        f"запросы: {on_fragment_path!r}"
    )

    # --- ПРЕДМЕТ: НА ПУТИ ДЕГРАДАЦИИ НЕ ИСПОЛНЯЕТСЯ НИ ОДНО ----------------
    with _observed_statements(db_session) as on_degraded_path:
        degraded = await authed_client.post(
            f"/schedules/{on_degraded.id}/delete",
            content=body,
            headers=FORM_HEADERS,
            follow_redirects=False,
        )

    assert degraded.status_code == 302, (
        f"путь деградации ответил {degraded.status_code} вместо 302 — человек "
        f"без JavaScript остался бы без ответа, и правило мерило бы не тот путь"
    )
    assert degraded.headers["location"] == f"/ads/{ad.id}/edit"
    leaked = _deferred_reads_in(on_degraded_path)
    assert leaked == set(), (
        f"на пути БЕЗ заголовка htmx исполнились чтения отложенной сборки: "
        f"{sorted(leaked)}. Это и есть `IN-03`, переставший держаться: человек "
        f"без JavaScript платит запросами за разметку, которая ему НЕ УЕДЕТ "
        f"вовсе. Исполненные запросы: {on_degraded_path!r}"
    )


@pytest.mark.asyncio
async def test_the_transition_branch_sends_no_summary_node(
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Удаление ПОСЛЕДНЕГО расписания по-прежнему уходит в ветку перехода (D-04).

    ⚠️ ПРАВИЛО НЕ ИЗБЫТОЧНО ПРИ ЖИВЫХ ПРАВИЛАХ ВЕТВЛЕНИЯ, И ОСНОВАНИЕ НАЗЫВАЕТСЯ
    ПРЯМО. Настоящий план добавил в отложенную сборку два чтения и узел сводки,
    и соблазн подать сводку «на всякий случай» и на переходной ветке — прямой.
    Второй экземпляр пустого состояния запрещён решением D-04: ветка «расписаний
    пока нет» живёт в `ads/form.html` в ОДНОМ экземпляре, и второй её отрисовкой
    она разошлась бы с первой молча. Запрет обязан иметь зубы ИМЕННО СЕЙЧАС.

    Опустевший редактор закрывается ПЕРЕХОДОМ: фрагмент не собирается вовсе,
    узла сводки в ответе нет — и это объявленное поведение, а не дефект.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    only = await _seed_schedule(db_session, ad.id, account.id)

    response = await htmx_client.post(
        f"/schedules/{only.id}/delete",
        content=_editor_delete_body(ad),
        headers=FORM_HEADERS,
    )

    assert response.status_code == 204, (
        f"удаление последнего расписания ответило {response.status_code} вместо "
        f"204 — редактор перестал закрываться переходом, и пустое состояние "
        f"обзавелось вторым экземпляром (D-04)"
    )
    assert response.headers.get("HX-Location") == f"/ads/{ad.id}/edit", (
        f"заголовок перехода {response.headers.get('HX-Location')!r} не равен "
        f"адресу редактора объявления"
    )
    assert response.text == "", (
        f"у ответа 204 появилось тело — у этого статуса тела нет по "
        f"определению: {response.text!r}"
    )
    assert _oob_node(response.text, AD_SUMMARY_NODE_ID) is None, (
        "узел сводки приехал на ПЕРЕХОДНОЙ ветке, где тела нет вовсе"
    )

"""Фаза 17, план 05 (PHONE-06): номер на админских экранах рядом с отдельным `#id`.

Администратор работает по идентификатору (логи, контейнеры, очередь), и номер
ему — подсказка, а не замена (D-04, D-17). Поэтому на экранах «Воркеры»,
«Очередь» и в карточке пользователя подряд стоят три вещи: канал, номер (или
приглушённое «Номер неизвестен») и ОТДЕЛЬНЫЙ `#id` — всегда, у двойников и у
недвойников одинаково (D-17: в админке `account_label(..., with_twin_id=false)`
и отдельный `account_id_mark`).

Подпись и знак находятся по АДРЕСУ элемента (`data-account-label`,
`data-account-id`), а не вхождением `"#1" in html`: подстрока `#1` входит в
`#10`, а слово «Номер неизвестен» у соседа засчитало бы подпись не тому
аккаунту (D-06). Фальшивки Redis ввозятся из `test_admin_panel` — вторая копия
разошлась бы с первой молча (прецедент ввоза между модулями тестов —
`test_confirmation_panel_settle.py`).
"""

from __future__ import annotations

import re
import time
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from tests.account_label_support import (
    id_mark_texts,
    label_texts,
    muted_label_ids,
    seed_account,
)
from tests.test_pages.test_admin_panel import _fake_redis

PHONE_STORED = "+79991234567"
PHONE_SHOWN = "+7 999 123-45-67"
UNKNOWN = "Номер неизвестен"


async def _admin_user_id(db_session: AsyncSession) -> int:
    """Владелец засеянных аккаунтов — единственный пользователь, созданный `admin_client`."""
    return (await db_session.execute(select(User))).scalars().first().id


def _workers_redis():
    """Двойник Redis для «Воркеров»: три службы инфраструктуры и один живой воркер."""
    fresh = str(int(time.time() * 1000))
    return _fake_redis([fresh, fresh, fresh], [fresh, 0])


async def _get_workers(admin_client: AsyncClient, path: str) -> str:
    with patch("app.services.ops_state._get_redis", return_value=_workers_redis()):
        response = await admin_client.get(path)
    assert response.status_code == 200, f"{path}: {response.status_code}"
    return response.text


# ---- Строка воркера ----


@pytest.mark.asyncio
async def test_the_worker_row_shows_the_number_and_the_id(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """ТРАССЕР: строка воркера даёт номер по `data-account-label` и `#id` по `data-account-id`."""
    account_id = await seed_account(
        db_session, await _admin_user_id(db_session), "wa", phone=PHONE_STORED
    )

    html = await _get_workers(admin_client, "/admin/workers")

    assert label_texts(html)[str(account_id)] == [PHONE_SHOWN]
    assert id_mark_texts(html)[str(account_id)] == [f"#{account_id}"]


@pytest.mark.asyncio
async def test_the_worker_id_stays_a_link_to_its_logs(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """`#id` по-прежнему ссылка на логи ЭТОГО воркера (D-17): знак лежит внутри `<a href=…>`."""
    account_id = await seed_account(
        db_session, await _admin_user_id(db_session), "wa", phone=PHONE_STORED
    )

    html = await _get_workers(admin_client, "/admin/workers")

    links = re.findall(
        rf'<a href="/admin/logs\?source={account_id}"[^>]*>(.*?)</a>', html, flags=re.S
    )
    assert len(links) == 1, f"ссылка на логи воркера {account_id}: найдено {len(links)}"
    assert f'data-account-id="{account_id}"' in links[0], (
        "ссылка на логи не обёрнула отдельный знак #id"
    )
    assert "data-account-label" not in links[0], (
        "номер попал внутрь ссылки на логи: ссылка ведёт по идентификатору, а не по номеру"
    )


@pytest.mark.asyncio
async def test_an_unknown_worker_number_is_muted_and_keeps_the_id(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Аккаунт без номера: приглушённое «Номер неизвестен», а `#id` на месте всё равно."""
    account_id = await seed_account(db_session, await _admin_user_id(db_session), "wa")

    html = await _get_workers(admin_client, "/admin/workers")

    assert label_texts(html)[str(account_id)] == [UNKNOWN]
    assert str(account_id) in muted_label_ids(html), "«Номер неизвестен» не приглушён"
    assert id_mark_texts(html)[str(account_id)] == [f"#{account_id}"]


@pytest.mark.asyncio
async def test_the_worker_partial_matches_the_page_label(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Паршал опроса несёт тот же адрес и тот же текст, что первичная страница (D-02)."""
    account_id = await seed_account(
        db_session, await _admin_user_id(db_session), "wa", phone=PHONE_STORED
    )

    page = await _get_workers(admin_client, "/admin/workers")
    partial = await _get_workers(admin_client, "/admin/workers/partial")

    assert label_texts(partial)[str(account_id)] == [PHONE_SHOWN]
    assert id_mark_texts(partial)[str(account_id)] == [f"#{account_id}"]
    assert label_texts(partial)[str(account_id)] == label_texts(page)[str(account_id)]


# ---- Очередь и карточка пользователя ----


def _queue_html_pieces(html: str) -> tuple[str, str]:
    """(заголовок аккаунта, разметка строки очереди) — тексты режутся по адресу, а не по странице.

    Строка очереди кончается первым закрывающим `</div>`: ячейки строки состоят
    из `<span>`, вложенных блоков в них нет (та же посылка, что у `_row_markup`).
    """
    heading = re.search(r'<h3 class="card__title">(.*?)</h3>', html, flags=re.S)
    assert heading is not None, "заголовок аккаунта в очереди не найден"
    rows = html.split("<div data-row data-queue-row")[1:]
    assert len(rows) == 1, f"строк очереди найдено {len(rows)}, ожидалась одна"
    return heading.group(1), rows[0][: rows[0].index("</div>")]


async def _get_queue(admin_client: AsyncClient, account_id: int) -> str:
    from tests.test_pages.test_admin_panel import _FakeQueuePageRedis, _queue_task

    client = _FakeQueuePageRedis({f"wa:queue:{account_id}": [_queue_task("task-one")]})
    with patch("app.services.ops_state._get_redis", return_value=client):
        response = await admin_client.get("/admin/queue")
    assert response.status_code == 200
    return response.text


@pytest.mark.asyncio
async def test_the_queue_row_shows_the_number_and_the_id(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Строка очереди: канал, номер по `data-account-label` и отдельный `#id` (D-17)."""
    account_id = await seed_account(
        db_session, await _admin_user_id(db_session), "wa", phone=PHONE_STORED
    )

    html = await _get_queue(admin_client, account_id)
    _heading, row = _queue_html_pieces(html)

    assert label_texts(row)[str(account_id)] == [PHONE_SHOWN]
    assert id_mark_texts(row)[str(account_id)] == [f"#{account_id}"]
    assert "WhatsApp" in row, "канал в строке очереди не назван"


@pytest.mark.asyncio
async def test_the_queue_heading_keeps_the_id_and_gains_the_number(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Заголовок «Аккаунт #5» сохраняет `#id` и получает номер рядом через « · » (D-17)."""
    account_id = await seed_account(
        db_session, await _admin_user_id(db_session), "wa", phone=PHONE_STORED
    )

    html = await _get_queue(admin_client, account_id)
    heading, _row = _queue_html_pieces(html)

    assert "Аккаунт" in heading
    assert id_mark_texts(heading)[str(account_id)] == [f"#{account_id}"]
    assert label_texts(heading)[str(account_id)] == [f"WhatsApp {PHONE_SHOWN}"]
    plain = " ".join(re.sub(r"<[^>]+>", " ", heading).split())
    assert plain == f"Аккаунт #{account_id} · WhatsApp {PHONE_SHOWN}", plain


@pytest.mark.asyncio
async def test_the_user_card_names_the_channel_and_the_number(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Карточка пользователя: «Telegram» вместо сырого `tg_user`, номер и отдельный `#id` (D-11)."""
    user_id = await _admin_user_id(db_session)
    account_id = await seed_account(db_session, user_id, "tg_user", phone=PHONE_STORED)

    response = await admin_client.get(f"/admin/users/{user_id}")
    assert response.status_code == 200
    html = response.text

    assert label_texts(html)[str(account_id)] == [f"Telegram {PHONE_SHOWN}"]
    assert id_mark_texts(html)[str(account_id)] == [f"#{account_id}"]
    assert f"tg_user #{account_id}" not in html, "сырой тип канала остался в карточке"

"""Захват номера при подключении WhatsApp: опросчик `GET /accounts/connect/wa/status` (Фаза 19, план 19-05).

PHONE-13 / PHONE-15, сторона приложения. Воркер WA отдаёт в `/status` поле `phone`
(строка цифр E.164 без `+` или `null`); опросчик читает его одним дополнительным
GET после `connected: true` и пишет номер в том же коммите, что и переход в
`syncing`.

АДАПТЕР НАСТОЯЩИЙ. Подменено только то, что стоит на границе процесса: адрес
контейнера воркера (`app.messengers.whatsapp.ensure_wa_container`), HTTP-клиент
(`app.messengers.whatsapp.get_http_client`, ответы `/status` и `/qr`) и модуль
очереди (`app.worker.celery_app`, образец `tests/test_pages/test_history_retry.py`).
Поэтому каждый тест проходит разбор тела, адаптер, обработчик, помощник захвата
и единственного писателя без единой подмены собственного кода фазы.

ПОСТЫ ИДУТ НА ЛИТЕРАЛЬНЫЕ АДРЕСА, а утверждений `302` здесь нет: опросчики — GET,
числа сквозных гейтов (`tests/test_pages/test_htmx_post_pairs.py`) не двигаются.
Номер сеется только через `tests/account_label_support.py::seed_account`.
"""

import contextlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messenger_account import MessengerAccount
from app.models.user import User
from tests.account_label_support import MANUAL_MARK, label_texts, seed_account

WORKER = "http://wa-worker.test:3000"
REPORTED = "79991234567"
DISPLAY_FORM = "+7 999 123-45-67"
STORED_FORM = "+79991234567"
CONNECTED_TEXT = "WhatsApp подключён!"
SYNC_TASK = "app.worker.tasks.sync_wa_groups"


@pytest_asyncio.fixture
async def owner(authed_client: AsyncClient, db_session: AsyncSession) -> User:
    return (
        await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


@contextlib.contextmanager
def wa_worker_answers(*bodies: dict):
    """Воркер WA отвечает 200 телами из `bodies` по порядку запросов; отдаёт `(get, send_task)`."""
    client = MagicMock()
    client.get = AsyncMock(side_effect=[httpx.Response(200, json=body) for body in bodies])
    fake_queue = MagicMock()
    with patch("app.messengers.whatsapp.ensure_wa_container", return_value=WORKER):
        with patch("app.messengers.whatsapp.get_http_client", return_value=client):
            with patch.dict(sys.modules, {"app.worker.celery_app": fake_queue}):
                yield client.get, fake_queue.celery.send_task


async def _row(db: AsyncSession, account_id: int) -> MessengerAccount:
    db.expire_all()
    return (
        await db.execute(select(MessengerAccount).where(MessengerAccount.id == account_id))
    ).scalar_one()


@pytest.mark.asyncio
async def test_a_wa_connection_stores_the_number_the_worker_reported(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-01, PHONE-13: номер из `/status` и `syncing` уходят одним коммитом; подпись в списке — с номером."""
    aid = await seed_account(db_session, owner.id, "wa", status="connecting")
    connected = {"connected": True, "exists": True, "syncState": None, "phone": REPORTED}

    with wa_worker_answers(connected, connected) as (get_mock, send_task):
        response = await authed_client.get("/accounts/connect/wa/status")

    assert response.status_code == 200
    assert CONNECTED_TEXT in response.text
    assert REPORTED not in response.text and DISPLAY_FORM not in response.text, (
        "шаг «Подключено» показал номер (D-12)"
    )

    row = await _row(db_session, aid)
    assert row.phone == STORED_FORM, "опрос подключения WA не записал номер из /status"
    assert row.phone_is_manual is False
    assert row.status == "syncing"
    assert row.credentials == str(aid)

    assert send_task.call_count == 1
    assert send_task.call_args.args == (SYNC_TASK,)
    assert send_task.call_args.kwargs == {"args": [aid]}
    assert get_mock.await_count == 2
    assert [call.args[0] for call in get_mock.await_args_list] == [
        f"{WORKER}/api/sessions/{aid}/status"
    ] * 2

    listing = await authed_client.get("/accounts")
    labels = label_texts(listing.text)[str(aid)]
    assert labels and all(DISPLAY_FORM in text for text in labels), labels
    assert all(MANUAL_MARK not in text for text in labels), labels


async def _poll_and_read(
    client: AsyncClient, db: AsyncSession, account_id: int, *bodies: dict
) -> tuple[httpx.Response, MessengerAccount, AsyncMock, MagicMock]:
    """Один опрос подключения с заданными ответами воркера; строка перечитана из базы."""
    with wa_worker_answers(*bodies) as (get_mock, send_task):
        response = await client.get("/accounts/connect/wa/status")
    return response, await _row(db, account_id), get_mock, send_task


def _assert_connected_and_syncing(response, row, send_task, account_id: int) -> None:
    assert response.status_code == 200
    assert CONNECTED_TEXT in response.text, response.text
    assert row.status == "syncing"
    assert row.credentials == str(account_id)
    assert send_task.call_count == 1
    assert send_task.call_args.args == (SYNC_TASK,)
    assert send_task.call_args.kwargs == {"args": [account_id]}


@pytest.mark.asyncio
async def test_an_old_worker_status_connects_the_wa_account_with_an_unknown_number(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-05, PHONE-15, критерий 4: `/status` старой формы без поля `phone` подключает аккаунт как раньше.

    Это чистое доказательство «номер остаётся неизвестен» на WA: у WA формы
    ввода номера нет. Решение владельца OQ1 (2026-11-22) для MAX — план 19-07.
    """
    aid = await seed_account(db_session, owner.id, "wa", status="connecting")
    old_shape = {"connected": True, "exists": True, "syncState": None}

    response, row, _get, send_task = await _poll_and_read(
        authed_client, db_session, aid, old_shape, old_shape
    )

    _assert_connected_and_syncing(response, row, send_task, aid)
    assert row.phone is None, f"старая форма /status записала номер: {row.phone!r}"


@pytest.mark.asyncio
async def test_a_lid_only_session_leaves_the_number_unknown(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-03: воркер отдал `phone: null` (LID или пусто) — аккаунт подключён, номер неизвестен."""
    aid = await seed_account(db_session, owner.id, "wa", status="connecting")
    lid_only = {"connected": True, "exists": True, "syncState": None, "phone": None}

    response, row, _get, send_task = await _poll_and_read(
        authed_client, db_session, aid, lid_only, lid_only
    )

    _assert_connected_and_syncing(response, row, send_task, aid)
    assert row.phone is None
    listing = await authed_client.get("/accounts")
    labels = label_texts(listing.text)[str(aid)]
    assert labels and all("Номер неизвестен" in text for text in labels), labels
    assert all(MANUAL_MARK not in text for text in labels), labels


@pytest.mark.asyncio
async def test_a_failing_capture_still_connects_the_account(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
    monkeypatch,
    caplog,
):
    """D-05, T-19-15, T-19-17: сбой писателя откатывает сейвпоинт, но не подключение; номера в журнале нет."""
    aid = await seed_account(db_session, owner.id, "wa", status="connecting")
    monkeypatch.setattr(
        "app.application.accounts.connect_phone.fill_reported_phone",
        AsyncMock(side_effect=RuntimeError(f"boom {REPORTED}")),
    )
    connected = {"connected": True, "exists": True, "syncState": None, "phone": REPORTED}

    with caplog.at_level("INFO"):
        response, row, _get, send_task = await _poll_and_read(
            authed_client, db_session, aid, connected, connected
        )

    _assert_connected_and_syncing(response, row, send_task, aid)
    assert row.phone is None
    failures = [
        record.msg
        for record in caplog.records
        if isinstance(record.msg, dict) and record.msg.get("event") == "connect_phone_capture_failed"
    ]
    assert len(failures) == 1, f"событий сбоя захвата: {len(failures)}"
    assert failures[0]["account_id"] == aid
    assert failures[0]["error_type"] == "RuntimeError"
    for record in caplog.records:
        assert REPORTED not in str(record.msg), "номер попал в журнал"
        assert REPORTED not in record.getMessage(), "номер попал в журнал"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extra",
    [{}, {"phone": None}, {"phone": "79995554433"}],
    ids=["no-field", "null", "other-number"],
)
async def test_an_empty_or_other_report_never_overwrites_a_known_number(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, extra: dict
):
    """D-05, T-19-16: пустое и чужое значение не пишутся поверх известного номера."""
    aid = await seed_account(db_session, owner.id, "wa", phone="79990001122", status="connecting")
    body = {"connected": True, "exists": True, "syncState": None, **extra}

    response, row, _get, send_task = await _poll_and_read(
        authed_client, db_session, aid, body, body
    )

    _assert_connected_and_syncing(response, row, send_task, aid)
    assert row.phone == "+79990001122", f"известный номер перезаписан: {row.phone!r}"
    assert row.phone_is_manual is False


@pytest.mark.asyncio
async def test_the_number_is_not_asked_before_the_account_connects(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-15: пока `connected: false`, `/status` читается один раз; номер не запрашивается."""
    aid = await seed_account(db_session, owner.id, "wa", status="connecting")
    waiting = {"connected": False, "exists": True, "syncState": None}
    qr = {"qr": "data:image/png;base64,QR"}

    response, row, get_mock, send_task = await _poll_and_read(
        authed_client, db_session, aid, waiting, qr
    )

    assert response.status_code == 200
    assert "data:image/png;base64,QR" in response.text
    addresses = [call.args[0] for call in get_mock.await_args_list]
    assert addresses == [f"{WORKER}/api/sessions/{aid}/status", f"{WORKER}/api/sessions/{aid}/qr"], addresses
    assert row.status == "connecting"
    assert row.phone is None
    assert send_task.call_count == 0

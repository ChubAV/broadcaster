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

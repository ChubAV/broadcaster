"""Номер и отдельный `#id` в истории пользователя в админке (Фаза 17, план 07, PHONE-06).

Администратор работает по идентификатору, номер ему — подсказка рядом (D-04,
D-17): карточка записи несёт ДВА адреса — `data-account-label="<id>"` (номер или
приглушённое «Номер неизвестен») и отдельный `data-account-id="<id>"` (`#id`) —
всегда, у двойников и у недвойников одинаково. Подпись находится по АДРЕСУ, а не
подстрокой (`tests/account_label_support.py`): `#1` входит в `#10`.

Смотрит администратор, а аккаунты принадлежат ДРУГОМУ пользователю — просматриваемому
по адресу `/admin/users/{id}/history`. Карта номеров строится по нему, не по
администратору (D-14, T-17-21): поэтому везде здесь владелец аккаунтов и
владелец сессии — разные люди.

Гейты номера (`tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`,
`tests/test_application/test_phone_single_writer_gate.py`) модуль не трогает: номер
ставится только писателем Фазы 16 через `seed_account`.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.send_log import SendLog
from app.models.user import User
from tests.account_label_support import (
    id_mark_texts,
    label_texts,
    muted_label_ids,
    option_texts,
    seed_account,
)
from tests.conftest import seed_group

PHONE_STORED = "+79991234567"
PHONE_SHOWN = "+7 999 123-45-67"
UNKNOWN = "Номер неизвестен"


async def _seed_viewed_user(db: AsyncSession, email: str = "viewed@test.com") -> int:
    """Пользователь, чью историю смотрит администратор; возвращает id."""
    user = User(email=email, password_hash="x", name="Просматриваемый")
    db.add(user)
    await db.commit()
    return user.id


async def _admin_user_id(db: AsyncSession) -> int:
    """Администратор — единственный пользователь, созданный `admin_client` до посева."""
    return (await db.execute(select(User).order_by(User.id))).scalars().first().id


async def _seed_log(
    db: AsyncSession, user_id: int, group_id: int | None, *, name: str = "Группа отправки"
) -> int:
    """Запись журнала на группу (или без неё); возвращает id."""
    log = SendLog(
        user_id=user_id,
        group_id=group_id,
        ad_title="Объявление",
        ad_text="Текст",
        ad_images=[],
        group_name=name,
        messenger_type="wa",
        task_id="task-1",
        status="ok",
        sent_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()
    return log.id


async def _admin_history_with_one_record(
    db: AsyncSession, client: AsyncClient, type_: str = "tg_user", **account_kw
) -> tuple[int, str]:
    """Аккаунт просматриваемого пользователя, группа, одна запись.

    Возвращает (id аккаунта, html `/admin/users/{id}/history`).
    """
    viewed = await _seed_viewed_user(db)
    account_id = await seed_account(db, viewed, type_, **account_kw)
    group = await seed_group(db, account_id, viewed)
    await _seed_log(db, viewed, group.id)
    response = await client.get(f"/admin/users/{viewed}/history")
    assert response.status_code == 200
    return account_id, response.text


# --- страница `/admin/users/{id}/history` -----------------------------------------


@pytest.mark.asyncio
async def test_the_admin_history_card_shows_the_number_and_the_id(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """ТРАССЕР: номер и отдельный `#id` доходят до карточки админской истории."""
    account_id, html = await _admin_history_with_one_record(
        db_session, admin_client, "tg_user", phone=PHONE_STORED
    )

    assert label_texts(html)[str(account_id)] == [PHONE_SHOWN]
    assert id_mark_texts(html)[str(account_id)] == [f"#{account_id}"]


@pytest.mark.asyncio
async def test_the_admin_history_filter_option_always_carries_the_id(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """D-11, D-12, D-17: `<option>` — «Мессенджер номер #id», у недвойника тоже."""
    account_id, html = await _admin_history_with_one_record(
        db_session, admin_client, "tg_user", phone=PHONE_STORED
    )

    options = option_texts(html, "account_id")

    assert options[str(account_id)] == f"Telegram {PHONE_SHOWN} #{account_id}"


@pytest.mark.asyncio
async def test_an_unknown_number_in_the_admin_history_is_muted(
    admin_client: AsyncClient, db_session: AsyncSession
):
    account_id, html = await _admin_history_with_one_record(db_session, admin_client, "wa")

    assert label_texts(html)[str(account_id)] == [UNKNOWN]
    assert str(account_id) in muted_label_ids(html)
    assert id_mark_texts(html)[str(account_id)] == [f"#{account_id}"]
    # Один `#`: `#id` стоит отдельным знаком, а не дописан к подписи.
    assert "#" not in label_texts(html)[str(account_id)][0]

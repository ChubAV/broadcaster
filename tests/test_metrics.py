from datetime import datetime, timezone

import pytest

from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.subscription import Subscription
from app.models.user import User


@pytest.mark.asyncio
async def test_update_business_metrics(db_session):
    """Business metrics are correctly computed from DB state."""
    from app.metrics import (
        ACTIVE_SCHEDULES,
        ACTIVE_USERS,
        MESSAGES_SENT,
        update_business_metrics,
    )

    # Seed: User
    user = User(
        email="metrics@test.com",
        password_hash="hashed",
        name="Metrics Tester",
    )
    db_session.add(user)
    await db_session.flush()

    # Seed: MessengerAccount
    account = MessengerAccount(
        user_id=user.id,
        type="tg_user",
        credentials="{}",
        status="connected",
    )
    db_session.add(account)
    await db_session.flush()

    # Seed: Ad
    ad = Ad(
        user_id=user.id,
        title="Test Ad",
        text="Buy now!",
        images=[],
    )
    db_session.add(ad)
    await db_session.flush()

    # Seed: 2 active schedules + 1 inactive
    for active in (True, True, False):
        schedule = Schedule(
            ad_id=ad.id,
            account_id=account.id,
            group_ids=[1],
            days_of_week=[0, 1, 2],
            times_of_day=["09:00"],
            is_active=active,
        )
        db_session.add(schedule)

    # Seed: 1 active subscription
    #
    # ⚠️ РЯД СЧИТАЕТ ВСЕХ, У КОГО ЕСТЬ ДОСТУП, А НЕ ТОЛЬКО ПЛАТЯЩИХ. До ревизии
    # `0020` строка подписки заводилась только подтверждённым платежом, и число
    # совпадало со счётом плативших; теперь строка есть у пробных и у открытых
    # администратором тоже. Тариф конструктору не передаётся — колонки нет.
    subscription = Subscription(
        user_id=user.id,
        expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
        is_active=True,
    )
    db_session.add(subscription)

    # Seed: SendLogs — 3 tg/sent, 1 tg/failed, 2 wa/sent
    now = datetime.now(timezone.utc)
    for messenger, status, count in [("tg", "sent", 3), ("tg", "failed", 1), ("wa", "sent", 2)]:
        for _ in range(count):
            log = SendLog(
                user_id=user.id,
                ad_id=ad.id,
                messenger_type=messenger,
                status=status,
                sent_at=now,
            )
            db_session.add(log)

    await db_session.commit()

    # Act
    await update_business_metrics(db_session)

    # Assert
    assert ACTIVE_SCHEDULES._value.get() == 2
    assert ACTIVE_USERS._value.get() == 1
    assert MESSAGES_SENT.labels(messenger="tg", status="sent")._value.get() == 3
    assert MESSAGES_SENT.labels(messenger="tg", status="failed")._value.get() == 1
    assert MESSAGES_SENT.labels(messenger="wa", status="sent")._value.get() == 2


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    # instrumentator default metrics
    assert "http_request" in body
    # our custom gauges
    assert "broadcaster_active_schedules" in body
    assert "broadcaster_active_users" in body

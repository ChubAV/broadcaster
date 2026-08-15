"""CR-03, вторая линия: испорченная строка не выключает экраны владельца.

ГЛАВНАЯ линия защиты — 422 на явный null в JSON-входе
(tests/test_routes/test_schedules_api_null.py): нечитаемая запись не
порождается вовсе. Разметка здесь — ВТОРАЯ линия: строки, испорченные ДО фикса
(None в days_of_week, times_of_day или group_ids вместо списка), уже лежат в
базе, и путь восстановления через интерфейс существует только пока оба экрана
владельца — сводный список (SCH-04) и редактор объявления (ADS-07) — живы.

До фикса schedule_row.html:108 выполнял `d in None`, а sched_card.html:66/171/181
сортировал и итерировал None: оба экрана отвечали 500 навсегда.

Тумблер испорченной строки размечается как у НЕПОЛНОГО расписания (SCH-05,
D-08): None фальсивен как пустой список, поэтому возобновление на паузе
заблокировано с подсказкой, а пауза активного доступна всегда.

Образец засева — tests/test_pages/test_schedules_list.py; порча поля идёт
напрямую через db_session — симуляция записи, сделанной до фикса. Таймзона
страничным ядом не травится: колонка NOT NULL строковая, её случай закрывает
422 на входе.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User

BLOCKED_HINT = "Возобновить нельзя: расписание не заполнено"


async def _user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_poisoned_schedule(
    db: AsyncSession, field: str, is_active: bool = False
) -> tuple[int, int]:
    """Полное расписание владельца с последующей порчей одного поля.

    Возвращает (schedule_id, ad_id). Расписание засевается ПОЛНЫМ и на паузе
    (если не сказано иное): resume_blocked в разметке требует `not s.is_active`,
    иначе ветка заблокированного тумблера не рендерится вовсе. Порча —
    присваивание None напрямую через сессию: ровно так выглядела строка,
    записанная дефектным патчем до фикса (JSON-колонка хранит документ `null`).
    """
    user = await _user(db)
    ad = Ad(
        user_id=user.id,
        title="Объявление испорченной строки",
        text="Текст объявления",
        images=[],
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)

    account = MessengerAccount(
        user_id=user.id, type="wa", credentials="session", status="active"
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)

    group = Group(
        user_id=user.id,
        account_id=account.id,
        messenger_type="wa",
        group_external_id="ext-poisoned",
        name="Группа испорченной строки",
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[group.id],
        days_of_week=[0, 2, 4],
        times_of_day=["09:30"],
        timezone="UTC",
        is_active=is_active,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    setattr(schedule, field, None)
    await db.commit()
    return schedule.id, ad.id


# --- Испорченная строка НА ПАУЗЕ: оба экрана живы, тумблер заблокирован -------


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["days_of_week", "times_of_day", "group_ids"])
async def test_poisoned_paused_row_keeps_both_owner_screens_alive(
    authed_client: AsyncClient, db_session: AsyncSession, field: str
):
    """Оба экрана владельца отвечают 200; тумблер — как у неполного расписания.

    Вторая линия CR-03: главная линия (422 на входе) не помогает строкам,
    испорченным до фикса. Разметка обязана быть тотальной по данным базы —
    членство и итерация только по подстрахованным спискам. Тумблер испорченной
    строки на паузе заблокирован с подсказкой (SCH-05, D-08): None фальсивен
    как пустой список, расписание неполно, возобновлять его нечем.
    """
    schedule_id, ad_id = await _seed_poisoned_schedule(
        db_session, field, is_active=False
    )

    listing = await authed_client.get("/schedules")
    assert listing.status_code == 200, (
        f"сводный список мёртв при {field}=None — вторая линия не держит"
    )
    html = listing.text
    assert f'id="schedule-row-{schedule_id}"' in html, (
        "карточка испорченной строки не отрисована"
    )
    assert f'id="schedule-toggle-{schedule_id}" value="1" disabled>' in html, (
        "тумблер испорченной строки на паузе доступен к нажатию"
    )
    assert BLOCKED_HINT in html, "подсказка заблокированного тумблера не отрисована"

    # Развёрнутая карточка — тот самый адрес, на который ведёт действие
    # «Открыть объявление» из сводного списка: путь восстановления идёт именно
    # сюда, и свёрнутый рендер не покрыл бы итерацию времён (:181) и дней (:171).
    editor = await authed_client.get(f"/ads/{ad_id}/edit?sched={schedule_id}")
    assert editor.status_code == 200, (
        f"редактор объявления мёртв при {field}=None — вторая линия не держит"
    )
    assert f'id="sched-{schedule_id}"' in editor.text, (
        "карточка испорченного расписания не отрисована в редакторе"
    )


# --- Испорченная АКТИВНАЯ строка: пауза не блокируется ------------------------


@pytest.mark.asyncio
async def test_poisoned_active_row_keeps_the_pause_available(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Тумблер испорченной АКТИВНОЙ строки жив: пауза доступна всегда.

    Сценарий верификатора: дефектный патч коммитил порчу активного расписания.
    Вторая половина SCH-05/D-08 — право поставить на паузу не зависит от
    заполненности, поэтому у испорченной активной строки тумблер не
    заблокирован и показывает включённое состояние.
    """
    schedule_id, _ = await _seed_poisoned_schedule(
        db_session, "days_of_week", is_active=True
    )

    listing = await authed_client.get("/schedules")
    assert listing.status_code == 200
    html = listing.text
    assert f'id="schedule-row-{schedule_id}"' in html
    assert f'id="schedule-toggle-{schedule_id}" value="1" checked>' in html, (
        "пауза испорченной активной строки заблокирована — SCH-05 нарушен"
    )

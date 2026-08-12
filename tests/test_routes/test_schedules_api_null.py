"""CR-03: явный null в патче расписания отвергается НА ВХОДЕ — 422 до записи.

`UpdateScheduleRequest` объявляет каждое поле `T | None = None`, и
`model_dump(exclude_unset=True)` отличает отсутствующий ключ от присланного, но
не присланный-и-пустой: тело `{"group_ids": null}` считается присланным, и в
колонку JSON ложится документ `null`. Отказ наступал только на сериализации
ответа (`ScheduleResponse.group_ids: list`), когда запись уже закоммичена, — то
есть один аутентифицированный вызов владельца порождал строку, которую
невозможно прочитать обратно: `GET /api/schedules` после него отвечал 500
постоянно.

Здесь закрепляется ГЛАВНАЯ линия защиты: 422 силами схемы, до какого-либо
setattr. Вторая линия — живучесть разметки при строках, испорченных ДО фикса, —
живёт в tests/test_pages/test_schedules_poisoned_row.py.

Образец засева и авторизации — tests/test_routes/test_schedules_api_ownership.py:
тот файл шлёт патчи, только ОПУСКАЯ ключи; этот — шлёт явный null.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule
from tests.conftest import seed_group

# Значения полного расписания, засеянного через публичный маршрут. После
# отклонённого патча строка обязана остаться РАВНОЙ засеянной — сравнение идёт
# именно с этими значениями, перечитанными через ORM.
SEEDED_DAYS = [0, 1, 2, 3, 4, 5, 6]
SEEDED_TIMES = ["09:00"]
SEEDED_TIMEZONE = "UTC"


async def _create_ad(client: AsyncClient, auth_headers: dict) -> int:
    response = await client.post(
        "/api/ads",
        json={"title": "Schedule Ad", "text": "Текст объявления"},
        headers=auth_headers,
    )
    return response.json()["id"]


async def _create_account(client: AsyncClient, auth_headers: dict) -> int:
    response = await client.post(
        "/api/accounts",
        json={"type": "tg_user", "credentials": "creds"},
        headers=auth_headers,
    )
    return response.json()["id"]


async def _create_group(db_session: AsyncSession, account_id: int) -> int:
    """Группа этого аккаунта прямой вставкой через ORM.

    Прикладного входа создания группы нет: GRP-08 снято, JSON-маршрут групп
    удалён (план 03-07). Владельца и тип канала группа наследует от аккаунта.
    """
    group = await seed_group(
        db_session,
        account_id,
        group_external_id="-1001000000001",
        name="Своя группа",
    )
    return group.id


async def _seed_full_schedule(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> tuple[int, int]:
    """Полное расписание: (schedule_id, group_id)."""
    ad_id = await _create_ad(client, auth_headers)
    account_id = await _create_account(client, auth_headers)
    group_id = await _create_group(db_session, account_id)
    response = await client.post(
        "/api/schedules",
        json={
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": [group_id],
            "days_of_week": SEEDED_DAYS,
            "times_of_day": SEEDED_TIMES,
            "timezone": SEEDED_TIMEZONE,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()["id"], group_id


async def _stored(db_session: AsyncSession, schedule_id: int) -> Schedule:
    db_session.expire_all()
    return (
        await db_session.execute(select(Schedule).where(Schedule.id == schedule_id))
    ).scalar_one()


# --- Явный null в каждом из четырёх полей: 422 и строка не тронута ------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field", ["group_ids", "days_of_week", "times_of_day", "timezone"]
)
async def test_explicit_null_is_rejected_before_any_write(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict, field: str
):
    """PUT с `{"<field>": null}` → 422; строка равна засеянной; список читается.

    Правило JSON-входа: не допускается запись, которую невозможно прочитать
    обратно. Отказ обязан стоять ДО первого setattr — иначе он оставил бы
    запись частично изменённой, а `GET /api/schedules` — мёртвым навсегда.
    """
    schedule_id, group_id = await _seed_full_schedule(client, auth_headers, db_session)
    seeded = {
        "group_ids": [group_id],
        "days_of_week": SEEDED_DAYS,
        "times_of_day": SEEDED_TIMES,
        "timezone": SEEDED_TIMEZONE,
    }

    response = await client.put(
        f"/api/schedules/{schedule_id}",
        json={field: None},
        headers=auth_headers,
    )

    assert response.status_code == 422
    stored = await _stored(db_session, schedule_id)
    assert getattr(stored, field) == seeded[field], (
        f"отклонённый патч изменил поле {field} — отказ стоит после записи"
    )

    listing = await client.get("/api/schedules", headers=auth_headers)
    assert listing.status_code == 200, (
        "список расписаний не читается после отклонённого патча"
    )


# --- Контроль незатронутого контракта: частичный патч работает (D-15) ---------


@pytest.mark.asyncio
async def test_valid_partial_patch_still_updates_exactly_that_field(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    """ПРИСУТСТВУЮЩЕЕ корректное поле обновляется, остальные не тронуты.

    Отказ на явный null не имеет права сузить контракт частичного патча:
    отсутствующий ключ по-прежнему означает «не трогать» (exclude_unset), и
    валидатор не должен срабатывать на значениях по умолчанию.
    """
    schedule_id, group_id = await _seed_full_schedule(client, auth_headers, db_session)

    response = await client.put(
        f"/api/schedules/{schedule_id}",
        json={"days_of_week": [1, 2]},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["days_of_week"] == [1, 2]
    stored = await _stored(db_session, schedule_id)
    assert stored.days_of_week == [1, 2]
    assert stored.group_ids == [group_id]
    assert stored.times_of_day == SEEDED_TIMES
    assert stored.timezone == SEEDED_TIMEZONE

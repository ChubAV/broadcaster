"""CR-01: строка с днями ВНЕ ОБЛАСТИ ЗНАЧЕНИЙ обязана получать ОТКАЗ, а не 500.

ПРЕДМЕТ. Ревизия `0022` (`ck_schedules_active_requires_next_run`) запрещает в
СХЕМЕ пару «включено + нет момента». Накат при этом ВЫКЛЮЧАЕТ нарушителей и —
по записанному продуктовому решению — `days_of_week`/`times_of_day` НЕ ТРОГАЕТ.
Значит после наката на бою лежат строки, ПОЛНЫЕ по `is_schedule_complete`
(список дней непуст) и НЕИСПОЛНИМЫЕ по значениям (`[9]` — не день недели).

Восстановительный путь, объявленный шапкой самой ревизии, звучит так: «человек
дозаполняет расписание в редакторе, ЖМЁТ ТУМБЛЕР». В половине «жмёт тумблер» он
до этого файла отвечал ПЯТИСОТКОЙ: оба тумблера включали расписание
БЕЗУСЛОВНО, а `next_run_at` считали ПОСЛЕ, — `compute_next_run_at` отдавал
`None`, и `db.commit()` ронял `IntegrityError` о том самом ограничении.

⚠️ ПОЧЕМУ ЭТОГО НЕ ЛОВИЛО НИ ОДНО ИЗ 3182 ПРАВИЛ СУИТЫ. Существующая отсечка
области значений (`tests/test_routes/test_schedules_api_value_domain.py`) стои́т
на ВХОДАХ СОЗДАНИЯ И ОБНОВЛЕНИЯ — она не даёт РОДИТЬ такую строку через API.
Тумблер же читает дни из УЖЕ СОХРАНЁННОЙ строки и не отсекает ничего, а
`is_schedule_complete([9], ["10:00"])` отвечает `True`, потому что список
непуст, — значит ни страничный `resume_blocked`, ни `HTTP 400` JSON-входа не
срабатывают. Ни одно правило суиты не СЕЯЛО строку с днями вне диапазона и не
ЖАЛО на ней тумблер, поэтому полная зелень означала «этот вход не измеряется»,
а не «этот вход исправен». Посев здесь прямой, через `db_session`, — ровно так
выглядит строка, оставшаяся на бою после наката `0022`.

⚠️ ГРАНИЦА ФАЙЛА, НАЗВАННАЯ ЯВНО. Предмет — ОТКАЗ ПО ОТСУТСТВИЮ МОМЕНТА, а не
по пустоте списков. Отказ по НЕПОЛНОТЕ (пустые группы, снятый аккаунт) —
предмет других модулей (`test_schedules_toggle_detached.py`, D-08), и здесь он
не проверяется и не дублируется. Проверяется ровно то, чего не видел никто: ПО
СОСТАВУ ПОЛНАЯ, ПО ЗНАЧЕНИЯМ НЕИСПОЛНИМАЯ строка.

⚠️ ПОЧЕМУ ФАЙЛ ЛЕЖИТ В КОРНЕ `tests/`, А НЕ В `test_pages/` ИЛИ `test_routes/`.
Дефект ОДИН, а входов у него ТРИ: страничный тумблер, тумблер JSON-API и
частичное обновление JSON-API. Разложить их по каталогам значило бы развести
один засев на три копии — а засев здесь и есть самое дорогое место файла: это
он воспроизводит промышленную строку. Прецедент корневого размещения —
`tests/test_schedule_relationships.py`.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User
from app.pages import notices
from app.services.schedule_rules import is_schedule_complete
from app.services.schedule_service import compute_next_run_at
from tests.conftest import seed_group

# День вне `0..6`. Именно эта форма родила промышленную строку `sched=48`:
# список НЕПУСТ (значит расписание «полное»), а перебор `day_offset 0..7` не
# встречает девятого дня недели ни разу и возвращает `None`.
OUT_OF_DOMAIN_DAYS = [9]
IN_DOMAIN_TIMES = ["10:00"]


async def _user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_out_of_domain_schedule(
    db: AsyncSession, *, is_active: bool = False
) -> tuple[int, int]:
    """Расписание, ПОЛНОЕ по составу и НЕИСПОЛНИМОЕ по значениям дней.

    Возвращает `(schedule_id, ad_id)`.

    Дни портятся ОТДЕЛЬНЫМ присваиванием после первого `commit()`, а не
    передаются в конструктор: так засев проходит те же входы модели, что и
    обычная строка, и порча остаётся ЕДИНСТВЕННЫМ отличием от законной записи.

    `next_run_at` выдаётся только включённой строке — пары «включено + нет
    момента» схема не примет и в засеве (`ck_schedules_active_requires_next_run`
    стои́т и в модели). Включённая строка с ЗАКОННЫМ моментом и испорченными
    днями ограничению не противоречит: оно знает про пару `is_active`/
    `next_run_at` и НЕ ЗНАЕТ про область значений дней — это записано его
    собственной границей.
    """
    user = await _user(db)

    ad = Ad(
        user_id=user.id,
        title="Объявление строки вне области значений",
        text="Текст объявления",
        images=[],
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    ad_id = ad.id

    account = MessengerAccount(
        user_id=user.id, type="wa", credentials="session", status="active"
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    account_id = account.id

    group = await seed_group(db, account_id, name="Группа строки вне области")
    group_id = group.id

    legal_moment = compute_next_run_at(
        days_of_week=[0, 1, 2, 3, 4, 5, 6], times_of_day=IN_DOMAIN_TIMES, tz_name="UTC"
    )
    assert legal_moment is not None, "засев не смог получить законный момент запуска"

    schedule = Schedule(
        ad_id=ad_id,
        account_id=account_id,
        group_ids=[group_id],
        days_of_week=[0, 2, 4],
        times_of_day=list(IN_DOMAIN_TIMES),
        timezone="UTC",
        is_active=is_active,
        next_run_at=legal_moment if is_active else None,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    schedule_id = schedule.id

    schedule.days_of_week = list(OUT_OF_DOMAIN_DAYS)
    await db.commit()
    return schedule_id, ad_id


async def _reload(db: AsyncSession, schedule_id: int) -> Schedule:
    db.expire_all()
    return (
        await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    ).scalar_one()


# ─────────────────────────────────────────────────────────────────────────────
# ЧИСТЫЙ ЗАМЕР ФОРМЫ — без базы и без HTTP
# ─────────────────────────────────────────────────────────────────────────────


def test_the_seeded_shape_is_complete_and_yet_has_no_moment():
    """Почему отсечка по ПУСТОТЕ эту строку не ловит — показано прямо.

    Утверждение без базы и без HTTP: объяснить его зелёный цвет нечем, кроме
    самих правил. Это и есть причина существования всего файла — «полное» и
    «исполнимое» здесь РАСХОДЯТСЯ, а оба тумблера до правки спрашивали только
    первое.
    """
    assert is_schedule_complete(1, [1], OUT_OF_DOMAIN_DAYS, IN_DOMAIN_TIMES) is True, (
        "правило полноты перестало считать список [9] непустым — предмет файла "
        "изменился, и правила ниже больше не про то, ради чего заведены"
    )
    assert (
        compute_next_run_at(
            days_of_week=OUT_OF_DOMAIN_DAYS,
            times_of_day=IN_DOMAIN_TIMES,
            tz_name="UTC",
        )
        is None
    ), "день вне 0..6 внезапно дал момент запуска — расхождение исчезло"


# ─────────────────────────────────────────────────────────────────────────────
# ТУМБЛЕР JSON-API
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_api_toggle_refuses_a_row_whose_days_are_out_of_domain(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    """Отказ 400, а не 500: ограничение не должно доезжать до `commit()`.

    Пятисотка здесь — не «некрасивый код ответа». Это отказ БЕЗ ОБЪЯСНЕНИЯ и
    БЕЗ ПУТИ ВОССТАНОВЛЕНИЯ на единственном действии, которым владелец пробует
    вернуть строку, выключенную накатом `0022`.
    """
    schedule_id, _ = await _seed_out_of_domain_schedule(db_session, is_active=False)

    response = await client.post(
        f"/api/schedules/{schedule_id}/toggle", headers=auth_headers
    )

    assert response.status_code == 400, (
        f"включение строки с днями {OUT_OF_DOMAIN_DAYS} ответило "
        f"{response.status_code}, а не отказом 400"
    )
    assert "редактор" in response.json()["detail"].lower(), (
        "отказ не называет пути восстановления — человеку некуда идти"
    )

    row = await _reload(db_session, schedule_id)
    assert row.is_active is False, "отвергнутое включение всё-таки тронуло состояние"
    assert row.next_run_at is None, "отвергнутое включение выдало момент запуска"


@pytest.mark.asyncio
async def test_api_toggle_still_pauses_a_row_whose_days_are_out_of_domain(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    """АНТИВАКУУМНАЯ ПОЛОВИНА: отказ не съел ПАУЗУ.

    Отказывать полагается только ВКЛЮЧЕНИЮ. Право поставить на паузу не зависит
    ни от заполненности, ни от области значений — иначе правка заперла бы
    испорченную строку во ВКЛЮЧЁННОМ состоянии, то есть сделала бы хуже, чем
    было. Без этой половины правило выше зеленело бы и у обработчика, который
    отвечает 400 на ЛЮБОЕ нажатие.
    """
    schedule_id, _ = await _seed_out_of_domain_schedule(db_session, is_active=True)

    response = await client.post(
        f"/api/schedules/{schedule_id}/toggle", headers=auth_headers
    )

    assert response.status_code == 200, (
        f"постановка на паузу ответила {response.status_code} — отказ по области "
        "значений съел право остановить отправку"
    )
    row = await _reload(db_session, schedule_id)
    assert row.is_active is False, "пауза не сохранилась"
    assert row.next_run_at is None, "пауза оставила момент запуска"


# ─────────────────────────────────────────────────────────────────────────────
# ЧАСТИЧНОЕ ОБНОВЛЕНИЕ JSON-API
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_api_update_refuses_a_patch_that_leaves_the_row_unrunnable(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    """ТОТ ЖЕ НЕПОКРЫТЫЙ ВИД У `update_schedule`.

    Патч, НЕ ТРОГАЮЩИЙ `days_of_week`, на ВКЛЮЧЁННОЙ строке с испорченными
    днями уходил в тот же `IntegrityError`: пересчёт возвращал `None`, а
    `is_active` оставался `True`. Валидаторы входа сюда не помогают по
    построению — они смотрят на ПРИСЛАННОЕ, а испорченные дни приезжают ИЗ
    БАЗЫ.
    """
    schedule_id, _ = await _seed_out_of_domain_schedule(db_session, is_active=True)

    response = await client.put(
        f"/api/schedules/{schedule_id}",
        json={"times_of_day": ["11:00"]},
        headers=auth_headers,
    )

    assert response.status_code == 400, (
        f"патч включённой строки с днями {OUT_OF_DOMAIN_DAYS} ответил "
        f"{response.status_code}, а не отказом 400"
    )

    row = await _reload(db_session, schedule_id)
    assert row.times_of_day == list(IN_DOMAIN_TIMES), (
        "отвергнутый патч всё-таки записал часть полей — частичная запись хуже "
        "отказа целиком"
    )


# ─────────────────────────────────────────────────────────────────────────────
# СТРАНИЧНЫЙ ТУМБЛЕР
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_page_toggle_refuses_a_row_whose_days_are_out_of_domain(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Страничный вход отказывает ПЛАШКОЙ, а не пятисоткой и не молчанием.

    Политика входа своя (страница возвращает человека в редактор с кодом
    исхода, JSON-API отвечает 400), правило — одно. Молчаливый возврат тоже не
    годится: человек нажал тумблер, ничего не изменилось, и почему — не сказано
    нигде.
    """
    schedule_id, ad_id = await _seed_out_of_domain_schedule(
        db_session, is_active=False
    )

    response = await authed_client.post(
        f"/schedules/{schedule_id}/toggle",
        data={"ad_id": str(ad_id)},
        follow_redirects=False,
    )

    assert response.status_code == 302, (
        f"страничный тумблер ответил {response.status_code}, а не переходом"
    )
    location = response.headers["location"]
    assert f"notice={notices.SCHEDULE_VALUES_OUT_OF_DOMAIN}" in location, (
        f"переход {location} не несёт кода исхода — отказ молчит"
    )

    row = await _reload(db_session, schedule_id)
    assert row.is_active is False, "отвергнутое включение всё-таки тронуло состояние"
    assert row.next_run_at is None, "отвергнутое включение выдало момент запуска"


@pytest.mark.asyncio
async def test_page_toggle_still_pauses_a_row_whose_days_are_out_of_domain(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """АНТИВАКУУМНАЯ ПОЛОВИНА страничного входа — довод тот же, что у API."""
    schedule_id, ad_id = await _seed_out_of_domain_schedule(db_session, is_active=True)

    response = await authed_client.post(
        f"/schedules/{schedule_id}/toggle",
        data={"ad_id": str(ad_id)},
        follow_redirects=False,
    )

    assert response.status_code == 302, (
        f"страничная пауза ответила {response.status_code}, а не переходом"
    )
    assert "notice=" not in response.headers["location"], (
        "успешная пауза принесла код отказа"
    )

    row = await _reload(db_session, schedule_id)
    assert row.is_active is False, "пауза не сохранилась"
    assert row.next_run_at is None, "пауза оставила момент запуска"

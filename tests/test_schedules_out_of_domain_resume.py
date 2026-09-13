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

from dataclasses import dataclass, field

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User
from app.pages import notices
from app.services import schedule_rules
from app.services.schedule_rules import is_schedule_complete
from app.services.schedule_service import compute_next_run_at
from tests.conftest import seed_group

# День вне `0..6`. Именно эта форма родила промышленную строку `sched=48`:
# список НЕПУСТ (значит расписание «полное»), а перебор `day_offset 0..7` не
# встречает девятого дня недели ни разу и возвращает `None`.
OUT_OF_DOMAIN_DAYS = [9]
IN_DOMAIN_TIMES = ["10:00"]


# ─────────────────────────────────────────────────────────────────────────────
# ОБЪЯВЛЕННЫЙ ПЕРЕЧЕНЬ ФОРМ НЕИСПОЛНИМОЙ СОХРАНЁННОЙ СТРОКИ
# ─────────────────────────────────────────────────────────────────────────────
#
# ⚠️ ПОЧЕМУ ПЕРЕЧЕНЬ, А НЕ ПЯТЬ ОТДЕЛЬНЫХ ПРАВИЛ НА КАЖДЫЙ ВХОД. Форма,
# добавленная сюда, обязана становиться требованием ко ВСЕМ трём входам сразу.
# Без перечня следующая форма закроется на одном входе и останется открытой на
# двух — то есть повторится ровно тот дефект, который эти правила закрывают:
# прошлая партия закрыла ОДИН исход из шести и записала половину дела целым.
#
# ⚠️ `measured` ЕСТЬ ЗАМЕР, А НЕ ЦИТАТА ИЗ ОТЧЁТА. Каждая строка снята вызовом
# `compute_next_run_at` на шести формах (перезамер двенадцатого круга
# верификации, 2026-09-12, дерево `16df128`) и перепроверяется правилом чистой
# формы при КАЖДОМ прогоне: правило печатает ПОЛУЧЕННЫЙ исход, поэтому
# расхождение записи с деревом видно в тексте отказа, а не подразумевается.
#
# ⚠️ `label` НАБРАН ЛАТИНИЦЕЙ НАМЕРЕННО. Он уезжает в `ids` параметризации, а
# pytest экранирует не-ASCII в идентификаторах — и тогда отказ называл бы форму
# escape-последовательностью вместо имени. Человеческое имя живёт в
# `description` и печатается в сообщениях отказов.


@dataclass(frozen=True)
class MalformedStoredForm:
    """Одна форма СОХРАНЁННОЙ строки, неисполнимой по значениям."""

    label: str
    description: str
    days_of_week: list = field(default_factory=list)
    times_of_day: list = field(default_factory=list)
    timezone: str = "UTC"
    measured: str = ""


MALFORMED_STORED_FORMS: list[MalformedStoredForm] = [
    MalformedStoredForm(
        label="times-abc",
        description="время не разбирается: times_of_day=['abc']",
        days_of_week=[1],
        times_of_day=["abc"],
        timezone="UTC",
        measured="ValueError: invalid literal for int() with base 10: 'abc'",
    ),
    MalformedStoredForm(
        label="times-25-00",
        description="час вне суток: times_of_day=['25:00']",
        days_of_week=[1],
        times_of_day=["25:00"],
        timezone="UTC",
        measured="ValueError: hour must be in 0..23",
    ),
    MalformedStoredForm(
        label="times-9",
        description="время без минут: times_of_day=['9']",
        days_of_week=[1],
        times_of_day=["9"],
        timezone="UTC",
        measured="IndexError: list index out of range",
    ),
    MalformedStoredForm(
        label="times-int-9",
        description="время числом, а не строкой: times_of_day=[9]",
        days_of_week=[1],
        times_of_day=[9],
        timezone="UTC",
        measured="AttributeError: 'int' object has no attribute 'split'",
    ),
    MalformedStoredForm(
        label="tz-mars-phobos",
        description="незнакомая зона: timezone='Mars/Phobos'",
        days_of_week=[1],
        times_of_day=["10:00"],
        timezone="Mars/Phobos",
        measured="ZoneInfoNotFoundError: No time zone found with key Mars/Phobos",
    ),
    MalformedStoredForm(
        label="days-str-1",
        description="день строкой, а не числом: days_of_week=['1']",
        days_of_week=["1"],
        times_of_day=["10:00"],
        timezone="UTC",
        measured="None — ЕДИНСТВЕННЫЙ исход, закрытый прошлой партией",
    ),
]

MALFORMED_STORED_FORMS_BY_LABEL = {
    form.label: form for form in MALFORMED_STORED_FORMS
}

# Умолчание посева — форма промышленной строки `sched=48`. В перечень она НЕ
# ВХОДИТ: перечень есть замер ШЕСТИ форм двенадцатого круга, а эта седьмая
# форма живёт здесь ровно затем, чтобы шесть действующих правил модуля остались
# побайтово прежними.
DEFAULT_STORED_FORM = MalformedStoredForm(
    label="days-out-of-domain",
    description="день вне 0..6: days_of_week=[9]",
    days_of_week=list(OUT_OF_DOMAIN_DAYS),
    times_of_day=list(IN_DOMAIN_TIMES),
    timezone="UTC",
    measured="None — перебор day_offset 0..7 не встречает девятого дня недели",
)

# ПОЛОЖИТЕЛЬНЫЙ КОНТРОЛЬ. Не форма порчи, а её противоположность: тот же посев,
# те же поля, ЗАКОННЫЕ значения. Без него правила отказа зеленели бы и у
# обработчика, отказывающего ВСЕГДА, — а «починка», ломающая законный путь,
# хуже исходного дефекта.
LEGAL_STORED_FORM = MalformedStoredForm(
    label="control-legal",
    description="ЗАКОННАЯ строка: все дни недели и время '10:00'",
    days_of_week=[0, 1, 2, 3, 4, 5, 6],
    times_of_day=list(IN_DOMAIN_TIMES),
    timezone="UTC",
    measured="момент запуска (datetime) — путь включения обязан работать",
)

# Часовой отказ вычислителя, добытый ВЫЗОВОМ, а не предположением: см.
# `_calculator_outcome`. Отдельная метка нужна затем, чтобы «поднял исключение»
# и «вернул None» различались в ПЕЧАТИ отказа, оставаясь ОДНИМ исходом для
# вызывающего.
RAISED = object()


async def _user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_out_of_domain_schedule(
    db: AsyncSession,
    *,
    is_active: bool = False,
    form: MalformedStoredForm = DEFAULT_STORED_FORM,
) -> tuple[int, int]:
    """Расписание, ПОЛНОЕ по составу и НЕИСПОЛНИМОЕ по значениям.

    Возвращает `(schedule_id, ad_id)`.

    ⚠️ ПОРЧА ПЕРЕДАЁТСЯ ПАРАМЕТРОМ, А УМОЛЧАНИЕ ОСТАЛОСЬ ПОБАЙТОВО ПРЕЖНИМ
    (`days_of_week=[9]`, `times_of_day=["10:00"]`, `timezone="UTC"`). Иначе
    шесть действующих правил модуля пришлось бы править вместе с посевом, и
    переход их цвета перестал бы что-либо означать: нельзя отличить «правило
    стало ловить дефект» от «правило сверяет другую строку».

    Значения портятся ОТДЕЛЬНЫМ присваиванием после первого `commit()`, а не
    передаются в конструктор: так засев проходит те же входы модели, что и
    обычная строка, и порча остаётся ЕДИНСТВЕННЫМ отличием от законной записи.

    ⚠️ АНТИВАКУУМНЫЙ ЗУБ ПОСЕВА. После второго `commit()` строка ПЕРЕЧИТЫВАЕТСЯ
    из СУБД, и утверждается, что порча ПРИЗЕМЛИЛАСЬ. Без этого утверждения
    правила ниже зеленели бы и на строке, которая испорчена не была, — то есть
    «этот вход не измеряется» стало бы неотличимо от «этот вход исправен»,
    ровно тот класс ложной зелени, который назвала шапка этого файла.

    `next_run_at` выдаётся только включённой строке — пары «включено + нет
    момента» схема не примет и в засеве (`ck_schedules_active_requires_next_run`
    стои́т и в модели). Включённая строка с ЗАКОННЫМ моментом и испорченными
    значениями ограничению не противоречит: оно знает про пару `is_active`/
    `next_run_at` и НЕ ЗНАЕТ про область значений дней, времён и зоны — это
    записано его собственной границей (`app/models/schedule.py:46-52`). Поэтому
    снятие проверок СУБД (`PRAGMA ignore_check_constraints`) посеву НЕ НУЖНО, и
    это замер, а не догадка: посев проходит без него.
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

    schedule.days_of_week = list(form.days_of_week)
    schedule.times_of_day = list(form.times_of_day)
    schedule.timezone = form.timezone
    await db.commit()

    landed = await _reload(db, schedule_id)
    assert landed.days_of_week == list(form.days_of_week), (
        f"посев формы {form.label} не приземлился: в СУБД лежит "
        f"days_of_week={landed.days_of_week!r}, а не {form.days_of_week!r} — "
        "правило измеряло бы НЕ ИСПОРЧЕННУЮ строку"
    )
    assert landed.times_of_day == list(form.times_of_day), (
        f"посев формы {form.label} не приземлился: в СУБД лежит "
        f"times_of_day={landed.times_of_day!r}, а не {form.times_of_day!r} — "
        "правило измеряло бы НЕ ИСПОРЧЕННУЮ строку"
    )
    assert landed.timezone == form.timezone, (
        f"посев формы {form.label} не приземлился: в СУБД лежит "
        f"timezone={landed.timezone!r}, а не {form.timezone!r} — "
        "правило измеряло бы НЕ ИСПОРЧЕННУЮ строку"
    )
    return schedule_id, ad_id


async def _reload(db: AsyncSession, schedule_id: int) -> Schedule:
    db.expire_all()
    return (
        await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    ).scalar_one()


def _detached_row(form: MalformedStoredForm) -> Schedule:
    """Строка расписания БЕЗ СУБД — ровно те три поля, которые читает расчёт.

    Нужна правилу чистой формы: предмет там — договор между вычислителем и
    помощником, и втягивать в него сессию, клиента и посев значило бы измерять
    заодно и их.
    """
    return Schedule(
        ad_id=0,
        account_id=None,
        group_ids=[],
        days_of_week=list(form.days_of_week),
        times_of_day=list(form.times_of_day),
        timezone=form.timezone,
        is_active=False,
        next_run_at=None,
    )


def _calculator_outcome(form: MalformedStoredForm) -> tuple[object, str]:
    """ПОЛУЧЕННЫЙ исход вычислителя и его ПЕЧАТЬ — вызовом, а не чтением.

    Возвращает пару «значение, печать». Значение равно `RAISED`, если
    вычислитель сообщил о неисполнимости ИСКЛЮЧЕНИЕМ. Печать уезжает в текст
    отказа ДОСЛОВНО: утверждение «правило покраснело» без полученного значения
    не отличает измеренный отказ от ошибки сбора, описки в отборе `-k` и
    отказа ввоза — это записано лессоном партии о RED по одному коду возврата.
    """
    try:
        value = compute_next_run_at(
            days_of_week=form.days_of_week,
            times_of_day=form.times_of_day,
            tz_name=form.timezone,
        )
    except Exception as exc:  # noqa: BLE001 — здесь ловится ЗАМЕР, а не политика
        return RAISED, f"{type(exc).__name__}: {exc}"
    return value, repr(value)


async def _press_page_toggle(
    authed_client: AsyncClient, schedule_id: int, ad_id: int
) -> tuple[int | None, str, str]:
    """ОДНО нажатие страничного тумблера: код, ПЕЧАТЬ полученного и адресат.

    Возвращает тройку `(status_code, printed, location)`; `status_code` равен
    `None`, если исход пришёл исключением, а `location` пуст, если заголовка
    перехода в ответе нет.

    ⚠️ НАЖАТИЕ ЗДЕСЬ РОВНО ОДНО, И ЭТО НЕСУЩЕЕ СВОЙСТВО. Тумблер меняет
    состояние, поэтому второе нажатие ради второго утверждения измеряло бы уже
    другую строку.

    ⚠️ КОД ОТВЕТА И ИСКЛЮЧЕНИЕ ЛОВЯТСЯ ОДНОЙ ПАРОЙ ЗНАЧЕНИЙ НАМЕРЕННО. До
    правки неисполнимая строка доезжает до общего обработчика `app/main.py`,
    который отвечает пятисоткой, — но транспорт ASGI правил пропускает
    исключение приложения наружу, и тогда «полученным» оказывается класс
    исключения. Печатается то, что ПОЛУЧЕНО, а не то, что ожидалось.
    """
    try:
        response = await authed_client.post(
            f"/schedules/{schedule_id}/toggle",
            data={"ad_id": str(ad_id)},
            follow_redirects=False,
        )
    except Exception as exc:  # noqa: BLE001 — здесь ловится ЗАМЕР, а не политика
        return None, f"исключение {type(exc).__name__}: {exc}", ""
    return (
        response.status_code,
        f"код ответа {response.status_code}",
        response.headers.get("location", ""),
    )


def _snapshot(row: Schedule) -> tuple:
    """Пять полей строки, которых отказ не имеет права коснуться."""
    return (
        row.is_active,
        row.next_run_at,
        list(row.days_of_week or []),
        list(row.times_of_day or []),
        row.timezone,
    )


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


def test_the_calculator_reports_unrunnability_two_ways_and_the_helper_one():
    """ДВА способа сообщить о неисполнимости у вычислителя — ОДИН у помощника.

    Предмет — договор, а не внутренности. `compute_next_run_at` отвечает на
    вопрос «есть ли момент» ДВУМЯ разными способами: значением `None` на одних
    формах и ИСКЛЮЧЕНИЕМ на других. Вызывающему отдан РОВНО ОДИН вопрос, и
    разбор внутренностей вычислителя ему не поручен — этот разбор и есть работа
    помощника `next_run_or_none`.

    ⚠️ КЛАСС ИСКЛЮЧЕНИЯ ПОИМЁННО НЕ ПРИШПИЛИВАЕТСЯ. Пришпиленный класс заморозил
    бы внутренности вычислителя и краснел бы на всякой их правке, ничего не
    говоря о договоре. Полученное ПЕЧАТАЕТСЯ, свойство УТВЕРЖДАЕТСЯ.
    """
    form = MALFORMED_STORED_FORMS_BY_LABEL["times-abc"]
    value, printed = _calculator_outcome(form)

    assert value is RAISED or value is None, (
        f"форма «{form.description}» внезапно дала момент запуска: получено "
        f"{printed} — предмет правила исчез"
    )

    helper = getattr(schedule_rules, "next_run_or_none", None)
    assert helper is not None, (
        "помощника next_run_or_none нет в app/services/schedule_rules.py, а "
        f"вычислитель на форме «{form.description}» ответил {printed}: "
        "неисполнимость доезжает до вызывающего ИСКЛЮЧЕНИЕМ, мимо сличения с "
        "пустым значением, и оборачивается пятисоткой без объяснения"
    )
    assert helper(_detached_row(form)) is None, (
        f"помощник на форме «{form.description}» не ответил None, хотя "
        f"вычислитель дал {printed} — два способа сказать «нет» остались "
        "делом вызывающего"
    )


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


@pytest.mark.asyncio
async def test_page_toggle_refuses_a_row_whose_times_are_malformed(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ИСПОРЧЕННОЕ ВРЕМЯ, А НЕ ДЕНЬ: тот же отказ, а не пятисотка.

    Форма наследуется у соседнего правила про дни вне области значений — тот же
    клиент, тот же посев, то же чтение адресата плашки. Отличие одно и оно
    ПРЕДМЕТНОЕ: на этой форме вычислитель сообщает о неисполнимости
    ИСКЛЮЧЕНИЕМ, а не значением `None`, и сличение `if next_run is None`
    пропускает его мимо себя. Человек получает 500 без объяснения и без пути
    восстановления — на ЕДИНСТВЕННОМ действии, которым он возвращает строку,
    выключенную накатом `0022`.
    """
    form = MALFORMED_STORED_FORMS_BY_LABEL["times-abc"]
    schedule_id, ad_id = await _seed_out_of_domain_schedule(
        db_session, is_active=False, form=form
    )
    before = _snapshot(await _reload(db_session, schedule_id))

    status_code, printed, location = await _press_page_toggle(
        authed_client, schedule_id, ad_id
    )

    assert status_code == 302, (
        f"страничный тумблер на форме «{form.description}» дал {printed}, а не "
        "переход 302 с кодом исхода: отказ расчёта прошёл мимо сличения с "
        "пустым значением"
    )
    assert f"notice={notices.SCHEDULE_VALUES_OUT_OF_DOMAIN}" in location, (
        f"переход {location} не несёт кода исхода — отказ молчит"
    )

    assert _snapshot(await _reload(db_session, schedule_id)) == before, (
        f"отвергнутое включение на форме «{form.description}» тронуло строку — "
        "отказ обязан оставить её ровно там, где нашёл"
    )


@pytest.mark.asyncio
async def test_control_a_legal_row_is_still_switched_on(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ПОЛОЖИТЕЛЬНЫЙ КОНТРОЛЬ: отказ не огульный.

    Тот же посев и то же нажатие на ЗАКОННЫХ значениях включают расписание. Без
    этого правила соседнее зеленело бы и у обработчика, отказывающего ВСЕГДА, —
    а «починка», ломающая законный путь, есть худший исход, чем исходный
    дефект.
    """
    schedule_id, ad_id = await _seed_out_of_domain_schedule(
        db_session, is_active=False, form=LEGAL_STORED_FORM
    )

    status_code, printed, _location = await _press_page_toggle(
        authed_client, schedule_id, ad_id
    )

    assert status_code == 302, (
        f"законная строка при нажатии дала {printed}, а не переход 302"
    )
    row = await _reload(db_session, schedule_id)
    assert row.is_active is True, (
        "законная строка не включилась — отказ по неисполнимости стал огульным"
    )
    assert row.next_run_at is not None, (
        "законная строка включилась без момента запуска"
    )

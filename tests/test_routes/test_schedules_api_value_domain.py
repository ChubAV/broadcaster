"""ОБЛАСТЬ ЗНАЧЕНИЙ на JSON-входе расписания: день 0..6, время ЧЧ:ММ.

Предмет файла — ТО ЖЕ РАСХОЖДЕНИЕ, что закрыл
`test_schedules_api_create_completeness.py`, только на другом правиле. Правило
«какие значения дней и времён система вообще умеет исполнять» живёт на
СТРАНИЧНОМ входе (`_TIME_RE` и `_clean_ints(low=0, high=6)` в
`app/pages/schedules.py`) и до этого файла отсутствовало на JSON-входе целиком.
Ровно тот класс, ради которого заведён нейтральный
`app/services/schedule_rules.py`: правило на одном входе и ничего на другом
расходится молча (WR-05, CR-02).

⚠️ ДВА ПОСЛЕДСТВИЯ, И ОНИ РАЗНЫЕ ПО ТЯЖЕСТИ. Испорченное значение попадает в
`compute_next_run_at`, и дальше всё решает, по какую сторону разбора строки оно
ломается:

  - ИСПОРЧЕННОЕ ВРЕМЯ ломает разбор. `compute_next_run_at` делает
    `int(parts[0])` / `parts[1]` без всякой защиты, поэтому `"abc"` даёт
    ValueError, `"25:00"` — «hour must be in 0..23», `"12:99"` — «minute must be
    in 0..59». Наружу это 500, строка при этом НЕ ПИШЕТСЯ.

  - ДЕНЬ ВНЕ ДИАПАЗОНА разбор ПРОХОДИТ и потому страшнее. Список `[9]`
    НЕПУСТ, поэтому `is_schedule_complete` отвечает True; а
    `compute_next_run_at` перебирает day_offset 0..7, ни разу не встречает
    девятый день недели и возвращает None на `if not candidates`. Получается
    `is_active=true` при `next_run_at=NULL` — В ТОЧНОСТИ форма промышленной
    строки sched=48, ЧЕРЕЗ ТОТ САМЫЙ МАРШРУТ, который правка 7833844 закрывала.
    Строка мертва навсегда и молча: отбор к отправке фильтрует
    `is_active = true AND next_run_at <= now`, а `NULL <= now` в SQL не истинно
    никогда, и единственная ветка, пересчитывающая `next_run_at`, работает
    только по УЖЕ ВЫБРАННЫМ строкам.

⚠️ ЧТО ЭТО ГОВОРИТ О ТЕКСТЕ ПРЕЖНЕЙ ПРАВКИ. Комментарий в `create_schedule`
утверждал, что согласованность двух правил держится по построению, потому что
`compute_next_run_at` возвращает None «ровно на пустых днях ИЛИ временах».
Пустота — не единственное такое условие; день вне диапазона второе. Правка
7833844 верна и необходима, но её полнота была заявлена шире факта, и этот файл
— место, где заявление стало проверяемым.

ПОЧЕМУ ЗДЕСЬ ОТКАЗ (422), А ПРИ НЕПОЛНОТЕ БЫЛ НЕ ОТКАЗ. Это не два ответа на
одно правило, а один ответ на два разных вопроса. Неполное расписание —
ЗАКОННОЕ промежуточное состояние черновика: и страничный создатель, и обновление
этого же API сохраняют его выключенным. А `"abc"` — не время; `9` — не день
недели. Такого состояния в предметной области не существует вовсе, и JSON-слой
уже отвечает на испорченное значение поля отказом: `timezone` не из
`VALID_TIMEZONES` даёт 422 с самого начала, а `UpdateScheduleRequest` отвечает
422 на явный null (CR-03). Отказ здесь — ПРОДОЛЖЕНИЕ поведения этого входа, а не
третье поведение.

Страничный слой при этом остаётся на своём: он ОТБРАСЫВАЕТ негодное значение и
сохраняет остальные, потому что форма шлёт повторяющиеся поля и одно испорченное
не повод потерять всё остальное (`_clean_times`, `_clean_ints`). ОДНО ПРАВИЛО,
ДВЕ ПОЛИТИКИ — по одной на вход, и каждая уже была у своего входа до этого
файла. Расхождением WR-05 было другое: там у одного правила было ДВА РАЗНЫХ
ОПРЕДЕЛЕНИЯ.

⚠️ ВИДИМОЕ КЛИЕНТАМ ИЗМЕНЕНИЕ, НАЗВАННОЕ ЗДЕСЬ, А НЕ ОБНАРУЖЕННОЕ ИМИ. Время с
однозначным часом (`"9:00"`) РАНЬШЕ ПРИНИМАЛОСЬ этим входом: `int("9")`
разбирается успешно, и расписание сохранялось. Теперь это 422. Формат ЧЧ:ММ —
единственное определение формата в проекте (`_TIME_RE` с самого начала требует
двух цифр часа), его же ждёт `<input type="time">` редактора, и в нём же
значение уезжает в разметку карточки. Принять два написания одного времени
значило бы завести второе определение формата — то самое, чего модуль общих
правил не допускает.
"""

import pytest

from app.services.schedule_rules import is_schedule_complete
from app.services.schedule_service import compute_next_run_at
from tests.conftest import seed_group


async def _ad_account_groups(client, auth_headers, db_session):
    """Своё объявление, свой аккаунт и настоящая группа этого аккаунта.

    Группы сеются через ORM: маршрут сверяет владение группами (CR-02), и на
    выдуманном числе он ответил бы 404 — предмет файла до проверки бы не дожил.
    """
    ad_id = (
        await client.post(
            "/api/ads",
            json={"title": "Область значений", "text": "Текст объявления"},
            headers=auth_headers,
        )
    ).json()["id"]

    account_id = (
        await client.post(
            "/api/accounts",
            json={"type": "tg_user", "credentials": "bot-token-value-domain"},
            headers=auth_headers,
        )
    ).json()["id"]

    group = await seed_group(
        db_session,
        account_id,
        group_external_id="-1002000000099",
        name="Группа области значений",
    )
    return ad_id, account_id, [group.id]


async def _post_schedule(client, auth_headers, body, case):
    """POST, у которого ПАДЕНИЕ МАРШРУТА становится внятным отказом теста.

    `ASGITransport` поднят с `raise_app_exceptions` по умолчанию, поэтому
    необработанное исключение обработчика прилетает СЮДА, а не превращается в
    ответ 500. Без этой обёртки красная фаза читалась бы как ошибка окружения —
    а это ровно предмет проверки, и он обязан быть назван словами.
    """
    try:
        return await client.post("/api/schedules", json=body, headers=auth_headers)
    except Exception as exc:  # noqa: BLE001 — предмет проверки, а не помеха
        pytest.fail(
            f"{case}: обработчик УПАЛ вместо ответа — {type(exc).__name__}: {exc}. "
            f"Значение не той области доехало до compute_next_run_at, который "
            f"разбирает строку времени без защиты; наружу это 500."
        )


# ─────────────────────────────────────────────────────────────────────────────
# ДЕНЬ ВНЕ ДИАПАЗОНА — мёртвая строка
# ─────────────────────────────────────────────────────────────────────────────

_BAD_DAYS = [
    pytest.param([9], "день 9 — недели такой длины не бывает", id="day_9"),
    pytest.param([7], "день 7 — сосед по границе сверху (0..6)", id="day_7_boundary"),
    pytest.param([-1], "день -1 — сосед по границе снизу", id="day_minus_1_boundary"),
    pytest.param([0, 9], "один годный день и один негодный", id="mixed_good_and_bad"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("days_of_week,case", _BAD_DAYS)
async def test_create_with_out_of_range_day_never_saves_a_dead_row(
    client, auth_headers, db_session, days_of_week, case
):
    """⚠️ ГЛАВНОЕ УТВЕРЖДЕНИЕ ФАЙЛА: форма sched=48 недостижима и этим входом тоже.

    Проверяется СНАЧАЛА инвариант, и только потом код ответа. Порядок не
    косметический: падать обязано сообщение про МЁРТВУЮ СТРОКУ, потому что
    неверный код ответа — мелочь рядом с записью, которую невозможно ни выбрать,
    ни починить.
    """
    ad_id, account_id, group_ids = await _ad_account_groups(
        client, auth_headers, db_session
    )

    response = await _post_schedule(
        client,
        auth_headers,
        {
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": group_ids,
            "days_of_week": days_of_week,
            "times_of_day": ["09:00"],
            "timezone": "Europe/Moscow",
        },
        case,
    )

    if response.status_code == 201:
        data = response.json()
        assert not (data["is_active"] and data["next_run_at"] is None), (
            f"{case}: сохранена МЁРТВАЯ СТРОКА — is_active=true при "
            f"next_run_at=null, то есть форма промышленной строки sched=48 "
            f"через маршрут, который правка 7833844 закрывала. Отбор к отправке "
            f"её не выберет никогда, а пересчитать next_run_at некому: пересчёт "
            f"идёт только по уже выбранным строкам."
        )

    assert response.status_code == 422, (
        f"{case}: день недели вне 0..6 — значение, которого в предметной области "
        f"не существует; вход обязан ответить отказом, как он уже отвечает на "
        f"незнакомый timezone."
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("days_of_week,case", _BAD_DAYS)
async def test_update_with_out_of_range_day_never_saves_a_dead_row(
    client, auth_headers, db_session, days_of_week, case
):
    """То же на ОБНОВЛЕНИИ: второй JSON-вход, та же область значений.

    Отдельный тест, а не параметр первого: обновление приходит на УЖЕ АКТИВНУЮ
    строку, и ветка пересчёта там другая — `elif schedule.is_active`. Испорченный
    день проводит её мимо `is_schedule_complete` (список непуст) прямо в
    `compute_next_run_at`, который вернёт None поверх ЖИВОГО расписания. То есть
    обновление способно УБИТЬ работающую строку, а не только родить мёртвую.
    """
    ad_id, account_id, group_ids = await _ad_account_groups(
        client, auth_headers, db_session
    )

    created = await client.post(
        "/api/schedules",
        json={
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": group_ids,
            "days_of_week": [0, 3],
            "times_of_day": ["09:00"],
            "timezone": "Europe/Moscow",
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    schedule_id = created.json()["id"]
    assert created.json()["is_active"] is True
    assert created.json()["next_run_at"] is not None

    try:
        response = await client.put(
            f"/api/schedules/{schedule_id}",
            json={"days_of_week": days_of_week},
            headers=auth_headers,
        )
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"{case}: обновление УПАЛО — {type(exc).__name__}: {exc}")

    if response.status_code == 200:
        data = response.json()
        assert not (data["is_active"] and data["next_run_at"] is None), (
            f"{case}: обновление УБИЛО живое расписание — is_active=true при "
            f"next_run_at=null. Строка была отправляемой до запроса и перестала "
            f"быть после, не сообщив об этом никому."
        )

    assert response.status_code == 422, case


# ─────────────────────────────────────────────────────────────────────────────
# ИСПОРЧЕННОЕ ВРЕМЯ — падение разбора
# ─────────────────────────────────────────────────────────────────────────────

_BAD_TIMES = [
    pytest.param("abc", "вовсе не время", id="abc"),
    pytest.param("", "пустая строка", id="empty_string"),
    pytest.param("12", "час без минут — двоеточия нет", id="no_colon"),
    pytest.param("24:00", "час 24 — сосед по границе сверху", id="hour_24_boundary"),
    pytest.param("23:60", "минута 60 — сосед по границе сверху", id="minute_60_boundary"),
    pytest.param("12:99", "минута вне диапазона", id="minute_99"),
    pytest.param("-1:00", "отрицательный час", id="negative_hour"),
    pytest.param("09:00:00", "секунды — не тот формат", id="with_seconds"),
    pytest.param("9:00", "однозначный час — РАНЬШЕ ПРИНИМАЛСЯ, см. шапку файла", id="single_digit_hour"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_time,case", _BAD_TIMES)
async def test_create_with_malformed_time_answers_422_instead_of_crashing(
    client, auth_headers, db_session, bad_time, case
):
    """Испорченное время — отказ формы, а не 500 из недр расчёта."""
    ad_id, account_id, group_ids = await _ad_account_groups(
        client, auth_headers, db_session
    )

    response = await _post_schedule(
        client,
        auth_headers,
        {
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": group_ids,
            "days_of_week": [0, 3],
            "times_of_day": [bad_time],
            "timezone": "Europe/Moscow",
        },
        case,
    )

    assert response.status_code == 422, (
        f"{case} ({bad_time!r}): ожидался отказ формы. Получен "
        f"{response.status_code}."
    )


@pytest.mark.asyncio
async def test_create_with_one_bad_time_among_good_ones_is_refused_whole(
    client, auth_headers, db_session
):
    """Отказ распространяется на ВЕСЬ запрос, а не на негодное значение.

    Тем самым JSON-вход отличается от страничного НАМЕРЕННО, и отличие
    закрепляется здесь, чтобы никто не «починил» его в сторону тихого
    отбрасывания. Форма шлёт повторяющиеся поля и не умеет сообщить, какое из них
    отброшено, — поэтому страница отбрасывает. Клиент JSON прислал ОДИН документ
    и обязан узнать, что документ не принят: сохранить его наполовину значило бы
    отдать 201 на расписание, времена которого клиент не присылал.
    """
    ad_id, account_id, group_ids = await _ad_account_groups(
        client, auth_headers, db_session
    )

    response = await _post_schedule(
        client,
        auth_headers,
        {
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": group_ids,
            "days_of_week": [0, 3],
            "times_of_day": ["09:00", "abc", "18:00"],
            "timezone": "Europe/Moscow",
        },
        "одно негодное значение среди годных",
    )

    assert response.status_code == 422

    listed = await client.get("/api/schedules", headers=auth_headers)
    assert listed.json() == [], (
        "после отказа в таблице осталась строка — запрос принят наполовину"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_time,case", _BAD_TIMES)
async def test_update_with_malformed_time_answers_422_instead_of_crashing(
    client, auth_headers, db_session, bad_time, case
):
    """То же на обновлении — второй JSON-вход."""
    ad_id, account_id, group_ids = await _ad_account_groups(
        client, auth_headers, db_session
    )
    created = await client.post(
        "/api/schedules",
        json={
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": group_ids,
            "days_of_week": [0, 3],
            "times_of_day": ["09:00"],
            "timezone": "Europe/Moscow",
        },
        headers=auth_headers,
    )
    schedule_id = created.json()["id"]

    try:
        response = await client.put(
            f"/api/schedules/{schedule_id}",
            json={"times_of_day": [bad_time]},
            headers=auth_headers,
        )
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"{case} ({bad_time!r}): обновление УПАЛО — {type(exc).__name__}: {exc}")

    assert response.status_code == 422, f"{case} ({bad_time!r})"


# ─────────────────────────────────────────────────────────────────────────────
# ПОЛОЖИТЕЛЬНЫЙ КОНТРОЛЬ — без него отказ на ВСЁМ был бы зелёным
# ─────────────────────────────────────────────────────────────────────────────

_GOOD = [
    pytest.param([0], ["00:00"], "полночь и понедельник — обе нижние границы", id="lower_bounds"),
    pytest.param([6], ["23:59"], "воскресенье и 23:59 — обе верхние границы", id="upper_bounds"),
    pytest.param([0, 1, 2, 3, 4, 5, 6], ["09:00", "15:15"], "вся неделя и два времени", id="full_week"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("days_of_week,times_of_day,case", _GOOD)
async def test_values_inside_the_domain_are_accepted_and_scheduled(
    client, auth_headers, db_session, days_of_week, times_of_day, case
):
    """⚠️ БЕЗ ЭТОГО ТЕСТА ПРАВКА «ОТКАЗЫВАТЬ ВСЕГДА» БЫЛА БЫ ЗЕЛЁНОЙ.

    Границы диапазона перечислены поимённо с обеих сторон: правило, отвергающее
    `0` или `23:59`, ломает законные расписания и обязано падать здесь.
    """
    ad_id, account_id, group_ids = await _ad_account_groups(
        client, auth_headers, db_session
    )

    response = await _post_schedule(
        client,
        auth_headers,
        {
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": group_ids,
            "days_of_week": days_of_week,
            "times_of_day": times_of_day,
            "timezone": "Europe/Moscow",
        },
        case,
    )

    assert response.status_code == 201, f"{case}: законное значение отвергнуто"
    data = response.json()
    assert data["is_active"] is True, case
    assert data["next_run_at"] is not None, case


# ─────────────────────────────────────────────────────────────────────────────
# ЧИСТЫЙ ИНВАРИАНТ ДВУХ ПРАВИЛ — без базы и без HTTP
# ─────────────────────────────────────────────────────────────────────────────

_IN_DOMAIN_DAYS = [[0], [1], [2], [3], [4], [5], [6], [0, 6], [0, 1, 2, 3, 4, 5, 6]]
_IN_DOMAIN_TIMES = [["00:00"], ["23:59"], ["09:00", "15:15"], ["12:30"]]


@pytest.mark.parametrize("days_of_week", _IN_DOMAIN_DAYS)
@pytest.mark.parametrize("times_of_day", _IN_DOMAIN_TIMES)
@pytest.mark.parametrize("tz_name", ["UTC", "Europe/Moscow"])
def test_completeness_implies_a_computable_next_run(days_of_week, times_of_day, tz_name):
    """⚠️ ИМЕННО ЭТО УТВЕРЖДЕНИЕ И БЫЛО ЗАЯВЛЕНО ШИРЕ ФАКТА.

    Комментарий правки 7833844 гласил: согласованность двух правил держится по
    построению, потому что `compute_next_run_at` возвращает None ровно на пустых
    днях ИЛИ временах. На ОБЛАСТИ ЗНАЧЕНИЙ это верно — и проверяется здесь
    напрямую, без базы и без HTTP, то есть без единой возможности объяснить
    зелёный цвет чем-то, кроме самих правил.

    За пределами области — неверно, и это ловят тесты маршрута выше. Два
    утверждения вместе и составляют границу: правило полноты согласовано с
    расчётом ТОЛЬКО ПОСЛЕ того, как вход отсёк значения не той области.
    """
    assert is_schedule_complete(1, [1], days_of_week, times_of_day) is True

    next_run = compute_next_run_at(
        days_of_week=days_of_week, times_of_day=times_of_day, tz_name=tz_name
    )

    assert next_run is not None, (
        f"полное расписание {days_of_week} {times_of_day} {tz_name} осталось без "
        f"момента запуска — это и есть мёртвая строка"
    )

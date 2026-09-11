"""D-08 на входе СОЗДАНИЯ JSON-API: активным сохраняется только полное расписание.

Предмет файла — инвариант «`is_active = true` НЕСОВМЕСТИМО с `next_run_at IS NULL`».
Строка, нарушившая его, мертва НАВСЕГДА и притом молча:

  - отбор к отправке (`app/application/scheduling/use_cases.py::collect_due_schedules`)
    фильтрует `is_active = true AND next_run_at <= now`, а в SQL `NULL <= now` не
    истинно НИКОГДА — строка не выбирается;
  - единственная ветка, которая `next_run_at` ПЕРЕСЧИТЫВАЕТ, живёт ВНУТРИ цикла по
    уже выбранным строкам — то есть на невыбираемой строке не выполняется тоже.

Самовосстановления, стало быть, нет: починить такую строку нечему. Интерфейс же
показывает её включённой. Пользователь видит активное расписание, которое не
отправит ничего и никогда.

Дыра была ОДНА на семь мест записи: `create_schedule` считал `next_run_at`
(а `compute_next_run_at` возвращает None на пустом списке дней или времён) и звал
`ScheduleRepository.create` БЕЗ `is_active` — то есть брал умолчание колонки
`is_active=True` (`app/models/schedule.py`). Общее правило полноты
`is_schedule_complete` на этом входе не вызывалось. Остальные шесть — оба
обновления, оба тумблера, отвязка при удалении аккаунта и пересчёт в отборе —
инвариант держали.

Это ТОТ ЖЕ класс расхождения, ради которого заведён нейтральный
`app/services/schedule_rules.py`: правило, живущее на одном входе и отсутствующее
на другом, расходится молча (WR-05, CR-02). Под общее правило тогда подвели
обновление и тумблер API, а СОЗДАНИЕ — нет.
"""

import pytest

from app.services.schedule_rules import is_schedule_complete
from app.services.schedule_service import compute_next_run_at
from tests.conftest import seed_group


async def _ad_account_groups(client, auth_headers, db_session):
    """Своё объявление, свой аккаунт и ДВЕ настоящие группы этого аккаунта.

    Группы сеются через ORM, а не выдумываются числами: маршрут создания сверяет
    владение группами (CR-02), и на выдуманных значениях он ответил бы 404 —
    предмет этого файла до проверки бы не дожил.
    """
    ad_id = (
        await client.post(
            "/api/ads",
            json={"title": "Расписание", "text": "Текст объявления"},
            headers=auth_headers,
        )
    ).json()["id"]

    account_id = (
        await client.post(
            "/api/accounts",
            json={"type": "tg_user", "credentials": "bot-token-completeness"},
            headers=auth_headers,
        )
    ).json()["id"]

    group_ids = [
        (
            await seed_group(
                db_session,
                account_id,
                group_external_id=f"-100200000000{index}",
                name=f"Группа {index + 1}",
            )
        ).id
        for index in range(2)
    ]
    return ad_id, account_id, group_ids


# Соседи по границе класса эквивалентности, а не один заявленный случай.
#
# Промышленная строка sched=48 несла ПУСТЫЕ ДНИ при непустых временах и группе —
# это первый набор. Одного его мало: `compute_next_run_at` возвращает None по
# дизъюнкции (`not days_of_week or not times_of_day`), а `is_schedule_complete`
# требует конъюнкции из ЧЕТЫРЁХ полей, и проверка одного набора закрепила бы
# ровно одну её ветвь. Пустые времена, пустые группы, пустое всё и одиночные
# значения (минимальный непустой случай) перечислены поимённо.
_INCOMPLETE = [
    pytest.param([0, 2], [], "пустые времена", id="empty_times"),
    pytest.param([], ["09:00", "15:15"], "пустые дни (форма промышленной строки sched=48)", id="empty_days"),
    pytest.param([], [], "пусты и дни, и времена", id="empty_both"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("days_of_week,times_of_day,case", _INCOMPLETE)
async def test_create_incomplete_schedule_is_never_saved_active(
    client, auth_headers, db_session, days_of_week, times_of_day, case
):
    """Неполное расписание сохраняется ВЫКЛЮЧЕННЫМ, а не активным-без-запуска.

    Отказ формой (422) здесь был бы НЕВЕРНЫМ исходом и разошёлся бы с двумя уже
    существующими местами: страничный создатель сохраняет неполное расписание
    выключенным (D-08), и обновление того же JSON-API — тоже. Неполнота есть
    законное промежуточное состояние черновика, а не ошибка запроса.
    """
    ad_id, account_id, group_ids = await _ad_account_groups(
        client, auth_headers, db_session
    )

    response = await client.post(
        "/api/schedules",
        json={
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": group_ids,
            "days_of_week": days_of_week,
            "times_of_day": times_of_day,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201, case
    data = response.json()

    # Собственно инвариант. Он проверяется ОТДЕЛЬНОЙ строкой и первым, а не
    # выводится из двух проверок ниже: именно эта пара значений и есть мёртвая
    # строка, и сообщение о падении обязано называть её, а не одно из полей.
    assert not (data["is_active"] and data["next_run_at"] is None), (
        f"{case}: сохранена НЕОТПРАВЛЯЕМАЯ строка — is_active=true при "
        f"next_run_at=null. Отбор к отправке её не выберет никогда "
        f"(NULL <= now ложно), а пересчёт next_run_at выполняется только на "
        f"выбранных строках, поэтому починить себя она не сможет."
    )
    assert data["is_active"] is False, case
    assert data["next_run_at"] is None, case


@pytest.mark.asyncio
async def test_create_without_groups_is_never_saved_active(
    client, auth_headers, db_session
):
    """Пустой состав групп — та же неполнота, хотя `compute_next_run_at` о нём не знает.

    Ветка вынесена из параметризации выше намеренно: там пустеют поля, от которых
    зависит РАСЧЁТ следующего запуска, здесь — поле, от которого он не зависит
    вовсе. Дни и времена непусты, поэтому `next_run_at` посчитается; активной
    строка стать всё равно не имеет права — отправлять её некуда. Именно этот
    случай назван в страничном создателе: «сохраняется выключенным, а не молча
    активным с нулём групп».
    """
    ad_id, account_id, _ = await _ad_account_groups(client, auth_headers, db_session)

    response = await client.post(
        "/api/schedules",
        json={
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": [],
            "days_of_week": [0, 2],
            "times_of_day": ["09:00"],
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["is_active"] is False
    # Момент запуска у ВЫКЛЮЧЕННОГО расписания пуст, и это не придирка к лишнему
    # полю. Дни и времена здесь непусты, поэтому безусловный расчёт положил бы в
    # строку осмысленную дату — а сводка редактора читает её и обещает по ней
    # отправку, которой не будет (WR-06). Оба обновления и оба тумблера это
    # правило уже держат; создание обязано держать его тоже, иначе на одно
    # правило снова придётся два поведения.
    assert data["next_run_at"] is None


@pytest.mark.asyncio
async def test_create_complete_schedule_stays_active_with_next_run(
    client, auth_headers, db_session
):
    """Контрольный ПОЛОЖИТЕЛЬНЫЙ случай: минимальное полное расписание.

    Без него правку нечем отличить от «выключать всё подряд»: проверки выше
    зеленеют и на `is_active = False` константой. Набор — МИНИМАЛЬНЫЙ непустой
    (одна группа, один день, одно время), то есть ближайший сосед границы с
    другой её стороны.
    """
    ad_id, account_id, group_ids = await _ad_account_groups(
        client, auth_headers, db_session
    )

    response = await client.post(
        "/api/schedules",
        json={
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": group_ids[:1],
            "days_of_week": [0],
            "times_of_day": ["09:00"],
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["is_active"] is True
    assert data["next_run_at"] is not None


@pytest.mark.parametrize("days_of_week", [[], [0], [0, 6]])
@pytest.mark.parametrize("times_of_day", [[], ["09:00"], ["09:00", "15:15"]])
@pytest.mark.parametrize("group_ids", [[], [1]])
def test_completeness_and_next_run_can_never_disagree(
    days_of_week, times_of_day, group_ids
):
    """Оба правила согласованы ПО ПОСТРОЕНИЮ, и это то, на чём держится правка.

    Проверка синхронная и без базы — она о самих правилах, а не о маршруте.
    `is_schedule_complete` требует конъюнкции четырёх полей, `compute_next_run_at`
    возвращает None ровно на пустых днях ИЛИ временах. Значит полнота ВЛЕЧЁТ
    непустой момент запуска, и «сохранить активным то, что полно» не может
    оставить `next_run_at` пустым ни при каком наборе. Разъедься эти два правила
    впредь — упадёт здесь, а не промышленной строкой, которую никто не выберет.
    """
    complete = is_schedule_complete(1, group_ids, days_of_week, times_of_day)
    next_run = compute_next_run_at(days_of_week, times_of_day, "Europe/Moscow")
    assert not (complete and next_run is None)

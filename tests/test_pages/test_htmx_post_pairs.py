"""ПАРЫ ТРАНСПОРТОВ ПЕРЕВЕДЁННЫХ POST-ОБРАБОТЧИКОВ СТРАНИЧНОГО СЛОЯ (GATE-02, D-14).

ПОЧЕМУ ОДИН МОДУЛЬ. Критерий 4 роадмапа Фазы 11 требует пар «без htmx / с htmx»
на каждом переведённом обработчике — и прямо запрещает размножать их в «320
функций» (D-14). Функция-двойник на каждое утверждение 302 молчала бы о
следующем переведённом обработчике: своей функции у него ещё нет, и уронить
нечего. Параметризованный реестр плюс ЗАМЫКАНИЕ над множеством переведённых
превращают это молчание в красное: обработчик, пошедший через `respond()`, но не
получивший ни одного случая, называется поимённо.

ПРОЧТЕНИЕ КРИТЕРИЯ 4 (D-14). Вторая половина пары утверждает «путь htmx не
получает ни полного документа, ни перенаправления»:

| Ветка | Ответ на транспорте htmx |
|---|---|
| `FRAGMENT` — действие оставляет экран | 200, фрагмент несёт свою метку, `<!DOCTYPE` нет |
| `LOCATION` — действие уводит с экрана | 204, `HX-Location` посимвольно равен адресу 302, тела нет |
| `EXTERNAL` — переход на чужой сайт | 204, `HX-Redirect`, тела нет (первый случай — план 11-15) |

Буквальное «с заголовком → 200 для всех» отвергнуто: оно противоречит
отгруженной ветке перехода Фазы 8.

⚠️ СУЩЕСТВУЮЩИЕ УТВЕРЖДЕНИЯ 302 СУИТЫ НЕ ТРОГАЮТСЯ. Они остаются в своих файлах
и продолжают стеречь путь деградации; этот модуль добавляет к ним ВТОРУЮ
половину, а не переписывает первую. Обход, сличающий каждое такое утверждение с
парой, — предмет плана 11-20.

⚠️ ОБЕ ПОЛОВИНЫ НА СВЕЖЕМ СОСТОЯНИИ. Правка меняет строку; вторая половина,
пришедшая на уже изменённое состояние, проверяла бы не тот исход, который
названа проверять. Поэтому `arrange` зовётся дважды.

⚠️ ФИКСТУРА `htmx_client` ЗДЕСЬ НЕ ЗАПРАШИВАЕТСЯ — по основанию, записанному в
шапке `test_confirm_delete_transport.py`: она метит ОБЩИЙ объект клиента, и
половина деградации молча стала бы второй половиной htmx. Признак ставится на
один запрос из двух, а `follow_redirects=True` на половине htmx — часть
предмета: 302 пришёл бы ей кодом 200 и телом чужого документа.

⚠️ ЗАМЫКАНИЕ ПОКРЫВАЕТ ДВА РЕЕСТРА. Маршруты за панелью подтверждения уже имеют
пары в `CONFIRMED_DELETE_ROUTES` (Фаза 10) — дублировать их здесь значило бы
завести второй источник одного утверждения. Покрытыми считаются ключи ЭТОГО
реестра и ключи того.
"""
from dataclasses import dataclass
from typing import Awaitable, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule
from app.pages import notices
from app.pages.identifiers import ID_MAX
from tests.test_pages.test_account_groups import (
    _seed_account as _seed_groups_account,
    _seed_group as _seed_account_group,
)
from tests.test_pages.test_confirm_delete_transport import (
    CONFIRMED_DELETE_ROUTES,
    DOCUMENT_MARK,
    HTMX_HEADERS,
    _Arranged,
    _current_user,
    _foreign_user,
    _identify,
)
from tests.test_pages.test_editor_schedules import (
    _seed_account as _seed_editor_account,
    _seed_ad as _seed_editor_ad,
    _seed_group as _seed_editor_group,
    _seed_schedule,
)
from tests.test_pages.test_htmx_gates import _pages_sources, _post_handlers

# Ожидаемая форма ответа на транспорте htmx.
FRAGMENT = "ожидается 200 и фрагмент"
LOCATION = "ожидается 204 и заголовок перехода"
EXTERNAL = "ожидается 204 и заголовок внешнего перехода"


@dataclass(frozen=True)
class _PairCase:
    """ОДИН случай пары: обработчик × исход × ожидаемая форма ответа htmx.

    `landing` и `fragment_mark` — строки формата над `_Arranged.landing_args`:
    идентификаторы появляются только после посева, а посев у каждой половины
    свой.

    ⚠️ `resolve_after` СУЩЕСТВУЕТ ДЛЯ СОЗДАЮЩИХ ДЕЙСТВИЙ, И ЭТО НЕ УДОБСТВО
    (Фаза 11, план 11-05). У правки и тумблера идентификатор строки известен
    ПОСЕВОМ, то есть до запроса. У СОЗДАНИЯ его не существует до запроса вовсе:
    строку заводит сам запрос, и адрес приземления называет её идентификатор.
    Предсказывать его сложением единицы к посеянному значило бы утверждать
    поведение автоинкремента драйвера вместо поведения обработчика — правило
    краснело бы на смене драйвера и зеленело бы на неверном адресе, совпавшем с
    предсказанием. Поэтому подстановки адреса ДОБИРАЮТСЯ ИЗ БАЗЫ ПОСЛЕ запроса,
    и обе половины добирают их независимо, каждая на своём состоянии.
    """

    key: str
    name: str
    identity: str
    arrange: Callable[..., Awaitable[_Arranged]]
    landing: str
    transport: str
    fragment_mark: str | None = None
    resolve_after: Callable[[AsyncSession, _Arranged], Awaitable[dict]] | None = None

    @property
    def handler(self) -> str:
        return self.key.split("::", 1)[1]


# =============================================================================
# Посев: правка расписания в редакторе объявления
# =============================================================================

SCHEDULES_UPDATE = "app/pages/schedules.py::schedules_update"
MISSING_SCHEDULE_ID = 987654
# Первая величина вне колонки идентификатора — 2147483648 (Фаза 11, план 11-02).
OUT_OF_COLUMN_SCHEDULE_ID = ID_MAX + 1


async def _seed_editor_schedule(db: AsyncSession, user_id: int):
    ad = await _seed_editor_ad(db, user_id)
    account = await _seed_editor_account(db, user_id)
    schedule = await _seed_schedule(db, ad.id, account.id)
    return ad, account, schedule


def _edit_body(ad_id: int, account_id: int, *, to_editor: bool = True) -> dict:
    body = {
        "ad_id": str(ad_id),
        "account_id": str(account_id),
        "days_of_week": "1",
        "times_of_day": "18:30",
        "timezone": "UTC",
    }
    if to_editor:
        body["return_to"] = "editor"
    return body


async def _arrange_edit_success(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad, account, schedule = await _seed_editor_schedule(db, user.id)
    return _Arranged(
        url=f"/schedules/{schedule.id}/edit",
        data=_edit_body(ad.id, account.id),
        landing_args={"ad_id": ad.id, "schedule_id": schedule.id},
    )


async def _arrange_edit_missing_schedule(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    # Объявление СВОЁ, расписания с таким идентификатором нет вовсе.
    ad = await _seed_editor_ad(db, user.id)
    account = await _seed_editor_account(db, user.id)
    return _Arranged(
        url=f"/schedules/{MISSING_SCHEDULE_ID}/edit",
        data=_edit_body(ad.id, account.id),
        landing_args={"ad_id": ad.id},
    )


async def _arrange_edit_out_of_column_schedule(
    client, db, settings, identity
) -> _Arranged:
    user = await _current_user(db, identity, settings)
    # Объявление СВОЁ, идентификатор расписания лежит ВНЕ колонки (Фаза 11,
    # план 11-02, D-07): величина идёт той же веткой, что и отсутствующее
    # расписание, — посимвольно тем же адресом приземления.
    ad = await _seed_editor_ad(db, user.id)
    account = await _seed_editor_account(db, user.id)
    return _Arranged(
        url=f"/schedules/{OUT_OF_COLUMN_SCHEDULE_ID}/edit",
        data=_edit_body(ad.id, account.id),
        landing_args={"ad_id": ad.id},
    )


async def _arrange_edit_foreign_ad(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    _, account, schedule = await _seed_editor_schedule(db, user.id)
    # Расписание своё, а объявление в теле формы — чужое: вердикт владения
    # отказывает по объявлению.
    stranger = await _foreign_user(db)
    foreign_ad = await _seed_editor_ad(db, stranger.id, title="Чужое объявление")
    return _Arranged(
        url=f"/schedules/{schedule.id}/edit",
        data=_edit_body(foreign_ad.id, account.id),
    )


async def _arrange_edit_account_gone(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad, _, schedule = await _seed_editor_schedule(db, user.id)
    # Объявление своё, аккаунт в теле формы — чужой: вердикт владения отказывает
    # по аккаунту, и человека можно вернуть в его редактор с объяснением.
    stranger = await _foreign_user(db)
    foreign_account = await _seed_editor_account(db, stranger.id)
    return _Arranged(
        url=f"/schedules/{schedule.id}/edit",
        data=_edit_body(ad.id, foreign_account.id),
        landing_args={"ad_id": ad.id},
    )


async def _arrange_edit_without_marker(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad, account, schedule = await _seed_editor_schedule(db, user.id)
    return _Arranged(
        url=f"/schedules/{schedule.id}/edit",
        data=_edit_body(ad.id, account.id, to_editor=False),
    )


# =============================================================================
# Посев: тумблер расписания (Фаза 11, план 11-03)
# =============================================================================

SCHEDULES_TOGGLE = "app/pages/schedules.py::schedules_toggle"


async def _arrange_toggle_editor_success(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad, _, schedule = await _seed_editor_schedule(db, user.id)
    return _Arranged(
        url=f"/schedules/{schedule.id}/toggle",
        data={"return_to": "editor"},
        landing_args={"ad_id": ad.id, "schedule_id": schedule.id},
    )


async def _arrange_toggle_out_of_domain(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad = await _seed_editor_ad(db, user.id)
    account = await _seed_editor_account(db, user.id)
    group = await _seed_editor_group(db, user.id, account.id)
    # По составу полное, по значениям неисполнимое: день `9` не день недели
    # (CR-01). Возобновление отказывает кодом реестра.
    schedule = await _seed_schedule(
        db,
        ad.id,
        account.id,
        group_ids=[group.id],
        days=[9],
        times=["10:00"],
        is_active=False,
    )
    return _Arranged(
        url=f"/schedules/{schedule.id}/toggle",
        data={"return_to": "editor"},
        landing_args={"ad_id": ad.id},
    )


async def _arrange_toggle_missing(client, db, settings, identity) -> _Arranged:
    return _Arranged(
        url=f"/schedules/{MISSING_SCHEDULE_ID}/toggle",
        data={"return_to": "editor"},
    )


async def _arrange_toggle_from_list(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    _, _, schedule = await _seed_editor_schedule(db, user.id)
    # Строка сводного списка признака возврата не шлёт. Идентификатор уезжает в
    # `landing_args` затем, что метку фрагмента (строку своего экрана) можно
    # назвать только после посева.
    return _Arranged(
        url=f"/schedules/{schedule.id}/toggle",
        data={},
        landing_args={"schedule_id": schedule.id},
    )


# =============================================================================
# Посев: создание расписания в редакторе объявления (Фаза 11, план 11-05)
# =============================================================================

SCHEDULES_CREATE = "app/pages/schedules.py::schedules_create"


def _create_body(ad_id: int, account_id: int, *, to_editor: bool = True) -> dict:
    body = {"ad_id": str(ad_id), "account_id": str(account_id)}
    if to_editor:
        body["return_to"] = "editor"
    return body


async def _created_schedule_of_the_ad(db: AsyncSession, arranged: _Arranged) -> dict:
    """Идентификатор строки, заведённой ЭТОЙ половиной пары.

    Выборка скоуплена объявлением ИЗ ТЕЛА ФОРМЫ и берёт последнюю строку по
    возрастанию идентификатора — то есть ровно ту, которую создал запрос этой
    половины. Соседняя половина сеет СВОЁ объявление, поэтому две половины друг
    друга не видят и порядок их исполнения на результат не влияет.
    """
    ad_id = int(arranged.data["ad_id"])
    row = (
        await db.execute(
            select(Schedule)
            .where(Schedule.ad_id == ad_id)
            .order_by(Schedule.id.desc())
            .limit(1)
        )
    ).scalars().first()
    return {"schedule_id": row.id} if row is not None else {}


async def _arrange_create_into_a_list(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    # Список НЕ пуст: контейнер на экране есть, и новой карточке есть куда
    # приземлиться (D-05).
    ad, account, _ = await _seed_editor_schedule(db, user.id)
    return _Arranged(
        url="/schedules/new",
        data=_create_body(ad.id, account.id),
        landing_args={"ad_id": ad.id},
    )


async def _arrange_create_the_first_one(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    # Расписаний нет: контейнера в документе нет вовсе, и ответ уходит переходом.
    ad = await _seed_editor_ad(db, user.id)
    account = await _seed_editor_account(db, user.id)
    return _Arranged(
        url="/schedules/new",
        data=_create_body(ad.id, account.id),
        landing_args={"ad_id": ad.id},
    )


async def _arrange_create_on_a_foreign_ad(client, db, settings, identity) -> _Arranged:
    await _current_user(db, identity, settings)
    stranger = await _foreign_user(db)
    foreign_ad = await _seed_editor_ad(db, stranger.id, title="Чужое объявление")
    foreign_account = await _seed_editor_account(db, stranger.id)
    return _Arranged(
        url="/schedules/new",
        data=_create_body(foreign_ad.id, foreign_account.id),
    )


async def _arrange_create_with_account_gone(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad = await _seed_editor_ad(db, user.id)
    # Объявление своё, аккаунт в теле формы — чужой: вердикт владения отказывает
    # по аккаунту, и человека возвращают в ЕГО редактор с объяснением.
    stranger = await _foreign_user(db)
    foreign_account = await _seed_editor_account(db, stranger.id)
    return _Arranged(
        url="/schedules/new",
        data=_create_body(ad.id, foreign_account.id),
        landing_args={"ad_id": ad.id},
    )


# =============================================================================
# Посев: тумблер группы аккаунта (Фаза 9)
# =============================================================================


async def _arrange_group_toggle(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    account = await _seed_groups_account(db, "wa", user_id=user.id)
    group = await _seed_account_group(db, account, "Группа пары", user_id=user.id)
    return _Arranged(
        url=f"/accounts/{account.id}/groups/{group.id}/toggle",
        data={"is_active": "on"},
        landing_args={"account_id": account.id, "group_id": group.id},
    )


# =============================================================================
# РЕЕСТР
# =============================================================================

POST_PAIR_CASES: tuple[_PairCase, ...] = (
    # Фаза 11, план 11-01. Правка расписания в редакторе: карточка остаётся на
    # экране и подменяет саму себя (D-02).
    _PairCase(
        key=SCHEDULES_UPDATE,
        name="правка расписания — успех",
        identity="user",
        arrange=_arrange_edit_success,
        landing="/ads/{ad_id}/edit?sched={schedule_id}#sched-{schedule_id}",
        transport=FRAGMENT,
        fragment_mark='id="sched-{schedule_id}"',
    ),
    # Исходы, НЕ оставляющие карточку на экране (D-06): код реестра едет ровно
    # там, где он выдаётся сегодня.
    _PairCase(
        key=SCHEDULES_UPDATE,
        name="правка расписания — расписания нет при своём объявлении",
        identity="user",
        arrange=_arrange_edit_missing_schedule,
        landing="/ads/{ad_id}/edit?notice=" + notices.SCHEDULE_AD_MISSING,
        transport=LOCATION,
    ),
    # Фаза 11, план 11-02 (D-07). Идентификатор вне колонки — та же ветка, что у
    # отсутствующего расписания: неразличимость «вне диапазона» и «нет строки»
    # (T-11-05) утверждается посимвольным равенством адреса приземления.
    _PairCase(
        key=SCHEDULES_UPDATE,
        name="правка расписания — идентификатор вне колонки при своём объявлении",
        identity="user",
        arrange=_arrange_edit_out_of_column_schedule,
        landing="/ads/{ad_id}/edit?notice=" + notices.SCHEDULE_AD_MISSING,
        transport=LOCATION,
    ),
    _PairCase(
        key=SCHEDULES_UPDATE,
        name="правка расписания — объявление чужое",
        identity="user",
        arrange=_arrange_edit_foreign_ad,
        landing="/schedules",
        transport=LOCATION,
    ),
    _PairCase(
        key=SCHEDULES_UPDATE,
        name="правка расписания — аккаунт недоступен",
        identity="user",
        arrange=_arrange_edit_account_gone,
        landing="/ads/{ad_id}/edit?notice=" + notices.SCHEDULE_ACCOUNT_GONE,
        transport=LOCATION,
    ),
    # На сводном списке карточки нет — то же основание, что у ветки `WR-01`
    # удаления: фрагменту редактора там некуда приземлиться.
    _PairCase(
        key=SCHEDULES_UPDATE,
        name="правка расписания — без признака возврата",
        identity="user",
        arrange=_arrange_edit_without_marker,
        landing="/schedules",
        transport=LOCATION,
    ),
    # Фаза 11, план 11-03. Тумблер расписания: в редакторе карточка подменяет
    # саму себя с серверным состоянием (D-02, D-11).
    _PairCase(
        key=SCHEDULES_TOGGLE,
        name="тумблер расписания — успех в редакторе",
        identity="user",
        arrange=_arrange_toggle_editor_success,
        landing="/ads/{ad_id}/edit",
        transport=FRAGMENT,
        fragment_mark='id="sched-{schedule_id}"',
    ),
    # Исход уводит с экрана тем же кодом реестра, что и без htmx (D-06).
    _PairCase(
        key=SCHEDULES_TOGGLE,
        name="тумблер расписания — значения вне области",
        identity="user",
        arrange=_arrange_toggle_out_of_domain,
        landing="/ads/{ad_id}/edit?notice=" + notices.SCHEDULE_VALUES_OUT_OF_DOMAIN,
        transport=LOCATION,
    ),
    _PairCase(
        key=SCHEDULES_TOGGLE,
        name="тумблер расписания — расписания нет",
        identity="user",
        arrange=_arrange_toggle_missing,
        landing="/schedules",
        transport=LOCATION,
    ),
    # Фаза 11, план 11-04 (D-02, D-11). Строка сводного списка подменяет САМУ
    # СЕБЯ: экран остаётся, и цель у фрагмента на нём есть — сама строка.
    # ⚠️ ВЕТКА СМЕНИЛА КЛАСС, А НЕ ЗАВЕЛАСЬ ЗАНОВО: планом 11-03 этот же случай
    # стоял переходом (`LOCATION`), потому что разметки строки под фрагмент ещё
    # не было и приземляться ответу было некуда. Адрес деградации при этом не
    # сдвинулся ни на символ — половина без признака по-прежнему 302 на
    # `/schedules`, и именно её неподвижность доказывает, что сменилась ФОРМА
    # ОТВЕТА, а не поведение действия.
    _PairCase(
        key=SCHEDULES_TOGGLE,
        name="тумблер расписания — со сводного списка",
        identity="user",
        arrange=_arrange_toggle_from_list,
        landing="/schedules",
        transport=FRAGMENT,
        fragment_mark='id="schedule-row-{schedule_id}"',
    ),
    # Фаза 11, план 11-05. Создание расписания: карточка ВСТАВЛЯЕТСЯ в список
    # редактора, контейнер не перерисовывается (D-05, FORM-07).
    _PairCase(
        key=SCHEDULES_CREATE,
        name="создание расписания — в непустой список",
        identity="user",
        arrange=_arrange_create_into_a_list,
        landing="/ads/{ad_id}/edit?sched={schedule_id}#sched-{schedule_id}",
        transport=FRAGMENT,
        fragment_mark='id="sched-{schedule_id}"',
        resolve_after=_created_schedule_of_the_ad,
    ),
    # ⚠️ «БЫЛО НОЛЬ» — ПЕРЕХОД, И ЭТО НЕ ОТСТУПЛЕНИЕ ОТ ФРАГМЕНТНОГО КЛАССА, А
    # ЕГО ГРАНИЦА: при пустом списке контейнера в документе нет вовсе, и
    # приземляться фрагменту некуда (D-05). Адрес — тот же, посимвольно.
    _PairCase(
        key=SCHEDULES_CREATE,
        name="создание расписания — было ноль",
        identity="user",
        arrange=_arrange_create_the_first_one,
        landing="/ads/{ad_id}/edit?sched={schedule_id}#sched-{schedule_id}",
        transport=LOCATION,
        resolve_after=_created_schedule_of_the_ad,
    ),
    _PairCase(
        key=SCHEDULES_CREATE,
        name="создание расписания — объявление чужое",
        identity="user",
        arrange=_arrange_create_on_a_foreign_ad,
        landing="/schedules",
        transport=LOCATION,
    ),
    _PairCase(
        key=SCHEDULES_CREATE,
        name="создание расписания — аккаунт недоступен",
        identity="user",
        arrange=_arrange_create_with_account_gone,
        landing="/ads/{ad_id}/edit?notice=" + notices.SCHEDULE_ACCOUNT_GONE,
        transport=LOCATION,
    ),
    # Фаза 9, план 09-01, заведено планом 11-01. Первый фрагментный обработчик
    # вехи; в `CONFIRMED_DELETE_ROUTES` его нет (за панелью подтверждения он не
    # стоит), и без этой записи замыкание называет его непокрытым.
    _PairCase(
        key="app/pages/account_groups.py::account_groups_toggle",
        name="тумблер группы аккаунта — успех",
        identity="user",
        arrange=_arrange_group_toggle,
        landing="/accounts/{account_id}/groups",
        transport=FRAGMENT,
        fragment_mark='id="group-row-{group_id}"',
    ),
)

# ЛЕТОПИСЬ ЧИСЛА (каждое движение — запись, число ставится ПРОГОНОМ):
#   0 → 6, Фаза 11, план 11-01: реестр заведён — пять исходов правки расписания
#   в редакторе объявления и успех тумблера группы аккаунта.
#   6 → 7, Фаза 11, план 11-02: правка с идентификатором расписания вне колонки
#   (D-07) — та же ветка, что у отсутствующего расписания.
#   7 → 11, Фаза 11, план 11-03: четыре исхода переключения расписания — успех
#   в редакторе (фрагмент), значения вне области, расписания нет и строка
#   сводного списка (переход).
#   11 → 15, Фаза 11, план 11-05: четыре исхода СОЗДАНИЯ расписания — вставка в
#   непустой список (фрагмент), «было ноль», чужое объявление и недоступный
#   аккаунт (переход).
POST_PAIR_CASES_DECLARED = 15


def _case_id(case: _PairCase) -> str:
    return f"{case.handler}-{case.name}"


async def _landing_args(
    case: _PairCase, db: AsyncSession, arranged: _Arranged
) -> dict:
    """Подстановки адреса приземления, добранные ПОСЛЕ запроса, если случай просит.

    Случай без `resolve_after` отдаёт подстановки посева неизменными — то есть
    одиннадцать прежних записей проходят этот помощник байт-в-байт тем же
    словарём, каким пользовались до него.
    """
    if case.resolve_after is None:
        return arranged.landing_args
    return {**arranged.landing_args, **await case.resolve_after(db, arranged)}


# =============================================================================
# ОБХОД: обе половины пары
# =============================================================================


@pytest.mark.parametrize("case", POST_PAIR_CASES, ids=_case_id)
@pytest.mark.asyncio
async def test_every_pair_case_answers_both_transports(
    case: _PairCase, client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Без признака — 302 на адрес посимвольно; с признаком — форма по ветке."""
    await _identify(client, case.identity, test_settings)

    degraded = await case.arrange(client, db_session, test_settings, case.identity)
    with degraded.context():
        without = await client.post(
            degraded.url, data=degraded.data, follow_redirects=False
        )
    # Подстановки добираются ПОСЛЕ запроса: у создающего действия строки, чей
    # идентификатор называет адрес, до запроса не существует (см. `_PairCase`).
    expected = case.landing.format(**await _landing_args(case, db_session, degraded))
    assert without.status_code == 302, (
        f"{case.name}: путь деградации ответил {without.status_code} вместо 302"
    )
    assert without.headers["location"] == expected, (
        f"{case.name}: адрес деградации {without.headers['location']!r} не совпал "
        f"с ожидаемым {expected!r} ПОСИМВОЛЬНО"
    )

    arranged = await case.arrange(client, db_session, test_settings, case.identity)
    with arranged.context():
        with_layer = await client.post(
            arranged.url,
            data=arranged.data,
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )
    landing_args = await _landing_args(case, db_session, arranged)
    expected = case.landing.format(**landing_args)

    assert DOCUMENT_MARK not in with_layer.text, (
        f"{case.name}: слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ — обработчик ответил "
        "перенаправлением, и клиент прошёл по нему прозрачно"
    )

    if case.transport is FRAGMENT:
        assert with_layer.status_code == 200, (
            f"{case.name}: фрагментный путь ответил {with_layer.status_code} вместо 200"
        )
        mark = case.fragment_mark.format(**landing_args)
        assert mark in with_layer.text, (
            f"{case.name}: во фрагменте нет метки {mark!r}"
        )
        return

    if case.transport is LOCATION:
        assert with_layer.status_code == 204, (
            f"{case.name}: слою письма ответили {with_layer.status_code} вместо 204"
        )
        assert with_layer.headers.get("HX-Location") == expected, (
            f"{case.name}: заголовок перехода {with_layer.headers.get('HX-Location')!r} "
            f"не совпал с адресом деградации {expected!r}"
        )
        assert with_layer.content == b"", f"{case.name}: у ответа 204 появилось тело"
        return

    assert case.transport is EXTERNAL, f"{case.name}: неизвестная ветка {case.transport!r}"
    assert with_layer.status_code == 204
    assert with_layer.headers.get("HX-Redirect") == expected
    assert with_layer.content == b""


# =============================================================================
# ЧИСЛО И ЗАМЫКАНИЕ
# =============================================================================


def test_the_number_of_pair_cases_is_the_declared_one():
    """Длина реестра равна объявленному числу; пустой реестр краснит."""
    assert POST_PAIR_CASES, "реестр пар пуст — обход вакуумно зелен"
    assert len(POST_PAIR_CASES) == POST_PAIR_CASES_DECLARED, (
        f"случаев пар в реестре {len(POST_PAIR_CASES)}, объявлено "
        f"{POST_PAIR_CASES_DECLARED}. Поставьте число ПРОГОНОМ этого отказа"
    )
    ids = [_case_id(case) for case in POST_PAIR_CASES]
    assert len(set(ids)) == len(ids), "два случая названы одинаково"


def _closure_complaints(
    cases: tuple[_PairCase, ...], sources: dict[str, str] | None = None
) -> list[str]:
    """Переведённые POST-обработчики, у которых нет НИ ОДНОГО случая пары.

    Реестр приходит параметром, чтобы контроль ниже проверял ТУ ЖЕ проверку, а не
    её вторую копию.
    """
    handlers = _post_handlers(_pages_sources() if sources is None else sources)
    converted = {key for key, handler in handlers.items() if handler.calls_respond}
    covered = {case.key for case in cases} | {
        route.key for route in CONFIRMED_DELETE_ROUTES
    }
    return sorted(converted - covered)


def test_every_converted_handler_has_a_pair():
    """ЗАМЫКАНИЕ: каждый обработчик на слое ответа имеет хотя бы одну пару."""
    complaints = _closure_complaints(POST_PAIR_CASES)
    assert not complaints, (
        "обработчики идут через слой ответа, но пары транспортов у них нет ни в "
        "реестре `POST_PAIR_CASES`, ни в `CONFIRMED_DELETE_ROUTES`:\n  "
        + "\n  ".join(complaints)
    )


def test_control_a_handler_without_a_case_reddens_the_closure():
    """Отрицательный контроль: реестр без правки расписания — замыкание называет её."""
    stripped = tuple(case for case in POST_PAIR_CASES if case.key != SCHEDULES_UPDATE)
    assert len(stripped) < len(POST_PAIR_CASES), "контроль ничего не снял"
    assert SCHEDULES_UPDATE in _closure_complaints(stripped), (
        "замыкание не заметило обработчика без единого случая — правило вакуумно"
    )

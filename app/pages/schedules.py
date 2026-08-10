import re
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.constants import AD_STATUS_DRAFT, VALID_TIMEZONES
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.services.schedule_service import compute_next_run_at
from app.pages.common import check_is_admin, get_user_from_cookie, templates

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30

# Признак «пришло из редактора объявления». Это ПРИЗНАК, а не адрес: значение
# поля формы подконтрольно отправителю, и подстановка его в редирект как есть
# была бы открытым редиректом (T-02-23) — страница увела бы пользователя на
# чужой домен сразу после успешного сохранения. Адрес строит сервер сам, из
# идентификатора объявления УЖЕ ПРОВЕРЕННОЙ на владение записи.
RETURN_TO_EDITOR = "editor"

# Формат значения времени: два числа через двоеточие в допустимых диапазонах.
# Проверка стоит ДО вызова compute_next_run_at, который разбирает строку
# `int(parts[0])` / `parts[1]` без всякой защиты: любое значение не этого
# формата давало 500 на прямом POST мимо браузера (T-02-24, Pitfall 9).
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

# Время, которым заполняется только что добавленная таблетка. Пустое значение
# хранить нельзя: обработчик отбрасывает пустые строки, и «+ ВРЕМЯ» без JS не
# оставлял бы после себя ничего видимого.
DEFAULT_TIME = "09:00"

# Сколько имён групп показывает карточка сводного списка, прежде чем остаток
# сворачивается в «и ещё K». SCH-04 и критерий 4 перечисляют группы наравне с
# объявлением, каналом, днями и временем — то есть требуют СОДЕРЖАНИЯ, а не
# количества; предел существует, чтобы карточка не росла неограниченно.
SUMMARY_GROUP_NAMES = 3

# Оси фильтрации сводного списка (UI-SPEC §Copywriting Contract, E14). Значения
# канала — те же, что у `MessengerAccount.type`; значения состояния описывают
# `Schedule.is_active`. Перечни объявлены здесь, а не в шаблоне: неизвестное
# значение обязано отсекаться СЕРВЕРОМ, разметка точкой принуждения не является.
CHANNEL_FILTER_VALUES = ("tg_user", "wa", "max")
STATE_FILTER_VALUES = ("active", "paused")


def _clean_choice(value: str | None, allowed) -> str:
    """Неизвестное или испорченное значение фильтра → вариант «Все».

    Пустая строка означает «не фильтровать по этой оси». Отказ страницы был бы
    здесь неверным исходом: значение приходит строкой запроса, то есть из
    ссылки, закладки или чужого сообщения, и уронить на нём страницу — это
    отказ в обслуживании по подконтрольному отправителю значению (T-02-35).
    """
    if not value:
        return ""
    value = value.strip()
    return value if value in allowed else ""


def _filter_params(channel: str, state: str, search: str) -> dict:
    """Действующие фильтры для URL сентинела бесконечной прокрутки.

    Потерянный здесь фильтр не роняет страницу — он молча подмешивает
    неотфильтрованные расписания к отфильтрованным на второй странице выдачи.
    """
    params = {}
    if channel:
        params["channel"] = channel
    if state:
        params["state"] = state
    if search:
        params["search"] = search
    return params


async def _time_matching_ids(db: AsyncSession, user_id: int, term: str) -> list[int]:
    """Расписания, у которых искомое встречается во ВРЕМЕНИ запуска.

    Времена лежат JSON-массивом, и переносимого предиката «подстрока внутри
    элемента массива» у проекта нет: `app/pages/groups.py` по той же причине
    считает расписания по группам в Python. Запрос ОДИН и выполняется только
    при непустом поиске — по числу расписаний страницы он не растёт.
    """
    rows = await db.execute(
        select(Schedule.id, Schedule.times_of_day)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Ad.user_id == user_id)
    )
    needle = term.lower()
    return [
        row.id
        for row in rows
        if any(needle in (t or "").lower() for t in (row.times_of_day or []))
    ]


async def _group_names_for(db: AsyncSession, user_id: int, schedules) -> dict[int, str]:
    """Отображение «идентификатор группы → имя» для ВСЕЙ страницы одним запросом.

    Запрос обязан ограничиваться группами пользователя. Расписание хранит
    идентификаторы групп массивом и своего `user_id` не имеет: без связки по
    владельцу достаточно сохранить своё расписание с чужим идентификатором,
    чтобы имя чужой группы отрисовалось в карточке (T-02-34).

    Запросов НА РАСПИСАНИЕ не делается — образец обогащения одним
    сгруппированным запросом стоит в `app/pages/ads.py:_enrich_ads_with_stats`
    (T-02-38).
    """
    ids = {
        gid
        for schedule in schedules
        for gid in (schedule.group_ids or [])
        if isinstance(gid, int)
    }
    if not ids:
        return {}
    rows = await db.execute(
        select(Group.id, Group.name).where(Group.id.in_(ids), Group.user_id == user_id)
    )
    return {row.id: row.name for row in rows}


def _clean_times(values: list[str]) -> list[str]:
    """Оставить только значения формата ЧЧ:ММ, сохранив порядок."""
    return [v for v in values if _TIME_RE.match(v.strip())]


def _clean_ints(values: list[str], low: int | None = None, high: int | None = None) -> list[int]:
    """Привести к числам, отбросив непреобразуемые и вышедшие из диапазона.

    Отбрасывание, а не отказ: список идентификаторов групп и дней приходит
    повторяющимися полями формы, и одно испорченное значение не повод потерять
    остальные. Без этой фильтрации `int(g)` бросал ValueError на любой строке —
    то есть 500 вместо валидации (T-02-25).
    """
    cleaned: list[int] = []
    for value in values:
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if low is not None and number < low:
            continue
        if high is not None and number > high:
            continue
        cleaned.append(number)
    return cleaned


def _is_complete(
    account_id: int | None,
    group_ids: list[int],
    days_of_week: list[int],
    times_of_day: list[str],
) -> bool:
    """D-08: заполнено ли расписание настолько, чтобы его можно было включить.

    Одно определение на все четыре обработчика и на разметку карточки
    (app/templates/ads/includes/sched_card.html): второе разъехалось бы с
    первым, и пользователь видел бы бейдж «Не заполнено» на расписании, которое
    сервер считает полным.
    """
    return bool(account_id and group_ids and days_of_week and times_of_day)


def _editor_redirect(form_data, ad_id: int | None, schedule_id: int | None = None):
    """Куда вернуть пользователя после правки расписания.

    Признак происхождения читается из формы, но АДРЕС строится здесь: из
    `ad_id`, взятого из записи, владение которой уже подтверждено запросом.
    Значение поля в адрес не попадает ни при каких условиях (T-02-23).

    Без признака поведение прежнее — сводный список: сводная страница
    продолжает работать ровно так, как работала.
    """
    if form_data.get("return_to") == RETURN_TO_EDITOR and ad_id is not None:
        url = f"/ads/{ad_id}/edit"
        if schedule_id is not None:
            url += f"?sched={schedule_id}#sched-{schedule_id}"
        return RedirectResponse(url=url, status_code=302)
    return RedirectResponse(url="/schedules", status_code=302)


def _apply_named_actions(
    form_data,
    group_ids: list[int],
    days_of_week: list[int],
    times_of_day: list[str],
    available_group_ids: list[int],
) -> tuple[list[int], list[int], list[str]]:
    """Пресеты дней, групповое действие и работа со временами — БЕЗ JavaScript.

    Каждый элемент управления карточки — ИМЕНОВАННАЯ кнопка отправки (образец —
    `remove_image` в редакторе объявления). Обработка на сервере означает, что
    базовый путь и улучшенный — один и тот же код: разойтись им негде, и
    отключённый Alpine не превращает кнопку в молчаливую заглушку.
    """
    days_preset = form_data.get("days_preset")
    if days_preset == "workdays":
        days_of_week = [0, 1, 2, 3, 4]
    elif days_preset == "everyday":
        days_of_week = [0, 1, 2, 3, 4, 5, 6]

    groups_preset = form_data.get("groups_preset")
    if groups_preset == "all":
        group_ids = list(available_group_ids)
    elif groups_preset == "none":
        group_ids = []

    removed = form_data.get("remove_time")
    if removed and removed in times_of_day:
        # Ровно ОДНО вхождение: порядок остальных времён сохраняется.
        times_of_day.remove(removed)
    if "add_time" in form_data:
        times_of_day = times_of_day + [DEFAULT_TIME]

    return group_ids, days_of_week, times_of_day


async def _owns_ad_and_account(
    db: AsyncSession, user_id: int, ad_id: int, account_id: int | None
) -> bool:
    """Проверить владение объявлением и аккаунтом мессенджера запросом.

    Владение проверяется запросом со связкой по `user_id`, а не выборкой строки
    с последующим сравнением: так «нет такой строки» и «строка чужая» дают один
    и тот же исход, и ветку невозможно забыть.

    `account_id` в схеме nullable с `ON DELETE SET NULL` (issue #35): пустое
    значение — законное состояние отвязанного расписания, поэтому проверка
    владения применяется только к непустому значению.
    """
    own_ad = (
        await db.execute(
            select(Ad.id).where(Ad.id == ad_id, Ad.user_id == user_id)
        )
    ).scalar_one_or_none()
    if own_ad is None:
        return False

    if account_id is None:
        return True

    own_account = (
        await db.execute(
            select(MessengerAccount.id).where(
                MessengerAccount.id == account_id,
                MessengerAccount.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    return own_account is not None


def _summary_query(user_id: int):
    """Общий каркас выдачи сводного списка: соединения и связка по владельцу."""
    return (
        select(
            Schedule,
            Ad.title.label("ad_title"),
            Ad.status.label("ad_status"),
            MessengerAccount.type.label("messenger_type"),
        )
        .join(Ad, Schedule.ad_id == Ad.id)
        # outer join: расписание с удалённым аккаунтом (account_id IS NULL)
        # должно остаться видимым (issue #35)
        .join(MessengerAccount, Schedule.account_id == MessengerAccount.id, isouter=True)
        .where(Ad.user_id == user_id)
    )


def _summary_count_query(user_id: int):
    """Тот же набор строк, но счётчиком: подпись «{n} расписаний» считает ВСЕ
    найденные, а не только попавшие на первую страницу выдачи."""
    return (
        select(func.count())
        .select_from(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .join(MessengerAccount, Schedule.account_id == MessengerAccount.id, isouter=True)
        .where(Ad.user_id == user_id)
    )


def _apply_filters(query, channel: str, state: str, search: str, time_ids: list[int]):
    """Три оси фильтрации, одинаковые для страницы, счётчика и порции прокрутки.

    Один набор условий на три запроса: разъехавшись, счётчик показывал бы одно
    число, а список — другой набор карточек.
    """
    if channel:
        query = query.where(MessengerAccount.type == channel)
    if state:
        query = query.where(Schedule.is_active.is_(state == "active"))
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(Ad.title.ilike(pattern), Schedule.id.in_(time_ids))
        )
    return query


def _build_schedule_items(result, user, tz, group_names=None):
    """Build schedule items with next_run_local from raw query result.

    `group_names` — отображение, полученное ОДНИМ запросом на страницу.
    Идентификатор, которому имени не нашлось (группа удалена или отвязана), в
    имена не превращается и не рендерится пустой строкой; остаток «и ещё K»
    считается по РАЗРЕШЁННЫМ именам, иначе карточка обещала бы группы, показать
    которые нечем.
    """
    names = group_names or {}
    items = [
        {
            "schedule": r.Schedule,
            "ad_title": r.ad_title,
            "messenger_type": r.messenger_type,
            # Сравнение с КОНСТАНТОЙ, а не со строковым литералом: значение
            # состояния объявления живёт в app/constants.py единственным
            # источником на весь проект (D-02).
            "is_draft": r.ad_status == AD_STATUS_DRAFT,
        }
        for r in result
    ]
    tz_name = user.timezone if user.timezone in VALID_TIMEZONES else "UTC"
    for item in items:
        sched = item["schedule"]
        resolved = [
            names[gid] for gid in (sched.group_ids or []) if gid in names
        ]
        item["group_names"] = resolved[:SUMMARY_GROUP_NAMES]
        item["group_extra"] = max(len(resolved) - SUMMARY_GROUP_NAMES, 0)
        item["group_total"] = len(resolved)
        if sched.next_run_at:
            item["next_run_local"] = sched.next_run_at.astimezone(tz)
            item["tz_label"] = tz_name.split("/")[-1] if "/" in tz_name else tz_name
        else:
            item["next_run_local"] = None
            item["tz_label"] = ""
    return items


@router.get("/schedules/partial", response_class=HTMLResponse)
async def schedules_partial(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=100),
    channel: str | None = Query(None),
    state: str | None = Query(None),
    search: str | None = Query(None),
    # D-15: параметр компоновки принимается и игнорируется — см. app/pages/ads.py
    layout: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    tz_name = user.timezone if user.timezone in VALID_TIMEZONES else "UTC"
    tz = ZoneInfo(tz_name)

    channel = _clean_choice(channel, CHANNEL_FILTER_VALUES)
    state = _clean_choice(state, STATE_FILTER_VALUES)
    search = (search or "").strip()
    time_ids = await _time_matching_ids(db, user.id, search) if search else []

    query = _apply_filters(_summary_query(user.id), channel, state, search, time_ids)
    result = await db.execute(
        query.order_by(Schedule.id).offset(offset).limit(limit + 1)
    )
    rows = list(result)
    has_next = len(rows) > limit
    page = rows[:limit]
    group_names = await _group_names_for(db, user.id, [r.Schedule for r in page])
    schedules = _build_schedule_items(page, user, tz, group_names)
    return templates.TemplateResponse(
        "schedules/partial_cards.html",
        {
            "request": request,
            "user": user,
            "schedules": schedules,
            "has_next": has_next,
            "next_offset": offset + limit,
            "filter_params": _filter_params(channel, state, search),
        },
    )


@router.get("/schedules", response_class=HTMLResponse)
async def schedules_list(
    request: Request,
    channel: str | None = Query(None),
    state: str | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    tz_name = user.timezone if user.timezone in VALID_TIMEZONES else "UTC"
    tz = ZoneInfo(tz_name)

    channel = _clean_choice(channel, CHANNEL_FILTER_VALUES)
    state = _clean_choice(state, STATE_FILTER_VALUES)
    search = (search or "").strip()
    time_ids = await _time_matching_ids(db, user.id, search) if search else []
    # Признак «фильтр применён» различает ДВА пустых состояния: «расписаний нет
    # вовсе» и «фильтр ничего не нашёл» (UI-SPEC E13 `empty`). Второго запроса
    # для этого не нужно: набор фильтров сам отвечает на вопрос.
    filters_active = bool(channel or state or search)

    result = await db.execute(
        _apply_filters(_summary_query(user.id), channel, state, search, time_ids)
        .order_by(Schedule.id)
        .limit(PAGE_SIZE + 1)
    )
    rows = list(result)
    has_next = len(rows) > PAGE_SIZE
    page = rows[:PAGE_SIZE]
    group_names = await _group_names_for(db, user.id, [r.Schedule for r in page])
    schedules = _build_schedule_items(page, user, tz, group_names)
    total = (
        await db.execute(
            _apply_filters(
                _summary_count_query(user.id), channel, state, search, time_ids
            )
        )
    ).scalar_one()
    return templates.TemplateResponse(
        "schedules/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "schedules": schedules,
            "has_next": has_next,
            "next_offset": PAGE_SIZE,
            "active_page": "schedules",
            "total": total,
            "filters_active": filters_active,
            "filter_channel": channel,
            "filter_state": state,
            "filter_search": search,
            "filter_params": _filter_params(channel, state, search),
        },
    )


# D-14, D-16: ОТДЕЛЬНЫХ СТРАНИЦ создания и редактирования расписания больше нет.
# `GET /schedules/new` и `GET /schedules/{id}/edit` вместе с шаблоном
# `schedules/form.html` сняты планом 02-06: расписание настраивается ровно одним
# способом — в редакторе объявления (`/ads/{id}/edit`), где карточка
# `ads/includes/sched_card.html` несёт собственные формы.
#
# ОБРАБОТЧИКИ ФОРМ ОСТАЛИСЬ. `POST /schedules/new` и `POST /schedules/{id}/edit`
# ниже обслуживают именно карточку редактора — снос POST-маршрутов оборвал бы
# новый путь ровно в тот момент, когда старый уже удалён (SC-3).


async def _groups_of_account(
    db: AsyncSession, user_id: int, account_id: int | None
) -> list[int]:
    """Идентификаторы групп, принадлежащих пользователю И этому аккаунту."""
    if account_id is None:
        return []
    return list(
        (
            await db.execute(
                select(Group.id).where(
                    Group.account_id == account_id,
                    Group.user_id == user_id,
                )
            )
        )
        .scalars()
        .all()
    )


@router.post("/schedules/new")
async def schedules_create(
    request: Request,
    ad_id: int = Form(...),
    # Аккаунт НЕОБЯЗАТЕЛЕН. При нескольких подключённых аккаунтах ни один не
    # выбран заранее (UI-SPEC E4 zero-one-many), поэтому «+ РАСПИСАНИЕ» в
    # редакторе создаёт расписание БЕЗ аккаунта; отказ формы на этом месте
    # лишил бы пользователя единственного способа добавить карточку. Схема это
    # уже допускает: account_id nullable с ON DELETE SET NULL (issue #35), и
    # расписание без аккаунта по D-08 сохраняется выключенным.
    account_id: int | None = Form(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Владение объявлением и аккаунтом проверяется запросом, а не последующим
    # `if`, — по образцу проверки групп ниже. `Schedule` не имеет собственного
    # `user_id`, поэтому пришедшие формой `ad_id` и `account_id` задают не только
    # содержание рассылки, но и её владельца: без запроса пользователь ставит
    # рассылку на чужое объявление и отправляет её через чужую сессию (CR-01).
    #
    # Признак происхождения на эту проверку не влияет НИКАК: он подконтролен
    # отправителю ровно так же, как ad_id и account_id (T-02-26).
    if not await _owns_ad_and_account(db, user.id, ad_id, account_id):
        return RedirectResponse(url="/schedules", status_code=302)

    form_data = await request.form()
    # Фильтрация ДО приведения типов и ДО вычисления следующего запуска:
    # клиентским данным в этой фазе не верят (D-13).
    group_ids = _clean_ints(form_data.getlist("group_ids"))
    days_of_week = _clean_ints(form_data.getlist("days_of_week"), low=0, high=6)
    times_of_day = _clean_times(form_data.getlist("times_of_day"))

    available = await _groups_of_account(db, user.id, account_id)
    group_ids, days_of_week, times_of_day = _apply_named_actions(
        form_data, group_ids, days_of_week, times_of_day, available
    )
    # Группы обязаны принадлежать выбранному аккаунту: расписание не может нести
    # группы другого аккаунта. Несоответствующие отбрасываются, и если по итогам
    # список пуст — расписание сохраняется выключенным (D-08), а не молча
    # активным с нулём групп (Pitfall 8).
    group_ids = [gid for gid in group_ids if gid in available]

    # Умолчание — ТАЙМЗОНА ПРОФИЛЯ, а не литерал UTC. Снятая форма расписания
    # подставляла её в селект сама (`default_timezone`), а карточка редактора
    # таймзону не спрашивает вовсе: по UI-SPEC это подпись «Время по {tz из
    # профиля}» только для чтения, и поля `timezone` в форме добавления нет.
    # С литералом UTC расписание после переезда молча создавалось бы в чужом
    # часовом поясе, а подпись обещала бы пользовательский — расхождение,
    # которое видно только по неотправленной вовремя рассылке.
    profile_tz = user.timezone if user.timezone in VALID_TIMEZONES else "UTC"
    tz = form_data.get("timezone", profile_tz)
    if tz not in VALID_TIMEZONES:
        tz = profile_tz

    complete = _is_complete(account_id, group_ids, days_of_week, times_of_day)
    next_run = (
        compute_next_run_at(
            days_of_week=days_of_week, times_of_day=times_of_day, tz_name=tz
        )
        if complete
        else None
    )

    schedule = Schedule(
        ad_id=ad_id,
        account_id=account_id,
        group_ids=group_ids,
        days_of_week=days_of_week,
        times_of_day=times_of_day,
        timezone=tz,
        is_active=complete,
        next_run_at=next_run,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return _editor_redirect(form_data, ad_id, schedule.id)


@router.post("/schedules/{schedule_id}/edit")
async def schedules_update(
    request: Request,
    schedule_id: int,
    ad_id: int = Form(...),
    # Необязательность — по той же причине, что и на создании: снятый выбор
    # аккаунта это законное неполное состояние, а не отказ формы.
    account_id: int | None = Form(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Schedule.id == schedule_id, Ad.user_id == user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        return RedirectResponse(url="/schedules", status_code=302)

    # Владение самим расписанием проверено выше, но `ad_id` и `account_id`
    # приходят формой заново: без этой проверки своё расписание переставляется на
    # чужое объявление и чужой аккаунт (CR-01). Проверка стоит до первой записи
    # в модель, иначе отказ оставил бы запись частично изменённой.
    if not await _owns_ad_and_account(db, user.id, ad_id, account_id):
        return RedirectResponse(url="/schedules", status_code=302)

    form_data = await request.form()
    group_ids = _clean_ints(form_data.getlist("group_ids"))
    days_of_week = _clean_ints(form_data.getlist("days_of_week"), low=0, high=6)
    times_of_day = _clean_times(form_data.getlist("times_of_day"))

    available = await _groups_of_account(db, user.id, account_id)
    group_ids, days_of_week, times_of_day = _apply_named_actions(
        form_data, group_ids, days_of_week, times_of_day, available
    )
    # Смена аккаунта очищает ранее выбранные группы: расписание не может нести
    # группы другого аккаунта.
    group_ids = [gid for gid in group_ids if gid in available]

    tz = form_data.get("timezone", schedule.timezone)
    if tz not in VALID_TIMEZONES:
        tz = schedule.timezone

    schedule.ad_id = ad_id
    schedule.account_id = account_id
    schedule.group_ids = group_ids
    schedule.days_of_week = days_of_week
    schedule.times_of_day = times_of_day
    schedule.timezone = tz
    # Неполное расписание выключается ВСЕГДА (D-08). Полное — сохраняет своё
    # состояние: правка не имеет права снимать паузу, поставленную вручную,
    # иначе тумблер переставал бы что-либо значить.
    if not _is_complete(account_id, group_ids, days_of_week, times_of_day):
        schedule.is_active = False
        schedule.next_run_at = None
    else:
        schedule.next_run_at = (
            compute_next_run_at(
                days_of_week=days_of_week, times_of_day=times_of_day, tz_name=tz
            )
            if schedule.is_active
            else None
        )
    await db.commit()
    return _editor_redirect(form_data, ad_id, schedule_id)


@router.post("/schedules/{schedule_id}/toggle")
async def schedules_toggle(
    request: Request,
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Schedule.id == schedule_id, Ad.user_id == user.id)
    )
    schedule = result.scalar_one_or_none()
    # issue #35 и D-08: НЕПОЛНОЕ расписание нельзя возобновить, пока пользователь
    # не дозаполнит его в редакторе объявления. Отвязанное после удаления
    # аккаунта — частный случай той же неполноты. Пауза активного не
    # блокируется: право поставить на паузу не зависит от заполненности.
    #
    # Тумблер неполного расписания размечен недоступным, но разметка — не точка
    # принуждения: прямой POST на этот маршрут обязан получить тот же отказ.
    resume_blocked = schedule is not None and not schedule.is_active and not _is_complete(
        schedule.account_id,
        schedule.group_ids or [],
        schedule.days_of_week or [],
        schedule.times_of_day or [],
    )
    if schedule and not resume_blocked:
        schedule.is_active = not schedule.is_active
        if schedule.is_active:
            schedule.next_run_at = compute_next_run_at(
                days_of_week=schedule.days_of_week,
                times_of_day=schedule.times_of_day,
                tz_name=schedule.timezone,
            )
        else:
            schedule.next_run_at = None
        await db.commit()
    form_data = await request.form()
    return _editor_redirect(
        form_data, schedule.ad_id if schedule else None, schedule_id
    )


@router.post("/schedules/{schedule_id}/delete")
async def schedules_delete(
    request: Request,
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Schedule.id == schedule_id, Ad.user_id == user.id)
    )
    schedule = result.scalar_one_or_none()
    # Идентификатор объявления снимается ДО удаления: после него читать его уже
    # не с чего, а адрес возврата строится именно из него.
    ad_id = schedule.ad_id if schedule else None
    if schedule:
        await db.delete(schedule)
        await db.commit()
    form_data = await request.form()
    # Параметра выбранного расписания в адресе нет: разворачивать больше нечего.
    return _editor_redirect(form_data, ad_id)

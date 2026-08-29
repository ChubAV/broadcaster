"""Экран групп аккаунта мессенджера — `/accounts/{id}/groups` (D-02, GRP-04).

Раздел живёт ВНУТРИ «Аккаунтов»: `active_page` у страницы — `accounts`, и вход
на неё — строка аккаунта на `/accounts`. Глобальный раздел `/groups` снесён
планом 03-08 (D-01): от него осталась заглушка-перенаправление в
`app/pages/groups.py`, и этот модуль — единственный экран групп в продукте.

ВЛАДЕНИЕ ПРОВЕРЯЕТСЯ НА КАЖДОМ ВХОДЕ. `account_id` приходит из URL, то есть от
недоверенного клиента, поэтому проверка не делается один раз «на странице» и не
наследуется маршрутом изменения состояния: у toggle она своя (правило Фазы 2,
T-03-01/T-03-02). Парная спецификация этого модуля —
tests/test_pages/test_account_groups.py.
"""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.accounts.group_resync import parse_sync_result
from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User
from app.pages.common import check_is_admin, get_user_from_cookie, templates
from app.pages.htmx import respond
from app.repositories.schedule import ScheduleRepository

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30


def _clean_search(search: str | None) -> str | None:
    """Return the trimmed search term, or None when it carries nothing."""
    value = (search or "").strip()
    return value or None


def _build_groups_query(user_id: int, account_id: int, search: str | None):
    """Выборка групп экрана: владелец, аккаунт, необязательный поиск по имени.

    Фильтров по мессенджеру и по активности у экрана нет (D-03): аккаунт задан
    маршрутом, а тумблер — состояние строки, а не измерение списка.

    Сортировка ЯВНАЯ: без неё порядок строк — свойство плана запроса, а не
    контракта, и постраничная загрузка смещением начала бы дублировать одни
    строки и терять другие.
    """
    q = select(Group).where(Group.user_id == user_id, Group.account_id == account_id)
    if search:
        # Шаблон уходит BIND-ПАРАМЕТРОМ сравнения, а не конкатенацией SQL:
        # строка приходит из адреса запроса, то есть от недоверенного клиента
        # (T-03-21).
        q = q.where(Group.name.ilike(f"%{search}%"))
    return q.order_by(Group.id)


def _filter_params(search: str | None) -> dict:
    """Параметры, которые обязаны доехать до следующей порции прокрутки."""
    return {"search": search} if search else {}


async def _load_owned_account(
    db: AsyncSession, user: User, account_id: int
) -> MessengerAccount | None:
    """Аккаунт пользователя или None. Вызывается на КАЖДОМ входе экрана."""
    result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.id == account_id,
            MessengerAccount.user_id == user.id,
        )
    )
    return result.scalar_one_or_none()


async def _schedule_counts(
    db: AsyncSession, user_id: int, group_ids: list[int]
) -> dict[int, int]:
    """Сколько расписаний ВЛАДЕЛЬЦА содержит каждую из отрисованных групп (D-08).

    Состав групп хранится JSON-списком в `Schedule.group_ids`, поэтому агрегата
    по нему в SQL не существует — списки обходятся в Python, как в старом
    разделе. Отличие от аналога одно и оно обязательное: выборка расписаний
    ОГРАНИЧЕНА владельцем через связь с объявлением. Аналог этого ограничения не
    имел, и чужое расписание, случайно содержащее наш идентификатор, завышало
    бы подпись (правило Фазы 2: владение — на каждом чтении).

    Обход идёт по 30 отрисованным строкам страницы, а не по всей таблице групп
    (T-03-24).
    """
    if not group_ids:
        return {}

    rows = await db.execute(
        select(Schedule.group_ids)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Ad.user_id == user_id)
    )
    counts: dict[int, int] = {group_id: 0 for group_id in group_ids}
    for row in rows:
        for group_id in row.group_ids or []:
            if group_id in counts:
                counts[group_id] += 1
    return counts


async def _group_counts(
    db: AsyncSession, user_id: int, account_id: int
) -> tuple[int, int]:
    """Числа линейки счётчика: `(active_groups, total_groups)`.

    ДВА ВЫДЕЛЕННЫХ ЗАПРОСА ПОДСЧЁТА (D-04). Считать по загруженной странице
    нельзя: при 35 группах страница знает про 30 и линейка сказала бы «из 30» —
    соврала бы ровно там, где список перестал помещаться на экран, то есть там,
    где цена вранья наибольшая. Поиск в подсчёт НЕ входит: линейка описывает
    аккаунт целиком, а не текущую выдачу.

    ⚠️ ПОМОЩНИК ЖИВЁТ В ЭТОМ ЖЕ МОДУЛЕ, И ЭТО НЕ ВОПРОС ВКУСА. Признак пути
    деградации гейта (tests/test_templates/test_htmx_markup_gates.py) считает
    достижимость по цепочке функций ВНУТРИ модуля; помощник, вынесенный наружу,
    унёс бы с собой имя шаблона ответа, и классификация маршрута поехала бы.

    Зовут его и страница, и оба обработчика экрана: вторая копия этих двух
    запросов разошлась бы с первой при первой же правке, и линейка после
    действия отличалась бы от линейки после перезагрузки — молча.
    """
    total_groups = int(
        await db.scalar(
            select(func.count())
            .select_from(Group)
            .where(Group.user_id == user_id, Group.account_id == account_id)
        )
        or 0
    )
    active_groups = int(
        await db.scalar(
            select(func.count())
            .select_from(Group)
            .where(
                Group.user_id == user_id,
                Group.account_id == account_id,
                Group.is_active.is_(True),
            )
        )
        or 0
    )
    return active_groups, total_groups


@router.get("/accounts/{account_id}/groups", response_class=HTMLResponse)
async def account_groups_page(
    request: Request,
    account_id: int,
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    account = await _load_owned_account(db, user, account_id)
    if not account:
        # Тот же ответ, что и у несуществующего аккаунта: различимый отказ
        # сообщал бы, какие идентификаторы заняты чужими аккаунтами.
        return RedirectResponse(url="/accounts", status_code=302)

    term = _clean_search(search)

    # Приём limit+1: наличие следующей порции определяется одной лишней
    # строкой, а не вторым COUNT.
    result = await db.execute(
        _build_groups_query(user.id, account_id, term).limit(PAGE_SIZE + 1)
    )
    rows = list(result.scalars().all())
    has_next = len(rows) > PAGE_SIZE
    groups = rows[:PAGE_SIZE]

    # Числа линейки приходят ДВУМЯ ВЫДЕЛЕННЫМИ ЗАПРОСАМИ ПОДСЧЁТА (D-04) —
    # обоснование целиком лежит в докстринге помощника, который зовут и страница,
    # и оба обработчика экрана.
    active_groups, total_groups = await _group_counts(db, user.id, account_id)

    return templates.TemplateResponse(
        "account_groups/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "account": account,
            # account_id отдельным ключом: разметка сентинела обязана быть
            # ПОСИМВОЛЬНО одинаковой здесь и в порции прокрутки, а у порции
            # объекта аккаунта нет.
            "account_id": account_id,
            "groups": groups,
            "schedule_counts": await _schedule_counts(
                db, user.id, [group.id for group in groups]
            ),
            "total_groups": total_groups,
            "active_groups": active_groups,
            # СВОДКА ПОСЛЕДНЕГО СИНКА читается из АККАУНТА, а не из памяти
            # запроса (D-09): плашка обязана быть видна и при перезаходе на
            # экран, а не только сразу после нажатия кнопки. Разбор идёт
            # защищённым парсером — испорченная строка даёт None, то есть
            # отсутствие плашки, а не стек-трейс на экране (T-03-08, T-03-27).
            "sync_result": parse_sync_result(account.last_sync_result),
            "has_next": has_next,
            "next_offset": PAGE_SIZE,
            "filter_params": _filter_params(term),
            "filter_search": term or "",
            # D-02: экран живёт в разделе «Аккаунты», подсветка меню — оттуда.
            "active_page": "accounts",
        },
    )


@router.get("/accounts/{account_id}/groups/partial", response_class=HTMLResponse)
async def account_groups_partial(
    request: Request,
    account_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=100),
    search: str | None = Query(None),
    # D-15: параметр компоновки принимается и игнорируется — см. app/pages/ads.py
    layout: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Следующая порция строк для сентинела бесконечной прокрутки.

    Аутентификация и владение аккаунтом проверяются ЗДЕСЬ ЗАНОВО, а не
    наследуются от страницы: адрес паршала вызывается напрямую так же легко,
    как адрес страницы (T-03-19).

    Линейку счётчика паршал не вычисляет и в контекст не кладёт (D-04): у неё
    не бывает промежуточного состояния, и подмена порции её не касается.
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    account = await _load_owned_account(db, user, account_id)
    if not account:
        return RedirectResponse(url="/accounts", status_code=302)

    term = _clean_search(search)
    result = await db.execute(
        _build_groups_query(user.id, account_id, term).offset(offset).limit(limit + 1)
    )
    rows = list(result.scalars().all())
    has_next = len(rows) > limit
    groups = rows[:limit]

    return templates.TemplateResponse(
        "account_groups/partial_cards.html",
        {
            "request": request,
            "user": user,
            "account_id": account_id,
            "groups": groups,
            "schedule_counts": await _schedule_counts(
                db, user.id, [group.id for group in groups]
            ),
            "has_next": has_next,
            "next_offset": offset + limit,
            "filter_params": _filter_params(term),
        },
    )


@router.get("/accounts/{account_id}/groups/sync-status", response_class=HTMLResponse)
async def account_groups_sync_status(
    request: Request,
    account_id: int,
    # D-15: параметр компоновки принимается и игнорируется — см. app/pages/ads.py
    layout: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Блок статуса синхронизации — цель самоостанавливающегося опроса.

    Статус читается из базы: фоновые задачи WA и MAX пишут его сами, а экран
    его ДОБИРАЕТ. Опрос прекращается тем, что очередной ответ приходит без
    атрибутов запроса и триггера — условие живёт в шаблоне, а не здесь, потому
    что первичная отрисовка страницы обязана подчиняться ровно тому же условию
    (T-03-26).

    Аутентификация и владение аккаунтом проверяются ЗДЕСЬ ЗАНОВО: этот адрес
    вызывается автоматически каждые пять секунд, то есть перебрать чужие
    идентификаторы через него дешевле, чем через страницу (T-03-25).

    ОТКАЗ — ПУСТОЙ ОТВЕТ, а не редирект. Пустой ответ и не отдаёт разметки, и
    останавливает опрос: редирект на страницу входа вернул бы в подменяемый
    блок целую страницу логина, а опрос продолжился бы как ни в чём не бывало.

    Рендер идёт получением шаблона из окружения и его рендером напрямую — по
    образцу входа статуса экрана «Аккаунты»: у ответа нет ни шелла, ни
    контекста запроса, ему нужны ровно два значения.
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return HTMLResponse("")

    account = await _load_owned_account(db, user, account_id)
    if not account:
        return HTMLResponse("")

    # Вне трёх известных статусов разметки нет: выдуманная подпись сообщала бы
    # о состоянии, которого словарь экрана «Аккаунты» не знает.
    if account.status not in ("active", "sync_failed", "syncing"):
        return HTMLResponse("")

    html = templates.env.get_template(
        "account_groups/partials/sync_result.html"
    ).render(account_id=account_id, status=account.status)
    return HTMLResponse(html)


@router.post("/accounts/{account_id}/groups/{group_id}/toggle")
async def account_groups_toggle(
    request: Request,
    account_id: int,
    group_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Переключение группы — первый обработчик вехи, идущий через слой ответа.

    ⚠️ СОБСТВЕННОГО ОТВЕТА-ПЕРЕНАПРАВЛЕНИЯ ЗДЕСЬ НЕТ НИ В ОДНОЙ ВЕТКЕ, ВКЛЮЧАЯ
    «НЕТ СЕССИИ», И ЭТО ТРЕБОВАНИЕ, А НЕ АККУРАТНОСТЬ. Гейт G-2
    (tests/test_pages/test_htmx_gates.py::test_no_converted_handler_builds_its_own_redirect)
    считает нарушением ЛЮБУЮ собственную сборку перенаправления — и класс
    ответа, и статус 302 где угодно в теле — у обработчика, который вдобавок
    зовёт `respond()`: два решения об одной форме ответа означают, что какое из
    них исполнится, решает ветка, — то есть путь деградации снова перестаёт быть
    обязательным. Форма 302 при этом не теряется: её строит сам слой ответа, тем
    же кодом и на том же адресе.

    ⚠️ Имена класса ответа и статуса набраны здесь СЛОВАМИ, а не литералами:
    отсутствие собственного перенаправления проверяется в том числе грепом по
    телу этого обработчика, и докстринг, набравший их дословно, удовлетворил бы
    греп сам.

    Вердикт доступа вычисляется ДО развилки транспорта: заголовок запроса
    меняет только ФОРМУ ответа, но не то, что человеку позволено (T-9-05).
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return await respond(request, redirect="/login")

    # ТРОЙНОЙ WHERE. Проверка владельца одна не закрывает вход: свою группу
    # можно адресовать через свой ЖЕ, но другой аккаунт, и связка «группа
    # принадлежит именно этому аккаунту» перестала бы удерживаться (T-03-02).
    result = await db.execute(
        select(Group).where(
            Group.id == group_id,
            Group.user_id == user.id,
            Group.account_id == account_id,
        )
    )
    group = result.scalar_one_or_none()
    if group is None:
        # ЧУЖАЯ И НЕСУЩЕСТВУЮЩАЯ ГРУППА ИДУТ ОДНОЙ ВЕТКОЙ И ОСТАЮТСЯ
        # НЕОТЛИЧИМЫМИ (D-13, T-9-02). Различимый отказ сообщал бы, какие
        # идентификаторы заняты чужими группами: карту чужих данных можно было
        # бы составить перебором по адресу, не получив ни одной строки.
        # Фрагмента нет, поэтому слой отвечает 302 без htmx и 204 с заголовком
        # перехода — с ним.
        return await respond(request, redirect=f"/accounts/{account_id}/groups")

    # ИНВЕРСИЯ, а не установка: действие обратимо одним нажатием и потому
    # обходится без панели подтверждения (D-08). Обработчик, жёстко
    # ставящий False, оставил бы пользователя без способа включить группу.
    #
    # ⚠️ ОНА ЖЕ ДЕЛАЕТ ПОВТОРНОЕ НАЖАТИЕ БЕЗВРЕДНЫМ (QUAL-01). Два запроса дают
    # два инвертирования и НИ ОДНОЙ новой строки; единица записи — один `commit`
    # одной строки под тройным `WHERE`. Клиентская блокировка повторной отправки
    # (`hx-disabled-elt`) серверной защитой НЕ является и таковой не
    # объявляется (PAY-02) — она убирает второе нажатие у человека, а не второй
    # запрос у злоумышленника.
    group.is_active = not group.is_active
    await db.commit()

    # D-05: состав расписаний маршрут не читает и не пишет. Выключенная группа
    # пропускается при диспетчеризации, а не вычищается из Schedule.group_ids —
    # иначе включение группы обратно не вернуло бы её в рассылку.

    async def _fragment() -> HTMLResponse:
        """Строка группы плюс внеполосный узел линейки счётчика.

        ⚠️ ФУНКЦИЯ НУЛЬАРНАЯ И АСИНХРОННАЯ: слой ответа делает `await
        fragment()`, и `lambda`, возвращающая готовый ответ, ему не подошла бы.
        Отложенность здесь несущая — на пути без htmx разметка не собирается
        вовсе, то есть два лишних запроса подсчёта не выполняются.

        Число расписаний берётся ТЕМ ЖЕ помощником, что и на странице: второй
        экземпляр ограничения владельца через связь с объявлением разъехался бы
        с первым, и чужое расписание завышало бы подпись строки.
        """
        schedules_count = (await _schedule_counts(db, user.id, [group.id])).get(
            group.id, 0
        )
        active_groups, total_groups = await _group_counts(db, user.id, account_id)
        html = templates.env.get_template(
            "account_groups/partials/toggle_response.html"
        ).render(
            group=group,
            account_id=account_id,
            schedules_count=schedules_count,
            user=user,
            active_groups=active_groups,
            total_groups=total_groups,
        )
        return HTMLResponse(html)

    # `notice` НЕ передаётся (D-10): исход виден в самой строке и в счётчике,
    # а плашка на каждый успех превратила бы обратную связь в шум.
    return await respond(
        request, redirect=f"/accounts/{account_id}/groups", fragment=_fragment
    )


@router.post("/accounts/{account_id}/groups/{group_id}/delete")
async def account_groups_delete(
    request: Request,
    account_id: int,
    group_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Удаление группы из списка аккаунта (GRP-06).

    В отличие от тумблера удаление НЕОБРАТИМО, поэтому состав расписаний здесь
    трогать обязательно: оставленный в `Schedule.group_ids` идентификатор
    удалённой строки не роняет отправку, он делает её тихо неполной.
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # ТОТ ЖЕ ТРОЙНОЙ WHERE, что у тумблера: свою группу можно адресовать через
    # свой ЖЕ, но другой аккаунт, и одной проверки владельца не хватает
    # (T-03-20).
    result = await db.execute(
        select(Group).where(
            Group.id == group_id,
            Group.user_id == user.id,
            Group.account_id == account_id,
        )
    )
    group = result.scalar_one_or_none()
    if group:
        # Чистка расписаний — ГОТОВЫМ методом репозитория: он учитывает
        # JSON-природу колонки и ограничивает выборку владельцем через связь с
        # объявлением. Собственный обход расписаний пришлось бы снабдить тем же
        # ограничением заново, и второй экземпляр этого правила разъехался бы с
        # первым при первой же правке.
        await ScheduleRepository(db).remove_group_ids(user.id, {group.id})
        await db.delete(group)
        await db.commit()

    # Ответ ОДИНАКОВ и для найденной, и для ненайденной группы: это делает
    # повторный запрос безвредным (кнопка «назад», повторная отправка формы) и
    # не сообщает, какие идентификаторы заняты чужими группами.
    return RedirectResponse(url=f"/accounts/{account_id}/groups", status_code=302)

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

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Query, Request
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


def _screen_url(account_id: int, search: str | None) -> str:
    """Адрес экрана групп С СОХРАНЁННЫМ фильтром — приземление после действия.

    Собирается ТЕМ ЖЕ `_filter_params`, что и адрес сентинела: адрес после
    действия и адрес после перезагрузки обязаны приходить из одного источника,
    иначе они разъедутся молча — и человек, нажавший кнопку, увидит не тот
    экран, что человек, обновивший страницу.

    ⚠️ ПРИ ПУСТОЙ СТРОКЕ ПОИСКА АДРЕС ОСТАЁТСЯ ПОСИМВОЛЬНО ПРЕЖНИМ. Лишний
    вопросительный знак не меняет того, куда попадёт человек, но он меняет
    ЗНАЧЕНИЕ, которое уезжает в заголовок перехода, — а его сегодняшние тесты
    деградации сверяют дословно.

    Значение кодируется для адреса: строка поиска приходит из недоверенного
    документа, а `_local_path` слоя ответа не выпускает в заголовок ни символа
    вне ASCII (значения заголовков кодируются в latin-1) и ни одного
    управляющего символа.
    """
    params = _filter_params(search)
    if not params:
        return f"/accounts/{account_id}/groups"
    return f"/accounts/{account_id}/groups?{urlencode(params)}"


async def _current_listing_has_a_row(
    db: AsyncSession, user_id: int, account_id: int, search: str | None
) -> bool:
    """Осталась ли в ТЕКУЩЕЙ ВЫДАЧЕ хотя бы одна строка.

    ⚠️ ИМЯ ГОВОРИТ О ВЫДАЧЕ, А НЕ О ЧИСЛЕ ГРУПП АККАУНТА, И ЭТО НЕ ВКУС.
    Вопрос «сколько групп в аккаунте» и вопрос «осталось ли что-то в том, что
    человек СЕЙЧАС видит» — разные, и подмена первого вторым стоила фазе
    дефекта WR-06: под активным поиском список на экране пустел, а число групп
    аккаунта оставалось больше нуля.

    Запрос — тот же `_build_groups_query` с ограничением в одну строку: второй
    экземпляр условий выборки (владелец, аккаунт, поиск) разошёлся бы с первым
    при первой же правке, и ветка ответа перестала бы соответствовать экрану.

    Числами линейки счётчика этот вопрос НЕ отвечается и в них не подмешивается:
    линейка описывает аккаунт целиком, а не выдачу (записанное решение Фазы 3).
    """
    row = await db.scalar(_build_groups_query(user_id, account_id, search).limit(1))
    return row is not None


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
            # КЛЮЧ ПОСЛЕДНЕЙ ОТРИСОВАННОЙ СТРОКИ, А НЕ ЕЁ ПОРЯДКОВЫЙ НОМЕР
            # (план 09-13, решение владельца `keyset`). Курсор перестал быть
            # величиной, которую можно снять в один момент и применить в
            # другой: удаление любой уже отрисованной строки оставляет границу
            # сравнения корректной, поэтому чинить его ответу удаления не нужно.
            "next_after_id": groups[-1].id if groups else None,
            # РАЗМЕР СТРАНИЦЫ ДОЕЗЖАЕТ ДО РАЗМЕТКИ ИЗ КОНТЕКСТА, А НЕ
            # НАБИРАЕТСЯ В НЕЙ ЛИТЕРАЛОМ (WR-05): второй экземпляр величины
            # разъехался бы с `PAGE_SIZE` молча, а клиент не может поднять её
            # разметкой (T-09-13-03).
            "page_size": PAGE_SIZE,
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
    after_id: int | None = Query(None, ge=1),
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

    # КЛЮЧЕВОЙ КУРСОР ВМЕСТО СМЕЩЕНИЯ (план 09-13, решение владельца `keyset`).
    # Порция добирает строки СТРОГО БОЛЬШЕ ключа последней отрисованной, а не
    # пропускает объявленное клиентом число строк. Сортировка по `Group.id`
    # объявлена в `_build_groups_query` и является ПРЕДУСЛОВИЕМ этой формы:
    # сравнение по ключу без порядка по тому же ключу теряло бы строки.
    #
    # ⚠️ ПОДДЕЛАННЫЙ КЛЮЧ СУЖАЕТ ВЫБОРКУ, НО НЕ ОТМЕНЯЕТ ТРОЙНОГО `WHERE`
    # (T-09-13-01): владелец и аккаунт проверяются здесь заново, поэтому
    # клиент двигает СВОЙ СОБСТВЕННЫЙ документ и чужих строк не открывает.
    query = _build_groups_query(user.id, account_id, term)
    if after_id is not None:
        query = query.where(Group.id > after_id)
    result = await db.execute(query.limit(limit + 1))
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
            "next_after_id": groups[-1].id if groups else None,
            # То же значение, что кладёт страница: размер, объявленный ОДИН
            # раз, и клиенту через разметку не подвластный (WR-05, T-09-13-03).
            "page_size": PAGE_SIZE,
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
    search: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Удаление группы из списка аккаунта (GRP-06) — второй обработчик вехи.

    В отличие от тумблера удаление НЕОБРАТИМО, поэтому состав расписаний здесь
    трогать обязательно: оставленный в `Schedule.group_ids` идентификатор
    удалённой строки не роняет отправку, он делает её тихо неполной.

    ⚠️ СОБСТВЕННОГО ОТВЕТА-ПЕРЕНАПРАВЛЕНИЯ ЗДЕСЬ НЕТ НИ В ОДНОЙ ВЕТКЕ, ВКЛЮЧАЯ
    «НЕТ СЕССИИ», И ЭТО ТРЕБОВАНИЕ, А НЕ АККУРАТНОСТЬ. Гейт G-2 считает
    нарушением ЛЮБУЮ собственную сборку перенаправления — и класс ответа, и
    статус 302 где угодно в теле — у обработчика, который вдобавок зовёт
    `respond()`: два решения об одной форме ответа означают, что какое из них
    исполнится, решает ветка, — то есть путь деградации снова перестаёт быть
    обязательным. Форма 302 при этом не теряется: её строит сам слой ответа.
    Имена класса ответа и статуса набраны здесь СЛОВАМИ, а не литералами:
    отсутствие собственного перенаправления проверяется в том числе грепом по
    телу этого обработчика.

    ⚠️ ВЕТВЛЕНИЕ «СПИСОК ОПУСТЕЛ / НЕ ОПУСТЕЛ» СЧИТАЕТСЯ ПО ТЕКУЩЕЙ ВЫДАЧЕ, А
    НЕ ПО ЧИСЛУ ГРУПП АККАУНТА И НЕ ПО ФАКТУ НАХОЖДЕНИЯ СТРОКИ. Прежняя ветка
    по числам аккаунта оставляла человека ПЕРЕД ПУСТОЙ КАРТОЧКОЙ, ИЗ КОТОРОЙ
    НЕТ ВЫХОДА (WR-06): поиск сужал выдачу до одной строки, человек её удалял,
    `total_groups` оставался больше нуля — и ответ снимал строку на месте
    фрагментом. Все три различимых пустых состояния, включая ветвь «Группы не
    найдены» с кнопкой «Сбросить», живут на СТРАНИЦЕ и во фрагмент не приезжают
    (D-09), поэтому вернуться к неотфильтрованному списку можно было только
    правкой адреса. Вопрос теперь задаётся один и прямой: осталась ли в выдаче
    с этой строкой поиска хотя бы одна строка.

    ⚠️ НЕОТЛИЧИМОСТЬ ЭТА СМЕНА НЕ СЛОМАЛА, И ВОТ ПОЧЕМУ (D-04 в редакции
    D-04-A, T-9-10). У ЧУЖОЙ и у НЕСУЩЕСТВУЮЩЕЙ группы текущая выдача не
    меняется ни на строку: тройной `WHERE` не вернул ничего, удалять было
    нечего, и выборка после запроса даёт ровно то же, что и до него. Значит и
    ветка у них та же, какой она была бы у соседнего УСПЕШНОГО удаления в том
    же аккаунте, — различимого признака не появляется ни в статусе, ни в теле,
    ни в заголовках. Величина, по которой выбирается ветка, для обоих случаев
    одна, потому что она вычисляется из состояния списка, а не из исхода
    поиска строки.

    ⚠️ ЧИСЛА ЛИНЕЙКИ СЧЁТЧИКА ПРИ ЭТОМ СЧИТАЮТСЯ ПО-ПРЕЖНЕМУ ПО АККАУНТУ
    ЦЕЛИКОМ и строкой поиска не сужаются: линейка описывает аккаунт, а не
    выдачу (записанное решение Фазы 3). Смешать два вопроса в одном запросе
    нельзя — получилась бы линейка, врущая ровно там, где список перестал
    помещаться на экран.

    ⚠️ ЧТО ЭТОЙ ПРАВКОЙ НЕ ЗАКРЫВАЕТСЯ И НЕ ДОЛЖНО. Удаление последней строки
    ТЕКУЩЕЙ ПОРЦИИ при непустых следующих страницах остаётся фрагментной
    веткой: выдача не пуста, экран не опустел, и закрывать этот случай
    переходом было бы неверно — курсор прокрутки чинит четвёртый внеполосный
    узел (план 09-05), а не ветка ответа. Это ИЗЪЯТИЕ, а не незакрытая
    половина WR-06.

    ⚠️ СЕРВЕР БОЛЬШЕ НЕ СПРАШИВАЕТ ДОКУМЕНТ НИ О ЧЁМ (план 09-13, решение
    владельца `keyset`). Курсор прокрутки перестал быть ЧИСЛОМ и стал КЛЮЧОМ
    последней отрисованной строки, который живёт в адресе сентинела и никуда с
    клиента не приезжает. Поэтому этот обработчик курсор не чинит: удаление
    любой уже отрисованной строки оставляет границу сравнения корректной, и
    чинить нечего. Отказ закрыт тем, что стал НЕВЫРАЗИМЫМ, а не тем, что стал
    вычисляться аккуратнее.

    ⚠️ ДВА АБЗАЦА ПРЕЖНЕЙ ФОРМЫ НЕ ВЫЧЁРКИВАЮТСЯ, А НАЗЫВАЮТСЯ ОПИСЫВАЮЩИМИ
    СНЯТОЕ (образец — записи D-30 и D-32 .planning/STATE.md). До плана 09-13
    здесь стояло: «ЧИСЛО ОТРИСОВАННЫХ СТРОК ПРИХОДИТ ОТ КЛИЕНТА, И ЭТО НЕ ЛЕНЬ,
    А ЕДИНСТВЕННАЯ ВОЗМОЖНОСТЬ — сервер не знает, ДОКУДА дочитан список», и
    «ВЫЧИТАЕТСЯ ЧИСЛО СНЯТЫХ С ЭКРАНА СТРОК, А НЕ ЕДИНИЦА». Оба были верны ДЛЯ
    СВОЕЙ ФОРМЫ и оба сняты вместе с ней. Посылка первого — «вычислить нельзя в
    принципе» — оказалась верной лишь для СМЕЩЕНИЯ: ключ вычислять и не нужно,
    он уже стоит в адресе, который документ несёт. Второй абзац защищал
    неотличимость внутри арифметики, которой больше нет: число снятых с экрана
    строк не считается вовсе, поэтому класс «строка не найдена» неразличим
    изнутри БЕЗ отдельной оговорки — ответ у всех четырёх случаев (найденная,
    чужая, несуществующая, уже удалённая) собирается из `group_id` пути и
    совпадает побайтно.

    ⚠️ ЦЕНА ЭТОЙ ФОРМЫ, ОПЛАЧЕННАЯ ОДНАЖДЫ, НАЗЫВАЕТСЯ ЗДЕСЬ ЦЕЛИКОМ. Прежняя
    форма была введена планом 09-05, чтобы закрыть молчаливую ПОТЕРЮ группы, и
    свою задачу решала. Она же внесла зеркальный отказ: снятое в момент
    ОТПРАВКИ число применялось к узлу момента ПРИМЕНЕНИЯ, и под достижимым
    чередованием строки приезжали вторично с задвоенными `id` (CR-01,
    09-VERIFICATION.md gap 1, регрессионный тест
    `test_an_interleaved_portion_and_delete_never_double_a_row`).
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return await respond(request, redirect="/login")

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
    active_groups, total_groups = await _group_counts(db, user.id, account_id)

    # СТРОКА ПОИСКА ПРИХОДИТ ТЕЛОМ ФОРМЫ ПОДТВЕРЖДЕНИЯ и проходит тот же
    # `_clean_search`, что и на странице: ветка ответа обязана считаться по той
    # же выдаче, которую человек видит перед собой.
    term = _clean_search(search)

    # АДРЕС ПРИЗЕМЛЕНИЯ СОБИРАЕТСЯ ОДИН РАЗ И ОДИН НА ОБЕ ВЕТКИ. Он же уезжает
    # человеку без JavaScript перенаправлением, он же — заголовком перехода: два
    # независимо собранных адреса разошлись бы молча, и путь деградации терял бы
    # фильтр там, где путь htmx его сохраняет.
    screen_url = _screen_url(account_id, term)

    if not await _current_listing_has_a_row(db, user.id, account_id, term):
        # ТЕКУЩАЯ ВЫДАЧА ОПУСТЕЛА — ЗАКРЫВАЕТСЯ ПЕРЕХОДОМ, А НЕ ВТОРОЙ
        # ОТРИСОВКОЙ ПУСТОГО СОСТОЯНИЯ (D-09). Фрагмента нет, поэтому слой
        # отвечает 302 без htmx и 204 с заголовком перехода — с ним. Три
        # различимых пустых состояния экрана живут в
        # `account_groups/list.html` в ОДНОМ экземпляре: второй их экземпляр во
        # фрагменте разошёлся бы с первым молча, и человек видел бы разный
        # экран в зависимости от того, как он на него попал. Адрес несёт
        # фильтр — иначе человек приземлялся бы на НЕотфильтрованный список и
        # не узнал бы, что его поиск больше ничему не отвечает.
        return await respond(request, redirect=screen_url)

    async def _fragment() -> HTMLResponse:
        """Три внеполосных узла: снятие строки, снятие панели, счётчик.

        ⚠️ ФУНКЦИЯ НУЛЬАРНАЯ И АСИНХРОННАЯ: слой ответа делает `await
        fragment()`. Отложенность здесь несущая — на пути без htmx разметка не
        собирается вовсе.

        ⚠️ ТЕЛО СОБИРАЕТСЯ ИЗ `group_id` ПУТИ, А НЕ ИЗ НАЙДЕННОЙ СТРОКИ. Строки
        к этому месту уже нет ни в одном случае: либо она удалена, либо её и не
        было. По несуществующему идентификатору внеполосное снятие не находит
        узла и не делает ничего — молча и безвредно.

        ⚠️ ЧЕТВЁРТОГО УЗЛА ЗДЕСЬ БОЛЬШЕ НЕТ (план 09-13, `keyset`): курсор не
        чинится, потому что не ломается. Строка поиска при этом по-прежнему
        проходит тем же `_clean_search`, что и на странице, — она выбирает
        ВЕТКУ ответа и адрес приземления, и потерянная подмешала бы к выдаче
        поиска остальной список аккаунта.
        """
        html = templates.env.get_template(
            "account_groups/partials/delete_response.html"
        ).render(
            group_id=group_id,
            active_groups=active_groups,
            total_groups=total_groups,
        )
        return HTMLResponse(html)

    # `notice` НЕ передаётся (D-10): исход виден по исчезнувшей строке и по
    # счётчику, а плашка на каждый успех превратила бы обратную связь в шум.
    return await respond(request, redirect=screen_url, fragment=_fragment)

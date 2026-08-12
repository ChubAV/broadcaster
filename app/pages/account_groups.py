"""Экран групп аккаунта мессенджера — `/accounts/{id}/groups` (D-02, GRP-04).

Раздел живёт ВНУТРИ «Аккаунтов»: `active_page` у страницы — `accounts`, и вход
на неё — строка аккаунта на `/accounts`. Глобальный раздел `/groups` остаётся
нетронутым до плана 03-03, который сносит его целиком (D-01).

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

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User
from app.pages.common import check_is_admin, get_user_from_cookie, templates

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

    # ДВА ВЫДЕЛЕННЫХ ЗАПРОСА ПОДСЧЁТА (D-04). Считать по загруженной странице
    # нельзя: при 35 группах страница знает про 30 и линейка сказала бы «из 30»
    # — соврала бы ровно там, где список перестал помещаться на экран, то есть
    # там, где цена вранья наибольшая. Поиск в подсчёт НЕ входит: линейка
    # описывает аккаунт целиком, а не текущую выдачу.
    total_groups = int(
        await db.scalar(
            select(func.count())
            .select_from(Group)
            .where(Group.user_id == user.id, Group.account_id == account_id)
        )
        or 0
    )
    active_groups = int(
        await db.scalar(
            select(func.count())
            .select_from(Group)
            .where(
                Group.user_id == user.id,
                Group.account_id == account_id,
                Group.is_active.is_(True),
            )
        )
        or 0
    )

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


@router.post("/accounts/{account_id}/groups/{group_id}/toggle")
async def account_groups_toggle(
    request: Request,
    account_id: int,
    group_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

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
    if group:
        # ИНВЕРСИЯ, а не установка: действие обратимо одним нажатием и потому
        # обходится без панели подтверждения (D-08). Обработчик, жёстко
        # ставящий False, оставил бы пользователя без способа включить группу.
        group.is_active = not group.is_active
        await db.commit()

    # D-05: состав расписаний маршрут не читает и не пишет. Выключенная группа
    # пропускается при диспетчеризации, а не вычищается из Schedule.group_ids —
    # иначе включение группы обратно не вернуло бы её в рассылку.
    return RedirectResponse(url=f"/accounts/{account_id}/groups", status_code=302)

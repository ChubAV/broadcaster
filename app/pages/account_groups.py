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

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.pages.common import check_is_admin, get_user_from_cookie, templates

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30


@router.get("/accounts/{account_id}/groups", response_class=HTMLResponse)
async def account_groups_page(
    request: Request,
    account_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    account_result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.id == account_id,
            MessengerAccount.user_id == user.id,
        )
    )
    account = account_result.scalar_one_or_none()
    if not account:
        # Тот же ответ, что и у несуществующего аккаунта: различимый отказ
        # сообщал бы, какие идентификаторы заняты чужими аккаунтами.
        return RedirectResponse(url="/accounts", status_code=302)

    # Сортировка ЯВНАЯ: без неё порядок строк — свойство плана запроса, а не
    # контракта, и постраничная загрузка смещением начала бы дублировать одни
    # строки и терять другие. Приём limit+1 — из groups_partial: наличие
    # следующей порции определяется одной лишней строкой, а не вторым COUNT.
    result = await db.execute(
        select(Group)
        .where(Group.user_id == user.id, Group.account_id == account_id)
        .order_by(Group.id)
        .limit(PAGE_SIZE + 1)
    )
    rows = list(result.scalars().all())
    has_next = len(rows) > PAGE_SIZE
    groups = rows[:PAGE_SIZE]

    return templates.TemplateResponse(
        "account_groups/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "account": account,
            "groups": groups,
            "has_next": has_next,
            "next_offset": PAGE_SIZE,
            # D-02: экран живёт в разделе «Аккаунты», подсветка меню — оттуда.
            "active_page": "accounts",
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

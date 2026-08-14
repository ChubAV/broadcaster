"""Маршрут паршала живой ленты дашборда (DASH-03).

ПОЧЕМУ У ЭТОГО ПАРШАЛА СВОЙ РОУТЕР, А НЕ ОБЩИЙ СТРАНИЧНЫЙ.

`app/pages/__init__.py` объявляет страничный роутер С ЗАВИСИМОСТЬЮ
`load_shell_context`, и она висит на КАЖДОМ его маршруте, включая паршалы.
Зависимость зовёт `get_shell_context`, а тот делает четыре обращения к базе:
счётчики навигации, подписка, баланс сообщений и журнал списаний
(`app/pages/common.py`). Для страницы это правильная цена — шелл рисуется на
каждой странице и обязан быть живым.

Ленте эта цена не нужна ни разу: её паршал шелл НЕ НАСЛЕДУЕТ и ни одного
значения из контекста шелла не читает. А главное — цена здесь не разовая.
Опрос ленты БЕССРОЧНЫЙ (D-07): он тикает, пока вкладка открыта, поэтому четыре
запроса умножаются на число открытых вкладок всех пользователей и делятся на
`FEED_POLL_SECONDS`. Это и есть смягчение T-04-18: сам опрос — осознанное
решение, а его стоимость снижена там, где она снижаема.

Включение мимо страничного роутера НИ ОДНОГО существующего маршрута не меняет:
роутер объявлен здесь, включается в `app/main.py` рядом с остальными, а
`app/pages/__init__.py` этот модуль не импортирует вовсе.

Гард входа поэтому написан ЗДЕСЬ и дословно повторяет остальные страничные
обработчики: `get_user_from_cookie` и редирект на страницу входа. Роутер без
зависимости шелла — это роутер без зависимости шелла, а не роутер без проверки
владельца (T-04-17). Границу владельца держит вторым слоем сам запрос ленты:
`recent_feed` принимает `user_id` обязательным именованным параметром, и ветки
«по всем пользователям» у него нет.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import recent_feed
from app.config import Settings
from app.dependencies import get_db, get_settings
from app.pages.common import get_user_from_cookie, templates

# Число строк ленты и интервал опроса. ОБА значения живут здесь, а не литералами
# в разметке: интервал читает страница дашборда (она вешает опрос), лимит читает
# этот маршрут (он отдаёт строки), и выписанные порознь они разъехались бы
# молча — лента показывала бы одно число строк, а обновлялась бы с другой
# частотой, чем предполагал автор шаблона.
#
# Значения — середины вилок, отнесённых планом к Claude's Discretion: интервал
# 15-30 секунд (D-07) и 6-10 строк (D-08).
FEED_LIMIT = 8
FEED_POLL_SECONDS = 20

router = APIRouter(tags=["pages"])


@router.get("/dashboard/feed", response_class=HTMLResponse)
async def dashboard_feed(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Очередная порция строк живой ленты.

    Отдаёт ТОЛЬКО строки: ни атрибутов опроса, ни контейнера — они живут на
    странице и в DOM остаются. Обоснование этой асимметрии с остальными
    опросами проекта выписано в самом паршале.
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "dashboard/partial_feed.html",
        {
            "request": request,
            "user": user,
            "feed": await recent_feed(db, user_id=user.id, limit=FEED_LIMIT),
        },
    )

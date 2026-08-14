from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import (
    activity_heatmap,
    recent_feed,
    send_metrics,
    upcoming_sends,
)
from app.config import Settings
from app.dependencies import get_db, get_settings
from app.pages.common import (
    _get_timezone_for_user,
    check_is_admin,
    get_user_from_cookie,
    templates,
)
from app.pages.dashboard_feed import FEED_LIMIT, FEED_POLL_SECONDS

router = APIRouter(tags=["pages"])


def dashboard_next_step(nav_counts: dict | None) -> tuple[str, str]:
    """Подпись и адрес СЛЕДУЮЩЕГО шага пользователя по счётчикам шелла (D-40).

    Пустой дашборд обязан вести по тому, чего НЕ ХВАТАЕТ, а не показывать один
    и тот же призыв всем: «создайте объявление» пользователю без подключённого
    канала бесполезно — объявление он создаст, а отправить его будет некуда.
    Порядок ветвей и есть порядок шагов продукта: канал → объявление →
    расписание.

    Счётчики УЖЕ посчитаны шеллом на каждом страничном маршруте
    (`load_shell_context` → `get_shell_context`), поэтому второго запроса за
    ними здесь нет. Пустой словарь — валидный вход: шелл отдаёт его, когда
    пользователя нет, и обращение к отсутствующему ключу дало бы пятисотку
    вместо призыва.

    АДРЕСА ПОВТОРЯЮТ пустые состояния самих разделов, а не изобретают свои:
    «нет объявлений» ведёт туда же, куда ведёт `ads/list.html`, «нет
    расписаний» — туда же, куда `schedules/list.html` (в редактор объявления, а
    не на сводный список: создать расписание там больше нельзя, D-14). Два
    разных адреса на один вопрос — ровно та болезнь, которую лечит эта фаза.

    Единственное расхождение — «нет аккаунтов»: раздел аккаунтов ведёт сразу в
    подключение Telegram, а дашборд ведёт НА раздел, где предложены все каналы.
    Пользователь дашборда канал ещё не выбирал, и решать за него, что это
    Telegram, значит отвечать не на его вопрос.

    Функция ЧИСТАЯ: ни запросов, ни `Request`, ни шаблонов — поэтому её ветки
    проверяются напрямую, без поднятия страницы.
    """
    counts = nav_counts or {}
    if not counts.get("accounts"):
        return ("Подключить аккаунт", "/accounts")
    if not counts.get("ads"):
        return ("Создать объявление", "/ads/new")
    if not counts.get("schedules"):
        return ("К объявлениям", "/ads")
    return ("", "")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Плитки. Страница агрегатов НЕ СЧИТАЕТ: восемь чисел приходят одним
    # запросом из модуля аналитики, который зовут и история, и Фаза 6 (D-35).
    # Три счётчика сущностей и отправки «от UTC-полуночи» отсюда сняты по
    # D-01/D-02 — счётчики дублировали боковое меню, а полночь показывала почти
    # ноль в первые часы суток независимо от того, работала система ночью.
    metrics = await send_metrics(db, user_id=user.id)

    # Heatmap активности за неделю (DASH-04). Таймзона приезжает СЮДА, а не
    # берётся внутри модуля: локальный час ячейки — свойство ЧИТАТЕЛЯ экрана, и
    # в админке Фазы 6 тот же модуль позовут с зоной администратора, а не
    # просматриваемого пользователя.
    heatmap_view = await activity_heatmap(
        db, user_id=user.id, tz=_get_timezone_for_user(user)
    )

    # Ближайшие отправки (DASH-02). Пометки причин считает модуль: страница не
    # знает ни про черновик объявления, ни про статус аккаунта, ни про флаги
    # групп — иначе то же правило пришлось бы повторить в Фазе 6.
    upcoming = await upcoming_sends(db, user_id=user.id)

    # Живая лента (DASH-03). Первичная отрисовка идёт ТЕМ ЖЕ паршалом, что
    # отдаёт маршрут опроса, поэтому строки приезжают под тем же именем `feed`
    # и с тем же лимитом: блок, посчитанный здесь по своим правилам, разъехался
    # бы с первым же тиком опроса.
    #
    # Блок «Последние отправки» отсюда СНЯТ вместе со своим шаблоном строки: его
    # место заняла лента, а недостижимых шаблонов в проекте не оставляют.
    feed = await recent_feed(db, user_id=user.id, limit=FEED_LIMIT)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "metrics": metrics,
            "heatmap_view": heatmap_view,
            "upcoming": upcoming,
            # Пара «подпись, адрес» для пустых состояний блоков (D-40).
            # Счётчики берутся из шелла, уже посчитанного зависимостью маршрута.
            "next_step": dashboard_next_step(
                getattr(request.state, "shell", {}).get("nav_counts")
            ),
            "feed": feed,
            # Интервал опроса едет в разметку ИЗ КОНСТАНТЫ модуля маршрута, где
            # рядом живёт лимит строк: литерал в шаблоне разъехался бы с ним
            # молча.
            "feed_poll_seconds": FEED_POLL_SECONDS,
            "active_page": "dashboard",
        },
    )

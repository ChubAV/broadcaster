from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.billing.subscription_period import access_is_open
from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.subscription import Subscription
from app.pages.common import get_shell_context, get_user_from_cookie

from app.pages.auth import router as auth_router
from app.pages.dashboard import router as dashboard_router
from app.pages.ads import router as ads_router
from app.pages.accounts import router as accounts_router
from app.pages.account_groups import router as account_groups_router
from app.pages.groups import router as groups_router
from app.pages.schedules import router as schedules_router
from app.pages.billing import router as billing_router
from app.pages.history import router as history_router
from app.pages.admin import router as admin_router
from app.pages.profile import router as profile_router


async def load_shell_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> None:
    """Put the live shell data into request.state.shell for every page route.

    Единая точка подмешивания вместо 26 словарей контекста в обработчиках:
    шаблон всегда получает request, поэтому шелл читает request.state.shell
    без изменений в роутерах. На страницах входа (user is None) зависимость
    возвращается без единого запроса к БД.

    Контекст-процессоры Starlette для этого не подходят: в 0.52.1 они
    вызываются синхронно (context.update(context_processor(request))),
    и async-выборку в них не выполнить.
    """
    user = await get_user_from_cookie(request, db, settings)
    request.state.shell = await get_shell_context(db, user)


ACCESS_EXPIRED_LOCATION = "/billing?expired=1"


async def require_access(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> None:
    """Отказать в странице, создающей ценность, когда доступ закрыт (критерий 2b).

    Форма взята у `require_admin` (`app/dependencies.py`): зависимость, которая
    ОТКАЗЫВАЕТ, а не возвращает значение. Вердикт считает `access_is_open` —
    единственное объявление предиката доступа на проект; второго сравнения дат
    здесь нет.

    ⚠️ НЕАУТЕНТИФИЦИРОВАННЫЙ ЗАПРОС ПРОХОДИТ ЭТУ ЗАВИСИМОСТЬ БЕЗ ОТКАЗА, И ЭТО
    РЕШЕНИЕ, А НЕ ДЫРА. Она отвечает на вопрос «оплачен ли доступ», а не «кто
    пришёл»: за аутентификацию отвечает сам маршрут, и он уже уводит гостя на
    `/login`. Отказать здесь значило бы завести ВТОРОЙ ответ на вопрос входа —
    и гость получал бы `/billing?expired=1` вместо страницы входа, то есть
    предложение оплатить доступ учётной записи, которой у него нет.

    ⚠️ ОТКАЗ — `HTTPException` СО СТАТУСОМ 302 И ЗАГОЛОВКОМ `location`, А НЕ
    ВОЗВРАТ `RedirectResponse`, И ВЫБОР ЗДЕСЬ ВЫНУЖДЕННЫЙ. Зависимость,
    объявленная через `APIRouter(dependencies=[...])`, своего возвращаемого
    значения никуда не отдаёт — FastAPI его ОТБРАСЫВАЕТ, — поэтому
    `return RedirectResponse(...)` не прервал бы обработчик ни на одном
    маршруте: гейт выглядел бы поставленным и не срабатывал бы НИ РАЗУ. Прервать
    цепочку зависимость может единственным способом — исключением. Форма отказа
    раздела при этом сохранена дословно: 302 на `/billing?expired=1` — тот же
    ответ, что у гардов формы оплаты (`app/pages/billing.py`), и человек попадает
    туда, где чинят, а не на страницу ошибки.

    ⚠️ ПАРАМЕТР `?expired=1` — АРТЕФАКТ РЕДИРЕКТА, А НЕ ВХОД ОБРАБОТЧИКА.
    Читать его в `/billing` запрещено (UI-контракт, E2): состояние доступа
    известно серверу из строки подписки, и решать по параметру адресной строки,
    что показать, значило бы отдать этот вопрос владельцу ссылки.

    ⚠️ ЗАПРОС ПОДПИСКИ ПОВТОРЯЕТ `get_shell_context` ДОСЛОВНО
    (`app/pages/common.py`): те же три условия, та же сортировка, тот же
    `limit(1)`. Читатель (шелл рисует срок) и гейт (решает, пускать ли) обязаны
    смотреть на ОДНУ строку — иначе экран говорил бы одно, а дверь отвечала бы
    другое.
    """
    user = await get_user_from_cookie(request, db, settings)
    if user is None:
        return

    subscription = (
        await db.execute(
            select(Subscription)
            .where(Subscription.user_id == user.id, Subscription.is_active.is_(True))
            .order_by(Subscription.expires_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if not access_is_open(subscription, datetime.now(timezone.utc)):
        raise HTTPException(
            status_code=302, headers={"location": ACCESS_EXPIRED_LOCATION}
        )


# ГЕЙТ ДОСТУПА ВЕШАЕТСЯ ПЕР-РОУТЕРНО НА ТЕХ, КТО СОЗДАЁТ ЦЕННОСТЬ, — И ЭТО
# ЧЁРНЫЙ СПИСОК, А НЕ БЕЛЫЙ. Перечень «кого пускать всегда» (вход, регистрация,
# выход, подписка, оплата, профиль, админка, дашборд) длиннее и опаснее перечня
# «кого закрывать», и он ГНИЁТ при добавлении маршрута: новый маршрут по
# умолчанию оказался бы ЗАКРЫТ вместе со страницей входа, то есть гейт запирал
# бы человека в системе, где он не может ни войти, ни заплатить (T-05.1-03).
# Пер-роутерное применение ошибается в сторону «пользователь попал куда не
# надо», а не «пользователь не может восстановить доступ».
#
# ⚠️ ЧТО РОУТЕР, ДОБАВЛЕННЫЙ БУДУЩИМ ПЛАНОМ БЕЗ ЗАВИСИМОСТИ, НЕ ПРОСКОЧИТ МОЛЧА,
# держит машинный гейт `tests/test_pages/test_access_gate.py`: он читает ЭТОТ
# ИСХОДНИК, а не собранное приложение — роутер без зависимости в объекте
# приложения выглядит совершенно обычно (T-05.1-01).
router = APIRouter(dependencies=[Depends(load_shell_context)])
router.include_router(auth_router)
router.include_router(dashboard_router)
router.include_router(ads_router, dependencies=[Depends(require_access)])
router.include_router(accounts_router, dependencies=[Depends(require_access)])
router.include_router(account_groups_router, dependencies=[Depends(require_access)])
router.include_router(groups_router, dependencies=[Depends(require_access)])
router.include_router(schedules_router, dependencies=[Depends(require_access)])
router.include_router(billing_router)
router.include_router(history_router, dependencies=[Depends(require_access)])
router.include_router(admin_router)
router.include_router(profile_router)

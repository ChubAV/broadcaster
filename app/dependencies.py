from typing import AsyncGenerator
import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.config import Settings, get_settings
from app.services.auth_service import actor_id, decode_access_token
from app.services.subscription_service import check_access

logger = structlog.get_logger(__name__)

security = HTTPBearer(auto_error=False)

_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(session_factory: async_sessionmaker[AsyncSession]) -> None:
    global _session_factory
    _session_factory = session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if _session_factory is None:
        raise RuntimeError("Database not initialized")
    async with _session_factory() as session:
        yield session


async def get_current_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: Settings = Depends(get_settings),
) -> int:
    token = None
    if credentials is not None:
        token = credentials.credentials
    if token is None:
        token = request.cookies.get("access_token")
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(token, settings.secret_key)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload["sub"]


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> "User":
    """Get current user object (not just ID). Checks is_blocked."""
    from app.models.user import User

    # Extract token from header or cookie
    token = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if token is None:
        token = request.cookies.get("access_token")
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(token, settings.secret_key)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await db.get(User, payload["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is blocked")
    return user


async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> "User":
    """Права администратора — по ДЕЙСТВУЮЩЕМУ ЛИЦУ, а не по субъекту (D-20).

    ⚠️ ВОЗВРАЩАЕТСЯ ТОТ, КТО ДЕЙСТВУЕТ, А НЕ ТОТ, ЧЬЮ УЧЁТНУЮ ЗАПИСЬ ОТКРЫЛИ.
    Обработчики админки пишут `admin.id` в журнал привилегированных операций
    (`admin_toggle_free_access`, `admin_restart_worker`); верни эта зависимость
    субъекта — и журнал называл бы автором действия того, НАД КЕМ оно
    совершено. Это ровно тот класс записи, ради которого журнал и ведётся.

    ⚠️ БЛОКИРОВКА СУБЪЕКТА ЗДЕСЬ НЕ СПРАШИВАЕТСЯ ПРИ НАЛИЧИИ ДЕЙСТВУЮЩЕГО ЛИЦА
    (D-26). Общая проверка `get_current_user` отказывает заблокированному 403, и
    администратор, вошедший под заблокированным ради вопроса «за что меня
    заблокировали», потерял бы вместе с этим и админку — то есть путь назад.
    Блокировка самого ДЕЙСТВУЮЩЕГО ЛИЦА при этом действует: заблокированный
    администратор админом быть перестаёт.

    ⚠️ ПОРЯДОК ВЕТОК НЕСУЩИЙ: сначала «есть ли действующее лицо», потом всё
    остальное. Ветка «сначала обычная проверка, а если она отказала — посмотреть
    на признак» отказывала бы заблокированному субъекту раньше, чем узнала бы,
    что за ним стоит администратор.
    """
    from app.models.user import User

    acting_id = _actor_id(request, None, settings)
    if acting_id is not None:
        actor = await db.get(User, acting_id)
        if actor is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        if actor.is_blocked or actor.email != settings.admin_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )
        return actor

    user = await get_current_user(request, db, settings)
    if user.email != settings.admin_email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


# ТЕЛО ОТКАЗА — ОБЪЯСНЕНИЕ, А НЕ КОД СОСТОЯНИЯ ПРОДУКТА. Страничная поверхность
# отвечает редиректом, и слова там рисует разметка из закрытого множества
# (UI-контракт E2); JSON-клиенту показывать нечего, и единственное, что он может
# сделать с отказом осмысленно, — сказать словами, что произошло и куда идти.
ACCESS_EXPIRED_DETAIL = (
    "Доступ закрыт: срок подписки истёк. Продлите доступ в разделе оплаты."
)


async def get_current_user_id_with_access(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> int:
    """Идентификатор вошедшего — при условии, что доступ ОПЛАЧЕН (критерий 2b).

    Форма взята у `require_admin`: зависимость, которая сначала спрашивает
    существующую проверку, а затем ОТКАЗЫВАЕТ исключением. Отказ обязан быть
    именно исключением — зависимость, объявленная через
    `include_router(dependencies=[...])`, своего возвращаемого значения никуда не
    отдаёт, и «вернуть отказ» значило бы поставить гейт, не срабатывающий ни на
    одном маршруте.

    ⚠️ `get_current_user_id` НЕ ТРОНУТА НИ ОДНОЙ СТРОКОЙ, И ЭТО НЕСУЩЕЕ РЕШЕНИЕ,
    А НЕ ОСТОРОЖНОСТЬ. Она обслуживает и те маршруты, которые обязаны остаться
    открытыми при истёкшем доступе, — прежде всего `GET /api/billing/*`, откуда
    человек и узнаёт, сколько платить. Проверка доступа ВНУТРИ неё закрыла бы их
    заодно, то есть заперла бы человека в продукте, где единственное открывающее
    действие само требует доступа (T-05.1-16). Отказ поэтому живёт в СОСЕДНЕЙ
    зависимости, которая вешается пер-роутерно и перечнем. Закреплено
    `test_the_api_authentication_dependency_is_left_untouched`.

    КОД 402, А НЕ 403, И РАЗНИЦА ЗДЕСЬ ОСМЫСЛЕННАЯ. 403 говорит «у вас нет
    прав», и клиент, получивший его, ничего сделать не может; 402 говорит «не
    оплачено», и на это есть ровно одно действие. Различимость двух причин
    отказа стоит одного кода состояния.

    ⚠️ АДМИНИСТРАТОР ЭТОЙ ЗАВИСИМОСТЬЮ НЕ ЗАДЕВАЕТСЯ. Она не висит ни на
    `require_admin`, ни на маршрутах админки: администратор без действующей
    подписки обязан входить в админку — иначе он не сможет выдать бесплатный
    доступ ни себе, ни другому (T-05.1-17).
    """
    user_id = await get_current_user_id(request, credentials, settings)

    allowed, _reason = await check_access(db, user_id)
    if not allowed:
        raise HTTPException(status_code=402, detail=ACCESS_EXPIRED_DETAIL)
    return user_id


# ТЕЛО ОТКАЗА ЗАБЛОКИРОВАННОМУ — ОБЪЯСНЕНИЕ, А НЕ КОД СОСТОЯНИЯ. Основание то
# же, что у соседней константы выше: JSON-клиенту показывать нечего, и
# единственное, что он может сделать с отказом осмысленно, — сказать словами,
# что произошло. Молчаливый отказ приводит человека в поддержку с «у меня не
# работает» и без единого способа отличить блокировку от поломки (T-06-BL5).
BLOCKED_DETAIL = (
    "Учётная запись заблокирована. Разделы продукта закрыты до снятия "
    "блокировки — обратитесь в поддержку."
)


def _actor_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
    settings: Settings,
) -> int | None:
    """Идентификатор действующего лица из того же токена — либо `None`.

    ⚠️ ТОКЕН РАЗБИРАЕТСЯ ВТОРОЙ РАЗ, И ЭТО НАЗВАННАЯ ЦЕНА, А НЕ НЕДОСМОТР.
    Общий аутентификатор отдаёт наружу только `sub`, а трогать его нельзя ни
    одной строкой — запрет закреплён машинным гейтом и держит открытыми
    маршруты, которым сессия БД не нужна. Поэтому «есть ли действующее лицо»
    читается рядом, второй проверкой подписи. Цена — один HMAC на запрос к
    ЗАКРЫТЫМ маршрутам; цена альтернативы — расширение зависимости,
    обслуживающей в том числе незащищённые пути.

    Отсутствие токена и негодный токен дают `None`, а не исключение: отказ по
    ним — работа аутентификатора, и второе его определение здесь разошлось бы
    с первым.

    ⚠️ ПОРЯДОК ИСТОЧНИКОВ ТОКЕНА ПОВТОРЯЕТ `get_current_user` ДОСЛОВНО: сначала
    разобранные учётные данные, затем заголовок, затем cookie. Читатель,
    забывший заголовок, видел бы «действующего лица нет» ровно у клиентов с
    Bearer — то есть терял бы админ-доступ у половины поверхностей и сохранял у
    другой.

    Приведение типа здесь НЕ делается: оно живёт внутри чтения токена, а
    значение снимается единственным читателем признака на проект.
    """
    token = None
    if credentials is not None:
        token = credentials.credentials
    if token is None:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if token is None:
        token = request.cookies.get("access_token")
    if token is None:
        return None
    return actor_id(decode_access_token(token, settings.secret_key))


async def get_current_user_id_active(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> int:
    """Идентификатор вошедшего — при условии, что учётная запись ДЕЙСТВУЕТ.

    Форма копируется с соседа (`get_current_user_id_with_access`) целиком, и
    вместе с ней копируется причина, по которой проверка живёт СНАРУЖИ
    аутентификатора: `get_current_user_id` обслуживает и незащищённые пути, и
    цена запроса к базе на них ничем не оправдана. Отказ обязан быть именно
    исключением — зависимость, объявленная через
    `include_router(dependencies=[...])`, своего возвращаемого значения никуда
    не отдаёт.

    ⚠️ ЛОБОВАЯ ПОЧИНКА — ПРОВЕРКА `is_blocked` ВНУТРИ `get_current_user_id` —
    ЗАПРЕЩЕНА, И ЗАПРЕТ ЗАКРЕПЛЁН ТЕСТОМ. Выглядит она как «сделать в одном
    месте вместо пяти», а означает закрытие денежного роутера заодно:
    уведомление ЮKassa о СОСТОЯВШЕМСЯ платеже получило бы отказ, то есть приём
    денег остановился бы по уже совершённым платежам (D-53). Перечень
    закрываемых роутеров поэтому пер-роутерный и выписан решением.

    ⚠️ ПРИ НАЛИЧИИ ПРИЗНАКА ДЕЙСТВУЮЩЕГО ЛИЦА БЛОКИРОВКА СУБЪЕКТА НЕ
    ПРИМЕНЯЕТСЯ (D-26). Вход администратора под заблокированным пользователем
    разрешён ЯВНЫМ решением: «за что меня заблокировали» — типовой вопрос, и
    ответить на него можно, только увидев продукт глазами заблокированного.
    Ветка написана сейчас и до плана 06-12, выпускающего такие токены, мертва —
    это осознанно: наивная починка блокировки выкинула бы заодно
    администратора, и следующая правка авторизации закрыла бы вход молча.

    ⚠️ КЭША ВЕРДИКТА ЗДЕСЬ НЕТ (D-31). Это чтение строки по первичному ключу;
    кэш добавил бы поверхность инвалидации — новый источник ошибок ради
    неизмеренной экономии. Готовый кэш вердикта из фазы 05.1 лежит рядом и
    остаётся приёмом на случай, если замер покажет обратное.

    БЛОКИРОВКА НЕ ВЫСЕЛЯЕТ ОТКРЫТЫЙ СЕАНС МГНОВЕННО: она закрывает СЛЕДУЮЩЕЕ
    обращение. Мгновенное выселение потребовало бы списка отозванных токенов,
    то есть хранилища, которого фаза не заводит.
    """
    from app.models.user import User

    user_id = await get_current_user_id(request, credentials, settings)

    if _actor_id(request, credentials, settings) is not None:
        return user_id

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    if user.is_blocked:
        # 403, а не 402: «нет прав», а не «не оплачено». Различимость двух
        # причин отказа стоит одного кода состояния — у неоплаты есть ровно
        # одно действие, у блокировки нет ни одного.
        logger.warning(
            "blocked_request_refused", user_id=user_id, path=request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=BLOCKED_DETAIL
        )
    return user_id

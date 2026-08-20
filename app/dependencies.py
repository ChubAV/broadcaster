from typing import AsyncGenerator
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.config import Settings, get_settings
from app.services.auth_service import decode_access_token
from app.services.subscription_service import check_access

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
    """Require current user to be admin. Returns User object."""
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

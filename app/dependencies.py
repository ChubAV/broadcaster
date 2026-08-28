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


def email_is_admin(email: str | None, settings: Settings) -> bool:
    """ЕДИНСТВЕННОЕ выражение правила «кто администратор» на проект (WR-01).

    ⚠️ ПРАВИЛО БЫЛО ВЫПИСАНО ДВАЖДЫ, И ДВЕ КОПИИ РАЗОШЛИСЬ РОВНО В ТУ СТОРОНУ,
    КОТОРАЯ ДАЁТ ДОСТУП. Страничная проверка (`check_is_admin`) открывалась
    веткой «настройка не задана — администраторов нет»; зависимость, гейтящая
    все маршруты раздела, такой ветки не имела и сравнивала адрес напрямую.
    Умолчание `admin_email` — ПУСТАЯ СТРОКА, поэтому на развёртывании без
    заданного `ADMIN_EMAIL` строка пользователя с пустым адресом проходила бы
    в админку по всем маршрутам, тогда как ссылка на раздел оставалась бы
    скрытой: два ответа на один вопрос, и расходились они молча.

    ⚠️ ПУСТАЯ НАСТРОЙКА — «АДМИНИСТРАТОРОВ НЕТ», А НЕ «АДМИНИСТРАТОР ЛЮБОЙ С
    ПУСТЫМ АДРЕСОМ». Достижимость второго сегодня узкая (оба пути регистрации
    пустой адрес не принимают), но предмет находки не в достижимости, а в том,
    что правило существовало в двух экземплярах.

    Ветка сравнения здесь одна, и потому разойтись ей больше не с чем.
    """
    if not settings.admin_email:
        return False
    return email == settings.admin_email


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
        if actor.is_blocked or not email_is_admin(actor.email, settings):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )
        return actor

    user = await get_current_user(request, db, settings)
    if not email_is_admin(user.email, settings):
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


def _presented_tokens(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> list[str]:
    """ВСЕ носители токена, ПРЕДЪЯВЛЕННЫЕ запросом, без повторов.

    Единственное место на проект, где выписан ПЕРЕЧЕНЬ носителей:
    разобранные учётные данные, заголовок `Authorization: Bearer`, cookie
    сессии. Порядок сохранён тот же, что у `get_current_user`, чтобы
    «кто пришёл» и «есть ли действующее лицо» начинали с одного и того же
    носителя; но читатель признака обязан дойти до конца перечня.

    Пустой список — НОРМАЛЬНЫЙ ИСХОД, а не ошибка: уведомление
    ЮKassa приходит не от браузера и никакого токена не несёт (D-53).
    """
    tokens: list[str] = []
    if credentials is not None:
        tokens.append(credentials.credentials)
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        header_token = auth_header[7:]
        if header_token not in tokens:
            tokens.append(header_token)
    cookie_token = request.cookies.get("access_token")
    if cookie_token and cookie_token not in tokens:
        tokens.append(cookie_token)
    return tokens


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

    ⚠️ СПРАШИВАЮТСЯ ВСЕ ПРЕДЪЯВЛЕННЫЕ НОСИТЕЛИ, А НЕ ПЕРВЫЙ ПО ПОРЯДКУ, И ЭТО
    НЕСУЩЕЕ СВОЙСТВО, А НЕ ПЕРЕСТРАХОВКА. Прежняя редакция читала ТОЛЬКО ПЕРВЫЙ
    найденный токен в порядке «учётные данные → заголовок → cookie», а все
    страничные обработчики, которых закрывает `forbid_when_impersonating`,
    аутентифицируются через `get_user_from_cookie`, читающий ТОЛЬКО cookie.
    Два чтения расходились в том, что считать «токеном запроса», и любой
    заголовок `Authorization: Bearer ...` — В ТОМ ЧИСЛЕ НЕГОДНЫЙ, В ТОМ ЧИСЛЕ
    НЕ ТОКЕН ВОВСЕ — отключал запрет целиком: гард видел «действующего лица
    нет», обработчик продолжал действовать под чужой личностью, и отказ не
    попадал даже в журнал (CR-01 ревизии фазы 6). Обход ВСЕГО
    предъявленного закрывает расхождение В ОБЕ СТОРОНЫ и не требует от
    зависимости знания о том, каким именно чтением аутентифицируется
    каждый из закрытых маршрутов, — знания, которое разошлось бы снова.

    ДОСТУП Bearer-КЛИЕНТА НЕ ПОТЕРЯН: токен из заголовка по-прежнему
    спрашивается и по-прежнему ПЕРВЫМ — изменилось только то, что его
    ОТСУТСТВИЕ признака больше не заканчивает поиск. Маршрутов, где читается
    признак действующего лица, всего три семейства (`require_admin`,
    `forbid_when_impersonating`, `get_current_user_id_active`), и ни на одном
    из них два разных действующих лица одновременно не предъявляются.

    Приведение типа здесь НЕ делается: оно живёт внутри чтения токена, а
    значение снимается единственным читателем признака на проект.
    """
    for token in _presented_tokens(request, credentials):
        found = actor_id(decode_access_token(token, settings.secret_key))
        if found is not None:
            return found
    return None


# ТЕЛО ОТКАЗА ПОД ЧУЖОЙ ЛИЧНОСТЬЮ — И ОНО ОБЯЗАНО ОТЛИЧАТЬСЯ ОТ ОТКАЗА ПО
# ПРАВАМ (D-22). Администратор, получивший «Admin access required» там, где на
# самом деле мешает чужая личность, пойдёт чинить ПРАВА: проверять адрес в
# настройке, перевыпускать токен, читать журнал доступа. Настоящая причина —
# что он не вышел из чужой учётной записи — не была бы названа ни одним словом,
# и единственное нужное ему действие осталось бы невыполненным. Различимость
# двух причин отказа стоит отдельной константы.
#
# Текст называет и ПРИЧИНУ, и ВЫХОД: «вернитесь в свою учётную запись» — ровно
# то, что делает полоса возврата в шелле (план 06-12).
IMPERSONATION_FORBIDDEN_DETAIL = (
    "Действие недоступно под чужой учётной записью: вы вошли под пользователем. "
    "Вернитесь в свою учётную запись, чтобы выполнить его."
)

# КУДА УВОДИТ ОТВЕРГНУТОЕ ДЕЙСТВИЕ, КОГДА ЗАПРОС ПРИШЁЛ ОТ СЛОЯ ПИСЬМА.
#
# Адрес обязан быть ЛОКАЛЬНЫМ и GET-СОВМЕСТИМЫМ, и оба требования вынужденные.
# Локальность — потому что значение уезжает в заголовок, приказывающий браузеру
# уйти по адресу: чужой адрес там есть готовый открытый редирект (T-08-05), и
# `app/pages/htmx.py::_local_path` отвергает такой ещё до отправки ответа.
# GET-совместимость — потому что отвергается ЗАПИСЬ, и вернуть человека на её
# собственный путь нельзя: тот принимает только POST.
#
# `/dashboard` — домашний экран ТОЙ ЛИЧНОСТИ, под которой работает
# администратор, и выбран он не за нейтральность: именно там видна полоса
# возврата «ВЕРНУТЬСЯ В АДМИНА», то есть ВЫХОД из положения, а не только его
# название.
#
# ⚠️ КОД `impersonation_forbidden` РЕГИСТРИРУЕТСЯ В РЕЕСТРЕ УВЕДОМЛЕНИЙ
# СОСЕДНИМ ПЛАНОМ (08-02), И ДО ЭТОГО МОМЕНТА ДЕГРАДАЦИЯ ТИХАЯ. Реестр —
# ЗАКРЫТОЕ множество: по незнакомому коду он не возвращает ничего, поэтому
# человек попадает на домашний экран без плашки, а не видит пустую рамку или
# чужой текст. Полноту кодов стережёт машинный гейт (план 08-06), а не
# бдительность читателя.
IMPERSONATION_REFUSED_LOCATION = "/dashboard?notice=impersonation_forbidden"


async def forbid_when_impersonating(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: Settings = Depends(get_settings),
) -> None:
    """Отказать в НЕОБРАТИМОМ и ДЕНЕЖНОМ действии под чужой личностью (D-22).

    Форма копируется с соседних гардов (`get_current_user_id_with_access`,
    `get_current_user_id_active`) целиком: зависимость, которая спрашивает
    существующее чтение признака и затем ОТКАЗЫВАЕТ исключением.

    ⚠️ ОТКАЗ — ИСКЛЮЧЕНИЕ, А НЕ ВОЗВРАЩАЕМОЕ ЗНАЧЕНИЕ. Зависимость, объявленная
    через `include_router(dependencies=[...])`, своего результата никуда не
    отдаёт — FastAPI его ОТБРАСЫВАЕТ, — поэтому «вернуть отказ» значило бы
    поставить запрет, не срабатывающий НИ НА ОДНОМ маршруте. Довод уже выписан
    в проекте у гейта доступа и повторяется здесь дословно, потому что ошибка
    выглядела бы как работающая защита.

    ⚠️ ОТСУТСТВИЕ ТОКЕНА — НЕ ОТКАЗ, И ЭТО НЕСУЩЕЕ СВОЙСТВО. Денежный роутер
    закрывается этой зависимостью ЦЕЛИКОМ, а единственный его вход —
    уведомление ЮKassa о СОСТОЯВШЕМСЯ платеже: оно приходит не от браузера и
    никакого токена не несёт. Зависимость, отвергающая запрос без действующего
    лица, остановила бы приём денег по УЖЕ СОВЕРШЁННЫМ платежам, а потерянное
    уведомление откатом кода не возвращается — ровно та цена, которую разбирал
    чекпойнт плана 06-06 (D-53). Негодный токен здесь тоже не отказ: отвечать
    на вопрос «кто пришёл» — работа аутентификатора, и второе его определение
    тут разошлось бы с первым.

    ⚠️ СЕССИИ БД ЗАВИСИМОСТЬ НЕ БЕРЁТ. Признак действующего лица читается из
    подписи токена, и запрос к базе здесь ничего не добавил бы, кроме цены на
    каждом закрытом маршруте — в том числе на вебхуке, который обязан
    отвечать быстро и не зависеть от доступности базы больше, чем уже зависит.

    ПОЛНОТУ ПЕРЕЧНЯ ЗАКРЫТЫХ МАРШРУТОВ ДЕРЖИТ НЕ ЭТА ФУНКЦИЯ, А МАШИННЫЙ ГЕЙТ
    `tests/test_pages/test_impersonation_gate.py` (D-23): он обходит КАЖДОЕ
    изменяющее объявление проекта по синтаксическому дереву и требует, чтобы
    маршрут попал либо в запрещённые, либо в объявленные разрешёнными. Маршрут,
    добавленный будущей фазой и не попавший никуда, роняет тест — вместо того
    чтобы оказаться разрешённым ПО УМОЛЧАНИЮ, как было бы с чёрным списком.

    ⚠️ ТРАНСПОРТОВ ОТКАЗА ТЕПЕРЬ ДВА, А ПРЕДИКАТ ОТКАЗА ПО-ПРЕЖНЕМУ ОДИН.
    Человеку без слоя письма отказ приезжает тем же 403 с тем же текстом;
    запросу от слоя письма — заголовком перехода, потому что тело `detail`
    слой письма никуда не показывает, и отвергнутое действие выглядело бы для
    человека просто НЕ СЛУЧИВШИМСЯ (FOUND-07). Отвечает на вопрос «отказать
    ли» по-прежнему одно выражение — `_actor_id(...) is not None`, — и стоит
    оно СТРОГО ДО развилки транспорта. Поэтому обе границы выше остаются в
    силе дословно: и «отсутствие токена — не отказ», и «негодный токен — не
    отказ» вычисляются раньше, чем становится важно, кто спрашивает.
    """
    if _actor_id(request, credentials, settings) is None:
        return

    # ИМПОРТ ОТЛОЖЕН ВНУТРЬ ФУНКЦИИ, И ЭТО ВЫНУЖДЕННО, А НЕ СТИЛЬ. Слой ответа
    # живёт в пакете `app.pages`, а его `__init__` собирает страничные роутеры и
    # ради этого импортирует ЭТОТ модуль; импорт слоя на уровне модуля замкнул
    # бы кольцо и уронил бы сборку приложения на полуинициализированном модуле.
    # Приём в этом файле уже принят — см. `from app.models.user import User` в
    # `get_current_user_id_active`.
    from app.pages.htmx import refuse

    # Запись в журнал стоит ДО отказа и в обоих транспортах ОДНА И ТА ЖЕ:
    # разбор инцидента не должен зависеть от того, был ли у человека включён
    # JavaScript, а вторая запись на второй ветке разошлась бы с первой.
    logger.warning(
        "impersonated_action_refused",
        path=request.url.path,
        method=request.method,
    )
    refuse(
        request,
        location=IMPERSONATION_REFUSED_LOCATION,
        without_htmx=HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=IMPERSONATION_FORBIDDEN_DETAIL,
        ),
    )


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

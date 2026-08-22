"""Блокировка ДЕЙСТВУЕТ — все три пути в одном файле (CR-01, D-30).

ЗАЧЕМ ОДИН ФАЙЛ НА ТРИ ПОВЕРХНОСТИ. Блокировка не есть свойство одного
маршрута: она обязана закрывать вход, уже выданную cookie на JSON-поверхности и
путь рассылки, — и до этого плана не закрывала НИ ОДНОГО из трёх, хотя кнопка в
админке была. Разложенная по трём файлам, она чинилась бы по одной поверхности
за раз, и каждая следующая фаза заново узнавала бы, что «блокировка вроде есть».
Здесь все три утверждения читаются подряд, и пропуск любого виден глазом.

ФАЙЛ ЗАМЕНЯЕТ `test_blocked_user_cannot_login` из `tests/test_admin.py`, чьё имя
обещало проверку ЭФФЕКТА блокировки, а тело проверяло ровно один JSON-маршрут
входа (`POST /api/auth/login`), который единственный этот эффект и имел. Человек
входит СТРАНИЧНОЙ формой, и она выдавала cookie заблокированному. Тест не
переименован, а удалён: переименование оставило бы второго, более слабого
свидетеля того же требования. Тумблер блокировки в админке (`admin_toggle_block`)
переехал сюда же — предмет один, и держать его половину в файле админки значило
бы снова разложить блокировку по файлам.

ЧЕГО ЗДЕСЬ НЕТ И ПОЧЕМУ. Страничный путь (`get_user_from_cookie`) НЕ правится
этим планом: он проверяет состояние учётной записи с фазы 05.1 (D-30). Его
утверждения живут в своих файлах, и дублировать их сюда значило бы завести
второго свидетеля.
"""
import ast
import contextlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.analytics.send_analytics import normalize_utc
from app.application.scheduling.use_cases import collect_due_schedules
from app.constants import AD_STATUS_PUBLISHED
from app.database import Base
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.subscription import Subscription
from app.models.user import User
from app.services.billing_cache import check_access_cached

DEPENDENCIES_PY = Path(__file__).resolve().parents[2] / "app" / "dependencies.py"

# Закрытые блокировкой JSON-маршруты, у которых есть чтение. Перечень выписан
# ЗДЕСЬ, а не выведен из сборки: полнота перечня РОУТЕРОВ держится машинным
# гейтом (`test_access_gate.py`), а здесь проверяется наблюдаемое поведение.
CLOSED_JSON_READS = ("/api/ads", "/api/accounts", "/api/schedules", "/api/history")

PASSWORD = "testpass123"


async def _register(client: AsyncClient, email: str) -> None:
    """Регистрация прикладным входом — вместе с пробным сроком.

    Именно поэтому не ORM: без строки подписки соседний гейт доступа отказал бы
    402 раньше блокировки, и тест зеленел бы по ЧУЖОЙ причине.
    """
    response = await client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "name": "U"},
    )
    assert response.status_code == 201, (
        f"регистрация не прошла ({response.status_code}) — тест блокировки "
        f"красил бы чужую поломку"
    )


async def _login_page(client: AsyncClient, email: str):
    """Вход СТРАНИЧНОЙ формой — тем путём, которым входит человек."""
    return await client.post(
        "/login",
        data={"email": email, "password": PASSWORD},
        follow_redirects=False,
    )


async def _user(db_session: AsyncSession, email: str) -> User:
    return (
        await db_session.execute(select(User).where(User.email == email))
    ).scalar_one()


async def _block(db_session: AsyncSession, user: User) -> None:
    """Признак ставится ПРЯМОЙ правкой строки, а не админским маршрутом.

    Предмет проверки — СЛЕДСТВИЕ блокировки; прогонять его через админку
    значило бы ронять все эти тесты за компанию при поломке админки. Сам
    тумблер проверяется отдельно, ниже в этом файле.
    """
    user.is_blocked = True
    await db_session.commit()


def _has_session_cookie(response) -> bool:
    return any(
        raw.split("=", 1)[0].strip() == "access_token"
        for raw in response.headers.get_list("set-cookie")
    )


# =============================================================================
# Путь 1 — вход (`login_submit`)
# =============================================================================


@pytest.mark.asyncio
async def test_a_blocked_user_gets_no_cookie_from_the_page_login(
    client: AsyncClient, db_session
):
    """Заблокированный с ВЕРНЫМ паролем не получает cookie и читает причину.

    ⚠️ ДВА УТВЕРЖДЕНИЯ, И ВТОРОЕ НЕ ДЕКОРАЦИЯ. Отсутствие cookie закрывает
    доступ; названная словами причина закрывает поход в поддержку. Молчаливый
    отказ читается человеком как «пароль не подходит», и различить блокировку
    от поломки не может ни он, ни поддержка.

    Пароль ВЕРНЫЙ намеренно: отказ по неверному паролю не доказал бы ничего.
    """
    await _register(client, "blocked@test.com")
    await _block(db_session, await _user(db_session, "blocked@test.com"))

    response = await _login_page(client, "blocked@test.com")

    assert not _has_session_cookie(response), (
        "вход выдал cookie заблокированному — блокировка не действует на первом "
        "же пути (CR-01)"
    )
    assert response.status_code == 200, (
        f"отказ во входе ответил {response.status_code} вместо страницы входа "
        f"со словами"
    )
    assert "заблокир" in response.text.lower(), (
        "отказ не назван словами: человек прочитает его как «неверный пароль» "
        "и придёт в поддержку с вопросом, на который она не сможет ответить"
    )


@pytest.mark.asyncio
async def test_the_login_refusal_is_journaled_with_the_user_id(
    client: AsyncClient, db_session, caplog
):
    """Отказ во входе оставляет ИМЕНОВАННУЮ строку журнала с идентификатором.

    Без неё отказ невидим целиком: cookie не выдана, запись никуда не легла, и
    поддержка не может отличить «его заблокировали» от «вход сломан».

    Запись снимается `caplog`-ом, а не `structlog.testing.capture_logs()`, по
    основанию, выписанному в `tests/test_admin.py`: ленивый прокси связывается
    с цепочкой процессоров при первом использовании и кэширует её.
    """
    await _register(client, "blocked@test.com")
    user = await _user(db_session, "blocked@test.com")
    user_id = user.id
    await _block(db_session, user)

    with caplog.at_level("WARNING", logger="app.pages.auth"):
        await _login_page(client, "blocked@test.com")

    entries = [
        record.msg
        for record in caplog.records
        if isinstance(record.msg, dict)
        and record.msg.get("event") == "blocked_login_refused"
    ]
    assert len(entries) == 1, (
        "отказ во входе не оставил записи `blocked_login_refused`: "
        f"{[getattr(r, 'msg', r) for r in caplog.records]}"
    )
    assert entries[0].get("user_id") == user_id, (
        "журнал не назвал, КОМУ отказали — запись без идентификатора не "
        "позволяет ответить на вопрос поддержки"
    )


@pytest.mark.asyncio
async def test_an_ordinary_user_still_logs_in_unchanged(
    client: AsyncClient, db_session
):
    """Граница сверху: НЕзаблокированный входит ровно как прежде.

    Без этого утверждения отказ, срабатывающий у ВСЕХ, прошёл бы обе проверки
    выше. Набор атрибутов cookie проверяется здесь же — правка встала в тот же
    обработчик, что и единая точка установки (план 06-02), и сломать его она
    могла бы молча.
    """
    await _register(client, "ordinary@test.com")

    response = await _login_page(client, "ordinary@test.com")

    assert response.status_code == 302, "вход обычного пользователя перестал работать"
    assert response.headers["location"] == "/dashboard"
    assert _has_session_cookie(response), "вход не выдал cookie обычному пользователю"

    raw = next(
        value
        for value in response.headers.get_list("set-cookie")
        if value.split("=", 1)[0].strip() == "access_token"
    )
    lowered = raw.lower()
    assert "httponly" in lowered
    assert "samesite=lax" in lowered
    assert "path=/" in lowered


# =============================================================================
# Путь 2 — уже выданная cookie на JSON-поверхности
# =============================================================================


@pytest.mark.asyncio
async def test_a_blocked_user_is_refused_on_a_closed_json_route(
    client: AsyncClient, db_session
):
    """УЖЕ ВЫДАННАЯ cookie перестаёт пускать: подпись верна, состояние — нет.

    Это второй путь долга целиком: до правки заблокированный продолжал работать
    по cookie, выданной ДО блокировки, потому что зависимость авторизации
    читала только подпись токена.

    ⚠️ БЛОКИРОВКА НЕ ВЫСЕЛЯЕТ ОТКРЫТЫЙ СЕАНС МГНОВЕННО — она закрывает
    СЛЕДУЮЩЕЕ обращение, и здесь проверяется ровно это. Мгновенное выселение
    потребовало бы списка отозванных токенов, то есть хранилища, которого фаза
    не заводит.
    """
    await _register(client, "blocked@test.com")
    await _login_page(client, "blocked@test.com")

    live = await client.get("/api/ads")
    assert live.status_code == 200, (
        f"до блокировки закрытый маршрут ответил {live.status_code} — тест "
        f"проверял бы чужую поломку"
    )

    await _block(db_session, await _user(db_session, "blocked@test.com"))

    response = await client.get("/api/ads")

    assert response.status_code == 403, (
        f"заблокированный прошёл по старой cookie: /api/ads ответил "
        f"{response.status_code}"
    )
    assert "location" not in response.headers, (
        "JSON-вход ответил редиректом — клиент получил бы HTML вместо отказа"
    )
    detail = response.json().get("detail", "")
    assert "заблокир" in detail.lower(), (
        f"отказ на JSON-поверхности не объяснён словами: {detail!r}"
    )


@pytest.mark.asyncio
async def test_the_json_refusal_is_journaled_with_the_user_id(
    client: AsyncClient, db_session, caplog
):
    """Отказ на JSON-поверхности тоже оставляет именованную строку журнала.

    Прохибиция прозрачности плана называет ОБА отказа, а не один: клиент,
    получивший 403, в поддержку приходит с тем же вопросом, что и человек,
    не вошедший в форму.
    """
    await _register(client, "blocked@test.com")
    await _login_page(client, "blocked@test.com")
    user = await _user(db_session, "blocked@test.com")
    user_id = user.id
    await _block(db_session, user)

    with caplog.at_level("WARNING", logger="app.dependencies"):
        await client.get("/api/ads")

    entries = [
        record.msg
        for record in caplog.records
        if isinstance(record.msg, dict)
        and record.msg.get("event") == "blocked_request_refused"
    ]
    assert len(entries) == 1, (
        "отказ JSON-поверхности не оставил записи `blocked_request_refused`: "
        f"{[getattr(r, 'msg', r) for r in caplog.records]}"
    )
    assert entries[0].get("user_id") == user_id


@pytest.mark.parametrize("path", CLOSED_JSON_READS)
@pytest.mark.asyncio
async def test_an_ordinary_user_still_passes_every_closed_json_route(
    client: AsyncClient, path: str
):
    """Граница сверху на КАЖДОМ закрытом маршруте, а не на одном.

    Ошибка в навеске зависимости закрывает работающие маршруты живым
    пользователям, и проявляется она у него, а не в суите: один проверенный
    маршрут оставил бы остальные четыре без свидетеля.
    """
    await _register(client, "ordinary@test.com")
    await _login_page(client, "ordinary@test.com")

    response = await client.get(path)

    assert response.status_code == 200, (
        f"{path} ответил {response.status_code} НЕзаблокированному пользователю"
    )


@pytest.mark.asyncio
async def test_an_impersonation_token_is_not_refused_by_the_subject_block(
    client: AsyncClient, db_session, test_settings
):
    """Признак действующего лица (`act`) снимает блокировку СУБЪЕКТА (D-26).

    ⚠️ ЭТО НЕ ПОСЛАБЛЕНИЕ, А ТОТ САМЫЙ СЛУЧАЙ, РАДИ КОТОРОГО ИМПЕРСОНАЦИЯ
    СУЩЕСТВУЕТ: «за что меня заблокировали» — типовой вопрос, и ответить на него
    администратор может, только войдя под заблокированным. Наивная починка
    блокировки выкинула бы заодно администратора, поэтому ветка написана СЕЙЧАС
    и закреплена тестом, а не оставлена следующей правке авторизации.

    Токен собирается ВРУЧНУЮ: выпуск токенов с `act` появится планом 06-12, и
    ждать его значило бы отгрузить блокировку без свидетеля этой ветки — то
    есть ровно с тем дефектом, который D-26 и запрещает.
    """
    await _register(client, "blocked@test.com")
    await _register(client, "admin@test.com")
    user = await _user(db_session, "blocked@test.com")
    admin = await _user(db_session, "admin@test.com")
    user_id, admin_id = user.id, admin.id
    await _block(db_session, user)

    token = jwt.encode(
        {
            "sub": str(user_id),
            "act": str(admin_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        },
        test_settings.secret_key,
        algorithm="HS256",
    )

    response = await client.get(
        "/api/ads", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200, (
        f"вход под заблокированным пользователем закрыт ({response.status_code}) "
        f"— блокировка применилась к субъекту при наличии `act` (D-26)"
    )


@pytest.mark.asyncio
async def test_the_money_router_stays_open_to_a_blocked_user(db_session, test_settings):
    """Денежный роутер заблокированному НЕ закрывается (D-53, вариант A).

    ⚠️ ПРЕДМЕТ — ВЕБХУК ЮKASSA, ЕДИНСТВЕННЫЙ ВХОД РОУТЕРА. Отказ на нём есть
    отказ в ответ на уведомление о СОСТОЯВШЕМСЯ платеже: ЮKassa повторит
    доставку несколько раз и перестанет, а потерянное уведомление откатом кода
    не возвращается. Ровно это делает решение D-53 несимметричным по цене.

    ПРОВЕРКА ИСТОЧНИКА ВЫКЛЮЧЕНА НАСТРОЙКОЙ, а не подделкой адреса: предмет
    вопроса — дошёл ли запрос до обработчика, а не устоит ли гард подлинности
    (у него свои свидетели). Событие намеренно НЕЗНАКОМОЕ: `handle_webhook`
    отвечает на такое `False`, и ответ 200 доказывает, что до него дошли.
    """
    settings = test_settings.model_copy(update={"yookassa_webhook_verify_ip": False})
    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: settings

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as money_client:
        await _register(money_client, "blocked@test.com")
        await _login_page(money_client, "blocked@test.com")
        await _block(db_session, await _user(db_session, "blocked@test.com"))

        response = await money_client.post(
            "/api/billing/webhook", json={"event": "payment.unknown_event"}
        )

    assert response.status_code == 200, (
        f"вебхук ответил {response.status_code} при заблокированном плательщике "
        f"— приём уведомлений о состоявшихся платежах остановлен (D-53)"
    )


def test_the_blocking_check_did_not_move_into_the_shared_authenticator():
    """`get_current_user_id` не узнала ни про блокировку, ни про сессию БД.

    ⚠️ ЭТО ЗАПРЕТ, А НЕ ПРЕДПОЧТЕНИЕ, И ОН БЛИЗНЕЦ ЗАПРЕТА ГЕЙТА ДОСТУПА
    (`test_access_gate.py::..._is_left_untouched`), а не его копия: тот
    сторожит `check_access`, этот — `is_blocked`. Лобовая починка блокировки
    выглядит как «сделать в одном месте вместо пяти» и закрывает заодно
    денежный роутер, который решением D-53 обязан остаться открытым.

    Утверждение снимается с ИСХОДНИКА по синтаксическому дереву: вопрос про
    ОТСУТСТВИЕ ветки, а отсутствие проверяется чтением кода, а не запросом.
    """
    tree = ast.parse(DEPENDENCIES_PY.read_text(encoding="utf-8"))
    authenticator = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "get_current_user_id"
    )

    assert "is_blocked" not in ast.unparse(authenticator), (
        "проверка блокировки переехала в зависимость аутентификации — денежный "
        "роутер закрылся вместе с остальными (D-53)"
    )
    assert "db" not in {argument.arg for argument in authenticator.args.args}, (
        "зависимость аутентификации получила сессию БД — она обслуживает и "
        "незащищённые пути, и цена запроса на них ничем не оправдана"
    )


# =============================================================================
# Путь 3 — сбор расписаний к отправке (`collect_due_schedules`)
# =============================================================================
#
# ⚠️ СОБСТВЕННЫЙ ДВИЖОК, А НЕ ФИКСТУРА `db_session`, — приём взят у соседа
# (`tests/test_application/test_access_gate_scheduling.py`). Причина та же:
# сбор расписаний работает с сессией напрямую и ПИШЕТ в неё (`next_run_at`), а
# посев здесь нужен точный — до строки подписки включительно.
#
# ⚠️ ЭТО САМАЯ ДОРОГАЯ ИЗ ТРЁХ ПОВЕРХНОСТЕЙ. Ошибка на входе стоит человеку
# одного экрана, ошибка на JSON-поверхности — обхода авторизации, а ошибка
# ЗДЕСЬ ТИХО ПРЕКРАЩАЕТ РАССЫЛКИ ЖИВЫМ ПЛАТЯЩИМ ЛЮДЯМ: отказ проявится не
# исключением, а отсутствием отправок, которого никто не заметит до жалобы.
# Поэтому смешанная выборка стоит ОТДЕЛЬНЫМ тестом, а не следствием.


@contextlib.asynccontextmanager
async def _scheduler_session():
    """Сессия на своём движке — для посева расписаний и прогона сбора."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    try:
        async with session_factory() as session:
            yield session
    finally:
        await engine.dispose()


@contextlib.contextmanager
def _no_redis():
    """Redis в тестовой среде нет, и вердикт доступа обязан считаться без него.

    Подмена стоит на `_get_redis`, а не на клиенте, по основанию, выписанному в
    `tests/test_application/test_access_gate_scheduling.py`: настоящий
    `from_url` объект СОЗДАЁТ, и тест зависел бы от того, поднят ли Redis на
    машине разработчика.
    """
    settings = MagicMock()
    settings.redis_url = "redis://localhost:6379/0"
    settings.billing_cache_ttl = 60
    with patch("app.services.billing_cache._get_redis", return_value=None):
        with patch("app.services.billing_cache.get_settings", return_value=settings):
            yield


async def _seed_sender(
    session: AsyncSession, email: str, *, blocked: bool = False
) -> User:
    """Пользователь с ЖИВЫМ доступом — под расписание к отправке.

    Доступ живой намеренно: на просроченном отсутствие задач не доказало бы
    ничего — их не было бы и без блокировки.
    """
    user = User(email=email, password_hash="x", name="U", is_blocked=blocked)
    session.add(user)
    await session.commit()

    session.add(
        Subscription(
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=3),
            is_active=True,
        )
    )
    await session.commit()
    return user


async def _seed_due_schedule(session: AsyncSession, user: User) -> Schedule:
    """Расписание, срок которого УЖЕ наступил, со всей живой тройкой под ним."""
    ad = Ad(
        user_id=user.id,
        title="T",
        text="Body",
        images=[],
        status=AD_STATUS_PUBLISHED,
    )
    account = MessengerAccount(
        user_id=user.id, type="tg_user", credentials="sess", status="active"
    )
    session.add_all([ad, account])
    await session.commit()

    group = Group(
        user_id=user.id,
        account_id=account.id,
        messenger_type="telegram",
        group_external_id=f"-100{account.id}",
        name="G",
    )
    session.add(group)
    await session.commit()

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[group.id],
        days_of_week=[0, 1, 2, 3, 4, 5, 6],
        times_of_day=["00:00", "06:00", "12:00", "18:00"],
        is_active=True,
        next_run_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        timezone="UTC",
    )
    session.add(schedule)
    await session.commit()
    return schedule


async def _collect(session: AsyncSession):
    with _no_redis():
        return await collect_due_schedules(
            session,
            now=datetime.now(timezone.utc),
            check_limit=check_access_cached,
        )


@pytest.mark.asyncio
async def test_a_blocked_user_dispatches_nothing_and_keeps_the_schedule():
    """Заблокированный не рассылает — и его расписание ПЕРЕНОСИТСЯ, а не тонет.

    ⚠️ ДВА УТВЕРЖДЕНИЯ, И ВТОРОЕ НЕСУЩЕЕ. Пустой список говорит «не отправили».
    Сдвиг `next_run_at` вперёд говорит второе: момент, оставленный в прошлом,
    при РАЗБЛОКИРОВКЕ выстрелит всеми накопленными слотами сразу — тихой
    рассылкой задним числом в чужие группы. Реализация, отфильтровавшая
    заблокированного в WHERE выборки, прошла бы первое утверждение и провалила
    второе.
    """
    async with _scheduler_session() as session:
        user = await _seed_sender(session, "blocked@test.com", blocked=True)
        schedule = await _seed_due_schedule(session, user)
        was_due_at = schedule.next_run_at

        tasks = await _collect(session)

        assert tasks == [], "заблокированный продолжает рассылать по расписанию"

        await session.refresh(schedule)
        assert schedule.is_active is True, "блокировка выключила расписание"
        # Оба момента через `normalize_utc`: колонка объявлена
        # `DateTime(timezone=True)`, но SQLite отдаёт её NAIVE, а PostgreSQL —
        # aware, и сравнение без приведения падает ровно на одном из диалектов.
        assert normalize_utc(schedule.next_run_at) > normalize_utc(was_due_at), (
            "момент следующего запуска не сдвинут вперёд — при разблокировке "
            "расписание выстрелит всеми накопленными слотами сразу"
        )


@pytest.mark.asyncio
async def test_an_ordinary_user_still_dispatches():
    """Граница сверху: НЕзаблокированный собирает задачи как прежде.

    Без этого утверждения правка, останавливающая рассылку ВСЕМ, прошла бы
    проверку выше — и заметила бы её жалоба, а не суита.
    """
    async with _scheduler_session() as session:
        user = await _seed_sender(session, "ordinary@test.com")
        await _seed_due_schedule(session, user)

        tasks = await _collect(session)

        assert tasks, "незаблокированный перестал рассылать по расписанию"


@pytest.mark.asyncio
async def test_the_blocking_verdict_is_asked_once_per_user():
    """Два расписания одного заблокированного — ОДИН вопрос о блокировке (Ф-5).

    Вердикт обязан лечь в ту же мемоизацию на пользователя, что и вердикт
    доступа. Реализация, спрашивающая блокировку на КАЖДОЕ расписание,
    умножает запросы к базе на число расписаний в такте планировщика.

    Считаются обращения `session.get(User, ...)`, а не строки лога: предмет —
    сколько РАЗ спросили, и наблюдается он на вызове, а не на его следе.
    """
    async with _scheduler_session() as session:
        user = await _seed_sender(session, "blocked@test.com", blocked=True)
        await _seed_due_schedule(session, user)
        await _seed_due_schedule(session, user)

        original_get = AsyncSession.get
        asked: list[object] = []

        async def counting_get(self, entity, ident, *args, **kwargs):
            if entity is User:
                asked.append(ident)
            return await original_get(self, entity, ident, *args, **kwargs)

        with patch.object(AsyncSession, "get", counting_get):
            tasks = await _collect(session)

        assert tasks == []
        assert len(asked) == 1, (
            f"вердикт блокировки спрошен {len(asked)} раз(а) на одного "
            f"пользователя — проверка встала вне мемоизации"
        )


@pytest.mark.asyncio
async def test_blocking_one_user_does_not_touch_the_others():
    """СМЕШАННАЯ ВЫБОРКА: рассылки остальных не задеты (T-06-BL3).

    ⚠️ ОТДЕЛЬНЫЙ ТЕСТ, А НЕ СЛЕДСТВИЕ ДВУХ ПРЕДЫДУЩИХ. Те гоняют выборку, где
    все пользователи одинаковы; здесь заблокированный и незаблокированные
    приходят ОДНИМ списком расписаний — то есть проверяется ровно то, что
    пропуск не выносит цикл целиком и не переносится на соседей по такту.
    Ошибка такого рода останавливает отправки живым платящим людям и
    проявляется отсутствием действия, а не отказом (D-30).
    """
    async with _scheduler_session() as session:
        blocked = await _seed_sender(session, "blocked@test.com", blocked=True)
        first = await _seed_sender(session, "first@test.com")
        second = await _seed_sender(session, "second@test.com")

        await _seed_due_schedule(session, blocked)
        live_ads = {
            (await _seed_due_schedule(session, first)).ad_id,
            (await _seed_due_schedule(session, second)).ad_id,
        }

        tasks = await _collect(session)

        assert {task.ad_id for task in tasks} == live_ads, (
            "смешанная выборка отдала не те задачи: блокировка одного "
            "пользователя задела рассылки остальных"
        )


@pytest.mark.asyncio
async def test_unblocking_returns_the_schedule_to_the_selection():
    """Разблокировка возвращает расписания в выборку без иных действий.

    Критерий 2 фазы требует «заблокировать И РАЗБЛОКИРОВАТЬ». Правка, которая
    закрывает путь необратимо (удалением расписания, снятием `is_active`),
    прошла бы все проверки выше и провалила бы обещание кнопки.
    """
    async with _scheduler_session() as session:
        user = await _seed_sender(session, "blocked@test.com", blocked=True)
        await _seed_due_schedule(session, user)

        assert await _collect(session) == []

        user.is_blocked = False
        await session.commit()

        # Момент сдвинут вперёд первым тактом, поэтому выборка спрашивается на
        # МОМЕНТ ПОСЛЕ него: предмет — вернулось ли расписание в выборку, а не
        # наступил ли уже следующий слот.
        with _no_redis():
            tasks = await collect_due_schedules(
                session,
                now=datetime.now(timezone.utc) + timedelta(days=1),
                check_limit=check_access_cached,
            )

        assert tasks, "разблокировка не вернула расписания в выборку"


@pytest.mark.asyncio
async def test_a_skipped_blocked_user_writes_no_send_log():
    """Пропуск заблокированного ТИХИЙ: записи в журнал отправок не делается.

    Журнал отражает СОВЕРШЁННЫЕ попытки отправки, а пропущенное расписание
    попытки не совершало — прецедент выключенной группы прямой (D-06). Запись
    «не отправлено, потому что заблокирован» превратила бы историю пользователя
    в ленту его блокировки, и по каждому слоту каждого расписания.
    """
    async with _scheduler_session() as session:
        user = await _seed_sender(session, "blocked@test.com", blocked=True)
        await _seed_due_schedule(session, user)

        await _collect(session)

        logs = (await session.execute(select(SendLog))).scalars().all()
        assert logs == [], (
            f"пропуск заблокированного оставил {len(logs)} записей в журнале "
            f"отправок — история показывает попытки, которых не было"
        )


# =============================================================================
# Тумблер блокировки в админке — переехал из `tests/test_admin.py`
# =============================================================================


@pytest.mark.asyncio
async def test_the_admin_toggle_blocks_a_user(client: AsyncClient, db_session):
    """Кнопка в админке ставит признак блокировки на чужую учётную запись.

    Переехала сюда вместе со всем предметом блокировки: половина, оставленная
    в файле админки, снова разложила бы блокировку по файлам — ровно то, из-за
    чего эффекта у кнопки не было целую фазу.
    """
    await _register(client, "admin@test.com")
    resp = await client.post(
        "/api/auth/login", json={"email": "admin@test.com", "password": PASSWORD}
    )
    admin_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    await _register(client, "target@test.com")
    target = await _user(db_session, "target@test.com")

    response = await client.post(
        f"/admin/users/{target.id}/block",
        headers=admin_headers,
        follow_redirects=False,
    )

    assert response.status_code == 302
    await db_session.refresh(target)
    assert target.is_blocked is True, "кнопка админки не поставила признак"


@pytest.mark.asyncio
async def test_the_admin_cannot_block_himself(client: AsyncClient, db_session):
    """Администратор не блокирует себя: иначе админку некому открыть.

    Восстановление после такой блокировки — правка строки в базе руками.
    """
    await _register(client, "admin@test.com")
    resp = await client.post(
        "/api/auth/login", json={"email": "admin@test.com", "password": PASSWORD}
    )
    admin_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    admin = await _user(db_session, "admin@test.com")

    response = await client.post(
        f"/admin/users/{admin.id}/block",
        headers=admin_headers,
        follow_redirects=False,
    )

    assert response.status_code == 302
    await db_session.refresh(admin)
    assert admin.is_blocked is False, "администратор заблокировал сам себя"

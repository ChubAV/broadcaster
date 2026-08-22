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
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_settings
from app.main import create_app
from app.models.user import User

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

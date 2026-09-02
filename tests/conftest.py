import itertools
import json
import shutil
import subprocess
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.database import Base
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.subscription import Subscription
from app.models.user import User


@pytest_asyncio.fixture
async def test_settings():
    return Settings(
        # .env разработчика не должен протекать в тесты: без этого фикстура
        # наследует боевые SMTP/S3-параметры рабочего каталога.
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret-key",
        telegram_api_id=12345,
        telegram_api_hash="test_api_hash",
        wa_bridge_urls=["http://localhost:3000"],
        admin_email="admin@test.com",
        smtp_host="",
        smtp_port=587,
        smtp_user="",
        smtp_password="",
        smtp_from="noreply@test.com",
    )


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session, test_settings):
    app = create_app(settings=test_settings)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: test_settings
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def htmx_client(client):
    """Клиент, приходящий ТАК ЖЕ, как приходит браузер с включённым JavaScript.

    Без этой фикстуры вся суита проверяет путь, которым не идёт НИ ОДИН
    сегодняшний пользователь: слой письма подключён в обоих шеллах, поэтому
    почти каждый запрос продукта несёт признак htmx, а тесты его не несут ни
    разу. Отказ, отвечающий человеку с JavaScript одним способом, а суите
    другим, до этой фикстуры был непроверяем в принципе — и именно в этой щели
    жила невидимость отказа, которую закрывает фаза (FOUND-07).

    ⚠️ ФИКСТУРА ВОЗВРАЩАЕТ ТОТ ЖЕ ОБЪЕКТ КЛИЕНТА, ЧТО И `client`, И ЭТО
    НЕСУЩЕЕ СВОЙСТВО, А НЕ ЭКОНОМИЯ. Благодаря ему она СКЛАДЫВАЕТСЯ с
    `authed_client` / `expired_client` / `admin_client` их совместным запросом
    в сигнатуре теста: cookie, выставленные соседней фикстурой, остаются на
    месте, и «просроченный пользователь, пришедший запросом htmx» пишется одной
    строкой параметров, а не третьей фикстурой на каждое сочетание.

    ⚠️ `follow_redirects=True` ЗДЕСЬ — ЧАСТЬ ПРЕДМЕТА ПРОВЕРКИ (умолчание
    проекта — `False`). Браузер, получивший на запрос htmx ответ 302, следует
    ему НЕЗАМЕТНО и подставляет в область свопа целый документ; человек при
    этом не узнаёт ни о каком отказе. Фикстура воспроизводит именно это
    поведение, поэтому тест, ожидающий 204 с заголовком перехода, не может
    случайно позеленеть на редиректе: редирект придёт к нему кодом 200 и телом
    чужой страницы.

    ⚠️ ИМЯ ЗАГОЛОВКА ЗАПИСАНО ЗДЕСЬ СТРОКОЙ, И ЭТО НЕ ВТОРОЕ ОБЪЯВЛЕНИЕ
    ПРИЗНАКА. Единственность, которую держит фаза, — единственность ЧТЕНИЯ
    признака приложением (`app/pages/htmx.py::is_htmx`); здесь же признак
    ПИШЕТСЯ, и пишущая сторона — не приложение, а клиент: в продукте им
    выступает сам слой письма в браузере, который об этом модуле ничего не
    знает. Импорт константы из приложения связал бы ВЕСЬ файл фикстур с
    модулем страниц ради значения, заданного чужим протоколом и неизменяемого
    нами.
    """
    client.headers["HX-Request"] = "true"
    client.follow_redirects = True
    return client


@pytest_asyncio.fixture
async def auth_headers(client):
    """Register a user and return auth headers."""
    await client.post("/api/auth/register", json={
        "email": "testuser@test.com",
        "password": "testpass123",
        "name": "Test User",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "testuser@test.com",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def authed_client(client, auth_headers):
    """Client with the httpOnly access_token cookie of a regular user.

    Page routes read the cookie, not the Bearer header — auth_headers alone
    does not authorize a page request.
    """
    await client.post(
        "/login",
        data={"email": "testuser@test.com", "password": "testpass123"},
        follow_redirects=False,
    )
    return client


@pytest_asyncio.fixture
async def expired_client(authed_client, db_session):
    """Client of a regular user whose access period has ALREADY expired.

    Критерий 2 фазы 05.1 («по истечении пробного срока доступ прекращается»)
    без этой фикстуры непроверяем: каждый файл заводил бы просроченного
    пользователя своим хелпером, и длина пробного срока разъехалась бы по
    суите — ровно тот класс расхождения, ради которого `TRIAL_DAYS` живёт одной
    константой.

    СРОК СДВИГАЕТСЯ ПРЯМОЙ ПРАВКОЙ СТРОКИ ЧЕРЕЗ ORM, А НЕ МАРШРУТОМ, и это уже
    принятый в этом файле приём (см. объяснение у `seed_group` ниже):
    прикладного входа «состарить подписку» в продукте нет и быть не должно —
    единственный писатель `expires_at` есть подтверждённое уведомление ЮKassa,
    и двигать срок НАЗАД он не умеет.

    Строка подписки берётся ТА ЖЕ, что читает продукт: активная строка
    владельца. Если её нет вовсе, фикстура падает вслух — «пробный срок при
    регистрации не завёлся» есть поломка продукта, и молчаливый пропуск
    превратил бы её в зелёный тест доступа у пользователя вообще без подписки.
    """
    user = (
        await db_session.execute(
            select(User).where(User.email == "testuser@test.com")
        )
    ).scalar_one()

    subscription = (
        await db_session.execute(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    assert subscription is not None, (
        "у только что зарегистрированного пользователя нет активной подписки — "
        "пробный срок при регистрации не завёлся"
    )

    subscription.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    await db_session.commit()
    return authed_client


@pytest_asyncio.fixture
async def comped_client(expired_client, db_session):
    """Клиент пользователя с ВЫДАННЫМ бесплатным доступом и МЁРТВОЙ датой.

    Критерий 5 фазы 05.1 («администратор выдаёт бесплатный ДОСТУП») без этой
    фикстуры непроверяем на трёх поверхностях применения сразу: каждый файл
    заводил бы льготного пользователя своим хелпером, и «мёртвость» даты
    разъехалась бы по суите ровно так же, как разъехалась бы длина пробного
    срока без `expired_client`.

    ⚠️ ФИКСТУРА СТОИТ НА `expired_client`, А НЕ НА `authed_client`, И ЭТО
    ПРЕДМЕТ, А НЕ ЭКОНОМИЯ. Льгота, выданная человеку с ЖИВЫМ сроком, ничего не
    доказывает: доступ у него открыт и без неё, и тест зеленел бы при полностью
    непрочитанном признаке. Утверждение имеет силу только на просроченной
    строке — там вердикт «открыт» не может прийти ниоткуда, кроме признака.

    Признак ставится ПРЯМОЙ ПРАВКОЙ СТРОКИ через ORM, а не админским маршрутом,
    по тому же основанию, что и сдвиг срока у `expired_client`: предмет проверки
    — ПОВЕДЕНИЕ ДОСТУПА при выданной льготе, и прогонять его через ещё один
    маршрут значило бы уронить эти тесты за компанию при поломке админки.
    Сам маршрут тумблера проверяется отдельно (`tests/test_admin.py`).
    """
    user = (
        await db_session.execute(
            select(User).where(User.email == "testuser@test.com")
        )
    ).scalar_one()

    subscription = (
        await db_session.execute(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.is_active.is_(True),
            )
        )
    ).scalar_one()

    subscription.has_free_access = True
    await db_session.commit()
    return expired_client


# --- Посев групп --------------------------------------------------------------
#
# Группа заводится ПРЯМОЙ ВСТАВКОЙ через ORM, а не запросом к прикладному
# маршруту. Прикладного входа создания группы в приложении больше нет: GRP-08
# («добавить группу вручную») снято решением владельца, и вместе с ним удалён
# JSON-маршрут создания группы (`app/routes/groups.py` целиком) — единственный
# вход, который принимал `account_id` от клиента и НЕ проверял владение им
# (D-13, D-14, план 03-07). Единственный источник появления групп в продукте —
# синхронизация с мессенджером; посев здесь воспроизводит ровно её результат.
#
# Хелпер живёт функцией модуля, а не фикстурой: почти все вызывающие — свои
# `_create_group`/`setup_*` тестовых файлов, то есть обычные функции, которым
# фикстуру пришлось бы протаскивать лишним параметром через всю цепочку.
# Импортируется как `from tests.conftest import seed_group`.

_group_external_id_seq = itertools.count(1)


async def seed_group(
    session: AsyncSession,
    account_id: int,
    user_id: int | None = None,
    *,
    name: str | None = None,
    messenger_type: str | None = None,
    group_external_id: str | None = None,
) -> Group:
    """Строка `groups` на указанном аккаунте. Возвращает созданный объект.

    `user_id` и `messenger_type` по умолчанию берутся С АККАУНТА, а не из
    аргументов, и это не экономия печати. Группа, чей владелец или тип канала
    разошёлся с аккаунтом, синхронизацией непроизводима — такую строку в базе
    может оставить только ошибка теста. Значения передаются явно лишь там, где
    расхождение и есть предмет проверки (посев ЧУЖОЙ группы делается локальными
    хелперами соответствующих файлов, не этим).

    Идентификатор возвращённого объекта следует снимать сразу: последующие
    `commit()`/`expire_all()` в проверках сбрасывают загруженные атрибуты, и
    обращение к ним из синхронного кода теста ушло бы в ленивую подгрузку вне
    greenlet-а.
    """
    account = await session.get(MessengerAccount, account_id)
    if account is None:
        raise AssertionError(
            f"seed_group: аккаунта {account_id} нет в базе — "
            "группа не может принадлежать несуществующему аккаунту"
        )

    seq = next(_group_external_id_seq)
    group = Group(
        user_id=account.user_id if user_id is None else user_id,
        account_id=account_id,
        messenger_type=messenger_type or account.type,
        group_external_id=group_external_id or f"-100{account_id:03d}{seq:06d}",
        name=name or f"Группа {seq}",
    )
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return group


@pytest_asyncio.fixture
async def admin_client(client, test_settings):
    """Client with the httpOnly access_token cookie of the admin user.

    check_is_admin compares user.email to settings.admin_email, so the user
    must be registered with exactly that address.
    """
    await client.post("/api/auth/register", json={
        "email": test_settings.admin_email,
        "password": "testpass123",
        "name": "Admin User",
    })
    await client.post(
        "/login",
        data={"email": test_settings.admin_email, "password": "testpass123"},
        follow_redirects=False,
    )
    return client


# --- Области уведомления шелла ------------------------------------------------
#
# ⚠️ ХЕЛПЕР ЖИВЁТ ЗДЕСЬ, А НЕ КОПИЕЙ В КАЖДОМ ФАЙЛЕ, И ЭТО НЕ УДОБСТВО.
# Областей уведомления на проект две, разметка у них одна
# (`includes/notice_area.html`), и разбирать её будут все, кто проверяет исход
# действия. Вторая копия разбора разошлась бы с первой ровно на том экране, про
# который забыли, — тем же способом, каким расходились три частных реестра слов
# до плана 08-06.
#
# Импортируется как `from tests.conftest import notice_areas`.

POLITE_AREA_ANCHOR = 'id="notice"'
ASSERTIVE_AREA_ANCHOR = 'id="notice-alert"'


def notice_areas(html: str) -> str:
    """Содержимое ОБЕИХ областей уведомления шелла — и ничего кроме него.

    ⚠️ ИЗВЛЕЧЕНИЕ, А НЕ ПОИСК ПО ВСЕЙ СТРАНИЦЕ, И ЭТО НЕ ПЕДАНТИЗМ. Шелл
    доставляет в КАЖДЫЙ документ две СКРЫТЫЕ заготовки плашки — отказа сервера
    и обрыва связи (`includes/htmx_error_banner.html`), — и класс настойчивого
    варианта присутствует в них ВСЕГДА. Проверка «плашка нарисована» по всему
    документу поэтому зеленела бы на пустом экране: она утверждала бы не то, что
    человеку что-то сказано, а то, что шелл собран.

    Границы области считаются ПО ВЛОЖЕННОСТИ `div`, а не по первому `</div>`:
    плашка внутри области сама является элементом, и наивный поиск обрезал бы
    содержимое ровно по её закрытию, то есть терял бы её целиком.
    """
    parts = []
    for anchor in (POLITE_AREA_ANCHOR, ASSERTIVE_AREA_ANCHOR):
        start = html.index(anchor)
        cursor = html.index(">", start) + 1
        depth, scan = 1, cursor
        while depth:
            nxt_open = html.find("<div", scan)
            nxt_close = html.find("</div>", scan)
            assert nxt_close != -1, f"область {anchor} не закрыта"
            if nxt_open != -1 and nxt_open < nxt_close:
                depth += 1
                scan = nxt_open + 4
            else:
                depth -= 1
                scan = nxt_close + 6
        parts.append(html[cursor : scan - 6])
    return "\n".join(parts)


# --- Запуск исходника JS в интерпретаторе --------------------------------------
#
# ⚠️ ЗАПУСК ЖИВЁТ ЗДЕСЬ В ЕДИНСТВЕННОМ ЭКЗЕМПЛЯРЕ, И ЭТО НЕ ПЕРЕКЛАДЫВАНИЕ
# СТРОК. Правил, пересекающих линию «суита не исполняет ни строчки JS», в
# проекте уже два предмета: жизненный цикл панели подтверждения
# (`tests/test_templates/test_components.py`) и число регистраций обработчиков
# общего канала отказа (`tests/test_pages/test_shell.py`). Второе ОПРЕДЕЛЕНИЕ
# одного механизма — ровно то, что доктрина единственного источника проекта
# запрещает прямым текстом (абзац о перечне стоков в `test_shell.py`: «второго
# ОПРЕДЕЛЕНИЯ одного запрета в проекте не заводится»). Две копии запуска
# разошлись бы молча — в разборе вердикта, в таймауте или в том, что одна из
# них однажды получила бы `pytest.skip`.
#
# ⚠️ ЭТО ФУНКЦИЯ МОДУЛЯ, А НЕ ФИКСТУРА, И ВЫБОР НАЗВАН. Фикстура потребовала бы
# параметра у каждого правила и связала бы запуск интерпретатора с жизненным
# циклом теста, которого у него нет: у подпроцесса нет ни подготовки, ни
# уборки, ни разделяемого состояния.
#
# Импортируется как `from tests.conftest import run_node_script`.

# Интерпретатор JS НОВОЙ ЗАВИСИМОСТЬЮ НЕ ЯВЛЯЕТСЯ: на нём собран `wa_worker/`,
# и `justfile` несёт его рецепты (`wa-worker-build`, `wa-workers`).
NODE_BIN = "node"

NODE_SCRIPT_TIMEOUT = 60


def run_node_script(source: str) -> dict:
    """Исполнить поданный исходник JS и разобрать его вердикт.

    Вердикт — ПОСЛЕДНЯЯ строка стандартного вывода, разобранная как JSON.
    Последняя, а не весь вывод: гарнир вправе печатать по дороге диагностику, и
    правило, читающее вывод целиком, разъехалось бы с ним при первой же
    отладочной строке.

    ⚠️ ОТСУТСТВИЕ ИНТЕРПРЕТАТОРА РОНЯЕТ ПРАВИЛО ГРОМКО, А НЕ ПРОПУСКАЕТ ЕГО.
    ``pytest.skip`` здесь не применяется НИ ПРИ КАКОЙ причине: пропущенное
    правило неотличимо от зелёного, и фаза оплатила этот класс однажды (WARN-4
    первого круга Фазы 9). Ненулевой код подпроцесса роняет прогон по той же
    причине — вместе со стандартным потоком ошибок, иначе отказ гарнира
    неотличим от отказа предмета.
    """
    if shutil.which(NODE_BIN) is None:
        pytest.fail(
            f"интерпретатор JS `{NODE_BIN}` не найден в PATH, и правило, "
            "исполняющее исходник, исполнить нечем. Пропуск здесь запрещён: "
            "пропущенное правило неотличимо от зелёного. Интерпретатор в "
            "проекте уже есть — на нём собран wa_worker/, рецепты justfile: "
            "wa-worker-build, wa-workers"
        )

    proc = subprocess.run(
        [NODE_BIN, "-e", source],
        capture_output=True,
        text=True,
        timeout=NODE_SCRIPT_TIMEOUT,
    )
    if proc.returncode != 0:
        pytest.fail(
            f"гарнир JS вернул код {proc.returncode}; вывод ошибки:\n"
            f"{proc.stderr.strip()}"
        )

    lines = [line for line in proc.stdout.strip().splitlines() if line.strip()]
    if not lines:
        pytest.fail(
            "гарнир JS не напечатал ни одной строки — вердикта нет, и разбирать "
            f"нечего; вывод ошибки:\n{proc.stderr.strip()}"
        )
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:  # pragma: no cover — диагностический путь
        pytest.fail(
            "гарнир JS не вернул вердикт разбираемой строкой; получено: "
            f"{lines[-1]!r}"
        )

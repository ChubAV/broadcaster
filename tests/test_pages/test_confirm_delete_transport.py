"""ПАРЫ ТРАНСПОРТОВ ВСЕХ МАРШРУТОВ, СТОЯЩИХ ЗА ПАНЕЛЬЮ ПОДТВЕРЖДЕНИЯ (FORM-06).

ПОЧЕМУ ОДИН МОДУЛЬ, А НЕ ВОСЕМЬ ФУНКЦИЙ В ВОСЬМИ ФАЙЛАХ. Свойство здесь ОДНО —
транспорт подтверждённого необратимого действия, — а маршрутов, которые им
обладают, восемь, и живут они в пяти разных модулях страничного слоя. Восемь
отдельных функций, разложенных по файлам своих разделов, МОЛЧАЛИ БЫ о девятом:
маршрут, добавленный будущей фазой за панелью подтверждения, не уронил бы ни
одной из них, потому что своей функции у него ещё нет. Параметризованный обход
превращает это в КРАСНОЕ: перечень маршрутов сличается со своим числом, и
маршрут, исчезнувший из обхода или не попавший в него, виден сразу.

Форма прямо наследует критерий 4 Фазы 11 («пары параметризованным обходом, а не
320 функций») и идиому счёта числом D-13 Фазы 8: каждый гейт утверждает размер
множества, обойдённого его собственным обходом.

⚠️ ДВЕ ОСИ ОБХОДА И ДВА ЧИСЛА — ЧИТАТЬ ДО ПРАВКИ ПЕРЕЧНЯ.

| Ось | Что считает | Константа |
|---|---|---|
| МАРШРУТЫ | записи перечня; ОДНА ЗАПИСЬ = ОДИН МАРШРУТ | `CONFIRMED_DELETE_ROUTES_DECLARED` |
| СЛУЧАИ ОБХОДА | пары «маршрут × ожидаемый исход» | `CONFIRMED_DELETE_OUTCOME_CASES_DECLARED` |

Маршрут, выдающий четыре кода исхода, даёт ЧЕТЫРЕ СЛУЧАЯ ОБХОДА и остаётся ОДНОЙ
записью перечня: коды живут ПОЛЕМ записи, а развёртывание происходит на уровне
параметризации. Два числа считают РАЗНЫЕ МНОЖЕСТВА, и привести их к согласию
правкой одного НЕЛЬЗЯ — приведи первое к числу случаев, и «восемь маршрутов»
перестанет быть проверяемым; приведи второе к числу маршрутов, и потерянный код
исхода пройдёт молча. Идиома у проекта своя и записана прямо в коде
(`MODAL_CONSUMERS` против `MODAL_IMPORTERS` в
`tests/test_templates/test_components.py`: «два счёта РАЗНЫХ множеств, приводить
их к согласию правкой одного нельзя»).

⚠️ ОБЕ ПОЛОВИНЫ ПАРЫ УТВЕРЖДАЮТСЯ КАЖДЫМ СЛУЧАЕМ, И РАЗЛИЧЕНИЕ «ПРИШЁЛ ЗАГОЛОВОК
ПЕРЕХОДА» / «В ТЕЛЕ НЕТ ДОКУМЕНТА» — НЕСУЩЕЕ. Одиночное утверждение о
перенаправлении зеленело бы ровно в том состоянии продукта, которое фаза и
чинит: панель шлёт запрос через слой письма, обработчик отвечает 302, слой письма
идёт по нему ПРОЗРАЧНО и выбрасывает полученный документ — человек видит открытую
панель и тишину. Поэтому половина htmx приходит с `follow_redirects=True`: 302
вернулся бы ей кодом 200 и телом чужой страницы, и утверждение о 204 позеленеть
не может.

⚠️ ЧУЖОЙ И НЕСУЩЕСТВУЮЩИЙ ИДЕНТИФИКАТОР И ВЕТКА «НЕТ СЕССИИ» ИДУТ ОТДЕЛЬНЫМИ
УТВЕРЖДЕНИЯМИ И В СЧЁТ ИСХОДОВ НЕ ВХОДЯТ. Они свойство ТРАНСПОРТА, а не исход
действия: попади они в список исходов, оба числа перестали бы называть то, что
называют, — «сколько кодов исхода выдаёт маршрут» превратилось бы в «сколько
проверок мы написали».

⚠️ ФИКСТУРА `htmx_client` ЗДЕСЬ НЕ ЗАПРАШИВАЕТСЯ, И ЭТО ЗАПИСАННЫЙ ОПЫТ ПЛАНА
10-01, А НЕ ВКУС. Она ставит признак на ОБЩИЙ объект клиента; запрошенная рядом с
половиной деградации, она пометила бы и тот запрос, который обязан прийти БЕЗ
признака, и половина деградации молча превратилась бы во вторую половину htmx.
Признак ставится в самом обходе, ровно на один запрос из двух.
"""
import contextlib
import itertools
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Awaitable, Callable
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User
from app.pages import history as history_module
from app.pages import notices
from app.services.ops_state import (
    DROP_MISSING,
    DROP_REMOVED,
    DROP_UNAVAILABLE,
    queue_key,
)

# ⚠️ ДВОЙНИКИ И ПОСЕВ ВВОЗЯТСЯ, А НЕ ПЕРЕПИСЫВАЮТСЯ. Двойник очереди держит
# списки по-настоящему, а посев записи журнала заводит целую тройку сущностей;
# вторая копия любого из них разошлась бы с первой молча — ровно тот класс
# расхождения, из-за которого в проекте единственный источник у запуска
# интерпретатора JS и у разбора областей уведомления.
from tests.test_pages.test_admin_panel import _FakeQueuePageRedis, _queue_task
from tests.test_pages.test_editor_schedules import _seed_schedule
from tests.test_pages.test_history_retry import _retry_env, _seed_log, _seed_retryable

PASSWORD = "testpass123"

# Личности обхода. Имя пользователя совпадает с тем, которое заводит фикстура
# `authed_client`, а адрес администратора — с настройкой `admin_email`
# тестового окружения: админство в продукте есть совпадение адреса с ней.
USER_EMAIL = "testuser@test.com"
FOREIGN_EMAIL = "stranger@test.com"

# Признак запроса от слоя письма. Литерал стоит ЗДЕСЬ, а не ввозится из
# приложения, по тому основанию, которое выписано у фикстуры `htmx_client`:
# единственность, которую держит веха, — единственность ЧТЕНИЯ признака
# приложением; здесь признак ПИШЕТСЯ, и пишущая сторона — клиент.
HTMX_HEADERS = {"HX-Request": "true"}

DOCUMENT_MARK = "<!DOCTYPE"


# =============================================================================
# Форма записи перечня
# =============================================================================


@dataclass
class _Arranged:
    """Подготовленный случай: адрес, тело формы и подстановки адреса приземления.

    `context` — ФАБРИКА менеджера подмен, нужных ровно этому случаю (очередь,
    менеджер контейнеров, гейт доступа). Именно фабрика, а не готовый менеджер:
    менеджер, собранный декоратором `contextmanager`, ОДНОРАЗОВЫЙ, а половин у
    пары две — второе вхождение в тот же объект уронило бы обход по причине, не
    имеющей отношения к его предмету. У случая без подмен фабрика отдаёт пустой
    менеджер: ветка «если подмены есть» в обходе означала бы, что половина
    случаев идёт другим путём.
    """

    url: str
    data: dict[str, str] = field(default_factory=dict)
    context: Callable[[], object] = contextlib.nullcontext
    landing_args: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class _Outcome:
    """ОДИН ожидаемый исход маршрута — своё состояние данных и свой адрес.

    ⚠️ ИСХОД НЕ ЯВЛЯЕТСЯ ЗАПИСЬЮ ПЕРЕЧНЯ. Он поле записи, и разведение сделано
    затем, чтобы длина перечня осталась числом МАРШРУТОВ: правило числа маршрутов
    сличает `len()` перечня со своей константой, и подмешивание кодов исхода в
    записи сделало бы это сличение неисполнимым.
    """

    name: str
    arrange: Callable[..., Awaitable[_Arranged]]
    landing: str
    outcome_key: str | None = None
    outcome_code: str | None = None

    def expected_landing(self, arranged: _Arranged) -> str:
        """Адрес приземления ПОСИМВОЛЬНО — тот же на обоих транспортах."""
        address = self.landing.format(**arranged.landing_args)
        if self.outcome_code is None:
            return address
        separator = "&" if "?" in address else "?"
        return f"{address}{separator}{self.outcome_key}={self.outcome_code}"


@dataclass(frozen=True)
class _Route:
    """ОДНА запись перечня = ОДИН маршрут подтверждения."""

    key: str
    name: str
    identity: str
    htmx_form: str
    outcomes: tuple[_Outcome, ...]
    # Отдельные утверждения обхода, В СЧЁТ ИСХОДОВ НЕ ВХОДЯЩИЕ.
    missing_identifier: Callable[..., Awaitable[_Arranged]] | None = None
    missing_identifier_landing: str | None = None
    foreign_owner: Callable[..., Awaitable[tuple[_Arranged, object]]] | None = None
    session_landing: str | None = None

    @property
    def handler(self) -> str:
        return self.key.split("::", 1)[1]


# Ожидаемая форма ответа на транспорте htmx.
LOCATION = "ожидается 204 и заголовок перехода"
FRAGMENT = "ожидается 200 и фрагмент"


# Теги, у которых закрывающей половины нет: без них счётчик вложенности уехал бы
# вниз на первом же `<br>` и «верхний уровень» перестал бы быть верхним.
_VOID_TAGS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
     "param", "source", "track", "wbr"}
)


class _OobNodes(HTMLParser):
    """Разбор РАЗМЕТКИ ответа: идентификаторы внеполосных узлов ВЕРХНЕГО уровня.

    ⚠️ РАЗБОР, А НЕ ПОИСК ПОДСТРОКИ. Сличение ответов по вхождению текста
    зеленело бы на любом совпадении: строка `sched-7` встречается и в теле
    линейки счётчика, и в чужой разметке, приехавшей вложенным включением.
    Предмет сличения — именно УЗЕЛ, несущий признак внеполосной подмены, и
    именно на верхнем уровне ответа: вложенный узел с тем же признаком был бы
    ДРУГИМ свойством (рантайм применяет внеполосные узлы верхнего уровня), и
    подмешивание его в множество сделало бы отказ неразличимым.

    ⚠️ ИДЕНТИФИКАТОР УЗЛА — ЭТО `id`, А ГДЕ ЕГО НЕТ, ЦЕЛЬ ИЗ ЗНАЧЕНИЯ ПРИЗНАКА.
    Узел счётчика адресует цель селектором внутри `hx-swap-oob`
    (`innerHTML:#sched-count`) и собственного `id` не несёт вовсе; выбросив его,
    множество перестало бы называть все три узла ответа. Узел, у которого нет ни
    того, ни другого, НЕ пропускается молча — он попадает в множество особой
    записью, потому что молчаливый пропуск и есть тот отказ, от которого стои́т
    весь этот разбор.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.ids: set[str] = set()

    def _record(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if "hx-swap-oob" not in attributes:
            return
        node_id = attributes.get("id")
        if node_id:
            self.ids.add(node_id)
            return
        value = attributes.get("hx-swap-oob") or ""
        if ":" in value:
            self.ids.add(value.split(":", 1)[1])
            return
        self.ids.add(f"<{tag} без идентификатора: hx-swap-oob={value!r}>")

    def handle_starttag(self, tag, attrs):
        if self.depth == 0:
            self._record(tag, attrs)
        if tag not in _VOID_TAGS:
            self.depth += 1

    def handle_startendtag(self, tag, attrs):
        if self.depth == 0:
            self._record(tag, attrs)

    def handle_endtag(self, tag):
        if tag not in _VOID_TAGS:
            self.depth = max(0, self.depth - 1)


def _oob_node_ids(body: str) -> set[str]:
    """МНОЖЕСТВО идентификаторов внеполосных узлов верхнего уровня ответа.

    ⚠️ МНОЖЕСТВО, А НЕ СПИСОК, И ЭТО РЕШЕНИЕ, А НЕ УДОБСТВО. Порядок внеполосных
    узлов в ответе НЕ ОБЪЯВЛЕН свойством контракта ни одной записью проекта —
    ни шапкой шаблона ответа, ни докстрингом обработчика, — и утверждать его
    значило бы завести контракт, которого нет, а потом чинить перестановку строк
    шаблона как регресс.
    """
    parser = _OobNodes()
    parser.feed(body)
    parser.close()
    return parser.ids


# =============================================================================
# Личности обхода
# =============================================================================


async def _sign_in(client: AsyncClient, email: str, name: str) -> None:
    """Регистрация прикладным входом и вход по cookie.

    ⚠️ ЛИЧНОСТЬ ВЫБИРАЕТСЯ ПАРАМЕТРОМ, А НЕ ФИКСТУРОЙ, И ЭТО НЕ ОБХОД ФИКСТУР.
    `authed_client` и `admin_client` возвращают ОДИН И ТОТ ЖЕ объект клиента и
    оба выполняют вход; запрошенные вместе — а параметризованному обходу нужны
    обе личности — они оставили бы в клиенте cookie того, чья фикстура
    инициализировалась последней, то есть выбор личности зависел бы от порядка
    аргументов теста. Здесь личность выбирает ЗАПИСЬ МАРШРУТА.

    Регистрация идёт прикладным входом, а не ORM: без строки подписки соседний
    гейт доступа отказал бы 402 раньше всего, что здесь проверяется, и обход
    краснел бы по ЧУЖОЙ причине.
    """
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "name": name},
    )
    response = await client.post(
        "/login",
        data={"email": email, "password": PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 302, (
        f"вход под {email} не состоялся ({response.status_code}) — обход "
        "проверял бы ответ неаутентифицированному запросу"
    )


async def _identify(client: AsyncClient, identity: str, settings) -> None:
    if identity == "admin":
        await _sign_in(client, settings.admin_email, "Администратор")
        return
    await _sign_in(client, USER_EMAIL, "Пользователь")


async def _user_of(db: AsyncSession, email: str) -> User:
    return (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one()


async def _current_user(db: AsyncSession, identity: str, settings) -> User:
    return await _user_of(
        db, settings.admin_email if identity == "admin" else USER_EMAIL
    )


async def _foreign_user(db: AsyncSession) -> User:
    existing = (
        await db.execute(select(User).where(User.email == FOREIGN_EMAIL))
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    stranger = User(
        email=FOREIGN_EMAIL, password_hash="x", name="Чужой", timezone="UTC"
    )
    db.add(stranger)
    await db.commit()
    await db.refresh(stranger)
    return stranger


# =============================================================================
# Посев: удаление аккаунта мессенджера
# =============================================================================


async def _seed_account(db: AsyncSession, user_id: int, *, account_type: str = "wa"):
    account = MessengerAccount(
        user_id=user_id, type=account_type, credentials="{}", status="active"
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def _arrange_account_delete(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    account = await _seed_account(db, user.id)
    return _Arranged(url=f"/accounts/{account.id}/delete")


async def _arrange_missing_account(client, db, settings, identity) -> _Arranged:
    return _Arranged(url="/accounts/987654/delete")


async def _arrange_foreign_account(client, db, settings, identity):
    stranger = await _foreign_user(db)
    account = await _seed_account(db, stranger.id)
    return _Arranged(url=f"/accounts/{account.id}/delete"), (
        MessengerAccount,
        account.id,
    )


# =============================================================================
# Посев: удаление объявления
# =============================================================================


async def _seed_ad(db: AsyncSession, user_id: int) -> Ad:
    ad = Ad(user_id=user_id, title="Летняя распродажа", text="Скидки", images=[])
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


async def _arrange_ad_delete(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad = await _seed_ad(db, user.id)
    return _Arranged(url=f"/ads/{ad.id}/delete")


async def _arrange_missing_ad(client, db, settings, identity) -> _Arranged:
    return _Arranged(url="/ads/987654/delete")


async def _arrange_foreign_ad(client, db, settings, identity):
    stranger = await _foreign_user(db)
    ad = await _seed_ad(db, stranger.id)
    return _Arranged(url=f"/ads/{ad.id}/delete"), (Ad, ad.id)


# =============================================================================
# Посев: повтор отправки из журнала — ЧЕТЫРЕ ДЕЙСТВУЮЩИХ КОДА ИСХОДА
# =============================================================================
#
# ⚠️ РЕЕСТР УДЕРЖАНИЯ ПОВТОРА ЧИСТИТСЯ ФИКСТУРОЙ НИЖЕ, И ЭТО УСЛОВИЕ
# ОСМЫСЛЕННОСТИ ОБХОДА, А НЕ ГИГИЕНА. Реестр объявлен на уровне модуля раздела и
# живёт весь прогон, а база поднимается на каждый тест заново — «запись №1» в
# двадцати тестах это ОДИН ключ и ДВАДЦАТЬ разных записей. Без чистки первый же
# успешный случай армировал бы ключ на весь остаток прогона, и следующий случай
# получал бы код «повтор занят» по причине, не видной из его собственного текста.


@pytest.fixture(autouse=True)
def _isolate_retry_registry():
    history_module._RETRY_IN_FLIGHT.clear()
    yield
    history_module._RETRY_IN_FLIGHT.clear()


async def _arrange_retry_queued(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    log = await _seed_retryable(db, user.id)
    return _Arranged(
        url=f"/history/{log.id}/retry", context=lambda: _retry_env(allowed=True)
    )


async def _arrange_retry_busy(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    log = await _seed_retryable(db, user.id)
    # Удержание армируется ДО запроса той же функцией, которой его армирует
    # обработчик: второе определение «занято» разошлось бы с первым молча.
    assert history_module._claim_retry_slot(log.id), (
        "удержание не армировалось — случай «повтор занят» проверял бы свободный "
        "слот и зеленел бы на коде успеха"
    )
    return _Arranged(
        url=f"/history/{log.id}/retry", context=lambda: _retry_env(allowed=True)
    )


async def _arrange_retry_gone(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    # Запись без целой тройки: объявления и группы, на которые она ссылается,
    # нет вовсе — предпроверка целости отвечает «повторить нечего».
    log = await _seed_log(db, user.id, ad_id=None, group_id=None)
    return _Arranged(
        url=f"/history/{log.id}/retry", context=lambda: _retry_env(allowed=True)
    )


async def _arrange_retry_access_closed(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    log = await _seed_retryable(db, user.id)
    return _Arranged(
        url=f"/history/{log.id}/retry", context=lambda: _retry_env(allowed=False)
    )


async def _arrange_missing_log(client, db, settings, identity) -> _Arranged:
    return _Arranged(
        url="/history/987654/retry", context=lambda: _retry_env(allowed=True)
    )


# =============================================================================
# Посев: перезапуск контейнера воркера
# =============================================================================

WA_CONTAINER = "app.services.wa_container_manager.start_container"


async def _arrange_restart_success(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    account = await _seed_account(db, user.id, account_type="wa")
    return _Arranged(
        url=f"/admin/workers/{account.id}/restart",
        context=lambda: patch(WA_CONTAINER, return_value="http://x"),
    )


async def _arrange_restart_no_container(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    # У telegram-аккаунта своего контейнера нет вовсе — молчаливый успех здесь
    # был бы хуже отказа.
    account = await _seed_account(db, user.id, account_type="tg_user")
    return _Arranged(url=f"/admin/workers/{account.id}/restart")


async def _arrange_restart_failed(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    account = await _seed_account(db, user.id, account_type="wa")
    return _Arranged(
        url=f"/admin/workers/{account.id}/restart",
        context=lambda: patch(WA_CONTAINER, side_effect=RuntimeError("демон молчит")),
    )


async def _arrange_missing_worker(client, db, settings, identity) -> _Arranged:
    return _Arranged(url="/admin/workers/987654/restart")


# =============================================================================
# Посев: снятие задачи из очереди отправки
# =============================================================================

QUEUE_REDIS = "app.services.ops_state._get_redis"
DROPPED_TASK = "drop-me"


def _queue_with(account_id: int, *tasks: str):
    """Фабрика подмены клиента очереди со списками, которые меняются взаправду."""
    key = queue_key("wa", account_id)
    return lambda: patch(
        QUEUE_REDIS,
        return_value=_FakeQueuePageRedis(
            {key: [_queue_task(task) for task in tasks]}
        ),
    )


async def _arrange_drop_removed(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    account = await _seed_account(db, user.id, account_type="wa")
    return _Arranged(
        url=f"/admin/queue/{account.id}/drop",
        data={"task_id": DROPPED_TASK},
        context=_queue_with(account.id, "keep-me", DROPPED_TASK),
    )


async def _arrange_drop_missing(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    account = await _seed_account(db, user.id, account_type="wa")
    # Задача ушла из очереди сама, пока администратор читал экран.
    return _Arranged(
        url=f"/admin/queue/{account.id}/drop",
        data={"task_id": DROPPED_TASK},
        context=_queue_with(account.id, "keep-me"),
    )


async def _arrange_drop_unavailable(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    account = await _seed_account(db, user.id, account_type="wa")
    # Очередь хранится ТОЛЬКО в Redis: без него снимать нечего и негде.
    return _Arranged(
        url=f"/admin/queue/{account.id}/drop",
        data={"task_id": DROPPED_TASK},
        context=lambda: patch(QUEUE_REDIS, return_value=None),
    )


async def _arrange_drop_unknown_account(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    account = await _seed_account(db, user.id, account_type="tg_user")
    return _Arranged(
        url=f"/admin/queue/{account.id}/drop", data={"task_id": DROPPED_TASK}
    )


async def _arrange_missing_queue_account(client, db, settings, identity) -> _Arranged:
    return _Arranged(url="/admin/queue/987654/drop", data={"task_id": DROPPED_TASK})


# =============================================================================
# Посев: удаление пользователя из его карточки
# =============================================================================

_victim_sequence = itertools.count(1)


async def _seed_victim(db: AsyncSession) -> User:
    """Пользователь, которого удаляют. Адрес у каждого свой — и это предмет.

    Обе половины пары удаляют СВОЮ строку; общий адрес означал бы, что вторая
    половина заводит удалённого заново, и уцелевшая после первой половины строка
    прошла бы незамеченной.
    """
    victim = User(
        email=f"victim{next(_victim_sequence)}@test.com",
        password_hash="x",
        name="Удаляемый",
        timezone="UTC",
    )
    db.add(victim)
    await db.commit()
    await db.refresh(victim)
    return victim


async def _arrange_delete_user(client, db, settings, identity) -> _Arranged:
    victim = await _seed_victim(db)
    return _Arranged(url=f"/admin/users/{victim.id}/delete")


async def _arrange_delete_self(client, db, settings, identity) -> _Arranged:
    admin = await _current_user(db, identity, settings)
    return _Arranged(
        url=f"/admin/users/{admin.id}/delete", landing_args={"user_id": admin.id}
    )


async def _arrange_missing_user(client, db, settings, identity) -> _Arranged:
    return _Arranged(url="/admin/users/987654/delete")


# =============================================================================
# Посев: вход администратора под личностью пользователя
# =============================================================================

_impersonated_sequence = itertools.count(1)


async def _seed_impersonation_target(db: AsyncSession) -> User:
    target = User(
        email=f"target{next(_impersonated_sequence)}@test.com",
        password_hash="x",
        name="Целевой",
        timezone="UTC",
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return target


async def _arrange_impersonate(client, db, settings, identity) -> _Arranged:
    target = await _seed_impersonation_target(db)
    return _Arranged(url=f"/admin/users/{target.id}/impersonate")


async def _arrange_impersonate_self(client, db, settings, identity) -> _Arranged:
    admin = await _current_user(db, identity, settings)
    return _Arranged(
        url=f"/admin/users/{admin.id}/impersonate", landing_args={"user_id": admin.id}
    )


async def _arrange_missing_impersonation_target(
    client, db, settings, identity
) -> _Arranged:
    return _Arranged(url="/admin/users/987654/impersonate")


# =============================================================================
# Посев: удаление расписания из редактора объявления — ЕДИНСТВЕННЫЙ ФРАГМЕНТНЫЙ
#
# ⚠️ ЭТА ЗАПИСЬ НЕ ПРАВИТ НИ ОДНОГО ОБРАБОТЧИКА: маршрут переведён планом 10-01.
# Она включает единственный фрагментный путь фазы в ОБЩИЙ обход, чтобы число
# маршрутов подтверждения было ПОЛНЫМ. Перечень, накрывающий семь из восьми,
# молчал бы о восьмом ровно так же, как молчали бы восемь отдельных функций, —
# то есть терял бы ровно то свойство, ради которого обход и заведён.
# =============================================================================


async def _arrange_editor_schedule_delete(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad = await _seed_ad(db, user.id)
    account = await _seed_account(db, user.id)
    schedule = await _seed_schedule(db, ad.id, account.id)
    # Второе расписание оставляет экран НЕПУСТЫМ: на последнем маршрут уходит в
    # ветку перехода (D-04), и фрагмента у него не было бы вовсе.
    await _seed_schedule(db, ad.id, account.id)
    return _Arranged(
        url=f"/schedules/{schedule.id}/delete",
        data={"return_to": "editor", "ad_id": str(ad.id)},
        landing_args={"ad_id": ad.id},
    )


# =============================================================================
# ПЕРЕЧЕНЬ МАРШРУТОВ ПОДТВЕРЖДЕНИЯ — ОДНА ЗАПИСЬ НА МАРШРУТ
# =============================================================================
#
# Ключ записи совпадает с формой ключа перечня отставания
# (`tests/test_pages/test_htmx_gates.py`), и это сцепка, а не совпадение: там
# маршрут ЧИСЛИТСЯ переведённым, здесь — ПРОВЕРЯЕТСЯ обеими половинами пары.

CONFIRMED_DELETE_ROUTES: tuple[_Route, ...] = (
    _Route(
        key="app/pages/accounts.py::accounts_delete",
        name="удаление аккаунта мессенджера",
        identity="user",
        htmx_form=LOCATION,
        outcomes=(
            _Outcome(
                name="успех",
                arrange=_arrange_account_delete,
                landing="/accounts",
            ),
        ),
        missing_identifier=_arrange_missing_account,
        missing_identifier_landing="/accounts",
        foreign_owner=_arrange_foreign_account,
        session_landing="/login",
    ),
    _Route(
        key="app/pages/ads.py::ads_delete",
        name="удаление объявления",
        identity="user",
        htmx_form=LOCATION,
        outcomes=(
            _Outcome(name="успех", arrange=_arrange_ad_delete, landing="/ads"),
        ),
        missing_identifier=_arrange_missing_ad,
        missing_identifier_landing="/ads",
        foreign_owner=_arrange_foreign_ad,
        session_landing="/login",
    ),
    _Route(
        key="app/pages/history.py::history_retry",
        name="повтор отправки из журнала",
        identity="user",
        htmx_form=LOCATION,
        # ⚠️ ЧЕТЫРЕ ИСХОДА — ОДНА ЗАПИСЬ. Маршрут выдаёт четыре ДЕЙСТВУЮЩИХ кода
        # реестра, и каждый обязан быть проверен на ОБОИХ транспортах: пара,
        # написанная только на успехе, молчала бы о трёх отказных ветках, где
        # человек как раз и остаётся без ответа.
        outcomes=(
            _Outcome(
                name="повтор-поставлен-в-очередь",
                arrange=_arrange_retry_queued,
                landing="/history",
                outcome_key="notice",
                outcome_code=notices.RETRY_QUEUED,
            ),
            _Outcome(
                name="повтор-занят",
                arrange=_arrange_retry_busy,
                landing="/history",
                outcome_key="notice",
                outcome_code=notices.RETRY_BUSY,
            ),
            _Outcome(
                name="повтор-невозможен",
                arrange=_arrange_retry_gone,
                landing="/history",
                outcome_key="notice",
                outcome_code=notices.RETRY_GONE,
            ),
            _Outcome(
                name="доступ-закрыт",
                arrange=_arrange_retry_access_closed,
                landing="/history",
                outcome_key="notice",
                outcome_code=notices.RETRY_ACCESS_CLOSED,
            ),
        ),
        missing_identifier=_arrange_missing_log,
        missing_identifier_landing="/history",
        session_landing="/login",
    ),
    _Route(
        key="app/pages/admin.py::admin_restart_worker",
        name="перезапуск контейнера воркера",
        identity="admin",
        htmx_form=LOCATION,
        outcomes=(
            _Outcome(
                name="успех",
                arrange=_arrange_restart_success,
                landing="/admin/workers",
            ),
            _Outcome(
                name="контейнера-нет",
                arrange=_arrange_restart_no_container,
                landing="/admin/workers",
                outcome_key="notice",
                outcome_code=notices.WORKER_NO_CONTAINER,
            ),
            _Outcome(
                name="перезапуск-не-удался",
                arrange=_arrange_restart_failed,
                landing="/admin/workers",
                outcome_key="notice",
                outcome_code=notices.WORKER_RESTART_FAILED,
            ),
        ),
        missing_identifier=_arrange_missing_worker,
        missing_identifier_landing="/admin/workers",
    ),
    _Route(
        key="app/pages/admin.py::admin_drop_task",
        name="снятие задачи из очереди отправки",
        identity="admin",
        htmx_form=LOCATION,
        # ⚠️ КЛЮЧ ИСХОДА ЗДЕСЬ НЕ `notice`, И ЭТО ИЗМЕРЕННЫЙ ФАКТ, А НЕ ОПЕЧАТКА.
        # У подраздела очереди свой частный ключ адресной строки со своим местом
        # отрисовки; в реестр кодов он НЕ сведён, и сводить его здесь запрещено
        # (D-07). Обход утверждает адрес ПОСИМВОЛЬНО именно поэтому: сведение,
        # сделанное мимоходом, покраснело бы здесь, а не на живом экране.
        outcomes=(
            _Outcome(
                name="задача-снята",
                arrange=_arrange_drop_removed,
                landing="/admin/queue",
                outcome_key="result",
                outcome_code=DROP_REMOVED,
            ),
            _Outcome(
                name="задача-уже-ушла",
                arrange=_arrange_drop_missing,
                landing="/admin/queue",
                outcome_key="result",
                outcome_code=DROP_MISSING,
            ),
            _Outcome(
                name="очередь-недоступна",
                arrange=_arrange_drop_unavailable,
                landing="/admin/queue",
                outcome_key="result",
                outcome_code=DROP_UNAVAILABLE,
            ),
            _Outcome(
                name="у-аккаунта-нет-очереди",
                arrange=_arrange_drop_unknown_account,
                landing="/admin/queue",
                outcome_key="result",
                outcome_code="unknown_account",
            ),
        ),
        missing_identifier=_arrange_missing_queue_account,
        missing_identifier_landing="/admin/queue?result=unknown_account",
    ),
    _Route(
        key="app/pages/admin.py::admin_delete_user",
        name="удаление пользователя из его карточки",
        identity="admin",
        htmx_form=LOCATION,
        outcomes=(
            _Outcome(
                name="успех",
                arrange=_arrange_delete_user,
                landing="/admin/users",
            ),
            _Outcome(
                name="нельзя-удалить-себя",
                arrange=_arrange_delete_self,
                landing="/admin/users/{user_id}",
            ),
        ),
        missing_identifier=_arrange_missing_user,
        missing_identifier_landing="/admin/users",
    ),
    _Route(
        key="app/pages/admin.py::admin_impersonate",
        name="вход администратора под личностью пользователя",
        identity="admin",
        htmx_form=LOCATION,
        # ⚠️ ЗДЕСЬ ОБХОД УТВЕРЖДАЕТ ТОЛЬКО ТРАНСПОРТ. Cookie личности и
        # ФАКТИЧЕСКАЯ смена лица утверждаются ТРОЙНОЙ парой в
        # `tests/test_pages/test_impersonation.py`: заголовок перехода приезжает
        # и при потерянной cookie, и обход, проверяющий один транспорт, об этом
        # промолчал бы. Два разных предмета — два разных правила.
        outcomes=(
            _Outcome(
                name="успех",
                arrange=_arrange_impersonate,
                landing="/dashboard",
            ),
            _Outcome(
                name="нельзя-войти-под-собой",
                arrange=_arrange_impersonate_self,
                landing="/admin/users/{user_id}",
            ),
        ),
        missing_identifier=_arrange_missing_impersonation_target,
        missing_identifier_landing="/admin/users",
    ),
    _Route(
        key="app/pages/schedules.py::schedules_delete",
        name="удаление расписания из редактора объявления",
        identity="user",
        # ЕДИНСТВЕННЫЙ фрагментный маршрут фазы: действие убирает строку с
        # экрана, который ОСТАЁТСЯ, а прокрутки в редакторе нет — ключи карточки
        # и панели первичные, сдвигаться нечему. Обход ветвится по ЭТОМУ ПОЛЮ, а
        # не по имени маршрута.
        htmx_form=FRAGMENT,
        outcomes=(
            _Outcome(
                name="успех",
                arrange=_arrange_editor_schedule_delete,
                landing="/ads/{ad_id}/edit",
            ),
        ),
        session_landing="/login",
    ),
)

# ⚠️ ЧИСЛО МАРШРУТОВ. Считает ЗАПИСИ перечня: одна запись = один маршрут.
#
# ЛЕТОПИСЬ ЧИСЛА:
#   0 → 2, Фаза 10, план 10-03, задача 1: заведены удаление аккаунта мессенджера
#   и удаление объявления — оба уходят в ветку перехода по объявленному изъятию
#   (`OFFSET_CURSOR_EXCEPTIONS`). Число доводят до восьми задачи 2 и 3, каждая
#   своим движением с летописью.
#
#   2 → 6, Фаза 10, план 10-03, задача 2: заведены ЧЕТЫРЕ записи — повтор
#   отправки из журнала, перезапуск контейнера воркера, снятие задачи из очереди
#   отправки и удаление пользователя из его карточки. ⚠️ КОДЫ ИСХОДА НОВЫХ
#   ЗАПИСЕЙ НЕ СОЗДАЮТ: у повтора отправки их четыре, у перезапуска два, у
#   снятия задачи четыре — и все они живут ПОЛЕМ «список ожидаемых исходов»
#   внутри СВОЕЙ записи. Длина перечня после этой задачи равна ШЕСТИ, а число
#   случаев обхода — заметно больше; сличать их между собой ЗАПРЕЩЕНО.
#
#   6 → 8, Фаза 10, план 10-03, задача 3: заведены ДВЕ записи — вход
#   администратора под личностью пользователя и удаление расписания из редактора
#   объявления. Вторая НЕ ПРАВИТ ОБРАБОТЧИКА (он переведён планом 10-01) и стоит
#   здесь затем, чтобы перечень накрывал ВСЕ маршруты фазы: у неё своя ожидаемая
#   форма ответа — фрагмент вместо перехода, — и обход ветвится по полю записи.
#   ⚠️ ВОСЕМЬ — ЭТО ВСЕ МАРШРУТЫ ПОДТВЕРЖДЕНИЯ ФАЗЫ. Появление девятого без
#   записи КРАСНЕЕТ, и это и есть то свойство, ради которого обход собран одним
#   модулем, а не восемью функциями по файлам разделов.
CONFIRMED_DELETE_ROUTES_DECLARED = 8

# ⚠️ ЧИСЛО СЛУЧАЕВ ОБХОДА. Считает ПАРЫ «маршрут × ожидаемый исход» — ДРУГОЕ
# МНОЖЕСТВО, чем число выше. Маршрут с четырьмя кодами исхода даёт четыре случая
# при ОДНОЙ записи перечня, поэтому эти два числа не равны и приводить их к
# согласию правкой одного НЕЛЬЗЯ: первое перестало бы отвечать за «сколько у
# фазы маршрутов подтверждения», второе — за «сколько у них исходов».
#
# ЛЕТОПИСЬ ЧИСЛА:
#   0 → 2, Фаза 10, план 10-03, задача 1: у обоих заведённых маршрутов список
#   исходов содержит РОВНО ОДИН исход — успех; кодов исхода эти два маршрута не
#   выдают вовсе. Число ПОСТАВЛЕНО ПРОГОНОМ покрасневшего правила, а не
#   сложением в уме.
#
#   2 → 15, Фаза 10, план 10-03, задача 2. Прибавка тринадцать: четыре кода
#   повтора отправки, два кода и успех перезапуска воркера, четыре исхода
#   закрытого словаря снятия задачи, успех и «нельзя удалить себя» у удаления
#   пользователя. ⚠️ ЧИСЛО ПОСТАВЛЕНО ПРОГОНОМ ПОКРАСНЕВШЕГО ПРАВИЛА, дословно:
#   `AssertionError: случаев обхода (пар «маршрут × исход») стало 15, а объявлено
#   2. ⚠️ ЭТО НЕ ЧИСЛО МАРШРУТОВ: их 6 …` — то есть сумма НЕ складывалась в уме,
#   и её назвал сам отказ.
#
#   15 → 18, Фаза 10, план 10-03, задача 3. Прибавка три: успех и «нельзя войти
#   под собой» у входа под пользователем, успех у единственного фрагментного
#   маршрута фазы. Число ПОСТАВЛЕНО ПРОГОНОМ покрасневшего правила, дословно:
#   `AssertionError: случаев обхода (пар «маршрут × исход») стало 18, а объявлено
#   15. ⚠️ ЭТО НЕ ЧИСЛО МАРШРУТОВ: их 8 …`.
#
#   ⚠️ ОБА ЧИСЛА ФАЗЫ ЗАКРЫТЫ И БОЛЬШЕ НЕ ДВИГАЮТСЯ. Их предметы названы РАЗНЫМИ
#   фразами намеренно: выше — МАРШРУТЫ ПОДТВЕРЖДЕНИЯ (сколько мест продукта
#   стоит за панелью), здесь — СЛУЧАИ ОБХОДА, то есть пары «маршрут × ожидаемый
#   исход» (сколько различимых ответов эти места дают). Числа не равны потому,
#   что маршрут с четырьмя кодами исхода даёт четыре случая при ОДНОЙ записи
#   перечня; две летописи с одинаковой формулировкой были бы приглашением
#   следующей фазе свести их в одно.
CONFIRMED_DELETE_OUTCOME_CASES_DECLARED = 18


def _outcome_cases() -> list[tuple[_Route, _Outcome]]:
    """РАЗВЁРНУТЫЕ пары «маршрут × исход» — предмет параметризации обхода."""
    return [
        (route, outcome)
        for route in CONFIRMED_DELETE_ROUTES
        for outcome in route.outcomes
    ]


def _case_id(case: tuple[_Route, _Outcome]) -> str:
    route, outcome = case
    return f"{route.handler}-{outcome.name}"


# =============================================================================
# ДВА ПРАВИЛА ЧИСЛА — ПО ОДНОМУ НА ОСЬ
# =============================================================================


def test_the_number_of_confirmed_delete_routes_is_the_declared_one():
    """Длина перечня равна числу МАРШРУТОВ, а не числу случаев обхода.

    ⚠️ ПРЕДМЕТ — МОЛЧАЛИВОЕ ИСЧЕЗНОВЕНИЕ МАРШРУТА. Запись, выпавшая из перечня,
    уносит с собой обе половины пары своего маршрута: обход остаётся зелёным, а
    маршрут — непроверенным ни на одном транспорте. Сличать длину перечня с
    числом СЛУЧАЕВ запрещено — это разные множества (см. шапку модуля).
    """
    assert len(CONFIRMED_DELETE_ROUTES) == CONFIRMED_DELETE_ROUTES_DECLARED, (
        f"маршрутов подтверждения в перечне {len(CONFIRMED_DELETE_ROUTES)}, а "
        f"объявлено {CONFIRMED_DELETE_ROUTES_DECLARED}. Падение означает, что "
        "маршрут выпал из обхода и остался непроверенным на ОБОИХ транспортах; "
        "рост — что маршрут появился, а решения о его форме ответа никто не "
        "принимал"
    )

    keys = [route.key for route in CONFIRMED_DELETE_ROUTES]
    assert len(set(keys)) == len(keys), (
        f"два маршрута объявлены одним ключом: {sorted(keys)}. Одна запись = "
        "один маршрут, и столкновение ключей схлопнуло бы два маршрута в один"
    )


def test_every_outcome_case_of_every_confirmed_delete_route_is_traversed():
    """Число СЛУЧАЕВ обхода равно объявленному, и пустых списков исходов нет.

    ⚠️ ЭТО ВТОРАЯ ОСЬ, И ЕЁ ПРЕДМЕТ ДРУГОЙ: молчаливая потеря КОДА ИСХОДА при
    целом маршруте. Маршрут повтора отправки выдаёт четыре кода; потерянный
    четвёртый не трогает длины перечня вовсе, и правило числа маршрутов о нём не
    узнает.

    ⚠️ АНТИВАКУУМНАЯ ПОЛОВИНА ОБЯЗАТЕЛЬНА. Маршрут с ПУСТЫМ списком исходов дал
    бы ноль случаев обхода: обе половины его пары не проверялись бы вовсе, а
    сумма сошлась бы с объявленным числом ровно тогда, когда число опустили бы
    вместе с ним.
    """
    empty = [route.key for route in CONFIRMED_DELETE_ROUTES if not route.outcomes]
    assert not empty, (
        "у маршрута ПУСТОЙ список ожидаемых исходов:\n  " + "\n  ".join(empty) +
        "\n\nНоль случаев обхода означает, что обе половины его пары не "
        "проверяются вовсе, а сумма по перечню об этом молчит"
    )

    cases = _outcome_cases()
    assert len(cases) == CONFIRMED_DELETE_OUTCOME_CASES_DECLARED, (
        f"случаев обхода (пар «маршрут × исход») стало {len(cases)}, а "
        f"объявлено {CONFIRMED_DELETE_OUTCOME_CASES_DECLARED}. ⚠️ ЭТО НЕ ЧИСЛО "
        f"МАРШРУТОВ: их {len(CONFIRMED_DELETE_ROUTES)}, и приводить два числа к "
        "согласию правкой одного нельзя. Поставьте число ПРОГОНОМ этого отказа, "
        "а не сложением в уме"
    )

    names = [(route.key, outcome.name) for route, outcome in cases]
    assert len(set(names)) == len(names), (
        "у одного маршрута два исхода названы одинаково — идентификаторы "
        "случаев обхода схлопнулись бы, и один из них не исполнился бы"
    )


# =============================================================================
# ОБХОД: обе половины пары на каждом случае
# =============================================================================


@pytest.mark.parametrize("case", _outcome_cases(), ids=_case_id)
@pytest.mark.asyncio
async def test_every_confirmed_delete_route_answers_both_transports(
    case, client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Без признака htmx — прежний 302 на прежний адрес; с признаком — 204 и
    заголовок перехода на ТОТ ЖЕ адрес, без тела.

    Состояние готовится ЗАНОВО для каждой половины: подтверждённое действие
    необратимо, и вторая половина, пришедшая на уже изменённое состояние,
    проверяла бы не тот исход, который названа проверять.
    """
    route, outcome = case
    await _identify(client, route.identity, test_settings)

    degraded = await outcome.arrange(client, db_session, test_settings, route.identity)
    expected = outcome.expected_landing(degraded)
    with degraded.context():
        without = await client.post(
            degraded.url, data=degraded.data, follow_redirects=False
        )

    assert without.status_code == 302, (
        f"{route.name}: путь деградации ответил {without.status_code} вместо 302 "
        "— человек без JavaScript остался бы без ответа"
    )
    assert without.headers["location"] == expected, (
        f"{route.name}: адрес деградации {without.headers['location']!r} не "
        f"совпал с ожидаемым {expected!r} ПОСИМВОЛЬНО"
    )

    # ⚠️ ЛИЧНОСТЬ ВОССТАНАВЛИВАЕТСЯ ПЕРЕД ВТОРОЙ ПОЛОВИНОЙ, И ЭТО ПРЕДМЕТ, А НЕ
    # УБОРКА. Один из маршрутов обхода МЕНЯЕТ ЛИЧНОСТЬ: после его половины
    # деградации клиент несёт cookie чужого лица, а вложенный вход отвергается
    # зависимостью запрета — вторая половина проверяла бы отказ, а не переход.
    await _identify(client, route.identity, test_settings)

    arranged = await outcome.arrange(client, db_session, test_settings, route.identity)
    expected = outcome.expected_landing(arranged)
    with arranged.context():
        # ⚠️ `follow_redirects=True` — ЧАСТЬ ПРЕДМЕТА. Ответ 302 пришёл бы сюда
        # кодом 200 и телом чужого документа, и утверждение о 204 позеленеть на
        # нём не может.
        with_layer = await client.post(
            arranged.url,
            data=arranged.data,
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )

    if route.htmx_form is FRAGMENT:
        assert with_layer.status_code == 200, (
            f"{route.name}: фрагментный маршрут ответил "
            f"{with_layer.status_code} вместо 200"
        )
        assert DOCUMENT_MARK not in with_layer.text, (
            f"{route.name}: в ответе слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ — "
            "значит обработчик ответил перенаправлением, а клиент прошёл по нему"
        )
        assert with_layer.text.strip(), (
            f"{route.name}: фрагментный маршрут ответил пустым телом"
        )
        return

    assert with_layer.status_code == 204, (
        f"{route.name}: слою письма ответили {with_layer.status_code} вместо 204."
        " Код 200 здесь означает, что обработчик ответил перенаправлением и "
        "клиент прошёл по нему прозрачно — человек увидел бы открытую панель и "
        "тишину"
    )
    assert with_layer.headers["HX-Location"] == expected, (
        f"{route.name}: заголовок перехода {with_layer.headers['HX-Location']!r} "
        f"не совпал с адресом деградации {expected!r}"
    )
    assert with_layer.text == "", (
        f"{route.name}: у ответа 204 появилось тело — у этого статуса тела нет "
        "по определению"
    )
    assert DOCUMENT_MARK not in with_layer.text


# =============================================================================
# ОТДЕЛЬНЫЕ УТВЕРЖДЕНИЯ ОБХОДА — В СЧЁТ ИСХОДОВ НЕ ВХОДЯТ
# =============================================================================


@pytest.mark.parametrize(
    "route",
    [route for route in CONFIRMED_DELETE_ROUTES if route.missing_identifier],
    ids=lambda route: route.handler,
)
@pytest.mark.asyncio
async def test_a_missing_identifier_is_answered_exactly_like_a_success(
    route, client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Несуществующий идентификатор отвечает ТОЙ ЖЕ формой, что и успех.

    ⚠️ ЭТО СВОЙСТВО ТРАНСПОРТА, А НЕ ИСХОД ДЕЙСТВИЯ, поэтому оно не входит в счёт
    случаев обхода. Различимый ответ означал бы, что по маршруту удаления можно
    ПЕРЕЧИСЛЯТЬ чужие идентификаторы, ничего не удаляя.
    """
    await _identify(client, route.identity, test_settings)
    arranged = await route.missing_identifier(
        client, db_session, test_settings, route.identity
    )

    with arranged.context():
        response = await client.post(
            arranged.url,
            data=arranged.data,
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )

    assert response.status_code == 204, (
        f"{route.name}: несуществующий идентификатор ответил "
        f"{response.status_code} — ответ отличим от успешного"
    )
    assert response.headers["HX-Location"] == route.missing_identifier_landing
    assert response.text == ""


@pytest.mark.parametrize(
    "route",
    [route for route in CONFIRMED_DELETE_ROUTES if route.foreign_owner],
    ids=lambda route: route.handler,
)
@pytest.mark.asyncio
async def test_a_foreign_row_is_not_touched_and_is_answered_like_a_success(
    route, client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Чужая строка НЕ удаляется, а ответ неотличим от успешного (T-10-19).

    Новый транспорт не имеет права ослабить ограничение владельца в выборке:
    удаление чужого — это и есть та беда, ради которой ограничение стоит внутри
    запроса, а не последующим `if`.
    """
    await _identify(client, route.identity, test_settings)
    arranged, (model, row_id) = await route.foreign_owner(
        client, db_session, test_settings, route.identity
    )

    with arranged.context():
        response = await client.post(
            arranged.url,
            data=arranged.data,
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )

    assert response.status_code == 204, (
        f"{route.name}: чужой идентификатор ответил {response.status_code} — "
        "ответ отличим от успешного"
    )
    assert response.headers["HX-Location"] == route.missing_identifier_landing

    db_session.expire_all()
    assert await db_session.get(model, row_id) is not None, (
        f"{route.name}: ЧУЖАЯ СТРОКА УДАЛЕНА — ограничение владельца потеряно "
        "при переезде на слой ответа"
    )


@pytest.mark.parametrize(
    "route",
    [route for route in CONFIRMED_DELETE_ROUTES if route.session_landing],
    ids=lambda route: route.handler,
)
@pytest.mark.asyncio
async def test_the_branch_without_a_session_answers_both_transports(
    route, client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Ветка «нет сессии» тоже идёт через слой ответа (G-2).

    Собственное перенаправление, оставленное в этой ветке, — второе решение о
    форме ответа: слой письма пошёл бы по нему прозрачно и вклеил бы целую
    страницу входа туда, где ждали снятия строки.
    """
    # Личность нужна ДО чистки cookie: посев случая заводит строку под её
    # владельцем, и без входа он упал бы на отсутствующем пользователе — то есть
    # тест краснел бы по чужой причине, ничего не сказав о ветке «нет сессии».
    await _identify(client, route.identity, test_settings)
    arranged = await route.outcomes[0].arrange(
        client, db_session, test_settings, route.identity
    )
    client.cookies.clear()

    with arranged.context():
        without = await client.post(
            arranged.url, data=arranged.data, follow_redirects=False
        )
    assert without.status_code == 302
    assert without.headers["location"] == route.session_landing

    with arranged.context():
        with_layer = await client.post(
            arranged.url,
            data=arranged.data,
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )
    assert with_layer.status_code == 204, (
        f"{route.name}: ветка «нет сессии» ответила слою письма "
        f"{with_layer.status_code} вместо 204"
    )
    assert with_layer.headers["HX-Location"] == route.session_landing
    assert with_layer.text == ""


# =============================================================================
# РЕБРО ИДЕМПОТЕНТНОСТИ (FORM-06): ПОВТОРНОЕ ПОДТВЕРЖДЁННОЕ УДАЛЕНИЕ
# =============================================================================
#
# ⚠️ ЭТО ОТДЕЛЬНОЕ УТВЕРЖДЕНИЕ ОБХОДА, И В СЧЁТ ИСХОДОВ ОНО НЕ ВХОДИТ. Повтор
# не является ИСХОДОМ маршрута: исход — это различимый ответ ДЕЙСТВИЯ, а повтор
# есть свойство ТРАНСПОРТА («что происходит, если это выполнится дважды на том
# же входе»). Подмешивание его в счёт случаев сделало бы сличение числа случаев
# неисполнимым — ровно по тому же основанию, по которому в счёт не входят чужой
# и несуществующий идентификатор и ветка «нет сессии».
#
# ⚠️ ЧЕМ ЭТО ОТЛИЧАЕТСЯ ОТ ДЕЙСТВУЮЩЕГО ПРАВИЛА НЕСУЩЕСТВУЮЩЕГО ИДЕНТИФИКАТОРА
# (`test_a_missing_identifier_is_answered_exactly_like_a_success`) — ЧИТАТЬ ДО
# ТОГО, КАК СНИМАТЬ ОДНО ИЗ ДВУХ КАК ДУБЛИКАТ. Там идентификатор НЕ СУЩЕСТВОВАЛ
# НИКОГДА, правило параметризовано маршрутами ПЕРЕХОДА и утверждает 204 с
# заголовком перехода и пустым телом. Здесь строка СУЩЕСТВОВАЛА И БЫЛА УДАЛЕНА
# ПРЕДЫДУЩИМ ЗАПРОСОМ ЭТОГО ЖЕ ЧЕЛОВЕКА, предмет — ЕДИНСТВЕННЫЙ ФРАГМЕНТНЫЙ
# маршрут фазы, и ответ есть 200 с телом. Совпадение двух ответов между собой
# ничего не говорит о совпадении с ответом на никогда не существовавший
# идентификатор, и наоборот: два разных предмета — два разных правила.


def _the_fragment_route() -> _Route:
    """ЕДИНСТВЕННЫЙ фрагментный маршрут фазы — предмет правила ниже.

    Ветвление идёт по ПОЛЮ ЗАПИСИ (`htmx_form`), а не по имени маршрута: имя
    сменилось бы правкой строки, и правило молча перестало бы иметь предмет.
    """
    fragment_routes = [
        route for route in CONFIRMED_DELETE_ROUTES if route.htmx_form is FRAGMENT
    ]
    assert len(fragment_routes) == 1, (
        "фрагментных маршрутов в перечне "
        f"{len(fragment_routes)}: {[route.key for route in fragment_routes]}. "
        "Правило написано на ЕДИНСТВЕННЫЙ такой маршрут; появление второго "
        "означает, что решение о его форме ответа принято, а о неотличимости "
        "его повтора — нет"
    )
    return fragment_routes[0]


def _addressed_schedule_id(arranged: _Arranged) -> int:
    """Идентификатор адресуемой строки — ИЗ АДРЕСА расстановки.

    Расстановка отдаёт идентификатор только адресом, и это не обходной путь:
    второй посев ради того, чтобы «узнать номер», был бы ВТОРОЙ КОПИЕЙ посева,
    а он несёт несущую тонкость (второе расписание оставляет экран непустым,
    иначе маршрут ушёл бы в ветку перехода и фрагмента не было бы вовсе).
    """
    parts = arranged.url.strip("/").split("/")
    assert parts[0] == "schedules" and parts[-1] == "delete", (
        f"адрес расстановки {arranged.url!r} перестал быть адресом удаления "
        "расписания — идентификатор из него читать больше нельзя"
    )
    return int(parts[1])


def _expected_oob_ids(schedule_id: int) -> set[str]:
    """Три внеполосных узла ответа, названные ПОИМЁННО по разметке.

    Два из трёх СОБИРАЮТСЯ ИЗ ИДЕНТИФИКАТОРА ПОСЕВА, а не выписаны литералами:
    литерал разошёлся бы с посевом при первом же изменении последовательности
    идентификаторов, и правило зеленело бы на чужих узлах.

    ⚠️ ТРЕТИЙ — СТАТИЧЕСКИЙ СЕЛЕКТОР, И ЭТО ИЗМЕРЕННЫЙ ФАКТ РАЗМЕТКИ, А НЕ
    ПОСЛАБЛЕНИЕ. Узел линейки счётчика адресует цель `innerHTML:#sched-count` и
    от идентификатора удаляемой строки НЕ ЗАВИСИТ ВОВСЕ (`ads/partials/
    sched_delete_response.html`): собирать его «из посева» было бы нечем, а
    расхождения с посевом у него быть не может по построению.
    """
    return {f"sched-{schedule_id}", f"sched-del-{schedule_id}", "#sched-count"}


@pytest.mark.asyncio
async def test_a_repeated_confirmed_delete_on_the_fragment_route_answers_the_same_shape(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Повтор подтверждённого удаления отвечает ТОЙ ЖЕ формой, что и первое.

    ⚠️ КАКОЕ РЕБРО ЭТО РАЗРЕШАЕТ. Идемпотентность отката-фолбэка FORM-06 — проба
    «что происходит, если это выполнится дважды на том же входе». Обработчик
    удаления расписания ОБЪЯВЛЯЕТ о себе неотличимость повтора и выписывает, чем
    именно она достигается (`_ad_id_from_form`: «на повторном запросе строки уже
    нет, `ad_id` становится неизвестен, и обработчик уходил в ветку перехода
    вместо ветки фрагмента»), — но до этого правила её не утверждало НИЧТО.

    ⚠️ ПОЧЕМУ ПРЕДМЕТ ИМЕННО ФРАГМЕНТНЫЙ МАРШРУТ. Он ЕДИНСТВЕННЫЙ, где повтор
    ПЕРЕВЫСТАВЛЯЕТ внеполосные узлы снятия по идентификатору, которого в
    документе уже нет. На маршрутах перехода тела нет вовсе, и сличать там
    нечего, кроме статуса и адреса (это делает соседнее параметризованное
    правило).

    ⚠️ ЧЕМ ЭТО ОТЛИЧАЕТСЯ ОТ ПРАВИЛА НЕСУЩЕСТВУЮЩЕГО ИДЕНТИФИКАТОРА — см. абзац
    над разделом. Коротко: там идентификатор не существовал НИКОГДА и ответ есть
    переход; здесь строка СУЩЕСТВОВАЛА И БЫЛА УДАЛЕНА, а ответ есть фрагмент.

    ⚠️ ПРАВИЛО ЗЕЛЕНО ПЕРВЫМ ЖЕ ПРОГОНОМ, И ЭТО ОЖИДАЕМО: свойство сегодня
    ДЕРЖИТСЯ. Зубы ему даёт не переход цвета, а отрицательный контроль ниже.
    """
    route = _the_fragment_route()
    outcome = route.outcomes[0]
    await _identify(client, route.identity, test_settings)

    arranged = await outcome.arrange(client, db_session, test_settings, route.identity)
    schedule_id = _addressed_schedule_id(arranged)

    # АНТИВАКУУМ ДО: адресуемая строка ЕСТЬ. Состояние читается ЗАПРОСОМ К БАЗЕ,
    # а не выводится из ответа: ответ и есть предмет сличения, и выводить из него
    # состояние базы значило бы проверять утверждение самим утверждением.
    db_session.expire_all()
    assert await db_session.get(Schedule, schedule_id) is not None, (
        f"адресуемого расписания {schedule_id} не было в базе ДО первого "
        "запроса — тогда «повтор» неотличим от второй попытки первого, и "
        "правило утверждало бы не то, чем называется"
    )

    # ⚠️ ОБА ЗАПРОСА — ВНУТРИ ОДНОГО ВХОЖДЕНИЯ В МЕНЕДЖЕР ПОДМЕН. У фрагментного
    # маршрута подмен нет и менеджер пуст, но форма обращения остаётся общей:
    # ветка «если подмены есть» означала бы, что половина случаев идёт другим
    # путём (записанное основание поля `context`).
    with arranged.context():
        first = await client.post(
            arranged.url,
            data=arranged.data,
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )
        # АНТИВАКУУМ ПОСЛЕ: строки НЕТ, то есть второй запрос действительно
        # ПОВТОР, а не вторая попытка первого.
        db_session.expire_all()
        after_first = await db_session.get(Schedule, schedule_id)
        repeat = await client.post(
            arranged.url,
            data=arranged.data,
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )

    assert after_first is None, (
        f"расписание {schedule_id} осталось в базе ПОСЛЕ первого запроса — "
        "второй запрос не является повтором удаления, и вся форма правила "
        "разговаривает не о том предмете"
    )

    assert first.status_code == 200, (
        f"первое удаление ответило {first.status_code} вместо 200 — предметом "
        "сличения перестал быть фрагментный ответ"
    )
    assert repeat.status_code == first.status_code, (
        f"повтор ответил {repeat.status_code}, а первое удаление "
        f"{first.status_code} — ответы РАЗЛИЧИМЫ уже статусом"
    )
    assert DOCUMENT_MARK not in first.text, (
        "в ответе на первое удаление приехал ЦЕЛЫЙ ДОКУМЕНТ"
    )
    assert DOCUMENT_MARK not in repeat.text, (
        "в ответе на повтор приехал ЦЕЛЫЙ ДОКУМЕНТ — значит обработчик ушёл в "
        "ветку перехода, а первое удаление уходило в ветку фрагмента"
    )

    first_ids = _oob_node_ids(first.text)
    repeat_ids = _oob_node_ids(repeat.text)
    expected = _expected_oob_ids(schedule_id)

    # АНТИВАКУУМ МНОЖЕСТВА: пустое множество, равное пустому, зеленело бы
    # независимо от предмета.
    assert first_ids == expected, (
        f"внеполосные узлы первого удаления {sorted(first_ids)} не совпали с "
        f"ожидаемыми {sorted(expected)} — три узла ответа названы поимённо по "
        "разметке `ads/partials/sched_delete_response.html`"
    )
    assert repeat_ids == first_ids, (
        f"внеполосные узлы повтора {sorted(repeat_ids)} отличны от узлов "
        f"первого удаления {sorted(first_ids)}. Различимость ответов позволяет "
        "ПЕРЕЧИСЛЯТЬ занятые идентификаторы, ничего не удаляя (T-10-34)"
    )


@pytest.mark.asyncio
async def test_control_negative_a_shifted_identifier_reddens_the_sameness_check(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ: другой идентификатор даёт ДРУГОЕ множество.

    ⚠️ ЧТО ИМЕННО ДОКАЗЫВАЕТСЯ. Что сличение множеств внеполосных узлов НЕ
    ТРИВИАЛЬНО: правило, сличающее величины, которые совпадают всегда, зелено
    независимо от предмета — и именно такой зелени в этой партии не остаётся.
    Правило выше зелено первым же прогоном, перехода цвета у него нет, и зубы
    ему даёт этот контроль.

    ⚠️ ПОЧЕМУ ЗДЕСЬ ПОСЕЯНА ТРЕТЬЯ СТРОКА. Действующая расстановка сеет ДВЕ, и
    удаление второй оставило бы объявление без расписаний вовсе — обработчик
    ушёл бы в ветку перехода (D-04), ответил бы 204 без тела, и множество
    оказалось бы ПУСТЫМ. Сличение «три узла против ничего» доказывает смену
    ВЕТКИ, а не чувствительность к идентификатору, то есть ровно тот класс
    вакуумной зелени, ради которого контроль и заведён. Третья строка держит
    третий запрос НА ТОЙ ЖЕ ФРАГМЕНТНОЙ ВЕТКЕ: форма ответа та же, различаться
    обязаны ИМЕННО идентификаторы. Второй расстановки при этом не заводится —
    сеялка та же (`_seed_schedule`), объявление и аккаунт те же.
    """
    route = _the_fragment_route()
    outcome = route.outcomes[0]
    await _identify(client, route.identity, test_settings)

    arranged = await outcome.arrange(client, db_session, test_settings, route.identity)
    schedule_id = _addressed_schedule_id(arranged)
    ad_id = arranged.landing_args["ad_id"]

    db_session.expire_all()
    others = (
        await db_session.execute(
            select(Schedule)
            .where(Schedule.ad_id == ad_id, Schedule.id != schedule_id)
            .order_by(Schedule.id)
        )
    ).scalars().all()
    assert others, (
        f"у объявления {ad_id} нет ВТОРОГО посеянного расписания — контролю "
        "нечего адресовать, и он выродился бы в повторение несущего правила"
    )
    other = others[0]
    await _seed_schedule(db_session, ad_id, other.account_id)

    other_url = f"/schedules/{other.id}/delete"
    # КОНТРОЛЬ ОБЯЗАН ДОКАЗАТЬ, ЧТО ИЗМЕНИЛ ЧТО-ТО И ИМЕННО ТО: адрес третьего
    # запроса сличается с адресом первых двух на НЕРАВЕНСТВО ДО отправки.
    assert other_url != arranged.url, (
        f"адрес контроля {other_url!r} совпал с адресом первых двух запросов — "
        "контроль подставил ТО ЖЕ САМОЕ и доказывать ему нечего"
    )

    with arranged.context():
        first = await client.post(
            arranged.url,
            data=arranged.data,
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )
        repeat = await client.post(
            arranged.url,
            data=arranged.data,
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )
        shifted = await client.post(
            other_url,
            data=arranged.data,
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )

    repeat_ids = _oob_node_ids(repeat.text)
    shifted_ids = _oob_node_ids(shifted.text)

    assert shifted.status_code == repeat.status_code == 200, (
        f"контроль ответил {shifted.status_code}, повтор "
        f"{repeat.status_code} — ответы разошлись ВЕТКОЙ, и различие множеств "
        "доказывало бы смену ветки, а не чувствительность к идентификатору"
    )
    assert repeat_ids, (
        "множество внеполосных узлов повтора ПУСТО — сличение пустого с "
        "непустым зелено независимо от предмета"
    )
    assert shifted_ids, (
        "множество внеполосных узлов контроля ПУСТО — см. выше"
    )
    assert shifted_ids != repeat_ids, (
        f"ответ на ДРУГОЙ идентификатор дал ТО ЖЕ множество {sorted(shifted_ids)}, "
        f"что и повтор {sorted(repeat_ids)}. Значит сличение множеств совпадает "
        "ВСЕГДА, и несущее правило зелено независимо от предмета"
    )
    assert shifted_ids == _expected_oob_ids(other.id), (
        f"внеполосные узлы контроля {sorted(shifted_ids)} не совпали с "
        f"ожидаемыми для расписания {other.id} — контроль изменил ЧТО-ТО, но не "
        "то, что называется"
    )

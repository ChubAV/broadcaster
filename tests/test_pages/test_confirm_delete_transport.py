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
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User
from app.pages import history as history_module
from app.pages.common import templates
from app.pages import notices
# ⚠️ ГРАНИЦА ВЕЛИЧИНЫ ВВОЗИТСЯ У ПРИЛОЖЕНИЯ, А НЕ ПОВТОРЯЕТСЯ ЗДЕСЬ ЧИСЛОМ.
# Выписанная вторым литералом, она разошлась бы с продуктом при первой же правке
# колонки, и отбор величины «вне диапазона» молча стал бы отбором величины
# «вне числа, которое когда-то было границей». Владелец величины — план 10-12.
from app.pages.schedules import ID_MAX
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

# ⚠️ ПОСЕВ ФАЗЫ 9 ВВОЗИТСЯ ПОД ПСЕВДОНИМАМИ, И ЭТО НЕ УКРАШЕНИЕ ИМЁН. Имя
# `_seed_account` в ЭТОМ модуле уже занято посевом аккаунта мессенджера с ДРУГОЙ
# сигнатурой (`(db, user_id, *, account_type)` против `(db, type_, user_id)`);
# ввоз под настоящим именем молча перекрыл бы первое, и половина расстановок
# поехала бы не тем посевом — с перепутанными местами позиционными аргументами,
# то есть без единого признака отказа в тексте самих расстановок. Основание то же,
# по которому ввозятся, а не переписываются двойники выше: второй экземпляр посева
# разошёлся бы с первым молча.
from tests.test_pages.test_account_groups import (
    _seed_account as _seed_groups_account,
    _seed_group as _seed_account_group,
)

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
# Посев: удаление группы аккаунта — ВТОРОЙ ФРАГМЕНТНЫЙ МАРШРУТ ПЕРЕЧНЯ
#
# ⚠️ ЭТА ЗАПИСЬ НЕ ПРАВИТ ОБРАБОТЧИКА НИ НА СИМВОЛ: маршрут переведён и обойдён
# руками ФАЗОЙ 9. Он появляется здесь только сейчас потому, что Фаза 10 объявила
# СВОИМИ восемь маршрутов подтверждения и девятый, унаследованный, в перечень не
# попал — то есть модуль, объявляющий себя местом, где «маршрут, добавленный за
# панелью подтверждения, краснеет», о нём молчал ровно так же, как молчали бы
# восемь отдельных функций. Прибавка есть закрытие УНАСЛЕДОВАННОЙ ДЫРЫ ОБХОДА, а
# не новая работа продукта.
# =============================================================================

# Несуществующий аккаунт отдельных утверждений обхода. ЛИТЕРАЛ ЗДЕСЬ НЕСУЩИЙ:
# адрес приземления этого маршрута собирается из аккаунта ПУТИ
# (`_screen_url(account_id, term)`), а параметризованные правила несуществующего
# идентификатора и чужого владельца сличают его с ОБЪЯВЛЕННЫМ полем записи
# (`missing_identifier_landing`) — то есть с литералом, известным ДО прогона.
# Аккаунт, посеянный на прогоне, номера заранее не имеет, и адрес приземления
# объявить было бы нечем.
MISSING_ACCOUNT_GROUPS_ACCOUNT = 987654
MISSING_ACCOUNT_GROUPS_LANDING = f"/accounts/{MISSING_ACCOUNT_GROUPS_ACCOUNT}/groups"


async def _listing_rows(db: AsyncSession, user_id: int, account_id: int) -> int:
    """Сколько строк в НЕОТФИЛЬТРОВАННОЙ выдаче аккаунта — ЗАПРОСОМ К БАЗЕ.

    ⚠️ АНТИВАКУУМ РАССТАНОВОК СНИМАЕТСЯ ЗДЕСЬ, А НЕ ВЫВОДИТСЯ ИЗ ОТВЕТА. Ветку
    ответа этого маршрута выбирает состояние ВЫДАЧИ, а не исход поиска строки
    (`_current_listing_has_a_row`): расстановка, у которой выдача опустела
    случайно, проверяла бы ветку перехода под именем фрагментной — и наоборот.
    Выводить состояние базы из ответа значило бы проверять утверждение самим
    утверждением.
    """
    rows = (
        await db.execute(
            select(Group).where(
                Group.user_id == user_id, Group.account_id == account_id
            )
        )
    ).scalars().all()
    return len(rows)


async def _arrange_account_group_delete(client, db, settings, identity) -> _Arranged:
    """УСПЕХ ФРАГМЕНТНОЙ ВЕТКИ: адресуется одна из ДВУХ строк выдачи.

    Вторая группа оставляет выдачу НЕПУСТОЙ — тот же приём и по той же причине,
    что у расстановки удаления расписания: на последней строке маршрут уходит в
    ветку перехода, и «фрагментная половина» проверяла бы переход.

    Владелец передаётся посеву Фазы 9 ЯВНО: его собственный посев разрешает
    владельца сам (по адресу `testuser@test.com`), и два независимых разрешения
    разошлись бы молча — строки достались бы не тому пользователю, под которым
    ходит обход.
    """
    user = await _current_user(db, identity, settings)
    account = await _seed_groups_account(db, user_id=user.id)
    group = await _seed_account_group(db, account, "Альфа", user_id=user.id)
    await _seed_account_group(db, account, "Бета", user_id=user.id)

    rows = await _listing_rows(db, user.id, account.id)
    assert rows >= 2, (
        f"в выдаче аккаунта {account.id} строк {rows}, а нужно НЕ МЕНЕЕ ДВУХ: "
        "после удаления адресуемой выдача обязана остаться непустой, иначе "
        "маршрут уходит в ветку перехода и фрагментная половина проверяет переход"
    )
    return _Arranged(
        # ⚠️ ТЕЛО НЕСЁТ ПРИЗНАК ФИЛЬТРА ПОИСКА В ТОМ ВИДЕ, В КАКОМ ЕГО ШЛЁТ
        # РАЗМЕТКА СТРОКИ. Контекст экрана приходит скрытым полем `search` обеих
        # форм пути удаления (D-02, WR-03 плана 09-15); расстановка, отправившая
        # ПУСТОЕ тело, проверяла бы не тот путь, которым ходит продукт.
        url=f"/accounts/{account.id}/groups/{group.id}/delete",
        data={"search": ""},
        landing_args={"account_id": account.id},
    )


async def _arrange_account_group_last(client, db, settings, identity) -> _Arranged:
    """ОПУСТЕВШАЯ ВЫДАЧА: адресуется РОВНО ОДНА строка, и после неё не остаётся
    ничего — маршрут закрывается переходом на экран групп аккаунта (D-09).
    """
    user = await _current_user(db, identity, settings)
    account = await _seed_groups_account(db, user_id=user.id)
    group = await _seed_account_group(db, account, "Единственная", user_id=user.id)

    rows = await _listing_rows(db, user.id, account.id)
    assert rows == 1, (
        f"в выдаче аккаунта {account.id} строк {rows}, а нужна РОВНО ОДНА: при "
        "второй строке выдача не опустеет, и расстановка проверяла бы "
        "фрагментную ветку под именем ветки перехода"
    )
    return _Arranged(
        url=f"/accounts/{account.id}/groups/{group.id}/delete",
        data={"search": ""},
        landing_args={"account_id": account.id},
    )


async def _arrange_missing_account_group(client, db, settings, identity) -> _Arranged:
    return _Arranged(
        url=(
            f"/accounts/{MISSING_ACCOUNT_GROUPS_ACCOUNT}"
            f"/groups/{MISSING_ACCOUNT_GROUPS_ACCOUNT}/delete"
        ),
        data={"search": ""},
    )


async def _arrange_foreign_account_group(client, db, settings, identity):
    """ЧУЖАЯ СТРОКА ЖИВАЯ, а адресуется она через аккаунт, которого нет.

    ⚠️ ПОЧЕМУ АККАУНТ В АДРЕСЕ НЕ ЧУЖОЙ, А НЕСУЩЕСТВУЮЩИЙ. Тройной `WHERE`
    обработчика сличает и владельца, и аккаунт, поэтому строка не находится в
    обоих случаях одинаково; а вот АДРЕС ПРИЗЕМЛЕНИЯ собирается из аккаунта
    ПУТИ, и параметризованное правило сличает его с объявленным литералом записи.
    Номер чужого аккаунта известен только на прогоне — объявить им поле записи
    нечем. Предмет правила от этого не меняется: чужая группа ЖИВАЯ, ответ обязан
    быть неотличим от ответа того же аккаунта на любой другой вход, а строка —
    уцелеть.
    """
    stranger = await _foreign_user(db)
    account = await _seed_groups_account(db, user_id=stranger.id)
    group = await _seed_account_group(db, account, "Чужая", user_id=stranger.id)
    return _Arranged(
        url=(
            f"/accounts/{MISSING_ACCOUNT_GROUPS_ACCOUNT}"
            f"/groups/{group.id}/delete"
        ),
        data={"search": ""},
    ), (Group, group.id)


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
    _Route(
        key="app/pages/account_groups.py::account_groups_delete",
        name="удаление группы аккаунта",
        identity="user",
        # ВТОРОЙ фрагментный маршрут перечня. Действие снимает строку с экрана,
        # который ОСТАЁТСЯ, тремя внеполосными узлами (снятие строки, снятие
        # осиротевшей панели, содержимое линейки счётчика).
        htmx_form=FRAGMENT,
        # ⚠️ ОДИН ИСХОД, А НЕ ДВА, И ЭТО РЕШЕНИЕ, ПРИНЯТОЕ ПО ДОКТРИНЕ МОДУЛЯ, А
        # НЕ НЕДОСМОТР. Обработчик отвечает ДВУМЯ формами: фрагментом, пока в
        # текущей выдаче осталась хотя бы одна строка, и переходом, когда выдача
        # опустела (D-09). Вторая форма ИСХОДОМ ДЕЙСТВИЯ НЕ ЯВЛЯЕТСЯ: исход
        # действия здесь один — группа удалена, — кодов исхода маршрут не выдаёт
        # вовсе (`notice` не передаётся, D-10), и различает две формы СОСТОЯНИЕ
        # ЭКРАНА, а не результат удаления. Это ровно тот класс, который шапка
        # модуля держит ОТДЕЛЬНЫМИ утверждениями, в счёт исходов не входящими
        # («свойство ТРАНСПОРТА, а не исход действия»): подмешай его в список
        # исходов — и «сколько кодов исхода выдаёт маршрут» превратилось бы в
        # «сколько проверок мы написали». Ветка опустевшей выдачи накрыта своим
        # правилом ниже, обеими половинами пары.
        #
        # ⚠️ И ВТОРАЯ ПРИЧИНА, ИЗМЕРЕННАЯ, А НЕ ДОКТРИНАЛЬНАЯ: поле ожидаемой
        # формы ответа (`htmx_form`) живёт у ЗАПИСИ, а не у исхода, и
        # параметризованный обход ветвится по нему. Исход с другой формой ответа
        # внутри одной записи обход бы УРОНИЛ — а расширять структуру записи на
        # ходу здесь запрещено. Ограничение записано ОКНОМ 43 `.planning/WINDOWS.md`
        # и передано дальше; структура не правится, обход не правится.
        outcomes=(
            _Outcome(
                name="успех",
                arrange=_arrange_account_group_delete,
                landing="/accounts/{account_id}/groups",
            ),
        ),
        missing_identifier=_arrange_missing_account_group,
        missing_identifier_landing=MISSING_ACCOUNT_GROUPS_LANDING,
        foreign_owner=_arrange_foreign_account_group,
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
#
#   8 → 9, Фаза 10, план 10-11, задача 1: заведена ОДНА запись — удаление группы
#   аккаунта (`app/pages/account_groups.py::account_groups_delete`). ⚠️ ПОЧЕМУ
#   МАРШРУТ ПОЯВЛЯЕТСЯ ТОЛЬКО СЕЙЧАС, ХОТЯ ОН СТАРШЕ ПЕРЕЧНЯ. Он переведён на
#   слой ответа ФАЗОЙ 9 и обойдён ЕЁ СОБСТВЕННЫМ ручным обходом, а перечень
#   собирала Фаза 10, объявившая своими ВОСЕМЬ маршрутов подтверждения, — то
#   есть унаследованный девятый не попал в него ровно так же, как молчали бы
#   восемь отдельных функций о маршруте, добавленном за панелью. ПРИБАВКА ЕСТЬ
#   ЗАКРЫТИЕ УНАСЛЕДОВАННОЙ ДЫРЫ ОБХОДА, А НЕ НОВАЯ РАБОТА ПРОДУКТА: обработчик
#   этим планом не правится ни на символ. Число ПОСТАВЛЕНО ПРОГОНОМ покрасневшего
#   правила, дословно: `AssertionError: маршрутов подтверждения в перечне 9, а
#   объявлено 8 …`.
CONFIRMED_DELETE_ROUTES_DECLARED = 9

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
#
#   18 → 19, Фаза 10, план 10-11, задача 1. ⚠️ ПРЕЖНЯЯ СТРОКА «ОБА ЧИСЛА ФАЗЫ
#   ЗАКРЫТЫ» НЕ ВЫЧЁРКИВАЕТСЯ, А НАЗЫВАЕТСЯ ВЕРНОЙ ДЛЯ СОСТАВА ФАЗЫ, КОТОРЫЙ ОНА
#   ПЕРЕЖИЛА (образец обращения с отменённой формулировкой — записи D-30 и D-32
#   `.planning/STATE.md`): она была верна для восьми маршрутов, объявленных
#   Фазой 10 своими, и перестала быть верной, когда партия закрытия гейпов внесла
#   в перечень УНАСЛЕДОВАННЫЙ девятый.
#
#   Прибавка ОДИН и названа поимённо: единственный ожидаемый исход удаления
#   группы аккаунта — успех фрагментной ветки. ⚠️ ВТОРАЯ ФОРМА ОТВЕТА ЭТОГО
#   МАРШРУТА (переход на опустевшей выдаче, D-09) СЛУЧАЕМ ОБХОДА НЕ СТАЛА, И ЭТО
#   ПРИНЯТОЕ РЕШЕНИЕ, А НЕ ПРОПУСК: кодов исхода маршрут не выдаёт вовсе
#   (`notice` не передаётся, D-10), исход ДЕЙСТВИЯ у него один — группа удалена,
#   — а две формы ответа различает СОСТОЯНИЕ ЭКРАНА. Это ровно тот класс, который
#   шапка модуля держит отдельными утверждениями: «свойство ТРАНСПОРТА, а не исход
#   действия». Ветка опустевшей выдачи накрыта своим правилом обеими половинами
#   пары; ограничение структуры записи, из-за которого исходом её объявить нельзя,
#   записано ОКНОМ 43 `.planning/WINDOWS.md`.
#
#   Число ПОСТАВЛЕНО ПРОГОНОМ покрасневшего правила, дословно: `AssertionError:
#   случаев обхода (пар «маршрут × исход») стало 19, а объявлено 18. ⚠️ ЭТО НЕ
#   ЧИСЛО МАРШРУТОВ: их 9 …` — то есть сумма НЕ складывалась в уме, её назвал сам
#   отказ.
CONFIRMED_DELETE_OUTCOME_CASES_DECLARED = 19


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


# Ключи, по которым правила ниже выбирают СВОЙ маршрут. Выбор идёт по КЛЮЧУ
# ЗАПИСИ, а не по полю формы ответа и не по имени: имя сменилось бы правкой
# строки, а поле формы ответа с появлением второго фрагментного маршрута
# перестало быть различающим.
SCHEDULE_ROUTE_KEY = "app/pages/schedules.py::schedules_delete"
ACCOUNT_GROUP_ROUTE_KEY = "app/pages/account_groups.py::account_groups_delete"


def _route_by_key(key: str) -> _Route:
    """Запись перечня ПО КЛЮЧУ. Отсутствие ключа — отказ, а не пустой обход."""
    found = [route for route in CONFIRMED_DELETE_ROUTES if route.key == key]
    assert len(found) == 1, (
        f"по ключу {key!r} в перечне найдено записей {len(found)}, а нужна ровно "
        f"одна. Известные ключи:\n  "
        + "\n  ".join(sorted(route.key for route in CONFIRMED_DELETE_ROUTES))
        + "\n\nПравило, потерявшее предмет, зеленеет молча"
    )
    return found[0]


@pytest.mark.asyncio
async def test_the_emptied_listing_branch_of_the_account_group_route_answers_both_transports(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """ВТОРАЯ ФОРМА ОТВЕТА девятого маршрута: опустевшая выдача идёт ПЕРЕХОДОМ.

    ⚠️ ПОЧЕМУ ЭТО ОТДЕЛЬНОЕ УТВЕРЖДЕНИЕ, А НЕ ВТОРОЙ ИСХОД ЗАПИСИ — ЧИТАТЬ ДО
    ТОГО, КАК ПЕРЕНЕСТИ ЕГО В `outcomes`. Основание ДВОЙНОЕ, и обе половины
    несущие.

    ПЕРВОЕ, ПО СУЩЕСТВУ. Исход — это различимый ответ ДЕЙСТВИЯ; здесь действие
    одно и его результат один (группа удалена), кодов исхода маршрут не выдаёт
    вовсе (`notice` не передаётся, D-10), а две формы ответа различает СОСТОЯНИЕ
    ЭКРАНА: осталась ли в текущей выдаче хотя бы одна строка
    (`_current_listing_has_a_row`). Это свойство ТРАНСПОРТА, ровно как чужой и
    несуществующий идентификатор и ветка «нет сессии», — и по тому же основанию
    оно в счёт случаев обхода не входит: иначе «сколько кодов исхода выдаёт
    маршрут» превратилось бы в «сколько проверок мы написали».

    ВТОРОЕ, ИЗМЕРЕННОЕ. Поле ожидаемой формы ответа (`htmx_form`) живёт у ЗАПИСИ,
    а параметризованный обход ветвится по нему — исход с ДРУГОЙ формой ответа
    внутри одной записи обход бы уронил. Расширять структуру записи на ходу
    запрещено; ограничение записано ОКНОМ 43 `.planning/WINDOWS.md` и передано
    дальше.

    ⚠️ ОБЕ ПОЛОВИНЫ ПАРЫ УТВЕРЖДАЮТСЯ ЗДЕСЬ ЖЕ, и это то, ради чего правило и
    заведено: без него ветка опустевшей выдачи не проверялась бы НИ НА ОДНОМ
    транспорте — то есть маршрут числился бы пройденным там, где пройден
    наполовину.
    """
    route = _route_by_key(ACCOUNT_GROUP_ROUTE_KEY)
    await _identify(client, route.identity, test_settings)

    # Состояние готовится ЗАНОВО на каждую половину: удаление необратимо, и
    # вторая половина на уже опустевшем экране проверяла бы не ту ветку.
    degraded = await _arrange_account_group_last(
        client, db_session, test_settings, route.identity
    )
    expected = f"/accounts/{degraded.landing_args['account_id']}/groups"
    without = await client.post(
        degraded.url, data=degraded.data, follow_redirects=False
    )
    assert without.status_code == 302, (
        f"{route.name}: путь деградации опустевшей выдачи ответил "
        f"{without.status_code} вместо 302 — человек без JavaScript остался бы "
        "без ответа"
    )
    assert without.headers["location"] == expected, (
        f"{route.name}: адрес деградации {without.headers['location']!r} не "
        f"совпал с ожидаемым {expected!r} ПОСИМВОЛЬНО"
    )

    arranged = await _arrange_account_group_last(
        client, db_session, test_settings, route.identity
    )
    expected = f"/accounts/{arranged.landing_args['account_id']}/groups"
    with_layer = await client.post(
        arranged.url,
        data=arranged.data,
        headers=HTMX_HEADERS,
        follow_redirects=True,
    )
    assert with_layer.status_code == 204, (
        f"{route.name}: опустевшая выдача ответила слою письма "
        f"{with_layer.status_code} вместо 204. Код 200 здесь означал бы, что "
        "экран закрылся ВТОРОЙ отрисовкой пустого состояния, а три различимых "
        "пустых состояния живут в `account_groups/list.html` в одном экземпляре "
        "(D-09)"
    )
    assert with_layer.headers["HX-Location"] == expected, (
        f"{route.name}: заголовок перехода "
        f"{with_layer.headers['HX-Location']!r} не совпал с адресом деградации "
        f"{expected!r}"
    )
    assert with_layer.text == "", (
        f"{route.name}: у ответа 204 появилось тело — у этого статуса тела нет "
        "по определению"
    )
    assert DOCUMENT_MARK not in with_layer.text


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


def _fragment_routes() -> list[_Route]:
    """ВСЕ фрагментные маршруты перечня. Отбор идёт по ПОЛЮ ЗАПИСИ.

    Поле, а не имя: имя сменилось бы правкой строки, и отбор молча перестал бы
    иметь предмет.
    """
    return [route for route in CONFIRMED_DELETE_ROUTES if route.htmx_form is FRAGMENT]


def _the_fragment_route() -> _Route:
    """Фрагментный маршрут УДАЛЕНИЯ РАСПИСАНИЯ — предмет правила ниже.

    ⚠️ ПРЕЖНЕЕ ОСНОВАНИЕ ЭТОГО ПОМОЩНИКА НЕ ВЫЧЁРКИВАЕТСЯ, А ПЕРЕПИСЫВАЕТСЯ, И
    РАЗНИЦА НЕ РЕДАКТОРСКАЯ (образец обращения с отменённой формулировкой —
    записи D-30 и D-32 `.planning/STATE.md`). Здесь стояло: «ЕДИНСТВЕННЫЙ
    фрагментный маршрут фазы», а отбор шёл по полю формы ответа с отказом
    «появление второго означает, что решение о его форме ответа принято, а о
    неотличимости его повтора — нет». Утверждение было ВЕРНО ДЛЯ СОСТАВА ПЕРЕЧНЯ,
    КОТОРЫЙ ОНО ПЕРЕЖИЛО: фрагментный маршрут был один. План 10-11 внёс второй
    (удаление группы аккаунта), и отказ сработал ровно так, как был написан, —
    он назвал НЕПРИНЯТОЕ РЕШЕНИЕ, а не поломку.

    ⚠️ ЧТО ИЗМЕНИЛОСЬ, А ЧТО ОСТАЛОСЬ. Изменился МЕХАНИЗМ: маршрут выбирается по
    КЛЮЧУ ЗАПИСИ, потому что поле формы ответа с появлением второго фрагментного
    маршрута перестало быть различающим. Осталось СУЩЕСТВО: второй фрагментный
    маршрут обязан принести СВОЁ решение о неотличимости повтора — и это больше
    не подразумевается отказом этого помощника, а утверждается отдельным
    правилом `test_every_fragment_route_has_an_accepted_repeat_decision`, которое
    называет поимённо маршруты без решения.
    """
    return _route_by_key(SCHEDULE_ROUTE_KEY)


# ⚠️ ФРАГМЕНТНЫЕ МАРШРУТЫ, У КОТОРЫХ ЕСТЬ СВОЁ ПРАВИЛО НЕОТЛИЧИМОСТИ ПОВТОРА.
# Ключ записи → имя правила, которое это свойство утверждает. Имя правила стоит
# ЗНАЧЕНИЕМ, а не подразумевается: отказ обязан говорить читателю, ГДЕ смотреть,
# а перечень без имён превратился бы в множество ключей, о которых нельзя
# сказать, чем именно они накрыты.
#
# ПОЧЕМУ ПЕРЕЧЕНЬ, А НЕ ПОИСК ПО ИМЕНАМ ФУНКЦИЙ МОДУЛЯ. Поиск по именам зеленел
# бы на любой функции, чьё имя похоже, — в том числе на отрицательном контроле, —
# и решение о повторе перестало бы быть РЕШЕНИЕМ, став совпадением строк.
FRAGMENT_REPEAT_RULED_ROUTES: dict[str, str] = {
    SCHEDULE_ROUTE_KEY: (
        "test_a_repeated_confirmed_delete_on_the_fragment_route_answers_the_same_shape"
    ),
    ACCOUNT_GROUP_ROUTE_KEY: (
        "test_a_repeated_confirmed_delete_on_the_account_group_route_"
        "answers_the_same_shape"
    ),
}


def test_every_fragment_route_has_an_accepted_repeat_decision():
    """У КАЖДОГО фрагментного маршрута решение о повторе ПРИНЯТО, а не подразумевается.

    ⚠️ ЭТО ПРАВИЛО ЗАМЕНЯЕТ СОБОЙ МОЛЧАЛИВОЕ ДОПУЩЕНИЕ, А НЕ ДОБАВЛЯЕТСЯ К НЕМУ.
    До плана 10-11 единственность фрагментного маршрута утверждал СВОИМ ОТКАЗОМ
    помощник выбора: «появление второго означает, что решение о его форме ответа
    принято, а о неотличимости его повтора — нет». Пока маршрут был один, это
    работало; со вторым — упало бы, назвав непринятое решение, но не сказав, что
    считать принятым. Здесь сказано: решение принято, если у маршрута есть СВОЁ
    правило повтора ЛИБО запись перечня изъятий с основанием. Третьего пути нет.

    ⚠️ ДВА СПОСОБА ПРИНЯТЬ РЕШЕНИЕ РАЗЛИЧНЫ ПО СУЩЕСТВУ, А НЕ ПО УДОБСТВУ.
    Правило означает «повтор здесь неотличим, и вот чем это проверено»; изъятие
    означает «повтор здесь не является повтором удаления, и вот почему». Первое
    утверждает свойство, второе объясняет его отсутствие; пустого пересечения
    между ними правило не требует — требуется, чтобы КАЖДЫЙ фрагментный маршрут
    попал хотя бы в одно.

    ⚠️ АНТИВАКУУМ ОБЯЗАТЕЛЕН. Пустое множество фрагментных маршрутов сошлось бы с
    любым перечнем решений, и правило зеленело бы независимо от предмета.
    """
    fragment_keys = {route.key for route in _fragment_routes()}
    assert fragment_keys, (
        "фрагментных маршрутов в перечне НЕТ НИ ОДНОГО. Пустое множество сходится "
        "с любым перечнем решений, и правило зеленеет независимо от предмета — а "
        "заодно теряет предмет правило неотличимости повтора на фрагментной ветке"
    )

    decided = set(FRAGMENT_REPEAT_RULED_ROUTES) | set(REPEAT_EXEMPT_ROUTES)
    undecided = sorted(fragment_keys - decided)
    assert not undecided, (
        "у фрагментного маршрута решение о неотличимости его повтора НЕ ПРИНЯТО:\n"
        "  " + "\n  ".join(undecided) + "\n\nРешение принимается ОДНИМ ИЗ ДВУХ: "
        "своим правилом повтора (запись в `FRAGMENT_REPEAT_RULED_ROUTES`) либо "
        "записью перечня изъятий с основанием НА ЗАПИСЬ (`REPEAT_EXEMPT_ROUTES`, "
        "и тогда двигается объявленное число изъятий). Маршрут без решения — "
        "ровно то состояние, ради которого это правило и стои́т"
    )

    stray = sorted(set(FRAGMENT_REPEAT_RULED_ROUTES) - fragment_keys)
    assert not stray, (
        "правило повтора объявлено для маршрута, который фрагментным НЕ ЯВЛЯЕТСЯ "
        "или выпал из перечня:\n  " + "\n  ".join(stray) + "\n\nТакая запись лжёт "
        "о составе множества и молча закрывает собой другой маршрут, если ключ "
        "когда-нибудь совпадёт"
    )

    blank = sorted(
        key for key, rule in FRAGMENT_REPEAT_RULED_ROUTES.items() if not rule.strip()
    )
    assert not blank, (
        "правило повтора объявлено БЕЗ ИМЕНИ:\n  " + "\n  ".join(blank) + "\n\nОтказ "
        "обязан говорить читателю, где смотреть; перечень без имён — множество "
        "ключей, о которых нельзя сказать, чем они накрыты"
    )

    # ⚠️ ИМЯ ПРАВИЛА СЛИЧАЕТСЯ С МОДУЛЕМ, А НЕ ПРИНИМАЕТСЯ НА ВЕРУ. Запись,
    # называющая правило, которого нет, объявляет решение принятым ровно там, где
    # оно не принято, — то есть делает этот перечень местом, где проверка
    # выключается молча. Ровно тот отказ, ради которого перечень и заведён.
    absent = sorted(
        f"{key} → {rule}"
        for key, rule in FRAGMENT_REPEAT_RULED_ROUTES.items()
        if not callable(globals().get(rule))
    )
    assert not absent, (
        "перечень называет правило повтора, которого в модуле НЕТ:\n  "
        + "\n  ".join(absent) + "\n\nРешение объявлено принятым, а утверждать его "
        "нечем"
    )


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


# =============================================================================
# РЕБРО ИДЕМПОТЕНТНОСТИ НА ВТОРОМ ФРАГМЕНТНОМ МАРШРУТЕ — УДАЛЕНИЕ ГРУППЫ АККАУНТА
# =============================================================================
#
# ⚠️ РЕШЕНИЕ О НЕОТЛИЧИМОСТИ ПОВТОРА ЗДЕСЬ ПРИНЯТО ПО ПУТИ ПРАВИЛА, А НЕ ПО ПУТИ
# ИЗЪЯТИЯ, И ВЫВЕДЕНО ОНО ЧТЕНИЕМ ОБРАБОТЧИКА, А НЕ ПО АНАЛОГИИ С МАРШРУТОМ
# РАСПИСАНИЯ. Основание выписано в самом обработчике
# (`app/pages/account_groups.py::account_groups_delete`) дословно:
#
#   «класс "строка не найдена" неразличим изнутри БЕЗ отдельной оговорки — ответ
#    у всех четырёх случаев (найденная, чужая, несуществующая, УЖЕ УДАЛЁННАЯ)
#    собирается из `group_id` пути и совпадает побайтно»
#
# и во вложенной сборке фрагмента:
#
#   «ТЕЛО СОБИРАЕТСЯ ИЗ `group_id` ПУТИ, А НЕ ИЗ НАЙДЕННОЙ СТРОКИ. Строки к этому
#    месту уже нет ни в одном случае: либо она удалена, либо её и не было. Узлы
#    снятия уезжают И ТОГДА, когда тройной `WHERE` не нашёл строки, — этого
#    ТРЕБУЕТ неотличимость (D-04-A)»
#
# Случай «УЖЕ УДАЛЁННАЯ» назван обработчиком ПОИМЁННО — это и есть повтор.
# Предикат включения перечня изъятий (`REPEAT_EXEMPT_ROUTES`) сюда не подходит ни
# одной половиной: действие УНИЧТОЖАЕТ адресуемую строку, заново ничего не
# запускает и личности не меняет. Значит путь один — правило.
#
# ⚠️ ПО АНАЛОГИИ С МАРШРУТОМ РАСПИСАНИЯ РЕШЕНИЕ ПРИНЯТЬ БЫЛО НЕЛЬЗЯ, И ЭТО НЕ
# ФОРМАЛЬНОСТЬ. У них РАЗНЫЕ источники контекста экрана (там — поле `ad_id` тела
# формы с запасным чтением из строки, здесь — `account_id` ПУТИ и строка поиска
# тела) и РАЗНЫЕ побочные области ответа (там три узла расписания, здесь снятие
# строки, снятие панели и содержимое линейки счётчика). Совпадение вывода не
# делает совпадающими доводы.
#
# ⚠️ ВЕТКА ОТВЕТА ЗДЕСЬ ЗАВИСИТ ОТ СОСТОЯНИЯ ВЫДАЧИ, ПОЭТОМУ ПОВТОР ОБЯЗАН
# ОСТАТЬСЯ НА ТОЙ ЖЕ ВЕТКЕ. Расстановка сеет ДВЕ строки: после первого удаления
# выдача не пуста, и повтор идёт фрагментом — тем же, что и первое удаление.
# Расстановка с одной строкой увела бы повтор в ветку перехода, и правило
# сличало бы СМЕНУ ВЕТКИ, выдавая её за различимость ответов.


def _addressed_group_id(arranged: _Arranged) -> tuple[int, int]:
    """`(account_id, group_id)` — ИЗ АДРЕСА расстановки, а не вторым посевом.

    Второй посев ради того, чтобы «узнать номер», был бы второй копией посева, а
    он несёт несущую тонкость (вторая группа оставляет выдачу непустой, иначе
    маршрут уходит в ветку перехода и фрагмента не было бы вовсе).
    """
    parts = arranged.url.strip("/").split("/")
    assert (
        len(parts) == 5
        and parts[0] == "accounts"
        and parts[2] == "groups"
        and parts[-1] == "delete"
    ), (
        f"адрес расстановки {arranged.url!r} перестал быть адресом удаления "
        "группы аккаунта — идентификаторы из него читать больше нельзя"
    )
    return int(parts[1]), int(parts[3])


def _expected_group_oob_ids(group_id: int) -> set[str]:
    """Три внеполосных узла ответа, названные ПОИМЁННО по разметке.

    Два из трёх СОБИРАЮТСЯ ИЗ ИДЕНТИФИКАТОРА ПОСЕВА, а не выписаны литералами:
    литерал разошёлся бы с посевом при первом же изменении последовательности
    идентификаторов, и правило зеленело бы на чужих узлах.

    ⚠️ ТРЕТИЙ — СТАТИЧЕСКИЙ СЕЛЕКТОР, И ЭТО ИЗМЕРЕННЫЙ ФАКТ РАЗМЕТКИ, А НЕ
    ПОСЛАБЛЕНИЕ. Узел линейки счётчика адресует цель `innerHTML:#account-groups-
    count` и собственного `id` не несёт вовсе
    (`account_groups/partials/count_rule_oob.html`): собирать его «из посева» было
    бы нечем, а разойтись с посевом он не может по построению.
    """
    return {
        f"group-row-{group_id}",
        f"group-del-{group_id}",
        "#account-groups-count",
    }


@pytest.mark.asyncio
async def test_a_repeated_confirmed_delete_on_the_account_group_route_answers_the_same_shape(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Повтор удаления группы аккаунта отвечает ТОЙ ЖЕ формой, что и первое.

    ⚠️ ЧЕМ ЭТО ОТЛИЧАЕТСЯ ОТ ПРАВИЛА МАРШРУТА РАСПИСАНИЯ — ЧИТАТЬ ДО ТОГО, КАК
    СНЯТЬ ОДНО ИЗ ДВУХ КАК ДУБЛИКАТ. Форма правил общая намеренно, а предметы
    разные: там ответ собирается вокруг `ad_id`, приехавшего ТЕЛОМ формы, и
    сличаются три узла расписания; здесь — вокруг `group_id` и `account_id` ПУТИ,
    и сличаются снятие строки, снятие панели и содержимое линейки счётчика.
    Совпадение ответов на одном маршруте не говорит ничего о другом.

    ⚠️ ЧЕМ ЭТО ОТЛИЧАЕТСЯ ОТ ПРАВИЛА НЕСУЩЕСТВУЮЩЕГО ИДЕНТИФИКАТОРА. Там
    идентификатор не существовал НИКОГДА, адрес нёс несуществующий аккаунт, и
    ответ есть переход. Здесь строка СУЩЕСТВОВАЛА И БЫЛА УДАЛЕНА ПРЕДЫДУЩИМ
    ЗАПРОСОМ ЭТОГО ЖЕ ЧЕЛОВЕКА, а ответ есть фрагмент.

    ⚠️ ПРАВИЛО ЗЕЛЕНО ПЕРВЫМ ЖЕ ПРОГОНОМ, И ЭТО ОЖИДАЕМО: свойство сегодня
    ДЕРЖИТСЯ, обработчик объявляет его о себе прямо. Зубы ему даёт не переход
    цвета, а отрицательный контроль ниже.
    """
    route = _route_by_key(ACCOUNT_GROUP_ROUTE_KEY)
    outcome = route.outcomes[0]
    await _identify(client, route.identity, test_settings)

    arranged = await outcome.arrange(client, db_session, test_settings, route.identity)
    account_id, group_id = _addressed_group_id(arranged)

    # АНТИВАКУУМ ДО: адресуемая строка ЕСТЬ. Состояние читается ЗАПРОСОМ К БАЗЕ, а
    # не выводится из ответа: ответ и есть предмет сличения.
    db_session.expire_all()
    assert await db_session.get(Group, group_id) is not None, (
        f"адресуемой группы {group_id} не было в базе ДО первого запроса — тогда "
        "«повтор» неотличим от второй попытки первого, и правило утверждало бы не "
        "то, чем называется"
    )

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
        after_first = await db_session.get(Group, group_id)
        # АНТИВАКУУМ ВЕТКИ: выдача НЕ ОПУСТЕЛА, иначе повтор ушёл бы переходом, и
        # сличалась бы смена ветки, а не различимость ответов.
        rows_after_first = await _listing_rows(
            db_session, (await _current_user(db_session, route.identity, test_settings)).id,
            account_id,
        )
        repeat = await client.post(
            arranged.url,
            data=arranged.data,
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )

    assert after_first is None, (
        f"группа {group_id} осталась в базе ПОСЛЕ первого запроса — второй запрос "
        "не является повтором удаления, и вся форма правила разговаривает не о том "
        "предмете"
    )
    assert rows_after_first >= 1, (
        f"выдача аккаунта {account_id} опустела после первого удаления (строк "
        f"{rows_after_first}) — повтор ушёл бы в ветку перехода, и правило сличало "
        "бы СМЕНУ ВЕТКИ, выдавая её за различимость ответов"
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
    expected = _expected_group_oob_ids(group_id)

    # АНТИВАКУУМ МНОЖЕСТВА: пустое множество, равное пустому, зеленело бы
    # независимо от предмета.
    assert first_ids == expected, (
        f"внеполосные узлы первого удаления {sorted(first_ids)} не совпали с "
        f"ожидаемыми {sorted(expected)} — три узла ответа названы поимённо по "
        "разметке `account_groups/partials/delete_response.html`"
    )
    assert repeat_ids == first_ids, (
        f"внеполосные узлы повтора {sorted(repeat_ids)} отличны от узлов первого "
        f"удаления {sorted(first_ids)}. Различимость ответов позволяет "
        "ПЕРЕЧИСЛЯТЬ занятые идентификаторы, ничего не удаляя (T-10-34)"
    )


@pytest.mark.asyncio
async def test_control_negative_a_shifted_group_identifier_reddens_the_sameness_check(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ правила выше: другой идентификатор — другое множество.

    ⚠️ ПРАВИЛО ПОВТОРА БЕЗ СОБСТВЕННОГО КОНТРОЛЯ ЗАИМСТВУЕТ ЗУБЫ У СОСЕДНЕГО.
    Контроль маршрута расписания стережёт СВОЁ множество узлов и о разметке
    ответа удаления группы не говорит ничего: сличение, совпадающее ВСЕГДА,
    зелено независимо от предмета — и именно такой зелени в этой партии не
    остаётся.

    ⚠️ ПОЧЕМУ ЗДЕСЬ СЕЕТСЯ ТРЕТЬЯ СТРОКА. Расстановка сеет ДВЕ, и удаление второй
    оставило бы выдачу пустой — обработчик ушёл бы в ветку перехода (D-09),
    ответил бы 204 без тела, и множество оказалось бы ПУСТЫМ. Сличение «три узла
    против ничего» доказывало бы смену ВЕТКИ, а не чувствительность к
    идентификатору, то есть ровно тот класс вакуумной зелени, ради которого
    контроль и заведён. Третья строка держит третий запрос НА ТОЙ ЖЕ ФРАГМЕНТНОЙ
    ВЕТКЕ: форма ответа та же, различаться обязаны ИМЕННО идентификаторы.
    """
    route = _route_by_key(ACCOUNT_GROUP_ROUTE_KEY)
    outcome = route.outcomes[0]
    await _identify(client, route.identity, test_settings)

    arranged = await outcome.arrange(client, db_session, test_settings, route.identity)
    account_id, group_id = _addressed_group_id(arranged)

    db_session.expire_all()
    others = (
        await db_session.execute(
            select(Group)
            .where(Group.account_id == account_id, Group.id != group_id)
            .order_by(Group.id)
        )
    ).scalars().all()
    assert others, (
        f"у аккаунта {account_id} нет ВТОРОЙ посеянной группы — контролю нечего "
        "адресовать, и он выродился бы в повторение несущего правила"
    )
    other = others[0]
    # Сеялка та же, аккаунт тот же: второй расстановки не заводится.
    await _seed_account_group(
        db_session, await db_session.get(MessengerAccount, account_id), "Гамма",
        user_id=other.user_id,
    )

    other_url = f"/accounts/{account_id}/groups/{other.id}/delete"
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
        f"контроль ответил {shifted.status_code}, повтор {repeat.status_code} — "
        "ответы разошлись ВЕТКОЙ, и различие множеств доказывало бы смену ветки, "
        "а не чувствительность к идентификатору"
    )
    assert repeat_ids, (
        "множество внеполосных узлов повтора ПУСТО — сличение пустого с непустым "
        "зелено независимо от предмета"
    )
    assert shifted_ids, (
        "множество внеполосных узлов контроля ПУСТО — см. выше"
    )
    assert shifted_ids != repeat_ids, (
        f"ответ на ДРУГОЙ идентификатор дал ТО ЖЕ множество {sorted(shifted_ids)}, "
        f"что и повтор {sorted(repeat_ids)}. Значит сличение множеств совпадает "
        "ВСЕГДА, и несущее правило зелено независимо от предмета"
    )
    assert shifted_ids == _expected_group_oob_ids(other.id), (
        f"внеполосные узлы контроля {sorted(shifted_ids)} не совпали с ожидаемыми "
        f"для группы {other.id} — контроль изменил ЧТО-ТО, но не то, что "
        "называется"
    )
    assert first.status_code == 200, (
        f"первое удаление ответило {first.status_code} вместо 200 — предметом "
        "сличения перестал быть фрагментный ответ"
    )


# =============================================================================
# НЕГОДНАЯ ВЕЛИЧИНА ПОЛЯ КОНТЕКСТА — БЛОКЕР `CR-01` ОТЧЁТА ВЕРИФИКАЦИИ
# =============================================================================
#
# ⚠️ ЧТО ИМЕННО ЗДЕСЬ ПРОВЕРЯЕТСЯ И ЧЕМ ЭТО ОТЛИЧАЕТСЯ ОТ СОСЕДНИХ ПРАВИЛ.
# Соседние правила утверждают, что ответ на НЕСУЩЕСТВУЮЩИЙ и на ПОВТОРНЫЙ
# идентификатор неотличим от ответа на успех. Здесь предмет другой: поле
# контекста экрана (`ad_id`) приходит ТЕЛОМ формы, коэрция ограничивает его ТИП
# и не ограничивает ВЕЛИЧИНУ, а результат уезжает операндом в сравнение
# `Schedule.ad_id == ad_id`. Величина вне диапазона колонки роняла обработчик
# драйвером БД — то есть давала ЧЕТВЁРТУЮ форму ответа (500), которой фаза себе
# не объявляла, и прямо опровергала инвариант модуля правил редактора
# (`tests/test_pages/test_editor_schedules.py`: «прямой POST мимо браузера
# обязан давать отказ валидации, а не 500», T-02-24 / T-02-25).
#
# ⚠️ ПОЧЕМУ АДРЕС ЗАПРОСА — НЕСУЩЕСТВУЮЩАЯ СТРОКА. Поле контекста работает
# ЗАПАСНЫМ источником и вступает в дело ТОЛЬКО там, где строки нет (записанный
# приоритет `_ad_id_from_form`). На живой строке величина из формы не читается
# вовсе, и правило не имело бы предмета.
#
# ⚠️ АБЗАЦ ВЫШЕ НЕ ВЫЧЁРКНУТ, А ПОМЕЧЕН ОПРОВЕРГНУТЫМ В ТОЙ ЧАСТИ, В КОТОРОЙ
# ОКАЗАЛСЯ ЛОЖНЫМ (идиома D-30/D-32 `.planning/STATE.md`: опровергнутое стои́т
# РЯДОМ с истинным, а не стирается). Он ВЕРЕН ДОСЛОВНО для СВОЕГО предмета —
# запасного источника контекста: правилу оси ТЕЛА нужна строка, которой нет, и
# величина адреса у него обязана быть ВНУТРИ диапазона колонки, иначе запрос
# отвергается раньше, чем поле контекста вообще читается, и правило теряет
# предмет. ОПРОВЕРГНУТО другое — ЧТЕНИЕ «раз адрес зашит, маршрут накрыт
# целиком». Замер верификатора третьего круга, воспроизведённый на маршруте
# подтверждённого удаления, показал: те же пять величин едут и ВТОРОЙ осью —
# идентификатором пути `POST /schedules/{schedule_id}/delete`, — и по ней
# матрица не прогонялась ВОВСЕ. Хуже: `MISSING_SCHEDULE_URL` лежит ВНУТРИ
# диапазона колонки, то есть на заведомо годном пути запроса, и правило оси тела
# зеленело одинаково на починенном дереве и на сломанном в половине своего
# предмета. Закрыто ниже: вторая константа адреса ВНЕ диапазона
# (`OUT_OF_RANGE_SCHEDULE_URL`), прогон матрицы по оси адреса и объявленное
# число осей. Свести две константы в одну НЕЛЬЗЯ НИ В КАКУЮ СТОРОНУ — это не
# дублирование, а два разных предмета, и разделение записано у каждой.

# Пять негодных значений поля контекста. Перечень взят из `gaps[0].missing`
# отчёта верификации ДОСЛОВНО, и каждое значение ломает СВОЁ:
UNUSABLE_AD_ID_VALUES: tuple[str, ...] = (
    # ВЕЛИЧИНА: коэрция принимает, значение доезжает до драйвера БД и роняет
    # запрос (`OverflowError` на SQLite, `DataError` вне диапазона int32 на
    # PostgreSQL) — это и есть воспроизведённый блокер.
    "9" * 25,
    # ДОМЕН: в колонке автоинкремента таких идентификаторов не бывает, но АДРЕС
    # приземления до правки собирался ИЗ НИХ — `/ads/-1/edit`.
    "-1",
    # ДОМЕН, вторая половина: `/ads/0/edit` — тот же бессмысленный адрес.
    "0",
    # ФОРМА ЗАПИСИ: `int()` её отвергает уже сегодня, значение до запроса не
    # доходит. Стоит в перечне затем, чтобы граница величины не выдавалась за
    # починку того, что и так работало.
    "1e3",
    # ЛОВУШКА ЧИТАТЕЛЯ: подчёркивание внутри числа `int()` ПРИНИМАЕТ
    # (`int("1_0") == 10`), и значение доезжает до запроса ГОДНЫМ. Правило,
    # объявившее все пять «негодными», молча утверждало бы неверное — поэтому
    # ожидаемый исход у этого значения СВОЙ.
    "1_0",
)

# Адрес заведомо несуществующей строки: предмет — ЗАПАСНОЙ источник контекста.
#
# ⚠️ ПРЕДМЕТ ЭТОЙ КОНСТАНТЫ — ОСЬ ТЕЛА, И ВЕЛИЧИНА ЕЁ АДРЕСА ОБЯЗАНА ЛЕЖАТЬ
# ВНУТРИ ДИАПАЗОНА КОЛОНКИ. Величина вне диапазона отвергалась бы псевдонимом
# `ScheduleIdPath` до входа в тело обработчика, поле контекста не читалось бы
# вовсе, и правило оси тела осталось бы без предмета. Ниже стои́т ВТОРАЯ
# константа — с величиной ВНЕ диапазона, — и она нужна оси АДРЕСА. Свести их в
# одну нельзя ни в какую сторону: приведи эту к величине вне диапазона — ось
# тела перестанет доходить до поля контекста; приведи ту к величине внутри
# диапазона — ось адреса перестанет доставать до границы величины, ради которой
# заведена. Разбор — помеченный опровергнутым абзац выше.
MISSING_SCHEDULE_URL = "/schedules/999999/delete"


def _unusable_path_url(value: str) -> str:
    """Адрес маршрута удаления, собранный из подаваемой величины СТРОКОЙ.

    Строкой, а не числом: величина из двадцати пяти девяток, приведённая к
    `int` здесь, приехала бы на маршрут уже нормализованной, и первое приведение
    спрятало бы предмет — ровно то основание, по которому тело оси тела шлётся
    сырой строкой (`_unusable_ad_id_body`).
    """
    return f"/schedules/{value}/delete"


def _int_or_none(value: str) -> int | None:
    """Как величину читает коэрция маршрута — ИЗМЕРЕНИЕМ, а не рассуждением."""
    try:
        return int(value)
    except ValueError:
        return None


def _the_out_of_range_value() -> str:
    """ЕДИНСТВЕННАЯ величина перечня, лежащая ВНЕ диапазона колонки.

    ⚠️ ВЫБИРАЕТСЯ ИЗ ПЕРЕЧНЯ, А НЕ ВЫПИСЫВАЕТСЯ ВТОРЫМ ЛИТЕРАЛОМ. Второй литерал
    разошёлся бы с первым МОЛЧА: правка перечня оставила бы адрес прежним, и
    правило оси адреса продолжало бы зеленеть, стережа величину, которой в
    перечне уже нет. Отбор идёт по СВОЙСТВУ величины — по той самой границе
    `ID_MAX`, которую поставил план 10-12, — а не по месту в перечне: индекс
    сдвинулся бы прибавкой шестой величины и утащил бы предмет за собой.
    """
    outside = [
        value
        for value in UNUSABLE_AD_ID_VALUES
        if (parsed := _int_or_none(value)) is not None and parsed > ID_MAX
    ]
    assert len(outside) == 1, (
        f"величин ВНЕ диапазона колонки в перечне {len(outside)}: {outside}. "
        "Ось адреса требует РОВНО ОДНУ: ни одной — и константа адреса вне "
        "диапазона собирается не из чего, а правило оси адреса теряет предмет "
        "(именно эта слепая зона и закрывается); двух и более — и выбор между "
        "ними стал бы молчаливым"
    )
    return outside[0]


def _the_coercible_value() -> str:
    """ЕДИНСТВЕННАЯ величина перечня, которую коэрция маршрута ПРИНИМАЕТ.

    Отбирается тем же способом и по тому же основанию, что и величина выше: по
    свойству самой величины, а не по месту в перечне. Её исход по оси адреса
    ОТЛИЧАЕТСЯ от исхода остальных четырёх, и правило, объявившее все пять
    «негодными для маршрута», молча утверждало бы неверное.
    """
    inside = [
        value
        for value in UNUSABLE_AD_ID_VALUES
        if (parsed := _int_or_none(value)) is not None and 1 <= parsed <= ID_MAX
    ]
    assert len(inside) == 1, (
        f"величин, принимаемых коэрцией маршрута, в перечне {len(inside)}: "
        f"{inside}. Ожидается РОВНО ОДНА — ловушка читателя `1_0`; изменение "
        "числа означает, что состав перечня или граница величины сдвинулись, а "
        "отображение ожидаемых исходов оси адреса об этом не узнало"
    )
    return inside[0]


# ⚠️ ВТОРАЯ КОНСТАНТА АДРЕСА: ВЕЛИЧИНА ВНЕ ДИАПАЗОНА КОЛОНКИ, и её предмет —
# ось АДРЕСА. Основание: константа гейта, выбранная ВНУТРИ диапазона, за которым
# живёт дефект, делает правило неспособным до дефекта ДОЙТИ, и такое правило
# зеленеет одинаково на починенном дереве и на сломанном. Предъявлять его прогон
# доводом закрытия нельзя — предупреждение таблицы Anti-Patterns отчёта
# верификации третьего круга, строка `:2272` этого файла.
OUT_OF_RANGE_PATH_ID_VALUE = _the_out_of_range_value()
OUT_OF_RANGE_SCHEDULE_URL = _unusable_path_url(OUT_OF_RANGE_PATH_ID_VALUE)

# Величина, которую коэрция принимает, и число, в которое она превращается.
# Ожидаемый исход этой величины по оси адреса собран ИЗ НЕГО.
COERCIBLE_PATH_ID_VALUE = _the_coercible_value()
COERCED_PATH_ID = int(COERCIBLE_PATH_ID_VALUE)

# Сводный список — экран, на который приземляется запрос без годного контекста.
SUMMARY_SCREEN = "/schedules"

# Тело шлётся СЫРОЙ строкой, а не отображением: значение из двадцати пяти
# девяток в отображении пришлось бы приводить к строке, и первое приведение
# спрятало бы предмет. Заголовок типа содержимого — обязательная часть сырого
# тела, иначе форма на сервере не разберётся.
FORM_CONTENT_TYPE = {"Content-Type": "application/x-www-form-urlencoded"}

# Признак возврата в редактор. Литерал стоит ЗДЕСЬ по тому же основанию, что и
# признак слоя письма (шапка модуля): единственность, которую держит веха, —
# единственность ЧТЕНИЯ признака приложением; здесь он ПИШЕТСЯ.
RETURN_TO_EDITOR_VALUE = "editor"

# Значение `1_0` коэрция принимает как 10, и адрес приземления собирается из
# него. Ожидаемые исходы ПОСЛЕ границы величины:
UNUSABLE_AD_ID_LANDINGS: dict[str, str] = {
    "9" * 25: SUMMARY_SCREEN,
    "-1": SUMMARY_SCREEN,
    "0": SUMMARY_SCREEN,
    "1e3": SUMMARY_SCREEN,
    "1_0": "/ads/10/edit",
}


def _unusable_ad_id_body(value: str) -> str:
    return f"return_to={RETURN_TO_EDITOR_VALUE}&ad_id={value}"


async def _post_with_context_field(client: AsyncClient, value: str):
    """Прямой POST мимо браузера на несуществующую строку с полем контекста.

    `follow_redirects=True` — часть предмета, а не удобство: ответ 302 пришёл бы
    сюда кодом 200 и телом чужого документа, и утверждение о форме ответа
    позеленеть на нём не может (записанное основание соседнего обхода).
    """
    return await client.post(
        MISSING_SCHEDULE_URL,
        content=_unusable_ad_id_body(value),
        headers={**HTMX_HEADERS, **FORM_CONTENT_TYPE},
        follow_redirects=True,
    )


@pytest.mark.parametrize("value", UNUSABLE_AD_ID_VALUES)
@pytest.mark.asyncio
async def test_an_unusable_ad_id_never_reaches_the_database(
    value, client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Негодная ВЕЛИЧИНА поля контекста не роняет обработчик и не заводит
    третьей формы ответа.

    ⚠️ ТРИ УТВЕРЖДЕНИЯ, И ВТОРОЕ НЕСУЩЕЕ НАРАВНЕ С ПЕРВЫМ. «Не 500» — дословный
    предмет гэпа; но одного его мало: обработчик, ответивший 4xx на негодное
    поле, тоже «не 500», а различимая по величине поля третья форма ответа
    вернула бы КАРТУ ЗАНЯТЫХ ИДЕНТИФИКАТОРОВ, запрещённую свойством T-10-07.
    Поэтому форма ответа сличается с ДВУМЯ объявленными фазой: 204 с заголовком
    перехода либо 200 с фрагментом. Третье утверждение — отсутствие целого
    документа — ловит прозрачно пройденное перенаправление.
    """
    route = _the_fragment_route()
    outcome = route.outcomes[0]
    await _identify(client, route.identity, test_settings)
    await outcome.arrange(client, db_session, test_settings, route.identity)

    response = await _post_with_context_field(client, value)
    landing = response.headers.get("HX-Location", "")

    assert response.status_code != 500, (
        f"значение {value!r} доехало до запроса и уронило обработчик: "
        f"код {response.status_code}, тело {response.text[:120]!r}. Это ЧЕТВЁРТАЯ "
        "форма ответа маршрута и прямое опровержение инварианта T-02-24 / "
        "T-02-25 («прямой POST мимо браузера даёт отказ валидации, а не 500»)"
    )

    if response.status_code == 204:
        assert landing, (
            f"значение {value!r}: ответ 204 пришёл БЕЗ заголовка перехода — "
            "человек остался бы на открытой панели и в тишине"
        )
        assert response.text == "", (
            f"значение {value!r}: у ответа 204 появилось тело — у этого статуса "
            "тела нет по определению"
        )
    elif response.status_code == 200:
        assert response.text.strip(), (
            f"значение {value!r}: фрагментная форма ответила пустым телом"
        )
    else:
        raise AssertionError(
            f"значение {value!r} получило ТРЕТЬЮ форму ответа: код "
            f"{response.status_code}, адрес приземления {landing!r}. Фаза "
            "объявила ДВЕ — 204 с заголовком перехода и 200 с фрагментом; "
            "различимая по величине поля третья вернула бы карту занятых "
            "идентификаторов (T-10-07)"
        )

    assert DOCUMENT_MARK not in response.text, (
        f"значение {value!r}: в ответе слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ — "
        "значит обработчик ответил перенаправлением, а клиент прошёл по нему"
    )


@pytest.mark.asyncio
async def test_the_landing_screen_is_never_assembled_from_a_rejected_context_field(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Отброшенная величина не собирает АДРЕС: приземление уходит на сводный
    список, а не на `/ads/<величина>/edit`.

    ⚠️ ЭТО ВТОРОЙ ДЕФЕКТ ТОГО ЖЕ КЛАССА, И БЕЗ ЭТОГО ПРАВИЛА ОН ОСТАЛСЯ БЫ.
    «Ошибку проглотили» и «величину отбросили» различает ровно адрес: до границы
    величины значения `-1` и `0` отвечали 204 с адресом `/ads/-1/edit` и
    `/ads/0/edit` — бессмысленным адресом, собранным из испорченного поля самого
    отправителя. ⚠️ ЭТО ИЗМЕНЕНИЕ ПОВЕДЕНИЯ НА ДВУХ ЗНАЧЕНИЯХ ИЗ ПЯТИ, и оно
    УТВЕРЖДАЕТСЯ здесь, а не обнаруживается следующим кругом верификации.

    ⚠️ ИСХОДЫ СНИМАЮТСЯ ВСЕ ПЯТЬ И СЛИЧАЮТСЯ ОТОБРАЖЕНИЕМ ЦЕЛИКОМ, а не по
    одному в цикле с ранним отказом: покрасневшее сличение обязано показать ВСЕ
    пять строк таблицы, иначе следующая правка чинится по одной строке за
    прогон.

    ⚠️ АНТИВАКУУМ ЗДЕСЬ ДВОЙНОЙ, и оба нужны. Без первого правило зеленело бы на
    помощнике, отбрасывающем ВСЁ: годное поле обязано по-прежнему давать
    фрагмент. Без второго — на помощнике, у которого адрес перестал собираться
    вовсе: годный идентификатор обязан по-прежнему приземлять в свой редактор.
    """
    route = _the_fragment_route()
    outcome = route.outcomes[0]
    await _identify(client, route.identity, test_settings)
    arranged = await outcome.arrange(client, db_session, test_settings, route.identity)
    live_ad_id = arranged.landing_args["ad_id"]
    user = await _current_user(db_session, route.identity, test_settings)

    # Значение `1_0` коэрция принимает как 10, и ожидаемый адрес собран из него.
    # Если объявление 10 в базе ЕСТЬ, ожидание перестаёт говорить о величине
    # поля и начинает говорить о живой записи.
    db_session.expire_all()
    assert await db_session.get(Ad, 10) is None, (
        "в базе есть объявление 10 — ожидаемый адрес `/ads/10/edit` перестал "
        "быть утверждением о ВЕЛИЧИНЕ поля и стал утверждением о живой записи"
    )

    observed: dict[str, tuple[int, str]] = {}
    for value in UNUSABLE_AD_ID_VALUES:
        response = await _post_with_context_field(client, value)
        observed[value] = (
            response.status_code,
            response.headers.get("HX-Location", ""),
        )

    expected = {value: (204, landing) for value, landing in UNUSABLE_AD_ID_LANDINGS.items()}
    assert observed == expected, (
        "исходы «значение → код и адрес приземления» разошлись с ожидаемыми.\n"
        f"  снято:    {observed}\n"
        f"  ожидалось: {expected}\n"
        "⚠️ Адрес, собранный из непроверенной величины поля (`/ads/-1/edit`, "
        "`/ads/0/edit`), — второй дефект класса CR-01: человек уезжает на "
        "бессмысленный адрес, собранный из его же испорченного поля"
    )

    # АНТИВАКУУМ 1: годное значение поля по-прежнему даёт ФРАГМЕНТ. Помощник,
    # отбрасывающий всё, покраснел бы здесь.
    usable = await _post_with_context_field(client, str(live_ad_id))
    assert usable.status_code == 200, (
        f"годное значение поля {live_ad_id} ответило {usable.status_code} вместо "
        "200 — граница величины отбросила ГОДНЫЙ идентификатор, то есть правило "
        "выше зеленело бы и на помощнике, возвращающем None всегда"
    )
    assert DOCUMENT_MARK not in usable.text and usable.text.strip(), (
        f"годное значение поля {live_ad_id} ответило не фрагментом"
    )

    # АНТИВАКУУМ 2: адрес ПРОДОЛЖАЕТ собираться из годного идентификатора.
    # Объявление без расписаний уходит в ветку перехода (D-04), и адрес виден
    # заголовком.
    empty_ad = await _seed_ad(db_session, user.id)
    landing_response = await _post_with_context_field(client, str(empty_ad.id))
    assert (
        landing_response.status_code == 204
        and landing_response.headers.get("HX-Location") == f"/ads/{empty_ad.id}/edit"
    ), (
        f"годный идентификатор {empty_ad.id} приземлил на "
        f"{landing_response.headers.get('HX-Location')!r} с кодом "
        f"{landing_response.status_code} вместо 204 и `/ads/{empty_ad.id}/edit` — "
        "адрес перестал собираться из годного поля вовсе, и правило выше "
        "утверждало бы «всё уходит на сводный список» вместо «негодное "
        "отбрасывается»"
    )


# =============================================================================
# ТЕ ЖЕ ПЯТЬ ВЕЛИЧИН ВТОРОЙ ОСЬЮ — АДРЕСОМ ЗАПРОСА (`CR-01`, второй `missing`)
# =============================================================================
#
# ⚠️ ЧЕМ ЭТА ОСЬ ОТЛИЧАЕТСЯ ОТ ОСИ ВЫШЕ И ПОЧЕМУ ОДНОЙ БЫЛО МАЛО. Выше те же
# пять величин едут ТЕЛОМ формы — полем контекста экрана. Здесь они едут
# АДРЕСОМ запроса — идентификатором пути `POST /schedules/{schedule_id}/delete`.
# Источник значения второй, величина та же, и до третьего круга верификации по
# этой оси не прогонялось НИЧЕГО: адрес был зашит константой ВНУТРИ диапазона
# колонки, то есть заведомо годным путём запроса.
#
# ⚠️ ПРЕДМЕТ ЗДЕСЬ — НЕ ГРАНИЦА ВЕЛИЧИНЫ, А СПОСОБНОСТЬ ПРАВИЛА ДО НЕЁ ДОСТАТЬ.
# Саму границу ставит план 10-12 псевдонимом `ScheduleIdPath` на стороне
# приложения; обработчики этими правилами не правятся ни на символ. Проверяемое
# свойство — что правило КРАСНЕЕТ на дереве, где дефект жив: показано мутацией
# границы (снятой и возвращённой внутри задачи), а не заявлено прозой.
#
# ⚠️ ТЕЛО ЗАПРОСА ЗДЕСЬ НЕСЁТСЯ ГОДНЫМ, И ЭТО НЕСУЩЕЕ. Испорченное тело рядом с
# испорченным адресом проверяло бы ОБЕ оси разом и не утверждало бы ничего ни об
# одной: покрасневший исход нельзя было бы отнести ни к телу, ни к адресу.


def _usable_context_body(ad_id: int) -> str:
    """Тело формы с ГОДНЫМ полем контекста.

    Сборка тела ВВОЗИТСЯ у оси тела, а не переписывается вторым сборщиком:
    второй разошёлся бы с первым молча — то же основание, по которому в модуле
    ввозятся, а не копируются двойники и посевы. Имя `_unusable_ad_id_body`
    говорит о ПРЕДМЕТЕ оси тела; сюда в него подаётся ГОДНАЯ величина, потому
    что предмет оси адреса лежит в АДРЕСЕ.
    """
    return _unusable_ad_id_body(str(ad_id))


async def _post_with_path_identifier(client: AsyncClient, value: str, *, ad_id: int):
    """Прямой POST мимо браузера по оси АДРЕСА: величина едет ПУТЁМ.

    Форма отправки наследуется у оси тела целиком и по тем же основаниям: те же
    заголовки разметки, тот же тип содержимого сырого тела и то же прослеживание
    перенаправлений — ответ 302 пришёл бы сюда кодом 200 и телом чужого
    документа, и утверждение о форме ответа позеленеть на нём не может.
    """
    return await client.post(
        _unusable_path_url(value),
        content=_usable_context_body(ad_id),
        headers={**HTMX_HEADERS, **FORM_CONTENT_TYPE},
        follow_redirects=True,
    )


# ⚠️ ОЖИДАЕМЫЕ ИСХОДЫ ОСИ АДРЕСА: «величина → код и адрес приземления». У КАЖДОЙ
# ЗАПИСИ СВОЁ ОСНОВАНИЕ НА ЗАПИСЬ, И ЭТО НЕСУЩЕЕ ТРЕБОВАНИЕ, А НЕ УКРАШЕНИЕ.
# Снятый исход, записанный ожидаемым без объяснения, есть ОТПЕЧАТОК ПОВЕДЕНИЯ:
# он позеленел бы на любом поведении, которое случилось первым, и утверждением о
# продукте не стал бы. Поэтому у каждой величины названо, ЧТО именно её
# отвергает и почему исход именно такой.
UNUSABLE_PATH_ID_OUTCOMES: dict[str, tuple[int, str]] = {
    # ВЕЛИЧИНА. Отвергает ГРАНИЦА ВЕЛИЧИНЫ на стороне приложения: `le=ID_MAX`
    # псевдонима `ScheduleIdPath` (план 10-12). Отказ приходит ДО входа в тело
    # обработчика, то есть ДО любого обращения к базе, — поэтому исход есть
    # отказ валидации, а не пятисотый от драйвера БД. ⚠️ ИМЕННО ЭТА СТРОКА
    # КРАСНЕЕТ НА ДЕРЕВЕ БЕЗ ГРАНИЦЫ: там величина доезжает до запроса и роняет
    # обработчик (`OverflowError` на SQLite, `DataError` вне int32 на
    # PostgreSQL). Заголовка перехода у отказа валидации нет: его ставит слой
    # ответа, до которого запрос не доходит.
    "9" * 25: (422, ""),
    # ДОМЕН, первая половина. Отвергает НИЖНЯЯ граница `ge=1` того же
    # псевдонима: в колонке автоинкремента отрицательных идентификаторов не
    # бывает. Отказ приходит там же и по той же причине, что и у величины выше,
    # — а НЕ выборкой, не нашедшей строки: строка `-1` не искалась бы вовсе.
    "-1": (422, ""),
    # ДОМЕН, вторая половина. Та же нижняя граница `ge=1`: ноль в колонке
    # автоинкремента тоже не выдаётся. Стои́т отдельной строкой, а не «как выше»:
    # граница, съехавшая до `ge=0`, оставила бы `-1` красным и пропустила бы `0`,
    # и одна запись на две величины этого не показала бы.
    "0": (422, ""),
    # ФОРМА ЗАПИСИ. Отвергает КОЭРЦИЯ ТИПА, а не граница величины: `int()` эту
    # запись не читает (`type=int_parsing`), значение до сравнения с границей не
    # доходит. Стои́т в отображении затем, чтобы граница величины не выдавалась
    # за починку того, что и так работало: эта строка была бы `422` и на дереве
    # БЕЗ границы.
    "1e3": (422, ""),
    # ЛОВУШКА ЧИТАТЕЛЯ, И ЕЁ ИСХОД ОТЛИЧАЕТСЯ ОТ ЧЕТЫРЁХ ОСТАЛЬНЫХ. Подчёркивание
    # внутри числа коэрция ПРИНИМАЕТ (`int("1_0") == 10`, измерено), величина
    # укладывается в диапазон колонки и приезжает на маршрут ГОДНЫМ
    # идентификатором. Строки с таким номером в базе нет, поэтому маршрут уходит
    # в ветку НЕОТЛИЧИМОСТИ повтора подтверждённого удаления (T-10-07): ответ
    # совпадает с ответом на удаление живой чужой строки и есть ФРАГМЕНТ — 200 с
    # телом и без заголовка перехода, потому что у объявления тела запроса
    # расписания остались. ⚠️ ЗАПИСАТЬ ЗДЕСЬ 422 ЗНАЧИЛО БЫ ПОТРЕБОВАТЬ ОТ
    # МАРШРУТА ОТЛИЧАТЬ НЕСУЩЕСТВУЮЩИЙ ИДЕНТИФИКАТОР ОТ СУЩЕСТВУЮЩЕГО, то есть
    # выдавать карту занятых идентификаторов перебором по адресу.
    "1_0": (200, ""),
}


@pytest.mark.asyncio
async def test_an_unusable_path_identifier_never_reaches_the_database(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Негодная величина в АДРЕСЕ запроса не роняет обработчик и не заводит
    третьей формы ответа; исходы всех пяти сличаются отображением ЦЕЛИКОМ.

    ⚠️ ТРИ УТВЕРЖДЕНИЯ — ТЕ ЖЕ, ЧТО У ПРАВИЛА ОСИ ТЕЛА, И ПО ТЕМ ЖЕ ОСНОВАНИЯМ.
    «Не 500» — дословный предмет гэпа `CR-01`; одного его мало, потому что
    различимая ПО ВЕЛИЧИНЕ третья форма ответа вернула бы карту занятых
    идентификаторов (T-10-07), поэтому исход сличается с ДВУМЯ объявленными
    фазой формами (204 с заголовком перехода, 200 с фрагментом) ЛИБО с отказом
    валидации; третье — отсутствие целого документа — ловит прозрачно пройденное
    перенаправление.

    ⚠️ ЧЕТВЁРТОЙ ФОРМОЙ ОТВЕТА ЗДЕСЬ ЯВЛЯЕТСЯ И ОТКАЗ ВАЛИДАЦИИ, И ЭТО НЕ
    ПОСЛАБЛЕНИЕ. По оси ТЕЛА поле контекста необязательно и негодное
    ОТБРАСЫВАЕТСЯ (решение плана 10-08), поэтому там отказа валидации не бывает
    вовсе. По оси АДРЕСА идентификатор — ОБЯЗАТЕЛЬНЫЙ вход маршрута, и
    распоряжение негодной величиной различается ПО РОЛИ значения (записанное
    решение плана 10-12): обязательный вход отвечает отказом валидации. Отказ
    валидации карты идентификаторов не выдаёт — он одинаков для любой величины
    вне диапазона независимо от того, занята она или нет.

    ⚠️ ИСХОДЫ СНИМАЮТСЯ ВСЕ ПЯТЬ И СЛИЧАЮТСЯ ОТОБРАЖЕНИЕМ ЦЕЛИКОМ, а не по
    одному в цикле с ранним отказом: покрасневшее сличение обязано показать ВСЕ
    пять строк таблицы, иначе следующая правка чинится по одной строке за
    прогон. По той же причине нарушения трёх утверждений КОПЯТСЯ и называются
    одним сообщением.

    ⚠️ ЗУБЫ ЭТОГО ПРАВИЛА ПОКАЗАНЫ МУТАЦИЕЙ, А НЕ ЗАЯВЛЕНЫ. Со снятой границей
    `le=ID_MAX` первая строка отображения отвечает 500, и правило краснеет —
    вывод выписан в сводку плана 10-15. Правило, чья константа лежит ВНУТРИ
    диапазона, покраснеть не могло бы вовсе, и его зелёный прогон доводом
    закрытия не является.
    """
    route = _the_fragment_route()
    outcome = route.outcomes[0]
    await _identify(client, route.identity, test_settings)
    arranged = await outcome.arrange(client, db_session, test_settings, route.identity)
    live_ad_id = arranged.landing_args["ad_id"]

    # Величина, принимаемая коэрцией, приезжает на маршрут номером строки. Если
    # строка с таким номером ЕСТЬ, ожидание перестаёт говорить о ВЕЛИЧИНЕ и
    # начинает говорить о живой записи — и заодно удаляет её на прогоне.
    db_session.expire_all()
    assert await db_session.get(Schedule, COERCED_PATH_ID) is None, (
        f"в базе есть расписание {COERCED_PATH_ID} — ожидаемый исход величины "
        f"{COERCIBLE_PATH_ID_VALUE!r} перестал быть утверждением о ВЕЛИЧИНЕ "
        "адреса и стал утверждением о живой записи, которую прогон ещё и удалит"
    )

    observed: dict[str, tuple[int, str]] = {}
    complaints: list[str] = []
    for value in UNUSABLE_AD_ID_VALUES:
        response = await _post_with_path_identifier(client, value, ad_id=live_ad_id)
        landing = response.headers.get("HX-Location", "")
        observed[value] = (response.status_code, landing)

        if response.status_code == 500:
            complaints.append(
                f"  {value!r}: величина доехала до запроса и уронила обработчик "
                f"(500, тело {response.text[:120]!r}). Это ЧЕТВЁРТАЯ форма "
                "ответа маршрута и прямое опровержение инварианта T-02-24 / "
                "T-02-25 («прямой POST мимо браузера даёт отказ валидации, а не "
                "500») — теперь по оси АДРЕСА"
            )
        elif response.status_code == 204 and not landing:
            complaints.append(
                f"  {value!r}: ответ 204 пришёл БЕЗ заголовка перехода — человек "
                "остался бы на открытой панели и в тишине"
            )
        elif response.status_code == 200 and not response.text.strip():
            complaints.append(
                f"  {value!r}: фрагментная форма ответила пустым телом"
            )
        elif response.status_code not in (200, 204, 422):
            complaints.append(
                f"  {value!r}: ТРЕТЬЯ форма ответа — код {response.status_code}, "
                f"адрес приземления {landing!r}. Фаза объявила ДВЕ (204 с "
                "заголовком перехода и 200 с фрагментом) плюс отказ валидации "
                "для обязательного входа маршрута; различимая по величине "
                "третья вернула бы карту занятых идентификаторов (T-10-07)"
            )

        if DOCUMENT_MARK in response.text:
            complaints.append(
                f"  {value!r}: в ответе слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ — "
                "значит обработчик ответил перенаправлением, а клиент прошёл по "
                "нему"
            )

    # ⚠️ ОТЧЁТ ОДИН НА ОБА ПРЕДМЕТА, И ЭТО НЕ ЭКОНОМИЯ СТРОК. Два раздельных
    # утверждения означали бы РАННИЙ ОТКАЗ: первое покраснело бы и унесло с
    # собой всю таблицу исходов, а следующая правка чинилась бы по одному
    # предмету за прогон. Здесь и таблица ВСЕХ пяти строк, и ВСЕ названные
    # нарушения инварианта приезжают ОДНИМ сообщением.
    rows = "\n".join(
        f"  {value!r}: снято {observed[value]!r}, ожидалось "
        f"{UNUSABLE_PATH_ID_OUTCOMES.get(value)!r}"
        + (
            ""
            if observed[value] == UNUSABLE_PATH_ID_OUTCOMES.get(value)
            else "  <<< РАЗОШЛОСЬ"
        )
        for value in UNUSABLE_AD_ID_VALUES
    )
    assert observed == UNUSABLE_PATH_ID_OUTCOMES and not complaints, (
        "ОСЬ АДРЕСА: исходы «величина → код и адрес приземления» разошлись с "
        "ожидаемыми либо нарушен инвариант формы ответа.\n"
        "⚠️ ПОКАЗАНЫ ВСЕ ПЯТЬ СТРОК, а не первая разошедшаяся:\n"
        f"{rows}\n"
        + (
            "⚠️ НАРУШЕНИЯ ИНВАРИАНТА НАЗВАНЫ ВСЕ, а не первое:\n"
            + "\n".join(complaints)
            + "\n"
            if complaints
            else ""
        )
        + "⚠️ У каждой записи отображения есть ЗАПИСАННОЕ ОСНОВАНИЕ, что именно "
        "величину отвергает; исход, не укладывающийся в основание, есть "
        "изменение поведения продукта, а не повод подправить ожидание"
    )


@pytest.mark.asyncio
async def test_a_usable_path_identifier_still_answers_with_a_fragment(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """АНТИВАКУУМ ОСИ АДРЕСА: годный идентификатор ЖИВОЙ строки по-прежнему даёт
    фрагментную форму ответа.

    ⚠️ БЕЗ ЭТОЙ ПОЛОВИНЫ ПРАВИЛО ВЫШЕ ЗЕЛЕНЕЛО БЫ НА ПРИЛОЖЕНИИ, ОТВЕРГАЮЩЕМ
    ВСЁ: граница величины, съехавшая до `le=0`, дала бы отказ валидации на все
    пять величин отображения — и на живую строку тоже, — а «ни одна величина не
    роняет обработчик» осталось бы верным дословно. Вторая половина антивакуума
    живёт на оси ТЕЛА (`test_the_landing_screen_is_never_assembled_from_a_...`):
    годная величина ПОЛЯ по-прежнему приземляет в свой редактор. Нужны обе: без
    первой правило зеленеет на приложении, отвергающем всё; без второй — на
    приложении, у которого адрес перестал собираться вовсе.

    ⚠️ СВОИХ ПОСЕВОВ НЕ ЗАВОДИТСЯ: расстановка берётся действующим помощником
    фрагментного маршрута, и она же сеет ВТОРОЕ расписание — на последнем
    маршрут уходит в ветку перехода (D-04), и фрагмента у него не было бы вовсе.
    """
    route = _the_fragment_route()
    outcome = route.outcomes[0]
    await _identify(client, route.identity, test_settings)
    arranged = await outcome.arrange(client, db_session, test_settings, route.identity)
    live_ad_id = arranged.landing_args["ad_id"]

    with arranged.context():
        usable = await client.post(
            arranged.url,
            content=_usable_context_body(live_ad_id),
            headers={**HTMX_HEADERS, **FORM_CONTENT_TYPE},
            follow_redirects=True,
        )

    assert usable.status_code == 200, (
        f"годный идентификатор строки в АДРЕСЕ ({arranged.url}) ответил "
        f"{usable.status_code} вместо 200 — граница величины отвергает ГОДНОЕ, "
        "то есть правило оси адреса зеленело бы и на приложении, отвергающем "
        "любой идентификатор"
    )
    assert usable.text.strip() and DOCUMENT_MARK not in usable.text, (
        f"годный идентификатор строки в АДРЕСЕ ({arranged.url}) ответил не "
        f"фрагментом: тело {usable.text[:120]!r}"
    )


# =============================================================================
# ЧИСЛО ОСЕЙ ОБХОДА НЕГОДНЫХ ВЕЛИЧИН — ОСЬ НЕ ВЫПАДАЕТ ИЗ ОБХОДА МОЛЧА
# =============================================================================
#
# ⚠️ ТРЕТЬЕ ЧИСЛО МОДУЛЯ, И ОНО СЧИТАЕТ ТРЕТЬЕ МНОЖЕСТВО. Шапка модуля ведёт две
# оси и два числа — МАРШРУТЫ подтверждения и СЛУЧАИ ОБХОДА — и запрещает сличать
# их между собой. Здесь заводится ТРЕТЬЯ ось счёта: ИСТОЧНИКИ ЗНАЧЕНИЯ, которыми
# одна и та же негодная величина приезжает на маршрут. Сегодня их два — тело
# формы и адрес запроса.
#
# ⚠️ ЗАПРЕТ СВЕДЕНИЯ ЧИСЕЛ, И ОН ТАКОЙ ЖЕ НЕСУЩИЙ, КАК У ДВУХ ДЕЙСТВУЮЩИХ. Число
# ниже НЕ приводится к согласию ни с числом МАРШРУТОВ подтверждения
# (`CONFIRMED_DELETE_ROUTES_DECLARED`), ни с числом СЛУЧАЕВ обхода
# (`CONFIRMED_DELETE_OUTCOME_CASES_DECLARED`). Три числа считают ТРИ РАЗНЫХ
# МНОЖЕСТВА: сколько у фазы мест за панелью подтверждения; сколько различимых
# ответов эти места дают; сколькими ИСТОЧНИКАМИ ЗНАЧЕНИЯ до одного из этих мест
# доезжает недоверенная величина. Сведение любых двух лишило бы каждое своего
# предмета — приведи это число к числу маршрутов, и «матрица прогоняется по
# обоим источникам» перестанет быть проверяемым вовсе.
#
# ЛЕТОПИСЬ ЧИСЛА:
#   0 → 2, Фаза 10, план 10-15, задача 2. ⚠️ НОЛЬ ЗДЕСЬ ОЗНАЧАЕТ «ЧИСЛО НЕ
#   ВЕЛОСЬ ВОВСЕ», а не «осей не было». Источник расхождения назван поимённо:
#   отчёт верификации третьего круга, `gaps[0].missing`, пункт «прогнать матрицу
#   `UNUSABLE_AD_ID_VALUES` ещё и по АДРЕСУ запроса, а не только по телу».
#
#   ⚠️ ПРЕЖНЕЕ ОТСУТСТВИЕ ЧИСЛА НЕ БЫЛО ОШИБКОЙ ЗАПИСИ, И НАЗВАТЬ ЕГО ТАК ЗНАЧИЛО
#   БЫ СОЛГАТЬ О ПРИЧИНЕ. Ось была ОДНА — тело формы, — и считать было нечего:
#   число, объявленное единицей, не поймало бы ничего, чего не поймал бы сам
#   единственный обход. Ошибкой было ДРУГОЕ: единственность оси нигде НЕ
#   УТВЕРЖДАЛАСЬ. Поэтому вторая ось не «выпала» из обхода — она в него никогда
#   и не входила, и это молчание было неотличимо от полноты. Ровно эту
#   неотличимость число и снимает: теперь ось, выпавшая из обхода, краснит
#   прогон, а ось, прибавленная молча, — тоже.

# Оси обхода негодных величин: имя оси → отображение её ожидаемых исходов. У
# каждой оси СВОЁ отображение, и признак принадлежности к обходу — именно оно:
# ось, у которой отображения нет, ничего не обходит, как бы она ни называлась.
UNUSABLE_VALUE_AXES: dict[str, dict[str, object]] = {
    "тело формы (поле контекста `ad_id`)": dict(UNUSABLE_AD_ID_LANDINGS),
    "адрес запроса (идентификатор пути `schedule_id`)": dict(UNUSABLE_PATH_ID_OUTCOMES),
}


def _traversed_axes(source: dict[str, dict[str, object]]) -> list[str]:
    """Оси, которые ДЕЙСТВИТЕЛЬНО обходят матрицу негодных величин.

    ⚠️ ИСТОЧНИК ПРИНИМАЕТСЯ ПАРАМЕТРОМ, А НЕ ЧИТАЕТСЯ ИЗ МОДУЛЯ. Только так
    выразим отрицательный контроль: он подаёт сюда УКОРОЧЕННЫЙ перечень и
    показывает, что правило числа на нём краснеет. Разборщик, читающий
    глобальный перечень, зубы правила показать не мог бы — их пришлось бы
    заявить прозой.

    ⚠️ ОСЬ С НЕПОЛНЫМ ОТОБРАЖЕНИЕМ ОСЬЮ НЕ СЧИТАЕТСЯ, И ЭТО НЕ ПРИДИРКА. Предмет
    числа — «те же пять величин едут ОБОИМИ источниками»; отображение, потерявшее
    величину, обходит уже не матрицу, а её огрызок, и засчитывать его осью
    значило бы объявить обход полным там, где он неполон.
    """
    return sorted(
        name
        for name, outcomes in source.items()
        if outcomes and set(outcomes) == set(UNUSABLE_AD_ID_VALUES)
    )


# ⚠️ ЧИСЛО ПОСТАВЛЕНО ПРОГОНОМ ПОКРАСНЕВШЕГО ПРАВИЛА, А НЕ СЧЁТОМ В УМЕ,
# дословно: `AssertionError: осей обхода негодных величин 2, а объявлено 0.
# ⚠️ ЭТО НЕ ЧИСЛО МАРШРУТОВ (их 9) И НЕ ЧИСЛО СЛУЧАЕВ ОБХОДА (их 19) …`.
UNUSABLE_VALUE_AXES_DECLARED = 2


def test_the_number_of_unusable_value_axes_is_declared():
    """Число осей обхода негодных величин равно объявленному.

    ⚠️ ПРЕДМЕТ — МОЛЧАЛИВАЯ ПОТЕРЯ ИСТОЧНИКА ЗНАЧЕНИЯ. Правила самих осей ловят
    негодную величину, приехавшую ПО СВОЕЙ оси, и о существовании второй оси не
    знают ничего: снятая ось не роняет ни одного из них, потому что своего
    правила у неё больше нет. Ровно так вторая ось и не обходилась до третьего
    круга верификации — молча.

    ⚠️ СЛИЧАТЬ ЭТО ЧИСЛО С ДВУМЯ ДЕЙСТВУЮЩИМИ ЧИСЛАМИ МОДУЛЯ ЗАПРЕЩЕНО: они
    считают другие множества (разбор — у самой константы и в шапке модуля).
    """
    axes = _traversed_axes(UNUSABLE_VALUE_AXES)
    assert len(axes) == UNUSABLE_VALUE_AXES_DECLARED, (
        f"осей обхода негодных величин {len(axes)}, а объявлено "
        f"{UNUSABLE_VALUE_AXES_DECLARED}. ⚠️ ЭТО НЕ ЧИСЛО МАРШРУТОВ (их "
        f"{CONFIRMED_DELETE_ROUTES_DECLARED}) И НЕ ЧИСЛО СЛУЧАЕВ ОБХОДА (их "
        f"{CONFIRMED_DELETE_OUTCOME_CASES_DECLARED}) — три множества разные, и "
        "приводить их к согласию правкой одного нельзя. Падение означает, что "
        "ИСТОЧНИК ЗНАЧЕНИЯ выпал из обхода и недоверенная величина по нему "
        "больше не проверяется; рост — что источник появился, а решения о том, "
        "чем его исходы отличаются от исходов соседней оси, никто не "
        "принимал.\nНайденные оси:\n  " + "\n  ".join(axes or ["(ни одной)"])
    )

    incomplete = sorted(set(UNUSABLE_VALUE_AXES) - set(axes))
    assert not incomplete, (
        "ось объявлена, но матрицу негодных величин НЕ обходит — её отображение "
        "ожидаемых исходов пусто или потеряло величину:\n  "
        + "\n  ".join(incomplete)
        + f"\n\nМатрица — {sorted(UNUSABLE_AD_ID_VALUES)}. Ось с огрызком "
        "матрицы засчиталась бы полной, и половина величин по ней не "
        "проверялась бы вовсе"
    )


def test_control_a_shortened_axis_list_reddens_the_axis_count():
    """ЗУБЫ ПРАВИЛА ЧИСЛА ОСЕЙ — УКОРОЧЕННЫМ ПЕРЕЧНЕМ, А НЕ ПРОЗОЙ.

    ⚠️ БЕЗ ЭТОГО КОНТРОЛЯ ПРАВИЛО ВЫШЕ ЗЕЛЕНЕЛО БЫ И НА РАЗБОРЩИКЕ, ВОЗВРАЩАЮЩЕМ
    ЧТО УГОДНО ДЛИНОЙ ДВА. Контроль подаёт разборщику перечень БЕЗ одной оси и
    показывает, что счёт расходится с объявленным числом; и второй половиной —
    что ось с ОПУСТОШЁННЫМ отображением из счёта выпадает, а не проходит за
    полную.
    """
    names = sorted(UNUSABLE_VALUE_AXES)
    assert len(names) >= 2, (
        "контроль требует минимум двух осей: на одной укорачивать нечего"
    )

    shortened = {name: UNUSABLE_VALUE_AXES[name] for name in names[1:]}
    assert len(_traversed_axes(shortened)) == UNUSABLE_VALUE_AXES_DECLARED - 1, (
        f"перечень, укороченный на ось {names[0]!r}, дал прежний счёт — значит "
        "разборщик читает НЕ поданный источник, и правило числа осей зеленело "
        "бы на любом перечне"
    )

    emptied = {**UNUSABLE_VALUE_AXES, names[0]: {}}
    assert len(_traversed_axes(emptied)) == UNUSABLE_VALUE_AXES_DECLARED - 1, (
        f"ось {names[0]!r} с ПУСТЫМ отображением ожидаемых исходов засчиталась "
        "осью обхода. Такая ось не обходит ничего, а число сошлось бы с "
        "объявленным ровно тогда, когда обход выключили бы молча"
    )


# =============================================================================
# РАЗВИЛКА ФОРМЫ ОТВЕТА И АДРЕС ПРИЗЕМЛЕНИЯ ЧИТАЮТ ОДИН ПРИЗНАК — `WR-01`
# =============================================================================


@pytest.mark.asyncio
async def test_the_fragment_branch_needs_the_editor_flag(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Запрос БЕЗ признака возврата приземляет ОБА транспорта на один экран.

    ⚠️ ПРЕДМЕТ ПРАВИЛА — НЕ КОД 204, А СХОЖДЕНИЕ ДВУХ ТРАНСПОРТОВ НА ОДНОМ
    ЭКРАНЕ. Утверждение об одном коде зеленело бы и при двух РАЗНЫХ адресах,
    поэтому адрес заголовка перехода сличается с адресом перенаправления
    ПОСИМВОЛЬНО.

    ⚠️ ЧТО ИМЕННО БЫЛО СЛОМАНО. `_editor_url` отдаёт адрес редактора ТОЛЬКО при
    признаке возврата, иначе сводный список. Развилка формы ответа строкой ниже
    спрашивала СОВСЕМ ДРУГОЕ — остались ли у объявления строки расписания — и
    признака возврата не читала вовсе. Запрос с ЖИВЫМ идентификатором строки и
    без признака возврата получал: на пути деградации — 302 на сводный список,
    на пути htmx — 200 и фрагмент РЕДАКТОРА. Ни один из трёх внеполосных узлов
    ответа на сводном списке цели не находит (`schedules/list.html` печатает
    своё число собственной разметкой `<p class="sched-count">`), то есть путь
    htmx получал ответ, который некуда приземлить, а удалённая строка оставалась
    на экране. Это ровно тот класс молчаливого расхождения, ради невозможности
    которого `_editor_url` и был заведён: адрес собирался один раз, а ВЕТКА —
    по-прежнему дважды.

    ⚠️ АНТИВАКУУМ НЕСУЩИЙ, А НЕ ГИГИЕНИЧЕСКИЙ. Без него правило зеленело бы на
    обработчике, у которого фрагментной ветки не осталось ВОВСЕ, — то есть на
    удалении предмета вместо его починки.

    ⚠️ СОСТОЯНИЕ ГОТОВИТСЯ ЗАНОВО ДЛЯ КАЖДОЙ ПОЛОВИНЫ: подтверждённое удаление
    необратимо, и вторая половина, пришедшая на уже изменённое состояние,
    проверяла бы не тот исход, который названа проверять (форма соседнего
    обхода, перенята дословно).
    """
    route = _the_fragment_route()
    outcome = route.outcomes[0]
    await _identify(client, route.identity, test_settings)

    # ПОЛОВИНА HTMX: живая строка, ПУСТОЕ тело — признака возврата нет.
    arranged = await outcome.arrange(client, db_session, test_settings, route.identity)
    with arranged.context():
        with_layer = await client.post(
            arranged.url,
            content="",
            headers={**HTMX_HEADERS, **FORM_CONTENT_TYPE},
            follow_redirects=True,
        )

    layer_landing = with_layer.headers.get("HX-Location", "")
    layer_oob = _oob_node_ids(with_layer.text)
    assert with_layer.status_code == 204, (
        f"без признака возврата путь htmx ответил {with_layer.status_code} "
        f"вместо 204, адрес приземления {layer_landing!r}, внеполосные узлы "
        f"{sorted(layer_oob)}. Код 200 здесь означает, что развилка выдала "
        "ФРАГМЕНТ РЕДАКТОРА запросу, чей адрес приземления есть сводный список"
    )
    assert layer_landing == SUMMARY_SCREEN, (
        f"заголовок перехода {layer_landing!r} не равен {SUMMARY_SCREEN!r}"
    )
    assert with_layer.text == "", (
        "у ответа 204 появилось тело — у этого статуса тела нет по определению"
    )
    assert not layer_oob, (
        f"ответ без признака возврата принёс внеполосные узлы "
        f"{sorted(layer_oob)}, целей которых на сводном списке нет"
    )
    assert DOCUMENT_MARK not in with_layer.text

    # ПОЛОВИНА ДЕГРАДАЦИИ: то же обращение без признака слоя письма.
    await _identify(client, route.identity, test_settings)
    degraded_arranged = await outcome.arrange(
        client, db_session, test_settings, route.identity
    )
    with degraded_arranged.context():
        without = await client.post(
            degraded_arranged.url,
            content="",
            headers=FORM_CONTENT_TYPE,
            follow_redirects=False,
        )

    assert without.status_code == 302, (
        f"путь деградации ответил {without.status_code} вместо 302 — человек "
        "без JavaScript остался бы без ответа"
    )
    assert without.headers["location"] == layer_landing, (
        f"адрес деградации {without.headers['location']!r} и заголовок перехода "
        f"{layer_landing!r} НЕ СОВПАЛИ ПОСИМВОЛЬНО — два транспорта одного "
        "действия приземляют человека на РАЗНЫЕ экраны, и ни один из них не "
        "видит расхождения в одиночку"
    )

    # АНТИВАКУУМ: фрагментная ветка не удалена, а загейтирована. С признаком
    # возврата и годным полем контекста ответ прежний — 200 и ТРИ узла.
    await _identify(client, route.identity, test_settings)
    gated = await outcome.arrange(client, db_session, test_settings, route.identity)
    schedule_id = _addressed_schedule_id(gated)
    with gated.context():
        with_flag = await client.post(
            gated.url,
            data=gated.data,
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )

    assert with_flag.status_code == 200, (
        f"с признаком возврата фрагментный маршрут ответил "
        f"{with_flag.status_code} вместо 200 — фрагментной ветки не осталось "
        "вовсе, то есть предмет удалён, а не починен"
    )
    assert _oob_node_ids(with_flag.text) == _expected_oob_ids(schedule_id), (
        f"с признаком возврата внеполосные узлы стали "
        f"{sorted(_oob_node_ids(with_flag.text))} вместо "
        f"{sorted(_expected_oob_ids(schedule_id))}"
    )
    assert DOCUMENT_MARK not in with_flag.text

# =============================================================================
# ТРЕТИЙ УЗЕЛ ОТВЕТА — ЛИНЕЙКА СЧЁТЧИКА (`WR-05`)
# =============================================================================
#
# ⚠️ ЧТО ЗДЕСЬ ПРЕДМЕТ, А ЧТО НЕТ. Предмет — СООТВЕТСТВИЕ ЗАПИСИ ПОВЕДЕНИЮ.
# Перечень изъятий докстринга сборки фрагмента называл ДВА узла ответа из ТРЁХ и
# заканчивался принципом, который сам же нарушал: «дефект был бы в том, чтобы
# утверждать прозой ШИРЕ поведения». Третий узел — линейка счётчика — адресуется
# СТАТИЧЕСКИМ селектором `#sched-count`, а число считается для объявления,
# ВЛАДЕЮЩЕГО удалённой строкой. Правило ниже превращает это из прозы в
# ИЗМЕРЕННЫЙ ФАКТ и стережёт перечень от возвращения к неполноте.
#
# ⚠️ ПРАВИЛО УТВЕРЖДАЕТ ФАКТ, А НЕ ОСУЖДАЕТ ЕГО. Кросс-объявленческое удаление
# границ привилегий НЕ пересекает (оба объявления принадлежат одному владельцу),
# а после гейта развилки (`WR-01`, задача 2 этого же плана) собрать такое
# обращение из интерфейса нельзя вовсе: признак возврата и поле контекста несут
# ОБЕ формы пути удаления, и разметка не даёт послать удаление строки чужого
# объявления с экрана своего. Остаётся собранное руками тело запроса.


async def _seed_second_ad_with_schedules(
    db: AsyncSession, user_id: int, count: int
) -> tuple[Ad, int]:
    """ВТОРОЕ объявление того же владельца и `count` расписаний к нему.

    Своих моделей и своего посева не заводится: объявление сеет `_seed_ad`,
    аккаунт — `_seed_account`, расписание — ввезённый `_seed_schedule`. Вторая
    копия любого из них разошлась бы с первой молча.

    Возвращает объявление и идентификатор ОДНОЙ из его строк — правилу нужны обе
    величины: первая называет объявление, вторая адресует запрос.
    """
    ad = await _seed_ad(db, user_id)
    account = await _seed_account(db, user_id)
    first_schedule_id = None
    for _ in range(count):
        schedule = await _seed_schedule(db, ad.id, account.id)
        if first_schedule_id is None:
            first_schedule_id = schedule.id
    assert first_schedule_id is not None, (
        "второе объявление посеяно БЕЗ расписаний — адресовать запросу нечего"
    )
    return ad, first_schedule_id


async def _schedule_count_of(db: AsyncSession, ad_id: int) -> int:
    db.expire_all()
    return len(
        (
            await db.execute(select(Schedule.id).where(Schedule.ad_id == ad_id))
        ).scalars().all()
    )


COUNTER_OOB_OPEN = '<div hx-swap-oob="innerHTML:#sched-count">'


def _counter_line_of(body: str) -> str:
    """ЦЕЛЫЙ текст линейки счётчика из третьего внеполосного узла ответа.

    ⚠️ СЛИЧАЕТСЯ ЦЕЛОЕ, А НЕ ПОДСТРОКА, И ЭТО РЕШЕНИЕ. Линейка печатает число
    ЦИФРОЙ И СЛОВОМ через правило склонения
    (`ads/includes/sched_count_rule.html`), и сличение «есть ли в теле „2“»
    зеленело бы на «12», найденной внутри «12 расписаний» ЧУЖОГО объявления.
    """
    assert COUNTER_OOB_OPEN in body, (
        "в ответе нет узла линейки счётчика — сличать нечего, и правило "
        f"утверждало бы не о том предмете. Тело: {body[:200]!r}"
    )
    start = body.index(COUNTER_OOB_OPEN) + len(COUNTER_OOB_OPEN)
    end = body.index("</div>", start)
    return body[start:end].strip()


def _rendered_counter_line(count: int) -> str:
    """Линейка, отрисованная ТЕМ ЖЕ шаблоном на заданном числе.

    Ожидание собирается ШАБЛОНОМ, а не литералом: литерал разошёлся бы с
    разметкой при первой же правке формулировки, и правило краснело бы на
    редактуре текста вместо предмета.
    """
    return (
        templates.env.get_template("ads/includes/sched_count_rule.html")
        .render(schedules_count=count)
        .strip()
    )


@pytest.mark.asyncio
async def test_the_counter_node_belongs_to_the_ad_named_by_the_request(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Линейка счётчика несёт число объявления, ВЛАДЕЮЩЕГО удалённой строкой.

    ⚠️ РАССТАНОВКА ВОСПРОИЗВОДИТ ИМЕННО ТОТ СЛУЧАЙ, КОТОРЫЙ ОПИСЫВАЕТ ПЕРЕЧЕНЬ
    ИЗЪЯТИЙ. У одного владельца два объявления: A (экран, на котором человек
    стои́т — его называет ПОЛЕ КОНТЕКСТА) и B (объявление, которому принадлежит
    удаляемая строка — его называет АДРЕС ЗАПРОСА). Приоритет у найденной
    строки, поэтому счёт идёт по B; цель третьего узла — статический селектор,
    поэтому в документе, открытом на A, это число встанет в ЕГО линейку и
    переживёт запрос до перезагрузки.

    ⚠️ АНТИВАКУУМ ЧИСЛОМ, И ЕГО ДВЕ ПОЛОВИНЫ. Числа расписаний у A и B обязаны
    быть РАЗНЫМИ и ДО запроса, и ПОСЛЕ него. Равные числа ПОСЛЕ удаления сделали
    бы вердикт неотличимым от вердикта на правильном объявлении, и правило
    зеленело бы независимо от предмета — поэтому у B посеяно ЧЕТЫРЕ строки, а не
    три: после удаления у него остаётся три против двух у A.

    ⚠️ ПРАВИЛО ЗЕЛЕНО ПЕРВЫМ ЖЕ ПРОГОНОМ, И ЭТО ОЖИДАЕМО: оно утверждает
    СЕГОДНЯШНЕЕ поведение, а предмет задачи — ЗАПИСЬ. Зубы ему даёт не переход
    цвета, а мутация обработчика (счёт по объявлению из найденной строки заменён
    на счёт по полю формы) — на ней правило обязано покраснеть, и её вывод
    приведён в сводке плана.
    """
    route = _the_fragment_route()
    outcome = route.outcomes[0]
    await _identify(client, route.identity, test_settings)

    arranged = await outcome.arrange(client, db_session, test_settings, route.identity)
    ad_a_id = arranged.landing_args["ad_id"]
    user = await _current_user(db_session, route.identity, test_settings)
    ad_b, ad_b_schedule_id = await _seed_second_ad_with_schedules(
        db_session, user.id, 4
    )
    # ⚠️ ИДЕНТИФИКАТОР СНИМАЕТСЯ СРАЗУ, ДО ПЕРВОГО СЧЁТА. Счёт сбрасывает
    # состояние сессии (`expire_all`), и обращение к атрибуту объекта ПОСЛЕ
    # него потребовало бы синхронной подгрузки вне гринлета — отказ, не имеющий
    # отношения к предмету правила.
    ad_b_id = ad_b.id

    a_before = await _schedule_count_of(db_session, ad_a_id)
    b_before = await _schedule_count_of(db_session, ad_b_id)
    assert a_before != b_before, (
        f"у объявления A {a_before} расписаний и у B {b_before} — числа СОВПАЛИ "
        "ещё до запроса, и вердикт правила был бы неотличим от вердикта на "
        "правильном объявлении"
    )

    with arranged.context():
        response = await client.post(
            f"/schedules/{ad_b_schedule_id}/delete",
            content=f"return_to={RETURN_TO_EDITOR_VALUE}&ad_id={ad_a_id}",
            headers={**HTMX_HEADERS, **FORM_CONTENT_TYPE},
            follow_redirects=True,
        )

    assert response.status_code == 200, (
        f"кросс-объявленческое удаление ответило {response.status_code} вместо "
        "200 — предметом сличения перестал быть фрагментный ответ"
    )

    a_after = await _schedule_count_of(db_session, ad_a_id)
    b_after = await _schedule_count_of(db_session, ad_b_id)
    assert (a_after, b_after) == (a_before, b_before - 1), (
        f"после запроса у A стало {a_after} расписаний (было {a_before}), у B "
        f"{b_after} (было {b_before}) — удалена не та строка, о которой "
        "говорит правило"
    )
    assert a_after != b_after, (
        f"после удаления числа сравнялись ({a_after}) — вердикт «линейка несёт "
        "число B» стал неотличим от «линейка несёт число A», и правило зелено "
        "независимо от предмета"
    )

    observed = _counter_line_of(response.text)
    expected_b = _rendered_counter_line(b_after)
    expected_a = _rendered_counter_line(a_after)
    assert expected_a != expected_b, (
        f"шаблон линейки отрисовал ОДИНАКОВЫЙ текст на {a_after} и {b_after} "
        f"({expected_b!r}) — сличение текста перестало различать объявления"
    )
    assert observed == expected_b, (
        f"линейка ответа {observed!r} не совпала с линейкой объявления B "
        f"({b_after} расписаний, {expected_b!r}). Линейка объявления A — "
        f"{expected_a!r}. ⚠️ Число считается для объявления, ВЛАДЕЮЩЕГО "
        "удалённой строкой, а цель узла — статический селектор `#sched-count`: "
        "именно это и перечисляет расширенный перечень изъятий докстринга "
        "сборки фрагмента"
    )

# =============================================================================
# ТРЕТЬЕ МНОЖЕСТВО МОДУЛЯ: МАРШРУТЫ, ИЗЪЯТЫЕ ИЗ ПРАВИЛА НЕОТЛИЧИМОСТИ ПОВТОРА
# =============================================================================
#
# ⚠️ ЭТО ТРЕТЬЕ МНОЖЕСТВО, А НЕ ТРЕТИЙ СЧЁТ ТОГО ЖЕ. Число МАРШРУТОВ отвечает на
# вопрос «сколько у фазы маршрутов подтверждения» (8). Число СЛУЧАЕВ ОБХОДА —
# «сколько различимых ответов эти маршруты дают» (18). Число ИЗЪЯТИЙ — «для
# скольких из них повтор НЕ ЯВЛЯЕТСЯ повтором удаления». Три числа считают три
# РАЗНЫХ множества, и приводить их к согласию правкой одного НЕЛЬЗЯ — записанная
# идиома проекта (см. шапку модуля и `MODAL_CONSUMERS` против `MODAL_IMPORTERS`
# в `tests/test_templates/test_components.py`).
#
# КАКОЕ РЕБРО ОБСЛУЖИВАЕТ ПЕРЕЧЕНЬ. Идемпотентность отката-фолбэка FORM-06 —
# проба «что происходит, если это выполнится дважды на том же входе».
#
# ПРЕДИКАТ ВКЛЮЧЕНИЯ, ДОСЛОВНО И ОДИН: маршрут ОСТАЁТСЯ под правилом, если его
# действие УНИЧТОЖАЕТ АДРЕСУЕМУЮ СТРОКУ, то есть второй запрос с тем же телом
# уже не имеет предмета. Маршрут ИЗЫМАЕТСЯ, если повтор ЗАПУСКАЕТ ДЕЙСТВИЕ
# ЗАНОВО (постановка работы в очередь, перезапуск процесса, смена личности) либо
# если адресуемая строка не уничтожается вовсе: там «дважды на том же входе»
# означает ДВА ВЫПОЛНЕННЫХ ДЕЙСТВИЯ, а не одно и один безвредный холостой путь,
# и утверждать равенство ответов было бы неверно ПО СУЩЕСТВУ, а не неудобно.
#
# ⚠️ СОСТАВ ВЫВЕДЕН ЧТЕНИЕМ ОБРАБОТЧИКОВ, А НЕ УГАДЫВАНИЕМ ПО ИМЕНАМ: по одному
# чтению на каждый из восьми ключей перечня маршрутов (план 10-06, задача 2).
# Ключ, по которому обработчик прочитан не был, в перечень не попадает ни в одну
# сторону.
#
# ⚠️ ФРАГМЕНТНЫЙ МАРШРУТ В ЭТОТ ПЕРЕЧЕНЬ НЕ ВХОДИТ И ИЗЪЯТЫМ НЕ ЯВЛЯЕТСЯ. Его
# повтор накрыт СВОИМ правилом выше
# (`test_a_repeated_confirmed_delete_on_the_fragment_route_answers_the_same_shape`),
# потому что сличать там надо ДРУГОЕ — множество идентификаторов внеполосных
# узлов, а не заголовок перехода. Из параметризации он выбывает по ПОЛЮ ЗАПИСИ
# `htmx_form`, а не по изъятию: изъятие означало бы «повтор здесь не проверяется».
REPEAT_EXEMPT_ROUTES: dict[str, str] = {
    "app/pages/history.py::history_retry": (
        "повтор СТАВИТ ОТПРАВКУ В ОЧЕРЕДЬ ЗАНОВО, а не удаляет строку: запись "
        "журнала переживает запрос целиком. Второе нажатие в пределах окна "
        "удержания отвечает СВОИМ кодом исхода (`retry_busy`), и это записанный "
        "контракт защиты от второй необратимой отправки, а не расхождение"
    ),
    "app/pages/admin.py::admin_restart_worker": (
        "повтор ПЕРЕЗАПУСКАЕТ КОНТЕЙНЕР ЗАНОВО: аккаунт, адресуемый путём, не "
        "уничтожается ничем, и два подтверждения означают два выполненных "
        "перезапуска, а не один и холостой путь"
    ),
    "app/pages/admin.py::admin_drop_task": (
        "адресуемая ПУТЁМ строка — аккаунт — не уничтожается вовсе; снимается "
        "задача, названная ТЕЛОМ формы. Закрытый словарь исходов подраздела "
        "ОБЯЗАН различать «снял» (`drop_removed`) и «её уже не было» "
        "(`drop_missing`): обработчик записывает дословно, что молчаливый успех "
        "был бы ХУЖЕ отказа — администратор решил бы, что снял отправку, "
        "которой не касался"
    ),
    "app/pages/admin.py::admin_impersonate": (
        "повтор МЕНЯЕТ ЛИЧНОСТЬ ЗАНОВО, ничего не уничтожая: после первого "
        "запроса клиент уже несёт cookie цели, и второй отвергается "
        "зависимостью запрета вложенного входа — другая ветка, а не тот же "
        "ответ"
    ),
}

# ⚠️ ЧИСЛО ИЗЪЯТИЙ. Считает ЗАПИСИ перечня выше — НЕ маршруты и НЕ случаи обхода.
#
# ЛЕТОПИСЬ ЧИСЛА:
#   0 → 4, Фаза 10, план 10-06, задача 2: перечень заведён вместе с правилом
#   неотличимости повтора. Источник движения СЛОВАМИ: из восьми маршрутов
#   подтверждения по предикату включения изъяты те, где повтор запускает
#   действие заново либо не уничтожает адресуемой строки, — повтор отправки из
#   журнала, перезапуск контейнера воркера, снятие задачи из очереди и вход под
#   пользователем. Число ПОСТАВЛЕНО ПРОГОНОМ покрасневшего правила, дословно:
#   `AssertionError: изъятий из правила неотличимости повтора найдено 4, а
#   объявлено 0. ⚠️ ЭТО НЕ ЧИСЛО МАРШРУТОВ (их 8) И НЕ ЧИСЛО СЛУЧАЕВ ОБХОДА (их
#   18) …` — то есть сумма НЕ складывалась в уме, её назвал сам отказ.
REPEAT_EXEMPT_ROUTES_DECLARED = 4


def test_the_number_of_repeat_exempt_routes_is_the_declared_one():
    """Длина перечня изъятий равна объявленному числу, ключи живы, основания есть.

    ⚠️ ЧТО ЭТО ПРАВИЛО ЛОВИТ И ЧЕГО НЕ ЛОВИТ — ЧИТАТЬ ДО ТОГО, КАК СЧЕСТЬ ЕГО
    ЗУБАМИ СОСЕДНЕГО. Оно стережёт ДЕВЯТЫЙ МАРШРУТ, заведённый без решения
    «повтор здесь обязателен или изъят», и ИЗЪЯТИЕ, ПЕРЕЖИВШЕЕ УДАЛЁННЫЙ
    МАРШРУТ (такое изъятие молча выключило бы проверку у другого). Регресс
    САМОГО свойства неотличимости на УЖЕ ПЕРЕЧИСЛЕННОМ маршруте оно не ловит и
    поймать не может: при таком регрессе число изъятий не двигается. Зубы
    параметризованному правилу даёт его СОБСТВЕННЫЙ отрицательный контроль.
    """
    assert len(REPEAT_EXEMPT_ROUTES) == REPEAT_EXEMPT_ROUTES_DECLARED, (
        f"изъятий из правила неотличимости повтора найдено "
        f"{len(REPEAT_EXEMPT_ROUTES)}, а объявлено "
        f"{REPEAT_EXEMPT_ROUTES_DECLARED}. ⚠️ ЭТО НЕ ЧИСЛО МАРШРУТОВ (их "
        f"{len(CONFIRMED_DELETE_ROUTES)}) И НЕ ЧИСЛО СЛУЧАЕВ ОБХОДА (их "
        f"{CONFIRMED_DELETE_OUTCOME_CASES_DECLARED}) — три множества разные, и "
        "приводить их к согласию правкой одного нельзя. Найденные ключи:\n  "
        + "\n  ".join(sorted(REPEAT_EXEMPT_ROUTES))
    )

    known = {route.key for route in CONFIRMED_DELETE_ROUTES}
    stray = sorted(set(REPEAT_EXEMPT_ROUTES) - known)
    assert not stray, (
        "изъятие пережило свой маршрут — ключа нет в перечне маршрутов "
        "подтверждения:\n  " + "\n  ".join(stray) + "\n\nТакое изъятие молча "
        "выключает проверку у ДРУГОГО маршрута, если ключ когда-нибудь "
        "совпадёт, и до тех пор просто лжёт о составе множества"
    )

    blank = sorted(
        key for key, reason in REPEAT_EXEMPT_ROUTES.items() if not reason.strip()
    )
    assert not blank, (
        "изъятие без основания:\n  " + "\n  ".join(blank) + "\n\nОснование "
        "обязано называть, ПОЧЕМУ повтор на этом маршруте не является повтором "
        "удаления, — иначе перечень становится местом, где проверка выключается "
        "молча"
    )


# =============================================================================
# НЕОТЛИЧИМОСТЬ ПОВТОРА НА МАРШРУТАХ ПЕРЕХОДА — И ЕЁ СОБСТВЕННЫЙ КОНТРОЛЬ
# =============================================================================
#
# ⚠️ ЭТО ОТДЕЛЬНОЕ УТВЕРЖДЕНИЕ ОБХОДА, В СЧЁТ ИСХОДОВ НЕ ВХОДЯЩЕЕ, по тому же
# основанию, что и правило фрагментного повтора выше: повтор не является ИСХОДОМ
# маршрута, и подмешивание его в счёт случаев сделало бы сличение числа случаев
# неисполнимым.


@dataclass(frozen=True)
class _LandingAnswer:
    """СНЯТЫЙ ответ маршрута перехода — три величины, которые сличает предикат.

    Снимок заведён затем, чтобы контроль мог ИСПОРТИТЬ ЗНАЧЕНИЕ, а не слать
    второй запрос по другому адресу: второй запрос менял бы и статус, и адрес
    разом, и было бы неизвестно, на что предикат отреагировал.
    """

    status: int
    landing: str | None
    body: str


def _landing_answer(response) -> _LandingAnswer:
    return _LandingAnswer(
        status=response.status_code,
        landing=response.headers.get("HX-Location"),
        body=response.text,
    )


@dataclass(frozen=True)
class _Sameness:
    """Вердикт сличения. При отказе НАЗЫВАЕТ, что именно не сошлось."""

    matched: bool
    reason: str = ""


def _repeat_matches_the_first(
    first: _LandingAnswer, repeat: _LandingAnswer
) -> _Sameness:
    """ЕДИНСТВЕННОЕ место сличения ответа повтора с ответом первого запроса.

    ⚠️ ОДНО МЕСТО, А НЕ ДВА, И ЭТО НЕСУЩЕЕ. Предикат зовёт и несущее правило, и
    его отрицательный контроль. Второе, отдельно написанное сличение внутри
    контроля стерегло бы НЕ ТО, что исполняет правило, — и разошлось бы с ним
    молча при первой же правке одного из двух.

    Сличаются три величины: статус, заголовок перехода ПОСИМВОЛЬНО и пустота
    тела. Непустота заголовка проверяется ЗДЕСЬ ЖЕ: предикат, сличающий два
    отсутствия, зелен независимо от предмета — ровно тот класс зелени, ради
    которого заведена вся партия.
    """
    if first.status != repeat.status:
        return _Sameness(
            False,
            f"статус: первое удаление {first.status}, повтор {repeat.status}",
        )
    if not first.landing:
        return _Sameness(
            False,
            "заголовок перехода ПЕРВОГО удаления пуст или отсутствует — "
            f"{first.landing!r}; сличать нечего",
        )
    if not repeat.landing:
        return _Sameness(
            False,
            f"заголовок перехода ПОВТОРА пуст или отсутствует — {repeat.landing!r}",
        )
    if first.landing != repeat.landing:
        return _Sameness(
            False,
            f"заголовок перехода: первое удаление {first.landing!r}, повтор "
            f"{repeat.landing!r} — адреса разошлись ПОСИМВОЛЬНО",
        )
    if first.body != "" or repeat.body != "":
        return _Sameness(
            False,
            f"тело: первое удаление {first.body!r}, повтор {repeat.body!r} — у "
            "статуса 204 тела нет по определению",
        )
    return _Sameness(True)


def _repeat_asserted_routes() -> list[_Route]:
    """Маршруты перечня МИНУС изъятия МИНУС фрагментный.

    Вычитание объявлено ДВУМЯ РАЗНЫМИ основаниями, и путать их нельзя: изъятие
    означает «повтор здесь не является повтором удаления», а фрагментный маршрут
    выбывает потому, что накрыт СВОИМ правилом, сличающим ДРУГИЕ величины.
    """
    return [
        route
        for route in CONFIRMED_DELETE_ROUTES
        if route.key not in REPEAT_EXEMPT_ROUTES and route.htmx_form is not FRAGMENT
    ]


@pytest.mark.parametrize(
    "route", _repeat_asserted_routes(), ids=lambda route: route.handler
)
@pytest.mark.asyncio
async def test_a_repeated_confirmed_delete_is_indistinguishable_from_the_first(
    route, client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Повтор на маршруте перехода отвечает ТЕМ ЖЕ, чем первое удаление.

    ⚠️ РЕБРО ИДЕМПОТЕНТНОСТИ FORM-06 на второй половине множества маршрутов:
    первая (единственный фрагментный) накрыта правилом выше, где сличаются
    идентификаторы внеполосных узлов; здесь тела нет вовсе, и сличать надо
    статус, заголовок перехода и пустоту тела.

    ⚠️ ЧЕМ ЭТО ОТЛИЧАЕТСЯ ОТ ПРАВИЛА НЕСУЩЕСТВУЮЩЕГО ИДЕНТИФИКАТОРА. Там
    идентификатор не существовал НИКОГДА, и утверждается совпадение с ОЖИДАЕМОЙ
    формой успеха. Здесь строка СУЩЕСТВОВАЛА И БЫЛА УДАЛЕНА ПРЕДЫДУЩИМ ЗАПРОСОМ
    ЭТОГО ЖЕ ЧЕЛОВЕКА, и утверждается совпадение ДВУХ НАБЛЮДЁННЫХ ответов между
    собой. Совпадение с ожидаемой формой не влечёт совпадения двух наблюдений, и
    наоборот: снимать одно из двух как дубликат нельзя.

    ⚠️ ЗУБЫ ЭТОМУ ПРАВИЛУ ДАЁТ ЕГО СОБСТВЕННЫЙ КОНТРОЛЬ НИЖЕ, а не правило числа
    изъятий: то стережёт появление НОВОГО маршрута без решения и регресса
    сличения на уже перечисленном не ловит — при таком регрессе число изъятий не
    двигается.
    """
    outcome = route.outcomes[0]
    await _identify(client, route.identity, test_settings)

    arranged = await outcome.arrange(client, db_session, test_settings, route.identity)
    # Адрес приземления берётся МЕТОДОМ ЗАПИСИ ИСХОДА, а не собирается заново:
    # второй сборщик адреса разошёлся бы с первым молча.
    expected = outcome.expected_landing(arranged)

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

    assert first.status_code == 204, (
        f"{route.name}: первое удаление ответило {first.status_code} вместо 204 "
        "— предметом сличения перестал быть ответ маршрута перехода"
    )
    assert first.headers.get("HX-Location") == expected, (
        f"{route.name}: адрес первого удаления "
        f"{first.headers.get('HX-Location')!r} не совпал с ожидаемым "
        f"{expected!r} ПОСИМВОЛЬНО"
    )

    verdict = _repeat_matches_the_first(
        _landing_answer(first), _landing_answer(repeat)
    )
    assert verdict.matched, (
        f"{route.name}: повтор ОТЛИЧИМ от первого удаления — {verdict.reason}. "
        "Различимость ответов позволяет ПЕРЕЧИСЛЯТЬ занятые идентификаторы, "
        "ничего не удаляя (T-10-34)"
    )


def test_the_set_of_repeat_asserted_routes_is_not_empty():
    """АНТИВАКУУМ параметризации: под правилом выше есть КОГО обходить.

    Параметризация по пустому множеству не исполняет ни одного случая и зеленеет
    молча — правило есть, предмета нет. Число называется в отказе ЯВНО, вместе с
    обоими вычитаемыми множествами.
    """
    asserted = _repeat_asserted_routes()
    fragment_routes = [
        route for route in CONFIRMED_DELETE_ROUTES if route.htmx_form is FRAGMENT
    ]
    assert asserted, (
        f"под правилом неотличимости повтора не осталось НИ ОДНОГО маршрута: "
        f"маршрутов {len(CONFIRMED_DELETE_ROUTES)}, изъятий "
        f"{len(REPEAT_EXEMPT_ROUTES)}, фрагментных "
        f"{len(fragment_routes)}. Параметризация по пустому множеству зеленеет "
        "молча"
    )
    assert len(asserted) == (
        len(CONFIRMED_DELETE_ROUTES)
        - len(REPEAT_EXEMPT_ROUTES)
        - len(fragment_routes)
    ), (
        f"вычитание не сошлось: под правилом {len(asserted)}, а "
        f"{len(CONFIRMED_DELETE_ROUTES)} − {len(REPEAT_EXEMPT_ROUTES)} − "
        f"{len(fragment_routes)} даёт другое число. Значит какой-то ключ изъятия "
        "указывает на фрагментный маршрут, и одно вычитание съело другое"
    )


@pytest.mark.asyncio
async def test_control_negative_a_perturbed_landing_header_reddens_the_repeat_sameness_check(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ ПАРАМЕТРИЗОВАННОГО ПРАВИЛА ВЫШЕ.

    ⚠️ ЧТО ОН ДОКАЗЫВАЕТ И ЧЕГО НЕ ДОКАЗЫВАЕТ ПРАВИЛО ЧИСЛА ИЗЪЯТИЙ. Число
    изъятий ловит ДЕВЯТЫЙ МАРШРУТ, заведённый без решения «повтор здесь
    обязателен или изъят», и НЕ ЛОВИТ регресс сличения на УЖЕ ПЕРЕЧИСЛЕННОМ
    маршруте: при таком регрессе число изъятий не двигается вовсе. Поэтому зубы
    параметризованному правилу даёт этот контроль, и только он.

    ⚠️ ЭТО НЕ ДУБЛИКАТ `shifted_identifier`. Тот стережёт ФРАГМЕНТНЫЙ маршрут и
    сличает МНОЖЕСТВА ИДЕНТИФИКАТОРОВ внеполосных узлов; этот стережёт МАРШРУТЫ
    ПЕРЕХОДА и сличает статус, заголовок перехода и пустоту тела. Предметы
    разные, снимать одно из двух нельзя.

    ⚠️ ПОРЧА ВНОСИТСЯ В СНЯТОЕ ЗНАЧЕНИЕ, А НЕ ВТОРЫМ ЗАПРОСОМ ПО ДРУГОМУ АДРЕСУ:
    второй запрос менял бы и статус, и адрес разом, и было бы неизвестно, на что
    предикат отреагировал.
    """
    routes = _repeat_asserted_routes()
    assert routes, (
        "под параметризованным правилом нет маршрутов — контролю нечего "
        "стеречь, и он выродился бы в утверждение о пустоте"
    )
    # ПЕРВЫЙ ПО ПОРЯДКУ ПЕРЕЧНЯ и НАЗВАННЫЙ ПОИМЁННО в каждом отказе ниже:
    # контроль, молчащий о том, на чём он снят, невоспроизводим.
    route = routes[0]
    outcome = route.outcomes[0]
    await _identify(client, route.identity, test_settings)

    arranged = await outcome.arrange(client, db_session, test_settings, route.identity)
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

    first_answer = _landing_answer(first)
    repeat_answer = _landing_answer(repeat)

    # АНТИВАКУУМ ДО ПОДСТАНОВКИ: сличать два отсутствия зелено независимо от
    # предмета, и контроль на такой паре доказывал бы ноль.
    assert first_answer.landing, (
        f"{route.name}: заголовок перехода ПЕРВОГО удаления пуст "
        f"({first_answer.landing!r}) — портить нечего"
    )
    assert repeat_answer.landing, (
        f"{route.name}: заголовок перехода ПОВТОРА пуст "
        f"({repeat_answer.landing!r}) — портить нечего"
    )

    # ⚠️ КОНТРОЛЬ ОБЯЗАН ДОКАЗАТЬ, ЧТО ПРАВИЛО ЗЕЛЕНО НА НЕИСПОРЧЕННОЙ ПАРЕ:
    # предикат, отказывающий ВСЕГДА, «краснеет» на подстановке ровно так же, как
    # чувствительный, и контроль на нём ничего не значил бы.
    clean = _repeat_matches_the_first(first_answer, repeat_answer)
    assert clean.matched, (
        f"{route.name}: предикат отказал на НЕИСПОРЧЕННОЙ паре — {clean.reason}. "
        "Тогда его отказ на испорченной ничего не доказывает"
    )

    perturbed_landing = f"{repeat_answer.landing}#перевёрнуто-контролем"
    assert perturbed_landing != repeat_answer.landing, (
        f"{route.name}: испорченное значение {perturbed_landing!r} совпало с "
        f"исходным {repeat_answer.landing!r} — контроль не изменил НИЧЕГО"
    )
    perturbed = _LandingAnswer(
        status=repeat_answer.status,
        landing=perturbed_landing,
        body=repeat_answer.body,
    )

    verdict = _repeat_matches_the_first(first_answer, perturbed)
    assert not verdict.matched, (
        f"{route.name}: предикат `_repeat_matches_the_first` ПРИЗНАЛ ответы "
        f"одинаковыми при заголовке перехода {perturbed_landing!r} против "
        f"{first_answer.landing!r}. Значит он сличает НЕ ТО, чем правило "
        "неотличимости объявляет себя, и правило зелено независимо от предмета"
    )
    assert "заголовок перехода" in verdict.reason, (
        f"{route.name}: предикат отказал, но назвал причиной {verdict.reason!r} "
        "— отказ не по той величине, которую испортил контроль"
    )

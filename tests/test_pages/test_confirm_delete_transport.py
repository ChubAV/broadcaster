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
from dataclasses import dataclass, field
from typing import Awaitable, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.user import User

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

    `context` — менеджер подмен, нужных ровно этому случаю (очередь, менеджер
    контейнеров, гейт доступа). У случая без подмен он пустой: ветка «если
    подмены есть» в обходе означала бы, что половина случаев идёт другим путём.
    """

    url: str
    data: dict[str, str] = field(default_factory=dict)
    context: object = field(default_factory=contextlib.nullcontext)
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
)

# ⚠️ ЧИСЛО МАРШРУТОВ. Считает ЗАПИСИ перечня: одна запись = один маршрут.
#
# ЛЕТОПИСЬ ЧИСЛА:
#   0 → 2, Фаза 10, план 10-03, задача 1: заведены удаление аккаунта мессенджера
#   и удаление объявления — оба уходят в ветку перехода по объявленному изъятию
#   (`OFFSET_CURSOR_EXCEPTIONS`). Число доводят до восьми задачи 2 и 3, каждая
#   своим движением с летописью.
CONFIRMED_DELETE_ROUTES_DECLARED = 2

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
CONFIRMED_DELETE_OUTCOME_CASES_DECLARED = 2


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
    with degraded.context:
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

    arranged = await outcome.arrange(client, db_session, test_settings, route.identity)
    expected = outcome.expected_landing(arranged)
    with arranged.context:
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

    with arranged.context:
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

    with arranged.context:
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

    with arranged.context:
        without = await client.post(
            arranged.url, data=arranged.data, follow_redirects=False
        )
    assert without.status_code == 302
    assert without.headers["location"] == route.session_landing

    with arranged.context:
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

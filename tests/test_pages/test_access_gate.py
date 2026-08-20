"""Гейт доступа: кого закрывает истёкший срок и кого не закрывает НИКОГДА.

ФАЙЛ ДЕРЖИТ ДВЕ ГРУППЫ, РАЗЛИЧИМЫЕ ПО `-k pages` И `-k api`, И ЭТО НЕ
ОФОРМЛЕНИЕ. Поверхностей отказа в продукте две, и устроены они по-разному:
страничная отвечает редиректом на место, где чинят (человеку нужен экран), а
JSON-API обязан отвечать кодом и телом (клиенту редирект бессмыслен). Общий
файл заводится затем, чтобы ПЕРЕЧЕНЬ закрытого нельзя было расширить на одной
поверхности, забыв про другую.

ГРУППА `api` ЗАПОЛНЕНА ПЛАНОМ `05.1-03`. Запись долга
(`test_api_surface_of_the_gate_is_not_built_yet`), стоявшая здесь до него,
ЗАМЕНЕНА настоящими утверждениями отказа, а не дополнена ими: утверждение «этого
ещё нет» и утверждение «это работает так» не могут быть верны одновременно, и
оставить оба значило бы держать в суите заведомо красный тест как декорацию.

ДВА ГЕЙТА ПЕРЕЧНЯ ЧИТАЮТ ДВА РАЗНЫХ ИСХОДНИКА ОДНИМ ПОМОЩНИКОМ. Страничная
сборка живёт в `app/pages/__init__.py`, JSON-сборка — в `app/main.py`; вторая
копия разбора разошлась бы с первой, и расхождение проявилось бы ровно на той
поверхности, про которую забыли.

ПОЧЕМУ ГЕЙТ ПЕРЕЧНЯ ЧИТАЕТ ИСХОДНИК, А НЕ СОБРАННОЕ ПРИЛОЖЕНИЕ. Цель —
поймать роутер, добавленный БУДУЩИМ планом БЕЗ зависимости. В объекте
приложения такой роутер выглядит совершенно обычно: у его маршрутов просто нет
одной зависимости, и отличить «забыли» от «не должно быть» там нечем. В
исходнике же решение записано явным вызовом, и множество вызовов замкнуто.
Форма взята у отрицательных утверждений `tests/test_pages/test_history_retry.py`.
"""
import ast
from pathlib import Path

import pytest
from httpx import AsyncClient

PAGES_INIT = Path(__file__).resolve().parents[2] / "app" / "pages" / "__init__.py"
MAIN_PY = Path(__file__).resolve().parents[2] / "app" / "main.py"
DEPENDENCIES_PY = Path(__file__).resolve().parents[2] / "app" / "dependencies.py"

EXPIRED_LOCATION = "/billing?expired=1"

# РОУТЕРЫ, КОТОРЫЕ ЗАКРЫВАЕТ ИСТЁКШИЙ ДОСТУП. Перечень выписан ЗДЕСЬ, а не
# выведен из исходника: тест, выводящий ожидание из проверяемого, согласился бы
# с любой правкой. Изменение этого множества обязано быть решением, записанным
# в двух местах сразу.
GATED_ROUTERS = {
    "ads_router",
    "accounts_router",
    "account_groups_router",
    "groups_router",
    "schedules_router",
    "history_router",
}

# РОУТЕРЫ, КОТОРЫЕ НЕ ЗАКРЫВАЮТСЯ НИКОГДА (T-05.1-03). Вход, регистрация и
# выход — иначе человек не может даже войти, чтобы заплатить; подписка и оплата —
# иначе гейт запирает продукт от единственного действия, которое его открывает;
# профиль и админка — администратор без оплаченного доступа обязан входить в
# админку; дашборд — он только читает и служит местом, куда человека приводят
# после входа со словами о том, что произошло.
OPEN_ROUTERS = {
    "auth_router",
    "dashboard_router",
    "billing_router",
    "admin_router",
    "profile_router",
}


# РОУТЕРЫ JSON-API, КОТОРЫЕ ЗАКРЫВАЕТ ИСТЁКШИЙ ДОСТУП. Перечень выписан ЗДЕСЬ по
# той же причине, что и страничный: тест, выводящий ожидание из проверяемого,
# согласился бы с любой правкой.
GATED_API_ROUTERS = {
    "ads_router",
    "accounts_router",
    "schedules_router",
    "history_router",
    "uploads_router",
}

# РОУТЕРЫ JSON-API, КОТОРЫЕ НЕ ЗАКРЫВАЮТСЯ НИКОГДА. Вход — иначе человек не
# может даже войти, чтобы заплатить (T-05.1-16); денежный роутер — там живут и
# чтения раздела, и вебхук ЮKassa, отказ на котором остановил бы приём денег;
# страничный роутер держит СВОЙ пер-роутерный гейт внутри
# (`app/pages/__init__.py`), и второй поверх него закрыл бы вход и оплату.
#
# ⚠️ `dashboard_feed_router` СТОИТ ЗДЕСЬ ПО ОТДЕЛЬНОМУ РЕШЕНИЮ (T-05.1-15), а не
# заодно с соседями, и обоснование записано абзацем в `app/main.py` рядом с его
# включением. Молчание здесь было бы ровно той формой обхода, которую этот файл
# закрывает.
OPEN_API_ROUTERS = {
    "auth_router",
    "billing_router",
    "dashboard_feed_router",
    "pages_router",
}


def _routers_with_dependency(source: Path, dependency: str) -> dict[str, bool]:
    """Каждый вызов `.include_router(...)` → «висит ли на нём названная зависимость».

    Разбор по синтаксическому дереву, а не грепом: греп по строке
    `Depends(require_access)` посчитал бы её и в комментарии, и в докстринге, и
    в объявлении самой зависимости, а вопрос здесь ровно один — с какими
    аргументами позван `include_router`.
    """
    tree = ast.parse(source.read_text(encoding="utf-8"))
    found: dict[str, bool] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "include_router":
            continue
        if not node.args or not isinstance(node.args[0], ast.Name):
            continue

        router_name = node.args[0].id
        gated = False
        for keyword in node.keywords:
            if keyword.arg != "dependencies":
                continue
            for element in ast.walk(keyword.value):
                if isinstance(element, ast.Name) and element.id == dependency:
                    gated = True
        found[router_name] = gated

    return found


def _included_routers() -> dict[str, bool]:
    """Страничная сборка: кто включён и на ком висит `require_access`."""
    return _routers_with_dependency(PAGES_INIT, "require_access")


def _api_included_routers() -> dict[str, bool]:
    """Сборка приложения: кто включён и на ком висит гейт доступа JSON-входа."""
    return _routers_with_dependency(MAIN_PY, "get_current_user_id_with_access")


# =============================================================================
# Группа `pages` — страничная поверхность отказа
# =============================================================================


def test_pages_gate_covers_exactly_the_declared_routers():
    """Множество закрытых роутеров равно объявленному — ни шире, ни уже.

    ⚠️ РОУТЕР, ДОБАВЛЕННЫЙ БУДУЩИМ ПЛАНОМ, РОНЯЕТ ЭТОТ ТЕСТ В ЛЮБОМ СЛУЧАЕ, И В
    ЭТОМ ВЕСЬ СМЫСЛ. Он не назван ни в `GATED_ROUTERS`, ни в `OPEN_ROUTERS`,
    поэтому последнее утверждение красит его независимо от того, поставили на
    него зависимость или забыли. Автор нового роутера обязан ОТВЕТИТЬ на вопрос
    «закрывает ли его истёкший доступ» здесь, а не оставить ответ умолчанием
    сборки.
    """
    included = _included_routers()

    gated = {name for name, is_gated in included.items() if is_gated}
    open_ = {name for name, is_gated in included.items() if not is_gated}

    assert gated == GATED_ROUTERS, (
        f"перечень закрытых роутеров разошёлся с объявленным: "
        f"лишние {gated - GATED_ROUTERS}, недостающие {GATED_ROUTERS - gated}"
    )
    assert open_ == OPEN_ROUTERS, (
        f"перечень ВСЕГДА открытых роутеров разошёлся с объявленным: "
        f"лишние {open_ - OPEN_ROUTERS}, недостающие {OPEN_ROUTERS - open_}"
    )
    assert set(included) == GATED_ROUTERS | OPEN_ROUTERS, (
        "в сборку страниц включён роутер, о котором этот тест не знает — "
        "решение «закрывает ли его истёкший доступ» не принято"
    )


@pytest.mark.parametrize(
    "path",
    ["/ads", "/accounts", "/schedules", "/groups", "/history"],
)
@pytest.mark.asyncio
async def test_pages_of_value_are_closed_when_access_expired(
    expired_client: AsyncClient, path: str
):
    """Страница создания ценности отвечает 302 на место, где чинят."""
    response = await expired_client.get(path, follow_redirects=False)

    assert response.status_code == 302, (
        f"{path} ответил {response.status_code} при истёкшем доступе"
    )
    assert response.headers["location"] == EXPIRED_LOCATION, (
        f"{path} увёл на {response.headers.get('location')!r} вместо "
        f"{EXPIRED_LOCATION!r} — человек не узнал, что произошло и что делать"
    )


@pytest.mark.parametrize(
    "path",
    ["/login", "/billing", "/profile", "/dashboard"],
)
@pytest.mark.asyncio
async def test_pages_of_recovery_stay_open_when_access_expired(
    expired_client: AsyncClient, path: str
):
    """Путь к оплате, вход и профиль истёкшим доступом НЕ закрываются (T-05.1-03).

    Утверждение написано ОТ ПРОТИВНОГО — «не уведён на `?expired=1`», — а не
    «ответил 200», и это существеннее, чем кажется. Часть этих страниц имеет
    право ответить редиректом по СВОЕЙ причине (например, увести гостя на
    `/login`), и требовать от них двухсотки значило бы вписать в тест гейта
    доступа чужие правила. Единственное, чего им делать НЕЛЬЗЯ, — отправлять
    человека оплачивать доступ вместо того, что он попросил.
    """
    response = await expired_client.get(path, follow_redirects=False)

    assert response.headers.get("location") != EXPIRED_LOCATION, (
        f"{path} закрыт гейтом доступа: человек не может ни войти, ни заплатить"
    )
    assert response.status_code in (200, 302), (
        f"{path} ответил {response.status_code} при истёкшем доступе"
    )


@pytest.mark.asyncio
async def test_pages_of_value_stay_open_while_the_trial_is_live(
    authed_client: AsyncClient
):
    """Граница сверху: внутри пробного срока те же страницы ОТКРЫТЫ.

    Без этого утверждения гейт, закрывающий ВСЕХ, прошёл бы все проверки выше.
    Пробный период обещан «в полном объёме» (критерий 2), и урезанного режима в
    плоской модели нет вовсе.

    ⚠️ `/groups` ПРОВЕРЯЕТСЯ ДРУГИМ УТВЕРЖДЕНИЕМ, И ПРИЧИНА НАЗВАНА ЗДЕСЬ, ЧТОБЫ
    СЛЕДУЮЩИЙ ЧИТАТЕЛЬ НЕ «ПРИВЁЛ ЕГО В СООТВЕТСТВИЕ». Раздел снят решением
    владельца (GRP-08, план 03-07), и его адрес БЕЗУСЛОВНО уводит на
    `/accounts` — двухсотки он не отдаёт никому и никогда, ни с доступом, ни
    без. Требовать её значило бы проверять не гейт, а снятый раздел; поэтому у
    него утверждение от противного — его редирект обязан быть СВОИМ, а не
    гейтовским.
    """
    for path in ("/ads", "/accounts", "/schedules", "/history"):
        response = await authed_client.get(path, follow_redirects=False)
        assert response.status_code == 200, (
            f"{path} ответил {response.status_code} внутри пробного срока"
        )

    retired = await authed_client.get("/groups", follow_redirects=False)
    assert retired.status_code == 302
    assert retired.headers["location"] == "/accounts", (
        "снятый раздел увёл не на свой адрес — гейт вмешался в живой доступ"
    )


# =============================================================================
# Группа `api` — JSON-поверхность отказа (заполняет план 05.1-03)
# =============================================================================


def test_api_gate_covers_exactly_the_declared_routers():
    """Множество закрытых JSON-роутеров равно объявленному — ни шире, ни уже.

    ⚠️ БЛИЗНЕЦ `test_pages_gate_covers_exactly_the_declared_routers`, И ЧИТАЕТ
    ОН ДРУГОЙ ИСХОДНИК. Страничная сборка живёт в `app/pages/__init__.py`,
    JSON-сборка — в `app/main.py`; перечень закрытого расширить на одной
    поверхности, забыв про другую, — ровно тот исход, ради которого обе группы
    держатся в одном файле.

    Роутер, добавленный будущим планом, роняет этот тест В ЛЮБОМ СЛУЧАЕ: он не
    назван ни в `GATED_API_ROUTERS`, ни в `OPEN_API_ROUTERS`. Ручное «не забыть
    повесить зависимость» средством защиты не считается (T-05.1-14).
    """
    included = _api_included_routers()

    gated = {name for name, is_gated in included.items() if is_gated}
    open_ = {name for name, is_gated in included.items() if not is_gated}

    assert gated == GATED_API_ROUTERS, (
        f"перечень закрытых JSON-роутеров разошёлся с объявленным: "
        f"лишние {gated - GATED_API_ROUTERS}, недостающие {GATED_API_ROUTERS - gated}"
    )
    assert open_ == OPEN_API_ROUTERS, (
        f"перечень ВСЕГДА открытых JSON-роутеров разошёлся с объявленным: "
        f"лишние {open_ - OPEN_API_ROUTERS}, недостающие {OPEN_API_ROUTERS - open_}"
    )
    assert set(included) == GATED_API_ROUTERS | OPEN_API_ROUTERS, (
        "в сборку приложения включён роутер, о котором этот тест не знает — "
        "решение «закрывает ли его истёкший доступ» не принято"
    )


def test_the_api_authentication_dependency_is_left_untouched():
    """`get_current_user_id` не получила ни проверки доступа, ни сессии БД.

    ⚠️ ЭТО ЗАПРЕТ, А НЕ ПРЕДПОЧТЕНИЕ. Зависимость обслуживает в том числе
    маршруты, которые обязаны оставаться открытыми (`GET /api/billing/*`), и
    добавление проверки доступа В НЕЁ расширило бы радиус отказа на них молча —
    правкой, выглядящей как «сделать в одном месте вместо пяти». Отказ по
    неоплате живёт в СОСЕДНЕЙ зависимости, и это единственная причина, по
    которой денежные маршруты не закрываются вместе с остальными.
    """
    tree = ast.parse(DEPENDENCIES_PY.read_text(encoding="utf-8"))
    authenticator = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "get_current_user_id"
    )
    body = ast.unparse(authenticator)

    assert "check_access" not in body, (
        "проверка доступа переехала в зависимость аутентификации — денежные "
        "маршруты закрылись вместе с остальными"
    )
    parameters = {argument.arg for argument in authenticator.args.args}
    assert "db" not in parameters, (
        "зависимость аутентификации получила сессию БД — она обслуживает и "
        "незащищённые пути, и цена запроса на них ничем не оправдана"
    )


def test_the_api_admin_gate_does_not_ask_about_paid_access():
    """Администратор без действующей подписки входит в админку (T-05.1-17).

    ⚠️ ЭТО НЕ УДОБСТВО, А УСЛОВИЕ ВОССТАНОВИМОСТИ ПРОДУКТА. Админка — место, где
    выдают бесплатный доступ; повесив на неё гейт доступа, мы получили бы
    систему, в которой администратор с истёкшим сроком не может открыть доступ
    НИ СЕБЕ, НИ ДРУГОМУ, и чинится она только правкой строки в базе руками.

    Утверждение снимается с ИСХОДНИКА по синтаксическому дереву, потому что
    вопрос здесь — про отсутствие ветки, а отсутствие проверяется чтением кода, а
    не запросом: маршрут, отвечающий администратору 200 сегодня, ничего не
    говорит о том, спросят ли у него оплату завтра. Вторая половина того же
    утверждения — что `admin_router` стоит в `OPEN_ROUTERS` страничной сборки —
    закреплена `test_pages_gate_covers_exactly_the_declared_routers`.
    """
    tree = ast.parse(DEPENDENCIES_PY.read_text(encoding="utf-8"))
    admin_gate = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "require_admin"
    )

    assert "check_access" not in ast.unparse(admin_gate), (
        "гейт прав администратора начал спрашивать про оплату — администратор "
        "без подписки не сможет выдать бесплатный доступ ни себе, ни другому"
    )


@pytest.mark.asyncio
async def test_api_of_value_is_refused_by_code_when_access_expired(
    expired_client: AsyncClient,
):
    """Просроченный не создаёт объявление через JSON-вход: отказ приходит КОДОМ.

    Код отказа — 402 либо 403, и он ОБЯЗАН отличаться от успеха: страничная
    поверхность отвечает 302 на место, где чинят, а JSON-клиенту редирект
    бессмыслен — он проследовал бы по нему и получил бы HTML вместо ресурса.
    """
    response = await expired_client.post(
        "/api/ads",
        json={"title": "T", "text": "Body", "images": []},
        follow_redirects=False,
    )

    assert response.status_code != 201, (
        "истёкший доступ создал объявление через JSON-вход — те же данные "
        "достижимы в обход страничного гейта"
    )
    assert response.status_code in (402, 403), (
        f"/api/ads ответил {response.status_code} при истёкшем доступе"
    )


@pytest.mark.asyncio
async def test_the_api_refusal_is_json_and_not_a_redirect(expired_client: AsyncClient):
    """Тело отказа — JSON с объяснением, а не HTML и не пустой редирект."""
    response = await expired_client.post(
        "/api/ads",
        json={"title": "T", "text": "Body", "images": []},
        follow_redirects=False,
    )

    assert "location" not in response.headers, (
        "JSON-вход ответил редиректом — клиент получил бы HTML страницы оплаты "
        "вместо объяснения отказа"
    )
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert body.get("detail"), "отказ не объяснён ни словом"


@pytest.mark.asyncio
async def test_api_of_money_stays_open_when_access_expired(
    expired_client: AsyncClient,
):
    """Денежные маршруты истёкшим доступом НЕ закрываются (T-05.1-16).

    Закрыть их значило бы запереть человека в продукте, где единственное
    действие, открывающее доступ, само требует доступа.
    """
    response = await expired_client.get("/api/billing/balance")

    assert response.status_code not in (402, 403), (
        "денежный маршрут закрыт гейтом доступа: человек не может заплатить"
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_the_api_of_login_stays_open_when_access_expired(expired_client: AsyncClient):
    """Вход истёкшим доступом НЕ закрывается — иначе чинить нечем."""
    response = await expired_client.post(
        "/api/auth/login",
        json={"email": "testuser@test.com", "password": "testpass123"},
    )

    assert response.status_code == 200, (
        f"вход ответил {response.status_code} при истёкшем доступе"
    )
    assert response.json().get("access_token")


@pytest.mark.asyncio
async def test_api_of_value_stays_open_while_the_trial_is_live(
    authed_client: AsyncClient,
):
    """Граница сверху: внутри пробного срока тот же вход отдаёт 201.

    Без этого утверждения гейт, отказывающий ВСЕМ, прошёл бы проверки выше.
    """
    response = await authed_client.post(
        "/api/ads",
        json={"title": "T", "text": "Body", "images": []},
    )

    assert response.status_code == 201, (
        f"/api/ads ответил {response.status_code} внутри пробного срока"
    )

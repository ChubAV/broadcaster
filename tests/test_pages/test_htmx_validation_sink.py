"""Сток T-07-13: отказ валидации фреймворка на пути htmx у страничного слоя.

ПОЧЕМУ ЭТОТ ФАЙЛ СУЩЕСТВУЕТ. Правило `{"code":"422"}` блока конфигурации со
свопом подменяет содержимое страницы ТЕЛОМ ответа. Пока такое тело — умолчание
веб-фреймворка, оно дословно повторяет присланное пользователем значение в поле
`input`, а `allowScriptTags`/`allowEval` остаются умолчаниями артефакта (оба
`true`), и подменяемое тело проходит через воскрешающий скрипты помощник
рантайма. Своп возвращает план 11-09 — ОДНОВРЕМЕННО с первым авторским 422;
смягчение обязано приземлиться РАНЬШЕ, иначе между двумя планами существует
дерево, на котором сток открыт. Этот файл и есть доказательство, что не
существует.

⚠️ ГРАНИЦА ОБХОДА НАЗЫВАЕТСЯ ЗДЕСЬ СЛОВАМИ, А НЕ ОСТАВЛЯЕТСЯ НА ДОГАДКУ. Гейт,
чья вселенная не выписана, через фазу читается как утверждение обо ВСЁМ — и
пропуск в нём становится неизвестным.

1. СИСТЕМАТИЧЕСКИ ОБХОДЯТСЯ МАРШРУТЫ С ЦЕЛЫМ ПАРАМЕТРОМ ПУТИ, И ТОЛЬКО ОНИ.
   Основание не в удобстве: только у них отказ разбора наступает ГАРАНТИРОВАННО
   и ДО тела обработчика. Строковый параметр пропустил бы токен внутрь
   обработчика, и тот ИСПОЛНИЛ БЫ ДЕЙСТВИЕ — обход, «проверяющий» отказ,
   удалял бы строки.

2. ОТКАЗЫ ТЕЛА ФОРМЫ И СТРОКИ ЗАПРОСА ЗАКРЫТЫ ТЕМ ЖЕ ВЫХОДОМ, НО ОБХОДОМ НЕ
   ПРОВЕРЯЮТСЯ. Ветвь выбирается ТИПОМ ИСКЛЮЧЕНИЯ и ПРИНАДЛЕЖНОСТЬЮ обработчика
   пакету страничного слоя, а НЕ местом ошибки: выход `exc.errors()` не читает
   вовсе. Поэтому место ошибки закрывается ПОИМЁННЫМИ случаями (тело: POST
   `/schedules/new` без `ad_id`; строка запроса: GET курсора групп с
   `after_id=0`) и модульным тестом выхода на исключениях трёх мест
   (`tests/test_pages/test_htmx_response_layer.py`), а не третьим обходом.

3. СИСТЕМАТИЧЕСКОГО ОБХОДА ПОЛЕЙ ТЕЛА И СТРОКИ ЗАПРОСА НЕТ, И ЭТО РЕШЕНИЕ, А НЕ
   ЗАБЫВЧИВОСТЬ. Он потребовал бы собирать ГОДНЫЕ значения всех прочих полей
   каждого маршрута — а значения этих полей в интерфейсе рисует сервер, то есть
   обход выдумывал бы вход, которого продукт не порождает.

⚠️ ВЕТВЬ ВЫБИРАЕТСЯ ДВУМЯ ПРИЗНАКАМИ, И ВТОРОЙ НЕ УКРАШЕНИЕ (D-07). Обработчик
`RequestValidationError` регистрируется на ПРИЛОЖЕНИИ ЦЕЛИКОМ — своих
обработчиков исключений у `APIRouter` нет. Ветвь по ОДНОМУ заголовку превратила
бы запрос к JSON-API `app/routes/` с заголовком htmx в пустой 400, то есть
сломала бы контракт другого транспорта. Поэтому второй признак — принадлежность
сорвавшегося обработчика пакету `app.pages`, и граница эта утверждается здесь
обходом ОБОИХ слоёв, а не доверием к прозе.
"""

import pytest
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_settings
from app.main import create_app
from tests.test_pages.test_account_groups import _seed_account
from tests.test_templates.test_htmx_markup_gates import (
    CALL_BLOCK_OPEN,
    _all_templates,
    _call_argument,
    _strip_comments,
    _value_pattern,
)

# Пакеты двух слоёв. Именами, а не проверкой пути файла: принадлежность
# обработчика слою есть свойство МОДУЛЯ, и приложение видит именно его.
PAGE_LAYER_PACKAGE = "app.pages"
JSON_API_PACKAGE = "app.routes"

# Признак слоя письма ставится ПОЗАПРОСНО, а не фикстурой `htmx_client`:
# фикстура выставила бы его ВСЕМУ клиенту, а половина утверждений ниже нужна
# БЕЗ него — и объект клиента у фикстур общий (записанное свойство `htmx_client`).
HTMX_HEADERS = {"HX-Request": "true"}

# Токен, который целым числом не разбирается НИКОГДА. Словом, а не числом вне
# диапазона: диапазон закрывают границы внутри обработчиков (D-07), и величина
# вне колонки идёт сегодня веткой «записи нет», а не отказом валидации.
MALFORMED_PATH_TOKEN = "not-a-number"

# Форма ответа смягчения: пустой 400. Не 422 — с плана 11-09 правило 422
# свопает, а `[45]..` не свопает, и плашка отказа поднимается.
EMPTY_BAD_REQUEST = 400

# Приставка адресов JSON-API. Сверка по НАЧАЛУ значения: адрес, начинающийся с
# неё, уезжает на другой транспорт с другим контрактом.
JSON_API_PREFIX = "/api/"

# Атрибуты, значением которых слой письма задаёт АДРЕС ЗАПРОСА.
HX_REQUEST_ATTRIBUTES = ("hx-get", "hx-post", "hx-put", "hx-patch", "hx-delete")

# ЛЕТОПИСЬ ЧИСЕЛ. Оба выписаны ЗДЕСЬ литералами и ПОСТАВЛЕНЫ ПРОГОНОМ, а не
# выведены обходом в момент проверки: гейт, считающий ожидание по проверяемому
# охвату, узаконил бы собственным зелёным цветом и появление нового маршрута, и
# поломку разбора, отдавшую пустой обход (форма записи — с
# `tests/test_pages/test_htmx_response_contract.py`).
#
# 2026-09-16, Фаза 11, план 11-07, задача 1. Замер — обходом таблицы маршрутов
# собранного `create_app`: пары «маршрут × метод» (кроме HEAD и OPTIONS), у
# которых хотя бы один параметр ПУТИ объявлен целым.
#   страничный слой (`app.pages`) — 27 пар: 10 GET и 17 POST;
#   JSON-API (`app.routes`)       —  8 пар: 2 GET, 1 POST, 2 PUT, 3 DELETE.
#
# ⚠️ ПРАВИЛО ОТБОРА МЕТОДОВ ОДНО НА ОБА СЛОЯ, И АСИММЕТРИИ ЗДЕСЬ НЕТ. У
# страничного слоя методов кроме GET и POST не оказалось НИ ОДНОГО, поэтому
# «все методы» и «GET либо POST» дают для него одно и то же множество; у
# JSON-API ограничение до GET/POST выбросило бы пять пар из восьми — то есть
# границу D-07 утверждали бы три маршрута вместо восьми.
VALIDATION_SINK_ROUTES_DECLARED = 27
JSON_API_BOUNDARY_ROUTES_DECLARED = 8

# Методы, которые обход не трогает: собственного тела у них нет, а HEAD вдобавок
# добавляется транспортом, а не объявлением маршрута.
UNTRAVERSED_METHODS = frozenset({"HEAD", "OPTIONS"})


# --- РАЗБОРЩИКИ ТАБЛИЦЫ МАРШРУТОВ --------------------------------------------


def _integer_path_parameters(route: APIRoute) -> list[str]:
    """Имена параметров ПУТИ маршрута, объявленных целым числом."""
    return [
        parameter.name
        for parameter in route.dependant.path_params
        if getattr(parameter.field_info, "annotation", None) is int
    ]


def _belongs_to(route: APIRoute, package: str) -> bool:
    """Живёт ли обработчик маршрута в названном пакете.

    Сверяется и само имя пакета, и его приставка с точкой: `app.pages` и
    `app.pages.schedules` — один слой, а `app.pages_extra` был бы другим.
    """
    module = getattr(route.endpoint, "__module__", "") or ""
    return module == package or module.startswith(f"{package}.")


def _traversed_pairs(app, package: str) -> list[tuple[str, str]]:
    """Пары «метод × маршрут» слоя, у которых отказ разбора ПУТИ гарантирован.

    Возвращаются пары, а не маршруты: один объект маршрута может нести
    несколько методов, и обход, считающий маршруты, утверждал бы о меньшем
    числе запросов, чем делает.
    """
    pairs: list[tuple[str, str]] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not _belongs_to(route, package):
            continue
        if not _integer_path_parameters(route):
            continue
        for method in sorted(route.methods):
            if method in UNTRAVERSED_METHODS:
                continue
            pairs.append((method, route.path))
    return sorted(pairs)


def _malformed_url(path: str) -> str:
    """Адрес маршрута, каждый местозаполнитель которого заменён негодным токеном.

    Заменяются ВСЕ местозаполнители, а не только целочисленный: маршрут с двумя
    параметрами иначе получил бы в один из них пустую строку, и отказ пришёл бы
    не от того параметра, о котором правило говорит.
    """
    result = ""
    rest = path
    while "{" in rest:
        before, _, after = rest.partition("{")
        _placeholder, _, tail = after.partition("}")
        result += before + MALFORMED_PATH_TOKEN
        rest = tail
    return result + rest


async def _traverse(
    client: AsyncClient,
    pairs: list[tuple[str, str]],
    *,
    headers: dict[str, str],
) -> dict[tuple[str, str], object]:
    """Ответы слоя на негодный адрес по каждой паре обхода.

    ⚠️ ИСКЛЮЧЕНИЕ ЛОВИТСЯ И СТАНОВИТСЯ ИСХОДОМ, А НЕ ПАДЕНИЕМ ОБХОДА. Со снятым
    обработчиком отказ валидации ВЫЛЕТАЕТ из транспорта наружу (замерено), и
    обход, не ловящий его, уронил бы отрицательный контроль по‑питоновски —
    вместо того чтобы НАЗВАТЬ нарушителя, ради чего контроль и написан.
    """
    seen: dict[tuple[str, str], object] = {}
    for method, path in pairs:
        url = _malformed_url(path)
        try:
            seen[(method, path)] = await client.request(
                method, url, headers=headers, follow_redirects=False
            )
        except Exception as exc:  # noqa: BLE001 — исход, а не сбой обхода
            seen[(method, path)] = exc
    return seen


def _carries_a_framework_validation_body(outcome) -> bool:
    """Несёт ли исход ТЕЛО отказа валидации фреймворка.

    ⚠️ ПРИЗНАК СУЖЕН ДО «422 И JSON», А НЕ «В ТЕЛЕ ЕСТЬ `detail`», И СУЖЕН ПО
    ЗАМЕРУ. Прежняя редакция считала нарушителем ЛЮБОЕ тело с `detail`, и на
    первом же прогоне объявила таковыми десять админских маршрутов, отвечающих
    `403 {"detail":"Admin access required"}`. Отказ АВТОРИЗАЦИИ телом отказа
    валидации не является: он приходит из зависимости, свопаться ему нечем, и
    смешение двух отказов означало бы, что правило краснеет там, где предмета
    нет, — а значит, его научатся гасить.

    Исключение считается несущим: со снятым обработчиком тело собрал бы кто
    угодно выше по стеку, и «нарушителя нет» было бы неправдой.
    """
    if isinstance(outcome, Exception):
        return True
    return outcome.status_code == 422 and "application/json" in (
        outcome.headers.get("content-type", "")
    )


# --- РАЗБОРЩИКИ РАЗМЕТКИ -----------------------------------------------------


def _htmx_addresses(templates: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Адреса запросов слоя письма в разметке: пары «шаблон — адрес».

    Считаются ОБА способа задать адрес: значение атрибута запроса и аргумент
    `action` блочного вызова макроса-обёртки — у второго адрес уезжает сразу в
    `action` и в `hx-post`, поэтому пропуск его означал бы слепоту к пяти
    сегодняшним формам письма.
    """
    found: list[tuple[str, str]] = []
    for name, source in templates:
        body = _strip_comments(source)
        for attribute in HX_REQUEST_ATTRIBUTES:
            for match in _value_pattern(attribute).finditer(body):
                value = match.group(2) if match.group(2) is not None else match.group(3)
                found.append((name, value or ""))
        for call in CALL_BLOCK_OPEN.finditer(body):
            passed, value = _call_argument(call.group(1), "action")
            if passed and value is not None:
                found.append((name, value))
    return found


def _addresses_pointing_at_the_json_api(
    templates: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Адреса запросов слоя письма, указывающие на JSON-API."""
    return [
        (name, value)
        for name, value in _htmx_addresses(templates)
        if value.startswith(JSON_API_PREFIX)
    ]


# --- ПОИМЁННЫЕ СЛУЧАИ ТРЁХ МЕСТ ОШИБКИ ---------------------------------------


@pytest.mark.asyncio
async def test_a_malformed_htmx_request_gets_an_empty_bad_request(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Три МЕСТА ошибки у страничного слоя под htmx — один и тот же пустой 400.

    Места разные (путь, тело формы, строка запроса), выход один: ветвь не
    зависит от места ошибки. Правило поимённое, потому что систематический обход
    закрывает только ось ПУТИ — граница выписана в шапке модуля.
    """
    account = await _seed_account(db_session)

    cases = {
        "путь": await authed_client.post(
            f"/schedules/{MALFORMED_PATH_TOKEN}/toggle",
            headers=HTMX_HEADERS,
            follow_redirects=False,
        ),
        "тело формы": await authed_client.post(
            "/schedules/new",
            data={},
            headers=HTMX_HEADERS,
            follow_redirects=False,
        ),
        "строка запроса": await authed_client.get(
            f"/accounts/{account.id}/groups/partial?after_id=0",
            headers=HTMX_HEADERS,
            follow_redirects=False,
        ),
    }

    disagreed = {
        place: (response.status_code, response.content[:120])
        for place, response in cases.items()
        if response.status_code != EMPTY_BAD_REQUEST or response.content != b""
    }

    assert not disagreed, (
        "отказ валидации страничного слоя на пути htmx обязан быть ПУСТЫМ "
        f"{EMPTY_BAD_REQUEST} при ЛЮБОМ месте ошибки, а разошлись: "
        + "; ".join(
            f"{place} = код {code}, тело {body!r}"
            for place, (code, body) in sorted(disagreed.items())
        )
        + ". Непустое тело здесь есть СТОК: с плана 11-09 правило 422 свопает "
        "его в DOM, а состав такого тела выбирает не приложение"
    )


# --- ОБХОД СТРАНИЧНОГО СЛОЯ --------------------------------------------------


@pytest.mark.asyncio
async def test_no_htmx_request_receives_a_framework_validation_body(
    admin_client: AsyncClient, test_settings
):
    """Каждый маршрут страничного слоя отвечает слою письма ПУСТЫМ 400.

    ⚠️ ОБХОД ИДЁТ ПОД АДМИНИСТРАТОРОМ, И ЭТО НЕ УДОБСТВО, А УСЛОВИЕ ТОГО, ЧТОБЫ
    ОБХОД ВООБЩЕ ДОХОДИЛ ДО ПРЕДМЕТА. Замер первого прогона: под обычным
    пользователем ДЕСЯТЬ из двадцати семи пар отвечают `403 Admin access
    required` — `app/pages/admin.py` держит права ЗАВИСИМОСТЬЮ
    (`Depends(require_admin)`), а зависимости решаются РАНЬШЕ разбора
    параметров маршрута. То есть отказ валидации на них не наступал вовсе, и
    обход, объявленный полным, проверял бы семнадцать маршрутов из двадцати
    семи. Права здесь — не предмет правила; предмет — форма отказа разбора, и
    добраться до него можно только пройдя гард. Прочих маршрутов личность не
    касается: владение проверяется В ТЕЛЕ обработчика, то есть ПОСЛЕ разбора.

    ⚠️ УТВЕРЖДАЕТСЯ РАВЕНСТВО МИТИГИРОВАННОЙ ФОРМЕ, А НЕ ОТСУТСТВИЕ `detail`.
    Слабая редакция («тела отказа нет») зеленела бы на ЛЮБОМ ответе, до
    валидации не дошедшем, — на том же `403`, на редиректе, на чём угодно.
    Гард, заведённый будущей фазой на страничном роутере, выхолостил бы обход в
    зелёную пустоту МОЛЧА. Равенство `(400, b"")` этого не позволяет: маршрут,
    не дошедший до разбора, краснеет так же громко, как маршрут, отдавший тело.
    """
    app = create_app(settings=test_settings)
    pairs = _traversed_pairs(app, PAGE_LAYER_PACKAGE)

    outcomes = await _traverse(admin_client, pairs, headers=HTMX_HEADERS)

    disagreed = {
        pair: outcome
        for pair, outcome in outcomes.items()
        if isinstance(outcome, Exception)
        or (outcome.status_code, outcome.content) != (EMPTY_BAD_REQUEST, b"")
    }

    assert not disagreed, (
        f"пар обхода страничного слоя, ответивших слою письма не пустым "
        f"{EMPTY_BAD_REQUEST}: {len(disagreed)} из {len(pairs)}\n"
        + "\n".join(
            f"  {method} {path} → "
            + (
                f"исключение {type(outcome).__name__}"
                if isinstance(outcome, Exception)
                else f"{outcome.status_code} {outcome.content[:100]!r}"
                + (
                    "  ← ТЕЛО ОТКАЗА ВАЛИДАЦИИ ФРЕЙМВОРКА"
                    if _carries_a_framework_validation_body(outcome)
                    else "  ← до разбора параметров запрос НЕ ДОШЁЛ"
                )
            )
            for (method, path), outcome in sorted(disagreed.items())
        )
        + "\nТело отказа валидации дословно повторяет присланное пользователем "
        "значение, а правило 422 с плана 11-09 подменяет им содержимое "
        "страницы (T-07-13). Ответ, до разбора не дошедший, означает, что "
        "обход перестал наблюдать предмет на этом маршруте"
    )


# --- ГРАНИЦА ДРУГОГО ТРАНСПОРТА (D-07) ---------------------------------------


@pytest.mark.asyncio
async def test_the_json_api_keeps_its_validation_contract(
    client: AsyncClient, auth_headers: dict, test_settings
):
    """JSON-API отвечает БАЙТ-В-БАЙТ одинаково с заголовком htmx и без него.

    ⚠️ ЭТО УТВЕРЖДЕНИЕ О ГРАНИЦЕ, А НЕ О ФОРМЕ ОТВЕТА. Обработчик исключения
    висит на приложении целиком, поэтому «JSON-API не трогается» (D-07) есть не
    отсутствие правки, а СВОЙСТВО, которое обязано быть измерено: ветвь по
    одному заголовку htmx превратила бы каждый ответ ниже в пустой 400.
    """
    app = create_app(settings=test_settings)
    pairs = _traversed_pairs(app, JSON_API_PACKAGE)

    without = await _traverse(client, pairs, headers=auth_headers)
    with_htmx = await _traverse(
        client, pairs, headers={**auth_headers, **HTMX_HEADERS}
    )

    disagreed: list[str] = []
    for pair in pairs:
        bare, flagged = without[pair], with_htmx[pair]
        method, path = pair
        if isinstance(bare, Exception) or isinstance(flagged, Exception):
            disagreed.append(f"  {method} {path} → обход вылетел исключением")
            continue
        if bare.status_code != 422:
            disagreed.append(
                f"  {method} {path} → без заголовка htmx пришло "
                f"{bare.status_code}, а контракт JSON-API объявляет 422 "
                "(правило перестало наблюдать предмет)"
            )
        if (bare.status_code, bare.content) != (flagged.status_code, flagged.content):
            disagreed.append(
                f"  {method} {path} → заголовок htmx ИЗМЕНИЛ ответ: без него "
                f"{bare.status_code} {bare.content[:80]!r}, с ним "
                f"{flagged.status_code} {flagged.content[:80]!r}"
            )

    assert not disagreed, (
        "ветвь htmx дотянулась до JSON-API `app/routes/` — это другой "
        "транспорт со своим контрактом 422 (D-07):\n" + "\n".join(disagreed)
    )

    # ПОИМЁННЫЙ СЛУЧАЙ ТЕЛА: место ошибки у JSON-API тоже не должно ничего
    # менять. Обход выше закрывает только ось ПУТИ.
    body_bare = await client.post("/api/schedules", json={}, headers=auth_headers)
    body_flagged = await client.post(
        "/api/schedules", json={}, headers={**auth_headers, **HTMX_HEADERS}
    )
    assert (body_bare.status_code, body_bare.content) == (
        body_flagged.status_code,
        body_flagged.content,
    ), (
        "отказ ТЕЛА у JSON-API разошёлся между транспортами: без заголовка "
        f"{body_bare.status_code} {body_bare.content[:80]!r}, с заголовком "
        f"{body_flagged.status_code} {body_flagged.content[:80]!r}"
    )
    assert body_bare.status_code == 422, (
        f"поимённый случай тела JSON-API ответил {body_bare.status_code}, а не "
        "422 — правило перестало наблюдать контракт, о котором говорит"
    )


def test_the_page_branch_is_chosen_only_for_page_endpoints(test_settings):
    """Признак страничного слоя истинен РОВНО у обработчиков пакета `app.pages`.

    Обходится ВСЯ таблица маршрутов приложения, а не выборка: предмет — граница,
    и выборка, собранная по тому же правилу, которое проверяется, утверждала бы
    сама о себе.
    """
    from starlette.requests import Request

    from app.pages.htmx import _validated_by_the_page_layer

    app = create_app(settings=test_settings)

    def _request_for(endpoint) -> Request:
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "server": ("test", 80),
            "path": "/",
            "root_path": "",
            "query_string": b"",
            "headers": [],
        }
        if endpoint is not None:
            scope["endpoint"] = endpoint
        return Request(scope)

    page_routes, other_routes, disagreed = 0, 0, []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        expected = _belongs_to(route, PAGE_LAYER_PACKAGE)
        observed = _validated_by_the_page_layer(_request_for(route.endpoint))
        if expected:
            page_routes += 1
        else:
            other_routes += 1
        if observed is not expected:
            disagreed.append(
                f"  {sorted(route.methods)} {route.path} "
                f"({getattr(route.endpoint, '__module__', '?')}) → признак "
                f"{observed}, ожидался {expected}"
            )

    assert not disagreed, (
        "признак страничного слоя разошёлся с принадлежностью обработчика:\n"
        + "\n".join(disagreed)
    )

    # АНТИВАКУУМ ОБЕИХ СТОРОН. Без него правило зеленело бы и на признаке,
    # возвращающем всегда `False` (не нашлось бы страничных), и на всегда
    # `True` (не нашлось бы прочих).
    assert page_routes > 0 and other_routes > 0, (
        f"обход нашёл страничных маршрутов {page_routes}, прочих "
        f"{other_routes} — одна из сторон границы пуста, и правило "
        "утверждало бы ни о чём"
    )

    # ОТСУТСТВИЕ ОБРАБОТЧИКА В ОБЛАСТИ ЗАПРОСА — ЛОЖЬ, А НЕ ОШИБКА. Маршрут не
    # найден либо исключение пришло из другого источника: ветвь htmx в таком
    # случае не берётся вовсе.
    assert _validated_by_the_page_layer(_request_for(None)) is False, (
        "признак истинен на запросе БЕЗ обработчика в области видимости — "
        "ветвь бралась бы там, где сорвавшийся обработчик неизвестен"
    )


@pytest.mark.asyncio
async def test_control_without_the_handler_the_traversal_names_an_offender(
    admin_client: AsyncClient, db_session, test_settings
):
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ: без обработчика обход НАЗЫВАЕТ нарушителя.

    ⚠️ ЗУБЫ ОБХОДА ПОКАЗЫВАЮТСЯ, А НЕ ЗАЯВЛЯЮТСЯ. Обход, ничего не находящий на
    дереве БЕЗ смягчения, зеленел бы и на дереве со снятым смягчением — то есть
    охранял бы ровно ничего. Подаётся приложение, собранное тем же
    `create_app`, у которого обработчик отказа валидации ИЗЪЯТ.

    ⚠️ КОНТРОЛЬ ХОДИТ ПОД ВОШЕДШИМ АДМИНИСТРАТОРОМ, И ЭТО ЗАПИСАННЫЙ ЗАМЕР, А
    НЕ ПРЕДОСТОРОЖНОСТЬ. Первая редакция ходила клиентом БЕЗ входа и находила
    НОЛЬ нарушителей на двадцати семи парах за 0.89 с: зависимость слоя страниц
    отказывает РАНЬШЕ разбора параметров, и до отказа валидации запрос не
    доходил вовсе. Контроль, не дошедший до собственного предмета, доказывает
    не отсутствие зубов, а собственную негодность.

    ⚠️ COOKIE БЕРЁТСЯ У ФИКСТУРЫ, А ВХОД НЕ ПОВТОРЯЕТСЯ ЗДЕСЬ. Приложение
    контроля собрано теми же настройками (тот же ключ подписи) и делит ту же
    сессию базы, поэтому удостоверение, выданное фикстурой, действительно и
    здесь. Вторая копия последовательности входа разошлась бы с фикстурой
    молча — той же доктриной единственного источника, по которой обход берёт
    разборщики разметки ввозом.

    ⚠️ СМЯГЧЕНИЕ ПОДМЕНЯЕТСЯ УМОЛЧАНИЕМ ФРЕЙМВОРКА, А НЕ ИЗЫМАЕТСЯ, И ЭТО
    ПОПРАВКА ПО ЗАМЕРУ. Первая редакция ВЫНИМАЛА обработчик вовсе и получила на
    всех двадцати семи парах `500`: у приложения зарегистрирован ещё и общий
    обработчик `Exception` (`app/main.py`), и вынутый отказ валидации доезжал до
    него, превращаясь в пятисотку. Такого дерева не существовало НИКОГДА —
    контроль показывал зубы на небывальщине. Снятое смягчение есть возврат
    УМОЛЧАНИЯ ФРЕЙМВОРКА (тело 422 с эхо ввода), и именно его подмена
    воспроизводит дерево ДО этого плана.

    ⚠️ В КРАСНОЙ ФАЗЕ ЭТОТ КОНТРОЛЬ КРАСЕН, И ЭТО ЕГО ЧЕСТНОЕ СОСТОЯНИЕ, А НЕ
    ПОЛОМКА. Пока смягчения нет, подменять нечего: посылка контроля («на отказе
    валидации стои́т СВОЙ обработчик») ложна, и утверждение об этом краснеет
    первым — с текстом, называющим причину.
    """
    app = create_app(settings=test_settings)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: test_settings

    mitigated = app.exception_handlers.get(RequestValidationError)
    assert mitigated is not None, (
        "обработчика отказа валидации в собранном приложении не оказалось — "
        "контроль подменял бы то, чего нет, и зеленел бы по этой причине"
    )
    assert mitigated is not request_validation_exception_handler, (
        "на отказе валидации в собранном приложении стои́т УМОЛЧАНИЕ "
        "ФРЕЙМВОРКА, то есть смягчения T-07-13 в дереве нет: контроль подменил "
        "бы умолчание умолчанием и объявил бы зубы, ничего не показав"
    )

    # Дерево ДО этого плана: тело 422 с эхо ввода, которое правило 422 с плана
    # 11-09 свопает в DOM.
    app.exception_handlers[RequestValidationError] = (
        request_validation_exception_handler
    )
    # Стек промежуточных слоёв собирается лениво и запоминается; без сброса
    # подмена не доехала бы до транспорта.
    app.middleware_stack = None

    pairs = _traversed_pairs(app, PAGE_LAYER_PACKAGE)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies=admin_client.cookies,
    ) as bare_client:
        outcomes = await _traverse(bare_client, pairs, headers=HTMX_HEADERS)

    offenders = [
        pair
        for pair, outcome in outcomes.items()
        if _carries_a_framework_validation_body(outcome)
    ]

    observed = sorted(
        {
            (
                f"исключение {type(outcome).__name__}"
                if isinstance(outcome, Exception)
                else str(outcome.status_code)
            )
            for outcome in outcomes.values()
        }
    )

    assert offenders, (
        "со СНЯТЫМ обработчиком обход не нашёл ни одного нарушителя — значит "
        "он не находит их никогда, и зелёный цвет соседнего правила не "
        f"означает ничего. Обойдено пар: {len(pairs)}; снятые исходы: "
        f"{observed}. Исходы, среди которых нет ни отказа валидации, ни "
        "исключения, означают, что запрос до РАЗБОРА ПАРАМЕТРОВ не дошёл — "
        "чините контроль, а не обход"
    )


# --- ГЕЙТ АДРЕСОВ РАЗМЕТКИ (T-11-38) -----------------------------------------


def test_no_htmx_address_in_templates_points_at_the_json_api():
    """Ни один адрес запроса слоя письма в разметке не указывает на JSON-API.

    ⚠️ ЭТО ЗАКРЫТИЕ ОСТАТКА, А НЕ ПОВТОР ГРАНИЦЫ D-07. Граница говорит, что
    запрос htmx к JSON-API сохранит контракт 422 — то есть получит тело
    умолчания фреймворка. Здесь утверждается, что такой запрос из разметки
    НЕДОСТИЖИМ вовсе: остаток закрывается отсутствием адресата, а не
    экранированием.
    """
    offenders = _addresses_pointing_at_the_json_api(_all_templates())

    assert not offenders, (
        "адрес запроса слоя письма указывает на JSON-API:\n"
        + "\n".join(f"  {name}: {value}" for name, value in sorted(offenders))
        + "\nОтвет такого запроса — умолчание фреймворка с эхо ввода, и ветвь "
        "страничного слоя до него не дотянется по построению (D-07)"
    )


def test_control_a_synthetic_json_api_address_reddens_the_template_rule():
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ гейта адресов — ОБА способа задать адрес.

    Контроль подаёт сканеру ИЗМЕНЁННОЕ дерево, а не проверяемое: правило,
    зелёное на сегодняшней разметке, обязано показать зубы на разметке, которой
    оно запрещает появиться. Способов задать адрес два, и слепота к любому из
    них означала бы, что гейт стережёт половину.
    """
    synthetic_attribute = [
        ("синтетический_атрибут.html", '<form hx-post="/api/ads/1"></form>')
    ]
    synthetic_wrapper = [
        (
            "синтетический_вызов.html",
            "{% call form_wrapper(action='/api/ads/1') %}{% endcall %}",
        )
    ]

    assert _addresses_pointing_at_the_json_api(synthetic_attribute), (
        "сканер не увидел адреса JSON-API в ЗНАЧЕНИИ АТРИБУТА запроса — гейт "
        "слеп к первому из двух способов задать адрес"
    )
    assert _addresses_pointing_at_the_json_api(synthetic_wrapper), (
        "сканер не увидел адреса JSON-API в аргументе `action` вызова "
        "макроса-обёртки — гейт слеп ко второму способу, а именно им заданы "
        "сегодняшние формы письма"
    )

    # АНТИВАКУУМ: сканер не объявляет нарушителем ЛЮБОЙ адрес.
    local = [("синтетический_местный.html", '<form hx-post="/schedules/new"></form>')]
    assert not _addresses_pointing_at_the_json_api(local), (
        "сканер объявил нарушителем местный адрес — он краснел бы на всей "
        "сегодняшней разметке, и его зелёный цвет ничего не означал бы"
    )


# --- АНТИВАКУУМ ОБОИХ ОБХОДОВ ------------------------------------------------


def test_the_number_of_traversed_routes_is_the_declared_one(test_settings):
    """Оба обхода обходят ОБЪЯВЛЕННОЕ число пар, а не сколько получилось.

    Без этого правила поломка разбора таблицы маршрутов давала бы ПУСТОЙ обход,
    а пустой обход зелен по построению: соседние правила объявили бы отсутствие
    нарушителей, не сделав ни одного запроса.
    """
    app = create_app(settings=test_settings)

    page_pairs = _traversed_pairs(app, PAGE_LAYER_PACKAGE)
    api_pairs = _traversed_pairs(app, JSON_API_PACKAGE)

    assert len(page_pairs) == VALIDATION_SINK_ROUTES_DECLARED, (
        f"пар обхода страничного слоя стало {len(page_pairs)}, в летописи "
        f"записано {VALIDATION_SINK_ROUTES_DECLARED}:\n"
        + "\n".join(f"  {method} {path}" for method, path in page_pairs)
        + "\nРост означает новый маршрут с целым параметром пути — он обязан "
        "войти в обход осознанно; убыль означает снятый маршрут либо "
        "сломанный разбор таблицы"
    )
    assert len(api_pairs) == JSON_API_BOUNDARY_ROUTES_DECLARED, (
        f"пар обхода JSON-API стало {len(api_pairs)}, в летописи записано "
        f"{JSON_API_BOUNDARY_ROUTES_DECLARED}:\n"
        + "\n".join(f"  {method} {path}" for method, path in api_pairs)
        + "\nГраница D-07 утверждается ИМЕННО этими парами"
    )

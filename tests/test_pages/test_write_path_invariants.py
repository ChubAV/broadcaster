"""Запреты Фазы 10 о СЕРВЕРНОЙ стороне письма, которые суита не держала целиком.

Предмет (план 15-26, решение владельца Г-1 «Правила сейчас», класс ответа
`require-enforcement` — план 15-12, D-04). Двенадцать строк реестра запретов
класса `product-invariant` говорят о серверной стороне письма: гард
происхождения, граница идентификатора, постраничный вывод, адрес приземления,
cookie сессии. По каждой сперва искалось действующее правило, и оно
засчитывалось, только если краснело на нарушении ИМЕННО этой формулировки,
внесённом временной правкой дерева (замеры — в `15-26-SUMMARY.md`). Здесь стоят
правила на то, на чём действующие правила оставались зелёными. Каждое правило
называет в докстринге тождество своего запрета:

* `10-03#5` — собственного `set_cookie` в обработчике входа под пользователем
  нет, cookie ставит единственная функция установки:
  `test_the_session_cookie_is_set_only_by_its_single_setter`;
* `10-18#0` — гард происхождения не висит на маршрутах чтения и не расширен на
  всё приложение: `test_the_origin_guard_is_called_only_inside_post_route_handlers`;
* `10-18#1` — форма отказа гарда одна у всех потребителей:
  `test_every_origin_guard_site_answers_the_refusal_of_the_existing_consumers`;
* `10-25#3`, `10-32#3` — граница «запрос без обоих заголовков пропускается» не
  пересматривается на месте вызова:
  `test_no_origin_guard_site_re_examines_the_headerless_boundary`;
* `10-28#1`, `10-29#1` — смещение и размер порции (и в админском модуле) не
  ограничены границей идентификатора:
  `test_no_pagination_value_is_limited_by_the_identifier_bound`;
* `10-08#2` — негодное поле контекста не получает отказа обработчика ни на
  одном из двух транспортов:
  `test_an_unusable_context_field_answers_as_an_absent_one_on_both_transports`;
* `10-12#3` — отбрасывание негодного поля контекста не стоит самого действия:
  `test_an_unusable_context_field_never_costs_the_deletion_itself`.

У каждого правила есть контроль на синтетике. У правил, читающих исходники,
это копия боевого файла с нарушением: разборщик принимает исходники
ПАРАМЕТРОМ, и контроль утверждает, что копия названа, а боевое дерево — нет. У
двух правил, исполняющих маршрут, контроль подаёт сличителю синтетические
наблюдения. Сам маршрут в контроле не правится, направление по продукту
замерено правкой дерева в сводке плана.

ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ (D-16). Правила читают исходники `app/**/*.py`
разбором `ast` и исполняют один маршрут — `POST /schedules/{id}/delete` —
клиентом суиты. Браузер, прокси и заголовки, которые шлёт настоящий клиент, не
исполняются. Отдельно по строкам:
* `10-03#5`: утверждается, что вызов `.set_cookie(` и строковая константа
  `set-cookie` (запись заголовка руками) встречаются в `app/` только внутри
  функции установки. Правило строже предмета: оно смотрит на всё приложение, а
  не только на обработчик входа под пользователем. Cookie, собранную
  промежуточным слоем стороннего пакета, разбор `app/` не видит. Совпадение
  набора атрибутов установки и снятия держат правила `test_impersonation.py` и
  `test_cookie_flags.py`, а не этот файл.
* `10-18#0`: гард узнаётся по имени, под которым его ввезли из
  `app.pages.common` (с псевдонимом импорта и обращением через модуль). Функция,
  повторяющая сверку заголовков своими словами, не узнаётся как гард: её
  держит правило `10-25#3` ниже через чтение заголовков. Какие ИЗМЕНЯЮЩИЕ
  маршруты гард несут, решает владелец. Число мест вызова держит
  `test_the_boundary_of_both_gate_universes_is_declared_by_number`, а этот файл
  утверждает только, что вне POST-обработчиков вызова нет.
* `10-18#1`: утверждается посимвольная (по дереву разбора) форма отказа на
  месте вызова — `ORIGIN_GUARD_REFUSAL`. Ответ, который отдаёт клиенту
  фреймворк, здесь не исполняется. Форму выбрал владелец (D-08 Фазы 11, D-01
  Фазы 14), и её смена — новое решение владельца вместе с литералом.
* `10-25#3`, `10-32#3`: предикат ведёт себя по своему докстрингу — это держит
  `test_control_a_request_with_neither_header_still_passes` модуля гарда. Здесь
  утверждается, что на месте вызова условие отказа — ровно `not гард(...)`, и
  что заголовки `Origin` и `Sec-Fetch-Site` читает только сам гард. Заголовок,
  имя которого собрано из частей во время исполнения, разбором не виден.
* `10-28#1`, `10-29#1`: величины порции узнаются по именам `offset`/`limit`
  (`PAGINATION_EXCLUSION_NAMES` гейта границы). Величина порции под другим
  именем вне охвата, и её обязан заметить гейт границы числом вселенной.
* `10-08#2`, `10-12#3`: негодные величины — перечень
  `UNUSABLE_AD_ID_VALUES` модуля транспорта удаления без величины `1_0`,
  которую коэрция принимает как 10 (она в диапазоне, и граница её не касается).
  Сличаются код и адреса приземления (`Location`, `HX-Location`) с ответом на
  тот же запрос без поля. Разметка фрагмента не сличается: у разных строк она
  законно разная.
"""

from __future__ import annotations

import ast
from typing import NamedTuple

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.schedule import Schedule
from app.models.user import User
from app.pages.htmx import HX_LOCATION_HEADER, HX_REQUEST_HEADER
from app.pages.schedules import RETURN_TO_EDITOR
from tests.test_pages.test_confirm_delete_transport import (
    COERCIBLE_PATH_ID_VALUE,
    UNUSABLE_AD_ID_VALUES,
)
from tests.test_pages.test_identifier_bounds import (
    FIRST_USE_CHECK_HELPER,
    PAGINATION_EXCLUSION_DECLARED,
    PAGINATION_EXCLUSION_NAMES,
    _app_sources,
    _catalogue_sources,
    _route_declarations,
    bounded_alias_names,
    catalogue_parameters,
)
from tests.test_pages.test_origin_guard_on_destructive_routes import (
    ADMIN_MODULE,
    ORIGIN_GUARD,
    ORIGIN_GUARD_CALL_SITES_MEASURED,
)

# =============================================================================
# Общие разборщики
# =============================================================================


def _parents(tree: ast.AST) -> dict[int, ast.AST]:
    """Родитель каждого узла дерева — по `id`, потому что узлы не хешируются по значению."""
    found: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            found[id(child)] = node
    return found


def _enclosing_functions(node: ast.AST, parents: dict[int, ast.AST]) -> list[ast.AST]:
    """Объемлющие функции узла — от ближней к дальней."""
    chain: list[ast.AST] = []
    current = parents.get(id(node))
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            chain.append(current)
        current = parents.get(id(current))
    return chain


def _place(module: str, node: ast.AST, parents: dict[int, ast.AST]) -> str:
    """Человекочитаемое место узла: модуль, строка, ближняя функция."""
    functions = _enclosing_functions(node, parents)
    owner = functions[0].name if functions else "<уровень модуля>"
    return f"{module}:{node.lineno} ({owner})"


# =============================================================================
# 10-03#5 — cookie сессии ставит единственная функция установки
# =============================================================================

# Единственная функция установки cookie сессии (план 06-02) и обработчик входа
# под пользователем, который обязан ходить через неё. Названы ПУТЁМ и ИМЕНЕМ:
# правило, требующее лишь «одного места», зеленело бы и на установке, уехавшей
# в обработчик вместе с единственным вызовом.
SESSION_COOKIE_SETTER = ("app/pages/auth.py", "set_session_cookie")
IMPERSONATION_HANDLER = ("app/pages/admin.py", "admin_impersonate")


def session_cookie_offences(sources: dict[str, str]) -> list[str]:
    """Места, где cookie ставится мимо единственной функции установки.

    Два признака: вызов `<что-то>.set_cookie(...)` вне функции установки и
    строковая константа `set-cookie` (заголовок, записанный руками) где угодно.
    Плюс антивакуум: вызов `.set_cookie(` внутри функции установки ровно один,
    а обработчик входа под пользователем её зовёт.
    """
    offences: list[str] = []
    setter_module, setter_name = SESSION_COOKIE_SETTER
    handler_module, handler_name = IMPERSONATION_HANDLER
    inside_setter = 0
    handler_calls_setter = False
    handler_seen = False

    for module, text in sorted(sources.items()):
        tree = ast.parse(text)
        parents = _parents(tree)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "set_cookie"
            ):
                functions = _enclosing_functions(node, parents)
                if (
                    module == setter_module
                    and functions
                    and functions[0].name == setter_name
                ):
                    inside_setter += 1
                else:
                    offences.append(
                        f"{_place(module, node, parents)}: собственный `.set_cookie(` "
                        f"мимо `{setter_name}`"
                    )
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value.strip().lower() == "set-cookie"
            ):
                offences.append(
                    f"{_place(module, node, parents)}: заголовок `set-cookie` "
                    "записан руками"
                )
            if (
                module == handler_module
                and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == handler_name
            ):
                handler_seen = True
                handler_calls_setter = any(
                    isinstance(call, ast.Call)
                    and (getattr(call.func, "id", None) or getattr(call.func, "attr", None))
                    == setter_name
                    for call in ast.walk(node)
                )

    if inside_setter != 1:
        offences.append(
            f"АНТИВАКУУМ: вызовов `.set_cookie(` внутри `{setter_module}::"
            f"{setter_name}` {inside_setter}, а не один — функция установки "
            "перестала быть местом установки"
        )
    if not handler_seen:
        offences.append(
            f"АНТИВАКУУМ: обработчик `{handler_module}::{handler_name}` не найден — "
            "правило смотрит не туда"
        )
    elif not handler_calls_setter:
        offences.append(
            f"{handler_module}::{handler_name}: обработчик входа под пользователем "
            f"не зовёт `{setter_name}`"
        )
    return offences


def test_the_session_cookie_is_set_only_by_its_single_setter():
    """`10-03#5`: собственный `set_cookie` в обработчике входа под пользователем не заводится.

    Установка идёт единственной функцией (план 06-02). Правила, сличающие набор
    атрибутов установки и снятия, на собственном `set_cookie` с ТЕМ ЖЕ набором
    зелены (замер плана 15-26: 67 правил трёх модулей). Второй набор при этом
    уже живёт рядом с первым, и первая же правка одного из них их разведёт.
    Поэтому правило читает МЕСТО установки, а не её результат.
    """
    offences = session_cookie_offences(_app_sources())

    assert offences == [], (
        "COOKIE СЕССИИ СТАВИТСЯ МИМО ЕДИНСТВЕННОЙ ФУНКЦИИ УСТАНОВКИ: "
        + "; ".join(offences)
        + f". Ставить cookie сессии обязан `{SESSION_COOKIE_SETTER[1]}` "
        f"({SESSION_COOKIE_SETTER[0]}, план 06-02): второй набор атрибутов рядом с "
        "первым возврат из имперсонации не сопоставит со своей перезаписью"
    )


def test_control_an_own_set_cookie_in_the_impersonation_handler_is_named():
    """КОНТРОЛЬ: копия `admin.py` с собственным `set_cookie` того же набора названа."""
    sources = _app_sources()
    module, _ = IMPERSONATION_HANDLER
    original = sources[module]
    mutated = original.replace(
        "    set_session_cookie(response, token, settings)\n",
        '    response.set_cookie(key="access_token", value=token, path="/", '
        'httponly=True, samesite="lax", secure=settings.cookie_secure)\n',
    )
    assert mutated != original, "подмена не приземлилась — контроль доказывал бы промах"

    offences = session_cookie_offences({**sources, module: mutated})

    assert any("admin_impersonate" in item and ".set_cookie(" in item for item in offences), (
        f"собственный `set_cookie` в обработчике входа под пользователем не назван: {offences}"
    )
    assert any("не зовёт" in item for item in offences), offences

    header_written = original + '\n\ndef _raw(response):\n    response.headers.append("Set-Cookie", "x=1")\n'
    assert any(
        "записан руками" in item
        for item in session_cookie_offences({**sources, module: header_written})
    ), "заголовок `Set-Cookie`, записанный руками, не назван"

    assert session_cookie_offences(sources) == []


# =============================================================================
# 10-18#0, 10-18#1, 10-25#3, 10-32#3 — гард происхождения
# =============================================================================

# Владелец гарда: модуль и имя. Отсюда гард ввозят все потребители.
ORIGIN_GUARD_OWNER = ("app/pages/common.py", ORIGIN_GUARD)
ORIGIN_GUARD_OWNER_IMPORT = "app.pages.common"

# ⚠️ ФОРМА ОТКАЗА ГАРДА — ОДНА НА ВСЕХ ПОТРЕБИТЕЛЕЙ, И ОНА СНЯТА С ДЕРЕВА.
# Летопись: литерал снят 2026-09-25 (план 15-26) со всех четырнадцати мест
# вызова, у которых тело ветки отказа было одним и тем же. Голый 403 без тела —
# форма, выбранная владельцем: D-08 Фазы 11 (2026-09-14) и D-01 Фазы 14
# (2026-09-22). Сменить её значит принять новое решение владельца о форме
# отказа, и литерал правится вместе с этим решением, а не вместо него.
ORIGIN_GUARD_REFUSAL = "return Response(status_code=403)"

# Заголовки, по которым гард судит о происхождении. Читать их вправе только он
# сам: чтение на месте вызова и есть пересмотр границы «без обоих заголовков
# пропускается» в обход её записанного закрытия.
ORIGIN_GUARD_HEADERS = frozenset({"origin", "sec-fetch-site"})


class _GuardReference(NamedTuple):
    module: str
    node: ast.AST
    parents: dict[int, ast.AST]


def _guard_names(tree: ast.AST) -> tuple[frozenset[str], frozenset[str]]:
    """Имена, под которыми модуль ввёз гард, и имена, под которыми ввёз модуль-владелец."""
    direct: set[str] = set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == ORIGIN_GUARD_OWNER_IMPORT:
            for alias in node.names:
                if alias.name == ORIGIN_GUARD:
                    direct.add(alias.asname or alias.name)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == ORIGIN_GUARD_OWNER_IMPORT and alias.asname:
                    modules.add(alias.asname)
    return frozenset(direct), frozenset(modules)


def guard_references(sources: dict[str, str]) -> list[_GuardReference]:
    """Каждое обращение к гарду по всему `app/` — кроме его собственного объявления.

    Узнаются голое имя (с псевдонимом импорта) и обращение через модуль
    владельца (`common.is_same_origin`, `app.pages.common.is_same_origin`).
    """
    found: list[_GuardReference] = []
    for module, text in sorted(sources.items()):
        tree = ast.parse(text)
        parents = _parents(tree)
        direct, modules = _guard_names(tree)
        if module == ORIGIN_GUARD_OWNER[0]:
            direct = direct | {ORIGIN_GUARD}
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in direct:
                found.append(_GuardReference(module, node, parents))
            elif isinstance(node, ast.Attribute) and node.attr == ORIGIN_GUARD:
                base = node.value
                dotted = ast.unparse(base)
                if dotted in modules or dotted == ORIGIN_GUARD_OWNER_IMPORT or (
                    isinstance(base, ast.Name) and base.id == "common"
                ):
                    found.append(_GuardReference(module, node, parents))
    return found


def _is_post_only_route_handler(function: ast.AST) -> bool:
    routes = _route_declarations(function)
    return bool(routes) and all(method == "POST" for method, _path in routes)


def guard_placement_offences(sources: dict[str, str]) -> list[str]:
    """Обращения к гарду вне тела POST-обработчика маршрута.

    Обращение внутри обработчика GET (маршрут чтения), в промежуточном слое, в
    зависимости, в модульном коде или переданное значением — нарушение.
    Антивакуум: обработчиков, зовущих гард, ровно столько, сколько объявил гейт
    границы вселенных (`ORIGIN_GUARD_CALL_SITES_MEASURED`).
    """
    offences: list[str] = []
    guarded: set[str] = set()
    for reference in guard_references(sources):
        functions = _enclosing_functions(reference.node, reference.parents)
        handler = next(
            (function for function in functions if _route_declarations(function)),
            None,
        )
        where = _place(reference.module, reference.node, reference.parents)
        if handler is None:
            offences.append(f"{where}: гард вне обработчика маршрута")
        elif not _is_post_only_route_handler(handler):
            methods = sorted({method for method, _ in _route_declarations(handler)})
            offences.append(
                f"{where}: гард в обработчике маршрута чтения "
                f"`{handler.name}` ({', '.join(methods)})"
            )
        else:
            guarded.add(f"{reference.module}::{handler.name}")
    if len(guarded) != ORIGIN_GUARD_CALL_SITES_MEASURED:
        offences.append(
            f"АНТИВАКУУМ: POST-обработчиков, зовущих гард, найдено {len(guarded)}, "
            f"а гейт границы объявил {ORIGIN_GUARD_CALL_SITES_MEASURED}: {sorted(guarded)}"
        )
    return offences


def test_the_origin_guard_is_called_only_inside_post_route_handlers():
    """`10-18#0`: гард не вешается на маршруты ЧТЕНИЯ и не расширяется на всё приложение.

    Гейт границы вселенных считает только POST-обработчики, поэтому гард на
    обработчике GET и гард промежуточным слоем приложения он не видит (замер
    плана 15-26: оба зелены). Здесь каждое обращение к гарду обязано стоять в
    теле POST-обработчика маршрута. Расширение на следующий POST-маршрут держит
    число мест вызова соседнего гейта.
    """
    offences = guard_placement_offences(_app_sources())

    assert offences == [], (
        "ГАРД ПРОИСХОЖДЕНИЯ СТОИТ НЕ ТАМ: "
        + "; ".join(offences)
        + ". Гард, отказывающий там, где нечего защищать, отключают целиком "
        "вместе со свойством (10-18). Изменяющие маршруты, которые его несут, "
        "выбирает владелец, а маршруты чтения его не несут"
    )


def test_control_a_guard_on_a_read_route_or_in_a_middleware_is_named():
    """КОНТРОЛЬ: гард на обработчике GET и гард промежуточным слоем — названы."""
    sources = _app_sources()

    ads = sources["app/pages/ads.py"]
    anchor = (
        "    layout: str | None = Query(None),\n"
        "    db: AsyncSession = Depends(get_db),\n"
        "    settings: Settings = Depends(get_settings),\n"
        "):\n"
    )
    assert ads.count(anchor) == 1, "якорь обработчика чтения сдвинулся — контроль слеп"
    on_read = ads.replace(
        anchor,
        anchor + "    if not is_same_origin(request):\n        return Response(status_code=403)\n",
    )
    offences = guard_placement_offences({**sources, "app/pages/ads.py": on_read})
    assert any("маршрута чтения" in item and "ads_partial" in item for item in offences), offences

    main = sources["app/main.py"]
    anchor = "    app.add_middleware(RequestIdMiddleware)\n"
    assert main.count(anchor) == 1, "якорь сборки приложения сдвинулся — контроль слеп"
    everywhere = main.replace(
        anchor,
        anchor
        + "    from app.pages.common import is_same_origin as origin_ok\n"
        + '    @app.middleware("http")\n'
        + "    async def _origin_everywhere(request, call_next):\n"
        + '        if request.method == "POST" and not origin_ok(request):\n'
        + "            return None\n"
        + "        return await call_next(request)\n",
    )
    offences = guard_placement_offences({**sources, "app/main.py": everywhere})
    assert any("вне обработчика маршрута" in item and "app/main.py" in item for item in offences), offences

    assert guard_placement_offences(sources) == []


class _GuardSite(NamedTuple):
    where: str
    test_is_the_bare_verdict: bool
    refusal: str | None


def guard_sites(sources: dict[str, str]) -> list[_GuardSite]:
    """Каждый ВЫЗОВ гарда вне его объявления — с формой условия и ветки отказа.

    Форма условия: вызов стоит под `not`, и этот `not` есть условие `if` целиком.
    Ветка отказа: тело такого `if` без ветки `else`, распечатанное из дерева
    разбора (комментарии в дерево не попадают).
    """
    sites: list[_GuardSite] = []
    for reference in guard_references(sources):
        parent = reference.parents.get(id(reference.node))
        if not (isinstance(parent, ast.Call) and parent.func is reference.node):
            continue
        call = parent
        where = _place(reference.module, call, reference.parents)
        negation = reference.parents.get(id(call))
        branch = reference.parents.get(id(negation)) if negation is not None else None
        bare = (
            isinstance(negation, ast.UnaryOp)
            and isinstance(negation.op, ast.Not)
            and isinstance(branch, ast.If)
            and branch.test is negation
            and len(call.args) == 1
            and not call.keywords
        )
        refusal = None
        if bare and not branch.orelse:
            refusal = "\n".join(ast.unparse(statement) for statement in branch.body)
        sites.append(_GuardSite(where, bare, refusal))
    return sites


def guard_refusal_offences(sources: dict[str, str]) -> list[str]:
    """Места вызова, чья ветка отказа не есть объявленная форма действующих потребителей."""
    expected = ast.unparse(ast.parse(ORIGIN_GUARD_REFUSAL))
    offences = [
        f"{site.where}: ветка отказа `{site.refusal}` вместо `{expected}`"
        for site in guard_sites(sources)
        if site.test_is_the_bare_verdict and site.refusal != expected
    ]
    refusing = [site for site in guard_sites(sources) if site.refusal == expected]
    if len(refusing) != ORIGIN_GUARD_CALL_SITES_MEASURED:
        offences.append(
            f"АНТИВАКУУМ: мест вызова с объявленной формой отказа {len(refusing)}, "
            f"а гейт границы объявил {ORIGIN_GUARD_CALL_SITES_MEASURED}"
        )
    return offences


def test_every_origin_guard_site_answers_the_refusal_of_the_existing_consumers():
    """`10-18#1`: форма ответа на отказ гарда НЕ изобретается заново.

    Она берётся у действующих потребителей дословно: второй вид отказа на то же
    событие развёл бы два места одного правила. Реестр собственных выходов
    держит ВИД сборки (имя вызова и код), и отказ, получивший тело при том же
    коде, он пропускает (замер плана 15-26). Здесь ветка отказа сличается
    целиком с `ORIGIN_GUARD_REFUSAL`.
    """
    offences = guard_refusal_offences(_app_sources())

    assert offences == [], (
        "ОТКАЗ ГАРДА ПРОИСХОЖДЕНИЯ СОБРАН НЕ ТОЙ ФОРМОЙ: "
        + "; ".join(offences)
        + f". Форма одна у всех потребителей — `{ORIGIN_GUARD_REFUSAL}` (D-08 "
        "Фазы 11, D-01 Фазы 14); её смена — решение владельца, а не правка места"
    )


def test_control_a_refusal_with_a_body_is_named():
    """КОНТРОЛЬ: 403 с телом на месте вызова `accounts_delete` назван, боевое дерево — нет."""
    sources = _app_sources()
    original = sources["app/pages/accounts.py"]
    site = "    if not is_same_origin(request):\n        return Response(status_code=403)\n"
    assert original.count(site) == 1, "место вызова гарда сдвинулось — контроль слеп"
    mutated = original.replace(
        site,
        "    if not is_same_origin(request):\n"
        '        return Response(status_code=403, content="cross-site request refused")\n',
    )

    offences = guard_refusal_offences({**sources, "app/pages/accounts.py": mutated})

    assert any("accounts_delete" in item and "content=" in item for item in offences), offences
    assert guard_refusal_offences(sources) == []


def headerless_boundary_offences(sources: dict[str, str]) -> list[str]:
    """Места, где граница «без обоих заголовков пропускается» пересматривается мимо гарда.

    Два признака: условие отказа на месте вызова — не ровно `not гард(<запрос>)`
    (к вердикту гарда приписано своё условие), и чтение заголовка `Origin` или
    `Sec-Fetch-Site` (строковая константа имени) вне самого гарда. Антивакуум:
    сам гард оба заголовка читает.
    """
    offences = [
        f"{site.where}: условие отказа не есть ровно `not {ORIGIN_GUARD}(<запрос>)`"
        for site in guard_sites(sources)
        if not site.test_is_the_bare_verdict
    ]
    owner_module, owner_name = ORIGIN_GUARD_OWNER
    read_by_the_guard: set[str] = set()
    for module, text in sorted(sources.items()):
        tree = ast.parse(text)
        parents = _parents(tree)
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value.strip().lower() in ORIGIN_GUARD_HEADERS
            ):
                continue
            functions = _enclosing_functions(node, parents)
            if module == owner_module and functions and functions[0].name == owner_name:
                read_by_the_guard.add(node.value.strip().lower())
            else:
                offences.append(
                    f"{_place(module, node, parents)}: заголовок `{node.value}` "
                    "читается мимо гарда"
                )
    if read_by_the_guard != ORIGIN_GUARD_HEADERS:
        offences.append(
            f"АНТИВАКУУМ: гард читает {sorted(read_by_the_guard)}, а не "
            f"{sorted(ORIGIN_GUARD_HEADERS)} — правило смотрит не на тот предикат"
        )
    return offences


def test_no_origin_guard_site_re_examines_the_headerless_boundary():
    """`10-25#3`, `10-32#3`: граница «запрос без обоих заголовков пропускается» НЕ ПЕРЕСМАТРИВАЕТСЯ.

    Предикат держит `test_control_a_request_with_neither_header_still_passes`.
    Место вызова, приписавшее к вердикту гарда своё условие по заголовку, этот
    контроль и оба гейта полноты гарда пропускают (замер плана 15-26: 13 правил
    зелены). Здесь условие отказа на месте вызова — ровно вердикт гарда, а
    заголовки происхождения читает только гард.
    """
    offences = headerless_boundary_offences(_app_sources())

    assert offences == [], (
        "ГРАНИЦА ГАРДА ПЕРЕСМАТРИВАЕТСЯ НА МЕСТЕ: "
        + "; ".join(offences)
        + ". Запрос без обоих заголовков пропускается — это записанное закрытие "
        "прежнего круга (докстринг гарда, «НАЗВАННАЯ ГРАНИЦА ЗАЩИТЫ»), и "
        "пересматривать его вправе только новое решение, а не место вызова"
    )


def test_control_a_site_that_refuses_a_headerless_request_is_named():
    """КОНТРОЛЬ: приписанное к вердикту условие и отдельная проверка заголовка — названы."""
    sources = _app_sources()
    original = sources["app/pages/accounts.py"]
    site = "    if not is_same_origin(request):\n"
    assert original.count(site) == 1, "место вызова гарда сдвинулось — контроль слеп"

    appended = original.replace(
        site, '    if not is_same_origin(request) or "origin" not in request.headers:\n'
    )
    offences = headerless_boundary_offences({**sources, "app/pages/accounts.py": appended})
    assert any("не есть ровно" in item and "accounts_delete" in item for item in offences), offences
    assert any("читается мимо гарда" in item for item in offences), offences

    separate = original.replace(
        site,
        '    if request.headers.get("Sec-Fetch-Site") is None:\n'
        "        return Response(status_code=403)\n" + site,
    )
    offences = headerless_boundary_offences({**sources, "app/pages/accounts.py": separate})
    assert any("Sec-Fetch-Site" in item for item in offences), offences

    assert headerless_boundary_offences(sources) == []


# =============================================================================
# 10-28#1, 10-29#1 — величины порции не ограничены границей идентификатора
# =============================================================================


def _handler_nodes(text: str) -> dict[str, ast.AST]:
    return {
        node.name: node
        for node in ast.walk(ast.parse(text))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _checked_by_the_identifier_bound(handler: ast.AST, name: str) -> bool:
    """Уходит ли параметр аргументом в помощник границы идентификатора где угодно в теле."""
    for node in ast.walk(handler):
        if not isinstance(node, ast.Call):
            continue
        callee = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if callee != FIRST_USE_CHECK_HELPER:
            continue
        arguments = [*node.args, *(keyword.value for keyword in node.keywords)]
        if any(isinstance(argument, ast.Name) and argument.id == name for argument in arguments):
            return True
    return False


def pagination_offences(sources: dict[str, str]) -> list[str]:
    """Величины порции, ограниченные границей идентификатора, — и антивакуум охвата."""
    aliases = bounded_alias_names({**_app_sources(), **sources})
    parameters = [
        parameter
        for parameter in catalogue_parameters(sources, aliases)
        if parameter.name in PAGINATION_EXCLUSION_NAMES
    ]
    handlers = {module: _handler_nodes(text) for module, text in sources.items()}

    offences: list[str] = []
    for parameter in parameters:
        where = f"{parameter.module}::{parameter.handler}({parameter.name}: {parameter.annotation})"
        if parameter.carries_the_bound:
            offences.append(f"{where}: объявление несёт границу идентификатора")
        if parameter.post_alias:
            offences.append(f"{where}: объявлен POST-псевдонимом идентификатора")
        handler = handlers[parameter.module].get(parameter.handler)
        if handler is not None and _checked_by_the_identifier_bound(handler, parameter.name):
            offences.append(f"{where}: сверяется `{FIRST_USE_CHECK_HELPER}`")

    admin = [parameter for parameter in parameters if parameter.module.endswith(ADMIN_MODULE)]
    if len(parameters) != PAGINATION_EXCLUSION_DECLARED:
        offences.append(
            f"АНТИВАКУУМ: величин порции найдено {len(parameters)}, гейт границы "
            f"объявил {PAGINATION_EXCLUSION_DECLARED}"
        )
    if not admin or len(admin) == len(parameters):
        offences.append(
            "АНТИВАКУУМ: охват не накрывает обе половины предмета — админский модуль "
            f"({len(admin)}) и остальные ({len(parameters) - len(admin)})"
        )
    return offences


def test_no_pagination_value_is_limited_by_the_identifier_bound():
    """`10-28#1`, `10-29#1`: смещение и размер порции НЕ ОГРАНИЧИВАЮТСЯ границей ИДЕНТИФИКАТОРА.

    Они не есть идентификатор, и отказ по ним ничего не говорит о владении
    строкой. Гейт границы изымает их из вселенной и считает их число, а
    ограничение `le=ID_MAX`, поставленное смещению, число не двигает (замер
    плана 15-26: гейт зелен на обеих половинах — пользовательской и админской).
    Здесь у каждой величины порции нет ни границы идентификатора в объявлении,
    ни POST-псевдонима, ни сверки помощником границы в теле.
    """
    offences = pagination_offences(_catalogue_sources())

    assert offences == [], (
        "ВЕЛИЧИНА ПОСТРАНИЧНОГО ВЫВОДА ОГРАНИЧЕНА ГРАНИЦЕЙ ИДЕНТИФИКАТОРА: "
        + "; ".join(offences)
        + ". Граница у порции своя и по своему основанию (`le=100` у размера — "
        "защита выдачи), а граница колонки идентификатора к ней не относится "
        "(записанное основание `PAGINATION_EXCLUSION_NAMES`)"
    )


def test_control_the_identifier_bound_on_an_offset_is_named_in_both_halves():
    """КОНТРОЛЬ: `le=ID_MAX` у смещения — и в `ads.py`, и в админском модуле — назван."""
    sources = _catalogue_sources()

    ads = sources["app/pages/ads.py"]
    anchor = "    offset: int = Query(0, ge=0),\n    limit: int = Query(PAGE_SIZE, ge=1, le=100),\n    search:"
    assert ads.count(anchor) == 1, "якорь порции `ads.py` сдвинулся — контроль слеп"
    bounded = ads.replace(anchor, anchor.replace("Query(0, ge=0)", "Query(0, ge=0, le=ID_MAX)"))
    offences = pagination_offences({**sources, "app/pages/ads.py": bounded})
    assert any("ads.py::ads_partial(offset" in item for item in offences), offences

    admin = sources["app/pages/admin.py"]
    anchor = "    offset: int = Query(0, ge=0),\n    limit: int = Query(PAGE_SIZE, ge=1, le=100),\n"
    assert admin.count(anchor) == 1, "якорь порции админского модуля сдвинулся — контроль слеп"
    bounded = admin.replace(anchor, anchor.replace("Query(0, ge=0)", "Query(0, ge=0, le=ID_MAX)"))
    offences = pagination_offences({**sources, "app/pages/admin.py": bounded})
    assert any("admin.py::admin_user_history_partial(offset" in item for item in offences), offences

    assert pagination_offences(sources) == []


# =============================================================================
# 10-08#2, 10-12#3 — негодное поле контекста удаления расписания
# =============================================================================

FORM_CONTENT_TYPE = {"Content-Type": "application/x-www-form-urlencoded"}
OWNER_EMAIL = "testuser@test.com"

# Несуществующая строка — там, где поле контекста только и читается: пока строка
# есть, контекст берётся из неё (докстринг `_ad_id_from_form`).
MISSING_SCHEDULE_URL = "/schedules/999999/delete"

# Негодные величины поля — перечень соседнего модуля без величины, которую
# коэрция принимает (`1_0` → 10 лежит в диапазоне колонки).
UNUSABLE_CONTEXT_VALUES = tuple(
    value for value in UNUSABLE_AD_ID_VALUES if value != COERCIBLE_PATH_ID_VALUE
)

TRANSPORTS: dict[str, dict[str, str]] = {
    "без htmx": {},
    "htmx": {HX_REQUEST_HEADER: "true"},
}


def _answer(response) -> tuple[int, str | None, str | None, bytes]:
    """Что снаружи различимо в ответе: код, оба адреса приземления, тело."""
    return (
        response.status_code,
        response.headers.get("location"),
        response.headers.get(HX_LOCATION_HEADER),
        response.content,
    )


def _landing(answer: tuple) -> tuple:
    """То же без тела: у фрагментов разных строк разметка законно разная."""
    return answer[:3]


def context_divergences(observed: dict[tuple[str, str], tuple], baseline: dict[str, tuple]) -> list[str]:
    """Пары «транспорт, величина», чей ответ отличим от ответа без поля.

    Антивакуум — в самом сличителе: ответ без поля обязан быть не отказом (код
    ниже 400) на каждом транспорте, иначе равенство с ним ничего не доказывает.
    """
    divergences = [
        f"{transport} / базовый ответ без поля — отказ {answer[0]}"
        for transport, answer in sorted(baseline.items())
        if answer[0] >= 400
    ]
    for (transport, value), answer in sorted(observed.items()):
        if answer != baseline[transport]:
            divergences.append(
                f"{transport} / ad_id={value!r}: {answer[:3]} вместо {baseline[transport][:3]}"
            )
    if len(observed) != len(TRANSPORTS) * len(UNUSABLE_CONTEXT_VALUES):
        divergences.append(f"АНТИВАКУУМ: наблюдений {len(observed)}")
    return divergences


async def _post_delete(client: AsyncClient, url: str, body: str, transport: str):
    return await client.post(
        url,
        content=body,
        headers={**FORM_CONTENT_TYPE, **TRANSPORTS[transport]},
        follow_redirects=False,
    )


@pytest.mark.asyncio
async def test_an_unusable_context_field_answers_as_an_absent_one_on_both_transports(
    authed_client: AsyncClient,
):
    """`10-08#2`: граница величины НЕ вводится отказом обработчика (4xx/5xx на негодное поле).

    Форма ответа маршрута объявлена ДВУМЯ транспортами, и третья, различимая по
    величине поля, вернула бы карту занятых идентификаторов (T-10-07). Правило
    соседнего модуля (`test_an_unusable_ad_id_never_reaches_the_database`)
    ходит только транспортом htmx, и отказ на пути без htmx оно не видит (замер
    плана 15-26: 275 правил трёх модулей зелены). Здесь на ОБОИХ транспортах
    ответ на негодное поле неотличим от ответа на тот же запрос без поля.
    """
    baseline = {
        transport: _answer(
            await _post_delete(
                authed_client, MISSING_SCHEDULE_URL, f"return_to={RETURN_TO_EDITOR}", transport
            )
        )
        for transport in TRANSPORTS
    }
    observed = {
        (transport, value): _answer(
            await _post_delete(
                authed_client,
                MISSING_SCHEDULE_URL,
                f"return_to={RETURN_TO_EDITOR}&ad_id={value}",
                transport,
            )
        )
        for transport in TRANSPORTS
        for value in UNUSABLE_CONTEXT_VALUES
    }

    divergences = context_divergences(observed, baseline)

    assert divergences == [], (
        "НЕГОДНОЕ ПОЛЕ КОНТЕКСТА ПОЛУЧИЛО СВОЙ ОТВЕТ: "
        + "; ".join(divergences)
        + ". Негодное поле отбрасывается (решение плана 10-08), и ответ обязан "
        "быть тем же, что без поля, на каждом из двух транспортов"
    )


async def _owner_ad_with_an_anchor_schedule(db: AsyncSession) -> int:
    """Объявление владельца и расписание-якорь, которое остаётся после каждого удаления.

    Якорь нужен затем, чтобы объявление не пустело: у опустевшего объявления
    ответ законно другой (переход, D-04), и сличение с базой измеряло бы не то.
    """
    user = (await db.execute(select(User).where(User.email == OWNER_EMAIL))).scalar_one()
    ad = Ad(user_id=user.id, title="Объявление для поля контекста", text="Текст", images=[])
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    ad_id = ad.id
    await _seed_schedule(db, ad_id)
    return ad_id


async def _seed_schedule(db: AsyncSession, ad_id: int) -> int:
    """Расписание объявления; возвращается ЧИСЛО, а не объект: объекты сессии
    истекают после каждой фиксации, и чтение их полей в асинхронной сессии
    ушло бы в ленивую загрузку."""
    schedule = Schedule(
        ad_id=ad_id,
        account_id=None,
        group_ids=[],
        days_of_week=[0],
        times_of_day=["10:00"],
        timezone="UTC",
        is_active=False,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule.id


async def _still_there(db: AsyncSession, schedule_id: int) -> bool:
    db.expire_all()
    found = await db.execute(select(Schedule.id).where(Schedule.id == schedule_id))
    return found.scalar_one_or_none() is not None


def deletion_losses(survivors: list[str], baseline_survived: dict[str, bool]) -> list[str]:
    """Удаления, которых не случилось, — и антивакуум: базовое удаление случилось."""
    losses = [
        f"{transport} / базовое удаление без поля не случилось"
        for transport, survived in sorted(baseline_survived.items())
        if survived
    ]
    losses += [f"{item}: строка осталась" for item in survivors]
    return losses


@pytest.mark.asyncio
async def test_an_unusable_context_field_never_costs_the_deletion_itself(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """`10-12#3`: отбрасывание негодного поля КОНТЕКСТА не отменяется и не подменяется отказом.

    Испорченное поле контекста — не повод потерять само действие. Правила
    соседнего модуля шлют негодное поле на НЕСУЩЕСТВУЮЩУЮ строку, и
    обработчик, молча не удаляющий живую строку при негодном поле, они не видят
    (замер плана 15-26: 190 правил двух модулей зелены). Здесь каждая негодная
    величина едет на ЖИВУЮ строку владельца на обоих транспортах: строка
    исчезает, а код и адреса приземления те же, что у удаления без поля.
    """
    ad_id = await _owner_ad_with_an_anchor_schedule(db_session)

    baseline: dict[str, tuple] = {}
    baseline_survived: dict[str, bool] = {}
    for transport in TRANSPORTS:
        target = await _seed_schedule(db_session, ad_id)
        response = await _post_delete(
            authed_client,
            f"/schedules/{target}/delete",
            f"return_to={RETURN_TO_EDITOR}",
            transport,
        )
        baseline[transport] = _landing(_answer(response))
        baseline_survived[transport] = await _still_there(db_session, target)

    observed: dict[tuple[str, str], tuple] = {}
    survivors: list[str] = []
    for transport in TRANSPORTS:
        for value in UNUSABLE_CONTEXT_VALUES:
            target = await _seed_schedule(db_session, ad_id)
            response = await _post_delete(
                authed_client,
                f"/schedules/{target}/delete",
                f"return_to={RETURN_TO_EDITOR}&ad_id={value}",
                transport,
            )
            observed[(transport, value)] = _landing(_answer(response))
            if await _still_there(db_session, target):
                survivors.append(f"{transport} / ad_id={value!r}")

    problems = deletion_losses(survivors, baseline_survived) + context_divergences(
        observed, baseline
    )

    assert problems == [], (
        "НЕГОДНОЕ ПОЛЕ КОНТЕКСТА СТОИЛО ДЕЙСТВИЯ: "
        + "; ".join(problems)
        + ". Поле отбрасывается, строка удаляется, и ответ тот же, что без поля "
        "(решение плана 10-08, запрет плана 10-12)"
    )


def test_control_the_context_comparators_name_a_refusal_and_a_lost_deletion():
    """КОНТРОЛЬ: сличители называют отказ на одном транспорте и несостоявшееся удаление."""
    baseline = {"без htmx": (302, "/schedules", None, b""), "htmx": (204, None, "/schedules", b"")}
    observed = {
        (transport, value): baseline[transport]
        for transport in TRANSPORTS
        for value in UNUSABLE_CONTEXT_VALUES
    }
    assert context_divergences(observed, baseline) == []

    refused = dict(observed)
    refused[("без htmx", UNUSABLE_CONTEXT_VALUES[0])] = (400, None, None, b"")
    divergences = context_divergences(refused, baseline)
    assert any("без htmx" in item and "400" in item for item in divergences), divergences

    refusing_baseline = {**baseline, "htmx": (422, None, None, b"")}
    assert any("отказ 422" in item for item in context_divergences(observed, refusing_baseline))

    assert any("строка осталась" in item for item in deletion_losses(["htmx / ad_id='-1'"], {}))
    assert any(
        "базовое удаление" in item for item in deletion_losses([], {"htmx": True})
    )
    assert deletion_losses([], {"htmx": False, "без htmx": False}) == []

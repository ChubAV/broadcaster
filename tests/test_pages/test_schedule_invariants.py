"""Запреты Фазы 10 о ПРАВИЛАХ РАСПИСАНИЯ и об ОТВЕТЕ УДАЛЕНИЯ, которые суита не держала.

Предмет (план 15-29, решение владельца Г-1 «Правила сейчас», класс ответа
`require-enforcement` — план 15-12, D-04). Семь строк реестра запретов класса
`product-invariant` говорят о вычислителе момента запуска и входах расписания
(план 10-55) и об ответе удаления расписания из редактора (план 10-50). По
каждой сперва искалось действующее правило, и оно засчитывалось, только если
краснело на нарушении ИМЕННО этой формулировки, внесённом временной правкой
дерева (замеры — в `15-29-SUMMARY.md`). Здесь стоят правила на то, на чём
действующие правила оставались зелёными:

* `10-55#0` — исходник `compute_next_run_at` посимвольно равен объявленному
  снимку: `test_the_next_run_calculator_source_is_unchanged`;
* `10-55#2` — три отсечки входов на месте:
  `test_the_input_gates_of_create_and_update_stay_in_place`; зона вне перечня
  отвергается 422 на создании И ОБНОВЛЕНИИ:
  `test_an_unknown_timezone_is_refused_by_the_input_gate_on_create_and_update`;
* `10-55#9` — снятие проверок СУБД в посеве идёт с `rollback()` первой
  строкой `finally`: `test_no_seed_lifts_check_constraints_without_rolling_back_first`;
* `10-50#0` (остаток) — в шаблоне ответа удаления нет ни одной ветви:
  `test_the_delete_response_template_has_no_branch_on_the_delete_fact`;
* `10-50#3` (находка D-05) — чтения ответа удаления не отдают ни одного поля
  чужого объявления: `test_the_delete_response_reads_are_scoped_to_the_owner`
  (чтения напрямую, два пользователя),
  `test_a_delete_naming_a_foreign_ad_carries_no_field_of_it` (HTTP) и
  `test_the_delete_response_reads_carry_the_owner_link_in_the_tree` (дерево).

Строки `10-55#4` (перечень ловимых классов) и `10-50#1` (общей обёртки у узлов
ответа нет) держат действующие правила целиком — `test_schedule_rules_gate.py`,
`test_editor_delete_returns_oob_nodes` и
`test_every_oob_node_is_a_top_level_node_of_its_response` краснели на каждой
форме нарушения, — и второго экземпляра их утверждений этот файл не заводит.

У каждого правила по дереву есть контроль: разборщик принимает исходник
ПАРАМЕТРОМ, копия с нарушением строится подстановкой в настоящий исходник, и
контроль утверждает, что копия названа, а боевое дерево — нет. Контроли
точности утверждают обратное: правка, которую формулировка РАЗРЕШАЕТ (помощник
рядом с вычислителем, снятие проверок с верной очерёдностью), правило не
краснит.

ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ (D-16).
* `10-55#0`: снимок — исходник ОДНОЙ функции от `def` до конца тела. Соседние
  функции модуля, его ввозы и помощник `next_run_or_none` (`schedule_rules.py`)
  правилом не читаются: формулировка сама ставит защиту помощником рядом.
  Смысл `None` держат правила `tests/test_services/test_schedule_service.py`,
  а не этот файл.
* `10-55#2`: `_clean_times` — страничная ПОЛИТИКА отбрасывания
  (`app/pages/schedules.py`, абзац над `DEFAULT_TIME`), а не отказ 422, хотя
  формулировка называет три функции вместе. Её отсечку держат действующие
  правила `test_editor_schedules.py`; здесь — только то, что она на месте и
  стоит на обоих путях. Зона страничного пути идёт из профиля
  (`profile_timezone_or_utc`, план 15-23) и предметом строки не является.
* `10-55#9`: исключён ОДИН сайт — образец `IN-04`
  (`tests/test_application/test_send_analytics.py`,
  `test_upcoming_sends_skips_the_shape_the_schema_now_forbids`): находка
  ревизии отложена записью `10-REVIEW.md`/`deferred-items.md` Фазы 10, и
  формулировка оставляет её отложенной. Исключение НЕ утверждает, что образец
  неверен: его починка правило не краснит. Сайт снятия — вызов со строковым
  аргументом `ignore_check_constraints = ON`; снятие, собранное из частей
  строки, правилу не видно.
* `10-50#0`: правило читает ОДИН шаблон — `ads/partials/sched_delete_response.html`.
  Включаемые им `summary.html` и `sched_count_rule.html` ветвятся по полям
  объявления и счёту, и это не ветвь по факту удаления. Ветвь в обработчике,
  меняющая ИДЕНТИФИКАТОРЫ узлов, — предмет действующего правила повтора
  `test_confirm_delete_transport.py`.
* `10-50#3`: путь запроса к чужому объявлению закрыт ВЫШЕ чтений — предикатом
  `_ad_has_a_schedule` (ветка перехода). Поэтому HTTP-половина правила краснеет
  лишь тогда, когда скоуп снят и у предиката; снятие скоупа у ОДНОГО чтения
  видят вызов чтения напрямую и правило по дереву.
"""

import ast
import hashlib
import re
from datetime import timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient
from jinja2 import nodes as jinja_nodes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED
from app.models.ad import Ad
from app.models.schedule import Schedule
from app.models.user import User
from app.pages.common import format_datetime_for_user, templates
from app.pages.schedules import _ad_next_run_at, _ad_row, _ad_schedule_count
from tests.conftest import a_future_run_moment
from tests.test_pages.test_editor_schedules import (
    AD_SUMMARY_NODE_ID,
    FORM_HEADERS,
    HTMX_HEADERS,
    _form,
    _oob_region,
    _seed_account,
    _seed_group,
    _seed_schedule,
    _stranger,
    _summary_row,
)
from tests.test_planning.test_the_walkthrough_stand_is_seedable import (
    seed_program,
    walkthrough_source,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CALCULATOR_PATH = "app/services/schedule_service.py"
PAGES_PATH = "app/pages/schedules.py"
API_PATH = "app/routes/schedules.py"
DELETE_RESPONSE_TEMPLATE = "ads/partials/sched_delete_response.html"


def _tree_source(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


def _substituted(source: str, old: str, new: str) -> str:
    """Копия исходника с ОДНОЙ подстановкой; якорь обязан быть единственным."""
    assert source.count(old) == 1, (
        f"якорь контроля встречается {source.count(old)} раз(а), а не один — "
        f"контроль мерил бы не ту копию: {old[:80]!r}"
    )
    return source.replace(old, new)


# =============================================================================
# 10-55#0 — вычислитель не правится ни на символ
# =============================================================================
#
# Снимок снят с дерева `d69a8025` (план 15-29) и сличён по истории файла:
# `app/services/schedule_service.py` не менялся с `65b6e902` (2026-02-19,
# «Task 19»), а план 10-55 записал дифф модуля от своей базы ПУСТЫМ
# (`10-55-SUMMARY.md`). Форма отпечатка — первые двенадцать знаков sha256,
# та же, что у `statement_digest` прибора переписи (`scripts/prohibitions_census.py`).
# Правка ОБЯЗАНА сопровождаться решением владельца, снимающим запрет, а не
# подъёмом константы в том же коммите.

NEXT_RUN_CALCULATOR = "compute_next_run_at"
NEXT_RUN_CALCULATOR_SOURCE_DIGEST = "698f47d4e018"


def _function_source_digest(source: str, name: str) -> str | None:
    """Отпечаток исходника функции верхнего уровня (от `def` до конца тела) или None."""
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            segment = ast.get_source_segment(source, node)
            return hashlib.sha256(segment.encode("utf-8")).hexdigest()[:12]
    return None


@pytest.mark.characterisation
def test_the_next_run_calculator_source_is_unchanged():
    """`10-55#0`: исходник `compute_next_run_at` посимвольно равен снимку.

    ⚠️ СЛЕПОК, А НЕ УТВЕРЖДЕНИЕ О ПРАВИЛЬНОСТИ (решение владельца `chubav`
    2026-10-06, H4 (б) отчёта Фазы 15; запрет 15-08 #2, advisory WR-08).
    Правило держит БУКВУ `10-55#0`, но заодно замораживает вычислитель с
    известным дефектом: будущая починка его покраснит. Красный при починке
    значит «перепиши отпечаток вместе с починкой», а не «откати починку».

    Внесённый внутрь `try` превратил бы `None` из «моментов нет» в «что-то
    пошло не так», и восьмой вызывающий — планировщик `app/worker/` — перестал
    бы отличать пустое расписание от испорченного. Правила смысла `None`
    краснеют лишь на правке, меняющей их случаи; правка докстринга, окна
    просмотра или перехват на форме, которую они не подают, им не видны.
    """
    digest = _function_source_digest(_tree_source(CALCULATOR_PATH), NEXT_RUN_CALCULATOR)
    assert digest is not None, (
        f"функции `{NEXT_RUN_CALCULATOR}` в `{CALCULATOR_PATH}` нет — вычислитель "
        f"перенесён или переименован, а запрет `10-55#0` говорит «не правится ни "
        f"на символ»"
    )
    assert digest == NEXT_RUN_CALCULATOR_SOURCE_DIGEST, (
        f"ИСХОДНИК ВЫЧИСЛИТЕЛЯ `{NEXT_RUN_CALCULATOR}` ИЗМЕНЁН: отпечаток {digest}, "
        f"объявлен {NEXT_RUN_CALCULATOR_SOURCE_DIGEST}. Защита ставится ПОМОЩНИКОМ "
        f"рядом (`next_run_or_none`, `app/services/schedule_rules.py`), а не внутри "
        f"вычислителя (запрет `10-55#0`). Если это ПОЧИНКА вычислителя — правило "
        f"характеризующее: перепиши отпечаток тем же коммитом"
    )


def test_control_a_body_edit_of_the_calculator_changes_its_digest():
    source = _tree_source(CALCULATOR_PATH)
    assert _function_source_digest(source, NEXT_RUN_CALCULATOR) == NEXT_RUN_CALCULATOR_SOURCE_DIGEST
    edited = _substituted(
        source,
        "    tz = ZoneInfo(tz_name)\n",
        "    try:\n        tz = ZoneInfo(tz_name)\n    except Exception:\n        return None\n",
    )
    assert _function_source_digest(edited, NEXT_RUN_CALCULATOR) != NEXT_RUN_CALCULATOR_SOURCE_DIGEST
    one_character = _substituted(source, "range(8)", "range(9)")
    assert _function_source_digest(one_character, NEXT_RUN_CALCULATOR) != NEXT_RUN_CALCULATOR_SOURCE_DIGEST


def test_control_a_helper_next_to_the_calculator_keeps_its_digest():
    """Формулировка РАЗРЕШАЕТ помощника рядом: он правило не краснит."""
    source = _tree_source(CALCULATOR_PATH)
    with_helper = source.rstrip("\n") + (
        "\n\n\ndef _neighbour(days, times, tz):\n"
        "    try:\n        return compute_next_run_at(days, times, tz)\n"
        "    except ValueError:\n        return None\n"
    )
    assert _function_source_digest(with_helper, NEXT_RUN_CALCULATOR) == NEXT_RUN_CALCULATOR_SOURCE_DIGEST


# =============================================================================
# 10-55#2 — входы создания и обновления не ослабляются
# =============================================================================

TIMEZONE_VALIDATOR = "validate_timezone"
MALFORMED_TIMES_GATE = "_reject_malformed_times"
PAGE_TIMES_GATE = "_clean_times"
API_REQUEST_CLASSES = ("CreateScheduleRequest", "UpdateScheduleRequest")
PAGE_HANDLERS = ("schedules_create", "schedules_update")


def _top_level(tree: ast.Module) -> dict[str, ast.AST]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def _calls_name(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == name
        for call in ast.walk(node)
    )


def _timezone_validator_findings(cls: ast.ClassDef) -> list[str]:
    method = next(
        (
            node
            for node in cls.body
            if isinstance(node, ast.FunctionDef) and node.name == TIMEZONE_VALIDATOR
        ),
        None,
    )
    if method is None:
        return [f"`{cls.name}.{TIMEZONE_VALIDATOR}` снят"]
    findings = []
    decorated = any(
        isinstance(dec, ast.Call)
        and isinstance(dec.func, ast.Name)
        and dec.func.id == "field_validator"
        and any(isinstance(arg, ast.Constant) and arg.value == "timezone" for arg in dec.args)
        for dec in method.decorator_list
    )
    if not decorated:
        findings.append(f"`{cls.name}.{TIMEZONE_VALIDATOR}` не объявлен валидатором поля `timezone`")
    raises = any(isinstance(node, ast.Raise) for node in ast.walk(method))
    reads_list = any(
        isinstance(node, ast.Name) and node.id == "VALID_TIMEZONES" for node in ast.walk(method)
    )
    if not (raises and reads_list):
        findings.append(
            f"`{cls.name}.{TIMEZONE_VALIDATOR}` не отказывает по перечню `VALID_TIMEZONES`"
        )
    return findings


def _input_gate_findings(api_source: str, pages_source: str) -> list[str]:
    """Отсечки входов, которых на месте нет, — пусто, если все три стоят."""
    findings: list[str] = []
    api = _top_level(ast.parse(api_source))
    if MALFORMED_TIMES_GATE not in api:
        findings.append(f"`{MALFORMED_TIMES_GATE}` снят с `{API_PATH}`")
    for name in API_REQUEST_CLASSES:
        cls = api.get(name)
        if not isinstance(cls, ast.ClassDef):
            findings.append(f"класса запроса `{name}` в `{API_PATH}` нет")
            continue
        if not _calls_name(cls, MALFORMED_TIMES_GATE):
            findings.append(f"`{name}` не зовёт `{MALFORMED_TIMES_GATE}`")
        findings.extend(_timezone_validator_findings(cls))
    pages = _top_level(ast.parse(pages_source))
    if PAGE_TIMES_GATE not in pages:
        findings.append(f"`{PAGE_TIMES_GATE}` снят с `{PAGES_PATH}`")
    for name in PAGE_HANDLERS:
        handler = pages.get(name)
        if handler is None or not _calls_name(handler, PAGE_TIMES_GATE):
            findings.append(f"обработчик `{name}` не зовёт `{PAGE_TIMES_GATE}`")
    return findings


def test_the_input_gates_of_create_and_update_stay_in_place():
    """`10-55#2`: `_clean_times`, `_reject_malformed_times`, `validate_timezone` на месте.

    Помощник `next_run_or_none` закрывает путь СОХРАНЁННЫХ значений и не
    заменяет отсечку входов: сняв её, план открыл бы родить неисполнимую строку
    через API. Правило по дереву держит МЕСТО отсечек (оба класса запроса, оба
    страничных обработчика); что они ОТКАЗЫВАЮТ, держат поведенческие правила
    `test_schedules_api_value_domain.py`, `test_schedules.py`,
    `test_editor_schedules.py` и правило зоны ниже.
    """
    findings = _input_gate_findings(_tree_source(API_PATH), _tree_source(PAGES_PATH))
    assert findings == [], (
        "ОТСЕЧКА ВХОДОВ РАСПИСАНИЯ ОСЛАБЛЕНА (запрет `10-55#2`):\n  " + "\n  ".join(findings)
    )


def test_control_a_dropped_input_gate_is_named():
    api, pages = _tree_source(API_PATH), _tree_source(PAGES_PATH)
    assert _input_gate_findings(api, pages) == []
    update_validator = (
        "    @field_validator(\"timezone\")\n    @classmethod\n"
        "    def validate_timezone(cls, v: str | None) -> str | None:\n"
    )
    without_update_zone = _substituted(
        api, update_validator, "    @classmethod\n    def _renamed(cls, v: str | None) -> str | None:\n"
    )
    assert _input_gate_findings(without_update_zone, pages) == [
        f"`UpdateScheduleRequest.{TIMEZONE_VALIDATOR}` снят"
    ]
    head, tail = pages.split("async def schedules_update(", 1)
    pages_without_update_gate = head + "async def schedules_update(" + _substituted(
        tail,
        "_clean_times(form_data.getlist(\"times_of_day\"))",
        "list(form_data.getlist(\"times_of_day\"))",
    )
    assert _input_gate_findings(api, pages_without_update_gate) == [
        f"обработчик `schedules_update` не зовёт `{PAGE_TIMES_GATE}`"
    ]


UNKNOWN_TIMEZONE = "Not/A/Timezone"


@pytest_asyncio.fixture
async def owner(authed_client: AsyncClient, db_session: AsyncSession) -> User:
    return (
        await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


def _refused_by_the_timezone_gate(response) -> bool:
    if response.status_code != 422:
        return False
    detail = response.json().get("detail")
    return isinstance(detail, list) and any(
        isinstance(item, dict) and "timezone" in (item.get("loc") or []) for item in detail
    )


@pytest.mark.asyncio
async def test_an_unknown_timezone_is_refused_by_the_input_gate_on_create_and_update(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    owner: User,
):
    """`10-55#2`: зона вне перечня отвергается 422 ВАЛИДАТОРОМ на обоих входах API.

    ⚠️ ОБНОВЛЕНИЕ ДО ЭТОГО ПРАВИЛА НЕ ДЕРЖАЛ НИКТО (замер плана 15-29): у
    `UpdateScheduleRequest.validate_timezone` правил не было, и ослабленный
    валидатор давал ВЫКЛЮЧЕННОЙ строке ответ 200 с зоной вне перечня в базе, а
    включённой — 400 помощника вместо 422 входа. Поэтому утверждается и форма
    отказа (поле `timezone` в `loc`), и неизменность сохранённой зоны.
    """
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)
    ad = Ad(user_id=owner.id, title="Объявление зоны", text="Текст", images=[],
            status=AD_STATUS_PUBLISHED)
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)
    ad_id, account_id, group_id = ad.id, account.id, group.id

    created = await client.post(
        "/api/schedules",
        json={
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": [group_id],
            "days_of_week": [0],
            "times_of_day": ["09:00"],
            "timezone": UNKNOWN_TIMEZONE,
        },
        headers=auth_headers,
    )
    assert _refused_by_the_timezone_gate(created), (
        f"создание с зоной {UNKNOWN_TIMEZONE!r} не отвергнуто валидатором поля: "
        f"{created.status_code} {created.text[:300]}"
    )

    paused = await _seed_schedule(db_session, ad_id, account_id, [group_id], is_active=False)
    active = await _seed_schedule(db_session, ad_id, account_id, [group_id], is_active=True)
    for row_id in (paused.id, active.id):
        updated = await client.put(
            f"/api/schedules/{row_id}",
            json={"timezone": UNKNOWN_TIMEZONE},
            headers=auth_headers,
        )
        assert _refused_by_the_timezone_gate(updated), (
            f"обновление строки {row_id} зоной {UNKNOWN_TIMEZONE!r} не отвергнуто "
            f"валидатором поля: {updated.status_code} {updated.text[:300]}"
        )
        stored = (
            await db_session.execute(
                select(Schedule.timezone).where(Schedule.id == row_id)
            )
        ).scalar_one()
        assert stored == "UTC", f"зона строки {row_id} сменилась на {stored!r}"


# =============================================================================
# 10-55#9 — снятие проверок СУБД в посеве: `rollback()` первой строкой `finally`
# =============================================================================

LIFT_RE = re.compile(r"ignore_check_constraints\s*=\s*(?:ON|1|TRUE|YES)\b", re.IGNORECASE)
SCANNED_TREES = ("app", "scripts", "tests")
# Образец `IN-04` Фазы 10 — находка ревизии, оставленная отложенной самой
# формулировкой; исключение не утверждает, что он неверен (см. шапку).
IN_04_SAMPLE = (
    "tests/test_application/test_send_analytics.py",
    "test_upcoming_sends_skips_the_shape_the_schema_now_forbids",
)
# Посев плана 10-55 — строка вне области значений; и программа посева стенда
# обхода. Правило обязано ВИДЕТЬ обе, а не зеленеть на их отсутствии.
OUT_OF_DOMAIN_SEED = ("tests/test_schedules_out_of_domain_resume.py", "_seed_out_of_domain_schedule")
WALKTHROUGH_SEED_LABEL = ".planning/phases/10-rychag-components-modal-html/10-UAT.md (программа посева)"


def _is_rollback(statement: ast.stmt) -> bool:
    value = statement.value if isinstance(statement, ast.Expr) else None
    if isinstance(value, ast.Await):
        value = value.value
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and value.func.attr == "rollback"
    )


def _lift_sites(source: str) -> list[tuple[str, ast.AST | None]]:
    """Вызовы со строковым аргументом снятия проверок и объемлющая функция каждого."""
    tree = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    sites = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not any(
            isinstance(arg, ast.Constant) and isinstance(arg.value, str) and LIFT_RE.search(arg.value)
            for arg in node.args
        ):
            continue
        scope = parents.get(node)
        while scope is not None and not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
            scope = parents.get(scope)
        sites.append((scope.name if scope is not None else "<модуль>", scope))
    return sites


def _lift_order_findings(source: str, label: str) -> list[str]:
    """Сайты снятия проверок без `rollback()` первой строкой `finally`."""
    findings = []
    judged: set[int] = set()
    for name, scope in _lift_sites(source):
        # Сайтов в одной функции бывает несколько (снятие и возврат в одном
        # блоке, два посева подряд); судится ФУНКЦИЯ, и отказ о ней — один.
        if (label, name) == IN_04_SAMPLE or id(scope) in judged:
            continue
        judged.add(id(scope))
        guards = [
            node for node in ast.walk(scope if scope is not None else ast.parse(source))
            if isinstance(node, ast.Try) and node.finalbody
        ]
        if not guards:
            findings.append(f"{label}::{name}: снятие проверок без блока `finally`")
        elif not all(_is_rollback(guard.finalbody[0]) for guard in guards):
            findings.append(
                f"{label}::{name}: первая строка `finally` — не `rollback()` "
                f"(очерёдность образца `IN-04`)"
            )
    return findings


def _function_segment(source: str, name: str) -> str | None:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(source, node)
    return None


def test_no_seed_lifts_check_constraints_without_rolling_back_first():
    """`10-55#9`: снятие `PRAGMA ignore_check_constraints` — с `rollback()` первой строкой `finally`.

    Иначе отказ посева маскирует ПЕРВИЧНУЮ причину `PendingRollbackError`-ом.
    Сегодня посев плана 10-55 и программа посева стенда снятия проверок не
    содержат вовсе (замер плана 15-29), и правило держит это ОТСУТСТВИЕМ
    сайтов в них, а не порядком. Порядок оно утверждает у любого сайта
    `app/`, `scripts/`, `tests/` и программы посева, кроме образца `IN-04`.
    """
    seed_path, seed_name = OUT_OF_DOMAIN_SEED
    seed_source = _tree_source(seed_path)
    assert _function_segment(seed_source, seed_name) is not None, (
        f"посева `{seed_name}` в `{seed_path}` нет — правило не видит программы "
        f"посева плана 10-55 и зеленело бы вакуумом"
    )
    walkthrough_program = seed_program(walkthrough_source())
    assert "Schedule(" in walkthrough_program, "программа посева стенда не разобрана"

    findings = _lift_order_findings(walkthrough_program, WALKTHROUGH_SEED_LABEL)
    scanned = 0
    for top in SCANNED_TREES:
        for path in sorted((PROJECT_ROOT / top).rglob("*.py")):
            if ".venv" in path.parts:
                continue
            scanned += 1
            findings.extend(
                _lift_order_findings(
                    path.read_text(encoding="utf-8"), path.relative_to(PROJECT_ROOT).as_posix()
                )
            )
    assert scanned > 100, f"обход видел {scanned} файлов — дерево не найдено"
    assert findings == [], (
        "СНЯТИЕ ПРОВЕРОК СУБД БЕЗ `rollback()` ПЕРВОЙ СТРОКОЙ `finally` "
        "(запрет `10-55#9`):\n  " + "\n  ".join(findings)
    )


SYNTHETIC_IN_04_SHAPE = '''
async def seed(db):
    await db.execute(text("PRAGMA ignore_check_constraints = ON"))
    try:
        await db.commit()
    finally:
        await db.execute(text("PRAGMA ignore_check_constraints = OFF"))
'''

SYNTHETIC_ROLLBACK_FIRST = '''
async def seed(db):
    await db.execute(text("PRAGMA ignore_check_constraints = ON"))
    try:
        await db.commit()
    finally:
        await db.rollback()
        await db.execute(text("PRAGMA ignore_check_constraints = OFF"))
'''

SYNTHETIC_UNGUARDED = '''
def seed(connection):
    connection.execute("PRAGMA ignore_check_constraints = 1")
    connection.commit()
'''


def test_control_a_seed_lift_in_the_in_04_order_is_named():
    assert _lift_order_findings(SYNTHETIC_IN_04_SHAPE, "синтетика") == [
        "синтетика::seed: первая строка `finally` — не `rollback()` (очерёдность образца `IN-04`)"
    ]
    assert _lift_order_findings(SYNTHETIC_UNGUARDED, "синтетика") == [
        "синтетика::seed: снятие проверок без блока `finally`"
    ]
    # Исключение — по паре «файл, функция», а не по имени функции.
    renamed = SYNTHETIC_IN_04_SHAPE.replace("async def seed", f"async def {IN_04_SAMPLE[1]}")
    assert len(_lift_order_findings(renamed, "tests/другой_модуль.py")) == 1
    # Посев плана 10-55 с очерёдностью образца — назван.
    seed_path, seed_name = OUT_OF_DOMAIN_SEED
    seed_source = _tree_source(seed_path)
    assert _lift_order_findings(seed_source, seed_path) == []
    anchor = "    schedule.days_of_week = list(form.days_of_week)\n"
    doctored = _substituted(
        seed_source,
        anchor,
        "    await db.execute(text(\"PRAGMA ignore_check_constraints = ON\"))\n"
        "    try:\n        await db.commit()\n    finally:\n"
        "        await db.execute(text(\"PRAGMA ignore_check_constraints = OFF\"))\n" + anchor,
    )
    assert _lift_order_findings(doctored, seed_path) == [
        f"{seed_path}::{seed_name}: первая строка `finally` — не `rollback()` "
        f"(очерёдность образца `IN-04`)"
    ]


def test_control_a_seed_lift_with_rollback_first_is_silent():
    """Формулировка РАЗРЕШАЕТ снятие с верной очерёдностью: оно правило не краснит."""
    assert _lift_order_findings(SYNTHETIC_ROLLBACK_FIRST, "синтетика") == []
    assert len(_lift_sites(SYNTHETIC_ROLLBACK_FIRST)) == 1
    # Верная и неверная очерёдность в одной функции — ОДИН отказ о функции.
    doubled = SYNTHETIC_ROLLBACK_FIRST + SYNTHETIC_IN_04_SHAPE.replace("async def seed(db):\n", "", 1)
    assert len(_lift_sites(doubled)) == 2
    assert len(_lift_order_findings(doubled, "синтетика")) == 1


# =============================================================================
# 10-50#0 / 10-50#1 — форма ответа удаления
# =============================================================================


def _template_branches(source: str) -> list[str]:
    """Ветви шаблона: `{% if %}`/`{% elif %}` и условные выражения `… if … else …`."""
    parsed = templates.env.parse(source)
    return [
        f"{type(node).__name__} в строке {node.lineno}"
        for node in parsed.find_all((jinja_nodes.If, jinja_nodes.CondExpr))
    ]


def _delete_response_template_source() -> str:
    return templates.env.loader.get_source(templates.env, DELETE_RESPONSE_TEMPLATE)[0]


def test_the_delete_response_template_has_no_branch_on_the_delete_fact():
    """`10-50#0` (остаток): в шаблоне ответа удаления нет НИ ОДНОЙ ветви.

    Условная сборка сделала бы НАЛИЧИЕ узла (или его содержимое) признаком
    того, что удаление состоялось, и карту чужих идентификаторов можно было бы
    составить перебором по адресу. Действующее правило повтора сличает
    идентификаторы узлов двух ответов; ветвь, меняющую СОДЕРЖИМОЕ узла при тех
    же идентификаторах, и ветвь по найденности объявления оно не видит.
    Комментарии шаблона разбором отброшены: ветвь, названная в прозе, ветвью
    не является.
    """
    branches = _template_branches(_delete_response_template_source())
    assert branches == [], (
        f"В ШАБЛОНЕ ОТВЕТА УДАЛЕНИЯ `{DELETE_RESPONSE_TEMPLATE}` ПОЯВИЛАСЬ ВЕТВЬ "
        f"(запрет `10-50#0`): {branches}"
    )


def test_control_a_branch_in_the_delete_response_template_is_named():
    source = _delete_response_template_source()
    assert _template_branches(source) == []
    summary_node = '<div id="ad-summary" hx-swap-oob="true">{% include "ads/includes/summary.html" %}</div>'
    around = _substituted(source, summary_node, "{% if ad %}" + summary_node + "{% endif %}")
    assert len(_template_branches(around)) == 1
    inside = _substituted(
        source,
        summary_node,
        '<div id="ad-summary" hx-swap-oob="true">{% if deleted %}{% include "ads/includes/summary.html" %}{% endif %}</div>',
    )
    assert len(_template_branches(inside)) == 1
    inline = _substituted(
        source,
        '<div id="sched-{{ schedule_id }}" hx-swap-oob="delete"></div>',
        '<div id="sched-{{ schedule_id }}" hx-swap-oob="{{ \'delete\' if ad else \'none\' }}"></div>',
    )
    assert [branch.split()[0] for branch in _template_branches(inline)] == ["CondExpr"]


# =============================================================================
# 10-50#3 — скоуп владельца у чтений ответа удаления (находка D-05)
# =============================================================================

DELETE_HANDLER = "schedules_delete"
DELETE_FRAGMENT = "_fragment"
OWNER_PARAMETER = "user_id"
REQUESTER_EXPRESSION = "user.id"
# Чтения, которые формулировка называет: объявление и ближайший момент (план
# 10-50) — «как действующий счёт расписаний».
DELETE_RESPONSE_READS = ("_ad_schedule_count", "_ad_row", "_ad_next_run_at")


def _is_owner_compare(node: ast.AST, owner_expression: str) -> bool:
    """`Ad.user_id == <владелец>` в любом порядке сторон."""
    if not (isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq)):
        return False
    sides = sorted(ast.unparse(side) for side in (node.left, node.comparators[0]))
    return sides == sorted(["Ad.user_id", owner_expression])


def _is_ad_join(node: ast.AST) -> bool:
    """`.join(Ad, Schedule.ad_id == Ad.id)` в любом порядке сторон сравнения."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "join"):
        return False
    if len(node.args) != 2 or ast.unparse(node.args[0]) != "Ad":
        return False
    link = node.args[1]
    return isinstance(link, ast.Compare) and sorted(
        ast.unparse(side) for side in (link.left, link.comparators[0])
    ) == ["Ad.id", "Schedule.ad_id"]


def _executes(function: ast.AST) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "execute"
    ]


def _read_findings(function: ast.AST, label: str, owner_expression: str | None) -> list[str]:
    """Нарушения скоупа у каждого `execute(...)` функции; владелец — выражение сравнения."""
    findings = []
    for call in _executes(function):
        if owner_expression is None:
            findings.append(f"`{label}` читает базу, а параметра владельца `{OWNER_PARAMETER}` у неё нет")
            continue
        query = call.args[0] if call.args else None
        if query is None or not _calls_name(query, "select"):
            findings.append(f"`{label}`: выборка не набрана на месте — связь владельца не видна")
            continue
        if not any(_is_owner_compare(node, owner_expression) for node in ast.walk(query)):
            findings.append(f"`{label}`: выборка без сравнения `Ad.user_id == {owner_expression}`")
        mentions_schedule = any(isinstance(node, ast.Name) and node.id == "Schedule" for node in ast.walk(query))
        if mentions_schedule and not any(_is_ad_join(node) for node in ast.walk(query)):
            findings.append(f"`{label}`: выборка расписаний без связи `join(Ad, Schedule.ad_id == Ad.id)`")
    return findings


def _delete_response_read_findings(source: str) -> tuple[set[str], list[str]]:
    """Чтения сборки ответа удаления (транзитивно по помощникам модуля) и нарушения скоупа.

    Сборка `_fragment` видит владельца как `user.id` (замыкание обработчика),
    помощник — как свой параметр `user_id`; вызов помощника обязан передавать
    ему владельца вызывающего, а не иное выражение.
    """
    module = _top_level(ast.parse(source))
    handler = module.get(DELETE_HANDLER)
    assert handler is not None, f"обработчика `{DELETE_HANDLER}` нет"
    fragment = next(
        (
            node
            for node in ast.walk(handler)
            if isinstance(node, ast.AsyncFunctionDef) and node.name == DELETE_FRAGMENT
        ),
        None,
    )
    assert fragment is not None, f"сборки `{DELETE_FRAGMENT}` в `{DELETE_HANDLER}` нет"

    findings = _read_findings(fragment, DELETE_FRAGMENT, REQUESTER_EXPRESSION)
    reads: set[str] = set()
    seen: set[str] = set()
    pending: list[tuple[ast.AST, str | None]] = [(fragment, REQUESTER_EXPRESSION)]
    while pending:
        caller, owner_expression = pending.pop()
        for call in ast.walk(caller):
            if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)):
                continue
            callee = module.get(call.func.id)
            if not isinstance(callee, (ast.FunctionDef, ast.AsyncFunctionDef)) or callee.name in seen:
                continue
            seen.add(callee.name)
            parameters = [arg.arg for arg in callee.args.args]
            has_owner = OWNER_PARAMETER in parameters
            if has_owner:
                index = parameters.index(OWNER_PARAMETER)
                passed = call.args[index] if index < len(call.args) else next(
                    (kw.value for kw in call.keywords if kw.arg == OWNER_PARAMETER), None
                )
                shown = ast.unparse(passed) if passed is not None else "—"
                if owner_expression is None or shown != owner_expression:
                    findings.append(
                        f"`{callee.name}` зовётся с владельцем `{shown}`, а не `{owner_expression}`"
                    )
            if _executes(callee):
                reads.add(callee.name)
                findings.extend(_read_findings(callee, callee.name, OWNER_PARAMETER if has_owner else None))
            pending.append((callee, OWNER_PARAMETER if has_owner else None))
    return reads, findings


def test_the_delete_response_reads_carry_the_owner_link_in_the_tree():
    """`10-50#3` (дерево): каждое чтение сборки ответа удаления идёт со связью владельца.

    Обход транзитивный: чтение, заведённое новым помощником или прямо в сборке,
    правило видит тоже, и помощник без параметра владельца назван.
    """
    reads, findings = _delete_response_read_findings(_tree_source(PAGES_PATH))
    missing = set(DELETE_RESPONSE_READS) - reads
    assert not missing, f"чтений {sorted(missing)} в сборке ответа удаления нет — мерить нечего"
    assert findings == [], (
        "ЧТЕНИЕ ОТВЕТА УДАЛЕНИЯ БЕЗ СКОУПА ВЛАДЕЛЬЦА (запрет `10-50#3`):\n  "
        + "\n  ".join(findings)
    )


def test_control_an_unscoped_delete_response_read_is_named():
    source = _tree_source(PAGES_PATH)
    assert _delete_response_read_findings(source)[1] == []
    ad_read = _substituted(
        source,
        "select(Ad).where(Ad.id == ad_id, Ad.user_id == user_id)",
        "select(Ad).where(Ad.id == ad_id)",
    )
    assert _delete_response_read_findings(ad_read)[1] == [
        "`_ad_row`: выборка без сравнения `Ad.user_id == user_id`"
    ]
    moment_read = (
        "                select(Schedule.next_run_at)\n"
        "                .join(Ad, Schedule.ad_id == Ad.id)\n"
    )
    without_join = _substituted(source, moment_read, "                select(Schedule.next_run_at)\n")
    assert _delete_response_read_findings(without_join)[1] == [
        "`_ad_next_run_at`: выборка расписаний без связи `join(Ad, Schedule.ad_id == Ad.id)`"
    ]
    other_owner = _substituted(
        source,
        "                ad=await _ad_row(db, user.id, ad_id),\n",
        "                ad=await _ad_row(db, ad_owner_id, ad_id),\n",
    )
    assert _delete_response_read_findings(other_owner)[1] == [
        "`_ad_row` зовётся с владельцем `ad_owner_id`, а не `user.id`"
    ]
    new_helper = _substituted(
        source,
        "async def _ad_next_run_at(\n",
        "async def _ad_tags(db, ad_id):\n"
        "    return (await db.execute(select(Ad.title).where(Ad.id == ad_id))).all()\n\n\n"
        "async def _ad_next_run_at(\n",
    )
    new_helper = _substituted(
        new_helper,
        "                user=user,\n                editor={\n",
        "                user=user,\n                tags=await _ad_tags(db, ad_id),\n                editor={\n",
    )
    assert _delete_response_read_findings(new_helper)[1] == [
        "`_ad_tags` читает базу, а параметра владельца `user_id` у неё нет"
    ]


FOREIGN_IMAGES = ["foreign-1.jpg", "foreign-2.jpg"]
MOMENT_FORMAT = "%d.%m %H:%M"


async def _two_owners(db: AsyncSession, owner: User) -> dict:
    """Своё и чужое объявление с расписаниями; поля чужого РАЗЛИЧИМЫ со своими.

    Своё: черновик без вложений, три включённых расписания. Чужое: опубликовано,
    два вложения, одно расписание с моментом, отличным от своего. Различимость
    нужна, чтобы «чужого поля нет» не совпало с «поле случайно равно своему».
    """
    own_account = await _seed_account(db, owner.id)
    own_ad = Ad(user_id=owner.id, title="Своё объявление", text="Свой текст", images=[],
                status=AD_STATUS_DRAFT)
    stranger = await _stranger(db)
    foreign_account = await _seed_account(db, stranger.id)
    foreign_ad = Ad(user_id=stranger.id, title="Чужое объявление", text="Чужой текст",
                    images=list(FOREIGN_IMAGES), status=AD_STATUS_PUBLISHED)
    db.add_all([own_ad, foreign_ad])
    await db.commit()
    await db.refresh(own_ad)
    await db.refresh(foreign_ad)
    arranged = {"own_ad": own_ad.id, "foreign_ad": foreign_ad.id, "stranger": stranger.id}
    own_rows = [await _seed_schedule(db, own_ad.id, own_account.id) for _ in range(3)]
    foreign_moment = a_future_run_moment(days=4) + timedelta(hours=7, minutes=13)
    foreign_row = Schedule(ad_id=arranged["foreign_ad"], account_id=foreign_account.id,
                           group_ids=[], days_of_week=[0], times_of_day=["09:00"],
                           timezone="UTC", is_active=True, next_run_at=foreign_moment)
    db.add(foreign_row)
    await db.commit()
    await db.refresh(foreign_row)
    arranged.update(
        own_rows=[row.id for row in own_rows],
        foreign_row=foreign_row.id,
        printed_foreign_moment=format_datetime_for_user(foreign_moment, owner, MOMENT_FORMAT),
        printed_own_moment=format_datetime_for_user(own_rows[0].next_run_at, owner, MOMENT_FORMAT),
    )
    assert arranged["printed_foreign_moment"] != arranged["printed_own_moment"]
    return arranged


@pytest.mark.asyncio
async def test_the_delete_response_reads_are_scoped_to_the_owner(
    db_session: AsyncSession, owner: User
):
    """`10-50#3` (чтения): под своим владельцем чужое объявление не читается ничем.

    Выборка объявления и выборка ближайшего момента (план 10-50) идут со связью
    владельца, как действующий счёт расписаний. Чтения зовутся НАПРЯМУЮ: путь
    запроса до них с чужим объявлением не доходит — его закрывает выше
    предикат ветки (см. шапку), — и снятие скоупа у одного чтения ответом
    маршрута не наблюдается.
    """
    arranged = await _two_owners(db_session, owner)
    foreign_ad = arranged["foreign_ad"]
    assert await _ad_row(db_session, owner.id, foreign_ad) is None, (
        "чтение объявления отдало ЧУЖОЕ объявление под своим владельцем (запрет `10-50#3`)"
    )
    assert await _ad_next_run_at(db_session, owner.id, foreign_ad) is None, (
        "чтение ближайшего момента отдало момент ЧУЖОГО объявления (запрет `10-50#3`)"
    )
    assert await _ad_schedule_count(db_session, owner.id, foreign_ad) == 0, (
        "счёт расписаний посчитал ЧУЖОЕ объявление (запрет `10-50#3`)"
    )
    # Антивакуум: те же чтения под НАСТОЯЩИМ владельцем чужую строку видят.
    assert (await _ad_row(db_session, arranged["stranger"], foreign_ad)) is not None
    assert await _ad_next_run_at(db_session, arranged["stranger"], foreign_ad) is not None
    assert await _ad_schedule_count(db_session, arranged["stranger"], foreign_ad) == 1


@pytest.mark.asyncio
async def test_a_delete_naming_a_foreign_ad_carries_no_field_of_it(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """`10-50#3` (HTTP): ни одно поле чужого объявления не уходит в ответ удаления.

    Два запроса с чужим объявлением в поле контекста: удаление своего
    расписания (контекст берётся из найденной строки — сводка своя) и удаление
    чужого расписания (строки нет — контекст из поля). Правило краснеет, если
    скоуп снят и у чтений, и у предиката ветки (см. шапку).
    """
    arranged = await _two_owners(db_session, owner)
    headers = {**FORM_HEADERS, **HTMX_HEADERS}
    context = _form([("return_to", "editor"), ("ad_id", str(arranged["foreign_ad"]))])

    own = await authed_client.post(
        f"/schedules/{arranged['own_rows'][0]}/delete", content=context, headers=headers
    )
    assert own.status_code == 200, own.status_code
    summary = _oob_region(own.text, AD_SUMMARY_NODE_ID)
    assert summary is not None, f"узла сводки в ответе нет: {own.text!r}"
    assert _summary_row(summary, "Статус") == "Черновик", summary
    assert _summary_row(summary, "Вложения") == "0", summary
    assert _summary_row(summary, "Расписания") == "2", summary
    assert _summary_row(summary, "Ближайший запуск") == arranged["printed_own_moment"], summary

    foreign = await authed_client.post(
        f"/schedules/{arranged['foreign_row']}/delete", content=context, headers=headers
    )
    assert foreign.status_code < 500, foreign.status_code
    leaked = _oob_region(foreign.text, AD_SUMMARY_NODE_ID)
    if leaked is not None:
        assert _summary_row(leaked, "Статус") != "Опубликовано", (
            f"статус ЧУЖОГО объявления ушёл в ответ удаления (запрет `10-50#3`): {leaked}"
        )
        assert _summary_row(leaked, "Вложения") != str(len(FOREIGN_IMAGES)), leaked
        assert _summary_row(leaked, "Расписания") != "1", leaked
    assert arranged["printed_foreign_moment"] not in foreign.text, (
        f"момент ЧУЖОГО объявления ушёл в ответ удаления (запрет `10-50#3`): {foreign.text!r}"
    )
    still_there = (
        await db_session.execute(select(Schedule.id).where(Schedule.id == arranged["foreign_row"]))
    ).scalar_one_or_none()
    assert still_there == arranged["foreign_row"]

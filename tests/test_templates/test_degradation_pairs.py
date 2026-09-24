"""Фаза 15, GATE-10: ПАРЫ тестов деградации считаются по объявленному предикату, а не по именам.

ПРЕДИКАТ ПАРЫ — ОБЪЯВЛЕН ЗДЕСЬ, ВЫШЕ ПЕРВОГО ЧИСЛА И ВЫШЕ ПЕРВОГО ТЕСТА:

    **Пара** — два теста, объявившие ОДИН И ТОТ ЖЕ ключ предмета
    ``(экран, действие)`` и деградирующие РАЗНЫЕ клиентские механизмы: один
    ``*_degrades_without_alpine``, другой ``*_degrades_without_htmx``.

Всё число пар ниже ВЫВЕДЕНО из этого определения, а не наоборот. Условие поставлено
при закрытии `15-RESEARCH.md` §Open Questions #2 (2026-09-23): выбор предиката отдан
дискреции планировщика с одним жёстким требованием — объявить его в докстринге до
первого теста и вывести число из него.

ПОЧЕМУ НЕ ДВА ДРУГИХ ЧТЕНИЯ — с замером на каждое:

- **Паритет счёта** (``count(htmx) >= count(alpine)``) даёт «не хватает 2», но парность
  он не измеряет вовсе: две новые функции ЛЮБОГО предмета сделали бы его зелёным, а
  точных пар осталось бы ноль.
- **Совпадение основы имени** даёт «не хватает 5», но ОШИБАЕТСЯ на измеренном примере:
  ``test_editor_delete_form_degrades_without_alpine``
  (``tests/test_pages/test_ads_editor.py``, удаление ОБЪЯВЛЕНИЯ из его редактора) и
  ``test_editor_delete_degrades_without_htmx``
  (``tests/test_pages/test_editor_schedules.py``, удаление РАСПИСАНИЯ из секции
  расписаний того же редактора) сошлись бы в пару по основе ``editor_delete``, будучи
  разными действиями на разных маршрутах в разных файлах. ⚠️ Уточнение замером: ЭКРАН
  у них один (``/ads/{ad_id}/edit`` — ответ деградации htmx-теста ведёт именно туда),
  а различается ДЕЙСТВИЕ (``POST /ads/{ad_id}/delete`` против
  ``POST /schedules/{schedule_id}/delete``). Значит, и совпадение экрана без действия
  парой не является — ключ предмета есть ПАРА полей, а не одно.

ЗАМЕР ДО ФАЗЫ (2026-09-23, перезамер планирования подтвердил все восемь имён):
``*_degrades_without_alpine`` — 5, ``*_degrades_without_htmx`` — 3, пересечение
объявленных ключей предмета ПУСТО, то есть точных пар НОЛЬ. Под объявленным
предикатом не хватает 5 пар, а не 2.

ЛЕТОПИСЬ ЧИСЛА (форма `REQUIREMENTS.md` §FORM-06): не хватает 2 → не хватает 5,
Фаза 15, план 15-03. Число 2 записано решением D-14 (`15-CONTEXT.md`) — это
ВЫЧИТАНИЕ ``5 − 3``, выданное за замер: оно ВЕРНО как паритет счёта и НЕВЕРНО как
число пар, потому что предметы пяти alpine-тестов и трёх htmx-тестов не пересекаются
вовсе. ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ: он был верен для того чтения, в котором
писался, и перестал отвечать на вопрос, когда предикат объявили. Текст D-14 НЕ
ВЫЧЁРКИВАЕТСЯ — рядом пишется, чем и когда он заменён (идиома D-30/D-32).

КЛЮЧ ПРЕДМЕТА — ЗАПИСАННОЕ ПОЛЕ, А НЕ ВЫВОДИМОЕ ИЗ ИМЕНИ. Отображение
``DEGRADATION_SUBJECTS`` держит по строке на каждый тест обоих перечней:
``(screen, action, mechanism, file)``. Тот же приём, которым Ф-04 обосновала запись
класса запрета полем: вывод из ТЕКСТА зависит от порядка правил и ошибается, а
записанное поле не ошибается никогда и правится видимо. Равенство ключей снимается
ТОЧНЫМ сравнением кодовых точек — без нормализации регистра, пробелов и основы;
``editor_delete_form`` и ``editor_delete`` под этим сравнением РАЗЛИЧНЫ.

ДВА ИМЕНИ ФОРМЫ ``_degrades_without_*`` ИЗЪЯТЫ ИЗ ВСЕЛЕННОЙ ПАР ЯВНО, с причиной на
запись (``PAIR_UNIVERSE_EXEMPTIONS``). Оба найдены перезамером планирования и не
входят ни в один из двух перечней замера D-14 — без явного изъятия перечень основ
оказался бы неполон по собственному образцу имени. Молчаливое изъятие ЗАПРЕЩЕНО, и
появление третьего такого имени краснит правило.

ТРИ СУЩЕСТВУЮЩИХ htmx-ТЕСТА ОБЪЯВЛЕНЫ НЕПАРНЫМИ С ОСНОВАНИЕМ (``UNPAIRED_HTMX_TESTS``):
критерий 4 ROADMAP ОДНОСТОРОНЕН — «тесты ``*_degrades_without_alpine`` получили
ПАРНЫЕ ``*_degrades_without_htmx``», — alpine-пары для htmx-тестов он не требует, и
заводить их фаза не будет. Это НАЗВАННОЕ состояние, а не тихий зачёт их парами.

РАЗБОР — ``ast`` ПО ``tests/**/*.py``, ВСЕЛЕННАЯ — ПАРАМЕТРОМ. Каждая функция
принимает отображение «путь → исходник», поэтому контроли от вакуума выражаются
подачей синтетического файла, а межтестового состояния гейт не держит: кэшируется
только чистая функция разбора по паре (путь, текст), и число пар одинаково при любом
порядке сбора. Греп ЗАПРЕЩЁН: он посчитал бы имя и в комментарии, и в докстринге, и
в закомментированном коде (довод `tests/test_pages/test_impersonation_gate.py`,
граница «обходится объявление, а не тело»).

ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ. Зелёный цвет означает ровно две вещи: пар столько,
сколько объявлено, и ни одно объявленное имя не исчезло из дерева. Он НЕ означает,
что хоть один из парных тестов проверяет деградацию НА РАНТАЙМЕ — суита не исполняет
ни строчки JS; деградация утверждается по РАЗМЕТКЕ (``method="post"``, непустой
``action``, работоспособность формы без атрибутов механизма) и по ответу маршрута без
признака htmx, и это УЛИКА, а не наблюдение. И он НЕ означает, что ключ предмета
объявлен ВЕРНО: верность ключа есть человеческое суждение; гейт утверждает его
ПОЛНОТУ (ключ есть у каждого имени) и НЕПРОТИВОРЕЧИВОСТЬ (механизм поля совпадает с
суффиксом имени, файл поля — с файлом объявления).
"""

import ast
import functools
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = REPO_ROOT / "tests"

DEGRADATION_MARK = "_degrades_without_"
ALPINE = "alpine"
HTMX = "htmx"

FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)

BILLING_FILE = "tests/test_pages/test_billing_section.py"
RESPONSIVE_FILE = "tests/test_pages/test_responsive_markup.py"
ADS_EDITOR_FILE = "tests/test_pages/test_ads_editor.py"
ACCOUNT_GROUPS_FILE = "tests/test_pages/test_account_groups.py"
EDITOR_SCHEDULES_FILE = "tests/test_pages/test_editor_schedules.py"
ADMIN_PANEL_FILE = "tests/test_pages/test_admin_panel.py"


class DegradationSubject(NamedTuple):
    """Объявленный предмет теста деградации.

    ``screen`` — страница, на которой человек совершает действие; ``action`` —
    изменяющий маршрут, который это действие шлёт. Ключ предмета — ПАРА этих двух
    полей: ни экран, ни действие по отдельности пару не определяют (контрпример в
    докстринге модуля).
    """

    screen: str
    action: str
    mechanism: str
    file: str

    @property
    def key(self) -> tuple[str, str]:
        return (self.screen, self.action)


class Exemption(NamedTuple):
    """Имя формы ``_degrades_without_*``, изъятое из вселенной пар с причиной."""

    file: str
    reason: str


# ПЯТЬ ОСНОВ ALPINE — ЛИТЕРАЛОМ, а не выводом из дерева в момент прогона: перечень,
# выведенный из проверяемого кода, согласится с любой правкой и молча переживёт
# исчезновение имени.
ALPINE_DEGRADATION_TESTS = (
    "test_the_only_payment_left_is_a_real_form_and_degrades_without_alpine",
    "test_accounts_delete_form_degrades_without_alpine",
    "test_ads_delete_form_degrades_without_alpine",
    "test_admin_user_delete_form_degrades_without_alpine",
    "test_editor_delete_form_degrades_without_alpine",
)

# ⚠️ ЧИСЛО ВЫПИСАНО ОТДЕЛЬНОЙ КОНСТАНТОЙ НАМЕРЕННО (идиома SP-1): перечень,
# опустевший молча, оставил бы правило пар зелёным ровно тогда, когда
# alpine-тестов не стало.
#
# ЛЕТОПИСЬ: 5, Фаза 15, план 15-03, задача 1 — замер D-14 от 2026-09-23,
# подтверждён перезамером планирования и разбором `ast` этого файла.
ALPINE_DEGRADATION_TESTS_DECLARED = 5

# Критерий 4 ROADMAP односторонен: он требует пар ДЛЯ alpine-тестов, а alpine-пары
# для htmx-тестов не требует. Три теста ниже — половины пар SP-3 другого рода
# («без признака htmx → прежний 302 / с признаком → фрагмент»), и их предмет не
# совпадает ни с одним из пяти alpine-предметов.
UNPAIRED_GROUND = (
    "критерий 4 односторонен (ROADMAP, Фаза 15): он требует пар ДЛЯ alpine-тестов, а "
    "alpine-пары для htmx-тестов не требует; заводить её фаза не будет"
)
UNPAIRED_HTMX_TESTS: dict[str, str] = {
    "test_toggle_degrades_without_htmx": (
        UNPAIRED_GROUND + ". Тумблер группы на экране групп аккаунта — форма без "
        "перехвата Alpine, деградировать без Alpine ей нечему"
    ),
    "test_delete_degrades_without_htmx": (
        UNPAIRED_GROUND + ". Удаление группы с экрана групп аккаунта; ни один из пяти "
        "alpine-тестов этот экран не объявляет"
    ),
    "test_editor_delete_degrades_without_htmx": (
        UNPAIRED_GROUND + ". Удаление РАСПИСАНИЯ из редактора объявления; alpine-тест "
        "того же редактора объявляет другое действие — удаление объявления"
    ),
}

# ЛЕТОПИСЬ: 3, Фаза 15, план 15-03, задача 1 — замер D-14 от 2026-09-23.
UNPAIRED_HTMX_TESTS_DECLARED = 3

# htmx-тесты, заведённые ПАРОЙ к alpine-тесту по совпадающему ключу предмета
# (Фаза 15, план 15-03, задача 2). Каждый стоит в файле своей alpine-пары СРАЗУ
# после неё. Основа имени НЕ совпадает с основой пары намеренно: htmx-тест смотрит
# на ФОРМУ ПАНЕЛИ ПОДТВЕРЖДЕНИЯ (ту, что несёт `hx-post`), alpine-тест — на
# форму-триггер строки; предмет у них один, а пару держит записанный ключ.
PAIRED_HTMX_TESTS: tuple[str, ...] = (
    "test_the_payment_form_keeps_its_route_and_degrades_without_htmx",
    "test_accounts_delete_confirm_degrades_without_htmx",
    "test_ads_delete_confirm_degrades_without_htmx",
    "test_admin_user_delete_confirm_degrades_without_htmx",
    "test_editor_ad_delete_confirm_degrades_without_htmx",
)

HTMX_DEGRADATION_TESTS = (*UNPAIRED_HTMX_TESTS, *PAIRED_HTMX_TESTS)

# ЛЕТОПИСЬ:
#   3, Фаза 15, план 15-03, задача 1 — замер D-14 от 2026-09-23.
#   3 → 8, Фаза 15, план 15-03, задача 2 — пять пар к пяти alpine-тестам. Число
#     поставлено ПРОГОНОМ ПОКРАСНЕВШЕГО ПРАВИЛА, а не арифметикой плана: см.
#     летопись `DEGRADATION_PAIRS_DECLARED` ниже.
HTMX_DEGRADATION_TESTS_DECLARED = 8

PAIR_UNIVERSE_EXEMPTIONS: dict[str, Exemption] = {
    "test_subsection_navigation_degrades_without_js": Exemption(
        file=ADMIN_PANEL_FILE,
        reason=(
            "суффикс `_without_js` НЕ НАЗЫВАЕТ механизма: без JS отключены оба, "
            "и парного утверждения у такого теста быть не может по построению"
        ),
    ),
    "test_the_delete_degrades_without_the_rendered_rows_field": Exemption(
        file=ACCOUNT_GROUPS_FILE,
        reason=(
            "деградирует ОТСУТСТВИЕ ПОЛЯ контракта (`rendered_rows`, снято планом "
            "09-13), а не клиентский механизм — предмет другого рода"
        ),
    ),
}

# ЛЕТОПИСЬ: 2, Фаза 15, план 15-03, задача 1 — оба имени найдены перезамером
# планирования 2026-09-23 вне обоих перечней замера D-14.
PAIR_UNIVERSE_EXEMPTIONS_DECLARED = 2

DEGRADATION_SUBJECTS: dict[str, DegradationSubject] = {
    # --- alpine ---------------------------------------------------------------
    "test_the_only_payment_left_is_a_real_form_and_degrades_without_alpine": (
        DegradationSubject(
            screen="/billing",
            action="POST /billing/subscribe",
            mechanism=ALPINE,
            file=BILLING_FILE,
        )
    ),
    "test_accounts_delete_form_degrades_without_alpine": DegradationSubject(
        screen="/accounts",
        action="POST /accounts/{account_id}/delete",
        mechanism=ALPINE,
        file=RESPONSIVE_FILE,
    ),
    "test_ads_delete_form_degrades_without_alpine": DegradationSubject(
        screen="/ads",
        action="POST /ads/{ad_id}/delete",
        mechanism=ALPINE,
        file=RESPONSIVE_FILE,
    ),
    "test_admin_user_delete_form_degrades_without_alpine": DegradationSubject(
        screen="/admin/users/{user_id}",
        action="POST /admin/users/{user_id}/delete",
        mechanism=ALPINE,
        file=RESPONSIVE_FILE,
    ),
    "test_editor_delete_form_degrades_without_alpine": DegradationSubject(
        screen="/ads/{ad_id}/edit",
        action="POST /ads/{ad_id}/delete",
        mechanism=ALPINE,
        file=ADS_EDITOR_FILE,
    ),
    # --- htmx, непарные -------------------------------------------------------
    "test_toggle_degrades_without_htmx": DegradationSubject(
        screen="/accounts/{account_id}/groups",
        action="POST /accounts/{account_id}/groups/{group_id}/toggle",
        mechanism=HTMX,
        file=ACCOUNT_GROUPS_FILE,
    ),
    "test_delete_degrades_without_htmx": DegradationSubject(
        screen="/accounts/{account_id}/groups",
        action="POST /accounts/{account_id}/groups/{group_id}/delete",
        mechanism=HTMX,
        file=ACCOUNT_GROUPS_FILE,
    ),
    "test_editor_delete_degrades_without_htmx": DegradationSubject(
        screen="/ads/{ad_id}/edit",
        action="POST /schedules/{schedule_id}/delete",
        mechanism=HTMX,
        file=EDITOR_SCHEDULES_FILE,
    ),
    # --- htmx, пары к alpine (план 15-03, задача 2) ---------------------------
    # ⚠️ Ключ каждой записи ниже ПОСИМВОЛЬНО равен ключу её alpine-пары выше.
    "test_the_payment_form_keeps_its_route_and_degrades_without_htmx": (
        DegradationSubject(
            screen="/billing",
            action="POST /billing/subscribe",
            mechanism=HTMX,
            file=BILLING_FILE,
        )
    ),
    "test_accounts_delete_confirm_degrades_without_htmx": DegradationSubject(
        screen="/accounts",
        action="POST /accounts/{account_id}/delete",
        mechanism=HTMX,
        file=RESPONSIVE_FILE,
    ),
    "test_ads_delete_confirm_degrades_without_htmx": DegradationSubject(
        screen="/ads",
        action="POST /ads/{ad_id}/delete",
        mechanism=HTMX,
        file=RESPONSIVE_FILE,
    ),
    "test_admin_user_delete_confirm_degrades_without_htmx": DegradationSubject(
        screen="/admin/users/{user_id}",
        action="POST /admin/users/{user_id}/delete",
        mechanism=HTMX,
        file=RESPONSIVE_FILE,
    ),
    "test_editor_ad_delete_confirm_degrades_without_htmx": DegradationSubject(
        screen="/ads/{ad_id}/edit",
        action="POST /ads/{ad_id}/delete",
        mechanism=HTMX,
        file=ADS_EDITOR_FILE,
    ),
}

# ЧИСЛО ПАР ПО ОБЪЯВЛЕННОМУ ПРЕДИКАТУ.
#
# ЛЕТОПИСЬ:
#   0, Фаза 15, план 15-03, задача 1 — объявлено ИЗМЕРЕНИЕМ: пересечение
#     объявленных ключей пяти alpine-тестов и трёх htmx-тестов ПУСТО. Ноль здесь
#     честный: правило ниже зелено на нём потому, что пар действительно нет, а не
#     потому, что их никто не считал.
#   0 → 5, Фаза 15, план 15-03, задача 2 — пять ключей записаны ПОСИМВОЛЬНО
#     равными ключам alpine-пар ДО того, как функции появились в дереве (RED), и
#     правило покраснело, назвав всех пятерых БЕЗ ПАРЫ. Число поставлено ПРОГОНОМ
#     ПОКРАСНЕВШЕГО ПРАВИЛА, а не арифметикой плана, дословно:
#     `пар по объявленному предикату 0, объявлено 5:` — далее пять строк
#     `<alpine-имя> (<экран>, <действие>): БЕЗ ПАРЫ` — и `assert 0 == 5`.
DEGRADATION_PAIRS_DECLARED = 5

# Правило GATE-06, стоящее адресно этой фазе прохибицией плана 09-03 (элемент #0):
# «не переименовывается и не заменяется предметом».
GATE_06_RULE = "test_no_client_state_node_is_a_swap_target"
GATE_06_FILE = "tests/test_templates/test_htmx_markup_gates.py"

# Замер 2026-09-23: 174 файла тестов, имён тестовых функций — больше тысячи.
SUITE_UNIVERSE_FLOOR = 1000


class _TestDef(NamedTuple):
    """Объявление тестовой функции, найденное по дереву."""

    name: str
    file: str
    line: int
    collectable: bool
    parametrized: bool


def _suite_sources() -> dict[str, str]:
    """Исходники суиты: путь от корня репозитория → текст. СВЕЖИЙ словарь на вызов."""
    return dict(_read_suite())


@functools.cache
def _read_suite() -> tuple[tuple[str, str], ...]:
    return tuple(
        (path.relative_to(REPO_ROOT).as_posix(), path.read_text(encoding="utf-8"))
        for path in sorted(TESTS_DIR.rglob("*.py"))
    )


def _dotted(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _is_parametrize(decorator: ast.expr) -> bool:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    return _dotted(target).endswith("parametrize")


@functools.cache
def _test_defs_in(path: str, text: str) -> tuple[_TestDef, ...]:
    """Каждое объявление ``test*`` в одном файле — по ``ast``, не по строке.

    ``collectable`` — функция стоит прямо в модуле либо прямо в теле класса
    модуля, то есть pytest её соберёт; вложенная функция (продукт фабрики) —
    не соберёт.
    """
    tree = ast.parse(text, filename=path)
    collectable: list[ast.AST] = []
    for node in tree.body:
        if isinstance(node, FUNCTION_NODES):
            collectable.append(node)
        elif isinstance(node, ast.ClassDef):
            collectable.extend(m for m in node.body if isinstance(m, FUNCTION_NODES))

    found = []
    for node in ast.walk(tree):
        if isinstance(node, FUNCTION_NODES) and node.name.startswith("test"):
            found.append(
                _TestDef(
                    name=node.name,
                    file=path,
                    line=node.lineno,
                    collectable=any(node is c for c in collectable),
                    parametrized=any(_is_parametrize(d) for d in node.decorator_list),
                )
            )
    return tuple(found)


def _test_defs(sources: dict[str, str]) -> list[_TestDef]:
    return [
        definition
        for path in sorted(sources)
        for definition in _test_defs_in(path, sources[path])
    ]


def _mechanism(name: str) -> str:
    """То, что стоит после ``_degrades_without_``: имя отключённого механизма."""
    return name.split(DEGRADATION_MARK, 1)[1]


def _degradation_tests(sources: dict[str, str]) -> dict[str, set[str]]:
    """Имя каждой функции формы ``*_degrades_without_*`` → файлы её объявления."""
    tests: dict[str, set[str]] = {}
    for definition in _test_defs(sources):
        if DEGRADATION_MARK in definition.name:
            tests.setdefault(definition.name, set()).add(definition.file)
    return tests


def _names_of(sources: dict[str, str], mechanism: str) -> set[str]:
    return {n for n in _degradation_tests(sources) if _mechanism(n) == mechanism}


def _exotic_names(sources: dict[str, str]) -> set[str]:
    """Имена формы ``_degrades_without_<нечто>``, где ``<нечто>`` не механизм пары."""
    return {
        n for n in _degradation_tests(sources) if _mechanism(n) not in (ALPINE, HTMX)
    }


def _pairs(
    sources: dict[str, str], subjects: dict[str, DegradationSubject]
) -> set[tuple[str, str]]:
    """Пары ``(alpine, htmx)`` по ОБЪЯВЛЕННОМУ ПРЕДИКАТУ.

    Оба теста обязаны существовать в дереве (``ast``) и нести записанный ключ;
    ключи равны ТОЧНО, механизмы — разные. Ничего не нормализуется.
    """
    found = _degradation_tests(sources)
    declared = [n for n in found if n in subjects]
    alpine = [n for n in declared if subjects[n].mechanism == ALPINE]
    htmx = [n for n in declared if subjects[n].mechanism == HTMX]
    return {
        (a, h)
        for a in alpine
        for h in htmx
        if subjects[a].key == subjects[h].key
        and subjects[a].mechanism != subjects[h].mechanism
    }


def _pair_offence(
    sources: dict[str, str], subjects: dict[str, DegradationSubject]
) -> str:
    """Поимённая расшифровка счёта пар: у кого из alpine-тестов пара есть, у кого нет."""
    pairs = _pairs(sources, subjects)
    lines = []
    for name in ALPINE_DEGRADATION_TESTS:
        partners = sorted(h for a, h in pairs if a == name)
        subject = subjects.get(name)
        key = subject.key if subject else "<ключ не объявлен>"
        lines.append(f"  {name} {key}: {', '.join(partners) or 'БЕЗ ПАРЫ'}")
    return "\n".join(lines)


def test_the_alpine_list_has_the_declared_number():
    """ПЕРВОЕ утверждение идиомы SP-1: перечень alpine-основ — объявленной длины.

    Оно же антивакуум: опустевший перечень оставил бы правило пар зелёным ровно
    тогда, когда alpine-тестов не стало.
    """
    assert len(ALPINE_DEGRADATION_TESTS) == ALPINE_DEGRADATION_TESTS_DECLARED, (
        f"в перечне {len(ALPINE_DEGRADATION_TESTS)} имён, объявлено "
        f"{ALPINE_DEGRADATION_TESTS_DECLARED}: обнови число и допиши строку летописи"
    )
    assert ALPINE_DEGRADATION_TESTS_DECLARED > 0, (
        "перечень alpine-тестов деградации объявлен пустым — счёт пар потерял предмет"
    )
    assert len(set(ALPINE_DEGRADATION_TESTS)) == len(ALPINE_DEGRADATION_TESTS), (
        "имя в перечне alpine-тестов повторено"
    )


def test_every_declared_alpine_test_lives_in_the_suite():
    """Множество alpine-имён в дереве РАВНО объявленному перечню.

    Исчезновение любого из пяти (переименование, удаление) краснит правило и
    НАЗЫВАЕТ пропавшее; появление шестого — тоже, потому что шестой обязан войти
    в перечень решением, а не молча.
    """
    found = _names_of(_suite_sources(), ALPINE)
    declared = set(ALPINE_DEGRADATION_TESTS)

    assert found == declared, (
        f"пропали из дерева: {sorted(declared - found)}; "
        f"появились вне перечня: {sorted(found - declared)}"
    )


def test_every_declared_htmx_test_lives_in_the_suite():
    """Множество htmx-имён в дереве РАВНО объявленному перечню, и число — объявленное."""
    assert len(HTMX_DEGRADATION_TESTS) == HTMX_DEGRADATION_TESTS_DECLARED, (
        f"в перечне {len(HTMX_DEGRADATION_TESTS)} имён, объявлено "
        f"{HTMX_DEGRADATION_TESTS_DECLARED}: обнови число и допиши строку летописи"
    )

    found = _names_of(_suite_sources(), HTMX)
    declared = set(HTMX_DEGRADATION_TESTS)

    assert found == declared, (
        f"пропали из дерева: {sorted(declared - found)}; "
        f"появились вне перечня: {sorted(found - declared)}"
    )


def test_every_degradation_test_declares_its_subject():
    """Каждое имя обоих перечней несёт записанный ключ предмета, и запись непротиворечива.

    Полнота объявления, а не порог: имя без ключа краснит правило. Механизм поля
    обязан совпасть с суффиксом имени, а файл поля — с файлом, где функция
    объявлена по дереву. Лишняя запись (ключ у имени вне перечней) тоже краснит:
    иначе пару можно было бы подогнать записью, которой не соответствует ни один
    перечень.
    """
    found = _degradation_tests(_suite_sources())
    listed = set(ALPINE_DEGRADATION_TESTS) | set(HTMX_DEGRADATION_TESTS)

    missing = sorted(listed - set(DEGRADATION_SUBJECTS))
    assert not missing, f"имена без объявленного ключа предмета: {missing}"

    extra = sorted(set(DEGRADATION_SUBJECTS) - listed)
    assert not extra, f"ключ предмета объявлен у имени вне обоих перечней: {extra}"

    contradictions = []
    for name, subject in DEGRADATION_SUBJECTS.items():
        if subject.mechanism != _mechanism(name):
            contradictions.append(
                f"{name}: механизм поля {subject.mechanism!r}, суффикс имени "
                f"{_mechanism(name)!r}"
            )
        if subject.file not in found.get(name, set()):
            contradictions.append(
                f"{name}: файл поля {subject.file}, по дереву — "
                f"{sorted(found.get(name, set())) or 'нигде'}"
            )
        if not subject.screen or not subject.action:
            contradictions.append(f"{name}: пустое поле ключа {subject.key!r}")
    assert not contradictions, "\n".join(contradictions)


def test_the_pair_count_is_the_declared_one():
    """Число пар по объявленному предикату равно ``DEGRADATION_PAIRS_DECLARED``.

    Отказ называет поимённо, у какого alpine-теста пара есть, а у какого нет, и
    ключ каждого — то есть разошедшаяся пара видна без отладки.
    """
    sources = _suite_sources()
    pairs = _pairs(sources, DEGRADATION_SUBJECTS)

    assert len(pairs) == DEGRADATION_PAIRS_DECLARED, (
        f"пар по объявленному предикату {len(pairs)}, объявлено "
        f"{DEGRADATION_PAIRS_DECLARED}:\n{_pair_offence(sources, DEGRADATION_SUBJECTS)}"
    )


def test_false_pair_editor_delete_form_and_editor_delete_are_not_a_pair():
    """Измеренная ложная пара НЕ является парой — на ЭТОЙ паре имён, а не вообще.

    Предикат «совпадение основы» свёл бы их: основа alpine-имени начинается с
    основы htmx-имени. Объявленный предикат их различает, потому что ключи
    предмета различны: экран один, действие — разное. Равенство снимается точным
    сравнением кодовых точек, без нормализации.
    """
    alpine = "test_editor_delete_form_degrades_without_alpine"
    htmx = "test_editor_delete_degrades_without_htmx"
    a, h = DEGRADATION_SUBJECTS[alpine], DEGRADATION_SUBJECTS[htmx]

    alpine_stem = alpine.removeprefix("test_").split(DEGRADATION_MARK)[0]
    htmx_stem = htmx.removeprefix("test_").split(DEGRADATION_MARK)[0]
    assert (alpine_stem, htmx_stem) == ("editor_delete_form", "editor_delete")
    assert alpine_stem.startswith(htmx_stem), (
        "контрпример перестал быть контрпримером: основы больше не вложены"
    )
    assert alpine_stem != htmx_stem

    assert a.file != h.file, "ложная пара лежит в одном файле — контрпример устарел"
    assert a.screen == h.screen, (
        "экран ложной пары разошёлся: замер 2026-09-24 дал один экран для обоих"
    )
    assert a.action != h.action
    assert a.key != h.key

    assert (alpine, htmx) not in _pairs(_suite_sources(), DEGRADATION_SUBJECTS)


def test_the_exemptions_from_the_pair_universe_are_declared_with_reasons():
    """Изъятия из вселенной пар — объявленным числом, каждое с причиной и в своём файле.

    Множество имён формы ``_degrades_without_<не alpine и не htmx>`` в дереве
    РАВНО перечню изъятий: появление третьего такого имени краснит правило, как
    и молчаливая пропажа одного из двух.
    """
    assert len(PAIR_UNIVERSE_EXEMPTIONS) == PAIR_UNIVERSE_EXEMPTIONS_DECLARED, (
        f"изъятий {len(PAIR_UNIVERSE_EXEMPTIONS)}, объявлено "
        f"{PAIR_UNIVERSE_EXEMPTIONS_DECLARED}"
    )
    assert PAIR_UNIVERSE_EXEMPTIONS_DECLARED > 0

    unreasoned = [n for n, e in PAIR_UNIVERSE_EXEMPTIONS.items() if not e.reason.strip()]
    assert not unreasoned, f"изъятие без причины: {unreasoned}"

    found = _degradation_tests(_suite_sources())
    misplaced = [
        f"{name}: объявлен в {e.file}, по дереву — {sorted(found.get(name, set()))}"
        for name, e in PAIR_UNIVERSE_EXEMPTIONS.items()
        if e.file not in found.get(name, set())
    ]
    assert not misplaced, "\n".join(misplaced)

    exotic = _exotic_names(_suite_sources())
    assert exotic == set(PAIR_UNIVERSE_EXEMPTIONS), (
        f"не изъяты: {sorted(exotic - set(PAIR_UNIVERSE_EXEMPTIONS))}; "
        f"изъяты, но в дереве нет: {sorted(set(PAIR_UNIVERSE_EXEMPTIONS) - exotic)}"
    )


def test_the_unpaired_htmx_tests_are_named_with_their_ground():
    """Три htmx-теста объявлены НЕПАРНЫМИ с основанием и в счёт пар не входят."""
    assert len(UNPAIRED_HTMX_TESTS) == UNPAIRED_HTMX_TESTS_DECLARED, (
        f"непарных {len(UNPAIRED_HTMX_TESTS)}, объявлено {UNPAIRED_HTMX_TESTS_DECLARED}"
    )
    assert all(
        ground.startswith(UNPAIRED_GROUND) for ground in UNPAIRED_HTMX_TESTS.values()
    ), "основание непарности переписано мимо общего довода об односторонности"

    paired = {h for _, h in _pairs(_suite_sources(), DEGRADATION_SUBJECTS)}
    counted = sorted(set(UNPAIRED_HTMX_TESTS) & paired)
    assert not counted, (
        f"объявленные непарными вошли в счёт пар: {counted} — либо ключ подогнан, "
        f"либо тест перестал быть непарным и обязан уйти из перечня решением"
    )
    assert not set(UNPAIRED_HTMX_TESTS) & set(PAIRED_HTMX_TESTS)


def test_control_the_universe_of_test_names_is_not_empty():
    """Контроль от вакуума, положительный: разбор видит суиту, а не пустоту.

    Разборщик, не нашедший ни одного файла, дал бы ноль имён формы
    ``_degrades_without_*`` и ноль пар — и правило «пар 0, объявлено 0» было бы
    зелено на пустом месте.
    """
    sources = _suite_sources()
    names = {d.name for d in _test_defs(sources)}

    assert len(names) > SUITE_UNIVERSE_FLOOR, (
        f"разбор нашёл {len(names)} имён тестовых функций в {len(sources)} файлах — "
        f"вселенная пуста или разборщик слеп"
    )


def _synthetic(name: str) -> str:
    return f"async def {name}():\n    pass\n"


SYNTHETIC_FILE = "tests/test_pages/test_synthetic_pair_control.py"


def test_control_a_matching_subject_makes_exactly_one_more_pair():
    """Контроль от вакуума, отрицательный: предикат ДЕЙСТВУЕТ, а не согласен со всем.

    Синтетический htmx-тест, объявивший ключ предмета одного из пяти alpine-тестов,
    поднимает счёт пар ровно на одну. Запись ключа без функции в дереве пары не
    создаёт — пару держат оба конца.
    """
    alpine = ALPINE_DEGRADATION_TESTS[0]
    name = "test_synthetic_pair_control" + DEGRADATION_MARK + HTMX
    subjects = {
        **DEGRADATION_SUBJECTS,
        name: DegradationSubject(
            *DEGRADATION_SUBJECTS[alpine].key, mechanism=HTMX, file=SYNTHETIC_FILE
        ),
    }
    sources = _suite_sources()
    before = _pairs(sources, DEGRADATION_SUBJECTS)

    assert _pairs(sources, subjects) == before, (
        "ключ, записанный без функции в дереве, создал пару"
    )

    after = _pairs({**sources, SYNTHETIC_FILE: _synthetic(name)}, subjects)
    assert after == before | {(alpine, name)}, (
        f"синтетическая пара к {alpine} не засчитана либо засчитана не одна: "
        f"{sorted(after - before)}"
    )


def test_control_a_foreign_subject_makes_no_pair():
    """Контроль от вакуума, отрицательный: имя правильной формы пары не делает.

    Два синтетических htmx-теста: один с ключом, которого нет ни у одного
    alpine-теста, другой с ключом alpine-теста, отличающимся ОДНИМ регистром
    глагола. Ни один пару не создаёт — сравнение точное, без нормализации.
    """
    screen, action = DEGRADATION_SUBJECTS[ALPINE_DEGRADATION_TESTS[0]].key
    foreign = "test_synthetic_foreign_control" + DEGRADATION_MARK + HTMX
    casefold = "test_synthetic_casefold_control" + DEGRADATION_MARK + HTMX
    subjects = {
        **DEGRADATION_SUBJECTS,
        foreign: DegradationSubject(
            "/nowhere", "POST /nowhere", mechanism=HTMX, file=SYNTHETIC_FILE
        ),
        casefold: DegradationSubject(
            screen, action.lower(), mechanism=HTMX, file=SYNTHETIC_FILE
        ),
    }
    assert action.lower() != action, "контроль регистра потерял предмет"

    sources = _suite_sources()
    before = _pairs(sources, DEGRADATION_SUBJECTS)
    after = _pairs(
        {**sources, SYNTHETIC_FILE: _synthetic(foreign) + _synthetic(casefold)},
        subjects,
    )

    assert _names_of({SYNTHETIC_FILE: _synthetic(foreign)}, HTMX) == {foreign}, (
        "разборщик не увидел синтетическую функцию — контроль ничего не доказывает"
    )
    assert after == before, f"чужой ключ создал пару: {sorted(after - before)}"


def test_the_gate_06_rule_is_still_in_the_suite():
    """Прохибиция плана 09-03, элемент #0: правило GATE-06 не переименовано.

    Утверждение по дереву: имя обязано стоять ОБЪЯВЛЕНИЕМ функции в своём файле,
    а не упоминанием в прозе.
    """
    sources = _suite_sources()
    defined = {
        d.name for d in _test_defs_in(GATE_06_FILE, sources[GATE_06_FILE]) if d.collectable
    }
    assert GATE_06_RULE in defined, (
        f"{GATE_06_RULE} (GATE-06) исчез из {GATE_06_FILE}: прохибиция плана 09-03 "
        f"запрещает переименовывать его и заменять предметом"
    )

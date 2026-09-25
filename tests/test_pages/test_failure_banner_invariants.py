"""Запреты Фазы 10 о СЦЕНАРИИ, ТЕКСТАХ, ПОДЪЁМЕ и СТОПКЕ плашек отказа, которые суита не держала.

(Заголовок расширен планом 15-28; прежний — «Запреты Фазы 10 о СЦЕНАРИИ и
ТЕКСТАХ плашек отказа, которые суита не держала» — верно называл файл плана
15-27. Раздел таблицы стилей описан ниже абзацем «Подъём и стопка».)

Предмет (план 15-27, решение владельца Г-1 «Правила сейчас», класс ответа
`require-enforcement` — план 15-12, D-04). Десять строк реестра запретов класса
`product-invariant` говорят о заготовках плашек отказа в
`includes/htmx_error_banner.html`: тексты обеих плашек, тело третьего
обработчика (`htmx:afterRequest`, план 10-49), чтение ответа сценарием, форма
строки узла обрыва связи. По каждой сперва искалось действующее правило, и оно
засчитывалось, только если краснело на нарушении ИМЕННО этой формулировки,
внесённом временной правкой шаблона (замеры — в `15-27-SUMMARY.md`). Здесь стоят
правила на то, на чём действующие правила `test_shell.py` оставались зелёными:

* `10-49#2`, `10-56#6`, `10-57#7` (половина о текстах) — тексты обеих плашек
  посимвольно равны объявленным: `test_both_failure_banner_texts_are_unchanged`;
* `10-56#6`, `10-57#7` (половина о строке) — строка узла обрыва связи несёт
  вызов макроса плашки целиком:
  `test_the_network_banner_node_stays_one_line_with_its_macro_call`;
* `10-52#0`, `10-57#3` — третий обработчик не правится ни на символ и не
  переносится: `test_the_third_failure_handler_body_is_unchanged`;
* `10-49#1` (половина о чтении ответа) — сценарий читает из события отказа
  только признаки состояния:
  `test_the_banner_script_reads_only_state_signals_from_the_response`.

⚠️ ЗАМЕЩЁННЫЕ СОСТОЯНИЯ ЗДЕСЬ НЕ УТВЕРЖДАЮТСЯ. Строки `10-33#1` и `10-35#0`
(«третий обработчик не заводится, число обработчиков остаётся 2») замещены
планом 10-49 (`4e24d61b`, 2026-09-11): в дереве три обработчика. Половина
«сценарий не правится ни на строку» строки `10-56#5` замещена планом 10-57
(`1753c10c`, 2026-09-13): две строки сброса органа снятия добавлены в тела ДВУХ
ДРУГИХ обработчиков решением владельца (ветвь `A`, запись `overrides` в
`10-VERIFICATION.md`). Эти три строки переданы чекпойнту плана 15-32. Поэтому
правило третьего обработчика читает ТОЛЬКО его регистрацию и тело: тела двух
других обработчиков оно не сличает, и их правка его не краснит (контроль ниже).

У каждого правила есть контроль на синтетике: разборщики принимают путь к
шаблону ПАРАМЕТРОМ, копия с нарушением кладётся во временный каталог
(`_scratch_banner` модуля `test_shell.py`), и контроль утверждает, что копия
названа, а боевое дерево — нет. Контроли точности утверждают обратное: правка
чужого предмета (доступного имени органа снятия, тела другого обработчика)
правило НЕ краснит.

Подъём и стопка (план 15-28, то же решение Г-1). Девять строк о блоке подъёма
заготовок и о стопке в `app/static/css/app.css` проходились тем же протоколом:
временная правка таблицы, прогон, возврат (замеры — в `15-28-SUMMARY.md`).
Правила ниже стоят на том, на чём действующие правила `test_shell.py`,
`test_components.py` и `test_banner_dismiss.py` оставались зелёными:

* `10-51#2` — блок подъёма ОДИН по разбору селектора, а не по вхождению
  идентификатора: `test_exactly_one_stylesheet_block_lifts_the_failure_banners`;
* `10-51#3` — блок признака блокировки прокрутки объявляет `overflow: hidden`:
  `test_the_modal_open_mark_declares_the_scroll_lock`;
* `10-56#2`, `10-57#8` — блок подъёма (селектор и тело) посимвольно равен
  объявленному: `test_the_failure_banner_lift_block_is_unchanged`;
* `10-56#4` — базовое положение первой заготовки равно замеренному литералу:
  `test_the_first_failure_banner_keeps_its_measured_offset`;
* `10-56#3`, `10-57#8`, `10-57#9` — ни один блок, достигающий узла заготовки по
  разбору, не объявляет показывающего способа отображения и сокращения `all`:
  `test_no_block_reaching_a_failure_banner_shows_it_through_display_or_all`;
* `10-33#3` — ни один блок, достигающий узла `#notice-alert`, не поднимает его:
  `test_the_notice_region_is_not_lifted`.

⚠️ ЗАМЕЩЁННОЕ СОСТОЯНИЕ ЗДЕСЬ НЕ УТВЕРЖДАЕТСЯ. Строка `10-33#0` («БЕЗУСЛОВНЫЙ
подъём плашки не заводится») замещена планом 10-51 (`34ac7747`, 2026-09-11):
подъём безусловен, и `test_the_failure_banner_lift_is_unconditional`
утверждает обратное её формулировке. Правила условного подъёма (открытая
панель как условие) здесь нет; строка передана чекпойнту плана 15-32.

ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ (D-16). Правила читают ИСХОДНИК шаблона. Сценарий
не исполняется: что браузер показывает плашку и гасит её, держат гарниры
`test_shell.py` и ручной обход, а отрисовку и слышимость текста — только обход.
Отдельно по строкам:
* `10-49#2`, `10-56#6`, `10-57#7`: текст плашки — первый строковый аргумент
  вызова `alert(...)` в узле заготовки, и сверх вызова узел текста не несёт
  (теги вырезаются). Доступные имена органов снятия (`aria-label`) и прочие
  атрибуты узла правилом НЕ читаются: их правит план 15-19 (UI-пункт 7), и
  они не текст плашки. Второй аргумент макроса (вид плашки) — не текст, и его
  правило не сличает. Литералы `FAILURE_BANNER_TEXTS` сняты с дерева: текст
  отказа сервера стоит с плана 08-04, текст обрыва связи — с плана 09-04 (D-16
  Фазы 9), и с тех пор ни одна правка их не меняла (сличено по истории файла).
  Смысл второй фразы обрыва связи по-прежнему стерегут основы
  `NETWORK_BANNER_DIVERGENCE` правила `test_shell.py`, и прежний довод там
  («фраза целиком охраняла бы буквы») верен для правила СМЫСЛА. Буквы стерегут
  запреты Фазы 10: находка `UI-3` о формулировках отложена (`10-57#7`), и смена
  текста — новое решение владельца вместе с литералом здесь.
* `10-56#6`, `10-57#7` (строка): строка выбирается тем же предикатом, что у
  `_network_banner_line` (вхождение `id="htmx-failure-network"`), и утверждается,
  что вызов `{{ alert(...) }}` стоит в ней целиком. Узел отказа сервера этой
  половиной не касается: формулировка говорит только об узле обрыва связи.
* `10-52#0`, `10-57#3`: утверждается, что регистрация `htmx:afterRequest` в
  шаблоне одна, висит на `document.body`, стоит третьей внутри блока признака
  однократности и что её параметр и тело посимвольно равны
  `THIRD_HANDLER_PARAMS` / `THIRD_HANDLER_BODY` (сняты с дерева; тело
  байт-в-байт то же, что заведено планом 10-49 коммитом `4e24d61b`). «Не
  откатывается» держат действующие правила `test_shell.py` (запись строки
  называет их). Перенос в сценарий другого шаблона краснит это правило
  отсутствием регистрации здесь, а второй источник называет
  `test_failure_banner_has_single_source`.
* `10-49#1` (чтение): утверждается, что каждое обращение к объекту события
  (параметру любой функции сценария и глобальному `event`) есть либо чтение из
  закрытого перечня `FAILURE_BANNER_RESPONSE_READS` (код состояния, признак
  успешности), либо проверка наличия из `FAILURE_BANNER_RESPONSE_PRESENCE_TESTS`
  в положении условия. Привязка объекта события или транспорта к другому имени,
  обращение скобками, вызов метода и `arguments` названы нарушениями. Чтение
  ответа мимо объекта события (через глобальный объект рантайма) разбор не
  видит. Стоки разметки и `responseText` держит
  `test_the_failure_banner_touches_no_markup_sink`, а не этот файл.
* Подъём и стопка (план 15-28): правила читают ОБЪЯВЛЕНИЯ таблицы, а не
  отрисовку. Движка раскладки и каскада в суите нет: что браузер нарисовал
  плашку поверх панели, в окне и без пустых подложек, остаётся ручному обходу.
  «Достигает узла» значит: последняя составная часть одного из селекторов
  списка может совпасть с открывающим тегом узла, снятым из шаблона (имя тега,
  идентификатор, классы, признаки с их значениями), И называет узел хотя бы
  одним идентификатором, классом или признаком. Псевдоклассы (состояние,
  положение, `:has`, `:not`) считаются способными совпасть — это осторожная
  сторона; `:root` и псевдоэлементы — нет. Часть из одного имени тега, знака
  всеобщности или псевдокласса (`[data-row] > *`) узла не называет и не
  считается: предки в разбор не входят, и такой блок совпал бы с любым
  элементом своего места. Селектор, называющий узел, но с предком, которого у
  узла нет (`.x .failure-stack`), считается достигающим — осторожная сторона. Наследование (`display: inherit`
  от предка) и объявления на ПРЕДКАХ заготовки эти правила не читают: предков
  держит правило ловушек предков `test_shell.py`. Блок признака блокировки
  прокрутки сличается по двум замеренным селекторам и одному свойству
  `overflow`; перенос блокировки в `overflow-y` или на другой селектор правило
  назовёт, и это новое решение владельца, а не починка. Подъём области
  `#notice-alert` — это `z-index` либо положение `fixed`/`sticky` у блока,
  достигающего её узла; подъём её ВНУТРЕННЕЙ плашки (`.alert`) правило не читает.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

from tests.test_pages.test_shell import (
    FAILURE_BANNER_HANDLERS_MEASURED,
    FAILURE_BANNER_IDS,
    FAILURE_BANNER_OFFSET_PROPERTY,
    FAILURE_BANNER_OWNER,
    FAILURE_BANNER_STACK_CLASS,
    FAILURE_BANNER_STEP_PROPERTY,
    FAILURE_BANNER_SUCCESS_EVENT,
    MODAL_SCROLL_LOCK_FLAG,
    PROJECT_ROOT,
    _app_css_path,
    _banner_elevation_rules,
    _compound_simple_selectors,
    _css_declarations,
    _css_rule_block,
    _css_rules_of,
    _failure_banner_path,
    _failure_banner_script,
    _failure_banner_source,
    _network_banner_line,
    _scratch_banner,
    _scratch_stylesheet,
    _selector_compounds,
    _stack_blocks,
    _stylesheet_source,
    _without_comments,
)

# --- Тексты плашек ----------------------------------------------------------
#
# ⚠️ СНЯТЫ С ДЕРЕВА, А НЕ ВЗЯТЫ ИЗ ПАМЯТИ: первый строковый аргумент вызова
# `alert(...)` в узле каждой заготовки. Ожидание выписано здесь, а не выбрано из
# проверяемого файла (довод `VALIDATION_STATUS` модуля `test_shell.py`):
# ожидание, добытое из предмета проверки, согласилось бы с любой его правкой.
FAILURE_BANNER_TEXTS = {
    FAILURE_BANNER_IDS[0]: "Действие не выполнено. Попробуйте ещё раз через минуту.",
    FAILURE_BANNER_IDS[1]: (
        "Запрос не дошёл до сервера. Проверьте соединение и попробуйте ещё раз. "
        "Показанное на экране могло разойтись с тем, что записано на сервере: "
        "обновите страницу, чтобы увидеть настоящее состояние."
    ),
}

# --- Третий обработчик --------------------------------------------------------
#
# ⚠️ СНЯТЫ С ДЕРЕВА. Узел регистрации, параметр и тело (текст между фигурными
# скобками функции, с отступами и переводами строк) — посимвольно. Тело
# байт-в-байт то же, что заведено планом 10-49 (`4e24d61b`, 2026-09-11): замер
# `git show 4e24d61b:<шаблон>` против дерева 15-27 — различий нет. Позиция 2
# (счёт с нуля) — ТРЕТЬЯ регистрация в блоке признака однократности, откуда и
# имя обработчика во всех записях Фазы 10.
THIRD_HANDLER_HOST = "document.body"
THIRD_HANDLER_PARAMS = "event"
THIRD_HANDLER_POSITION = 2
THIRD_HANDLER_BODY = (
    "\n"
    "    if (!event.detail || !event.detail.successful) { return; }\n"
    "    var done_server = document.getElementById('htmx-failure-server');\n"
    "    if (done_server) { done_server.setAttribute('hidden', ''); }\n"
    "    var done_network = document.getElementById('htmx-failure-network');\n"
    "    if (done_network) { done_network.setAttribute('hidden', ''); }\n"
    "  "
)

# --- Чтение ответа ------------------------------------------------------------
#
# ⚠️ ЗАКРЫТЫЙ ПЕРЕЧЕНЬ СНЯТ С ДЕРЕВА. Сценарий обращается к объекту события
# ровно так: `event.detail.xhr.status` (код состояния — отличить ответ валидации
# 422 от аварии, T-08-19) и `event.detail.successful` (признак успеха обмена,
# план 10-49). Остальные обращения — проверки наличия перед чтением:
# `event.detail` и `event.detail.xhr` в положении условия. Путь пишется от
# объекта события без его имени.
FAILURE_BANNER_RESPONSE_READS = ("detail.xhr.status", "detail.successful")
FAILURE_BANNER_RESPONSE_PRESENCE_TESTS = ("detail", "detail.xhr")

# Имя глобального объекта события старых браузеров: обращение к нему из
# обработчика без параметра читает тот же объект, что и параметр.
_GLOBAL_EVENT = "event"

_IDENT = r"[A-Za-z_$][\w$]*"
_REGISTRATION_RE = re.compile(
    rf"({_IDENT}(?:\s*\.\s*{_IDENT})*)\s*\.\s*addEventListener\s*\("
)
_FUNCTION_PARAMS_RE = re.compile(rf"\bfunction\b\s*(?:{_IDENT}\s*)?\(([^)]*)\)")
_ARROW_PARAMS_RE = re.compile(rf"(?:\(([^)]*)\)|({_IDENT}))\s*=>")
_ONCE_GUARD_RE = re.compile(
    rf"\bif\s*\(\s*!\s*{_IDENT}(?:\s*\.\s*{_IDENT})*\s*\.\s*dataset\s*\.\s*{_IDENT}\s*\)\s*\{{"
)
_ALERT_CALL_RE = re.compile(r"\{\{-?\s*alert\s*\(")
_ALERT_EXPRESSION_RE = re.compile(r"\{\{-?\s*alert\s*\(.*?\)\s*-?\}\}", re.DOTALL)
_FIRST_STRING_ARG_RE = re.compile(
    r"\{\{-?\s*alert\s*\(\s*(['\"])(.*?)(?<!\\)\1", re.DOTALL
)
_TAG_RE = re.compile(r"<[^>]*>")


def _masked(code: str) -> str:
    """Сценарий той же длины, где содержимое строк и комментариев замаскировано.

    Кавычки остаются на месте, содержимое строки заменено буквой `x`,
    комментарий — пробелами. Позиции совпадают с исходником, поэтому скобки
    внутри строк не сбивают счёт, а имя события читается из исходника по тем же
    позициям.
    """
    out = list(code)
    i, n = 0, len(code)
    while i < n:
        ch = code[i]
        if ch in "'\"`":
            j = i + 1
            while j < n and code[j] != ch:
                if code[j] == "\\":
                    out[j] = "x"
                    j += 1
                if j < n:
                    out[j] = "x" if code[j] != "\n" else "\n"
                j += 1
            i = j + 1
            continue
        if code.startswith("//", i):
            j = code.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                out[k] = " "
            i = j
            continue
        if code.startswith("/*", i):
            j = code.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                out[k] = out[k] if code[k] == "\n" else " "
            i = j
            continue
        i += 1
    return "".join(out)


def _matching_brace(masked: str, opening: int) -> int:
    """Позиция закрывающей скобки к `{` в позиции `opening` (по маске)."""
    depth = 0
    for k in range(opening, len(masked)):
        if masked[k] == "{":
            depth += 1
        elif masked[k] == "}":
            depth -= 1
            if depth == 0:
                return k
    raise AssertionError(
        f"{FAILURE_BANNER_OWNER}: у фигурной скобки в позиции {opening} нет пары — "
        "разборщик сценария разошёлся с исходником"
    )


class _Registration(NamedTuple):
    host: str
    event: str
    params: str
    body: str
    start: int


def _registrations(script: str) -> list[_Registration]:
    """Регистрации обработчиков сценария в порядке исходника.

    Разбирается форма `<узел>.addEventListener('<событие>', function (<п>) {…})`.
    Регистрация иной формы (ссылкой на функцию, стрелкой) попадает в перечень с
    пустым телом и параметром `<?>`: правило третьего обработчика её назовёт, а
    не пропустит.
    """
    masked = _masked(script)
    found: list[_Registration] = []
    for match in _REGISTRATION_RE.finditer(masked):
        host = re.sub(r"\s+", "", match.group(1))
        rest = match.end()
        quote = re.match(r"\s*(['\"])", masked[rest:])
        event = ""
        if quote:
            q_start = rest + quote.end() - 1
            q_end = masked.index(quote.group(1), q_start + 1)
            event = script[q_start + 1 : q_end]
            rest = q_end + 1
        head = re.match(r"\s*,\s*function\s*\(([^)]*)\)\s*\{", masked[rest:])
        if not head:
            found.append(_Registration(host, event, "<?>", "", match.start()))
            continue
        opening = rest + head.end() - 1
        closing = _matching_brace(masked, opening)
        found.append(
            _Registration(
                host,
                event,
                script[rest + head.start(1) : rest + head.end(1)],
                script[opening + 1 : closing],
                match.start(),
            )
        )
    return found


def _once_guard_span(script: str) -> tuple[int, int] | None:
    """Границы блока признака однократности `if (!<узел>.dataset.<имя>) {…}`."""
    masked = _masked(script)
    guard = _ONCE_GUARD_RE.search(masked)
    if not guard:
        return None
    opening = guard.end() - 1
    return opening, _matching_brace(masked, opening)


def _banner_node(code: str, banner_id: str) -> str | None:
    """Содержимое узла заготовки: от открывающего тега до первого `</div>`."""
    opening = re.search(
        rf"<div\b[^>]*\bid=(['\"]){re.escape(banner_id)}\1[^>]*>", code
    )
    if not opening:
        return None
    closing = code.find("</div>", opening.end())
    return code[opening.end() : closing if closing >= 0 else len(code)]


def _banner_text_findings(path: Path) -> tuple[str, ...]:
    """Расхождения текстов плашек с `FAILURE_BANNER_TEXTS`. Пусто — тексты те же.

    Читается ТОЛЬКО аргумент макроса и текст вне тегов: атрибуты узла, в том
    числе доступное имя органа снятия, сюда не попадают по построению.
    """
    code = _without_comments(_failure_banner_source(path))
    findings: list[str] = []
    for banner_id, expected in FAILURE_BANNER_TEXTS.items():
        node = _banner_node(code, banner_id)
        if node is None:
            findings.append(f"#{banner_id}: узла заготовки в шаблоне нет")
            continue
        calls = len(_ALERT_CALL_RE.findall(node))
        if calls != 1:
            findings.append(
                f"#{banner_id}: вызовов макроса `alert(...)` в узле {calls}, а не один"
            )
            continue
        argument = _FIRST_STRING_ARG_RE.search(node)
        got = argument.group(2) if argument else None
        if got != expected:
            findings.append(
                f"#{banner_id}: ТЕКСТ ПЛАШКИ ИЗМЕНЁН\n"
                f"      получено:  {got!r}\n"
                f"      ожидалось: {expected!r}"
            )
        outside = _TAG_RE.sub("", _ALERT_EXPRESSION_RE.sub("", node)).strip()
        if outside:
            findings.append(
                f"#{banner_id}: в узле есть текст ВНЕ вызова макроса: {outside!r}"
            )
    return tuple(findings)


def _network_node_line_findings(path: Path) -> tuple[str, ...]:
    """Строка узла обрыва связи несёт вызов макроса целиком. Пусто — несёт."""
    marker = f'id="{FAILURE_BANNER_IDS[1]}"'
    carriers = [
        line for line in _failure_banner_source(path).splitlines() if marker in line
    ]
    if len(carriers) != 1:
        return (f"строк с `{marker}` в шаблоне {len(carriers)}, а не одна",)
    line = _network_banner_line(path)
    if not _ALERT_EXPRESSION_RE.search(line):
        return (
            f"СТРОКА УЗЛА #{FAILURE_BANNER_IDS[1]} НЕ НЕСЁТ ВЫЗОВА МАКРОСА ЦЕЛИКОМ\n"
            f"      получено:  {line!r}\n"
            "      ожидалось: `{{ alert(...) }}` в этой же строке — "
            "`_network_banner_line` читает ровно одну строку",
        )
    return ()


def _third_handler_findings(path: Path) -> tuple[str, ...]:
    """Расхождения третьего обработчика с объявленным. Пусто — он тот же и там же.

    Тела ДРУГИХ регистраций не сличаются: читается только их число и порядок в
    блоке признака однократности, чтобы найти позицию третьей.
    """
    script = _failure_banner_script(path)
    registrations = _registrations(script)
    third = [r for r in registrations if r.event == FAILURE_BANNER_SUCCESS_EVENT]
    if len(third) != 1:
        return (
            f"регистраций `{FAILURE_BANNER_SUCCESS_EVENT}` в сценарии {len(third)}, "
            "а не одна — третий обработчик откатан, перенесён из шаблона или удвоен",
        )
    handler = third[0]
    findings: list[str] = []
    guard = _once_guard_span(script)
    guarded = (
        [r for r in registrations if guard[0] < r.start < guard[1]] if guard else []
    )
    if handler not in guarded:
        findings.append(
            "третий обработчик ПЕРЕНЕСЁН за пределы блока признака однократности"
        )
    elif guarded.index(handler) != THIRD_HANDLER_POSITION:
        findings.append(
            "третий обработчик ПЕРЕНЕСЁН в порядке регистрации\n"
            f"      получено:  позиция {guarded.index(handler)} в блоке\n"
            f"      ожидалось: позиция {THIRD_HANDLER_POSITION}"
        )
    if handler.host != THIRD_HANDLER_HOST:
        findings.append(
            f"третий обработчик ПЕРЕНЕСЁН на узел `{handler.host}` "
            f"(ожидался `{THIRD_HANDLER_HOST}`)"
        )
    if handler.params != THIRD_HANDLER_PARAMS:
        findings.append(
            f"параметр третьего обработчика {handler.params!r}, "
            f"ожидался {THIRD_HANDLER_PARAMS!r}"
        )
    if handler.body != THIRD_HANDLER_BODY:
        at = next(
            (
                k
                for k, (a, b) in enumerate(zip(handler.body, THIRD_HANDLER_BODY))
                if a != b
            ),
            min(len(handler.body), len(THIRD_HANDLER_BODY)),
        )
        findings.append(
            f"ТЕЛО ТРЕТЬЕГО ОБРАБОТЧИКА ИЗМЕНЕНО с символа {at}\n"
            f"      получено:  {handler.body[max(0, at - 20) : at + 40]!r}\n"
            f"      ожидалось: {THIRD_HANDLER_BODY[max(0, at - 20) : at + 40]!r}"
        )
    return tuple(findings)


def _declared_parameters(masked: str) -> tuple[list[str], list[tuple[int, int]]]:
    """Параметры всех функций сценария и позиции их объявлений."""
    params: list[str] = []
    spans: list[tuple[int, int]] = []
    matches = [(m, 1) for m in _FUNCTION_PARAMS_RE.finditer(masked)] + [
        (m, 1 if m.group(1) is not None else 2) for m in _ARROW_PARAMS_RE.finditer(masked)
    ]
    for match, group in matches:
        spans.append(match.span(group))
        params.extend(p.strip() for p in match.group(group).split(",") if p.strip())
    return params, spans


def _response_read_findings(path: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(нарушения, найденные чтения) обращений сценария к объекту события."""
    script = _failure_banner_script(path)
    masked = _masked(script)
    findings: list[str] = []
    reads: list[str] = []
    params, decl_spans = _declared_parameters(masked)
    for param in params:
        if not re.fullmatch(_IDENT, param):
            findings.append(
                f"параметр функции {param!r} не есть простое имя — разбор объекта "
                "события в объявлении прячет обращения к ответу"
            )
    if re.search(r"(?<![\w$.])arguments(?![\w$])", masked):
        findings.append("сценарий обращается к `arguments` — объект события мимо имени")
    roots = sorted({p for p in params if re.fullmatch(_IDENT, p)} | {_GLOBAL_EVENT})
    for root in roots:
        for match in re.finditer(rf"(?<![\w$.]){re.escape(root)}(?![\w$])", masked):
            if any(a <= match.start() < b for a, b in decl_spans):
                continue
            path_parts: list[str] = []
            cursor = match.end()
            while True:
                step = re.match(rf"\s*\.\s*({_IDENT})", masked[cursor:])
                if not step:
                    break
                path_parts.append(step.group(1))
                cursor += step.end()
            chain = ".".join(path_parts)
            shown = f"{root}.{chain}" if chain else root
            line = script.count("\n", 0, match.start()) + 1
            after = masked[cursor:].lstrip()
            if after.startswith(("[", "(")):
                findings.append(
                    f"строка {line} сценария: `{shown}{after[0]}…` — обращение "
                    "скобками или вызов на объекте события"
                )
                continue
            if chain in FAILURE_BANNER_RESPONSE_READS:
                reads.append(chain)
                continue
            before = masked[: match.start()].rstrip()
            in_test = before.endswith(("(", "!", "&&", "||")) and after.startswith(
                ("&&", "||", ")")
            )
            if chain in FAILURE_BANNER_RESPONSE_PRESENCE_TESTS and in_test:
                continue
            findings.append(
                f"строка {line} сценария: `{shown}` — обращение к объекту события "
                "вне закрытого перечня признаков состояния "
                f"{FAILURE_BANNER_RESPONSE_READS} (проверки наличия "
                f"{FAILURE_BANNER_RESPONSE_PRESENCE_TESTS} — только в условии)"
            )
    return tuple(findings), tuple(reads)


def _scratch(tmp_path: Path, name: str, text: str) -> Path:
    """Копия шаблона в собственном подкаталоге: несколько копий в одном контроле."""
    where = tmp_path / name
    where.mkdir()
    return _scratch_banner(where, text)


def _replace_once(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, (
        f"якорь подмены {old[:60]!r} встречается {text.count(old)} раз(а), а не один "
        "— подмена была бы молчаливой"
    )
    return text.replace(old, new)


# --- Правила ------------------------------------------------------------------


def test_both_failure_banner_texts_are_unchanged():
    """Тексты обеих плашек посимвольно равны объявленным (`10-49#2`, `10-56#6`, `10-57#7`).

    Правило читает аргумент макроса `alert(...)` и текст узла вне тегов. Правка
    доступного имени органа снятия его не краснит (контроль ниже): имена правит
    план 15-19, а тексты плашек — только новое решение владельца (находка
    `UI-3` отложена).
    """
    findings = _banner_text_findings(_failure_banner_path())

    assert findings == (), f"{FAILURE_BANNER_OWNER}:\n" + "\n".join(
        f"  — {line}" for line in findings
    )


def test_the_network_banner_node_stays_one_line_with_its_macro_call():
    """Строка узла обрыва связи несёт вызов макроса целиком (`10-56#6`, `10-57#7`).

    `test_the_network_banner_names_the_screen_server_divergence` читает ровно
    одну строку и краснеет, если текст ушёл на соседнюю. Если же текст остался,
    а вызов макроса закрылся на следующей строке, основы на месте и то правило
    зелено. Это правило краснеет и на такой форме.
    """
    findings = _network_node_line_findings(_failure_banner_path())

    assert findings == (), f"{FAILURE_BANNER_OWNER}:\n" + "\n".join(
        f"  — {line}" for line in findings
    )


def test_the_third_failure_handler_body_is_unchanged():
    """Третий обработчик не правится ни на символ и не переносится (`10-52#0`, `10-57#3`).

    Он закрывает дефект `G-10-5` (плашка отказа переживала успешный обмен).
    Правило читает только его регистрацию: одна, на `document.body`, третья в
    блоке признака однократности, параметр и тело посимвольно равны
    объявленным. Тела двух других обработчиков план 10-57 правил решением
    владельца, и правило их не сличает.
    """
    findings = _third_handler_findings(_failure_banner_path())

    assert findings == (), f"{FAILURE_BANNER_OWNER}:\n" + "\n".join(
        f"  — {line}" for line in findings
    )


def test_the_banner_script_reads_only_state_signals_from_the_response():
    """Сценарий читает из события отказа только признаки состояния (`10-49#1`).

    Тело или заголовки чужого ответа, попавшие в плашку, вынесли бы наружу
    внутреннее устройство (T-08-20). Действующее правило запрещает одно имя —
    `responseText`. Здесь перечень обращений ЗАКРЫТ: всё, что не код состояния
    и не признак успеха, названо.

    ⚠️ АНТИВАКУУМ: разбор нашёл хотя бы одно чтение перечня. Разборщик, не
    нашедший ни одного обращения, зеленел бы на любом сценарии. Равенства
    перечню правило НЕ требует: пропажа чтения (например, откат третьего
    обработчика вместе с `detail.successful`) — не чтение сверх признаков
    состояния, и её держат правила третьего обработчика, а не это.
    """
    findings, reads = _response_read_findings(_failure_banner_path())

    assert reads, (
        f"{FAILURE_BANNER_OWNER}: разбор не нашёл ни одного чтения из перечня "
        f"{FAILURE_BANNER_RESPONSE_READS} — правило проверяло бы пустоту"
    )
    assert findings == (), f"{FAILURE_BANNER_OWNER}:\n" + "\n".join(
        f"  — {line}" for line in findings
    )


# --- Контроли -----------------------------------------------------------------


def test_control_an_edited_banner_text_reddens_and_an_edited_dismiss_name_does_not(
    tmp_path,
):
    """Правило текстов называет правку текста и молчит на правке доступного имени."""
    assert _banner_text_findings(_failure_banner_path()) == (), (
        "боевое дерево само красно по правилу текстов — контролю не с чем сличать"
    )
    original = _failure_banner_source(_failure_banner_path())

    server = _banner_text_findings(
        _scratch(
            tmp_path,
            "server",
            _replace_once(original, "через минуту.", "через минутку."),
        )
    )
    assert any(FAILURE_BANNER_IDS[0] in f and "минутку" in f for f in server), server

    network = _banner_text_findings(
        _scratch(
            tmp_path,
            "network",
            _replace_once(original, "Проверьте соединение", "Проверьте подключение"),
        )
    )
    assert any(FAILURE_BANNER_IDS[1] in f and "подключение" in f for f in network), (
        "правка текста обрыва связи, сохранившая основы смысла, не названа: "
        f"{network}"
    )

    extra = _banner_text_findings(
        _scratch(
            tmp_path,
            "extra",
            _replace_once(
                original,
                "'error') }}</div>\n<div id=\"htmx-failure-network\"",
                "'error') }}<p>Сервер перегружен.</p></div>\n<div id=\"htmx-failure-network\"",
            ),
        )
    )
    assert any("ВНЕ вызова макроса" in f for f in extra), extra

    label = re.search(r'aria-label="([^"]*)"', original)
    assert label, "в шаблоне нет доступного имени органа снятия — контролировать нечего"
    renamed = _banner_text_findings(
        _scratch(
            tmp_path,
            "label",
            original.replace(label.group(0), 'aria-label="Закрыть"', 1),
        )
    )
    assert renamed == (), (
        "ПРАВИЛО ТЕКСТОВ КРАСНЕЕТ НА ПРАВКЕ ДОСТУПНОГО ИМЕНИ органа снятия — оно "
        f"стережёт чужой предмет (план 15-19): {renamed}"
    )


def test_control_a_split_macro_call_on_the_network_line_reddens(tmp_path):
    """Правило строки называет вызов макроса, закрытый на следующей строке."""
    path = _failure_banner_path()
    assert _network_node_line_findings(path) == () and _banner_text_findings(path) == (), (
        "боевое дерево само красно по правилу строки или текстов — контролю не с чем "
        "сличать"
    )
    original = _failure_banner_source(path)
    text = FAILURE_BANNER_TEXTS[FAILURE_BANNER_IDS[1]]
    split = _replace_once(original, f"'{text}', 'error') }}}}", f"'{text}',\n'error') }}}}")

    findings = _network_node_line_findings(_scratch(tmp_path, "split", split))

    assert any("НЕ НЕСЁТ ВЫЗОВА МАКРОСА" in f for f in findings), findings
    assert _banner_text_findings(_scratch(tmp_path, "texts", split)) == (), (
        "разбиение строки задело правило текстов — их предметы должны быть разведены"
    )


def test_control_an_edited_moved_or_removed_third_handler_reddens(tmp_path):
    """Правило третьего обработчика называет правку, перенос и откат, но не чужое тело."""
    path = _failure_banner_path()
    assert _third_handler_findings(path) == (), (
        "боевое дерево само красно по правилу третьего обработчика — контролю не с "
        "чем сличать"
    )
    original = _failure_banner_source(path)
    registrations = _registrations(_failure_banner_script(path))
    assert len(registrations) == FAILURE_BANNER_HANDLERS_MEASURED, (
        f"разборщик нашёл {len(registrations)} регистраций, а измерено "
        f"{FAILURE_BANNER_HANDLERS_MEASURED} — контроль сличал бы не тот сценарий"
    )
    head = (
        f"  {THIRD_HANDLER_HOST}.addEventListener('{FAILURE_BANNER_SUCCESS_EVENT}', "
        f"function ({THIRD_HANDLER_PARAMS}) {{"
    )
    block = head + THIRD_HANDLER_BODY + "});\n"
    first = "  document.body.addEventListener('htmx:responseError'"

    cases = {
        "char": (
            _replace_once(
                original,
                "!event.detail.successful) { return; }",
                "event.detail.successful !== true) { return; }",
            ),
            "ТЕЛО ТРЕТЬЕГО ОБРАБОТЧИКА ИЗМЕНЕНО",
        ),
        "space": (
            _replace_once(original, "successful) { return; }", "successful) {return;}"),
            "ТЕЛО ТРЕТЬЕГО ОБРАБОТЧИКА ИЗМЕНЕНО",
        ),
        "reorder": (
            _replace_once(_replace_once(original, block, ""), first, block + first),
            "в порядке регистрации",
        ),
        "outside": (
            _replace_once(
                _replace_once(original, block, ""), "  }\n</script>", "  }\n" + block + "</script>"
            ),
            "за пределы блока",
        ),
        "host": (
            _replace_once(
                original,
                f"  {THIRD_HANDLER_HOST}.addEventListener('{FAILURE_BANNER_SUCCESS_EVENT}'",
                f"  document.addEventListener('{FAILURE_BANNER_SUCCESS_EVENT}'",
            ),
            "на узел `document`",
        ),
        "removed": (_replace_once(original, block, ""), "регистраций"),
    }
    for name, (text, marker) in cases.items():
        findings = _third_handler_findings(_scratch(tmp_path, name, text))
        assert any(marker in f for f in findings), (
            f"копия `{name}` не названа правилом третьего обработчика: {findings}"
        )

    other = _replace_once(
        original,
        "if (server) { server.removeAttribute('hidden'); }",
        "if (server) { server.removeAttribute( 'hidden' ); }",
    )
    assert _third_handler_findings(_scratch(tmp_path, "other", other)) == (), (
        "ПРАВИЛО ТРЕТЬЕГО ОБРАБОТЧИКА КРАСНЕЕТ НА ПРАВКЕ ТЕЛА ДРУГОГО обработчика — "
        "оно утверждало бы замещённое «сценарий не правится ни на строку»"
    )


def test_control_a_response_read_beyond_state_signals_is_named(tmp_path):
    """Правило чтений называет каждое обращение вне закрытого перечня.

    Замер перечня: на боевом дереве разбор находит ровно
    `FAILURE_BANNER_RESPONSE_READS` и ни одного нарушения.
    """
    tree_findings, tree_reads = _response_read_findings(_failure_banner_path())
    assert tree_findings == () and set(tree_reads) == set(
        FAILURE_BANNER_RESPONSE_READS
    ), (
        "перечень чтений разошёлся с деревом — контролю не с чем сличать: "
        f"{tree_findings}, {sorted(set(tree_reads))}"
    )
    original = _failure_banner_source(_failure_banner_path())
    anchor = "    if (server) { server.removeAttribute('hidden'); }\n"

    cases = {
        "header": "    if (server) { server.title = event.detail.xhr.getResponseHeader('X-Reason'); }\n",
        "response": "    if (server) { server.title = event.detail.xhr.response; }\n",
        "alias": "    var reply = event.detail.xhr; if (server) { server.title = reply.statusText; }\n",
        "bracket": "    if (server) { server.title = event['detail'].xhr.status; }\n",
        "arguments": "    if (server) { server.title = arguments[0].detail.xhr.statusText; }\n",
    }
    expected = {
        "header": "event.detail.xhr.getResponseHeader(",
        "response": "`event.detail.xhr.response`",
        "alias": "`event.detail.xhr`",
        "bracket": "`event[",
        "arguments": "`arguments`",
    }
    for name, addition in cases.items():
        findings, _reads = _response_read_findings(
            _scratch(tmp_path, name, _replace_once(original, anchor, anchor + addition))
        )
        assert any(expected[name] in f for f in findings), (
            f"копия `{name}` не названа правилом чтений: {findings}"
        )


# =============================================================================
# ПОДЪЁМ И СТОПКА В ТАБЛИЦЕ СТИЛЕЙ (план 15-28)
# =============================================================================
#
# ⚠️ ЛИТЕРАЛЫ СНЯТЫ С ДЕРЕВА (`app/static/css/app.css`, дерево `b2a6b399`), А
# НЕ ВЗЯТЫ ИЗ ПАМЯТИ, И ИСТОРИЯ КАЖДОГО СЛИЧЕНА ПО ФАЙЛУ:
# * блок подъёма — в этом виде с плана 10-56 (`9583ca4e`, 2026-09-13), и ни
#   одна правка после не меняла его ни на символ (планы 10-57, 15-07, 15-19
#   трогали соседние блоки и `:root`); селектор — в этом виде с плана 10-51
#   (`34ac7747`), когда с него снят признак-предок;
# * базовое положение `12px` стояло литералом `top: 12px` в блоке подъёма с плана
#   10-33 (`48d5788e`) по план 10-51, и план 10-56 перенёс его в базовый блок
#   стопки величиной (`10-56#4`: «базовое значение остаётся тем же, что стояло
#   литералом»);
# * блок признака блокировки прокрутки — с плана 09-13 (`03266943`), не менялся.
FAILURE_BANNER_LIFT_BLOCK = (
    "#htmx-failure-server,\n"
    "#htmx-failure-network {\n"
    "  position: fixed;\n"
    "  top: var(--failure-banner-top, 12px); left: 0; right: 0;\n"
    "  z-index: 70;\n"
    "  width: min(560px, calc(100% - 24px));\n"
    "  margin-left: auto; margin-right: auto;\n"
    "  border-radius: var(--r-lg);\n"
    "  background: var(--surface);\n"
    "  box-shadow: 0 24px 60px rgba(8, 8, 11, .6);\n"
    "}"
)
FAILURE_BANNER_BASE_OFFSET = "12px"

# Объявления, делающие блок блоком ПОДЪЁМА: слой и положение. Вторая копия любого
# из них у узла заготовки есть «вторая копия величин» формулировки `10-51#2`.
FAILURE_BANNER_LIFT_PROPERTIES = ("z-index", "position")

# Селекторы блока блокировки прокрутки собраны из имени признака, замеренного по
# рычагу (`MODAL_SCROLL_LOCK_FLAG`), а не выписаны вторым литералом.
SCROLL_LOCK_SELECTORS = (
    f".{MODAL_SCROLL_LOCK_FLAG}",
    f".{MODAL_SCROLL_LOCK_FLAG} body",
)
SCROLL_LOCK_DECLARATION = ("overflow", "hidden")

# Область уведомлений об ошибке, которую подъём не включает (`10-33#3`).
NOTICE_REGION_ID = "notice-alert"
NOTICE_REGION_OWNER = "includes/notice_area.html"
NOTICE_LIFT_POSITIONS = ("fixed", "sticky")

_OPENING_TAG_RE = re.compile(r"<([A-Za-z][\w-]*)\b([^<>]*)>")
_TAG_ATTRIBUTE_RE = re.compile(
    r"([^\s=/>\"']+)(?:\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s\"'>]+)))?"
)
_ATTRIBUTE_SELECTOR_RE = re.compile(
    r"^\[\s*([\w-]+)\s*(?:([~|^$*]?=)\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s\]]+))"
    r"\s*([iIsS])?\s*)?\]$"
)
_PSEUDO_ELEMENTS = (":before", ":after", ":first-line", ":first-letter")


class _Node(NamedTuple):
    """Открывающий тег узла: имя и признаки (значения — как в шаблоне)."""

    tag: str
    attributes: dict[str, str]


def _notice_region_path() -> Path:
    """Путь шаблона области уведомлений — единственное место, где он собирается."""
    return PROJECT_ROOT / "app" / "templates" / NOTICE_REGION_OWNER


def _node_of(template: Path, element_id: str) -> _Node | None:
    """Узел с этим идентификатором в шаблоне без комментариев, если он ровно один."""
    code = _without_comments(_failure_banner_source(template))
    found: list[_Node] = []
    for tag in _OPENING_TAG_RE.finditer(code):
        attributes: dict[str, str] = {}
        for attribute in _TAG_ATTRIBUTE_RE.finditer(tag.group(2)):
            value = next((g for g in attribute.groups()[1:] if g is not None), "")
            attributes[attribute.group(1).lower()] = value
        if attributes.get("id") == element_id:
            found.append(_Node(tag.group(1).lower(), attributes))
    return found[0] if len(found) == 1 else None


def _banner_nodes(template: Path) -> dict[str, _Node | None]:
    return {banner_id: _node_of(template, banner_id) for banner_id in FAILURE_BANNER_IDS}


def _selector_list(selector: str) -> tuple[str, ...]:
    """Селекторы списка: деление по запятой только вне скобок (`:is(a, b)` цел)."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for symbol in selector:
        if symbol in "([":
            depth += 1
        elif symbol in ")]":
            depth = max(depth - 1, 0)
        if symbol == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(symbol)
    parts.append("".join(current).strip())
    return tuple(part for part in parts if part)


def _attribute_may_match(simple: str, node: _Node) -> bool:
    hit = _ATTRIBUTE_SELECTOR_RE.match(simple)
    if hit is None:
        return True  # неразобранный признак — осторожная сторона: «может достать»
    name, operator = hit.group(1).lower(), hit.group(2)
    if name not in node.attributes:
        return False
    if operator is None:
        return True
    expected = next(g for g in hit.groups()[2:5] if g is not None)
    actual = node.attributes[name]
    if (hit.group(6) or "").lower() == "i":
        expected, actual = expected.lower(), actual.lower()
    return {
        "=": actual == expected,
        "~=": expected in actual.split(),
        "|=": actual == expected or actual.startswith(expected + "-"),
        "^=": bool(expected) and actual.startswith(expected),
        "$=": bool(expected) and actual.endswith(expected),
        "*=": bool(expected) and expected in actual,
    }[operator]


def _compound_may_match(compound: str, node: _Node) -> bool:
    """Может ли составная часть совпасть с узлом, НАЗЫВАЯ его. Границы — в докстринге модуля.

    ⚠️ ЧАСТЬ БЕЗ ИДЕНТИФИКАТОРА, КЛАССА ИЛИ ПРИЗНАКА УЗЛА НЕ СЧИТАЕТСЯ ДОСТИГАЮЩЕЙ.
    Замер дерева `b2a6b399`: без этого условия узлы заготовок «достигали» блоки
    `*`, `[data-row] > *`, `[data-dashpair] > *`, `.sched-card__sum > *` и
    `.acct-card__kv .kv > :last-child` — предки в разбор не входят, и такой блок
    совпадает с ЛЮБЫМ элементом своего места. Первая же правка вида
    `[data-row] > * { position: relative; }` покраснила бы правило подъёма за
    форму чужой правки, а не за второй подъём (ровно довод `10-56#1`).
    """
    classes = node.attributes.get("class", "").split()
    named = False
    for simple in _compound_simple_selectors(compound):
        lowered = simple.lower()
        if simple.startswith("#"):
            if simple[1:] != node.attributes.get("id"):
                return False
            named = True
        elif simple.startswith("."):
            if simple[1:] not in classes:
                return False
            named = True
        elif simple.startswith("["):
            if not _attribute_may_match(simple, node):
                return False
            named = True
        elif simple.startswith(":"):
            if lowered.startswith("::") or lowered in _PSEUDO_ELEMENTS:
                return False
            if lowered == ":root":
                return False
        elif simple != "*" and lowered != node.tag:
            return False
    return named


def _selector_reaches(selector: str, node: _Node) -> bool:
    """Достигает ли блок узла: последняя составная часть одного из селекторов списка."""
    for part in _selector_list(selector):
        compounds = _selector_compounds(part)
        if compounds and _compound_may_match(compounds[-1], node):
            return True
    return False


def _missing_banner_nodes(nodes: dict[str, _Node | None]) -> tuple[str, ...]:
    missing = [banner_id for banner_id, node in nodes.items() if node is None]
    if not missing:
        return ()
    return (
        f"{FAILURE_BANNER_OWNER}: узел заготовки {missing} не найден ровно один раз "
        "— сличать достижимость не с чем",
    )


def _banner_lift_block_findings(stylesheet: Path, template: Path) -> tuple[str, ...]:
    """Блоки, достигающие узлов заготовок и объявляющие слой или положение. Пусто — один."""
    nodes = _banner_nodes(template)
    missing = _missing_banner_nodes(nodes)
    if missing:
        return missing
    lifting: list[tuple[str, list[str], list[str]]] = []
    for selector, body, _raw in _css_rules_of(stylesheet):
        declared = [
            f"{prop}: {value}"
            for prop, value in _css_declarations(body)
            if prop in FAILURE_BANNER_LIFT_PROPERTIES
        ]
        if not declared:
            continue
        reached = [
            banner_id for banner_id, node in nodes.items()
            if node is not None and _selector_reaches(selector, node)
        ]
        if reached:
            lifting.append((selector, declared, reached))
    if len(lifting) != 1:
        return (
            f"БЛОКОВ ПОДЪЁМА ЗАГОТОВОК В ТАБЛИЦЕ {len(lifting)}, А НЕ ОДИН — вторая "
            "копия величин разошлась бы с первой молча (`10-51#2`):\n"
            + "\n".join(
                f"      `{selector}` → {', '.join(reached)}: {'; '.join(declared)}"
                for selector, declared, reached in lifting
            ),
        )
    selector, _declared, reached = lifting[0]
    if sorted(reached) != sorted(FAILURE_BANNER_IDS):
        return (
            f"единственный блок подъёма `{selector}` достигает не обеих заготовок: "
            f"{reached}",
        )
    return ()


def _scroll_lock_findings(stylesheet: Path) -> tuple[str, ...]:
    """Селекторы блокировки прокрутки без действующего `overflow: hidden`. Пусто — объявлено."""
    rules = _css_rules_of(stylesheet)
    prop, expected = SCROLL_LOCK_DECLARATION
    findings: list[str] = []
    for target in SCROLL_LOCK_SELECTORS:
        blocks = [
            body for selector, body, _raw in rules
            if target in _selector_list(selector)
        ]
        if not blocks:
            findings.append(
                f"`{target}`: блока с этим селектором в таблице НЕТ — правило "
                "блокировки прокрутки снято, и список за открытой панелью едет"
            )
            continue
        values = [value for body in blocks for name, value in _css_declarations(body)
                  if name == prop]
        if not values:
            findings.append(
                f"`{target}`: селектор жив, а объявления `{prop}` в его блоках НЕТ — "
                "признак поднимается и не блокирует ничего (план 09-13)"
            )
        elif values[-1] != expected:
            findings.append(
                f"`{target}`: объявлено `{prop}: {values[-1]}`, ожидалось "
                f"`{prop}: {expected}` — прокрутка за открытой панелью не заблокирована"
            )
    return tuple(findings)


def _lift_block_text_findings(stylesheet: Path) -> tuple[str, ...]:
    """Расхождение блока подъёма с объявленным литералом. Пусто — равен посимвольно."""
    rules = _banner_elevation_rules(stylesheet)
    if len(rules) != 1:
        return (
            f"блоков подъёма (селектор с адресом заготовки) в таблице {len(rules)}, "
            "а не один — сличать блок не с чем",
        )
    block = _css_rule_block(rules[0][2])
    if block == FAILURE_BANNER_LIFT_BLOCK:
        return ()
    position = next(
        (i for i, (got, want) in enumerate(zip(block, FAILURE_BANNER_LIFT_BLOCK))
         if got != want),
        min(len(block), len(FAILURE_BANNER_LIFT_BLOCK)),
    )
    where = "СЕЛЕКТОР" if position <= FAILURE_BANNER_LIFT_BLOCK.index("{") else "ТЕЛО"
    return (
        f"БЛОК ПОДЪЁМА ИЗМЕНЁН ({where}) с символа {position}:\n"
        f"      получено:  {block[position:position + 60]!r}\n"
        f"      ожидалось: {FAILURE_BANNER_LIFT_BLOCK[position:position + 60]!r}\n"
        "      запреты `10-56#2`, `10-57#8`: блок и его селектор не правятся",
    )


def _base_offset_findings(stylesheet: Path) -> tuple[str, ...]:
    """Базовое положение первой заготовки. Пусто — равно замеренному литералу."""
    base = _stack_blocks(stylesheet)["base"]
    if len(base) != 1:
        return (
            f"базовых блоков `.{FAILURE_BANNER_STACK_CLASS}` с величиной "
            f"`{FAILURE_BANNER_OFFSET_PROPERTY}` в таблице {len(base)}, а не один",
        )
    selector, value, _raw = base[0]
    if value != FAILURE_BANNER_BASE_OFFSET:
        return (
            "ПОЛОЖЕНИЕ ПЕРВОЙ ЗАГОТОВКИ СДВИНУТО:\n"
            f"      получено:  `{selector}` → {FAILURE_BANNER_OFFSET_PROPERTY}: {value}\n"
            f"      ожидалось: {FAILURE_BANNER_OFFSET_PROPERTY}: "
            f"{FAILURE_BANNER_BASE_OFFSET} (литерал `top`, стоявший до плана 10-56)\n"
            "      следствие: прямоугольник ОДНОЙ показанной заготовки сдвинут, и "
            "человеческие наблюдения о нём обесценены (`10-56#4`)",
        )
    return ()


def _banner_display_findings(stylesheet: Path, template: Path) -> tuple[str, ...]:
    """Показывающие объявления у блоков, достигающих узла заготовки. Пусто — нет."""
    nodes = _banner_nodes(template)
    missing = _missing_banner_nodes(nodes)
    if missing:
        return missing
    findings: list[str] = []
    for selector, body, _raw in _css_rules_of(stylesheet):
        if not any(
            node is not None and _selector_reaches(selector, node)
            for node in nodes.values()
        ):
            continue
        for prop, value in _css_declarations(body):
            if prop == "display" and value != "none":
                findings.append(
                    f"`{selector}`: display: {value} — перебивает атрибут скрытия, "
                    "две пустые подложки на каждом экране"
                )
            elif prop == "all":
                findings.append(
                    f"`{selector}`: all: {value} — сокращение объявляет и способ "
                    "отображения, и он уже не «нет»"
                )
    return tuple(findings)


def _notice_lift_findings(stylesheet: Path, template: Path) -> tuple[str, ...]:
    """Блоки, поднимающие узел области уведомлений. Пусто — не поднят."""
    node = _node_of(template, NOTICE_REGION_ID)
    if node is None:
        return (
            f"{NOTICE_REGION_OWNER}: узел `#{NOTICE_REGION_ID}` не найден ровно один "
            "раз — сличать достижимость не с чем",
        )
    findings: list[str] = []
    for selector, body, _raw in _css_rules_of(stylesheet):
        if not _selector_reaches(selector, node):
            continue
        for prop, value in _css_declarations(body):
            if prop == "z-index" or (prop == "position" and value in NOTICE_LIFT_POSITIONS):
                findings.append(
                    f"`{selector}`: {prop}: {value} — область `#{NOTICE_REGION_ID}` "
                    "включена в подъём, а коды отказа приезжают туда только "
                    "транспортом перехода (`10-33#3`, WR-02)"
                )
    return tuple(findings)


def _scratch_css(tmp_path: Path, name: str, text: str) -> Path:
    """Копия таблицы в собственном подкаталоге: несколько копий в одном контроле."""
    where = tmp_path / name
    where.mkdir()
    return _scratch_stylesheet(where, text)


# --- Правила подъёма и стопки ---------------------------------------------------


def test_exactly_one_stylesheet_block_lifts_the_failure_banners():
    """Блок подъёма заготовок ОДИН по разбору селектора (`10-51#2`).

    Действующие правила отбирают блоки подъёма по вхождению идентификатора
    заготовки. Второй блок, достающий узел классом стопки или признаком
    идентификатора, они не считают; это правило считает всякий блок, чья
    последняя составная часть совпадает с узлом, снятым из шаблона, и который
    объявляет слой или положение.
    """
    findings = _banner_lift_block_findings(_app_css_path(), _failure_banner_path())

    assert findings == (), "app.css:\n" + "\n".join(findings)


def test_the_modal_open_mark_declares_the_scroll_lock():
    """Блок признака `is-modal-open` объявляет `overflow: hidden` (`10-51#3`).

    Действующее правило `test_the_panel_raises_the_scroll_lock_when_it_opens`
    утверждает имя селектора в таблице и подъём признака панелью; снятое
    объявление при живом селекторе оставляло его зелёным.
    """
    findings = _scroll_lock_findings(_app_css_path())

    assert findings == (), "app.css:\n" + "\n".join(findings)


def test_the_failure_banner_lift_block_is_unchanged():
    """Блок подъёма — селектор и тело — посимвольно равен объявленному (`10-56#2`, `10-57#8`)."""
    findings = _lift_block_text_findings(_app_css_path())

    assert findings == (), "app.css:\n" + "\n".join(findings)


def test_the_first_failure_banner_keeps_its_measured_offset():
    """Базовое положение первой заготовки равно литералу до плана 10-56 (`10-56#4`)."""
    findings = _base_offset_findings(_app_css_path())

    assert findings == (), "app.css:\n" + "\n".join(findings)


def test_no_block_reaching_a_failure_banner_shows_it_through_display_or_all():
    """У узла заготовки способ отображения — только «нет», и `all` нет (`10-56#3`, `10-57#8`, `10-57#9`)."""
    findings = _banner_display_findings(_app_css_path(), _failure_banner_path())

    assert findings == (), "app.css:\n" + "\n".join(findings)


def test_the_notice_region_is_not_lifted():
    """Ни один блок, достигающий `#notice-alert`, не поднимает область (`10-33#3`)."""
    findings = _notice_lift_findings(_app_css_path(), _notice_region_path())

    assert findings == (), "app.css:\n" + "\n".join(findings)


# --- Контроли подъёма и стопки ------------------------------------------------


def test_control_a_second_lift_block_by_any_selector_is_named(tmp_path):
    """Второй блок подъёма назван в любой форме; блоки потомков и псевдоэлементов — нет."""
    css, template = _app_css_path(), _failure_banner_path()
    assert _banner_lift_block_findings(css, template) == (), (
        "боевая таблица сама красна по правилу блока подъёма — контролю не с чем сличать"
    )
    original = _stylesheet_source(css)

    for name, block, named in (
        ("stack", ".failure-stack { z-index: 71; }", "`.failure-stack`"),
        ("pair", ".failure-stack + .failure-stack { z-index: 71; }", "+ .failure-stack`"),
        ("attribute", '[id="htmx-failure-server"] { position: fixed; top: 40px; }',
         '[id="htmx-failure-server"]'),
        ("identifier", "#htmx-failure-network { z-index: 71; }", "`#htmx-failure-network`"),
    ):
        findings = _banner_lift_block_findings(
            _scratch_css(tmp_path, name, original + "\n" + block + "\n"), template
        )
        assert len(findings) == 1 and named in findings[0], (
            f"второй блок подъёма `{block}` не назван: {findings}"
        )

    for name, block in (
        ("child", ".failure-stack > .alert { position: relative; z-index: 2; }"),
        ("pseudo", ".failure-stack::before { position: absolute; }"),
        ("other", ".connect-step { position: relative; }"),
        ("universal", "[data-row] > * { position: relative; z-index: 1; }"),
    ):
        findings = _banner_lift_block_findings(
            _scratch_css(tmp_path, name, original + "\n" + block + "\n"), template
        )
        assert findings == (), (
            f"правило назвало блок, не достигающий узла заготовки (`{block}`): {findings}"
        )


def test_control_a_scroll_lock_without_its_declaration_reddens(tmp_path):
    """Снятое или ослабленное `overflow: hidden` при живом селекторе названо."""
    css = _app_css_path()
    assert _scroll_lock_findings(css) == (), (
        "боевая таблица сама красна по правилу блокировки прокрутки"
    )
    original = _stylesheet_source(css)
    lock = ".is-modal-open,\n.is-modal-open body {\n  overflow: hidden;\n}"

    dropped = _scroll_lock_findings(_scratch_css(
        tmp_path, "dropped",
        _replace_once(original, lock, ".is-modal-open,\n.is-modal-open body {\n}"),
    ))
    assert len(dropped) == 2 and all("НЕТ" in f for f in dropped), dropped

    weakened = _scroll_lock_findings(_scratch_css(
        tmp_path, "weakened", _replace_once(original, lock, lock.replace("hidden", "auto"))
    ))
    assert len(weakened) == 2 and all("overflow: auto" in f for f in weakened), weakened

    halved = _scroll_lock_findings(_scratch_css(
        tmp_path, "halved",
        _replace_once(original, lock, ".is-modal-open {\n  overflow: hidden;\n}"),
    ))
    assert len(halved) == 1 and "`.is-modal-open body`" in halved[0], halved

    elsewhere = _scroll_lock_findings(_scratch_css(
        tmp_path, "elsewhere", original + "\n.modal { overflow: auto; }\n"
    ))
    assert elsewhere == (), f"правило назвало чужой блок: {elsewhere}"


def test_control_an_edited_lift_block_reddens_and_an_edited_stack_does_not(tmp_path):
    """Правка селектора или тела блока подъёма названа; правка стопки — нет."""
    css = _app_css_path()
    assert _lift_block_text_findings(css) == (), (
        "боевой блок подъёма сам расходится с литералом"
    )
    original = _stylesheet_source(css)
    head = "#htmx-failure-server,\n#htmx-failure-network {"

    for name, old, new, where in (
        ("reorder", head, "#htmx-failure-network,\n#htmx-failure-server {", "СЕЛЕКТОР"),
        ("spaces", head, "#htmx-failure-server, #htmx-failure-network {", "СЕЛЕКТОР"),
        ("state", head, "#htmx-failure-server,\n#htmx-failure-network:not([hidden]) {",
         "СЕЛЕКТОР"),
        ("width", "  width: min(560px, calc(100% - 24px));\n  margin-left: auto;",
         "  width: min(600px, calc(100% - 24px));\n  margin-left: auto;", "ТЕЛО"),
    ):
        findings = _lift_block_text_findings(
            _scratch_css(tmp_path, name, _replace_once(original, old, new))
        )
        assert len(findings) == 1 and f"({where})" in findings[0], (
            f"правка `{name}` не названа как правка {where}: {findings}"
        )

    stack = _lift_block_text_findings(_scratch_css(
        tmp_path, "stack",
        _replace_once(original, "  --failure-stack-step: 96px;", "  --failure-stack-step: 100px;"),
    ))
    assert stack == (), f"правило блока подъёма краснеет на правке стопки: {stack}"


def test_control_a_shifted_base_offset_reddens_and_a_changed_step_does_not(tmp_path):
    """Согласованный сдвиг базы назван; правка шага стопки — нет."""
    css = _app_css_path()
    assert _base_offset_findings(css) == (), "боевая база сама расходится с литералом"
    original = _stylesheet_source(css)

    shifted = original
    for old, new in (
        (".failure-stack {\n  --failure-banner-top: 12px;\n  --failure-stack-step",
         ".failure-stack {\n  --failure-banner-top: 16px;\n  --failure-stack-step"),
        ("--failure-banner-top: calc(12px + ", "--failure-banner-top: calc(16px + "),
        (".failure-stack[hidden] + .failure-stack {\n  --failure-banner-top: 12px;",
         ".failure-stack[hidden] + .failure-stack {\n  --failure-banner-top: 16px;"),
    ):
        shifted = _replace_once(shifted, old, new)
    findings = _base_offset_findings(_scratch_css(tmp_path, "shifted", shifted))
    assert len(findings) == 1 and "16px" in findings[0], findings

    step = _base_offset_findings(_scratch_css(
        tmp_path, "step",
        _replace_once(original, f"  {FAILURE_BANNER_STEP_PROPERTY}: 96px;",
                      f"  {FAILURE_BANNER_STEP_PROPERTY}: 100px;"),
    ))
    assert step == (), f"правило базы краснеет на правке шага: {step}"


def test_control_a_showing_display_or_all_at_a_banner_node_is_named(tmp_path):
    """Показывающее значение и `all` у узла названы в любой форме селектора."""
    css, template = _app_css_path(), _failure_banner_path()
    assert _banner_display_findings(css, template) == (), (
        "боевая таблица сама красна по правилу способа отображения"
    )
    original = _stylesheet_source(css)
    hiding = ".failure-stack:has(> .banner-dismiss:checked) { display: none; }"
    lift = "#htmx-failure-network {\n  position: fixed;"

    for name, text, named in (
        ("hiding", _replace_once(original, hiding, hiding.replace("none", "block")),
         "display: block"),
        ("attribute", original + '\n[id^="htmx-failure"] { display: block; }\n',
         '[id^="htmx-failure"]'),
        ("lift-all", _replace_once(original, lift, lift.replace("{\n", "{\n  all: initial;\n")),
         "all: initial"),
        ("hiding-all", _replace_once(original, hiding, hiding.replace("none; }", "none; all: unset; }")),
         "all: unset"),
    ):
        findings = _banner_display_findings(_scratch_css(tmp_path, name, text), template)
        assert len(findings) == 1 and named in findings[0], (
            f"копия `{name}` не названа: {findings}"
        )

    for name, block in (
        ("pseudo", ".failure-stack::before { display: block; }"),
        ("child", ".failure-stack > .alert { display: flex; }"),
        ("universal", "[data-dashpair] > * { display: block; }"),
    ):
        findings = _banner_display_findings(
            _scratch_css(tmp_path, name, original + "\n" + block + "\n"), template
        )
        assert findings == (), f"правило назвало блок, не достигающий узла (`{block}`): {findings}"


def test_control_a_lifted_notice_region_is_named(tmp_path):
    """Подъём `#notice-alert` назван в селекторе подъёма и собственным блоком; прочее — нет."""
    css, template = _app_css_path(), _notice_region_path()
    assert _notice_lift_findings(css, template) == (), (
        "боевая таблица сама поднимает область уведомлений"
    )
    original = _stylesheet_source(css)
    head = "#htmx-failure-server,\n#htmx-failure-network {"

    joined = _notice_lift_findings(_scratch_css(
        tmp_path, "joined",
        _replace_once(original, head, "#htmx-failure-server,\n#htmx-failure-network,\n#notice-alert {"),
    ), template)
    assert joined and all(f"`#{NOTICE_REGION_ID}`" in f for f in joined), joined

    own = _notice_lift_findings(_scratch_css(
        tmp_path, "own", original + "\n#notice-alert { position: fixed; top: 12px; z-index: 70; }\n"
    ), template)
    assert len(own) == 2, own

    flow = _notice_lift_findings(_scratch_css(
        tmp_path, "flow", original + "\n#notice-alert { position: relative; margin-top: 4px; }\n"
    ), template)
    assert flow == (), f"правило назвало положение в потоке подъёмом: {flow}"

    universal = _notice_lift_findings(_scratch_css(
        tmp_path, "universal", original + "\n[data-row] > * { position: sticky; z-index: 1; }\n"
    ), template)
    assert universal == (), f"правило назвало блок, не называющий узла: {universal}"

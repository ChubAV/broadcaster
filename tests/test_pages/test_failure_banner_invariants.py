"""Запреты Фазы 10 о СЦЕНАРИИ и ТЕКСТАХ плашек отказа, которые суита не держала.

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
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

from tests.test_pages.test_shell import (
    FAILURE_BANNER_HANDLERS_MEASURED,
    FAILURE_BANNER_IDS,
    FAILURE_BANNER_OWNER,
    FAILURE_BANNER_SUCCESS_EVENT,
    _failure_banner_path,
    _failure_banner_script,
    _failure_banner_source,
    _network_banner_line,
    _scratch_banner,
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

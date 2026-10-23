"""Маска номера в выводе журнала — защита на исполнении (решение владельца О-23 (а), свойство 2).

ЗАЧЕМ. Статический гейт приватности (`tests/test_phone_privacy_gate.py`, D-17) судит исходник,
и обещанием «любое написание вызова журнала найдено» он не сходился: раунды 6–10 ревью находили
следующее написание динамического чтения (объект модуля `sys.modules[__name__]` под псевдонимом,
`importlib`, `operator.methodcaller` на носителе — CR-05, WR-32, WR-33), и номер печатался.
Решение владельца О-23 (а), 2026-10-22, свойство 2: номер, дошедший до вывода журнала любым
написанием, маскируется на исполнении формой `mask_phone` (D-10) в любом поле события.
Статический гейт приватности остаётся — это второй рубеж; запрет динамических конструкций
(планы 16-53, 16-54) держит то, что защита на исполнении не видит. D-11 для мест вызова не меняется:
место вызова номер в журнал не кладёт даже маской (только признак `phone_set`); маска здесь —
последний рубеж, а не разрешение.

ЧТО «ПОХОЖЕ НА НОМЕР» — решение владельца О-24 (а), 2026-10-22: подстрока, которую нормализатор
фазы (`app/services/phone.py`) признаёт номером хотя бы одним путём: `normalize_reported` (с `+`
и без, Fragment `+888…` автопутём), `normalize_manual` (российская запись с `8`, разбивка
`+7 (999) 123-45-67`); сверх буквы — разбивка показа `format_phone` (`+888 0123 4567`: ручной
путь её отвергает по О-1, автопуть не читает разделителей, поэтому судят цифры разбивки с `+`;
это номер, который фаза выводит сама). Кандидатов дают две грамматики: цепочка `_DIGIT_RUN`
(7…15 цифр с необязательным `+`, не прилегающая слева к букве, цифре, `+`, `.`, `-` и справа к
букве, цифре, `-`, «`.` + цифра») и разбивка `_SPACED_NUMBER` (начало — `+цифры`, `(цифры)` или
`8` перед разделителем; дальше цифры, пробелы, `-` и скобки). У разбивки, которую судья не
признал целиком, судятся её префиксы по границам групп цифр: «номер и хвост»
(`+7 999 123-45-67 5`) маскирует номер. Судья — нормализатор, а не длина: вариант (б) «любые
11–15 цифр» ОТВЕРГНУТ ВЛАДЕЛЬЦЕМ. Непредвиденная ошибка разбора кандидата даёт маску (отказ в
закрытую), а не утечку.

ЧТО ВИДНО (замер О-24 (а)): ID групп Telegram `-100…` (поле `group_id` событий отправки; и без
знака, и с `+`), JID групп WhatsApp (`120363…@g.us`), метки времени (миллисекунды
`1729500000000`, `20261022063000`, строки ISO), UUID, адреса, десятичные дроби, ID малой группы
`-123456789` и уже наложенная маска — повторное наложение ничего не меняет.

ЦЕНА — названная цена решения владельца О-24 (а), безвредная: цепочка 7–10 цифр, которую
автопуть читает номером, маскируется — `5123456789` → `+51 ******89` (Перу), `123456789` →
`+1 ******89`, `1234567` → `+1 ****67`, `4951234567` → `+49 **** **67`; так же секундная метка
времени из 10 цифр (`1729500000` читается номером зоны `+1`). Это лишняя маска на числе, а не
утечка номера.

ГДЕ СТОИТ (`app/logging_config.py`). Процессор `mask_numbers_in_event` — в цепочке
`ProcessorFormatter` корневого обработчика после `format_exc_info` и до рендерера: видит событие
structlog и запись stdlib с подставленными аргументами и текстом исключения и проходит любое
поле — строку, целое (номер-целое становится строкой маски, JSON остаётся разбираемым),
вложенные словари, списки, кортежи, множества (списком), `positional_args`, объект, чей `repr`
несёт номер. Фильтр `NumberMaskingFilter` — на корневом обработчике и на обработчиках журналов,
существующих к вызову `setup_logging` (uvicorn: обработчики `uvicorn` и `uvicorn.access` с
`propagate=False` корня не достигают). Фильтр сохраняет типы аргументов `%`, при ошибке
подстановки маскирует текстом (отчёт `--- Logging error ---` печатает только маскированное), не
поднимает исключение и не роняет запись.

ГРАНИЦА, НАЗВАННАЯ ПРЯМО (чего защита на исполнении НЕ видит):
* `print` и запись в `sys.stdout` / `sys.stderr` мимо журнала — их судит статический гейт
  приватности (D-17), а формы раунда 10 с `out = print` — запрет конструкции (планы 16-53,
  16-54); обёртка потоков процесса мешала бы захвату pytest и uvicorn и в свойство 2 не входит;
* обработчики, поставленные после вызова `setup_logging`, и журналы, настроенные мимо неё;
* процессы, не вызывающие `setup_logging` (скрипты `scripts/`), контейнеры `max_worker` (свой
  журнал) и `wa_worker` (Node) — там остаётся статический гейт приватности;
* номер, разбитый не пробелом, `-` и скобками (`+7.999.123.45.67`), и номер, прилегающий к
  букве (`id79991234567`, `x+79991234567`) — край грамматики;
* отчёт `--- Logging error ---` о сбое самого конвейера события structlog (рендерер упал)
  печатает словарь события как есть: фильтр запись structlog не трогает.
"""

import logging
import re

from app.services.phone import (
    E164_MAX_DIGITS,
    REPORTED_MIN_DIGITS,
    PhoneError,
    mask_phone,
    normalize_manual,
    normalize_reported,
)

# Край кандидата: слева не буква, не цифра, не `+`, `.`, `-`; справа не буква, не цифра, не `-`
# и не «`.` + цифра». Так ID группы `-100…`, хвосты UUID и десятичные дроби кандидатом не становятся.
_LEFT = r"(?<![^\W_]|[+.\-])"
_RIGHT = r"(?![^\W_]|-|\.\d)"

# Цепочка цифр с необязательным `+`: от `REPORTED_MIN_DIGITS` (7) до `E164_MAX_DIGITS` (15) цифр.
_DIGIT_RUN = re.compile(_LEFT + r"\+?[0-9]{7,15}" + _RIGHT)

# Разбивка: начинается с `+цифры`, `(цифры)` или `8` перед разделителем; дальше цифры и
# разделители (пробел, `-`, скобки); кончается цифрой.
_SPACED_NUMBER = re.compile(_LEFT + r"(?:\+[0-9]|\([0-9]{1,5}\)|8(?=[ \-(]))[0-9 \-()]*[0-9]" + _RIGHT)

_SEPARATORS = " -()"
_CONTAINER_DEPTH = 16
_MASK_ERROR = "[number-mask-error]"


def _digit_count(text: str) -> int:
    return sum(1 for ch in text if "0" <= ch <= "9")


def _recognised(text: str) -> str | None:
    """E.164 кандидата, если нормализатор фазы признаёт его номером хотя бы одним путём."""
    digit_count = _digit_count(text)
    if not REPORTED_MIN_DIGITS <= digit_count <= E164_MAX_DIGITS:
        return None
    found = normalize_reported(text)
    if found is not None:
        return found
    try:
        return normalize_manual(text)
    except PhoneError:
        pass
    if text.startswith("+"):
        # Разбивка показа `format_phone` (`+888 0123 4567`): ручной путь её отвергает, автопуть
        # не читает разделителей — судят цифры разбивки с `+`.
        return normalize_reported("+" + "".join(ch for ch in text if "0" <= ch <= "9"))
    return None


def _mask_of(text: str) -> str | None:
    """Маска кандидата или `None`; непредвиденная ошибка разбора — маска (отказ в закрытую)."""
    try:
        found = _recognised(text)
    except Exception:
        found = text
    if found is None:
        return None
    try:
        return mask_phone(found)
    except Exception:
        return "+***"


def _group_ends(text: str) -> list[int]:
    """Концы групп цифр разбивки, от самого длинного префикса к короткому."""
    ends = [index + 1 for index in range(len(text)) if "0" <= text[index] <= "9" and (
        index + 1 == len(text) or text[index + 1] in _SEPARATORS
    )]
    return ends[::-1]


def _mask_spaced(text: str) -> str:
    parts: list[str] = []
    position = 0
    search_from = 0
    while True:
        match = _SPACED_NUMBER.search(text, search_from)
        if match is None:
            break
        candidate = match.group()
        replaced = False
        for end in _group_ends(candidate):
            prefix = candidate[:end]
            if _digit_count(prefix) < REPORTED_MIN_DIGITS:
                break
            mask = _mask_of(prefix)
            if mask is not None:
                parts.append(text[position:match.start()])
                parts.append(mask)
                position = match.start() + end
                search_from = position
                replaced = True
                break
        if not replaced:
            search_from = match.start() + 1
    parts.append(text[position:])
    return "".join(parts)


def _mask_run(match: re.Match[str]) -> str:
    mask = _mask_of(match.group())
    return match.group() if mask is None else mask


def mask_numbers(text: str) -> str:
    """Текст, где каждая подстрока, признанная номером, заменена маской `mask_phone` (D-10)."""
    return _DIGIT_RUN.sub(_mask_run, _mask_spaced(text))


def _masked_text(value: object) -> str | None:
    """Маскированный `repr` (или `str`) объекта, если в нём номер; иначе `None`."""
    for render in (repr, str):
        try:
            shown = render(value)
        except Exception:
            continue
        masked = mask_numbers(shown)
        if masked != shown:
            return masked
    return None


def _masked_value(value: object, depth: int = 0) -> object:
    """Значение поля события с маской на каждом номере; без номера — прежний объект."""
    if value is None or isinstance(value, (bool, float)):
        return value
    if isinstance(value, str):
        return mask_numbers(value)
    if isinstance(value, int):
        shown = str(value)
        masked = mask_numbers(shown)
        return value if masked == shown else masked
    if depth < _CONTAINER_DEPTH:
        if isinstance(value, dict):
            pairs = list(value.items())
            items = [(_masked_value(key, depth + 1), _masked_value(item, depth + 1)) for key, item in pairs]
            if all(new[0] is old[0] and new[1] is old[1] for new, old in zip(items, pairs)):
                return value
            return dict(items)
        if isinstance(value, (list, tuple, set, frozenset)):
            members = list(value)
            masked_members = [_masked_value(member, depth + 1) for member in members]
            if all(new is old for new, old in zip(masked_members, members)):
                return value
            if isinstance(value, tuple):
                return tuple(masked_members)
            return masked_members
    masked = _masked_text(value)
    return value if masked is None else masked


def _guarded(value: object) -> object:
    try:
        return _masked_value(value)
    except Exception:
        return _MASK_ERROR


def mask_numbers_in_event(logger: object, method_name: str, event_dict: dict) -> dict:
    """Процессор structlog: новый словарь события, где номер в любом поле — маска."""
    return {_guarded(key): _guarded(value) for key, value in event_dict.items()}


def _masked_reprs(args: object) -> tuple:
    """Аргументы записи, чья подстановка упала, — маскированным текстом (отчёт `--- Logging error ---`)."""
    if not args:
        return ()
    if isinstance(args, tuple):
        return tuple(mask_numbers(repr(item)) for item in args)
    return (mask_numbers(repr(args)),)


def _mask_message(record: logging.LogRecord) -> None:
    try:
        rendered = record.getMessage()
    except Exception:
        record.msg = mask_numbers(str(record.msg))
        record.args = _masked_reprs(record.args)
        return
    if mask_numbers(rendered) == rendered:
        return
    if isinstance(record.args, tuple):
        record.args = tuple(mask_numbers(item) if isinstance(item, str) else item for item in record.args)
    if isinstance(record.msg, str):
        record.msg = mask_numbers(record.msg)
    try:
        again = record.getMessage()
    except Exception:
        again = None
    if again is None or mask_numbers(again) != again:
        record.msg = mask_numbers(rendered)
        record.args = ()


class NumberMaskingFilter(logging.Filter):
    """Фильтр stdlib: номер в сообщении, аргументах, тексте исключения и `stack_info` — маска.

    Всегда пропускает запись. Строковые аргументы маскируются на месте, прочие сохраняют тип
    (`%d` не ломается); если номер остался в тексте — запись несёт готовый маскированный текст.
    Запись structlog (словарь в `msg`) не трогается: её маскирует `mask_numbers_in_event`.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, dict):
                return True
            _mask_message(record)
            if record.exc_text:
                record.exc_text = mask_numbers(record.exc_text)
            elif record.exc_info:
                record.exc_text = mask_numbers(logging.Formatter().formatException(record.exc_info))
            if record.stack_info:
                record.stack_info = mask_numbers(record.stack_info)
        except Exception:
            record.msg = _MASK_ERROR
            record.args = ()
            record.exc_info = None
            record.exc_text = None
            record.stack_info = None
        return True


def attach_number_masking(handler: logging.Handler) -> None:
    """Поставить `NumberMaskingFilter` на обработчик, если его там ещё нет."""
    if not any(isinstance(existing, NumberMaskingFilter) for existing in handler.filters):
        handler.addFilter(NumberMaskingFilter())

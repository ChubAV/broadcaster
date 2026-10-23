"""Маска номера в выводе журнала: подстрока, которую нормализатор фазы признаёт номером, — `mask_phone`."""

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
            items = [(_masked_value(key, depth + 1), _masked_value(item, depth + 1)) for key, item in value.items()]
            if all(new_key is key and new_item is item for (new_key, new_item), (key, item) in zip(items, value.items())):
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

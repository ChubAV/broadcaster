"""Маска номера в выводе журнала — защита на исполнении (решение владельца О-23 (а), свойство 2).

ЗАЧЕМ. Статический гейт приватности (`tests/test_phone_privacy_gate.py`, D-17) судит исходник,
и обещанием «любое написание вызова журнала найдено» он не сходился: раунды 6–10 ревью находили
следующее написание динамического чтения (объект модуля `sys.modules[__name__]` под псевдонимом,
`importlib`, `operator.methodcaller` на носителе — CR-05, WR-32, WR-33), и номер печатался.
Решение владельца О-23 (а), 2026-10-22, свойство 2: номер, дошедший до вывода журнала любым
написанием, маскируется на исполнении формой `mask_phone` (D-10) в любом поле события.
Статический гейт приватности остаётся — в процессах с `setup_logging` это второй рубеж, в
процессах без неё (см. «ГРАНИЦА») — единственный; запрет динамических конструкций (планы 16-53,
16-54) держит то, что защита на исполнении не видит. D-11 для мест вызова не меняется: место
вызова номер в журнал не кладёт даже маской (только признак `phone_set`); маска здесь —
последний рубеж, а не разрешение. Партия раунда 11 — решение владельца О-25 (а), 2026-10-26
(свойства 1, 2, 3, 5, 6; планы 16-57, 16-60); договор раунда 12 — О-26 (а).

ЧТО «ПОХОЖЕ НА НОМЕР» — решение владельца О-24 (а), 2026-10-22: подстрока, которую нормализатор
фазы (`app/services/phone.py`) признаёт номером хотя бы одним путём: `normalize_reported` (с `+`
и без, Fragment `+888…` автопутём), `normalize_manual` (российская запись с `8`, разбивка
`+7 (999) 123-45-67`); сверх буквы — разбивка показа `format_phone` (`+888 0123 4567`: ручной
путь её отвергает по О-1, автопуть не читает разделителей, поэтому судят цифры разбивки с `+`;
это номер, который фаза выводит сама). Кандидатов дают две грамматики: цепочка `_DIGIT_RUN`
(7…15 цифр с необязательным `+`, не прилегающая слева к букве, цифре, `+`, `.`, `-` и справа к
букве, цифре, `-`, «`.` + цифра») и разбивка (начало `_SPACED_NUMBER_START` — `+цифра`,
`(цифры)` или `8` перед разделителем; дальше цифры, пробелы, `-` и скобки). У разбивки судятся
её префиксы по границам групп цифр от длинного к короткому, от 7 до 15 цифр: «номер и хвост»
(`+7 999 123-45-67 5`) маскирует номер. Судья — нормализатор, а не длина: вариант (б) «любые
11–15 цифр» ОТВЕРГНУТ ВЛАДЕЛЬЦЕМ. Непредвиденная ошибка разбора кандидата даёт маску (отказ в
закрытую), а не утечку.
СВЁРТКА (WR-39; О-25 (а), свойство 2): знаки, которые нормализатор читает внутри номера, а
грамматика нет, судятся свёрнутыми (`_NUMBER_FOLD`, знак в знак, маска — на исходных позициях):
18 разделителей — пробелы U+00A0 (NBSP), U+200B, U+2060, U+3000, тире U+00AD, U+2010,
U+2011 (неразрывный дефис), U+2012…U+2015, U+2053, U+2212, U+223C, U+30FC, U+FF0D, скобки
U+FF08, U+FF09; полноширинный плюс U+FF0B; цифры 67 блоков `Nd` (полноширинные, арабские и
прочие). Второй проход по свёрнутой копии идёт, только если в тексте есть такие знаки, и края
номера, найденного первым проходом, не меняет — поэтому номер, у которого голова до свёрнутого
знака сама признаётся номером, маскируется наполовину (`+49 30 123` + NBSP + `4567` →
`+49 ** *23 4567`; ревью WR-41, принятая граница, см. «ГРАНИЦА»). Правило
`test_every_character_the_normalizer_reads_in_a_number_is_folded_or_named` перебирает
U+0021…U+FFFF и все блоки `Nd` и держит таблицу в согласии с нормализатором.

ЧТО ВИДНО (замер О-24 (а)): ID групп Telegram `-100…` (поле `group_id` событий отправки; и без
знака, и с `+`), JID групп WhatsApp (`120363…@g.us`), метки времени (миллисекунды
`1729500000000`, `20261022063000`, строки ISO), UUID, адреса, десятичные дроби, ID малой группы
`-123456789` и уже наложенная маска — повторное наложение ничего не меняет.

СТОИМОСТЬ (CR-07; О-25 (а), свойство 3). Кандидат ограничен длиной номера: судятся префиксы
не длиннее `E164_MAX_DIGITS` (15) цифр, цифры считаются нарастающим итогом, конец цепочки
разбивки — один раз на поле; суд одного кандидата за вызов один (память судов), а судов
нормализатора на вызов `mask_numbers` — не больше `MASK_JUDGMENT_BUDGET` (64). Работа на поле
линейна по его длине. Замер исполнения 16-60 (2026-10-26): 8 000 знаков разбитого входа
(`"(1) " * 2000`, `"8 " * 4000`, `"(12)" * 2000`, пять случайных) — от 3 до 14 мс (лучшее из
трёх; прототип планирования — не больше 25 мс), путь запроса из 7 999 знаков через настоящий
`setup_logging` и `RequestIdMiddleware` — 20–30 мс (из 1 801 знака — 5–8 мс); правила
`test_a_long_split_field_is_masked_in_bounded_time` и
`test_a_long_split_request_path_is_logged_in_bounded_time` держат предел 0,25 с. Так закрыта
названная угроза — отказ в обслуживании веб-процесса без входа (T-16-137): путь запроса
попадает в событие `request` (`RequestIdMiddleware`) на каждом запросе, в том числе на 404. Летопись: до плана
16-60 кандидат был неограничен, стоимость — кубическая (`535c4f20`: 2,45 с на путь из 1 801
знака в цикле событий единственного uvicorn). Разделителей подряд — сколько угодно, как и до
плана: нормализатор читает `+7    999    123    45    67`, и маска его маскирует.

ЦЕНА — названная цена решения владельца О-24 (а), безвредная: цепочка 7–10 цифр, которую
автопуть читает номером, маскируется — `5123456789` → `+51 ******89` (Перу), `123456789` →
`+1 ******89`, `1234567` → `+1 ****67`, `4951234567` → `+49 **** **67`; так же секундная метка
времени из 10 цифр (`1729500000` читается номером зоны `+1`). Это лишняя маска на числе, а не
утечка номера. Вторая названная цена — отказ в закрытую сверх `MASK_JUDGMENT_BUDGET`: единица бюджета —
суд префикса разбивки, до 9 на одно начало, поэтому бюджет кончается уже на 9–19 фразах
разбивки (`(dd) d …`, `+d d d …`, `repr` списка) или на 63 цепочках цифр (замер ревью IN-27);
оставшиеся кандидаты получают `*` вместо цифр (`_closed_mask`; ID и метки в них тоже) — номер
не утекает, теряется только наблюдаемость такого поля (T-16-140).

ГДЕ СТОИТ. Веб-процесс: `create_app` → `setup_logging` (`app/logging_config.py`). Воркеры
Celery и `celery beat`: получатель `setup_celery_logging` сигнала
`celery.signals.setup_logging` (план 16-57) зовёт `setup_logging`, и Celery при нём корень не
захватывает; дочерние процессы пула prefork наследуют обработчик корня с маской. Правила —
`tests/test_worker/test_celery_log_mask.py`. Процессор `mask_numbers_in_event` — в цепочке
`ProcessorFormatter` корневого обработчика после `format_exc_info` и до рендерера: видит событие
structlog и запись stdlib с подставленными аргументами и текстом исключения и проходит любое
поле — строку, целое (номер-целое становится строкой маски, JSON остаётся разбираемым),
вложенные словари, списки, кортежи, множества (списком), `positional_args`, объект, чей `repr`
несёт номер. Фильтр `NumberMaskingFilter` — на корневом обработчике (флаг
`formatter_masks_event_dicts`: словарь события там маскирует процессор форматтера) и на
обработчиках журналов, существующих к вызову `setup_logging` (uvicorn: обработчики `uvicorn` и
`uvicorn.access` с `propagate=False` корня не достигают; словарь в `msg` любой записи там
маскирует фильтр — IN-25). Фильтр сохраняет типы аргументов `%`, при ошибке подстановки
маскирует текстом (отчёт `--- Logging error ---` печатает только маскированное), не поднимает
исключение и не роняет запись.

ГРАНИЦА, НАЗВАННАЯ ПРЯМО (чего защита на исполнении НЕ видит; по замеру):
* `print` и запись в `sys.stdout` / `sys.stderr` мимо журнала — их судит статический гейт
  приватности (D-17), а формы раунда 10 с `out = print` — запрет конструкции (планы 16-53,
  16-54); обёртка потоков процесса мешала бы захвату pytest и uvicorn и в свойство 2 не входит.
  В воркере Celery так же: при получателе `setup_logging` Celery `stdout` в журнал не
  перенаправляет;
* процессы, не вызывающие `setup_logging` (правило
  `test_the_processes_without_setup_logging_are_measured_and_named`): скрипты `scripts/`,
  Alembic (`alembic/env.py` — свой `fileConfig`), `celery flower` (свой журнал tornado),
  контейнеры `max_worker` (свой журнал) и `wa_worker` (Node) — там статический гейт
  приватности — единственный рубеж;
* обработчики, поставленные после вызова `setup_logging`, и журналы, настроенные мимо неё;
* строки `MASK_BOUNDARY_SUBSTRINGS`: номер, разбитый `.`, `/`, `[`, `]` (`+7.999.123.45.67`)
  или их полноширинными двойниками U+FF0E, U+FF0F, U+FF3B, U+FF3D, — нормализатор его читает,
  но это граница 16-52 (дроби, адреса, пути); номер, разбитый звёздами `*` (знак самой маски —
  свёртка сломала бы идемпотентность); номер, разбитый узким неразрывным пробелом U+202F или
  тонким пробелом U+2009, — нормализатор номером его не читает (замер), по О-24 (а) это не
  номер; номер, прилегающий к букве (`id79991234567`, `x+79991234567`), — край `_LEFT`;
  разбивка, чьё начало вне грамматики `_SPACED_NUMBER_START`: `8` перед `)`
  (`8)999)123)45)67`) и шесть цифр в скобках начала (`(999123) 45 67`), — нормализатор
  читает такие формы, а маска не маскировала их и до плана 16-60 (замер сверки «база ↔ HEAD»
  плана 16-60, семейство (b): 100 форм); расширение начала изменило бы ответ маски на ASCII;
* принятые границы ревью раунда 12 (О-26, финальный раунд; суд не расширен): знак в ОДНОЙ
  позиции номера — `~` (U+007E), `～` (U+FF5E) или буква (`+7~999 123 45 67`,
  `8 999 123x45 67`) — нормализатор отбрасывает, а маска не сворачивает, и номер печатается
  целиком (WR-42); номер, у которого голова до свёрнутого знака сама признаётся номером, —
  маска наполовину (WR-41, см. «СВЁРТКА»);
* отчёт `--- Logging error ---` о сбое самого конвейера события structlog на корневом
  обработчике (рендерер упал) печатает словарь события как есть: там фильтр словарь не трогает.
Летопись WR-39 и IN-25: до плана 16-60 граница называла краем только `+7.999.123.45.67` и
букву, а NBSP, U+2011 и полноширинные цифры нормализатор читал номером, маска — нет; словарь в
`msg` любой записи фильтр считал записью structlog и пропускал, и на обработчике uvicorn он
печатался с номером.
"""

import bisect
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

# Разбивка: начинается с `+цифры`, `(цифры)` или `8` перед разделителем (`_SPACED_NUMBER_START`);
# дальше — цепочка цифр и разделителей (пробел, `-`, скобки), кончается цифрой с краем `_RIGHT`.
#
# СТОИМОСТЬ (CR-07; решение владельца О-25 (а), свойство 3). До плана 16-60 кандидат был
# регулярным выражением без верхней границы (`[0-9 \-()]*[0-9]`): на `"(1) " * k` каждое начало
# тянуло кандидата до конца поля, а префиксы пересчитывали цифры заново — куб по длине поля
# (`535c4f20`: путь запроса из 1 801 знака — 2,45 с в цикле событий uvicorn). Теперь кандидат
# ограничен длиной номера: судятся только префиксы от `REPORTED_MIN_DIGITS` до `E164_MAX_DIGITS`
# цифр (длиннее судья не признаёт никогда — `_recognised`), конец цепочки и её последний
# допустимый край считаются один раз на поле, цифры префикса — нарастающим итогом по позициям
# цифр. Разделителей подряд — сколько угодно, как и до плана: нормализатор читает
# `+7    999    123    45    67`, и маска базы его маскировала (замер исполнения 16-60;
# предел «три разделителя» потерял бы эти номера). Работа на поле линейна по длине.
_SPACED_NUMBER_START = re.compile(_LEFT + r"(?:\+[0-9]|\([0-9]{1,5}\)|8(?=[ \-(]))")
_RIGHT_EDGE = re.compile(_RIGHT)

_SEPARATORS = " -()"
_SPLIT_CHARACTERS = frozenset("0123456789" + _SEPARATORS)
_CLOSED_EDGES = frozenset(" ()")
_CONTAINER_DEPTH = 16
_MASK_ERROR = "[number-mask-error]"

# Бюджет судов нормализатора на один вызов `mask_numbers` (CR-07; О-25 (а), свойство 3). Суд —
# разбор `phonenumbers` (до 0,3 мс с `mask_phone`); сверх бюджета новый кандидат маскируется без
# суда — каждая цифра `*` (`_closed_mask`, отказ в закрытую): номер не утекает, цена — звёзды на
# числах патологического поля с больше чем 64 разными кандидатами.
MASK_JUDGMENT_BUDGET: int = 64

_CLOSED_DIGITS = str.maketrans("0123456789", "**********")

# СВЁРТКА (WR-39; О-25 (а), свойство 2). Знаки, которые `normalize_manual` читает внутри номера,
# а грамматика маски — нет: замер исполнения 16-60 (2026-10-26, HEAD `14b8cfbe`, перебор
# U+0021…U+FFFF формой `+7{c}999{c}123{c}45{c}67` и всех блоков `Nd` формой `+` + цифры; правило
# `test_every_character_the_normalizer_reads_in_a_number_is_folded_or_named` держит таблицу в
# согласии с нормализатором — обновление `phonenumberslite` покраснит его). Маска судит копию,
# где эти знаки свёрнуты знак в знак (`str.translate`: позиции те же, NFKC менял бы длину), и
# кладёт маску на исходные позиции.
# НЕ свёрнуты: `.`, `/`, `[`, `]` и полноширинные U+FF0E, U+FF0F, U+FF3B, U+FF3D — граница 16-52
# (дроби, адреса, пути); `*` — знак самой маски (свёртка сломала бы идемпотентность); U+202F и
# U+2009 — нормализатор номером их не читает (замер), а по О-24 (а) «похоже на номер» судит он.
_FOLDED_DIGIT_ZEROS: tuple[int, ...] = (
    0x0660, 0x06F0, 0x07C0, 0x0966, 0x09E6, 0x0A66, 0x0AE6, 0x0B66, 0x0BE6, 0x0C66, 0x0CE6,
    0x0D66, 0x0DE6, 0x0E50, 0x0ED0, 0x0F20, 0x1040, 0x1090, 0x17E0, 0x1810, 0x1946, 0x19D0,
    0x1A80, 0x1A90, 0x1B50, 0x1BB0, 0x1C40, 0x1C50, 0xA620, 0xA8D0, 0xA900, 0xA9D0, 0xA9F0,
    0xAA50, 0xABF0, 0xFF10, 0x104A0, 0x10D30, 0x11066, 0x110F0, 0x11136, 0x111D0, 0x112F0,
    0x11450, 0x114D0, 0x11650, 0x116C0, 0x11730, 0x118E0, 0x11950, 0x11C50, 0x11D50, 0x11DA0,
    0x11F50, 0x16A60, 0x16AC0, 0x16B50, 0x1D7CE, 0x1D7D8, 0x1D7E2, 0x1D7EC, 0x1D7F6, 0x1E140,
    0x1E2F0, 0x1E4F0, 0x1E950, 0x1FBF0,
)
_FOLDED_SEPARATORS: dict[int, str] = {
    0x00A0: " ", 0x200B: " ", 0x2060: " ", 0x3000: " ",
    0x00AD: "-", 0x2010: "-", 0x2011: "-", 0x2012: "-", 0x2013: "-", 0x2014: "-", 0x2015: "-",
    0x2053: "-", 0x2212: "-", 0x223C: "-", 0x30FC: "-", 0xFF0D: "-",
    0xFF08: "(", 0xFF09: ")",
    0xFF0B: "+",
}
_NUMBER_FOLD: dict[int, str] = {
    **{zero + value: str(value) for zero in _FOLDED_DIGIT_ZEROS for value in range(10)},
    **_FOLDED_SEPARATORS,
}


def _digit_count(text: str) -> int:
    return sum(1 for ch in text if "0" <= ch <= "9")


def _closed_mask(text: str) -> str:
    """Отказ в закрытую сверх бюджета: каждая цифра ASCII — `*`, прочие знаки прежние."""
    return text.translate(_CLOSED_DIGITS)


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


class _Judgments:
    """Суды одного вызова `mask_numbers`: память «кандидат → маска или `None`» и бюджет.

    Суд (`_mask_of` → `_recognised`) вызывается только для нового кандидата и, пока бюджет не
    исчерпан, уменьшает его; сверх бюджета новый кандидат получает `_closed_mask` — отказ в
    закрытую. Память и бюджет общие у разбивки и у цепочки цифр одного вызова.
    """

    __slots__ = ("left", "seen")

    def __init__(self) -> None:
        self.seen: dict[str, str | None] = {}
        self.left = MASK_JUDGMENT_BUDGET

    def mask(self, candidate: str) -> str | None:
        if candidate in self.seen:
            return self.seen[candidate]
        if self.left > 0:
            self.left -= 1
            verdict = _mask_of(candidate)
        else:
            verdict = _closed_mask(candidate)
        self.seen[candidate] = verdict
        return verdict


def _last_edges(text: str) -> list[int]:
    """Для каждой позиции цепочки разбивки — последний допустимый конец кандидата в ней (или -1).

    Цепочка — непрерывный ряд цифр ASCII, пробелов, `-` и скобок. Допустимый конец — цифра,
    за которой пробел или скобка, либо последняя цифра цепочки, за которой выполняется `_RIGHT`.
    Жадный кандидат базы кончался ровно здесь; считается один раз на поле.
    """
    size = len(text)
    edges = [-1] * size
    index = 0
    while index < size:
        if text[index] not in _SPLIT_CHARACTERS:
            index += 1
            continue
        end = index
        while end < size and text[end] in _SPLIT_CHARACTERS:
            end += 1
        last = -1
        for position in range(end - 1, index - 1, -1):
            if not "0" <= text[position] <= "9":
                continue
            if position == end - 1:
                if _RIGHT_EDGE.match(text, end) is not None:
                    last = position
                    break
            elif text[position + 1] in _CLOSED_EDGES:
                last = position
                break
        for position in range(index, end):
            edges[position] = last
        index = end
    return edges


def _spaced_spans(text: str, judgments: _Judgments) -> list[tuple[int, int, str]]:
    """Спаны (начало, конец, маска) разбивок, признанных номером; поиск линеен по длине поля."""
    spans: list[tuple[int, int, str]] = []
    start = _SPACED_NUMBER_START.search(text)
    if start is None:
        return spans
    edges = _last_edges(text)
    digits = [index for index, ch in enumerate(text) if "0" <= ch <= "9"]
    while start is not None:
        begin, token_end = start.span()
        last = edges[token_end - 1]
        replaced_to = None
        if last >= token_end:
            # Цифры префикса — нарастающим итогом: `first` — первая цифра кандидата, префикс до
            # цифры `digits[k]` несёт `k - first + 1` цифр; от длинного к короткому, не длиннее
            # `E164_MAX_DIGITS` и не короче `REPORTED_MIN_DIGITS`.
            first = bisect.bisect_left(digits, begin)
            top = min(first + E164_MAX_DIGITS, bisect.bisect_right(digits, last)) - 1
            for k in range(top, first + REPORTED_MIN_DIGITS - 2, -1):
                position = digits[k]
                if position != last and text[position + 1] not in _SEPARATORS:
                    continue
                mask = judgments.mask(text[begin:position + 1])
                if mask is not None:
                    spans.append((begin, position + 1, mask))
                    replaced_to = position + 1
                    break
        start = _SPACED_NUMBER_START.search(text, begin + 1 if replaced_to is None else replaced_to)
    return spans


def _run_spans(text: str, judgments: _Judgments) -> list[tuple[int, int, str]]:
    """Спаны цепочек цифр (`_DIGIT_RUN`), признанных номером."""
    spans: list[tuple[int, int, str]] = []
    for match in _DIGIT_RUN.finditer(text):
        mask = judgments.mask(match.group())
        if mask is not None:
            spans.append((match.start(), match.end(), mask))
    return spans


def _apply_spans(text: str, spans: list[tuple[int, int, str]]) -> str:
    parts: list[str] = []
    position = 0
    for begin, end, mask in spans:
        parts.append(text[position:begin])
        parts.append(mask)
        position = end
    parts.append(text[position:])
    return "".join(parts)


def _mask_pass(text: str, view: str, judgments: _Judgments) -> str:
    """Кандидаты и суд — на `view` (та же длина, знак в знак), маска — на позициях `text`.

    Порядок прежний: сначала разбивка, затем цепочки цифр на тексте после первой стадии.
    """
    spaced = _spaced_spans(view, judgments)
    spaced_text = _apply_spans(text, spaced)
    spaced_view = _apply_spans(view, spaced)
    return _apply_spans(spaced_text, _run_spans(spaced_view, judgments))


def mask_numbers(text: str) -> str:
    """Текст, где каждая подстрока, признанная номером, заменена маской `mask_phone` (D-10).

    Первый проход судит текст как есть — ровно то, что маскировала маска до свёртки; второй —
    только если в тексте есть знаки `_NUMBER_FOLD`: судит свёрнутую копию и кладёт маску на
    исходные позиции. Так свёртка добавляет номера Юникода, но не меняет края (`_LEFT`,
    `_RIGHT`) номера, который первый проход уже нашёл. Судов нормализатора на вызов — не больше
    `MASK_JUDGMENT_BUDGET`, сверх — отказ в закрытую.
    """
    judgments = _Judgments()
    masked = _mask_pass(text, text, judgments)
    folded = masked.translate(_NUMBER_FOLD)
    if folded == masked:
        return masked
    return _mask_pass(masked, folded, judgments)


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
    Словарь в `msg` (событие structlog или словарь любой записи): на обработчике, чей форматтер
    маскирует словарь события сам (`formatter_masks_event_dicts=True` — корневой обработчик
    `setup_logging` с `mask_numbers_in_event`), запись не трогается; на прочих обработчиках
    (uvicorn: обычный `Formatter`) словарь заменяется маскированным (IN-25).
    """

    def __init__(self, *, formatter_masks_event_dicts: bool = False) -> None:
        super().__init__()
        self.formatter_masks_event_dicts = formatter_masks_event_dicts

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, dict):
                if self.formatter_masks_event_dicts:
                    return True
                record.msg = _guarded(record.msg)
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


def attach_number_masking(handler: logging.Handler, *, formatter_masks_event_dicts: bool = False) -> None:
    """Поставить `NumberMaskingFilter` на обработчик, если его там ещё нет."""
    if not any(isinstance(existing, NumberMaskingFilter) for existing in handler.filters):
        handler.addFilter(NumberMaskingFilter(formatter_masks_event_dicts=formatter_masks_event_dicts))

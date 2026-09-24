"""Фаза 15, FORM-01 (разметочная половина): инвентарь мест ПИСЬМА числом.

Требование FORM-01 говорит «пользователь выполняет любое действие письма без
перезагрузки страницы — все 47 форм идут через ``hx-post``». Его обработчиковая
половина уже закрыта (``NOT_YET_CONVERTED_COUNT = 0`` с тремя удерживающими
правилами); работы по переводу обработчиков в Фазе 15 нет. Этот файл закрывает
разметочную половину: СНИМАЕТ число мест письма прибором и объявляет его
литералом. «47 форм» и «27 файлов» — прогноз разведки от 2026-08-26, а не замер
(D-09), и число здесь двигается ЗАМЕРОМ, а не переопределением прибора.

ОПРЕДЕЛЕНИЕ ВСЕЛЕННОЙ — ПРЕЖДЕ ЧИСЛА, И ЭТО НЕСУЩЕЕ РЕШЕНИЕ ФАЙЛА.

* МЕСТО ФОРМЫ — либо вызов ``{% call form_wrapper(…) %}`` (макрос раздаёт тег
  ``<form method="post" … hx-post=…>`` по построению:
  ``components/form_wrapper.html``, ``{% macro %}`` на :187, тег на :188), либо
  сырой тег ``<form …>`` в исходнике шаблона ПОСЛЕ вырезания Jinja- и
  HTML-комментариев.
* МЕСТО ПИСЬМА — место формы, чей метод есть ЛИТЕРАЛЬНЫЙ ``post`` в исходнике
  шаблона. Регистр значения не различается (HTML его не различает): девять из
  восемнадцати Alpine-триггеров пишут ``method="POST"``. Вызов ``form_wrapper``
  место письма по построению макроса.
* ТЕЛО МАКРОСА ``form_wrapper`` — ПРОВАЙДЕР, А НЕ МЕСТО. Его тег считается
  каждым вызовом; посчитать ещё и тело значило бы учесть одну и ту же разметку
  дважды. Форма ``components/modal.html`` — наоборот МЕСТО: её вызовы местами
  не считаются (местами считаются восемнадцать форм-триггеров, открывающих
  панель), и единственная форма, реально несущая ``hx-post`` для этих действий,
  без неё выпала бы из учёта.
* ВНЕ КОНТРАКТА ПИСЬМА, поимённо и числом: GET-поиск ``ads/list.html:33`` (1
  место) и ``components/filters.html:31`` — форма, чей ``method`` приходит
  параметром макроса ``filters(id, action=None, method='get', …)`` (1 место).
  С ними всех мест формы 51 в 29 файлах.
* НЕ ФОРМА ВОВСЕ — тег ``<form id="ad-form">`` на ``ads/form.html:275``: он
  лежит внутри блока ``{#- … -#}`` (проза о снятой заботе о вложенной форме).
  Наивная сеть по сырому ``<form`` его считает; этот прибор — нет.

Под этим определением мест письма 49 в 27 файлах, и они делятся на три класса
как 29 / 18 / 2 (вызовы ``form_wrapper`` / сырой POST без ``hx-post`` — это
Alpine-триггеры модалки, по D-07 считающиеся переведёнными / сырой POST с
``hx-post`` — ``ads/form.html:149`` и ``components/modal.html:805``). Замер
2026-09-24 обходом с вырезанием комментариев и классификацией каждого места —
не вычитанием.

⚠️ КООРДИНАТЫ ДВУХ СЫРЫХ POST С ``hx-post`` — СТРОКА ОТКРЫТИЯ ТЕГА. У
``ads/form.html`` тег открывается на 149, атрибут ``hx-post`` стои́т на 152; у
``components/modal.html`` — 805 и 807. ``15-CONTEXT.md`` D-08 называет 149 и
805, план 15-02 — 152 для первой: обе записи верны, одна называет строку тега,
другая — строку атрибута. Расхождение названо, а не сглажено.

⚠️ 18 ТРИГГЕРОВ И ФОРМА МОДАЛКИ — РАЗДЕЛЬНЫЕ МЕСТА. Соблазн слить их (связка
же одна) дал бы 49 − 18 = 31 и переопределил бы вселенную задним числом. 18
считаются в своём классе, форма модалки — в своём. Отношение между ними
утверждает гейт связки плана 15-09, и оно НЕ есть слияние мест.

КЛЮЧ МЕСТА — ``путь#порядковый_номер``: путь относительно ``app/templates`` плюс
номер вхождения места формы в файле (по порядку в исходнике без комментариев;
порядок файлов — отсортированный обход ``_all_templates``). Ключ по ТЕКСТУ ТЕГА
ЗАПРЕЩЁН: ``accounts/list.html`` несёт три посимвольно одинаковых тега, и ключ
по тексту схлопнул бы их в одну запись — решение о втором и третьем не принимал
бы никто (идиома ``test_htmx_inventory.py``, ``_poll_fragments``).

ЛЕТОПИСЬ ЧИСЛА МЕСТ ПИСЬМА: 47 → 49 (Фаза 15, план 15-02, D-09). Прежнее
значение — 47 — было ПРОГНОЗОМ РАЗВЕДКИ от 2026-08-26 (``.planning/research/``,
коммит 73a42b54).
⚠️ ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ: на момент своей записи он был верным, и
правится не он, а числа, которые он пережил. Записи разведки
(``.planning/research/*``) НЕ ПРАВЯТСЯ.
Новое значение 49 снято ОБХОДОМ С ВЫРЕЗАНИЕМ КОММЕНТАРИЕВ И КЛАССИФИКАЦИЕЙ
каждого места, а не вычитанием, и несёт машинный гейт — этот файл. Текст
требований FORM-01 и QUAL-01 НЕ ПРАВИТСЯ ни на символ: решение владельца
``accept-override`` (``REQUIREMENTS.md:342``) оставляет Фазе 15 сверять формы по
прежней букве, и 47 → 49 записывается замером фазы, а не правкой требования.
ИСТОЧНИК +2. Разведка пометила его ``[ASSUMED]`` («планы 09–14 добавляли и
сливали места формы после записи прогноза»). Прогон
``git log -S '{% call form_wrapper' -- app/templates`` 2026-09-24 дал 21 коммит,
все после прогноза: 09-01, 11-01, 11-03, 11-04, 11-05, 11-10, 11-12, 11-13,
11-15, 11-16, 11-18, 12-01, 13-01, 13-02, 13-03, 14-01…14-06. Команда называет,
ГДЕ менялось число вызовов макроса, но не ЧЕМ: перевод сырой формы на макрос
число мест не меняет. Поэтому источник +2 ЭТОЙ КОМАНДОЙ ЗАМЕРОМ НЕ НАЗВАН.
Вторым замером тот же прибор прогнан по дереву шаблонов КАЖДОГО коммита,
касавшегося ``app/templates`` после 73a42b54 (``git archive`` в каталог вне
проекта, обход с параметром каталога). Результат:
  - на дереве прогноза прибор даёт 43 места письма в 24 файлах, а всех мест
    формы 46 в 27 файлах; наивная сеть ``grep -o '<form'`` на том же дереве
    даёт РОВНО 47 вхождений в 27 файлах (46 форм + одно упоминание в прозе
    комментария ``ads/form.html``). Прогноз, значит, считал СЫРЫЕ ВХОЖДЕНИЯ
    ``<form`` вместе с GET-формами, а не места письма;
  - рост мест письма тем же прибором 43 → 49 (+6): 10-09 (+1 — метод формы
    панели стал литералом ``post``, прежде он шёл параметром), 12-01 (+1),
    13-01 (+2), 13-02 (+1), 13-03 (+1); все остальные коммиты числа не
    двигали.
Число «+2» есть, таким образом, разность ДВУХ РАЗНЫХ СЕТЕЙ над двумя разными
деревьями, а не прирост одного множества: 47 — сеть сырых вхождений на дереве
2026-08-26, 49 — сеть мест письма на дереве 2026-09-24.

⚠️ ЛЕТОПИСИ «27 → 29» НЕТ — И ЭТО ЗАПИСАНО ОТДЕЛЬНОЙ СТРОКОЙ.
Под определением «место письма» файлов ровно 27, столько же, сколько объявил
прогноз. 29 получается только если включить GET-поиск и параметрический макрос фильтров,
то есть ровно то, что граница фазы исключает; летопись 27 → 29 записала бы
расхождение объявленного числа, которого нет, и превратила бы верный прогноз в
ошибку (идиома D-30/D-32 охраняет ровно от этого).
⚠️ ОГОВОРКА К ЭТОЙ СТРОКЕ, СНЯТАЯ ТЕМ ЖЕ ВТОРЫМ ЗАМЕРОМ. Совпадение 27 = 27 —
совпадение ЧИСЕЛ, а не множеств: 27 файлов прогноза — это файлы, несущие хоть
одно сырое ``<form`` на дереве 2026-08-26 (в той же сети мест письма их было
24), а 27 сегодня — файлы с местами письма (рост 24 → 27: 10-09, 12-01, 13-01).
В сети «все места формы» число файлов прошло 27 → 29 (12-01, 13-01). Эта
оговорка записью летописи НЕ является: объявленное число здесь — число файлов
мест ПИСЬМА, и его расхождения с прогнозом нет. Нужна ли отдельная запись по
сети «все места формы» — вопрос не прибора, а решения владельца, и он вынесен в
сводку плана 15-02, а не решён здесь молча.

ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ. Зелёный цвет здесь означает ровно одно: мест
письма 49 в 27 файлах, и они распределены по трём классам как 29 / 18 / 2. Он НЕ
означает, что хоть одно из 49 мест сработало на рантайме htmx 2.0.10: суита не
исполняет ни строчки JS и ни одной страницы не рендерит браузером. Он НЕ
означает, что связка 18 триггеров с формой модалки исправна — это отдельное
утверждение плана 15-09 в ``tests/test_templates/test_htmx_markup_gates.py``
(здесь утверждено лишь, что 18 триггеров СУЩЕСТВУЮТ, составляют свой класс
поимённо и открывают панель; перезамер их координат 2026-09-24 — все 18
совпали с D-08). ГРАНИЦА РАЗБОРЩИКА: форма, чей ``method`` приходит
параметром макроса, сети по литеральному ``post`` НЕ ВИДНА НИ В КАКОМ СЛУЧАЕ,
даже если вызывающий передаст ``method='post'``. Замер 2026-09-24,
``grep -rn 'filters(' app/templates/`` — 8 строк: определение макроса
(``components/filters.html:24``), пример вызова в его докстринге
(``components/filters.html:8``, внутри Jinja-комментария) и ШЕСТЬ вызывающих —
``account_groups/list.html:174``, ``schedules/list.html:34``,
``admin/user_history.html:28``, ``admin/users.html:60``, ``admin/logs.html:60``,
``history/list.html:74``. Ни один из шести ``method`` не переопределяет: все
получают GET по умолчанию макроса. Это замер, а не перенесённое допущение A2
разведки. Граница не только названа, но и ЗАКРЫТА правилами (приём второго
уровня, ниже в файле): форма с ``method`` из выражения в дереве ровно одна;
вызывающий ``filters`` с ``method=`` краснеет; вложенных форм нет.

Файл живёт в ``tests/test_templates/``: это гейт РАЗМЕТКИ, читающий исходники
шаблонов. Обход и вырезание комментариев ИМПОРТИРОВАНЫ из
``test_htmx_markup_gates.py``, а не написаны заново: каталог там принимается
параметром ровно затем, чтобы группа контроля могла подать ИЗМЕНЁННУЮ копию
дерева, и второй обход завёл бы второе определение «шаблона».
"""

import re
from enum import Enum
from typing import NamedTuple

from tests.test_templates.test_htmx_markup_gates import (
    ACTION_VALUE,
    HTML_COMMENT,
    HX_POST_ATTR,
    HX_POST_TAG,
    JINJA_COMMENT,
    METHOD_VALUE,
    Site,
    _all_templates,
    _attr_value,
    _attribute_count,
    _sites,
    _strip_comments,
)

# --- ОБЪЯВЛЕННЫЕ ЧИСЛА (замер 2026-09-24, план 15-02) ------------------------
#
# Выписаны ЗДЕСЬ, а не выведены из шаблонов: тест, считающий ожидание по коду в
# момент прогона, согласится с любой правкой и молча переживёт исчезновение
# места. Уменьшение допустимо и означает СОЗНАТЕЛЬНОЕ снятие места, записанное
# следующей записью летописи в докстринге модуля.

WRITE_FORM_PLACES = 49
WRITE_FORM_FILES = 27

FORM_WRAPPER_CALLS = 29
RAW_POST_WITHOUT_HX_POST = 18
RAW_POST_WITH_HX_POST = 2

ALL_FORM_PLACES = 51
ALL_FORM_FILES = 29

# Провайдер: тело макроса, чьи вызовы и есть места. Ровно один.
FORM_WRAPPER_PROVIDERS = 1

# Упоминаний ``<form`` в комментариях ``ads/form.html`` — одно (строка 275).
ADS_FORM_COMMENTED_FORM_TAGS = 1


class PlaceKind(Enum):
    """Класс места формы. Каждое место попадает РОВНО в один класс."""

    FORM_WRAPPER_CALL = "вызов form_wrapper"
    RAW_POST_WITHOUT_HX_POST = "сырой POST без hx-post"
    RAW_POST_WITH_HX_POST = "сырой POST с hx-post"
    GET_LITERAL = "сырой GET (вне контракта письма)"
    VARIABLE_METHOD = "method из выражения шаблонизатора (вне контракта письма)"


WRITE_KINDS = frozenset(
    {
        PlaceKind.FORM_WRAPPER_CALL,
        PlaceKind.RAW_POST_WITHOUT_HX_POST,
        PlaceKind.RAW_POST_WITH_HX_POST,
    }
)

DECLARED_BY_KIND: dict[PlaceKind, int] = {
    PlaceKind.FORM_WRAPPER_CALL: FORM_WRAPPER_CALLS,
    PlaceKind.RAW_POST_WITHOUT_HX_POST: RAW_POST_WITHOUT_HX_POST,
    PlaceKind.RAW_POST_WITH_HX_POST: RAW_POST_WITH_HX_POST,
}

# Изъятия из вселенной письма — ПОИМЁННО, ключом места. Новое место вне
# контракта письма, не названное здесь, краснеет: изъятие не выводится из
# класса, а объявляется.
WRITE_FORM_EXCLUSIONS: dict[str, str] = {
    "ads/list.html#0": "GET-поиск объявлений (method=\"get\" литералом)",
    "components/filters.html#0": (
        "форма макроса filters: method приходит параметром, по умолчанию 'get'"
    ),
}


# --- РЕГУЛЯРКИ ПРИБОРА -------------------------------------------------------

# Сырой тег формы. Просмотр вперёд отсекает имена, у которых ``form`` — лишь
# начало (``<formula>``); границы ``[^<>]`` — те же, что у тегов гейтов разметки.
FORM_TAG = re.compile(r"<form(?![-\w])[^<>]*>", re.IGNORECASE)

# Вызов макроса-обёртки блоком — с аргументами вызывающего (``call(x)``) и без.
FORM_WRAPPER_CALL = re.compile(
    r"\{%-?\s*call(?:\s*\([^()]*\))?\s+form_wrapper\s*\(.*?%\}", re.DOTALL
)

# Блок определения макроса-обёртки: тег внутри него — провайдер, не место.
FORM_WRAPPER_MACRO = re.compile(
    r"\{%-?\s*macro\s+form_wrapper\s*\(.*?\{%-?\s*endmacro\s*-?%\}", re.DOTALL
)

# Литеральный ``method="post"`` как атрибут — без разбора границ тега. Просмотр
# назад отсекает ``formmethod`` и ``data-method``.
METHOD_POST_ATTR = re.compile(r"(?<![-\w])method\s*=\s*(\"post\"|'post')", re.IGNORECASE)

# Наивная сеть: сырое вхождение ``<form`` без вырезания комментариев.
NAIVE_FORM = re.compile(r"<form(?![-\w])", re.IGNORECASE)


class WriteFormPlace(NamedTuple):
    """Место формы: ключ ``путь#порядковый_номер``, класс и текст несущей разметки.

    ``kind`` равен ``None`` у места, которое ни в один класс не попало, — такое
    место не теряется, а называется правилом полноты классификации.
    """

    key: str
    template: str
    ordinal: int
    kind: PlaceKind | None
    text: str


# --- ПРИБОР ------------------------------------------------------------------


def _template_sources() -> dict[str, str]:
    """Все шаблоны дерева СЛОВАРЁМ «путь → исходник».

    Форма заведена ради группы контроля: приняв исходники словарём, прибор
    получает ИЗМЕНЁННУЮ копию дерева и доказывает, что гейт краснеет, не тронув
    ни одного файла проекта. Порядок ключей — отсортированный обход
    ``_all_templates``.
    """
    return dict(_all_templates())


def _classify_form_place(tag: str) -> PlaceKind | None:
    """Класс СЫРОГО тега формы; ``None`` — ни один объявленный класс.

    Метод читается как СЫРОЕ значение атрибута: выражение шаблонизатора в нём —
    отдельный класс, а не догадка о том, во что оно вычислится. Тег без
    ``method`` и тег с методом, отличным от ``post``/``get``, не классифицируются
    — их называет правило полноты.
    """
    method = _attr_value(tag, METHOD_VALUE)
    if method is None:
        return None
    if "{{" in method or "{%" in method:
        return PlaceKind.VARIABLE_METHOD
    if method.strip().lower() == "get":
        return PlaceKind.GET_LITERAL
    if method.strip().lower() == "post":
        if HX_POST_ATTR.search(tag):
            return PlaceKind.RAW_POST_WITH_HX_POST
        return PlaceKind.RAW_POST_WITHOUT_HX_POST
    return None


def _form_places(sources: dict[str, str]) -> list[WriteFormPlace]:
    """Все места формы дерева — письма и изъятия, без провайдера.

    Исходник каждого шаблона читается БЕЗ комментариев (``_strip_comments``:
    сначала Jinja, потом HTML). Места файла — вызовы ``form_wrapper`` и сырые
    теги формы — упорядочены по позиции в этом исходнике, и порядковый номер
    идёт сквозной по обоим видам. Тег, лежащий внутри блока определения
    ``form_wrapper``, — провайдер: номера он не получает.
    """
    found: list[WriteFormPlace] = []
    for rel, source in sources.items():
        body = _strip_comments(source)
        provider_spans = [m.span() for m in FORM_WRAPPER_MACRO.finditer(body)]
        events: list[tuple[int, PlaceKind | None, str]] = []
        for match in FORM_WRAPPER_CALL.finditer(body):
            events.append((match.start(), PlaceKind.FORM_WRAPPER_CALL, match.group(0)))
        for match in FORM_TAG.finditer(body):
            if any(start <= match.start() < end for start, end in provider_spans):
                continue
            tag = match.group(0)
            events.append((match.start(), _classify_form_place(tag), tag))
        events.sort(key=lambda event: event[0])
        for ordinal, (_, kind, text) in enumerate(events):
            found.append(WriteFormPlace(f"{rel}#{ordinal}", rel, ordinal, kind, text))
    return found


def _write_form_places(sources: dict[str, str]) -> list[WriteFormPlace]:
    """Места ПИСЬМА: места формы классов ``WRITE_KINDS``."""
    return [place for place in _form_places(sources) if place.kind in WRITE_KINDS]


def _provider_tags(sources: dict[str, str]) -> list[Site]:
    """Теги формы, лежащие в теле макроса ``form_wrapper``."""
    found: list[Site] = []
    for rel, source in sources.items():
        for macro in FORM_WRAPPER_MACRO.finditer(_strip_comments(source)):
            found.extend(Site(rel, tag) for tag in FORM_TAG.findall(macro.group(0)))
    return found


def _inventory_offence(declared: int, measured: int) -> str:
    """Пустая строка, если замеренное равно объявленному; иначе текст нарушения.

    Чистая функция: два числа на входе, строка на выходе (форма
    ``_ceiling_offence`` из ``test_htmx_inventory.py``). Два направления
    расхождения называются РАЗНЫМИ утверждениями: рост — утверждением «не
    выросло» (новое место прошло мимо объявления); падение — утверждением
    РАВЕНСТВА (место исчезло молча, а «не выросло» на него законно молчит).
    Правило, краснеющее только вверх, пережило бы исчезновение места.
    """
    if measured > declared:
        return (
            f"ЧИСЛО ВЫРОСЛО: замерено {measured}, объявлено {declared} — новое "
            f"место письма прошло мимо объявления"
        )
    if measured < declared:
        return (
            f"РАВЕНСТВО НАРУШЕНО ПАДЕНИЕМ: замерено {measured}, объявлено "
            f"{declared} — место письма исчезло молча"
        )
    return ""


# --- УТВЕРЖДЕНИЯ: ИНВЕНТАРЬ ---------------------------------------------------


def test_write_form_places_equal_the_declared_number() -> None:
    """Мест письма ровно ``WRITE_FORM_PLACES`` — равенство, а не порог."""
    found = _write_form_places(_template_sources())

    assert len(found) == WRITE_FORM_PLACES, (
        f"мест письма {len(found)}, объявлено {WRITE_FORM_PLACES}: "
        f"{_inventory_offence(WRITE_FORM_PLACES, len(found))}"
    )


def test_write_form_files_equal_the_declared_number() -> None:
    """Файлов, несущих хоть одно место письма, ровно ``WRITE_FORM_FILES``."""
    files = {place.template for place in _write_form_places(_template_sources())}

    assert len(files) == WRITE_FORM_FILES, (
        f"файлов с местами письма {len(files)}, объявлено {WRITE_FORM_FILES}: "
        f"{sorted(files)}"
    )


def test_write_form_places_split_by_kind_as_declared() -> None:
    """Разбивка 29 / 18 / 2 — и её сумма, ВТОРОЙ счёт того же множества."""
    found = _write_form_places(_template_sources())
    by_kind = {kind: sum(1 for p in found if p.kind is kind) for kind in DECLARED_BY_KIND}

    assert by_kind == DECLARED_BY_KIND, (
        f"разбивка по классам разошлась с объявленной: найдено "
        f"{ {k.value: v for k, v in by_kind.items()} }, объявлено "
        f"{ {k.value: v for k, v in DECLARED_BY_KIND.items()} }"
    )
    assert FORM_WRAPPER_CALLS + RAW_POST_WITHOUT_HX_POST + RAW_POST_WITH_HX_POST == WRITE_FORM_PLACES, (
        "сумма объявленных классов не равна объявленному числу мест письма — "
        "литералы разошлись между собой"
    )
    assert sum(by_kind.values()) == len(found), (
        "место письма вне трёх классов письма — счёт по классам и счёт мест "
        "разошлись"
    )


def test_every_form_place_is_classified_exactly_once() -> None:
    """Полнота классификации: место без класса КРАСНЕЕТ и НАЗЫВАЕТСЯ.

    Класс места — одно значение ``PlaceKind``, так что «ровно один» здесь
    держится типом; утверждается, что ``None`` не выпал ни одному месту.
    """
    unclassified = [
        f"{p.key}: {p.text[:120]!r}" for p in _form_places(_template_sources()) if p.kind is None
    ]

    assert unclassified == [], (
        "место формы вне всех объявленных классов — вселенная письма не знает, "
        f"что это: {unclassified}"
    )


def test_exclusions_from_the_write_universe_are_named_one_by_one() -> None:
    """Изъятия названы поимённо, и с ними всех мест формы 51 в 29 файлах."""
    places = _form_places(_template_sources())
    excluded = {p.key: p.kind for p in places if p.kind not in WRITE_KINDS}

    assert set(excluded) == set(WRITE_FORM_EXCLUSIONS), (
        "места вне контракта письма разошлись с объявленными изъятиями: "
        f"найдено {sorted(excluded)}, объявлено {sorted(WRITE_FORM_EXCLUSIONS)}"
    )
    assert excluded.get("ads/list.html#0") is PlaceKind.GET_LITERAL
    assert excluded.get("components/filters.html#0") is PlaceKind.VARIABLE_METHOD
    assert len(places) == ALL_FORM_PLACES, (
        f"всех мест формы {len(places)}, объявлено {ALL_FORM_PLACES}"
    )
    assert len({p.template for p in places}) == ALL_FORM_FILES, (
        f"файлов с местами формы {len({p.template for p in places})}, "
        f"объявлено {ALL_FORM_FILES}"
    )
    assert ALL_FORM_PLACES == WRITE_FORM_PLACES + len(WRITE_FORM_EXCLUSIONS)


def test_the_form_wrapper_macro_body_is_a_provider_not_a_place() -> None:
    """Тело макроса исключено ОТДЕЛЬНЫМ правилом, а не совпадением.

    Провайдер несёт ``method="post"`` и ``hx-post`` — то есть без изъятия он
    сам попал бы в класс «сырой POST с ``hx-post``», и класс дал бы 3 вместо 2.
    Утверждается и то, что он ЕСТЬ (иначе изъятие было бы пустым), и то, что
    ни одно место не лежит в его файле.
    """
    sources = _template_sources()
    providers = _provider_tags(sources)

    assert len(providers) == FORM_WRAPPER_PROVIDERS, (
        f"тегов формы в теле макроса form_wrapper {len(providers)}, объявлено "
        f"{FORM_WRAPPER_PROVIDERS}"
    )
    assert providers[0].template == "components/form_wrapper.html"
    assert _classify_form_place(providers[0].tag) is PlaceKind.RAW_POST_WITH_HX_POST, (
        "провайдер перестал выглядеть как сырой POST с hx-post — изъятие стало "
        "совпадением, а не решением"
    )
    assert not [p for p in _form_places(sources) if p.template == "components/form_wrapper.html"], (
        "в файле провайдера нашлось место формы — тело макроса посчитано местом"
    )


def test_a_form_inside_a_jinja_comment_is_not_counted() -> None:
    """``ads/form.html`` даёт по сырым тегам на одно место МЕНЬШЕ наивной сети.

    Наивная сеть по сырому ``<form`` без вырезания комментариев считает и
    ``<form id="ad-form">`` на строке 275 — внутри ``{#- … -#}``.
    """
    key = "ads/form.html"
    source = _template_sources()[key]
    raw_tag_places = [
        p
        for p in _form_places({key: source})
        if p.kind is not PlaceKind.FORM_WRAPPER_CALL
    ]
    naive = len(NAIVE_FORM.findall(source))

    assert naive - len(raw_tag_places) == ADS_FORM_COMMENTED_FORM_TAGS, (
        f"наивная сеть {naive}, мест по сырым тегам {len(raw_tag_places)}: "
        f"разность {naive - len(raw_tag_places)}, объявлена "
        f"{ADS_FORM_COMMENTED_FORM_TAGS}"
    )
    assert len(NAIVE_FORM.findall(_strip_comments(source))) == len(raw_tag_places), (
        "разность не объясняется комментариями: без них наивная сеть и прибор "
        "обязаны совпасть"
    )
    assert len(NAIVE_FORM.findall(JINJA_COMMENT.sub("", source))) == len(raw_tag_places), (
        "упоминание формы лежит не в Jinja-комментарии"
    )
    assert len(NAIVE_FORM.findall(HTML_COMMENT.sub("", source))) == naive, (
        "упоминание формы снимается HTML-комментарием — порядок вырезания "
        "перестал быть значимым для этого файла"
    )


def test_two_paths_agree_on_the_tags_the_parser_found() -> None:
    """Две величины РАЗНЫМИ путями из одного источника без комментариев.

    Путь А — разбор границ тега (``_sites``); путь Б — счёт вхождений атрибута
    без разбора тегов (``_attribute_count``). Их расхождение означает ОШИБКУ
    РАЗБОРА ГРАНИЦ ТЕГА, а не пропажу разметки. Их согласие при отличии от
    объявленного — уже другое событие: изменилось само число носителей.

    Сверяются две величины: теги формы с литеральным ``method="post"`` (20 мест
    сырого POST и провайдер) и носители ``hx-post`` (2 места и провайдер —
    других носителей ``hx-post`` в дереве нет, замер 2026-09-24).
    """
    templates = list(_template_sources().items())
    declared_post = RAW_POST_WITHOUT_HX_POST + RAW_POST_WITH_HX_POST + FORM_WRAPPER_PROVIDERS
    declared_hx_post = RAW_POST_WITH_HX_POST + FORM_WRAPPER_PROVIDERS

    parsed_post = [s for s in _sites(templates, FORM_TAG) if METHOD_POST_ATTR.search(s.tag)]
    counted_post = _attribute_count(templates, METHOD_POST_ATTR)
    assert len(parsed_post) == counted_post, (
        f"ОШИБКА РАЗБОРА ГРАНИЦ ТЕГА: тегов формы с method=post {len(parsed_post)}, "
        f"вхождений атрибута {counted_post}"
    )
    assert counted_post == declared_post, (
        f"носителей литерального method=post {counted_post}, объявлено {declared_post}"
    )

    parsed_hx = _sites(templates, HX_POST_TAG)
    counted_hx = _attribute_count(templates, HX_POST_ATTR)
    assert len(parsed_hx) == counted_hx, (
        f"ОШИБКА РАЗБОРА ГРАНИЦ ТЕГА: тегов с hx-post {len(parsed_hx)}, "
        f"вхождений атрибута {counted_hx}"
    )
    assert counted_hx == declared_hx_post, (
        f"носителей hx-post {counted_hx}, объявлено {declared_hx_post}"
    )
    assert len([s for s in parsed_post if HX_POST_ATTR.search(s.tag)]) == declared_hx_post, (
        "носитель hx-post оказался не формой с method=post"
    )


def test_place_keys_are_path_and_ordinal_and_never_collapse() -> None:
    """Ключ ``путь#индекс``: два места одного файла — два ключа.

    ``accounts/list.html`` несёт три посимвольно одинаковых тега сырого POST
    (плюс один вызов ``form_wrapper``); ключ по тексту схлопнул бы три в один.
    """
    places = _form_places(_template_sources())
    keys = [p.key for p in places]

    assert len(set(keys)) == len(places), "два места схлопнулись в один ключ"
    assert all(p.key == f"{p.template}#{p.ordinal}" for p in places)

    same_file = [
        p
        for p in places
        if p.template == "accounts/list.html" and p.kind is PlaceKind.RAW_POST_WITHOUT_HX_POST
    ]
    assert len(same_file) == 3, (
        f"сырых POST без hx-post в accounts/list.html {len(same_file)}, ожидалось 3"
    )
    assert len({p.text for p in same_file}) == 1, (
        "три места accounts/list.html перестали совпадать посимвольно — "
        "довод о ключе по тексту здесь больше не показан"
    )
    assert len({p.key for p in same_file}) == 3


# --- ГРУППА КОНТРОЛЯ: ЧИСЛА, ДОКАЗАННЫЕ ОТ ВАКУУМА ----------------------------
#
# Контроли ПОДМЕНЯЮТ СЛОВАРЬ ИСХОДНИКОВ, А НЕ ФАЙЛОВУЮ СИСТЕМУ: ни один файл
# проекта не трогается и временный каталог не заводится. Это несущее решение
# формы (образец — tests/test_templates/test_htmx_inventory.py, группа
# контроля над ``_template_sources()``): файловые операции там, где их нет,
# увели бы форму контроля от той, которую дерево уже проверило.
#
# ⚠️ ДОКАЗАТЕЛЬСТВО СОСТОИТ ИЗ ДВУХ ПОЛОВИН, И ОБЕ СНИМАЮТСЯ ТЕМ ЖЕ ПРОГОНОМ,
# ЧТО И САМИ ЧИСЛА. Половина А: вселенная обхода НЕПУСТА — шаблоны находятся, и
# на неизменённом дереве все утверждения молчат. Половина Б: на дереве, где
# искомому ЕСТЬ ЧТО НАЙТИ (пятидесятое место, снятый вызов, форма в
# комментарии), то же выражение его находит и НАЗЫВАЕТ. Число, у которого зелены
# обе половины, есть исполненная работа; число, у которого красна любая из них,
# есть поломка измерителя.
#
# ⚠️ КОНТРОЛИ РАВЕНСТВА КРАСНЕЮТ В РАЗНЫЕ СТОРОНЫ, И РАЗЛИЧИЕ УТВЕРЖДАЕТСЯ:
# рост реддит утверждение роста, падение — утверждение равенства. Правило,
# краснеющее только вверх, молча переживёт исчезновение места — ровно тот
# отказ, ради которого инвентарные гейты в проекте и заведены.

SYNTHETIC_WRITE_FORM = (
    '<form method="post" action="/synthetic/one-more-write" '
    'hx-post="/synthetic/one-more-write" hx-swap="none"></form>\n'
)


def test_control_negative_a_fiftieth_write_place_reddens_the_growth_gate() -> None:
    """ЧТО ДОКАЗЫВАЕТ: пятидесятое место письма обход ВИДИТ, и «не выросло» краснеет."""
    key = "synthetic/one_more_write_form.html"
    sources = _template_sources()
    assert key not in sources, "синтетический шаблон совпал по имени с настоящим"

    changed = dict(sources)
    changed[key] = SYNTHETIC_WRITE_FORM
    assert changed != sources, "подмена ничего не изменила"

    found = _write_form_places(changed)

    assert len(found) == WRITE_FORM_PLACES + 1, (
        f"ПЯТИДЕСЯТОЕ МЕСТО ПИСЬМА ПРОШЛО МИМО ОБХОДА: найдено {len(found)}, "
        f"ожидалось {WRITE_FORM_PLACES + 1}"
    )
    assert not (len(found) <= WRITE_FORM_PLACES), (
        "утверждение «не выросло» осталось истинным при выросшем числе — "
        "счётчик зелен по построению"
    )
    assert "ВЫРОСЛО" in _inventory_offence(WRITE_FORM_PLACES, len(found)), (
        "рост назван не утверждением роста"
    )


def test_control_negative_a_removed_form_wrapper_call_reddens_the_equality_gate() -> None:
    """ЧТО ДОКАЗЫВАЕТ: СНЯТЫЙ вызов ``form_wrapper`` замечает равенство, а не рост.

    ⚠️ ЭТО И ЕСТЬ ПРИЧИНА, ПО КОТОРОЙ УТВЕРЖДЕНИЙ ДВА. Упавшее число «не
    выросло» пропускает совершенно правильно; молчали бы оба — счётчик описывал
    бы прошлое состояние сколько угодно долго.
    """
    sources = _template_sources()
    first_call = next(
        p for p in _write_form_places(sources) if p.kind is PlaceKind.FORM_WRAPPER_CALL
    )
    key = first_call.template

    changed = dict(sources)
    changed[key] = sources[key].replace(
        first_call.text, first_call.text.replace("form_wrapper", "not_a_form_wrapper", 1), 1
    )
    assert changed[key] != sources[key], "подмена ничего не изменила"

    found = _write_form_places(changed)

    assert len(found) == WRITE_FORM_PLACES - 1, (
        f"снятый вызов не изменил счёта: найдено {len(found)}, ожидалось "
        f"{WRITE_FORM_PLACES - 1}"
    )
    assert len(found) <= WRITE_FORM_PLACES, (
        "утверждение «не выросло» покраснело на УПАВШЕМ числе"
    )
    assert len(found) != WRITE_FORM_PLACES, (
        "УТВЕРЖДЕНИЕ О РАВЕНСТВЕ ОСТАЛОСЬ ИСТИННЫМ ПРИ УПАВШЕМ ЧИСЛЕ — место "
        "исчезло молча"
    )
    offence = _inventory_offence(WRITE_FORM_PLACES, len(found))
    assert "РАВЕНСТВ" in offence and "ВЫРОСЛО" not in offence, (
        f"падение названо не утверждением равенства: {offence!r}"
    )


def test_control_negative_a_form_inside_a_comment_adds_no_place() -> None:
    """ЧТО ДОКАЗЫВАЕТ: форма в Jinja-комментарии мест НЕ добавляет, а наивная сеть — добавляет."""
    key = "synthetic/commented_write_form.html"
    sources = _template_sources()
    assert key not in sources, "синтетический шаблон совпал по имени с настоящим"

    commented = "{#- " + SYNTHETIC_WRITE_FORM.strip() + " -#}\n"
    changed = dict(sources)
    changed[key] = commented
    assert changed != sources, "подмена ничего не изменила"

    stripped_places = len(_form_places({key: commented}))
    naive = len(NAIVE_FORM.findall(commented))

    assert stripped_places == 0, (
        f"форма в комментарии посчитана местом: {stripped_places}"
    )
    assert naive == 1, f"наивная сеть не увидела формы в комментарии: {naive}"
    assert naive - stripped_places == 1
    assert len(_write_form_places(changed)) == WRITE_FORM_PLACES, (
        "форма в комментарии сдвинула число мест письма дерева"
    )


def test_control_negative_an_empty_source_map_reddens_the_nonzero_declaration() -> None:
    """ЧТО ДОКАЗЫВАЕТ: на пустом словаре ненулевое объявление КРАСНЕЕТ, а прибор не падает."""
    found = _write_form_places({})

    assert found == [], "обход нашёл место письма там, где нет ни одного шаблона"
    assert not (len(found) > 0), "пустое дерево дало непустой обход"
    assert _inventory_offence(WRITE_FORM_PLACES, len(found)) != "", (
        "ОБЪЯВЛЕННЫЕ 49 СОШЛИСЬ С ПУСТОТОЙ — утверждение о числе зеленеет вакуумом"
    )
    assert _form_places({}) == [] and _provider_tags({}) == []


def test_control_positive_the_untouched_tree_keeps_every_inventory_gate_green() -> None:
    """ЧТО ДОКАЗЫВАЕТ: на НЕИЗМЕНЁННОМ дереве все утверждения молчат, и обход НЕ ПУСТ.

    ⚠️ БЕЗ ЭТОГО КОНТРОЛЯ ОТРИЦАТЕЛЬНЫЕ ВЫШЕ ПРОШЛИ БЫ И У ГЕЙТА, КОТОРЫЙ
    КРАСНЕЕТ ВСЕГДА. Это половина А доказательства: классификация, сошедшаяся
    потому, что обход не нашёл ни одного файла, неотличима от сошедшейся по
    существу.
    """
    sources = _template_sources()

    assert len(sources) > 50, (
        f"обход нашёл всего {len(sources)} шаблонов — группы могли сойтись на пустоте"
    )
    places = _form_places(sources)
    write = _write_form_places(sources)
    assert _inventory_offence(WRITE_FORM_PLACES, len(write)) == ""
    assert _inventory_offence(ALL_FORM_PLACES, len(places)) == ""
    assert [p for p in places if p.kind is None] == []
    assert {p.key for p in places if p.kind not in WRITE_KINDS} == set(WRITE_FORM_EXCLUSIONS)


def test_control_negative_the_declaration_not_the_fact_reddens_in_both_directions() -> None:
    """ЧТО ДОКАЗЫВАЕТ: чистая функция сравнения краснеет в ОБЕ стороны и РАЗНЫМИ текстами.

    Контроли выше доказывают, что гейт видит изменение ФАКТА на дереве. Этот
    доказывает то же на самой функции сравнения, без дерева: замер на единицу
    больше объявления краснеет утверждением роста, равный молчит, на единицу
    меньше — краснеет утверждением РАВЕНСТВА, а не роста.
    """
    declared = WRITE_FORM_PLACES

    up = _inventory_offence(declared, declared + 1)
    same = _inventory_offence(declared, declared)
    down = _inventory_offence(declared, declared - 1)

    assert up != "", "ВЫРОСШИЙ ЗАМЕР ПРОШЁЛ МИМО ФУНКЦИИ СРАВНЕНИЯ"
    assert same == "", "функция сравнения покраснела на равенстве"
    assert down != "", "УПАВШИЙ ЗАМЕР ПРОШЁЛ МИМО ФУНКЦИИ СРАВНЕНИЯ — место исчезло бы молча"
    assert "ВЫРОСЛО" in up, f"рост назван не утверждением роста: {up!r}"
    assert "РАВЕНСТВ" in down and "ВЫРОСЛО" not in down, (
        f"падение названо утверждением роста, а не равенства: {down!r}"
    )
    assert up != down, "два направления расхождения неразличимы по тексту"


# --- ПЕРЕЧЕНЬ 18 ALPINE-ТРИГГЕРОВ ПОИМЁННО ----------------------------------
#
# Класс «сырой POST без ``hx-post``» выписан ЛИТЕРАЛОМ: ключ места → основание
# (какое действие письма форма запускает). Действие каждой формы идёт через
# htmx формой панели подтверждения ``components/modal.html:805`` (D-07); сама
# форма-триггер отправку перехватывает (``x-on:submit.prevent``) и открывает
# панель событием ``modal-open-…``.
#
# ⚠️ ГРАНИЦА, ПЕРЕДАВАЕМАЯ ПЛАНУ 15-09, НАЗЫВАЕТСЯ ЗДЕСЬ ПРЯМО. Этот файл
# утверждает, что 18 триггеров СУЩЕСТВУЮТ, составляют свой класс и открывают
# панель. Он НЕ утверждает, что submit каждого из них действительно доезжает до
# формы модалки с ``hx-post``: это связка двух узлов, её утверждает план 15-09 в
# ``tests/test_templates/test_htmx_markup_gates.py`` независимыми счётами по
# форме ``test_modal_site_inventory`` (``tests/test_templates/test_components.py``).
#
# ПЕРЕЗАМЕР КООРДИНАТ 2026-09-24. Строки открытия 18 тегов сняты обходом и
# сверены с ``15-CONTEXT.md`` D-08: ВСЕ 18 СОВПАЛИ С D-08 (group_row 234;
# accounts/list 105, 136, 169; partial_cards 60, 90, 119; sync_status_card 89,
# 112, 128; queue_row 87; user_actions 98, 109; worker_row 108; ads/form 416;
# ad_card 116; sched_card 309; history_card 162). Летописи сдвига нет — сдвига
# нет. Координаты строк в гейт НЕ вписаны: ключ места — порядковый номер, и
# правка текста выше формы гейт не роняет.
#
# Основание несёт статический скелет адреса действия (``{…}`` — выражение
# шаблонизатора), и он СВЕРЯЕТСЯ с атрибутом ``action`` тега: основание, не
# совпавшее с формой, краснеет, а не живёт отдельно от разметки.

ALPINE_TRIGGER_PLACES: dict[str, str] = {
    "account_groups/includes/group_row.html#1": (
        "удаление группы из аккаунта — POST /accounts/{id}/groups/{gid}/delete"
    ),
    "accounts/list.html#0": (
        "удаление аккаунта, карточка «синхронизация» — POST /accounts/{id}/delete"
    ),
    "accounts/list.html#2": (
        "удаление аккаунта, карточка «синхронизация не удалась» — POST /accounts/{id}/delete"
    ),
    "accounts/list.html#3": (
        "удаление аккаунта, карточка прочих состояний — POST /accounts/{id}/delete"
    ),
    "accounts/partial_cards.html#0": (
        "удаление аккаунта из порции подгрузки, «синхронизация» — POST /accounts/{id}/delete"
    ),
    "accounts/partial_cards.html#2": (
        "удаление аккаунта из порции подгрузки, «синхронизация не удалась» — "
        "POST /accounts/{id}/delete"
    ),
    "accounts/partial_cards.html#3": (
        "удаление аккаунта из порции подгрузки, прочие состояния — POST /accounts/{id}/delete"
    ),
    "accounts/partials/sync_status_card.html#0": (
        "удаление аккаунта из опрашиваемой карточки, «активен» — POST /accounts/{id}/delete"
    ),
    "accounts/partials/sync_status_card.html#2": (
        "удаление аккаунта из опрашиваемой карточки, «синхронизация не удалась» — "
        "POST /accounts/{id}/delete"
    ),
    "accounts/partials/sync_status_card.html#3": (
        "удаление аккаунта из опрашиваемой карточки, «синхронизация» — POST /accounts/{id}/delete"
    ),
    "admin/includes/queue_row.html#0": (
        "сброс очереди отправки аккаунта — POST /admin/queue/{id}/drop"
    ),
    "admin/includes/user_actions.html#2": (
        "вход под личностью пользователя — POST /admin/users/{id}/impersonate"
    ),
    "admin/includes/user_actions.html#3": (
        "удаление пользователя — POST /admin/users/{id}/delete"
    ),
    "admin/includes/worker_row.html#0": (
        "перезапуск воркера аккаунта — POST /admin/workers/{id}/restart"
    ),
    "ads/form.html#2": "удаление объявления из редактора — POST /ads/{id}/delete",
    "ads/includes/ad_card.html#0": (
        "удаление объявления из карточки списка — POST /ads/{id}/delete"
    ),
    "ads/includes/sched_card.html#2": (
        "удаление расписания из карточки редактора — POST /schedules/{id}/delete"
    ),
    "history/includes/history_card.html#0": (
        "повтор неудавшейся отправки из истории — POST /history/{id}/retry"
    ),
}

# ⚠️ ЧИСЛО ВЫПИСАНО ОТДЕЛЬНОЙ КОНСТАНТОЙ НАМЕРЕННО (идиома SP-1): перечень,
# опустевший молча, оставил бы правило зелёным ровно тогда, когда триггеров не
# стало, — и неотличимым от перечня, чьи записи тихо отменили.
#
# ЛЕТОПИСЬ: 18, Фаза 15, план 15-02 — снято ОБХОДОМ (класс «сырой POST без
# ``hx-post``»), совпало с D-08 поимённо.
ALPINE_TRIGGER_PLACES_DECLARED = 18

MODAL_OPEN_DISPATCH = re.compile(r"x-on:submit(?:\.[\w.]+)?\s*=\s*\"[^\"]*\$dispatch\('modal-open-")
JINJA_EXPRESSION = re.compile(r"\{\{.*?\}\}", re.DOTALL)
BASIS_PLACEHOLDER = re.compile(r"\{[^{}]*\}")
BASIS_PATH = re.compile(r"POST (\S+)")


def _action_skeleton(action: str) -> str:
    """Адрес действия без выражений шаблонизатора: ``/ads/{{ ad.id }}/delete`` → ``/ads//delete``."""
    return JINJA_EXPRESSION.sub("", action)


def test_alpine_trigger_list_is_declared_and_never_empty() -> None:
    """Первое и второе утверждения SP-1: число — объявленное, и оно не ноль."""
    assert len(ALPINE_TRIGGER_PLACES) == ALPINE_TRIGGER_PLACES_DECLARED, (
        f"записей в перечне {len(ALPINE_TRIGGER_PLACES)}, объявлено "
        f"{ALPINE_TRIGGER_PLACES_DECLARED}: триггер заведён или снят — обнови число "
        f"вместе с решением о нём и допиши строку летописи"
    )
    assert ALPINE_TRIGGER_PLACES_DECLARED > 0, (
        "перечень Alpine-триггеров объявлен ПУСТЫМ — правило о классе стало бы "
        "зелёным ровно тогда, когда триггеров не стало"
    )
    assert ALPINE_TRIGGER_PLACES_DECLARED == RAW_POST_WITHOUT_HX_POST


def test_alpine_trigger_places_equal_the_declared_list() -> None:
    """Места класса «сырой POST без ``hx-post``» — ровно перечень, поимённо."""
    found = {
        p.key
        for p in _form_places(_template_sources())
        if p.kind is PlaceKind.RAW_POST_WITHOUT_HX_POST
    }

    assert found == set(ALPINE_TRIGGER_PLACES), (
        f"класс разошёлся с перечнем: лишние {sorted(found - set(ALPINE_TRIGGER_PLACES))}, "
        f"пропавшие {sorted(set(ALPINE_TRIGGER_PLACES) - found)}"
    )


def test_every_alpine_trigger_opens_the_confirmation_panel_and_matches_its_basis() -> None:
    """Каждый триггер перехватывает submit событием ``modal-open-…``, и основание сверено с ``action``."""
    places = {p.key: p for p in _form_places(_template_sources())}
    offenders: list[str] = []
    for key, basis in ALPINE_TRIGGER_PLACES.items():
        place = places.get(key)
        if place is None:
            offenders.append(f"{key}: места нет")
            continue
        if not MODAL_OPEN_DISPATCH.search(place.text):
            offenders.append(f"{key}: submit не открывает панель подтверждения")
        action = _attr_value(place.text, ACTION_VALUE) or ""
        basis_path = BASIS_PATH.search(basis)
        if basis_path is None:
            offenders.append(f"{key}: основание не называет действие письма")
        elif BASIS_PLACEHOLDER.sub("", basis_path.group(1)) != _action_skeleton(action):
            offenders.append(f"{key}: основание {basis_path.group(1)!r} не совпало с action {action!r}")

    assert offenders == [], f"триггеры, расходящиеся с перечнем: {offenders}"


# --- ПРИЁМ ВТОРОГО УРОВНЯ: НЕВИДИМОЕ РАЗБОРЩИКУ ЗАПРЕЩЕНО --------------------
#
# Образец — tests/test_pages/test_impersonation_gate.py («гейт, который чего-то
# не видит, обязан требовать, чтобы этого и не было»). Это же — ответ на первую
# ветвь критерия 5 ROADMAP Фазы 15: «либо такая форма запрещена гейтом, либо
# проверена глазами». Границы названы, и каждая закрыта отдельным правилом:
#
# 1. Форма, чей ``method`` приходит из выражения шаблонизатора, сети по
#    литеральному ``post`` невидима. Правило: таких мест в дереве РОВНО ОДНО —
#    ``components/filters.html#0``, объявленное изъятием поимённо; второе такое
#    место краснеет. И отдельно: ни один вызывающий ``filters(`` метод не
#    переопределяет — иначе единственное изъятие стало бы формой письма, которой
#    прибор не видит.
# 2. Форма, вложенная в другую форму, разбору границ тега невидима: браузер
#    вложенную форму молча отбрасывает, а прибор посчитал бы её местом. Правило:
#    вложенных форм в дереве НЕТ. Вложенность ищется с учётом того, что форму
#    рождают не только сырые теги: вызов блоком макроса, кладущего ``caller()``
#    внутрь своей формы (``form_wrapper``, ``modal``, ``filters`` — множество
#    СНИМАЕТСЯ с дерева), вызов макроса, рендерящего форму (транзитивно), и
#    ``{% include %}`` файла, рендерящего форму (транзитивно). Единственное
#    вхождение вложенности по сырому тексту — ``ads/form.html:275``, внутри
#    Jinja-комментария; наивный проход по тексту без вырезания комментариев
#    видит его как незакрытую форму и объявляет вложенной сырую форму на 416.
#    ГРАНИЦА ЭТОГО ПРАВИЛА: включение по ПЕРЕМЕННОЙ (``{% include screen_template %}``)
#    не разрешается в файл — поэтому оно ЗАПРЕЩЕНО внутри формы тем же правилом;
#    макросы опознаются по имени, псевдонимов импорта (``import … as``) в
#    дереве ноль (замер 2026-09-24).

MACRO_BLOCK = re.compile(r"\{%-?\s*macro\s+(\w+)\s*\(.*?\{%-?\s*endmacro\s*-?%\}", re.DOTALL)
MACRO_OPEN = re.compile(r"\{%-?\s*macro\s+\w+\s*\(")
MACRO_CLOSE = re.compile(r"\{%-?\s*endmacro\s*-?%\}")
CALL_OPEN = re.compile(r"\{%-?\s*call(?:\s*\([^()]*\))?\s+(\w+)\s*\(")
CALL_CLOSE = re.compile(r"\{%-?\s*endcall\s*-?%\}")
FORM_CLOSE = re.compile(r"</form\s*>", re.IGNORECASE)
INCLUDE = re.compile(r"\{%-?\s*include\s+(.+?)\s*-?%\}", re.DOTALL)
LITERAL_TARGET = re.compile(r"^(?:\"([^\"]+)\"|'([^']+)')")
NAME_CALL = re.compile(r"(?<![\w.])(\w+)\s*\(")
CALLER_CALL = re.compile(r"(?<![\w.])caller\s*\(")
FILTERS_CALL = re.compile(r"\{%-?\s*call(?:\s*\([^()]*\))?\s+filters\s*\((.*?)%\}", re.DOTALL)
METHOD_ARGUMENT = re.compile(r"(?<![\w.])method\s*=")

NESTING_KNOWN_RAW_TEXT_FILES = frozenset({"ads/form.html"})


def _include_target(argument: str) -> str | None:
    """Литеральная цель включения; ``None`` — цель из выражения, файлом не разрешима."""
    match = LITERAL_TARGET.match(argument.strip())
    if match is None:
        return None
    return match.group(1) or match.group(2)


def _form_rendering(bodies: dict[str, str]) -> tuple[set[str], set[str], set[str]]:
    """Три множества, снятые с дерева: (caller-в-форме, макросы с формой, файлы с формой).

    Макрос «кладёт ``caller()`` в форму», если в его теле ``caller(`` стоит после
    открытия тега формы и до её закрытия. Макрос и файл «рендерят форму», если
    несут сырой тег формы, зовут рендерящий макрос или включают рендерящий
    файл, — до неподвижной точки.
    """
    macros: dict[str, list[str]] = {}
    for body in bodies.values():
        for match in MACRO_BLOCK.finditer(body):
            macros.setdefault(match.group(1), []).append(match.group(0))

    caller_in_form: set[str] = set()
    for name, blocks in macros.items():
        for block in blocks:
            for form in FORM_TAG.finditer(block):
                close = FORM_CLOSE.search(block, form.end())
                caller = CALLER_CALL.search(block, form.end())
                if caller and (close is None or caller.start() < close.start()):
                    caller_in_form.add(name)

    def renders(text: str, macro_names: set[str], files: set[str]) -> bool:
        if FORM_TAG.search(text):
            return True
        if any(name in macro_names for name in NAME_CALL.findall(text)):
            return True
        return any(_include_target(arg) in files for arg in INCLUDE.findall(text))

    rendering_macros: set[str] = set()
    rendering_files: set[str] = set()
    changed = True
    while changed:
        changed = False
        for name, blocks in macros.items():
            if name not in rendering_macros and any(
                renders(block[block.index("%}") + 2 :], rendering_macros, rendering_files)
                for block in blocks
            ):
                rendering_macros.add(name)
                changed = True
        for rel, body in bodies.items():
            if rel not in rendering_files and renders(body, rendering_macros, rendering_files):
                rendering_files.add(rel)
                changed = True
    return caller_in_form, rendering_macros, rendering_files


def _nested_form_offences(sources: dict[str, str]) -> dict[str, str]:
    """Места, где форма рождается ВНУТРИ другой формы: ``путь#номер`` → что именно.

    Исходник читается без комментариев. Глубина формы растёт на сыром теге и на
    вызове блоком макроса, кладущего ``caller()`` в форму; падает на
    ``</form>`` и на закрытии такого вызова. Тело определения макроса
    читается с нулевой глубиной — его контекст задаёт вызывающий, а не место
    определения.
    """
    bodies = {rel: _strip_comments(source) for rel, source in sources.items()}
    caller_in_form, rendering_macros, rendering_files = _form_rendering(bodies)
    offences: dict[str, str] = {}
    for rel, body in bodies.items():
        events: list[tuple[int, str, str]] = []
        events += [(m.start(), "open", m.group(0)) for m in FORM_TAG.finditer(body)]
        events += [(m.start(), "close", "") for m in FORM_CLOSE.finditer(body)]
        events += [(m.start(), "call", m.group(1)) for m in CALL_OPEN.finditer(body)]
        events += [(m.start(), "endcall", "") for m in CALL_CLOSE.finditer(body)]
        events += [(m.start(), "macro", "") for m in MACRO_OPEN.finditer(body)]
        events += [(m.start(), "endmacro", "") for m in MACRO_CLOSE.finditer(body)]
        heads = [m.span() for m in CALL_OPEN.finditer(body)] + [
            m.span() for m in MACRO_OPEN.finditer(body)
        ]
        for match in NAME_CALL.finditer(body):
            if match.group(1) in rendering_macros and not any(
                start <= match.start() < end for start, end in heads
            ):
                events.append((match.start(), "render", match.group(1)))
        for match in INCLUDE.finditer(body):
            target = _include_target(match.group(1))
            if target is None:
                events.append((match.start(), "unresolved-include", match.group(1).strip()))
            elif target in rendering_files:
                events.append((match.start(), "include", target))
        events.sort(key=lambda event: event[0])

        depth = 0
        stack: list[bool] = []
        saved: list[tuple[int, list[bool]]] = []
        ordinal = 0

        def offend(what: str) -> None:
            nonlocal ordinal
            offences[f"{rel}#{ordinal}"] = what
            ordinal += 1

        for _, kind, what in events:
            if kind == "open":
                if depth:
                    offend(f"сырая форма внутри формы: {what[:80]}")
                depth += 1
            elif kind == "close":
                depth = max(0, depth - 1)
            elif kind == "call":
                opens_form = what in caller_in_form
                if depth and (opens_form or what in rendering_macros):
                    offend(f"вызов {what} рендерит форму внутри формы")
                depth += 1 if opens_form else 0
                stack.append(opens_form)
            elif kind == "endcall":
                if stack and stack.pop():
                    depth = max(0, depth - 1)
            elif kind == "macro":
                saved.append((depth, stack))
                depth, stack = 0, []
            elif kind == "endmacro":
                if saved:
                    depth, stack = saved.pop()
            elif kind == "render" and depth:
                offend(f"вызов {what} рендерит форму внутри формы")
            elif kind == "include" and depth:
                offend(f"включение {what} рендерит форму внутри формы")
            elif kind == "unresolved-include" and depth:
                offend(f"включение по выражению {what!r} внутри формы — файл не разрешим")
    return offences


def _naive_raw_text_nesting(sources: dict[str, str]) -> set[str]:
    """Файлы, где проход по СЫРОМУ тексту (без вырезания комментариев) видит вложенность."""
    found: set[str] = set()
    for rel, source in sources.items():
        events = sorted(
            [(m.start(), 1) for m in FORM_TAG.finditer(source)]
            + [(m.start(), -1) for m in FORM_CLOSE.finditer(source)]
        )
        depth = 0
        for _, step in events:
            if step == 1 and depth:
                found.add(rel)
            depth = max(0, depth + step)
    return found


def _filters_method_overrides(sources: dict[str, str]) -> tuple[int, list[str]]:
    """(число вызывающих ``filters`` блоком, вызывающие, передавшие ``method=``)."""
    calls = 0
    overriding: list[str] = []
    for rel, source in sources.items():
        for match in FILTERS_CALL.finditer(_strip_comments(source)):
            calls += 1
            if METHOD_ARGUMENT.search(match.group(1)):
                overriding.append(f"{rel}: {match.group(0)[:100]!r}")
    return calls, overriding


def test_invisible_variable_method_forms_are_exactly_the_declared_one() -> None:
    """Форм с ``method`` из выражения ровно одна — ``components/filters.html``."""
    found = {
        p.key for p in _form_places(_template_sources()) if p.kind is PlaceKind.VARIABLE_METHOD
    }

    assert found == {"components/filters.html#0"}, (
        "форма с method из выражения шаблонизатора невидима сети по литеральному "
        f"post, и допускается ровно одна, объявленная изъятием: найдено {sorted(found)}"
    )
    assert "components/filters.html#0" in WRITE_FORM_EXCLUSIONS


def test_boundary_no_filters_caller_overrides_the_method() -> None:
    """Ни один вызывающий ``filters`` не передаёт ``method=`` — изъятие остаётся GET."""
    calls, overriding = _filters_method_overrides(_template_sources())

    assert calls > 0, "вызывающих filters не найдено — правило молчало бы на пустоте"
    assert overriding == [], (
        "вызывающий filters переопределил method — форма письма, которой прибор "
        f"не видит: {overriding}"
    )


def test_invisible_nested_forms_do_not_exist() -> None:
    """Вложенных форм в дереве нет; наивный проход по сырому тексту ошибся бы в одном файле."""
    sources = _template_sources()

    assert _nested_form_offences(sources) == {}, (
        f"форма рождается внутри формы: {_nested_form_offences(sources)}"
    )
    assert _naive_raw_text_nesting(sources) == NESTING_KNOWN_RAW_TEXT_FILES, (
        "проход по сырому тексту видит вложенность не там, где её объясняет "
        f"комментарий ads/form.html:275: {sorted(_naive_raw_text_nesting(sources))}"
    )
    caller_in_form, rendering_macros, _ = _form_rendering(
        {rel: _strip_comments(source) for rel, source in sources.items()}
    )
    assert caller_in_form == {"form_wrapper", "modal", "filters"}, (
        f"макросы, кладущие caller() в форму, сменились: {sorted(caller_in_form)}"
    )
    assert caller_in_form <= rendering_macros


def test_control_negative_a_second_invisible_variable_method_form_reddens_the_rule() -> None:
    """ЧТО ДОКАЗЫВАЕТ: вторая форма с ``method`` из выражения правилом ВИДНА."""
    key = "synthetic/variable_method_form.html"
    sources = _template_sources()
    assert key not in sources, "синтетический шаблон совпал по имени с настоящим"

    changed = dict(sources)
    changed[key] = '<form method="{{ verb }}" action="/synthetic"></form>\n'
    assert changed != sources, "подмена ничего не изменила"

    found = {p.key for p in _form_places(changed) if p.kind is PlaceKind.VARIABLE_METHOD}
    assert found == {"components/filters.html#0", f"{key}#0"}, (
        f"вторая невидимая форма прошла мимо правила: {sorted(found)}"
    )


def test_control_negative_a_filters_caller_overriding_the_method_reddens_the_boundary_rule() -> None:
    """ЧТО ДОКАЗЫВАЕТ: вызывающий ``filters(…, method='post')`` правилом границы ВИДЕН."""
    key = "synthetic/filters_post.html"
    sources = _template_sources()
    assert key not in sources, "синтетический шаблон совпал по имени с настоящим"

    changed = dict(sources)
    changed[key] = "{% call filters('synthetic', action='/synthetic', method='post') %}{% endcall %}\n"
    assert changed != sources, "подмена ничего не изменила"

    _, overriding = _filters_method_overrides(changed)
    assert len(overriding) == 1 and overriding[0].startswith(key), (
        f"переопределённый метод фильтров прошёл мимо правила: {overriding}"
    )


def test_control_negative_an_invisible_nested_form_reddens_the_nesting_rule() -> None:
    """ЧТО ДОКАЗЫВАЕТ: вложенность рождением формы тремя путями правилом ВИДНА."""
    sources = _template_sources()
    cases = {
        "synthetic/nested_by_call.html": (
            '<form method="post" action="/a">'
            "{% call form_wrapper(action='/b') %}{% endcall %}</form>\n"
        ),
        "synthetic/nested_by_include.html": (
            '<form method="post" action="/a">'
            '{% include "ads/includes/ad_card.html" %}</form>\n'
        ),
        "synthetic/nested_by_expression_include.html": (
            '<form method="post" action="/a">{% include screen_template %}</form>\n'
        ),
        "synthetic/nested_in_a_panel.html": (
            "{% call modal('x', 'Заголовок', action='/c') %}"
            '<form method="post" action="/d"></form>{% endcall %}\n'
        ),
    }
    for key, text in cases.items():
        assert key not in sources, "синтетический шаблон совпал по имени с настоящим"
        changed = dict(sources)
        changed[key] = text
        assert changed != sources, "подмена ничего не изменила"

        offences = _nested_form_offences(changed)
        assert list(offences) == [f"{key}#0"], (
            f"вложенная форма {key} прошла мимо правила: {offences}"
        )

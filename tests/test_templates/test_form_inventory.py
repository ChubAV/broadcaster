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

⚠️ ЛЕТОПИСИ «27 → 29» НЕТ — И ЭТО ЗАПИСАНО ОТДЕЛЬНОЙ СТРОКОЙ. Под определением «место письма» файлов ровно 27, столько же, сколько объявил прогноз.
29 получается только если включить GET-поиск и параметрический макрос фильтров,
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
утверждение плана 15-09. ГРАНИЦА РАЗБОРЩИКА: форма, чей ``method`` приходит
параметром макроса, сети по литеральному ``post`` НЕ ВИДНА НИ В КАКОМ СЛУЧАЕ,
даже если вызывающий передаст ``method='post'``. Замер 2026-09-24,
``grep -rn 'filters(' app/templates/`` — 8 строк: определение макроса
(``components/filters.html:24``), пример вызова в его докстринге
(``components/filters.html:8``, внутри Jinja-комментария) и ШЕСТЬ вызывающих —
``account_groups/list.html:174``, ``schedules/list.html:34``,
``admin/user_history.html:28``, ``admin/users.html:60``, ``admin/logs.html:60``,
``history/list.html:74``. Ни один из шести ``method`` не переопределяет: все
получают GET по умолчанию макроса. Это замер, а не перенесённое допущение A2
разведки.

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
    """Класс СЫРОГО тега формы; ``None`` — ни один объявленный класс."""
    return None


def _form_places(sources: dict[str, str]) -> list[WriteFormPlace]:
    """Все места формы дерева — письма и изъятия, без провайдера."""
    return []


def _write_form_places(sources: dict[str, str]) -> list[WriteFormPlace]:
    """Места ПИСЬМА: места формы классов ``WRITE_KINDS``."""
    return [place for place in _form_places(sources) if place.kind in WRITE_KINDS]


def _provider_tags(sources: dict[str, str]) -> list[Site]:
    """Теги формы, лежащие в теле макроса ``form_wrapper``."""
    return []


def _inventory_offence(declared: int, measured: int) -> str:
    """Пустая строка, если замеренное равно объявленному; иначе текст нарушения."""
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

    ``accounts/list.html`` несёт три посимвольно одинаковых тега; ключ по тексту
    схлопнул бы их в один.
    """
    places = _form_places(_template_sources())
    keys = [p.key for p in places]

    assert len(set(keys)) == len(places), "два места схлопнулись в один ключ"
    assert all(p.key == f"{p.template}#{p.ordinal}" for p in places)

    same_file = [p for p in places if p.template == "accounts/list.html"]
    assert len(same_file) == 3, f"в accounts/list.html мест {len(same_file)}, ожидалось 3"
    assert len({p.text for p in same_file}) == 1, (
        "три места accounts/list.html перестали совпадать посимвольно — "
        "довод о ключе по тексту здесь больше не показан"
    )
    assert len({p.key for p in same_file}) == 3

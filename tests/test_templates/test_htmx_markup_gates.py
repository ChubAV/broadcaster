"""Фаза 8, GATE-04/05/06: девять машинных правил РАЗМЕТКИ htmx.

Фазы 9-15 переводят на htmx сорок семь форм. Дефект контракта, допущенный
первой из них, размножится в сорок семь экземпляров прежде, чем его кто-нибудь
увидит глазами: форма без метода — мёртвая кнопка при отключённом JS, адрес
действия, разошедшийся с адресом запроса на один символ, — две разные
маршрутизации у одной формы, цель подмены с опечаткой — своп «в никуда», о
котором браузер не говорит ни слова. Гейты пишутся ДО перевода первой формы
именно поэтому.

ЧЕТЫРЕ СВОЙСТВА, БЕЗ КОТОРЫХ ГЕЙТ РАЗМЕТКИ НИЧЕГО НЕ УТВЕРЖДАЕТ.

1. КАЖДЫЙ ИНВЕНТАРЬ ОБЪЯВЛЕН ЧИСЛОМ, СОБРАННЫМ СОБСТВЕННЫМ ОБХОДОМ. Опечатка в
   регулярке обхода даёт пустое множество, пустое множество даёт вакуумно
   зелёное пересечение, и зелёный цвет сломанного гейта посимвольно совпадает с
   зелёным цветом соблюдённого правила. Различает их только собственное число:
   ``HX_POST_PLACES``, ``OOB_BLOCKS``, ``HX_TARGETS``, ``CLIENT_STATE_NODES``,
   ``FRAGMENT_ROUTES_DECLARED``. Ноль объявляется ИМЕНОВАННОЙ константой, а не
   выводится из пустоты (прецедент — ``SERVER_SIDE_VALIDATION_RESPONSES = 0``).

2. КОММЕНТАРИИ ОБОИХ ВИДОВ ВЫРЕЗАЮТСЯ ДО СЧЁТА. Кодовая база проекта несёт
   комментарии-обоснования объёмные, и они свободно называют имена атрибутов:
   ``ads/includes/autosave_response.html`` объясняет неизменяемость адреса
   запроса, набирая имя атрибута отправки его собственным литералом. Гейт,
   считающий прозу, получает два отказа сразу — краснеет на правку
   документации и позволяет комментарию ЗАМЕНИТЬ собой пропавшее место, оставив
   число верным.

3. СЧЁТ ИДЁТ ПО ВХОЖДЕНИЯМ АТРИБУТА И ПО ТЕГАМ, ИХ НЕСУЩИМ, И ДВЕ ВЕЛИЧИНЫ
   СВЕРЯЮТСЯ. Свойства правил (метод, адрес, тег, цель) читаются из ТЕКСТА
   ТЕГА, то есть верны ровно настолько, насколько верно найдены границы тега.
   Тег, поглотивший соседа или оборвавшийся на угловой скобке внутри
   Jinja-выражения, дал бы меньше мест, чем есть атрибутов, и внутри общего
   счёта такая потеря неотличима от исчезновения разметки.

4. У КАЖДОГО ПРАВИЛА ЕСТЬ СЛУЧАЙ КОНТРОЛЯ (``-k control``). Каждый подаёт
   обходу изменённую копию дерева шаблонов во временном каталоге и требует,
   чтобы гейт на ней ПОКРАСНЕЛ. Подстановка при этом обязана доказать, что она
   что-то изменила: контроль, чья подстановка не нашлась, «проходит» на
   нетронутом дереве и утверждает ровно ничего.

ПОЧЕМУ ЭТОТ ФАЙЛ ЖИВЁТ В ``tests/`` И НЕ МОЖЕТ УДОВЛЕТВОРИТЬ СОБСТВЕННЫЙ
ПОИСК — ЭТО СВОЙСТВО РАСПОЛОЖЕНИЯ, А НЕ ОСТОРОЖНОСТИ ФОРМУЛИРОВОК. Область
поиска всех гейтов файла — ``app/templates`` и ``app/pages``; сам файл лежит в
``tests/test_templates/``. Его собственные литералы — а их здесь много, потому
что группа контроля обязана собирать нарушения из настоящих строк — не попадают
в область поиска ни одним путём. Прежняя форма защиты (набирать проверяемые
строки в комментариях СЛОВАМИ) в этой же фазе уже дала отказ: гейт, чьи
собственные литералы лежат в области его поиска, ломает собственные критерии
счёта, и лечится это переносом гейта, а не подбором слов. Абзац написан затем,
чтобы следующая уборка не переселила файл в ``app/``: там он станет зелёным по
построению.

Каталог выбран тот же, что у ``test_htmx_inventory.py``, и по той же причине:
это гейт РАЗМЕТКИ, читающий исходники шаблонов текстом. Приложение он не
поднимает и ни одного его модуля не подключает — суита гейта обязана быть
исполнимой на одном дереве исходников.

⚠️ ЧЕГО ГЕЙТ НЕ ВИДИТ.

а) АТРИБУТ, СОБРАННЫЙ УСЛОВИЕМ JINJA ВНУТРИ ТЕГА. Обход видит ИСХОДНИК, где
   атрибут есть всегда, а человек видит отрендеренную страницу, где его может
   не быть вовсе. Один такой атрибут в проекте есть: признак внеполосной
   подмены индикатора автосохранения выставляется веткой ``{% if %}`` внутри
   открывающего тега (``ads/includes/autosave.html``), и в инвентарь он входит
   безусловно. Это та же слепая зона, что описана механизмом 3 инвентаря
   ``hx-get`` (``test_htmx_inventory.py``), и закрывается она тем же способом —
   пунктом 9 перечня ручного UAT, а не молчанием.

б) СУЩЕСТВОВАНИЕ ЦЕЛИ ПРОВЕРЯЕТСЯ ПО ВСЕМУ ДЕРЕВУ ШАБЛОНОВ, А НЕ ПО ДОКУМЕНТУ,
   КОТОРЫЙ СОБИРАЕТ КОНКРЕТНЫЙ МАРШРУТ. Обход не разворачивает наследование и
   включения. Цель, объявленная в шаблоне, который на этой странице не
   подключается, гейт пропустит. Допущение записано планом как требующее
   решения человека, если такой случай появится.

в) ПРИЗНАКОМ КЛИЕНТСКОГО СОСТОЯНИЯ СЧИТАЕТСЯ РОВНО ОДИН АТРИБУТ, И ВЛОЖЕННОСТЬ
   НЕ УЧИТЫВАЕТСЯ. Узел-потомок узла с клиентским состоянием целью подмены быть
   может, и гейт этого не заметит. Требует решения человека, если потеря
   состояния при подмене потомка обнаружится обходом UAT.

г) ПУТЬ, СОБРАННЫЙ ВО ВРЕМЯ ИСПОЛНЕНИЯ, ИЗВЛЕЧЕНИЮ НЕ ПОДДАЁТСЯ — И ПОТОМУ
   ЗАПРЕЩЁН ЭТИМ ЖЕ ГЕЙТОМ. Гейт, который чего-то не видит, обязан требовать,
   чтобы этого и не было: см. ``test_no_action_is_assembled_from_an_unknown_value``.
"""

import ast
import re
from pathlib import Path
from typing import NamedTuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = PROJECT_ROOT / "app" / "templates"
PAGES_DIR = PROJECT_ROOT / "app" / "pages"


# --- ИНВЕНТАРЬ ---------------------------------------------------------------
#
# ЛЕТОПИСЬ ЧИСЕЛ. Величины ниже выписаны ЗДЕСЬ, а не выведены из проверяемых
# шаблонов в момент прогона: тест, считающий ожидание по коду, согласится с
# любой правкой и молча переживёт исчезновение места. Форма записи — с
# tests/test_templates/test_htmx_inventory.py и tests/test_pages/test_access_gate.py.
#
# Уменьшение объявленного числа допустимо и означает СОЗНАТЕЛЬНОЕ снятие места,
# записанное следующей записью этой летописи. Молчаливое исчезновение краснеет.

# Мест отправки htmx сегодня ОДНО — форма редактора объявлений. Второе
# текстовое вхождение имени этого атрибута в дереве шаблонов живёт в
# Jinja-комментарии соседнего включения и обязано быть вырезано ДО счёта; ровно
# это и утверждает test_the_inventory_ignores_prose на настоящем дереве.
HX_POST_PLACES = 1


# --- РЕГУЛЯРКИ ОБХОДА --------------------------------------------------------
#
# Каркас скопирован с test_htmx_inventory.py дословно, и это решение, а не
# небрежность. Импортировать разборщики оттуда значило бы связать гейт РАЗМЕТКИ
# ФАЗЫ 8 с инвентарным гейтом ФАЗЫ 7: правка его регулярок под свою задачу
# молча меняла бы смысл здешних утверждений, а перенос общего каркаса в третье
# место завёл бы модуль-помощник, которого у гейтов разметки в проекте нет.
# Каждая часть каркаса закрывает названную ловушку — они перечислены ниже.

JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.DOTALL)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def _attr_pattern(name: str) -> re.Pattern[str]:
    """Вхождение атрибута ``name`` со значением.

    Отрицательный просмотр назад отсекает атрибуты, у которых искомое имя —
    лишь хвост более длинного (данные вида ``data-<имя>``): граница слова его
    бы не отсекла, потому что дефис сам по себе не буква.
    """
    return re.compile(rf"(?<![-\w]){re.escape(name)}\s*=")


def _tag_pattern(name: str) -> re.Pattern[str]:
    """Тег, несущий атрибут ``name``: от открывающей скобки до закрывающей.

    Границы чужих тегов не пересекаются (``[^<>]``). Тег, внутри которого
    угловая скобка всё-таки встретилась, этим выражением НЕ найдётся — и это не
    молчаливая потеря: число найденных тегов утверждается равным числу
    вхождений самого атрибута отдельным тестом, который такой случай и назовёт.
    """
    return re.compile(rf"<[^<>]*?(?<![-\w]){re.escape(name)}\s*=[^<>]*>")


HX_POST_ATTR = _attr_pattern("hx-post")
HX_POST_TAG = _tag_pattern("hx-post")

TAG_NAME = re.compile(r"<\s*([A-Za-z][-\w]*)")


def _value_pattern(name: str) -> re.Pattern[str]:
    """Значение атрибута ``name`` внутри текста тега, в кавычках любого вида."""
    return re.compile(rf"(?<![-\w]){re.escape(name)}\s*=\s*(\"([^\"]*)\"|'([^']*)')")


METHOD_VALUE = _value_pattern("method")
ACTION_VALUE = _value_pattern("action")
HX_POST_VALUE = _value_pattern("hx-post")


class Site(NamedTuple):
    """Место разметки: шаблон и ПОЛНЫЙ ТЕКСТ несущего тега.

    Единицей утверждения выбран тег, а не строка исходника: два места
    умещаются на одной строке, а один тег занимает несколько. Гейт, читающий
    свойства правила из строки, краснел бы на переформатирование разметки,
    которая не менялась (07-REVIEW.md, WR-07).
    """

    template: str
    tag: str


# --- РАЗБОРЩИКИ ИСХОДНИКОВ ---------------------------------------------------


def _all_templates(directory: Path | None = None) -> list[tuple[str, str]]:
    """Все шаблоны дерева парами «путь относительно корня — исходник».

    Каталог ПРИНИМАЕТСЯ ПАРАМЕТРОМ, а не берётся из константы, и это несущее
    решение гейта. Группа контроля обязана подать обходу ИЗМЕНЁННУЮ копию
    дерева; разборщик, зашитый на единственный каталог, сделал бы группу
    контроля невыразимой, и зубы гейта пришлось бы ЗАЯВЛЯТЬ вместо того, чтобы
    их показывать. Тот же приём и по той же причине применён у гейта шелла
    (tests/test_pages/test_shell.py, план 08-04), где чтение включения вынесено
    в функцию, принимающую путь.

    Обход РЕКУРСИВНЫЙ и ОТСОРТИРОВАННЫЙ: плоский не увидел бы шаблонов
    подкаталогов (ловушка, уже пойманная ревизией test_impersonation_gate.py),
    а несортированный давал бы разный порядок в сообщении об отказе от прогона
    к прогону.
    """
    root = TEMPLATES_DIR if directory is None else directory
    return [
        (path.relative_to(root).as_posix(), path.read_text(encoding="utf-8"))
        for path in sorted(root.rglob("*.html"))
    ]


def _strip_comments(source: str) -> str:
    """Исходник без Jinja- и HTML-комментариев.

    Порядок вырезания значим: сначала Jinja, потом HTML — Jinja исполняется
    раньше, и HTML-комментарий, лежащий внутри ``{# … #}``, до браузера не
    доходит вовсе.
    """
    return HTML_COMMENT.sub("", JINJA_COMMENT.sub("", source))


def _sites(templates: list[tuple[str, str]], tag_re: re.Pattern[str]) -> list[Site]:
    """Места разметки по всему дереву: (шаблон, текст тега)."""
    found: list[Site] = []
    for rel, source in templates:
        for tag in tag_re.findall(_strip_comments(source)):
            found.append(Site(rel, tag))
    return found


def _attribute_count(templates: list[tuple[str, str]], attr_re: re.Pattern[str]) -> int:
    """Число вхождений атрибута — независимо от разбора границ тега.

    Считается по тому же исходнику без комментариев, что и теги, но БЕЗ разбора
    тегов. Две величины, полученные разными путями из одного источника,
    сверяются отдельным тестом: расхождение означает ошибку разбора границ, а
    не пропажу разметки.
    """
    return sum(len(attr_re.findall(_strip_comments(source))) for _, source in templates)


def _post_sites(templates: list[tuple[str, str]]) -> list[Site]:
    return _sites(templates, HX_POST_TAG)


def _tag_name(tag: str) -> str:
    match = TAG_NAME.match(tag)
    return match.group(1).lower() if match else ""


def _attr_value(tag: str, pattern: re.Pattern[str]) -> str | None:
    """СЫРОЕ значение атрибута из текста тега, без кавычек.

    Сырое — то есть вместе с выражением шаблонизатора целиком, если оно там
    есть. Утверждение о посимвольном совпадении адреса запроса с адресом
    действия работает именно на этом виде значения: два РАЗНЫХ выражения,
    дающих один и тот же адрес, гейт признаёт нарушением осознанно. Одно
    выражение обязано быть выписано один раз в двух атрибутах — иначе правка
    одного из них разводит две маршрутизации одной формы молча.
    """
    match = pattern.search(tag)
    if not match:
        return None
    return match.group(2) if match.group(2) is not None else match.group(3)


# --- УТВЕРЖДЕНИЯ: ИНВЕНТАРЬ И РАЗБОР -----------------------------------------


def test_the_number_of_htmx_post_places_is_the_declared_one() -> None:
    """Мест отправки htmx ровно ``HX_POST_PLACES``.

    Первое из пяти инвентарных утверждений файла. Без него сломанный обход даёт
    пустое множество мест, и ВСЕ правила деградации ниже становятся вакуумно
    зелёными: правило, которому не на чем сработать, зелено всегда.
    """
    sites = _post_sites(_all_templates())
    assert len(sites) == HX_POST_PLACES, (
        f"мест отправки htmx найдено {len(sites)}, объявлено {HX_POST_PLACES}: "
        f"{[site.template for site in sites]} — место молча исчезло, появилось "
        f"незаявленное, либо обход перестал их находить, и правила деградации "
        f"ниже утверждают пустоту"
    )


def test_the_attribute_count_matches_the_tag_count() -> None:
    """Парный контроль обхода: тегов ровно столько, сколько вхождений атрибута.

    Утверждение о РАЗБОРЕ, а не об инвентаре, и потому отдельное. Все правила
    деградации читаются из ТЕКСТА ТЕГА и потому неверны везде, где границы тега
    разобраны неверно. Тег, поглотивший соседа или оборвавшийся на угловой
    скобке внутри Jinja-выражения, дал бы меньше мест, чем есть атрибутов, а
    внутри общего счёта такая потеря неотличима от исчезновения разметки.
    """
    templates = _all_templates()
    offenders: dict[str, str] = {}
    for rel, source in templates:
        body = _strip_comments(source)
        attributes = len(HX_POST_ATTR.findall(body))
        tags = len(HX_POST_TAG.findall(body))
        if attributes != tags:
            offenders[rel] = f"вхождений атрибута {attributes}, тегов {tags}"

    assert not offenders, (
        f"число тегов, несущих атрибут отправки, разошлось с числом вхождений "
        f"самого атрибута: {offenders} — это ошибка РАЗБОРА ГРАНИЦ ТЕГА, а не "
        f"пропажа разметки"
    )
    assert _attribute_count(templates, HX_POST_ATTR) == HX_POST_PLACES


def test_the_inventory_ignores_prose() -> None:
    """Проза, называющая атрибут, инвентарь не увеличивает.

    Проверяется ДВАЖДЫ, и обе половины нужны.

    ПОЛОВИНА ПЕРВАЯ — подставные исходники, собранные прямо здесь. Настоящие
    шаблоны сегодня отформатированы так, что каждое место лежит на своей
    строке; то есть на настоящем дереве разбор мог бы быть зелен по СОВПАДЕНИЮ
    форматирования, а не по построению. Случаи ниже держат разбор в границах,
    верных независимо от того, как отформатированы шаблоны сегодня.

    ПОЛОВИНА ВТОРАЯ — настоящее дерево. Вхождение имени атрибута в комментарии
    в проекте ЕСТЬ (соседнее включение редактора объявлений объясняет
    неизменяемость адреса запроса, набирая имя атрибута его литералом), и
    вырезание комментариев на настоящем дереве работает, а не только на
    подставном.
    """
    # 1. Два места на ОДНОЙ строке — два места, а не одно.
    two_on_one_line = (
        '<form method="post" action="/a" hx-post="/a"></form>'
        '<form method="post" action="/b" hx-post="/b"></form>'
    )
    assert len(_post_sites([("synthetic.html", two_on_one_line)])) == 2, (
        "два места отправки на одной строке схлопнулись в одно: счёт идёт по "
        "строкам исходника, а место есть АТРИБУТ — переформатирование разметки "
        "в одну строку молча потеряло бы половину мест"
    )

    # 2. Имя атрибута только в Jinja-комментарии — мест НЕТ.
    jinja_prose = (
        '{# Форма несёт неизменяемый hx-post="/ads/new": адрес запроса не '
        "переписывается никогда. Форма описана здесь, места здесь нет. #}\n"
        "<p>обычная разметка</p>"
    )
    assert _post_sites([("synthetic.html", jinja_prose)]) == [], (
        "Jinja-комментарий, называющий атрибут отправки, посчитан настоящим "
        "местом: проза способна СОЗДАТЬ место и тем самым замаскировать пропажу "
        "настоящего, оставив инвентарное число верным"
    )

    # 3. Имя атрибута только в HTML-комментарии — мест НЕТ.
    html_prose = (
        '<!-- Автосохранение уходит на hx-post="/ads/new" и подмены не делает -->\n'
        "<p>обычная разметка</p>"
    )
    assert _post_sites([("synthetic.html", html_prose)]) == [], (
        "HTML-комментарий, называющий атрибут отправки, посчитан настоящим "
        "местом: гейт разметки обязан считать разметку, а не документацию о ней"
    )

    # 4. Атрибуты одного тега разнесены переносом строки — место ОДНО, и его
    #    свойства читаются так же, как у записанного в одну строку.
    wrapped = (
        "<form\n"
        '  method="post"\n'
        '  action="/ads/new"\n'
        '  hx-post="/ads/new"\n'
        '  hx-swap="none">'
    )
    inline = '<form method="post" action="/ads/new" hx-post="/ads/new" hx-swap="none">'
    wrapped_sites = _post_sites([("synthetic.html", wrapped)])
    inline_sites = _post_sites([("synthetic.html", inline)])
    assert len(wrapped_sites) == len(inline_sites) == 1
    assert _tag_name(wrapped_sites[0].tag) == _tag_name(inline_sites[0].tag) == "form"
    assert _attr_value(wrapped_sites[0].tag, ACTION_VALUE) == _attr_value(
        inline_sites[0].tag, ACTION_VALUE
    ), (
        "один и тот же тег, записанный в одну строку и в несколько, разобран "
        "по-разному — свойства правила читаются из СТРОКИ, а несёт их ТЕГ"
    )

    # 5. Настоящее дерево: сырых вхождений больше, чем мест разметки.
    templates = _all_templates()
    raw = sum(len(HX_POST_ATTR.findall(source)) for _, source in templates)
    stripped = _attribute_count(templates, HX_POST_ATTR)
    assert stripped == HX_POST_PLACES
    assert raw > stripped, (
        f"на настоящем дереве сырых вхождений имени атрибута {raw}, мест "
        f"разметки {stripped} — вырезание комментариев здесь ничего не "
        f"вырезает. Либо обход перестал видеть комментарии, либо проза, ради "
        f"которой вырезание заведено, из дерева ушла целиком: во втором случае "
        f"это утверждение теряет предмет и снимается ЯВНО, вместе с записью в "
        f"летописи чисел, а не подгонкой под новый счёт"
    )


# --- УТВЕРЖДЕНИЯ: ДЕГРАДАЦИЯ (G-3, G-4, G-6) ---------------------------------


def _offenders_tag_is_a_form(templates: list[tuple[str, str]]) -> dict[str, str]:
    """G-6: тег, несущий признак отправки, обязан быть тегом формы."""
    return {
        f"{site.template}:{_tag_name(site.tag)}": site.tag[:120]
        for site in _post_sites(templates)
        if _tag_name(site.tag) != "form"
    }


def _offenders_method_and_action(templates: list[tuple[str, str]]) -> dict[str, str]:
    """G-3: у каждого такого тега есть метод POST и НЕПУСТОЙ адрес действия."""
    offenders: dict[str, str] = {}
    for site in _post_sites(templates):
        method = _attr_value(site.tag, METHOD_VALUE)
        action = _attr_value(site.tag, ACTION_VALUE)
        if method is None or method.strip().lower() != "post":
            offenders[f"{site.template}:метод"] = repr(method)
        if action is None or not action.strip():
            offenders[f"{site.template}:адрес"] = repr(action)
    return offenders


def _offenders_post_matches_action(templates: list[tuple[str, str]]) -> dict[str, str]:
    """G-4: признак отправки посимвольно равен адресу действия."""
    offenders: dict[str, str] = {}
    for site in _post_sites(templates):
        action = _attr_value(site.tag, ACTION_VALUE)
        posted = _attr_value(site.tag, HX_POST_VALUE)
        if action != posted:
            offenders[site.template] = f"адрес действия {action!r}, адрес запроса {posted!r}"
    return offenders


def test_only_a_form_tag_carries_the_post_attribute() -> None:
    """G-6: признак отправки стоит ТОЛЬКО на теге формы.

    Кнопка, несущая признак отправки сама, при отключённом JS не делает ничего:
    у неё нет ни метода, ни адреса, и браузеру нечего отправлять. Это не
    «ухудшенный вид» — это мёртвая кнопка, и отличить её от рабочей глазами на
    странице с включённым JS нельзя.
    """
    offenders = _offenders_tag_is_a_form(_all_templates())
    assert not offenders, (
        f"признак отправки htmx стоит на теге, который формой не является: "
        f"{offenders} — без JS такой элемент мёртв, потому что отправлять "
        f"браузеру нечего"
    )


def test_every_such_form_keeps_its_method_and_action() -> None:
    """G-3: у каждой формы с признаком отправки есть метод POST и адрес.

    Это и есть контракт деградации в его минимальной форме: форма, у которой
    метод и адрес на месте, работает без единой строчки JS — браузер отправит
    её сам. htmx на такой форме только ПЕРЕХВАТЫВАЕТ отправку.
    """
    offenders = _offenders_method_and_action(_all_templates())
    assert not offenders, (
        f"форма с признаком отправки htmx потеряла метод или адрес действия: "
        f"{offenders} — при отключённом JS отправлять её браузеру некуда и "
        f"нечем"
    )


def test_the_post_attribute_matches_the_action_character_for_character() -> None:
    """G-4: адрес запроса посимвольно равен адресу действия.

    СИЛЬНЕЙШЕЕ одиночное утверждение вехи. Оно делает «htmx только
    перехватывает отправку» СВОЙСТВОМ ИСХОДНИКА, а не намерением автора: пока
    два значения совпадают посимвольно, путь с JS и путь без JS ведут в одно и
    то же место по построению, и разойтись они могут только заметно.

    Сравнение идёт по СЫРОЙ строке шаблона, включая выражение шаблонизатора
    целиком. Два РАЗНЫХ выражения, дающих один и тот же адрес, гейт признаёт
    нарушением, и это осознанно строже требования: одно выражение обязано быть
    выписано ОДИН РАЗ в двух атрибутах, иначе правка одного из них разводит две
    маршрутизации одной формы — молча и на любой глубине условия.
    """
    offenders = _offenders_post_matches_action(_all_templates())
    assert not offenders, (
        f"адрес запроса htmx разошёлся с адресом действия формы: {offenders} — "
        f"у одной формы стало два разных адреса, и какой из них сработает, "
        f"решает наличие JS у человека"
    )


# --- УТВЕРЖДЕНИЯ: АДРЕС ДЕЙСТВИЯ ВЕДЁТ НА ПОЛНЫЙ ДОКУМЕНТ (G-5) --------------
#
# Правила выше доказывают, что форма ОТПРАВИТСЯ без JS. Здесь доказывается, что
# отправленная без JS форма приведёт человека НА СТРАНИЦУ, а не на голый кусок
# разметки вне шелла: браузер покажет ответ маршрута целиком, и фрагмент,
# собранный для подмены, окажется документом — без навигации, без стилей шелла
# и без области уведомления. Статус ответа при этом двухсотый, и заметить это
# автоматической проверкой доступности нельзя.

ROUTE_METHODS = ("get", "post", "put", "patch", "delete")
PATH_PARAM = re.compile(r"\{[^{}]*\}")
PARAM = "{}"

# Признак ПУТИ ДЕГРАДАЦИИ в обработчике страничного слоя. Оба имени объявлены
# планом 08-01 и живут в одном модуле ответа: чтение признака запроса htmx —
# единственное на проект, а главный выход обработчика принимает адрес
# деградации ОБЯЗАТЕЛЬНЫМ ключевым аргументом, то есть обработчик, забывший
# путь без JS, не собирается как вызов. Присутствие любого из двух имён в
# достижимом коде обработчика и означает «маршрут умеет отвечать не только
# фрагментом».
#
# Почему признак именно такой. Наивное «обработчик рендерит шаблон из каталога
# фрагментов» объявило бы фрагментным маршрут автосохранения редактора — тот
# самый, на который ведёт единственный сегодняшний адрес действия, — и гейт
# покраснел бы на работающем коде в первый же прогон. Маршрут автосохранения
# фрагмент отдаёт, но ТОЛЬКО запросу htmx; человеку без JS он отвечает
# перенаправлением. Наивное «обработчик возвращает перенаправление» столь же
# негодно с другой стороны: перенаправлением на вход отвечает КАЖДЫЙ маршрут,
# и фрагментных маршрутов не осталось бы вовсе — пустое множество, вакуумно
# зелёное пересечение и ровно тот дефект, который инвентарные числа этого файла
# и заведены различать.
DEGRADATION_MARKERS = frozenset({"is_htmx", "respond"})

# Шеллов у проекта два, и собой они документы, а не фрагменты: `{% extends %}`
# в них не встречается по построению.
SHELL_TEMPLATES = frozenset({"base.html", "auth_base.html"})
EXTENDS = re.compile(r"\{%-?\s*extends\b")


class Route(NamedTuple):
    """Объявление маршрута страничного слоя с НОРМАЛИЗОВАННЫМ путём.

    Нормализация приводит имена параметров пути к безымянному виду: имя
    параметра принадлежит обработчику, а адрес действия в шаблоне подставляет
    на его место значение и имени не знает. Сверять их именами значило бы
    требовать от шаблона знания сигнатуры.
    """

    method: str
    path: str


def _normalized(path: str) -> str:
    return PATH_PARAM.sub(PARAM, path)


def _document_templates() -> frozenset[str]:
    """Шаблоны, дающие ПОЛНЫЙ документ: наследники шелла и сами шеллы.

    Признак структурный, а не по имени каталога. Каталог фрагментов
    (``includes/``, ``partials/``) — соглашение, которое соблюдается не везде:
    порции бесконечной подгрузки лежат прямо в каталогах своих разделов
    (``ads/partial_cards.html`` и ещё три таких же) и по имени каталога
    фрагментами не опознаются, хотя шелла не несут и в браузере как страница
    нечитаемы. Наследование же есть ровно тот механизм, которым документ
    получает шелл, и обойти его, оставшись документом, нельзя.
    """
    documents: set[str] = set()
    for rel, source in _all_templates():
        if rel in SHELL_TEMPLATES or EXTENDS.search(_strip_comments(source)):
            documents.add(rel)
    return frozenset(documents)


def _page_routes() -> dict[Route, bool]:
    """Маршруты страничного слоя: объявление → «отдаёт только фрагмент».

    Множество собирается РАЗБОРОМ дерева ``app/pages/**/*.py``, а не
    объявляется перечнем. Перечень, выписанный руками, устарел бы на первом же
    новом маршруте и молча объявил бы его неопасным.

    Достижимость считается в пределах модуля: тело обработчика плюс тела
    объявленных в том же модуле функций, чьи имена в нём упоминаются, и так
    далее по цепочке. Этого достаточно и не случайно: разметка ответа в этом
    проекте живёт в шаблоне, а помощник, её рендерящий, — рядом с обработчиком
    (образец — помощник ответа опроса подключения в разделе аккаунтов).
    """
    routes: dict[Route, bool] = {}
    documents = _document_templates()

    for path in sorted(PAGES_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        prefixes: dict[str, str] = {}
        template_constants: dict[str, str] = {}
        functions: dict[str, ast.AST] = {}

        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if not isinstance(target, ast.Name):
                        continue
                    value = node.value
                    if isinstance(value, ast.Constant) and _is_template(value.value):
                        template_constants[target.id] = value.value
                    if (
                        isinstance(value, ast.Call)
                        and getattr(value.func, "id", None) == "APIRouter"
                    ):
                        prefix = ""
                        for keyword in value.keywords:
                            if keyword.arg == "prefix" and isinstance(
                                keyword.value, ast.Constant
                            ):
                                prefix = keyword.value.value
                        prefixes[target.id] = prefix
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions[node.name] = node

        def facts(node: ast.AST, seen: frozenset[str] = frozenset()) -> tuple[set[str], bool]:
            templates: set[str] = set()
            degrades = False
            names: set[str] = set()
            for inner in ast.walk(node):
                if isinstance(inner, ast.Constant) and _is_template(inner.value):
                    templates.add(inner.value)
                if isinstance(inner, ast.Name):
                    names.add(inner.id)
            for name in names:
                if name in template_constants:
                    templates.add(template_constants[name])
                if name in DEGRADATION_MARKERS:
                    degrades = True
            for name in sorted(names):
                if name in functions and name not in seen:
                    sub_templates, sub_degrades = facts(functions[name], seen | {name})
                    templates |= sub_templates
                    degrades = degrades or sub_degrades
            return templates, degrades

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr in ROUTE_METHODS
                ):
                    continue
                router = getattr(decorator.func.value, "id", None)
                if router not in prefixes:
                    continue
                if not decorator.args or not isinstance(decorator.args[0], ast.Constant):
                    continue
                rendered, degrades = facts(node)
                is_fragment = (
                    bool(rendered)
                    and not degrades
                    and all(name not in documents for name in rendered)
                )
                route = Route(
                    decorator.func.attr.upper(),
                    _normalized(prefixes[router] + decorator.args[0].value),
                )
                routes[route] = routes.get(route, False) or is_fragment

    return routes


def _is_template(value: object) -> bool:
    return isinstance(value, str) and value.endswith(".html")


PAGE_ROUTES = _page_routes()

# Маршруты, отдающие ФРАГМЕНТ и только его: пути деградации у них нет вовсе.
# Множество СОБРАНО обходом; число объявлено ниже отдельной константой, потому
# что сломанный разбор дал бы пустое множество, пустое множество — вакуумно
# зелёное пересечение с адресами действия, а зелёный цвет сломанного гейта
# посимвольно совпадает с зелёным цветом соблюдённого правила (D-13).
FRAGMENT_ROUTES = frozenset(route for route, fragment in PAGE_ROUTES.items() if fragment)

FRAGMENT_ROUTES_DECLARED = 12


def _to_python_expression(expression: str) -> str | None:
    """Выражение шаблонизатора в виде, разбираемом синтаксисом Python.

    Единственное различие, существенное для адреса, — знак склейки: у
    шаблонизатора он тильда, у Python — плюс. Замена идёт ТОЛЬКО вне кавычек:
    тильда внутри литерала есть часть пути, и подмена её плюсом молча изменила
    бы извлечённый адрес, оставив гейт зелёным на неверном значении.
    """
    out: list[str] = []
    quote: str | None = None
    for char in expression:
        if quote is not None:
            out.append(char)
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
            out.append(char)
            continue
        out.append("+" if char == "~" else char)
    if quote is not None:
        return None
    return "".join(out)


def _expression_branches(expression: str) -> tuple[str, ...] | None:
    """ВСЕ значения, которые может дать выражение, с параметрами вместо величин.

    Извлекаются ВСЕ ветви, а не первая: значение адреса действия единственной
    сегодняшней формы есть условное выражение, и ветвей у него ДВЕ — создание и
    правка. Гейт, взявший первую, проверил бы половину контракта и промолчал бы
    о второй, то есть ровно о том пути, который в проекте новее.
    """
    source = _to_python_expression(expression.strip())
    if source is None:
        return None
    try:
        node = ast.parse(source, mode="eval").body
    except SyntaxError:
        return None
    return _branches(node)


def _branches(node: ast.AST) -> tuple[str, ...]:
    """Ветви выражения. Всё, что не литерал и не склейка, — ПАРАМЕТР пути."""
    if isinstance(node, ast.IfExp):
        return _branches(node.body) + _branches(node.orelse)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return tuple(
            left + right for left in _branches(node.left) for right in _branches(node.right)
        )
    if isinstance(node, ast.Constant):
        return (node.value,) if isinstance(node.value, str) else (str(node.value),)
    return (PARAM,)


JINJA_EXPRESSION = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
JINJA_STATEMENT = re.compile(r"\{%")


def _literal_paths(raw: str) -> tuple[str, ...] | None:
    """Пути, которые может дать значение адреса действия. ``None`` — не извлечь.

    Значение разбирается на чередование текста и выражений шаблонизатора; у
    каждого выражения берутся ВСЕ ветви, и множество путей есть их произведение
    с окружающим текстом.

    ⚠️ ГРАНИЦА, КОТОРУЮ ГЕЙТ НЕ ПЕРЕСЕКАЕТ И ПОТОМУ ЗАПРЕЩАЕТ. Путь, собранный
    во время исполнения — склейка из величины, значение которой шаблону
    неизвестно, — извлечению не поддаётся, и здесь возвращается ``None``. Такая
    форма адреса действия запрещена этим же гейтом
    (``test_no_action_is_assembled_from_an_unknown_value``): гейт, который
    чего-то не видит, обязан требовать, чтобы этого и не было, иначе первый же
    непроверяемый адрес станет способом обойти все правила файла разом.
    """
    if JINJA_STATEMENT.search(raw):
        return None
    variants = [""]
    position = 0
    for match in JINJA_EXPRESSION.finditer(raw):
        branches = _expression_branches(match.group(1))
        if branches is None:
            return None
        head = raw[position : match.start()]
        variants = [variant + head + branch for variant in variants for branch in branches]
        position = match.end()
    tail = raw[position:]
    return tuple(sorted({variant + tail for variant in variants}))


class ActionSite(NamedTuple):
    template: str
    raw: str
    paths: tuple[str, ...] | None


def _action_sites(templates: list[tuple[str, str]]) -> list[ActionSite]:
    """Адреса действия форм с признаком отправки htmx, вместе с их путями.

    ОДИН обход собирает и адреса, и — через ``FRAGMENT_ROUTES`` — множество, с
    которым они сверяются. Этим гейт замкнут на себя: форма, добавленная
    будущей фазой, попадает в проверяемое множество тем же способом, что и
    сегодняшняя, а не через отдельный перечень, который можно забыть пополнить.
    """
    sites: list[ActionSite] = []
    for site in _post_sites(templates):
        raw = _attr_value(site.tag, ACTION_VALUE) or ""
        sites.append(ActionSite(site.template, raw, _literal_paths(raw)))
    return sites


def _extracted_paths(templates: list[tuple[str, str]]) -> set[str]:
    return {
        path for site in _action_sites(templates) if site.paths for path in site.paths
    }


def _offenders_unknown_action(templates: list[tuple[str, str]]) -> dict[str, str]:
    """Адрес действия, чей путь не поддаётся извлечению из шаблона."""
    offenders: dict[str, str] = {}
    for site in _action_sites(templates):
        if site.paths is None:
            offenders[site.template] = f"{site.raw!r}: путь не извлекается"
            continue
        for path in site.paths:
            if not path.startswith("/"):
                offenders[f"{site.template}:{path}"] = "путь не начинается с корня"
            elif any(
                segment != PARAM and PARAM in segment for segment in path.split("/")
            ):
                offenders[f"{site.template}:{path}"] = (
                    "величина подставлена внутрь сегмента, а не сегментом целиком"
                )
    return offenders


def _offenders_action_is_not_a_route(templates: list[tuple[str, str]]) -> dict[str, str]:
    declared = {route.path for route in PAGE_ROUTES if route.method == "POST"}
    offenders: dict[str, str] = {}
    for site in _action_sites(templates):
        for path in site.paths or ():
            if path not in declared:
                offenders[f"{site.template}:{path}"] = "объявления маршрута нет"
    return offenders


def _offenders_action_hits_a_fragment_route(
    templates: list[tuple[str, str]],
) -> set[str]:
    fragments = {route.path for route in FRAGMENT_ROUTES}
    return _extracted_paths(templates) & fragments


def test_the_number_of_fragment_routes_is_the_declared_one() -> None:
    """Маршрутов, отдающих только фрагмент, ровно ``FRAGMENT_ROUTES_DECLARED``.

    Инвентарное утверждение, без которого пересечение ниже вакуумно. Сломанный
    разбор страничного слоя — опечатка в имени декоратора, потерянный префикс
    роутера, неверно посчитанная достижимость — даёт пустое множество, пустое
    пересечение и зелёный цвет, посимвольно совпадающий с зелёным цветом
    соблюдённого правила. Только собственное число различает их (D-13).

    Отдельно утверждается, что число НЕ НУЛЬ: ноль здесь означал бы не
    «фрагментных маршрутов в проекте нет» — их видно глазами в разделе
    аккаунтов и в порциях бесконечной подгрузки, — а «обход их не находит».
    """
    assert FRAGMENT_ROUTES_DECLARED > 0, (
        "объявленное число фрагментных маршрутов равно нулю: в проекте они "
        "есть, и ноль здесь означал бы сломанный разбор, а не пустое множество"
    )
    assert len(FRAGMENT_ROUTES) == FRAGMENT_ROUTES_DECLARED, (
        f"фрагментных маршрутов найдено {len(FRAGMENT_ROUTES)}, объявлено "
        f"{FRAGMENT_ROUTES_DECLARED}: {sorted(FRAGMENT_ROUTES)} — маршрут "
        f"потерял путь деградации, приобрёл его, либо разбор страничного слоя "
        f"перестал их находить"
    )
    assert len(PAGE_ROUTES) > len(FRAGMENT_ROUTES), (
        "фрагментными опознаны ВСЕ маршруты страничного слоя — признак пути "
        "деградации не срабатывает ни на одном обработчике"
    )


def test_every_action_path_is_a_declared_route() -> None:
    """Каждый извлечённый путь адреса действия — объявленный маршрут POST.

    Адрес действия, ведущий в никуда, при отключённом JS даёт четырёхсотчетвёртую
    страницу вместо результата, и на пути с JS это не видно вовсе: там адрес
    берётся из соседнего атрибута, и опечатка в ``action`` не проявляется ничем
    до тех пор, пока кто-нибудь не выключит JS.
    """
    offenders = _offenders_action_is_not_a_route(_all_templates())
    assert not offenders, (
        f"адрес действия формы не соответствует ни одному объявлению маршрута "
        f"POST страничного слоя: {offenders} — без JS такая форма уходит в "
        f"никуда"
    )


def test_no_action_path_leads_to_a_fragment_route() -> None:
    """G-5: адрес действия не ведёт на маршрут, отдающий только фрагмент.

    Без JS браузер показывает ответ маршрута ЦЕЛИКОМ и как документ. Фрагмент,
    собранный для подмены куска страницы, окажется всей страницей: без
    навигации, без шелла и без области уведомления, со статусом 200 — то есть
    ни один автоматический признак отказа не сработает, и увидит это только
    человек.
    """
    hits = _offenders_action_hits_a_fragment_route(_all_templates())
    assert not hits, (
        f"адрес действия ведёт на маршрут, отдающий только фрагмент: "
        f"{sorted(hits)} — человек без JS попадёт на голый кусок разметки вне "
        f"шелла, и статус ответа при этом будет двухсотым"
    )


def test_no_action_is_assembled_from_an_unknown_value() -> None:
    """Адрес действия обязан быть извлекаемым из шаблона.

    Утверждение о ГРАНИЦЕ САМОГО ГЕЙТА, а не о разметке. Путь, собранный во
    время исполнения из величины, значение которой шаблону неизвестно, гейт
    прочитать не может — и потому запрещает: непроверяемый адрес был бы
    способом обойти и правило существования маршрута, и правило полного
    документа разом, не уронив ни одного теста.

    Величина внутри пути при этом разрешена и извлекается как ПАРАМЕТР
    СЕГМЕНТА: единственная сегодняшняя форма подставляет идентификатор
    объявления между двумя литеральными кусками пути, и обе её ветви
    извлекаются целиком.
    """
    offenders = _offenders_unknown_action(_all_templates())
    assert not offenders, (
        f"адрес действия не поддаётся извлечению из шаблона: {offenders} — "
        f"такой адрес непроверяем ни одним правилом этого файла"
    )


def test_both_branches_of_the_editor_action_are_extracted() -> None:
    """Из условного адреса действия извлечены ОБЕ ветви, а не первая.

    Утверждение о РАЗБОРЕ, и потому отдельное от правил. Значение адреса
    единственной сегодняшней формы есть условное выражение с двумя ветвями —
    правка существующей записи и создание новой. Разборщик, берущий первую
    ветвь, оставил бы вторую непроверенной ни одним правилом выше, а общий
    счёт мест при этом остался бы верным.
    """
    paths = _extracted_paths(_all_templates())
    assert len(paths) == 2, (
        f"из адресов действия извлечено путей: {sorted(paths)} — ожидались обе "
        f"ветви условного выражения единственной формы"
    )
    assert all(path.startswith("/") for path in paths)
    assert any(PARAM in path for path in paths), (
        f"ни один извлечённый путь не несёт параметра сегмента: {sorted(paths)} "
        f"— ветвь правки существующей записи адресуется идентификатором, и её "
        f"отсутствие означает, что разобрана только ветвь создания"
    )


# --- ИНВЕНТАРЬ СВОПА, ВНЕПОЛОСНЫХ БЛОКОВ И КЛИЕНТСКОГО СОСТОЯНИЯ -------------
#
# Продолжение летописи чисел. Три величины ниже собраны собственным обходом
# этого файла и сверены с планированием фазы; расхождений не было.

# Целей подмены в проекте сегодня НЕ ОБЪЯВЛЕНО НИ ОДНОЙ. Ноль объявляется
# ИМЕНОВАННОЙ КОНСТАНТОЙ, а не выводится из пустого множества: без числа
# правила существования цели и границы клиентского состояния были бы вакуумно
# зелёными навсегда, и первая же цель, добавленная Фазой 9, вошла бы в проект
# ни одним правилом не проверенной. Прецедент формы — SERVER_SIDE_VALIDATION_RESPONSES.
HX_TARGETS = 0

# Внеполосных блоков шесть: три собирает ответ автосохранения редактора
# объявлений, четвёртый — индикатор состояния, чей признак выставляется ВЕТКОЙ
# ШАБЛОНИЗАТОРА внутри открывающего тега (обход обязан увидеть и его, иначе
# инвентарь недосчитает один из шести), и два — внеполосная форма уведомления,
# заведённая планом 08-04.
OOB_BLOCKS = 6

# Узлов с признаком клиентского состояния двадцать четыре. Двадцать пятое
# текстовое вхождение имени этого атрибута живёт в Jinja-комментарии
# компонента модального окна (образец вызова) и вырезается до счёта.
CLIENT_STATE_NODES = 24

# ⚠️ ПРАВИЛО ПОДМЕНЫ СОДЕРЖИМОГО ОТНОСИТСЯ ТОЛЬКО К ЭТИМ ДВУМ
# ИДЕНТИФИКАТОРАМ, И ГРАНИЦА ОБЪЯВЛЕНА ПЕРЕЧНЕМ ИМЕННО ЗАТЕМ, ЧТОБЫ ЕЁ НЕ
# РАСШИРИЛИ. Области уведомления живут в ШЕЛЛЕ и обязаны пережить любое число
# ответов: унесённая подменой узла область лишает цели ВСЕ последующие ответы,
# и молча — о ненайденной цели свопа браузер не сообщает ничем.
#
# Четыре внеполосных блока редактора объявлений подменяют УЗЕЛ осознанно: их
# цели — собственные узлы фрагмента, который ответ собирает целиком и заменяет
# целиком, а не общая область шелла, живущая дольше ответа. Правило,
# распространённое на них, покраснело бы на работающем коде и было бы снято
# первым же коммитом — то есть защищало бы ноль минут. Граница выписана словами
# и в самом шаблоне внеполосной формы уведомления (план 08-04).
NOTICE_REGION_IDS = ("notice", "notice-alert")

HX_SWAP_OOB_ATTR = _attr_pattern("hx-swap-oob")
HX_SWAP_OOB_TAG = _tag_pattern("hx-swap-oob")
HX_SWAP_OOB_VALUE = _value_pattern("hx-swap-oob")

HX_TARGET_ATTR = _attr_pattern("hx-target")
HX_TARGET_TAG = _tag_pattern("hx-target")
HX_TARGET_VALUE = _value_pattern("hx-target")

HX_SWAP_VALUE = _value_pattern("hx-swap")
ID_VALUE = _value_pattern("id")
ID_OCCURRENCE = re.compile(r"(?<![-\w])id\s*=\s*\"([^\"]*)\"")

# Признак клиентского состояния объявляется и БЕЗ значения (голым атрибутом на
# теге формы — самая частая его форма в проекте), поэтому у него собственная
# пара выражений: общая, требующая знака равенства, потеряла бы двадцать из
# двадцати четырёх узлов и оставила бы границу клиентского состояния вакуумной.
CLIENT_STATE_ATTR = re.compile(r"(?<![-\w])x-data(?![-\w])")
CLIENT_STATE_TAG = re.compile(r"<[^<>]*?(?<![-\w])x-data(?![-\w])[^<>]*>")

# Умолчание рантайма для внеполосного блока — подмена УЗЛА; значение «true»
# есть его синоним, и приводится к нему здесь, чтобы правило содержимого
# сравнивало способы подмены, а не написания.
NODE_SWAP = "outerHTML"
CONTENT_SWAP = "innerHTML"
NO_SWAP = "none"

# Открывающая ветка шаблонизатора ВНУТРИ тега — признак атрибута, собранного
# условием. Ровно этой формой объявлен шестой внеполосный блок проекта.
JINJA_CONDITION = re.compile(r"\{%-?\s*if\b")

# Относительные формы цели («этот», «ближайший …», «следующий …») адресуют узел
# от места объявления, а не по идентификатору: существование такой цели по
# исходнику не проверяется и проверяться не может. Они названы ПЕРЕЧНЕМ, а не
# пропущены остаточным признаком: незаявленная форма цели обязана быть
# замечена, а не отнесена к относительным по тому, что не начинается с решётки.
RELATIVE_TARGET_PREFIXES = ("this", "closest ", "find ", "next", "previous", "body", "document", "window")


def _oob_sites(templates: list[tuple[str, str]]) -> list[Site]:
    return _sites(templates, HX_SWAP_OOB_TAG)


def _target_sites(templates: list[tuple[str, str]]) -> list[Site]:
    return _sites(templates, HX_TARGET_TAG)


def _client_state_sites(templates: list[tuple[str, str]]) -> list[Site]:
    return _sites(templates, CLIENT_STATE_TAG)


def _id_occurrences(templates: list[tuple[str, str]]) -> dict[str, int]:
    """Сколько раз каждый ЛИТЕРАЛЬНЫЙ идентификатор объявлен в дереве.

    Идентификаторы, собранные шаблонизатором (``{{ … }}``), из счёта исключены:
    их значение известно только в момент рендера, и сверять с ними цель подмены
    нечем. Граница названа в докстринге правила существования цели.
    """
    counts: dict[str, int] = {}
    for _, source in templates:
        for value in ID_OCCURRENCE.findall(_strip_comments(source)):
            if "{{" in value or "{%" in value:
                continue
            counts[value] = counts.get(value, 0) + 1
    return counts


def _oob_target(tag: str) -> tuple[str, str | None]:
    """Способ подмены внеполосного блока и идентификатор его цели.

    Цель объявляется ДВУМЯ способами, и оба законны: селектором прямо в
    значении признака (``способ:#цель``) либо собственным идентификатором
    несущего тега. Второй способ — умолчание рантайма, и именно поэтому блок
    без идентификатора и без селектора игнорируется молча: цели у него нет
    вовсе, а сообщения об этом не будет ни в консоли, ни в ответе.
    """
    raw = _attr_value(tag, HX_SWAP_OOB_VALUE) or ""
    head, _, selector = raw.partition(":")
    mode = head.strip() or "true"
    if mode.lower() == "true":
        mode = NODE_SWAP
    selector = selector.strip()
    if selector:
        return mode, selector[1:] if selector.startswith("#") else None
    return mode, _attr_value(tag, ID_VALUE) or None


def _swap_target_ids(templates: list[tuple[str, str]]) -> set[str]:
    """Идентификаторы, объявленные целями подмены, — ТЕМ ЖЕ обходом.

    ⚠️ ЭТИМ ГЕЙТ ЗАМКНУТ НА СЕБЯ. Множество целей собирается той же функцией,
    которой пользуются правило существования цели, правило двух ролей и граница
    клиентского состояния. Второй перечень целей, выписанный руками, разошёлся
    бы с этим молча: цель, добавленная будущей фазой на узел с клиентским
    состоянием, попала бы в разметку и не попала бы в перечень, и граница
    осталась бы зелёной ровно там, где её впервые нарушили.
    """
    found: set[str] = set()
    for site in _target_sites(templates):
        value = (_attr_value(site.tag, HX_TARGET_VALUE) or "").strip()
        if value.startswith("#"):
            found.add(value[1:])
    return found


def _oob_target_ids(templates: list[tuple[str, str]]) -> set[str]:
    return {
        target
        for site in _oob_sites(templates)
        if (target := _oob_target(site.tag)[1]) is not None
    }


def _client_state_ids(templates: list[tuple[str, str]]) -> set[str]:
    """Литеральные идентификаторы узлов с признаком клиентского состояния.

    Идентификатор, СОБРАННЫЙ шаблонизатором, из множества исключён по той же
    причине, что и в счёте объявлений: сверять с ним цель подмены нечем, его
    значение известно только в момент рендера. Сегодня таких узлов в проекте
    большинство (компонент отбора и компонент модального окна принимают
    идентификатор параметром макроса), поэтому множество литеральных целей
    клиентского состояния пусто — и именно поэтому число узлов объявлено
    отдельной константой: без него граница была бы вакуумной дважды.
    """
    found: set[str] = set()
    for site in _client_state_sites(templates):
        own = _attr_value(site.tag, ID_VALUE)
        if own and "{{" not in own and "{%" not in own:
            found.add(own)
    return found


# --- ПРАВИЛА СВОПА И ВНЕПОЛОСНЫХ БЛОКОВ (G-7, G-9, G-10, G-11, G-12) ---------


def _offenders_swap_is_declared(templates: list[tuple[str, str]]) -> dict[str, str]:
    """G-7: у места отправки объявлена цель ЛИБО явное отсутствие подмены."""
    offenders: dict[str, str] = {}
    for site in _post_sites(templates):
        has_target = _attr_value(site.tag, HX_TARGET_VALUE) is not None
        swap = (_attr_value(site.tag, HX_SWAP_VALUE) or "").strip().lower()
        if not has_target and swap != NO_SWAP:
            offenders[site.template] = f"цели нет, способ подмены {swap!r}"
    return offenders


def _offenders_target_does_not_exist(templates: list[tuple[str, str]]) -> dict[str, str]:
    """G-9: цель подмены существует в разметке."""
    ids = _id_occurrences(templates)
    offenders: dict[str, str] = {}
    for site in _target_sites(templates):
        value = (_attr_value(site.tag, HX_TARGET_VALUE) or "").strip()
        if "{{" in value or "{%" in value:
            continue
        if value.startswith("#"):
            if value[1:] not in ids:
                offenders[f"{site.template}:{value}"] = "такого идентификатора в разметке нет"
            continue
        if not any(value.startswith(prefix) for prefix in RELATIVE_TARGET_PREFIXES):
            offenders[f"{site.template}:{value}"] = "незаявленная форма цели"
    return offenders


def _offenders_oob_without_id(templates: list[tuple[str, str]]) -> dict[str, str]:
    """G-10: внеполосный блок несёт идентификатор цели."""
    return {
        f"{site.template}:{index}": site.tag[:120]
        for index, site in enumerate(_oob_sites(templates))
        if _oob_target(site.tag)[1] is None
    }


def _offenders_id_in_two_roles(templates: list[tuple[str, str]]) -> set[str]:
    """G-11: идентификатор не бывает целью подмены и внеполосной целью разом."""
    return _swap_target_ids(templates) & _oob_target_ids(templates)


def _offenders_notice_region_by_node(templates: list[tuple[str, str]]) -> dict[str, str]:
    """Область уведомления подменяется СОДЕРЖИМЫМ, а не узлом."""
    offenders: dict[str, str] = {}
    for site in _oob_sites(templates):
        mode, target = _oob_target(site.tag)
        if target in NOTICE_REGION_IDS and mode != CONTENT_SWAP:
            offenders[f"{site.template}:{target}"] = f"способ подмены {mode!r}"
    return offenders


def _offenders_client_state_is_a_target(templates: list[tuple[str, str]]) -> set[str]:
    """G-12: узел с признаком клиентского состояния не является целью подмены."""
    return _client_state_ids(templates) & _swap_target_ids(templates)


def test_every_htmx_post_declares_its_swap_target_or_its_absence() -> None:
    """G-7: объявлена цель подмены либо ЯВНОЕ её отсутствие.

    Умолчание рантайма — «этот же элемент». Для формы это означает, что ответ
    сервера подменит собой саму форму: поле ввода уедет вместе с кареткой и
    выделением, а на пути автосохранения человек физически не сможет набрать
    длинный текст. Умолчание, съедающее собственную форму, обязано быть
    невыразимым — либо цель названа, либо отсутствие подмены объявлено словом.
    """
    offenders = _offenders_swap_is_declared(_all_templates())
    assert not offenders, (
        f"место отправки htmx не объявило ни цели подмены, ни явного её "
        f"отсутствия: {offenders} — умолчание рантайма подменит форму её же "
        f"ответом и сбросит каретку"
    )


def test_the_number_of_swap_targets_is_the_declared_one() -> None:
    """Целей подмены ровно ``HX_TARGETS``, и парный контроль обхода сходится.

    Число объявлено ИМЕНОВАННОЙ КОНСТАНТОЙ, хотя оно и ноль. Без него правило
    существования цели, правило двух ролей и граница клиентского состояния
    остались бы вакуумно зелёными навсегда: пустое множество удовлетворяет их
    все, и отличить «целей нет» от «обход целей не находит» было бы нечем.
    """
    templates = _all_templates()
    sites = _target_sites(templates)
    assert _attribute_count(templates, HX_TARGET_ATTR) == len(sites), (
        "число тегов, несущих цель подмены, разошлось с числом вхождений "
        "самого атрибута — ошибка разбора границ тега"
    )
    assert len(sites) == HX_TARGETS, (
        f"целей подмены найдено {len(sites)}, объявлено {HX_TARGETS}: "
        f"{[site.template for site in sites]} — цель появилась или исчезла, а "
        f"летопись чисел этого файла об этом не знает"
    )


def test_every_swap_target_points_at_an_existing_id() -> None:
    """G-9: цель подмены существует в разметке.

    Опечатка в цели даёт подмену «в никуда»: ответ приезжает, подменять нечего,
    и НИ ОДНОГО сообщения об этом не появляется — ни в консоли, ни в ответе, ни
    в статусе. Отличить это от «сервер ничего не вернул» на глаз нельзя.

    Существование проверяется по ВСЕМУ дереву шаблонов, а не по документу,
    который собирает конкретный маршрут: обход не разворачивает наследование и
    включения. Цель, объявленная в шаблоне, который на этой странице не
    подключается, здесь пройдёт — граница названа в перечне «чего гейт не
    видит» и требует решения человека, если такой случай появится.
    """
    offenders = _offenders_target_does_not_exist(_all_templates())
    assert not offenders, (
        f"цель подмены не существует в разметке или объявлена незаявленной "
        f"формой: {offenders} — подмена «в никуда» не сообщает о себе ничем"
    )


def test_the_number_of_oob_blocks_is_the_declared_one() -> None:
    """Внеполосных блоков ровно ``OOB_BLOCKS``, и парный контроль сходится.

    Шестой блок собирается ВЕТКОЙ ШАБЛОНИЗАТОРА внутри открывающего тега
    индикатора автосохранения. Обход обязан увидеть и его: разбор, спотыкающийся
    о ветку внутри тега, недосчитал бы один из шести, и правило идентификатора
    ниже не проверило бы именно тот блок, который собран самым хитрым способом.
    """
    templates = _all_templates()
    sites = _oob_sites(templates)
    offenders: dict[str, str] = {}
    for rel, source in templates:
        body = _strip_comments(source)
        attributes = len(HX_SWAP_OOB_ATTR.findall(body))
        tags = len(HX_SWAP_OOB_TAG.findall(body))
        if attributes != tags:
            offenders[rel] = f"вхождений атрибута {attributes}, тегов {tags}"
    assert not offenders, (
        f"число внеполосных тегов разошлось с числом вхождений атрибута: "
        f"{offenders} — ошибка разбора границ тега"
    )
    assert len(sites) == OOB_BLOCKS, (
        f"внеполосных блоков найдено {len(sites)}, объявлено {OOB_BLOCKS}: "
        f"{sorted({site.template for site in sites})}"
    )

    # Блок, СОБРАННЫЙ ВЕТКОЙ ШАБЛОНИЗАТОРА, утверждается отдельно и по имени.
    # Общее число этого не доказывает: недосчитанный блок с условием и лишний
    # блок где-то ещё дали бы ту же сумму, и инвентарь остался бы зелёным при
    # непроверенном шестом блоке.
    conditional = [site for site in sites if JINJA_CONDITION.search(site.tag)]
    assert len(conditional) == 1, (
        f"внеполосных блоков, собранных веткой шаблонизатора внутри тега, "
        f"найдено {len(conditional)}, ожидался один (индикатор состояния "
        f"автосохранения): {[site.template for site in conditional]} — разбор "
        f"спотыкается о ветку внутри открывающего тега, и один из шести блоков "
        f"ни одним правилом ниже не проверен"
    )


def test_every_oob_block_carries_an_id() -> None:
    """G-10: у каждого внеполосного блока есть цель по идентификатору.

    Блок без идентификатора и без селектора рантайм игнорирует МОЛЧА: он не
    ошибка ответа и не ошибка разметки, он просто ничего не делает. Обнаружить
    это можно только заметив, что кусок экрана перестал обновляться.
    """
    offenders = _offenders_oob_without_id(_all_templates())
    assert not offenders, (
        f"внеполосный блок не объявил цели ни идентификатором тега, ни "
        f"селектором: {offenders} — рантайм молча его игнорирует"
    )


def test_no_id_is_both_a_swap_target_and_an_oob_target() -> None:
    """G-11: идентификатор не бывает целью подмены и внеполосной целью разом.

    Один узел, подменяемый и основным свопом, и внеполосным блоком того же
    ответа, получает две подмены подряд в порядке, который разметкой не задан.
    Вторая перетирает первую, позиция прокрутки теряется, и воспроизводится это
    через раз.
    """
    conflicts = _offenders_id_in_two_roles(_all_templates())
    assert not conflicts, (
        f"идентификатор объявлен и целью подмены, и внеполосной целью: "
        f"{sorted(conflicts)} — узел подменяется дважды за один ответ"
    )


def test_the_notice_regions_are_replaced_by_content_not_by_node() -> None:
    """Области уведомления подменяются СОДЕРЖИМЫМ, а не узлом.

    ⚠️ ПРАВИЛО ПРИМЕНЯЕТСЯ ТОЛЬКО К ИДЕНТИФИКАТОРАМ ИЗ ``NOTICE_REGION_IDS``, И
    ЭТО ГРАНИЦА, А НЕ ПОСЛАБЛЕНИЕ. Область уведомления живёт в шелле и обязана
    пережить любое число ответов: унесённая подменой узла один раз, она лишает
    цели все последующие — молча, потому что о ненайденной цели свопа рантайм
    не сообщает ничем.

    Четыре внеполосных блока редактора объявлений подменяют узел ОСОЗНАННО: их
    цели — собственные узлы фрагмента, который ответ собирает и заменяет
    целиком. Гейт, распространённый на них, покраснел бы на работающем коде и
    был бы снят первым же коммитом — то есть защищал бы ноль минут.
    """
    templates = _all_templates()
    offenders = _offenders_notice_region_by_node(templates)
    assert not offenders, (
        f"внеполосный блок подменяет УЗЕЛ области уведомления, а не её "
        f"содержимое: {offenders} — область уедет из документа, и все "
        f"последующие ответы останутся без цели"
    )

    # ГРАНИЦА УТВЕРЖДАЕТСЯ, А НЕ ПОДРАЗУМЕВАЕТСЯ. Правило выше зелено в том
    # числе потому, что в дереве ЕСТЬ внеполосные блоки, подменяющие узел, и
    # оно их сознательно не трогает. Без этого утверждения нельзя отличить
    # «граница проведена верно» от «блоков с подменой узла в проекте не
    # осталось вовсе», а во втором случае правило снова становится вакуумным.
    node_swaps = {
        site.template
        for site in _oob_sites(templates)
        if _oob_target(site.tag)[0] == NODE_SWAP
    }
    assert node_swaps, (
        "в дереве не осталось ни одного внеполосного блока, подменяющего узел "
        "— граница правила потеряла предмет, и снимать её следует ЯВНО, вместе "
        "с записью в летописи чисел"
    )
    assert not (node_swaps & {NOTICE_OOB}), (
        f"подмена узла объявлена во внеполосной форме уведомления: {node_swaps}"
    )


def test_every_notice_region_is_declared_once() -> None:
    """Каждая область уведомления объявлена в разметке ровно один раз.

    Две области с одним идентификатором означают молчание на базовом пути:
    подмена найдёт первую, а человек будет смотреть на вторую — и никакого
    признака отказа при этом не появится.
    """
    ids = _id_occurrences(_all_templates())
    offenders = {
        region: ids.get(region, 0)
        for region in NOTICE_REGION_IDS
        if ids.get(region, 0) != 1
    }
    assert not offenders, (
        f"область уведомления объявлена в разметке не один раз: {offenders} — "
        f"ноль означает, что цели внеполосной подмены не существует вовсе, "
        f"два и более — что подмена найдёт не ту область, на которую смотрит "
        f"человек"
    )


def test_the_number_of_client_state_nodes_is_the_declared_one() -> None:
    """Узлов с признаком клиентского состояния ровно ``CLIENT_STATE_NODES``.

    Инвентарь, без которого граница ниже вакуумна: сломанный обход даёт пустое
    множество узлов, пустое пересечение с целями и зелёный цвет, неотличимый от
    соблюдённого правила.
    """
    templates = _all_templates()
    sites = _client_state_sites(templates)
    attributes = sum(
        len(CLIENT_STATE_ATTR.findall(_strip_comments(source))) for _, source in templates
    )
    assert attributes == len(sites), (
        f"вхождений признака клиентского состояния {attributes}, несущих его "
        f"тегов {len(sites)} — ошибка разбора границ тега"
    )
    assert len(sites) == CLIENT_STATE_NODES, (
        f"узлов с клиентским состоянием найдено {len(sites)}, объявлено "
        f"{CLIENT_STATE_NODES}"
    )


def test_no_client_state_node_is_a_swap_target() -> None:
    """G-12: узел с клиентским состоянием не является целью подмены.

    Подмена уносит узел вместе с его клиентским состоянием: открытая панель
    закроется, набранное в ней потеряется, а фокус уедет в начало документа.
    Ничего из этого не является ошибкой ни для одной автоматической проверки.

    ⚠️ Множество целей собирается ТЕМ ЖЕ обходом, которым проверяется правило
    (``_swap_target_ids``), — этим гейт замкнут на себя: цель, добавленная
    будущей фазой на узел с клиентским состоянием, краснеет сама, без правки
    какого-либо перечня. Вложенность при этом НЕ учитывается: узел-потомок
    узла с клиентским состоянием целью быть может, и это записано в перечне
    «чего гейт не видит».
    """
    conflicts = _offenders_client_state_is_a_target(_all_templates())
    assert not conflicts, (
        f"целью подмены объявлен узел с признаком клиентского состояния: "
        f"{sorted(conflicts)} — подмена унесёт узел вместе с его состоянием"
    )


# --- ГРУППА КОНТРОЛЯ ---------------------------------------------------------
#
# Зубы гейта ДОКАЗЫВАЮТСЯ, а не заявляются. Каждый случай ниже подаёт обходу
# изменённую копию дерева шаблонов во временном каталоге и требует, чтобы
# правило на ней покраснело. Настоящее дерево при этом не трогается ни одним
# байтом: подстановки применяются к прочитанным исходникам, а пишется копия.
#
# ⚠️ ПОДСТАНОВКА ОБЯЗАНА ДОКАЗАТЬ, ЧТО ОНА ЧТО-ТО ИЗМЕНИЛА, И ЧТО ИЗМЕНИЛА
# ИМЕННО ТО. Контроль, чей образец в шаблоне не нашёлся, «проходит» на
# нетронутом дереве и утверждает ровно ничего — то есть притворяется
# доказательством зубов, не будучи им. Хуже того, образец, встретившийся
# ДВАЖДЫ, меняет не то место, что имел в виду автор, и контроль краснеет по
# чужой причине. Поэтому ``_tree_with`` требует РОВНО ОДНОГО вхождения образца
# и отдельно проверяет, что результат отличается от исходника.


class Substitution(NamedTuple):
    template: str
    old: str
    new: str


def _tree_with(tmp_path: Path, *substitutions: Substitution) -> Path:
    """Копия дерева шаблонов с подстановками, во временном каталоге."""
    sources = dict(_all_templates())
    for substitution in substitutions:
        assert substitution.template in sources, (
            f"шаблон {substitution.template} в дереве не найден: контроль "
            f"подаёт подстановку в несуществующий файл и потому ничего не "
            f"доказывает"
        )
        source = sources[substitution.template]
        occurrences = source.count(substitution.old)
        assert occurrences == 1, (
            f"образец подстановки встречается в {substitution.template} "
            f"{occurrences} раз(а), а не один: {substitution.old!r} — контроль "
            f"меняет не то место, что имел в виду автор, либо не меняет ничего"
        )
        changed = source.replace(substitution.old, substitution.new)
        assert changed != source, (
            f"подстановка в {substitution.template} ничего не изменила: "
            f"{substitution.old!r} → {substitution.new!r}"
        )
        sources[substitution.template] = changed

    root = tmp_path / "templates"
    for rel, source in sources.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    return root


FORM = "ads/form.html"
AUTOSAVE_RESPONSE = "ads/includes/autosave_response.html"
NOTICE_OOB = "includes/notice_oob.html"
FILTERS = "components/filters.html"

FORM_OPEN = '<form id="ad-form"\n          method="post"\n'
FORM_CLOSE = 'hx-swap="none">'
EDITOR_ACTION = "action=\"{{ '/ads/' ~ ad.id ~ '/edit' if ad else '/ads/new' }}\""
EDITOR_POST = "hx-post=\"{{ '/ads/' ~ ad.id ~ '/edit' if ad else '/ads/new' }}\""


def test_control_negative_a_form_without_a_method_reddens_the_gate(tmp_path: Path) -> None:
    """Форма без метода: без JS браузеру нечем её отправить."""
    root = _tree_with(tmp_path, Substitution(FORM, FORM_OPEN, '<form id="ad-form"\n'))
    assert _offenders_method_and_action(_all_templates(root)), (
        "форма с признаком отправки htmx осталась без метода, и правило "
        "деградации этого не заметило"
    )


def test_control_negative_an_action_off_by_one_character_reddens_the_gate(
    tmp_path: Path,
) -> None:
    """Адрес запроса разошёлся с адресом действия на один символ."""
    root = _tree_with(
        tmp_path,
        Substitution(
            FORM,
            EDITOR_POST,
            "hx-post=\"{{ '/ads/' ~ ad.id ~ '/edits' if ad else '/ads/new' }}\"",
        ),
    )
    assert _offenders_post_matches_action(_all_templates(root)), (
        "адрес запроса и адрес действия разошлись на один символ, и правило "
        "посимвольного совпадения этого не заметило — то есть путь с JS и путь "
        "без JS ведут в разные места"
    )


def test_control_negative_a_post_attribute_on_a_button_reddens_the_gate(
    tmp_path: Path,
) -> None:
    """Признак отправки на кнопке: без JS это мёртвая кнопка."""
    root = _tree_with(
        tmp_path,
        Substitution(
            FORM,
            FORM_CLOSE,
            FORM_CLOSE + '\n      <button type="button" hx-post="/ads/new">Сохранить</button>',
        ),
    )
    assert _offenders_tag_is_a_form(_all_templates(root)), (
        "признак отправки оказался на теге кнопки, и правило тега формы этого "
        "не заметило"
    )


def test_control_negative_an_action_on_a_fragment_route_reddens_the_gate(
    tmp_path: Path,
) -> None:
    """Адрес действия ведёт на маршрут, отдающий только фрагмент."""
    root = _tree_with(
        tmp_path,
        Substitution(FORM, EDITOR_ACTION, 'action="/ads/partial"'),
        Substitution(FORM, EDITOR_POST, 'hx-post="/ads/partial"'),
    )
    assert _offenders_action_hits_a_fragment_route(_all_templates(root)), (
        "адрес действия увёл на маршрут фрагмента, и G-5 этого не заметил — "
        "человек без JS получил бы голый кусок разметки со статусом 200"
    )


def test_control_negative_a_place_without_a_declared_swap_reddens_the_gate(
    tmp_path: Path,
) -> None:
    """Место отправки без цели и без явного отсутствия подмены."""
    root = _tree_with(tmp_path, Substitution(FORM, '\n          ' + FORM_CLOSE, ">"))
    assert _offenders_swap_is_declared(_all_templates(root)), (
        "место отправки осталось без цели и без явного отсутствия подмены, и "
        "G-7 этого не заметил — умолчание рантайма съело бы собственную форму"
    )


def test_control_negative_a_target_pointing_nowhere_reddens_the_gate(
    tmp_path: Path,
) -> None:
    """Цель подмены указывает на несуществующий идентификатор."""
    root = _tree_with(
        tmp_path,
        Substitution(
            FORM, FORM_CLOSE, 'hx-swap="none"\n          hx-target="#no-such-node">'
        ),
    )
    assert _offenders_target_does_not_exist(_all_templates(root)), (
        "цель подмены указала на несуществующий идентификатор, и G-9 этого не "
        "заметил — подмена «в никуда» не сообщает о себе ничем"
    )


def test_control_negative_an_oob_block_without_an_id_reddens_the_gate(
    tmp_path: Path,
) -> None:
    """Внеполосный блок без идентификатора и без селектора."""
    root = _tree_with(
        tmp_path,
        Substitution(
            AUTOSAVE_RESPONSE,
            '<div id="ad-preview" hx-swap-oob="true">',
            '<div hx-swap-oob="true">',
        ),
    )
    assert _offenders_oob_without_id(_all_templates(root)), (
        "внеполосный блок остался без цели, и G-10 этого не заметил — рантайм "
        "молча его игнорирует"
    )


def test_control_negative_one_id_in_two_roles_reddens_the_gate(tmp_path: Path) -> None:
    """Один идентификатор объявлен и целью подмены, и внеполосной целью."""
    root = _tree_with(
        tmp_path,
        Substitution(
            FORM, FORM_CLOSE, 'hx-swap="none"\n          hx-target="#ad-preview">'
        ),
    )
    assert _offenders_id_in_two_roles(_all_templates(root)), (
        "идентификатор оказался в двух ролях сразу, и G-11 этого не заметил — "
        "узел подменялся бы дважды за один ответ"
    )


def test_control_negative_a_notice_region_replaced_by_node_reddens_the_gate(
    tmp_path: Path,
) -> None:
    """Область уведомления объявлена подменой УЗЛА."""
    root = _tree_with(
        tmp_path,
        Substitution(
            NOTICE_OOB,
            '<div hx-swap-oob="innerHTML:#notice-alert">',
            '<div hx-swap-oob="outerHTML:#notice-alert">',
        ),
    )
    assert _offenders_notice_region_by_node(_all_templates(root)), (
        "область уведомления стала подменяться узлом, и правило содержимого "
        "этого не заметило — область уехала бы из документа навсегда"
    )


def test_control_negative_a_client_state_node_as_a_target_reddens_the_gate(
    tmp_path: Path,
) -> None:
    """Узел с клиентским состоянием стал целью подмены.

    Подстановка ЗАМЕНЯЕТ собранный шаблонизатором идентификатор узла на
    литеральный, а не дописывает второй рядом. Первая редакция этого контроля
    дописывала — и была красной: у узла оказалось ДВА признака идентификатора,
    разбор берёт первый, первым остался собранный шаблонизатором, и правило
    честно ответило «литеральных целей клиентского состояния нет». Контроль
    краснел по чужой причине и доказывал не зубы гейта, а собственную
    небрежность в выборе места подстановки.
    """
    root = _tree_with(
        tmp_path,
        Substitution(
            FILTERS,
            'id="{{ id }}"\n         x-data="{ open: false }"',
            'id="filters-panel"\n         x-data="{ open: false }"',
        ),
        Substitution(
            FORM, FORM_CLOSE, 'hx-swap="none"\n          hx-target="#filters-panel">'
        ),
    )
    assert _offenders_client_state_is_a_target(_all_templates(root)), (
        "целью подмены стал узел с клиентским состоянием, и G-12 этого не "
        "заметил — подмена унесла бы узел вместе с его состоянием"
    )


def test_control_negative_an_extra_oob_block_reddens_the_counter(tmp_path: Path) -> None:
    """Лишний внеполосный блок: инвентарное число обязано разойтись.

    Контроль СЧЁТЧИКА, а не правила. Он доказывает, что инвентарь ловит
    появление незаявленного блока — то есть что число собрано обходом, а не
    списано с правил, которые новый блок как раз проходит: у добавленного здесь
    блока и идентификатор на месте, и подмена узлом законна.
    """
    root = _tree_with(
        tmp_path,
        Substitution(
            NOTICE_OOB,
            '<div hx-swap-oob="innerHTML:#notice">',
            '<div id="extra-oob" hx-swap-oob="true">лишний</div>\n'
            '<div hx-swap-oob="innerHTML:#notice">',
        ),
    )
    templates = _all_templates(root)
    assert not _offenders_oob_without_id(templates), (
        "добавленный блок нарушает правило идентификатора — контроль счётчика "
        "покраснел бы по чужой причине"
    )
    assert len(_oob_sites(templates)) == OOB_BLOCKS + 1, (
        "незаявленный внеполосный блок не изменил инвентарного числа — значит "
        "число собрано не обходом"
    )


def test_control_positive_the_untouched_tree_keeps_every_gate_green(
    tmp_path: Path,
) -> None:
    """Настоящее дерево, переписанное во временный каталог, зелено целиком.

    Положительный случай нужен ровно затем, чтобы одиннадцать отрицательных
    что-то значили: правило, красное ВСЕГДА, краснеет и на нарушении. Заодно
    утверждается, что сама пересборка дерева во временном каталоге ничего не
    ломает — иначе любой отрицательный контроль краснел бы от копирования, а не
    от подстановки.
    """
    root = _tree_with(tmp_path)
    templates = _all_templates(root)

    assert len(templates) == len(_all_templates())
    assert not _offenders_tag_is_a_form(templates)
    assert not _offenders_method_and_action(templates)
    assert not _offenders_post_matches_action(templates)
    assert not _offenders_unknown_action(templates)
    assert not _offenders_action_is_not_a_route(templates)
    assert not _offenders_action_hits_a_fragment_route(templates)
    assert not _offenders_swap_is_declared(templates)
    assert not _offenders_target_does_not_exist(templates)
    assert not _offenders_oob_without_id(templates)
    assert not _offenders_id_in_two_roles(templates)
    assert not _offenders_notice_region_by_node(templates)
    assert not _offenders_client_state_is_a_target(templates)

    assert len(_post_sites(templates)) == HX_POST_PLACES
    assert len(_oob_sites(templates)) == OOB_BLOCKS
    assert len(_target_sites(templates)) == HX_TARGETS
    assert len(_client_state_sites(templates)) == CLIENT_STATE_NODES

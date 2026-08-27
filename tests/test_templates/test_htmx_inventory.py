"""Фаза 7, D-18: инвентарь 22 мест ``hx-get`` числом по трём механизмам.

Фаза заменяет рантайм htmx 1.9.10 → 2.0.10 и заводит блок конфигурации. Ни один
``hx-*`` атрибут при этом не правится — но ВСЕ 22 места разметки начинают
исполняться на другом рантайме. Критерий 5 роадмапа («22 места работают на
2.0.10, каскада на infinite scroll нет») закрывается ГЛАЗАМИ по построению:
суита не исполняет ни строчки JS, браузерного стенда в проекте нет и не
заводится. Роадмап говорит это дословно — «зелёная суита здесь не значит
ничего».

Тогда что здесь утверждается. Не поведение — ЧИСЛО. Ручной обход
(``07-UAT.md``) записывает НАБЛЮДЕНИЕ по десяти экранам; этот файл записывает
СОСТАВ того, что обходили. Отметка «обошли 22 места» без второго тихо
устаревает в тот момент, когда следующая фаза добавит двадцать третье, и Фаза
15, собирающая сводное закрытие GATE-09, унаследует старое число как факт.
Гейт держит число, артефакт держит наблюдение, и ни один из двух не
притворяется вторым.

Файл живёт в ``tests/test_templates/``, а не в ``tests/test_pages/``: это гейт
РАЗМЕТКИ, читающий исходники шаблонов, и его канонический образец —
``test_components.py`` (``ROW_DELETE_PLACES``, ``MODAL_PLACES``). Гейты в
``tests/test_pages/test_access_gate.py`` и ``test_impersonation_gate.py`` —
гейты множеств по синтаксическому дереву Python; форма у них другая.
"""

import re
from pathlib import Path
from typing import NamedTuple

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"


class HxGetSite(NamedTuple):
    """Шаблон, несущий места ``hx-get`` одного механизма.

    places — ОЖИДАЕМОЕ число мест в этом шаблоне, а не порог «хотя бы одно».
    Три файла несут по ДВА места: ``accounts/list.html`` и
    ``accounts/partial_cards.html`` — одно ``revealed`` и одно ``every 5s``
    (разные механизмы, поэтому файл стоит в двух перечнях по одному месту), а
    ``accounts/connect_wa.html`` и ``accounts/connect_max.html`` — по ДВА места
    ``every 3s`` в одном файле каждый (ветки состояния подключения). Порог
    «хотя бы одно» растворил бы потерю одной из двух веток подключения: экран
    остался бы зелёным, опрашивая состояние только в одной из них.
    """

    template: str
    places: int


# ЛЕТОПИСЬ ЧИСЕЛ. Перечни ниже выписаны ЗДЕСЬ, а не выведены из проверяемых
# шаблонов: тест, считающий ожидание по коду в момент прогона, согласится с
# любой правкой и молча переживёт исчезновение места — ровно тот отказ, ради
# которого инвентарные гейты в проекте и заведены (прецедент формулировки —
# tests/test_pages/test_access_gate.py:40-43).
#
# ПОПРАВКА РАЗБИВКИ 10/10/2 → 12/8/2 (планирование Фазы 7 против счёта по
# файлам). Планирование Фазы 7 записало в 07-CONTEXT.md (D-14, D-18) разбивку
# 22 мест по механизмам как revealed = 10 / безусловных every Ns = 10 /
# условных = 2. Счёт по файлам дал 12 / 8 / 2 при той же СУММЕ 22: сумма была
# верна, разбивка — нет. Принята величина, полученная счётом, а не перенесённая
# из ожидания; гейт, написанный по CONTEXT.md, был бы красным в момент
# написания. Поправка записана здесь ПЕРВОЙ записью летописи именно как
# поправка: тихо выписать верные числа значило бы стереть свидетельство о том,
# что ожидание разошлось с кодом, — а следующая фаза, увидев здесь 12/8/2 рядом
# с другой разбивкой в 07-CONTEXT.md, не смогла бы понять, какую из двух
# считали.
# Форма записи — с tests/test_templates/test_components.py:757-800, где
# прецедент признания не сбывшегося прогноза уже записан («Ожидание плана 03-05
# "16 → 15" не сбылось… Число проверено счётом по файлам, а не перенесено из
# прогноза»).
#
# Уменьшение объявленных чисел допустимо и означает СОЗНАТЕЛЬНОЕ снятие места,
# записанное следующей записью этой летописи. Молчаливое исчезновение места
# по-прежнему краснеет.

# --- Механизм 1: бесконечная подгрузка, hx-trigger="revealed" (12 мест) ------
#
# Пары «список + карточки списка» несут ОДНУ И ТУ ЖЕ разметку в двух файлах:
# страница отдаёт первую порцию, а порция подгрузки — все следующие. Поэтому
# мест 12, а экранов ручного обхода 6 (07-UAT.md, механизм 1).
REVEALED_SITES = (
    HxGetSite("account_groups/list.html", 1),
    HxGetSite("account_groups/partial_cards.html", 1),
    HxGetSite("accounts/list.html", 1),
    HxGetSite("accounts/partial_cards.html", 1),
    HxGetSite("admin/history_partial_cards.html", 1),
    HxGetSite("admin/user_history.html", 1),
    HxGetSite("ads/list.html", 1),
    HxGetSite("ads/partial_cards.html", 1),
    HxGetSite("history/list.html", 1),
    HxGetSite("history/partial_cards.html", 1),
    HxGetSite("schedules/list.html", 1),
    HxGetSite("schedules/partial_cards.html", 1),
)

REVEALED_PLACES = 12

# --- Механизм 2: поллинг, hx-trigger="every Ns", БЕЗУСЛОВНЫЙ (8 мест) --------
#
# Шесть шаблонов, восемь мест: два экрана подключения несут по два места каждый
# (ветки состояния), и обход обязан увидеть оба.
POLL_SITES = (
    HxGetSite("accounts/connect_max.html", 2),
    HxGetSite("accounts/connect_wa.html", 2),
    HxGetSite("accounts/list.html", 1),
    HxGetSite("accounts/partial_cards.html", 1),
    HxGetSite("admin/workers.html", 1),
    HxGetSite("dashboard.html", 1),
)

POLL_PLACES = 8

# --- Механизм 3: атрибуты СОБРАНЫ Jinja-условием (2 места) -------------------
#
# `{% if status == 'syncing' %} hx-get … {% endif %}` — атрибутов на странице
# нет вовсе, пока карточка не в состоянии синхронизации. Это слепая зона любого
# гейта разметки: гейт видит ИСХОДНИК, где атрибут есть всегда, а пользователь
# видит отрендеренную страницу, где его может не быть. Отсюда прохибиция
# 07-UAT.md: экран, не приведённый в состояние синхронизации, обхода НЕ
# проходил — он показал ту же страницу без атрибутов.
CONDITIONAL_SITES = (
    HxGetSite("account_groups/partials/sync_result.html", 1),
    HxGetSite("accounts/partials/sync_status_card.html", 1),
)

CONDITIONAL_PLACES = 2

HX_GET_PLACES = 22

# ЛОВУШКА СЧЁТА. Наивный поиск строки `hx-trigger="revealed"` по шаблонам даёт
# ТРИНАДЦАТЬ попаданий, а не двенадцать: тринадцатое — прозаический комментарий
# app/templates/base.html:241 («View Transitions отключены: при infinite scroll
# (hx-trigger="revealed") вызывали мерцание и рывки скролла»), места разметки не
# несущий. Гейт обязан считать МЕСТА, несущие `hx-get`, а не вхождения строки,
# иначе он зелен на 13 по совпадению — и совпадение чисел прочиталось бы как
# подтверждение. Прецедент того же класса решения — `_macro_calls()` в
# test_components.py:868-875, где объявление макроса сознательно исключено из
# счёта вызовов.
#
# Обе величины утверждаются СРАЗУ и отдельным тестом: тогда исчезновение
# комментария или появление четырнадцатого вхождения тоже становится видимым, а
# не растворяется в первом числе.
REVEALED_LITERAL_OCCURRENCES = 13

REVEALED_TRIGGER = 'hx-trigger="revealed"'
JINJA_CONDITION_OPEN = re.compile(r"\{%-?\s*if\b")
POLL_TRIGGER = re.compile(r'hx-trigger="every\s')


# --- разборщики исходников ---------------------------------------------------


def _all_templates() -> list[tuple[str, str]]:
    """Все шаблоны проекта парами «путь относительно app/templates — исходник».

    Обход РЕКУРСИВНЫЙ (`rglob`). Плоский обход каталогов не увидел бы 4 из 22
    мест: два места механизма 3 живут в `account_groups/partials/` и
    `accounts/partials/`, плюс `admin/` и прочие подкаталоги. Эта граница в
    проекте уже записана как ИСПРАВЛЕННАЯ, а не как гипотеза — ревизия
    tests/test_pages/test_impersonation_gate.py:61-64 поймала ровно её на
    обходе `*.py` вместо `**/*.py`.
    """
    return [
        (path.relative_to(TEMPLATES_DIR).as_posix(), path.read_text(encoding="utf-8"))
        for path in sorted(TEMPLATES_DIR.rglob("*.html"))
    ]


def _hx_get_lines(source: str) -> list[str]:
    """Строки исходника, несущие `hx-get`. Место = такая строка."""
    return [line for line in source.splitlines() if "hx-get" in line]


def _mechanism_of(line: str) -> str:
    """Механизм места по СТРОКЕ, несущей `hx-get`.

    Порядок разбора значим: сначала `revealed` (механизм 1), затем условность
    (механизм 3 — открывающее Jinja-условие в ТОЙ ЖЕ строке), и только потом
    расписание (механизм 2). Место, не подошедшее ни под один, возвращает
    "unknown" и роняет гейт по имени шаблона: незаявленная форма срабатывания
    обязана быть замечена, а не отнесена к поллингу по остаточному признаку.
    """
    if REVEALED_TRIGGER in line:
        return "revealed"
    if JINJA_CONDITION_OPEN.search(line):
        return "conditional"
    if POLL_TRIGGER.search(line):
        return "poll"
    return "unknown"


def _counted_by_mechanism() -> dict[str, dict[str, int]]:
    """Счёт мест по механизмам: механизм → {шаблон: число мест}."""
    found: dict[str, dict[str, int]] = {
        "revealed": {},
        "conditional": {},
        "poll": {},
        "unknown": {},
    }
    for rel, source in _all_templates():
        for line in _hx_get_lines(source):
            bucket = found[_mechanism_of(line)]
            bucket[rel] = bucket.get(rel, 0) + 1
    return found


def _declared(sites: tuple[HxGetSite, ...]) -> dict[str, int]:
    return {site.template: site.places for site in sites}


def _places(source: str) -> list[str]:
    """Механизмы всех мест исходника, в порядке появления.

    Единственная точка, через которую утверждения о РАЗБОРЕ обращаются к
    разборщикам файла. Она заведена, чтобы контракт разбора («сколько мест и
    какого механизма даёт вот такой исходник») можно было выписать один раз и
    не переписывать при смене самого разборщика: меняется тело этой обёртки,
    а не ожидания тестов.
    """
    return [_mechanism_of(fragment) for fragment in _hx_get_lines(source)]


# --- утверждения -------------------------------------------------------------


def test_inventory_gate_ignores_prose() -> None:
    """Разбор гейта на ПОДСТАВНЫХ исходниках: пять названных случаев.

    Проверяется не разметка проекта, а сами разборщики — на строках, собранных
    прямо здесь. Причина отдельного теста: настоящие шаблоны сегодня
    отформатированы так, что каждое место лежит на своей строке и ни один
    комментарий не несёт `hx-get`. То есть гейт зелен по СОВПАДЕНИЮ
    форматирования, а не по построению, и первая же правка разметки —
    переносом атрибутов или комментарием-обоснованием рядом с местом — это
    совпадение снимет. Пять случаев ниже держат разбор в тех границах, в
    которых он должен быть верен независимо от того, как отформатированы
    шаблоны сегодня (07-REVIEW.md, WR-07).

    Проза здесь — не выдуманная угроза: кодовая база проекта несёт
    комментарии-обоснования объёмные, и один из них (`base.html`, о переходах
    вида) уже упоминает срабатывание `revealed` в тексте.
    """
    # 1. Два атрибута на ОДНОЙ строке — два места, а не одно.
    two_on_one_line = (
        '<div hx-get="/a" hx-trigger="revealed"></div>'
        '<div hx-get="/b" hx-trigger="revealed"></div>'
    )
    assert _places(two_on_one_line) == ["revealed", "revealed"], (
        "два атрибута `hx-get` на одной строке схлопнулись в одно место: счёт "
        "идёт по строкам исходника, а место есть АТРИБУТ — переформатирование "
        "разметки в одну строку молча потеряло бы половину мест"
    )

    # 2. Атрибут только в Jinja-комментарии — мест НЕТ.
    jinja_prose = (
        '{# Подгрузка объявляется атрибутом hx-get="/ads" с '
        'hx-trigger="revealed" — форма описана здесь, места здесь нет. #}\n'
        "<p>обычная разметка</p>"
    )
    assert _places(jinja_prose) == [], (
        "Jinja-комментарий, упоминающий `hx-get`, посчитан настоящим местом: "
        "проза способна СОЗДАТЬ место и тем самым замаскировать пропажу "
        "настоящего — ровно та подмена, которую раздел «ЛОВУШКА СЧЁТА» "
        "описывает для строки срабатывания"
    )

    # 3. Атрибут только в HTML-комментарии — мест НЕТ.
    html_prose = (
        "<!-- View Transitions отключены: при infinite scroll "
        '(hx-get="/ads", hx-trigger="revealed") вызывали мерцание -->\n'
        "<p>обычная разметка</p>"
    )
    assert _places(html_prose) == [], (
        "HTML-комментарий, упоминающий `hx-get`, посчитан настоящим местом: "
        "гейт разметки обязан считать разметку, а не документацию о ней"
    )

    # 4. Атрибут и его срабатывание разнесены переносом строки ВНУТРИ тега.
    wrapped_tag = (
        "<div\n"
        '  hx-get="/ads?page=2"\n'
        '  hx-trigger="revealed"\n'
        '  hx-swap="beforeend"></div>'
    )
    inline_tag = '<div hx-get="/ads?page=2" hx-trigger="revealed" hx-swap="beforeend"></div>'
    assert _places(wrapped_tag) == ["revealed"], (
        "перенос атрибутов одного тега на несколько строк переклассифицировал "
        "место: механизм читается из СТРОКИ, а несёт его ТЕГ — чистое "
        "переформатирование уронило бы гейт сообщением о разметке, которая не "
        "менялась"
    )
    assert _places(wrapped_tag) == _places(inline_tag), (
        "один и тот же тег, записанный в одну строку и в несколько, "
        "классифицируется по-разному — разбор зависит от форматирования"
    )

    # 5. Срабатывание другого механизма упомянуто в комментарии РЯДОМ с местом.
    prose_beside_place = (
        '<div id="wa-status" hx-get="/accounts/connect/wa/status" '
        'hx-trigger="every 3s"></div>'
        '{#- срабатывание hx-trigger="revealed" объявлено в списках, '
        "здесь опрос -#}"
    )
    assert _places(prose_beside_place) == ["poll"], (
        "место классифицировано по соседней ПРОЗЕ, а не по своему тегу: "
        "комментарий рядом с местом поллинга перевёл его в механизм подгрузки "
        "— разбивка по механизмам разъехалась бы, оставив общее число верным"
    )


def test_hx_get_inventory_matches_declared_mechanisms() -> None:
    """22 места `hx-get` числом по трём механизмам (D-18).

    Утверждений ДВА, как в образце (test_components.py:1005-1015). Первое —
    перечень против суммы: ловит расхождение ВНУТРИ самого теста, когда
    константу-число поправили, а перечень нет. Второе — перечень против
    исходников: ловит расхождение теста с кодом. Только вместе они не дают
    перечню механизмов и числу 22 разъехаться молча — по отдельности каждое
    можно удовлетворить, оставив второе неверным.
    """
    # 1. Перечень против объявленных чисел.
    assert sum(site.places for site in REVEALED_SITES) == REVEALED_PLACES, (
        "перечень механизма 1 (revealed) разошёлся с числом мест"
    )
    assert sum(site.places for site in POLL_SITES) == POLL_PLACES, (
        "перечень механизма 2 (every Ns) разошёлся с числом мест"
    )
    assert sum(site.places for site in CONDITIONAL_SITES) == CONDITIONAL_PLACES, (
        "перечень механизма 3 (условные атрибуты) разошёлся с числом мест"
    )
    assert REVEALED_PLACES + POLL_PLACES + CONDITIONAL_PLACES == HX_GET_PLACES, (
        f"сумма трёх механизмов "
        f"{REVEALED_PLACES + POLL_PLACES + CONDITIONAL_PLACES}, объявлено "
        f"{HX_GET_PLACES} — разбивка и сумма разъехались внутри теста"
    )

    # 2. Перечень против исходников.
    found = _counted_by_mechanism()

    assert not found["unknown"], (
        f"места `hx-get` с неопознанной формой срабатывания: "
        f"{sorted(found['unknown'])} — ни `revealed`, ни Jinja-условия, ни "
        f"`every Ns` в строке нет; механизм обязан быть объявлен, а не отнесён "
        f"к поллингу по остаточному признаку"
    )

    offenders: dict[str, str] = {}
    for mechanism, declared in (
        ("revealed", _declared(REVEALED_SITES)),
        ("poll", _declared(POLL_SITES)),
        ("conditional", _declared(CONDITIONAL_SITES)),
    ):
        actual = found[mechanism]
        for template in sorted(set(declared) | set(actual)):
            expected_places = declared.get(template, 0)
            actual_places = actual.get(template, 0)
            if actual_places != expected_places:
                offenders[f"{mechanism}:{template}"] = (
                    f"мест {actual_places}, ожидалось {expected_places}"
                )

    assert not offenders, (
        f"мест `hx-get` по механизмам {sorted(offenders)}, ожидалось "
        f"{HX_GET_PLACES} всего — место молча исчезло или появилось "
        f"незаявленное: {offenders}"
    )

    total = sum(sum(bucket.values()) for bucket in found.values())
    assert total == HX_GET_PLACES, (
        f"мест `hx-get` всего {total}, ожидалось {HX_GET_PLACES} — место молча "
        f"исчезло или появилось незаявленное"
    )


def test_revealed_literal_count_exceeds_site_count() -> None:
    """Вхождений строки `revealed` — 13, мест разметки — 12 (ловушка счёта).

    Обе величины утверждаются СРАЗУ, а не одна через другую. Тест, знающий
    только про 12, позеленел бы и на наивном поиске строки, если бы разметка
    потеряла место ровно в тот момент, когда прибавился ещё один комментарий, —
    два расхождения погасили бы друг друга в одном числе. Тест, знающий только
    про 13, не заметил бы переезда места разметки в комментарий.
    """
    literal = sum(
        source.count(REVEALED_TRIGGER) for _rel, source in _all_templates()
    )
    assert literal == REVEALED_LITERAL_OCCURRENCES, (
        f"вхождений строки {REVEALED_TRIGGER!r} в шаблонах {literal}, ожидалось "
        f"{REVEALED_LITERAL_OCCURRENCES} (12 мест разметки плюс прозаический "
        f"комментарий app/templates/base.html:241)"
    )

    sites = sum(
        1
        for _rel, source in _all_templates()
        for line in _hx_get_lines(source)
        if REVEALED_TRIGGER in line
    )
    assert sites == REVEALED_PLACES, (
        f"мест `hx-get` с {REVEALED_TRIGGER!r} {sites}, ожидалось "
        f"{REVEALED_PLACES} — место молча исчезло или появилось незаявленное"
    )

    assert literal - sites == 1, (
        f"разница «вхождений строки минус мест разметки» {literal - sites}, "
        f"ожидалась 1 — ровно один прозаический комментарий "
        f"(app/templates/base.html:241). Совпадение двух чисел означало бы, что "
        f"наивный счёт по строке снова неотличим от счёта по местам"
    )

"""Фаза 15, план 15-09: литерал размера страницы в разметке. Правило утверждает его ОТСУТСТВИЕ.

Долг ``DEF-09-03`` (``.planning/REQUIREMENTS.md``, запись «закрытие WR-05 ТРЕТЬЕГО
круга не держит НИ ОДНО правило») назначен этой фазе поимённо. Размер страницы
бесконечной прокрутки объявлен в Python ОДИН раз, константой ``PAGE_SIZE`` в
каждом из трёх модулей (``app/pages/ads.py``, ``app/pages/accounts.py``,
``app/pages/schedules.py``). Шаблон, набирающий то же число литералом, заводит
ВТОРОЙ его носитель, и тот разойдётся с первым молча: правка константы изменит
выборку, а адрес следующей порции продолжит просить прежнее число.

Предмет правила — ОТСУТСТВИЕ литерала в ИСХОДНИКЕ шаблона, а не отрендеренный
адрес. Отрендеренный адрес одинаков и при значении контекста, и при вернувшемся
литерале, пока оба равны тридцати. Поэтому правило, сверяющее адрес, различить
эти два состояния не может по построению.

ЛЕТОПИСЬ ЧИСЛА МЕСТ: 6 → 0 (план 15-09, задача 1, 2026-09-24).

- БЫЛО: шесть мест, все в строке сборки адреса порции, три пары «страница +
  карточки порции»:
  ``app/templates/ads/list.html:61``, ``app/templates/ads/partial_cards.html:7``,
  ``app/templates/accounts/list.html:203``,
  ``app/templates/accounts/partial_cards.html:146``,
  ``app/templates/schedules/list.html:66``,
  ``app/templates/schedules/partial_cards.html:12``.
  Замер: ``grep -rc 'limit=30' app/templates/`` на дереве ``f532fe8a``: шесть
  файлов по одному вхождению.
- ЧЕМ СНЯТО: литерал заменён значением контекста ``page_size``. Оба обработчика
  каждого модуля (страница и порция) кладут в контекст ИМЕННО ``PAGE_SIZE``.
  Новых носителей числа не заведено. Пара правлена одним ходом в обе половины.
  Экран групп аккаунта (``account_groups/includes/sentinel.html``) и оба экрана
  истории несли значение контекста и до этой фазы. Образец взят оттуда, а имя
  ключа совпадает.
- ⚠️ ПРЕЖНЕЕ ПРИНУЖДЕНИЕ ИЗМЕРЕНО И ПРИЗНАНО НЕДОСТАТОЧНЫМ, А НЕ ЗАБЫТО.
  Вхождений ``limit=30`` в ``tests/`` до этого файла было 30 (``grep -rc``,
  шесть модулей), и ни одно не утверждает ОТСУТСТВИЯ. Ближайшее из них,
  ``test_page_shows_thirty_rows_and_a_sentinel``
  (``tests/test_pages/test_account_groups.py``), сверяет ОТРЕНДЕРЕННЫЙ адрес и
  остаётся зелёным и при параметре, и при вернувшемся литерале. Запись
  ``DEF-09-03`` говорит это дословно. Правила адреса этот файл не отменяет:
  они остаются в силе наравне с новым (правило 7 ниже).
- Оговорка к прежним записям, называвшим шесть живых мест: ПРОГНОЗ НЕ БЫЛ
  ОШИБКОЙ — ОН УСТАРЕЛ: на момент своей записи он был верным, и правится не он,
  а числа, которые он пережил.

ЛЕТОПИСЬ НОСИТЕЛЯ РАЗМЕРА: литерал → выражение → ОТСУТСТВИЕ.

1. До плана 15-09 — литерал ``limit=30`` в шести строках (второй носитель числа).
2. План 15-09 — выражение ``limit={{ page_size }}``, ключ контекста кладут оба
   обработчика каждого раздела.
3. План 15-21 (2026-09-25, решение владельца Г-2; UI-ревью Фазы 15, приоритет 3
   и пункт 8) — размер из шести сентинелов снят ЦЕЛИКОМ. Выражение оставляло
   молчаливый путь отказа: окружение Jinja с мягким ``Undefined`` печатало
   ``limit=`` при пропавшем ключе, сервер отвечал 422, слушатель плашки на 422
   выходил рано, и сентинел висел «Загрузка» вечно. Прежний литерал так упасть
   не мог. Теперь размер знает только сервер: умолчание ``Query(PAGE_SIZE)``
   обработчика порции — единственный носитель числа, и цель DEF-09-03 достигнута
   полнее. Ключ ``page_size`` из контекстов шести мест снят (ни один шаблон
   цепочки его больше не читает). Правило 6 держит отсутствие размера; прежнее
   правило 6 названо летописью на своём месте. На тех же строках подпись
   ``Загрузка...`` сменилась на ``Загрузка…`` и добавлен ``role="status"``;
   обе половины каждой пары сменились одним коммитом (правило 5).

⚠️ ОСТАТОК НАЗВАН, А НЕ ЗАБЫТ. Выражение ``limit={{ page_size }}`` по-прежнему
несут сентинелы ВНЕ области решения Г-2: четыре сентинела истории —
``app/templates/history/list.html``, ``app/templates/history/partial_cards.html``,
``app/templates/admin/user_history.html``,
``app/templates/admin/history_partial_cards.html`` — и, замером исполнителя плана
15-21, пятое место той же формы: макрос ``sentinel`` экрана групп аккаунта
(``app/templates/account_groups/includes/sentinel.html``), с которого образец
15-09 и был взят. Адресат всех пяти — следующая веха; эта партия их не трогает.
Правило 1 их не ловит (выражение — не литерал), и это верно: предмет правила 1 —
второй носитель числа, а не путь отказа при пропавшем ключе.

ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ. Зелёный цвет означает ровно две вещи: литерала
размера страницы в исходниках шаблонов нет, и сеть, которая его ищет, не слепа.
Он НЕ означает, что бесконечная прокрутка РАБОТАЕТ. Суита не исполняет JS и не
наблюдает ``revealed``. Поведение закрыто ручным обходом, пункт 2 перечня Фазы 7.
Он НЕ означает, что размер страницы ВЕРЕН: тридцать — решение продукта, а не
предмет гейта. Он НЕ означает, что литерала нет в ``app/static/`` или в
``tests/``. Вселенная обхода объявлена как ``app/templates/**/*.html``, и это её
граница. Обход и вырезание комментариев ввезены из
``tests/test_templates/test_htmx_markup_gates.py``, а не написаны заново:
второй обход того же дерева разошёлся бы с первым молча.
"""

from __future__ import annotations

import inspect
import re
from importlib import import_module

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule
from tests.test_pages.test_htmx_preserved import _seed_section, _sentinel_urls
from tests.test_templates.test_htmx_markup_gates import _all_templates, _strip_comments

# --- ОБЪЯВЛЕННЫЕ ЛИТЕРАЛЫ -----------------------------------------------------
#
# Число выписано здесь, а не выведено из дерева в момент прогона: правило,
# считающее ожидание по коду, согласится с любой правкой.

PAGE_SIZE_LITERAL_PLACES = 0

# ⚠️ ПЕРЕЧЕНЬ ПУСТ — ИМЕНОВАННЫЙ НОЛЬ, А НЕ ЗАБЫТОЕ ОБЪЯВЛЕНИЕ. Форма взята у
# `MANUAL_FETCH_SITES` (tests/test_templates/test_htmx_inventory.py). Место,
# которое когда-нибудь понадобится объявить законным, встанет сюда ключом
# `путь#индекс` с причиной, и число выше поднимется записью летописи.
PAGE_SIZE_LITERAL_SITES: dict[str, str] = {}

# Имя ключа контекста, которым размер ехал в разметку с плана 15-09 по план
# 15-21. После 15-21 правило 6 утверждает его ОТСУТСТВИЕ в контекстах шести
# мест: мёртвый ключ приглашал бы вернуть `limit={{ page_size }}` в адрес.
PAGE_SIZE_CONTEXT_KEY = "page_size"

# Литерал размера страницы: параметр `limit`, значение которого набрано ЦИФРАМИ.
# Граница слова слева отсекает имена, у которых `limit` лишь хвост. Шаблонное
# выражение (`limit={{ page_size }}`) под образец не попадает: после знака
# равенства у него стоит скобка, а не цифра.
PAGE_SIZE_LITERAL = re.compile(r"(?<![-\w])limit=\d")

# Три пары «страница + карточки порции». Строка сборки адреса порции в обеих
# половинах пары ОДНА И ТА ЖЕ посимвольно: страница отдаёт первую порцию, а
# порция — все следующие (tests/test_templates/test_htmx_inventory.py, механизм 1:
# «мест 12, а экранов ручного обхода 6»).
PORTION_PAIRS: dict[str, tuple[str, str, str]] = {
    "ads": ("ads/list.html", "ads/partial_cards.html", 'hx-get="/ads/partial?'),
    "accounts": (
        "accounts/list.html",
        "accounts/partial_cards.html",
        'hx-get="/accounts/partial?',
    ),
    "schedules": (
        "schedules/list.html",
        "schedules/partial_cards.html",
        'hx-get="/schedules/partial?',
    ),
}
PORTION_PAIRS_DECLARED = 3

# Какой модуль `app/pages/` кормит какой шаблон. Ожидаемый размер читается
# константой ИЗ МОДУЛЯ, а не числом, переписанным в тест.
CONTEXT_CARRIERS: dict[str, str] = {
    "ads/list.html": "app.pages.ads",
    "ads/partial_cards.html": "app.pages.ads",
    "accounts/list.html": "app.pages.accounts",
    "accounts/partial_cards.html": "app.pages.accounts",
    "schedules/list.html": "app.pages.schedules",
    "schedules/partial_cards.html": "app.pages.schedules",
}

# Синтетический шаблон контролей. Такого файла в дереве нет: контроль кладёт в
# словарь исходников НОВЫЙ ключ, а не портит живой экран.
SYNTHETIC_TEMPLATE = "a_screen_some_future_phase_will_add/list.html"
SYNTHETIC_SENTINEL = (
    '<div hx-get="/future/partial?offset={{ next_offset }}&limit=30"'
    ' hx-trigger="revealed" hx-swap="outerHTML">Загрузка...</div>\n'
)


# --- РАЗБОРЩИКИ ---------------------------------------------------------------


def _template_sources() -> dict[str, str]:
    """Исходники `app/templates/**/*.html`: путь относительно каталога → текст."""
    return dict(_all_templates())


def _page_size_literal_places(
    sources: dict[str, str], *, strip_comments: bool = True
) -> list[str]:
    """Места литерала размера страницы ключами `путь#индекс`, отсортированно.

    Исходники приходят СЛОВАРЁМ, чтобы контроли могли подать изменённую копию
    дерева. Индекс — порядковый номер вхождения внутри файла. Номер строки не
    берётся: переформатирование разметки меняло бы ключ, хотя место то же.
    """
    places: list[str] = []
    for path in sorted(sources):
        text = _strip_comments(sources[path]) if strip_comments else sources[path]
        for index, _ in enumerate(PAGE_SIZE_LITERAL.finditer(text)):
            places.append(f"{path}#{index}")
    return places


def _portion_url_line(source: str, mark: str) -> str:
    """Строка сборки адреса порции: единственная строка исходника с `mark`.

    Отступ слева отрезается: страница аккаунтов несёт строку внутри блока с
    отступом, а карточки порции — без него. Предмет сверки — сама разметка
    адреса, а не её положение в файле.
    """
    lines = [line.strip() for line in _strip_comments(source).splitlines() if mark in line]
    assert len(lines) == 1, (
        f"строка сборки адреса порции `{mark}` найдена {len(lines)} раз, ожидалась одна"
    )
    return lines[0]


def _diverged_pairs(sources: dict[str, str]) -> list[str]:
    """Имена пар, чьи половины собирают адрес порции РАЗНЫМИ строками."""
    return [
        name
        for name, (page, portion, mark) in sorted(PORTION_PAIRS.items())
        if _portion_url_line(sources[page], mark) != _portion_url_line(sources[portion], mark)
    ]


# --- ПРАВИЛА ------------------------------------------------------------------


def test_no_page_size_literal_is_left_in_the_template_sources():
    """Правило 1: литерала размера страницы в исходниках шаблонов НЕТ.

    Утверждение сформулировано как отсутствие предмета. Отказ называет каждое
    найденное место ключом `путь#индекс`.
    """
    places = _page_size_literal_places(_template_sources())

    assert len(PAGE_SIZE_LITERAL_SITES) == PAGE_SIZE_LITERAL_PLACES
    assert places == sorted(PAGE_SIZE_LITERAL_SITES), (
        "ЛИТЕРАЛ РАЗМЕРА СТРАНИЦЫ В РАЗМЕТКЕ — второй носитель числа, который "
        "разойдётся с `PAGE_SIZE` молча. Места: "
        + ", ".join(places)
    )
    assert len(places) == PAGE_SIZE_LITERAL_PLACES


def test_control_negative_a_synthetic_template_with_the_literal_is_found_and_named():
    """Правило 2, контроль от вакуума: СИНТЕТИЧЕСКИЙ ключ с литералом найден и назван.

    ⚠️ Утверждение отсутствия истинно и на сломанной сети. Контроль кладёт в
    словарь исходников шаблон, которого в дереве нет, и требует, чтобы та же
    сеть нашла его и назвала по ключу. Иначе ноль правила 1 был бы неотличим от
    слепоты измерителя.
    """
    sources = _template_sources()
    assert SYNTHETIC_TEMPLATE not in sources, "синтетический ключ совпал с живым шаблоном"
    sources[SYNTHETIC_TEMPLATE] = SYNTHETIC_SENTINEL

    places = _page_size_literal_places(sources)

    assert f"{SYNTHETIC_TEMPLATE}#0" in places, (
        "СЕТЬ НЕ НАШЛА ЛИТЕРАЛ В СИНТЕТИЧЕСКОМ ШАБЛОНЕ — ноль правила 1 доказывал "
        "бы слепоту измерителя, а не отсутствие литерала"
    )
    assert not (places == sorted(PAGE_SIZE_LITERAL_SITES)), (
        "утверждение отсутствия осталось истинным при литерале в дереве"
    )


def test_control_positive_the_walked_universe_is_not_empty_and_the_rule_is_silent():
    """Правило 3, контроль от вакуума: обход видит дерево, и правило молчит на нём.

    Молчание правила 1 имеет цену, только если молчит оно не на пустоте. Обход
    обязан видеть больше пятидесяти шаблонов, и все шесть шаблонов трёх пар
    обязаны лежать в его вселенной.
    """
    sources = _template_sources()

    assert len(sources) > 50, f"вселенная обхода подозрительно мала: {len(sources)}"
    assert set(CONTEXT_CARRIERS) <= set(sources), (
        "шаблоны трёх пар выпали из вселенной обхода: "
        + ", ".join(sorted(set(CONTEXT_CARRIERS) - set(sources)))
    )
    assert _page_size_literal_places(sources) == []


def test_control_a_literal_inside_a_comment_is_not_counted():
    """Правило 4, контроль: литерал внутри комментария Jinja не считается местом.

    Тот же синтетический исходник считается дважды: с вырезанием комментариев и
    без. Оба числа и их разность утверждаются. Так видно, что ноль первого счёта
    дало вырезание, а не промах образца.
    """
    commented = "{#- " + SYNTHETIC_SENTINEL + " -#}\n"
    sources = {SYNTHETIC_TEMPLATE: commented}

    stripped = _page_size_literal_places(sources)
    raw = _page_size_literal_places(sources, strip_comments=False)

    assert stripped == []
    assert raw == [f"{SYNTHETIC_TEMPLATE}#0"]
    assert len(raw) - len(stripped) == 1


def test_both_halves_of_every_pair_build_the_portion_url_with_the_same_line():
    """Правило 5: внутри каждой пары строка сборки адреса порции ОДНА посимвольно.

    Это машинная защита от правки одной половины. Разошедшаяся пара
    обнаружилась бы только на второй порции прокрутки, то есть глазом.
    """
    assert len(PORTION_PAIRS) == PORTION_PAIRS_DECLARED
    diverged = _diverged_pairs(_template_sources())

    assert diverged == [], (
        "ПОЛОВИНЫ ПАРЫ СОБИРАЮТ АДРЕС ПОРЦИИ РАЗНЫМИ СТРОКАМИ: "
        + ", ".join(diverged)
    )


def test_control_negative_a_diverged_pair_is_named():
    """Контроль к правилу 5: правка одной половины пары краснеет и НАЗЫВАЕТ пару.

    ЛЕТОПИСЬ ПОДМЕНЫ. План 15-09: подмена меняла первый `&` строки на `&amp;`.
    План 15-21 снял `&limit=…` из адреса аккаунтов, и `&` в строке не осталось —
    подмена перестала бы приземляться. Теперь она возвращает размер в ОДНУ
    половину пары: ровно ту правку, от которой правило 5 и держит.
    """
    sources = _template_sources()
    page, _portion, mark = PORTION_PAIRS["accounts"]
    original = _portion_url_line(sources[page], mark)
    mutated = original.replace("{{ next_offset }}", "{{ next_offset }}&limit={{ page_size }}", 1)
    sources[page] = sources[page].replace(original, mutated)

    assert _portion_url_line(sources[page], mark) != original, "ПОДМЕНА НЕ ПРИЗЕМЛИЛАСЬ"
    assert _diverged_pairs(sources) == ["accounts"]


def _capture_contexts(monkeypatch) -> dict[str, dict]:
    """Контексты, с которыми обработчики зовут `TemplateResponse`: имя шаблона → контекст."""
    from app.pages import common

    original = common.templates.TemplateResponse
    seen: dict[str, dict] = {}

    def spy(*args, **kwargs):
        name = next(arg for arg in args if isinstance(arg, str))
        context = kwargs.get("context")
        if context is None:
            context = next(arg for arg in args if isinstance(arg, dict))
        seen[name] = context
        return original(*args, **kwargs)

    monkeypatch.setattr(common.templates, "TemplateResponse", spy)
    return seen


# Порция запрашивается с РАЗМЕРОМ, ОТЛИЧНЫМ от страничного: так правило
# различает носителя. Адрес следующей порции, подставивший присланный клиентом
# `limit`, понёс бы здесь семь, и правило 7 назвало бы это.
PORTION_PROBE_LIMIT = 7

# Обработчик порции каждого раздела: модуль и имя функции. Умолчание её
# параметра `limit` — ЕДИНСТВЕННЫЙ носитель размера после плана 15-21.
PORTION_HANDLERS: dict[str, tuple[str, str]] = {
    "ads": ("app.pages.ads", "ads_partial"),
    "accounts": ("app.pages.accounts", "accounts_partial"),
    "schedules": ("app.pages.schedules", "schedules_partial"),
}

# Признак карточки порции: по одному `id` на карточку. Счёт карточек отвечает
# на вопрос «сколько строк отдала порция без `limit`», а не «сколько разметки».
PORTION_CARD_IDS: dict[str, re.Pattern[str]] = {
    "ads": re.compile(r'id="ad-row-\d+"'),
    "accounts": re.compile(r'id="account-row-\d+"'),
    "schedules": re.compile(r'id="schedule-row-\d+"'),
}

HX_GET_VALUE = re.compile(r'hx-get="([^"]*)"')

# ЛЕТОПИСЬ ПРАВИЛА 6 (план 15-21, 2026-09-25, решение владельца Г-2, UI-ревью
# Фазы 15, приоритет 3). Здесь стояло правило
# `test_the_page_size_in_the_context_is_the_module_constant` (план 15-09): оно
# утверждало, что оба обработчика раздела кладут в контекст ключ `page_size`,
# равный `PAGE_SIZE` своего модуля, — носителем размера в разметке было
# выражение `limit={{ page_size }}`. Прежнее правило ошибкой не было: оно
# держало цель DEF-09-03 (один носитель числа) на шести сегодняшних рендерах.
# Заменено потому, что сама форма оставляла молчаливый путь отказа: при мягком
# `Undefined` пропавший ключ печатал `limit=`, сервер отвечал 422, слушатель
# плашки на 422 выходил рано, и сентинел висел «Загрузка» вечно. Размер больше
# не едет в разметку вовсе; правило ниже утверждает ОТСУТСТВИЕ размера в адресе
# и то, что единственный носитель — умолчание `Query(PAGE_SIZE)` обработчика.


@pytest.mark.asyncio
async def test_the_six_sentinels_carry_no_page_size_and_the_server_default_is_the_module_constant(
    authed_client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    """Правило 6: размер страницы не едет в разметку; его знает только сервер.

    Три половины одного утверждения, по всем трём разделам, с отказом, который
    называет КАЖДОЕ нарушение, а не первое:

    (а) в ИСХОДНИКАХ шести шаблонов адрес `hx-get` сентинела не содержит `limit`;
    (б) умолчание параметра `limit` обработчика порции (по `inspect.signature`)
        равно `PAGE_SIZE` своего модуля — константа читается ИЗ МОДУЛЯ;
    (в) рендер страницы и порции даёт адрес сентинела без `limit`, в контексте
        обоих обработчиков нет мёртвого ключа `page_size`, а запрос порции БЕЗ
        `limit` отдаёт ровно `PAGE_SIZE` карточек (посев больше `PAGE_SIZE`).
    """
    sources = _template_sources()
    seen = _capture_contexts(monkeypatch)
    offences: list[str] = []

    for section, (page_template, portion_template, mark) in sorted(PORTION_PAIRS.items()):
        module_name, handler_name = PORTION_HANDLERS[section]
        module = import_module(module_name)

        # (а) исходник
        for template in (page_template, portion_template):
            value = HX_GET_VALUE.search(_portion_url_line(sources[template], mark))
            assert value, f"{template}: у строки сентинела нет `hx-get`"
            if "limit" in value.group(1):
                offences.append(f"{template}: исходник адреса сентинела несёт `limit`")

        # (б) умолчание сервера
        parameter = inspect.signature(getattr(module, handler_name)).parameters["limit"]
        default = getattr(parameter.default, "default", parameter.default)
        if default != module.PAGE_SIZE:
            offences.append(
                f"{module_name}.{handler_name}: умолчание `limit` {default!r}, "
                f"а `PAGE_SIZE` = {module.PAGE_SIZE}"
            )

        # (в) рендер
        base = await _seed_section(db_session, section)
        page = await authed_client.get(base)
        portion = await authed_client.get(f"{base}/partial")
        assert page.status_code == 200 and portion.status_code == 200, section
        for template, response in ((page_template, page), (portion_template, portion)):
            urls = _sentinel_urls(response.text)
            assert urls, f"{template}: сентинела нет в ответе — посев мал"
            if "limit" in urls[-1]:
                offences.append(f"{template}: отрендеренный адрес `{urls[-1]}` несёт `limit`")
            assert template in seen, f"{template}: обработчик не отрисовал шаблон"
            if PAGE_SIZE_CONTEXT_KEY in seen[template]:
                offences.append(
                    f"{template}: в контексте мёртвый ключ `{PAGE_SIZE_CONTEXT_KEY}`"
                )
        cards = len(PORTION_CARD_IDS[section].findall(portion.text))
        if cards != module.PAGE_SIZE:
            offences.append(
                f"{base}/partial без `limit`: {cards} карточек, а `PAGE_SIZE` = "
                f"{module.PAGE_SIZE}"
            )

    assert offences == [], (
        "РАЗМЕР СТРАНИЦЫ ЕДЕТ В РАЗМЕТКУ или сервер его не знает — пропавший ключ "
        "контекста дал бы `limit=`, 422 и вечную «Загрузку»:\n" + "\n".join(offences)
    )


async def _schedule_ids(db: AsyncSession) -> list[int]:
    return list((await db.execute(select(Schedule.id).order_by(Schedule.id))).scalars())


@pytest.mark.asyncio
@pytest.mark.parametrize("section", ["ads", "accounts", "schedules"])
async def test_the_rendered_portion_url_is_unchanged(
    authed_client: AsyncClient, db_session: AsyncSession, section: str
):
    """Правило 7 (страховочное): отрендеренный адрес порции — ровно ожидаемый, до символа.

    Правило стоит рядом с прежними правилами адреса (`test_infinite_scroll_chain`
    и `test_infinite_scroll_keeps_filters` в tests/test_pages/test_htmx_preserved.py)
    и их не заменяет. Предмет ``DEF-09-03`` оно не держит: его держит правило 1.

    ЛЕТОПИСЬ ОЖИДАНИЯ. План 15-09: адрес нёс `&limit=<PAGE_SIZE>` при любом
    присланном `limit` порции, и правило утверждало, что замена литерала
    значением контекста его не сдвинула. План 15-21 (2026-09-25, Г-2): размер из
    адреса снят целиком, ожидание — адрес без `limit`. Имя правила прежнее:
    «unchanged» теперь значит «клиентский `limit` порции (семь) в адрес
    следующей порции не попадает никакой формой» — сдвигается только курсор.
    """
    base = await _seed_section(db_session, section)
    size = import_module(CONTEXT_CARRIERS[f"{section}/list.html"]).PAGE_SIZE

    page = await authed_client.get(base)
    portion = await authed_client.get(f"{base}/partial?limit={PORTION_PROBE_LIMIT}")

    if section == "schedules":
        ids = await _schedule_ids(db_session)
        expected_page = f"/schedules/partial?after_id={ids[size - 1]}"
        expected_portion = f"/schedules/partial?after_id={ids[PORTION_PROBE_LIMIT - 1]}"
    else:
        expected_page = f"/{section}/partial?offset={size}"
        expected_portion = f"/{section}/partial?offset={PORTION_PROBE_LIMIT}"

    assert _sentinel_urls(page.text)[-1] == expected_page
    assert _sentinel_urls(portion.text)[-1] == expected_portion

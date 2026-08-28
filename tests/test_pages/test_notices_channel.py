"""Гейт ЕДИНСТВЕННОСТИ КАНАЛА ОБРАТНОЙ СВЯЗИ (FOUND-05, D-09).

ЧТО ЭТОТ ФАЙЛ СТЕРЕЖЁТ. До плана 08-06 продукт сообщал человеку исход его
действия ПЯТЬЮ разными написаниями параметра адреса, а разрешали код в слова
ТРИ частных отображения в трёх разделах плюс одна строка, читавшая параметр
прямо в разметке экрана входа. Копий было столько же, сколько мест: правка
одной расходилась с остальными молча, а два исхода из четырнадцати не
рисовались нигде вовсе. Канал сведён в один: один параметр, один закрытый
реестр слов (`app/pages/notices.py`), одна пара областей отрисовки в шелле.
Этот файл — машинная половина решения: он не даёт снятому вернуться и не даёт
завести код мимо реестра.

⚠️ ГЕЙТ УТВЕРЖДАЕТ НОЛЬ, А НЕ УБЫВАНИЕ, И ЭТО СЛЕДСТВИЕ D-09. Периода
совместимости не было: пять написаний сняты СРАЗУ. Пока живы два написания,
утверждение о единственности канала невыразимо — «стало меньше» согласуется и
с тем, что половина экранов молча перестала сообщать исход.

⚠️ СОБСТВЕННЫЙ ИСХОДНИК ГЕЙТА НЕ СПОСОБЕН УДОВЛЕТВОРИТЬ ТО, ЧТО ГЕЙТ ИЩЕТ.
Снятые написания выписаны здесь ЛИТЕРАЛАМИ — иначе проверять было бы нечего, —
но область поиска есть `app/`, и только она. Файл живёт в `tests/`, поэтому
его собственные литералы в счёт не попадают ни одним путём. Урок не новый:
реестр уведомлений называет снятое ОПИСАТЕЛЬНО именно потому, что живёт внутри
области поиска, а области уведомления набирают свои признаки живости словами по
той же причине.

⚠️ ФАЙЛ НЕ ИМПОРТИРУЕТ НИ ОДНОГО МОДУЛЯ ПРИЛОЖЕНИЯ, И ЭТО ЗАПРЕТ, А НЕ СТИЛЬ.
Тест, выводящий ожидание из проверяемого, согласился бы с любой правкой: собери
он перечень снятых написаний из приложения — и вернувшееся написание оказалось
бы «ожидаемым» в тот же момент, как вернулось. Исходники читаются ТЕКСТОМ,
реестр разбирается синтаксическим деревом СВОЕГО ФАЙЛА, а перечни выписаны
руками. Свойство закреплено `test_the_gate_imports_no_application_module` —
форма взята у гейта запретов под чужой личностью.

ЧЕГО ГЕЙТ НЕ ВИДИТ — ВЫПИСАНО ЗДЕСЬ, А НЕ ОСТАВЛЕНО НА ДОГАДКУ (WR-08).
Ненаписанная граница через один рефакторинг становится границей НЕИЗВЕСТНОЙ.

1. КОД, СОБРАННЫЙ ПОДСТАНОВКОЙ ВО ВРЕМЯ ИСПОЛНЕНИЯ, из адресной строки
   исходника не читается. Такое место в продукте РОВНО ОДНО —
   `app/pages/schedules.py::_editor_error_redirect`, где адрес общий на два
   исхода. Граница закрыта не молчанием, а вторым обходом: гейт собирает ещё и
   все УПОМИНАНИЯ констант реестра в исходниках приложения, и оба кода этого
   места попадают в счёт через свои вызывающие. Обход мимо реестра поэтому
   невозможен и здесь.

2. ЗАПИСЬ ПАРАМЕТРА ИЗ ШАБЛОНА гейту невидима — разметка собирает адреса
   вычислением, и связать вычисленное с кодом по тексту нечем. Сегодня таких
   мест нет: параметр пишет только сервер, и это следствие того же плана,
   снявшего единственное чтение параметра прямо в разметке.

3. ЧИСЛО МЕСТ ЗАПИСИ ВЫПИСАНО ЗДЕСЬ РУКАМИ И БУДЕТ МЕНЯТЬСЯ. Собственное число
   ловит не только пропажу, но и СЛОМАННЫЙ обход: опечатка в регулярном
   выражении даёт тот же зелёный ноль, что и пустое дерево (D-13).

ГДЕ ЖИВЁТ ВТОРАЯ ПОЛОВИНА ПРОВЕРКИ. Этот файл утверждает, что каждый исход
ЗАПИСЫВАЕТСЯ приложением и что каждый записанный код РИСУЕТСЯ человеку словами
на обоих шеллах. Что конкретное ДЕЙСТВИЕ отвечает конкретным кодом, утверждают
регрессии в файлах своих разделов, где уже стоит их посев:
`test_password_reset.py`, `test_billing_payment_errors.py`,
`test_schedule_ownership.py`, `test_admin_panel.py`, `test_history_retry.py`.
Собирать их копии здесь значило бы завести второй посев четырёх разделов,
расходящийся с первым молча, — ровно тот дефект, который снимает этот план.
Исключение одно: сохранение настроек профиля, у которого регрессии не было
вовсе, потому что не было и отрисовки; оно живёт здесь.
"""
import ast
import re
from html import unescape
from pathlib import Path

import pytest
from httpx import AsyncClient

from tests.conftest import notice_areas

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"
PAGES_DIR = APP_DIR / "pages"
TEMPLATES_DIR = APP_DIR / "templates"
REGISTRY_FILE = PAGES_DIR / "notices.py"

# ПЯТЬ СНЯТЫХ НАПИСАНИЙ, выписанных литералами. Каждое было артефактом
# редиректа: порождалось сервером, потреблялось один раз и никем не
# закладывалось — поэтому снятие шло без периода совместимости (D-09).
RETIRED_QUERY_KEYS = ("?error=", "?saved=", "?reset=", "?retry=", "?sched_error=")

# Мест записи параметра в СТРАНИЧНОМ слое. Число выписано руками намеренно:
# см. границу 3 в докстринге файла.
NOTICE_WRITE_PLACES = 12

# Место записи ВНЕ страничного слоя ровно одно — отказ действия под чужой
# учётной записью (`app/dependencies.py`). Оно живёт в зависимости, а не в
# обработчике, потому что зависимость ответа не возвращает вовсе и прервать
# цепочку может единственным способом, исключением. Отдельное число, а не
# молчаливое расширение области счёта: место записи, заведённое будущей фазой в
# третьем слое, обязано уронить тест, а не раствориться в сумме.
NOTICE_WRITE_PLACES_OUTSIDE_PAGES = 1

# Признак, которым гейт доступа помечает СВОЙ редирект. Кодом уведомления он не
# является и в реестр не входит (D-11): состояние доступа сервер знает из
# строки подписки, а признак нужен журналам — по нему видно, что человек попал
# в раздел отказом гейта, а не пришёл сам.
ACCESS_REDIRECT_FLAG = "?expired=1"
ACCESS_FLAG_OWNER = "app/pages/__init__.py"
ACCESS_FLAG_MUST_NOT_BE_READ_IN = "app/pages/billing.py"

JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.DOTALL)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

# Место записи есть ВХОЖДЕНИЕ ключа в адресную строку, а не строка исходника:
# два места умещаются на одной строке, а один адрес переносится на несколько.
# Разделитель — либо начало строки запроса, либо присоединение к имеющейся.
WRITE_PLACE = re.compile(r"[?&]notice=")

# Код, уехавший в адрес КОНСТАНТОЙ реестра, — канон формы (`app/pages/*.py`).
WRITTEN_CONSTANT = re.compile(r"[?&]notice=\{notices\.([A-Z][A-Z0-9_]*)\}")

# Код, уехавший в адрес ЛИТЕРАЛОМ. Форма не канон, но встречается там, где
# адрес объявлен константой модуля целиком, — и обходом она обязана видеться,
# иначе мимо реестра можно было бы пройти, просто набрав код руками.
WRITTEN_LITERAL = re.compile(r"[?&]notice=([a-z][a-z0-9_]*)")

# Упоминание константы реестра где угодно в исходнике. Второй обход, закрывающий
# границу 1: код, уехавший в адрес через переменную, виден здесь.
CONSTANT_REFERENCE = re.compile(r"\bnotices\.([A-Z][A-Z0-9_]*)\b")


# --- разборщики исходников ----------------------------------------------------


def _python_sources() -> dict[str, str]:
    """Все модули приложения парами «путь от корня — исходник».

    Обход РЕКУРСИВНЫЙ: модуль, добавленный будущей фазой в подкаталог, обязан
    попасть в обход сам, иначе гейт молча перестал бы видеть целый слой.
    """
    return {
        str(path.relative_to(PROJECT_ROOT)): path.read_text(encoding="utf-8")
        for path in sorted(APP_DIR.rglob("*.py"))
    }


def _template_sources() -> dict[str, str]:
    """Все шаблоны приложения БЕЗ комментариев обоих видов.

    ⚠️ КОММЕНТАРИИ ВЫРЕЗАЮТСЯ ДО СЧЁТА, И ЭТО ТРЕБОВАНИЕ, А НЕ УДОБСТВО
    (правка 07-07 и её `test_inventory_gate_ignores_prose`). Кодовая база
    проекта несёт объёмные комментарии-обоснования, и объяснение «почему это
    написание снято», набранное самим написанием, СОЗДАЛО БЫ место — то есть
    проза уронила бы запрет, который сама же объясняет.
    """
    sources = {}
    for path in sorted(TEMPLATES_DIR.rglob("*.html")):
        source = path.read_text(encoding="utf-8")
        source = JINJA_COMMENT.sub("", source)
        source = HTML_COMMENT.sub("", source)
        sources[str(path.relative_to(PROJECT_ROOT))] = source
    return sources


def _scanned_sources() -> dict[str, str]:
    """Полная область поиска снятых написаний: модули и шаблоны приложения."""
    return {**_python_sources(), **_template_sources()}


def _registry_records() -> dict[str, tuple[str, str]]:
    """Реестр уведомлений, разобранный ПО ДЕРЕВУ своего исходника.

    ⚠️ РАЗБОР, А НЕ ИМПОРТ. Импортированный реестр сделал бы ожидания гейта
    следствием проверяемого; разобранный — оставляет их независимыми. Дерево, а
    не регулярное выражение: тексты записей набраны неявной склейкой строк на
    несколько физических строк, и разбор по строкам терял бы их хвосты молча.
    """
    tree = ast.parse(REGISTRY_FILE.read_text(encoding="utf-8"))

    constants: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if not isinstance(node.value, ast.Constant) or not isinstance(
            node.value.value, str
        ):
            continue
        constants[target.id] = node.value.value

    records: dict[str, tuple[str, str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "Notice":
            continue
        code_arg, text_arg, variant_arg = node.args[:3]
        code = (
            constants[code_arg.id]
            if isinstance(code_arg, ast.Name)
            else ast.literal_eval(code_arg)
        )
        records[code] = (ast.literal_eval(text_arg), ast.literal_eval(variant_arg))
    return records


def _registry_constants() -> dict[str, str]:
    """Имя константы реестра → её код. Нужен, чтобы разрешать записи в адресах."""
    tree = ast.parse(REGISTRY_FILE.read_text(encoding="utf-8"))
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if (
                isinstance(target, ast.Name)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                constants[target.id] = node.value.value
    return constants


def _retired_key_hits(sources: dict[str, str]) -> dict[str, list[str]]:
    """Снятое написание → файлы, в которых оно снова встречается."""
    hits: dict[str, list[str]] = {}
    for key in RETIRED_QUERY_KEYS:
        found = sorted(path for path, source in sources.items() if key in source)
        if found:
            hits[key] = found
    return hits


def _written_codes(sources: dict[str, str]) -> set[str]:
    """Множество кодов, которые приложение РЕАЛЬНО отправляет человеку.

    Собирается ДВУМЯ обходами, и второй не избыточен: он закрывает границу 1
    (адрес, собранный подстановкой). Имя константы, которого в реестре нет,
    остаётся в множестве КАК ИМЯ — иначе опечатка в имени просто исчезала бы из
    счёта, и гейт согласился бы с ней.
    """
    constants = _registry_constants()
    codes: set[str] = set()
    for source in sources.values():
        for name in WRITTEN_CONSTANT.findall(source):
            codes.add(constants.get(name, f"<неизвестная константа {name}>"))
        codes.update(WRITTEN_LITERAL.findall(source))
        for name in CONSTANT_REFERENCE.findall(source):
            codes.add(constants.get(name, f"<неизвестная константа {name}>"))
    return codes


def _unregistered_codes(sources: dict[str, str]) -> set[str]:
    """Коды, уезжающие человеку и НЕ объявленные в реестре."""
    return _written_codes(sources) - set(_registry_records())


def _write_places(sources: dict[str, str]) -> dict[str, int]:
    """Файл → число мест записи параметра в нём."""
    counted = {
        path: len(WRITE_PLACE.findall(source)) for path, source in sources.items()
    }
    return {path: count for path, count in counted.items() if count}


REGISTRY_RECORDS = _registry_records()


# --- гейты --------------------------------------------------------------------


@pytest.mark.parametrize("retired_key", RETIRED_QUERY_KEYS)
def test_no_retired_query_key_remains(retired_key: str):
    """НОЛЬ вхождений каждого снятого написания в исходниках приложения.

    Не «стало меньше», а ноль: убыль согласуется и с тем, что часть экранов
    молча перестала сообщать исход, — а именно этого снятие и не должно было
    сделать (D-09).
    """
    hits = _retired_key_hits(_scanned_sources())

    assert retired_key not in hits, (
        f"снятое написание {retired_key!r} вернулось в {hits.get(retired_key)}: "
        "канал обратной связи снова стал двумя, и утверждение о его "
        "единственности перестало быть проверяемым"
    )


def test_every_written_notice_code_is_registered():
    """Каждый код, уезжающий человеку, объявлен в закрытом реестре.

    ⚠️ ГЕЙТ ЗАМКНУТ НА СЕБЯ: множество записываемых кодов собирается ТЕМ ЖЕ
    обходом, которым считаются места записи. Реестр закрыт — незнакомый код не
    рисует НИЧЕГО, и само по себе это правильно; но опечатка в коде, записанном
    обработчиком, дала бы молча пропавший исход, то есть кнопку, вернувшую ту же
    страницу без единого слова. Здесь та же опечатка ловится там, где её ещё
    можно исправить, — в исходнике.
    """
    unregistered = _unregistered_codes(_scanned_sources())

    assert unregistered == set(), (
        f"приложение пишет коды мимо реестра: {sorted(unregistered)} — по ним "
        "не нарисуется ничего, и человек не узнает об исходе своего действия"
    )


def test_no_registered_notice_code_is_orphaned():
    """Обратная сторона: ни один объявленный исход не потерялся при сведении.

    ⚠️ БЕЗ ЭТОГО УТВЕРЖДЕНИЯ ГЕЙТ ВЫШЕ ЗЕЛЕНЕЛ БЫ НА ПОТЕРЕ. «Каждый
    записываемый код зарегистрирован» согласуется и с приложением, не пишущим
    НИ ОДНОГО кода: пустое множество есть подмножество любого. Двенадцать
    редиректов сводились в один канал, и молчаливая потеря исхода — главная
    опасность именно такой правки (T-08-29).
    """
    written = _written_codes(_scanned_sources())
    orphaned = set(REGISTRY_RECORDS) - written

    assert orphaned == set(), (
        f"коды {sorted(orphaned)} объявлены реестром, но приложением не "
        "пишутся: исход, о котором пользователю сообщали, исчез вместе со "
        "своим редиректом"
    )


def test_the_number_of_notice_writers_is_the_declared_one():
    """Число мест записи равно объявленному — отдельно по слоям.

    ⚠️ СОБСТВЕННОЕ ЧИСЛО ЛОВИТ НЕ ТОЛЬКО ПУСТОТУ, НО И СЛОМАННЫЙ ОБХОД (D-13).
    Опечатка в регулярном выражении даёт тот же зелёный ноль, что и дерево, из
    которого все места пропали, — и без выписанного числа оба случая выглядели
    бы как успех.
    """
    places = _write_places(_python_sources())

    in_pages = sum(
        count for path, count in places.items() if path.startswith("app/pages/")
    )
    outside_pages = sum(
        count for path, count in places.items() if not path.startswith("app/pages/")
    )

    assert in_pages == NOTICE_WRITE_PLACES, (
        f"мест записи в страничном слое {in_pages}, а объявлено "
        f"{NOTICE_WRITE_PLACES}: {places}"
    )
    assert outside_pages == NOTICE_WRITE_PLACES_OUTSIDE_PAGES, (
        f"мест записи вне страничного слоя {outside_pages}, а объявлено "
        f"{NOTICE_WRITE_PLACES_OUTSIDE_PAGES}: {places}"
    )


def test_the_access_redirect_flag_survives():
    """Признак гейта доступа на месте и по-прежнему НЕ читается разделом оплаты.

    ⚠️ СНЯТИЕ ПЯТИ НАПИСАНИЙ НЕ ИМЕЕТ ПРАВА УТАЩИТЬ С СОБОЙ ШЕСТОЕ, КОТОРОЕ
    СНИМАТЬ НЕ ПРОСИЛИ (D-11). Признак похож на снятые ровно настолько, чтобы
    попасть под руку заодно: он тоже артефакт редиректа. Но он не код
    уведомления и в реестр не входит — он нужен ЖУРНАЛАМ, чтобы по ним было
    видно, что человек попал в раздел отказом гейта, а не пришёл сам.

    Вторая половина утверждения не менее важна первой: раздел оплаты его НЕ
    читает. Плашка о закрытом доступе рисуется по СОСТОЯНИЮ с сервера — иначе
    вопрос «закрыт ли доступ» решал бы владелец ссылки.
    """
    sources = _python_sources()

    assert ACCESS_REDIRECT_FLAG in sources[ACCESS_FLAG_OWNER], (
        f"признак {ACCESS_REDIRECT_FLAG!r} исчез из {ACCESS_FLAG_OWNER}: "
        "разбор инцидента лишился следа, по которому видно, что человека "
        "привёл в раздел отказ гейта"
    )

    billing = sources[ACCESS_FLAG_MUST_NOT_BE_READ_IN]
    # ⚠️ ПРОВЕРЯЕТСЯ ЧТЕНИЕ, А НЕ УПОМИНАНИЕ СЛОВА. Слово `expired` в разделе
    # оплаты живёт законно — им названо СОСТОЯНИЕ доступа (`STATE_EXPIRED`),
    # которое сервер вычисляет из строки подписки. Запрещено не слово, а
    # обращение к адресной строке: именно оно отдало бы вопрос «закрыт ли
    # доступ» владельцу ссылки.
    assert ACCESS_REDIRECT_FLAG not in billing, (
        "раздел оплаты снова знает адрес редиректа гейта — признак рискует "
        "стать входом обработчика вместо следа в журнале"
    )
    assert "query_params" not in billing, (
        "раздел оплаты снова читает параметр адреса: второе место разрешения "
        "кода в текст расходится с первым молча"
    )

    assert ACCESS_REDIRECT_FLAG.lstrip("?").split("=")[0] not in REGISTRY_RECORDS, (
        "признак гейта доступа заведён кодом уведомления — состояние доступа "
        "стало решаться параметром адресной строки"
    )


def test_the_gate_imports_no_application_module():
    """Гейт не импортирует НИ ОДНОГО модуля приложения ради построения ожиданий.

    ⚠️ ЭТО ЗАПРЕТ, А НЕ СТИЛЬ. Тест, выводящий ожидание из проверяемого,
    согласился бы с любой правкой: собери он перечень снятых написаний или
    множество кодов реестра из самого приложения — и вернувшееся написание
    оказалось бы «ожидаемым» в тот же момент, как вернулось. Форма и довод
    взяты у `tests/test_pages/test_impersonation_gate.py`.
    """
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))

    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    from_application = [
        name for name in imported if name == "app" or name.startswith("app.")
    ]

    assert not from_application, (
        f"гейт импортирует модули приложения {from_application} — ожидания "
        "могли быть выведены из проверяемого, и тест согласился бы с любой "
        "правкой"
    )


# --- регрессии: исход виден человеку на ОБОИХ шеллах --------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("code", sorted(REGISTRY_RECORDS))
async def test_every_notice_code_lands_with_its_words_on_the_main_shell(
    authed_client: AsyncClient, code: str
):
    """Каждый код реестра рисует СВОИ слова в общей области основного шелла.

    Это половина «исход не потерялся», которую не проверял НИ ОДИН тест до
    плана 08-06: прежде каждый исход рисовался своим блоком на своём экране, и
    двух исходов из четырнадцати не рисовалось нигде вовсе. Проверяется вся
    линия целиком — код в адресе, запись реестра, вариант плашки, область.
    """
    text, variant = REGISTRY_RECORDS[code]

    response = await authed_client.get(f"/history?notice={code}")

    assert response.status_code == 200
    areas = unescape(notice_areas(response.text))
    assert text in areas, (
        f"код {code!r} приехал в адрес и не нарисовал ничего: человек нажал "
        "кнопку и получил ту же страницу без единого слова"
    )
    assert f"alert--{variant}" in areas, (
        f"плашка кода {code!r} нарисована не тем вариантом: вариант решает и "
        "тон, и то, объявит ли вспомогательная технология сообщение настойчиво"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("code", sorted(REGISTRY_RECORDS))
async def test_every_notice_code_lands_with_its_words_on_the_auth_shell(
    client: AsyncClient, code: str
):
    """То же на ВТОРОМ шелле — и второй шелл здесь не формальность.

    Исход смены пароля приземляется на экран ВХОДА, то есть в `auth_base.html`.
    Две копии разметки области держались бы в единстве только бдительностью
    читателя: правка идентификатора, внесённая в один шелл и забытая во втором,
    оставила бы внеполосную подмену без цели молча. Источник у областей один, и
    этот тест — та проверка, которая упала бы, если бы копий стало две.
    """
    text, variant = REGISTRY_RECORDS[code]

    response = await client.get(f"/login?notice={code}")

    assert response.status_code == 200
    areas = unescape(notice_areas(response.text))
    assert text in areas, f"на шелле авторизации код {code!r} не нарисовал ничего"
    assert f"alert--{variant}" in areas


@pytest.mark.asyncio
async def test_an_unknown_notice_code_prints_nothing_at_all(
    authed_client: AsyncClient,
):
    """Незнакомый код не рисует НИЧЕГО — ни слов, ни пустой рамки.

    ⚠️ РАДИУС ЭТОГО СВОЙСТВА ВЫРОС ВМЕСТЕ С КАНАЛОМ. Параметр рисует плашку
    теперь на КАЖДОЙ странице обоих шеллов, а не на пяти экранах: сравнение
    ЦЕЛИКОМ по закрытому множеству и есть то единственное, что не даёт
    владельцу ссылки написать человеку сообщение от имени приложения где угодно
    (T-08-08).
    """
    hostile = "<b>Ваш+аккаунт+заблокирован</b>"

    response = await authed_client.get(f"/history?notice={hostile}")

    assert response.status_code == 200
    assert "alert--" not in notice_areas(response.text), (
        "неизвестный код нарисовал плашку"
    )
    assert "заблокирован" not in response.text, (
        "значение параметра напечатано пользователю от имени приложения"
    )


@pytest.mark.asyncio
async def test_saving_the_profile_finally_tells_the_person_it_worked(
    authed_client: AsyncClient,
):
    """Сохранение настроек профиля ВПЕРВЫЕ в истории продукта отвечает словами.

    ⚠️ ЭТОТ ТЕСТ ЗАКРЫВАЕТ МОЛЧАВШИЙ ПУТЬ, А НЕ ПЕРЕНОСИТ СУЩЕСТВУЮЩИЙ. До
    плана 08-06 обработчик писал в адрес БУЛЕВ признак сохранения, и отрисовки
    у этого признака не было НИ В ОДНОМ шаблоне: человек менял часовой пояс —
    то есть время, В КОТОРОЕ УХОДЯТ ЕГО РАССЫЛКИ, — и получал ту же страницу
    молча, неотличимо от «ничего не произошло». Регрессии на этот исход не
    существовало, потому что не существовало и самого ответа.

    Проверяется вся линия: адрес редиректа, приземление и слова на экране.
    """
    response = await authed_client.post(
        "/profile",
        data={"timezone": "Europe/Moscow"},
        headers={"Origin": "http://test", "Referer": "http://test/profile"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["location"]
    assert location == "/profile?notice=profile_saved", location

    landing = await authed_client.get(location)
    text, _variant = REGISTRY_RECORDS["profile_saved"]
    assert text in unescape(notice_areas(landing.text)), (
        "сохранение снова отвечает молча — исход есть, слов нет"
    )


# --- контроль: зубы гейта доказаны, а не заявлены -----------------------------


def _sources_with(path: str, source: str) -> dict[str, str]:
    """Копия дерева исходников с ОДНИМ подменённым файлом.

    Подмена идёт в памяти, а не на диске: контроль доказывает свойства
    РАЗБОРЩИКА, и записывать ради этого во временное дерево значило бы
    проверять заодно файловую систему.

    ⚠️ ПОДМЕНЁННЫЙ ШАБЛОН ПРОХОДИТ ТУ ЖЕ ПОДГОТОВКУ, ЧТО И НАСТОЯЩИЙ. Вырезание
    комментариев есть часть ОБХОДА, а не свойство файлов на диске: подсунув
    сырой шаблон мимо него, контроль проверял бы не тот разборщик, который
    работает на настоящем дереве, — и «проза не создаёт места» доказывалось бы
    на пути, которым проза никогда не идёт.
    """
    sources = _scanned_sources()
    assert path in sources, f"подменяемого файла {path} в области поиска нет"
    if path.endswith(".html"):
        source = HTML_COMMENT.sub("", JINJA_COMMENT.sub("", source))
    sources[path] = source
    return sources


def test_control_negative_a_returned_retired_key_reddens_the_gate():
    """ЧТО ДОКАЗЫВАЕТ: гейт ловит ВЕРНУВШЕЕСЯ снятое написание.

    Это первый отрицательный контроль, и он про самый вероятный способ вернуть
    снятое: будущая фаза добавляет обработчику собственный признак, потому что
    так было написано у соседа полгода назад.
    """
    module = "app/pages/profile.py"
    original = _scanned_sources()[module]
    returned = original + '\n_A_FUTURE_PHASE_MIGHT_WRITE = "/profile?saved=1"\n'

    hits = _retired_key_hits(_sources_with(module, returned))

    assert "?saved=" in hits and module in hits["?saved="], (
        "ГЕЙТ НЕ ЗАМЕТИЛ ВЕРНУВШЕЕСЯ СНЯТОЕ НАПИСАНИЕ — он зелёный по "
        "построению, и второй канал обратной связи заведётся мимо него"
    )


def test_control_negative_an_unregistered_code_reddens_the_gate():
    """ЧТО ДОКАЗЫВАЕТ: обход ловит код, заведённый МИМО реестра.

    Это второй отрицательный контроль, и он про случай, РАДИ КОТОРОГО обход и
    существует: код, добавленный будущей фазой в адрес и забытый в реестре.
    Такой код не роняет ничего сам по себе — он просто не рисует НИЧЕГО, и
    обнаруживается это жалобой на кнопку, вернувшую ту же страницу без слов.
    """
    module = "app/pages/profile.py"
    original = _scanned_sources()[module]
    invented = (
        original
        + '\n_A_FUTURE_PHASE_MIGHT_WRITE = "/profile?notice=a_code_nobody_registered"\n'
    )

    unregistered = _unregistered_codes(_sources_with(module, invented))

    assert "a_code_nobody_registered" in unregistered, (
        "ОБХОД НЕ ЗАМЕТИЛ КОД МИМО РЕЕСТРА — исход, записанный будущей фазой, "
        "молча не нарисует ничего"
    )


def test_control_negative_a_lost_outcome_reddens_the_completeness():
    """ЧТО ДОКАЗЫВАЕТ: утверждение полноты ловит ПОТЕРЯННЫЙ исход.

    Третий отрицательный контроль — про опасность самой этой правки (T-08-29):
    двенадцать редиректов сводились в один канал, и исход, выпавший при
    сведении, не роняет ничего сам по себе. Экран продолжает работать, кнопка
    продолжает нажиматься, слов не появляется.
    """
    module = "app/pages/history.py"
    original = _scanned_sources()[module]
    lost = original.replace("notices.RETRY_QUEUED", "notices.RETRY_BUSY")
    assert lost != original, "подмена ничего не заменила — контроль пуст"

    written = _written_codes(_sources_with(module, lost))

    assert "retry_queued" not in written, (
        "УТВЕРЖДЕНИЕ ПОЛНОТЫ НЕ ЗАМЕТИЛО ПОТЕРЯННЫЙ ИСХОД — успешная "
        "постановка повтора перестала бы сообщать о себе, и тест промолчал бы"
    )


def test_control_positive_a_retired_key_inside_a_template_comment_is_not_a_place():
    """ЧТО ДОКАЗЫВАЕТ: проза шаблона не создаёт места (правка 07-07).

    Комментарий, объясняющий снятие, набранный самим снятым написанием, уронил
    бы запрет, который сам же объясняет. Проверяются оба вида комментариев:
    Jinja и HTML.
    """
    module = "app/templates/auth/login.html"
    prose = (
        "{# Признак смены пароля писался как ?reset=success и снят планом "
        "08-06. #}\n"
        "<!-- Раздел оплаты писал ?error=payment; написание снято. -->\n"
        "<p>обычная разметка</p>"
    )

    hits = _retired_key_hits(_sources_with(module, prose))

    assert hits == {}, (
        f"проза шаблона посчитана настоящим местом ({hits}): объяснение "
        "снятия роняет собственный запрет, и следующий читатель снимет "
        "объяснение вместо того, чтобы снять место"
    )


def test_control_positive_the_untouched_source_tree_keeps_the_gate_green():
    """ЧТО ДОКАЗЫВАЕТ: на НЕИЗМЕНЁННОМ дереве гейт молчит.

    ⚠️ БЕЗ ЭТОГО КОНТРОЛЯ ВСЕ ОТРИЦАТЕЛЬНЫЕ ПРОШЛИ БЫ И У ГЕЙТА, КОТОРЫЙ
    КРАСНЕЕТ ВСЕГДА. «Ловит подмену» и «ловит ТОЛЬКО подмену» — разные
    утверждения, и доказательство зубов состоит из обоих: гейт, роняющий
    сборку на любом дереве, был бы не строже, а просто сломан, и его сняли бы
    первым же коммитом.
    """
    sources = _scanned_sources()

    assert _retired_key_hits(sources) == {}
    assert _unregistered_codes(sources) == set()
    assert set(REGISTRY_RECORDS) - _written_codes(sources) == set()

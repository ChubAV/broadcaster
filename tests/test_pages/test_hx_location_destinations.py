"""Экраны-цели заголовка перехода и их клиентский слой.

Фаза 10 перевела ветку удаления ПОСЛЕДНЕГО расписания с обычного
перенаправления на ответ 204 с заголовком перехода (`app/pages/htmx.py`,
`location_response`). Рантайм разметки на такой ответ делает ajax-переход:
подменяет содержимое тела документа и ИСПОЛНЯЕТ узлы сценария подменённого
тела. До фазы браузер строил документ заново, и инлайн-скрипт экрана исполнялся
ровно один раз; теперь он исполняется ВТОРОЙ раз в ТОЙ ЖЕ области имён.

Повторное объявление `const`/`let` на верхнем уровне есть РАННЯЯ ошибка языка:
скрипт падает целиком, до исполнения первой своей строки. Умирают загрузка
изображений, счётчик символов и снятие вложений — молча, без единого признака
на сервере.

⚠️ ГРАНИЦА МАШИННО УТВЕРЖДАЕМОГО НАЗЫВАЕТСЯ ЗДЕСЬ ПРЯМО, А НЕ ОСТАВЛЯЕТСЯ
ЧИТАТЕЛЮ. Правила этого модуля утверждают ровно два свойства: (1) ИСХОДНИК
инлайн-скрипта экрана редактора переживает ВТОРОЕ исполнение в одной области
имён — это утверждается ИСПОЛНЕНИЕМ исходника в интерпретаторе, а не чтением
его текста; (2) ни один экран, служащий целью заголовка перехода, не несёт
объявлений верхнего уровня в инлайн-скрипте — это утверждается разбором
исходника шаблонов. Здесь НЕ утверждается и утверждаться не может: что рантайм
браузера действительно ведёт себя по установленной цепи, что внеполосный узел
применён, что человек после перехода видит ЖИВОЙ клиентский слой. Машинной
подмены рантайма разметки в этом модуле нет намеренно — правило, изображающее
свопы htmx, вернуло бы фазе ровно тот дефект, которым она провалена первым
кругом: расхождение ЗАПИСИ с рантаймом. Человеческая половина есть шаг 1.10
обхода `10-UAT.md` и закрывается глазом, а не этим файлом.
"""

import ast
import json
import re
from pathlib import Path

import pytest
import pytest_asyncio

from tests.conftest import run_node_script
from tests.test_pages.test_editor_schedules import _seed_ad

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = PROJECT_ROOT / "app" / "templates"
PAGES_DIR = PROJECT_ROOT / "app" / "pages"

# Инлайн-скрипт = тег `<script>` БЕЗ атрибута `src`. Внешний файл сценария
# рантайм подменённого тела исполняет по другим правилам, и предметом этого
# модуля он не является.
INLINE_SCRIPT_RE = re.compile(
    r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.DOTALL | re.IGNORECASE
)

# ⚠️ ПРИЗНАК ПРИНАДЛЕЖНОСТИ ЭКРАНУ, А НЕ «ПЕРВЫЙ ПОПАВШИЙСЯ СКРИПТ». Документ
# редактора несёт ещё и скрипты общего шелла (включаемая плашка отказов), и
# правило, взявшее любое тело, меряло бы не тот предмет. Имя выбрано потому,
# что оно объявлено ИМЕННО этим экраном и ни одним другим.
EDITOR_SCRIPT_MARKER = "IMAGE_BASE_URL"

# ⚠️ ГАРНИР ПОЛУЧАЕТ ПАВЛОАД ПОДСТАНОВКОЙ, А НЕ СТАНДАРТНЫМ ВВОДОМ — форма
# наследована у гарнира жизненного цикла панели (план 09-19): общий запуск
# `run_node_script` принимает ровно исходник и потоков в подпроцесс не
# открывает. Образец `__PAYLOAD__` встречается ровно один раз, и единственность
# утверждается в `_run_twice` ПЕРЕД подстановкой.
#
# ⚠️ ГАРНИР ОБЯЗАН ЗАВЕРШАТЬСЯ УСПЕШНО В ЛЮБОМ СЛУЧАЕ. Общий запуск роняет
# правило на ненулевом коде подпроцесса, и красный от предмета стал бы
# неотличим от поломки гарнира: отказ каждого прогона ловится здесь и уезжает
# ЗАПИСЬЮ вердикта, а не кодом возврата.
DOUBLE_EXECUTION_HARNESS = """
'use strict';
const vm = require('vm');
const payload = __PAYLOAD__;
const SOURCE = payload.source;

// ⚠️ ЗАГЛУШКА ДОКУМЕНТА СНИСХОДИТЕЛЬНА ПО ПОСТРОЕНИЮ, И ОСНОВАНИЕ ЗАПИСАНО.
// Предмет правила — СТОЛКНОВЕНИЕ ОБЪЯВЛЕНИЙ при втором исполнении, а не
// полнота модели документа. Заглушка, спотыкающаяся на каком-нибудь узле,
// превратила бы правило в утверждение о заглушке: оба прогона падали бы
// одинаково, и вердикт «второй прогон отказал» перестал бы что-либо значить.
// Поэтому любое обращение к свойству возвращает вызываемый объект того же
// рода, а любой вызов возвращает его же.
function anything() {
  const target = function () {};
  return new Proxy(target, {
    get(_t, prop) {
      // Три свойства обязаны быть НАСТОЯЩИМИ, иначе снисходительность ломает
      // сама себя: приведение к строке, длина и перебор встречаются в хвосте
      // скрипта, и объект-заглушка на их месте уронил бы ПЕРВЫЙ прогон.
      if (prop === Symbol.toPrimitive) { return function () { return ''; }; }
      if (prop === Symbol.iterator) { return function* () {}; }
      if (prop === Symbol.toStringTag) { return 'Anything'; }
      if (prop === 'length') { return 0; }
      // `then` обязан отсутствовать: заглушка, у которой он есть, выглядит
      // обещанием, и `await` над ней зависает.
      if (prop === 'then') { return undefined; }
      return anything();
    },
    set() { return true; },
    has() { return true; },
    deleteProperty() { return true; },
    apply() { return anything(); },
    construct() { return anything(); }
  });
}

const sandbox = {};
for (const name of ['document', 'window', 'self', 'navigator', 'fetch',
                    'FormData', 'Event', 'CustomEvent', 'htmx',
                    'localStorage', 'sessionStorage', 'alert']) {
  sandbox[name] = anything();
}
// Консоль ГЛУШИТСЯ: вердикт есть ПОСЛЕДНЯЯ строка вывода, и диагностика
// подопытного исходника, попавшая туда, разъехалась бы с разбором.
sandbox.console = { log() {}, warn() {}, error() {}, info() {}, debug() {} };

// ⚠️ ОДНА ОБЛАСТЬ ИМЁН НА ОБА ПРОГОНА — И ЭТО ВЕСЬ ПРЕДМЕТ. Второй контекст
// сделал бы правило зелёным всегда: столкновению объявлений было бы негде
// произойти.
const context = vm.createContext(sandbox);

function runOnce() {
  try {
    vm.runInContext(SOURCE, context, { filename: 'inline-script.js' });
    return { ok: true, name: null, message: null };
  } catch (error) {
    return {
      ok: false,
      name: (error && error.name) ? error.name : String(error),
      message: (error && error.message) ? error.message : String(error)
    };
  }
}

const first = runOnce();
const second = runOnce();
console.log(JSON.stringify({ first: first, second: second }));
"""


def _run_twice(source: str) -> dict:
    """Исполнить поданный исходник ДВАЖДЫ в одной области имён и вернуть вердикт.

    ⚠️ ЗАПУСК ОБЩИЙ, А НЕ СОБСТВЕННЫЙ (записанное основание плана 09-19). Имя
    интерпретатора есть свойство ЗАПУСКА, а не свойство этого правила, и второй
    его экземпляр разошёлся бы с первым молча. Там же живёт и причина, по
    которой отсутствие интерпретатора РОНЯЕТ правило, а не пропускает его.
    """
    assert DOUBLE_EXECUTION_HARNESS.count("__PAYLOAD__") == 1, (
        "образец подстановки павлоада встречается в гарнире не один раз — "
        "подстановка стала бы молчаливой"
    )
    payload = json.dumps({"source": source})
    return run_node_script(DOUBLE_EXECUTION_HARNESS.replace("__PAYLOAD__", payload))


def _inline_script_bodies(markup: str) -> list[str]:
    """Тела инлайн-скриптов поданной РАЗМЕТКИ.

    Разметка принимается ПАРАМЕТРОМ, а не берётся из константы, и это то же
    несущее решение, по которому разборщик шаблонов проекта принимает каталог
    (`_all_templates(directory)`, план 07): группа контроля обязана подать
    ИЗМЕНЁННУЮ копию исходника, и разборщик, зашитый на единственный источник,
    сделал бы зубы правила незаявляемыми иначе как словами.
    """
    return [match.group(1) for match in INLINE_SCRIPT_RE.finditer(markup)]


def _editor_script_of(markup: str) -> str:
    """Единственное тело скрипта ЭКРАНА РЕДАКТОРА из поданной разметки.

    Ноль выбранных тел означал бы правило, зеленеющее на пустоте; два — что
    признак принадлежности экрану перестал различать, и правило меряет уже не
    тот скрипт.
    """
    bodies = [b for b in _inline_script_bodies(markup) if EDITOR_SCRIPT_MARKER in b]
    assert len(bodies) == 1, (
        f"в разметке выбрано тел скрипта экрана редактора: {len(bodies)}, а "
        f"обязано быть ровно одно (признак — объявление {EDITOR_SCRIPT_MARKER!r}). "
        "Ноль означает, что правило зеленело бы на пустоте; больше одного — что "
        "признак перестал принадлежать одному экрану"
    )
    return bodies[0]


@pytest_asyncio.fixture
async def editor_markup(authed_client, db_session) -> str:
    """НАСТОЯЩАЯ разметка редактора: посев объявления и запрос по маршруту.

    Сборкой шаблона с выдуманным окружением заменить нельзя: предмет — исходник
    ПОСЛЕ подстановок шаблонизатора, а значения настроек и базы приезжают в него
    сериализацией.
    """
    from sqlalchemy import select

    from app.models.user import User

    user = (
        await db_session.execute(
            select(User).where(User.email == "testuser@test.com")
        )
    ).scalar_one()
    ad = await _seed_ad(db_session, user.id)
    resp = await authed_client.get(f"/ads/{ad.id}/edit")
    assert resp.status_code == 200, (
        f"маршрут редактора ответил {resp.status_code}, а не 200 — мерить нечего"
    )
    return resp.text


# --- ЗАДАЧА 1: ИСХОДНИК ЭКРАНА-ЦЕЛИ ПЕРЕЖИВАЕТ ВТОРОЕ ИСПОЛНЕНИЕ --------------


@pytest.mark.asyncio
async def test_the_first_execution_of_the_editor_script_succeeds(editor_markup):
    """ПОЛОЖИТЕЛЬНЫЙ КОНТРОЛЬ (антивакуум), и он обязателен.

    Правило, у которого падают ОБА прогона, позеленело бы после правки шаблона,
    не утверждая о переисполнении ничего: достаточно было бы, чтобы отказ
    первого прогона перестал быть ранней ошибкой языка. Заодно это утверждение
    держит заглушку окружения ДОСТАТОЧНОЙ: весь скрипт обязан пройти до конца,
    включая хвост с подключением обработчиков и вызовом отрисовки.
    """
    verdict = _run_twice(_editor_script_of(editor_markup))
    assert verdict["first"]["ok"], (
        "ПЕРВЫЙ прогон исходника экрана редактора отказал "
        f"{verdict['first']['name']}: {verdict['first']['message']}. Это не "
        "дефект шаблона, а недостаточная заглушка окружения: правило, у "
        "которого падают оба прогона, ничего о переисполнении не утверждает"
    )


@pytest.mark.asyncio
async def test_the_editor_script_survives_a_second_execution_in_the_same_realm(
    editor_markup,
):
    """НЕСУЩЕЕ ПРАВИЛО: второй прогон в ТОЙ ЖЕ области имён не отказывает.

    Утверждается ИСПОЛНЕНИЕМ, а не чтением текста: правило, читающее исходник,
    зеленело бы на любой форме записи, которая ему нравится, и до места, где
    живёт дефект, не доставало бы вовсе.
    """
    verdict = _run_twice(_editor_script_of(editor_markup))
    assert verdict["second"]["ok"], (
        "ВТОРОЙ прогон исходника экрана редактора в той же области имён отказал "
        f"{verdict['second']['name']}: {verdict['second']['message']}. Экран "
        "редактора есть цель заголовка перехода (ветка удаления ПОСЛЕДНЕГО "
        "расписания, app/pages/schedules.py), рантайм разметки исполняет узлы "
        "сценария подменённого тела заново, и ранняя ошибка языка убивает "
        "клиентский слой целиком: загрузку изображений, счётчик символов и "
        "снятие вложений — молча, без единого признака на сервере"
    )


@pytest.mark.asyncio
async def test_a_reinstated_top_level_binding_reddens_the_double_execution_rule(
    editor_markup,
):
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ (мутация): зубы правила показаны, а не заявлены.

    Тому же гарниру подаётся исходник, в который ВЕРНУЛИ одно объявление
    верхнего уровня. Копия собирается в памяти; файл дерева не правится.
    """
    reinstated = (
        f"const {EDITOR_SCRIPT_MARKER} = 'reinstated';\n"
        + _editor_script_of(editor_markup)
    )
    verdict = _run_twice(reinstated)
    assert verdict["first"]["ok"], (
        "мутант обязан пройти ПЕРВЫЙ прогон — иначе контроль краснит правило "
        f"не тем: {verdict['first']['name']}: {verdict['first']['message']}"
    )
    assert not verdict["second"]["ok"], (
        "исходник с ВОЗВРАЩЁННЫМ объявлением верхнего уровня прошёл второй "
        "прогон — значит гарнир столкновения объявлений не ловит, и зелёный "
        "несущего правила ничего не стоит"
    )
    assert verdict["second"]["name"] == "SyntaxError", (
        "мутант отказал не РАННЕЙ ошибкой языка, а "
        f"{verdict['second']['name']}: {verdict['second']['message']} — гарнир "
        "меряет не тот предмет"
    )
    assert EDITOR_SCRIPT_MARKER in verdict["second"]["message"], (
        "отказ мутанта не называет имени столкнувшегося объявления: получено "
        f"{verdict['second']['message']!r}"
    )


# --- ЗАДАЧА 2: МНОЖЕСТВО ЦЕЛЕЙ ЗАГОЛОВКА ПЕРЕХОДА И ФОРМА ИХ СКРИПТОВ --------

# ⚠️ ЧИСЛО ПОСТАВЛЕНО ПРОГОНОМ ПОКРАСНЕВШЕГО ПРАВИЛА (план 10-13), а не
# посчитано в уме и не взято из текста плана. Летопись числа:
#   — ЧТО СЧИТАЕТСЯ: вызовы `respond(...)` в страничных модулях `app/pages/`,
#     У КОТОРЫХ НЕ ЗАДАН `fragment`. Ветвление `respond` (app/pages/htmx.py:305)
#     и есть определение множества: заголовок перехода отдаётся РОВНО тогда,
#     когда фрагмент не задан. Вызов с фрагментом на пути разметки отдаёт
#     фрагмент и целью перехода не является — правило, посчитавшее все вызовы
#     подряд, утверждало бы о множестве, которого нет.
#   — ЧЕМ ИЗМЕРЕНО: разбором ИСХОДНИКА В ДЕРЕВО (`ast`), а не грепом. Дерево
#     вырезает комментарии и докстринги СТРУКТУРНО, а не вычитанием образцов:
#     кодовая база проекта несёт абзацы-обоснования, свободно называющие и имя
#     функции, и имя её аргумента, — и счёт по прозе краснел бы на правку
#     документации, а хуже того, позволял бы комментарию ЗАМЕНИТЬ собой
#     исчезнувший вызов (записанное основание `_strip_comments`,
#     tests/test_templates/test_htmx_inventory.py).
#   — КАКИМ ПЛАНОМ: 10-13, третья партия закрытия гейпов Фазы 10.
#   — ПОСТАВЛЕНО ПРОГОНОМ: `вызовов слоя ответа БЕЗ фрагмента найдено 32, а
#     объявлено 0` (покрасневшее правило, до записи числа).
HX_LOCATION_DESTINATION_CALLS_DECLARED = 32

# Модуль, где `respond` ОБЪЯВЛЕН, из обхода исключён: его собственные вызовы
# принадлежат слою письма, а не страничному обработчику.
RESPONSE_LAYER_MODULE = "htmx.py"

# ⚠️ СБОРЩИКИ АДРЕСА ОБЪЯВЛЕНЫ ПОИМЁННО, И ЭТО ТОТ ЖЕ ПРИЁМ, ЧТО У ОБЪЯВЛЕННОГО
# ЧИСЛА. Адрес приземления не всегда литерал: часть вызовов подаёт переменную,
# собранную помощником. Помощник, встреченный обходом и ЗДЕСЬ НЕ ОБЪЯВЛЕННЫЙ,
# краснит прогон — иначе новый сборщик адреса привёз бы новый экран-цель молча.
# Формы сняты чтением `return` каждого помощника.
ADDRESS_BUILDERS = {
    # app/pages/account_groups.py:68 — с фильтром и без него адрес один и тот же
    # экран; строка запроса ниже отбрасывается приведением.
    "_screen_url": ("/accounts/{}/groups",),
    # app/pages/schedules.py:378 — с признаком возврата в редактор и без него.
    "_editor_url": ("/ads/{}/edit", "/schedules"),
}

# ⚠️ СООТВЕТСТВИЕ «АДРЕС ПРИЗЕМЛЕНИЯ → ШАБЛОН, ЕГО ОТРИСОВЫВАЮЩИЙ». Перечень
# обязан НАКРЫВАТЬ все адреса, найденные счётом: адрес без сопоставленного
# шаблона краснит прогон, иначе перечень объявлял бы себя полным, не будучи им.
# Адреса, собираемые из значений (идентификатор объявления, аккаунта,
# пользователя), приведены к ФОРМЕ адреса: подставляемое значение заменено на
# `{}`, строка запроса и якорь отброшены — экран определяется путём, а не
# параметрами.
HX_LOCATION_DESTINATION_TEMPLATES = {
    "/login": "auth/login.html",
    "/dashboard": "dashboard.html",
    "/ads": "ads/list.html",
    "/ads/{}/edit": "ads/form.html",
    "/schedules": "schedules/list.html",
    "/accounts": "accounts/list.html",
    "/accounts/{}/groups": "account_groups/list.html",
    "/history": "history/list.html",
    "/admin/users": "admin/users.html",
    "/admin/users/{}": "admin/user_detail.html",
    "/admin/workers": "admin/workers.html",
    "/admin/queue": "admin/queue.html",
}

# ⚠️ ИЗЪЯТИЕ РОВНО ОДНО, И ОНО С ОСНОВАНИЕМ НА ЗАПИСЬ, А НЕ МОЛЧАНИЕМ. Перечень
# без обоснований превращается в список того, до чего не дошли руки (форма,
# принятая планом 10-06). Основание каждой записи утверждается правилом
# непустоты ниже.
TOP_LEVEL_BINDING_EXEMPT_TEMPLATES = {
    "accounts/connect_tg_user.html": (
        "Экран несёт ТУ ЖЕ ФОРМУ, что и редактор (два объявления верхнего уровня "
        "в инлайн-скрипте, `let currentSessionId` и `let pollInterval`), но целью "
        "заголовка перехода НЕ ЯВЛЯЕТСЯ — ни один вызов слоя ответа на него не "
        "приземляет, и это ИЗМЕРЕНО счётом выше, а не предположено (утверждается "
        "правилом `test_the_connect_screen_is_not_a_transition_destination_today`). "
        "Вслепую он не правится: его функции достижимы ИЗ АТРИБУТОВ РАЗМЕТКИ — "
        "`onclick=\"startQR()\"`, `onclick=\"refreshQR()\"`, `onclick=\"submit2FA()\"` "
        "(app/templates/accounts/connect_tg_user.html:32,44,59), — и обёртка убрала "
        "бы их из области имён документа, сломав три работающие кнопки ради "
        "зелёного правила. Починка требует снятия трёх вызовов из атрибутов "
        "разметки и потому принадлежит фазе, которая сделает экран целью."
    ),
}

# ⚠️ ПРЕДМЕТ — ФОРМЫ, ДАЮЩИЕ РАННЮЮ ОШИБКУ ЯЗЫКА ПРИ ПОВТОРНОМ ОБЪЯВЛЕНИИ, И
# ТОЛЬКО ОНИ. `var` и `function` на верхнем уровне ПЕРЕОБЪЯВЛЯЮТСЯ БЕЗ ОШИБКИ
# (они var-областные, и второе исполнение просто переписывает связь), поэтому
# скрипт из-за них не падает и предметом этого правила они не являются. Внесение
# их сюда сделало бы правило шире поведения, а читатель понёс бы дальше широкую
# версию.
TOP_LEVEL_BINDING_KEYWORDS = ("const", "let", "class")

_BINDING_RE = re.compile(
    r"(?<![\w$.])(" + "|".join(TOP_LEVEL_BINDING_KEYWORDS) + r")\s+([A-Za-z_$][\w$]*)"
)


def _strip_js_comments(source: str) -> str:
    """Исходник JS без комментариев обоих родов, длина и переводы строк целы.

    ⚠️ ВЫРЕЗАНИЕ ЕСТЬ НЕСУЩЕЕ РЕШЕНИЕ ПРАВИЛА, А НЕ УДОБСТВО РАЗБОРА — то же
    основание, по которому вырезает `_strip_comments` гейта инвентаря. Абзац
    обоснования, называющий ЗАПРЕЩЁННУЮ ФОРМУ, отменял бы правило сам собой:
    оно краснело бы на прозе о том, что оно же и охраняет. Что вырезание
    работает, ПОКАЗАНО прогоном (`test_the_static_rule_does_not_cancel_itself`),
    а не заявлено здесь.

    Замена идёт ПРОБЕЛАМИ, а не удалением: номера строк в сообщении об отказе
    обязаны совпадать с номерами строк исходника, иначе читатель получит
    «где-то есть» вместо предмета.

    Разбор СОСТОЯНИЕМ СТРОКОВОГО ЛИТЕРАЛА, а не образцом: `//` внутри строки
    (`'https://…'`) комментарием не является, и вырезание по образцу съело бы
    хвост строки вместе с половиной выражения.
    """
    out = []
    i, n = 0, len(source)
    quote = None
    while i < n:
        c = source[i]
        if quote is not None:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(source[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "'\"`":
            quote = c
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and source[i + 1] == "/":
            while i < n and source[i] != "\n":
                out.append(" ")
                i += 1
            continue
        if c == "/" and i + 1 < n and source[i + 1] == "*":
            while i < n and not (source[i] == "*" and i + 1 < n and source[i + 1] == "/"):
                out.append("\n" if source[i] == "\n" else " ")
                i += 1
            out.append("  ")
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _blank_string_literals(source: str) -> str:
    """Исходник, у которого СОДЕРЖИМОЕ строковых литералов заменено пробелами.

    Нужно ровно для одного: считать уровень вложенности скобок. Фигурная скобка
    внутри строки или шаблонного литерала скобкой кода не является, и счёт по
    сырому тексту объявил бы верхний уровень там, где его нет. Длина и переводы
    строк сохраняются — номера строк в отказе обязаны остаться верными.
    """
    out = list(source)
    i, n = 0, len(source)
    quote = None
    while i < n:
        c = source[i]
        if quote is None:
            if c in "'\"`":
                quote = c
            i += 1
            continue
        if c == "\\" and i + 1 < n:
            out[i] = " "
            if source[i + 1] != "\n":
                out[i + 1] = " "
            i += 2
            continue
        if c == quote:
            quote = None
            i += 1
            continue
        if c != "\n":
            out[i] = " "
        i += 1
    return "".join(out)


def _top_level_bindings(script_body: str) -> list[tuple[int, str, str]]:
    """Объявления верхнего уровня тела скрипта: `(строка, ключевое слово, имя)`.

    ⚠️ ВЕРХНИЙ УРОВЕНЬ ЕСТЬ НУЛЕВАЯ ВЛОЖЕННОСТЬ СКОБОК, А НЕ НУЛЕВОЙ ОТСТУП.
    Отступ есть форма записи и от неё зависеть нельзя: обёртка, не сдвинувшая
    тело отступом (ровно та, что заведена этим планом в `ads/form.html` и до
    него — в `includes/htmx_error_banner.html`), оставила бы правило красным,
    хотя предмета в ней уже нет. Считается И КРУГЛАЯ вложенность: `for (const x
    of …)` на верхнем уровне объявляет связь, областью которой является ЦИКЛ, а
    не область имён документа, — столкновения при втором исполнении она не даёт.
    """
    body = _blank_string_literals(_strip_js_comments(script_body))
    depth_curly = 0
    depth_paren = 0
    depth_at = []
    for ch in body:
        depth_at.append((depth_curly, depth_paren))
        if ch == "{":
            depth_curly += 1
        elif ch == "}":
            depth_curly -= 1
        elif ch == "(":
            depth_paren += 1
        elif ch == ")":
            depth_paren -= 1

    found = []
    for match in _BINDING_RE.finditer(body):
        curly, paren = depth_at[match.start()]
        if curly != 0 or paren != 0:
            continue
        line = body.count("\n", 0, match.start()) + 1
        found.append((line, match.group(1), match.group(2)))
    return found


def _top_level_bindings_of_template(source: str) -> list[tuple[int, str, str]]:
    """Объявления верхнего уровня во ВСЕХ инлайн-скриптах поданного шаблона.

    Номер строки приводится к строке ШАБЛОНА, а не тела скрипта: читателю нужен
    предмет в файле, который он откроет.
    """
    from tests.test_templates.test_htmx_markup_gates import _strip_comments

    cleaned = _strip_comments(source)
    findings = []
    for match in INLINE_SCRIPT_RE.finditer(cleaned):
        offset = cleaned.count("\n", 0, match.start(1))
        for line, keyword, name in _top_level_bindings(match.group(1)):
            findings.append((offset + line, keyword, name))
    return findings


def _page_modules() -> list[tuple[str, str]]:
    """Страничные модули парами «имя файла — исходник», без слоя письма."""
    return [
        (path.name, path.read_text(encoding="utf-8"))
        for path in sorted(PAGES_DIR.glob("*.py"))
        if path.name != RESPONSE_LAYER_MODULE and not path.name.startswith("__")
    ]


def _address_forms(node, scope: dict) -> set[str]:
    """Формы адреса, к которым приводится выражение аргумента `redirect=`."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return {node.value}
    if isinstance(node, ast.JoinedStr):
        forms = {""}
        for piece in node.values:
            if isinstance(piece, ast.Constant) and isinstance(piece.value, str):
                tails = {piece.value}
            elif isinstance(piece, ast.FormattedValue):
                tails = _address_forms(piece.value, scope) or {"{}"}
            else:  # pragma: no cover — иных узлов у f-строки не бывает
                tails = {"{}"}
            forms = {head + tail for head in forms for tail in tails}
        return forms
    if isinstance(node, ast.Name):
        return set().union(*(_address_forms(v, scope) for v in scope.get(node.id, []))) if scope.get(node.id) else set()
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        builder = node.func.id
        assert builder in ADDRESS_BUILDERS, (
            f"адрес приземления собирает помощник `{builder}`, которого нет в "
            "ADDRESS_BUILDERS. Необъявленный сборщик привёз бы новый экран-цель "
            "молча — объявите его формы адреса, сняв их с `return` помощника"
        )
        return set(ADDRESS_BUILDERS[builder])
    return set()


def _normalize_address(address: str) -> str:
    """Адрес, приведённый к ФОРМЕ: без строки запроса и без якоря.

    Экран определяется ПУТЁМ: `?result=…` и `#sched-…` меняют то, ЧТО экран
    покажет, но не то, КАКОЙ это экран и какой у него клиентский слой.
    """
    return address.split("?", 1)[0].split("#", 1)[0]


def _transition_destination_calls() -> list[tuple[str, int, set[str]]]:
    """Вызовы слоя ответа, отдающие ЗАГОЛОВОК ПЕРЕХОДА.

    Возвращает `(модуль, строка, формы адреса приземления)` для каждого вызова
    `respond(...)`, У КОТОРОГО НЕ ЗАДАН `fragment`.
    """
    calls = []
    for name, source in _page_modules():
        tree = ast.parse(source, filename=name)
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            scope: dict[str, list] = {}
            for node in ast.walk(function):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            scope.setdefault(target.id, []).append(node.value)
            for node in ast.walk(function):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                    continue
                if node.func.id != "respond":
                    continue
                if any(keyword.arg == "fragment" for keyword in node.keywords):
                    continue
                redirect = next(
                    (kw.value for kw in node.keywords if kw.arg == "redirect"), None
                )
                assert redirect is not None, (
                    f"{name}:{node.lineno}: вызов слоя ответа без `redirect=` — "
                    "адрес приземления неизвестен, и цель перехода не выводится"
                )
                calls.append(
                    (name, node.lineno, {
                        _normalize_address(form)
                        for form in _address_forms(redirect, scope)
                    })
                )
    return calls


def test_the_number_of_transition_answering_calls_is_declared():
    """Число вызовов, отдающих заголовок перехода, ОБЪЯВЛЕНО и стережётся.

    ⚠️ ПРЕДМЕТ — МОЛЧАЛИВЫЙ ПРИЕЗД НОВОГО ЭКРАНА-ЦЕЛИ. Правило, стерегущее
    только ИЗВЕСТНЫЕ цели, слепо к новой — ровно та форма отказа, которой фаза
    провалена третьим кругом. Рост числа означает, что появился вызов, чей
    экран приземления никто на переисполнение не проверял; убыль — что цель
    исчезла, и перечень ниже сторожит то, чего уже нет.
    """
    calls = _transition_destination_calls()
    listing = "\n".join(f"  {mod}:{line} → {sorted(forms)}" for mod, line, forms in calls)
    assert len(calls) == HX_LOCATION_DESTINATION_CALLS_DECLARED, (
        f"вызовов слоя ответа БЕЗ фрагмента найдено {len(calls)}, а объявлено "
        f"{HX_LOCATION_DESTINATION_CALLS_DECLARED}. Найденное:\n{listing}"
    )


def test_every_transition_destination_has_a_declared_template():
    """Перечень целей ПОЛОН относительно счёта.

    Адрес без сопоставленного шаблона краснит прогон: перечень, не накрывающий
    счёт, объявлял бы себя полным, не будучи им, и статическое правило ниже
    молча не проверило бы новый экран.
    """
    found = {form for _, _, forms in _transition_destination_calls() for form in forms}
    missing = sorted(found - set(HX_LOCATION_DESTINATION_TEMPLATES))
    assert not missing, (
        f"адреса приземления без сопоставленного шаблона: {missing}. Пока адрес "
        "не сопоставлен шаблону, экран-цель никем не проверен на переисполнение"
    )
    stale = sorted(set(HX_LOCATION_DESTINATION_TEMPLATES) - found)
    assert not stale, (
        f"в перечне целей стоят адреса, которых счёт больше не находит: {stale}. "
        "Правило сторожило бы экран, целью перехода уже не являющийся"
    )
    for address, template in sorted(HX_LOCATION_DESTINATION_TEMPLATES.items()):
        assert (TEMPLATES_DIR / template).is_file(), (
            f"адресу {address} сопоставлен шаблон {template}, которого в дереве нет"
        )


def test_no_transition_destination_declares_a_top_level_binding_inline():
    """НЕСУЩЕЕ СТАТИЧЕСКОЕ ПРАВИЛО: цель перехода не несёт объявлений верхнего уровня.

    Утверждается ФОРМА ИСХОДНИКА целей. Что рантайм браузера ведёт себя по
    установленной цепи — не утверждается ничем машинным (см. докстринг модуля).
    """
    offenders = []
    for address, template in sorted(HX_LOCATION_DESTINATION_TEMPLATES.items()):
        if template in TOP_LEVEL_BINDING_EXEMPT_TEMPLATES:
            continue
        source = (TEMPLATES_DIR / template).read_text(encoding="utf-8")
        for line, keyword, binding in _top_level_bindings_of_template(source):
            offenders.append(f"  {template}:{line}: {keyword} {binding} (цель {address})")
    assert not offenders, (
        "экраны-цели заголовка перехода несут объявления верхнего уровня в "
        "инлайн-скрипте; второе исполнение падает РАННЕЙ ошибкой языка и "
        "убивает клиентский слой экрана целиком:\n" + "\n".join(offenders)
    )


def test_a_reinstated_top_level_binding_reddens_the_static_rule():
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ статического разбора: зубы показаны, а не заявлены.

    Разборщику подаётся КОПИЯ исходника экрана редактора с возвращённым
    объявлением верхнего уровня. Копия в памяти; файл дерева не правится.
    """
    template = HX_LOCATION_DESTINATION_TEMPLATES["/ads/{}/edit"]
    source = (TEMPLATES_DIR / template).read_text(encoding="utf-8")
    assert not _top_level_bindings_of_template(source), (
        "исходник дерева обязан быть чист — иначе контроль ниже ничего не доказывает"
    )
    mutant = source.replace(
        "<script>\n(function () {",
        "<script>\nconst REINSTATED_TOP_LEVEL = 1;\n(function () {",
        1,
    )
    assert mutant != source, "мутация не применилась — образец обёртки разъехался"
    findings = _top_level_bindings_of_template(mutant)
    assert findings, (
        "копия исходника с ВОЗВРАЩЁННЫМ объявлением верхнего уровня прошла "
        "разбор — значит статическое правило зубов не имеет"
    )
    lines = [line for line, _, _ in findings]
    names = [name for _, _, name in findings]
    assert "REINSTATED_TOP_LEVEL" in names, (
        f"отказ не называет ИМЕНИ возвращённого объявления: получено {findings}"
    )
    assert all(line > 0 for line in lines), (
        f"отказ не называет номера строки: получено {findings}"
    )


def test_the_static_rule_does_not_cancel_itself():
    """ПРАВИЛО НЕ САМООТМЕНЯЕТСЯ: комментарий, называющий запрещённую форму, инертен.

    Разборщику подаётся исходник, в который добавлена СТРОКА КОММЕНТАРИЯ,
    называющая ровно ту форму, которую правило запрещает. Вердикт обязан не
    измениться — иначе абзац обоснования отменял бы правило сам собой, и
    кодовая база проекта, несущая такие абзацы почти в каждом месте, красила бы
    прогон прозой.
    """
    template = HX_LOCATION_DESTINATION_TEMPLATES["/ads/{}/edit"]
    source = (TEMPLATES_DIR / template).read_text(encoding="utf-8")
    before = _top_level_bindings_of_template(source)
    with_prose = source.replace(
        "<script>\n(function () {",
        "<script>\n// ЗАПРЕЩЁННАЯ ФОРМА, НАЗВАННАЯ ПРОЗОЙ: const IMAGE_BASE_URL = 1;\n"
        "/* и второй род комментария: let pollInterval = null; */\n(function () {",
        1,
    )
    assert with_prose != source, "проза не добавилась — образец обёртки разъехался"
    after = _top_level_bindings_of_template(with_prose)
    assert after == before, (
        "вердикт правила изменился от ДОБАВЛЕННОГО КОММЕНТАРИЯ: было "
        f"{before}, стало {after}. Правило считает прозу и отменяет себя само"
    )


def test_every_exempt_template_carries_a_non_empty_rationale():
    """У каждой записи перечня изъятий основание НЕПУСТО.

    Перечень без обоснований превращается в список того, до чего не дошли руки
    (форма, принятая планом 10-06): читатель следующей фазы не отличит
    «решено и записано почему» от «забыли».
    """
    assert TOP_LEVEL_BINDING_EXEMPT_TEMPLATES, (
        "перечень изъятий пуст — правило непустоты стало бы вакуумным"
    )
    for template, rationale in sorted(TOP_LEVEL_BINDING_EXEMPT_TEMPLATES.items()):
        assert (TEMPLATES_DIR / template).is_file(), (
            f"изъят шаблон {template}, которого в дереве нет"
        )
        assert rationale and rationale.strip(), (
            f"изъятие {template} не несёт основания — изъятие без основания есть "
            "не решение, а умолчание"
        )


def test_the_connect_screen_is_not_a_transition_destination_today():
    """Основание изъятия ИЗМЕРЕНО, а не объявлено.

    Экран подключения изъят ровно потому, что целью заголовка перехода он не
    является. Как только вызов слоя ответа приземлит на него, это правило
    покраснеет — и изъятие придётся пересматривать, а не наследовать молча.
    """
    destinations = set(HX_LOCATION_DESTINATION_TEMPLATES.values())
    for template in sorted(TOP_LEVEL_BINDING_EXEMPT_TEMPLATES):
        assert template not in destinations, (
            f"шаблон {template} стои́т и в перечне ЦЕЛЕЙ, и в перечне ИЗЪЯТИЙ: "
            "изъятие сделало бы цель непроверенной молча. Основание изъятия "
            "(«целью перехода не является») больше не верно — пересмотрите его"
        )

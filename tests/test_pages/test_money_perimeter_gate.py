"""Машинный гейт ПЕРИМЕТРА ОПАСНЫХ МАРШРУТОВ (D-08, G-18, требование PAY-02).

ОПАСНЫЙ МАРШРУТ — тот, чьё второе исполнение НЕОБРАТИМО. Признаков два:
маршрут ставит задачу в очередь либо создаёт платёж. Второе нажатие по такому
маршруту приходит ВТОРЫМ НЕЗАВИСИМЫМ ЗАПРОСОМ, и клиентский атрибут блокировки
кнопки его не останавливает: разметка живёт в браузере, который второй запрос и
посылает. Значит удержание обязано существовать НА СЕРВЕРЕ и НЕЗАВИСИМО от
разметки, а гейт обязан утверждать, что оно там есть.

ПОЧЕМУ ПЕРИМЕТР СОБИРАЕТСЯ ОБХОДОМ, А НЕ ВЫПИСАН СПИСКОМ. Рукописный список
отвечает на вопрос «что мы решили про эти пять маршрутов» и молчит про шестой.
Здесь множество опасных маршрутов собирается ТЕМ ЖЕ разбором, которым
проверяется правило, и утверждается РАВЕНСТВО найденного объединению двух
объявленных перечней. Третий опасный маршрут, добавленный будущей фазой, не
попадёт ни в один перечень и уронит тест — вместо того чтобы оказаться без
удержания по умолчанию и обнаружиться второй необратимой отправкой в чужую
группу или вторым списанием денег. Механика взята у
``tests/test_pages/test_impersonation_gate.py`` целиком: там же записан и довод,
почему перечни ВЫПИСАНЫ РУКАМИ, а не выведены из проверяемого — тест,
выводящий ожидание из предмета проверки, согласился бы с любой правкой.

ДВА ПЕРЕЧНЯ, А НЕ ОДИН, И ЭТО СУТЬ ФОРМЫ (D-08). ``HOLD_REQUIRED`` — маршруты,
где удержание требуется И СУЩЕСТВУЕТ; обоснование называет, ЧЕМ именно оно
держится. ``HOLD_NOT_BUILT_YET`` — маршруты, которым удержание пришлось бы
ПОСТРОИТЬ, а не проверить; расширение на них отвергнуто решением D-08 как
расширение объёма вехи. Из ПЕРИМЕТРА они при этом не выпадают: без второго
перечня «не проверено» стало бы неотличимо от «не найдено», и первый же читатель
принял бы молчание за отсутствие опасности.

ЗАПРЕТ ОЧЕРЕДИ ЗАПРОСОВ ОГРАНИЧЕН ПЕРИМЕТРОМ, И ГРАНИЦА ДОКАЗАНА ОБЕИМИ
СТОРОНАМИ. Очередь наложенных запросов htmx превращает отброшенное второе
нажатие в ОТЛОЖЕННУЮ вторую отправку: запрос не отменяется, а ждёт и уходит.
На маршрутах периметра это запрещено. Вне периметра — разрешено и используется:
форма редактора объявлений ставит запросы в очередь ОСОЗНАННО, с обоснованием на
восемь строк (``app/templates/ads/form.html``), потому что ответ там несёт
идентификатор созданного черновика и терять его нельзя. Гейт «нигде нет очереди»
покраснел бы на этой форме зря, поэтому правило проведено по периметру, и обе
стороны границы закреплены контролями.

⚠️ ЧЕГО ГЕЙТ НЕ ВИДИТ — ВЫПИСАНО ЗДЕСЬ, А НЕ ОСТАВЛЕНО НА ДОГАДКУ. Гейт,
который чего-то не видит, ОБЯЗАН ТРЕБОВАТЬ, ЧТОБЫ ЭТОГО НЕ БЫЛО, — иначе
ненаписанная граница через один рефакторинг становится границей НЕИЗВЕСТНОЙ.
Границ три, и ни одна не закрыта молчанием:

1. ПОСТАНОВКА ЗАДАЧИ, СПРЯТАННАЯ ЗА ВСПОМОГАТЕЛЬНОЙ ФУНКЦИЕЙ СОСЕДНЕГО МОДУЛЯ,
   разбору не видна: в теле обработчика стоял бы вызов помощника, а сама
   постановка — за другим файлом, и обход не связал бы их ничем. Форма поэтому
   ЗАПРЕЩЕНА — ``test_no_queue_call_hides_outside_a_route_handler``: каждая
   постановка задачи в приложении обязана стоять ПРЯМО в теле обработчика
   маршрута страничного слоя.

2. СОЗДАНИЕ ПЛАТЕЖА ЧЕРЕЗ ПСЕВДОНИМ ИМПОРТА (``as``) переименовывает вызов, и
   обход по имени его не узнаёт. Форма ЗАПРЕЩЕНА —
   ``test_no_payment_creation_hides_behind_an_import_alias``. Обращение через
   модуль при этом разрешено и узнаётся наравне с голым именем: переименования
   там нет.

3. АДРЕС ДЕЙСТВИЯ, СОБРАННЫЙ ЦЕЛИКОМ ИЗ ПЕРЕМЕННЫХ, БЕЗ ЕДИНОГО ЛИТЕРАЛА (форма
   ``action="{{ action }}"`` общего макроса окна подтверждения), гейту
   непрозрачен: определить, ведёт ли он на периметр, нечем. Такой адрес
   разрешён ровно до тех пор, пока не объявляет очередь запросов, — и это
   утверждается ``test_no_opaque_address_declares_a_request_queue``. Сегодня
   общий макрос очереди не объявляет, а форма редактора объявлений, которая её
   объявляет, свой адрес собирает ИЗ ЛИТЕРАЛОВ и потому видна.

ПРИНЯТАЯ ГРАНИЦА, КОТОРУЮ ЗАКРЫТЬ НЕЛЬЗЯ, И ОНА ОДНА. Опасность определяется
двумя признаками — очередь и платёж. Маршрут, необратимо меняющий состояние без
очереди и без платежа (удаление записи), в периметр не попадает и удержания не
получает. Граница выбрана вслед за D-08 и требует РЕШЕНИЯ ЧЕЛОВЕКА, если
появится третий класс необратимого действия; она записана и в плане 08-10, и
здесь, чтобы не превратиться в умолчание.

ЗУБЫ ГЕЙТА ДОКАЗАНЫ, А НЕ ЗАЯВЛЕНЫ. Пять контролей в конце файла (``-k
control``) подают разбору ИЗМЕНЁННЫЕ копии исходников и разметки: гейт краснеет
на неклассифицированном опасном маршруте, на снятом удержании и на очереди
запросов внутри периметра — и ОСТАЁТСЯ ЗЕЛЁНЫМ на очереди ВНЕ периметра и на
нетронутом дереве. Последние два — не украшение: «ловит нарушение» и «ловит
ТОЛЬКО нарушение» суть разные высказывания, и второе из первого не следует.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Слой, в котором живут маршруты периметра. Каталог обходится ЦЕЛИКОМ и
# РЕКУРСИВНО: модуль, положенный будущей фазой в подкаталог, обязан попасть в
# обход сам, иначе гейт молча перестал бы видеть часть слоя ровно в тот момент,
# когда слой начал расти.
PAGE_DIRECTORY = "app/pages"

# Каталоги, в которых ищется СПРЯТАННАЯ постановка задачи. Шире страничного
# слоя намеренно: граница 1 докстринга — про помощника СОСЕДНЕГО модуля.
APPLICATION_DIRECTORY = "app"

TEMPLATE_DIRECTORY = "app/templates"

# Модуль, где объявлено имя ограничения схемы, которым держится денежный путь.
PAYMENT_SERVICE = "app/services/payment_service.py"

# Методы, которыми маршрут объявляется декоратором. Читающие методы включены
# намеренно: опасность здесь определяется НЕ методом, а тем, что маршрут делает.
# Две постановки задачи из пяти сегодня стоят в обработчиках `GET` — опросах
# состояния подключения, — и множество, суженное до изменяющих методов, их бы
# просто не увидело.
ROUTE_METHODS = frozenset(
    {"get", "post", "put", "patch", "delete", "head", "options", "api_route"}
)

# Признак постановки задачи в очередь: вызов метода с этим именем.
QUEUE_CALL = "send_task"

# Признак создания платежа: вызов функции с этим именем — голым либо через
# модуль. Переименование псевдонимом импорта запрещено отдельным утверждением.
PAYMENT_CALL = "create_payment"

# Имена удержаний, которые гейт ищет в исходнике по имени.
RETRY_HOLD = "_claim_retry_slot"
MONEY_HOLD = "OPEN_INTENT_INDEX_NAME"

# ⚠️ ЧИСЛО МАРШРУТОВ ПЕРИМЕТРА ВЫПИСАНО ОТДЕЛЬНЫМ УТВЕРЖДЕНИЕМ НАМЕРЕННО.
# Перечни ниже поймали бы появление шестого и сами, но по числу ВИДНО СРАЗУ, что
# именно произошло, а правка числа обязана быть осознанной: беззвучно выросшее
# число означает, что опасный маршрут появился, а решения о его удержании никто
# не принимал.
PERIMETER_ROUTES = 5


# =============================================================================
# Перечень 1: УДЕРЖАНИЕ ТРЕБУЕТСЯ И СУЩЕСТВУЕТ
# =============================================================================

# Обоснование называет, ЧЕМ ИМЕННО держится маршрут, а не «защищён». Перечень, у
# которого написано только «да», через фазу читается как «наверное, так надо», и
# проверить его нечем.
HOLD_REQUIRED = {
    "app/pages/billing.py::subscribe_to_plan": (
        "ДЕНЕЖНЫЙ ПУТЬ. Удержание — ОГРАНИЧЕНИЕ СХЕМЫ: частичный уникальный "
        "индекс незакрытого подписочного намерения, объявленный ревизией 0021 и "
        "моделью платежа (планы 08-03 и 08-05). Строка-намерение резервируется "
        "ДО обращения к ЮKassa, и второе намерение отвергает база, а не код, — "
        "то есть удержание живёт вне процесса приложения и от разметки не "
        "зависит вовсе. Имя ограничения объявлено константой "
        f"`{MONEY_HOLD}` в `{PAYMENT_SERVICE}`"
    ),
    "app/pages/history.py::history_retry": (
        "ПУТЬ РАССЫЛКИ. Удержание — ОКНО В ПАМЯТИ ПРОЦЕССА, открываемое вызовом "
        f"`{RETRY_HOLD}` ДО постановки задачи и ПЕРЕЖИВАЮЩЕЕ ответ: именно "
        "поэтому второе последовательное нажатие второй задачи не ставит, в том "
        "числе при выключенном JavaScript, когда панель подтверждения не "
        "открывается вовсе. Условие, при котором окно работает — ОДИН процесс "
        "боевого сервиса, — стало машинным в "
        "`tests/test_infra/test_web_service_is_single_process.py`"
    ),
}


# =============================================================================
# Перечень 2: УДЕРЖАНИЕ ПРИШЛОСЬ БЫ ПОСТРОИТЬ (D-08)
# =============================================================================

# ⚠️ ЭТОТ ПЕРЕЧЕНЬ СУЩЕСТВУЕТ РОВНО ЗАТЕМ, ЧТОБЫ «НЕ ПРОВЕРЕНО» НЕ СТАЛО
# НЕОТЛИЧИМО ОТ «НЕ НАЙДЕНО». Эти маршруты в периметре — они ставят задачу в
# очередь, — но удержания у них нет, и решение D-08 состоит в том, что строить
# его в этой вехе не будут: постройка удержания есть расширение объёма, а не
# проверка сделанного. Обоснование называет это ПРЯМО, а не смягчает.
HOLD_NOT_BUILT_YET = {
    "app/pages/accounts.py::accounts_connect_wa_status": (
        "опрос состояния подключения WhatsApp ставит задачу синхронизации групп "
        "при переходе в подключённое состояние. Удержания НЕТ, и его пришлось "
        "бы ПОСТРОИТЬ (D-08): цена второго исполнения здесь — лишний проход "
        "синхронизации, а не вторая необратимая отправка и не второе списание"
    ),
    "app/pages/accounts.py::accounts_connect_max_status": (
        "опрос состояния подключения MAX — то же самое и по той же причине: "
        "удержания НЕТ, строить его в этой вехе решением D-08 не будут"
    ),
    "app/pages/accounts.py::accounts_retry_sync": (
        "повтор синхронизации групп аккаунта ставит задачу по нажатию человека. "
        "Удержания НЕТ; ближайшее по смыслу — реестр идущих синхронизаций "
        "`_claim_sync_slot` в том же модуле, но на ЭТОМ маршруте он не "
        "открывается, и выдать соседнее удержание за здешнее значило бы "
        "написать в перечне неправду. Строить решением D-08 не будут"
    ),
}


# =============================================================================
# Разбор исходника
# =============================================================================


@dataclass(frozen=True)
class _Route:
    """Одно объявление маршрута страничного слоя."""

    module: str
    handler: str
    path: str | None
    first_line: int
    last_line: int
    queues_a_task: bool
    creates_a_payment: bool

    @property
    def key(self) -> str:
        return f"{self.module}::{self.handler}"

    @property
    def is_dangerous(self) -> bool:
        return self.queues_a_task or self.creates_a_payment


def _page_sources() -> dict[str, str]:
    """Относительный путь → ТЕКСТ исходника страничного слоя.

    Возвращается словарь текстов, а не путей, ровно затем, чтобы контроли в
    конце файла могли подать разбору ИЗМЕНЁННУЮ копию, не трогая ни одного
    боевого файла.
    """
    sources: dict[str, str] = {}
    for path in sorted((PROJECT_ROOT / PAGE_DIRECTORY).glob("**/*.py")):
        sources[str(path.relative_to(PROJECT_ROOT))] = path.read_text(encoding="utf-8")
    return sources


def _application_sources() -> dict[str, str]:
    """Относительный путь → ТЕКСТ исходника ВСЕГО приложения.

    Шире страничного слоя: граница 1 докстринга — про постановку задачи,
    спрятанную за помощником СОСЕДНЕГО модуля, и увидеть её можно только обойдя
    все модули, а не один слой.
    """
    sources: dict[str, str] = {}
    for path in sorted((PROJECT_ROOT / APPLICATION_DIRECTORY).glob("**/*.py")):
        sources[str(path.relative_to(PROJECT_ROOT))] = path.read_text(encoding="utf-8")
    return sources


def _template_sources() -> dict[str, str]:
    """Относительный путь → ТЕКСТ шаблона разметки."""
    sources: dict[str, str] = {}
    for path in sorted((PROJECT_ROOT / TEMPLATE_DIRECTORY).glob("**/*.html")):
        sources[str(path.relative_to(PROJECT_ROOT))] = path.read_text(encoding="utf-8")
    return sources


def _route_decorator_path(decorator: ast.Call) -> tuple[bool, str | None]:
    """`(это объявление маршрута, адрес)` для одного декоратора.

    Адрес читается только из ПЕРВОГО позиционного литерала: адрес, собранный
    выражением, вернётся как `None`, и правило очереди на таком маршруте
    проверить будет нечем — сегодня таких нет, а появись он, отсутствие адреса
    видно в отказе, а не растворяется в зелёном цвете.
    """
    func = decorator.func
    if not isinstance(func, ast.Attribute) or func.attr not in ROUTE_METHODS:
        return False, None
    path = None
    if decorator.args:
        first = decorator.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            path = first.value
    return True, path


def _is_queue_call(node: ast.AST) -> bool:
    """Постановка задачи в очередь — вызов метода с именем `send_task`.

    Разбор по дереву, а не грепом: строка `send_task` встречается в комментарии
    над самой постановкой (`app/pages/history.py`), и греп посчитал бы её вторым
    вхождением, а число маршрутов периметра — ложно выросшим.
    """
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == QUEUE_CALL
    )


def _is_payment_call(node: ast.AST) -> bool:
    """Создание платежа — вызов `create_payment` голым именем либо через модуль."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == PAYMENT_CALL
    if isinstance(func, ast.Attribute):
        return func.attr == PAYMENT_CALL
    return False


def _routes(sources: dict[str, str]) -> dict[str, _Route]:
    """Каждое объявление маршрута страничного слоя в поданных исходниках."""
    routes: dict[str, _Route] = {}

    for module, text in sources.items():
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            declares = False
            path: str | None = None
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                is_route, decorator_path = _route_decorator_path(decorator)
                if is_route:
                    declares = True
                    path = path or decorator_path
            if not declares:
                continue

            body = list(ast.walk(node))
            routes[f"{module}::{node.name}"] = _Route(
                module=module,
                handler=node.name,
                path=path,
                first_line=node.lineno,
                last_line=max(
                    getattr(element, "lineno", node.lineno) for element in body
                ),
                queues_a_task=any(_is_queue_call(element) for element in body),
                creates_a_payment=any(_is_payment_call(element) for element in body),
            )

    return routes


def _perimeter(sources: dict[str, str]) -> dict[str, _Route]:
    """Маршруты, попадающие в периметр: ставят задачу либо создают платёж."""
    return {key: route for key, route in _routes(sources).items() if route.is_dangerous}


def _unclassified(sources: dict[str, str]) -> set[str]:
    """Маршруты периметра, не попавшие НИ В ОДИН из двух перечней.

    Это и есть предмет главного утверждения файла: непустой результат означает,
    что опасный маршрут существует, а решения о его удержании никто не принимал.
    """
    return {
        key
        for key in _perimeter(sources)
        if key not in HOLD_REQUIRED and key not in HOLD_NOT_BUILT_YET
    }


def _first_line_of_call(route: _Route, tree_of_module: ast.Module, predicate) -> int | None:
    """Номер строки первого вызова, удовлетворяющего признаку, в теле маршрута."""
    for node in ast.walk(tree_of_module):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != route.handler:
            continue
        lines = [element.lineno for element in ast.walk(node) if predicate(element)]
        if lines:
            return min(lines)
    return None


def _named_hold_is_missing(sources: dict[str, str]) -> dict[str, str]:
    """Ключ маршрута → ЧТО ИМЕННО не найдено, для маршрутов первого перечня.

    ⚠️ ОТКАЗ ОБЯЗАН НАЗЫВАТЬ НЕНАЙДЕННОЕ. Сообщение «удержание отсутствует»
    отправляет читателя искать по всему обработчику; здесь называется имя
    вызова или константы, которых не хватает, — то есть ровно то, что чинить.

    Проверок ровно две, по числу записей перечня, и связаны они с ключами
    маршрутов ЯВНО: запись, добавленная в перечень без своей проверки, роняет
    утверждение отдельным сообщением, а не проходит зелёной.
    """
    routes = _routes(sources)
    missing: dict[str, str] = {}

    for key in HOLD_REQUIRED:
        route = routes.get(key)
        if route is None:
            missing[key] = (
                "маршрут объявлен в перечне удержаний, но в исходнике его нет "
                "вовсе — перечень разошёлся с деревом"
            )
            continue

        module_tree = ast.parse(sources[route.module])

        if key.endswith("::history_retry"):
            # ПУТЬ РАССЫЛКИ: окно удержания открывается ДО постановки задачи.
            # Порядок здесь и есть защита: окно, открытое ПОСЛЕ обращения к
            # брокеру, не остановило бы второе нажатие, успевшее прийти между
            # двумя строками.
            hold_at = _first_line_of_call(
                route,
                module_tree,
                lambda element: (
                    isinstance(element, ast.Call)
                    and isinstance(element.func, ast.Name)
                    and element.func.id == RETRY_HOLD
                ),
            )
            queue_at = _first_line_of_call(route, module_tree, _is_queue_call)
            if hold_at is None:
                missing[key] = (
                    f"в теле обработчика нет вызова `{RETRY_HOLD}` — окно "
                    "удержания повтора не открывается, и второе нажатие "
                    "поставит вторую необратимую отправку"
                )
            elif queue_at is not None and hold_at > queue_at:
                missing[key] = (
                    f"вызов `{RETRY_HOLD}` стоит на строке {hold_at}, ПОСЛЕ "
                    f"постановки задачи на строке {queue_at}: окно, открытое "
                    "после обращения к брокеру, второе нажатие не держит"
                )
            continue

        if key.endswith("::subscribe_to_plan"):
            # ДЕНЕЖНЫЙ ПУТЬ: вызов создания платежа в теле обработчика и имя
            # ограничения схемы, объявленное модулем сервиса.
            #
            # ⚠️ ГЕЙТ УТВЕРЖДАЕТ ОБЪЯВЛЕНИЕ ИМЕНИ, А НЕ РАЗБОР ОТКАЗА ПО ИМЕНИ.
            # Отказ ограничения различается ПЕРЕЧИТЫВАНИЕМ СОСТОЯНИЯ, а не
            # текстом ошибки драйвера: имени индекса в сообщении SQLite нет
            # вовсе (план 08-05). Константа здесь — якорь поиска, кодом она не
            # читается, и это записано над самой константой. Что ограничение
            # действительно объявлено обоими источниками схемы, утверждает
            # `tests/test_models/test_payment_open_intent_index.py`; здесь оно
            # не переутверждается, чтобы у свойства не стало двух хозяев.
            if not route.creates_a_payment:
                missing[key] = (
                    f"в теле обработчика нет вызова `{PAYMENT_CALL}` — "
                    "денежный путь ведёт мимо места, где стоит потолок"
                )
                continue
            service = (PROJECT_ROOT / PAYMENT_SERVICE).read_text(encoding="utf-8")
            declared = any(
                isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == MONEY_HOLD
                    for target in node.targets
                )
                for node in ast.walk(ast.parse(service))
            )
            if not declared:
                missing[key] = (
                    f"в `{PAYMENT_SERVICE}` не объявлена константа "
                    f"`{MONEY_HOLD}` — имя ограничения схемы, которым держится "
                    "денежный путь, перестало быть названным"
                )
            continue

        missing[key] = (
            "для этой записи перечня в гейте нет ПРОВЕРКИ удержания: запись "
            "объявляет, чем маршрут держится, а утвердить это нечем — допиши "
            "проверку рядом с двумя соседними"
        )

    return missing


# =============================================================================
# Разбор разметки: очередь запросов на адресе периметра
# =============================================================================

_JINJA = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.S)
_LITERAL = re.compile(r"'[^']*'|\"[^\"]*\"")
_ATTRIBUTE = re.compile(r"""([A-Za-z_:@][-\w:.]*)\s*=\s*("([^"]*)"|'([^']*)')""")

# Атрибут, объявляющий стратегию наложения запросов, и слово, которым в нём
# называется ОЧЕРЕДЬ. Отмена (`abort`, `drop`, `replace`) правилом не задета:
# отменённый запрос второй отправки не производит.
SYNC_ATTRIBUTE = "hx-sync"
QUEUE_WORD = "queue"

# Атрибуты, несущие АДРЕС ДЕЙСТВИЯ элемента.
ADDRESS_ATTRIBUTES = (
    "action",
    "hx-post",
    "hx-get",
    "hx-put",
    "hx-patch",
    "hx-delete",
)


def _opening_tags(text: str) -> list[str]:
    """Открывающие теги разметки, выделенные ПОСИМВОЛЬНО, а не одним выражением.

    Регулярное выражение вида `<[^>]*>` разрезало бы тег по первому же `>`
    внутри значения атрибута или внутри вставки шаблонизатора, а такие в проекте
    есть (обработчики Alpine несут стрелки и сравнения). Разбор ведётся
    состоянием: кавычки и вставки `{{ }}` / `{% %}` закрывают `>` от чтения.
    """
    tags: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        if text[index] != "<" or index + 1 >= length or not text[index + 1].isalpha():
            index += 1
            continue
        cursor = index + 1
        quote: str | None = None
        while cursor < length:
            char = text[cursor]
            if quote is not None:
                if char == quote:
                    quote = None
                cursor += 1
                continue
            if char in "\"'":
                quote = char
                cursor += 1
                continue
            if text.startswith("{{", cursor):
                closing = text.find("}}", cursor)
                cursor = length if closing == -1 else closing + 2
                continue
            if text.startswith("{%", cursor):
                closing = text.find("%}", cursor)
                cursor = length if closing == -1 else closing + 2
                continue
            if char == ">":
                break
            cursor += 1
        tags.append(text[index : cursor + 1])
        index = cursor + 1
    return tags


def _attributes(tag: str) -> dict[str, str]:
    """Атрибуты тега со значениями. Повтор имени берётся первым вхождением."""
    found: dict[str, str] = {}
    for match in _ATTRIBUTE.finditer(tag):
        name = match.group(1).lower()
        value = match.group(3) if match.group(3) is not None else match.group(4)
        found.setdefault(name, value or "")
    return found


def _splice_literals(expression: str) -> str:
    """Литералы выражения шаблонизатора, склеенные через `*` на местах пропусков.

    Адрес `{{ '/ads/' ~ ad.id ~ '/edit' if ad else '/ads/new' }}` собран из
    литералов, и без этой склейки он выглядел бы одной сплошной вставкой, о
    которой известно только то, что она есть. Со склейкой видна ФОРМА адреса, и
    сравнить её с формой маршрута периметра уже есть чем.
    """
    pieces: list[str] = []
    cursor = 0
    for match in _LITERAL.finditer(expression):
        gap = expression[cursor : match.start()]
        if gap.strip():
            pieces.append("*")
        pieces.append(match.group(0)[1:-1])
        cursor = match.end()
    if expression[cursor:].strip():
        pieces.append("*")
    return "".join(pieces)


def _address_candidates(value: str) -> set[str]:
    """Возможные формы адреса: вставки как подстановка и как склейка литералов."""
    candidates = {_JINJA.sub("*", value).strip()}
    whole = re.fullmatch(r"\s*\{\{(?P<body>.*)\}\}\s*", value, re.S)
    if whole:
        spliced = _splice_literals(whole.group("body"))
        if spliced:
            candidates.add(spliced)
    return {candidate.split("?")[0].split("#")[0] for candidate in candidates}


def _leads_to(address: str, path: str) -> bool:
    """Ведёт ли адрес разметки на маршрут с этой формой пути.

    Сравнение ПОСЕГМЕНТНОЕ: параметр пути (`{log_id}`) и вставка шаблонизатора
    (`*`) считаются подстановочными. Сегмент, СОДЕРЖАЩИЙ вставку, тоже считается
    подстановочным — ошибаться этому гейту полагается в сторону отказа, а не в
    сторону молчания.
    """
    left = address.split("/")
    right = path.split("/")
    if len(left) != len(right):
        return False
    for actual, expected in zip(left, right):
        if expected.startswith("{") and expected.endswith("}"):
            continue
        if "*" in actual:
            continue
        if actual != expected:
            return False
    return True


def _declares_a_queue(tag: str) -> bool:
    value = _attributes(tag).get(SYNC_ATTRIBUTE)
    return value is not None and QUEUE_WORD in value.lower()


def _queued_perimeter_forms(
    sources: dict[str, str], templates: dict[str, str]
) -> set[str]:
    """`шаблон::адрес` — места, где форма маршрута периметра объявила очередь."""
    paths = [
        route.path for route in _perimeter(sources).values() if route.path is not None
    ]

    offenders: set[str] = set()
    for template, text in templates.items():
        for tag in _opening_tags(text):
            if not _declares_a_queue(tag):
                continue
            attributes = _attributes(tag)
            for name in ADDRESS_ATTRIBUTES:
                value = attributes.get(name)
                if value is None:
                    continue
                for candidate in _address_candidates(value):
                    if any(_leads_to(candidate, path) for path in paths):
                        offenders.add(f"{template}::{value}")
    return offenders


def _opaque_queued_addresses(templates: dict[str, str]) -> set[str]:
    """Места, где очередь объявлена на адресе БЕЗ ЕДИНОГО ЛИТЕРАЛА.

    Такой адрес гейту непрозрачен: определить, ведёт ли он на периметр, нечем —
    и очередь на нём была бы разрешена ПО УМОЛЧАНИЮ, ровно тем дефектом, ради
    которого файл написан.
    """
    offenders: set[str] = set()
    for template, text in templates.items():
        for tag in _opening_tags(text):
            if not _declares_a_queue(tag):
                continue
            attributes = _attributes(tag)
            addresses = [
                attributes[name] for name in ADDRESS_ATTRIBUTES if name in attributes
            ]
            if not addresses:
                offenders.add(f"{template}::<адреса действия нет вовсе>")
                continue
            for value in addresses:
                static = _JINJA.sub("", value).strip()
                inside = "".join(
                    match.group(0) for match in _JINJA.finditer(value)
                )
                if not static and not _LITERAL.search(inside):
                    offenders.add(f"{template}::{value}")
    return offenders


# =============================================================================
# Гейт
# =============================================================================


def test_the_number_of_perimeter_routes_is_the_declared_one():
    """Число маршрутов периметра равно выписанному.

    ⚠️ БЕЗЗВУЧНО ВЫРОСШЕЕ ЧИСЛО ОЗНАЧАЕТ, ЧТО ОПАСНЫЙ МАРШРУТ ПОЯВИЛСЯ, А
    РЕШЕНИЯ О ЕГО УДЕРЖАНИИ НИКТО НЕ ПРИНИМАЛ. Перечни поймали бы это и сами, но
    по числу видно СРАЗУ, что именно произошло.
    """
    perimeter = _perimeter(_page_sources())

    assert len(perimeter) == PERIMETER_ROUTES, (
        f"маршрутов периметра стало {len(perimeter)}, а выписано "
        f"{PERIMETER_ROUTES}:\n  " + "\n  ".join(sorted(perimeter))
        + "\n\nОпасный маршрут появился или исчез — обнови число вместе с "
        "решением о его удержании."
    )


def test_every_perimeter_route_is_classified():
    """ЗАМЫКАЮЩЕЕ УТВЕРЖДЕНИЕ: объединение двух перечней РАВНО найденному.

    ⚠️ ИМЕННО ЭТО УТВЕРЖДЕНИЕ ОТЛИЧАЕТ ГЕЙТ ОТ СПИСКА, И БЕЗ НЕГО ФАЙЛ
    БЕССМЫСЛЕН. Третий опасный маршрут, добавленный будущей фазой, не попадёт ни
    в один перечень и уронит тест — вместо того чтобы остаться без удержания по
    умолчанию и обнаружиться второй отправкой или вторым списанием.
    """
    unclassified = _unclassified(_page_sources())

    assert not unclassified, (
        "в страничном слое есть ОПАСНЫЕ маршруты, о которых этот гейт не "
        "знает:\n  " + "\n  ".join(sorted(unclassified))
        + "\n\nЧТО ДЕЛАТЬ. Маршрут ставит задачу в очередь либо создаёт платёж, "
        "то есть его второе исполнение необратимо. Реши, есть ли у него "
        "серверное удержание, и внеси его В ОДИН из двух перечней этого файла: "
        "HOLD_REQUIRED (удержание существует — назови, ЧЕМ именно оно держится, "
        "и допиши его проверку в `_named_hold_is_missing`) или "
        "HOLD_NOT_BUILT_YET (удержания нет — назови прямо, что его пришлось бы "
        "ПОСТРОИТЬ). Молча удалять это утверждение нельзя: без него периметр "
        "перестаёт быть периметром."
    )


def test_the_two_sets_do_not_overlap():
    """Перечни не пересекаются: у каждого маршрута ОДИН ответ про удержание.

    Маршрут, попавший в оба, означает два ответа на один вопрос — «удержание
    есть» и «удержания нет», — и какой из них читает человек, зависело бы от
    того, до какого перечня он долистал.
    """
    overlap = set(HOLD_REQUIRED) & set(HOLD_NOT_BUILT_YET)

    assert not overlap, (
        f"маршрут объявлен и удержанным, и непостроенным: {sorted(overlap)}"
    )


def test_every_declared_route_carries_a_reason():
    """У каждой записи обоих перечней написано ОБОСНОВАНИЕ, а не пустая строка.

    Перечень, у которого не написано, почему кто-то в него входит, через фазу
    превращается в «наверное, так надо», и следующая фаза читает его как список
    без основания.
    """
    unexplained = {
        key
        for key, reason in (*HOLD_REQUIRED.items(), *HOLD_NOT_BUILT_YET.items())
        if not reason.strip()
    }

    assert not unexplained, (
        "запись перечня не снабжена обоснованием:\n  " + "\n  ".join(sorted(unexplained))
    )


def test_every_required_hold_exists_in_the_source():
    """На каждом маршруте первого перечня удержание НАЙДЕНО в исходнике по имени.

    ⚠️ УТВЕРЖДЕНИЕ ПО ДЕРЕВУ, А НЕ ПО ТЕКСТУ ФАЙЛА. Обработчик, у которого про
    удержание написано в докстринге, при чтении глазами выглядит защищённым и не
    защищён ничем — ровно тот случай, ради которого гейт смотрит на ВЫЗОВЫ в
    теле, а не на упоминания в файле.
    """
    missing = _named_hold_is_missing(_page_sources())

    assert not missing, "удержание, объявленное в перечне, в исходнике не найдено:\n  " + "\n  ".join(
        f"{key}: {reason}" for key, reason in sorted(missing.items())
    )


def test_no_perimeter_route_carries_a_queued_request_sync():
    """Ни одна форма маршрута периметра не объявляет ОЧЕРЕДЬ запросов.

    ⚠️ ПРАВИЛО ПРИМЕНЯЕТСЯ ТОЛЬКО К МАРШРУТАМ ПЕРИМЕТРА, И ЭТО НЕ ПОСЛАБЛЕНИЕ.
    Очередь превращает отброшенное второе нажатие в ОТЛОЖЕННУЮ вторую отправку:
    запрос не отменяется, а ждёт и уходит. Вне периметра очередь законна и
    используется осознанно — форма редактора объявлений несёт её с обоснованием
    на восемь строк, потому что ответ там переносит идентификатор созданного
    черновика. Гейт «нигде нет очереди» покраснел бы на ней зря, и обе стороны
    границы закреплены контролями.
    """
    offenders = _queued_perimeter_forms(_page_sources(), _template_sources())

    assert not offenders, (
        "форма маршрута ПЕРИМЕТРА объявляет очередь наложенных запросов:\n  "
        + "\n  ".join(sorted(offenders))
        + "\n\nВторое нажатие здесь не отбрасывается, а ждёт и уходит вторым "
        "запросом — то есть второй необратимой отправкой или вторым платежом. "
        f"Сними `{SYNC_ATTRIBUTE}` с очередью на этом адресе либо перенеси "
        "стратегию на отмену."
    )


def test_no_opaque_address_declares_a_request_queue():
    """Очередь не объявлена на адресе, о котором гейту НИЧЕГО не известно.

    ⚠️ ЭТО ЗАКРЫТИЕ СОБСТВЕННОЙ СЛЕПОТЫ, А НЕ ПРИДИРКА (граница 3 докстринга).
    Адрес, собранный целиком из переменных без единого литерала — форма
    `action="{{ action }}"` общего макроса окна подтверждения, — не даёт
    определить, ведёт ли он на периметр. Очередь на таком адресе оказалась бы
    разрешена ПО УМОЛЧАНИЮ. Гейт, который чего-то не видит, обязан требовать,
    чтобы этого и не было.
    """
    offenders = _opaque_queued_addresses(_template_sources())

    assert not offenders, (
        "очередь запросов объявлена на адресе, который гейт прочитать не "
        "может:\n  " + "\n  ".join(sorted(offenders))
        + "\n\nОпредели, ведёт ли адрес на маршрут периметра, нечем — значит "
        "очередь здесь запрещена. Собери адрес из литералов либо сними очередь."
    )


def test_no_queue_call_hides_outside_a_route_handler():
    """Каждая постановка задачи стоит ПРЯМО в теле обработчика маршрута.

    ⚠️ ГРАНИЦА 1 ДОКТРИНГА, ЗАКРЫТАЯ УТВЕРЖДЕНИЕМ, А НЕ МОЛЧАНИЕМ. Постановка,
    вынесенная в помощника соседнего модуля, обходу невидима: в теле
    обработчика стоял бы вызов помощника, и связать его с очередью нечем — то
    есть опасный маршрут не попал бы в периметр и остался бы без удержания, не
    уронив ни одного теста.

    Отказ здесь — не запрет формы навсегда, а требование СНАЧАЛА научить обход:
    сегодня постановка задачи есть только в страничном слое, и расширение
    множества мест обязано быть осознанным, а не случившимся.
    """
    sources = _application_sources()
    routes = _routes({
        module: text
        for module, text in sources.items()
        if module.startswith(f"{PAGE_DIRECTORY}/")
    })

    offenders: list[str] = []
    for module, text in sources.items():
        spans = [
            (route.first_line, route.last_line)
            for route in routes.values()
            if route.module == module
        ]
        for node in ast.walk(ast.parse(text)):
            if not _is_queue_call(node):
                continue
            if not any(start <= node.lineno <= end for start, end in spans):
                offenders.append(f"{module}:{node.lineno}")

    assert not offenders, (
        "постановка задачи в очередь стоит ВНЕ тела обработчика маршрута:\n  "
        + "\n  ".join(sorted(offenders))
        + "\n\nОбход периметра такую постановку не видит, и маршрут, зовущий "
        "этого помощника, останется без удержания по умолчанию. Верни "
        "постановку в тело обработчика либо научи `_perimeter` этой форме "
        "прежде, чем ею пользоваться."
    )


def test_no_payment_creation_hides_behind_an_import_alias():
    """Создание платежа ввозится в страничный слой БЕЗ переименования.

    ⚠️ ГРАНИЦА 2 ДОКТРИНГА. Псевдоним импорта (`as`) переименовывает вызов, и
    обход по имени его не узнаёт: денежный маршрут не попал бы в периметр вовсе.
    Обращение через модуль при этом разрешено — переименования там нет, и
    `_is_payment_call` узнаёт его наравне с голым именем.
    """
    offenders: list[str] = []
    for module, text in _page_sources().items():
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, ast.ImportFrom):
                continue
            for alias in node.names:
                if alias.name != PAYMENT_CALL:
                    continue
                if alias.asname and alias.asname != alias.name:
                    offenders.append(f"{module}:{node.lineno} → {alias.asname}")

    assert not offenders, (
        f"`{PAYMENT_CALL}` ввозится под псевдонимом:\n  "
        + "\n  ".join(sorted(offenders))
        + "\n\nПод другим именем обход периметра вызова не узнаёт, и денежный "
        "маршрут окажется вне периметра."
    )


def test_the_gate_imports_no_application_module():
    """Гейт не импортирует НИ ОДНОГО модуля приложения ради построения ожиданий.

    ⚠️ ЭТО ЗАПРЕТ, А НЕ СТИЛЬ. Тест, выводящий ожидание из проверяемого,
    согласился бы с любой правкой: собери он перечни из самого приложения — и
    опасный маршрут, добавленный без решения, оказался бы «классифицированным» в
    тот же момент, как появился. Здесь исходники читаются КАК ТЕКСТ, а перечни
    выписаны руками, и именно поэтому расхождение видно.

    Второе следствие того же запрета: гейт не поднимает приложения и не
    открывает соединения — он остаётся исполнимым в дереве, которое собрать
    нельзя.
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


# =============================================================================
# КОНТРОЛИ: доказательство того, что гейт КРАСНЕЕТ (`-k control`)
#
# ⚠️ ЗАЧЕМ ОНИ, ЕСЛИ ВЫШЕ УЖЕ ДЕВЯТЬ ТЕСТОВ. Гейт, обходящий пять маршрутов и
# зелёный ПО ПОСТРОЕНИЮ, создаёт уверенность вместо проверки, и обнаруживается
# это в тот единственный день, когда он пропускает настоящее снятие удержания.
# Утверждения выше говорят «сегодня всё сходится»; контроли ниже говорят «а
# когда перестанет — я это увижу», и «а когда НЕ перестанет — не покраснею
# зря». Это три разных высказывания, и ни одно не следует из остальных.
#
# НИ ОДИН КОНТРОЛЬ НЕ ТРОГАЕТ ФАЙЛОВ ПРОЕКТА. Изменённый исходник пишется во
# ВРЕМЕННЫЙ файл (`tmp_path`) и оттуда подаётся разбору; боевое дерево читается
# только на чтение.
# =============================================================================


def _sources_with(tmp_path, sources: dict[str, str], module: str, text: str) -> dict[str, str]:
    """Копия поданных исходников, в которой ОДИН файл подменён — через файл.

    Подмена идёт по-настоящему через файловую систему, а не строкой в памяти:
    так контроль проверяет тот же путь чтения, которым гейт ходит по боевому
    дереву, и не может разойтись с ним из-за кодировки или переносов строк.
    """
    scratch = tmp_path / Path(module).name
    scratch.write_text(text, encoding="utf-8")

    changed = dict(sources)
    changed[module] = scratch.read_text(encoding="utf-8")
    return changed


def test_control_negative_an_unclassified_dangerous_route_reddens_the_gate(tmp_path):
    """ЧТО ДОКАЗЫВАЕТ: замыкающее утверждение ловит НОВЫЙ опасный маршрут.

    Это случай, РАДИ КОТОРОГО гейт и существует: маршрут, добавленный будущей
    фазой, о котором ни один перечень не знает. Со списком вместо обхода такой
    маршрут остался бы без удержания молча.
    """
    module = "app/pages/billing.py"
    sources = _page_sources()

    future_route = (
        '\n\n@router.post("/billing/a-route-some-future-phase-will-add")\n'
        "async def a_route_some_future_phase_will_add(queue):\n"
        '    queue.send_task("app.worker.tasks.whatever", args=[1])\n'
        "    return None\n"
    )
    changed = _sources_with(tmp_path, sources, module, sources[module] + future_route)

    assert (
        f"{module}::a_route_some_future_phase_will_add" in _unclassified(changed)
    ), (
        "ЗАМЫКАЮЩЕЕ УТВЕРЖДЕНИЕ НЕ ЗАМЕТИЛО НОВЫЙ ОПАСНЫЙ МАРШРУТ — периметр "
        "выродился в список, и маршрут будущей фазы останется без удержания"
    )
    assert len(_perimeter(changed)) == PERIMETER_ROUTES + 1, (
        "число маршрутов периметра не выросло — обход не увидел постановку "
        "задачи в новом обработчике"
    )


def test_control_negative_a_perimeter_route_without_its_hold_reddens_the_gate(tmp_path):
    """ЧТО ДОКАЗЫВАЕТ: гейт ловит СНЯТОЕ удержание маршрута рассылки.

    Самый частый способ потерять удержание — не удалить его, а обойти: условие
    правится при отладке и остаётся правленым. Тело обработчика при этом
    выглядит прежним, и упоминание удержания в файле никуда не девается —
    контроль доказывает, что гейт смотрит на ВЫЗОВ в теле, а не на наличие
    имени в тексте.
    """
    module = "app/pages/history.py"
    sources = _page_sources()

    stripped = sources[module].replace(f"if not {RETRY_HOLD}(log.id):", "if False:")
    assert stripped != sources[module], (
        "подмена ничего не изменила — контроль проверял бы неизменённый исходник"
    )
    assert RETRY_HOLD in stripped, (
        "из подменённого исходника исчезло и упоминание удержания: контроль "
        "перестал доказывать, что гейт смотрит на вызов, а не на текст"
    )

    changed = _sources_with(tmp_path, sources, module, stripped)
    missing = _named_hold_is_missing(changed)

    assert f"{module}::history_retry" in missing, (
        "ГЕЙТ НЕ ЗАМЕТИЛ СНЯТОЕ УДЕРЖАНИЕ на маршруте периметра — он зелёный по "
        "построению, и вторая необратимая отправка пройдёт мимо него"
    )
    assert RETRY_HOLD in missing[f"{module}::history_retry"], (
        "отказ не называет, ЧТО ИМЕННО не найдено — читатель отправлен искать "
        "по всему обработчику"
    )


def test_control_negative_a_queued_request_on_a_perimeter_form_reddens_the_gate(
    tmp_path,
):
    """ЧТО ДОКАЗЫВАЕТ: очередь запросов НА ПЕРИМЕТРЕ гейт видит.

    Форма повтора отправки получает стратегию очереди — то есть второе нажатие
    перестаёт отбрасываться и уходит вторым запросом после первого.
    """
    template = "app/templates/history/includes/history_card.html"
    templates = _template_sources()

    marked = templates[template].replace(
        'action="/history/{{ log_id }}/retry" data-retry',
        'action="/history/{{ log_id }}/retry" hx-sync="this:queue last" data-retry',
    )
    assert marked != templates[template], (
        "подмена ничего не изменила — форма повтора в шаблоне не найдена"
    )

    changed = _sources_with(tmp_path, templates, template, marked)
    offenders = _queued_perimeter_forms(_page_sources(), changed)

    assert any(offender.startswith(f"{template}::") for offender in offenders), (
        "ОЧЕРЕДЬ ЗАПРОСОВ НА ФОРМЕ МАРШРУТА ПЕРИМЕТРА ПРОШЛА МИМО ГЕЙТА — "
        "отложенная вторая отправка окажется разрешена по умолчанию"
    )


def test_control_positive_a_queued_request_outside_the_perimeter_keeps_the_gate_green(
    tmp_path,
):
    """ЧТО ДОКАЗЫВАЕТ: ГРАНИЦА ПРАВИЛА ПРОВЕДЕНА, а не объявлена.

    ⚠️ ЭТО ОТРИЦАТЕЛЬНЫЙ СЛУЧАЙ ГРАНИЦЫ, И БЕЗ НЕГО ПРЕДЫДУЩИЙ КОНТРОЛЬ
    ДОКАЗЫВАЛ БЫ ЛИШЬ ТО, ЧТО ГЕЙТ УМЕЕТ КРАСНЕТЬ. Очередь запросов вне
    периметра законна и используется осознанно; правило, срабатывающее и там,
    было бы не строже, а просто неверным — и сняли бы его первой же правкой
    вместе со свойством, которое оно держит.
    """
    template = "app/templates/billing/balance.html"
    templates = _template_sources()

    outside = templates[template] + (
        '\n<form method="post" action="/billing/a-form-outside-the-perimeter"\n'
        '      hx-post="/billing/a-form-outside-the-perimeter"\n'
        '      hx-sync="this:queue last"></form>\n'
    )
    changed = _sources_with(tmp_path, templates, template, outside)

    sources = _page_sources()

    assert _queued_perimeter_forms(sources, changed) == set(), (
        "ГЕЙТ ПОКРАСНЕЛ НА ОЧЕРЕДИ ВНЕ ПЕРИМЕТРА — правило проведено не по "
        "периметру, а по всей разметке, и форма редактора объявлений падёт "
        "следующей"
    )
    assert _opaque_queued_addresses(changed) == set(), (
        "адрес вне периметра признан непрозрачным — он собран из литералов "
        "целиком, и признавать его нечитаемым не за что"
    )


def test_control_positive_the_untouched_tree_keeps_the_gate_green():
    """ЧТО ДОКАЗЫВАЕТ: на НЕИЗМЕНЁННОМ дереве гейт молчит.

    ⚠️ БЕЗ ЭТОГО КОНТРОЛЯ ОТРИЦАТЕЛЬНЫЕ ВЫШЕ ПРОШЛИ БЫ И У ГЕЙТА, КОТОРЫЙ
    КРАСНЕЕТ ВСЕГДА. Гейт, роняющий сборку на любом дереве, не строже — он
    просто сломан, и его сняли бы первым же коммитом вместе со свойством.
    """
    sources = _page_sources()
    templates = _template_sources()

    assert _unclassified(sources) == set(), (
        "утверждение полноты краснеет на неизменённом дереве — отрицательные "
        "контроли выше ничего не доказывают"
    )
    assert _named_hold_is_missing(sources) == {}, (
        "проверка удержаний краснеет на неизменённом дереве"
    )
    assert _queued_perimeter_forms(sources, templates) == set(), (
        "запрет очереди краснеет на неизменённой разметке"
    )
    assert _opaque_queued_addresses(templates) == set(), (
        "запрет непрозрачного адреса краснеет на неизменённой разметке"
    )

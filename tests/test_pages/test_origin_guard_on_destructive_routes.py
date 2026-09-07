"""Гард происхождения на маршрутах ПОДТВЕРЖДЁННОГО УДАЛЕНИЯ данных пользователя.

ЗАЧЕМ ЭТОТ ФАЙЛ СУЩЕСТВУЕТ. Аутентификация проекта идёт cookie, поэтому браузер
прикладывает её к межсайтовой форме САМ, и изменяющий запрос со стороннего сайта
неотличим от своего. Ревизия Фазы 6 (`CR-02`) закрыла ровно эту асимметрию у
АДМИНИСТРАТИВНОГО удаления пользователя: соседний маршрут имперсонации нёс гард
с доводом «без него сторонняя страница выписала бы себе токен», а маршрут,
удаляющий того же пользователя целиком, не нёс ничего. Ревизия Фазы 10 (`WR-07`)
нашла ТУ ЖЕ асимметрию на этаж ниже: удаление аккаунта мессенджера, объявления,
расписания и группы аккаунта — необратимое удаление данных САМОГО пользователя —
серверного рубежа не имело, при том что обработчики правились этой же фазой, а в
трёх соседних местах проект явную серверную проверку требует.

ЧЕГО ЭТОТ МОДУЛЬ НЕ ДОКАЗЫВАЕТ. Он НЕ утверждает, что гард ЗАЩИЩАЕТ. Граница
защиты объявлена собственным докстрингом гарда (`app/pages/common.py`): запрос,
не приславший НИ ОДНОГО из двух заголовков, ПРОПУСКАЕТСЯ — в том числе тестовая
суита проекта, которая их не шлёт. Эта граница здесь не пересматривается и не
проверяется. Модуль утверждает ровно одно: гард СТОИТ на каждом маршруте
подтверждённого удаления, и пятый такой маршрут не сможет появиться без принятого
решения о гарде на нём.

ПОЧЕМУ ЗАМЕР, А НЕ ТРИ ТОЧЕЧНЫХ ТЕСТА. Точечные тесты закрепили бы сегодняшнее
состояние и промолчали бы о СЛЕДУЮЩЕМ добавленном маршруте — тот самый чёрный
список, от которого проект отказался явно при построении гейта запретов под
чужой личностью (D-23) и гейта полноты админки (`CR-02`). Форма взята оттуда
целиком: разбор ДЕРЕВА исходника (поиск строки считал бы вхождение в докстринге,
то есть объяснение роняло бы утверждение), замыкающее требование «каждый
найденный маршрут» и отрицательные контроли, доказывающие, что правила КРАСНЕЮТ.
"""
import ast
from pathlib import Path

PAGES_DIR = Path("app/pages")

ORIGIN_GUARD = "is_same_origin"

# Критерий маршрута ПОДТВЕРЖДЁННОГО УДАЛЕНИЯ: метод POST и путь, оканчивающийся
# на `/delete`. Метод `GET` сюда не входит намеренно: гард на чтении закрыл бы
# раздел межсайтовой ссылке впустую, а правило, отказывающее там, где нечего
# защищать, отключают ЦЕЛИКОМ вместе со свойством.
DESTRUCTIVE_METHODS = frozenset({"post"})
DESTRUCTIVE_PATH_SUFFIX = "/delete"


# =============================================================================
# Реестр маршрутов и объявленные числа
# =============================================================================

# Реестр собран ЧТЕНИЕМ дерева, а не памятью: «модуль страничного слоя → имена
# обработчиков подтверждённого удаления».
DESTRUCTIVE_ROUTE_HANDLERS: dict[str, frozenset[str]] = {
    "accounts.py": frozenset({"accounts_delete"}),
    "account_groups.py": frozenset({"account_groups_delete"}),
    "ads.py": frozenset({"ads_delete"}),
    "schedules.py": frozenset({"schedules_delete"}),
}

# ⚠️ СЧЁТ ЧИСЛОМ, А НЕ ДЛИНОЙ ПЕРЕЧНЯ САМОГО ПО СЕБЕ. Без объявленного числа
# утверждение «каждый найденный несёт гард» зеленело бы и на ПУСТОМ множестве
# найденных — например, если разбор декораторов перестанет их узнавать.
#
# ЛЕТОПИСЬ ЧИСЛА НАЙДЕННЫХ (по ВСЕМУ `app/pages/`, ДО изъятия):
#   0 → 5, Фаза 10, план 10-18, задача 2. Откуда взялось: замер
#   `grep -rn '@router.post(.*delete' app/pages/` от 2026-09-05, повторённый
#   исполнителем плана. Чем измерено: разбор `ast` по всему каталогу, критерий
#   «POST + путь на `/delete`». Найдено пять маршрутов в пяти модулях —
#   `accounts.py`, `account_groups.py`, `ads.py`, `schedules.py` и `admin.py`.
DESTRUCTIVE_ROUTES_FOUND_DECLARED = 5

# ЛЕТОПИСЬ ЧИСЛА В РЕЕСТРЕ (после изъятия по владению, см. ниже):
#   0 → 4, Фаза 10, план 10-18, задача 2. Пять найденных минус один модуль,
#   изъятый ПО ВЛАДЕНИЮ: административное удаление пользователя стережёт ЧУЖОЙ
#   гейт со СВОИМ объявленным числом. Маршрут, добавленный или снятый в
#   НЕизъятом модуле, обязан быть решением о гарде, а не правкой числа.
DESTRUCTIVE_ROUTES_DECLARED = 4


class OwnershipExemption:
    """Модуль, изъятый из реестра ПО ВЛАДЕНИЮ, и ссылка на его владельца.

    Изъятие есть ССЫЛКА НА ЧУЖОЕ ОБЕЩАНИЕ, и переживи она своё основание —
    маршрут необратимого удаления оказался бы не стережём НИКЕМ при двух зелёных
    гейтах. Поэтому здесь хранится не только имя владельца, но и всё, чем его
    живость можно проверить ЧТЕНИЕМ: файл гейта, имя правила и имя его константы
    числа.
    """

    def __init__(
        self,
        *,
        gate_source: Path,
        gate_test: str,
        gate_count_constant: str,
        reason: str,
    ) -> None:
        self.gate_source = gate_source
        self.gate_test = gate_test
        self.gate_count_constant = gate_count_constant
        self.reason = reason


# ⚠️ ДВОЙНОЕ ВЛАДЕНИЕ РАЗВЕДЕНО РЕШЕНИЕМ, А НЕ СОВПАДЕНИЕМ КРИТЕРИЕВ. Пятый
# найденный маршрут — `app/pages/admin.py`, POST `/users/{user_id}/delete` —
# попадает под критерий этого модуля ДОСЛОВНО, и гард на нём УЖЕ СТОИТ. Два
# правила над одним маршрутом означают ДВА объявленных числа, которые придётся
# не забыть править вместе, — а забытая половина выглядела бы работающей. Это
# ровно тот дефект, ради которого гард в своё время свели к ОДНОМУ источнику.
#
# ⚠️ ИЗЪЯТИЕ ПО МОДУЛЮ, А НЕ ПО ПУТИ МАРШРУТА. Админский гейт стережёт ВСЕ
# изменяющие маршруты своего модуля — шире, чем `/delete`, — и изъятие по модулю
# совпадает с его вселенной. Изъятие по одному пути оставило бы будущий второй
# `/delete` админки в двойном владении снова.
DESTRUCTIVE_ROUTE_OWNERSHIP_EXEMPTIONS: dict[str, OwnershipExemption] = {
    "admin.py": OwnershipExemption(
        gate_source=Path("tests/test_pages/test_admin_panel.py"),
        gate_test="test_every_mutating_admin_route_checks_the_origin",
        gate_count_constant="ADMIN_MUTATING_ROUTE_COUNT",
        reason=(
            "административное удаление пользователя стережёт гейт полноты "
            "админки со своим объявленным числом, заведённый ревизией Фазы 6 "
            "под именем CR-02; его вселенная — ВСЕ изменяющие маршруты модуля, "
            "то есть шире критерия этого файла"
        ),
    ),
}

# ЛЕТОПИСЬ ЧИСЛА ИЗЪЯТИЙ:
#   0 → 1, Фаза 10, план 10-18, задача 2: заведено единственное изъятие —
#   административный модуль. Молча выросшее число означает модуль, ушедший под
#   чужого владельца БЕЗ решения; молча похудевшее — маршрут, оставшийся без
#   владельца вовсе.
OWNERSHIP_EXEMPTIONS_DECLARED = 1


# =============================================================================
# Разборщики
# =============================================================================


def _declares_a_destructive_route(decorator: ast.AST) -> bool:
    """Объявляет ли декоратор POST-маршрут с путём, оканчивающимся на `/delete`.

    Узнаются ОБЕ формы, которыми фреймворк объявляет маршрут: именованный метод
    (`@любой_роутер.post("...")`) и общая (`@любой_роутер.api_route("...",
    methods=["POST"])`). Вторая от первой не отличается ничем, кроме видимости
    для наивного разборщика, — то есть маршрут, написанный ею, выпал бы из
    обхода МОЛЧА.

    ⚠️ ИМЯ ОБЪЕКТА РОУТЕРА НЕ ПРОВЕРЯЕТСЯ: роутер, заведённый будущей фазой,
    выпал бы из обхода по имени, а не по существу.
    """
    if not isinstance(decorator, ast.Call):
        return False
    func = decorator.func
    if not isinstance(func, ast.Attribute):
        return False

    if func.attr in DESTRUCTIVE_METHODS:
        pass
    elif func.attr == "api_route":
        methods = [
            keyword.value
            for keyword in decorator.keywords
            if keyword.arg == "methods"
        ]
        declared = {
            element.value.lower()
            for node in methods
            if isinstance(node, (ast.List, ast.Tuple, ast.Set))
            for element in node.elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        }
        if not declared & DESTRUCTIVE_METHODS:
            return False
    else:
        return False

    if not decorator.args:
        return False
    path = decorator.args[0]
    return (
        isinstance(path, ast.Constant)
        and isinstance(path.value, str)
        and path.value.endswith(DESTRUCTIVE_PATH_SUFFIX)
    )


def _delete_handlers(source: str) -> dict[str, ast.AST]:
    """Обработчики подтверждённого удаления в ОДНОМ исходнике — по дереву.

    Разбор ведётся `ast`, а не построчным поиском: построчный сломался бы от
    переноса декоратора на вторую строку, а хрупкое правило отключают вместе со
    свойством, которое оно стерегло.
    """
    found: dict[str, ast.AST] = {}
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(_declares_a_destructive_route(d) for d in node.decorator_list):
            found[node.name] = node
    return found


def destructive_route_handlers(module_name: str, source: str) -> dict[str, ast.AST]:
    """Обработчики удаления, принадлежащие ВСЕЛЕННОЙ ЭТОГО реестра.

    Модуль, изъятый по владению, из вселенной исключается: его маршруты стережёт
    чужой гейт, и второе правило над ними означало бы второе объявленное число.

    Исходник приходит ТЕКСТОМ, а имя модуля — отдельным параметром: без них
    отрицательный контроль был бы невыразим, а боевой файл пришлось бы править
    ради доказательства зубов.
    """
    if module_name in DESTRUCTIVE_ROUTE_OWNERSHIP_EXEMPTIONS:
        return {}
    return _delete_handlers(source)


def handlers_without_the_origin_guard(module_name: str, source: str) -> set[str]:
    """Маршруты удаления этого модуля, НЕ зовущие гард происхождения."""
    missing = set()
    for name, handler in destructive_route_handlers(module_name, source).items():
        calls = {
            call.func.id
            for call in ast.walk(handler)
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
        }
        if ORIGIN_GUARD not in calls:
            missing.add(name)
    return missing


def _pages_sources() -> dict[str, str]:
    """Пары «имя файла страничного слоя → ТЕКСТ исходника», весь каталог."""
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(PAGES_DIR.glob("*.py"))
    }


# =============================================================================
# Правила
# =============================================================================


def test_the_number_of_destructive_routes_is_declared():
    """Найденных маршрутов удаления ровно столько, сколько объявлено — И ИЗЪЯТИЙ ТОЖЕ.

    ⚠️ ЭТО НЕ ДУБЛИРОВАНИЕ СЛЕДУЮЩЕГО ПРАВИЛА, А ЕГО ОПОРА. «Каждый найденный
    несёт гард» — утверждение, истинное и для ПУСТОГО множества найденных:
    сломайся разбор декораторов или переименуйся каталог, и правило полноты
    зеленело бы навсегда, ничего не обходя.
    """
    sources = _pages_sources()

    assert len(sources) > 0, (
        f"в каталоге {PAGES_DIR} не разобрано ни одного модуля — обход зеленеет "
        "вакуумом, и правило полноты гарда ниже не проверяет ничего"
    )

    found = {
        f"{name}::{handler}"
        for name, source in sources.items()
        for handler in _delete_handlers(source)
    }
    assert len(found) > 0, (
        "по всему страничному слою не найдено НИ ОДНОГО маршрута "
        f"подтверждённого удаления (критерий: POST + путь на "
        f"`{DESTRUCTIVE_PATH_SUFFIX}`) — разбор декораторов перестал их узнавать"
    )

    assert len(found) == DESTRUCTIVE_ROUTES_FOUND_DECLARED, (
        f"маршрутов подтверждённого удаления найдено {len(found)}, объявлено "
        f"{DESTRUCTIVE_ROUTES_FOUND_DECLARED}: {sorted(found)}. Маршрут добавлен "
        "или снят — решение о гарде происхождения обязано быть принято ЯВНО, а "
        "число исправлено вместе с ним"
    )

    assert len(DESTRUCTIVE_ROUTE_OWNERSHIP_EXEMPTIONS) == OWNERSHIP_EXEMPTIONS_DECLARED, (
        f"модулей, изъятых по владению, {len(DESTRUCTIVE_ROUTE_OWNERSHIP_EXEMPTIONS)}, "
        f"объявлено {OWNERSHIP_EXEMPTIONS_DECLARED}: "
        f"{sorted(DESTRUCTIVE_ROUTE_OWNERSHIP_EXEMPTIONS)}. Изъятие выросло — "
        "второй модуль ушёл под ЧУЖОГО владельца, и это решение, а не правка "
        "числа; изъятие похудело — маршрут остался без владельца вовсе"
    )

    registry = {
        name: set(destructive_route_handlers(name, source))
        for name, source in sources.items()
    }
    in_registry = {
        f"{name}::{handler}"
        for name, handlers in registry.items()
        for handler in handlers
    }
    assert len(in_registry) == DESTRUCTIVE_ROUTES_DECLARED, (
        f"в реестре после изъятия {len(in_registry)} маршрутов, объявлено "
        f"{DESTRUCTIVE_ROUTES_DECLARED}: {sorted(in_registry)}"
    )

    declared = {
        f"{module}::{handler}"
        for module, handlers in DESTRUCTIVE_ROUTE_HANDLERS.items()
        for handler in handlers
    }
    assert in_registry == declared, (
        "реестр разошёлся с деревом. Найдено и не заявлено: "
        f"{sorted(in_registry - declared)}; заявлено и не найдено: "
        f"{sorted(declared - in_registry)}. Маршрут, не попавший ни в реестр, ни "
        "в объявленное изъятие, обязан получить решение о гарде ЯВНО"
    )


def test_every_destructive_route_checks_the_origin():
    """КАЖДЫЙ маршрут подтверждённого удаления сверяет источник запроса (WR-07).

    ⚠️ ПОЧЕМУ ЭТОГО НЕ ЗАМЕНЯЕТ `samesite="lax"`. Умолчание cookie межсайтовый
    POST действительно не пропускает — и ровно поэтому оно было ЕДИНСТВЕННЫМ,
    что стояло между сторонней страницей и необратимым удалением данных
    пользователя: одна политика браузера без единого рубежа за ней, там где
    проект в трёх соседних маршрутах требует явной серверной проверки. Правило
    продукта не имеет права зависеть от умолчания, которое продукт не выставляет
    и не проверяет.

    Прецедент назван прямо: ревизия Фазы 6 (`CR-02`) закрыла ТУ ЖЕ асимметрию у
    административного удаления пользователя. Здесь она закрыта, а не
    воспроизведена этажом ниже.
    """
    missing = {
        f"{name}: {handler}"
        for name, source in _pages_sources().items()
        for handler in handlers_without_the_origin_guard(name, source)
    }

    assert missing == set(), (
        "маршрут подтверждённого удаления не сверяет источник запроса: "
        + ", ".join(sorted(missing))
        + ". Аутентификация проекта идёт cookie — браузер приложит её к "
        "межсайтовой форме сам, и запрос со стороннего сайта неотличим от своего"
    )


def test_every_ownership_exemption_names_a_living_gate():
    """ИЗЪЯТИЕ НЕ ПЕРЕЖИВЁТ СВОЕГО ОСНОВАНИЯ.

    Изъятие по владению есть ссылка на ЧУЖОЕ обещание. Переименуй, снеси или
    перепиши чужой гейт — и маршрут необратимого удаления окажется не стережём
    НИКЕМ, при том что оба гейта останутся зелёными. Поэтому исходник названного
    владельца ЧИТАЕТСЯ, и имя правила вместе с именем его константы числа обязано
    в нём быть.

    ⚠️ ЧУЖОЙ МОДУЛЬ ЧИТАЕТСЯ, А НЕ ПРАВИТСЯ: это разбор каталога, как всякий
    другой в этом файле.
    """
    assert DESTRUCTIVE_ROUTE_OWNERSHIP_EXEMPTIONS, (
        "изъятий нет вовсе — правило зеленеет вакуумом; если изъятие снято, "
        "снимите и его, и это правило одним движением"
    )

    for module, exemption in sorted(DESTRUCTIVE_ROUTE_OWNERSHIP_EXEMPTIONS.items()):
        assert exemption.gate_source.exists(), (
            f"изъятие модуля {module} ссылается на гейт-владельца "
            f"{exemption.gate_source}, которого больше НЕТ: маршруты этого "
            "модуля не стережёт никто. Основание изъятия: " + exemption.reason
        )

        gate = exemption.gate_source.read_text(encoding="utf-8")

        assert f"def {exemption.gate_test}(" in gate, (
            f"изъятие модуля {module} ссылается на правило "
            f"{exemption.gate_test}, которого в {exemption.gate_source} больше "
            "НЕТ — изъятие потеряло основание. Верните правило либо внесите "
            "маршруты модуля в этот реестр вместе с числом"
        )

        assert exemption.gate_count_constant in gate, (
            f"изъятие модуля {module} ссылается на объявленное число "
            f"{exemption.gate_count_constant}, которого в "
            f"{exemption.gate_source} больше НЕТ: полнота у чужого владельца "
            "перестала стеречься числом, и правило-владелец зеленело бы на "
            "пустом множестве"
        )


# =============================================================================
# Контроли: у правил выше есть ЗУБЫ
# =============================================================================

# Боевые файлы НЕ ПРАВЯТСЯ ни одним контролем: подмена живёт строкой в памяти, и
# разборщику подаётся она. Приём и его основание взяты у
# `test_control_negative_a_mutating_admin_route_without_the_guard_reddens`.
_SYNTHETIC_ONE_UNGUARDED = '''
from fastapi import APIRouter, Request, Response

router = APIRouter()


@router.post("/widgets/{widget_id}/delete")
async def widgets_delete(request: Request):
    """Синтетический маршрут удаления БЕЗ гарда происхождения."""
    return Response(status_code=204)


@router.post("/widgets/{widget_id}/rename")
async def widgets_rename(request: Request):
    """Изменяющий, но НЕ удаляющий: под критерий не попадает."""
    if not is_same_origin(request):
        return Response(status_code=403)
    return Response(status_code=204)
'''

_SYNTHETIC_TWO_DESTRUCTIVE = '''
from fastapi import APIRouter, Request, Response

router = APIRouter()


@router.post("/widgets/{widget_id}/delete")
async def widgets_delete(request: Request):
    if not is_same_origin(request):
        return Response(status_code=403)
    return Response(status_code=204)


@router.post("/gadgets/{gadget_id}/delete")
async def gadgets_delete(request: Request):
    """ВТОРОЙ маршрут удаления, которого реестр не знает."""
    if not is_same_origin(request):
        return Response(status_code=403)
    return Response(status_code=204)
'''


def test_control_a_route_without_the_guard_is_named():
    """ЧТО ДОКАЗЫВАЕТ: правило полноты КРАСНЕЕТ на снятом гарде и называет ИМЯ.

    ⚠️ БЕЗ ЭТОГО КОНТРОЛЯ ПРАВИЛО БЫЛО БЫ ЗЕЛЕНО ПО ПОСТРОЕНИЮ, а обнаружилось бы
    это в тот единственный день, когда оно пропустит настоящий пропуск.
    """
    found = _delete_handlers(_SYNTHETIC_ONE_UNGUARDED)
    assert set(found) == {"widgets_delete"}, (
        "разборщик перестал отличать маршрут удаления от соседнего изменяющего: "
        f"найдено {sorted(found)}"
    )

    missing = handlers_without_the_origin_guard("widgets.py", _SYNTHETIC_ONE_UNGUARDED)

    assert missing == {"widgets_delete"}, (
        "ПРАВИЛО НЕ ЗАМЕТИЛО СНЯТОГО ГАРДА либо назвало не тот маршрут: "
        f"{sorted(missing)} — оно зелёное по построению, и настоящий пропуск "
        "сверки источника пройдёт мимо него"
    )


def test_control_an_undeclared_destructive_route_reddens_the_count():
    """ЧТО ДОКАЗЫВАЕТ: незаявленный маршрут удаления КРАСНИТ счёт.

    Реестр знает про синтетический модуль один маршрут, в исходнике их два — и
    расхождение обязано быть видно ЧИСЛОМ, а не остаться перечнем того, до чего
    дошли руки.
    """
    known = 1
    found = destructive_route_handlers("widgets.py", _SYNTHETIC_TWO_DESTRUCTIVE)

    assert len(found) == 2, (
        "разборщик не нашёл ОБА маршрута удаления синтетического исходника: "
        f"{sorted(found)} — контроль проверял бы дерево, в котором второго "
        "маршрута нет, и доказывал бы меньше, чем утверждает"
    )
    assert len(found) != known, (
        "счёт НЕ РАСХОДИТСЯ с объявленным при незаявленном маршруте — правило "
        "числа зелено по построению, и пятый маршрут удаления появится молча"
    )

    # И тот же исходник под ИЗЪЯТЫМ именем модуля исчезает из вселенной целиком:
    # изъятие по модулю, а не по пути маршрута.
    assert destructive_route_handlers("admin.py", _SYNTHETIC_TWO_DESTRUCTIVE) == {}, (
        "изъятие по владению перестало исключать модуль из вселенной реестра — "
        "маршруты админки попали бы под ДВА объявленных числа сразу"
    )

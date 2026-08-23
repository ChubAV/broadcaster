"""Машинный гейт ЗАПРЕТОВ ПОД ЧУЖОЙ ЛИЧНОСТЬЮ (D-22, D-23).

ПОЧЕМУ ГЕЙТ ЧИТАЕТ ИСХОДНИК, А НЕ СОБРАННОЕ ПРИЛОЖЕНИЕ. Довод тот же, что у
`tests/test_pages/test_access_gate.py`, и повторяется он потому, что тот же:
цель — поймать изменяющий маршрут, добавленный БУДУЩЕЙ фазой БЕЗ зависимости
запрета. В объекте приложения такой маршрут выглядит совершенно обычно — у него
просто нет одной зависимости, и отличить «забыли» от «не должно быть» там нечем.
В исходнике же решение записано явным вызовом, и множество вызовов замкнуто.

⚠️ ПОЧЕМУ ФОРМА ГИБРИДНАЯ — «РОУТЕР ЦЕЛИКОМ ПЛЮС ОТДЕЛЬНЫЕ МАРШРУТЫ», А НЕ
ЧИСТО ПЕР-РОУТЕРНАЯ, КАК У ГЕЙТА ДОСТУПА. Это установленный факт устройства
продукта, а не вкус. Повтор отправки живёт в роутере ИСТОРИИ, чтение которого
под чужой личностью не просто разрешено, а составляет смысл входа («не
отправляется» — типовое обращение). Смена пароля живёт в роутере АВТОРИЗАЦИИ,
который обязан оставаться открытым, иначе в продукт не сможет войти никто.
Закрыть эти роутеры целиком нельзя ни один, ни другой — значит перечень
отдельных маршрутов неизбежен. Там же, где запрещено ВСЁ (денежные изменяющие
входы), стоит роутер целиком: новый маршрут обязан оказаться закрытым ПО
УМОЛЧАНИЮ.

⚠️ ЧЕМ ЭТО ОТЛИЧАЕТСЯ ОТ ЧЁРНОГО СПИСКА — ОДНИМ УТВЕРЖДЕНИЕМ, И ОНО ЗДЕСЬ
ГЛАВНОЕ. `test_every_mutating_route_is_classified` требует, чтобы ОБЪЕДИНЕНИЕ
трёх объявленных множеств равнялось множеству НАЙДЕННЫХ изменяющих маршрутов.
Маршрут, добавленный будущей фазой, не попадёт ни в одно из них и уронит тест —
вместо того чтобы оказаться разрешённым по умолчанию. Ровно тот дефект, от
которого проект уже отказался явно при построении гейта доступа: денежный
маршрут, добавленный позже, оказался бы открыт, и обнаружилось бы это деньгами
или рассылкой, ушедшей от чужого имени.

⚠️ ТРИ МНОЖЕСТВА ВЫПИСАНЫ ЗДЕСЬ, А НЕ ВЫВЕДЕНЫ ИЗ ИСХОДНИКА. Тест, выводящий
ожидание из проверяемого, согласился бы с любой правкой — довод записан в
проекте дословно и повторяется. По той же причине этот файл НЕ ИМПОРТИРУЕТ НИ
ОДНОГО модуля приложения: он читает их как текст. Свойство закреплено
`test_the_gate_imports_no_application_module`.

ЗУБЫ ГЕЙТА ДОКАЗАНЫ, А НЕ ЗАЯВЛЕНЫ. Три контроля в конце файла (`-k control`)
подают разборщику изменённые копии исходника и утверждают, что гейт краснеет на
снятой зависимости и на необъявленном маршруте и зеленеет на настоящем дереве.
Тест, обходящий сорок девять маршрутов и зелёный ПО ПОСТРОЕНИЮ, создавал бы
уверенность вместо проверки, и обнаружилось бы это в тот день, когда он
пропустит настоящий пропуск зависимости.
"""
import ast
from dataclasses import dataclass
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Слои, в которых живут маршруты. Каталоги обходятся ЦЕЛИКОМ, а не перечнем
# файлов: модуль, добавленный будущей фазой, обязан попасть в обход сам, иначе
# гейт молча перестал бы видеть целый слой.
ROUTE_DIRECTORIES = ("app/pages", "app/routes")

# Сборки, в которых роутеры включаются в приложение. Их две, и обе читаются
# одним помощником — вторая копия разбора разошлась бы с первой ровно на той
# поверхности, про которую забыли.
ASSEMBLIES = ("app/main.py", "app/pages/__init__.py")

MUTATING_METHODS = frozenset({"post", "put", "patch", "delete"})

DEPENDENCY = "forbid_when_impersonating"

# ⚠️ ЧИСЛО ИЗМЕНЯЮЩИХ МАРШРУТОВ ВЫПИСАНО ОТДЕЛЬНЫМ УТВЕРЖДЕНИЕМ НАМЕРЕННО. Оно
# будет меняться, и каждое его изменение обязано быть ОСОЗНАННЫМ: беззвучно
# выросшее число означает, что маршрут появился, а решения о нём никто не
# принимал. Перечни ниже поймали бы это и сами, но по числу видно СРАЗУ, что
# именно произошло.
MUTATING_ROUTE_COUNT = 49

# Столько модулей обоих слоёв объявляют изменяющие маршруты.
MUTATING_MODULE_COUNT = 15


# =============================================================================
# Множество 1: РОУТЕРЫ, ЗАПРЕЩЁННЫЕ ЦЕЛИКОМ
# =============================================================================

# Там, где под чужой личностью запрещено ВСЁ изменяющее, запрет висит на
# РОУТЕРЕ. Это единственная форма, при которой маршрут, добавленный будущей
# фазой, оказывается закрыт, НЕ СДЕЛАВ НИЧЕГО, — а для денежного пути ошибаться
# полагается именно в эту сторону.
FORBIDDEN_ROUTERS = {
    "app/pages/billing.py::money_router": (
        "страничные ДЕНЕЖНЫЕ изменяющие входы; чтение раздела осталось в "
        "соседнем роутере и под чужой личностью открыто — «я заплатил, а "
        "доступ не открылся» есть типовое обращение"
    ),
    "app/routes/billing.py::router": (
        "JSON-денежный роутер целиком; единственный его вход сегодня — вебхук "
        "ЮKassa, и он токена не несёт, поэтому зависимостью не задет (D-53)"
    ),
}


# =============================================================================
# Множество 2: МАРШРУТЫ, ЗАПРЕЩЁННЫЕ ПОИМЁННО
# =============================================================================

# Роутер целиком здесь закрыть НЕЛЬЗЯ, и у каждого случая своя причина — она и
# записана. Перечень, у которого не написано, почему кто-то в него входит, через
# фазу превращается в «наверное, так надо».
FORBIDDEN_ROUTES = {
    "app/pages/auth.py::forgot_password_send_code": (
        "смена пароля, шаг 1: код уходит НА ПОЧТУ ПОЛЬЗОВАТЕЛЯ — письмо, "
        "которого он не просил, и начало захвата учётной записи (D-22)"
    ),
    "app/pages/auth.py::forgot_password_verify": (
        "смена пароля, шаг 2 (D-22)"
    ),
    "app/pages/auth.py::forgot_password_resend_code": (
        "смена пароля, шаг 3 (D-22)"
    ),
    "app/pages/auth.py::forgot_password_reset": (
        "смена пароля, шаг 4 — запись нового хэша: администратор получил бы "
        "постоянный доступ к учётной записи пользователя (D-22)"
    ),
    "app/pages/profile.py::profile_post": (
        "правка учётных данных; закрыта ЦЕЛИКОМ на вырост — отдельного "
        "маршрута смены адреса сегодня нет, и когда его заведут, естественное "
        "место ему здесь, а поле в уже разрешённом маршруте гейт не заметил бы"
    ),
    "app/pages/history.py::history_retry": (
        "повтор ОТПРАВКИ: сообщение уходит в группы пользователя от его имени "
        "и необратимо; чтение той же истории разрешено и составляет смысл "
        "входа под пользователем (D-22)"
    ),
    "app/pages/admin.py::admin_toggle_free_access": (
        "выдача бесплатного доступа — ДЕНЬГИ, а весь денежный путь под чужой "
        "личностью запрещён (D-22); администратору достаточно сперва вернуться"
    ),
    "app/pages/admin.py::admin_impersonate": (
        "вложенный вход: цепочку личностей формат токена допускает, а продукт "
        "не поддерживает — полоса возврата назвала бы одного пользователя, "
        "возврат привёл бы к другому"
    ),
    "app/pages/admin.py::admin_delete_user": (
        "удаление учётной записи НЕОБРАТИМО — откатом кода пользователь не "
        "возвращается (D-22)"
    ),
}


# =============================================================================
# Множество 3: МАРШРУТЫ, РАЗРЕШЁННЫЕ ПОД ЧУЖОЙ ЛИЧНОСТЬЮ
# =============================================================================

# ⚠️ ПЕРЕЧЕНЬ РАЗРЕШЁННОГО ОБЪЯВЛЕН, А НЕ ВЫВЕДЕН ИЗ ОТСУТСТВИЯ ЗАПРЕТА, И ЭТО
# СУТЬ ФОРМЫ. «Разрешено всё, что не запрещено» — и есть чёрный список, от
# которого D-23 отказывается: новый маршрут попал бы сюда молча. Здесь у каждого
# элемента написано, ПОЧЕМУ он разрешён, и добавление нового требует написать
# причину — то есть принять решение.
#
# Режим «только чтение» отвергнут явно: смысл входа под пользователем — в
# ВОСПРОИЗВЕДЕНИИ проблемы, а типовые проблемы продукта суть «не отправляется» и
# «не синхронизируются группы» (D-22).
ALLOWED_ROUTES = {
    # ---- вход, регистрация и возврат: роутер авторизации обязан работать ----
    "app/pages/auth.py::login_submit": "вход в продукт; закрыть — запереть всех",
    "app/pages/auth.py::register_send_code": "регистрация НОВОЙ учётной записи, чужой не касается",
    "app/pages/auth.py::register_verify": "регистрация новой учётной записи",
    "app/pages/auth.py::register_resend_code": "регистрация новой учётной записи",
    "app/pages/auth.py::register_complete": "регистрация новой учётной записи",
    "app/pages/auth.py::stop_impersonation": (
        "ВОЗВРАТ из-под чужой личности — единственный путь назад; закрыть его "
        "значило бы запереть администратора в чужой учётной записи навсегда"
    ),
    "app/routes/auth.py::register": "JSON-регистрация новой учётной записи",
    "app/routes/auth.py::login": "JSON-вход в продукт",
    # ---- синхронизация и подключение: ради этого под пользователя и входят ----
    "app/pages/accounts.py::accounts_connect_tg_user_start_qr": "подключение аккаунта — воспроизведение жалобы «не подключается»",
    "app/pages/accounts.py::accounts_connect_tg_user_refresh_qr": "подключение аккаунта",
    "app/pages/accounts.py::accounts_connect_tg_user_verify_2fa": "подключение аккаунта",
    "app/pages/accounts.py::accounts_connect_tg_user_complete": "подключение аккаунта",
    "app/pages/accounts.py::accounts_connect_max_start": "подключение аккаунта",
    "app/pages/accounts.py::accounts_retry_sync": "повтор СИНХРОНИЗАЦИИ — разрешена поимённо (D-22)",
    "app/pages/accounts.py::accounts_sync_groups": "СИНХРОНИЗАЦИЯ ГРУПП — разрешена поимённо (D-22)",
    "app/pages/accounts.py::accounts_delete": (
        "отключение аккаунта мессенджера обратимо повторным подключением; "
        "учётной записи пользователя не касается"
    ),
    "app/routes/accounts.py::create_account": "JSON-сторона подключения аккаунта",
    "app/routes/accounts.py::delete_account": "JSON-сторона отключения аккаунта, обратимо",
    # ---- включение/выключение и правка объявлений: разрешены решением ----
    "app/pages/account_groups.py::account_groups_toggle": "ВКЛЮЧЕНИЕ/ВЫКЛЮЧЕНИЕ группы — разрешено поимённо (D-22)",
    "app/pages/account_groups.py::account_groups_delete": "удаление группы из списка возвращается синхронизацией",
    "app/pages/ads.py::ads_create": "правка объявления; ничего не отправляет и денег не трогает",
    "app/pages/ads.py::ads_update": "правка объявления",
    "app/pages/ads.py::ads_delete": "правка объявления",
    "app/routes/ads.py::create_ad": "JSON-сторона правки объявления",
    "app/routes/ads.py::update_ad": "JSON-сторона правки объявления",
    "app/routes/ads.py::delete_ad": "JSON-сторона правки объявления",
    "app/routes/uploads.py::upload_image": "загрузка картинки объявления",
    # ---- расписания: НАМЕРЕНИЕ отправить, обратимое до срабатывания ----
    #
    # ⚠️ ГРАНИЦА ЗДЕСЬ ТОНКАЯ И ПОТОМУ ВЫПИСАНА. Расписание в конце концов
    # приводит к отправке, но само по себе её не производит: оно обратимо
    # выключением и удалением ровно до того момента, как сработает планировщик, —
    # а «включение/выключение» D-22 называет разрешённым прямо. НЕОБРАТИМЫЙ
    # немедленный запуск отправки в продукте один, и он запрещён
    # (`history_retry`). Появись маршрут «отправить сейчас» — он не попадёт ни в
    # одно множество и уронит гейт, что и требуется.
    "app/pages/schedules.py::schedules_create": "заведение расписания — намерение, обратимое до срабатывания",
    "app/pages/schedules.py::schedules_update": "правка расписания, обратима",
    "app/pages/schedules.py::schedules_toggle": "ВКЛЮЧЕНИЕ/ВЫКЛЮЧЕНИЕ расписания — разрешено поимённо (D-22)",
    "app/pages/schedules.py::schedules_delete": "снятие расписания, отправку останавливает",
    "app/routes/schedules.py::create_schedule": "JSON-сторона заведения расписания",
    "app/routes/schedules.py::update_schedule": "JSON-сторона правки расписания",
    "app/routes/schedules.py::delete_schedule": "JSON-сторона снятия расписания",
    "app/routes/schedules.py::toggle_schedule": "JSON-сторона включения/выключения расписания",
    # ---- административные операции ДЕЙСТВУЮЩЕГО ЛИЦА ----
    #
    # Права администратора читаются по действующему лицу (D-20), поэтому админка
    # из-под имперсонации работает, и журнал записывает эти операции под
    # идентификатором АКТОРА, а не под чужим. Все три обратимы.
    "app/pages/admin.py::admin_restart_worker": "перезапуск воркера — операция актора, обратима",
    "app/pages/admin.py::admin_drop_task": "снятие задачи из очереди — операция актора",
    "app/pages/admin.py::admin_toggle_block": "блокировка обратима снятием блокировки",
}


# =============================================================================
# Разбор исходника
# =============================================================================


@dataclass(frozen=True)
class _Route:
    """Одно изменяющее объявление маршрута."""

    module: str
    router: str
    handler: str
    carries_dependency: bool

    @property
    def key(self) -> str:
        return f"{self.module}::{self.handler}"

    @property
    def router_key(self) -> str:
        return f"{self.module}::{self.router}"


def _project_sources() -> dict[str, str]:
    """Относительный путь → ТЕКСТ исходника по обоим слоям и обеим сборкам.

    Возвращается словарь, а не пути, ровно затем, чтобы контроли в конце файла
    могли подать разборщику ИЗМЕНЁННУЮ копию, не трогая ни одного боевого файла.
    """
    sources: dict[str, str] = {}
    for directory in ROUTE_DIRECTORIES:
        for path in sorted((PROJECT_ROOT / directory).glob("*.py")):
            sources[str(path.relative_to(PROJECT_ROOT))] = path.read_text(
                encoding="utf-8"
            )
    for assembly in ASSEMBLIES:
        path = PROJECT_ROOT / assembly
        sources[assembly] = path.read_text(encoding="utf-8")
    return sources


def _mentions_dependency(node: ast.AST) -> bool:
    """Упоминается ли зависимость запрета в этом узле дерева.

    Проверяются ОБА написания: голое имя (`forbid_when_impersonating`) и
    обращение через модуль (`app_dependencies.forbid_when_impersonating`).
    Второе живёт в `app/pages/history.py` намеренно — там закрыт ровно один
    маршрут из двух, и импорт по имени сделал бы это свойство непроверяемым
    поиском по файлу.
    """
    for element in ast.walk(node):
        if isinstance(element, ast.Name) and element.id == DEPENDENCY:
            return True
        if isinstance(element, ast.Attribute) and element.attr == DEPENDENCY:
            return True
    return False


def _declares_dependency(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Несёт ли ОБЪЯВЛЕНИЕ обработчика зависимость запрета.

    ⚠️ ОБХОДИТСЯ НЕ ВСЯ ФУНКЦИЯ, А ТОЛЬКО ЕЁ ОБЪЯВЛЕНИЕ: умолчания параметров и
    аргумент `dependencies=` декоратора. Обход тела посчитал бы упоминание в
    докстринге или комментарии — то есть зеленел бы на маршруте, где про запрет
    только НАПИСАНО.
    """
    defaults = [
        default
        for default in (*function.args.defaults, *function.args.kw_defaults)
        if default is not None
    ]
    if any(_mentions_dependency(default) for default in defaults):
        return True

    for decorator in function.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        for keyword in decorator.keywords:
            if keyword.arg == "dependencies" and _mentions_dependency(keyword.value):
                return True
    return False


def _mutating_routes(sources: dict[str, str]) -> dict[str, _Route]:
    """Каждое ИЗМЕНЯЮЩЕЕ объявление маршрута во всех поданных исходниках.

    Изменяющим считается объявление, украшенное `@<роутер>.<метод>(...)` с
    методом из `MUTATING_METHODS`. Разбор по дереву, а не грепом: греп по
    `@router.post` посчитал бы строку и в комментарии, и в докстринге, и в
    закомментированном коде.
    """
    routes: dict[str, _Route] = {}

    for module, text in sources.items():
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                func = decorator.func
                if not isinstance(func, ast.Attribute):
                    continue
                if func.attr not in MUTATING_METHODS:
                    continue
                if not isinstance(func.value, ast.Name):
                    continue

                route = _Route(
                    module=module,
                    router=func.value.id,
                    handler=node.name,
                    carries_dependency=_declares_dependency(node),
                )
                routes[route.key] = route

    return routes


def _router_origins(tree: ast.Module, assembly: str) -> dict[str, str]:
    """Локальное имя роутера в сборке → `модуль::атрибут`, откуда он привезён.

    Без этой карты «роутер закрыт целиком» нельзя связать с маршрутами: в
    сборке видно имя `billing_money_router`, а в объявлениях маршрутов —
    `money_router` в файле `app/pages/billing.py`. Один модуль при этом может
    держать ДВА роутера (`router` для чтения и `money_router` для денег), и
    сопоставление по одному лишь модулю склеило бы их в одно решение.
    """
    origins: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module is None:
            continue
        if not node.module.startswith("app."):
            continue
        module_path = node.module.replace(".", "/") + ".py"
        if module_path not in _MODULE_PATHS and f"{node.module.replace('.', '/')}/__init__.py" in _MODULE_PATHS:
            module_path = f"{node.module.replace('.', '/')}/__init__.py"
        for alias in node.names:
            local = alias.asname or alias.name
            origins[local] = f"{module_path}::{alias.name}"
    # Сборка страниц включает роутеры, объявленные в ней же (`router`).
    origins.setdefault("router", f"{assembly}::router")
    return origins


def _routers_closed_wholesale(sources: dict[str, str]) -> dict[str, str]:
    """`модуль::роутер` → сборка, в которой на него навешен запрет ЦЕЛИКОМ.

    Форма разбора навесок взята у `tests/test_pages/test_access_gate.py`
    целиком: вопрос ровно один — с какими аргументами позван `include_router`.
    """
    closed: dict[str, str] = {}

    for assembly in ASSEMBLIES:
        tree = ast.parse(sources[assembly])
        origins = _router_origins(tree, assembly)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute) or func.attr != "include_router":
                continue
            if not node.args or not isinstance(node.args[0], ast.Name):
                continue

            local = node.args[0].id
            for keyword in node.keywords:
                if keyword.arg != "dependencies":
                    continue
                if _mentions_dependency(keyword.value):
                    closed[origins.get(local, f"?::{local}")] = assembly

    return closed


_MODULE_PATHS = frozenset(
    [
        *(
            str(path.relative_to(PROJECT_ROOT))
            for directory in ROUTE_DIRECTORIES
            for path in (PROJECT_ROOT / directory).glob("*.py")
        ),
        *ASSEMBLIES,
    ]
)


# =============================================================================
# Проверки, которыми пользуются и основные тесты, и контроли
# =============================================================================


def _unclassified(sources: dict[str, str]) -> set[str]:
    """Изменяющие маршруты, не попавшие НИ В ОДНО из трёх множеств.

    Это и есть предмет главного утверждения файла: непустой результат означает,
    что маршрут существует, а решения «запрещён ли он под чужой личностью»
    никто не принимал.
    """
    routes = _mutating_routes(sources)
    closed_routers = set(_routers_closed_wholesale(sources))

    return {
        key
        for key, route in routes.items()
        if route.router_key not in closed_routers
        and key not in FORBIDDEN_ROUTES
        and key not in ALLOWED_ROUTES
    }


def _prohibitions_not_declared(sources: dict[str, str]) -> set[str]:
    """Маршруты из перечня запрещённых, чьё ОБЪЯВЛЕНИЕ зависимости не несёт.

    Утверждение снимается по дереву, а не по строке: маршрут, у которого про
    запрет написано в докстринге, зависимости не несёт.
    """
    routes = _mutating_routes(sources)

    missing = set()
    for key in FORBIDDEN_ROUTES:
        route = routes.get(key)
        if route is None or not route.carries_dependency:
            missing.add(key)
    return missing


# =============================================================================
# Гейт
# =============================================================================


def test_the_number_of_mutating_routes_is_the_declared_one():
    """Число изменяющих маршрутов и модулей равно выписанному.

    ⚠️ БЕЗЗВУЧНО ВЫРОСШЕЕ ЧИСЛО ОЗНАЧАЕТ, ЧТО МАРШРУТ ПОЯВИЛСЯ, А РЕШЕНИЯ О НЁМ
    НИКТО НЕ ПРИНИМАЛ. Перечни ниже поймали бы это и сами, но по числу видно
    СРАЗУ, что именно произошло, — и правка числа обязана быть осознанной.
    """
    routes = _mutating_routes(_project_sources())
    modules = {route.module for route in routes.values()}

    assert len(routes) == MUTATING_ROUTE_COUNT, (
        f"изменяющих маршрутов стало {len(routes)}, а выписано "
        f"{MUTATING_ROUTE_COUNT}: маршрут появился или исчез — обнови число "
        f"вместе с решением о нём"
    )
    assert len(modules) == MUTATING_MODULE_COUNT, (
        f"модулей с изменяющими маршрутами стало {len(modules)}, а выписано "
        f"{MUTATING_MODULE_COUNT}"
    )


def test_every_mutating_route_is_classified():
    """ЗАМЫКАЮЩЕЕ УТВЕРЖДЕНИЕ: объединение трёх множеств равно найденному.

    ⚠️ ИМЕННО ЭТО УТВЕРЖДЕНИЕ ОТЛИЧАЕТ ФОРМУ ОТ ЧЁРНОГО СПИСКА, И БЕЗ НЕГО ВЕСЬ
    ФАЙЛ БЕССМЫСЛЕН. Маршрут, добавленный будущей фазой, не попадёт ни в одно из
    трёх множеств и уронит тест — вместо того чтобы оказаться разрешённым ПО
    УМОЛЧАНИЮ и уйти на бой незамеченным.
    """
    unclassified = _unclassified(_project_sources())

    assert not unclassified, (
        "в проекте есть изменяющие маршруты, о которых этот гейт не знает:\n  "
        + "\n  ".join(sorted(unclassified))
        + "\n\nЧТО ДЕЛАТЬ. Реши, разрешён ли маршрут под ЧУЖОЙ учётной записью "
        "(D-22: запрещены деньги, смена пароля и адреса, удаление учётной "
        "записи, отправка и повтор рассылки), и внеси его В ОДНО из трёх "
        "множеств этого файла: FORBIDDEN_ROUTERS (роутер целиком), "
        "FORBIDDEN_ROUTES (поимённо, с навеской зависимости на объявлении) или "
        "ALLOWED_ROUTES (с ПРИЧИНОЙ, почему разрешён). Молча удалять это "
        "утверждение нельзя: оно и есть запрет чёрного списка (D-23)."
    )


def test_every_forbidden_route_declares_the_dependency():
    """Каждый запрещённый ПОИМЁННО маршрут несёт зависимость в объявлении.

    ⚠️ УТВЕРЖДЕНИЕ ПО ДЕРЕВУ, А НЕ ПО СТРОКЕ. Маршрут, у которого про запрет
    только написано в докстринге, выглядит закрытым при чтении глазами и открыт
    на самом деле — ровно тот случай, ради которого гейт читает объявление, а не
    файл целиком.
    """
    missing = _prohibitions_not_declared(_project_sources())

    assert not missing, (
        "маршрут объявлен запрещённым, но зависимости запрета не несёт:\n  "
        + "\n  ".join(sorted(missing))
        + f"\n\nЧТО ДЕЛАТЬ. Добавь в объявление обработчика параметр "
        f"`_under_another_identity: None = Depends({DEPENDENCY})` — либо сними "
        f"маршрут из FORBIDDEN_ROUTES, если решение о нём изменилось."
    )


def test_every_forbidden_router_carries_the_dependency_in_the_assembly():
    """Каждый роутер, объявленный запрещённым целиком, закрыт в сборке."""
    closed = _routers_closed_wholesale(_project_sources())

    assert set(FORBIDDEN_ROUTERS) == set(closed), (
        f"перечень роутеров, закрытых ЦЕЛИКОМ, разошёлся с объявленным: "
        f"лишние {set(closed) - set(FORBIDDEN_ROUTERS)}, "
        f"недостающие {set(FORBIDDEN_ROUTERS) - set(closed)}"
    )


def test_no_allowed_route_carries_the_dependency():
    """Ни один разрешённый маршрут зависимости запрета НЕ несёт.

    ⚠️ БЕЗ ЭТОГО УТВЕРЖДЕНИЯ РАЗРЕШЕНИЕ МОЛЧА ПЕРЕСТАЛО БЫ ДЕЙСТВОВАТЬ.
    Зависимость, поставленная на разрешённый маршрут «на всякий случай», закрыла
    бы синхронизацию групп или возврат из имперсонации — и первые два множества
    остались бы зелёными, потому что они про запрещённое.
    """
    routes = _mutating_routes(_project_sources())
    closed_routers = set(_routers_closed_wholesale(_project_sources()))

    wrongly_closed = {
        key
        for key in ALLOWED_ROUTES
        if key in routes
        and (routes[key].carries_dependency or routes[key].router_key in closed_routers)
    }

    assert not wrongly_closed, (
        "маршрут объявлен РАЗРЕШЁННЫМ под чужой личностью, но закрыт "
        "запретом:\n  " + "\n  ".join(sorted(wrongly_closed))
    )


def test_the_three_sets_do_not_overlap():
    """Множества не пересекаются: у каждого маршрута ОДНО решение.

    Маршрут, попавший в два множества сразу, означает два ответа на один вопрос,
    и какой из них исполняется — зависело бы от порядка проверок.
    """
    forbidden = set(FORBIDDEN_ROUTES)
    allowed = set(ALLOWED_ROUTES)

    assert not (forbidden & allowed), (
        f"маршрут объявлен и запрещённым, и разрешённым: {forbidden & allowed}"
    )

    routes = _mutating_routes(_project_sources())
    closed_routers = set(FORBIDDEN_ROUTERS)
    by_router = {
        key for key, route in routes.items() if route.router_key in closed_routers
    }

    assert not (by_router & forbidden), (
        f"маршрут закрыт и роутером, и поимённо: {by_router & forbidden}"
    )
    assert not (by_router & allowed), (
        f"маршрут закрыт роутером, но объявлен разрешённым: {by_router & allowed}"
    )


def test_every_allowed_route_carries_a_reason():
    """У каждого разрешённого маршрута написана ПРИЧИНА, а не пустая строка.

    Перечень, у которого не написано, почему кто-то в него входит, через фазу
    превращается в «наверное, забыли», и следующая фаза читает его как список
    без основания.
    """
    unexplained = {
        key for key, reason in ALLOWED_ROUTES.items() if not reason.strip()
    }

    assert not unexplained, (
        "разрешённый маршрут не снабжён причиной:\n  "
        + "\n  ".join(sorted(unexplained))
    )


def test_the_gate_imports_no_application_module():
    """Гейт не импортирует НИ ОДНОГО модуля приложения ради построения ожиданий.

    ⚠️ ЭТО ЗАПРЕТ, А НЕ СТИЛЬ. Тест, выводящий ожидание из проверяемого,
    согласился бы с любой правкой: собери он три множества из самого приложения
    — и маршрут, добавленный без решения, оказался бы «объявленным» в тот же
    момент, как появился. Здесь исходники читаются КАК ТЕКСТ, а перечни выписаны
    руками, и именно поэтому расхождение видно.
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
# ⚠️ ЗАЧЕМ ОНИ, ЕСЛИ ВЫШЕ УЖЕ ВОСЕМЬ ТЕСТОВ. Тест, обходящий сорок девять
# маршрутов и зелёный ПО ПОСТРОЕНИЮ, создаёт уверенность вместо проверки, и
# обнаруживается это в тот единственный день, когда он пропускает настоящий
# пропуск зависимости. Восемь утверждений выше говорят «сегодня всё сходится»;
# три контроля ниже говорят «а когда перестанет — я это увижу». Это разные
# высказывания, и второе не следует из первого.
#
# НИ ОДИН КОНТРОЛЬ НЕ ТРОГАЕТ ФАЙЛОВ ПРОЕКТА. Изменённый исходник пишется во
# ВРЕМЕННЫЙ файл (`tmp_path`) и оттуда подаётся разборщику; боевое дерево
# читается только на чтение.
# =============================================================================


def _sources_with(tmp_path, module: str, text: str) -> dict[str, str]:
    """Копия исходников проекта, в которой ОДИН модуль подменён — через файл.

    Подмена идёт по-настоящему через файловую систему, а не строкой в памяти:
    так контроль проверяет тот же путь чтения, которым гейт ходит по боевому
    дереву, и не может разойтись с ним из-за кодировки или переносов строк.
    """
    scratch = tmp_path / Path(module).name
    scratch.write_text(text, encoding="utf-8")

    sources = _project_sources()
    sources[module] = scratch.read_text(encoding="utf-8")
    return sources


def test_control_negative_a_forbidden_route_without_the_dependency_reddens_gate(
    tmp_path,
):
    """ЧТО ДОКАЗЫВАЕТ: гейт ловит СНЯТУЮ зависимость у запрещённого маршрута.

    Это первый из двух отрицательных контролей, и он про самый частый способ
    потерять запрет: параметр обработчика убрали при правке сигнатуры, а всё
    остальное осталось на месте.

    ⚠️ ИМПОРТ ЗАВИСИМОСТИ В ПОДМЕНЁННОМ ИСХОДНИКЕ НАМЕРЕННО ОСТАВЛЕН. Именно так
    и выглядит настоящая потеря: строка `from app.dependencies import
    forbid_when_impersonating, ...` переживает удаление параметра, файл
    продолжает УПОМИНАТЬ запрет, и поиск по тексту нашёл бы его. Контроль
    доказывает, что гейт смотрит на ОБЪЯВЛЕНИЕ обработчика, а не на наличие
    имени в файле, — иначе он зеленел бы на брошенном импорте.
    """
    module = "app/pages/profile.py"
    original = _project_sources()[module]

    stripped = "\n".join(
        line for line in original.splitlines() if f"Depends({DEPENDENCY})" not in line
    )
    assert stripped != original, (
        "подмена ничего не удалила — контроль проверял бы неизменённый исходник"
    )
    assert DEPENDENCY in stripped, (
        "из подменённого исходника исчезло и упоминание запрета: контроль "
        "перестал доказывать, что гейт смотрит на объявление, а не на текст"
    )

    sources = _sources_with(tmp_path, module, stripped)

    missing = _prohibitions_not_declared(sources)

    assert f"{module}::profile_post" in missing, (
        "ГЕЙТ НЕ ЗАМЕТИЛ СНЯТУЮ ЗАВИСИМОСТЬ у запрещённого маршрута — он "
        "зелёный по построению, и настоящий пропуск запрета пройдёт мимо него"
    )


def test_control_negative_an_undeclared_new_route_reddens_the_completeness(
    tmp_path,
):
    """ЧТО ДОКАЗЫВАЕТ: замыкающее утверждение полноты ловит НОВЫЙ маршрут.

    Это второй отрицательный контроль, и он про случай, РАДИ КОТОРОГО гейт и
    существует: маршрут, добавленный будущей фазой, о котором ни одно из трёх
    множеств не знает. При чёрном списке такой маршрут оказался бы разрешён ПО
    УМОЛЧАНИЮ и уехал бы на бой незамеченным — деньгами или рассылкой, ушедшей
    от чужого имени (D-23).
    """
    module = "app/pages/profile.py"
    original = _project_sources()[module]

    future_route = (
        '\n\n@router.post("/profile/a-route-some-future-phase-will-add")\n'
        "async def a_route_some_future_phase_will_add():\n"
        "    return None\n"
    )
    sources = _sources_with(tmp_path, module, original + future_route)

    unclassified = _unclassified(sources)

    assert (
        f"{module}::a_route_some_future_phase_will_add" in unclassified
    ), (
        "ЗАМЫКАЮЩЕЕ УТВЕРЖДЕНИЕ ПОЛНОТЫ НЕ ЗАМЕТИЛО НОВЫЙ ИЗМЕНЯЮЩИЙ МАРШРУТ — "
        "гейт выродился в чёрный список, и маршрут будущей фазы окажется "
        "разрешён по умолчанию"
    )


def test_control_positive_the_untouched_source_tree_keeps_the_gate_green():
    """ЧТО ДОКАЗЫВАЕТ: на НЕИЗМЕНЁННОМ дереве гейт молчит.

    ⚠️ БЕЗ ЭТОГО КОНТРОЛЯ ОБА ОТРИЦАТЕЛЬНЫХ ПРОШЛИ БЫ И У ГЕЙТА, КОТОРЫЙ
    КРАСНЕЕТ ВСЕГДА. «Ловит подмену» и «ловит ТОЛЬКО подмену» — разные
    утверждения, и доказательство зубов состоит из обоих: гейт, роняющий сборку
    на любом дереве, был бы не строже, а просто сломан, и его сняли бы первым же
    коммитом.
    """
    sources = _project_sources()

    assert _prohibitions_not_declared(sources) == set(), (
        "гейт краснеет на неизменённом дереве — отрицательные контроли выше "
        "ничего не доказывают"
    )
    assert _unclassified(sources) == set(), (
        "утверждение полноты краснеет на неизменённом дереве — отрицательные "
        "контроли выше ничего не доказывают"
    )

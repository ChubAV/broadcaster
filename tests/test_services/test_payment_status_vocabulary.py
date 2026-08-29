"""ГЕЙТ СЛОВАРЯ СТАТУСОВ ПЛАТЕЖА: пятый статус нельзя завести молча, и колонка
`payments.status` не принимает свободных строковых литералов.

ЧТО ЗДЕСЬ УТВЕРЖДАЕТСЯ ОДНОЙ ФРАЗОЙ. Перечисление статусов платежа — КОНТРАКТ, а
не набор строк: каждый его член обязан быть КЛАССИФИЦИРОВАН во всех множествах,
которые о нём спрашивают, и попасть в колонку он может только через объявленную
константу.

⚠️ ЗАЧЕМ ГЕЙТ, ЕСЛИ КОД СЕГОДНЯ ИСПРАВЕН. Он охраняет не сегодняшнее состояние,
а способ отказа, который эта фаза уже пережила ОДИН РАЗ. Фаза завела четвёртый
статус `expired` (D-01), а вопрос «за каким платежом администратор ждёт исхода»
был задан ДОПОЛНЕНИЕМ терминальных статусов — и четвёртый член перечисления
попал под правило МОЛЧА: снятое по сроку давности намерение поднимало постоянный
денежный инцидент и приходило под чипсом «В обработке». Разрыв 1 отчёта
верификации закрыт планом 08-11 положительным отбором (`AWAITING_STATUSES`), но
сама возможность завести пятый член и не классифицировать его никуда не делась.
Этот файл превращает два НАБЛЮДЕНИЯ, на которые опёрся выбор положительной
формы, в машинные утверждения — иначе выбор остался бы рассуждением, а не
свойством кода.

ПОЛОЖИТЕЛЬНЫЙ ОТБОР БЕЗОПАСЕН РОВНО ПОТОМУ, ЧТО СЛОВАРЬ КОЛОНКИ ЗАКРЫТ И
ПРИНАДЛЕЖИТ НАМ. Дополнение защищало от сценария «провайдер завёл статус, о
котором мы не знаем, — и он виден» ценой сценария «мы сами завели статус, и он
виден ошибочно». Второй сценарий наступил; первый недостижим, пока в колонку
пишет только платёжный сервис объявленными константами. Вторая группа этого
файла и есть доказательство недостижимости: собственные статусы ЮKassa
(`waiting_for_capture` и прочие) в колонку не попадают ни одним из пяти путей
записи.

ДВЕ ГРУППЫ УТВЕРЖДЕНИЙ:

1. РАЗБИЕНИЕ. Словарь статусов собирается ТЕМ ЖЕ ОБХОДОМ, каким проверяется
   (приём замыкания множества на себя): значения `STATUS_*` берутся разбором
   исходника, а не переписываются сюда списком. Каждый собранный член обязан
   лежать РОВНО В ОДНОЙ группе классификации — наблюдаемые, терминальные или
   поимённо названный остаток. Неклассифицированная константа роняет гейт.
2. ЗАКРЫТОСТЬ КОЛОНКИ. Записать в `payments.status` можно ПЯТЬЮ формами, и все
   пять перечислены поимённо. Утверждение на все пять одно: правый операнд НЕ
   ЯВЛЯЕТСЯ свободным строковым литералом. Форма выбрана именно такой, потому
   что `_claim_payment` принимает значение ПАРАМЕТРОМ: запрет литерала выдержит
   параметр и поймает ровно то, что должен, — слово, записанное в колонку мимо
   объявленного словаря.

ГЕЙТ ДОКАЗЫВАЕТ СВОИ ЗУБЫ. Три контрольных случая (`-k control`) подают
разборщику ПОДДЕЛАННЫЙ исходник и утверждают, что каждая проверка КРАСНЕЕТ.
Обход, зелёный по построению, создаёт уверенность вместо проверки, и
обнаруживается это в тот единственный день, когда он пропускает настоящее
нарушение.

================================================================================
ГРАНИЦЫ ОБЪЁМА — ИХ ЧЕТЫРЕ, И ОНИ ВЫПИСАНЫ, А НЕ ПОДРАЗУМЕВАЮТСЯ
================================================================================

(1) РЕВИЗИИ ALEMBIC ПОД ГЕЙТ НЕ ПОПАДАЮТ НАМЕРЕННО. Правило проекта запрещает
    ревизиям импортировать имена приложения (они обязаны читаться в отрыве от
    его сегодняшнего состояния), поэтому литералы в их сыром SQL ОБЯЗАТЕЛЬНЫ:
    `alembic/versions/0021_payments_open_intent_index.py` пишет `'expired'`
    строкой ЗАКОННО. Область обхода — `app/**/*.py`, и `alembic/` в неё не
    входит ни одним путём.

(2) ПРЕДИКАТ ЧАСТИЧНОГО ИНДЕКСА В САМОЙ МОДЕЛИ — ЧТЕНИЕ, А НЕ ЗАПИСЬ.
    `app/models/payment.py` (`__table_args__`) содержит `'pending'` ТЕКСТОМ
    внутри `sqlite_where`/`postgresql_where`. Это условие ОТБОРА строк, а не
    запись значения, и равенство этого текста копии из ревизии уже охраняет
    `test_the_two_sources_of_the_schema_declare_one_predicate`. Гейт закрытости
    смотрит на пять форм ЗАПИСИ и предиката не касается.

(3) ФОРМЫ (3) И (4) ПРОВЕРЯЮТСЯ В ВЫВЕДЕННОМ ПОДМНОЖЕСТВЕ МОДУЛЕЙ, А НЕ НА ВСЁМ
    `app/`, И ОСТАТОК НАЗЫВАЕТСЯ ИЗМЕРЕННЫМ, А НЕ ОБЪЯВЛЯЕТСЯ ПУСТЫМ.
    Присваивание `.status` и `set_committed_value(..., "status", ...)` ТИП
    ПОЛУЧАТЕЛЯ НЕ РАЗРЕШАЮТ: для дерева `account.status = "syncing"` и
    `reserved.status = STATUS_EXPIRED` неотличимы. Таких присваиваний в `app/`
    сегодня ПЯТНАДЦАТЬ, и платежу принадлежит РОВНО ОДНО; остальные четырнадцать
    пишут в `MessengerAccount.status`, `Ad.status` и в состояние входа Telegram,
    и двенадцать из них — строковым литералом, ЗАКОННО. Гейт, флагующий эти
    двенадцать, не стал бы зелёным ни при какой правке приложения, то есть
    охранял бы ноль. Поэтому формы (3) и (4) обходятся в подмножестве модулей,
    в чьём дереве ВСТРЕЧАЕТСЯ ИМЯ ТИПА `Payment`. Подмножество ВЫВОДИТСЯ тем же
    обходом, а не выписывается списком путей: список устаревает молча, а вывод —
    нет.
    ⚠️ ОСТАТОК ОБЛАСТИ СЕГОДНЯ НЕПУСТ, И ЭТО НАЗВАНО ПОИМЁННО.
    `app/pages/billing.py` держит ЖИВЫЕ строки `Payment`, полученные из
    `billing_service.get_payment_history() -> list[Payment]`, и НИ РАЗУ не
    называет тип: имя `Payment` встречается в нём только внутри
    `PaymentCreationError`, а это ДРУГОЙ идентификатор, и обход его не
    засчитывает. В подмножество этот модуль поэтому не попадает.
    ГЕЙТ ПРИ ЭТОМ ЗДОРОВ, И ДЕРЖИТ ЕГО ИЗМЕРЕННЫЙ ФАКТ, А НЕ ОТСУТСТВИЕ
    ОСТАТКА: присваиваний `.status` в `billing.py` НЕТ НИ ОДНОГО — платежи он
    только читает и печатает. Это свойство СЕГОДНЯШНЕГО кода, а не схемы:
    заведись в `billing.py` запись статуса, гейт её не увидит. Митигация
    `T-08-49` записана ЧАСТИЧНОЙ по этому названному остатку.
    ⚠️ ФОРМУЛИРОВКУ «ни одна функция вне `payment_service.py` не возвращает
    `Payment`» НЕ ПИСАТЬ: она неверна ровно на `get_payment_history`, и
    читатель, решающий по ней, покрыт ли его модуль гейтом, получил бы неверный
    ответ — той же формы отказ, каким открылся Разрыв 1.

(4) ГЕЙТ НЕ УТВЕРЖДАЕТ, ЧТО ЗНАЧЕНИЕ КОЛОНКИ В БАЗЕ ПРИНАДЛЕЖИТ СЛОВАРЮ. Данные
    могли прийти из прежних ревизий и из прежних редакций кода. Утверждается
    ровно одно: НОВЫХ путей записи мимо словаря код не заводит.

================================================================================
ЕДИНСТВЕННОЕ ПОИМЁННОЕ ИСКЛЮЧЕНИЕ — УМОЛЧАНИЕ КОЛОНКИ (ФОРМА 5)
================================================================================

`app/models/payment.py` объявляет `status: Mapped[str] = mapped_column(
String(50), default="pending")` — умолчание записано ЛИТЕРАЛОМ, и заменить его
на `STATUS_PENDING` НЕЛЬЗЯ: платёжный сервис импортирует `Payment` из модели, и
обратный импорт константы замкнул бы цикл. Переезд констант в `app/constants.py`
снял бы исключение одним движением, но это правка чужой границы и другая работа.

ПОЭТОМУ МОДЕЛЬ ЭТИМ ПЛАНОМ НЕ ТРОГАЕТСЯ, А ГЕЙТ ВМЕСТО ЗАПРЕТА УТВЕРЖДАЕТ
РАВЕНСТВО: значение умолчания обязано СОВПАДАТЬ со значением константы
`STATUS_PENDING`, собранной первой группой. Пятый статус, заведённый ПОДМЕНОЙ
УМОЛЧАНИЯ, роняет гейт — подставленного слова нет в собранном словаре. Путь
«переписать умолчание вместо объявления константы» закрыт машинно, а не
обещанием.

УСЛОВИЕ СНЯТИЯ ИСКЛЮЧЕНИЯ ЗАПИСАНО: переедут константы статусов в
`app/constants.py` — цикл импорта исчезнет, умолчание станет обычной формой под
общим запретом литерала, и поимённое исключение отсюда уйдёт.
"""

import ast
from pathlib import Path

import pytest

from app.services.payment_service import (
    AWAITING_STATUSES,
    STATUS_CANCELED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    STATUS_SUCCEEDED,
    TERMINAL_STATUSES,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = REPO_ROOT / "app"

# Модуль, объявляющий словарь статусов. Он же — исходник, из которого словарь
# СОБИРАЕТСЯ: гейт не переписывает значения к себе, он их читает.
SERVICE_MODULE = "app/services/payment_service.py"

# Модуль, объявляющий колонку. Форма (5) живёт здесь и здесь же проверяется.
MODEL_MODULE = "app/models/payment.py"

# ИМЯ ТИПА, ПО КОТОРОМУ ВЫВОДИТСЯ ОБЛАСТЬ ФОРМ (3)-(4). Слово выписано ОДИН раз
# и используется обходом; список путей вместо него запрещён — см. границу (3).
PAYMENT_TYPE_NAME = "Payment"

# Приставка объявленных констант словаря. Собираются модульные присваивания
# `STATUS_* = "<строка>"`, и ничего сверх.
STATUS_PREFIX = "STATUS_"

# ЧЕТЫРЕ СЛОВА, КОТОРЫЕ СЛОВАРЬ СОДЕРЖИТ СЕГОДНЯ. Величина выписана ЧИСЛОМ, а не
# выведена, НАМЕРЕННО: пятый статус обязан уронить гейт СЧЁТОМ ещё до того, как
# дойдёт до классификации, — иначе «классифицировать» его можно было бы, дописав
# в оба множества и не заметив, что вопрос о нём никто не задавал.
DECLARED_STATUS_COUNT = 4

# ИМЯ КОЛОНКИ, ЧЕЙ СЛОВАРЬ ОХРАНЯЕТСЯ. Форма (4) называет её строкой в вызове,
# формы (1), (2) и (5) — именованным аргументом, форма (3) — атрибутом.
STATUS_ATTRIBUTE = "status"

# Слово, которым подделываются контрольные случаи: СОБСТВЕННЫЙ статус ЮKassa,
# которого в нашем словаре нет и быть не должно. Ровно тот сценарий, ради
# которого вторая группа и написана.
FOREIGN_STATUS_WORD = "waiting_for_capture"


# ---- Чтение исходников -----------------------------------------------------


def _app_sources() -> dict[str, str]:
    """Все модули `app/**/*.py` как `путь -> текст`.

    Анализаторы ниже принимают именно ЭТОТ словарь, а не читают диск сами:
    контрольные случаи подменяют в нём один текст и прогоняют те же функции.
    Гейт, чьи зубы проверяются не на нём самом, доказывал бы не свои зубы.
    """
    sources: dict[str, str] = {}
    for path in sorted(APP_DIR.rglob("*.py")):
        sources[str(path.relative_to(REPO_ROOT))] = path.read_text(encoding="utf-8")
    return sources


def _sources_with(sources: dict[str, str], module: str, text: str) -> dict[str, str]:
    """Копия словаря исходников с подменённым текстом одного модуля."""
    forged = dict(sources)
    forged[module] = text
    return forged


# ---- Группа 1: разбиение словаря -------------------------------------------


def _declared_statuses(text: str) -> dict[str, str]:
    """Модульные константы `STATUS_* = "<строка>"` как `ИМЯ -> значение`.

    Берётся ТОЛЬКО модульный уровень: константа, объявленная внутри функции,
    словарём колонки не является и в классификации не участвует.
    """
    collected: dict[str, str] = {}
    for node in ast.parse(text).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not target.id.startswith(STATUS_PREFIX):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            collected[target.id] = node.value.value
    return collected


def test_the_status_vocabulary_is_collected_from_the_source_and_not_rewritten():
    """Словарь СОБРАН разбором исходника и сверен с импортом.

    ⚠️ ДВЕ ПОЛОВИНЫ УТВЕРЖДЕНИЯ НУЖНЫ ОБЕ. Сбор текстом даёт множество,
    ЗАМКНУТОЕ на объявление: дописанная константа попадает в него сама, и
    классификация обязана её увидеть. Сверка с ИМПОРТОМ доказывает, что гейт
    охраняет ТОТ файл: разойдись путь и модуль — обход читал бы один исходник, а
    приложение работало бы по другому, и зелёный не значил бы ничего.
    """
    collected = _declared_statuses(_app_sources()[SERVICE_MODULE])

    assert len(collected) == DECLARED_STATUS_COUNT, (
        f"словарь статусов изменил размер: собрано {sorted(collected)}, "
        f"ожидалось {DECLARED_STATUS_COUNT} константы. Новый член перечисления "
        "обязан быть КЛАССИФИЦИРОВАН, а не просто добавлен — см. соседние тесты"
    )
    assert collected == {
        "STATUS_PENDING": STATUS_PENDING,
        "STATUS_SUCCEEDED": STATUS_SUCCEEDED,
        "STATUS_CANCELED": STATUS_CANCELED,
        "STATUS_EXPIRED": STATUS_EXPIRED,
    }, (
        "собранное текстом множество разошлось со значениями, импортированными "
        f"из модуля: {collected}. Гейт охраняет не тот файл, который работает"
    )


def test_every_declared_status_belongs_to_exactly_one_answer():
    """Каждый объявленный статус лежит РОВНО В ОДНОЙ группе классификации.

    Три группы отвечают на три РАЗНЫХ вопроса: «за каким статусом администратор
    ждёт исхода» (наблюдаемые), «из какого статуса платёж уже не выйдет»
    (терминальные) и остаток — «оплачиваемый, но не ожидаемый».

    ⚠️ ЭТО И ЕСТЬ ГЕЙТ НА ПЯТЫЙ СТАТУС. Константа, дописанная будущей фазой,
    попадёт в собранный словарь обходом и НЕ попадёт ни в одну группу — тест
    покраснеет и заставит ответить на вопрос, на который Разрыв 1 ответили
    молча и неверно.
    """
    collected = set(_declared_statuses(_app_sources()[SERVICE_MODULE]).values())

    groups = {
        "наблюдаемые (AWAITING_STATUSES)": set(AWAITING_STATUSES),
        "терминальные (TERMINAL_STATUSES)": set(TERMINAL_STATUSES),
        "остаток (оплачиваемый, но не ожидаемый)": {STATUS_EXPIRED},
    }

    for status in sorted(collected):
        holders = [name for name, group in groups.items() if status in group]
        assert len(holders) == 1, (
            f"статус {status!r} классифицирован в {len(holders)} групп(ах) "
            f"{holders} вместо ровно одной. Член перечисления, о котором не "
            "спросила ни одна группа, попадает под правила МОЛЧА — ровно так "
            "четвёртый статус стал постоянным денежным инцидентом (D-01)"
        )

    union = set().union(*groups.values())
    assert union == collected, (
        f"объединение групп {sorted(union)} не совпало со словарём "
        f"{sorted(collected)}: классификация перестала быть разбиением"
    )


def test_the_awaiting_set_and_the_terminal_set_do_not_overlap():
    """Ни один статус не отвечает на ОБА вопроса сразу.

    Пересечение означало бы, что за платежом ждут исхода и одновременно знают,
    что он уже не выйдет из своего статуса, — то есть один из двух вопросов
    задан неверно.
    """
    assert not (AWAITING_STATUSES & TERMINAL_STATUSES), (
        "наблюдаемые и терминальные статусы пересеклись: "
        f"{sorted(AWAITING_STATUSES & TERMINAL_STATUSES)}"
    )
    assert STATUS_PENDING in AWAITING_STATUSES
    assert STATUS_EXPIRED not in AWAITING_STATUSES, (
        "снятое по сроку давности намерение вернулось в наблюдаемые: порог "
        "уборки и порог залипания считаются от ОДНОЙ константы и совпадают ПО "
        "ПОСТРОЕНИЮ, поэтому каждая снятая строка снова стала бы постоянным "
        "денежным инцидентом"
    )


def test_the_unclassified_remainder_is_named_by_name():
    """Остаток классификации назван ПОИМЁННО и равен ровно `{STATUS_EXPIRED}`.

    ⚠️ УТВЕРЖДЕНИЕ ПОИМЁННОЕ, А НЕ ПРО РАЗМЕР. «Оплачиваемый, но не ожидаемый»
    есть ТРЕТЬЯ ГРУППА, а не забытая: просроченное намерение остаётся
    оплачиваемым (`_claim_payment` продолжает спрашивать дополнение
    терминальных), но аномалией не является. Проверка на пустоту остатка была бы
    неверной, а проверка на его размер пропустила бы подмену одного слова другим.
    """
    collected = set(_declared_statuses(_app_sources()[SERVICE_MODULE]).values())
    remainder = collected - set(AWAITING_STATUSES) - set(TERMINAL_STATUSES)

    assert remainder == {STATUS_EXPIRED}, (
        f"остаток классификации стал {sorted(remainder)} вместо "
        f"[{STATUS_EXPIRED!r}]: третья группа получила нового члена, о котором "
        "ни один вопрос не задан"
    )


# ---- Группа 2: закрытость словаря колонки ----------------------------------


def _names_in_tree(tree: ast.Module) -> set[str]:
    """Все имена, ВСТРЕЧАЮЩИЕСЯ в дереве: импорты, обращения, объявления.

    ⚠️ `ast.ClassDef` УЧТЁН НАРЯДУ С ИМПОРТОМ И ОБРАЩЕНИЕМ, И ЭТО НЕСУЩЕЕ.
    Модуль, ОБЪЯВЛЯЮЩИЙ тип, называет его самым прямым образом, но ни `ast.Name`,
    ни `ast.alias` в нём не появляются: без этой ветви `app/models/payment.py`
    выпал бы из области собственной формы (5) и (3)-(4), а гейт охранял бы
    словарь колонки, не заглядывая в модуль, где колонка объявлена.

    Имя сравнивается ЦЕЛИКОМ: `PaymentCreationError` — ДРУГОЙ идентификатор, и
    модуль, знающий только его, тип платежа не называет. Именно на этом
    различении стоит измеренный остаток области — см. границу (3) в докстринге
    файла.
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.alias):
            found.add(node.asname or node.name.split(".")[-1])
        elif isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.ClassDef):
            found.add(node.name)
    return found


def _modules_naming_the_payment_type(sources: dict[str, str]) -> set[str]:
    """Подмножество модулей, в чьём дереве встречается имя типа `Payment`.

    ВЫВОДИТСЯ ОБХОДОМ, А НЕ ВЫПИСЫВАЕТСЯ СПИСКОМ. Список путей в исходнике гейта
    запрещён: он устаревает молча, и модуль, начавший писать статус завтра, в
    него не попал бы — то есть область проверки сузилась бы без единого красного.
    """
    return {
        module
        for module, text in sources.items()
        if PAYMENT_TYPE_NAME in _names_in_tree(ast.parse(text))
    }


def _chain_root(call: ast.Call) -> ast.Call | None:
    """Корень цепочки вызовов: `update(Payment).where(...).values(...)` -> `update(Payment)`.

    Нужен потому, что форма (2) разрешима по имени типа только В КОРНЕ цепочки:
    сам `values(...)` о `Payment` не знает ничего.
    """
    current: ast.expr = call
    while isinstance(current, ast.Call):
        func = current.func
        if isinstance(func, ast.Attribute):
            current = func.value
        elif isinstance(func, ast.Name):
            return current
        else:
            return None
    return None


def _is_free_string_literal(node: ast.expr) -> bool:
    """Правый операнд записи есть СВОБОДНЫЙ строковый литерал.

    ⚠️ ЗАПРЕЩАЕТСЯ ЛИТЕРАЛ, А НЕ «ВСЁ, КРОМЕ КОНСТАНТЫ», И ЭТО ВЫБОР ФОРМЫ.
    `_claim_payment` принимает значение ПАРАМЕТРОМ (`new_status`), и запрет
    «только имя объявленной константы» покраснел бы на исправном коде. Запрет
    литерала выдерживает параметр и ловит ровно то, что должен: слово,
    записанное в колонку мимо объявленного словаря.
    """
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _literal_status_writes(sources: dict[str, str]) -> list[tuple[str, str, int, str]]:
    """Все записи в `payments.status` СВОБОДНЫМ ЛИТЕРАЛОМ — как `(форма, модуль, строка, слово)`.

    Пять форм записи, и область у них РАЗНАЯ:

    * (1) конструктор `Payment(status=...)` — разрешима по имени типа прямо в
      узле, обходится на всём `app/`;
    * (2) `values(status=...)` на цепочке от `update(Payment)`/`insert(Payment)`
      — разрешима по корню цепочки, обходится на всём `app/`;
    * (3) присваивание `<объект>.status = ...` — тип получателя НЕ РАЗРЕШИМ,
      обходится в ВЫВЕДЕННОМ подмножестве;
    * (4) `set_committed_value(<объект>, "status", ...)` — тип получателя НЕ
      РАЗРЕШИМ, обходится в ВЫВЕДЕННОМ подмножестве;
    * (5) умолчание объявления колонки — проверяется ОТДЕЛЬНЫМ утверждением на
      равенство, а не запретом: единственное поимённое исключение, см. докстринг.
    """
    scoped = _modules_naming_the_payment_type(sources)
    violations: list[tuple[str, str, int, str]] = []

    for module, text in sources.items():
        tree = ast.parse(text)
        in_scope = module in scoped

        for node in ast.walk(tree):
            # Форма (3): присваивание атрибуту.
            if isinstance(node, ast.Assign) and in_scope:
                for target in node.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and target.attr == STATUS_ATTRIBUTE
                        and _is_free_string_literal(node.value)
                    ):
                        violations.append(
                            ("(3) присваивание", module, node.lineno, node.value.value)
                        )

            if not isinstance(node, ast.Call):
                continue
            func = node.func

            # Форма (1): конструктор.
            if isinstance(func, ast.Name) and func.id == PAYMENT_TYPE_NAME:
                for keyword in node.keywords:
                    if keyword.arg == STATUS_ATTRIBUTE and _is_free_string_literal(
                        keyword.value
                    ):
                        violations.append(
                            ("(1) конструктор", module, node.lineno, keyword.value.value)
                        )

            # Форма (2): массовый UPDATE/INSERT.
            if isinstance(func, ast.Attribute) and func.attr == "values":
                root = _chain_root(node)
                if (
                    root is not None
                    and isinstance(root.func, ast.Name)
                    and root.func.id in ("update", "insert")
                    and root.args
                    and isinstance(root.args[0], ast.Name)
                    and root.args[0].id == PAYMENT_TYPE_NAME
                ):
                    for keyword in node.keywords:
                        if keyword.arg == STATUS_ATTRIBUTE and _is_free_string_literal(
                            keyword.value
                        ):
                            violations.append(
                                ("(2) values", module, node.lineno, keyword.value.value)
                            )

            # Форма (4): зеркалирование выигранной заявки.
            if (
                isinstance(func, ast.Name)
                and func.id == "set_committed_value"
                and in_scope
                and len(node.args) >= 3
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value == STATUS_ATTRIBUTE
                and _is_free_string_literal(node.args[2])
            ):
                violations.append(
                    ("(4) set_committed_value", module, node.lineno, node.args[2].value)
                )

    return violations


def _column_default(text: str) -> str | None:
    """Значение `default=` у колонки `status` внутри `class Payment` — форма (5)."""
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, ast.ClassDef) or node.name != PAYMENT_TYPE_NAME:
            continue
        for statement in node.body:
            if (
                not isinstance(statement, ast.AnnAssign)
                or not isinstance(statement.target, ast.Name)
                or statement.target.id != STATUS_ATTRIBUTE
                or not isinstance(statement.value, ast.Call)
            ):
                continue
            for keyword in statement.value.keywords:
                if keyword.arg in ("default", "server_default") and isinstance(
                    keyword.value, ast.Constant
                ):
                    return keyword.value.value
    return None


def test_no_string_literal_is_ever_written_into_the_payment_status_column():
    """В колонку `payments.status` не пишет ни один свободный строковый литерал.

    ⚠️ ИМЕННО ЭТО УТВЕРЖДЕНИЕ ДЕЛАЕТ ПОЛОЖИТЕЛЬНЫЙ ОТБОР БЕЗОПАСНЫМ. Словарь
    колонки ЗАКРЫТ и принадлежит нам: он растёт только через объявление
    константы, которую первая группа заставляет классифицировать. Собственный
    статус провайдера (`waiting_for_capture` и прочие) в колонку не попадает ни
    одним из пяти путей, и потому недостижим для правила «незакрыт».

    ⚠️ КРИТЕРИЙ ДОСТИЖИМ, И ЭТО В НЁМ ПРОВЕРЯЕТСЯ ТОЖЕ. Тест ЗЕЛЁНЫЙ на
    действующем `app/` без единой правки прикладного кода — включая
    `_claim_payment`, где значение приезжает параметром, и включая двенадцать
    законных литералов вида `<объект>.status = "..."` вне платежа, которые в
    область форм (3)-(4) не входят по границе (3).
    """
    violations = _literal_status_writes(_app_sources())

    assert violations == [], (
        "статус записан в колонку свободным строковым литералом — слово попало "
        "в словарь колонки мимо объявленного перечисления и стало невидимым "
        f"положительному отбору: {violations}"
    )


def test_the_scope_of_the_column_gate_is_derived_from_the_type_name():
    """Область форм (3)-(4) ВЫВЕДЕНА обходом, а не выписана списком путей.

    ⚠️ ОСТАТОК ОБЛАСТИ УТВЕРЖДАЕТСЯ ИЗМЕРЕННЫМ, А НЕ ПУСТЫМ. Вне подмножества
    сегодня лежит `app/pages/billing.py`, держащий живые строки `Payment`: он
    получает их из `billing_service.get_payment_history()` и ни разу не называет
    тип. Гейт здоров не потому, что остатка нет, а потому, что присваиваний
    `.status` в этом модуле НЕТ НИ ОДНОГО. Утверждается ровно этот факт — чтобы
    день, когда он перестанет быть верным, был красным, а не молчаливым.
    """
    sources = _app_sources()
    scoped = _modules_naming_the_payment_type(sources)

    assert SERVICE_MODULE in scoped, "платёжный сервис выпал из области форм (3)-(4)"
    assert MODEL_MODULE in scoped, (
        "модуль, ОБЪЯВЛЯЮЩИЙ тип платежа, выпал из области: обход перестал "
        "засчитывать `class Payment` как называние типа"
    )

    # Модули, пишущие `.status` ЧУЖИХ моделей законным литералом, в область не
    # входят — иначе гейт не стал бы зелёным ни при какой правке приложения.
    for outsider in ("app/pages/accounts.py", "app/worker/tasks.py"):
        assert outsider in sources, f"проверяемый модуль {outsider} исчез из дерева"
        assert outsider not in scoped, (
            f"{outsider} попал в область форм (3)-(4), хотя типа платежа не "
            "называет: гейт начал флаговать законные литералы чужих моделей и "
            "не станет зелёным ни при какой правке"
        )

    # ИЗМЕРЕННЫЙ ОСТАТОК, названный поимённо (граница (3), митигация T-08-49).
    remainder = "app/pages/billing.py"
    assert remainder not in scoped, (
        f"{remainder} вошёл в область — запись формулировки остатка в докстринге "
        "файла и в T-08-49 устарела и обязана быть переписана"
    )
    billing_tree = ast.parse(sources[remainder])
    billing_status_writes = [
        node.lineno
        for node in ast.walk(billing_tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Attribute) and target.attr == STATUS_ATTRIBUTE
    ]
    assert billing_status_writes == [], (
        f"в {remainder} появилась запись статуса (строки "
        f"{billing_status_writes}), а модуль лежит ВНЕ области гейта: путь "
        "записи мимо словаря перестал быть непроверенным теоретически и стал "
        "непроверенным фактически"
    )


def test_the_column_default_of_the_model_is_tied_to_the_declared_pending_value():
    """Умолчание колонки — ПЯТАЯ форма записи, и она привязана к словарю.

    ⚠️ ПОИМЁННОЕ ИСКЛЮЧЕНИЕ, А НЕ ПРОБЕЛ. Умолчание записано литералом потому,
    что платёжный сервис импортирует `Payment` из модели, и обратный импорт
    константы замкнул бы цикл. Вместо запрета гейт утверждает РАВЕНСТВО: пятый
    статус, заведённый подменой умолчания, роняет тест — подставленного слова
    нет в собранном словаре.

    Условие снятия исключения: переедут константы в `app/constants.py` — цикл
    исчезнет, и умолчание станет обычной формой под общим запретом литерала.
    """
    sources = _app_sources()
    default = _column_default(sources[MODEL_MODULE])

    assert default is not None, (
        "умолчание колонки `status` не найдено разбором модели: форма (5) "
        "перестала быть видимой гейту, и подмена умолчания снова стала тихой"
    )
    assert default == STATUS_PENDING, (
        f"умолчание колонки {default!r} разошлось со значением STATUS_PENDING "
        f"{STATUS_PENDING!r}: статус, не объявленный константой, стал значением "
        "по умолчанию для каждой новой строки платежа"
    )
    assert default in _declared_statuses(sources[SERVICE_MODULE]).values(), (
        f"умолчание колонки {default!r} отсутствует в собранном словаре статусов"
    )


# ---- Контрольные случаи: гейт обязан уметь краснеть -------------------------


def test_control_a_fifth_status_constant_reddens_the_partition_gate():
    """ЧТО ДОКАЗЫВАЕТ: неклассифицированная константа `STATUS_*` роняет разбиение.

    Это случай, РАДИ КОТОРОГО первая группа существует: пятый статус, добавленный
    будущей фазой. Без гейта он попал бы под правило «незакрыт» молча — ровно
    так, как четвёртый статус попал в Разрыве 1.
    """
    original = _app_sources()[SERVICE_MODULE]
    forged = original + '\n\nSTATUS_REFUNDED = "refunded"\n'

    collected = _declared_statuses(forged)

    assert "STATUS_REFUNDED" in collected, (
        "ПОДМЕНА НЕ ПРИЗЕМЛИЛАСЬ: разборщик не увидел дописанной константы, и "
        "утверждения ниже доказывали бы не зубы гейта, а промах контроля"
    )
    assert len(collected) != DECLARED_STATUS_COUNT, (
        "счёт словаря не заметил пятой константы"
    )

    values = set(collected.values())
    remainder = values - set(AWAITING_STATUSES) - set(TERMINAL_STATUSES)
    assert remainder != {STATUS_EXPIRED}, (
        "ОСТАТОК КЛАССИФИКАЦИИ НЕ ЗАМЕТИЛ ПЯТОГО СТАТУСА — гейт выродился в "
        "проверку размера, и член перечисления, о котором не спросила ни одна "
        "группа, снова проходит молча"
    )
    assert "refunded" in remainder


@pytest.mark.parametrize(
    ("form", "snippet"),
    [
        (
            "(1) конструктор",
            "\n\ndef _forged_constructor(user_id):\n"
            f'    return Payment(user_id=user_id, status="{FOREIGN_STATUS_WORD}")\n',
        ),
        (
            "(2) values",
            "\n\ndef _forged_values():\n"
            "    return (\n"
            "        update(Payment)\n"
            "        .where(Payment.id == 1)\n"
            f'        .values(status="{FOREIGN_STATUS_WORD}")\n'
            "    )\n",
        ),
        (
            "(3) присваивание",
            "\n\ndef _forged_assignment(reserved):\n"
            f'    reserved.status = "{FOREIGN_STATUS_WORD}"\n',
        ),
        (
            "(4) set_committed_value",
            "\n\ndef _forged_mirror(db_payment):\n"
            f'    set_committed_value(db_payment, "status", "{FOREIGN_STATUS_WORD}")\n',
        ),
    ],
)
def test_control_a_literal_write_reddens_the_column_vocabulary_gate(form, snippet):
    """ЧТО ДОКАЗЫВАЕТ: каждая из ЧЕТЫРЁХ форм записи ловится ОТДЕЛЬНО.

    ⚠️ ФОРМЫ ПРОВЕРЯЮТСЯ ПООДИНОЧКЕ, А НЕ ОДНИМ ПОДДЕЛАННЫМ ФАЙЛОМ СО ВСЕМИ
    СРАЗУ. Общий контроль зеленел бы и у гейта, видящего РОВНО ОДНУ форму из
    четырёх, — а незамеченный путь записи есть в точности тот путь, которым
    чужое слово попадёт в колонку.

    Подмена вносится в `app/services/payment_service.py`: модуль называет тип
    `Payment` и потому лежит в области ВСЕХ четырёх форм, включая
    receiver-неразрешимые (3) и (4).
    """
    sources = _app_sources()
    assert _literal_status_writes(sources) == [], (
        "контроль бессмыслен: гейт красен уже на неизменённом дереве"
    )

    forged = _sources_with(
        sources, SERVICE_MODULE, sources[SERVICE_MODULE] + snippet
    )
    violations = _literal_status_writes(forged)

    assert violations, (
        f"ГЕЙТ ЗАКРЫТОСТИ КОЛОНКИ НЕ УВИДЕЛ ЗАПИСИ ЛИТЕРАЛОМ ФОРМОЙ {form}: "
        "путь записи мимо объявленного словаря остался неохраняемым, и "
        "положительный отбор перестал быть безопасным"
    )
    assert any(kind == form for kind, _, _, _ in violations), (
        f"нарушение найдено, но не формой {form}: {violations}. Гейт ловит "
        "чужой путь и не ловит проверяемый"
    )
    assert all(word == FOREIGN_STATUS_WORD for _, _, _, word in violations)


def test_control_a_rewritten_column_default_reddens_the_column_vocabulary_gate():
    """ЧТО ДОКАЗЫВАЕТ: подменённое умолчание колонки роняет привязку формы (5).

    Второй из двух путей завести пятый статус молча: не объявлять константу
    вовсе, а переписать `default=` в модели. Без этого контроля привязка
    умолчания была бы утверждением, зелёным по построению.
    """
    original = _app_sources()[MODEL_MODULE]
    forged = original.replace(
        'status: Mapped[str] = mapped_column(String(50), default="pending")',
        f'status: Mapped[str] = mapped_column(String(50), default="{FOREIGN_STATUS_WORD}")',
    )

    assert forged != original, (
        "ПОДМЕНА НЕ ПРИЗЕМЛИЛАСЬ: объявление колонки записано иначе, чем ждёт "
        "контроль, и утверждение ниже доказывало бы промах контроля, а не зубы"
    )

    default = _column_default(forged)

    assert default == FOREIGN_STATUS_WORD, (
        "разборщик не увидел подменённого умолчания"
    )
    assert default != STATUS_PENDING, (
        "ПРИВЯЗКА УМОЛЧАНИЯ НЕ ЗАМЕТИЛА ПОДМЕНЫ — путь «завести пятый статус, "
        "переписав умолчание вместо объявления константы» остался открытым"
    )
    assert default not in _declared_statuses(
        _app_sources()[SERVICE_MODULE]
    ).values(), "подставленное слово оказалось в объявленном словаре"

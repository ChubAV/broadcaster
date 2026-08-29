"""Два ИСТОЧНИКА СХЕМЫ объявляют один индекс, и разойтись молча им больше нечем.

Потолок незакрытых подписочных намерений (PAY-01) объявлен ДВАЖДЫ, и оба
объявления обязательны:

* `alembic/versions/0021_payments_open_intent_index.py` — то, что накатывается на
  боевую базу;
* `app/models/payment.py` (`__table_args__`) — то, из чего суита строит СВОЮ
  базу: `tests/conftest.py` поднимает схему `Base.metadata.create_all` и об
  Alembic не знает ВОВСЕ.

⚠️ ЗАЧЕМ СТОРОЖ, ЕСЛИ ОБА ОБЪЯВЛЕНИЯ УЖЕ НАПИСАНЫ. Он охраняет не сегодняшнее
состояние, а БУДУЩЕЕ расхождение: предикат поправят в одном файле и забудут в
другом. Для SQLite предикат частичного индекса есть ТЕКСТ — запись без пробелов
вокруг знака равенства и запись с пробелами суть РАЗНЫЕ ограничения под ОДНИМ
именем. Молча разошедшиеся источники схемы дали бы боевую базу с одним потолком,
а тестовую — с другим, и суита зеленела бы на ограничении, которого на бою нет.

РАЗБОР ТЕКСТОМ, А НЕ ИМПОРТОМ. Модуль ревизии этот файл не импортирует: импорт
связал бы тест с порядком накатов и нарушил бы правило проекта о ревизиях,
которые ничего не импортируют и ниоткуда не импортируются
(`0013`/`0014`/`0017`/`0018`/`0020`/`0021`). Оба файла читаются как ТЕКСТ и
разбираются `ast`. Что импорта нет, утверждается разбором СОБСТВЕННОГО дерева
этого файла, а не обещанием.

⚠️ ГРАНИЦА ОБЪЁМА ВЫПИСАНА, А НЕ ПОДРАЗУМЕВАЕТСЯ. Сверяется РОВНО ОДНА пара
«модель ↔ ревизия» — индекс платежей. Тот же класс расхождения существует и у
`uq_subscriptions_active_user` (`app/models/subscription.py` против ревизии
`0018`): там предикаты сегодня совпадают, но машиной это не утверждено НИГДЕ.
Обобщение сверки на все пары «модель ↔ ревизия» — работа своего размера, и её
отсутствие здесь есть РЕШЕНИЕ, а не недосмотр.
"""

import ast
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.payment import Payment
from app.models.user import User

INDEX_NAME = "uq_payments_open_subscription_intent"

# Оба диалектных параметра обязаны нести ОДИН предикат: PostgreSQL и SQLite
# получают частичный индекс разными ключами, и забытый второй ключ означал бы
# потолок ровно на одном из двух диалектов.
PREDICATE_KEYWORDS = ("sqlite_where", "postgresql_where")

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_PY = REPO_ROOT / "app" / "models" / "payment.py"
REVISION_PY = (
    REPO_ROOT / "alembic" / "versions" / "0021_payments_open_intent_index.py"
)


def _module_constants(tree: ast.Module) -> dict[str, str]:
    """Строковые константы модуля — `ИМЯ -> значение`.

    Нужны потому, что ревизия выписывает и имя индекса, и предикат ИМЕНОВАННЫМИ
    константами (`INDEX_NAME`, `OPEN_INTENT_PREDICATE`), а модель — литералами.
    Сверка обязана видеть ЗНАЧЕНИЯ, иначе она сравнивала бы способ записи.
    """
    constants: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                constants[target.id] = node.value.value
    return constants


def _as_string(node: ast.expr, constants: dict[str, str]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    return None


def _called_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _index_predicates(source: str) -> dict[str, str]:
    """Предикаты индекса `INDEX_NAME`, снятые из ТЕКСТА файла разбором `ast`.

    Возвращает `{'sqlite_where': ..., 'postgresql_where': ...}`. Ищутся вызовы
    `Index(...)` (модель) и `create_index(...)` (ревизия), среди позиционных
    аргументов которых стоит имя нашего индекса; предикат снимается из
    `text(...)` / `sa.text(...)`, переданного соответствующим ключом.
    """
    tree = ast.parse(source)
    constants = _module_constants(tree)
    found: dict[str, str] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _called_name(node) not in ("Index", "create_index"):
            continue
        names = {_as_string(arg, constants) for arg in node.args}
        if INDEX_NAME not in names:
            continue
        for keyword in node.keywords:
            if keyword.arg not in PREDICATE_KEYWORDS:
                continue
            value = keyword.value
            if isinstance(value, ast.Call) and _called_name(value) == "text":
                if len(value.args) == 1:
                    predicate = _as_string(value.args[0], constants)
                    if predicate is not None:
                        found[keyword.arg] = predicate
    return found


def _disagreements(model_source: str, revision_source: str) -> list[str]:
    """Расхождения двух источников схемы. Пустой список — источники согласны.

    Функция отдельная от теста НАМЕРЕННО: ею же проверяются ЗУБЫ сверки —
    подделке она обязана вернуть непустой список.
    """
    model = _index_predicates(model_source)
    revision = _index_predicates(revision_source)
    problems: list[str] = []

    for source_name, predicates in (("модель", model), ("ревизия", revision)):
        missing = set(PREDICATE_KEYWORDS) - set(predicates)
        if missing:
            problems.append(
                f"{source_name} не объявляет предикат ключами {sorted(missing)}"
            )

    values = set(model.values()) | set(revision.values())
    if len(values) > 1:
        problems.append(
            "предикаты РАЗОШЛИСЬ — для SQLite это разные ограничения под одним "
            f"именем: {sorted(values)}"
        )
    return problems


def test_the_model_declares_the_open_intent_index():
    """Модель объявляет ИМЕННО тот индекс: уникальный, по владельцу, частичный.

    Без этого объявления вся обычная суита работала бы на схеме БЕЗ потолка —
    ровно там, где прикладная проверка потолка снята (план 08-05, D-06).
    """
    indexes = {index.name: index for index in Payment.__table__.indexes}
    assert INDEX_NAME in indexes, (
        f"модель не объявляет {INDEX_NAME}: база из `Base.metadata.create_all` "
        "поднимется БЕЗ потолка, и суита его не проверит ни одним тестом"
    )
    index = indexes[INDEX_NAME]
    assert index.unique is True, "индекс не уникален — потолком он не является"
    assert [column.name for column in index.columns] == ["user_id"], (
        "потолок считает намерения не владельца"
    )
    for keyword in PREDICATE_KEYWORDS:
        clause = index.dialect_kwargs.get(keyword)
        assert clause is not None and str(clause).strip(), (
            f"предикат не объявлен ключом {keyword}: на этом диалекте индекс "
            "стал бы уникальностью по пользователю ЦЕЛИКОМ и запер бы его "
            "навсегда"
        )


def test_the_two_sources_of_the_schema_declare_one_predicate():
    """ЧЕТЫРЕ вхождения предиката (два в модели, два в ревизии) равны СИМВОЛ В СИМВОЛ."""
    problems = _disagreements(
        MODEL_PY.read_text(encoding="utf-8"),
        REVISION_PY.read_text(encoding="utf-8"),
    )

    assert not problems, "; ".join(problems)


def test_the_comparison_reddens_on_a_single_changed_space():
    """КОНТРОЛЬ ЗУБОВ: сверка обязана покраснеть на ОДНОМ лишнем пробеле.

    ⚠️ ЭТО НЕ ПЕДАНТИЗМ, А ПРЕДМЕТ, РАДИ КОТОРОГО СТОРОЖ И ПИШЕТСЯ. Для SQLite
    предикат частичного индекса есть ТЕКСТ: два написания, отличающиеся
    пробелом, дают ДВА РАЗНЫХ ограничения под одним именем. Сверка, не умеющая
    отличить их, охраняла бы ноль — а заявить её зубы вместо доказательства
    нельзя.
    """
    model_source = MODEL_PY.read_text(encoding="utf-8")
    revision_source = REVISION_PY.read_text(encoding="utf-8")
    assert not _disagreements(model_source, revision_source), (
        "контроль подделкой бессмыслен, пока настоящие источники расходятся"
    )

    tampered = model_source.replace(
        "kind = 'subscription' AND status = 'pending'",
        "kind = 'subscription'  AND status = 'pending'",
        1,
    )
    assert tampered != model_source, "подделка не подменила ни одного вхождения"

    assert _disagreements(tampered, revision_source), (
        "сверка не заметила лишнего пробела в предикате — она охраняет ноль"
    )


def test_this_file_never_imports_the_revision_module():
    """Сторож читает ревизию ТЕКСТОМ и не импортирует её — утверждено разбором.

    Импорт модуля ревизии связал бы тест с порядком накатов и нарушил бы правило
    проекта: ревизии ничего не импортируют и ниоткуда не импортируются. Правило,
    проверяемое только вниманием читателя, однажды нарушат — поэтому оно
    проверяется разбором СОБСТВЕННОГО дерева этого файла.
    """
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    offenders = [name for name in imported if "alembic" in name or "0021" in name]
    assert not offenders, f"модуль ревизии импортирован: {offenders}"


@pytest_asyncio.fixture
async def schema_from_models():
    """База, поднятая ТОЙ ЖЕ конструкцией, что и `tests/conftest.py`.

    Повторяется именно конструкция суиты (`Base.metadata.create_all` на
    `sqlite+aiosqlite:///:memory:`), а не изобретается своя: предмет проверки —
    что потолок есть В ТОЙ САМОЙ схеме, на которой идут все остальные тесты.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def _seed_user(session: AsyncSession) -> User:
    user = User(email="index@t.com", password_hash="h", name="T")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


def _payment(user: User, payment_id: str, *, status: str, kind: str) -> Payment:
    return Payment(
        user_id=user.id,
        yookassa_payment_id=payment_id,
        status=status,
        amount_value="3000.00",
        amount_currency="RUB",
        kind=kind,
        plan=None,
        messages_count=None,
        package_name=None,
    )


@pytest.mark.asyncio
async def test_the_cap_exists_in_the_schema_built_from_models(schema_from_models):
    """Вторая НЕЗАКРЫТАЯ подписочная строка отвергается базой из моделей."""
    session = schema_from_models
    user = await _seed_user(session)
    session.add(_payment(user, "yoo_first", status="pending", kind="subscription"))
    await session.commit()

    session.add(_payment(user, "yoo_second", status="pending", kind="subscription"))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,kind,why",
    [
        (
            "expired",
            "subscription",
            "просроченное намерение обязано остаться оплачиваемым и не запирать "
            "владельца — на этом держится ленивая уборка",
        ),
        (
            "succeeded",
            "subscription",
            "проведённый платёж не намерение: запретив его, потолок отнял бы у "
            "человека вторую покупку доступа навсегда",
        ),
        (
            "pending",
            "package",
            "пакет — другой предмет покупки и другие деньги; предикат берёт "
            "только подписочные намерения",
        ),
    ],
)
async def test_the_index_is_partial_and_lets_the_neighbours_through(
    schema_from_models, status, kind, why
):
    """Соседние строки предикатом НЕ ЗАХВАТЫВАЮТСЯ — по одной причине на каждую."""
    session = schema_from_models
    user = await _seed_user(session)
    session.add(_payment(user, "yoo_open", status="pending", kind="subscription"))
    await session.commit()

    session.add(_payment(user, "yoo_neighbour", status=status, kind=kind))
    await session.commit()

    assert (
        await session.get(Payment, 2)
    ) is not None, f"строка ({status}, {kind}) отвергнута, хотя {why}"

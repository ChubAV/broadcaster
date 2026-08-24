import pytest
from app.database import Base, get_engine


def test_base_has_metadata():
    assert Base.metadata is not None


def test_get_engine_returns_engine():
    engine = get_engine("sqlite+aiosqlite:///test.db")
    assert engine is not None


# =============================================================================
# ЗАМЕНА `lower()`/`upper()` В SQLite (WR-05 ревизии фазы 6)
#
# ⚠️ ЗАМЕНА ЗАВЕДЕНА, ЧТОБЫ УБРАТЬ РАСХОЖДЕНИЕ ДВУХ СУБД, И ОБЯЗАНА НЕ ЗАВОДИТЬ
# НОВОГО. Первая редакция звала `.lower()` на чём угодно: числовой или двоичный
# довод ронял вызов на уровне СУБД — то есть пятисоткой, а не промахом в
# поиске, ради которого замена написана. Утверждения ниже проверяют ОБЕ
# половины: кириллица складывается, а нетекстовый довод ведёт себя как у
# встроенной функции.
# =============================================================================


@pytest.mark.asyncio
async def test_the_case_fold_replacement_behaves_like_the_builtin_it_replaces():
    """Кириллица складывается, а нетекстовый довод не роняет запрос.

    Проверяется на ЖИВОМ соединении, а не вызовом питоновой функции: предмет —
    поведение выражения В ЗАПРОСЕ, и подмена, зарегистрированная неверно, из
    питона выглядела бы работающей.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.connect() as conn:
            async def one(sql: str):
                return (await conn.execute(text(sql))).scalar_one()

            assert await one("select lower('ИВАН')") == "иван", (
                "кириллица не складывается — расхождение с боевой СУБД на "
                "месте, и суита остаётся нечестной моделью продукта"
            )
            assert await one("select upper('иван')") == "ИВАН"

            # Встроенная функция приводит число к тексту; замена обязана вести
            # себя так же, иначе она чинит одно расхождение и заводит второе.
            assert await one("select lower(123)") == "123"
            assert await one("select upper(4.5)") == "4.5"

            # BLOB встроенная читает как текст. `b'ABC'` вместо `'abc'` было бы
            # третьим расхождением подряд.
            assert await one("select lower(x'414243')") == "abc"

            assert await one("select lower(null) is null") == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_the_case_fold_replacement_is_allowed_in_an_index_expression():
    """Замена объявлена ДЕТЕРМИНИРОВАННОЙ и потому годится для индекса.

    ⚠️ ЭТО НЕ ГИПОТЕТИЧЕСКАЯ ПРИДИРКА. Без признака SQLite отвергает функцию в
    выражениях индексов, частичных предикатах, порождаемых колонках и `CHECK`.
    Ревизия, добавляющая `CREATE INDEX … ON users (lower(email))`, падала бы в
    суите, работая в бою, — то есть расхождение двух СУБД вернулось бы через ту
    самую дверь, которую замена и закрывает.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as conn:
            await conn.execute(text("create table t (email text)"))
            await conn.execute(text("create index ix_t_email on t (lower(email))"))
    finally:
        await engine.dispose()

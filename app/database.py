from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


@event.listens_for(Engine, "connect")
def _teach_sqlite_to_fold_unicode_case(dbapi_connection, connection_record):
    """Делает `lower()`/`upper()` в SQLite такими же, как в PostgreSQL.

    ⚠️ ЭТО НЕ ОПТИМИЗАЦИЯ И НЕ УДОБСТВО — ЭТО СВЕДЕНИЕ ДВУХ СУБД К ОДНОМУ
    ОТВЕТУ. Встроенные `lower()`/`upper()` SQLite складывают регистр ТОЛЬКО для
    латиницы: `lower('ИВАН')` возвращает `'ИВАН'`. PostgreSQL складывает юникод.
    Пока это расхождение не закрыто, любой регистронезависимый поиск по русскому
    имени ведёт себя в суите иначе, чем в бою, — и хуже того, ведёт себя иначе
    ТИХО: запрос выполняется, страница отвечает 200, находится просто не всё.
    Тест, написанный на латинских данных, зелен при обоих поведениях и этого
    класса дефектов не видит вовсе (§Pitfall 6 исследования фазы 6).

    ⚠️ НАПРАВЛЕНИЕ ПРАВКИ ИМЕННО ТАКОЕ: тестовая СУБД подтягивается к боевой, а
    не наоборот. Поведение продукта не меняется ни на йоту — меняется только то,
    насколько суита является его честной моделью.

    ПРИЗНАК ВЫБРАН ПО ВОЗМОЖНОСТИ, А НЕ ПО ИМЕНИ ДИАЛЕКТА: `create_function`
    есть у соединения SQLite (и у адаптера aiosqlite, который проксирует вызов
    синхронно) и отсутствует у адаптеров PostgreSQL — проверено на
    `AsyncAdapt_asyncpg_connection`. Сверка по имени драйвера сломалась бы при
    смене драйвера, сверка по возможности — нет.

    ⚠️ ФУНКЦИИ ПЕРЕОПРЕДЕЛЯЮТСЯ ПАРОЙ. Мир, в котором `lower()` знает про
    кириллицу, а `upper()` нет, хуже мира, в котором про неё не знает ни одна:
    расхождение становится невидимым — половина выражений складывает регистр,
    половина нет, и какая именно, читается только по исходнику вызова.
    """
    create_function = getattr(dbapi_connection, "create_function", None)
    if create_function is None:
        return
    create_function("lower", 1, lambda value: value.lower() if value is not None else None)
    create_function("upper", 1, lambda value: value.upper() if value is not None else None)


def get_engine(database_url: str):
    return create_async_engine(database_url, echo=False, pool_pre_ping=True)


def get_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

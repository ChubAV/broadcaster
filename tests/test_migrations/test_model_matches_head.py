"""Отображённые колонки `Payment` против схемы, построенной настоящим Alembic до `head`.

ЗАЧЕМ. Отображённая колонка, у которой нет ревизии, — это не «новая функция не
доедет». ORM-выборка сущности выписывает в `SELECT` ПОЛНЫЙ перечень отображённых
колонок, а не только те, которые читает вызывающий, поэтому на схеме без такой
колонки `UndefinedColumn` поднимают ВСЕ читающие пути таблицы: и раздел «Тарифы»
(`get_payment_history`), и обработчик уведомления ЮKassa — причём последний падает
ДО ветвления по предмету покупки, то есть и для платежа за ПАКЕТ СООБЩЕНИЙ, к
новым колонкам отношения не имеющего. Класс дефекта обязан ловиться машиной здесь,
а не пользователем на боевом стенде.

⚠️ ПОЧЕМУ ОСТАЛЬНАЯ СУИТА ЭТОТ КЛАСС НЕ ЛОВИТ. `tests/conftest.py` строит схему
через `Base.metadata.create_all`, то есть ИЗ МОДЕЛИ. Колонка, объявленная в модели,
появляется в тестовой базе всегда — независимо от того, добавила ли её хоть одна
ревизия. Расхождение модели и очереди ревизий для такой суиты невидимо ПО
ПОСТРОЕНИЮ, и зелёный цвет остальных 56 файлов о нём ничего не говорит.

⚠️ ЧЕГО ЭТОТ ФАЙЛ НЕ ДОКАЗЫВАЕТ — ЧИТАТЬ ОБЯЗАТЕЛЬНО. Он сверяет модель с ГОЛОВНОЙ
РЕВИЗИЕЙ РЕПОЗИТОРИЯ и ни с чем больше. Какая ревизия накачена на БОЕВОЙ базе, он
не знает и знать не может: боевого доступа у суиты нет, схема строится в файле во
временном каталоге. На 2026-08-21 бой проверен `alembic current` и стоит на
`0019`, а репозиторий ушёл на `0020` — это расхождение ЭТИМ ТЕСТОМ НЕ ЛОВИТСЯ, и
опираться на его зелёный цвет как на утверждение о проде ЗАПРЕЩЕНО.

⚠️ ПРЕЖНИЙ ТЕКСТ ЭТОГО АБЗАЦА ГОВОРИЛ ПРО `0012` И РЕШЕНИЕ D-26. Он был верен на
момент написания и перестал быть верным: очередь `0013`…`0019` пройдена. Абзац
ПРАВЛЕН ПОД ФАКТ, а не оставлен со ссылкой на документ — операционное состояние,
названное неверно в файле, который читают перед выкатом, хуже, чем не названное
вовсе. Само состояние живёт в `.planning/STATE.md` и в докстринге ревизии `0020`,
а не здесь.

ТРИ РЕШЕНИЯ, ПОВТОРЁННЫЕ У `test_0019_payment_switch_authorized.py`. Причины
переписаны сюда целиком, а не заменены ссылкой: файл, объясняющий себя ссылкой на
соседа, теряет объяснение при первой же правке соседа.

**Файловая база, а не база в памяти.** Alembic открывает СОБСТВЕННОЕ соединение
(`alembic/env.py` создаёт свой async-движок), а содержимое SQLite, живущей в
оперативной памяти, между соединениями не сохраняется.

**Тест синхронный.** `alembic/env.py` в online-режиме сам вызывает `asyncio.run`;
внутри уже работающего цикла pytest-asyncio это упало бы RuntimeError.

**Стартовая ревизия названа явно и отмечена штампом.** Прогон от нуля на SQLite до
головы не доходит: ревизия `0005` использует `op.drop_constraint`, на котором
Alembic под SQLite поднимает `NotImplementedError`. Это свойство ЧУЖИХ ревизий, к
предмету проверки отношения не имеющее. Поэтому фикстура сама приводит базу в
состояние «схема на ревизии 0019», штампует эту ревизию и запускает
НАСТОЯЩИЙ `command.upgrade` до `head`.

ГРАНИЦА ОБЪЁМА, НАЗВАННАЯ ПРЯМО. Сверяется ОДНА таблица — `payments`, та, чьи
колонки расходятся сегодня. Обобщение на все таблицы модели потребовало бы снимка
каждой из них в состоянии стартовой ревизии — работа своего размера, и её
отсутствие здесь есть решение, а не недосмотр.

⚠️ СНИМОК СТАРТОВОЙ РЕВИЗИИ ШИРЕ ПРОВЕРЯЕМОЙ ТАБЛИЦЫ, И ЭТО НЕ РАСШИРЕНИЕ ПРЕДМЕТА.
Ревизия `0020` правит `subscriptions` и роняет обе таблицы валюты сообщений, а
`upgrade head` идёт ЧЕРЕЗ неё: снимок из одной таблицы платежей оборвал бы прогон
на «нет такой таблицы» — то есть тест падал бы по причине, к расхождению модели с
головой отношения не имеющей. Сверяется по-прежнему ОДНА таблица; в снимке лежит
ровно то, без чего очередь не проходит. Стартовая ревизия поэтому передвинута на
`0019`: снимок описывает схему на ЕЁ момент, и держать здесь второй снимок
`0018`, отличающийся одной колонкой платежей, значило бы завести второе описание
той же схемы.
"""

import sqlite3
from collections.abc import Iterable
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from app.models.payment import Payment

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

START_REVISION = "0019"

# Схема в состоянии стартовой ревизии. Снимок взят у
# `test_0020_flat_subscription.py`: состав колонок сверен по
# `0001_initial_schema.py` (`users`, `subscriptions`),
# `0009_add_message_balance_and_payment_tables.py` (обе таблицы валюты сообщений
# и `payments`), `0010_add_is_unlimited.py`, `0017_payment_kind_and_plan.py`
# (`kind`, `plan`, снятие NOT NULL с `messages_count`),
# `0018_subscriptions_unique_user.py` (частичный уникальный индекс) и
# `0019_payment_switch_authorized.py` (`switch_authorized`).
#
# Таблицы сверх `payments` лежат здесь не ради проверки, а ради ПРОХОДИМОСТИ
# очереди — см. абзац о границе объёма в шапке файла.
SCHEMA_AT_START = """
CREATE TABLE users (
    id INTEGER NOT NULL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE subscriptions (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    expires_at DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX uq_subscriptions_active_user
    ON subscriptions (user_id) WHERE is_active;

CREATE TABLE message_balances (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    balance INTEGER NOT NULL DEFAULT 0,
    free_balance_reset_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_unlimited BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE balance_transactions (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    payment_id VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE payments (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    yookassa_payment_id VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    amount_value VARCHAR(50) NOT NULL,
    amount_currency VARCHAR(10) NOT NULL DEFAULT 'RUB',
    messages_count INTEGER,
    package_name VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    confirmed_at DATETIME,
    kind VARCHAR(50) NOT NULL DEFAULT 'package',
    plan VARCHAR(50),
    switch_authorized BOOLEAN
);
"""


def missing_columns(mapped: Iterable[str], actual: Iterable[str]) -> list[str]:
    """Отображённые колонки, которых нет в схеме, — ПОИМЁННО и по алфавиту.

    Возвращается перечень имён, а не их количество и не булев ответ: «не хватает
    трёх» не говорит, каких, и разбирающему пришлось бы повторять работу
    проверки руками. Порядок отсортирован, чтобы сообщение об ошибке не зависело
    от порядка обхода множества и читалось одинаково в двух прогонах подряд.

    Направление сверки одностороннее и это намеренно: требуется, чтобы каждая
    ОТОБРАЖЁННАЯ колонка существовала в схеме. Обратное включение не требуется —
    колонка, существующая в схеме и не отображённая моделью, ничего не ломает:
    в `SELECT` уезжает перечень модели, а не перечень таблицы.
    """
    return sorted(set(mapped) - set(actual))


def _table_columns(db_path: Path, table: str) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


def _stamped_revision(db_path: Path) -> str | None:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def _repository_head() -> str:
    """Головная ревизия РЕПОЗИТОРИЯ — та, до которой доводит `upgrade head`.

    Читается у каталога ревизий, а не выписывается литералом: литерал устарел бы
    на следующей заведённой ревизии и превратил бы утверждение о достижении
    головы в утверждение о достижении вчерашней головы.
    """
    from alembic.script import ScriptDirectory

    return ScriptDirectory.from_config(Config(str(ALEMBIC_INI))).get_current_head()


@pytest.fixture
def db_at_head(tmp_path: Path, monkeypatch) -> Path:
    """Файловая база, доведённая НАСТОЯЩИМ Alembic до головной ревизии."""
    db_path = tmp_path / "model_vs_head.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_AT_START)
        conn.commit()
    finally:
        conn.close()

    url = f"sqlite+aiosqlite:///{db_path}"
    # `alembic/env.py` предпочитает DATABASE_URL любому значению из alembic.ini.
    # Переменная подменяется ЯВНО: без этого прогон ушёл бы на адрес из окружения
    # разработчика — то есть на живую базу. Тест не имеет права ни читать боевую
    # схему, ни писать в неё.
    monkeypatch.setenv("DATABASE_URL", url)

    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", url)
    command.stamp(config, START_REVISION)
    command.upgrade(config, "head")
    return db_path


def test_the_upgrade_actually_reached_head(db_at_head):
    """Прогон дошёл ДО ГОЛОВЫ, а не остановился по дороге.

    Утверждение обязательное, а не декоративное. Без него парная проверка ниже
    зеленела бы и в случае, когда `upgrade` встал на полпути: недостающая
    колонка нашлась бы «уже применённой» ревизией, до которой прогон дошёл, а
    правка, добавившая несовместимую с SQLite ревизию, прошла бы молча.
    """
    assert _stamped_revision(db_at_head) == _repository_head()


def test_the_check_names_the_missing_column_by_name():
    """НЕГАТИВНЫЙ КОНТРОЛЬ: у сверки есть зубы, и это доказывает машина.

    Подаётся перечень отображённых колонок и тот же перечень без одной. Сверка
    обязана назвать недостающую ПОИМЁННО: сообщение «не хватает одной» не
    говорит, какой, и разбирающему придётся повторять работу проверки руками.

    Тест стоит в суите ПОСТОЯННО, а не выполняется однократно при написании:
    правка, случайно превратившая сверку в тождественно пустую, обязана уронить
    его в тот же прогон, а не через раунд верификации.
    """
    mapped = {column.name for column in Payment.__table__.columns}
    without_one = mapped - {"switch_authorized"}

    assert missing_columns(mapped, without_one) == ["switch_authorized"]


def test_every_mapped_payment_column_exists_at_head(db_at_head):
    """⚠️ ОТОБРАЖЁННАЯ КОЛОНКА БЕЗ РЕВИЗИИ = 500 НА КАЖДОМ ЧТЕНИИ ТАБЛИЦЫ.

    Не «новая функция не доедет»: в `SELECT` уезжает ПОЛНЫЙ перечень отображённых
    колонок, поэтому на схеме без такой колонки отказывают ВСЕ читающие пути
    `payments` — включая обработчик уведомления ЮKassa, который падает ДО
    ветвления по предмету покупки, то есть и для пакетного платежа, к новым
    колонкам отношения не имеющего.

    Сверяется ГОЛОВНАЯ РЕВИЗИЯ РЕПОЗИТОРИЯ. О том, какая ревизия накачена на
    боевой базе (решением D-26 — `0012`), этот тест не знает ничего: см. шапку
    файла.
    """
    mapped = {column.name for column in Payment.__table__.columns}
    actual = _table_columns(db_at_head, "payments")

    absent = missing_columns(mapped, actual)
    assert not absent, (
        "отображены моделью, но не заведены ни одной ревизией до головы: "
        f"{absent}"
    )

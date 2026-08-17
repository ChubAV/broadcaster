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
временном каталоге. Решением владельца D-26 боевая база стоит на `0012`, а
репозиторий ушёл на `0019` — это расхождение ЭТИМ ТЕСТОМ НЕ ЛОВИТСЯ, и опираться
на его зелёный цвет как на утверждение о проде ЗАПРЕЩЕНО. Операционный факт D-26
живёт в `.planning/STATE.md`, а не здесь.

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
состояние «таблица `payments` на ревизии 0018», штампует эту ревизию и запускает
НАСТОЯЩИЙ `command.upgrade` до `head`.

ГРАНИЦА ОБЪЁМА, НАЗВАННАЯ ПРЯМО. Сверяется ОДНА таблица — `payments`, та, чьи
колонки расходятся сегодня. Обобщение на все таблицы модели потребовало бы снимка
каждой из них в состоянии стартовой ревизии — работа своего размера, и её
отсутствие здесь есть решение, а не недосмотр.
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

START_REVISION = "0018"

# Таблица платежей в состоянии стартовой ревизии. Снимок взят у
# `test_0019_payment_switch_authorized.py`: состав колонок сверен по
# `0009_add_message_balance_and_payment_tables.py` (исходная таблица) и
# `0017_payment_kind_and_plan.py` (`kind`, `plan`, снятие NOT NULL с
# `messages_count`). Ревизия `0018` таблицу `payments` не трогает — она про
# `subscriptions`.
PAYMENTS_AT_START = """
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
    plan VARCHAR(50)
);
"""


def missing_columns(mapped: Iterable[str], actual: Iterable[str]) -> list[str]:
    """ЗАГЛУШКА: перечень отображённых колонок, которых нет в схеме.

    Сейчас всегда сообщает «недостающих нет». Существует в таком виде ровно
    столько, сколько нужно негативному контролю ниже, чтобы упасть НА
    УТВЕРЖДЕНИИ: проверка, зелёная при любом входе, неотличима от отсутствующей,
    и отличать их обязана машина, а не память автора.
    """
    return []


def _table_columns(db_path: Path, table: str) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


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

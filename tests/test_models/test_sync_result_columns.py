"""Колонки результата синхронизации: D-11 и D-12 на уровне схемы.

Файл закрепляет три новые nullable-колонки ревизии `0014` — и ровно ту их
форму, на которую опираются планы 03-04 (запись результата) и 03-06 (плашка
сводки):

- `messenger_accounts.last_synced_at` — время последнего синка (D-12);
- `messenger_accounts.last_sync_result` — `Text`, а не `String(N)`: в колонку
  ложится JSON-строка `{"found":…, "new":…, "renamed":…, "missing":…, "error":…}`,
  и текст ошибки мессенджера длину не обещает;
- `groups.missing_since` — пометка «не найдена при последней синхронизации»
  (D-11). Колонка отдельная, а не переиспользованные `last_error`/`error_at`:
  те про ошибки ОТПРАВКИ.

Ключевое утверждение файла — НЕ «колонки существуют», а
`test_new_account_has_no_sync_result` вместе с `test_missing_since_clears_back_to_none`.
Оба состояния обязаны быть отличимы от нуля счётчиков: `last_synced_at IS NULL`
означает «синхронизация ещё НЕ выполнялась» и должен отличаться от «синк дал
ноль групп», а снятая пометка `missing_since IS NULL` — «группа вернулась», а не
«пропала давно». Ревизия целевой базы отстаёт (STATE.md: прод на `0012`),
поэтому NULL — не редкий крайний случай, а состояние всех существующих строк
сразу после выката.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import DateTime, Text, select

from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.user import User


def _as_utc(value: datetime) -> datetime:
    """SQLite не хранит смещение — восстанавливаем UTC для сравнения."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def _reload(db_session, model, pk: int):
    """Перечитывает строку НОВЫМ объектом, а не `refresh` того же.

    Разница не стилистическая. Объект SQLAlchemy остаётся обычным объектом
    Python: присваивание НЕмаппленного имени проходит молча и переживает
    `refresh`, потому что тот обновляет только маппленные колонки. Тест,
    написанный через `refresh`, зеленел бы и БЕЗ колонки в схеме — то есть не
    проверял бы ровно то, ради чего написан. `expunge_all` + повторная выборка
    строят объект из содержимого БД, поэтому отсутствие колонки даёт падение.
    """
    db_session.expunge_all()
    return (
        await db_session.execute(select(model).where(model.id == pk))
    ).scalar_one()


async def _seed_account(db_session, email: str) -> MessengerAccount:
    user = User(email=email, password_hash="hashed", name="Sync User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    account = MessengerAccount(
        user_id=user.id,
        type="wa",
        credentials='{"phone": "+1234567890"}',
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account


async def _seed_group(db_session, account: MessengerAccount) -> Group:
    group = Group(
        user_id=account.user_id,
        account_id=account.id,
        messenger_type=account.type,
        group_external_id="wa_group_1",
        name="Group",
    )
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)
    return group


@pytest.mark.asyncio
async def test_new_account_has_no_sync_result(db_session):
    """Аккаунт до первого синка: обе колонки NULL, а не нули счётчиков."""
    account = await _seed_account(db_session, "never_synced@example.com")

    assert account.last_synced_at is None
    assert account.last_sync_result is None


@pytest.mark.asyncio
async def test_new_group_has_no_missing_since(db_session):
    """Только что созданная группа считается найденной: пометки нет."""
    account = await _seed_account(db_session, "fresh_group@example.com")
    group = await _seed_group(db_session, account)

    assert group.missing_since is None


@pytest.mark.asyncio
async def test_last_synced_at_roundtrips_tz_aware(db_session):
    """Колонка принимает tz-aware datetime и возвращает тот же момент."""
    account = await _seed_account(db_session, "synced_at@example.com")
    moment = datetime.now(timezone.utc) - timedelta(minutes=7)

    account.last_synced_at = moment
    await db_session.commit()
    reloaded = await _reload(db_session, MessengerAccount, account.id)

    assert reloaded.last_synced_at is not None
    assert _as_utc(reloaded.last_synced_at) == moment


@pytest.mark.asyncio
async def test_last_sync_result_accepts_long_text(db_session):
    """Text, а не String(N): текст ошибки мессенджера длину не обещает."""
    account = await _seed_account(db_session, "long_result@example.com")
    payload = "x" * 1500

    account.last_sync_result = payload
    await db_session.commit()
    reloaded = await _reload(db_session, MessengerAccount, account.id)

    assert reloaded.last_sync_result == payload
    assert len(reloaded.last_sync_result) == 1500


@pytest.mark.asyncio
async def test_missing_since_clears_back_to_none(db_session):
    """Пометка ставится синком и снимается им же, когда группа вернулась."""
    account = await _seed_account(db_session, "missing_since@example.com")
    group = await _seed_group(db_session, account)
    group_id = group.id
    marked_at = datetime.now(timezone.utc)

    group.missing_since = marked_at
    await db_session.commit()
    marked = await _reload(db_session, Group, group_id)
    assert marked.missing_since is not None
    assert _as_utc(marked.missing_since) == marked_at

    marked.missing_since = None
    await db_session.commit()
    cleared = await _reload(db_session, Group, group_id)
    assert cleared.missing_since is None


def test_column_types_are_text_and_tz_aware():
    """Форма колонок, которую SQLite не различает, а PostgreSQL различает.

    Тестовая суита идёт на SQLite, где `String(20)` и `Text` неотличимы по
    поведению, а длина не проверяется вовсе. Утверждение о типе поэтому
    снимается с самой таблицы: иначе `last_sync_result` мог бы уехать в
    `String(255)` и обрезать текст ошибки только в проде.
    """
    account_columns = MessengerAccount.__table__.c
    assert isinstance(account_columns.last_sync_result.type, Text)
    assert isinstance(account_columns.last_synced_at.type, DateTime)
    assert account_columns.last_synced_at.type.timezone is True
    assert account_columns.last_synced_at.nullable is True
    assert account_columns.last_sync_result.nullable is True

    missing_since = Group.__table__.c.missing_since
    assert isinstance(missing_since.type, DateTime)
    assert missing_since.type.timezone is True
    assert missing_since.nullable is True

"""Полная переинвентаризация состава групп аккаунта — одна на все три пути.

ПОЧЕМУ ХЕЛПЕР ОДИН. До этой фазы блок синхронизации был скопирован в трёх
местах — страничный TG-обработчик (`app/pages/accounts.py`) и две Celery-таски
WA и MAX (`app/worker/tasks.py`) — и копии уже разошлись посимвольно. Пока
логика сводилась к «добавить недостающие», расхождение было терпимым. Начиная
с D-10/D-11/D-12 она втрое сложнее: обновление имён, пометка пропавших, снятие
пометки у вернувшихся, запись результата на аккаунт. Реализация этого в трёх
копиях означает, что однажды поправят две из трёх, и WA-путь начнёт вести себя
иначе, чем MAX-путь, — молча, без падения тестов. Поэтому логика живёт здесь, а
три места её ВЫЗЫВАЮТ (вызовы — план 03-04).

Смысл «полной переинвентаризации» (D-10): ответ мессенджера — это состав групп
целиком, а не список изменений. Группа, ранее удалённая пользователем вручную,
приходит в ответе и создаётся ЗАНОВО как новая: включённая, без старых связей с
расписаниями. Томбстоунов нет — если группа не нужна, её выключают, а не
удаляют.

ЧЕГО ХЕЛПЕР НЕ ДЕЛАЕТ (D-11, прохибиция плана):
- не удаляет строк: группа, не вернувшаяся из мессенджера, помечается
  `missing_since` и остаётся в списке. Мессенджер может не отдать группу из-за
  собственного сбоя, и удаление по такому сигналу стирало бы данные
  пользователя без его решения;
- не читает и не пишет флаг включённости группы: включённость — выбор
  пользователя, а не свойство ответа мессенджера. Отсутствие этого имени во
  всём модуле — проверяемая форма прохибиции;
- не коммитит: транзакцией управляет вызывающий — страничный обработчик и
  Celery-таска ведут её по-разному.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.accounts.dto import GroupResyncResult
from app.models.group import Group
from app.models.messenger_account import MessengerAccount


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _encode_result(result: GroupResyncResult) -> str:
    """Сериализует счётчики в форму, которую читает сводка синка.

    Ключ `new` соответствует полю `created` DTO — см. комментарий к
    `GroupResyncResult`. `ensure_ascii=False`: в `error` попадает текст ошибки
    мессенджера, и экранирование кириллицы раздувало бы значение вчетверо.
    """
    return json.dumps(
        {
            "found": result.found,
            "new": result.created,
            "renamed": result.renamed,
            "missing": result.missing,
            "error": result.error,
        },
        ensure_ascii=False,
    )


async def apply_group_resync(
    session: AsyncSession,
    account: MessengerAccount,
    fetched: Iterable[Mapping[str, Any]],
    *,
    messenger_type: str,
) -> GroupResyncResult:
    """Приводит состав групп аккаунта к ответу мессенджера.

    `fetched` — последовательность словарей `{"id": ..., "name": ...}` ровно
    того формата, что уже отдают `messenger.get_groups()` и поле `groups`
    ответа `get_sync_status()`. Содержимое НЕДОВЕРЕННОЕ: и идентификатор, и имя
    приходят из внешней системы.

    Не коммитит. Возвращает счётчики и записывает их на аккаунт.
    """
    # Двойной скоуп (T-03-06): внешний идентификатор уникален внутри
    # мессенджера, но не внутри нашей базы — у другого пользователя может
    # лежать группа с тем же group_external_id. Условие по владельцу здесь
    # избыточно ровно до тех пор, пока account передан после проверки владения;
    # оно и стоит на случай, когда это перестанет быть правдой.
    existing_rows = await session.execute(
        select(Group).where(
            Group.account_id == account.id,
            Group.user_id == account.user_id,
        )
    )
    existing: dict[str, Group] = {
        group.group_external_id: group for group in existing_rows.scalars().all()
    }

    created = 0
    renamed = 0
    seen: set[str] = set()

    for item in fetched:
        external_id = item.get("id")
        if external_id is None:
            continue
        external_id = str(external_id)
        if external_id in seen:
            # Дубли внутри одного ответа мессенджера схлопываются: вторая
            # запись про ту же группу не должна порождать вторую строку.
            continue
        seen.add(external_id)

        name = item.get("name") or external_id
        group = existing.get(external_id)

        if group is None:
            session.add(
                Group(
                    user_id=account.user_id,
                    account_id=account.id,
                    messenger_type=messenger_type,
                    group_external_id=external_id,
                    name=name,
                )
            )
            created += 1
            continue

        if group.name != name:
            group.name = name
            renamed += 1
        # Группа вернулась — пометка снимается независимо от того,
        # переименовалась она или нет.
        group.missing_since = None

    missing = 0
    marked_at = _utcnow()
    for external_id, group in existing.items():
        if external_id in seen:
            continue
        missing += 1
        # Время ПЕРВОЙ пропажи не перетирается: подпись «не найдена с …»
        # обязана говорить, когда группа исчезла, а не когда о ней вспомнили в
        # последний раз.
        if group.missing_since is None:
            group.missing_since = marked_at

    result = GroupResyncResult(
        found=len(seen),
        created=created,
        renamed=renamed,
        missing=missing,
        error=None,
    )
    account.last_synced_at = marked_at
    account.last_sync_result = _encode_result(result)
    return result


async def record_sync_failure(
    session: AsyncSession, account: MessengerAccount, message: str
) -> None:
    """Записывает неудавшийся синк той же формой, что и удавшийся.

    Счётчики нулевые, `error` — текст сообщения. Эта форма позволяет планам
    03-04 и 03-06 показать ошибку синка вместо сводки, не заводя второй
    колонки и не гадая по отсутствию значения. Не коммитит.
    """
    account.last_synced_at = _utcnow()
    account.last_sync_result = _encode_result(
        GroupResyncResult(found=0, created=0, renamed=0, missing=0, error=message)
    )


def parse_sync_result(raw: str | None) -> dict | None:
    """Читает `last_sync_result` с защитой от мусора.

    Возвращает `None` на пустом значении, невалидном JSON и несловарном
    верхнем уровне — и НИКОГДА не поднимает исключения (T-03-08). Значение
    пишется только кодом, но плашка результата обязана деградировать в
    отсутствие плашки, а не в стек-трейс на экране групп: строка в колонке
    может оказаться оборванной на полуслове или написанной прежней версией
    формата.
    """
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload

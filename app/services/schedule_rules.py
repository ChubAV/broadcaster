"""Правила расписания, общие для страничного и JSON-входа.

Модуль НЕЙТРАЛЕН: от него зависят оба слоя, а сам он не зависит ни от одного из
них. Направление зависимости здесь не украшение архитектуры, а прямое следствие
причины, по которой модуль появился: правило, живущее на одном входе и
отсутствующее на другом, расходится молча. Так разъехались определение полноты
расписания (страничный тумблер требовал аккаунт И группы И дни И времена,
API-тумблер — только аккаунт, WR-05 при том что D-08 требует ОДНОГО определения)
и правило владения группами (страничный слой сводил `group_ids` к своим,
JSON-API писал их дословно, CR-02 / T-02G-06).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group


def is_schedule_complete(
    account_id: int | None,
    group_ids: list[int],
    days_of_week: list[int],
    times_of_day: list[str],
) -> bool:
    """D-08: заполнено ли расписание настолько, чтобы его можно было включить.

    Одно определение на все обработчики обоих входов и на разметку карточки
    (app/templates/ads/includes/sched_card.html): второе разъехалось бы с
    первым, и пользователь видел бы бейдж «Не заполнено» на расписании, которое
    сервер считает полным.
    """
    return bool(account_id and group_ids and days_of_week and times_of_day)


async def owned_group_ids(
    db: AsyncSession,
    user_id: int,
    account_id: int | None,
    group_ids: list[int],
) -> set[int]:
    """Подмножество `group_ids`, принадлежащее пользователю И этому аккаунту.

    Ровно то правило, которое страничный слой уже применяет через
    `_groups_of_account`, поднятое на уровень, доступный обоим входам. Оно
    двойное намеренно: связки по владельцу мало, потому что расписание не может
    нести группы другого аккаунта — иначе своя группа чужого канала уехала бы в
    рассылку, для которой она не подключена.

    Пустой аккаунт (законное состояние отвязанного расписания, issue #35) не
    даёт групп вовсе: групп «без аккаунта» не существует.
    """
    if account_id is None or not group_ids:
        return set()
    rows = await db.execute(
        select(Group.id).where(
            Group.id.in_(group_ids),
            Group.user_id == user_id,
            Group.account_id == account_id,
        )
    )
    return set(rows.scalars().all())

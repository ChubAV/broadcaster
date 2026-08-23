"""Показатели «Обзора», которые НЕ считает модуль аналитики отправок.

ГРАНИЦЫ МОДУЛЯ (по образцу `queue_rows.py` и `users_query.py`). Модуль знает про
запрос к базе и не знает ни про Jinja, ни про `Request`, ни про подписи плиток:
он отдаёт числа. Права администратора проверяет обработчик.

ЧЕГО ЗДЕСЬ НЕТ И БЫТЬ НЕ ДОЛЖНО — СЧЁТА ОТПРАВОК. Он живёт в модуле аналитики
(`app/application/analytics/send_analytics.py`) и приезжает на «Обзор» оттуда,
потому что на тот же вопрос отвечает пользовательский дашборд, и второй счёт
рядом означал бы два разных числа об одном периоде (D-35 Фазы 4, D-39). Здесь —
только те величины, о которых аналитика отправок не знает: люди и деньги.

ПОЧЕМУ МОДУЛЬ ВООБЩЕ ЗАВЕДЁН, А ВЫРАЖЕНИЯ НЕ ОСТАЛИСЬ В ОБРАБОТЧИКЕ. Пока
агрегат стоит в страничном модуле, «не заводить там второй счёт отправок»
остаётся правилом, которое исполняет человек. Вынеся ВСЕ агрегаты в прикладной
слой, запрет становится проверяемым свойством: страничный модуль админки не
импортирует конструктор SQL-функций вовсе, и добавить туда агрегат нельзя, не
уронив `test_the_admin_pages_module_builds_no_aggregate_over_the_send_journal`.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.subscription import Subscription
from app.models.user import User
from app.repositories.user import paying_subscription_clauses

# Ширина окна прироста пользователей — НЕДЕЛЯ, и число живёт здесь одно. Подпись
# плитки собирается из него же: выписанная в разметке «за неделю» рядом с иным
# окном была бы подписью, называющей не то, что посчитано.
NEW_USERS_WINDOW = timedelta(days=7)


@dataclass(frozen=True, slots=True)
class UserTotals:
    """Люди: сколько всего и сколько пришло за окно прироста."""

    total: int
    joined_in_window: int


async def user_totals(session: AsyncSession, *, now: datetime) -> UserTotals:
    """Всего пользователей и прирост за неделю — ОДНИМ обращением к базе.

    Прирост считается по `User.created_at` — единственной колонке момента
    регистрации, которую даёт схема. Второе обращение ради второго числа
    удвоило бы поход в базу на пути рендера страницы, которую открывают в
    момент аварии; условный агрегат даёт оба числа одной строкой — тот же приём,
    которым модуль аналитики берёт оба окна плиток.
    """
    row = (
        await session.execute(
            select(
                func.count(User.id),
                func.sum(case((User.created_at >= now - NEW_USERS_WINDOW, 1), else_=0)),
            )
        )
    ).one()
    # `func.sum` над пустым набором отдаёт NULL, а плитка обязана показать ноль,
    # а не пустоту.
    return UserTotals(total=int(row[0] or 0), joined_in_window=int(row[1] or 0))


async def paying_total(session: AsyncSession, *, now: datetime) -> int:
    """Число ПЛАТЯЩИХ подписок — по трём условиям, а не по двум (D-38).

    ⚠️ УСЛОВИЯ ПРИХОДЯТ ИЗ СЛОЯ ДОСТУПА К ДАННЫМ, А НЕ ВЫПИСАНЫ ЗДЕСЬ, и это не
    вкус раскладки. Третье из них читает признак бесплатного доступа, а в
    `app/application/` его читает РОВНО ОДИН файл — предикат доступа; правило
    машинное (`test_the_free_access_flag_is_read_in_exactly_one_place_of_the_decision`),
    и вторая копия здесь развела бы одно правило по двум выражениям. Ровно тот
    же довод уже записан над осью доступа админского списка
    (`app/repositories/user.py`), и она лежит там по той же причине.

    Смысл третьего условия — в нём вся плитка: у пользователя с бесплатным
    доступом дверь открыта, а денег нет, и счёт из двух условий превратил бы
    административную льготу в выручку.
    """
    return (
        await session.execute(
            select(func.count(Subscription.id)).where(
                *paying_subscription_clauses(now)
            )
        )
    ).scalar() or 0


async def account_counts_by_user(
    session: AsyncSession, user_ids: list[int]
) -> dict[int, int]:
    """Число мессенджер-аккаунтов перечисленных пользователей — ОДНИМ запросом.

    ⚠️ ОДИН ЗАПРОС НА СПИСОК, А НЕ ЗАПРОС НА СТРОКУ. Колонка на строку,
    посчитанная запросом на строку, стоит числа обращений, растущего вместе с
    числом зарегистрированных, — а страница администратора видит их всех сразу.

    Пустой список НЕ ходит в базу: `IN ()` — синтаксическая ошибка на части
    диалектов и бессмысленный запрос на остальных.
    """
    if not user_ids:
        return {}

    rows = await session.execute(
        select(MessengerAccount.user_id, func.count(MessengerAccount.id))
        .where(MessengerAccount.user_id.in_(user_ids))
        .group_by(MessengerAccount.user_id)
    )
    return {row[0]: row[1] for row in rows.all()}


@dataclass(frozen=True, slots=True)
class UserCardCounts:
    """Числа карточки пользователя: объявления и группы."""

    ads: int
    groups: int


async def user_card_counts(session: AsyncSession, user_id: int) -> UserCardCounts:
    """Сколько у пользователя объявлений и групп — ДВУМЯ счётами.

    Объединять их одним запросом через join нельзя: строки объявлений и групп
    перемножились бы, и оба числа стали бы произведением. Два точных счёта
    честнее одного быстрого и неверного.
    """
    ads = (
        await session.execute(select(func.count(Ad.id)).where(Ad.user_id == user_id))
    ).scalar() or 0
    groups = (
        await session.execute(
            select(func.count(Group.id)).where(Group.user_id == user_id)
        )
    ).scalar() or 0
    return UserCardCounts(ads=ads, groups=groups)

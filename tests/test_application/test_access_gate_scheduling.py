"""Гейт доступа на ПУТИ ОТПРАВКИ — самой дорогой из трёх поверхностей отказа.

ЗАЧЕМ ОТДЕЛЬНЫЙ ФАЙЛ, А НЕ ДОПИСКА В `test_scheduling_use_cases.py`. Тот файл
проверяет ПОДБОР расписаний — какие задачи собираются и как устроена их сборка;
здесь проверяется, что подбор СПРАШИВАЕТ ВЕРДИКТ ДОСТУПА и что следует из
отказа. Пропуск гейта на страницах стоит человеку одного экрана, пропуск на
JSON-API — обхода авторизации, а пропуск ЗДЕСЬ означает, что истёкший доступ
продолжает рассылать по расписанию: деньги, которые продукт не берёт, при
работе, которую он выполняет.

СОБСТВЕННЫЙ ДВИЖОК, А НЕ ФИКСТУРА `db_session`, — приём взят у соседа
(`tests/test_application/test_scheduling_use_cases.py:23-27`). Причина та же:
`collect_due_schedules` работает с сессией напрямую и ПИШЕТ в неё
(`next_run_at`), а посев здесь нужен точный — до строки подписки включительно.

⚠️ ФАЙЛ УТВЕРЖДАЕТ ОБА СЛЕДСТВИЯ ОТКАЗА, А НЕ ОДНО. Пустой список задач говорит
только «не отправили». Сдвиг `next_run_at` вперёд говорит второе и не менее
важное: расписание ЖИВО, оно сохранено и перенесено, а не удалено и не
выключено. Прекращение доступа не имеет права уничтожать пользовательские данные
или делать их недостижимыми — после оплаты рассылка обязана возобновиться сама,
без единого действия человека над расписаниями.
"""
import contextlib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.analytics.send_analytics import normalize_utc
from app.application.scheduling.use_cases import collect_due_schedules
from app.constants import AD_STATUS_PUBLISHED
from app.database import Base
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.subscription import Subscription
from app.models.user import User
from app.services.billing_cache import check_access_cached
from app.services.subscription_service import check_access


@contextlib.asynccontextmanager
async def _session_with_user(*, expires_in_days: int | None):
    """Сессия на своём движке и пользователь с УПРАВЛЯЕМЫМ сроком доступа.

    `expires_in_days=None` означает «строки подписки нет вовсе» — состояние,
    которое переживёт выкат (популяция П-о-1) и обязано иметь определённый
    вердикт, а не исключение на середине цикла планировщика.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    try:
        async with session_factory() as session:
            user = User(email="u@test.com", password_hash="x", name="U")
            session.add(user)
            await session.commit()

            if expires_in_days is not None:
                session.add(
                    Subscription(
                        user_id=user.id,
                        expires_at=datetime.now(timezone.utc)
                        + timedelta(days=expires_in_days),
                        is_active=True,
                    )
                )
                await session.commit()

            yield session, user
    finally:
        await engine.dispose()


async def _seed_due_schedule(session: AsyncSession, user: User) -> Schedule:
    """Расписание, срок которого УЖЕ наступил, со всей живой тройкой под ним."""
    ad = Ad(
        user_id=user.id,
        title="T",
        text="Body",
        images=[],
        status=AD_STATUS_PUBLISHED,
    )
    account = MessengerAccount(
        user_id=user.id, type="tg_user", credentials="sess", status="active"
    )
    session.add_all([ad, account])
    await session.commit()

    group = Group(
        user_id=user.id,
        account_id=account.id,
        messenger_type="telegram",
        group_external_id="-100",
        name="G",
    )
    session.add(group)
    await session.commit()

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[group.id],
        days_of_week=[0, 1, 2, 3, 4, 5, 6],
        times_of_day=["00:00", "06:00", "12:00", "18:00"],
        is_active=True,
        next_run_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        timezone="UTC",
    )
    session.add(schedule)
    await session.commit()
    return schedule


@contextlib.contextmanager
def _no_redis():
    """Redis в тестовой среде нет, и вердикт обязан считаться без него.

    Подмена стоит на `_get_redis`, а не на клиенте: настоящий
    `redis.asyncio.from_url` объект СОЗДАЁТ (соединение ленивое) и падал бы
    только на первом обращении — то есть тест зависел бы от того, поднят ли на
    машине разработчика Redis, и на боевом стенде вёл бы себя иначе, чем в CI.

    Настройки подменяются рядом по той же причине, что и в
    `tests/test_billing_cache.py`: у файла своего приложения нет, а `Settings()`
    из окружения процесса собрать нельзя — тест краснел бы отсутствием `.env`,
    то есть чужой причиной.
    """
    settings = MagicMock()
    settings.redis_url = "redis://localhost:6379/0"
    settings.billing_cache_ttl = 60
    with patch("app.services.billing_cache._get_redis", return_value=None):
        with patch("app.services.billing_cache.get_settings", return_value=settings):
            yield


# =============================================================================
# Вердикт доступа — `check_access`
# =============================================================================


@pytest.mark.asyncio
async def test_a_live_period_opens_access():
    """Живой срок открывает доступ и причины отказа не называет."""
    async with _session_with_user(expires_in_days=3) as (session, user):
        assert await check_access(session, user.id) == (True, "")


@pytest.mark.asyncio
async def test_an_expired_period_closes_access_with_a_named_reason():
    """Истёкший срок закрывает доступ, и отказ НАЗВАН, а не молчалив.

    Причина — короткая строка журнального свойства, а не текст для экрана: слова
    пользователю рисует разметка из закрытого множества (UI-контракт E2), и
    вторая формулировка того же отказа разъехалась бы с первой. Но пустой она
    быть не имеет права: журнал воркера — единственное место, где отказ вообще
    виден, отправки-то не происходит.
    """
    async with _session_with_user(expires_in_days=-1) as (session, user):
        allowed, reason = await check_access(session, user.id)

    assert allowed is False
    assert reason, "отказ пути отправки не оставил в журнале ни слова о причине"


@pytest.mark.asyncio
async def test_a_user_without_a_subscription_row_is_refused_and_not_raised_at():
    """Отсутствие строки подписки — ОПРЕДЕЛЁННЫЙ вердикт, а не исключение.

    Такой пользователь существует сегодня и переживёт выкат (П-о-1). Исключение
    здесь уронило бы весь такт планировщика — то есть отказ ОДНОГО пользователя
    остановил бы рассылку ВСЕМ остальным.
    """
    async with _session_with_user(expires_in_days=None) as (session, user):
        allowed, reason = await check_access(session, user.id)

    assert allowed is False
    assert reason


# =============================================================================
# Следствие отказа для планировщика — `collect_due_schedules`
# =============================================================================


@pytest.mark.asyncio
async def test_an_expired_user_dispatches_nothing_and_keeps_the_schedule():
    """Просроченный не рассылает — и его расписание ПЕРЕНОСИТСЯ, а не пропадает.

    ⚠️ ДВА УТВЕРЖДЕНИЯ, И ВТОРОЕ НЕ ДЕКОРАЦИЯ. Пустой список говорит «не
    отправили»; сдвиг `next_run_at` вперёд говорит «расписание живо». Реализация,
    удаляющая или выключающая расписание просроченного, прошла бы первое
    утверждение и провалила второе — а именно она и нарушала бы прохибицию
    «прекращение доступа не уничтожает данные пользователя».
    """
    async with _session_with_user(expires_in_days=-1) as (session, user):
        schedule = await _seed_due_schedule(session, user)
        was_due_at = schedule.next_run_at

        with _no_redis():
            tasks = await collect_due_schedules(
                session,
                now=datetime.now(timezone.utc),
                check_limit=check_access_cached,
            )

        assert tasks == [], "истёкший доступ продолжает рассылать по расписанию"

        await session.refresh(schedule)
        assert schedule.is_active is True, "отказ выключил расписание пользователя"
        # Оба момента через `normalize_utc` (Pattern 3): колонка объявлена
        # `DateTime(timezone=True)`, но SQLite отдаёт её NAIVE, а PostgreSQL —
        # aware. Сравнение без приведения падает TypeError ровно на одном из двух
        # диалектов, то есть у пользователя, а не в суите.
        assert normalize_utc(schedule.next_run_at) > normalize_utc(was_due_at), (
            "срок следующего запуска не сдвинут вперёд — расписание выстрелит "
            "всеми накопленными слотами сразу, как только доступ вернётся"
        )


@pytest.mark.asyncio
async def test_a_user_with_a_live_period_still_dispatches():
    """Граница сверху: внутри живого срока те же задачи собираются.

    Без этого утверждения гейт, отказывающий ВСЕМ, прошёл бы проверку выше.
    """
    async with _session_with_user(expires_in_days=3) as (session, user):
        await _seed_due_schedule(session, user)

        with _no_redis():
            tasks = await collect_due_schedules(
                session,
                now=datetime.now(timezone.utc),
                check_limit=check_access_cached,
            )

        assert tasks, "живой доступ не собрал ни одной задачи отправки"

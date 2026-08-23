"""Платёжные величины и журнал админского подраздела «Платежи» (ADMIN-10).

⚠️ ГЛАВНОЕ УТВЕРЖДЕНИЕ ФАЙЛА — ПРО ТРЕТЬЕ УСЛОВИЕ ВЫРУЧКИ, И ОНО ПРОВЕРЯЕТСЯ
ДВАЖДЫ НАМЕРЕННО (D-38, §Pitfall 11). Первый тест сеет всю популяцию разом и
требует, чтобы выручку дал РОВНО ОДИН платящий; второй берёт льготного с ЖИВОЙ
датой окончания отдельно. Второй не следует из первого: слив условий «активна» и
«срок жив» в два вместо трёх ловится только льготным, чей срок ЖИВ, — у
льготного с мёртвой датой его отсекает срок, и тест из одной популяции остался
бы зелёным при накрученной выручке. Цена ошибки названа в решении прямо:
административная льгота показалась бы деньгами в отчёте, по которому принимают
решение о цене.

⚠️ ВТОРОЕ УТВЕРЖДЕНИЕ — ПРО ОТБОР НЕЗАКРЫТЫХ ПЛАТЕЖЕЙ ПО ОТСУТСТВИЮ
ТЕРМИНАЛЬНОГО СТАТУСА, а не по равенству одному (§Pitfall 12). Оно написано
ТРЕТЬИМ, НИКОГДА НЕ ВСТРЕЧАВШИМСЯ статусом: проверка на `pending` прошла бы и
при условии `status == "pending"`, то есть не проверяла бы ничего из того, ради
чего множество терминальных статусов вообще объявлено. Строка, отобранная по
равенству, исчезла бы из журнала ровно в тот день, когда платёжный провайдер
заведёт четвёртый статус, — и заметить это было бы некому.

⚠️ ТРЕТЬЕ — ПРО СЧЁТ, РАВНЫЙ СОДЕРЖИМОМУ. Число над журналом и строки под ним
приходят из одного набора условий; разойдясь, они дают администратору «найдено
12» и одиннадцать строк — тот самый дефект, за который проект уже платил в
разделе истории.
"""
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.admin.overview_stats import monthly_revenue, paying_total
from app.application.admin.payments_query import (
    EXPIRED_LOOKBACK_DAYS,
    PAYMENT_PERIOD_CHIPS,
    PAYMENT_PERIOD_VALUES,
    PAYMENT_STATUS_CHIPS,
    PAYMENT_STATUS_VALUES,
    apply_payment_filters,
    expired_not_renewed,
    payment_ledger,
)
from app.constants import PAYMENT_LIST_CAP
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.services.payment_service import (
    KIND_SUBSCRIPTION,
    STATUS_CANCELED,
    STATUS_PENDING,
    STATUS_SUCCEEDED,
)

# ⚠️ МОМЕНТ НАСТОЯЩИЙ, А НЕ ЗАФИКСИРОВАННЫЙ ДАТОЙ В ИСХОДНИКЕ. Все сроки ниже
# заданы СМЕЩЕНИЯМИ от него: дата, выписанная литералом, сделала бы «живую»
# подписку просроченной ровно тогда, когда до неё дойдёт календарь, и тест
# позеленел бы навсегда на ветке, ради которой не написан.
NOW = datetime.now(timezone.utc)

# Цена в той же форме, в какой её хранит настройка: машинная строка формата
# платёжного API. Разбор её — работа проверяемого кода, а не теста.
PRICE = "3000.00"

# ⚠️ ТРЕТИЙ, НИКОГДА НЕ ВСТРЕЧАВШИЙСЯ СТАТУС. Значение взято у платёжного
# провайдера (ЮKassa объявляет `waiting_for_capture` между созданием и
# подтверждением), но здесь важно не оно, а то, что проект о нём НЕ ЗНАЕТ:
# в `TERMINAL_STATUSES` его нет, в ветках обработчика вебхука — тоже. Строка с
# ним обязана попасть в журнал незакрытых по построению условия, а не потому,
# что кто-то вспомнил дописать её в перечень.
STATUS_THIRD_PARTY_NON_TERMINAL = "waiting_for_capture"


async def _seed_user(session: AsyncSession, email: str) -> User:
    user = User(
        email=email,
        password_hash=f"ХЕШ-ПАРОЛЯ-{email}-НЕ-ДОЛЖЕН-ПОПАСТЬ-В-РАЗМЕТКУ",
        name=f"Пользователь {email}",
        created_at=NOW - timedelta(days=365),
    )
    session.add(user)
    await session.flush()
    return user


async def _seed_subscription(
    session: AsyncSession,
    user: User,
    *,
    expires_at: datetime,
    is_active: bool = True,
    has_free_access: bool = False,
) -> None:
    session.add(
        Subscription(
            user_id=user.id,
            expires_at=expires_at,
            is_active=is_active,
            has_free_access=has_free_access,
        )
    )


_ids = iter(range(1, 100_000))


async def _seed_payment(
    session: AsyncSession,
    user: User,
    *,
    status: str = STATUS_SUCCEEDED,
    created_at: datetime | None = None,
    amount: str = PRICE,
    kind: str = KIND_SUBSCRIPTION,
    plan: str | None = None,
    package_name: str | None = None,
) -> Payment:
    payment = Payment(
        user_id=user.id,
        yookassa_payment_id=f"yoo-{next(_ids)}",
        status=status,
        amount_value=amount,
        kind=kind,
        plan=plan,
        package_name=package_name,
        created_at=created_at if created_at is not None else NOW,
    )
    session.add(payment)
    await session.flush()
    return payment


async def _revenue(session: AsyncSession) -> object:
    """Выручка ровно тем путём, которым её читает подраздел.

    ⚠️ ВЕЛИЧИНА НЕ ПЕРЕСЧИТЫВАЕТСЯ ЗДЕСЬ ВТОРЫМ ВЫРАЖЕНИЕМ. Тест обязан
    проверять ту цепочку, которую видит администратор: счёт платящих по трём
    условиям и умножение его на цену. Своя копия арифметики зеленела бы вместе
    с собственной ошибкой.
    """
    return monthly_revenue(await paying_total(session, now=NOW), PRICE)


# ---- Выручка: три условия, а не два (D-38, Pitfall 11) ----------------------


@pytest.mark.asyncio
async def test_mrr_counts_only_the_paying_subscription_of_the_whole_population(
    db_session: AsyncSession,
):
    """Платящий, льготный, истёкший и деактивированный → цена, умноженная на ЕДИНИЦУ.

    Популяция посеяна целиком именно затем, чтобы утверждение было про ОТБОР, а
    не про арифметику: любое из трёх условий, потерянное реализацией, поднимает
    результат выше цены, и тест называет, на сколько именно.
    """
    paying = await _seed_user(db_session, "paying@test.com")
    comped = await _seed_user(db_session, "comped@test.com")
    expired = await _seed_user(db_session, "expired@test.com")
    inactive = await _seed_user(db_session, "inactive@test.com")

    await _seed_subscription(db_session, paying, expires_at=NOW + timedelta(days=10))
    await _seed_subscription(
        db_session, comped, expires_at=NOW + timedelta(days=10), has_free_access=True
    )
    await _seed_subscription(db_session, expired, expires_at=NOW - timedelta(days=10))
    await _seed_subscription(
        db_session, inactive, expires_at=NOW + timedelta(days=10), is_active=False
    )
    await db_session.commit()

    assert await _revenue(db_session) == Decimal(PRICE)


@pytest.mark.asyncio
async def test_mrr_excludes_the_comped_user_whose_term_is_still_alive(
    db_session: AsyncSession,
):
    """Льготный с ЖИВОЙ датой окончания в выручку не входит — отдельный случай.

    ⚠️ ТЕСТ НЕ СЛЕДУЕТ ИЗ ПРЕДЫДУЩЕГО. Реализация из двух условий («активна» и
    «срок жив») проходит первый тест на льготном с мёртвой датой и падает
    только здесь: у этого человека дверь открыта администратором, денег он не
    платил, и посчитанный вместе с платящими он превращает льготу в выручку.
    """
    comped = await _seed_user(db_session, "comped-live@test.com")
    await _seed_subscription(
        db_session, comped, expires_at=NOW + timedelta(days=90), has_free_access=True
    )
    await db_session.commit()

    assert await _revenue(db_session) == Decimal("0")


@pytest.mark.asyncio
async def test_mrr_of_an_empty_base_is_zero_and_not_an_exception(
    db_session: AsyncSession,
):
    """Пустая база даёт ноль, а не отказ подраздела.

    Пустая база — состояние ПЕРВОГО дня продукта и любого свежего стенда.
    Отказ здесь означал бы админку, которую нельзя открыть, пока не появился
    первый платящий.
    """
    assert await _revenue(db_session) == Decimal("0")


# ---- Ушедшие: величина называет ровно то, что считает (D-41) ----------------


@pytest.mark.asyncio
async def test_expired_not_renewed_counts_the_dead_term_without_a_later_payment(
    db_session: AsyncSession,
):
    """Дата окончания в прошлом за окно и НИ ОДНОГО успешного платежа после неё.

    Три соседа в популяции отсекаются по трём разным причинам, и каждая
    названа: живой срок — не ушёл; мёртвый срок СТАРШЕ окна — ушёл давно и в
    величину окна не входит; льготный — платить и не должен был.
    """
    lapsed = await _seed_user(db_session, "lapsed@test.com")
    alive = await _seed_user(db_session, "alive@test.com")
    long_gone = await _seed_user(db_session, "long-gone@test.com")
    comped = await _seed_user(db_session, "comped-dead@test.com")

    await _seed_subscription(db_session, lapsed, expires_at=NOW - timedelta(days=3))
    await _seed_subscription(db_session, alive, expires_at=NOW + timedelta(days=3))
    await _seed_subscription(
        db_session,
        long_gone,
        expires_at=NOW - timedelta(days=EXPIRED_LOOKBACK_DAYS + 5),
    )
    await _seed_subscription(
        db_session, comped, expires_at=NOW - timedelta(days=3), has_free_access=True
    )
    await db_session.commit()

    assert await expired_not_renewed(db_session, now=NOW) == 1


@pytest.mark.asyncio
async def test_expired_not_renewed_skips_the_user_who_paid_after_the_term_died(
    db_session: AsyncSession,
):
    """Заплатил ПОСЛЕ даты окончания — не ушёл, сколько бы ни было мёртвых строк.

    ⚠️ ПРОДЛЕНИЕ ЖИВЁТ ТОЛЬКО В ЖУРНАЛЕ ПЛАТЕЖЕЙ (D-41). Строка подписки
    сдвигает свою дату и истории не хранит, поэтому «продлил ли он» — вопрос к
    `Payment`, а не к `Subscription`. Отклонённый платёж продлением НЕ является
    и человека из величины не забирает: деньги не пришли.
    """
    renewed = await _seed_user(db_session, "renewed@test.com")
    refused = await _seed_user(db_session, "refused@test.com")

    await _seed_subscription(db_session, renewed, expires_at=NOW - timedelta(days=5))
    await _seed_subscription(db_session, refused, expires_at=NOW - timedelta(days=5))
    await _seed_payment(
        db_session, renewed, status=STATUS_SUCCEEDED, created_at=NOW - timedelta(days=1)
    )
    await _seed_payment(
        db_session, refused, status=STATUS_CANCELED, created_at=NOW - timedelta(days=1)
    )
    await db_session.commit()

    assert await expired_not_renewed(db_session, now=NOW) == 1


# ---- Журнал: фильтры, счёт, потолок, санация --------------------------------


@pytest.mark.asyncio
async def test_the_ledger_count_equals_its_own_content_under_the_same_filters(
    db_session: AsyncSession,
):
    """Число над журналом равно тому, что в журнале лежит (D-34, форма проверки).

    Сравниваются НЕ два независимых вызова, а счёт и содержимое ОДНОЙ выдачи:
    раздельные выражения для списка и его счёта уже давали в проекте «показано
    не то, что посчитано».
    """
    user = await _seed_user(db_session, "ledger@test.com")
    await _seed_payment(db_session, user, status=STATUS_SUCCEEDED)
    await _seed_payment(db_session, user, status=STATUS_SUCCEEDED)
    await _seed_payment(db_session, user, status=STATUS_CANCELED)
    await _seed_payment(
        db_session,
        user,
        status=STATUS_SUCCEEDED,
        created_at=NOW - timedelta(days=200),
    )
    await db_session.commit()

    all_rows = await payment_ledger(db_session, now=NOW)
    assert all_rows.total == 4 == len(all_rows.rows)

    succeeded = await payment_ledger(db_session, status="succeeded", now=NOW)
    assert succeeded.total == 3 == len(succeeded.rows)

    recent = await payment_ledger(db_session, period="30d", now=NOW)
    assert recent.total == 3 == len(recent.rows)

    both = await payment_ledger(
        db_session, status="succeeded", period="30d", now=NOW
    )
    assert both.total == 2 == len(both.rows)


@pytest.mark.asyncio
async def test_the_ledger_selects_unclosed_payments_by_the_absence_of_a_terminal_status(
    db_session: AsyncSession,
):
    """Третий, никогда не встречавшийся статус попадает в «незакрытые» САМ.

    ⚠️ УЛИКА ИМЕННО В ТРЕТЬЕМ СТАТУСЕ. Проверка на `pending` прошла бы и при
    условии `status == "pending"` — то есть не сказала бы ничего о том, ради
    чего множество терминальных статусов объявлено. Строка, отобранная
    равенством, исчезла бы из журнала в тот день, когда платёжный провайдер
    заведёт четвёртый статус, и залипший платёж перестал бы быть видимым ровно
    тогда, когда за ним и приходят.
    """
    user = await _seed_user(db_session, "unclosed@test.com")
    await _seed_payment(db_session, user, status=STATUS_PENDING)
    await _seed_payment(db_session, user, status=STATUS_THIRD_PARTY_NON_TERMINAL)
    await _seed_payment(db_session, user, status=STATUS_SUCCEEDED)
    await _seed_payment(db_session, user, status=STATUS_CANCELED)
    await db_session.commit()

    unclosed = await payment_ledger(db_session, status="unclosed", now=NOW)

    assert unclosed.total == 2 == len(unclosed.rows)
    assert {row.status for row in unclosed.rows} == {
        STATUS_PENDING,
        STATUS_THIRD_PARTY_NON_TERMINAL,
    }


@pytest.mark.asyncio
async def test_the_ledger_cap_truncates_and_reports_its_own_firing(
    db_session: AsyncSession,
):
    """Усечение видно ОТДЕЛЬНЫМ полем, а не выводится из длины списка.

    ⚠️ ПРИЗНАК НЕ ВЫВОДИМ ИЗ ДЛИНЫ ВЫДАЧИ: ровно на потолке список полон, и
    «показано не всё» стало бы неотличимо от «столько и есть». Поэтому
    сравнивается ОБЩЕЕ число с потолком, и признак приезжает своим полем.

    Потолок подменяется на маленький вместо посева двух сотен строк: предмет
    утверждения — арифметика усечения, а не скорость вставки. Что значение
    берётся у проекта, а не назначено здесь, проверяет соседний тест.
    """
    user = await _seed_user(db_session, "cap@test.com")
    for offset in range(5):
        await _seed_payment(
            db_session, user, created_at=NOW - timedelta(minutes=offset)
        )
    await db_session.commit()

    with patch("app.application.admin.payments_query.PAYMENT_LIST_CAP", 3):
        capped = await payment_ledger(db_session, now=NOW)

    assert capped.total == 5
    assert len(capped.rows) == 3
    assert capped.truncated is True
    assert capped.cap == 3

    full = await payment_ledger(db_session, now=NOW)
    assert full.truncated is False
    assert full.cap == PAYMENT_LIST_CAP


@pytest.mark.asyncio
async def test_the_ledger_cap_is_the_value_the_project_already_declared(
    db_session: AsyncSession,
):
    """Потолок ВЗЯТ у проекта, а не назначен здесь вторым числом.

    Комментарий объявления прямо называет этот подраздел потребителем значения
    (`app/constants.py`), и второе число разошлось бы с первым молча: раздел
    пользователя и подраздел администратора показывали бы разные «последние N».
    """
    from app.application.admin import payments_query

    assert payments_query.PAYMENT_LIST_CAP == PAYMENT_LIST_CAP


@pytest.mark.asyncio
async def test_a_value_outside_the_declared_axis_means_all_and_never_reaches_the_query(
    db_session: AsyncSession,
):
    """Мусор в оси = «фильтр не применён», и в выражение он не попадает ВОВСЕ.

    ⚠️ ДВА УТВЕРЖДЕНИЯ, И ВТОРОЕ СИЛЬНЕЕ ПЕРВОГО. Совпадение выдачи с
    нефильтрованной говорит только о поведении; отсутствие подложенной строки в
    скомпилированном тексте запроса говорит, что значение не доехало до
    выражения ни сырым, ни экранированным. Значение приезжает строкой адреса —
    из ссылки, закладки или чужого сообщения (T-06-PAY3).
    """
    user = await _seed_user(db_session, "junk@test.com")
    await _seed_payment(db_session, user, status=STATUS_SUCCEEDED)
    await _seed_payment(db_session, user, status=STATUS_CANCELED)
    await db_session.commit()

    junk = "succeeded' OR 1=1 --"

    assert junk not in PAYMENT_STATUS_VALUES
    assert junk not in PAYMENT_PERIOD_VALUES

    poisoned = await payment_ledger(db_session, status=junk, period=junk, now=NOW)
    clean = await payment_ledger(db_session, now=NOW)

    assert poisoned.total == clean.total == 2

    statement = apply_payment_filters(
        select(Payment.id), status=junk, period=junk, now=NOW
    )
    rendered = str(statement.compile(compile_kwargs={"literal_binds": True}))
    assert junk not in rendered
    assert "1=1" not in rendered


@pytest.mark.asyncio
async def test_every_moment_that_leaves_the_ledger_carries_its_timezone(
    db_session: AsyncSession,
):
    """Моменты из базы приведены к единой зоне — тест зелёный на СУБД суиты.

    ⚠️ УТВЕРЖДЕНИЕ СУЩЕСТВУЕТ ИМЕННО ИЗ-ЗА РАСХОЖДЕНИЯ ДИАЛЕКТОВ. Колонка
    объявлена с таймзоной, но SQLite отдаёт её НАИВНОЙ, а PostgreSQL — с зоной.
    Сравнение наивного с осведомлённым поднимает TypeError, поэтому дефект,
    оставленный здесь, существовал бы ровно на одном из двух диалектов и ловился
    бы не суитой, а администратором.
    """
    user = await _seed_user(db_session, "tz@test.com")
    await _seed_payment(db_session, user, created_at=NOW - timedelta(hours=2))
    await _seed_payment(db_session, user, created_at=NOW - timedelta(days=2))
    await db_session.commit()

    ledger = await payment_ledger(db_session, now=NOW)

    assert ledger.rows
    for row in ledger.rows:
        assert row.created_at is not None
        assert row.created_at.tzinfo is not None, (
            "момент уехал из журнала наивным: на SQLite он сравнится с "
            "осведомлённым только исключением"
        )


# ---- Оси объявлены один раз, а множества выведены из объявления -------------


def test_the_axis_values_are_derived_from_the_declaration_and_not_rewritten():
    """Допустимые значения выведены ИЗ чипсов, а не выписаны вторым перечнем.

    Выписанный второй раз перечень — ровно тот способ, которым чипс переживает
    снятие своего условия: подпись рисуется, значение принимается, выражения за
    ним нет, и экран при этом исправен на вид.
    """
    assert PAYMENT_STATUS_VALUES == frozenset(
        value for value, _ in PAYMENT_STATUS_CHIPS if value
    )
    assert PAYMENT_PERIOD_VALUES == frozenset(
        value for value, _ in PAYMENT_PERIOD_CHIPS if value
    )
    # Вариант «все» есть у ОБЕИХ осей и значения не несёт: без него снять
    # фильтр можно было бы только правкой адреса руками.
    assert "" in {value for value, _ in PAYMENT_STATUS_CHIPS}
    assert "" in {value for value, _ in PAYMENT_PERIOD_CHIPS}


def test_the_module_never_names_the_metrics_that_the_decision_threw_out():
    """Ни средней величины платежа, ни доли ушедших в модуле нет (D-41).

    Гейт читает ИСХОДНИК: обе величины отброшены решением по существу, и
    вернуться они могут только вместе со своим именем. Проверяется текст, а не
    объявления, — величина, заведённая «пока в комментарии», ловится тоже.
    """
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "application"
        / "admin"
        / "payments_query.py"
    ).read_text(encoding="utf-8")

    found = re.findall(r"arpu|ARPU|churn", source)
    assert found == [], (
        f"снятые решением величины вернулись в модуль: {found} — средняя "
        "величина платежа при единственной цене тождественно равна ей, а доли "
        "ушедших подписка без истории продлений честно не даёт (D-41)"
    )

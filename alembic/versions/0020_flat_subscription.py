"""Плоская подписка: снятие тарифа, снятие валюты сообщений, бесплатный доступ

ЗАЧЕМ. Продукт перешёл на ОДИН предмет продажи — срок доступа (D-A, D-D, D-F).
Тарифов Free/Basic/Pro не существует ни в одной ветке решения с плана `05.1-07`,
валюта сообщений снята с пути отправки планом `05.1-06`, и в схеме остались три
предмета, которые больше никто не читает: колонка тарифа подписки и две таблицы
учёта сообщений. Ревизия приводит схему к тому, что код уже делает, и заводит
колонку признака бесплатного доступа, читателей которой вводит план `05.1-09`.

⚠️ ГДЕ ОНА В ОЧЕРЕДИ — ЕДИНСТВЕННОЙ НЕВЫКАЧЕННОЙ. Боевая база проверена
`alembic current` 2026-08-21 и стоит на ревизии `0019` — то есть на ТЕКУЩЕЙ
голове репозитория. Очередь невыкаченных ПУСТА, и `0020` встаёт в неё первой и
единственной: она применится на ближайшем же выкате, а не «когда-нибудь, когда
очередь прогонят».

⚠️ ЭТО РАСХОДИТСЯ С ЗАПИСЬЮ В ПЛАНИРОВОЧНЫХ ДОКУМЕНТАХ, И ВЕРЕН ЗДЕСЬ ФАКТ, А НЕ
ЗАПИСЬ. `.planning/STATE.md` и докстринги ревизий `0018`/`0019` говорят, что бой
стоит на `0012` и невыкачены семь ревизий (решение D-26). На 2026-08-21 это уже
неправда: очередь `0013`…`0019` пройдена. Число из документа сюда не переписано
намеренно — конвенция проекта требует, чтобы ревизия называла своё место в
очереди, и парный тест это утверждение ЗАКРЕПЛЯЕТ; неверное число он закрепил бы
как правду.

⚠️ ТРИ ПОТЕРИ, КОТОРЫЕ ОТКАТ НЕ ВЕРНЁТ, — ПОИМЁННО.

  1. ТАРИФ КАЖДОЙ ПОДПИСКИ. Откат возвращает колонку, но со значением
     бесплатного тарифа у КАЖДОЙ строки, включая тех, кто платил: какой у кого
     был тариф, ревизия нигде не сохраняет.
  2. ТАБЛИЦА БАЛАНСОВ СООБЩЕНИЙ (`message_balances`) — сколько сообщений и у
     кого было куплено.
  3. ТАБЛИЦА ЖУРНАЛА ОПЕРАЦИЙ ПО ОСТАТКУ (`balance_transactions`) — весь журнал
     начислений и списаний.

Ни (2), ни (3) не выводимы из журнала платежей: в `payments` нет колонки под
количество СПИСАННЫХ сообщений — только под купленное в одной сделке. Откат
создаст ДВЕ ПУСТЫЕ таблицы. Смягчающее обстоятельство названо владельцем при
принятии решения: сообщения в новой модели бесплатны у всех, поэтому
неизрасходованный купленный остаток теряет ПОКУПАТЕЛЬНУЮ ценность — утрачивается
учётная история, а не оплаченное благо.

ЖУРНАЛ ПЛАТЕЖЕЙ НЕ ТРОГАЕТСЯ НИ ОДНОЙ ОПЕРАЦИЕЙ (решение D-H). Что и по какой
цене было продано, остаётся записанным: колонки `kind`, `plan`, `messages_count`,
`package_name` и `amount_value` таблицы `payments` эта ревизия не видит вовсе, а
исторические строки не переименовываются. Колонка `payments.plan` — ЖУРНАЛЬНАЯ, и
её совпадение по имени со снимаемой колонкой подписки не делает их одним
предметом.

⚠️ ГРАНИЦА СРОКА ЗАКРЫТА В ПОЛЬЗУ ИСТЕЧЕНИЯ. Строка, у которой `expires_at` РАВЕН
моменту исполнения ревизии, считается ИСТЁКШЕЙ, а не действующей. Это не выбор
вкуса: `subscription_is_live` сравнивает СТРОГО (`app/application/billing/
subscription_period.py`), и ревизия, разошедшаяся с предикатом на строгости, дала
бы человеку, чья секунда совпала с миграцией, один ответ от миграции и
противоположный от продукта.

⚠️ «ДАТА МИГРАЦИИ» РЕШЕНИЯ D-G — ЭТО МОМЕНТ ИСПОЛНЕНИЯ ЭТОЙ РЕВИЗИИ, А НЕ ДЕНЬ
ВЫКАТА КОДА И НЕ ДЕНЬ, КОГДА ЭТОТ ФАЙЛ НАПИСАН. Поэтому отсчёт идёт от
`datetime.now(timezone.utc)`, снятого ВНУТРИ `upgrade`, и захардкоженной даты в
файле нет ни одной. Ревизия, несущая дату литералом, выдала бы при накате через
месяц пробный срок, кончившийся до наката.

ПОРЯДОК В НАКАТЕ НЕСУЩИЙ. Сначала ТРИ операции над данными по колонке тарифа,
и только потом её снятие: уронив колонку первой, отличить бесплатного подписчика
от платящего было бы НЕЧЕМ, и это необратимо.

ТРИ ПОПУЛЯЦИИ И ЧТО С НИМИ ДЕЛАЕТСЯ (решение D-G):

  * П-о-3 — активная строка с ПЛАТНЫМ тарифом: срок НЕ трогается, в том числе
    если он уже в прошлом («переносится без пересчёта»). Операция над данными
    здесь нулевая, но число таких строк уходит в журнал: молчание о популяции
    неотличимо от того, что её забыли.
  * П-о-2 — активная строка с БЕСПЛАТНЫМ тарифом: срок переставляется на
    `TRIAL_DAYS` от момента исполнения.
  * П-о-1 — пользователи БЕЗ активной строки подписки: им ВСТАВЛЯЕТСЯ активная
    строка со сроком `TRIAL_DAYS` от момента исполнения. Их ЧИСЛО НЕНУЛЕВОЕ и в
    норме составляет большинство: до плоской модели строка заводилась только
    подтверждённым платежом. Без этой операции выкат мгновенно отрезал бы от
    продукта почти всех, а административный тумблер плана `05.1-09` получил бы
    пользователя, у которого нечего переключать.

П-о-2 ИСПОЛНЯЕТСЯ ДО П-о-1, И ЭТО РЕШЕНИЕ, А НЕ ПОРЯДОК ЧТЕНИЯ. Вставка идёт с
бесплатным тарифом, поэтому исполненная первой она попала бы под условие
обновления сама — число в журнале перестало бы быть свидетельством о ПРЕЖНЕЙ
популяции и стало бы суммой прежней и созданной ревизией. Исход по данным от
перестановки не меняется; меняется правдивость следа.

⚠️ БУЛЕВЫ ЗНАЧЕНИЯ ЗАПИСЫВАЮТСЯ КЛЮЧЕВЫМ СЛОВОМ, НИКОГДА НУЛЁМ ИЛИ ЕДИНИЦЕЙ. На
PostgreSQL `is_active` — настоящий boolean, и целочисленный литерал он не
принимает; тестовая суита идёт по SQLite и этот дефект пропустила бы, а ревизия
оборвалась бы прямо на выкате. Тот же урок выписан в ревизиях `0015` и `0018`.

BATCH_ALTER_TABLE ЗДЕСЬ НЕ ПРИМЕНЯЕТСЯ, И ЭТО УТВЕРЖДЕНИЕ, А НЕ УМОЛЧАНИЕ.
PostgreSQL снимает колонку нативно; SQLite умеет `DROP COLUMN` с версии 3.35 (в
окружении 3.53), и колонка тарифа не участвует ни в одном индексе — частичный
уникальный `uq_subscriptions_active_user` построен по `user_id`. Batch-режим
пересоздавал бы таблицу подписок целиком — лишний риск на таблице, которую эта же
ревизия и правит.

Литералы имён таблиц и колонок выписаны ЗДЕСЬ строками и НЕ импортированы из
`app.models` — правило ревизий `0013`/`0014`/`0017`/`0018`/`0019`: ревизия
описывает схему на СВОЙ момент времени, и переименование атрибута задним числом
не имеет права изменить смысл давно выполненного шага.

Revision ID: 0020
Revises: 0019
"""
import logging
from datetime import datetime, timedelta, timezone

from alembic import op
import sqlalchemy as sa

revision = "0020"
down_revision = "0019"

TABLE_SUBSCRIPTIONS = "subscriptions"
TABLE_MESSAGE_BALANCES = "message_balances"
TABLE_BALANCE_TRANSACTIONS = "balance_transactions"

COLUMN_PLAN = "plan"
COLUMN_FREE_ACCESS = "has_free_access"

# Имя бесплатного тарифа — умолчание колонки с ревизии `0001`. Оно и есть
# признак, по которому П-о-2 отличается от П-о-3, и после снятия колонки этого
# признака не станет ни в одном месте базы.
FREE_PLAN = "free"

# Длина пробного срока. ЛИТЕРАЛ, А НЕ ИМПОРТ `app.constants.TRIAL_DAYS`: правка
# константы приложения завтра не имеет права изменить смысл шага, выполненного на
# бою сегодня. Значение сверено с `app/constants.py` на момент написания ревизии.
TRIAL_DAYS = 5

logger = logging.getLogger("alembic.runtime.migration")

# П-о-3 — платящие. Операции над данными НЕТ: срок переносится как есть. Считается
# ровно то, что не тронуто, чтобы в журнале стояло число, а не молчание.
_COUNT_PAID_CARRIED_OVER = sa.text(
    f"""
    SELECT COUNT(*) FROM {TABLE_SUBSCRIPTIONS}
    WHERE is_active AND {COLUMN_PLAN} <> '{FREE_PLAN}'
    """
)

# П-о-2 — активные бесплатные. Срок переставляется на окно от момента исполнения.
_RESET_FREE_EXPIRY = sa.text(
    f"""
    UPDATE {TABLE_SUBSCRIPTIONS} SET expires_at = :trial_expires_at
    WHERE is_active AND {COLUMN_PLAN} = '{FREE_PLAN}'
    """
)

# П-о-1 — пользователи без АКТИВНОЙ строки. Условие смотрит на `is_active`, а не
# на срок: строка деактивированной истории у пользователя быть может, а второй
# АКТИВНОЙ строки не допускает `uq_subscriptions_active_user` (ревизия `0018`).
# Вставка, проверяющая срок вместо активности, налетела бы на этот индекс у
# каждого, чей единственный активный период уже кончился.
#
# `is_active` пишется КЛЮЧЕВЫМ СЛОВОМ. Колонка тарифа перечислена ЯВНО, хотя у
# неё есть умолчание: полагаться на умолчание схемы в шаге, который эту же
# колонку через две операции снимает, значит зависеть от того, чего вот-вот не
# станет.
_INSERT_MISSING_SUBSCRIPTIONS = sa.text(
    f"""
    INSERT INTO {TABLE_SUBSCRIPTIONS} (user_id, {COLUMN_PLAN}, expires_at, is_active)
    SELECT u.id, '{FREE_PLAN}', :trial_expires_at, true
    FROM users AS u
    WHERE NOT EXISTS (
        SELECT 1 FROM {TABLE_SUBSCRIPTIONS} AS s
        WHERE s.user_id = u.id AND s.is_active
    )
    """
)


def upgrade():
    connection = op.get_bind()

    # МОМЕНТ ИСПОЛНЕНИЯ СНИМАЕТСЯ ОДИН РАЗ И ПЕРЕДАЁТСЯ ПАРАМЕТРОМ ВО ВСЕ
    # ОПЕРАЦИИ. Два обращения к часам дали бы двум популяциям разные сроки —
    # расхождение маленькое, необъяснимое и навсегда.
    now = datetime.now(timezone.utc)
    trial_expires_at = now + timedelta(days=TRIAL_DAYS)

    carried_over = connection.execute(_COUNT_PAID_CARRIED_OVER).scalar() or 0
    logger.info(
        "0020: %s paid active subscription row(s) carried over UNTOUCHED — their "
        "expires_at is preserved without recalculation, including dates already "
        "in the past (D-G). After this revision the plan they were bought on is "
        "NOT RECOVERABLE.",
        carried_over,
    )

    result = connection.execute(
        _RESET_FREE_EXPIRY, {"trial_expires_at": trial_expires_at}
    )
    reset = result.rowcount if result.rowcount is not None else -1
    logger.info(
        "0020: %s free-plan active subscription row(s) moved to %s (%s days from "
        "the moment this revision ran). THE PREVIOUS expires_at OF THESE ROWS IS "
        "NOT RECOVERABLE.",
        reset,
        trial_expires_at.isoformat(),
        TRIAL_DAYS,
    )

    result = connection.execute(
        _INSERT_MISSING_SUBSCRIPTIONS, {"trial_expires_at": trial_expires_at}
    )
    inserted = result.rowcount if result.rowcount is not None else -1
    logger.info(
        "0020: %s user(s) had no active subscription row and were given one "
        "expiring %s. Without this backfill the deploy would have closed the "
        "product to them the same minute. THIS IS NOT REVERSIBLE.",
        inserted,
        trial_expires_at.isoformat(),
    )

    # Колонка признака бесплатного доступа. Форма взята у ревизии `0010`: булева,
    # не допускает пустого значения, умолчание соответствует ЛЖИ. Читателей у неё
    # в этой ревизии не появляется — предикат, шелл и админские поверхности
    # вводит план `05.1-09`.
    op.add_column(
        TABLE_SUBSCRIPTIONS,
        sa.Column(
            COLUMN_FREE_ACCESS, sa.Boolean(), nullable=False, server_default="0"
        ),
    )

    # ⚠️ ТОЧКА НЕВОЗВРАТА ПО ДАННЫМ. Всё, что отличало платящего от бесплатного,
    # кончается здесь.
    op.drop_column(TABLE_SUBSCRIPTIONS, COLUMN_PLAN)

    # Порядок снятия зеркалит `downgrade` ревизии `0009`, которая эти таблицы
    # завела: журнал операций, потом сами балансы.
    op.drop_table(TABLE_BALANCE_TRANSACTIONS)
    op.drop_table(TABLE_MESSAGE_BALANCES)


def downgrade():
    """Возвращает СХЕМУ. Не возвращает НИ ОДНОГО из трёх утраченных значений.

    Откат намеренно НЕ ПРИТВОРЯЕТСЯ СИММЕТРИЧНЫМ — тот же класс, что `0013` и
    `0018`. Колонка тарифа возвращается у ВСЕХ строк со значением бесплатного
    тарифа, включая плативших; обе таблицы валюты сообщений возвращаются ПУСТЫМИ.
    Сроки, переставленные накатом, остаются переставленными, а строки, вставленные
    накатом популяции без подписки, остаются вставленными: какие именно строки
    ревизия тронула и завела, она нигде не сохраняет.

    СОСТАВ КОЛОНОК ДВУХ ТАБЛИЦ ВОССТАНАВЛИВАЕТСЯ НА МОМЕНТ `0019`, А НЕ `0009`.
    Это на одну колонку больше, чем в ревизии, их заводившей: `is_unlimited`
    добавлена в `message_balances` ревизией `0010`. Откат, вернувший состав
    `0009`, оставил бы базу в состоянии, которого в истории проекта не
    существовало ни секунды.
    """
    op.create_table(
        TABLE_MESSAGE_BALANCES,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            unique=True,
            index=True,
            nullable=False,
        ),
        sa.Column("balance", sa.Integer, nullable=False, server_default="0"),
        sa.Column("free_balance_reset_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # Добавлена ревизией `0010` — см. абзац о составе колонок выше.
        sa.Column("is_unlimited", sa.Boolean, nullable=False, server_default="0"),
    )

    op.create_table(
        TABLE_BALANCE_TRANSACTIONS,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("balance_after", sa.Integer, nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("payment_id", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.add_column(
        TABLE_SUBSCRIPTIONS,
        sa.Column(
            COLUMN_PLAN,
            sa.String(50),
            nullable=False,
            server_default=FREE_PLAN,
        ),
    )
    op.drop_column(TABLE_SUBSCRIPTIONS, COLUMN_FREE_ACCESS)

    logger.warning(
        "0020 downgrade: schema restored, DATA IS NOT. Three things are gone for "
        "good: (1) the plan of every subscription — the column comes back with "
        "'%s' in EVERY row, paying customers included; (2) table %s — how many "
        "messages each user had bought; (3) table %s — the whole journal of "
        "credits and deductions. Neither (2) nor (3) is derivable from %s: there "
        "is no column there for the number of messages SPENT. Both tables come "
        "back EMPTY.",
        FREE_PLAN,
        TABLE_MESSAGE_BALANCES,
        TABLE_BALANCE_TRANSACTIONS,
        "payments",
    )

from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.models.message_balance import MessageBalance
from app.models.balance_transaction import BalanceTransaction
from app.models.payment import Payment

logger = structlog.get_logger()


async def get_or_create_balance(db: AsyncSession, user_id: int) -> MessageBalance:
    result = await db.execute(
        select(MessageBalance).where(MessageBalance.user_id == user_id)
    )
    balance = result.scalar_one_or_none()
    if balance is None:
        balance = MessageBalance(user_id=user_id, balance=0)
        db.add(balance)
        await db.flush()
    return balance


async def get_balance(db: AsyncSession, user_id: int) -> int:
    bal = await get_or_create_balance(db, user_id)
    return bal.balance


async def check_balance(db: AsyncSession, user_id: int) -> tuple[bool, str]:
    bal = await get_or_create_balance(db, user_id)
    if bal.is_unlimited:
        return True, ""
    if bal.balance <= 0:
        return False, "Баланс сообщений исчерпан. Пополните баланс для продолжения отправки."
    return True, ""


async def deduct_message(db: AsyncSession, user_id: int) -> bool:
    """Atomically deduct 1 message. Returns True if deducted, False if insufficient."""
    bal = await get_or_create_balance(db, user_id)
    if bal.is_unlimited:
        return True
    result = await db.execute(
        update(MessageBalance)
        .where(MessageBalance.user_id == user_id, MessageBalance.balance > 0)
        .values(balance=MessageBalance.balance - 1)
        .returning(MessageBalance.balance)
    )
    row = result.first()
    if row is None:
        return False

    new_balance = row[0]
    tx = BalanceTransaction(
        user_id=user_id,
        amount=-1,
        balance_after=new_balance,
        type="send_deduction",
    )
    db.add(tx)
    return True


async def add_messages(
    db: AsyncSession,
    user_id: int,
    amount: int,
    type: str,
    description: str | None = None,
    payment_id: str | None = None,
) -> int:
    """Начисляет сообщения на баланс. Возвращает новый баланс.

    ПРИРАЩЕНИЕ СЧИТАЕТ СУБД, А НЕ PYTHON (T-05-36). Прежняя пара
    «прочитали строку → прибавили в Python → записали» теряла одно из двух
    наложившихся начислений: обе стороны читали одно и то же старое значение и
    обе записывали своё, затирая чужое. Выражение `balance + amount` считается
    на стороне СУБД внутри одного оператора, поэтому потерять запись НЕЧЕМ —
    это недостижимость, а не малая вероятность.

    `get_or_create_balance` остаётся: строка баланса обязана существовать до
    приращения, иначе UPDATE не заденет ни одной строки.

    ПОДПИСЬ И ВОЗВРАЩАЕМОЕ ЗНАЧЕНИЕ НЕ МЕНЯЮТСЯ — у функции есть другие
    вызывающие (`app/pages/admin.py`), и ключевое слово `type` тоже остаётся
    прежним намеренно (IN-01): его переименование правит все вызовы и к защите
    от двойного начисления отношения не имеет.
    """
    bal = await get_or_create_balance(db, user_id)

    result = await db.execute(
        update(MessageBalance)
        .where(MessageBalance.user_id == user_id)
        .values(balance=MessageBalance.balance + amount)
        .returning(MessageBalance.balance)
        .execution_options(synchronize_session=False)
    )
    new_balance = result.scalar_one()

    # Значение ставится как ЗАГРУЖЕННОЕ, а не присваиванием: присваивание
    # пометило бы объект грязным, и ORM выдала бы на flush второй UPDATE — то
    # есть прибавила бы `amount` ещё раз поверх уже посчитанного СУБД.
    set_committed_value(bal, "balance", new_balance)

    tx = BalanceTransaction(
        user_id=user_id,
        amount=amount,
        balance_after=new_balance,
        type=type,
        description=description,
        payment_id=payment_id,
    )
    db.add(tx)
    await db.flush()
    return new_balance


async def get_balance_info(db: AsyncSession, user_id: int) -> dict:
    bal = await get_or_create_balance(db, user_id)
    return {
        "balance": bal.balance,
        "is_unlimited": bal.is_unlimited,
        "free_balance_reset_at": bal.free_balance_reset_at.isoformat() if bal.free_balance_reset_at else None,
    }


# --- Журнал платежей ----------------------------------------------------------
#
# ЖУРНАЛ РАЗДЕЛА ОСТАЛСЯ ОДИН, И ЭТО ЖУРНАЛ ДЕНЕГ (D-14). Второй журнал —
# читатель операций по остатку сообщений — снят вместе со своим единственным
# входом: JSON-маршрута, который его звал, больше нет, а сама величина снимается
# этой же волной. Рублёвая сумма есть только у `Payment`, и критерий фазы
# требует показать пользователю именно её.


async def get_payment_history(
    db: AsyncSession, user_id: int, limit: int
) -> list[Payment]:
    """Платежи владельца, свежие сверху, не больше `limit` записей.

    ВОЗВРАЩАЮТСЯ СТРОКИ МОДЕЛИ, А НЕ СЛОВАРИ С `isoformat()`, в отличие от
    соседнего `get_transaction_history`. Тот отдаёт словари, потому что его
    читает JSON-маршрут; этот читает ТОЛЬКО разметка, а разметка форматирует
    дату существующим глобалом в зоне пользователя и требует настоящий
    `datetime`. Строка ISO пришлось бы разбирать обратно — то есть завести
    второй формат даты в проекте ради одного шаблона.

    ⚠️ СОРТИРОВКА ПО ДАТЕ, НИКОГДА ПО СУММЕ. `amount_value` объявлена СТРОКОЙ:
    ЮKassa оперирует decimal-строками, и хранение во `float` теряло бы копейки.
    Строковое сравнение поставило бы «999.00» выше «1490.00» — порядок выглядел
    бы правдоподобно и был бы неверен. Арифметики по суммам фазе не нужно вовсе:
    BILL-07 требует только показа.

    ВЛАДЕНИЕ — ПРЕДИКАТ ЗАПРОСА (T-05-20). Чужие платежи не приезжают
    вызывающему вовсе, поэтому забытый фильтр в шаблоне не может показать чужой
    денежный журнал.
    """
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == user_id)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def count_payments(db: AsyncSession, user_id: int) -> int:
    """Сколько всего платежей у владельца — БЕЗ выборки самих записей.

    Существует ради потолка: он обязан проверяться ДО конструирования списка и
    называть себя пользователю, а не обрезать молча. Вывести срабатывание из
    длины уже обрезанного списка нельзя — ровно на потолке список полон, и
    «показано не всё» неотличимо от «столько и есть».
    """
    return int(
        await db.scalar(
            select(func.count()).select_from(Payment).where(Payment.user_id == user_id)
        )
        or 0
    )


async def count_succeeded_subscription_payments(db: AsyncSession, user_id: int) -> int:
    """Сколько раз владелец РЕАЛЬНО оплатил доступ — без выборки записей.

    Отвечает ровно на один вопрос экрана подписки: «платил ли этот человек
    когда-нибудь». Пробный период отличается от оплаченного ТОЛЬКО этим
    признаком — оба срока живые, и по дате они неразличимы.

    ⚠️ СЧИТАЮТСЯ ТОЛЬКО ЗАВЕРШЁННЫЕ УСПЕХОМ И ТОЛЬКО ПОДПИСОЧНЫЕ. Намерение в
    статусе «в обработке» сделкой не является: человек, ушедший на страницу
    ЮKassa и отказавшийся платить, оставляет после себя строку — и, попади она
    в счёт, экран сообщил бы ему «подписка оплачена» о платеже, которого не
    было. Покупка пакета сообщений доступа не продлевает вовсе и в счёт не
    входит по тому же основанию.

    ПРЕДИКАТ ЗАПРОСА, А НЕ ФИЛЬТР В ПАМЯТИ: журнал платежей у долгоживущего
    аккаунта длиннее потолка выгрузки, и считать признак по УЖЕ ОБРЕЗАННОМУ
    списку значило бы получить «никогда не платил» у того, кто платил давно.
    """
    # ИМПОРТ ВНУТРИ ФУНКЦИИ — РАЗРЫВ ЦИКЛА, А НЕ НЕБРЕЖНОСТЬ: `payment_service`
    # импортирует `add_messages` из этого модуля, и встречный импорт на уровне
    # модуля дал бы ImportError на старте приложения. Своих литералов вида и
    # статуса здесь не заводится — они КОНСТАНТЫ (WR-04), и вторая их копия
    # разошлась бы с оригиналом молча: подписочный платёж перестал бы считаться,
    # а экран сообщил бы «пробный период» человеку, который платит третий месяц.
    from app.services.payment_service import KIND_SUBSCRIPTION, STATUS_SUCCEEDED

    return int(
        await db.scalar(
            select(func.count())
            .select_from(Payment)
            .where(
                Payment.user_id == user_id,
                Payment.kind == KIND_SUBSCRIPTION,
                Payment.status == STATUS_SUCCEEDED,
            )
        )
        or 0
    )

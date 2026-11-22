"""Захват номера при подключении WhatsApp и MAX поверх единственного писателя Фазы 16 (D-01, D-05, D-10).

Помощник вызывают два опросчика статуса подключения: WA (план 19-05) и MAX
(план 19-07). Номер пишет ТОЛЬКО `fill_reported_phone` — условный оператор «если
номера ещё нет и он не ручной»; этот модуль сам в колонку не пишет.

ТРАНЗАКЦИЕЙ ВЛАДЕЕТ ОБРАБОТЧИК. Помощник открывает только вложенную
транзакцию-сейвпоинт (образец `app/services/subscription_service.py`) и не
коммитит: номер и переход аккаунта в `syncing` уходят одним коммитом обработчика
(D-01). Сбой внутри захвата откатывает ровно сейвпоинт и подключение не ломает
(D-05): общий `except Exception` опросчика превратил бы его в «Ошибку соединения»
и вечный `connecting`.

ПОРЯДОК ИСТОЧНИКОВ (D-10): сначала номер, который сообщил сам мессенджер
(`reported_phone`); запасной, введённый человеком в форме (`entered_phone`),
пробуется только если первый — мусор (`UNPARSEABLE`). При `WRITTEN`, `KEPT` и
`MISSING` запасной не трогается: «ввёл A, отсканировал B» пишет B. Признак
«указан вручную» здесь не ставится ни в одном исходе.

ЖУРНАЛ БЕЗ ЗНАЧЕНИЯ (D-07, PHONE-21): `connect_phone_captured` несёт `account_id`
и `outcome`, `connect_phone_capture_failed` — `account_id` и `error_type`. Номер,
тело ответа воркера и текст исключения в журнал не попадают.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.accounts.phone import PhoneWrite, fill_reported_phone

logger = structlog.get_logger(__name__)


async def capture_connect_phone(
    session: AsyncSession,
    account_id: int,
    reported_phone: object,
    entered_phone: object = None,
) -> PhoneWrite | None:
    """Записать номер нового аккаунта в сейвпоинте; `None` — сбой захвата, он проглочен.

    Внешняя транзакция остаётся живой и в сбое: откатывается только сейвпоинт.
    """
    try:
        async with session.begin_nested():
            outcome = await fill_reported_phone(session, account_id, reported_phone)
            if outcome is PhoneWrite.UNPARSEABLE and entered_phone is not None:
                outcome = await fill_reported_phone(session, account_id, entered_phone)
    except Exception as exc:
        logger.warning(
            "connect_phone_capture_failed",
            account_id=account_id,
            error_type=type(exc).__name__,
        )
        return None
    logger.info("connect_phone_captured", account_id=account_id, outcome=outcome.value)
    return outcome

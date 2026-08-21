import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value
from yookassa import Configuration, Payment as YooPayment
from yookassa.domain.notification import WebhookNotificationEventType

from app.application.analytics.send_analytics import normalize_utc
from app.application.billing.subscription_period import (
    next_expiry,
    subscription_is_live,
)
from app.config import get_settings
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.services.billing_cache import invalidate_access_cache

logger = structlog.get_logger()

# Предметы покупки. Строки живут здесь, потому что их читает и пишет один этот
# модуль; ревизия 0017 выписывает свои копии отдельно и намеренно (правило 0013).
KIND_PACKAGE = "package"
KIND_SUBSCRIPTION = "subscription"

STATUS_PENDING = "pending"
STATUS_SUCCEEDED = "succeeded"
STATUS_CANCELED = "canceled"

# ТЕРМИНАЛЬНЫЕ СТАТУСЫ — те, из которых платёж больше не выходит. Их два, и
# защита от повторной обработки написана через это множество, а не через
# перечисление в каждой ветке: копия в ветке рано или поздно разойдётся с
# оригиналом — достаточно, чтобы третью ветку добавили, забыв её скопировать.
TERMINAL_STATUSES = frozenset({STATUS_SUCCEEDED, STATUS_CANCELED})

# СРОК ДАВНОСТИ НЕЗАКРЫТОГО ПОДПИСОЧНОГО НАМЕРЕНИЯ, В ЧАСАХ. Значение — ответ
# чекпойнта задачи 1 плана 05-15 (24 часа), но ЗДЕСЬ ВАЖНО НЕ ЧИСЛО, А ТО,
# ЗАЧЕМ КОНСТАНТА ВООБЩЕ СУЩЕСТВУЕТ.
#
# Подписка на событие `payment.canceled` в кабинете ЮKassa НЕ ПОДТВЕРЖДЕНА
# (D-27). Значит на проде платёж, от оплаты которого человек отказался, никогда
# не получит уведомления об отмене и останется `pending` НАВСЕГДА. Потолок без
# срока давности читал бы такую строку как живое намерение вечно и закрыл бы
# человеку оплату насовсем — то есть починил бы обход цены ЦЕНОЙ НЕВОЗМОЖНОСТИ
# ЗАПЛАТИТЬ. Пока отмена не приходит сама, срок давности — единственный выход
# наружу, и снять его можно будет только вместе с подтверждённой подпиской на
# `payment.canceled`, а не «когда покажется, что он мешает».
PENDING_INTENT_TTL_HOURS = 24

# ЗНАКОМЫЕ СОБЫТИЯ — КОНСТАНТАМИ SDK, НИКОГДА СТРОКОВЫМИ ЛИТЕРАЛАМИ (T-05-12).
# Опечатка в литерале не поднимает ошибку: событие просто молча не
# обрабатывается, платёж остаётся pending, а обнаруживается это на боевом
# приёме денег. Константа с опечаткой падает AttributeError на импорте модуля.
#
# В SDK объявлено семь событий; refund.succeeded, payout.* и deal.closed этой
# фазе не принадлежат и по-прежнему возвращают False.
KNOWN_EVENTS = frozenset(
    {
        WebhookNotificationEventType.PAYMENT_SUCCEEDED,
        WebhookNotificationEventType.PAYMENT_CANCELED,
    }
)


class PaymentCreationError(Exception):
    """ЮKassa не создала платёж. Своё исключение модуля, а не чужое дерево.

    ЗАЧЕМ ОТДЕЛЬНЫЙ ТИП. Вызывающий обязан отличить «платёж не создан» от любой
    другой поломки, и делать это по типу исключения SDK он не может: дерево
    исключений `yookassa` — чужой контракт, который меняется без нашего ведома,
    а сетевые отказы приходят из `requests` вовсе не через него. Ловить здесь
    `Exception` и поднимать СВОЙ тип — единственный способ дать вызывающему
    ветку, которая не разъедется с версией SDK.

    ТЕКСТ ЧУЖОГО ИСКЛЮЧЕНИЯ В ЭТОТ ОБЪЕКТ НЕ КЛАДЁТСЯ. Он уходит в журнал ключом
    `payment_create_failed` и НИКОГДА на экран (T-05-47): прецедент R-03-09
    Фазы 3 — раскрытие текста стороннего исключения в плашке — принят владельцем
    риском severity medium, и повторять его на ДЕНЕЖНОМ пути не следует.
    Исходное исключение остаётся доступным через `__cause__` для отладчика,
    который читает трассировку, а не страницу.
    Закреплено `test_the_third_party_exception_text_never_reaches_the_screen`.
    """


class PendingIntentCapError(Exception):
    """Мы отказали во втором одновременном подписочном намерении. НЕ ЮKassa.

    ЗАЧЕМ СВОЙ ТИП, А НЕ `PaymentCreationError`. Тот говорит «ЮKassa не создала
    платёж» — а здесь ЮKassa не спрашивали ВОВСЕ: отказ принят до единого
    обращения наружу. Переиспользование чужого типа привело бы человека к
    строке «попробуйте ещё раз через минуту», то есть посоветовало бы ровно то
    действие, которое отказ и вызвало. Ветка обработчика формы обязана быть
    ДРУГОЙ, и различать её по типу — единственный способ не разъехаться.

    ТЕКСТ ЭТОГО ИСКЛЮЧЕНИЯ НА ЭКРАН НЕ УХОДИТ (T-05-47, T-05-96). На экран
    уезжает КОД причины, строку по нему подбирает отображение раздела. Поэтому
    сообщение ФИКСИРОВАНО: ни числа незакрытых намерений, ни их планов, ни
    идентификаторов чужих платежей в него не подставляется — эти величины
    принадлежат журналу, а не человеку по ту сторону формы.
    Закреплено
    `test_a_second_subscription_intent_from_the_form_is_refused_with_words`: на
    экран уходят СВОИ слова кода причины.
    """


def _configure_yookassa():
    settings = get_settings()
    Configuration.account_id = settings.yookassa_shop_id
    Configuration.secret_key = settings.yookassa_secret_key


async def _open_subscription_intents(
    db: AsyncSession, user_id: int, now: datetime
) -> list[Payment]:
    """Незакрытые подписочные намерения пользователя, не старше срока давности.

    Незакрытое — значит НЕ В ТЕРМИНАЛЬНОМ СТАТУСЕ: из `succeeded` и `canceled`
    платёж не выходит, и намерением он больше не является. Условие написано
    через `TERMINAL_STATUSES`, а не через равенство `pending`, по той же
    причине, что и в `_claim_payment`: третий нетерминальный статус, добавленный
    когда-нибудь, обязан попасть сюда сам.
    Закреплено `test_a_terminal_payment_never_blocks_a_new_one`.

    ⚠️ СРОК ДАВНОСТИ ПРИМЕНЯЕТСЯ В PYTHON, А НЕ УСЛОВИЕМ SQL, И ЭТО НЕ ВКУС.
    Колонка объявлена `DateTime(timezone=True)`, но SQLite отдаёт её NAIVE, а
    PostgreSQL — aware. Сравнение, ушедшее в SQL, разошлось бы ровно на одном из
    двух диалектов: суита (SQLite) зеленела бы, а на бою (PostgreSQL) потолок
    вёл бы себя иначе — то есть дефект ловился бы пользователем, а не тестом.
    Значение проходит через `normalize_utc` — тот же приём и та же причина, что
    у `next_expiry` и `subscription_is_live`. Что срок давности ДЕЙСТВУЮЩИЙ,
    закреплено `test_a_stale_intent_does_not_block_a_new_one`; что терминальный
    платёж не считается вовсе — `test_a_terminal_payment_never_blocks_a_new_one`.
    """
    rows = (
        (
            await db.execute(
                select(Payment).where(
                    Payment.user_id == user_id,
                    Payment.kind == KIND_SUBSCRIPTION,
                    Payment.status.not_in(TERMINAL_STATUSES),
                )
            )
        )
        .scalars()
        .all()
    )

    cutoff = now - timedelta(hours=PENDING_INTENT_TTL_HOURS)
    fresh = []
    for row in rows:
        born = normalize_utc(row.created_at)
        # Строка без времени рождения (её ещё не видела СУБД) считается СВЕЖЕЙ:
        # «неизвестно когда» на стороне пользователя означало бы снятие потолка,
        # а снимать защиту по отсутствию данных — не то умолчание.
        if born is None or born >= cutoff:
            fresh.append(row)
    return fresh


async def create_payment(
    db: AsyncSession,
    user_id: int,
    price: str,
    *,
    kind: str,
    package_name: str | None = None,
    messages_count: int | None = None,
    plan: str | None = None,
    switch_authorized: bool | None,
) -> dict:
    """Создаёт платёж в ЮKassa и строку `payments` под него.

    `kind` ОБЯЗАТЕЛЕН И KEYWORD-ONLY намеренно. Сигнатура стала строже, чем
    была: необновлённый вызывающий обязан упасть громко на вызове, а не тихо
    записать платёж с угаданным предметом покупки — угаданный предмет
    обнаружился бы только на вебхуке, то есть после того, как деньги списаны.

    `switch_authorized` ОБЯЗАТЕЛЕН И KEYWORD-ONLY ПО ТОЙ ЖЕ ПРИЧИНЕ, И ЭТО НЕ
    единообразие ради единообразия. Колонка — ЖУРНАЛЬНАЯ (`payments`), и она
    хранит ответ гарда смены тарифа, снятый в момент ПРОДАЖИ: `True` — правило
    спросили и переход разрешило, `False` — спросили и отвергло, `None` — не
    спрашивали. Значение по умолчанию вернуло бы ровно ту дисциплину
    вызывающего, из-за которой две стадии правила разошлись дважды подряд:
    параметр, который можно не подать, однажды не подадут. Что вызов без него не
    собирается вовсе, закреплено `test_the_intent_records_that_no_rule_was_asked`.

    ⚠️ СЕГОДНЯ ЕДИНСТВЕННОЕ ПРОИЗВОДИМОЕ ЗНАЧЕНИЕ — `None`, И ЭТО ЗАПИСЬ ФАКТА,
    А НЕ ВЫРОЖДЕНИЕ ПАРАМЕТРА. Гарда смены тарифа не существует с плана 05.1-05,
    правила перехода — с плана 05.1-07, и `NULL` означает ровно «правило не
    спрашивали». Литерал `True` записал бы РАЗРЕШЕНИЕ, которого никто не выдавал,
    — подпись под сделкой от имени правила, которого нет (T-05.1-11).
    Исторические строки со значениями `True`/`False` в журнале остаются и
    читаются как есть: `payments` — ЖУРНАЛ, а не текущее состояние.
    Закреплено `test_the_intent_records_that_no_rule_was_asked`: намерение
    записывает `NULL`, а вызов без этого аргумента не собирается вовсе.

    ⚠️ В `metadata` ПЛАТЕЖА ЭТО ЗНАЧЕНИЕ НЕ УЕЗЖАЕТ, и это не экономия полей.
    Предмет и условия сделки решает СВОЯ строка, никогда тело уведомления
    (T-05-08, T-05-68): всё, что ушло в ЮKassa, возвращается оттуда как вход из
    сети, и решать по нему, что человеку выдать, значило бы отдать условия
    сделки наружу. Что ответ гарда живёт на СВОЕЙ строке и наружу не уходит,
    закреплено тем же `test_the_intent_records_that_no_rule_was_asked` — он
    читает и строку `payments`, и тело вызова, ушедшее в ЮKassa.

    ПОТОЛОК ОДНОВРЕМЕННЫХ ПОДПИСОЧНЫХ НАМЕРЕНИЙ — ПЕРВОЕ, ЧТО ЗДЕСЬ ДЕЛАЕТСЯ.
    ФОРМА: НЕ БОЛЕЕ ОДНОГО НЕЗАКРЫТОГО ПОДПИСОЧНОГО НАМЕРЕНИЯ НА ПОЛЬЗОВАТЕЛЯ
    (решение владельца D-I). Состояние, которое он не допускает: у человека
    ОДНОВРЕМЕННО висят два оплачиваемых счёта за один и тот же месяц доступа —
    оплатив оба, он платит 6000 ₽ за 3000 ₽ товара, и объяснять ему это придётся
    возвратом, а не словами.
    Закреплено
    `test_a_second_subscription_intent_is_refused_before_the_money_moves`,
    `test_a_user_without_open_intents_pays_without_obstruction` (граница снизу),
    `test_an_intent_of_another_user_does_not_reach_over` (потолок считает
    намерения ВЛАДЕЛЬЦА) и `test_a_package_payment_is_outside_the_cap`.

    ⚠️ ПОЧЕМУ ФОРМА СМЕНИЛАСЬ, И ПОЧЕМУ ПРЕЖНЮЮ НЕЛЬЗЯ БЫЛО ПРОСТО ОСТАВИТЬ.
    До плоской модели потолок отбирал намерения по НЕСОВПАДЕНИЮ ТАРИФА
    (`cap-different-plan`): он лечил скалярность `subscription.plan`, который не
    вмещал два перехода в разные стороны, и повтор оплаты ТОГО ЖЕ тарифа
    оставлял разрешённым. Тарифов больше нет (D-A, D-D), у всех намерений
    `plan IS NULL`, и сравнение тарифов стало бы ложным ВСЕГДА — то есть защита
    перестала бы срабатывать МОЛЧА, не покраснев ни одним тестом и не удалившись
    ни одной строкой. Молчаливое вырождение защиты и есть причина смены формы:
    потолок либо снимают решением, либо переоснуют решением. Владелец выбрал
    второе (D-I). Что новая форма СРАБАТЫВАЕТ на неразличимых по предмету
    намерениях — то есть ровно там, где прежняя выродилась бы, — закреплено
    `test_a_second_subscription_intent_is_refused_before_the_money_moves`.

    ⚠️ ЦЕНА НОВОЙ ФОРМЫ НАЗВАНА, А НЕ ЗАМОЛЧАНА. Прежняя форма НЕ наказывала
    самую частую человеческую ошибку — «нажал ещё раз, потому что вкладка
    зависла»; новая её ОТВЕРГАЕТ. Отказ при этом не молчит: человек получает
    словами, что незакрытой осталась его предыдущая оплата
    (`PAYMENT_ERROR_MESSAGES["pending"]`, UI-контракт E2), а выход из состояния
    даёт срок давности. Разменом принят второй счёт на те же деньги, и он дороже
    лишнего экрана. Что отказ приходит СО СЛОВАМИ, закреплено
    `test_a_second_subscription_intent_from_the_form_is_refused_with_words`; что
    выход из состояния существует —
    `test_a_stale_intent_does_not_block_a_new_one` и
    `test_a_canceled_intent_does_not_block_a_new_one`.

    ⚠️ СУЖАЕТ, А НЕ ДЕЛАЕТ НЕДОСТИЖИМЫМ, И ОСТАТОЧНЫХ ОКОН ДВА, А НЕ ОДНО.
    Прежняя редакция этого абзаца называла одно — гонку — и тем самым объявляла
    состояние недостижимым, имея в двухстах строках отсюда собственный ЗЕЛЁНЫЙ
    тест проекта, который его ДОСТИГАЕТ:
    `tests/test_services/test_payment_service.py::test_a_stale_intent_does_not_block_a_new_one`.
    Объявлять недостижимым состояние, которого достигает своя же суита, — тот же
    класс записанного обоснования, которого код не исполняет, за который этот
    раздел уже получил два раунда правок.

    ОКНО ВТОРОЕ — СРОК ДАВНОСТИ, И ОНО ШИРЕ ПЕРВОГО, ПОТОМУ ЧТО ДЕТЕРМИНИРОВАНО.
    Намерение старше `PENDING_INTENT_TTL_HOURS` перестаёт СЧИТАТЬСЯ
    (`_open_subscription_intents` отсеивает его по `created_at`), но
    ОПЛАЧИВАЕМЫМ быть не перестаёт: своей строки оно не теряет, терминальным не
    становится, и ссылка на оплату у ЮKassa продолжает работать. Пользователь,
    подождавший сутки, заводит ВТОРОЕ оплачиваемое намерение ГАРАНТИРОВАННО —
    не выиграв гонку, а просто подождав. Это цена неподтверждённой подписки на
    `payment.canceled` (D-27): на проде отменённый платёж остаётся `pending`
    навсегда, поэтому срок давности и есть единственный сегодня выход из
    незакрытого намерения. Закрыть окно можно ровно двумя способами — подтвердить
    подписку на `payment.canceled` либо СНИМАТЬ намерение с оплаты при истечении
    срока давности (отменять его у ЮKassa и переводить строку в терминальный
    статус), — а не молчаливым исключением строки из подсчёта, которым оно
    «закрыто» сегодня.
    Что намерение старше срока давности не считается, закреплено
    `test_a_stale_intent_does_not_block_a_new_one`.

    ⚠️ ОКНО ПЕРВОЕ — ГОНКА, И ЧЕГО ПОТОЛОК НЕ ДАЁТ, ЭТО АТОМАРНОСТИ. Между
    проверкой и появлением строки платежа лежит СЕТЕВОЙ ВЫЗОВ к ЮKassa, поэтому
    compare-and-swap, каким написан `_claim_payment`, здесь невозможен вовсе:
    условие и запись нельзя поставить в один оператор, если между ними обязан
    состояться разговор с чужим сервером. Две АБСОЛЮТНО одновременные попытки
    теоретически проходят проверку обе. Окно гонки несравнимо уже и окна «человек
    открыл две вкладки», которое потолок закрывает, и окна срока давности выше —
    но это ограничение, а не гарантия, и выдавать его за гарантию нельзя. То, что
    потолок ЗАКРЫВАЕТ, закреплено
    `test_a_second_subscription_intent_is_refused_before_the_money_moves` и
    `test_the_refusal_never_reaches_yookassa`; окно гонки не закреплено ничем и
    закреплено быть не может — исполнимого теста на одновременность двух сетевых
    вызовов у проекта нет, и это названо здесь, а не замолчано.

    ЧЕМ ИМЕННО КОНЧАЕТСЯ ЭТО ОКНО В ПЛОСКОЙ МОДЕЛИ, НАЗВАНО ЗДЕСЬ ПО
    ЗНАЧЕНИЯМ, И ОТВЕТ ИЗМЕНИЛСЯ ВМЕСТЕ С МОДЕЛЬЮ. Раньше два подтверждённых
    намерения РАЗНЫХ тарифов уничтожали друг друга: `subscription.plan` —
    скаляр, и последний подтверждённый платёж стирал тариф предыдущего, сколько
    бы тот ни стоил, то есть проданная сделка оказывалась НЕ ВЫДАННОЙ. Теперь
    стирать нечего: тарифа у платежа нет, и обе подтверждённые оплаты просто
    двигают `expires_at` вперёд через `next_expiry` — человек, заплативший
    дважды, получает два месяца доступа за две суммы. ДЕНЬГИ БЕЗ ТОВАРА ЭТО ОКНО
    БОЛЬШЕ НЕ ПРОИЗВОДИТ, и остаточный вред у него ровно один: списание, которого
    человек не хотел, вместо одного, которого хотел. Возврат такой оплаты —
    ручная операция кабинета ЮKassa, и в продукте её нет.

    ЧТО ЗАКРЫЛО БЫ ОКНО СВОЙСТВОМ, А НЕ ФОРМУЛИРОВКОЙ, НАЗВАНО
    ПОИМЁННО И НАЗВАНО НЕСДЕЛАННЫМ. Это ЧАСТИЧНЫЙ УНИКАЛЬНЫЙ ИНДЕКС «не более
    одного незакрытого подписочного намерения пользователя» — по образцу
    `uq_subscriptions_active_user` ревизии `0018`, где такой же индекс сделал
    вторую активную подписку невозможной на уровне СУБД, то есть независимо и от
    порядка, и от сетевых пауз. Он НЕ ПОСТРОЕН и является работой своего размера,
    а не обещанием: своя ревизия Alembic в невыкаченной очереди (D-26), своё
    решение о том, что делать с уже существующими строками, свой round-trip-тест
    и своя обработка отказа ограничения ЗДЕСЬ — прикладной отказ пришлось бы
    отличать от чужого ровно так, как это делает `_extend_subscription`. Пока
    индекса нет, потолок остаётся прикладной защитой от самого частого
    человеческого действия, а не инвариантом схемы.
    """
    # ⚠️ ПРОВЕРКА СТОИТ ДО `_configure_yookassa()`, ДО СБОРКИ `metadata` И ДО
    # `YooPayment.create`. Отказ, принятый ПОСЛЕ вызова SDK, оставил бы у ЮKassa
    # платёж, которого нет в нашей базе: он не пришёл бы ни успехом, ни отменой
    # и повис бы у них вечно — зеркало ровно той ловушки, ради которой запись в
    # свою базу стоит ПОСЛЕ вызова SDK (T-05-49). Закреплено
    # `test_the_refusal_never_reaches_yookassa`, который требует, чтобы отказ
    # потолка не дошёл до SDK ни одним вызовом.
    if kind == KIND_SUBSCRIPTION:
        open_intents = await _open_subscription_intents(
            db, user_id, datetime.now(timezone.utc)
        )
        # ФОРМА «НЕ БОЛЕЕ ОДНОГО НЕЗАКРЫТОГО»: мешает ЛЮБОЕ открытое намерение.
        # Отбор открытых остаётся за `_open_subscription_intents` — он уже
        # исключил и терминальные, и просроченные строки, и второй его копии
        # здесь нет. Закреплено
        # `test_a_second_subscription_intent_is_refused_before_the_money_moves`
        # (срабатывает), `test_a_user_without_open_intents_pays_without_obstruction`
        # (граница снизу) и `test_an_intent_of_another_user_does_not_reach_over`.
        if open_intents:
            # УРОВЕНЬ `warning`, А НЕ `info`: это исход, по которому к нам придёт
            # человек, и жалоба «я нажал, а мне отказали» обязана иметь опору.
            # ⚠️ ПРЕЖНЯЯ РЕДАКЦИЯ ССЫЛАЛАСЬ ЗА ОБОСНОВАНИЕМ НА КЛЮЧ СОХРАНЁННОГО
            # ТАРИФА, снятый планом 05.1-07 вместе с решением о плане. Довод от
            # несуществующего соседа не проверяем ничем, поэтому он назван здесь
            # своими словами, а не ссылкой. Закреплено
            # `test_the_refusal_leaves_its_own_trace`.
            logger.warning(
                "subscription_intent_cap_reached",
                user_id=user_id,
                open_intents=len(open_intents),
            )
            raise PendingIntentCapError(
                "Предыдущее подписочное намерение ещё не завершено"
            )

    _configure_yookassa()
    settings = get_settings()

    if kind == KIND_SUBSCRIPTION:
        description = f"Подписка «{plan}»"
        # Ключ `kind` в metadata обязателен: без него в личном кабинете ЮKassa
        # два предмета покупки неразличимы, и вопрос «за что этот платёж»
        # разрешается только сверкой со своей базой (T-05-08).
        metadata = {
            "user_id": str(user_id),
            "kind": kind,
            "plan": str(plan or ""),
        }
    else:
        description = f"Пополнение баланса: {package_name}"
        metadata = {
            "user_id": str(user_id),
            "kind": kind,
            "messages_count": str(messages_count),
            "package_name": str(package_name or ""),
        }

    idempotency_key = str(uuid.uuid4())
    # ВЫЗОВ SDK СТОИТ ДО ЗАПИСИ В БД, И ЭТОТ ПОРЯДОК ОБЯЗАТЕЛЕН (T-05-49).
    # Строка `payments`, оставшаяся после отказа, означала бы платёж, которого у
    # ЮKassa нет вовсе: он не пришёл бы ни успехом, ни отменой и висел бы
    # `pending` вечно, показывая пользователю «в обработке» там, где обработки
    # не начиналось.
    # Закреплено `test_a_failed_payment_leaves_no_row_in_the_journal`.
    #
    # ЛОВИТСЯ `Exception`, А НЕ ТИП ИЗ SDK. Отказ приезжает и своим деревом
    # исключений `yookassa`, и сетевым исключением `requests` из-под него, и
    # разбором чужого ответа. Перечислить это множество нельзя, а всякий
    # непойманный его элемент — необработанная пятисотка на кнопке оплаты.
    # `KeyboardInterrupt` и `SystemExit` наследуются от `BaseException` и сюда
    # намеренно не попадают.
    # Закреплено
    # `test_a_failed_subscription_payment_returns_the_person_with_a_reason` и
    # `test_a_failed_package_payment_returns_the_person_with_a_reason`.
    try:
        payment = YooPayment.create(
            {
                "amount": {"value": price, "currency": "RUB"},
                "confirmation": {
                    "type": "redirect",
                    "return_url": settings.yookassa_return_url or f"{settings.app_name}/billing",
                },
                "capture": True,
                "description": description,
                "metadata": metadata,
            },
            idempotency_key,
        )
    except Exception as exc:
        # СЛЕД ОБЯЗАТЕЛЕН (T-05-48). Отказ без записи в журнале превращает
        # жалобу «я нажал, ничего не произошло» в непроверяемую: на экране
        # человек видит одну фиксированную строку, и различить по ней сеть,
        # неверный ключ магазина и отвергнутую сумму невозможно.
        # Закреплено
        # `test_the_failure_is_recorded_in_the_journal_by_its_own_key`.
        #
        # Уровень `error`, а не `warning`: этот отказ останавливает приём денег,
        # и в потоке предупреждений он потерялся бы (тот же выбор, что у
        # `webhook_ip_header_not_configured`).
        logger.error(
            "payment_create_failed",
            user_id=user_id,
            kind=kind,
            plan=plan,
            package_name=package_name,
            messages=messages_count,
            amount=price,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        raise PaymentCreationError(
            "ЮKassa не создала платёж"
        ) from exc

    db_payment = Payment(
        user_id=user_id,
        yookassa_payment_id=payment.id,
        status="pending",
        amount_value=price,
        amount_currency="RUB",
        kind=kind,
        plan=plan,
        switch_authorized=switch_authorized,
        messages_count=messages_count,
        package_name=package_name,
    )
    db.add(db_payment)
    await db.commit()

    logger.info(
        "payment_created",
        user_id=user_id,
        yookassa_id=payment.id,
        amount=price,
        kind=kind,
        plan=plan,
        messages=messages_count,
    )

    return {
        "confirmation_url": payment.confirmation.confirmation_url,
        "payment_id": payment.id,
    }


async def _claim_payment(
    db: AsyncSession, yookassa_id: str, new_status: str, now: datetime
) -> bool:
    """Заявляет платёж на обработку. True — заявка выиграна, False — опередили.

    ЭТО COMPARE-AND-SWAP, А НЕ ПРОВЕРКА С ПОСЛЕДУЮЩЕЙ ЗАПИСЬЮ. Условие «статус
    ещё не терминальный» стоит В ТОМ ЖЕ операторе, что и запись нового статуса,
    поэтому между проверкой и записью не остаётся зазора ВОВСЕ. Прежняя пара
    «прочитали статус → много позже записали» оставляла окно, в которое
    помещалась целая вторая доставка: обе видели `pending`, обе начисляли.

    РАБОТАЕТ ОДИНАКОВО НА PostgreSQL И НА SQLite, и это принципиально. Суита
    проекта живёт на SQLite, где `SELECT ... FOR UPDATE` диалектом ИГНОРИРУЕТСЯ
    — то есть блокировка строки сама по себе регрессией непокрываема. Условный
    UPDATE покрываем, потому что атомарность одного оператора даёт и SQLite.

    `synchronize_session=False`: оператор идёт мимо identity map, и сессия о
    записи не знает. Поля объекта платежа отзеркаливает вызывающий.
    """
    result = await db.execute(
        update(Payment)
        .where(
            Payment.yookassa_payment_id == yookassa_id,
            Payment.status.not_in(TERMINAL_STATUSES),
        )
        .values(status=new_status, confirmed_at=now)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount == 1


def _mirror_claim(db_payment: Payment, new_status: str, now: datetime) -> None:
    """Отзеркаливает выигранную заявку на объект платежа в Python.

    `synchronize_session=False` означает, что сессия о записи не знает, а ниже
    по ветке эти поля читаются логированием и `_extend_subscription`.

    Значения ставятся `set_committed_value`, а не присваиванием: присваивание
    пометило бы объект грязным, и ORM выдала бы на коммите ВТОРОЙ UPDATE тех же
    колонок — лишний оператор, притворяющийся, что запись сделал он.
    """
    set_committed_value(db_payment, "status", new_status)
    set_committed_value(db_payment, "confirmed_at", now)


async def handle_webhook(
    db: AsyncSession, event: str, payment_data: dict
) -> bool:
    """Доводит платёж до терминального статуса по подтверждённому уведомлению.

    ПОРЯДОК ПРОВЕРОК ЗНАЧИМ И МЕНЯТЬСЯ НЕ ДОЛЖЕН: событие → наличие `id` →
    строка платежа в СВОЕЙ базе → терминальный статус → и только потом
    ветвление по исходу платежа и по предмету покупки.

    ЗАЩИТА ОТ ДВОЙНОГО НАЧИСЛЕНИЯ ДЕРЖИТСЯ ДВУМЯ МЕХАНИЗМАМИ, И ГРАНИЦА МЕЖДУ
    НИМИ НАЗВАНА ЗДЕСЬ НАМЕРЕННО (T-05-04, T-05-35):

    * `_claim_payment` — условный UPDATE, держит НАЛОЖИВШИЕСЯ доставки. Их обе
      прошли проверку статуса ниже, потому что обе прочитали строку, пока она
      была `pending`; заявку выигрывает ровно одна, проигравшая до начисления не
      доходит физически. Работает на обоих диалектах и покрыт регрессией
      `tests/test_services/test_payment_concurrency.py`;
    * `with_for_update()` на выборке — убирает саму конкуренцию НА PostgreSQL:
      вторая доставка ждёт на выборке и доходит до проверки статуса уже с
      обновлённым значением, то есть выходит раньше и без единой записи. НА
      SQLite эта половина не исполняется вовсе — диалект молча опускает
      `FOR UPDATE`, поэтому суита её не проверяет и проверить не может.

    Проверка терминального статуса стоит ДО ветвления намеренно, но единственной
    защитой она БОЛЬШЕ НЕ ЯВЛЯЕТСЯ: это быстрый выход для ПОСЛЕДОВАТЕЛЬНОЙ
    повторной доставки (первая завершилась, вторая пришла после). Ровно она же не
    даёт припоздавшему уведомлению об отмене отнять уже выданное (T-05-10):
    платёж в `succeeded` не переводится в `canceled`.

    ЗНАКОМЫХ СОБЫТИЙ ДВА — успех и отмена (D-16). До этого отмена возвращала
    False, и отменённый платёж навсегда оставался `pending`: история показывала
    бы «в обработке» там, где денег не взяли вовсе — то есть неправду, а не
    отсутствие данных (BILL-07).
    Закреплено `test_handle_webhook_ignores_an_event_it_does_not_know` и
    `test_a_canceled_webhook_gives_a_pending_payment_a_terminal_status`.

    ПРЕДМЕТ ПОКУПКИ РЕШАЕТ КОЛОНКА `kind` ИЗ БД, никогда `metadata`
    уведомления: тело уведомления приезжает из сети и источником истины быть не
    может (T-05-02). Пользователь берётся оттуда же — из строки платежа.
    """
    if event not in KNOWN_EVENTS:
        return False

    obj = payment_data.get("object", {})
    yookassa_id = obj.get("id")
    if not yookassa_id:
        logger.warning("webhook_missing_payment_id")
        return False

    result = await db.execute(
        select(Payment)
        .where(Payment.yookassa_payment_id == yookassa_id)
        .with_for_update()
    )
    db_payment = result.scalar_one_or_none()
    if db_payment is None:
        logger.warning("webhook_payment_not_found", yookassa_id=yookassa_id)
        return False

    if db_payment.status in TERMINAL_STATUSES:
        logger.info("webhook_payment_already_processed", yookassa_id=yookassa_id)
        return True

    now = datetime.now(timezone.utc)

    if event == WebhookNotificationEventType.PAYMENT_CANCELED:
        # ВЕТКА ОТМЕНЫ НАМЕРЕННО НИЧЕГО НЕ НАЧИСЛЯЕТ: ни сообщений, ни дней
        # подписки. Она только записывает исход — и тем снимает платёж с вечного
        # `pending`. Баланс при этом не изменился, поэтому и инвалидировать
        # кэш нечего.
        # Закреплено `test_a_canceled_package_payment_credits_nothing`,
        # `test_a_canceled_subscription_payment_creates_no_subscription` и
        # `test_a_repeated_canceled_webhook_writes_nothing_twice`.
        #
        # Момент решения пишется в СУЩЕСТВУЮЩУЮ колонку времени подтверждения:
        # колонка одна, и её смысл — «когда платёж перешёл в терминальное
        # состояние». Второй колонки под отмену D-15 не заводит, а расширять
        # решение владельца этот код не вправе.
        #
        # Причина отмены (`cancellation_details` в теле уведомления) не пишется
        # и не логируется (T-05-13): её не называет ни требование, ни макет, а
        # разбор чужой структуры ради неиспользуемого поля — лишний контракт с
        # внешним форматом.
        if not await _claim_payment(db, yookassa_id, STATUS_CANCELED, now):
            await db.rollback()
            logger.info("webhook_claim_lost", yookassa_id=yookassa_id)
            return True

        _mirror_claim(db_payment, STATUS_CANCELED, now)
        await db.commit()

        logger.info(
            "payment_canceled",
            user_id=db_payment.user_id,
            yookassa_id=yookassa_id,
            kind=db_payment.kind,
        )
        return True

    # ПРОВЕРКА ПРИГОДНОСТИ ПАКЕТА СТОИТ ДО ЗАЯВКИ (T-05-39, WR-04). Платёж с
    # пустым `messages_count` — последствие опечатки в `kind` у вызывающего:
    # подписочная покупка ушла в пакетную ветку, где считать нечего. Заявить его
    # проведённым и потом отказаться значило бы пометить платёж выданным, ничего
    # не выдав. Раньше начисление падало TypeError, маршрут отвечал 500, и
    # ЮKassa повторяла доставку до отказа при взятых деньгах.
    # Закреплено `test_a_package_payment_without_a_count_credits_nothing`.
    if db_payment.kind != KIND_SUBSCRIPTION and not db_payment.messages_count:
        logger.error(
            "webhook_package_without_messages_count",
            yookassa_id=yookassa_id,
            user_id=db_payment.user_id,
            kind=db_payment.kind,
        )
        return False

    # ЗАЯВКА СТОИТ ПЕРЕД ЛЮБОЙ ВЫДАЧЕЙ И В ТОЙ ЖЕ ТРАНЗАКЦИИ, ЧТО И ОНА:
    # единственный `commit` в конце ветки остаётся единственным. Отдельный
    # коммит заявки завёл бы окно, в котором платёж помечен проведённым, а
    # ресурс не выдан. Выдаваемый ресурс остался один — срок доступа: валюта
    # сообщений снята, и пакетной ветке выдавать больше нечего.
    # Закреплено `test_overlapping_deliveries_of_a_package_credit_nothing`
    # и `test_overlapping_deliveries_extend_subscription_by_one_month`.
    if not await _claim_payment(db, yookassa_id, STATUS_SUCCEEDED, now):
        # Не отказ: уведомление обработано — просто не этой доставкой. 5xx здесь
        # спровоцировал бы новую попытку ЮKassa по уже проведённому платежу.
        await db.rollback()
        logger.info("webhook_claim_lost", yookassa_id=yookassa_id)
        return True

    _mirror_claim(db_payment, STATUS_SUCCEEDED, now)

    if db_payment.kind == KIND_SUBSCRIPTION:
        await _extend_subscription(db, db_payment, now)
        await db.commit()
        # СБРОС ВЕРДИКТА ДОСТУПА СТОИТ ЗДЕСЬ, ПОСЛЕ КОММИТА И ДО ВОЗВРАТА.
        # Инвалидация в этой ветке отсутствовала и была верна: подписка баланса
        # не меняла, а кэш хранил именно баланс. С переводом гейта на вердикт
        # ДОСТУПА подписочная ветка стала писателем ровно той величины, которую
        # кэш и хранит, — без сброса оплативший до минуты (TTL) видел бы «доступ
        # закончился» на всех страницах и не рассылал бы по расписанию, то есть
        # деньги уже взяты, а куплённое ещё не выдано. Закреплено
        # `test_a_confirmed_subscription_payment_reopens_access_at_once`.
        #
        # ПОСЛЕ КОММИТА, А НЕ ДО НЕГО: сброс до фиксации срока дал бы гонку, в
        # которой соседний запрос перечитывает СТАРЫЙ срок и кладёт закрытый
        # вердикт обратно в кэш на целый TTL.
        # Закреплено `test_a_confirmed_subscription_payment_reopens_access_at_once`.
        await invalidate_access_cache(db_payment.user_id)
        logger.info(
            "subscription_payment_succeeded",
            user_id=db_payment.user_id,
            yookassa_id=yookassa_id,
            amount=db_payment.amount_value,
            plan=db_payment.plan,
        )
        return True

    # ПАКЕТНАЯ ВЕТКА СТАЛА ЖУРНАЛЬНОЙ, А НЕ УДАЛЁННОЙ (T-05.1-24). Закреплено
    # `test_a_package_notification_marks_the_payment_and_credits_nothing`.
    #
    # Валюта сообщений снята из продукта целиком, и начислять больше нечего.
    # Ветка при этом ОБЯЗАНА остаться: уведомление о покупке пакета всё ещё
    # может прийти по платежу, заведённому ДО выката — человек нажал «купить»
    # вчера, ЮKassa подтвердила сегодня. Взятые деньги обязаны получить
    # терминальный статус, поэтому платёж помечается проведённым выше
    # (`_claim_payment` + `_mirror_claim`) и фиксируется этим `commit`.
    # Закреплено `test_a_package_notification_marks_the_payment_and_credits_nothing`.
    #
    # ⚠️ ОТВЕТ УСПЕШНЫЙ, А НЕ ПЯТИСОТКА. Возврат 5xx спровоцировал бы новую
    # попытку доставки по УЖЕ ПРОВЕДЁННОМУ платежу — отказ, который сам себя
    # повторяет, и растущая очередь повторов у платёжного провайдера.
    # Закреплено `test_a_repeated_package_notification_is_still_processed_only_once`
    # и `test_the_losing_delivery_answers_accepted`.
    #
    # ⚠️ У НЕПРОВЕДЁННОГО НАЧИСЛЕНИЯ ЕСТЬ СЛЕД, И КЛЮЧ У НЕГО СВОЙ. Прежний ключ
    # успеха означал «выдано столько-то сообщений»; сохранить его значило бы
    # писать в журнал неправду о выдаче. Жалоба «я заплатил и ничего не
    # получил» проверяема ровно этой строкой, и причина названа в ней явно.
    # Закреплено `test_a_package_notification_records_the_fact_by_its_own_key`.
    await db.commit()

    logger.info(
        "webhook_package_payment_not_credited",
        user_id=db_payment.user_id,
        yookassa_id=yookassa_id,
        messages=db_payment.messages_count,
        reason="message_currency_removed",
    )
    return True


async def _extend_subscription(
    db: AsyncSession, db_payment: Payment, now: datetime
) -> None:
    """Двигает срок подписки владельца платежа или заводит её впервые.

    ЗАПРОС АКТИВНОЙ ПОДПИСКИ ПОВТОРЯЕТ `get_shell_context` ДОСЛОВНО
    (app/pages/common.py:397-404): те же три условия, та же сортировка, тот же
    `limit(1)`. Одинаковый запрос у ЧИТАТЕЛЯ (шелл показывает тариф и срок) и у
    ПИСАТЕЛЯ (этот код) держит их в согласии; разойдись они, продление двигало
    бы одну строку, а пользователь видел бы другую.

    ВТОРАЯ АКТИВНАЯ СТРОКА С РЕВИЗИИ 0018 НЕВОЗМОЖНА НА УРОВНЕ СУБД — частичный
    уникальный индекс `uq_subscriptions_active_user`. Это закрывает остаточную
    щель, которую прикладная заявка `_claim_payment` закрыть не могла: два
    РАЗНЫХ платежа одного пользователя, доставленные внахлёст при отсутствующей
    подписке, честно выигрывают КАЖДЫЙ СВОЮ заявку — строки платежей-то разные,
    — оба видят «подписки нет» и оба вставляют.

    ОТКАЗ ОГРАНИЧЕНИЯ ЗДЕСЬ ОБРАБАТЫВАЕТСЯ, А НЕ ПРОПУСКАЕТСЯ НАВЕРХ. Платёж
    настоящий, деньги взяты, и ответить на него 500-й значило бы наказать
    пользователя за гонку внутри платформы. Проигравшая вставку доставка
    перечитывает чужую строку и двигает срок НА НЕЙ — исход тот же, что при
    последовательном приходе двух платежей.
    Закреплено `test_a_rejected_subscription_insert_is_recovered_not_raised`.

    ВСТАВКА ИДЁТ В SAVEPOINT. Откат по нарушению ограничения обязан снять ТОЛЬКО
    неудавшуюся вставку: снаружи, в той же транзакции, уже лежит выигранная
    заявка на платёж (`_claim_payment`), и полный откат вернул бы платёж в
    `pending` — то есть потерял бы факт обработки денег.
    Закреплено `test_two_different_payments_leave_one_active_subscription`.

    Срок двигается ТОЛЬКО ЗДЕСЬ — то есть только по подтверждённому платежу.
    Возврат браузера с `return_url` доказательством оплаты не является и
    происходит в том числе при отказе (D-05, T-05-05).
    Закреплено
    `test_a_canceled_subscription_payment_does_not_move_an_existing_expiry`.

    ЧТО ИМЕННО ДЕЛАЕТ ПОДТВЕРЖДЁННЫЙ ПЛАТЁЖ. Он исполняется здесь ЛЮБОЙ, и
    деньги ВСЕГДА превращаются в дни: отказать оплаченному платежу значило бы
    взять деньги и не выдать ничего — худший из возможных исходов. Ветвиться при
    этом не на чем: тариф в системе один (D-A), и с плана 05.1-07 подтверждённый
    платёж делает ровно одно — двигает `expires_at`. Закреплено
    `test_a_confirmed_payment_only_moves_the_date` (действующая подписка) и
    `test_the_first_purchase_creates_the_row_from_today` (первая покупка).

    ЧТО ПРОИСХОДИТ, КОГДА ОПЛАЧЕННЫЙ СРОК УЖЕ ИСТЁК. Срок считается ОТ СЕГОДНЯ,
    а не от даты в прошлом (D-04): продление мёртвого периода не имеет права
    выдать дни, которые кончились ещё до платежа. Правило объявлено ОДИН раз —
    `countdown_base`, читаемая `next_expiry` в
    `app/application/billing/subscription_period.py`, — и денежный путь его
    ЧИТАЕТ, а не считает у себя. Пользователь БЕЗ строки подписки и пользователь
    с ИСТЁКШЕЙ строкой получают при одном намерении один исход, а не
    противоположные. Закреплено
    `test_next_expiry_of_an_expired_subscription_counts_from_today` (само
    правило) и `test_the_journal_of_an_extension_names_the_liveness_of_the_period`
    (денежный путь различает два исхода в журнале).

    ПРИЗНАК ЖИВОСТИ ОПЛАЧЕННОГО СРОКА — `subscription_is_live` из
    `app/application/billing/subscription_period.py`, ЕДИНСТВЕННОЕ его
    объявление на проект. ⚠️ ПОРЯДОК: признак снимается ДО сдвига срока.
    `next_expiry` перезаписывает величину, по которой признак считается, и
    перестановка двух операторов местами вернула бы дефект МОЛЧА — признак
    отвечал бы «живо» всегда. Порядок закреплён тестом по синтаксическому дереву
    `test_the_liveness_is_sampled_before_the_date_moves`.
    """
    subscription = await _active_subscription(db, db_payment.user_id)

    if subscription is not None:
        _apply_extension(subscription, db_payment, now)
        return

    # ⚠️ ВЕТКА ПЕРВОЙ ВСТАВКИ: РЕШЕНИЕ ЯВНОЕ, А НЕ УНАСЛЕДОВАННОЕ УМОЛЧАНИЕ
    # (T-05-108). Продлевать здесь НЕЧЕГО, и это свойство состояния, а не
    # упущение: активной строки подписки нет вовсе, значит нет и оплаченного
    # остатка, к которому мог бы прибавиться месяц. Платёж покупает ровно один
    # месяц от сегодня — тем же объявлением `next_expiry`, что двигает срок
    # действующей подписки, а не второй формулой рядом.
    # Закреплено `test_the_first_purchase_creates_the_row_from_today`.
    #
    # ТАРИФ КОНСТРУКТОРУ НЕ ПЕРЕДАЁТСЯ, ПОТОМУ ЧТО КОЛОНКИ БОЛЬШЕ НЕТ (ревизия
    # `0020`). Прежде сюда уезжал `db_payment.plan or "free"` — единственное
    # место, где имя тарифа платежа становилось именем тарифа подписки. Предмет
    # покупки теперь один, и второго источника правды о нём не заводится.
    # Закреплено `test_the_first_purchase_creates_the_row_from_today`.
    try:
        async with db.begin_nested():
            db.add(
                Subscription(
                    user_id=db_payment.user_id,
                    expires_at=next_expiry(None, now),
                    is_active=True,
                )
            )
            await db.flush()
        return
    except IntegrityError as rejection:
        logger.info(
            "subscription_insert_lost",
            user_id=db_payment.user_id,
            yookassa_id=db_payment.yookassa_payment_id,
        )
        rejected_by = rejection

    subscription = await _active_subscription(db, db_payment.user_id)
    if subscription is None:
        # Ограничение отвергло вставку, но активной строки нет — значит отказ
        # пришёл НЕ от `uq_subscriptions_active_user`, и глотать его нельзя:
        # исключение поднимается тем же объектом, а не новым.
        raise rejected_by
    _apply_extension(subscription, db_payment, now)


async def _active_subscription(db: AsyncSession, user_id: int) -> Subscription | None:
    """Действующая подписка пользователя — тем же запросом, что у читателя."""
    return (
        await db.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.is_active.is_(True),
            )
            .order_by(Subscription.expires_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


def _apply_extension(
    subscription: Subscription, db_payment: Payment, now: datetime
) -> None:
    """Двигает срок действующей подписки — и НИ ОТ ЧЕГО БОЛЬШЕ НЕ ВЕТВИТСЯ.
    Закреплено `test_a_confirmed_payment_only_moves_the_date`.

    ПОРЯДОК ДВУХ ДЕЙСТВИЙ ЗДЕСЬ — ПРАВИЛО, А НЕ ОФОРМЛЕНИЕ, И ОН ПЕРЕЖИЛ СНЯТИЕ
    МАТРИЦЫ ТАРИФОВ. ПЕРВЫМ действием тела снимается признак живости оплаченного
    срока — `subscription_is_live` от `subscription.expires_at`; ВТОРЫМ срок
    двигается. Раньше сдвига признак стоит не для красоты: величина, по которой
    он считается, следующим оператором перестанет существовать в прежнем
    значении, и признак, снятый после, отвечал бы «живо» при любом состоянии
    подписки. Перестановка двух операторов местами возвращает дефект МОЛЧА и в
    новой модели, поэтому порядок закреплён тестом по синтаксическому дереву
    `test_the_liveness_is_sampled_before_the_date_moves` (T-05-63), а не
    вниманием читателя.

    ⚠️ ЧТО ИМЕННО СНЯТО ЗДЕСЬ ПЛАНОМ 05.1-07, НАЗВАНО ЯВНО, ЧТОБЫ СЛЕДУЮЩИЙ
    ЧИТАТЕЛЬ НЕ ИСКАЛ ПРОПАЖУ. Решения о ПЛАНЕ в этой функции больше нет: ни
    записанного ответа гарда, ни сравнения рангов, ни доли месяца отвергнутого
    перехода, ни конверсии остатка по отношению цен. Все они существовали ради
    перехода МЕЖДУ тарифами; тариф в системе один (D-A), переходить некуда, и
    ветка, оставленная «на всякий случай», была бы мёртвой копией отменённой
    модели. Деньги двигают ровно одну величину строки подписки — `expires_at`.
    Закреплено `test_a_confirmed_payment_only_moves_the_date`.

    ⚠️ ПРИЗНАК ЖИВОСТИ НЕ СТАЛ ДЕКОРАЦИЕЙ, ПОТЕРЯВ ВЕТВЛЕНИЕ, И ЭТО НЕСУЩЕЕ
    РАЗЛИЧИЕ, А НЕ УКРАШЕНИЕ ЖУРНАЛА. Он уходит полем `period_was_live` и
    различает два исхода одного платежа, неразличимых по строке подписки:
    ПРОДЛЕНИЕ живого срока (оплаченный месяц лёг поверх остатка) и ВОЗВРАТ после
    перерыва (срок считается от сегодня, D-04). Человек, у которого «пропали
    дни», приходит с этим к нам, и разбирающему обращение опереться иначе не на
    что: строка подписки показывает ТОЛЬКО итог. Закреплено
    `test_the_journal_of_an_extension_names_the_liveness_of_the_period`.

    Функция синхронная и в БД не пишет сама: `commit` делает `handle_webhook`,
    и заявка платежа с начислением обязаны остаться в одной транзакции (05-08).
    """
    # ⚠️ ПРИЗНАК СНИМАЕТСЯ ЗДЕСЬ, А НЕ СТРОКОЙ НИЖЕ, И ЭТО ЛОВУШКА, А НЕ
    # ОФОРМЛЕНИЕ. Следующий оператор ПЕРЕЗАПИСЫВАЕТ `subscription.expires_at` —
    # ту самую величину, по которой признак считается. Снятый после сдвига, он
    # всегда вернул бы «живо» (T-05-63, гэп 1 раунда 3). Закреплено тестом по
    # синтаксическому дереву `test_the_liveness_is_sampled_before_the_date_moves`,
    # у которого есть свои негативные контроли —
    # `test_the_order_helper_reports_a_move_placed_above_the_sample`.
    period_is_live = subscription_is_live(subscription.expires_at, now)

    subscription.expires_at = next_expiry(subscription.expires_at, now)

    logger.info(
        "subscription_extended",
        user_id=db_payment.user_id,
        yookassa_id=db_payment.yookassa_payment_id,
        period_was_live=period_is_live,
    )
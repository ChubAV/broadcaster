import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

import structlog
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value
from yookassa import Configuration, Payment as YooPayment
from yookassa.domain.notification import WebhookNotificationEventType

from app.application.analytics.send_analytics import normalize_utc
from app.application.billing.plan_switch import switch_is_refused
from app.application.billing.subscription_period import (
    capped_carryover,
    converted_remainder,
    countdown_base,
    next_expiry,
    prorated_expiry,
    subscription_is_live,
)
from app.config import get_settings
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.services.billing_service import add_messages
from app.services.billing_cache import invalidate_access_cache, invalidate_balance_cache

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
    единообразие ради единообразия. Он несёт ОТВЕТ ГАРДА смены тарифа, снятый в
    момент ПРОДАЖИ (D-28): `True` — правило спросили и переход разрешило,
    `False` — спросили и отвергло, `None` — не спрашивали (пакетная покупка).
    Значение по умолчанию вернуло бы ровно ту дисциплину вызывающего, из-за
    которой две стадии правила разошлись дважды подряд: параметр, который можно
    не подать, однажды не подадут — и платёж уедет к ЮKassa, не неся того, что
    было продано. Пакетный вызов подаёт `None` ЯВНО, тем же способом, каким уже
    подаёт `messages_count=None` и `package_name=None`.
    Закреплено
    `test_the_deal_cannot_be_sold_without_recording_its_authorization`: продать
    сделку, не записав ответа гарда, нельзя.

    ⚠️ В `metadata` ПЛАТЕЖА ЭТО ЗНАЧЕНИЕ НЕ УЕЗЖАЕТ, и это не экономия полей.
    Предмет и условия сделки решает СВОЯ строка, никогда тело уведомления
    (T-05-08, T-05-68): всё, что ушло в ЮKassa, возвращается оттуда как вход из
    сети, и решать по нему, что человеку выдать, значило бы отдать условия
    сделки наружу. Что ответ гарда живёт на СВОЕЙ строке, закреплено
    `test_the_intent_stage_records_its_answer_on_the_payment` и
    `test_a_package_payment_records_that_the_rule_was_not_asked`.

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
            # УРОВЕНЬ `warning`, А НЕ `info`, по той же причине, что у
            # `subscription_plan_preserved`: это исход, по которому к нам придёт
            # человек, и жалоба «я нажал, а мне отказали» обязана иметь опору.
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

    # ЗАЯВКА СТОИТ ПЕРЕД ЛЮБЫМ НАЧИСЛЕНИЕМ И В ТОЙ ЖЕ ТРАНЗАКЦИИ, ЧТО И ОНО:
    # единственный `commit` в конце ветки остаётся единственным. Отдельный
    # коммит заявки завёл бы окно, в котором платёж помечен проведённым, а
    # ресурс не выдан.
    # Закреплено `test_overlapping_deliveries_credit_the_package_exactly_once`
    # и `test_overlapping_deliveries_write_one_balance_transaction`.
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
        # деньги уже взяты, а куплённое ещё не выдано.
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

    new_balance = await add_messages(
        db,
        db_payment.user_id,
        db_payment.messages_count,
        type="purchase",
        description=f"Покупка: {db_payment.package_name}",
        payment_id=yookassa_id,
    )
    await db.commit()
    await invalidate_balance_cache(db_payment.user_id)

    logger.info(
        "payment_succeeded",
        user_id=db_payment.user_id,
        yookassa_id=yookassa_id,
        messages=db_payment.messages_count,
        new_balance=new_balance,
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

    СЕМАНТИКА СМЕНЫ ПЛАНА — `upgrade-only`, РЕШЕНИЕ ВЛАДЕЛЬЦА (C2/WR-02,
    чекпойнт плана 05-10). Раньше этот докстринг молчал о том, что делается с
    планом, а `_apply_extension` перезаписывал его безусловно — то есть правило
    существовало как следствие порядка двух строк, а не как решение.

    Правило: повышение тарифа разрешено и оплаченный остаток НЕ СЖИГАЕТ СВЕРХ
    ОБЪЯВЛЕННОГО ИСКЛЮЧЕНИЯ, названного ниже числом с датой отсчёта;
    понижение при действующей подписке не предлагается карточкой и не продаётся
    гардом `POST /billing/subscribe`. ⚠️ ПЕРЕЧЕНЬ КОНЧАЕТСЯ ЗДЕСЬ, И ЭТО ПРАВКА
    ПЛАНА `05-24`: прежняя редакция добавляла к нему «и НЕ ПРИМЕНЯЕТСЯ ЗДЕСЬ»,
    то есть распространяла правило на стадию ПРИМЕНЕНИЯ, где код его не
    исполняет. Платёж, которому гард ПРОДАЛ переход (записанное разрешение
    `True`), исполняется как продан, каким бы ни стало состояние подписки за
    время оплаты. Прохибиция плана
    `05-01` — «MUST NOT сжигать неистраченный остаток уже оплаченного периода» —
    имеет ОБЪЯВЛЕННОЕ ИСКЛЮЧЕНИЕ, а не соблюдена безусловно, и названо оно теми
    же словами, какими его уже сказал код `capped_carryover`
    (`app/application/billing/subscription_period.py`):
    «ИСКЛЮЧЕНИЕ из прохибиции плана 05-01, а не её соблюдение».
    Каноническое прочтение статуса — решение `D-34` в
    `.planning/phases/05-tarify/05-CONTEXT.md`; пятого статуса той же прохибиции
    здесь не формулируется. Объём исключения назван числом с датой отсчёта:
    остаток свыше одного календарного месяца в ветке нечитаемой цены не
    переносится — 365 дней остатка дают 59 дней от 2026-01-10 и 61 день от
    2026-08-19, то есть предоплативший год теряет около одиннадцати месяцев
    оплаченного времени
    (`test_a_remainder_longer_than_a_month_is_capped_at_one_month`).
    ⚠️ ПРЕЖНЯЯ РЕДАКЦИЯ ЭТОГО ПРЕДЛОЖЕНИЯ объявляла прохибицию соблюдённой
    безусловно и утверждала, что ни один разрешённый переход остатка не
    затрагивает вовсе; соседний модуль о той же ветке говорил обратное, и спор
    двух объявлений одного денежного пути закрыт в сторону того, которое
    совпало с прогоном. Что перечень действительно кончается здесь, закреплено
    машиной —
    `test_neither_declaration_claims_the_plan_only_grows_at_the_apply_stage`; что
    разрешённый переход не затрагивает остатка сверх объявленного исключения —
    `test_an_upgrade_does_not_burn_the_paid_remainder`.

    ЦЕНА ЭТОГО ВАРИАНТА НАЗВАНА ПРЯМО (T-05-51), И НАЗВАНА ВЕЛИЧИНОЙ, А НЕ
    ЭПИТЕТОМ. Форма — `convert-remainder` (решение владельца, чекпойнт задачи 1
    плана `05-18`): повышение СЧИТАЕТ ДОПЛАТУ. Неистраченный остаток, купленный
    по цене младшего плана, конвертируется в дни старшего ПО ОТНОШЕНИЮ ЦЕН —
    `converted_remainder` в `app/application/billing/subscription_period.py`, — и
    уже к получившейся точке добавляется оплаченный месяц (`next_expiry`). То
    есть повышение получает столько дней старшего тарифа, сколько СТОИЛ его
    остаток, не меньше одного дня у живого остатка: 25 дней Basic по 1490 ₽/мес
    дают 7 дней Pro по 4900 ₽/мес, а не 25.

    ⚠️ ПРЕЖНЯЯ РЕДАКЦИЯ ЭТОГО АБЗАЦА ОПИСЫВАЛА СЕМАНТИКУ, КОТОРОЙ БОЛЬШЕ НЕТ, И
    ОПИСЫВАЛА ЕЁ ЭПИТЕТОМ, ДОПУСКАВШИМ ДВА ПРОЧТЕНИЯ НА ДВА ПОРЯДКА. Она
    говорила, что повышение отдаёт лимиты старшего тарифа на остаток младшего
    бесплатно, — и «остаток» читался как величина, ограниченная одним периодом,
    тогда как код не ограничивал её ничем: двенадцать предоплаченных месяцев
    `basic` плюс один платёж `pro` давали тринадцать месяцев Pro за 22 780 ₽ при
    прейскуранте 63 700 ₽ (гэп 1 раунда 5). Решение принималось по первому
    прочтению, а исполнялось второе. Подарком после `convert-remainder` остаётся
    ровно одно и оно ограничено: применения лимитов в системе нет вовсе (D-08),
    поэтому «лимиты Pro» сегодня не дают доступа ни к чему сверх показа. Что
    горизонт больше не переезжает целиком, закреплено
    `test_a_prepaid_horizon_is_not_converted_to_the_senior_plan_for_one_month` и
    `test_an_upgrade_with_one_paid_month_still_does_not_burn_the_remainder`.

    ⚠️ ОТСЧЁТ ПРИ ПОВЫШЕНИИ ИДЁТ НЕ ОТ `expires_at`, А ОТ КОНВЕРТИРОВАННОЙ ТОЧКИ,
    и это прямое следствие абзаца выше. От существующего `expires_at` срок
    считается ТОЛЬКО там, где план НЕ меняется (повтор своего тарифа). Там, где
    цену любого из двух планов прочитать нельзя (Free, план, выпавший из
    конфига), база — `capped_carryover`
    (`app/application/billing/subscription_period.py`), и порядка отсчёта,
    действовавшего ДО плана `05-22`, там больше нет: он и БЫЛ гэпом 1 раунда 6.
    Обещание «остаток не сгорает» держится ТОЛЬКО В ОБЪЁМЕ ВЕРХНЕЙ ГРАНИЦЫ:
    остаток КОРОЧЕ одного календарного месяца переносится целиком и не теряет ни
    дня (`test_a_remainder_shorter_than_a_month_is_carried_whole`), а остаток
    ДЛИННЕЕ месяца не переносится в части свыше месяца — 365 дней остатка дают
    59 дней от 2026-01-10 и 61 день от 2026-08-19
    (`test_a_remainder_longer_than_a_month_is_capped_at_one_month`). Статус
    прохибиции `05-01` формулируется НЕ ЗДЕСЬ: каноническое прочтение — решение
    `D-34` в `.planning/phases/05-tarify/05-CONTEXT.md`, и абзац его цитирует, а
    не сочиняет своё. ⚠️ ПРЕЖНЯЯ РЕДАКЦИЯ ЭТОГО АБЗАЦА называла ветку
    нечитаемой цены возвратом к порядку, действовавшему до плана `05-22`, и
    объявляла обещание о сохранении остатка безоговорочным на обеих ветках. До
    плана `05-22` это было верно; с него перестало — граница объявлена одной
    чистой функцией и читается кодом. Закреплено
    `test_an_upgrade_does_not_burn_the_paid_remainder` и
    `test_an_upgrade_from_free_does_not_carry_the_whole_horizon`.

    ⚠️ У ПРАВИЛА ДВЕ СТАДИИ, И ОБЕ ЧИТАЮТ ОДНО ОБЪЯВЛЕНИЕ —
    `switch_is_refused` из `app/application/billing/plan_switch.py`. Гард формы
    решает, ПРОДАВАТЬ ЛИ; здесь решается, что делать с УЖЕ УПЛАЧЕННЫМ. Пока
    сверка стояла только на входе, правило не выполнялось вовсе в самом
    достижимом сценарии: пользователь без подписки заводил два платежа — Pro,
    затем Basic, — гард не участвовал ни в одном нажатии (действующей подписки
    на тот момент не было), и оплаченный месяц старшего тарифа становился днями
    младшего (гэп 1, `05-VERIFICATION.md`). Что обе стадии читают ОДНО
    объявление, закреплено `test_both_stages_read_the_same_declaration_of_the_rule`;
    что названный сценарий закрыт —
    `test_a_pro_deal_sold_before_any_subscription_is_not_erased_by_a_later_basic`.

    ЧТО ИМЕННО ДЕЛАЕТ ПОДТВЕРЖДЁННЫЙ ПЛАТЁЖ. Он исполняется здесь ЛЮБОЙ, и
    деньги ВСЕГДА превращаются в дни: отказать оплаченному платежу значило бы
    взять деньги и не выдать ничего — худший из возможных исходов. Закреплено
    `test_a_refused_payment_buys_days_of_what_it_paid_for` (отвергнутый переход
    всё равно покупает дни) и
    `test_a_confirmed_higher_plan_is_applied_at_the_apply_stage` (разрешённый —
    применяется).

    ⚠️ ЧТО ПРОИСХОДИТ С ПЛАНОМ, ОПИСАНО ЗДЕСЬ ТЕМ, ЧТО ИСПОЛНЯЕТСЯ, А НЕ ТЕМ,
    ЧТО ОБЪЯВЛЕНО. Прежняя редакция этого абзаца утверждала ИНВАРИАНТ: план
    здесь якобы только повышается. Верификация раунда 6 опровергла его прогоном
    (`WR-03`): подписка `pro` с ЖИВЫМ сроком плюс подтверждённый платёж `basic`,
    несущий записанное разрешение `True`, даёт `plan == "basic"` — то есть
    ПОНИЖЕНИЕ, и до плана `05-24` оно происходило без единой записи в журнале.
    РЕШЕНИЕ ВЛАДЕЛЬЦА ПО КОНФЛИКТУ (чекпойнт задачи 1 плана `05-24`, вариант
    `record-wins`): D-28 остаётся в силе, а объявление снимается. Настоящее
    правило звучит так — `upgrade-only` есть правило стадии НАМЕРЕНИЯ, а не
    инвариант обеих стадий; стадия применения исполняет платёж КАК ПРОДАН. Что
    НИ ОДНО объявление больше не утверждает роста плана, закреплено машиной —
    `test_neither_declaration_claims_the_plan_only_grows_at_the_apply_stage`; что
    понижение достижимо и оставляет свой след —
    `test_a_demotion_by_the_recorded_answer_leaves_its_own_downgrade_trace`.

    ОТСЮДА ТРИ ИСХОДА, И У КАЖДОГО СВОЁ ИМЯ В ЖУРНАЛЕ. (1) Записанного ответа
    нет (`NULL`) и правило отвергает переход, либо записанный ответ есть и он
    ОТКАЗ, а оплаченный срок жив — план СОХРАНЯЕТСЯ, срок двигается на долю
    месяца (D-29), и расхождение уплаченного и действующего тарифа записывается
    ключом `subscription_plan_preserved` уровня `warning`. (2) Переход ведёт
    ВВЕРХ — тариф применяется, оплаченный остаток конвертируется по отношению
    цен. (3) Записанное разрешение есть, а переход ведёт ВНИЗ — тариф
    применяется ТОЖЕ, потому что так была продана сделка: остаток старшего
    тарифа конвертируется по отношению цен в дни младшего (25 дней Pro по
    4900 ₽/мес дают около 82 дней Basic по 1490 ₽/мес), то есть деньги примерно
    сохраняются, а тариф меняется вниз. Исход (3) достижим через окно СРОКА
    ДАВНОСТИ незакрытого намерения (`PENDING_INTENT_TTL_HOURS`); окно числится
    записанным долгом фазы и планом `05-24` не закрывается, поэтому исход
    получает СОБСТВЕННЫЙ ключ журнала уровня `warning` — разбирающий обращение
    обязан уметь назвать человеку, что произошло.

    СКОЛЬКО ДНЕЙ ПОЛУЧАЕТ ПЛАТЁЖ, ЧЕЙ ПЕРЕХОД ОТВЕРГНУТ (D-29). Не полный месяц
    действующего тарифа, а ДОЛЮ месяца по отношению уплаченной суммы к цене
    действующего плана, не меньше одного дня. Полный месяц здесь был денежной
    дырой, а не щедростью: платёж `basic` за 1490 ₽ покупал месяц `pro`
    стоимостью 4900 ₽, и число повторов не ограничивало ничто. Принцип «деньги
    всегда превращаются в дни» решением D-29 не отменён, а измерен: отказ в
    сдвиге срока был среди отвергнутых вариантов именно потому, что вводил бы
    исход «взяли и не дали ничего».
    Закреплено `test_a_refused_payment_buys_days_of_what_it_paid_for`, который
    проверяет ЧИСЛО выданных дней, а не факт сдвига.

    ЧТО РЕШАЕТ, ПРИМЕНЯТЬ ЛИ ПЛАН (D-28). Не сегодняшнее состояние подписки, а
    ЗАПИСАННОЕ РАЗРЕШЕНИЕ `payments.switch_authorized` — ответ гарда, снятый в
    момент ПРОДАЖИ и уехавший на строку платежа. Между продажей и подтверждением
    лежит вся сессия оплаты у ЮKassa, и состояние подписки за это время меняется;
    пока ответ нигде не сохранялся, эта стадия принимала решение ЗАНОВО и выдавала
    не то, что было продано. Правило спрашивается только у строк со
    `switch_authorized IS NULL` — пакетных и заведённых до ревизии `0019`.
    Закреплено
    `test_the_deal_cannot_be_sold_without_recording_its_authorization` (ответ
    записывается в момент продажи) и
    `test_a_legacy_payment_without_a_recorded_answer_still_decides_by_the_rule`
    (ветка `NULL`).

    ЧТО ПРОИСХОДИТ, КОГДА ОПЛАЧЕННЫЙ СРОК УЖЕ ИСТЁК (решение владельца,
    чекпойнт плана 05-13, вариант `apply-after-expiry`). Когда оплаченный срок
    истёк, отказ снимается на ОБЕИХ стадиях: защищать нечего — период кончился,
    и сжигать у пользователя больше нечего. План платежа ПРИМЕНЯЕТСЯ, каким бы он ни был,
    срок считается от сегодня (D-04), и следа `subscription_plan_preserved` на
    этом пути НЕТ — сохранять нечего, тариф выдан. Это устраняет асимметрию,
    которую отчёт верификации назвал дефектной: пользователь БЕЗ строки
    подписки и пользователь с ИСТЁКШЕЙ строкой получают при одном намерении
    один исход, а не противоположные. Закреплено
    `test_an_expired_period_lets_the_paid_plan_through_at_the_apply_stage` (план
    применяется), `test_the_expired_period_writes_no_preserved_plan_warning`
    (следа нет) и
    `test_an_expired_period_lifts_the_recorded_refusal_and_leaves_no_trace`
    (истёкший срок снимает и ЗАПИСАННЫЙ отказ).

    ПРИЗНАК ЖИВОСТИ ОПЛАЧЕННОГО СРОКА — `subscription_is_live` из
    `app/application/billing/subscription_period.py`, ЕДИНСТВЕННОЕ его
    объявление на проект; правило принимает его обязательным keyword-only
    аргументом `period_is_live`, поэтому спросить правило, не сказав, есть ли
    что защищать, физически нельзя. ⚠️ ПОРЯДОК: признак снимается ДО сдвига
    срока. `next_expiry` перезаписывает величину, по которой признак считается,
    и перестановка двух операторов местами вернула бы блокер МОЛЧА — правило
    получало бы «живо» всегда. Порядок закреплён тестом по синтаксическому дереву
    `test_the_liveness_is_sampled_before_the_date_moves`.
    """
    subscription = await _active_subscription(db, db_payment.user_id)

    if subscription is not None:
        _apply_extension(subscription, db_payment, now)
        return

    # ⚠️ ВЕТКА ПЕРВОЙ ВСТАВКИ И ГРАНИЦА ПЕРЕНОСА ОСТАТКА: РЕШЕНИЕ ЯВНОЕ, А НЕ
    # УНАСЛЕДОВАННОЕ УМОЛЧАНИЕ (T-05-108). Конвертировать здесь НЕЧЕГО, и это
    # свойство состояния, а не упущение: активной строки подписки нет вовсе,
    # значит нет ни прежнего плана, ни оплаченного остатка, купленного по другой
    # цене. Платёж покупает ровно один месяц СВОЕГО плана от сегодня. Обойти
    # границу этой веткой нельзя по построению — обходить нечего. Закреплено
    # `test_the_first_purchase_takes_the_plan_from_the_payment` и
    # `test_the_first_subscription_still_takes_its_plan_from_the_payment`.
    #
    # ⚠️ ЗАПИСАННЫЙ ОТКАЗ ЗДЕСЬ НЕ КОНСУЛЬТИРУЕТСЯ, И ЭТО НАЗВАНО ЯВНО, А НЕ
    # ОСТАВЛЕНО УМОЛЧАНИЕМ (`missing:` №4 раунда 6). Асимметрия настоящая: один
    # и тот же записанный ответ СОБЛЮДАЕТСЯ веткой продления выше и
    # ИГНОРИРУЕТСЯ здесь. Причина её в СОСТОЯНИИ, а не в упущении — отказывать
    # нечему. Прежнего плана не существует; правило смены тарифа сравнивает
    # РАНГИ ДВУХ планов, а не выдаёт ранг из воздуха, и вопрос «понижение ли
    # это» здесь не имеет ответа вовсе. Ровно то же свойство, что у границы
    # переноса абзацем выше, и записано оно рядом по той же причине: следующий
    # читатель, увидев чтение колонки в одной ветке и молчание в другой, иначе
    # «приведёт их в соответствие» и запретит первому платежу выдать тариф.
    # Закреплено `test_the_first_subscription_still_takes_its_plan_from_the_payment`:
    # первый платёж выдаёт свой тариф независимо от записанного ответа.
    try:
        async with db.begin_nested():
            db.add(
                Subscription(
                    user_id=db_payment.user_id,
                    plan=db_payment.plan or "free",
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


def _plan_price(plan_id: str | None) -> Decimal | None:
    """Цена плана из конфига, либо `None`, если её нельзя прочитать.

    `None` ВМЕСТО ИСКЛЮЧЕНИЯ — ТРЕБОВАНИЕ ВЫЗЫВАЮЩЕГО, А НЕ ВКУС. Единственный
    потребитель — `_apply_extension`, работающая внутри обработчика уведомления
    ЮKassa. Необработанное исключение там означает 5xx на уведомлении, а 5xx
    запускает цикл повторов и оставляет платёж `pending` навсегда: класс отказа,
    уже стоивший фазе находки `WR-04` раунда 2. Перечень тарифов правится
    окружением, а действующий план записан в строке подписки — разойтись они
    могут в любую сторону и без нашего участия.
    Закреплено
    `test_a_price_that_cannot_be_read_falls_back_to_the_whole_month`:
    вызывающий получает `None` и уходит на откат, а не ловит исключение.

    ⚠️ НЕПРИГОДНЫМ СЧИТАЕТСЯ И САМ ПЕРЕЧЕНЬ, А НЕ ТОЛЬКО ЦЕНА В НЁМ. Прежняя
    редакция этого объявления обещала ровно то же, что и нынешняя, но тело
    обещания не держало: защита накрывала ТОЛЬКО приведение цены к `Decimal`, а
    обход `parsed_plan_limits` стоял ВНЕ неё — то есть «`None` вместо
    исключения» было верно ровно для той половины входа, которую правит не
    оператор. `PLAN_LIMITS` — строка окружения, разбираемая `json.loads` без
    схемы и без валидации, и верификация раунда 7 воспроизвела на ней ЧЕТЫРЕ
    формы отказа: битый JSON — `JSONDecodeError`, объект вместо списка —
    `AttributeError`, список строк — `AttributeError`, `null` — `TypeError`.
    Сегодня все четыре дают `None` и собственную запись в журнале уровня
    `error` — ключ назван один раз, в теле ниже. Закреплено
    `test_a_malformed_plan_list_does_not_break_the_notification`, который на
    прежнем теле краснел на каждой из четырёх форм.

    ⚠️ НАЗВАНО И ТО, ЧЕГО ЭТА ЗАЩИТА НЕ ДЕЛАЕТ: она НЕ ВАЛИДИРУЕТ КОНФИГ НА
    СТАРТЕ. Перечень тарифов и строка подписки расходятся В РАБОТЕ и без нашего
    участия — стартовая проверка такого расхождения не видит вовсе и дала бы
    ложное чувство закрытия, потому что о ней отчитались бы как о защите.
    Поэтому единственное место защиты — здесь: денежный путь уже считает это
    место тотальным. Тем же
    `test_a_malformed_plan_list_does_not_break_the_notification` это и
    закреплено — он ходит через настоящий обработчик уведомления, а не через
    старт приложения.

    Непригодной считается цена, которой нет, которая не читается как `Decimal`,
    которая не конечна, и которая не больше нуля. Последнее — не паранойя: у
    плана Free цена объявлена `"0.00"`, и деление на неё было бы отказом
    обработчика на самом достижимом из планов.

    ⚠️ КОНЕЧНОСТЬ — ЧЕТВЁРТЫЙ ЧЛЕН ТОГО ЖЕ ПЕРЕЧНЯ, А НЕ ОГОВОРКА К НЕМУ, и
    классифицируется она ВНУТРИ той же защиты, что и разбор. Форма достижима
    ПРАВКОЙ ОКРУЖЕНИЯ, а не ошибкой программиста: `json.loads` принимает голые
    литералы `NaN` и `Infinity` ПО УМОЛЧАНИЮ и переполняет числовой литерал
    избыточного порядка (`1e400`) в бесконечность, а `PLAN_LIMITS` есть строка
    окружения, разбираемая без схемы (`app/config.py:120-121`). ⚠️ ПРЕЖНЯЯ
    РЕДАКЦИЯ ЭТОГО АБЗАЦА НАЗЫВАЕТСЯ, А НЕ СТИРАЕТСЯ: она обещала «`None`
    вместо исключения» БЕЗУСЛОВНО и на нефинитной цене обещания НЕ ДЕРЖАЛА —
    сравнение `result > 0` стояло ВНЕ `try`, поэтому `Decimal("NaN") > 0`
    поднимало `InvalidOperation`, а `Decimal("Infinity")` сравнение проходила и
    уезжала в `converted_remainder`, где `int()` давал `OverflowError`. Обе
    формы доходили до `app/routes/billing.py:200-202` и превращались в 500 на
    уведомлении ЮKassa при УЖЕ СПИСАННЫХ деньгах. ПРИЁМ ВЗЯТ У `format_amount`
    (`app/pages/common.py`, план 05-09), а не изобретён здесь: класс был
    известен этому дереву с названной причиной за девятнадцать волн до правки —
    «`NaN` и `Infinity` — валидные значения `Decimal`, и `except` вокруг
    разбора их не видит». Закреплено
    `test_a_non_finite_price_does_not_five_hundred_the_notification` (сквозной
    случай до HTTP-кода настоящего маршрута) и расширенным набором форм
    `test_a_malformed_plan_list_does_not_break_the_notification`.

    Помощник СИНХРОННЫЙ: настройки читаются синхронно, а `_apply_extension`
    обязана остаться синхронной и в БД не писать сама — `commit` делает
    `handle_webhook`, и порядок транзакции плана 05-08 не трогается.
    """
    unreadable = False
    result: Decimal | None = None
    try:
        for plan in get_settings().parsed_plan_limits:
            if not isinstance(plan, dict):
                # Сломан один элемент из трёх — остальные читаются, и чужая
                # строка в перечне не имеет права отнять у покупателя дни на
                # его собственном, исправном плане. Пропуск оставляет след:
                # флаг ниже доводит его до журнала. Закреплено
                # `test_a_malformed_plan_list_does_not_break_the_notification`.
                unreadable = True
                continue
            if plan.get("id") != plan_id:
                continue
            # КЛАССИФИКАЦИЯ ЦЕЛИКОМ ЖИВЁТ ВНУТРИ ЭТОЙ ЗАЩИТЫ, И ЭТО ПРИЁМ
            # `format_amount` (`app/pages/common.py:283`, план 05-09), а не
            # изобретение здесь: `NaN` и `Infinity` суть ВАЛИДНЫЕ значения
            # `Decimal`, поэтому `except` вокруг разбора их не видит, а
            # сравнение `NaN > 0` поднимает `InvalidOperation`. Порядок —
            # разбор, конечность, знак. За пределами защиты не остаётся НИ
            # ОДНОЙ операции над `Decimal`: последняя строка функции возвращает
            # `result` и ничего не вычисляет. Закреплено
            # `test_a_non_finite_price_does_not_five_hundred_the_notification`.
            try:
                candidate = Decimal(str(plan.get("price")))
                result = (
                    candidate
                    if candidate.is_finite() and candidate > 0
                    else None
                )
            except (InvalidOperation, TypeError, ValueError):
                # Цена этого плана не читается — штатный исход, а не поломка
                # перечня, и собственного следа поломки он не оставляет:
                # свой ключ пишет ветка отката в `_apply_extension`. Закреплено
                # `test_a_price_that_cannot_be_read_falls_back_to_the_whole_month`.
                result = None
            break
    except (InvalidOperation, TypeError, ValueError, AttributeError):
        # `JSONDecodeError` — подкласс `ValueError` и накрывается им;
        # `AttributeError` добавлен ради формы «элемент перечня не словарь».
        # Перечень типов оставлен закрытым, а не заменён на `Exception`: иначе
        # опечатка в имени поля отдала бы `None` молча. Закреплено
        # `test_a_malformed_plan_list_does_not_break_the_notification`.
        unreadable = True

    if unreadable:
        # Собственный ключ, а не `subscription_prorating_skipped`: без него
        # «перечень сломан целиком» неотличимо от «цена этого плана не
        # читается», а второе есть штатный исход, тогда как первое — авария
        # окружения. Содержимое переменной окружения в запись не попадает —
        # там цены, состав тарифов и возможные внутренние идентификаторы.
        # Закреплено
        # `test_a_malformed_plan_list_does_not_break_the_notification`.
        logger.error("plan_limits_unreadable", plan_id=plan_id)

    return result

def _apply_extension(
    subscription: Subscription, db_payment: Payment, now: datetime
) -> None:
    """Двигает срок действующей подписки и применяет план — ПО ЗАПИСАННОМУ ОТВЕТУ.

    ПОРЯДОК ДВУХ ДЕЙСТВИЙ ЗДЕСЬ — ПРАВИЛО, А НЕ ОФОРМЛЕНИЕ.

    ПЕРВЫМ действием тела снимается признак живости оплаченного срока —
    `subscription_is_live` от `subscription.expires_at`. Раньше сдвига он стоит
    не для красоты: величина, по которой он считается, через оператор перестанет
    существовать в прежнем значении, и признак, снятый после, вернул бы «живо»
    при любом состоянии подписки. Перестановка этих двух операторов местами
    восстанавливает блокер истёкшего срока молча, поэтому порядок закреплён
    тестом по синтаксическому дереву `test_the_liveness_is_sampled_before_the_date_moves`
    (T-05-63), а не вниманием читателя.

    ВТОРЫМ действием принимается решение о ПЛАНЕ, и первым его источником служит
    ЗАПИСАННЫЙ ФАКТ (D-28): `db_payment.switch_authorized` несёт ответ гарда,
    снятый в момент ПРОДАЖИ. Отказ есть отрицание записанного разрешения ПРИ
    ЖИВОМ оплаченном сроке, и правило по текущему состоянию БД тогда не
    спрашивается вовсе. ⚠️ ЧЛЕН ЖИВОСТИ ЗДЕСЬ НЕ ОФОРМЛЕНИЕ: истёкший срок
    снимает отказ и у ЗАПИСАННОГО ответа тоже, потому что защищать нечего
    независимо от того, кто отказ вынес (`WR-02` раунда 6); без него записанный
    `False` пережил бы собственный период. `NULL`
    означает «правило не спрашивали» — пакетный платёж либо строка старше
    ревизии `0019`, — и только для неё отказ считается `switch_is_refused` по
    сегодняшнему состоянию, как и до этого плана. Закреплено
    `test_a_legacy_payment_without_a_recorded_answer_still_decides_by_the_rule`
    (ветка `NULL`),
    `test_a_confirmed_lower_plan_does_not_strip_the_higher_one_at_the_apply_stage`
    (записанный отказ при живом сроке) и
    `test_an_expired_period_lifts_the_recorded_refusal_and_leaves_no_trace`
    (член живости).

    ТРЕТЬИМ действием двигается срок, и он двигается В КАЖДОЙ ВЕТКЕ СВОЙ, а не
    одним оператором выше решения о плане. Полный период (`next_expiry`) — там,
    где выдан и тариф, и у платежа без плана, которому менять нечего. Доля месяца
    (`prorated_expiry`, D-29) — там, где план отвергнут, и делимое НАЗВАНО ЗДЕСЬ
    ВЫРАЖЕНИЕМ, А НЕ ЭПИТЕТОМ: `paid / price(subscription.plan)` — уплаченная
    сумма, отнесённая к цене ДЕЙСТВУЮЩЕГО плана, ровно как объявляет
    `prorated_expiry` в `app/application/billing/subscription_period.py`.
    ⚠️ АЛЬТЕРНАТИВНОЕ ПРОЧТЕНИЕ («по цене плана ПЛАТЕЖА») опасно не оттенком:
    1490 / 1490 даёт полный месяц старшего тарифа, 1490 / 4900 — около девяти
    дней, и первое и было денежной дырой раунда 4. Прежняя редакция этого абзаца
    утверждала именно первое, поэтому следующая «починка» пошла бы по тексту и
    вернула бы закрытый блокер правкой, выглядящей приведением кода в соответствие
    с комментарием. Безусловной осталась не строка, а
    ПРИНЦИП, и он обязан быть назван здесь дословно: ДЕНЬГИ ВСЕГДА ПРЕВРАЩАЮТСЯ
    В ДНИ, «не выдать ничего» по-прежнему худший из исходов, и решение о плане не
    имеет права обнулить начисление — поэтому у доли месяца есть нижняя граница
    в один день. Прежняя редакция этого абзаца объявляла безусловным сам ОПЕРАТОР
    сдвига, стоявший выше решения о плане; именно эта безусловность и была второй
    половиной гэпа — отвергнутый платёж покупал полный месяц действующего
    старшего тарифа за цену младшего. Что делимое читается по цене ДЕЙСТВУЮЩЕГО
    плана, закреплено `test_a_refused_payment_buys_days_of_what_it_paid_for`; что
    нечитаемая цена уводит на откат к полному месяцу —
    `test_a_price_that_cannot_be_read_falls_back_to_the_whole_month`.

    ЧЕТВЁРТЫМ действием, и только на РАЗРЕШЁННОМ переходе между РАЗНЫМИ планами,
    оплаченный остаток переносится ПО ДЕНЬГАМ, а не по дням (форма
    `convert-remainder`, решение владельца, чекпойнт задачи 1 плана 05-18).
    До него пара «сдвиг срока плюс присваивание плана» одним движением переводила
    на новый тариф ВЕСЬ накопленный горизонт: `subscription.plan` — скаляр без
    истории, поэтому двенадцать предоплаченных месяцев `basic` плюс один платёж
    `pro` давали тринадцать месяцев Pro за 22 780 ₽ при прейскуранте 63 700 ₽, и
    величина эта не имела верхней границы ни в коде, ни в схеме, а управлял ею
    покупатель (гэп 1 раунда 5). Правило переноса объявлено ОДИН раз —
    `converted_remainder` в `app/application/billing/subscription_period.py`, — и
    ЧИТАЕТСЯ здесь, а не повторяется; нижняя граница в один день у живого
    остатка гарантирована `prorated_days`. Обещание «оплаченный остаток не
    сгорает» держится ТОЛЬКО В ОБЪЁМЕ ВЕРХНЕЙ ГРАНИЦЫ: остаток короче одного
    календарного месяца переносится целиком и не теряет ни дня
    (`test_a_remainder_shorter_than_a_month_is_carried_whole`), а остаток длиннее
    месяца не переносится в части свыше месяца — 365 дней остатка дают 59 дней
    от 2026-01-10 и 61 день от 2026-08-19
    (`test_a_remainder_longer_than_a_month_is_capped_at_one_month`). Когда цену
    любого из двух планов прочитать нельзя (Free, план, выпавший из конфига),
    база — `capped_carryover` (`app/application/billing/subscription_period.py`),
    и тело `_apply_extension` ЧИТАЕТ его, а не считает выражением у себя.
    Исключений здесь нет и быть не может: 5xx на уведомлении запустил бы цикл
    повторов ЮKassa и оставил бы платёж `pending` навсегда (T-05-104).
    ⚠️ ПРЕЖНЯЯ РЕДАКЦИЯ ЭТОГО АБЗАЦА объявляла обещание о сохранении остатка
    безоговорочно верным, а ветку нечитаемой цены — возвратом к порядку,
    действовавшему до плана `05-22`; с плана `05-22` оба утверждения неверны.
    Статус прохибиции `05-01` формулируется НЕ ЗДЕСЬ: каноническое прочтение —
    решение `D-34` в `.planning/phases/05-tarify/05-CONTEXT.md`. Закреплено
    `test_a_confirmed_higher_plan_is_applied_at_the_apply_stage` и
    `test_an_upgrade_does_not_burn_the_paid_remainder`.

    Сравнение рангов читает `switch_is_refused` — ТО ЖЕ объявление, что и гард
    формы `POST /billing/subscribe`. Вторая копия сравнения здесь и была тем
    дефектом, который закрывает план 05-11: гард на входе не срабатывает вовсе,
    когда действующей подписки на момент нажатия не было, и оплаченный месяц
    старшего тарифа становился днями младшего. Но план 05-11 объединил
    ОБЪЯВЛЕНИЕ правила и не объединил его ВХОДНЫЕ ДАННЫЕ: условие срока осталось
    на дисциплине вызывающего, гард его подавал, а эта стадия — нет. Поэтому
    условие приезжает в правило аргументом `period_is_live`, обязательным и
    keyword-only, а не вычисляется каждым вызывающим по своему усмотрению.
    Закреплено
    `test_a_paid_plan_without_a_rank_keeps_the_live_plan_at_the_apply_stage`.

    ЖУРНАЛ ВЕТКИ ОТКАЗА НАЗЫВАЕТ ТРИ ВЕЩИ СВЕРХ ПРЕЖНИХ: источник решения
    (записанный ответ или правило), число выданных дней и цену, по которой они
    посчитаны. Без них исход «выдано девять дней вместо тридцати» неотличим от
    «дни не выданы», и разбирающему обращение опереться не на что.

    Функция синхронная и в БД не пишет сама: `commit` делает `handle_webhook`,
    и заявка платежа с начислением обязаны остаться в одной транзакции (05-08).
    """
    # ⚠️ ПРИЗНАК СНИМАЕТСЯ ЗДЕСЬ, А НЕ СТРОКОЙ НИЖЕ, И ЭТО ЛОВУШКА, А НЕ
    # ОФОРМЛЕНИЕ. Следующий оператор ПЕРЕЗАПИСЫВАЕТ `subscription.expires_at` —
    # ту самую величину, по которой признак считается. Снятый после сдвига, он
    # всегда вернул бы «живо», отказ не снялся бы никогда, и блокер истёкшего
    # срока восстановился бы молча (T-05-63, гэп 1 раунда 3). Закреплено тестом
    # по синтаксическому дереву `test_the_liveness_is_sampled_before_the_date_moves`,
    # у которого есть свои негативные контроли —
    # `test_the_order_helper_reports_a_move_placed_above_the_sample`.
    period_is_live = subscription_is_live(subscription.expires_at, now)

    if not db_payment.plan:
        # У платежа без плана менять нечего, и полный период здесь верен: он
        # ничего не отвергает, а значит и делить месяц не на что.
        subscription.expires_at = next_expiry(subscription.expires_at, now)
        return

    # РЕШЕНИЕ ПРИНИМАЕТСЯ ЗДЕСЬ И ТОЛЬКО ЗДЕСЬ, И ПЕРВЫМ ЕГО ИСТОЧНИКОМ
    # СЛУЖИТ ЗАПИСАННЫЙ ФАКТ (D-28). У платежа, заведённого после ревизии
    # `0019`, ответ гарда снят в момент ПРОДАЖИ и лежит на строке; правило по
    # текущему состоянию БД тогда не спрашивается вовсе — именно этот
    # пересчёт по изменившейся строке и был корнем гэпа.
    # Закреплено
    # `test_a_legacy_payment_without_a_recorded_answer_still_decides_by_the_rule`.
    #
    # `NULL` означает «правило не спрашивали»: строка старше ревизии `0019`.
    # Для неё ответ считается правилом, как и до плана, — выдумать записанный
    # ответ хуже, чем пересчитать.
    if db_payment.switch_authorized is not None:
        # ⚠️ ЧЛЕН `period_is_live` СТОИТ И ЗДЕСЬ, А НЕ ТОЛЬКО В ВЕТКЕ ПРАВИЛА
        # (`WR-02` раунда 6). Истёкший срок снимает отказ независимо от того,
        # КТО отказ вынес: правило защищает УПЛАЧЕННОЕ, и когда период кончился,
        # защищать нечего — сжигать у пользователя больше нечего. Без этого
        # члена записанный `False` пережил бы собственный период: план платежа
        # не применялся бы там, где докстринг `_extend_subscription` обещает его
        # применение БЕЗУСЛОВНО, и `subscription_plan_preserved` писался бы там,
        # где тот же докстринг обещает отсутствие следа. Закреплено
        # `test_an_expired_period_lifts_the_recorded_refusal_and_leaves_no_trace`.
        #
        # ЗНАЧЕНИЕ `False` СЕГОДНЯ НЕДОСТИЖИМО ЧЕРЕЗ ФОРМУ — гард не продаёт
        # отвергнутого перехода, — но это свойство ГАРДА, а не колонки:
        # `app/models/payment.py` и ревизия `0019` ОБЕ явно требуют, чтобы
        # колонка умела его выразить, то есть проект сам объявляет его живым
        # контрактом, и от достижимости оно в одной правке гарда.
        refused = period_is_live and not db_payment.switch_authorized
        decided_by = "recorded_answer"
    else:
        refused = switch_is_refused(
            subscription.plan, db_payment.plan, period_is_live=period_is_live
        )
        decided_by = "rule"

    if refused:
        # УРОВЕНЬ `warning`, А НЕ `info`, И ЭТО НАМЕРЕННО. Платёж принят и
        # оплаченные дни выданы, но уплаченный тариф применён НЕ был — исход,
        # по которому к нам придёт человек. Без собственного ключа он прятался
        # бы за `subscription_payment_succeeded`, который печатает план ПЛАТЕЖА
        # как обычный успех, и разбирать обращение было бы не по чему.
        # Закреплено `test_the_preserved_plan_is_visible_in_the_log`.
        #
        # ИСТОЧНИК РЕШЕНИЯ НАЗЫВАЕТСЯ ОТДЕЛЬНЫМ ПОЛЕМ: два разных исхода
        # («так было продано» и «так решило правило, потому что продано было
        # неизвестно как») приходят в один ключ, и без поля разбирающий
        # обращение их не различит.
        # ДНИ СЧИТАЮТСЯ КАК `paid / price(subscription.plan)` (D-29): уплаченная
        # сумма, отнесённая к цене ДЕЙСТВУЮЩЕГО плана — ту самую цену и читает
        # СЛЕДУЮЩАЯ СТРОКА, `_plan_price(subscription.plan)`. Полный месяц здесь
        # и был второй половиной гэпа: 1490 ₽ покупали месяц Pro стоимостью
        # 4900 ₽, и повторов не ограничивало ничто.
        # Закреплено
        # `test_the_refused_branch_names_its_own_stage_in_the_journal`.
        #
        # ⚠️ ПРОЧТЕНИЕ «ПО ЦЕНЕ ПЛАНА ПЛАТЕЖА» ВЕРНУЛО БЫ ЭТУ ДЫРУ ОДНИМ СЛОВОМ:
        # 1490 / 1490 — полный месяц, 1490 / 4900 — около девяти дней. Прежняя
        # редакция этого комментария стояла НЕПОСРЕДСТВЕННО над строкой и
        # утверждала обратное ей; чинящий код по комментарию поменял бы аргумент
        # на `db_payment.plan` и назвал бы это приведением в соответствие.
        # Закреплено `test_a_refused_payment_buys_days_of_what_it_paid_for`,
        # который проверяет ЧИСЛО выданных дней, а не факт сдвига.
        price = _plan_price(subscription.plan)
        paid = None
        if price is not None:
            # КОНЕЧНОСТЬ КЛАССИФИЦИРУЕТСЯ ВНУТРИ ТОЙ ЖЕ ЗАЩИТЫ, ЧТО И РАЗБОР, И
            # ЭТО ПРИЁМ `_plan_price` И `format_amount` (`app/pages/common.py`,
            # план 05-09), А НЕ ИЗОБРЕТЕНИЕ ЗДЕСЬ. `NaN`, `Infinity` и `sNaN` —
            # ВАЛИДНЫЕ значения `Decimal`: разбор их ПРИНИМАЕТ, перечень типов
            # ниже их не видит вовсе, и отказ уезжал в `int(...)` внутри
            # `prorated_days`, роняя обработчик уведомления пятисоткой при уже
            # списанных деньгах (T-05-104). Ветка отката и её поле
            # `unreadable="amount"` были написаны и объявлены ЗАДОЛГО до этой
            # правки — менялся не контракт, а вход, который мимо них проходил.
            # За пределами защиты не остаётся ни одной операции над `Decimal`.
            # Закреплено
            # `test_an_unusable_amount_does_not_five_hundred_the_notification` и
            # `test_the_refused_branch_names_its_own_stage_in_the_journal`.
            try:
                candidate = Decimal(db_payment.amount_value)
                paid = candidate if candidate.is_finite() else None
            except (InvalidOperation, TypeError, ValueError):
                paid = None

        # ⚠️ ДОЛЯ МЕСЯЦА СЧИТАЕТСЯ ДО РАЗВИЛКИ, ПОТОМУ ЧТО НЕПРИГОДНОЙ ЦЕНУ
        # ДЕЛАЕТ НЕ ТОЛЬКО НЕЧИТАЕМОСТЬ. `prorated_expiry` отвечает `None`,
        # когда купленного срока НЕТ В КАЛЕНДАРЕ: `datetime` кончается 9999
        # годом, а цена в одну копейку при уплаченных 1490 ₽ покупает около
        # 4 619 000 дней. До этой правки такой ответ был `OverflowError`, он
        # доходил до `app/routes/billing.py:200-202` и давал 500 на уведомлении
        # при УЖЕ СПИСАННЫХ деньгах — тот же исход `T-05-104`, ради
        # недостижимости которого написан откат ниже. Делового потолка это НЕ
        # заводит: цена, купившая выразимый срок, отдаёт его целиком (D-29).
        # Закреплено
        # `test_a_price_beyond_the_calendar_does_not_five_hundred_the_notification`
        # и `test_a_span_that_the_calendar_can_express_is_not_capped`.
        new_expiry = None
        if price is not None and paid is not None:
            new_expiry = prorated_expiry(
                subscription.expires_at, now, paid=paid, price=price
            )

        if new_expiry is None:
            # ОТКАТ К ПОЛНОМУ МЕСЯЦУ, А НЕ ОТКАЗ В ДНЯХ, и не исключение.
            # Расхождение конфига с базой — наша беда, а не пользователя, и
            # отнимать за неё оплаченные дни не за что. Исключение здесь дало бы
            # 5xx на уведомлении и цикл повторов ЮKassa.
            # Закреплено
            # `test_a_price_that_cannot_be_read_falls_back_to_the_whole_month`.
            logger.warning(
                "subscription_prorating_skipped",
                user_id=db_payment.user_id,
                yookassa_id=db_payment.yookassa_payment_id,
                plan=subscription.plan,
                paid_plan=db_payment.plan,
                # ТРИ ИСХОДА, А НЕ ДВА, И У ТРЕТЬЕГО СВОЁ СЛОВО. `"price"` —
                # цену прочитать нельзя, `"amount"` — нельзя прочитать
                # уплаченную сумму, `"span"` — прочиталось ВСЁ, а срока,
                # купленного этими двумя числами, не существует. Сложить третий
                # исход с любым из первых двух значило бы сказать разбирающему
                # обращение неправду о том, что именно сломано.
                # Закреплено
                # `test_a_price_beyond_the_calendar_does_not_five_hundred_the_notification`.
                unreadable=(
                    "price"
                    if price is None
                    else "amount"
                    if paid is None
                    else "span"
                ),
                # ВЕТКУ НАЗЫВАЕТ ПОЛЕ, А НЕ КЛЮЧ (`IN-04`). Этот же ключ
                # испускает ветка КОНВЕРСИИ ниже, и словари `unreadable` у них
                # ПЕРЕСЕКАЮТСЯ (`"price"` есть у обеих): без поля разбирающий
                # обращение получает два разных исхода в одном событии и не
                # может сказать человеку, что именно произошло.
                # Закреплено
                # `test_the_refused_branch_names_its_own_stage_in_the_journal`.
                stage="prorate_refused",
            )
            granted_days = None
            new_expiry = next_expiry(subscription.expires_at, now)
        else:
            # База берётся ТЕМ ЖЕ объявлением, от которого посчитан сдвиг:
            # своя формула отсчёта здесь была бы третьей копией правила D-04.
            granted_days = (
                new_expiry - countdown_base(subscription.expires_at, now)
            ).days

        # ИСТОЧНИК РЕШЕНИЯ, ЧИСЛО ДНЕЙ И ЦЕНА — ТРИ ПОЛЯ, БЕЗ КОТОРЫХ ИСХОД
        # НЕОБЪЯСНИМ. «Выдано девять дней вместо тридцати» без них неотличимо от
        # «дни не выданы», и разбирающий обращение не сможет назвать человеку ни
        # числа, ни его основания.
        # Закреплено `test_the_preserved_plan_is_visible_in_the_log`.
        logger.warning(
            "subscription_plan_preserved",
            user_id=db_payment.user_id,
            yookassa_id=db_payment.yookassa_payment_id,
            plan=subscription.plan,
            paid_plan=db_payment.plan,
            decided_by=decided_by,
            granted_days=granted_days,
            price_basis=str(price) if price is not None else None,
        )
        subscription.expires_at = new_expiry
        return

    # ЧЕТВЁРТОЕ ДЕЙСТВИЕ — ВЕРХНЯЯ ГРАНИЦА НА ПЕРЕХОДЕ (форма `convert-remainder`,
    # решение владельца, чекпойнт задачи 1 плана 05-18). Пара операторов ниже
    # ОДНИМ движением переводила на новый тариф ВЕСЬ накопленный горизонт, потому
    # что `subscription.plan` — скаляр без истории: двенадцать предоплаченных
    # месяцев `basic` плюс один платёж `pro` давали тринадцать месяцев Pro за
    # 22 780 ₽ при прейскуранте 63 700 ₽, и величина эта росла линейно, а
    # управлял ею покупатель (гэп 1 раунда 5).
    # Закреплено
    # `test_a_prepaid_horizon_is_not_converted_to_the_senior_plan_for_one_month`.
    #
    # ТОЧКА ОТСЧЁТА ЧИТАЕТСЯ У `converted_remainder`, А НЕ СЧИТАЕТСЯ ЗДЕСЬ.
    # Правило переноса объявлено ОДИН раз, в `subscription_period.py`, рядом с
    # `next_expiry`, `countdown_base` и `prorated_expiry`; вторая копия условия
    # на денежном пути двигала бы срок от другой точки, и разница проявилась бы
    # только у пользователя с неистраченным остатком.
    # Закреплено `test_an_upgrade_does_not_burn_the_paid_remainder`.
    #
    # ⚠️ ЭТО ИНИЦИАЛИЗАЦИЯ ДЛЯ ОДНОГО-ЕДИНСТВЕННОГО СЛУЧАЯ, И НАЗВАН ОН ЗДЕСЬ
    # ЯВНО: «план НЕ меняется либо оплаченный срок МЁРТВ» — то есть условие ниже
    # ложно и переносить нечего. Во ВСЕХ остальных случаях базу присваивает
    # ветка, и ни одна из них не имеет права оставить это значение доживать до
    # сдвига срока: именно такое доживание в ветке отката и было гэпом 1,
    # пришедшим шестой раунд подряд (весь накопленный горизонт переезжал на
    # старший тариф за цену одного месяца). Закреплено
    # `test_a_prepaid_horizon_is_not_converted_to_the_senior_plan_for_one_month`.
    base = subscription.expires_at
    if period_is_live and db_payment.plan != subscription.plan:
        # ПРИЗНАК ЖИВОСТИ ВЗЯТ ТОТ ЖЕ, ЧТО СНЯТ ПЕРВЫМ ДЕЙСТВИЕМ, а не снят
        # заново: у мёртвого срока конвертировать нечего, и решение
        # `apply-after-expiry` (чекпойнт плана 05-13) этим условием не задето.
        # Закреплено
        # `test_an_expired_period_lets_the_paid_plan_through_at_the_apply_stage`.
        price_from = _plan_price(subscription.plan)
        price_to = _plan_price(db_payment.plan)

        # ⚠️ ПЕРЕНОС СЧИТАЕТСЯ ДО РАЗВИЛКИ ПО ТОЙ ЖЕ ПРИЧИНЕ, ЧТО И ДОЛЯ МЕСЯЦА В
        # ВЕТКЕ ОТКАЗА ВЫШЕ: дефект ОДИН на две ветки, а не два похожих.
        # `converted_remainder` зовёт тот же `prorated_days`, поэтому малая цена
        # НОВОГО плана даёт число дней, которого календарь от даты отложить не
        # может (25 дней Basic при цене `pro` в одну копейку — около 3 725 000
        # дней), и до этой правки такой перенос давал `OverflowError`, 500 на
        # уведомлении и вечный `pending` при списанных деньгах (T-05-104).
        # Закреплено
        # `test_a_price_beyond_the_calendar_does_not_break_the_conversion_branch`.
        converted = None
        if price_from is not None and price_to is not None:
            converted = converted_remainder(
                subscription.expires_at,
                now,
                old_price=price_from,
                new_price=price_to,
            )

        if converted is None:
            # ОТКАТ К ПРЕЖНЕМУ ПОВЕДЕНИЮ, А НЕ ОТКАЗ И НЕ ИСКЛЮЧЕНИЕ — та же
            # развилка и та же причина, что в ветке отказа выше: расхождение
            # конфига с базой наша беда, а не пользователя, а исключение здесь
            # дало бы 5xx на уведомлении и цикл повторов ЮKassa (T-05-104).
            # Ключ журнала переиспользован НАМЕРЕННО: событие ровно то же —
            # «цену прочитать нельзя, дни считаем по-старому», — и второй ключ
            # под тот же исход разошёлся бы с первым при первой же правке.
            # РАЗЛИЧАЕТ ВЕТКИ ТЕПЕРЬ ПОЛЕ, А НЕ КЛЮЧ (`IN-04`): значения
            # `prorate_refused` и `convert_remainder` постоянны и различны, и
            # оба утверждает тест — словари `unreadable` у двух испусканий
            # пересекаются, и по одному лишь ключу исход неразличим.
            # Закреплено
            # `test_an_unreadable_paid_plan_price_does_not_carry_the_whole_horizon`.
            logger.warning(
                "subscription_prorating_skipped",
                user_id=db_payment.user_id,
                yookassa_id=db_payment.yookassa_payment_id,
                plan=subscription.plan,
                paid_plan=db_payment.plan,
                # ТРИ ИСХОДА, А НЕ ДВА, И ТРЕТИЙ НАЗВАН СВОИМ СЛОВОМ — теми же
                # тремя словами, что и в ветке отказа выше: `"price"`,
                # `"paid_plan_price"`, `"span"`. Последнее означает, что обе
                # цены ПРОЧИТАНЫ, а момента, в который перенос упирается, не
                # существует.
                # Закреплено
                # `test_a_price_beyond_the_calendar_does_not_break_the_conversion_branch`.
                unreadable=(
                    "price"
                    if price_from is None
                    else "paid_plan_price"
                    if price_to is None
                    else "span"
                ),
                stage="convert_remainder",
            )
            # ⚠️ ВЕРХНЯЯ ГРАНИЦА СТОИТ И ЗДЕСЬ (форма `cap-one-month`, решение
            # владельца, чекпойнт задачи 1 плана 05-22). Конвертировать остаток
            # нечем — цены нет, — но переносить его ЦЕЛИКОМ нельзя: ровно это
            # доживание значения по умолчанию и есть гэп 1, приходящий шестой
            # раунд подряд (396 дней Pro за 22 780 ₽ при прейскуранте 63 700 ₽,
            # тогда как соседняя ветка того же решения даёт 140). Закреплено
            # `test_an_unreadable_paid_plan_price_does_not_carry_the_whole_horizon`.
            #
            # ЦЕНА ФОРМЫ НАЗВАНА ЧИСЛОМ, А НЕ ЭПИТЕТОМ. Обещание «оплаченный
            # остаток не сгорает» держится В ОБЪЁМЕ ГРАНИЦЫ: остаток короче
            # календарного месяца переносится целиком, а часть остатка СВЕРХ
            # месяца сгорает — исключение из прохибиции плана `05-01`,
            # допущенное сознательно.
            # Закреплено
            # `test_an_unreadable_paid_plan_price_does_not_carry_the_whole_horizon`.
            #
            # ПРАВИЛО ОБЪЯВЛЕНО ОДИН РАЗ И ЧИТАЕТСЯ ЗДЕСЬ, А НЕ СЧИТАЕТСЯ:
            # `capped_carryover` живёт в `subscription_period.py` рядом с
            # `countdown_base`, `next_expiry`, `prorated_expiry` и
            # `converted_remainder`. Своя формула на денежном пути была бы
            # третьей копией правила отсчёта D-04 — тем самым классом
            # расхождения, ради устранения которого заведён модуль.
            base = capped_carryover(subscription.expires_at, now)
        else:
            base = converted
            # УРОВЕНЬ `warning`, А НЕ `info`, по той же записанной причине, что у
            # `subscription_plan_preserved`: человек, у которого срок стал
            # КОРОЧЕ, чем он ожидал, придёт с этим к нам, и разбирающему
            # обращение нужны обе цены и обе величины в днях — иначе «перенесено
            # 110 дней вместо 364» неотличимо от «дни отняли».
            logger.warning(
                "subscription_remainder_converted",
                user_id=db_payment.user_id,
                yookassa_id=db_payment.yookassa_payment_id,
                plan=subscription.plan,
                paid_plan=db_payment.plan,
                price_from=str(price_from),
                price_to=str(price_to),
                remainder_days=(
                    countdown_base(subscription.expires_at, now)
                    - normalize_utc(now)
                ).days,
                converted_days=(base - normalize_utc(now)).days,
            )

    if switch_is_refused(
        subscription.plan, db_payment.plan, period_is_live=period_is_live
    ):
        # ДЕЙСТВУЮЩИЙ ТАРИФ МЕНЯЕТСЯ ВНИЗ, И ДО ЭТОЙ ЗАПИСИ ЭТО ПРОИСХОДИЛО
        # БЕССЛЕДНО (`WR-03` раунда 6, прохибиция BILL-05). Ветка отказа сюда не
        # заходит — записанное разрешение её сняло, — поэтому
        # `subscription_plan_preserved` не пишется, и разбирающему обращение
        # человеку опереться было бы не на что: строка подписки показывает
        # ТОЛЬКО итог, а не то, чем он вызван. Исход, по которому к нам придёт
        # человек, обязан быть РАЗБИРАЕМ по журналу, а не восстанавливаем по
        # догадке.
        # Закреплено
        # `test_a_demotion_by_the_recorded_answer_leaves_its_own_downgrade_trace`.
        #
        # УСЛОВИЕ ЧИТАЕТ ЕДИНСТВЕННОЕ ОБЪЯВЛЕНИЕ ПРАВИЛА, А НЕ СРАВНИВАЕТ РАНГИ
        # ЗАНОВО. Вторая копия сравнения на денежном пути и была тем классом
        # дефекта, ради устранения которого заведён `plan_switch.py`. Читается
        # оно здесь как вопрос «пропустило ли бы этот переход правило», и ответ
        # `True` при уже снятом отказе означает ровно одно: переход исполняется
        # по ЗАПИСАННОМУ разрешению вопреки тому, что правило сказало бы о
        # сегодняшнем состоянии подписки (D-28).
        # Закреплено `test_both_stages_read_the_same_declaration_of_the_rule`.
        #
        # ⚠️ ЦЕНА ЭТОГО ПРОЧТЕНИЯ НАЗВАНА, А НЕ ЗАМОЛЧАНА: правило отвергает и
        # НЕЗНАКОМЫЙ ранг, поэтому переход на план, выпавший из `PLAN_ORDER`,
        # попадёт в этот же ключ, хотя вниз он ведёт не обязательно. Отделить
        # один случай от другого можно было бы только вторым сравнением рангов
        # ЗДЕСЬ — то есть ровно той ценой, ради отказа от которой модуль правила
        # и заведён. Что незнакомый ранг отвергается, закреплено
        # `test_a_plan_without_a_rank_fails_closed` и
        # `test_a_paid_plan_without_a_rank_keeps_the_live_plan_at_the_apply_stage`.
        #
        # СОБСТВЕННЫЙ КЛЮЧ, А НЕ ПОЛЕ У СОСЕДНЕГО (`IN-04`): исход ДРУГОЙ — у
        # `subscription_plan_preserved` тариф СОХРАНЁН, здесь он ИЗМЕНЁН вниз, —
        # и сложить два несравнимых события в один ключ значило бы завести
        # третью пару, различимую только полем.
        # Закреплено
        # `test_a_demotion_by_the_recorded_answer_leaves_its_own_downgrade_trace`.
        logger.warning(
            "subscription_plan_downgraded",
            user_id=db_payment.user_id,
            yookassa_id=db_payment.yookassa_payment_id,
            plan=subscription.plan,
            paid_plan=db_payment.plan,
            decided_by=decided_by,
            # ПОЛЕ ПОСТОЯННО ПО ПОСТРОЕНИЮ И ОСТАВЛЕНО НАМЕРЕННО: при мёртвом
            # сроке правило отвечает `False`, и запись не испускается вовсе.
            # Читающий её видит главное — тариф сменён вниз при ЖИВОМ
            # оплаченном сроке, том самом состоянии, которое карточка младшего
            # плана обещает не трогать до его окончания.
            period_was_live=period_is_live,
        )

    subscription.expires_at = next_expiry(base, now)
    subscription.plan = db_payment.plan

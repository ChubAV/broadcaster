"""Повтор отправки из записи истории — пользовательская половина HIST-04.

Это ЕДИНСТВЕННОЕ отступление фазы от правила «интерфейс, а не функция»: здесь
заводится настоящее действие, и ведёт оно прямо в боевую очередь отправки.
Отправка в стороннюю группу необратима и тратит баланс, поэтому сверка
источника запроса, предпроверка целости тройки сущностей, гейт баланса и защита
от двойного нажатия — не украшения, а условие безопасности.

Файл собственный, а не дописка к `test_history.py`: тот держит фильтры и
счётчик, и смешивать с ними единственное необратимое действие раздела значило
бы прятать его среди чтения.

ЧЕГО ЗДЕСЬ НЕТ. Маршрутизация повтора по трём каналам и вторая линия проверок
внутри Celery-таска закреплены в `tests/test_worker/test_tasks.py` (план 04-03)
и сюда НЕ дублируются: два теста одного свойства расходятся при первой правке.
Здесь проверяется ровно граница HTTP — что уходит в очередь и что до неё не
доходит.
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import (
    STATUS_ACCOUNT_DISCONNECTED,
    STATUS_FAIL,
    STATUS_OK,
)
from app.models.ad import Ad
from app.models.group import Group
from app.models.message_balance import MessageBalance
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.models.user import User
from app.pages import history as history_module
from app.pages.history import RETRY_TASK_NAME

HISTORY_PY = Path(__file__).resolve().parents[2] / "app" / "pages" / "history.py"


# --- посев --------------------------------------------------------------------


async def _current_user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_other_user(db: AsyncSession) -> User:
    other = User(
        email="stranger@test.com",
        password_hash="x",
        name="Чужой",
        timezone="UTC",
    )
    db.add(other)
    await db.commit()
    await db.refresh(other)
    return other


async def _seed_balance(db: AsyncSession, user_id: int, amount: int = 100) -> None:
    db.add(MessageBalance(user_id=user_id, balance=amount))
    await db.commit()


async def _seed_triple(
    db: AsyncSession, user_id: int, *, account_status: str = "active"
) -> tuple[Ad, Group, MessengerAccount]:
    """Тройка сущностей, без которой повтор невозможен: объявление, группа, аккаунт."""
    account = MessengerAccount(
        user_id=user_id, type="wa", credentials="creds", status=account_status
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)

    group = Group(
        user_id=user_id,
        account_id=account.id,
        messenger_type="wa",
        group_external_id="-1005550001",
        name="Чат покупателей",
    )
    ad = Ad(user_id=user_id, title="Летняя распродажа", text="Скидки", images=[])
    db.add(group)
    db.add(ad)
    await db.commit()
    await db.refresh(group)
    await db.refresh(ad)
    return ad, group, account


async def _seed_log(
    db: AsyncSession,
    user_id: int,
    *,
    status: str = STATUS_FAIL,
    ad_id: int | None = None,
    group_id: int | None = None,
    error_message: str | None = "ECONNRESET",
) -> SendLog:
    log = SendLog(
        user_id=user_id,
        ad_id=ad_id,
        group_id=group_id,
        ad_title="Летняя распродажа",
        ad_text="Скидки",
        ad_images=[],
        group_name="Чат покупателей",
        messenger_type="wa",
        task_id="task-9f3c1d",
        status=status,
        error_message=error_message,
        sent_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def _seed_retryable(
    db: AsyncSession, user_id: int, *, status: str = STATUS_FAIL
) -> SendLog:
    """Запись, у которой цела вся тройка и хватает баланса."""
    ad, group, _account = await _seed_triple(db, user_id)
    await _seed_balance(db, user_id)
    return await _seed_log(
        db, user_id, status=status, ad_id=ad.id, group_id=group.id
    )


# --- окружение повтора --------------------------------------------------------
#
# Клиент очереди подменяется ПОДМЕНОЙ МОДУЛЯ — установленный в проекте образец
# (tests/test_routes/test_wa_sync_status.py). Именно он и требует локального
# импорта в обработчике: импорт, поднятый на уровень модуля, разрешился бы один
# раз при загрузке `app.pages.history`, и подмена до него не доехала бы —
# тест пошёл бы к настоящему брокеру.
#
# Гейт баланса подменяется по тому же образцу, что в тестах воркера
# (`patch("app.worker.tasks.check_balance_cached", ...)`): настоящий гейт лезет
# в Redis, которого в тестовой среде нет, и красил бы тесты чужой причиной.


class _RetryEnv:
    def __init__(self, send_task, balance):
        self.send_task = send_task
        self.balance = balance

    @property
    def queued(self) -> list:
        return self.send_task.call_args_list


def _retry_env(*, allowed: bool = True, reason: str = ""):
    """Контекст-менеджер подмены очереди и гейта баланса."""
    import contextlib

    @contextlib.contextmanager
    def _cm():
        fake_module = MagicMock()
        balance = AsyncMock(return_value=(allowed, reason))
        with patch.dict(sys.modules, {"app.worker.celery_app": fake_module}):
            with patch("app.pages.history.check_balance_cached", balance):
                yield _RetryEnv(fake_module.celery.send_task, balance)

    return _cm()


SAME_ORIGIN = {"Origin": "http://test"}


def _handler_source() -> str:
    """Тело обработчика повтора — от его объявления до следующего маршрута."""
    source = HISTORY_PY.read_text(encoding="utf-8")
    start = source.index("async def history_retry(")
    rest = source[start:]
    end = rest.find("\n@router")
    return rest if end == -1 else rest[:end]


# =============================================================================
# Сверка источника запроса (T-04-38, ASVS L1 V4.2.2)
# =============================================================================


@pytest.mark.asyncio
async def test_retry_rejects_a_cross_site_origin(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Чужой источник — 403, и задача НЕ ставится.

    Аутентификация проекта идёт cookie, а действие необратимо: страница,
    размещённая где угодно, иначе тратила бы баланс пользователя и слала бы
    рекламу в чужую группу, просто прокатившись на его сессии.
    """
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id)

    with _retry_env() as env:
        response = await authed_client.post(
            f"/history/{log.id}/retry",
            headers={"Origin": "https://evil.example"},
            follow_redirects=False,
        )

    assert response.status_code == 403, response.status_code
    assert env.queued == [], "межсайтовый запрос поставил задачу в очередь"


@pytest.mark.asyncio
async def test_retry_rejects_a_cross_site_fetch_context(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Заголовок контекста выборки со значением «не тот же источник» — 403."""
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id)

    with _retry_env() as env:
        response = await authed_client.post(
            f"/history/{log.id}/retry",
            headers={"Sec-Fetch-Site": "cross-site", "Origin": "http://test"},
            follow_redirects=False,
        )

    assert response.status_code == 403, response.status_code
    assert env.queued == [], "запрос чужого контекста выборки поставил задачу"


@pytest.mark.asyncio
async def test_retry_accepts_its_own_origin(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Свой источник проходит сверку: хост заголовка совпал с хостом запроса.

    Сравнивается именно ХОСТ: заголовок источника несёт схему и порт, и
    посимвольное сравнение сломалось бы на первом же развёртывании за обратным
    прокси.
    """
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id)

    with _retry_env() as env:
        response = await authed_client.post(
            f"/history/{log.id}/retry",
            headers={"Origin": "http://test", "Sec-Fetch-Site": "same-origin"},
            follow_redirects=False,
        )

    assert response.status_code == 302, response.status_code
    assert len(env.queued) == 1


@pytest.mark.asyncio
async def test_retry_lets_a_headerless_request_through(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Запрос без ОБОИХ заголовков проходит — названная граница защиты.

    Браузер, способный отправить межсайтовую форму, шлёт `Origin` на POST с
    2016 года; отсутствие обоих заголовков означает не-браузерного клиента, в
    том числе суиту проекта. Отказ по их отсутствию покрасил бы все остальные
    тесты повтора и не добавил бы ни одной защиты.
    """
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id)

    with _retry_env() as env:
        response = await authed_client.post(
            f"/history/{log.id}/retry", follow_redirects=False
        )

    assert response.status_code == 302, response.status_code
    assert len(env.queued) == 1


def test_retry_origin_check_runs_before_the_record_is_read():
    """Сверка источника стоит ДО чтения записи журнала.

    Проверка структурная: поведенчески «403 до чтения» и «403 после чтения»
    на клиенте неразличимы, а разница существенна — межсайтовый запрос не
    имеет права вызвать ни одного побочного эффекта.
    """
    body = _handler_source()

    assert "_is_same_origin(" in body, "сверки источника в обработчике нет"
    assert body.index("_is_same_origin(") < body.index("SendLog"), (
        "запись журнала читается раньше сверки источника — межсайтовый запрос "
        "успевает вызвать побочный эффект"
    )


def test_retry_origin_check_documents_its_boundary():
    """Пропуск запроса без обоих заголовков ВЫПИСАН, а не умолчан.

    Принятый остаточный риск, о котором не написано, через один рефакторинг
    становится неизвестным риском.
    """
    source = HISTORY_PY.read_text(encoding="utf-8")
    start = source.index("def _is_same_origin(")
    doc = source[start : start + 1800]

    assert "Sec-Fetch-Site" in doc
    assert "Origin" in doc
    assert "не-браузер" in doc or "не браузер" in doc, (
        "граница защиты (запрос без обоих заголовков пропускается) не названа "
        "в докстринге функции"
    )


# =============================================================================
# Пригодность записи (D-19)
# =============================================================================


@pytest.mark.asyncio
async def test_retry_of_an_eligible_record_queues_exactly_one_task(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Повтор своей неуспешной записи ставит РОВНО ОДНУ задачу.

    Аргументы — идентификатор записи и идентификатор пользователя: владение
    внутри таска проверяется повторно, потому что туда они приезжают из
    брокера, а не из запроса.
    """
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id)

    with _retry_env() as env:
        response = await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert response.status_code == 302
    assert len(env.queued) == 1, env.queued
    call = env.queued[0]
    assert call.args[0] == RETRY_TASK_NAME, call
    assert call.kwargs["args"] == [log.id, user.id], call


@pytest.mark.asyncio
async def test_retry_answers_with_a_redirect_not_a_page(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Ответ — перенаправление после отправки формы, а не отрисовка на месте.

    Это же закрывает повтор по обновлению страницы и по кнопке возврата
    браузера: необратимая отправка не имеет права уйти второй раз от F5.
    """
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id)

    with _retry_env():
        response = await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert response.status_code == 302
    assert response.headers["location"].startswith("/history")


@pytest.mark.asyncio
async def test_retry_of_a_successful_record_is_refused_by_the_server(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Успешную запись сервер повторять отказывается (D-19).

    Интерфейс кнопку не рисует, но интерфейс точкой принуждения не является:
    адрес повтора можно вызвать и без него.
    """
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id, status=STATUS_OK)

    with _retry_env() as env:
        response = await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert response.status_code == 302
    assert env.queued == [], "успешная запись ушла на повтор"


@pytest.mark.asyncio
async def test_retry_is_eligible_for_an_unknown_status(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Запись с НЕИЗВЕСТНЫМ статусом повторить можно.

    Предикат неуспешности — «статус НЕ успешный», а не «статус из перечня
    известных неудач»: перечень конечен ровно до появления следующего статуса,
    и запись с неизвестным значением осталась бы ни успешной, ни повторяемой.
    Тот же предикат держат счётчик неудач дашборда и кнопка копирования
    диагностики.
    """
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id, status="выдуманный_статус")

    with _retry_env() as env:
        response = await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert response.status_code == 302
    assert len(env.queued) == 1, "запись с неизвестным статусом повторить нельзя"


@pytest.mark.asyncio
async def test_retry_is_eligible_for_a_disconnected_account_status(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """`account_disconnected` — такая же несостоявшаяся отправка, как `fail`."""
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id, status=STATUS_ACCOUNT_DISCONNECTED)

    with _retry_env() as env:
        await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert len(env.queued) == 1


# =============================================================================
# Владение (T-04-35)
# =============================================================================


@pytest.mark.asyncio
async def test_retry_of_another_users_record_is_refused_by_ownership(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Чужая запись повтору не подлежит — владение проверяется на входе."""
    other = await _seed_other_user(db_session)
    log = await _seed_retryable(db_session, other.id)

    with _retry_env() as env:
        response = await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert response.status_code == 302
    assert env.queued == [], "чужая запись ушла на повтор"


@pytest.mark.asyncio
async def test_retry_of_a_missing_record_queues_nothing(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Несуществующая запись даёт перенаправление, а не пятисотку."""
    with _retry_env() as env:
        response = await authed_client.post(
            "/history/999999/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert response.status_code == 302
    assert env.queued == []


@pytest.mark.asyncio
async def test_retry_requires_login(client: AsyncClient, db_session: AsyncSession):
    """Неавторизованный запрос уходит на вход и задачи не ставит."""
    with _retry_env() as env:
        response = await client.post(
            "/history/1/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert response.status_code == 302
    assert response.headers["location"] == "/login"
    assert env.queued == []


# =============================================================================
# Предпроверка целости тройки сущностей (D-21, T-04-39)
# =============================================================================


@pytest.mark.asyncio
async def test_retry_precheck_stops_when_the_ad_is_gone(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Удалённое объявление останавливает повтор ДО очереди и ДО журнала."""
    user = await _current_user(db_session)
    _ad, group, _account = await _seed_triple(db_session, user.id)
    await _seed_balance(db_session, user.id)
    log = await _seed_log(db_session, user.id, ad_id=999999, group_id=group.id)

    before = len((await db_session.execute(select(SendLog))).all())

    with _retry_env() as env:
        response = await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert response.status_code == 302
    assert env.queued == [], "повтор без объявления ушёл в очередь"
    after = len((await db_session.execute(select(SendLog))).all())
    assert after == before, "журнал наполнился записью о невозможной отправке"


@pytest.mark.asyncio
async def test_retry_precheck_stops_when_the_group_is_gone(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Удалённая группа останавливает повтор.

    Случай не выдуманный: удалённая группа возвращается синхронизацией НОВОЙ
    строкой с новым идентификатором, поэтому ссылка старой записи журнала ведёт
    в никуда.
    """
    user = await _current_user(db_session)
    ad, _group, _account = await _seed_triple(db_session, user.id)
    await _seed_balance(db_session, user.id)
    log = await _seed_log(db_session, user.id, ad_id=ad.id, group_id=999999)

    with _retry_env() as env:
        response = await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert response.status_code == 302
    assert env.queued == []


@pytest.mark.asyncio
async def test_retry_precheck_stops_when_the_account_is_gone(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Аккаунт выводится ЧЕРЕЗ группу — колонки аккаунта в журнале нет."""
    user = await _current_user(db_session)
    ad, group, account = await _seed_triple(db_session, user.id)
    await _seed_balance(db_session, user.id)
    log = await _seed_log(db_session, user.id, ad_id=ad.id, group_id=group.id)

    await db_session.delete(account)
    await db_session.commit()

    with _retry_env() as env:
        response = await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert response.status_code == 302
    assert env.queued == []


@pytest.mark.asyncio
async def test_retry_precheck_stops_when_the_account_is_not_active(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Аккаунт есть, но отключён — отправить он всё равно не сможет."""
    user = await _current_user(db_session)
    ad, group, _account = await _seed_triple(
        db_session, user.id, account_status="sync_failed"
    )
    await _seed_balance(db_session, user.id)
    log = await _seed_log(db_session, user.id, ad_id=ad.id, group_id=group.id)

    with _retry_env() as env:
        response = await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert response.status_code == 302
    assert env.queued == []


def test_retry_precheck_runs_before_the_queue():
    """Предпроверка стоит в обработчике, а не внутри отправки.

    Проверка внутри отправки означала бы запись в журнал о заведомо
    невозможной отправке — то есть историю, наполненную свидетельствами того,
    чего быть не могло.
    """
    body = _handler_source()

    for symbol in ("Ad", "Group", "MessengerAccount"):
        assert symbol in body, f"предпроверка не смотрит на {symbol}"
        assert body.index(symbol) < body.index("send_task("), (
            f"проверка {symbol} стоит ПОСЛЕ постановки в очередь"
        )


# =============================================================================
# Гейт баланса (T-04-36)
# =============================================================================


@pytest.mark.asyncio
async def test_retry_is_refused_when_the_balance_is_exhausted(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Исчерпанный лимит отправок отклоняет повтор ДО очереди.

    Гейт баланса стоит у планировщика, а не внутри отправки. Без этого шага
    повтор стал бы способом отправить столько, сколько у пользователя неудачных
    записей, в обход тарифного лимита.
    """
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id)

    with _retry_env(allowed=False, reason="Баланс исчерпан") as env:
        response = await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert response.status_code == 302
    assert env.queued == [], "повтор обошёл гейт баланса"


@pytest.mark.asyncio
async def test_retry_explains_the_exhausted_balance_to_the_user(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Отказ по балансу ОБЪЯСНЯЕТСЯ, а не молчит.

    Молчаливое перенаправление на тот же список неотличимо от «ничего не
    произошло»: пользователь нажал, вернулся на прежний экран и не узнал, что
    отправки не будет.
    """
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id)

    with _retry_env(allowed=False, reason="Баланс исчерпан"):
        response = await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=True
        )

    assert response.status_code == 200
    assert "баланс" in response.text.lower(), "отказ по балансу не объяснён"


@pytest.mark.asyncio
async def test_retry_balance_gate_runs_before_the_queue(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Гейт баланса вызывается для действия отправки и ДО постановки."""
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id)

    with _retry_env() as env:
        await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert env.balance.await_count == 1, "гейт баланса не вызван"
    assert env.balance.await_args.args[2] == "send", env.balance.await_args

    body = _handler_source()
    assert body.index("check_balance_cached(") < body.index("send_task("), (
        "гейт баланса стоит ПОСЛЕ постановки задачи в очередь"
    )


def test_retry_does_not_touch_billing_itself():
    """Списание за повтор происходит там же, где у боевой рассылки (D-20).

    Второе место списания разошлось бы с первым, и повтор либо списывал бы
    дважды, либо не списывал вовсе.
    """
    body = _handler_source()

    assert "deduct_message" not in body
    assert "add_messages" not in body


# =============================================================================
# Защита от двойной постановки (T-04-37)
# =============================================================================


@pytest.mark.asyncio
async def test_retry_of_a_busy_record_queues_no_second_task(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Пока заявка занята, второй задачи не ставится."""
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id)

    assert history_module._claim_retry_slot(log.id) is True
    try:
        with _retry_env() as env:
            response = await authed_client.post(
                f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
            )
    finally:
        history_module._release_retry_slot(log.id)

    assert response.status_code == 302
    assert env.queued == [], "занятая заявка не остановила вторую постановку"


@pytest.mark.asyncio
async def test_retry_releases_the_slot_after_success(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """После успешной постановки следующий повтор той же записи возможен."""
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id)

    with _retry_env() as env:
        await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
        )
        assert log.id not in history_module._RETRY_IN_FLIGHT, "заявка не освобождена"
        await authed_client.post(
            f"/history/{log.id}/retry", headers=SAME_ORIGIN, follow_redirects=False
        )

    assert len(env.queued) == 2


@pytest.mark.asyncio
async def test_retry_releases_the_slot_after_an_exception(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Заявка освобождается и после исключения — иначе запись «залипла» бы.

    Незакрытая заявка означала бы, что одна ошибка навсегда лишает запись
    возможности повтора, причём молча и до перезапуска процесса.
    """
    user = await _current_user(db_session)
    log = await _seed_retryable(db_session, user.id)

    boom = AsyncMock(side_effect=RuntimeError("гейт баланса упал"))
    with patch.dict(sys.modules, {"app.worker.celery_app": MagicMock()}):
        with patch("app.pages.history.check_balance_cached", boom):
            # Исключение обработчика до теста не доезжает: посредник приложения
            # (`app/middleware.py`) ловит его, пишет в журнал и отдаёт 500.
            # Проверяется поэтому не всплытие, а СЛЕДСТВИЕ — заявка снята.
            response = await authed_client.post(
                f"/history/{log.id}/retry",
                headers=SAME_ORIGIN,
                follow_redirects=False,
            )

    assert response.status_code == 500, response.status_code
    assert log.id not in history_module._RETRY_IN_FLIGHT, (
        "заявка осталась занятой после исключения — запись больше не повторить"
    )


def test_retry_slot_claim_is_synchronous():
    """Занятие заявки — СИНХРОННАЯ функция без единого ожидания.

    Точка переключения задач между проверкой и добавлением вернула бы гонку
    ровно туда, откуда её убирают.

    ДОКСТРИНГ ИЗ ПРОВЕРКИ ВЫРЕЗАН. Он обязан объяснять, почему ожидания здесь
    нет, — то есть содержит само слово. Поиск по сырому тексту функции краснел
    бы именно на объяснении запрета: ровно то ложное срабатывание, которое в
    этом репозитории уже стоило переработки нескольким планам.
    """
    source = HISTORY_PY.read_text(encoding="utf-8")
    start = source.index("def _claim_retry_slot(")
    body = source[start : source.index("def _release_retry_slot(")]

    assert not re.search(r"^async def _claim_retry_slot", source[start:], re.M), (
        "функция занятия заявки стала асинхронной"
    )

    doc_open = body.index('"""')
    doc_close = body.index('"""', doc_open + 3) + 3
    code = body[:doc_open] + body[doc_close:]

    assert '"""' not in code, "докстринг вырезан не целиком — проверка неверна"
    assert "await" not in code, f"в занятии заявки появилось ожидание: {code!r}"


def test_retry_slot_release_is_a_discard_in_a_finally_block():
    """Освобождение — отбрасыванием и в блоке завершения.

    `discard`, а не `remove`: повторный вызов обязан быть безобидным.
    """
    source = HISTORY_PY.read_text(encoding="utf-8")
    start = source.index("def _release_retry_slot(")
    release = source[start : start + 700]

    assert ".discard(" in release, "освобождение снимает заявку не отбрасыванием"
    assert ".remove(" not in release

    body = _handler_source()
    assert "finally:" in body, "освобождения в блоке завершения нет"
    assert body.index("finally:") < body.index("_release_retry_slot("), body


def test_retry_slot_registry_documents_its_limit():
    """Ограничение реестра (память ОДНОГО процесса) выписано, а не умолчано."""
    source = HISTORY_PY.read_text(encoding="utf-8")
    start = source.index("_RETRY_IN_FLIGHT")
    around = source[max(0, start - 1500) : start + 2000]

    assert "процесс" in around, (
        "граница реестра (одна на процесс, нескольких рабочих процессов не "
        "переживает) не названа рядом с ним"
    )


# =============================================================================
# Форма маршрута
# =============================================================================


def test_retry_route_is_declared_as_a_post():
    """Необратимое действие уходит POST-ом, а не переходом по ссылке."""
    source = HISTORY_PY.read_text(encoding="utf-8")

    assert '@router.post("/history/{log_id}/retry"' in source


def test_retry_queue_client_is_imported_inside_the_handler():
    """Импорт клиента очереди — ЛОКАЛЬНЫЙ, внутри тела обработчика.

    Именно локальный импорт позволяет подменить модуль очереди в тесте.
    Поднятый на уровень модуля, он разрешился бы один раз при загрузке
    `app.pages.history`, и любой тест повтора пошёл бы к настоящему брокеру.
    """
    source = HISTORY_PY.read_text(encoding="utf-8")
    module_head = source[: source.index("router = APIRouter(")]

    assert "app.worker.celery_app" not in module_head, (
        "клиент очереди импортирован на уровне модуля — подмена в тесте "
        "перестанет работать"
    )
    assert "from app.worker.celery_app import celery" in _handler_source(), (
        "локального импорта клиента очереди в обработчике нет"
    )


# =============================================================================
# Задача 2: запуск повтора, панель подтверждения и предпроверка для интерфейса
# =============================================================================
#
# Признак доступности повтора вычисляется НА СЕРВЕРЕ и приезжает в карточку
# значением. Вычислять его в шаблоне нельзя вовсе: разметке не из чего узнать,
# цела ли тройка сущностей, а обращение к базе из Jinja означало бы запрос на
# каждую строку списка.

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"

CARD_HTML = TEMPLATES_DIR / "history" / "includes" / "history_card.html"
DETAIL_HTML = TEMPLATES_DIR / "history" / "detail.html"

# Разметка панели, собранная в обход библиотеки. Своя копия не унаследовала бы
# ни гарда повторной отправки, ни ловушки фокуса, ни закрытия по клавише отмены.
PANEL_MARKUP_MARKERS = ("modal__form", "modal__actions", "modal__panel")

_ARTICLE_RE = re.compile(r"<article\b.*?</article>", re.S)


def _retry_trigger_present(html: str) -> bool:
    return "data-retry" in html and "modal-open-history-retry-" in html


async def _seed_retryable_with_ids(
    db: AsyncSession, user_id: int, *, status: str = STATUS_FAIL
) -> tuple[SendLog, Ad, Group, MessengerAccount]:
    ad, group, account = await _seed_triple(db, user_id)
    await _seed_balance(db, user_id)
    log = await _seed_log(db, user_id, status=status, ad_id=ad.id, group_id=group.id)
    return log, ad, group, account


# --- запуск повтора в карточке списка -----------------------------------------


@pytest.mark.asyncio
async def test_unsuccessful_record_offers_a_retry_launcher(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """У неуспешной записи в карточке списка есть чем запустить повтор."""
    user = await _current_user(db_session)
    log, *_ = await _seed_retryable_with_ids(db_session, user.id)

    html = (await authed_client.get("/history")).text

    assert _retry_trigger_present(html), "запуска повтора у неуспешной записи нет"
    assert f"/history/{log.id}/retry" in html


@pytest.mark.asyncio
async def test_successful_record_offers_no_retry_launcher(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """У успешной записи запуска повтора НЕТ — ни кнопки, ни панели.

    Недоступность возможности выражается отсутствием органа управления, а не
    его бездействием: тот же принцип, по которому у успешной записи нет кнопки
    копирования диагностики.
    """
    user = await _current_user(db_session)
    await _seed_retryable_with_ids(db_session, user.id, status=STATUS_OK)

    html = (await authed_client.get("/history")).text

    assert not _retry_trigger_present(html), "успешной записи предложен повтор"
    assert "/retry" not in html


@pytest.mark.asyncio
async def test_record_with_a_missing_entity_explains_instead_of_offering_retry(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Заведомо непроходимый повтор не предлагается, но и не молчит (D-21).

    Молча спрятанная кнопка неотличима от «повтор не поддерживается»:
    пользователь не узнал бы, что мешает именно исчезнувшее объявление.
    """
    user = await _current_user(db_session)
    _ad, group, _account = await _seed_triple(db_session, user.id)
    await _seed_log(db_session, user.id, ad_id=999999, group_id=group.id)

    html = (await authed_client.get("/history")).text

    assert not _retry_trigger_present(html), "повтор предложен там, где невозможен"
    assert "data-retry-off" in html, "причина недоступности повтора не показана"


@pytest.mark.asyncio
async def test_retry_availability_is_computed_by_the_server(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Признак доступности приезжает в карточку значением, а не считается разметкой.

    Иначе шаблон обязан был бы ходить в базу на каждую строку списка.
    """
    source = CARD_HTML.read_text(encoding="utf-8")

    assert "can_retry" in source, "карточка не читает серверный признак"

    user = await _current_user(db_session)
    await _seed_retryable_with_ids(db_session, user.id)
    html = (await authed_client.get("/history")).text

    assert _retry_trigger_present(html)


@pytest.mark.asyncio
async def test_retry_launcher_survives_the_infinite_scroll_partial(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Порция прокрутки несёт тот же признак, что и первая страница.

    Признак, вычисленный только в списочном обработчике, потерялся бы на
    тридцать первой записи — молча, с исправным на вид экраном.
    """
    user = await _current_user(db_session)
    await _seed_retryable_with_ids(db_session, user.id)

    html = (await authed_client.get("/history/partial?offset=0&limit=30")).text

    assert _retry_trigger_present(html), "порция прокрутки потеряла запуск повтора"


# --- панель подтверждения -----------------------------------------------------


@pytest.mark.asyncio
async def test_retry_confirmation_panel_carries_a_real_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Панель подтверждения несёт НАСТОЯЩУЮ форму на адрес повтора.

    Панель — усиление поверх формы, а не замена ей: без Alpine перехват не
    навешивается, и форма уходит прежним методом на прежний маршрут.
    """
    user = await _current_user(db_session)
    log, *_ = await _seed_retryable_with_ids(db_session, user.id)

    html = (await authed_client.get("/history")).text

    start = html.find(f'id="history-retry-{log.id}"')
    assert start != -1, "панели подтверждения повтора в разметке нет"
    panel = html[start : start + 2000]
    assert 'method="post"' in panel, panel[:400]
    assert f'action="/history/{log.id}/retry"' in panel, panel[:400]
    assert 'type="submit"' in panel, panel[:400]


@pytest.mark.asyncio
async def test_retry_confirmation_panel_names_the_current_ad_content(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Текст панели называет следствие D-17 прямо.

    Уйдёт ТЕКУЩЕЕ содержимое объявления из базы, а не снапшот, показанный в
    записи. Умолчать это значит показать пользователю один текст, а отправить
    другой (T-04-40).
    """
    user = await _current_user(db_session)
    log, *_ = await _seed_retryable_with_ids(db_session, user.id)

    html = (await authed_client.get("/history")).text
    start = html.find(f'id="history-retry-{log.id}"')
    panel = html[start : start + 2000].lower()

    assert "текущ" in panel, "панель не говорит, что уйдёт текущее содержимое"
    assert "объявлени" in panel


@pytest.mark.asyncio
async def test_retry_panel_is_emitted_outside_the_record_markup(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Панель лежит ВНЕ разметки записи.

    Внутри карточки панель стала бы колонкой её сетки — она позиционируется
    фиксированно, — а внутри заменяемого прокруткой элемента размножилась бы
    после первой же подмены, и событие открывало бы сразу две панели с одним
    именем.
    """
    user = await _current_user(db_session)
    log, *_ = await _seed_retryable_with_ids(db_session, user.id)

    html = (await authed_client.get("/history")).text

    articles = _ARTICLE_RE.findall(html)
    assert articles, "записи в выдаче нет — проверять нечего"
    for article in articles:
        assert f'id="history-retry-{log.id}"' not in article, (
            "панель подтверждения оказалась внутри разметки записи"
        )
    assert f'id="history-retry-{log.id}"' in html, "панели нет вовсе"


def test_retry_uses_the_shared_confirmation_panel():
    """Подтверждение идёт ОБЩЕЙ панелью проекта, а не собственным диалогом.

    Своя копия панели не унаследовала бы ни гарда повторной отправки, ни
    ловушки фокуса, ни закрытия по клавише отмены — а браузерный диалог красит
    сплошной обход отрисованных страниц.
    """
    source = CARD_HTML.read_text(encoding="utf-8")

    assert "components/modal.html" in source, "общая панель не импортирована"
    own = [marker for marker in PANEL_MARKUP_MARKERS if marker in source]
    assert not own, f"панель собрана в обход библиотеки: {own}"


# --- страница записи ----------------------------------------------------------


@pytest.mark.asyncio
async def test_history_detail_offers_the_same_retry_path(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """На странице записи повтор запускается ТЕМ ЖЕ путём."""
    user = await _current_user(db_session)
    log, *_ = await _seed_retryable_with_ids(db_session, user.id)

    html = (await authed_client.get(f"/history/{log.id}")).text

    assert _retry_trigger_present(html), "страница записи не предлагает повтор"
    assert f'action="/history/{log.id}/retry"' in html


@pytest.mark.asyncio
async def test_history_detail_offers_no_retry_for_a_successful_record(
    authed_client: AsyncClient, db_session: AsyncSession
):
    user = await _current_user(db_session)
    log, *_ = await _seed_retryable_with_ids(db_session, user.id, status=STATUS_OK)

    html = (await authed_client.get(f"/history/{log.id}")).text

    assert not _retry_trigger_present(html)


@pytest.mark.asyncio
async def test_history_detail_panel_is_outside_the_record_markup(
    authed_client: AsyncClient, db_session: AsyncSession
):
    user = await _current_user(db_session)
    log, *_ = await _seed_retryable_with_ids(db_session, user.id)

    html = (await authed_client.get(f"/history/{log.id}")).text

    for article in _ARTICLE_RE.findall(html):
        assert f'id="history-retry-{log.id}"' not in article
    assert f'id="history-retry-{log.id}"' in html


def test_retry_launcher_has_one_definition_for_both_screens():
    """Запуск повтора объявлен ОДИН раз и импортируется страницей записи.

    Вторая копия разошлась бы с первой ровно там, где расхождение опаснее
    всего: в тексте, обещающем пользователю, ЧТО именно будет отправлено. Тот
    же приём, что у кнопки копирования диагностики (план 04-07).
    """
    detail = DETAIL_HTML.read_text(encoding="utf-8")

    assert "history/includes/history_card.html" in detail
    assert "retry" in detail
    own = [marker for marker in PANEL_MARKUP_MARKERS if marker in detail]
    assert not own, f"страница записи собрала панель сама: {own}"


# --- админский экран истории --------------------------------------------------


@pytest.mark.asyncio
async def test_admin_history_offers_no_retry_launcher(
    client: AsyncClient, test_settings, db_session: AsyncSession
):
    """Админская история чужого пользователя повтора НЕ предлагает.

    Тот же макрос карточки обслуживает админский экран, а признак доступности
    приходит туда значением, которого админский обработчик не кладёт. Кнопка,
    приехавшая туда сама, обещала бы админу действие, которое сервер всё равно
    отклонит проверкой владения, — то есть предлагала бы заведомый отказ.
    """
    owner = await _current_user(db_session)
    await _seed_retryable_with_ids(db_session, owner.id)

    await client.post(
        "/api/auth/register",
        json={
            "email": test_settings.admin_email,
            "password": "testpass123",
            "name": "Admin User",
        },
    )
    await client.post(
        "/login",
        data={"email": test_settings.admin_email, "password": "testpass123"},
        follow_redirects=False,
    )

    response = await client.get(f"/admin/users/{owner.id}/history")

    assert response.status_code == 200
    assert not _retry_trigger_present(response.text), (
        "админскому экрану предложен повтор чужой записи"
    )


# --- предпроверка для интерфейса ----------------------------------------------


@pytest.mark.asyncio
async def test_retry_availability_takes_a_bounded_number_of_queries(
    db_session: AsyncSession,
):
    """Предпроверка страницы стоит ФИКСИРОВАННОЕ число запросов.

    Проверка тройки сущностей по записи означала бы три обращения к базе на
    строку — девяносто на страницу в тридцать записей, и так на каждый рендер
    списка. Число запросов не имеет права зависеть от числа записей.
    """
    from sqlalchemy import event

    from app.pages.history import retry_availability

    user = await _current_user(db_session)
    ad, group, _account = await _seed_triple(db_session, user.id)
    rows = []
    for _ in range(20):
        log = await _seed_log(db_session, user.id, ad_id=ad.id, group_id=group.id)
        rows.append((log, group))

    statements: list[str] = []
    sync_engine = db_session.bind.sync_engine

    def _record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(sync_engine, "before_cursor_execute", _record)
    try:
        verdict = await retry_availability(db_session, rows)
    finally:
        event.remove(sync_engine, "before_cursor_execute", _record)

    assert len(verdict) == 20
    assert all(reason is None for reason in verdict.values()), verdict
    assert len(statements) <= 2, (
        f"предпроверка сделала {len(statements)} запросов на двадцать записей — "
        "это N+1 на каждом рендере списка"
    )


@pytest.mark.asyncio
async def test_retry_availability_ignores_successful_records(
    db_session: AsyncSession,
):
    """Успешная запись в предпроверку не попадает вовсе.

    Повтор ей не предлагается по статусу, и тратить на неё запросы незачем.
    """
    from app.pages.history import retry_availability

    user = await _current_user(db_session)
    ad, group, _account = await _seed_triple(db_session, user.id)
    ok = await _seed_log(
        db_session, user.id, status=STATUS_OK, ad_id=ad.id, group_id=group.id
    )
    bad = await _seed_log(db_session, user.id, ad_id=ad.id, group_id=group.id)

    verdict = await retry_availability(db_session, [(ok, group), (bad, group)])

    assert ok.id not in verdict
    assert verdict[bad.id] is None


@pytest.mark.asyncio
async def test_retry_availability_names_each_missing_entity(
    db_session: AsyncSession,
):
    """Причина называет ИМЕННО ту сущность, которой не хватает.

    Общее «повторить нельзя» на все четыре случая не сказало бы пользователю
    ничего о том, что чинить.
    """
    from app.pages.history import (
        RETRY_REASON_ACCOUNT_GONE,
        RETRY_REASON_ACCOUNT_OFF,
        RETRY_REASON_AD_GONE,
        RETRY_REASON_GROUP_GONE,
        retry_availability,
    )

    user = await _current_user(db_session)
    ad, group, _account = await _seed_triple(db_session, user.id)

    no_ad = await _seed_log(db_session, user.id, ad_id=999999, group_id=group.id)
    no_group = await _seed_log(db_session, user.id, ad_id=ad.id, group_id=None)
    whole = await _seed_log(db_session, user.id, ad_id=ad.id, group_id=group.id)

    verdict = await retry_availability(
        db_session, [(no_ad, group), (no_group, None), (whole, group)]
    )
    assert verdict[no_ad.id] == RETRY_REASON_AD_GONE
    assert verdict[no_group.id] == RETRY_REASON_GROUP_GONE
    assert verdict[whole.id] is None

    off_account = MessengerAccount(
        user_id=user.id, type="wa", credentials="creds", status="sync_failed"
    )
    db_session.add(off_account)
    await db_session.commit()
    await db_session.refresh(off_account)
    off_group = Group(
        user_id=user.id,
        account_id=off_account.id,
        messenger_type="wa",
        group_external_id="-100777",
        name="Отключённый",
    )
    orphan_group = Group(
        user_id=user.id,
        account_id=999999,
        messenger_type="wa",
        group_external_id="-100888",
        name="Без аккаунта",
    )
    db_session.add(off_group)
    db_session.add(orphan_group)
    await db_session.commit()
    await db_session.refresh(off_group)
    await db_session.refresh(orphan_group)

    log_off = await _seed_log(db_session, user.id, ad_id=ad.id, group_id=off_group.id)
    log_orphan = await _seed_log(
        db_session, user.id, ad_id=ad.id, group_id=orphan_group.id
    )

    verdict = await retry_availability(
        db_session, [(log_off, off_group), (log_orphan, orphan_group)]
    )
    assert verdict[log_off.id] == RETRY_REASON_ACCOUNT_OFF
    assert verdict[log_orphan.id] == RETRY_REASON_ACCOUNT_GONE

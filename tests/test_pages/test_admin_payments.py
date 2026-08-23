"""Подраздел «Платежи»: две величины, журнал и отсутствие тарифного плана (ADMIN-10).

⚠️ ГЛАВНОЕ УТВЕРЖДЕНИЕ ФАЙЛА ОТРИЦАТЕЛЬНОЕ, И ОНО ЗДЕСЬ САМОЕ ДОРОГОЕ (D-42).
Колонка тарифного плана осталась в хранилище после смены модели тарификации и
заполнена у исторических платежей. Исследование фазы проверило ПРЯМО, что голое
имя колонки не подпадает ни под один существующий греп-гейт (Ф-10), — значит её
отсутствие в разметке есть решение ПО СУЩЕСТВУ, и держаться оно может только
собственным тестом. Без него первый же читатель добавит колонку «Тариф»,
получит зелёную суиту и сообщит администратору, что тарифы живы; администратор
станет отвечать так же клиентам.

⚠️ ВТОРОЕ УТВЕРЖДЕНИЕ — ПРО ДВЕ ВЕЛИЧИНЫ, А НЕ ЧЕТЫРЕ. Макет рисует на этом
месте ещё среднюю величину платежа и долю ушедших; обе выброшены решением
(D-41), и обе проверяются ОТСУТСТВИЕМ имени в разметке. Число, дожившее до
прода из макета, читается администратором как ИЗМЕРЕННОЕ, и в аварии он примет
решение по нарисованной цифре.

⚠️ ТРЕТЬЕ — ПРО ЧИСЛА, КОТОРЫЕ НЕ КОПИРУЮТСЯ В КОПИРАЙТ. И потолок журнала, и
окно величины ушедших приезжают в текст экрана подстановкой из своей
единственной константы. Тест поэтому подменяет константу и требует, чтобы за
ней поехала ПОДПИСЬ: копия, выписанная в шаблоне литералом, разошлась бы с
настоящим значением молча — экран обещал бы одно, а считалось бы другое.
"""
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.admin.payments_query import (
    EXPIRED_LOOKBACK_DAYS,
    PURPOSE_SUBSCRIPTION,
)
from app.constants import PAYMENT_LIST_CAP
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.services.payment_service import (
    KIND_PACKAGE,
    KIND_SUBSCRIPTION,
    STATUS_CANCELED,
    STATUS_PENDING,
    STATUS_SUCCEEDED,
)

PAYMENTS_URL = "/admin/payments"

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"
PAYMENTS_TEMPLATE = TEMPLATES_DIR / "admin" / "payments.html"
PAYMENT_ROW_TEMPLATE = TEMPLATES_DIR / "admin" / "includes" / "payment_row.html"

NOW = datetime.now(timezone.utc)

# ⚠️ ЗНАЧЕНИЕ ТАРИФНОГО ПЛАНА ВЗЯТО ЗАМЕТНЫМ НАМЕРЕННО. Настоящие исторические
# значения — короткие латинские слова, и «нет ли `pro` в разметке» проверяло бы
# наличие трёх букв, которые встречаются в чём угодно. Утверждение здесь про
# КОЛОНКУ: что бы в ней ни лежало, оно не доезжает до экрана. Заметная строка
# делает это утверждение точным, а не приблизительным.
DEAD_PLAN = "PRO-ТАРИФ-ЭПОХИ-КОТОРОЙ-БОЛЬШЕ-НЕТ"

_ids = iter(range(1, 100_000))


async def _seed_user(session: AsyncSession, email: str, name: str) -> User:
    user = User(
        email=email,
        password_hash=f"ХЕШ-ПАРОЛЯ-{email}-НЕ-ДОЛЖЕН-ПОПАСТЬ-В-РАЗМЕТКУ",
        name=name,
        created_at=NOW - timedelta(days=365),
    )
    session.add(user)
    await session.flush()
    return user


async def _seed_payment(
    session: AsyncSession,
    user: User,
    *,
    status: str = STATUS_SUCCEEDED,
    created_at: datetime | None = None,
    amount: str = "3000.00",
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


# ---- Права и каркас ----------------------------------------------------------


@pytest.mark.asyncio
async def test_the_subsection_answers_the_admin_and_refuses_the_stranger(
    admin_client: AsyncClient,
):
    """200 администратору.

    Подраздел показывает платежи ВСЕХ пользователей одному человеку
    (T-06-PAY1), поэтому зависимость администратора на маршруте — не
    формальность: без неё денежный журнал сервиса открылся бы любому вошедшему.
    """
    assert (await admin_client.get(PAYMENTS_URL)).status_code == 200


@pytest.mark.asyncio
async def test_the_subsection_refuses_the_regular_user(authed_client: AsyncClient):
    """403 постороннему — утверждение отдельным тестом, а не второй строкой.

    Слитое с предыдущим, оно проверяло бы порядок фикстур: обе поднимают своего
    клиента, и вошедший последним переписал бы cookie первого.
    """
    assert (await authed_client.get(PAYMENTS_URL)).status_code == 403


# ---- Две величины, и ровно две (D-41) ---------------------------------------


@pytest.mark.asyncio
async def test_exactly_two_figures_are_printed_and_the_thrown_out_ones_are_absent(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Регулярная выручка и число непродлённых — и больше ни одной величины.

    Отсутствие проверяется по ИМЕНАМ выброшенных величин: вернуться они могут
    только вместе со своей подписью, а подпись — единственное, по чему
    администратор их узнает.
    """
    paying = await _seed_user(db_session, "paying@test.com", "Платящий")
    db_session.add(
        Subscription(user_id=paying.id, expires_at=NOW + timedelta(days=10))
    )
    await db_session.commit()

    html = (await admin_client.get(PAYMENTS_URL)).text

    assert 'data-payment-figure="mrr"' in html
    assert 'data-payment-figure="lapsed"' in html
    assert len(re.findall(r"data-payment-figure=", html)) == 2

    for thrown_out in ("ARPU", "Средний чек", "Отток"):
        assert thrown_out not in html, thrown_out


@pytest.mark.asyncio
async def test_the_lapsed_figure_prints_zero_instead_of_disappearing(
    admin_client: AsyncClient,
):
    """Ноль ушедших печатается НУЛЁМ, а не пустым местом (E3 zero-one-many).

    Спрятанная при нуле величина читается как «показатель сломан»: у экрана нет
    способа отличить «никто не ушёл» от «посчитать не удалось». Ноль — это
    ответ, и он лучший из возможных.
    """
    html = (await admin_client.get(PAYMENTS_URL)).text
    block = _figure_block(html, "lapsed")

    assert ">0<" in block, block


@pytest.mark.asyncio
async def test_the_lapsed_caption_takes_its_window_from_the_single_constant(
    admin_client: AsyncClient,
):
    """Окно приезжает в подпись подстановкой, а не выписано числом в шаблоне.

    ⚠️ ЧИСЛА НЕ КОПИРУЮТСЯ В КОПИРАЙТ. Копия окна в тексте экрана разошлась бы с
    настоящим окном молча: подпись обещала бы один срок, а считалось бы по
    другому, и заметить это можно было бы только пересчитав руками. Прецедент
    правила дословный — подпись потолка журнала платежей раздела пользователя.
    """
    html = (await admin_client.get(PAYMENTS_URL)).text
    assert f"за {EXPIRED_LOOKBACK_DAYS} " in html

    with patch(
        "app.application.admin.payments_query.EXPIRED_LOOKBACK_DAYS", 7
    ), patch("app.pages.admin.EXPIRED_LOOKBACK_DAYS", 7):
        moved = (await admin_client.get(PAYMENTS_URL)).text

    assert "за 7 " in moved
    assert f"за {EXPIRED_LOOKBACK_DAYS} " not in moved


# ---- Журнал: строка, статусы, суммы ------------------------------------------


@pytest.mark.asyncio
async def test_the_ledger_row_prints_date_user_amount_purpose_and_status(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Пять колонок строки, и каждая несёт своё значение.

    Подпись колонки едет ВМЕСТЕ со значением: ниже 861px шапка колонок скрыта, и
    подпись остаётся ЕДИНСТВЕННЫМ названием величины (M2 UI-контракта).
    """
    payer = await _seed_user(db_session, "payer@test.com", "Иван Плательщик")
    await _seed_payment(db_session, payer, amount="3000.00")
    await db_session.commit()

    html = (await admin_client.get(PAYMENTS_URL)).text

    assert "Иван Плательщик" in html
    assert PURPOSE_SUBSCRIPTION in html
    assert "проведён" in html
    for column in ("Дата", "Пользователь", "Сумма", "Предмет", "Статус"):
        assert f"<span data-cell-label>{column}</span>" in html, column


@pytest.mark.asyncio
async def test_the_unclosed_payment_is_visible_and_wears_its_own_status(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Незакрытый платёж виден в журнале и назван своим словом.

    Залипшие незакрытые платежи — та самая популяция, ради которой подраздел
    вообще открывают: они дают пятый признак инцидента. Спрятанное состояние
    платежа читается как «платежа не было».
    """
    payer = await _seed_user(db_session, "stuck@test.com", "Залипший Платёж")
    await _seed_payment(db_session, payer, status=STATUS_PENDING)
    await db_session.commit()

    html = (await admin_client.get(f"{PAYMENTS_URL}?status=unclosed")).text

    assert "Залипший Платёж" in html
    assert "в обработке" in html


@pytest.mark.asyncio
async def test_amounts_go_through_the_money_global_and_junk_does_not_break_the_page(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Суммы печатает общий денежный глобал; нечисловая сумма не роняет подраздел.

    ⚠️ ПРОВЕРКА КОНЕЧНОСТИ ЗНАЧЕНИЯ УЖЕ ВНУТРИ ГЛОБАЛА, и собственное
    форматирование рядом означало бы, что одна строка в колонке суммы уводит
    подраздел в пятисотку целиком. Непригодное значение печатается КАК ЕСТЬ:
    выдуманный ноль в денежном журнале — правдоподобная ложь, а странная строка
    на экране хотя бы называет себя странной.
    """
    payer = await _seed_user(db_session, "money@test.com", "Денежный")
    await _seed_payment(db_session, payer, amount="3000.00")
    await _seed_payment(db_session, payer, amount="не-число")
    await _seed_payment(db_session, payer, amount="NaN")
    await db_session.commit()

    response = await admin_client.get(PAYMENTS_URL)

    assert response.status_code == 200
    # Разделитель разрядов — неразрывный пробел, и он свойство глобала:
    # собранная вручную строка его бы не поставила.
    assert "3 000 ₽" in response.text
    assert "не-число" in response.text


# ---- Отрицательное утверждение: тарифного плана нет (D-42) -------------------


@pytest.mark.asyncio
async def test_no_plan_value_from_the_dead_tariff_column_reaches_the_markup(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Значение заполненной колонки тарифа НЕ появляется в разметке.

    Посев именно с ЗАПОЛНЕННЫМ планом: пустая колонка не отличила бы «не
    показываем» от «нечего показать», и тест зеленел бы на популяции, которой в
    проде нет. Историческая строка с планом в проде ЕСТЬ.
    """
    payer = await _seed_user(db_session, "historic@test.com", "Исторический")
    await _seed_payment(db_session, payer, plan=DEAD_PLAN)
    await db_session.commit()

    html = (await admin_client.get(PAYMENTS_URL)).text

    assert "Исторический" in html, "строка платежа вообще не отрисовалась"
    assert DEAD_PLAN not in html
    assert PURPOSE_SUBSCRIPTION in html, (
        "предмет исторического платежа обязан называться доступом, а не пустым "
        "местом: пустая ячейка в денежном журнале читается как неполная строка"
    )


def test_no_plan_lookup_exists_in_either_payments_template():
    """Ни один из двух шаблонов подраздела не обращается к колонке тарифа.

    Утверждение по ТЕКСТУ шаблонов, а не по отданной странице: обращение,
    добавленное в ветку, до которой не дошёл ни один посев, отдалась бы пустой
    строкой и прошло бы мимо проверки разметки. Здесь оно ловится объявлением.
    """
    for template in (PAYMENTS_TEMPLATE, PAYMENT_ROW_TEMPLATE):
        source = template.read_text(encoding="utf-8")
        assert re.search(r"payment\.plan|\.plan\b", source) is None, template.name


# ---- Фильтры и потолок --------------------------------------------------------


@pytest.mark.asyncio
async def test_both_axes_are_drawn_by_the_library_component_with_this_base_path(
    admin_client: AsyncClient
):
    """Две оси чипсов, и базовый адрес каждой — адрес ЭТОГО подраздела (Ф-15).

    ⚠️ ЗАБЫТЫЙ БАЗОВЫЙ АДРЕС НЕ ДАЁТ ОШИБКИ РАЗМЕТКИ — он даёт чипсы, уводящие
    администратора из подраздела при КАЖДОМ клике по фильтру, при статусе 200 и
    верной на вид разметке. Компонент поэтому требует параметр обязательным, а
    тест называет ожидаемый адрес вслух.
    """
    html = (await admin_client.get(PAYMENTS_URL)).text

    assert 'data-chipset="status"' in html
    assert 'data-chipset="period"' in html
    assert f'href="{PAYMENTS_URL}?status=succeeded"' in html
    assert f'href="{PAYMENTS_URL}?period=30d"' in html


@pytest.mark.asyncio
async def test_a_junk_axis_value_highlights_nothing_and_filters_nothing(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Мусор в оси не подсвечивает чипс и не отбирает строк.

    Неотсечённое для РАЗМЕТКИ значение доехало бы до чипсов как активное, и
    администратор увидел бы подсвеченный фильтр, которого не задавал и который
    ничего не отбирает.
    """
    payer = await _seed_user(db_session, "junk@test.com", "Мусорный Фильтр")
    await _seed_payment(db_session, payer)
    await db_session.commit()

    html = (await admin_client.get(f"{PAYMENTS_URL}?status=выдумка")).text

    assert "Мусорный Фильтр" in html
    assert "выдумка" not in html


@pytest.mark.asyncio
async def test_the_firing_cap_names_itself_above_the_ledger(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Сработавший потолок назван подписью, и число в ней — из константы.

    Молча усечённый журнал денег читается как «других платежей не было» — то
    есть как ответ на вопрос, ради которого администратор в подраздел и пришёл.
    """
    payer = await _seed_user(db_session, "cap@test.com", "Потолочный")
    for offset in range(5):
        await _seed_payment(
            db_session, payer, created_at=NOW - timedelta(minutes=offset)
        )
    await db_session.commit()

    with patch("app.application.admin.payments_query.PAYMENT_LIST_CAP", 3):
        capped = (await admin_client.get(PAYMENTS_URL)).text

    assert "Показаны последние 3 платежей из 5" in capped

    full = (await admin_client.get(PAYMENTS_URL)).text
    assert "Показаны последние" not in full
    assert str(PAYMENT_LIST_CAP) not in full or "Показаны последние" not in full


# ---- Два пустых состояния, и различие между ними несущее ---------------------


@pytest.mark.asyncio
async def test_an_empty_result_under_filters_offers_the_way_out(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Пустое состояние ФИЛЬТРОВ называет выход, а не констатирует пустоту.

    ⚠️ ДВА ПУСТЫХ СОСТОЯНИЯ, И СЛИТЫЕ В ОДНО ОНИ ОТВЕЧАЮТ ВТОРЫМ НА ПЕРВЫЙ
    ВОПРОС: администратор пойдёт искать поломку приёма платежей вместо того,
    чтобы снять свой же фильтр.
    """
    payer = await _seed_user(db_session, "filtered@test.com", "Отфильтрованный")
    await _seed_payment(db_session, payer, status=STATUS_SUCCEEDED)
    await db_session.commit()

    html = (await admin_client.get(f"{PAYMENTS_URL}?status=canceled")).text

    assert "Платежей нет" in html
    assert "Снимите фильтр или расширьте период" in html
    assert f'href="{PAYMENTS_URL}"' in html
    assert "Отфильтрованный" not in html


@pytest.mark.asyncio
async def test_an_empty_base_says_there_were_no_payments_at_all(
    admin_client: AsyncClient,
):
    """Без фильтров пустой журнал не предлагает ничего — предлагать нечего."""
    html = (await admin_client.get(PAYMENTS_URL)).text

    assert "Платежей ещё не было" in html
    assert "Снимите фильтр" not in html


@pytest.mark.asyncio
async def test_a_package_payment_keeps_its_own_purpose(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Не подписочный платёж называется своим предметом, а не доступом.

    Переименовать чужой прошлый платёж значило бы соврать в денежном журнале:
    колонки предмета — ЖУРНАЛ, а не состояние.
    """
    payer = await _seed_user(db_session, "package@test.com", "Пакетный")
    await _seed_payment(
        db_session,
        payer,
        kind=KIND_PACKAGE,
        package_name="Пакет на 5000 сообщений",
    )
    await db_session.commit()

    html = (await admin_client.get(PAYMENTS_URL)).text

    assert "Пакет на 5000 сообщений" in html


@pytest.mark.asyncio
async def test_the_screen_never_prints_the_external_payment_key(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Идентификатор платежа во внешней системе не печатается НИГДЕ (T-06-PAY1).

    Регрессия старше этой разметки: ключ — средство подделки уведомления об
    оплате. Здесь она повторена для нового потребителя тех же строк.
    """
    payer = await _seed_user(db_session, "key@test.com", "Ключевой")
    payment = await _seed_payment(db_session, payer)
    await db_session.commit()

    html = (await admin_client.get(PAYMENTS_URL)).text

    assert "Ключевой" in html
    assert payment.yookassa_payment_id not in html


def _figure_block(html: str, name: str) -> str:
    """Разметка одной величины — от её якоря до конца узла."""
    match = re.search(
        rf'data-payment-figure="{name}"(.*?)</div>', html, flags=re.S
    )
    assert match is not None, f"величина {name} в разметке не найдена"
    return match.group(1)

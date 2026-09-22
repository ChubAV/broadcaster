"""ТРАНСПОРТ ЭКРАНОВ АВТОРИЗАЦИИ (Фаза 14; SIGN-01, SIGN-02, SIGN-03).

Предмет — ФОРМА ответа форм второго шелла, а не их решения (D-15): что
проверять, в каком порядке и какими словами отказывать, решает обработчик, и
фаза этого не меняет. Меняется транспорт:

  * ошибка заполнения — 422 на ОБОИХ транспортах, и человек остаётся на том же
    экране со всем, что ввёл, КРОМЕ пароля (D-03, D-04);
  * отказ заблокированному — тот же 422, и cookie сессии в нём нет (D-05);
  * успех, меняющий личность, — полная загрузка: без признака htmx 302, с ним
    204 и заголовок полной перезагрузки, cookie на ЭТОМ ЖЕ ответе (D-10).

⚠️ ОБА ТРАНСПОРТА ПРОВЕРЯЮТСЯ ЭТИМ ЖЕ МОДУЛЕМ. Путь без JavaScript — не
второстепенный: форма без признака htmx обязана работать, как сегодня
(критерий 2 фазы), и тот же самый запрос здесь уходит дважды — без признака и с
ним, — а не расходится по двум файлам, где один из них однажды отстанет.

⚠️ ПОЛЬЗОВАТЕЛЬ ЗАВОДИТСЯ ПРИКЛАДНОЙ РЕГИСТРАЦИЕЙ, А НЕ ORM. С ней приходит
пробный срок, и кабинет, открытый после входа, открывается по СВОЕЙ причине, а
не отказывает гейтом доступа (приём `_register` из `test_blocked_user.py`).

Пополняется планами 14-02…14-05: каждый переведённый экран приносит сюда свои
правила ошибки и смены шага.
"""
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.models.email_verification import EmailVerificationCode
from app.models.subscription import Subscription
from app.models.user import User
from app.pages.auth import BLOCKED_LOGIN_ERROR
from app.services.auth_service import (
    create_verification_token,
    decode_verification_token,
)

HTMX_HEADERS = {"HX-Request": "true"}
DOCUMENT_MARK = "<!DOCTYPE"
HOSTILE = '"><script>alert(1)</script>'

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"

PASSWORD = "testpass123"
WRONG_PASSWORD = "wrong-pass-987"
LOGIN_TITLE = "<title>Вход — Broadcaster</title>"
LOGIN_ERROR = "Неверный email или пароль"
STEP_ANCHOR = 'id="auth-step"'
STEP_TARGET = 'hx-target="#auth-step"'

# Форма экранирования враждебного email в `value=`, СНЯТАЯ ПЕРВЫМ ПРОГОНОМ
# (допущение A5 RESEARCH): окружение шаблонов печатает кавычку как `&#34;`.
HOSTILE_ESCAPED = "&#34;&gt;&lt;script&gt;alert(1)&lt;/script&gt;"


async def _register(client: AsyncClient, email: str, name: str = "Входящий") -> None:
    """Регистрация прикладным входом — вместе с пробным сроком."""
    response = await client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "name": name},
    )
    assert response.status_code == 201, (
        f"регистрация не прошла ({response.status_code}) — правило входа красило "
        "бы чужую поломку"
    )


def _session_cookie_set(response) -> bool:
    """Выставил ли ответ cookie сессии с НЕПУСТЫМ значением."""
    for raw in response.headers.get_list("set-cookie"):
        name, _, rest = raw.partition("=")
        if name.strip() == "access_token" and rest.partition(";")[0].strip():
            return True
    return False


@pytest.mark.asyncio
async def test_the_login_path_walks_from_a_wrong_password_to_the_dashboard(
    client: AsyncClient,
):
    """ТРАСЕР ФАЗЫ: неверный пароль → тот же экран с email → верный → кабинет.

    Один клиент проходит путь человека с JavaScript целиком: страница входа,
    ошибка, повтор, кабинет. Звенья, которые здесь сходятся, — постоянный
    якорь шелла, экран включаемым шаблоном, ответ-фрагмент с `<title>` верхним
    узлом, выход ошибки поля и выход полной перезагрузки с cookie на
    возвращённом объекте. Разорванное любое из них ломает путь посреди, а не
    на своём месте.
    """
    email = "walker@test.com"
    await _register(client, email, name="Путник")
    client.cookies.clear()

    page = await client.get("/login")
    assert page.status_code == 200, f"страница входа ответила {page.status_code}"

    wrong = await client.post(
        "/login",
        data={"email": email, "password": WRONG_PASSWORD},
        headers=HTMX_HEADERS,
        follow_redirects=False,
    )
    assert wrong.status_code == 422, (
        "неверный пароль на htmx ответил не 422: правило 422 блока конфигурации "
        "не перерисует экран входа, и человек не увидит, что вход не состоялся"
    )
    assert page.text.count(STEP_ANCHOR) == 1, (
        "на странице входа не ровно один постоянный якорь шага — ответу ошибки "
        "некуда приземлиться"
    )
    assert DOCUMENT_MARK not in wrong.text, (
        "слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ: правило 422 вложит шелл в карточку"
    )
    assert wrong.text.lstrip().startswith(LOGIN_TITLE), (
        "первый узел фрагмента — не `<title>` экрана входа: вкладка не сменит "
        "заголовок, а сам узел уедет в разметку (Находка 4)"
    )
    assert f'value="{email}"' in wrong.text, "введённый email не вернулся в поле"
    assert WRONG_PASSWORD not in wrong.text, "присланный пароль вернулся в ответ (D-04)"
    assert STEP_TARGET in wrong.text, (
        "форма во фрагменте ошибки целится не в якорь шага — вторую отправку "
        "некуда будет приземлить"
    )

    right = await client.post(
        "/login",
        data={"email": email, "password": PASSWORD},
        headers=HTMX_HEADERS,
        follow_redirects=False,
    )
    assert right.status_code == 204, (
        f"верный пароль на htmx ответил {right.status_code} вместо 204"
    )
    assert right.headers.get("HX-Redirect") == "/dashboard", (
        "успех входа ушёл не заголовком полной перезагрузки на кабинет"
    )
    assert "HX-Location" not in right.headers, (
        "успех входа несёт заголовок частичного перехода: смена личности уехала "
        "бы XHR-подменой, а не полной загрузкой (D-10)"
    )
    assert right.content == b"", "у ответа полной перезагрузки есть тело"
    assert _session_cookie_set(right), (
        "cookie сессии не стоит на ответе 204: браузер уйдёт в кабинет без входа "
        "(Landmine CONTEXT — cookie не на том объекте)"
    )

    dashboard = await client.get("/dashboard", follow_redirects=False)
    assert dashboard.status_code == 200, (
        f"кабинет после входа ответил {dashboard.status_code}: заголовок приехал, "
        "а вход молча не состоялся"
    )
    assert '<span class="user-name">Путник</span>' in dashboard.text, (
        "кабинет открылся не для того, кто вошёл"
    )


@pytest.mark.asyncio
async def test_a_wrong_password_redraws_the_login_screen_on_both_transports(
    client: AsyncClient,
):
    """Неверный пароль — 422 с email в поле на ОБОИХ транспортах (D-03, D-04)."""
    email = "wrong@test.com"
    await _register(client, email)
    client.cookies.clear()

    without = await client.post(
        "/login",
        data={"email": email, "password": WRONG_PASSWORD},
        follow_redirects=False,
    )
    assert without.status_code == 422, (
        f"путь без htmx ответил {without.status_code} вместо 422 — код обязан быть "
        "одним на обоих транспортах"
    )
    assert DOCUMENT_MARK in without.text, (
        "человеку без JavaScript приехал фрагмент без шелла вместо страницы входа"
    )
    assert LOGIN_ERROR in without.text, "на странице нет текста ошибки входа"
    assert f'value="{email}"' in without.text, "введённый email не вернулся в поле"
    assert WRONG_PASSWORD not in without.text, "присланный пароль вернулся в ответ"
    assert not _session_cookie_set(without), "неудачный вход выдал cookie сессии"

    over_htmx = await client.post(
        "/login",
        data={"email": email, "password": WRONG_PASSWORD},
        headers=HTMX_HEADERS,
        follow_redirects=False,
    )
    assert over_htmx.status_code == 422, (
        f"путь htmx ответил {over_htmx.status_code} вместо 422"
    )
    assert DOCUMENT_MARK not in over_htmx.text, "слою письма приехал целый документ"
    assert over_htmx.text.lstrip().startswith(LOGIN_TITLE), (
        "первый узел фрагмента ошибки — не `<title>` экрана входа"
    )
    assert LOGIN_ERROR in over_htmx.text, "во фрагменте нет текста ошибки входа"
    assert f'value="{email}"' in over_htmx.text, "введённый email не вернулся в поле"
    assert WRONG_PASSWORD not in over_htmx.text, "присланный пароль вернулся в ответ"
    assert not _session_cookie_set(over_htmx), "неудачный вход выдал cookie сессии"


@pytest.mark.asyncio
async def test_a_hostile_email_comes_back_escaped_on_both_transports(
    client: AsyncClient,
):
    """Враждебный email возвращается ТОЛЬКО экранированным (D-04, T-14-03).

    Эхо едет автоэкранированием окружения шаблонов; фильтр безопасной разметки
    на этом пути вернул бы строку сырой, и закрытие атрибута с внедрённым
    тегом исполнилось бы в чужом браузере.
    """
    for headers in ({}, HTMX_HEADERS):
        response = await client.post(
            "/login",
            data={"email": HOSTILE, "password": WRONG_PASSWORD},
            headers=headers,
            follow_redirects=False,
        )
        transport = "htmx" if headers else "без htmx"
        assert response.status_code == 422, (
            f"враждебный email ({transport}) ответил {response.status_code} вместо 422"
        )
        assert HOSTILE not in response.text, (
            f"враждебный email ({transport}) вернулся СЫРЫМ — внедрённый тег исполнится"
        )
        assert f'value="{HOSTILE_ESCAPED}"' in response.text, (
            f"экранированный email ({transport}) не стоит в поле: эха нет вовсе"
        )


@pytest.mark.asyncio
async def test_a_blocked_user_is_refused_with_422_and_no_cookie_on_both_transports(
    client: AsyncClient, db_session: AsyncSession
):
    """Заблокированный с ВЕРНЫМ паролем — 422, причина словами, cookie нет (D-05).

    Пароль верный намеренно: отказ по неверному паролю не доказал бы, что
    проверка блокировки стоит ДО выдачи cookie.
    """
    email = "blocked-transport@test.com"
    await _register(client, email)
    user = (
        await db_session.execute(select(User).where(User.email == email))
    ).scalar_one()
    user.is_blocked = True
    await db_session.commit()
    client.cookies.clear()

    for headers in ({}, HTMX_HEADERS):
        response = await client.post(
            "/login",
            data={"email": email, "password": PASSWORD},
            headers=headers,
            follow_redirects=False,
        )
        transport = "htmx" if headers else "без htmx"
        assert response.status_code == 422, (
            f"отказ заблокированному ({transport}) ответил {response.status_code} "
            "вместо 422"
        )
        assert BLOCKED_LOGIN_ERROR in response.text, (
            f"отказ заблокированному ({transport}) не назван прежними словами"
        )
        assert f'value="{email}"' in response.text, (
            f"email заблокированного ({transport}) не вернулся в поле"
        )
        assert not _session_cookie_set(response), (
            f"заблокированный ({transport}) получил cookie сессии — блокировка "
            "не действует (D-05, D-30)"
        )


@pytest.mark.asyncio
async def test_a_right_password_leaves_by_a_full_load_with_the_cookie(
    client: AsyncClient,
):
    """Верный пароль — полная загрузка кабинета на обоих транспортах (D-10)."""
    email = "right@test.com"
    await _register(client, email)
    client.cookies.clear()

    without = await client.post(
        "/login",
        data={"email": email, "password": PASSWORD},
        follow_redirects=False,
    )
    assert without.status_code == 302, (
        f"вход без htmx ответил {without.status_code} вместо прежнего 302"
    )
    assert without.headers.get("location") == "/dashboard", (
        "вход без htmx увёл не в кабинет"
    )
    assert _session_cookie_set(without), "вход без htmx не выдал cookie сессии"

    client.cookies.clear()
    over_htmx = await client.post(
        "/login",
        data={"email": email, "password": PASSWORD},
        headers=HTMX_HEADERS,
        follow_redirects=False,
    )
    assert over_htmx.status_code == 204, (
        f"вход на htmx ответил {over_htmx.status_code} вместо 204"
    )
    assert over_htmx.headers.get("HX-Redirect") == "/dashboard", (
        "вход на htmx ушёл не заголовком полной перезагрузки на кабинет"
    )
    assert "HX-Location" not in over_htmx.headers, (
        "вход на htmx несёт второй заголовок перехода"
    )
    assert over_htmx.content == b"", "у ответа полной перезагрузки есть тело"
    assert _session_cookie_set(over_htmx), (
        "cookie сессии не стоит на ответе 204 — вход молча не состоялся"
    )


@pytest.mark.asyncio
async def test_the_login_page_puts_the_step_anchor_after_the_notice_regions(
    client: AsyncClient,
):
    """Якорь шага стоит ПОСЛЕ областей уведомления (RESEARCH Pattern 2, Pitfall 5).

    ⚠️ ПОРЯДОК НЕСУЩИЙ. Области `#notice`/`#notice-alert` долгоживущие: код
    исхода, отрисованный при загрузке `/login?notice=…`, обязан пережить первую
    же ошибку пароля. Попади они внутрь якоря — подмена его содержимого стёрла
    бы их, и сообщение «пароль изменён» исчезло бы с экрана молча.
    """
    page = await client.get("/login")
    anchor = page.text.index(STEP_ANCHOR)
    assert page.text.index('id="notice"') < anchor, (
        "область уведомления стоит внутри или после якоря шага"
    )
    assert page.text.index('id="notice-alert"') < anchor, (
        "аварийная область уведомления стоит внутри или после якоря шага"
    )

    form_tag = re.search(r'<form[^>]*action="/login"[^>]*>', page.text)
    assert form_tag is not None, "на странице входа нет формы с адресом `/login`"
    tag = form_tag.group(0)
    assert 'method="post" action="/login" hx-post="/login"' in tag, (
        "форма входа рождена не макросом-обёрткой: без JavaScript или с ним она "
        "отправляется не туда"
    )
    assert STEP_TARGET in tag, "форма входа целится не в якорь шага"
    assert 'hx-swap="innerHTML"' in tag, (
        "форма входа подменяет не СОДЕРЖИМОЕ якоря — узел якоря умер бы первой "
        "же подменой"
    )

    noticed = await client.get("/login?notice=password_reset_done")
    assert noticed.text.index("Пароль успешно изменён") < noticed.text.index(STEP_ANCHOR), (
        "код исхода рисуется внутри якоря шага и сотрётся первой ошибкой входа"
    )

    wrong = await client.post(
        "/login",
        data={"email": "nobody@test.com", "password": WRONG_PASSWORD},
        headers=HTMX_HEADERS,
        follow_redirects=False,
    )
    assert wrong.status_code == 422, f"ошибка входа ответила {wrong.status_code}"
    assert 'id="notice"' not in wrong.text, (
        "фрагмент ошибки несёт области уведомления — подмена якоря завела бы их "
        "вторую копию"
    )


def test_every_converted_screen_title_matches_its_page():
    """`<title>` фрагмента равен `<title>` страницы того же экрана (D-07).

    Заголовок фрагмента берётся из записи реестра `AUTH_SCREENS`, а заголовок
    страницы — из блока `title` её шаблона; двум записям одного текста негде
    разойтись незаметно только потому, что их сличает это правило.
    """
    from app.pages.auth import AUTH_SCREENS

    assert AUTH_SCREENS, "реестр экранов пуст — сличать нечего (анти-вакуум)"
    for key, screen in AUTH_SCREENS.items():
        source = (TEMPLATES_DIR / screen.page).read_text(encoding="utf-8")
        match = re.search(r"{%\s*block title\s*%}(.*?){%\s*endblock\s*%}", source)
        assert match is not None, f"у страницы экрана `{key}` нет блока title"
        assert match.group(1).strip() == screen.title, (
            f"заголовок фрагмента экрана `{key}` разошёлся с заголовком страницы"
        )


def test_the_screen_builders_refuse_a_password_in_the_context():
    """Пароль в контекст экрана не передаётся НИКОГДА (D-04, T-14-04).

    Отказ стоит у сборщиков, а не у шаблона: шаблон, получивший пароль, мог бы
    однажды его напечатать, и это обнаружилось бы в чужом ответе. Текст ошибки
    значения не подставляет — иначе пароль ушёл бы в журнал трассировкой.
    """
    from app.pages.auth import _screen_builders

    request = Request({"type": "http", "method": "POST", "path": "/login", "headers": []})
    with pytest.raises(ValueError) as refused:
        _screen_builders(request, "login", password="секрет-123")
    assert "секрет-123" not in str(refused.value), (
        "текст отказа подставил сам пароль — он ушёл бы в журнал"
    )


# --- Регистрация: «почта → экран кода» и повтор кода (Фаза 14, план 14-02) -----
#
# ⚠️ СМЕНА ЭКРАНА — 200, ОШИБКА НА ТОМ ЖЕ ЭКРАНЕ — 422 (D-03). Критерий — не
# текст отказа, а то, остаётся ли человек на экране, который заполнял.
#
# ⚠️ ПОДПИСАННЫЙ ТОКЕН ШАГА ЕДЕТ ТОЛЬКО СКРЫТЫМ ПОЛЕМ (D-08): у ответа смены
# экрана нет ни одного заголовка перехода, иначе токен ушёл бы в адрес.

REGISTER_TITLE = "<title>Регистрация — Broadcaster</title>"
REGISTER_VERIFY_TITLE = "<title>Подтверждение email — Broadcaster</title>"
TAKEN_EMAIL_ERROR = "Этот email уже зарегистрирован"
CODE_ALREADY_SENT = "Код уже отправлен. Подождите минуту перед повторной отправкой."
RESEND_TOO_EARLY = "Подождите минуту перед повторной отправкой."
RESEND_DONE = "Новый код отправлен на вашу почту."
STALE_LINK = "Ссылка устарела. Начните регистрацию заново."
NAVIGATION_HEADERS = ("HX-Location", "HX-Redirect", "HX-Push-Url")
TOKEN_FIELD = re.compile(r'name="token" value="([^"]*)"')


async def _seed_code(db_session: AsyncSession, email: str, *, age_seconds: int) -> None:
    """Код регистрации, выданный `age_seconds` секунд назад."""
    now = datetime.now(timezone.utc)
    db_session.add(
        EmailVerificationCode(
            email=email,
            code="123456",
            purpose="registration",
            expires_at=now + timedelta(minutes=10),
            created_at=now - timedelta(seconds=age_seconds),
        )
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_a_taken_email_keeps_the_address_and_answers_422_on_both_transports(
    client: AsyncClient,
):
    """Занятый адрес — 422, прежний текст и адрес в поле на ОБОИХ транспортах.

    Человек остаётся на экране начала регистрации с тем, что ввёл (D-03, D-04);
    текст отказа — прежний (D-15).
    """
    email = "taken-transport@test.com"
    await _register(client, email)
    client.cookies.clear()

    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        response = await client.post(
            "/register/send-code",
            data={"email": email},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 422, (
            f"занятый адрес ({transport}) ответил не 422: человек остаётся на том "
            "же экране, и правило 422 блока конфигурации обязано перерисовать его"
        )
        assert TAKEN_EMAIL_ERROR in response.text, (
            f"занятый адрес ({transport}) не назван прежними словами"
        )
        assert f'value="{email}"' in response.text, (
            f"введённый адрес ({transport}) не вернулся в поле"
        )
        if headers:
            assert DOCUMENT_MARK not in response.text, "слою письма приехал целый документ"
            assert response.text.lstrip().startswith(REGISTER_TITLE), (
                "первый узел фрагмента — не `<title>` экрана регистрации"
            )
        else:
            assert DOCUMENT_MARK in response.text, (
                "человеку без JavaScript приехал фрагмент вместо страницы"
            )


@pytest.mark.asyncio
async def test_the_registration_email_step_answers_the_code_screen_on_both_transports(
    client: AsyncClient,
):
    """Новый адрес — 200 и экран кода; токен скрытым полем, переходов нет.

    Каждая половина берёт СВОЙ адрес: второй запрос на тот же адрес попал бы в
    минуту между кодами и утверждал бы другой исход.
    """
    without = await client.post(
        "/register/send-code",
        data={"email": "step-bare@test.com"},
        follow_redirects=False,
    )
    assert without.status_code == 200, (
        f"шаг адреса без htmx ответил {without.status_code} вместо 200 — путь без "
        "JavaScript обязан получить страницу кода прямо в ответ на POST"
    )
    assert DOCUMENT_MARK in without.text, "путь без htmx получил не страницу"
    assert 'action="/register/verify"' in without.text, "на экране нет формы подтверждения"
    assert 'name="token"' in without.text, "токен шага не едет скрытым полем"

    over_htmx = await client.post(
        "/register/send-code",
        data={"email": "step-htmx@test.com"},
        headers=HTMX_HEADERS,
        follow_redirects=False,
    )
    assert over_htmx.status_code == 200, (
        f"шаг адреса на htmx ответил {over_htmx.status_code} вместо 200"
    )
    assert DOCUMENT_MARK not in over_htmx.text, "слою письма приехал целый документ"
    assert over_htmx.text.lstrip().startswith(REGISTER_VERIFY_TITLE), (
        "первый узел фрагмента — не `<title>` экрана кода"
    )
    assert 'hx-post="/register/resend-code"' in over_htmx.text, (
        "форма повтора во фрагменте рождена не макросом-обёрткой"
    )
    for header in NAVIGATION_HEADERS:
        assert header not in over_htmx.headers, (
            f"смена экрана несёт заголовок перехода {header} (D-08)"
        )


@pytest.mark.asyncio
async def test_a_repeated_email_step_within_a_minute_lands_on_the_code_screen(
    client: AsyncClient,
):
    """«Код уже отправлен» — 200 и экран кода с прежним текстом (D-03, D-15)."""
    email = "repeat@test.com"
    first = await client.post("/register/send-code", data={"email": email})
    assert first.status_code == 200, f"первый шаг адреса ответил {first.status_code}"

    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        response = await client.post(
            "/register/send-code",
            data={"email": email},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, (
            f"повтор шага адреса ({transport}) ответил {response.status_code} вместо 200"
        )
        assert CODE_ALREADY_SENT in response.text, (
            f"повтор шага адреса ({transport}) не назван прежними словами"
        )
        if headers:
            assert response.text.lstrip().startswith(REGISTER_VERIFY_TITLE), (
                "первый узел фрагмента — не `<title>` экрана кода"
            )


@pytest.mark.asyncio
async def test_resending_the_code_redraws_both_forms_with_one_token(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Повтор кода — 200 и ОБЕ формы экрана с ОДНИМ токеном ответа (D-06).

    Повтор выдаёт новый токен, поэтому подменяется весь якорь: подмена одной
    формы оставила бы форму подтверждения со старым (Landmine CONTEXT). Утверждается
    равенство двух полей, а не «токен сменился»: две выдачи внутри одной секунды
    дают один и тот же токен.
    """
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        email = f"resend-{'htmx' if headers else 'bare'}@test.com"
        await _seed_code(db_session, email, age_seconds=120)
        token = create_verification_token(email, test_settings.secret_key)

        response = await client.post(
            "/register/resend-code",
            data={"token": token},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, (
            f"повтор кода ({transport}) ответил {response.status_code} вместо 200"
        )
        assert RESEND_DONE in response.text, (
            f"повтор кода ({transport}) не назван прежними словами"
        )
        tokens = TOKEN_FIELD.findall(response.text)
        assert len(tokens) == 2, (
            f"скрытых полей токена ({transport}) {len(tokens)}, а форм на экране кода две"
        )
        assert tokens[0] == tokens[1] and tokens[0], (
            f"формы экрана кода ({transport}) несут разные токены — одна из них "
            "осталась со старым"
        )
        if headers:
            assert response.text.lstrip().startswith(REGISTER_VERIFY_TITLE), (
                "первый узел фрагмента — не `<title>` экрана кода"
            )


@pytest.mark.asyncio
async def test_resending_within_a_minute_answers_422_on_the_code_screen(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Повтор раньше минуты — 422 на экране кода с присланным токеном (D-03)."""
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        email = f"early-{'htmx' if headers else 'bare'}@test.com"
        await _seed_code(db_session, email, age_seconds=5)
        token = create_verification_token(email, test_settings.secret_key)

        response = await client.post(
            "/register/resend-code",
            data={"token": token},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 422, (
            f"повтор раньше минуты ({transport}) ответил {response.status_code} "
            "вместо 422 — человек остаётся на экране кода"
        )
        assert RESEND_TOO_EARLY in response.text, (
            f"повтор раньше минуты ({transport}) не назван прежними словами"
        )
        assert f'name="token" value="{token}"' in response.text, (
            f"присланный токен ({transport}) не вернулся скрытым полем"
        )


@pytest.mark.asyncio
async def test_resending_with_a_stale_link_returns_to_the_start_of_registration(
    client: AsyncClient,
):
    """Негодный токен — 200 и экран начала регистрации (D-03: «возврат на начало»)."""
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        response = await client.post(
            "/register/resend-code",
            data={"token": "x"},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, (
            f"устаревшая ссылка ({transport}) ответила {response.status_code} вместо 200"
        )
        assert STALE_LINK in response.text, (
            f"устаревшая ссылка ({transport}) не названа прежними словами"
        )
        if headers:
            assert response.text.lstrip().startswith(REGISTER_TITLE), (
                "первый узел фрагмента — не `<title>` экрана регистрации"
            )


@pytest.mark.asyncio
async def test_the_code_screen_carries_the_resend_form_into_the_anchor(
    client: AsyncClient,
):
    """Форма повтора — макросом в якорь; форма подтверждения — настоящим POST.

    Фаза 14, план 14-03: форма подтверждения тоже рождена макросом (правило
    `test_both_code_forms_ride_the_anchor_and_drop_a_second_request`); здесь
    остаётся утверждение о пути без JavaScript — тег по-прежнему шлёт POST.
    """
    page = await client.post(
        "/register/send-code",
        data={"email": "forms@test.com"},
        follow_redirects=False,
    )
    assert page.status_code == 200, f"шаг адреса ответил {page.status_code}"

    resend = re.search(r'<form[^>]*action="/register/resend-code"[^>]*>', page.text)
    assert resend is not None, "на экране кода нет формы повтора"
    tag = resend.group(0)
    assert (
        'method="post" action="/register/resend-code" hx-post="/register/resend-code"'
        in tag
    ), "форма повтора рождена не макросом-обёрткой"
    assert STEP_TARGET in tag, "форма повтора целится не в якорь шага"
    assert 'hx-swap="innerHTML"' in tag, "форма повтора подменяет не СОДЕРЖИМОЕ якоря"

    verify = re.search(r'<form[^>]*action="/register/verify"[^>]*>', page.text)
    assert verify is not None, "на экране кода нет формы подтверждения"
    assert 'method="post" action="/register/verify"' in verify.group(0), (
        "форма подтверждения отправляется не настоящим POST"
    )


# --- Регистрация: «код → имя и пароль → кабинет» (Фаза 14, план 14-03) ---------
#
# ⚠️ НЕВЕРНЫЙ КОД БОЛЬШЕ НЕ СТИРАЕТ НАБРАННОЕ (D-03, D-04): 422 на ТОМ ЖЕ экране,
# код — в `value=`, прежний токен — скрытым полем. Счёт попыток прежний (D-15):
# каждая половина берёт СВОЙ адрес, иначе вторая увидела бы на попытку меньше.
#
# ⚠️ ЗАВЕРШЕНИЕ — ПОЛНАЯ ЗАГРУЗКА С COOKIE НА ТОМ ЖЕ ОТВЕТЕ (D-10, Pitfall 4):
# правило, проверяющее один заголовок, зеленело бы при входе, который молча не
# состоялся, поэтому за ним стоит `GET /dashboard`.

REGISTER_COMPLETE_TITLE = "<title>Завершение регистрации — Broadcaster</title>"
TYPED_CODE = "654321"
SEEDED_CODE = "123456"
WRONG_CODE_ERROR = "Неверный код. Осталось попыток: 4"
EXHAUSTED_CODE_ERROR = "Код истёк или превышено число попыток. Отправьте код заново."
SHORT_PASSWORD_ERROR = "Пароль должен быть не менее 6 символов"
# Пять знаков и `!`: такого символа нет в алфавите подписанного токена, и
# совпасть со случайным куском разметки строке негде.
SHORT_PASSWORD = "p9!zq"


async def _seed_verify_code(
    db_session: AsyncSession, email: str, *, attempts: int = 0
) -> None:
    """Живой код регистрации `SEEDED_CODE` с заданным счётом попыток."""
    now = datetime.now(timezone.utc)
    db_session.add(
        EmailVerificationCode(
            email=email,
            code=SEEDED_CODE,
            purpose="registration",
            expires_at=now + timedelta(minutes=10),
            attempts=attempts,
        )
    )
    await db_session.commit()


def _token_is_verified(token: str, secret_key: str) -> bool:
    payload = decode_verification_token(token, secret_key)
    return bool(payload and payload.get("verified"))


@pytest.mark.asyncio
async def test_a_wrong_code_keeps_the_typed_code_and_answers_422_on_both_transports(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Неверный код — 422, «Осталось попыток: 4», код в поле, прежний токен (D-03, D-04)."""
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        email = f"wrong-code-{'htmx' if headers else 'bare'}@test.com"
        await _seed_verify_code(db_session, email)
        token = create_verification_token(email, test_settings.secret_key)

        response = await client.post(
            "/register/verify",
            data={"token": token, "code": TYPED_CODE},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 422, (
            f"неверный код ({transport}) ответил не 422: человек остаётся на экране "
            "кода, и правило 422 блока конфигурации обязано перерисовать его"
        )
        assert WRONG_CODE_ERROR in response.text, (
            f"неверный код ({transport}) не назван прежними словами с прежним счётом"
        )
        assert f'value="{TYPED_CODE}"' in response.text, (
            f"набранный код ({transport}) не вернулся в поле — ошибка стёрла набранное"
        )
        assert f'name="token" value="{token}"' in response.text, (
            f"присланный токен ({transport}) не вернулся скрытым полем"
        )
        if headers:
            assert DOCUMENT_MARK not in response.text, "слою письма приехал целый документ"
            assert response.text.lstrip().startswith(REGISTER_VERIFY_TITLE), (
                "первый узел фрагмента — не `<title>` экрана кода"
            )
        else:
            assert DOCUMENT_MARK in response.text, (
                "человеку без JavaScript приехал фрагмент вместо страницы"
            )


@pytest.mark.asyncio
async def test_an_exhausted_code_answers_422_with_the_typed_code(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Попытки кончились — 422, прежний текст, код в поле (D-03, D-15)."""
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        email = f"exhausted-{'htmx' if headers else 'bare'}@test.com"
        await _seed_verify_code(db_session, email, attempts=5)
        token = create_verification_token(email, test_settings.secret_key)

        response = await client.post(
            "/register/verify",
            data={"token": token, "code": SEEDED_CODE},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 422, (
            f"исчерпанный код ({transport}) ответил {response.status_code} вместо 422"
        )
        assert EXHAUSTED_CODE_ERROR in response.text, (
            f"исчерпанный код ({transport}) не назван прежними словами"
        )
        assert f'value="{SEEDED_CODE}"' in response.text, (
            f"набранный код ({transport}) не вернулся в поле"
        )
        assert f'name="token" value="{token}"' in response.text, (
            f"присланный токен ({transport}) не вернулся скрытым полем"
        )
        if headers:
            assert response.text.lstrip().startswith(REGISTER_VERIFY_TITLE), (
                "первый узел фрагмента — не `<title>` экрана кода"
            )


@pytest.mark.asyncio
async def test_a_right_code_opens_the_name_and_password_screen_on_both_transports(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Верный код — 200 и экран имени и пароля с подтверждённым токеном (D-03, D-06)."""
    email = "right-code-bare@test.com"
    await _seed_verify_code(db_session, email)
    token = create_verification_token(email, test_settings.secret_key)
    without = await client.post(
        "/register/verify",
        data={"token": token, "code": SEEDED_CODE},
        follow_redirects=False,
    )
    assert without.status_code == 200, (
        f"верный код без htmx ответил {without.status_code} вместо 200"
    )
    assert DOCUMENT_MARK in without.text, "путь без htmx получил не страницу"
    assert 'action="/register/complete"' in without.text, (
        "на экране нет формы завершения регистрации"
    )

    email = "right-code-htmx@test.com"
    await _seed_verify_code(db_session, email)
    token = create_verification_token(email, test_settings.secret_key)
    over_htmx = await client.post(
        "/register/verify",
        data={"token": token, "code": SEEDED_CODE},
        headers=HTMX_HEADERS,
        follow_redirects=False,
    )
    assert over_htmx.status_code == 200, (
        f"верный код на htmx ответил {over_htmx.status_code} вместо 200"
    )
    assert DOCUMENT_MARK not in over_htmx.text, "слою письма приехал целый документ"
    assert over_htmx.text.lstrip().startswith(REGISTER_COMPLETE_TITLE), (
        "первый узел фрагмента — не `<title>` экрана завершения"
    )
    assert 'hx-post="/register/complete"' in over_htmx.text, (
        "форма завершения во фрагменте рождена не макросом-обёрткой"
    )
    tokens = TOKEN_FIELD.findall(over_htmx.text)
    assert len(tokens) == 1 and _token_is_verified(tokens[0], test_settings.secret_key), (
        "экран завершения несёт не один подтверждённый токен скрытым полем"
    )
    for header in NAVIGATION_HEADERS:
        assert header not in over_htmx.headers, (
            f"смена экрана несёт заголовок перехода {header} (D-08)"
        )


@pytest.mark.asyncio
async def test_a_stale_link_on_the_code_step_returns_to_the_start_of_registration(
    client: AsyncClient,
):
    """Негодный токен на шаге кода — 200 и экран начала регистрации (D-03)."""
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        response = await client.post(
            "/register/verify",
            data={"token": "x", "code": SEEDED_CODE},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, (
            f"устаревшая ссылка ({transport}) ответила {response.status_code} вместо 200"
        )
        assert STALE_LINK in response.text, (
            f"устаревшая ссылка ({transport}) не названа прежними словами"
        )
        assert 'action="/register/send-code"' in response.text, (
            f"устаревшая ссылка ({transport}) вернула не на начало регистрации"
        )
        if headers:
            assert response.text.lstrip().startswith(REGISTER_TITLE), (
                "первый узел фрагмента — не `<title>` экрана регистрации"
            )


@pytest.mark.asyncio
async def test_a_hostile_code_and_name_come_back_escaped(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Враждебные код и имя — экранированными в `value=`, сырыми никогда (D-04, T-14-03)."""
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        email = f"hostile-code-{'htmx' if headers else 'bare'}@test.com"
        await _seed_verify_code(db_session, email)
        token = create_verification_token(email, test_settings.secret_key)

        code_step = await client.post(
            "/register/verify",
            data={"token": token, "code": HOSTILE},
            headers=headers,
            follow_redirects=False,
        )
        assert HOSTILE not in code_step.text, (
            f"враждебный код ({transport}) вернулся сырым — эхо без экранирования"
        )
        assert f'value="{HOSTILE_ESCAPED}"' in code_step.text, (
            f"враждебный код ({transport}) не вернулся экранированным в поле"
        )

        verified = create_verification_token(
            email, test_settings.secret_key, verified=True
        )
        name_step = await client.post(
            "/register/complete",
            data={"token": verified, "name": HOSTILE, "password": SHORT_PASSWORD},
            headers=headers,
            follow_redirects=False,
        )
        assert HOSTILE not in name_step.text, (
            f"враждебное имя ({transport}) вернулось сырым — эхо без экранирования"
        )
        assert f'value="{HOSTILE_ESCAPED}"' in name_step.text, (
            f"враждебное имя ({transport}) не вернулось экранированным в поле"
        )


@pytest.mark.asyncio
async def test_a_short_password_keeps_the_name_and_answers_422_without_the_password(
    client: AsyncClient, test_settings
):
    """Короткий пароль — 422, имя в поле, пароля в теле нет, новый подтверждённый токен."""
    name = "Новичок"
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        email = f"short-{'htmx' if headers else 'bare'}@test.com"
        verified = create_verification_token(
            email, test_settings.secret_key, verified=True
        )
        response = await client.post(
            "/register/complete",
            data={"token": verified, "name": name, "password": SHORT_PASSWORD},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 422, (
            f"короткий пароль ({transport}) ответил {response.status_code} вместо 422 — "
            "человек остаётся на экране завершения"
        )
        assert SHORT_PASSWORD_ERROR in response.text, (
            f"короткий пароль ({transport}) не назван прежними словами"
        )
        assert f'value="{name}"' in response.text, (
            f"введённое имя ({transport}) не вернулось в поле"
        )
        assert SHORT_PASSWORD not in response.text, (
            f"присланный пароль ({transport}) вернулся в ответ (D-04)"
        )
        tokens = TOKEN_FIELD.findall(response.text)
        assert len(tokens) == 1 and _token_is_verified(tokens[0], test_settings.secret_key), (
            f"экран завершения ({transport}) несёт не один подтверждённый токен"
        )
        if headers:
            assert DOCUMENT_MARK not in response.text, "слою письма приехал целый документ"
            assert response.text.lstrip().startswith(REGISTER_COMPLETE_TITLE), (
                "первый узел фрагмента — не `<title>` экрана завершения"
            )
        else:
            assert DOCUMENT_MARK in response.text, (
                "человеку без JavaScript приехал фрагмент вместо страницы"
            )


@pytest.mark.asyncio
async def test_a_taken_address_at_completion_returns_to_the_start_with_200(
    client: AsyncClient, test_settings
):
    """Адрес занят к завершению — 200 и экран начала (экран сменился: D-03, RESEARCH OQ 3)."""
    email = "raced@test.com"
    await _register(client, email)
    client.cookies.clear()
    verified = create_verification_token(email, test_settings.secret_key, verified=True)

    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        response = await client.post(
            "/register/complete",
            data={"token": verified, "name": "Второй", "password": PASSWORD},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, (
            f"занятый к завершению адрес ({transport}) ответил {response.status_code} "
            "вместо 200 — экран сменился на начало регистрации"
        )
        assert TAKEN_EMAIL_ERROR in response.text, (
            f"занятый адрес ({transport}) не назван прежними словами"
        )
        assert 'action="/register/send-code"' in response.text, (
            f"занятый адрес ({transport}) вернул не на начало регистрации"
        )
        assert not _session_cookie_set(response), (
            f"занятый адрес ({transport}) выдал cookie сессии"
        )
        if headers:
            assert response.text.lstrip().startswith(REGISTER_TITLE), (
                "первый узел фрагмента — не `<title>` экрана регистрации"
            )


@pytest.mark.asyncio
async def test_completing_registration_leaves_by_a_full_load_with_the_cookie_and_the_trial(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Завершение — 302 / 204 + `HX-Redirect`, cookie на том же ответе, пробный срок (D-10, D-B)."""
    email = "complete-bare@test.com"
    verified = create_verification_token(email, test_settings.secret_key, verified=True)
    without = await client.post(
        "/register/complete",
        data={"token": verified, "name": "Без скрипта", "password": PASSWORD},
        follow_redirects=False,
    )
    assert without.status_code == 302, (
        f"завершение без htmx ответило {without.status_code} вместо прежнего 302"
    )
    assert without.headers.get("location") == "/dashboard", (
        "завершение без htmx увело не в кабинет"
    )
    assert _session_cookie_set(without), "завершение без htmx не выдало cookie сессии"

    client.cookies.clear()
    email = "complete-htmx@test.com"
    verified = create_verification_token(email, test_settings.secret_key, verified=True)
    over_htmx = await client.post(
        "/register/complete",
        data={"token": verified, "name": "Со скриптом", "password": PASSWORD},
        headers=HTMX_HEADERS,
        follow_redirects=False,
    )
    assert over_htmx.status_code == 204, (
        f"завершение на htmx ответило {over_htmx.status_code} вместо 204"
    )
    assert over_htmx.headers.get("HX-Redirect") == "/dashboard", (
        "завершение на htmx ушло не заголовком полной перезагрузки на кабинет"
    )
    assert "HX-Location" not in over_htmx.headers, (
        "завершение на htmx несёт заголовок частичного перехода (D-10)"
    )
    assert over_htmx.content == b"", "у ответа полной перезагрузки есть тело"
    assert _session_cookie_set(over_htmx), (
        "cookie сессии не стоит на ответе 204 — регистрация молча не вошла "
        "(Landmine CONTEXT — cookie не на том объекте)"
    )

    user = (
        await db_session.execute(select(User).where(User.email == email))
    ).scalar_one()
    rows = (
        await db_session.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
    ).scalars().all()
    assert len(rows) == 1, (
        f"строк подписки у нового пользователя {len(rows)}, а пробный срок — одна (D-B)"
    )

    dashboard = await client.get("/dashboard", follow_redirects=False)
    assert dashboard.status_code == 200, (
        f"кабинет после регистрации ответил {dashboard.status_code}: заголовок "
        "приехал, а вход или доступ молча не состоялись"
    )
    assert '<span class="user-name">Со скриптом</span>' in dashboard.text, (
        "кабинет открылся не для того, кто зарегистрировался"
    )


@pytest.mark.asyncio
async def test_both_code_forms_ride_the_anchor_and_drop_a_second_request(
    client: AsyncClient,
):
    """Обе формы экрана кода — макросом в якорь, второй запрос отбрасывается (Pattern 5)."""
    page = await client.post(
        "/register/send-code",
        data={"email": "two-forms@test.com"},
        follow_redirects=False,
    )
    assert page.status_code == 200, f"шаг адреса ответил {page.status_code}"

    for action in ("/register/verify", "/register/resend-code"):
        found = re.search(rf'<form[^>]*action="{action}"[^>]*>', page.text)
        assert found is not None, f"на экране кода нет формы {action}"
        tag = found.group(0)
        assert f'hx-post="{action}"' in tag, f"форма {action} рождена не макросом-обёрткой"
        assert STEP_TARGET in tag, f"форма {action} целится не в якорь шага"
        assert 'hx-swap="innerHTML"' in tag, f"форма {action} подменяет не СОДЕРЖИМОЕ якоря"
        assert 'hx-sync="closest #auth-step:drop"' in tag, (
            f"форма {action} не отбрасывает второй запрос, пока летит первый"
        )


# --- Восстановление: «почта → экран кода» и повтор кода (Фаза 14, план 14-04) ---
#
# ⚠️ ТО ЖЕ УСТРОЙСТВО, ЧТО У РЕГИСТРАЦИИ (план 14-02): смена экрана — 200,
# ошибка на том же экране — 422 (D-03); экран кода приезжает в якорь целиком, и
# обе его формы несут токен восстановления только скрытым полем (D-06, D-08).
#
# ⚠️ ФОРМА ПОДТВЕРЖДЕНИЯ КОДА ВОССТАНОВЛЕНИЯ — ПОКА ОБЫЧНАЯ ФОРМА (окно до плана
# 14-05): её обработчик ещё отвечает готовыми страницами. Здесь утверждается
# только, что она отправляется настоящим POST.
# Окно закрыто планом 14-05: форма рождена макросом-обёрткой, и настоящий POST
# она по-прежнему несёт — утверждение ниже остаётся верным и после перевода.
#
# ⚠️ ОТКАЗ ПОД ЧУЖОЙ ЛИЧНОСТЬЮ НЕ ПЕРЕДЕЛЫВАЕТСЯ (D-13): зависимость отказа уже
# отвечает двумя транспортами; правило ниже закрепляет её половину htmx на двух
# переведённых шагах вместе с тем, что ни кода, ни письма не заводится.

FORGOT_TITLE = "<title>Забыли пароль — Broadcaster</title>"
FORGOT_VERIFY_TITLE = "<title>Код подтверждения — Broadcaster</title>"
UNKNOWN_EMAIL_ERROR = "Пользователь с таким email не найден"
RESET_STALE_LINK = "Ссылка устарела. Начните сброс пароля заново."
IMPERSONATION_REFUSED_LOCATION = "/dashboard?notice=impersonation_forbidden"


async def _seed_reset_code(
    db_session: AsyncSession, email: str, *, age_seconds: int
) -> None:
    """Код восстановления, выданный `age_seconds` секунд назад."""
    now = datetime.now(timezone.utc)
    db_session.add(
        EmailVerificationCode(
            email=email,
            code="123456",
            purpose="password_reset",
            expires_at=now + timedelta(minutes=10),
            created_at=now - timedelta(seconds=age_seconds),
        )
    )
    await db_session.commit()


def _reset_token(email: str, secret_key: str) -> str:
    return create_verification_token(email, secret_key, purpose="password_reset")


@pytest.mark.asyncio
async def test_an_unknown_email_keeps_the_address_and_answers_422_on_both_transports(
    client: AsyncClient,
):
    """Неизвестный адрес — 422, прежний текст и адрес в поле на ОБОИХ транспортах.

    Человек остаётся на экране начала восстановления с тем, что ввёл (D-03,
    D-04); текст отказа — прежний (D-15).
    """
    email = "nobody-recovery@test.com"
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        response = await client.post(
            "/forgot-password/send-code",
            data={"email": email},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 422, (
            f"неизвестный адрес ({transport}) ответил не 422: человек остаётся на "
            "том же экране, и правило 422 блока конфигурации обязано перерисовать его"
        )
        assert UNKNOWN_EMAIL_ERROR in response.text, (
            f"неизвестный адрес ({transport}) не назван прежними словами"
        )
        assert f'value="{email}"' in response.text, (
            f"введённый адрес ({transport}) не вернулся в поле"
        )
        if headers:
            assert DOCUMENT_MARK not in response.text, "слою письма приехал целый документ"
            assert response.text.lstrip().startswith(FORGOT_TITLE), (
                "первый узел фрагмента — не `<title>` экрана начала восстановления"
            )
        else:
            assert DOCUMENT_MARK in response.text, (
                "человеку без JavaScript приехал фрагмент вместо страницы"
            )


@pytest.mark.asyncio
async def test_the_recovery_email_step_answers_the_code_screen_on_both_transports(
    client: AsyncClient,
):
    """Известный адрес — 200 и экран кода; токен скрытым полем, переходов нет.

    Каждая половина берёт СВОЙ адрес: второй запрос на тот же адрес попал бы в
    минуту между кодами и утверждал бы другой исход.
    """
    await _register(client, "recovery-bare@test.com")
    await _register(client, "recovery-htmx@test.com")
    client.cookies.clear()

    without = await client.post(
        "/forgot-password/send-code",
        data={"email": "recovery-bare@test.com"},
        follow_redirects=False,
    )
    assert without.status_code == 200, (
        f"шаг адреса восстановления без htmx ответил {without.status_code} вместо "
        "200 — путь без JavaScript обязан получить страницу кода прямо в ответ на POST"
    )
    assert DOCUMENT_MARK in without.text, "путь без htmx получил не страницу"
    assert 'action="/forgot-password/verify"' in without.text, (
        "на экране кода нет формы подтверждения"
    )
    assert 'name="token"' in without.text, "токен восстановления не едет скрытым полем"

    over_htmx = await client.post(
        "/forgot-password/send-code",
        data={"email": "recovery-htmx@test.com"},
        headers=HTMX_HEADERS,
        follow_redirects=False,
    )
    assert over_htmx.status_code == 200, (
        f"шаг адреса восстановления на htmx ответил {over_htmx.status_code} вместо 200"
    )
    assert DOCUMENT_MARK not in over_htmx.text, "слою письма приехал целый документ"
    assert over_htmx.text.lstrip().startswith(FORGOT_VERIFY_TITLE), (
        "первый узел фрагмента — не `<title>` экрана кода восстановления"
    )
    assert 'hx-post="/forgot-password/resend-code"' in over_htmx.text, (
        "форма повтора во фрагменте рождена не макросом-обёрткой"
    )
    assert 'name="token"' in over_htmx.text, "токен восстановления не едет скрытым полем"
    verify = re.search(r'<form[^>]*action="/forgot-password/verify"[^>]*>', over_htmx.text)
    assert verify is not None, "во фрагменте нет формы подтверждения"
    assert 'method="post" action="/forgot-password/verify"' in verify.group(0), (
        "форма подтверждения отправляется не настоящим POST"
    )
    for header in NAVIGATION_HEADERS:
        assert header not in over_htmx.headers, (
            f"смена экрана несёт заголовок перехода {header} (D-08)"
        )


@pytest.mark.asyncio
async def test_a_repeated_recovery_step_within_a_minute_lands_on_the_code_screen(
    client: AsyncClient,
):
    """«Код уже отправлен» — 200 и экран кода с прежним текстом (D-03, D-15)."""
    email = "recovery-repeat@test.com"
    await _register(client, email)
    client.cookies.clear()
    first = await client.post("/forgot-password/send-code", data={"email": email})
    assert first.status_code == 200, f"первый шаг адреса ответил {first.status_code}"

    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        response = await client.post(
            "/forgot-password/send-code",
            data={"email": email},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, (
            f"повтор шага адреса ({transport}) ответил {response.status_code} вместо 200"
        )
        assert CODE_ALREADY_SENT in response.text, (
            f"повтор шага адреса ({transport}) не назван прежними словами"
        )
        assert 'name="token"' in response.text, (
            f"экран кода ({transport}) пришёл без токена восстановления"
        )
        if headers:
            assert response.text.lstrip().startswith(FORGOT_VERIFY_TITLE), (
                "первый узел фрагмента — не `<title>` экрана кода восстановления"
            )


@pytest.mark.asyncio
async def test_resending_the_recovery_code_redraws_both_forms_with_one_token(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Повтор кода восстановления — 200 и ОБЕ формы с ОДНИМ токеном ответа (D-06).

    Повтор выдаёт новый токен, поэтому подменяется весь якорь (Landmine
    CONTEXT). Утверждается равенство двух полей, а не «токен сменился»: две
    выдачи внутри одной секунды дают один и тот же токен.
    """
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        email = f"recovery-resend-{'htmx' if headers else 'bare'}@test.com"
        await _seed_reset_code(db_session, email, age_seconds=120)

        response = await client.post(
            "/forgot-password/resend-code",
            data={"token": _reset_token(email, test_settings.secret_key)},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, (
            f"повтор кода восстановления ({transport}) ответил "
            f"{response.status_code} вместо 200"
        )
        assert RESEND_DONE in response.text, (
            f"повтор кода восстановления ({transport}) не назван прежними словами"
        )
        tokens = TOKEN_FIELD.findall(response.text)
        assert len(tokens) == 2, (
            f"скрытых полей токена ({transport}) {len(tokens)}, а форм на экране кода две"
        )
        assert tokens[0] == tokens[1] and tokens[0], (
            f"формы экрана кода ({transport}) несут разные токены — одна из них "
            "осталась со старым"
        )
        if headers:
            assert response.text.lstrip().startswith(FORGOT_VERIFY_TITLE), (
                "первый узел фрагмента — не `<title>` экрана кода восстановления"
            )


@pytest.mark.asyncio
async def test_resending_the_recovery_code_within_a_minute_answers_422(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Повтор раньше минуты — 422 на экране кода с присланным токеном (D-03)."""
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        email = f"recovery-early-{'htmx' if headers else 'bare'}@test.com"
        await _seed_reset_code(db_session, email, age_seconds=5)
        token = _reset_token(email, test_settings.secret_key)

        response = await client.post(
            "/forgot-password/resend-code",
            data={"token": token},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 422, (
            f"повтор раньше минуты ({transport}) ответил {response.status_code} "
            "вместо 422 — человек остаётся на экране кода"
        )
        assert RESEND_TOO_EARLY in response.text, (
            f"повтор раньше минуты ({transport}) не назван прежними словами"
        )
        assert f'name="token" value="{token}"' in response.text, (
            f"присланный токен ({transport}) не вернулся скрытым полем"
        )
        if headers:
            assert response.text.lstrip().startswith(FORGOT_VERIFY_TITLE), (
                "первый узел фрагмента — не `<title>` экрана кода восстановления"
            )


@pytest.mark.asyncio
async def test_resending_with_a_stale_recovery_link_returns_to_the_start(
    client: AsyncClient,
):
    """Негодный токен — 200 и экран начала восстановления (D-03: «возврат на начало»)."""
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        response = await client.post(
            "/forgot-password/resend-code",
            data={"token": "x"},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, (
            f"устаревшая ссылка ({transport}) ответила {response.status_code} вместо 200"
        )
        assert RESET_STALE_LINK in response.text, (
            f"устаревшая ссылка ({transport}) не названа прежними словами"
        )
        if headers:
            assert response.text.lstrip().startswith(FORGOT_TITLE), (
                "первый узел фрагмента — не `<title>` экрана начала восстановления"
            )


@pytest.mark.asyncio
async def test_the_first_recovery_steps_are_refused_under_another_identity_on_both_transports(
    admin_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Под чужой личностью оба переведённых шага закрыты на ОБОИХ транспортах (D-13, D-22).

    Без признака htmx — 403, как сегодня; с ним — 204 и переход заголовком на
    домашний экран с кодом отказа, без тела: тело `detail` слой письма никуда
    не показывает. Ни кода восстановления, ни письма не заводится — иначе
    захват учётной записи начался бы и остановился на полпути.
    """
    from tests.test_pages.test_impersonation import TARGET_EMAIL, _enter, _seed_target

    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    async def _reset_codes() -> int:
        rows = await db_session.execute(
            select(EmailVerificationCode).where(
                EmailVerificationCode.purpose == "password_reset"
            )
        )
        return len(rows.scalars().all())

    before = await _reset_codes()
    # Годный токен восстановления: отказ обязан стоять ДО разбора токена, а не
    # случиться потому, что ссылка устарела.
    token = _reset_token(TARGET_EMAIL, test_settings.secret_key)

    for path, payload in (
        ("/forgot-password/send-code", {"email": TARGET_EMAIL}),
        ("/forgot-password/resend-code", {"token": token}),
    ):
        bare = await admin_client.post(path, data=payload, follow_redirects=False)
        assert bare.status_code == 403, (
            f"{path} без htmx ответил {bare.status_code} под чужой личностью — "
            "администратор может перехватить пароль пользователя"
        )

        over_htmx = await admin_client.post(
            path, data=payload, headers=HTMX_HEADERS, follow_redirects=False
        )
        assert over_htmx.status_code == 204, (
            f"{path} на htmx ответил {over_htmx.status_code} под чужой личностью "
            "вместо 204 — отказ пришёл бы телом в якорь"
        )
        assert over_htmx.headers.get("HX-Location") == IMPERSONATION_REFUSED_LOCATION, (
            f"{path} на htmx ведёт отказ не на домашний экран с кодом отказа"
        )
        assert over_htmx.content == b"", f"{path} на htmx несёт тело отказа"

    assert await _reset_codes() == before, (
        "под чужой личностью заведён код восстановления — письмо ушло бы на почту "
        "пользователя"
    )


# --- Восстановление: «код → новый пароль → вход с уведомлением» (Фаза 14, план 14-05)
#
# ⚠️ ТО ЖЕ УСТРОЙСТВО, ЧТО У РЕГИСТРАЦИИ (план 14-03): неверный код и короткий
# пароль — 422 на том же экране с набранным, КРОМЕ пароля (D-03, D-04); смена
# экрана — 200; успех — полная загрузка на `/login` с кодом исхода, который
# рисует область уведомления шелла ВНЕ якоря (D-10, FOUND-05, Pitfall 5).
#
# ⚠️ COOKIE СЕССИИ СМЕНА ПАРОЛЯ НЕ ВЫДАЁТ: человек входит новым паролем сам.

FORGOT_RESET_TITLE = "<title>Новый пароль — Broadcaster</title>"
RESET_DONE_TEXT = "Пароль успешно изменён. Войдите с новым паролем."
RESET_DONE_LANDING = "/login?notice=password_reset_done"
VANISHED_USER_ERROR = "Пользователь не найден."
NEW_PASSWORD = "fresh-pass-456"
SUBTITLE = re.compile(r'<p class="auth-subtitle">([^<]*)</p>')


async def _seed_recovery_code(
    db_session: AsyncSession, email: str, *, attempts: int = 0
) -> None:
    """Живой код восстановления `SEEDED_CODE` с заданным счётом попыток."""
    now = datetime.now(timezone.utc)
    db_session.add(
        EmailVerificationCode(
            email=email,
            code=SEEDED_CODE,
            purpose="password_reset",
            expires_at=now + timedelta(minutes=10),
            attempts=attempts,
        )
    )
    await db_session.commit()


def _verified_reset_token(email: str, secret_key: str) -> str:
    return create_verification_token(
        email, secret_key, verified=True, purpose="password_reset"
    )


def _is_verified_reset_token(token: str, secret_key: str) -> bool:
    payload = decode_verification_token(token, secret_key)
    return bool(
        payload
        and payload.get("verified")
        and payload.get("purpose") == "password_reset"
    )


def _no_session_cookie_at_all(response) -> bool:
    """Ни одного заголовка `set-cookie` с cookie сессии — ни с значением, ни снятия."""
    return all(
        "access_token" not in raw for raw in response.headers.get_list("set-cookie")
    )


@pytest.mark.asyncio
async def test_a_short_new_password_answers_422_without_echo_on_both_transports(
    client: AsyncClient, test_settings
):
    """Короткий новый пароль — 422, текст прежний, пароля в теле нет, новый токен (D-03, D-04)."""
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        email = f"reset-short-{'htmx' if headers else 'bare'}@test.com"
        await _register(client, email)
        client.cookies.clear()

        response = await client.post(
            "/forgot-password/reset",
            data={
                "token": _verified_reset_token(email, test_settings.secret_key),
                "password": SHORT_PASSWORD,
            },
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 422, (
            f"короткий новый пароль ({transport}) ответил не 422: человек остаётся "
            "на экране нового пароля, и правило 422 блока конфигурации обязано "
            "перерисовать его"
        )
        assert SHORT_PASSWORD_ERROR in response.text, (
            f"короткий новый пароль ({transport}) не назван прежними словами"
        )
        assert SHORT_PASSWORD not in response.text, (
            f"присланный пароль ({transport}) вернулся в ответ (D-04)"
        )
        tokens = TOKEN_FIELD.findall(response.text)
        assert len(tokens) == 1 and _is_verified_reset_token(
            tokens[0], test_settings.secret_key
        ), f"экран нового пароля ({transport}) несёт не один подтверждённый токен"
        if headers:
            assert DOCUMENT_MARK not in response.text, "слою письма приехал целый документ"
            assert response.text.lstrip().startswith(FORGOT_RESET_TITLE), (
                "первый узел фрагмента — не `<title>` экрана нового пароля"
            )
        else:
            assert DOCUMENT_MARK in response.text, (
                "человеку без JavaScript приехал фрагмент вместо страницы"
            )


@pytest.mark.asyncio
async def test_a_wrong_recovery_code_keeps_the_typed_code_and_answers_422(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Неверный код — 422, «Осталось попыток: 4», код в поле; исчерпанный — 422 (D-03, D-15)."""
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        suffix = "htmx" if headers else "bare"

        email = f"reset-wrong-{suffix}@test.com"
        await _seed_recovery_code(db_session, email)
        token = _reset_token(email, test_settings.secret_key)
        wrong = await client.post(
            "/forgot-password/verify",
            data={"token": token, "code": TYPED_CODE},
            headers=headers,
            follow_redirects=False,
        )
        assert wrong.status_code == 422, (
            f"неверный код восстановления ({transport}) ответил {wrong.status_code} "
            "вместо 422 — человек остаётся на экране кода"
        )
        assert WRONG_CODE_ERROR in wrong.text, (
            f"неверный код ({transport}) не назван прежними словами с прежним счётом"
        )
        assert f'value="{TYPED_CODE}"' in wrong.text, (
            f"набранный код ({transport}) не вернулся в поле — ошибка стёрла набранное"
        )
        assert f'name="token" value="{token}"' in wrong.text, (
            f"присланный токен ({transport}) не вернулся скрытым полем"
        )

        email = f"reset-exhausted-{suffix}@test.com"
        await _seed_recovery_code(db_session, email, attempts=5)
        token = _reset_token(email, test_settings.secret_key)
        exhausted = await client.post(
            "/forgot-password/verify",
            data={"token": token, "code": SEEDED_CODE},
            headers=headers,
            follow_redirects=False,
        )
        assert exhausted.status_code == 422, (
            f"исчерпанный код ({transport}) ответил {exhausted.status_code} вместо 422"
        )
        assert EXHAUSTED_CODE_ERROR in exhausted.text, (
            f"исчерпанный код ({transport}) не назван прежними словами"
        )
        assert f'value="{SEEDED_CODE}"' in exhausted.text, (
            f"набранный код ({transport}) не вернулся в поле"
        )

        for response in (wrong, exhausted):
            if headers:
                assert DOCUMENT_MARK not in response.text, "слою письма приехал целый документ"
                assert response.text.lstrip().startswith(FORGOT_VERIFY_TITLE), (
                    "первый узел фрагмента — не `<title>` экрана кода восстановления"
                )
            else:
                assert DOCUMENT_MARK in response.text, (
                    "человеку без JavaScript приехал фрагмент вместо страницы"
                )


@pytest.mark.asyncio
async def test_a_right_recovery_code_opens_the_new_password_screen(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Верный код — 200 и экран нового пароля с подтверждённым токеном (D-03, D-06)."""
    email = "reset-right-bare@test.com"
    await _seed_recovery_code(db_session, email)
    without = await client.post(
        "/forgot-password/verify",
        data={"token": _reset_token(email, test_settings.secret_key), "code": SEEDED_CODE},
        follow_redirects=False,
    )
    assert without.status_code == 200, (
        f"верный код без htmx ответил {without.status_code} вместо 200"
    )
    assert DOCUMENT_MARK in without.text, "путь без htmx получил не страницу"
    assert 'action="/forgot-password/reset"' in without.text, (
        "на экране нет формы нового пароля"
    )

    email = "reset-right-htmx@test.com"
    await _seed_recovery_code(db_session, email)
    over_htmx = await client.post(
        "/forgot-password/verify",
        data={"token": _reset_token(email, test_settings.secret_key), "code": SEEDED_CODE},
        headers=HTMX_HEADERS,
        follow_redirects=False,
    )
    assert over_htmx.status_code == 200, (
        f"верный код на htmx ответил {over_htmx.status_code} вместо 200"
    )
    assert DOCUMENT_MARK not in over_htmx.text, "слою письма приехал целый документ"
    assert over_htmx.text.lstrip().startswith(FORGOT_RESET_TITLE), (
        "первый узел фрагмента — не `<title>` экрана нового пароля"
    )
    assert 'hx-post="/forgot-password/reset"' in over_htmx.text, (
        "форма нового пароля во фрагменте рождена не макросом-обёрткой"
    )
    tokens = TOKEN_FIELD.findall(over_htmx.text)
    assert len(tokens) == 1 and _is_verified_reset_token(
        tokens[0], test_settings.secret_key
    ), "экран нового пароля несёт не один подтверждённый токен скрытым полем"
    for header in NAVIGATION_HEADERS:
        assert header not in over_htmx.headers, (
            f"смена экрана несёт заголовок перехода {header} (D-08)"
        )


@pytest.mark.asyncio
async def test_stale_recovery_links_return_to_the_start_with_200(client: AsyncClient):
    """Негодный токен на подтверждении и новом пароле — 200 и экран начала (D-03)."""
    for path, payload in (
        ("/forgot-password/verify", {"token": "x", "code": SEEDED_CODE}),
        ("/forgot-password/reset", {"token": "x", "password": NEW_PASSWORD}),
    ):
        for headers in ({}, HTMX_HEADERS):
            transport = "htmx" if headers else "без htmx"
            response = await client.post(
                path, data=payload, headers=headers, follow_redirects=False
            )
            assert response.status_code == 200, (
                f"{path}: устаревшая ссылка ({transport}) ответила "
                f"{response.status_code} вместо 200"
            )
            assert RESET_STALE_LINK in response.text, (
                f"{path}: устаревшая ссылка ({transport}) не названа прежними словами"
            )
            assert 'action="/forgot-password/send-code"' in response.text, (
                f"{path}: устаревшая ссылка ({transport}) вернула не на начало"
            )
            assert NEW_PASSWORD not in response.text, (
                f"{path}: присланный пароль ({transport}) вернулся в ответ (D-04)"
            )
            if headers:
                assert response.text.lstrip().startswith(FORGOT_TITLE), (
                    f"{path}: первый узел фрагмента — не `<title>` экрана начала"
                )


@pytest.mark.asyncio
async def test_a_vanished_user_returns_to_the_start_of_recovery_with_200(
    client: AsyncClient, test_settings
):
    """Подтверждённый токен на адрес без пользователя — 200 и экран начала (D-03)."""
    token = _verified_reset_token("reset-vanished@test.com", test_settings.secret_key)
    for headers in ({}, HTMX_HEADERS):
        transport = "htmx" if headers else "без htmx"
        response = await client.post(
            "/forgot-password/reset",
            data={"token": token, "password": NEW_PASSWORD},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, (
            f"исчезнувший пользователь ({transport}) ответил {response.status_code} "
            "вместо 200 — экран сменился на начало восстановления"
        )
        assert VANISHED_USER_ERROR in response.text, (
            f"исчезнувший пользователь ({transport}) не назван прежними словами"
        )
        assert NEW_PASSWORD not in response.text, (
            f"присланный пароль ({transport}) вернулся в ответ (D-04)"
        )
        if headers:
            assert response.text.lstrip().startswith(FORGOT_TITLE), (
                "первый узел фрагмента — не `<title>` экрана начала восстановления"
            )


@pytest.mark.asyncio
async def test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice(
    client: AsyncClient, test_settings
):
    """Новый пароль — 302 / 204 + `HX-Redirect` на `/login` с кодом исхода (D-10, FOUND-05).

    Cookie сессии смена пароля не выдаёт ни на одном транспорте; исход рисует
    область уведомления шелла ДО якоря, и вход новым паролем проходит.
    """
    email = "reset-done@test.com"
    await _register(client, email)
    client.cookies.clear()
    token = _verified_reset_token(email, test_settings.secret_key)

    without = await client.post(
        "/forgot-password/reset",
        data={"token": token, "password": NEW_PASSWORD},
        follow_redirects=False,
    )
    assert without.status_code == 302, (
        f"новый пароль без htmx ответил {without.status_code} вместо прежнего 302"
    )
    assert without.headers.get("location") == RESET_DONE_LANDING, (
        "новый пароль без htmx увёл не на вход с кодом исхода"
    )
    assert _no_session_cookie_at_all(without), (
        "смена пароля без htmx тронула cookie сессии"
    )

    over_htmx = await client.post(
        "/forgot-password/reset",
        data={"token": token, "password": NEW_PASSWORD},
        headers=HTMX_HEADERS,
        follow_redirects=False,
    )
    assert over_htmx.status_code == 204, (
        f"новый пароль на htmx ответил {over_htmx.status_code} вместо 204"
    )
    assert over_htmx.headers.get("HX-Redirect") == RESET_DONE_LANDING, (
        "новый пароль на htmx ушёл не заголовком полной перезагрузки на вход"
    )
    assert "HX-Location" not in over_htmx.headers, (
        "новый пароль на htmx несёт заголовок частичного перехода (D-10)"
    )
    assert over_htmx.content == b"", "у ответа полной перезагрузки есть тело"
    assert _no_session_cookie_at_all(over_htmx), (
        "смена пароля на htmx тронула cookie сессии"
    )

    landing = await client.get(RESET_DONE_LANDING)
    assert landing.status_code == 200, f"страница входа ответила {landing.status_code}"
    assert RESET_DONE_TEXT in landing.text, (
        "исход смены пароля не нарисован: код не доехал до человека"
    )
    assert landing.text.index(RESET_DONE_TEXT) < landing.text.index(STEP_ANCHOR), (
        "исход смены пароля рисуется внутри якоря и сотрётся первой ошибкой входа"
    )

    login = await client.post(
        "/login",
        data={"email": email, "password": NEW_PASSWORD},
        follow_redirects=False,
    )
    assert login.status_code == 302 and login.headers.get("location") == "/dashboard", (
        "вход новым паролем не прошёл — пароль молча не сменился"
    )


@pytest.mark.asyncio
async def test_the_last_recovery_steps_are_refused_under_another_identity_on_both_transports(
    admin_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Под чужой личностью подтверждение и новый пароль закрыты на ОБОИХ транспортах (D-13, D-22).

    Токены годные намеренно: отказ обязан стоять ДО их разбора, а не случиться
    потому, что ссылка устарела. Пароль пользователя не меняется.
    """
    from tests.test_pages.test_impersonation import TARGET_EMAIL, _enter, _seed_target

    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    async def _hash() -> str:
        return (
            await db_session.execute(
                select(User.password_hash).where(User.email == TARGET_EMAIL)
            )
        ).scalar_one()

    before = await _hash()
    await _seed_recovery_code(db_session, TARGET_EMAIL)

    for path, payload in (
        (
            "/forgot-password/verify",
            {"token": _reset_token(TARGET_EMAIL, test_settings.secret_key), "code": SEEDED_CODE},
        ),
        (
            "/forgot-password/reset",
            {
                "token": _verified_reset_token(TARGET_EMAIL, test_settings.secret_key),
                "password": NEW_PASSWORD,
            },
        ),
    ):
        bare = await admin_client.post(path, data=payload, follow_redirects=False)
        assert bare.status_code == 403, (
            f"{path} без htmx ответил {bare.status_code} под чужой личностью — "
            "администратор может сменить пароль пользователя"
        )

        over_htmx = await admin_client.post(
            path, data=payload, headers=HTMX_HEADERS, follow_redirects=False
        )
        assert over_htmx.status_code == 204, (
            f"{path} на htmx ответил {over_htmx.status_code} под чужой личностью "
            "вместо 204 — отказ пришёл бы телом в якорь"
        )
        assert over_htmx.headers.get("HX-Location") == IMPERSONATION_REFUSED_LOCATION, (
            f"{path} на htmx ведёт отказ не на домашний экран с кодом отказа"
        )
        assert over_htmx.content == b"", f"{path} на htmx несёт тело отказа"

    assert await _hash() == before, (
        "под чужой личностью пароль пользователя сменился — захват учётной записи"
    )


@pytest.mark.asyncio
async def test_both_recovery_code_forms_ride_the_anchor_and_drop_a_second_request(
    client: AsyncClient,
):
    """Обе формы экрана кода восстановления — макросом в якорь, второй запрос отбрасывается."""
    email = "reset-two-forms@test.com"
    await _register(client, email)
    client.cookies.clear()
    page = await client.post(
        "/forgot-password/send-code", data={"email": email}, follow_redirects=False
    )
    assert page.status_code == 200, f"шаг адреса ответил {page.status_code}"

    for action in ("/forgot-password/verify", "/forgot-password/resend-code"):
        found = re.search(rf'<form[^>]*action="{action}"[^>]*>', page.text)
        assert found is not None, f"на экране кода нет формы {action}"
        tag = found.group(0)
        assert f'hx-post="{action}"' in tag, f"форма {action} рождена не макросом-обёрткой"
        assert STEP_TARGET in tag, f"форма {action} целится не в якорь шага"
        assert 'hx-swap="innerHTML"' in tag, f"форма {action} подменяет не СОДЕРЖИМОЕ якоря"
        assert 'hx-sync="closest #auth-step:drop"' in tag, (
            f"форма {action} не отбрасывает второй запрос, пока летит первый"
        )


@pytest.mark.asyncio
async def test_the_shell_leaves_the_subtitle_to_every_screen(client: AsyncClient):
    """Шелл без переходного блока подзаголовка: его печатает каждый экран сам (D-06).

    Реестр экранов обязан накрывать ровно все страницы второго шелла: иначе
    правило «ни одна страница блок не объявляет» было бы зелено вакуумом для
    страницы, которой в реестре нет.
    """
    from app.pages.auth import AUTH_SCREENS

    shell = (TEMPLATES_DIR / "auth_base.html").read_text(encoding="utf-8")
    assert "auth_subtitle" not in shell, (
        "в шелле остался переходный блок подзаголовка — подмена якоря оставит "
        "подзаголовок прошлого шага"
    )
    pages = sorted((TEMPLATES_DIR / "auth").glob("*.html"))
    assert len(pages) == 7, f"страниц второго шелла {len(pages)}, а экранов семь"
    for page in pages:
        assert "auth_subtitle" not in page.read_text(encoding="utf-8"), (
            f"страница {page.name} объявляет переходный блок подзаголовка"
        )
    assert len(AUTH_SCREENS) == 7, f"в реестре экранов {len(AUTH_SCREENS)} записей, а не семь"
    assert {screen.page for screen in AUTH_SCREENS.values()} == {
        f"auth/{page.name}" for page in pages
    }, "реестр экранов не накрывает ровно все страницы второго шелла"

    for path in ("/login", "/register", "/forgot-password"):
        response = await client.get(path)
        assert response.status_code == 200, f"{path} ответил {response.status_code}"
        assert response.text.count('class="auth-subtitle"') == 1, (
            f"на {path} не ровно один подзаголовок"
        )
        subtitles = SUBTITLE.findall(response.text)
        assert len(subtitles) == 1 and subtitles[0].strip(), (
            f"подзаголовок {path} пуст — его печатает не экран"
        )

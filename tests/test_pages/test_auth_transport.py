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
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.models.user import User
from app.pages.auth import BLOCKED_LOGIN_ERROR

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

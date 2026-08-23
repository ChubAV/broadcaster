"""Вход администратора ПОД ПОЛЬЗОВАТЕЛЕМ и возврат (ADMIN-06, критерий 3).

ЗАЧЕМ ОДИН ФАЙЛ НА ВЕСЬ ПРЕДМЕТ. Имперсонация — единственная операция продукта,
в которой действия одного человека выглядят как действия другого, и её механика
размазана по четырём слоям: токен, обе проверки прав, страничный путь и шелл.
Разложенная по файлам этих слоёв, она проверялась бы по одному слою за раз, и
каждый следующий план заново узнавал бы, что «вход под пользователем вроде
есть». Здесь утверждения читаются подряд, и пропуск любого виден глазом.

⚠️ САМОЕ ДОРОГОЕ УТВЕРЖДЕНИЕ ФАЙЛА — «АДМИН-ДОСТУП НЕ ТЕРЯЕТСЯ» (D-20). Сегодня
админство есть совпадение адреса пользователя с настройкой, и под чужой учётной
записью оно исчезло бы: администратор, вошедший под пользователем, оказался бы
заперт в чужой учётке без пути назад. Инвариант утверждает ОБЕ половины правила
в одном теле — и краснеет в тот день, когда будущая правка вернёт чтение прав по
субъекту.

⚠️ ЧЕГО ЗДЕСЬ НЕТ. Машинный гейт запретов под чужой личностью (D-22, D-23 —
оплата, смена пароля, отправка рассылки) закрывается ПЛАНОМ 06-13, а не здесь.
До его исполнения вход под пользователем на бой не выкатывается; порядок записан
в сводке плана 06-12.
"""
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from jose import jwt
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth_service import IMPERSONATION_EXPIRE_MINUTES, decode_access_token

PASSWORD = "testpass123"

TARGET_EMAIL = "target@test.com"
TARGET_NAME = "Целевой Пользователь"


async def _register(client: AsyncClient, email: str, name: str = "U") -> None:
    """Регистрация прикладным входом — вместе с пробным сроком.

    Не ORM: без строки подписки соседний гейт доступа отказал бы 402 раньше
    всего, что здесь проверяется, и тест краснел бы по ЧУЖОЙ причине.
    """
    response = await client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "name": name},
    )
    assert response.status_code == 201, (
        f"регистрация не прошла ({response.status_code}) — тест имперсонации "
        "красил бы чужую поломку"
    )


async def _user(db_session: AsyncSession, email: str) -> User:
    return (
        await db_session.execute(select(User).where(User.email == email))
    ).scalar_one()


async def _seed_target(client: AsyncClient, db_session: AsyncSession) -> int:
    await _register(client, TARGET_EMAIL, TARGET_NAME)
    return (await _user(db_session, TARGET_EMAIL)).id


async def _impersonate(client: AsyncClient, user_id: int, **kwargs):
    return await client.post(
        f"/admin/users/{user_id}/impersonate", follow_redirects=False, **kwargs
    )


async def _enter(client: AsyncClient, user_id: int):
    """Вход под пользователем, УДОСТОВЕРИВШИЙСЯ, что он состоялся.

    Утверждения ниже про «под чужой личностью» ложны, если вход не сработал:
    администратор остался бы собой, и тест зеленел бы, ничего не проверяя.
    Отсутствующий маршрут отвечает 404, и без этой проверки он выглядел бы как
    успешно исполненное требование.
    """
    response = await _impersonate(client, user_id)
    assert response.status_code == 302 and response.headers["location"] == "/dashboard", (
        f"вход под пользователем не состоялся ({response.status_code}) — "
        "утверждение ниже проверяло бы обычную админскую сессию"
    )
    assert _act_of(response) is not None, (
        "выданный токен не несёт признака действующего лица — под чужой "
        "личностью администратор не оказался"
    )
    return response


async def _stop(client: AsyncClient, **kwargs):
    return await client.post(
        "/impersonation/stop", follow_redirects=False, **kwargs
    )


def _session_cookies(response) -> set[str]:
    """Имена cookie, выставленных ответом."""
    return {
        raw.split("=", 1)[0].strip()
        for raw in response.headers.get_list("set-cookie")
    }


def _cookie_attrs(response) -> frozenset[str]:
    """НАБОР АТРИБУТОВ cookie сессии — без её значения.

    Значение у каждого токена своё; предмет сравнения — набор атрибутов, по
    которому браузер сопоставляет установку с перезаписью (план 06-02,
    Pitfall 9). Разошедшийся набор означает вторую cookie рядом с первой, а не
    перезапись.
    """
    for raw in response.headers.get_list("set-cookie"):
        name, _, rest = raw.partition("=")
        if name.strip() != "access_token":
            continue
        _value, _, attributes = rest.partition(";")
        return frozenset(
            part.strip().lower() for part in attributes.split(";") if part.strip()
        )
    return frozenset()


def _act_of(response) -> int | None:
    """Признак действующего лица в токене, который ответ положил в cookie."""
    from app.services.auth_service import actor_id

    for raw in response.headers.get_list("set-cookie"):
        name, _, rest = raw.partition("=")
        if name.strip() != "access_token":
            continue
        token = rest.partition(";")[0]
        return actor_id(decode_access_token(token, "test-secret-key"))
    return None


# =============================================================================
# Вход под пользователем
# =============================================================================


@pytest.mark.asyncio
async def test_the_admin_enters_as_the_user_from_the_card(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 1: после входа продукт показывает ИМЕННО этого пользователя.

    Утверждение снимается с ПРОДУКТОВОЙ страницы, а не с админской: смысл входа
    — увидеть продукт глазами пользователя, и админская страница этого не
    доказывает.
    """
    target_id = await _seed_target(admin_client, db_session)

    entry = await _impersonate(admin_client, target_id)

    assert entry.status_code == 302, (
        f"вход под пользователем ответил {entry.status_code}"
    )
    assert entry.headers["location"] == "/dashboard", (
        "вход под пользователем не привёл в продукт — администратор остался в "
        "админке и не увидел того, ради чего входил"
    )

    page = await admin_client.get("/dashboard")

    assert page.status_code == 200
    assert f'<span class="user-name">{TARGET_NAME}</span>' in page.text, (
        "продукт показывает не того пользователя, под которым вошли"
    )


@pytest.mark.asyncio
async def test_the_impersonation_token_carries_the_short_lifetime(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Срок выданного токена — короткий срок имперсонации, а не обычный (D-25).

    Проверяется на ВЫДАННОМ токене, а не на константе: константа проверена в
    `tests/test_services/test_auth_token.py`, а здесь предмет — доехала ли она
    до обработчика. Обработчик, забывший её передать, выдал бы чужую учётную
    запись на сутки.
    """
    target_id = await _seed_target(admin_client, db_session)

    entry = await _impersonate(admin_client, target_id)

    raw = next(
        value
        for value in entry.headers.get_list("set-cookie")
        if value.startswith("access_token=")
    )
    token = raw.partition("=")[2].partition(";")[0]
    payload = decode_access_token(token, "test-secret-key")

    assert payload is not None
    lifetime = datetime.fromtimestamp(payload["exp"], tz=timezone.utc) - datetime.now(
        timezone.utc
    )
    assert lifetime <= timedelta(minutes=IMPERSONATION_EXPIRE_MINUTES), (
        "токен имперсонации живёт дольше объявленного короткого срока — "
        "забытая открытой чужая учётная запись переживёт рабочий день (D-25)"
    )


@pytest.mark.asyncio
async def test_admin_access_survives_under_the_other_identity(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 2 (критерий 3): под чужой учётной записью админ-доступ сохраняется.

    Без этого администратор оказался бы заперт в чужой учётной записи: путь
    назад лежит через админку, а админка была бы ему закрыта.
    """
    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    for route in ("/admin", "/admin/users", f"/admin/users/{target_id}"):
        response = await admin_client.get(route)
        assert response.status_code == 200, (
            f"{route} ответил {response.status_code} под чужой учётной записью "
            "— админ-доступ потерян (D-20, критерий 3)"
        )


@pytest.mark.asyncio
async def test_admin_ness_is_decided_by_the_actor_and_otherwise_by_the_subject(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 5 (ИНВАРИАНТ): обе половины правила — в одном теле.

    Для токена С признаком действующего лица админство определяется по
    ДЕЙСТВУЮЩЕМУ ЛИЦУ; для токена БЕЗ признака — по субъекту. Две половины
    стоят рядом намеренно: разложенные по разным тестам, они позволили бы
    «починить» одну, не заметив, что вторая перестала что-либо утверждать.

    Признак админства снимается со ССЫЛКИ НА АДМИНКУ в шелле — то есть с той
    самой страничной проверки прав, а не с админского маршрута: под чужой
    личностью администратор обязан видеть путь назад на продуктовой странице.
    """
    target_id = await _seed_target(admin_client, db_session)

    # Половина первая: действующее лицо есть — админство по нему.
    await _enter(admin_client, target_id)
    impersonated = await admin_client.get("/profile")

    assert 'href="/admin"' in impersonated.text, (
        "под чужой учётной записью админство определилось по СУБЪЕКТУ — "
        "администратор потерял права вместе с личностью (D-20)"
    )

    # Половина вторая: действующего лица нет — админство по субъекту.
    await admin_client.post(
        "/login",
        data={"email": TARGET_EMAIL, "password": PASSWORD},
        follow_redirects=False,
    )
    ordinary = await admin_client.get("/profile")

    assert 'href="/admin"' not in ordinary.text, (
        "обычный пользователь получил админский пункт меню — админство "
        "перестало определяться по субъекту при отсутствии признака (D-21)"
    )


# =============================================================================
# Возврат
# =============================================================================


@pytest.mark.asyncio
async def test_the_return_rewrites_the_cookie_with_the_same_attribute_set(
    admin_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Тест 3: возврат ПЕРЕЗАПИСЫВАЕТ cookie тем же набором атрибутов.

    ⚠️ ПЕРЕЗАПИСЬ, А НЕ УДАЛЕНИЕ (Pitfall 9). Удаление выставляет удаляющую
    cookie со СВОИМ набором атрибутов, и стоит установке получить признак
    транспортной защиты, а удалению — нет, браузер их не сопоставит: старая
    cookie переживёт возврат, то есть администратор останется под чужой
    личностью, будучи уверен, что вышел.
    """
    target_id = await _seed_target(admin_client, db_session)

    ordinary_login = await admin_client.post(
        "/login",
        data={"email": test_settings.admin_email, "password": PASSWORD},
        follow_redirects=False,
    )
    login_attrs = _cookie_attrs(ordinary_login)

    await _enter(admin_client, target_id)
    back = await _stop(admin_client)

    assert back.status_code == 302
    assert _cookie_attrs(back) == login_attrs, (
        "набор атрибутов cookie при возврате разошёлся с набором при обычном "
        "входе — это вторая cookie рядом с первой, а не перезапись"
    )
    assert _act_of(back) is None, (
        "возвращённый токен по-прежнему несёт признак действующего лица"
    )

    admin_page = await admin_client.get("/admin")
    assert admin_page.status_code == 200, "после возврата админка закрылась"

    dashboard = await admin_client.get("/dashboard")
    assert f'<span class="user-name">{TARGET_NAME}</span>' not in dashboard.text, (
        "после возврата продукт по-прежнему показывает чужую учётную запись"
    )


@pytest.mark.asyncio
async def test_an_outsider_can_neither_enter_as_anyone_nor_return(
    client: AsyncClient, db_session: AsyncSession
):
    """Тест 4: посторонний не входит под другим и не выполняет возврат.

    Возврат посторонним — не безобидная кнопка: обработчик выпускает токен на
    ДЕЙСТВУЮЩЕЕ ЛИЦО, и обработчик, не спросивший, есть ли оно, выдал бы токен
    на того, кого назвали снаружи.
    """
    target_id = await _seed_target(client, db_session)
    await _register(client, "outsider@test.com")
    await client.post(
        "/login",
        data={"email": "outsider@test.com", "password": PASSWORD},
        follow_redirects=False,
    )

    entry = await _impersonate(client, target_id)
    assert entry.status_code in (302, 403), entry.status_code
    assert "access_token" not in _session_cookies(entry), (
        "посторонний получил токен имперсонации"
    )

    back = await _stop(client)
    assert "access_token" not in _session_cookies(back), (
        "возврат выдал токен тому, у кого не было действующего лица"
    )

    still_outside = await client.get("/admin")
    assert still_outside.status_code == 403, (
        "посторонний получил админ-доступ через путь возврата"
    )


@pytest.mark.asyncio
async def test_both_the_entry_and_the_return_are_journaled_with_both_ids(
    admin_client: AsyncClient, db_session: AsyncSession, test_settings, caplog
):
    """Тест 6 (D-24): обе операции оставляют именованный след с ОБОИМИ ид.

    Это единственная операция продукта, в которой действия одного человека
    выглядят как действия другого. Без строки с обоими идентификаторами
    разобрать потом, кто это сделал, нечем: запись «пользователь X отправил
    рассылку» не отличима от той же записи, сделанной администратором за него.

    Запись снимается `caplog`-ом, а не `capture_logs()`: ленивый прокси
    structlog связывается с цепочкой процессоров при первом использовании и
    кэширует её (основание выписано в `tests/test_admin.py`).
    """
    target_id = await _seed_target(admin_client, db_session)
    admin_id = (await _user(db_session, test_settings.admin_email)).id

    with caplog.at_level("INFO", logger="app.pages.admin"):
        await _impersonate(admin_client, target_id)
    with caplog.at_level("INFO", logger="app.pages.auth"):
        await _stop(admin_client)

    events = {
        record.msg["event"]: record.msg
        for record in caplog.records
        if isinstance(record.msg, dict) and "event" in record.msg
    }

    for name in ("impersonation_start", "impersonation_stop"):
        assert name in events, (
            f"строки журнала `{name}` нет: {sorted(events)}"
        )
        assert events[name].get("admin_user_id") == admin_id, (
            f"`{name}` не назвал администратора"
        )
        assert events[name].get("target_user_id") == target_id, (
            f"`{name}` не назвал целевого пользователя"
        )


# =============================================================================
# Границы входа
# =============================================================================


@pytest.mark.asyncio
async def test_the_admin_may_enter_as_a_blocked_user(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 7 (D-26): вход под ЗАБЛОКИРОВАННЫМ пользователем РАЗРЕШЁН.

    ⚠️ ЭТО НЕ ПОСЛАБЛЕНИЕ, А ТОТ САМЫЙ СЛУЧАЙ, РАДИ КОТОРОГО ВХОД И НУЖЕН:
    «за что меня заблокировали» — типовой вопрос поддержки, и ответить на него
    можно, только увидев продукт глазами заблокированного.

    ⚠️ УТВЕРЖДЕНИЕ ИДЁТ СТРАНИЧНЫМ ПУТЁМ, И ЭТО ПРЕДМЕТ. Ветку `act` на
    JSON-стороне написал план 06-06, а страничный путь он трогать не имел права
    — стык был записан в `deferred-items.md` и закрывается здесь. Пока ветки
    здесь не было, администратор, вошедший под заблокированным, был неотличим
    от невошедшего: молчаливый редирект на вход без единого слова о причине.
    """
    target_id = await _seed_target(admin_client, db_session)
    target = await _user(db_session, TARGET_EMAIL)
    target.is_blocked = True
    await db_session.commit()

    await _enter(admin_client, target_id)
    page = await admin_client.get("/dashboard", follow_redirects=False)

    assert page.status_code == 200, (
        f"страница ответила {page.status_code} под заблокированным "
        "пользователем — блокировка применилась к субъекту при наличии "
        "действующего лица (D-26)"
    )
    assert f'<span class="user-name">{TARGET_NAME}</span>' in page.text


@pytest.mark.asyncio
async def test_the_page_purchase_form_stays_closed_to_a_blocked_user(
    client: AsyncClient, db_session: AsyncSession
):
    """ГРАНИЦА СНИЗУ у правки выше: без действующего лица блокировка ДЕЙСТВУЕТ.

    ⚠️ ЗАКРЫТОСТЬ ЭТОЙ ФОРМЫ СЕГОДНЯ — ПОБОЧНЫЙ ЭФФЕКТ `get_user_from_cookie`,
    и до этого теста она не была закреплена НИЧЕМ (находка плана 06-06,
    `deferred-items.md`). Ветка `act`, добавленная в ту же функцию, могла
    открыть форму молча — то есть заблокированный человек снова смог бы
    платить за продукт, которым ему пользоваться нельзя.
    """
    await _register(client, "blocked@test.com")
    blocked = await _user(db_session, "blocked@test.com")
    blocked.is_blocked = True
    await db_session.commit()

    await client.post(
        "/login",
        data={"email": "blocked@test.com", "password": PASSWORD},
        follow_redirects=False,
    )

    page = await client.get("/billing", follow_redirects=False)
    purchase = await client.post("/billing/subscribe", follow_redirects=False)

    assert page.status_code == 302 and page.headers["location"] == "/login", (
        "заблокированному открылась страница с формой покупки"
    )
    assert purchase.status_code == 302 and purchase.headers["location"] == "/login", (
        "заблокированный дошёл до создания платежа"
    )


@pytest.mark.asyncio
async def test_a_cross_origin_entry_is_refused_before_any_token_is_issued(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 8: гард происхождения стоит ДО выпуска токена.

    Аутентификация проекта идёт cookie, поэтому браузер прикладывает её к
    межсайтовой форме сам: без гарда сторонняя страница выписала бы себе токен
    имперсонации от имени вошедшего администратора.
    """
    target_id = await _seed_target(admin_client, db_session)

    entry = await _impersonate(
        admin_client, target_id, headers={"sec-fetch-site": "cross-site"}
    )

    assert entry.status_code == 403, (
        f"межсайтовый вход под пользователем ответил {entry.status_code}"
    )
    assert "access_token" not in _session_cookies(entry), (
        "токен имперсонации выпущен раньше гарда происхождения"
    )


@pytest.mark.asyncio
async def test_entering_as_a_missing_user_is_refused(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 9: вход под несуществующим пользователем не выпускает токена."""
    entry = await _impersonate(admin_client, 999_999)

    assert entry.status_code == 302
    assert "access_token" not in _session_cookies(entry), (
        "выпущен токен на идентификатор, которому не соответствует строка в базе"
    )


@pytest.mark.asyncio
async def test_entering_as_oneself_is_refused_and_issues_no_actor_claim(
    admin_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Тест 10: вход администратора ПОД САМИМ СОБОЙ отвергается ЯВНО.

    Поведение выбрано, а не оставлено неопределённым: токен, где действующее
    лицо совпадает с субъектом, — это состояние, которого в продукте не бывает,
    и первый же читатель признака истолковал бы его по-своему. Отказ здесь
    ничего не отнимает: администратор и так находится в своей учётной записи.
    """
    admin_id = (await _user(db_session, test_settings.admin_email)).id

    entry = await _impersonate(admin_client, admin_id)

    assert entry.status_code == 302
    assert "access_token" not in _session_cookies(entry), (
        "выпущен токен, в котором действующее лицо совпадает с субъектом"
    )

    admin_page = await admin_client.get("/admin")
    assert admin_page.status_code == 200, "отказ отнял у администратора его права"


@pytest.mark.asyncio
async def test_no_second_identity_cookie_appears(
    admin_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Тест 11: второго носителя личности не заводится.

    Две независимо валидных cookie рассинхронизируются, и возврат ломается при
    потере одной. Подпись ОДНОГО токена покрывает саму СВЯЗЬ
    администратор→пользователь, а не два отдельных факта.
    """
    target_id = await _seed_target(admin_client, db_session)

    ordinary_login = await admin_client.post(
        "/login",
        data={"email": test_settings.admin_email, "password": PASSWORD},
        follow_redirects=False,
    )
    entry = await _impersonate(admin_client, target_id)
    back = await _stop(admin_client)

    assert _session_cookies(entry) == _session_cookies(ordinary_login), (
        f"вход под пользователем завёл вторую cookie личности: "
        f"{_session_cookies(entry)}"
    )
    assert _session_cookies(back) == _session_cookies(ordinary_login), (
        f"возврат завёл вторую cookie личности: {_session_cookies(back)}"
    )


@pytest.mark.asyncio
async def test_a_hand_built_token_with_a_scalar_actor_claim_still_reads(
    admin_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Токены плана 06-06 со СКАЛЯРНЫМ признаком продолжают читаться.

    План 06-06 закрепил ветку D-26 на вручную собранном токене со скалярным
    признаком — до того, как выпуск таких токенов появился. Выпуск пишет
    объектную форму стандарта делегирования; чтение обязано остаться терпимым к
    скаляру, иначе правка формы молча обесценила бы чужое утверждение.
    """
    target_id = await _seed_target(admin_client, db_session)
    admin_id = (await _user(db_session, test_settings.admin_email)).id

    token = jwt.encode(
        {
            "sub": str(target_id),
            "act": str(admin_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        },
        test_settings.secret_key,
        algorithm="HS256",
    )
    payload = decode_access_token(token, test_settings.secret_key)

    from app.services.auth_service import actor_id

    assert actor_id(payload) == admin_id, (
        "скалярная форма признака перестала читаться — утверждение плана 06-06 "
        "обесценилось молча"
    )


# =============================================================================
# Полоса возврата в шелле — видна на КАЖДОЙ странице продукта (D-25, S8)
# =============================================================================
#
# ⚠️ ЭТО ИЗМЕНЕНИЕ УРОВНЯ ШЕЛЛА, А НЕ РАЗДЕЛА. Полоса рисуется на всех 26
# страничных маршрутах, и обход НЕСКОЛЬКИХ РАЗНЫХ разделов здесь не
# перестраховка: в макете полоса живёт внутри админского блока, и самая
# правдоподобная ошибка исполнения — поставить её туда же. Такая полоса прошла
# бы проверку на одной странице и молчала бы ровно там, где нужна: у
# администратора, ушедшего под чужой личностью в «Объявления».

# Разные РАЗДЕЛЫ продукта, а не разные адреса одного раздела.
SECTIONS = ("/dashboard", "/ads", "/accounts", "/schedules", "/billing", "/profile")

RETURN_FORM = '<form method="post" action="/impersonation/stop"'


@pytest.mark.asyncio
async def test_the_return_bar_is_present_in_every_section(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 1: под чужой личностью полоса есть в РАЗМЕТКЕ ЛЮБОЙ страницы.

    Обход идёт по шести разным разделам. Полоса, поставленная в админский блок
    вместо шелла, зеленела бы на админской странице и молчала бы во всех
    остальных — то есть ровно там, где администратор о чужой личности и
    забывает.
    """
    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    for route in SECTIONS:
        response = await admin_client.get(route)
        assert response.status_code == 200, f"{route} ответил {response.status_code}"
        assert "data-impersonation" in response.text, (
            f"{route}: полосы возврата нет — администратор не видит, что "
            "находится под чужой личностью (D-25)"
        )


@pytest.mark.asyncio
async def test_without_impersonation_no_section_draws_the_bar(
    authed_client: AsyncClient
):
    """Тест 2: нет признака — НЕТ РАЗМЕТКИ ВОВСЕ.

    Умолчание «показать» запрещено прямо: ложная полоса «вы работаете от имени»
    на 26 страницах хуже её отсутствия — она сообщает человеку, что его
    действия уходят от чужого имени, когда это неправда.
    """
    for route in SECTIONS:
        response = await authed_client.get(route)
        assert response.status_code == 200, route
        assert "data-impersonation" not in response.text, (
            f"{route}: полоса возврата нарисована пользователю, который ни под "
            "кем не находится"
        )
        assert RETURN_FORM not in response.text, route


@pytest.mark.asyncio
async def test_the_bar_names_the_user_the_admin_is_acting_as(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 3: полоса НАЗЫВАЕТ, под кем находится администратор.

    Полоса без имени отвечает «вы под кем-то» — то есть на вопрос, которого
    никто не задавал. У администратора в разборе обычно открыто несколько
    учётных записей подряд, и «под кем именно» — единственное, что полоса
    сообщает сверх самого факта.
    """
    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    html = (await admin_client.get("/dashboard")).text

    assert f"Вы работаете от имени пользователя {TARGET_NAME}" in html, (
        "полоса не называет, под кем находится администратор"
    )


@pytest.mark.asyncio
async def test_a_user_without_a_name_is_named_by_address_never_by_emptiness(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """У пользователя может не быть имени — тогда печатается АДРЕС.

    «Вы работаете от имени пользователя » — подпись, не называющая никого.
    Адрес есть у каждого, и он отвечает на тот же вопрос.
    """
    await _register(admin_client, "nameless@test.com", "")
    nameless = await _user(db_session, "nameless@test.com")
    nameless.name = None
    await db_session.commit()
    await _enter(admin_client, nameless.id)

    html = (await admin_client.get("/dashboard")).text

    assert "Вы работаете от имени пользователя nameless@test.com" in html, (
        "подпись полосы осталась без имени и без адреса"
    )


@pytest.mark.asyncio
async def test_an_arbitrarily_long_name_does_not_stretch_the_bar(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Имя — ПРОИЗВОЛЬНЫЙ ВВОД, а полоса рисуется на 26 маршрутах.

    Имя в двести знаков растянуло бы полосу на несколько строк над КАЖДЫМ
    экраном продукта. Усечение стоит в обработчике, а не в разметке: величина,
    обрезанная в шаблоне, обрезалась бы по-разному в каждом месте показа.
    """
    from app.pages.common import IMPERSONATION_LABEL_CAP

    long_name = "Пользователь " + "Ы" * 300
    await _register(admin_client, "long@test.com", long_name)
    long_user = await _user(db_session, "long@test.com")
    await _enter(admin_client, long_user.id)

    html = (await admin_client.get("/dashboard")).text

    assert long_name not in html, (
        "имя произвольной длины уехало в полосу целиком — полоса растянется "
        "над каждым экраном продукта"
    )
    printed = html.split("Вы работаете от имени пользователя ", 1)[1].split("<", 1)[0]
    assert len(printed.strip()) <= IMPERSONATION_LABEL_CAP, (
        f"подпись длиннее объявленного потолка: {len(printed.strip())}"
    )


@pytest.mark.asyncio
async def test_the_return_control_is_a_real_post_form(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 4: возврат — НАСТОЯЩАЯ форма POST, а не ссылка и не обработчик.

    Возврат меняет состояние: он перевыпускает токен и переписывает cookie.
    Переход по ссылке для такого действия неверен, а кнопка, работающая только
    при поднявшемся Alpine, оставила бы администратора запертым в чужой учётной
    записи ровно тогда, когда что-то пошло не так.
    """
    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    html = (await admin_client.get("/dashboard")).text

    assert RETURN_FORM in html, (
        "возврат сделан не формой POST — на странице без работающего JS пути "
        "назад не остаётся"
    )
    assert 'href="/impersonation/stop"' not in html, (
        "возврат сделан ссылкой: изменяющее состояние действие по GET"
    )
    assert "ВЕРНУТЬСЯ В АДМИНА" in html, "подписи возврата в полосе нет"


@pytest.mark.asyncio
async def test_the_bar_does_not_break_the_shell_layout(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 5: полоса не ломает раскладку шелла ни в одном разделе.

    Полоса встаёт в КАЖДУЮ страницу проекта, и ошибка вёрстки здесь видна всем
    сразу. Утверждение снимается с тех же признаков, которыми обход шелла
    проверяет целость раскладки.
    """
    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    for route in SECTIONS:
        html = (await admin_client.get(route)).text
        for marker in ("data-shell", "data-side", "data-nav", "data-tabs", "data-main"):
            assert marker in html, f"{route}: раскладка шелла потеряла {marker}"


@pytest.mark.asyncio
async def test_the_bar_costs_the_shell_no_query_of_its_own(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 6: признак имперсонации не стоит НИ ОДНОГО лишнего запроса.

    ⚠️ УТВЕРЖДЕНИЕ СТРУКТУРНОЕ, А НЕ О НАМЕРЕНИИ: у сборщика признака нет
    сессии БД в параметрах, поэтому обратиться к базе ему НЕЧЕМ. Полоса
    рисуется на каждом из 26 маршрутов, и запрос ради неё оплачивался бы на
    каждом рендере продукта.

    Второе чтение строки пользователей при имперсонации ЕСТЬ, и оно названо: это
    само действующее лицо, и нужно оно ПРОВЕРКЕ ПРАВ, а не полосе — админство
    есть совпадение АДРЕСА с настройкой, а адрес берётся только из строки.
    Третьего чтения полоса не добавляет.
    """
    import inspect

    from app.pages.common import impersonation_view

    assert "db" not in inspect.signature(impersonation_view).parameters, (
        "сборщик признака имперсонации получил сессию БД — полоса стала стоить "
        "запрос на каждом из 26 рендеров"
    )

    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    statements: list[str] = []

    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    bind = db_session.get_bind()
    engine = getattr(bind, "sync_engine", bind)
    event.listen(engine, "before_cursor_execute", record)
    try:
        response = await admin_client.get("/profile")
    finally:
        event.remove(engine, "before_cursor_execute", record)

    assert response.status_code == 200
    user_reads = [s for s in statements if "FROM users" in s]
    assert len(user_reads) == 2, (
        "чтений строки пользователей на рендере под чужой личностью не два "
        f"(субъект и действующее лицо), а {len(user_reads)}:\n"
        + "\n".join(user_reads)
    )

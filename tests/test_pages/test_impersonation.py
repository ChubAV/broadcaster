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
    admin_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Тест 6 (D-24): обе операции оставляют именованный след с ОБОИМИ ид.

    Это единственная операция продукта, в которой действия одного человека
    выглядят как действия другого. Без строки с обоими идентификаторами
    разобрать потом, кто это сделал, нечем: запись «пользователь X отправил
    рассылку» не отличима от той же записи, сделанной администратором за него.

    ⚠️ УТВЕРЖДЕНИЕ СНИМАЕТСЯ С САМОГО ВЫЗОВА ЖУРНАЛА, А НЕ С `caplog`, И ЭТО
    ВЫНУЖДЕННЫЙ ВЫБОР, А НЕ ПРЕДПОЧТЕНИЕ. Первая редакция теста снимала запись
    `caplog`-ом по образцу соседей и краснела ТОЛЬКО в полном прогоне: в наборе
    `test_admin.py … test_models` + этот файл (516 тестов, 70 секунд) запись
    `app.pages.admin` не доезжает до перехватчика, тогда как запись
    `app.pages.auth` в том же теле доезжает. Причина лежит в конфигурации
    журналирования, общей на процесс: `setup_logging` вызывается на КАЖДОЙ
    сборке приложения и чистит обработчики корневого регистратора
    (`app/logging_config.py`), а `tests/test_messengers/conftest.py`
    переконфигурирует structlog на старте сессии. Разведение этих двух — правка
    общей поверхности журналирования, то есть чужой предмет.

    Проверка через подмену самого регистратора от порядка файлов не зависит и
    утверждает ровно то, что требует D-24: ИМЯ события и ОБА идентификатора в
    нём. Чего она не утверждает — что запись доехала до вывода; это свойство
    общей настройки журналирования, и его проверяют тесты самой настройки.
    """
    from unittest.mock import MagicMock, patch

    import app.pages.admin as admin_module
    import app.pages.auth as auth_module

    target_id = await _seed_target(admin_client, db_session)
    admin_id = (await _user(db_session, test_settings.admin_email)).id

    entry_logger = MagicMock()
    with patch.object(admin_module, "logger", entry_logger):
        await _impersonate(admin_client, target_id)

    stop_logger = MagicMock()
    with patch.object(auth_module, "logger", stop_logger):
        await _stop(admin_client)

    def _event(mock, name: str) -> dict:
        for call in mock.info.call_args_list:
            if call.args and call.args[0] == name:
                return call.kwargs
        raise AssertionError(
            f"строки журнала `{name}` нет: "
            f"{[c.args[0] for c in mock.info.call_args_list if c.args]}"
        )

    for mock, name in ((entry_logger, "impersonation_start"), (stop_logger, "impersonation_stop")):
        fields = _event(mock, name)
        assert fields.get("admin_user_id") == admin_id, (
            f"`{name}` не назвал администратора: {fields}"
        )
        assert fields.get("target_user_id") == target_id, (
            f"`{name}` не назвал целевого пользователя: {fields}"
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
    # Колонка имени объявлена обязательной, поэтому «имени нет» в этой схеме
    # выражается ПУСТОЙ строкой, а не отсутствием значения. Подпись обязана
    # видеть в ней то же самое, что увидела бы в отсутствии.
    nameless.name = "   "
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

    # Предмет — ПОЛОСА, а не блок пользователя в сайдбаре: тот печатает имя
    # целиком и делал это до этого плана. Утверждение «имени нет нигде в
    # разметке» краснело бы на чужой, не этим планом заведённой поверхности.
    bar = html.split("data-impersonation", 1)[1].split("</div>", 1)[0]

    assert long_name not in bar, (
        "имя произвольной длины уехало в полосу целиком — полоса растянется "
        "над каждым экраном продукта"
    )
    printed = bar.split("Вы работаете от имени пользователя ", 1)[1].split("<", 1)[0]
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
    admin_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Тест 6: признак имперсонации не стоит НИ ОДНОГО запроса.

    ⚠️ ПЕРВОЕ УТВЕРЖДЕНИЕ СТРУКТУРНОЕ, А НЕ О НАМЕРЕНИИ: у сборщика признака нет
    сессии БД в параметрах, поэтому обратиться к базе ему НЕЧЕМ. Полоса рисуется
    на каждом из 26 маршрутов, и запрос ради неё оплачивался бы на каждом
    рендере продукта — в том числе у 100% пользователей, которые под чужой
    личностью не находятся никогда.

    ⚠️ ВТОРОЕ СРАВНИВАЕТ ДВА РЕНДЕРА ОДНОЙ И ТОЙ ЖЕ СТРАНИЦЫ — обычный и
    из-под чужой личности, — и требует, чтобы ВСЯ разница состояла из чтений
    строки пользователей. Это и есть точная формулировка названной цены: при
    имперсонации читается САМО ДЕЙСТВУЮЩЕЕ ЛИЦО, и нужно оно ПРОВЕРКЕ ПРАВ, а не
    полосе (админство есть совпадение АДРЕСА с настройкой, а адрес берётся
    только из строки). Появись из-за полосы хоть один запрос к любой другой
    таблице — разница его покажет.

    Сравнение идёт по ТЕКСТУ запросов, а не по их числу: два рендера сделаны от
    разных людей, и одинаковые по смыслу запросы отличаются только параметрами,
    которых в тексте нет.
    """
    import inspect
    from collections import Counter

    from app.pages.common import impersonation_view

    assert "db" not in inspect.signature(impersonation_view).parameters, (
        "сборщик признака имперсонации получил сессию БД — полоса стала стоить "
        "запрос на каждом из 26 рендеров"
    )

    target_id = await _seed_target(admin_client, db_session)

    async def _statements_of_profile_render() -> list[str]:
        recorded: list[str] = []

        def record(conn, cursor, statement, parameters, context, executemany):
            recorded.append(statement)

        bind = db_session.get_bind()
        engine = getattr(bind, "sync_engine", bind)
        event.listen(engine, "before_cursor_execute", record)
        try:
            response = await admin_client.get("/profile")
        finally:
            event.remove(engine, "before_cursor_execute", record)
        assert response.status_code == 200
        return recorded

    # Обычный рендер — тот же адрес, тот же человек, но без чужой личности.
    await admin_client.post(
        "/login",
        data={"email": TARGET_EMAIL, "password": PASSWORD},
        follow_redirects=False,
    )
    plain = await _statements_of_profile_render()

    # Тот же рендер из-под чужой личности.
    await admin_client.post(
        "/login",
        data={"email": test_settings.admin_email, "password": PASSWORD},
        follow_redirects=False,
    )
    await _enter(admin_client, target_id)
    impersonated = await _statements_of_profile_render()

    extra = Counter(impersonated) - Counter(plain)
    foreign = [s for s in extra.elements() if "FROM users" not in s]

    assert not foreign, (
        "полоса возврата привела с собой запрос помимо чтения строки "
        "действующего лица:\n" + "\n".join(foreign)
    )


# =============================================================================
# Запреты под чужой личностью (D-22, D-23 — план 06-13)
#
# ПОЧЕМУ ЭТИ УТВЕРЖДЕНИЯ ЖИВУТ ЗДЕСЬ, А НЕ В ФАЙЛЕ МАШИННОГО ГЕЙТА. Гейт
# (`test_impersonation_gate.py`) отвечает на вопрос «объявлен ли запрет на
# маршруте» и читает ИСХОДНИК; эти утверждения отвечают на вопрос «отказывает ли
# он на самом деле» и ходят по HTTP. Ни одно из двух не заменяет другое: гейт
# зеленел бы на зависимости, навешенной верно и не срабатывающей, а сквозная
# проверка зеленела бы на маршруте, о существовании которого она не знает.
# =============================================================================


PERMISSION_REFUSAL_DETAIL = "Admin access required"

# Опознавательный обрывок текста отказа под чужой личностью. Утверждения
# «отказ пришёл НЕ от запрета имперсонации» сравнивают именно с ним, а не с
# кодом состояния: код 403 у этих маршрутов есть и по своим причинам.
IMPERSONATION_REFUSAL_MARK = "чужой учётной записью"


def _detail_of(response) -> str:
    """Текст отказа из тела ответа — либо пустая строка."""
    try:
        return str(response.json().get("detail", ""))
    except Exception:
        return ""


async def _seed_account_with_group(db_session: AsyncSession, user_id: int):
    """Аккаунт мессенджера с одной группой у названного пользователя.

    Нужен утверждениям о РАЗРЕШЁННОМ: «синхронизация групп разрешена» и
    «переключение группы разрешено» без предмета проверялись бы на редиректе
    «аккаунта нет», то есть зеленели бы и при наглухо закрытом маршруте.
    """
    from app.models.messenger_account import MessengerAccount
    from tests.conftest import seed_group

    account = MessengerAccount(
        user_id=user_id,
        type="tg_user",
        credentials="{}",
        status="active",
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    account_id = account.id

    group = await seed_group(db_session, account_id, user_id)
    return account_id, group.id


@pytest.mark.asyncio
async def test_the_purchase_form_is_refused_under_another_identity(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Под чужой личностью НЕЛЬЗЯ ЗАПЛАТИТЬ, а без неё тот же вход работает (D-22).

    ⚠️ ВТОРАЯ ПОЛОВИНА УТВЕРЖДЕНИЯ НЕ УКРАШЕНИЕ. Запрет, закрывший денежный вход
    ВСЕМ, прошёл бы первую половину и остановил бы приём денег целиком —
    отличить «закрыто под чужой личностью» от «закрыто вообще» можно только
    вторым запросом.
    """
    target_id = await _seed_target(admin_client, db_session)

    await _enter(admin_client, target_id)
    refused = await admin_client.post("/billing/subscribe", follow_redirects=False)

    assert refused.status_code == 403, (
        f"вход оплаты ответил {refused.status_code} под чужой личностью — "
        "администратор может заплатить деньгами пользователя"
    )
    assert IMPERSONATION_REFUSAL_MARK in _detail_of(refused), (
        f"отказ не назвал причиной чужую личность: {_detail_of(refused)!r}"
    )

    await _stop(admin_client)
    allowed = await admin_client.post("/billing/subscribe", follow_redirects=False)

    assert allowed.status_code != 403, (
        "вход оплаты закрыт и БЕЗ имперсонации — запрет остановил приём денег "
        "вместо того, чтобы закрыть чужую личность"
    )


@pytest.mark.asyncio
async def test_the_password_change_is_refused_under_another_identity(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Под чужой личностью НЕЛЬЗЯ СМЕНИТЬ ПАРОЛЬ, а вход и выход работают (D-22).

    ⚠️ ЗАКРЫТ ВЕСЬ ПУТЬ ВОССТАНОВЛЕНИЯ, А НЕ ТОЛЬКО ПОСЛЕДНИЙ ШАГ. Смена пароля
    — это четыре маршрута подряд, и закрытый только последний оставил бы
    администратору три первых: код ушёл бы на почту пользователя, то есть
    захват учётной записи начался бы и остановился на полпути, с письмом,
    которого пользователь не просил.

    ВХОД И ВЫХОД ПРОВЕРЯЮТСЯ РЯДОМ, ПОТОМУ ЧТО ОНИ ЖИВУТ В ТОМ ЖЕ РОУТЕРЕ.
    Закрыть роутер авторизации целиком нельзя: никто не смог бы войти — и
    утверждение здесь ловит именно эту ошибку навески.
    """
    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    for path, payload in (
        ("/forgot-password/send-code", {"email": TARGET_EMAIL}),
        ("/forgot-password/verify", {"token": "x", "code": "000000"}),
        ("/forgot-password/resend-code", {"token": "x"}),
        ("/forgot-password/reset", {"token": "x", "password": "newpass123"}),
    ):
        response = await admin_client.post(
            path, data=payload, follow_redirects=False
        )
        assert response.status_code == 403, (
            f"{path} ответил {response.status_code} под чужой личностью — "
            "администратор может перехватить пароль пользователя"
        )

    logout = await admin_client.get("/logout", follow_redirects=False)
    assert logout.status_code == 302, (
        "выход закрыт запретом — администратор заперт под чужой личностью"
    )

    login = await admin_client.post(
        "/login",
        data={"email": TARGET_EMAIL, "password": PASSWORD},
        follow_redirects=False,
    )
    assert login.status_code == 302, (
        "вход закрыт запретом — запрет навешен на роутер авторизации целиком, "
        "и войти в продукт больше нельзя никому"
    )


@pytest.mark.asyncio
async def test_the_profile_change_is_refused_under_another_identity(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Под чужой личностью НЕЛЬЗЯ ПРАВИТЬ УЧЁТНЫЕ ДАННЫЕ пользователя (D-22).

    ⚠️ ОТДЕЛЬНОГО МАРШРУТА СМЕНЫ АДРЕСА В ПРОДУКТЕ СЕГОДНЯ НЕТ, и это записано
    здесь, чтобы следующий читатель не счёл утверждение неполным. D-22 называет
    смену адреса запрещённой; носителя у неё пока два — путь восстановления
    пароля по почте (закрыт утверждением выше) и форма профиля, куда поле
    адреса и приедет, когда его заведут. Форма профиля закрыта ЦЕЛИКОМ именно
    поэтому: поле, добавленное в уже разрешённый маршрут, машинный гейт не
    заметил бы — маршрут-то объявлен, — и запрет D-22 обошёлся бы молча.

    Сегодняшнее содержимое формы — часовой пояс, и он тоже не безобиден: им
    определяется, В КАКОЕ ВРЕМЯ уходят рассылки пользователя.
    """
    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    response = await admin_client.post(
        "/profile", data={"timezone": "Europe/Moscow"}, follow_redirects=False
    )

    assert response.status_code == 403, (
        f"форма профиля ответила {response.status_code} под чужой личностью"
    )


@pytest.mark.asyncio
async def test_the_account_deletion_is_refused_under_another_identity(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Под чужой личностью НЕЛЬЗЯ УДАЛИТЬ УЧЁТНУЮ ЗАПИСЬ (D-22).

    ⚠️ УДАЛЕНИЕ ДОСТИЖИМО ИМЕННО ПОД ЧУЖОЙ ЛИЧНОСТЬЮ, И В ЭТОМ ВЕСЬ ВОПРОС.
    Права администратора читаются по ДЕЙСТВУЮЩЕМУ ЛИЦУ (D-20), поэтому админка
    из-под имперсонации открыта — то есть кнопка удаления пользователя доступна
    администратору, находящемуся в чужой учётной записи. Операция необратима:
    откатом кода удалённый пользователь не возвращается.
    """
    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    response = await admin_client.post(
        f"/admin/users/{target_id}/delete", follow_redirects=False
    )

    assert response.status_code == 403, (
        f"удаление пользователя ответило {response.status_code} под чужой "
        "личностью — необратимая операция выполнена от чужого имени"
    )

    db_session.expire_all()
    survivor = await db_session.get(User, target_id)
    assert survivor is not None, (
        "пользователь удалён под чужой личностью — отказ пришёл ПОСЛЕ удаления"
    )


@pytest.mark.asyncio
async def test_the_send_retry_is_refused_but_the_history_reads(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Повтор отправки запрещён, ЧТЕНИЕ истории разрешено (D-22).

    ⚠️ РОВНО ЭТА ПАРА И ДЕЛАЕТ ЧИСТО ПЕР-РОУТЕРНЫЙ ЗАПРЕТ НЕДОСТАТОЧНЫМ.
    Повтор живёт в роутере истории, чтение которого под чужой личностью не
    просто разрешено, а СОСТАВЛЯЕТ СМЫСЛ входа: типовое обращение звучит как
    «не отправляется», и ответ на него виден именно в журнале отправок. Закрыть
    роутер целиком значило бы отнять то, ради чего входили.

    Отправка необратима: сообщение уходит в чужие группы от имени пользователя,
    и отменить его не может ни администратор, ни владелец учётной записи.
    """
    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    refused = await admin_client.post("/history/1/retry", follow_redirects=False)
    assert refused.status_code == 403, (
        f"повтор отправки ответил {refused.status_code} под чужой личностью — "
        "рассылка может уйти в чужие группы от имени пользователя"
    )
    assert IMPERSONATION_REFUSAL_MARK in _detail_of(refused), (
        f"отказ не назвал причиной чужую личность: {_detail_of(refused)!r}"
    )

    read = await admin_client.get("/history", follow_redirects=False)
    assert read.status_code == 200, (
        f"чтение истории ответило {read.status_code} под чужой личностью — "
        "закрыт роутер целиком, и воспроизвести жалобу «не отправляется» нечем"
    )


@pytest.mark.asyncio
async def test_the_group_sync_is_allowed_under_another_identity(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Синхронизация групп под чужой личностью РАЗРЕШЕНА (D-22).

    ⚠️ ЭТО ГРАНИЦА СВЕРХУ, БЕЗ КОТОРОЙ ЗАПРЕТ «НА ВСЁ» ПРОШЁЛ БЫ ВЕСЬ ФАЙЛ.
    Режим «только чтение» отвергнут явно: смысл входа под пользователем — в
    ВОСПРОИЗВЕДЕНИИ проблемы, а типовая проблема продукта звучит как «не
    синхронизируются группы». Запрет, закрывший синхронизацию, отнял бы у входа
    половину его назначения.

    Предмет утверждения — что запрет НЕ СРАБОТАЛ, а не что синхронизация
    удалась: настоящая синхронизация ушла бы в сеть прямо из суиты, и её исход
    к вопросу этого теста отношения не имеет.
    """
    target_id = await _seed_target(admin_client, db_session)
    account_id, _group_id = await _seed_account_with_group(db_session, target_id)
    await _enter(admin_client, target_id)

    response = await admin_client.post(
        f"/accounts/{account_id}/sync-groups", follow_redirects=False
    )

    assert IMPERSONATION_REFUSAL_MARK not in _detail_of(response), (
        "синхронизация групп закрыта под чужой личностью — вход под "
        "пользователем потерял половину своего назначения"
    )


@pytest.mark.asyncio
async def test_the_group_toggle_is_allowed_under_another_identity(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Включение и выключение группы под чужой личностью РАЗРЕШЕНЫ (D-22).

    Вторая граница сверху рядом с синхронизацией. Действие обратимо одним
    нажатием, ничего не отправляет и денег не трогает.

    Проверяется НЕ ТОЛЬКО код ответа, но и СОСТОЯВШИЙСЯ переворот флага: отказ,
    пришедший редиректом, кодом от успеха здесь неотличим.
    """
    from app.models.group import Group

    target_id = await _seed_target(admin_client, db_session)
    account_id, group_id = await _seed_account_with_group(db_session, target_id)
    await _enter(admin_client, target_id)

    response = await admin_client.post(
        f"/accounts/{account_id}/groups/{group_id}/toggle", follow_redirects=False
    )

    assert IMPERSONATION_REFUSAL_MARK not in _detail_of(response), (
        "переключение группы закрыто под чужой личностью — D-22 называет его "
        "разрешённым поимённо"
    )

    db_session.expire_all()
    group = await db_session.get(Group, group_id)
    assert group.is_active is False, (
        "переключение не состоялось: отказ пришёл молча, кодом успеха"
    )


@pytest.mark.asyncio
async def test_a_nested_impersonation_is_refused(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Находясь под чужой личностью, войти ещё под кем-то НЕЛЬЗЯ.

    ⚠️ ЦЕПОЧКУ ЛИЧНОСТЕЙ ФОРМАТ ТОКЕНА ДОПУСКАЕТ, А ПРОДУКТ НЕ ПОДДЕРЖИВАЕТ.
    Разрешить её молча значило бы завести состояние, о котором не думал никто:
    полоса возврата назвала бы одного пользователя, возврат привёл бы к
    другому, а журнал записал бы пару, которой не было. Отказ ничего не
    отнимает — администратор возвращается к себе одним нажатием и входит
    заново.
    """
    first_id = await _seed_target(admin_client, db_session)
    await _register(admin_client, "second@test.com", "Второй")
    second_id = (await _user(db_session, "second@test.com")).id

    await _enter(admin_client, first_id)
    response = await _impersonate(admin_client, second_id)

    assert response.status_code == 403, (
        f"вложенный вход ответил {response.status_code} — цепочка личностей "
        "заведена состоянием, которого продукт не предусматривает"
    )
    assert _act_of(response) is None, (
        "вложенный вход выдал токен — отказ пришёл ПОСЛЕ выпуска"
    )


@pytest.mark.asyncio
async def test_the_refusal_names_the_other_identity_and_not_missing_rights(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Текст отказа под чужой личностью ОТЛИЧАЕТСЯ от отказа по правам.

    ⚠️ ЭТО НЕ ВОПРОС ФОРМУЛИРОВОК, А ВОПРОС ТОГО, ЧТО ЧЕЛОВЕК ПОЙДЁТ ЧИНИТЬ.
    Администратор, получивший «недостаточно прав» там, где на самом деле мешает
    чужая личность, пойдёт разбираться с правами: проверять адрес в настройке,
    перевыпускать токен, читать журнал доступа. Настоящая причина — что он не
    вышел из чужой учётной записи — при этом не названа ни одним словом, и
    единственное действие, которое ему нужно, останется невыполненным.

    Отказ по правам берётся у СОСЕДНЕГО гейта ЖИВЫМ ЗАПРОСОМ, а не литералом:
    сравнение с константой согласилось бы с правкой, сблизившей два текста.
    """
    target_id = await _seed_target(admin_client, db_session)

    # Отказ по правам: посторонний (не администратор) просится в админку.
    await _register(admin_client, "outsider@test.com", "Посторонний")
    await admin_client.post(
        "/login",
        data={"email": "outsider@test.com", "password": PASSWORD},
        follow_redirects=False,
    )
    rights = await _impersonate(admin_client, target_id)
    rights_detail = _detail_of(rights)

    # Отказ по чужой личности: тот же администратор, но под пользователем.
    await admin_client.post(
        "/login",
        data={"email": "admin@test.com", "password": PASSWORD},
        follow_redirects=False,
    )
    await _enter(admin_client, target_id)
    identity = await admin_client.post("/billing/subscribe", follow_redirects=False)
    identity_detail = _detail_of(identity)

    # ⚠️ КОД ОТКАЗА УТВЕРЖДАЕТСЯ ДО СРАВНЕНИЯ ТЕКСТОВ, И ЭТО НЕ ПРИДИРКА.
    # Без него тест зеленел бы на ЛЮБОМ непохожем ответе — в том числе на 500
    # с телом «Internal server error», которое от отказа по правам тоже
    # отличается. Проверялась бы тогда не различимость причин, а несовпадение
    # двух случайных строк.
    assert rights.status_code == 403, (
        f"отказ по правам ответил {rights.status_code} — сравнивать не с чем"
    )
    assert identity.status_code == 403, (
        f"отказ по чужой личности ответил {identity.status_code} — тексты "
        "сравнивались бы у ответа, отказом не являющегося"
    )
    assert IMPERSONATION_REFUSAL_MARK in identity_detail, (
        f"отказ не назвал причиной чужую личность: {identity_detail!r}"
    )
    assert rights_detail, "отказ по правам не объяснён ни словом"
    assert identity_detail, "отказ по чужой личности не объяснён ни словом"
    assert identity_detail != rights_detail, (
        "два отказа неразличимы по тексту: администратор пойдёт чинить права "
        f"вместо того, чтобы выйти из чужой учётной записи ({identity_detail!r})"
    )
    assert identity_detail != PERMISSION_REFUSAL_DETAIL, (
        "отказ по чужой личности говорит словами отказа по правам"
    )


@pytest.mark.asyncio
async def test_the_payment_webhook_without_a_token_is_not_refused(
    client: AsyncClient,
):
    """Вебхук платёжной системы приходит БЕЗ токена и запретом НЕ задевается.

    ⚠️ ОТСУТСТВИЕ ТОКЕНА — НЕ ОТКАЗ, И ЭТО НЕСУЩЕЕ СВОЙСТВО ЗАПРЕТА. Денежный
    роутер закрыт ЦЕЛИКОМ, а единственный его вход — уведомление ЮKassa о
    СОСТОЯВШЕМСЯ платеже, приходящее не от браузера и никакого токена не
    несущее. Зависимость, отвергающая запрос без действующего лица, остановила
    бы приём денег по УЖЕ СОВЕРШЁННЫМ платежам, и потерянное уведомление
    откатом кода не возвращается — ровно цена, которую разбирал чекпойнт плана
    06-06 (D-53).

    Предмет — что отказ пришёл НЕ ОТ ЗАПРЕТА ИМПЕРСОНАЦИИ. Собственный гард
    вебхука (сверка адреса источника) отвечает 403 своим текстом, и это его
    работа, а не наша.
    """
    response = await client.post(
        "/api/billing/webhook",
        json={"event": "payment.succeeded", "object": {"id": "x"}},
    )

    assert response.status_code != 401, (
        "вебхук отвергнут по отсутствию токена — приём денег остановлен"
    )
    detail = _detail_of(response)
    assert IMPERSONATION_REFUSAL_MARK not in detail, (
        f"вебхук отвергнут ЗАПРЕТОМ ИМПЕРСОНАЦИИ ({detail!r}) — уведомление о "
        "состоявшемся платеже потеряно, и откатом кода оно не возвращается"
    )


@pytest.mark.asyncio
async def test_without_impersonation_no_forbidden_route_changed_behaviour(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """БЕЗ имперсонации ни один запрещённый маршрут поведения не изменил.

    ⚠️ ЭТО ГЛАВНАЯ ГРАНИЦА СВЕРХУ ВСЕГО ПЛАНА. Запрет, срабатывающий ВСЕГДА,
    прошёл бы каждое утверждение выше и при этом закрыл бы обычному
    пользователю оплату, восстановление пароля, правку профиля и повтор
    отправки — то есть сломал бы продукт целиком, оставаясь зелёным.

    Утверждения написаны ОТ ПРОТИВНОГО: предмет — что отказ пришёл НЕ ОТ
    ЗАПРЕТА ИМПЕРСОНАЦИИ. Собственные причины у этих маршрутов есть (истёкшая
    ссылка сброса, отсутствующая запись журнала), и требовать от них успеха
    значило бы вписать в этот тест чужие правила.
    """
    for path, payload in (
        ("/billing/subscribe", None),
        ("/forgot-password/send-code", {"email": "testuser@test.com"}),
        ("/forgot-password/reset", {"token": "x", "password": "newpass123"}),
        ("/profile", {"timezone": "Europe/Moscow"}),
        ("/history/1/retry", None),
    ):
        response = await authed_client.post(
            path, data=payload, follow_redirects=False
        )
        detail = _detail_of(response)
        assert IMPERSONATION_REFUSAL_MARK not in detail, (
            f"{path} закрыт запретом имперсонации БЕЗ имперсонации — запрет "
            "срабатывает всегда и ломает продукт обычному пользователю"
        )


# =============================================================================
# ИСТОЧНИК ТОКЕНА У ЗАПРЕТА — ПОВЕДЕНИЕ, А НЕ ОБЪЯВЛЕНИЕ (CR-01 ревизии фазы 6)
#
# ⚠️ ПОЧЕМУ ЭТИ УТВЕРЖДЕНИЯ ПОНАДОБИЛИСЬ ОТДЕЛЬНО ОТ ВСЕХ ВЫШЕ. Дефект, ради
# которого они написаны, пережил всю фазу при ЗЕЛЁНОМ машинном гейте и зелёных
# сквозных проверках выше, и причина ровно одна: ни те, ни другие не подавали
# запросу ВТОРОГО носителя токена. Гейт утверждает, что запрет ОБЪЯВЛЕН на
# маршруте; проверки выше утверждают, что он срабатывает НА ЗАПРОСЕ ОДНОГО
# ВИДА — с одной лишь cookie. Между «объявлен» и «срабатывает на любом запросе»
# помещалась дыра: `_actor_id` читал ПЕРВЫЙ предъявленный носитель, а закрытые
# страничные обработчики аутентифицируются ТОЛЬКО из cookie, и присланный
# заголовок `Authorization` — в том числе негодный, в том числе не токен
# вовсе — отключал запрет целиком.
#
# ⚠️ ПОКРЫТИЕ ОБЪЯВЛЕНИЯ И ПОКРЫТИЕ ПОВЕДЕНИЯ — РАЗНЫЕ ВЫСКАЗЫВАНИЯ. Мутация
# «снять зависимость с маршрута» краснит гейт и потому выглядит доказательством
# его зубов; мутация «прислать лишний заголовок» не краснила НИЧЕГО. Перечень
# носителей ниже выписан руками именно поэтому: он есть предмет, а не оформление.
# =============================================================================


# Носители, которые запрос может предъявить ПОМИМО cookie сессии. Пустой
# словарь — исходный случай, ради сравнения; остальные — ровно те заголовки,
# которыми запрет отключался.
PRESENTED_BESIDES_THE_COOKIE = (
    {},
    {"Authorization": "Bearer zzz"},
    {"Authorization": "Bearer "},
    {"Authorization": "Basic zzz"},
)

# Маршруты, на которых дыра была воспроизведена живым запросом: начало захвата
# учётной записи и денежный вход, закрытый роутером ЦЕЛИКОМ.
FORBIDDEN_PAGE_ENTRIES = (
    ("/forgot-password/send-code", {"email": TARGET_EMAIL}),
    ("/billing/subscribe", None),
)


@pytest.mark.asyncio
@pytest.mark.parametrize("path,payload", FORBIDDEN_PAGE_ENTRIES)
async def test_no_presented_header_switches_the_prohibition_off(
    path, payload, admin_client: AsyncClient, db_session: AsyncSession
):
    """Запрет держится при ЛЮБОМ предъявленном заголовке (CR-01, D-22).

    ⚠️ ПРЕДМЕТ — НЕ «ЗАГОЛОВОК ПЛОХОЙ», А «ИСТОЧНИК ТОКЕНА У ГАРДА И У
    ОБРАБОТЧИКА ОБЯЗАН БЫТЬ ОДИН». Обработчики этих маршрутов читают личность
    ТОЛЬКО из cookie (`get_user_from_cookie`); гард, читавший первый носитель по
    порядку, при наличии заголовка приходил к выводу «действующего лица нет» и
    пропускал запрос — при полностью живом сеансе имперсонации. Живой снимок
    дыры: `POST /forgot-password/send-code` без заголовка отвечал 403, с
    заголовком `Bearer zzz` — 200 и выписанным кодом сброса пароля ЖЕРТВЫ.

    ⚠️ ПУСТОЙ СЛОВАРЬ В ПЕРЕЧНЕ НОСИТЕЛЕЙ ОБЯЗАТЕЛЕН. Без него тест зеленел бы у
    запрета, отказывающего по САМОМУ ФАКТУ заголовка, а не по признаку
    действующего лица, и мы не отличили бы починку от новой поломки.
    """
    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    for headers in PRESENTED_BESIDES_THE_COOKIE:
        response = await admin_client.post(
            path, data=payload, headers=headers, follow_redirects=False
        )

        assert response.status_code == 403, (
            f"{path} ответил {response.status_code} под чужой личностью при "
            f"заголовках {headers} — запрет отключается присланным заголовком, "
            "и под чужой учётной записью доступны захват учётки и деньги"
        )
        assert IMPERSONATION_REFUSAL_MARK in _detail_of(response), (
            f"{path} при заголовках {headers} отказал ПО ДРУГОЙ ПРИЧИНЕ "
            f"({_detail_of(response)!r}) — совпадение кода 403 доказательством "
            "срабатывания запрета не является"
        )


@pytest.mark.asyncio
async def test_a_valid_bearer_token_of_the_actor_does_not_switch_it_off(
    admin_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Запрет держится и при ГОДНОМ токене в заголовке, а не только при мусоре.

    ⚠️ ЭТО САМЫЙ ПРАВДОПОДОБНЫЙ ВИД ДЫРЫ, И БЕЗ НЕГО ПОЧИНКА ВЫГЛЯДЕЛА БЫ КАК
    «отвергать негодные заголовки». Администратор с собственным API-токеном
    предъявляет его СОВЕРШЕННО ЗАКОННО; носитель годен, подпись верна,
    признака действующего лица в нём нет — и прежнее чтение «первый носитель по
    порядку» на этом заканчивалось, объявляя, что имперсонации нет. Сеанс
    имперсонации при этом продолжал ехать в cookie, которой обработчик и
    аутентифицируется.

    Отсюда и форма починки: спрашиваются ВСЕ предъявленные носители, а не
    первый. Проверка «заголовок разобрался — значит имперсонации нет» закрыла бы
    мусорный случай и оставила бы этот.
    """
    from app.services.auth_service import create_access_token

    target_id = await _seed_target(admin_client, db_session)
    admin_id = (await _user(db_session, test_settings.admin_email)).id
    ordinary = create_access_token(admin_id, test_settings.secret_key)

    await _enter(admin_client, target_id)

    response = await admin_client.post(
        "/billing/subscribe",
        headers={"Authorization": f"Bearer {ordinary}"},
        follow_redirects=False,
    )

    assert response.status_code == 403, (
        f"денежный вход ответил {response.status_code} под чужой личностью при "
        "ГОДНОМ токене администратора в заголовке — запрет отключается вторым "
        "законным носителем"
    )
    assert IMPERSONATION_REFUSAL_MARK in _detail_of(response), (
        f"отказ пришёл по другой причине: {_detail_of(response)!r}"
    )


@pytest.mark.asyncio
async def test_the_refusal_under_a_presented_header_reaches_the_journal(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Сработавший запрет ОСТАВЛЯЕТ СЛЕД — в том числе при лишнем заголовке.

    ⚠️ МОЛЧАНИЕ ЖУРНАЛА БЫЛО ВТОРОЙ ПОЛОВИНОЙ ДЕФЕКТА, И ОНО ЖЕ БЫЛО ПРИЧИНОЙ,
    ПО КОТОРОЙ ОН ПРОЖИЛ ВСЮ ФАЗУ. Обход не доходил до строки
    `impersonated_action_refused`, поэтому у эксплуатации не было ни одного
    наблюдаемого признака: ни отказа, ни записи. Утверждение про журнал стоит
    рядом с утверждением про код ответа именно поэтому — «отказал» и «отказ
    видно» суть разные свойства.

    Снимается с самого вызова журнала, а не с `caplog`, по причине, уже
    записанной у `test_both_the_entry_and_the_return_are_journaled_with_both_ids`:
    настройка журналирования общая на процесс, и запись до перехватчика
    доезжает не в каждом порядке файлов.
    """
    from unittest.mock import MagicMock, patch

    import app.dependencies as dependencies_module

    target_id = await _seed_target(admin_client, db_session)
    await _enter(admin_client, target_id)

    guard_logger = MagicMock()
    with patch.object(dependencies_module, "logger", guard_logger):
        response = await admin_client.post(
            "/billing/subscribe",
            headers={"Authorization": "Bearer zzz"},
            follow_redirects=False,
        )

    assert response.status_code == 403, (
        f"запрет не сработал ({response.status_code}) — утверждение о журнале "
        "проверяло бы след несостоявшегося отказа"
    )

    events = [
        call.args[0]
        for call in guard_logger.warning.call_args_list
        if call.args
    ]
    assert "impersonated_action_refused" in events, (
        "сработавший запрет не оставил именованной записи в журнале: "
        f"{events} — эксплуатация обхода не имела бы ни одного наблюдаемого "
        "признака"
    )

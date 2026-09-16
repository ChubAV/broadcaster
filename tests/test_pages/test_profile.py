import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.pages import notices

# Признак запроса от слоя письма. Литерал стоит ЗДЕСЬ, а не ввозится из
# приложения, и это не второе объявление признака: единственность, которую
# держит веха, — единственность ЧТЕНИЯ признака ПРИЛОЖЕНИЕМ
# (`app/pages/htmx.py::is_htmx`). Здесь признак ПИШЕТСЯ, а пишущая сторона —
# клиент; в продукте им выступает сам слой письма в браузере. То же основание
# выписано у фикстуры `htmx_client` и в шапке `test_confirm_delete_transport.py`.
HTMX_HEADERS = {"HX-Request": "true"}

DOCUMENT_MARK = "<!DOCTYPE"

# Цель ВЕЖЛИВОЙ области уведомления. Запись `profile_saved` объявлена вариантом
# `success`, а внеполосный блок выбирает область ПО ВАРИАНТУ записи
# (`includes/notice_oob.html`): настойчивая область достаётся только отказу.
POLITE_NOTICE_TARGET = 'hx-swap-oob="innerHTML:#notice"'

# Враждебное значение поля (T-11-13). Пояс приходит от пользователя, и на ветке
# ошибки обработчик подаёт шаблону ПРИСЛАННОЕ значение.
HOSTILE_TIMEZONE = '"><script>alert(1)</script>'

# Подстрока, которой враждебное значение выдало бы себя, приехав НЕЭКРАНИРОВАННЫМ.
HOSTILE_MARK = "<script>alert(1)"

# Текст ошибки поля — дословно тот, что рисует обработчик.
FIELD_ERROR_TEXT = "Неверный часовой пояс"


@pytest.mark.asyncio
async def test_profile_requires_auth(client: AsyncClient):
    response = await client.get("/profile", follow_redirects=False)
    assert response.status_code in (302, 307)
    location = response.headers.get("location", "")
    assert "/login" in location


@pytest.mark.asyncio
async def test_profile_get_renders_form_for_authenticated_user(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict,
):
    # Фикстура auth_headers создаёт пользователя через API-роуты
    result = await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    user = result.scalar_one()
    user.timezone = "Europe/Moscow"
    await db_session.commit()

    # Логинимся через page-роут, чтобы установить cookie access_token
    await client.post(
        "/login",
        data={"email": "testuser@test.com", "password": "testpass123"},
        follow_redirects=False,
    )

    response = await client.get("/profile")
    assert response.status_code == 200
    html = response.text
    assert "Профиль" in html
    assert 'name="timezone"' in html
    # Текущая таймзона должна быть выбрана
    assert '<option value="Europe/Moscow" selected' in html


@pytest.mark.asyncio
async def test_profile_post_updates_timezone(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict,
):
    result = await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    user = result.scalar_one()
    assert user.timezone == "UTC"

    # Логинимся через страницу, чтобы выставить cookie
    await client.post(
        "/login",
        data={"email": "testuser@test.com", "password": "testpass123"},
        follow_redirects=False,
    )

    response = await client.post(
        "/profile",
        data={"timezone": "Europe/Moscow"},
        follow_redirects=False,
    )
    # Ожидаем редирект обратно на /profile
    assert response.status_code in (302, 303, 307)
    location = response.headers.get("location", "")
    assert "/profile" in location

    await db_session.refresh(user)
    assert user.timezone == "Europe/Moscow"


@pytest.mark.asyncio
async def test_profile_post_invalid_timezone_does_not_update(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict,
):
    result = await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    user = result.scalar_one()
    user.timezone = "UTC"
    await db_session.commit()

    # Логинимся через страницу, чтобы выставить cookie
    await client.post(
        "/login",
        data={"email": "testuser@test.com", "password": "testpass123"},
        follow_redirects=False,
    )

    response = await client.post(
        "/profile",
        data={"timezone": "Not/AZone"},
    )
    # Возвращаем форму с ошибкой
    assert response.status_code == 422
    html = response.text
    assert "Неверный часовой пояс" in html

    await db_session.refresh(user)
    assert user.timezone == "UTC"


@pytest.mark.asyncio
async def test_profile_save_over_htmx_returns_the_form_and_the_notice(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Сохранение на htmx отвечает ФОРМОЙ и кодом исхода; без htmx — прежним 302.

    ⚠️ ЭТО ПЕРВОЕ ПОВЕДЕНИЕ ВЕТКИ «КОД ИСХОДА НА ФРАГМЕНТЕ» (D-02). Приклейка
    внеполосного блока к телу фрагмента существует с Фазы 8 и до этого плана не
    использовалась НИ ОДНИМ обработчиком приложения: механизм был заведён и
    покрыт суитой заранее. Здесь он впервые становится поведением продукта.

    ⚠️ ПРИЗНАК СТАВИТСЯ НА ОДИН ЗАПРОС ИЗ ДВУХ, А НЕ ФИКСТУРОЙ `htmx_client`.
    Она помечает ОБЩИЙ объект клиента, и половина деградации, запрошенная рядом
    с ней, молча превратилась бы во вторую половину htmx — то есть пара
    транспортов проверяла бы один транспорт дважды (записанный опыт плана 10-01,
    шапка `tests/test_pages/test_htmx_post_pairs.py`).

    ⚠️ ПОЛОВИНА htmx ИДЁТ С `follow_redirects=True`, И ЭТО ЧАСТЬ ПРЕДМЕТА, А НЕ
    УДОБСТВО. Браузер следует ответу 302 на запрос htmx НЕЗАМЕТНО и подставляет
    в область свопа целый документ; человек при этом не узнаёт ни о чём.
    Утверждение о 200 обязано уметь покраснеть именно на этом — с
    `follow_redirects=False` редирект пришёл бы кодом 302 и тоже покраснел, но
    утверждение «в теле нет целого документа» осталось бы непроверенным.
    """
    result = await db_session.execute(
        select(User).where(User.email == "testuser@test.com")
    )
    user = result.scalar_one()
    user.timezone = "UTC"
    await db_session.commit()

    over_htmx = await authed_client.post(
        "/profile",
        data={"timezone": "Europe/Moscow"},
        headers=HTMX_HEADERS,
        follow_redirects=True,
    )

    assert over_htmx.status_code == 200, (
        f"сохранение на htmx ответило {over_htmx.status_code} вместо 200 — "
        "экран остаётся на месте, и уводить с него нечем"
    )
    body = over_htmx.text
    assert DOCUMENT_MARK not in body, (
        "слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ — обработчик ответил "
        "перенаправлением, и клиент прошёл по нему прозрачно"
    )
    assert 'action="/profile"' in body, (
        "во фрагменте нет формы настроек — подменять в карточке нечем"
    )
    assert '<option value="Europe/Moscow" selected' in body, (
        "форма вернулась без СОХРАНЁННОГО пояса: человек увидел бы прежнее "
        "значение и решил, что сохранение не состоялось"
    )
    assert POLITE_NOTICE_TARGET in body, (
        "внеполосного блока уведомления в теле нет — исход действия виден "
        "только тому, кто получил редирект, то есть каналом пользуется лишь "
        "один транспорт из двух"
    )
    record = notices.notice_for(notices.PROFILE_SAVED)
    assert record is not None and record.text in body, (
        "текста записи реестра в теле нет — сохранение снова отвечает молча"
    )

    await db_session.refresh(user)
    assert user.timezone == "Europe/Moscow", (
        "часовой пояс не сохранён: перевод на слой ответа поменял ТРАНСПОРТ, а "
        "не то, что действие делает"
    )

    # --- половина деградации: прежний 302 с кодом исхода в адресе -------------
    user.timezone = "UTC"
    await db_session.commit()

    degraded = await authed_client.post(
        "/profile", data={"timezone": "Europe/Moscow"}, follow_redirects=False
    )

    assert degraded.status_code == 302, (
        f"путь без htmx ответил {degraded.status_code} вместо 302 — человек без "
        "JavaScript получил бы кусок разметки вместо страницы"
    )
    assert degraded.headers["location"] == f"/profile?notice={notices.PROFILE_SAVED}", (
        f"адрес деградации {degraded.headers['location']!r} не совпал с прежним "
        "ПОСИМВОЛЬНО: фаза меняет форму ответа, а не адрес приземления"
    )


@pytest.mark.asyncio
async def test_an_invalid_timezone_answers_422_with_the_echo_on_both_transports(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Негодный и ОТСУТСТВУЮЩИЙ пояс — 422 на обоих транспортах (FORM-08, D-06).

    ⚠️ КОД ОДИН И ТОТ ЖЕ НА ОБОИХ ТРАНСПОРТАХ, А ТЕЛО РАЗНОЕ. Ошибка заполнения
    не есть исход действия: действие не состоялось, и перенаправлять человека
    некуда — он остаётся на форме, которую заполнял. Поэтому путь без htmx
    получает СТРАНИЦУ со статусом 422, а не редирект, а путь htmx — фрагмент той
    же формы, потому что подменяется область формы, а не документ.

    ⚠️ ОТСУТСТВУЮЩЕЕ ПОЛЕ ИДЁТ ВЕТКОЙ ОБРАБОТЧИКА, А НЕ ОТКАЗОМ ФРЕЙМВОРКА, И
    ЭТО УТВЕРЖДЕНИЕ, А НЕ ПОБОЧНОЕ СЛЕДСТВИЕ. Обязательное поле без умолчания
    срывало бы разбор сигнатуры ДО тела обработчика, и ответ собирал бы не
    продукт: на пути htmx страничного слоя это пустой 400 смягчения T-07-13
    (план 11-07), то есть человек не увидел бы ни формы, ни причины.

    ⚠️ ВРАЖДЕБНОЕ ЗНАЧЕНИЕ НЕ ПРИЕЗЖАЕТ В ДОКУМЕНТ ВОВСЕ, И ЭТО СИЛЬНЕЕ
    ЭКРАНИРОВАНИЯ (T-11-13). Поле выбора рисует ЗАКРЫТЫЙ список поясов, а
    присланное значение лишь СРАВНИВАЕТСЯ с его элементами; значение, ни с одним
    не совпавшее, не попадает в разметку ни одним путём. Утверждение снимается с
    ответа именно поэтому: оно обязано краснеть и на потерянном экранировании, и
    на попытке напечатать присланное «как есть».
    """
    result = await db_session.execute(
        select(User).where(User.email == "testuser@test.com")
    )
    user = result.scalar_one()
    user.timezone = "UTC"
    await db_session.commit()

    # --- транспорт htmx: фрагмент формы с текстом ошибки ----------------------
    over_htmx = await authed_client.post(
        "/profile",
        data={"timezone": HOSTILE_TIMEZONE},
        headers=HTMX_HEADERS,
        follow_redirects=True,
    )

    assert over_htmx.status_code == 422, (
        f"ошибка поля на htmx ответила {over_htmx.status_code} вместо 422 — "
        "правило блока конфигурации ждёт именно этот код, и подмена формы "
        "выполняется по нему"
    )
    fragment = over_htmx.text
    assert FIELD_ERROR_TEXT in fragment, (
        "во фрагменте нет текста ошибки — человек получил бы перерисованную "
        "форму без единого слова о причине"
    )
    assert DOCUMENT_MARK not in fragment, (
        "слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ: правило 422 подменит им содержимое "
        "карточки, и в форме окажется страница внутри страницы"
    )
    assert HOSTILE_MARK not in fragment, (
        "присланное значение приехало в разметку НЕЭКРАНИРОВАННЫМ — подменяемое "
        "тело проходит через воскрешающий скрипты помощник рантайма (T-07-13)"
    )
    assert 'action="/profile"' in fragment, (
        "во фрагменте нет самой формы — подменять в карточке нечем, и кнопка "
        "сохранения станет мёртвой"
    )

    # --- транспорт без htmx: ПОЛНАЯ страница тем же кодом ---------------------
    without = await authed_client.post(
        "/profile", data={"timezone": HOSTILE_TIMEZONE}, follow_redirects=False
    )

    assert without.status_code == 422, (
        f"путь без htmx ответил {without.status_code} вместо 422 — код обязан "
        "быть ОДНИМ на обоих транспортах"
    )
    assert DOCUMENT_MARK in without.text, (
        "человеку без JavaScript приехал фрагмент без шелла вместо страницы"
    )
    assert FIELD_ERROR_TEXT in without.text, (
        "на странице нет текста ошибки — форма вернулась молча"
    )
    assert HOSTILE_MARK not in without.text, (
        "присланное значение напечатано в странице НЕЭКРАНИРОВАННЫМ"
    )

    # --- ОТСУТСТВУЮЩЕЕ поле: та же ветка обработчика, а не отказ фреймворка ---
    missing = await authed_client.post("/profile", data={}, follow_redirects=False)

    assert missing.status_code == 422, (
        f"запрос без поля пояса ответил {missing.status_code} вместо 422 — "
        "разбор сигнатуры сорвался ДО тела обработчика, и ответ собрал не "
        "продукт"
    )
    assert FIELD_ERROR_TEXT in missing.text, (
        "ответ на запрос без поля не несёт текста ошибки — это тело фреймворка, "
        "а не форма продукта"
    )

    await db_session.refresh(user)
    assert user.timezone == "UTC", (
        "негодный пояс записан в базу: ветка ошибки обязана оставить "
        "сохранённое значение нетронутым"
    )


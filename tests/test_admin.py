import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.send_log import SendLog
from app.models.user import User


@pytest.mark.asyncio
@pytest.mark.parametrize("axis", ["status", "messenger", "period"])
async def test_admin_history_ignores_an_unknown_filter_value(
    admin_client: AsyncClient, db_session: AsyncSession, axis: str
):
    """Мусор в оси фильтра НЕ ВЫБИРАЕТ НИЧЕГО — и на админских маршрутах тоже.

    Пользовательские маршруты истории прогоняют каждую ось через `clean_choice`
    до `apply_history_filters`; админские звали фильтрацию сырыми значениями.
    Неизвестное значение давало там пустой список, в котором ни один чипс не
    отмечен активным, а сырая строка уезжала в `filter_params` — то есть в адрес
    сентинеля прокрутки и в контекст шаблона как ДЕЙСТВУЮЩИЙ фильтр. Инъекции
    нет (значения связываются параметрами), но экран нечитаем ровно так же, как
    был бы нечитаем у пользователя.

    Утверждается ПОВЕДЕНИЕ, а не наличие вызова: запись остаётся на экране.
    """
    target = User(email="target@test.com", password_hash="x", name="Target")
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    db_session.add(
        SendLog(
            user_id=target.id,
            ad_id=1,
            group_id=1,
            status="fail",
            messenger_type="wa",
            ad_title="Заголовок под отсечку",
            group_name="Группа",
        )
    )
    await db_session.commit()

    clean = await admin_client.get(f"/admin/users/{target.id}/history")
    assert clean.status_code == 200
    assert "Заголовок под отсечку" in clean.text

    dirty = await admin_client.get(
        f"/admin/users/{target.id}/history?{axis}=нетакогозначения"
    )

    assert dirty.status_code == 200
    assert "Заголовок под отсечку" in dirty.text, (
        f"мусор в оси «{axis}» применён как фильтр и выбрал пустой список"
    )
    assert "нетакогозначения" not in dirty.text, (
        f"сырое значение оси «{axis}» уехало в разметку как действующий фильтр"
    )


@pytest.mark.asyncio
async def test_admin_history_partial_ignores_an_unknown_filter_value(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Паршал прокрутки — ВТОРОЙ вход на те же оси, и отсечка стоит и там.

    Значение приезжает к нему из адреса сентинеля, поэтому пропущенная здесь
    отсечка позволила бы мусору дожить до второй страницы выдачи — там, где
    пользователь его уже не связывает со своим действием.
    """
    target = (
        await db_session.execute(select(User).where(User.email == "target2@test.com"))
    ).scalar_one_or_none()
    if target is None:
        target = User(email="target2@test.com", password_hash="x", name="Target2")
        db_session.add(target)
        await db_session.commit()
        await db_session.refresh(target)

    db_session.add(
        SendLog(
            user_id=target.id,
            ad_id=1,
            group_id=1,
            status="fail",
            messenger_type="wa",
            ad_title="Запись паршала",
            group_name="Группа",
        )
    )
    await db_session.commit()

    response = await admin_client.get(
        f"/admin/users/{target.id}/history/partial?status=нетакогостатуса"
    )

    assert response.status_code == 200
    assert "Запись паршала" in response.text, (
        "мусор в оси статуса применён как фильтр в паршале прокрутки"
    )


@pytest.mark.asyncio
async def test_non_admin_cannot_access_admin_page(client: AsyncClient, auth_headers):
    """Regular user gets 403 on /admin."""
    resp = await client.get("/admin", headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_access_admin_dashboard(client: AsyncClient):
    """Admin user can access /admin."""
    await client.post("/api/auth/register", json={
        "email": "admin@test.com",
        "password": "adminpass123",
        "name": "Admin User",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpass123",
    })
    token = resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/admin", headers=admin_headers)
    assert resp.status_code == 200
    # ⚠️ ПЛИТКА ОБЩЕГО ОСТАТКА СНЯТА И НЕ ЗАМЕНЕНА (A-8). Утверждение стоит
    # здесь, а не отдельным именем: обзор либо отдаёт 200 без неё, либо не
    # отдаёт 200 вовсе, и разделять эти два вопроса было бы разделением одного.
    # Замену завела бы фаза 6, и показатель, поставленный сюда сейчас, был бы
    # работой под снос.
    assert "Общий баланс сообщений" not in resp.text, (
        "плитка снятой величины вернулась на админский обзор"
    )


@pytest.mark.asyncio
async def test_admin_users_list(client: AsyncClient):
    """Admin can see users list."""
    await client.post("/api/auth/register", json={
        "email": "admin@test.com",
        "password": "adminpass123",
        "name": "Admin",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpass123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/admin/users", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_admin_user_detail(client: AsyncClient, db_session):
    """Admin can view user detail."""
    await client.post("/api/auth/register", json={
        "email": "admin@test.com",
        "password": "adminpass123",
        "name": "Admin",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpass123",
    })
    admin_token = resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create regular user
    await client.post("/api/auth/register", json={
        "email": "user@test.com",
        "password": "userpass123",
        "name": "Regular User",
    })

    from app.models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "user@test.com"))
    target = result.scalar_one()

    resp = await client.get(f"/admin/users/{target.id}", headers=admin_headers)
    assert resp.status_code == 200
    # Карточка пополнения и плитка остатка сняты вместе с самой величиной.
    # Управляющий элемент, упирающийся в несуществующий маршрут, читается как
    # поломка админки, а не как «эта операция больше не предлагается».
    assert "Пополнить баланс" not in resp.text, (
        "карточка пополнения вернулась в карточку пользователя"
    )


@pytest.mark.asyncio
async def test_the_admin_top_up_route_no_longer_answers(client: AsyncClient, db_session):
    """Маршрута пополнения остатка сообщений не существует.

    ⚠️ ПРЕДМЕТ ИНВЕРТИРОВАН, А НЕ УДАЛЁН. Прежде тест утверждал, что
    администратор пополняет остаток формой; валюта сообщений снята из продукта
    целиком, и пополнять больше нечего. Утверждение «этого входа нет» держится
    регрессией, а не памятью: привилегированная операция над чужой учётной
    записью возвращается тем легче, чем меньше остаётся следов, зачем её сняли.

    Запрос идёт БЕЗ учётных данных намеренно: живой маршрут ответил бы отказом
    доступа, и именно этим «маршрут есть, но не пускает» отличается от
    «маршрута нет».
    """
    from app.models.user import User
    from sqlalchemy import select

    await client.post("/api/auth/register", json={
        "email": "user@test.com",
        "password": "userpass123",
        "name": "User",
    })
    result = await db_session.execute(select(User).where(User.email == "user@test.com"))
    target = result.scalar_one()

    resp = await client.post(
        f"/admin/users/{target.id}/balance",
        data={"amount": "100", "description": "Test top-up"},
        follow_redirects=False,
    )
    assert resp.status_code in (404, 405), (
        "маршрут админского пополнения всё ещё отвечает"
    )


@pytest.mark.asyncio
async def test_admin_block_user(client: AsyncClient, db_session):
    """Admin can block a user."""
    await client.post("/api/auth/register", json={
        "email": "admin@test.com",
        "password": "adminpass123",
        "name": "Admin",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpass123",
    })
    admin_token = resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    await client.post("/api/auth/register", json={
        "email": "user@test.com",
        "password": "userpass123",
        "name": "User",
    })

    from app.models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "user@test.com"))
    target = result.scalar_one()

    resp = await client.post(
        f"/admin/users/{target.id}/block",
        headers=admin_headers,
        follow_redirects=False,
    )
    assert resp.status_code == 302

    await db_session.refresh(target)
    assert target.is_blocked is True


@pytest.mark.asyncio
async def test_admin_delete_user(client: AsyncClient, db_session):
    """Admin can delete a user."""
    await client.post("/api/auth/register", json={
        "email": "admin@test.com",
        "password": "adminpass123",
        "name": "Admin",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpass123",
    })
    admin_token = resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    await client.post("/api/auth/register", json={
        "email": "user@test.com",
        "password": "userpass123",
        "name": "User",
    })

    from app.models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "user@test.com"))
    target = result.scalar_one()
    target_id = target.id

    resp = await client.post(
        f"/admin/users/{target_id}/delete",
        headers=admin_headers,
        follow_redirects=False,
    )
    assert resp.status_code == 302

    deleted = await db_session.get(User, target_id)
    assert deleted is None


# --- План 05.1-09: тумблер бесплатного ДОСТУПА -------------------------------
#
# ⚠️ ПРЕДМЕТ ЭТИХ ТЕСТОВ ВЕРНУЛСЯ, СМЕНИВ ХРАНИЛИЩЕ, А НЕ ВЕРНУЛСЯ КАК БЫЛ.
# `test_the_admin_unlimited_route_no_longer_answers`, живший здесь между планами
# `05.1-08` и `05.1-09`, утверждал ОТСУТСТВИЕ входа: ревизия `0020` уронила
# таблицу остатка сообщений, на которой стоял прежний признак, и переключать
# стало нечего. Право администратора открыть доступ бесплатно при этом не
# отменялось (D-E, критерий 5 фазы) — оно переехало на
# `subscriptions.has_free_access`. Тот тест сам называл своё падение сигналом
# «вход снова есть», и вот он, положительный, на его месте.
#
# Маршрут, метод и адрес СОХРАНЕНЫ дословно (`POST /admin/users/{id}/unlimited`):
# переиспользуется вход, меняются хранилище и подписи кнопок.


async def _register_target(client: AsyncClient, db_session) -> "User":
    """Обычный пользователь-цель админской операции. Возвращает строку `users`."""
    await client.post("/api/auth/register", json={
        "email": "user@test.com",
        "password": "userpass123",
        "name": "User",
    })
    return (
        await db_session.execute(select(User).where(User.email == "user@test.com"))
    ).scalar_one()


async def _active_subscription(db_session, user_id: int):
    from app.models.subscription import Subscription

    return (
        await db_session.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_the_admin_toggle_flips_free_access_in_both_directions(
    admin_client: AsyncClient, db_session
):
    """Тумблер ВЫДАЁТ и СНИМАЕТ бесплатный доступ одним и тем же маршрутом.

    Обе стороны в одном тесте намеренно: тумблер, который умеет включать и не
    умеет выключать, проходит любую проверку «выдача работает» и оставляет
    администратора без способа отозвать выданное благо. Обратимость — то
    свойство, которым этот план оправдывает отсутствие подтверждения (UI-SPEC
    E5, Destructive confirmation), и она обязана быть УТВЕРЖДЕНА, а не обещана.

    Признак читается ИЗ БАЗЫ после каждого нажатия, а не из ответа формы: ответ
    отдаёт редирект и о состоянии колонки не говорит ничего.
    """
    target = await _register_target(admin_client, db_session)

    resp = await admin_client.post(
        f"/admin/users/{target.id}/unlimited", follow_redirects=False
    )
    assert resp.status_code == 302, "тумблер не ответил редиректом на карточку"

    subscription = await _active_subscription(db_session, target.id)
    assert subscription is not None, "у цели нет активной строки подписки"
    await db_session.refresh(subscription)
    assert subscription.has_free_access is True, "бесплатный доступ не выдан"

    resp = await admin_client.post(
        f"/admin/users/{target.id}/unlimited", follow_redirects=False
    )
    assert resp.status_code == 302

    await db_session.refresh(subscription)
    assert subscription.has_free_access is False, (
        "бесплатный доступ не снимается тем же тумблером — выданное благо "
        "нечем отозвать"
    )


@pytest.mark.asyncio
async def test_the_free_access_toggle_is_refused_for_a_non_admin(
    authed_client: AsyncClient, db_session
):
    """Выдача бесплатного доступа НЕ ДОСТУПНА обычному пользователю (T-05.1-05).

    Привилегированная операция над ЧУЖОЙ учётной записью, раздающая платное
    благо. Проверка прав живёт в зависимости `require_admin` и этим планом не
    ослабляется; утверждение стоит и по коду ответа, и по СОСТОЯНИЮ КОЛОНКИ —
    отказ, после которого признак всё-таки выставлен, отказом не является.
    """
    target = (
        await db_session.execute(
            select(User).where(User.email == "testuser@test.com")
        )
    ).scalar_one()

    resp = await authed_client.post(
        f"/admin/users/{target.id}/unlimited", follow_redirects=False
    )

    assert resp.status_code == 403, (
        f"тумблер ответил {resp.status_code} обычному пользователю"
    )
    subscription = await _active_subscription(db_session, target.id)
    await db_session.refresh(subscription)
    assert subscription.has_free_access is False, (
        "обычный пользователь выдал себе бесплатный доступ"
    )


@pytest.mark.asyncio
async def test_the_free_access_toggle_survives_a_user_without_a_subscription_row(
    admin_client: AsyncClient, db_session
):
    """Пятисотки на админском пути НЕТ у пользователя без строки подписки.

    🧪 BACKSTOP UI-контракта (E5 error, C4). Ревизия `0020` завела строку всем
    существующим пользователям, но утверждать это ЗДЕСЬ нельзя: суита строит
    схему из моделей и Alembic не запускает, то есть про популяцию П-о-1 она не
    знает ничего. Пользователь без строки в базе создаётся руками именно затем,
    чтобы требование «не отдавать 500» проверялось на самом состоянии, а не на
    вере в то, что ревизия его больше не производит.

    Требование интерфейсное и сформулировано отрицательно: чем именно оно
    обеспечено — созданием строки или отказом со словами — решает реализация.
    """
    target = User(email="rowless@test.com", password_hash="x", name="Rowless")
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    assert await _active_subscription(db_session, target.id) is None, (
        "посев не удался: у цели уже есть строка подписки, и backstop проверяет "
        "не то состояние"
    )

    resp = await admin_client.post(
        f"/admin/users/{target.id}/unlimited", follow_redirects=False
    )

    assert resp.status_code < 500, (
        f"тумблер бесплатного доступа отдал {resp.status_code} пользователю без "
        "строки подписки — админский путь падает на популяции, которая переживёт "
        "выкат"
    )


@pytest.mark.asyncio
async def test_granting_free_access_invalidates_the_access_verdict_cache(
    admin_client: AsyncClient, db_session
):
    """Тумблер СБРАСЫВАЕТ кэш вердикта доступа — в обе стороны (T-05.1-04).

    Вердикт `check_access` кэшируется на минуту (`app/services/billing_cache.py`),
    и тумблер пишет РОВНО ТУ величину, из которой вердикт считается. Без сброса
    выданный бесплатный доступ до минуты не работал бы, а СНЯТЫЙ — до минуты
    продолжал бы работать: второе хуже, потому что это платный ресурс, который
    продукт уже перестал выдавать.

    Утверждается ВЫЗОВ, а не наблюдаемое следствие: Redis в суите не поднят, и
    настоящий кэш здесь недостижим ни в одну сторону.
    """
    from unittest.mock import AsyncMock, patch

    target = await _register_target(admin_client, db_session)

    with patch(
        "app.pages.admin.invalidate_access_cache", new_callable=AsyncMock
    ) as invalidate:
        await admin_client.post(
            f"/admin/users/{target.id}/unlimited", follow_redirects=False
        )
        assert invalidate.await_count == 1, "выдача не сбросила кэш вердикта"
        assert invalidate.await_args.args[0] == target.id, (
            "сброшен кэш не того пользователя"
        )

        await admin_client.post(
            f"/admin/users/{target.id}/unlimited", follow_redirects=False
        )
        assert invalidate.await_count == 2, "снятие не сбросило кэш вердикта"


@pytest.mark.asyncio
async def test_the_free_access_grant_is_journaled_with_both_identities(
    admin_client: AsyncClient, db_session
):
    """Выдача уходит в журнал ИМЕНОВАННЫМ ключом с обоими идентификаторами.

    T-05.1-05, вторая половина смягчения. Проверка прав отвечает на вопрос «кто
    имел право»; журнал отвечает на вопрос «кто и кому это сделал», и без него
    привилегированная операция над чужой учётной записью не оставляет следа
    вовсе. Оба идентификатора обязательны: запись без цели не позволяет узнать,
    кому выдали, а без администратора — кто выдал.

    Утверждается и НОВОЕ ЗНАЧЕНИЕ признака: одна пара записей на включение и
    выключение сделала бы журнал неспособным отличить выдачу от отзыва.
    """
    import structlog

    target = await _register_target(admin_client, db_session)

    with structlog.testing.capture_logs() as logs:
        await admin_client.post(
            f"/admin/users/{target.id}/unlimited", follow_redirects=False
        )

    entries = [entry for entry in logs if entry.get("event") == "free_access_toggled"]
    assert len(entries) == 1, (
        f"выдача бесплатного доступа не оставила записи `free_access_toggled`: "
        f"{[entry.get('event') for entry in logs]}"
    )
    entry = entries[0]
    assert entry.get("target_user_id") == target.id
    assert entry.get("admin_user_id") is not None, "журнал не назвал администратора"
    assert entry.get("has_free_access") is True, (
        "журнал не назвал НОВОЕ значение признака — выдача неотличима от отзыва"
    )


@pytest.mark.asyncio
async def test_blocked_user_cannot_login(client: AsyncClient, db_session):
    """Blocked user gets rejected on login."""
    from app.models.user import User
    from app.services.auth_service import hash_password

    user = User(
        email="blocked@test.com",
        password_hash=hash_password("pass123"),
        name="Blocked",
        is_blocked=True,
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post("/api/auth/login", json={
        "email": "blocked@test.com",
        "password": "pass123",
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_cannot_block_self(client: AsyncClient, db_session):
    """Admin cannot block themselves."""
    await client.post("/api/auth/register", json={
        "email": "admin@test.com",
        "password": "adminpass123",
        "name": "Admin",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpass123",
    })
    admin_token = resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    from app.models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "admin@test.com"))
    admin_user = result.scalar_one()

    resp = await client.post(
        f"/admin/users/{admin_user.id}/block",
        headers=admin_headers,
        follow_redirects=False,
    )
    assert resp.status_code == 302

    await db_session.refresh(admin_user)
    assert admin_user.is_blocked is False


@pytest.mark.asyncio
async def test_admin_cannot_delete_self(client: AsyncClient, db_session):
    """Admin cannot delete themselves."""
    await client.post("/api/auth/register", json={
        "email": "admin@test.com",
        "password": "adminpass123",
        "name": "Admin",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpass123",
    })
    admin_token = resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    from app.models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "admin@test.com"))
    admin_user = result.scalar_one()

    resp = await client.post(
        f"/admin/users/{admin_user.id}/delete",
        headers=admin_headers,
        follow_redirects=False,
    )
    assert resp.status_code == 302

    still_exists = await db_session.get(User, admin_user.id)
    assert still_exists is not None

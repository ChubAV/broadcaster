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


@pytest.mark.asyncio
async def test_admin_toggle_unlimited(client: AsyncClient, db_session):
    """Admin can toggle unlimited status for a user."""
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
    from app.models.message_balance import MessageBalance
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "user@test.com"))
    target = result.scalar_one()

    # Toggle on
    resp = await client.post(
        f"/admin/users/{target.id}/unlimited",
        headers=admin_headers,
        follow_redirects=False,
    )
    assert resp.status_code == 302

    bal_result = await db_session.execute(
        select(MessageBalance).where(MessageBalance.user_id == target.id)
    )
    bal = bal_result.scalar_one()
    assert bal.is_unlimited is True

    # Toggle off
    resp = await client.post(
        f"/admin/users/{target.id}/unlimited",
        headers=admin_headers,
        follow_redirects=False,
    )
    assert resp.status_code == 302

    await db_session.refresh(bal)
    assert bal.is_unlimited is False


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

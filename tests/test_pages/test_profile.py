import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User


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
    assert "Настройки профиля" in html
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
    assert response.status_code == 400
    html = response.text
    assert "Неверный часовой пояс" in html

    await db_session.refresh(user)
    assert user.timezone == "UTC"


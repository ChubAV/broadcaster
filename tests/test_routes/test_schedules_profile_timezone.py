import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User


@pytest.mark.asyncio
async def test_new_schedule_form_uses_user_timezone_by_default(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict,
):
    # Пользователь уже создан через auth_headers
    result = await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    user = result.scalar_one()
    user.timezone = "Europe/Moscow"
    await db_session.commit()

    # Логинимся через страницу, чтобы выставить cookie
    await client.post(
        "/login",
        data={"email": "testuser@test.com", "password": "testpass123"},
        follow_redirects=False,
    )

    resp = await client.get("/schedules/new")
    assert resp.status_code == 200
    html = resp.text

    # В форме должен быть выбран timezone пользователя.
    # Проверяем сам <option>, а не «что идёт после первого вхождения строки»:
    # шелл показывает таймзону пользователя в блоке data-user, поэтому
    # позиционная проверка ловила бы разметку шелла, а не поле формы.
    assert '<option value="Europe/Moscow" selected' in html


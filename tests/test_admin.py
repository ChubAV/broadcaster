import pytest
from httpx import AsyncClient


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


@pytest.mark.asyncio
async def test_admin_set_plan(client: AsyncClient, db_session):
    """Admin can set user plan."""
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
        "name": "User",
    })

    from app.models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "user@test.com"))
    target = result.scalar_one()

    resp = await client.post(
        f"/admin/users/{target.id}/balance",
        data={"amount": "100", "description": "Test top-up"},
        headers=admin_headers,
        follow_redirects=False,
    )
    assert resp.status_code == 302


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

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_info import GroupInfo


@pytest_asyncio.fixture
async def admin_login(client: AsyncClient):
    """Register admin user (admin@test.com) and login via page route to set cookie."""
    await client.post("/api/auth/register", json={
        "email": "admin@test.com",
        "password": "adminpass123",
        "name": "Admin",
    })
    await client.post(
        "/login",
        data={"email": "admin@test.com", "password": "adminpass123"},
        follow_redirects=False,
    )


@pytest_asyncio.fixture
async def sample_group_info(db_session: AsyncSession) -> GroupInfo:
    item = GroupInfo(
        messenger_type="tg_user",
        external_id="-100123",
        name="Test Group",
        member_count=42,
        admin_contacts=[{"id": "111", "name": "Admin User", "username": "admin"}],
        raw_metadata={"title": "Test Group", "participants_count": 42},
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest.mark.asyncio
async def test_groups_info_page_200_for_admin(
    client: AsyncClient,
    admin_login,
    sample_group_info: GroupInfo,
):
    response = await client.get("/admin/groups-info")
    assert response.status_code == 200
    assert "Справочник групп" in response.text
    assert "Test Group" in response.text


@pytest.mark.asyncio
async def test_groups_info_page_403_for_non_admin(
    client: AsyncClient,
):
    # Register and login as non-admin user
    await client.post("/api/auth/register", json={
        "email": "user@example.com",
        "password": "userpass123",
        "name": "Regular User",
    })
    await client.post(
        "/login",
        data={"email": "user@example.com", "password": "userpass123"},
        follow_redirects=False,
    )
    response = await client.get("/admin/groups-info")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_group_info_detail_200(
    client: AsyncClient,
    admin_login,
    sample_group_info: GroupInfo,
):
    response = await client.get(f"/admin/groups-info/{sample_group_info.id}")
    assert response.status_code == 200
    assert "Test Group" in response.text
    assert "-100123" in response.text
    assert "Admin User" in response.text

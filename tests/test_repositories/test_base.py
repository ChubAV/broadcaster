import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.user import User
from app.repositories.base import BaseRepository
from app.services.auth_service import hash_password


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    user = User(email="repo@test.com", password_hash=hash_password("pass"), name="Repo")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def ad_repo(db_session: AsyncSession) -> BaseRepository[Ad]:
    return BaseRepository(db_session, Ad)


@pytest.mark.asyncio
async def test_create(ad_repo, user):
    ad = await ad_repo.create(user_id=user.id, title="Test", text="Body")
    assert ad.id is not None
    assert ad.title == "Test"


@pytest.mark.asyncio
async def test_get_by_id(ad_repo, user):
    ad = await ad_repo.create(user_id=user.id, title="Test", text="Body")
    found = await ad_repo.get_by_id(ad.id)
    assert found is not None
    assert found.id == ad.id


@pytest.mark.asyncio
async def test_get_by_id_returns_none(ad_repo):
    found = await ad_repo.get_by_id(9999)
    assert found is None


@pytest.mark.asyncio
async def test_get_by_id_and_user(ad_repo, user):
    ad = await ad_repo.create(user_id=user.id, title="Test", text="Body")
    found = await ad_repo.get_by_id_and_user(ad.id, user.id)
    assert found is not None
    not_found = await ad_repo.get_by_id_and_user(ad.id, 9999)
    assert not_found is None


@pytest.mark.asyncio
async def test_list_by_user(ad_repo, user):
    await ad_repo.create(user_id=user.id, title="A1", text="Body")
    await ad_repo.create(user_id=user.id, title="A2", text="Body")
    items = await ad_repo.list_by_user(user.id)
    assert len(items) == 2


@pytest.mark.asyncio
async def test_update(ad_repo, user):
    ad = await ad_repo.create(user_id=user.id, title="Old", text="Body")
    updated = await ad_repo.update(ad, title="New")
    assert updated.title == "New"


@pytest.mark.asyncio
async def test_delete(ad_repo, user):
    ad = await ad_repo.create(user_id=user.id, title="Del", text="Body")
    await ad_repo.delete(ad)
    assert await ad_repo.get_by_id(ad.id) is None


@pytest.mark.asyncio
async def test_count_by_user(ad_repo, user):
    await ad_repo.create(user_id=user.id, title="A1", text="Body")
    await ad_repo.create(user_id=user.id, title="A2", text="Body")
    assert await ad_repo.count_by_user(user.id) == 2

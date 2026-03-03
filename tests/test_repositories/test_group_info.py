import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_info import GroupInfo
from app.repositories.group_info import GroupInfoRepository


@pytest_asyncio.fixture
async def repo(db_session: AsyncSession) -> GroupInfoRepository:
    return GroupInfoRepository(db_session)


@pytest.mark.asyncio
async def test_create_and_get(repo: GroupInfoRepository):
    item = await repo.create(
        messenger_type="tg_user",
        external_id="-100123",
        name="Test Group",
        member_count=42,
    )
    assert item.id is not None
    assert item.name == "Test Group"
    assert item.member_count == 42

    found = await repo.get_by_id(item.id)
    assert found is not None
    assert found.external_id == "-100123"


@pytest.mark.asyncio
async def test_upsert_insert(repo: GroupInfoRepository):
    item = await repo.upsert(
        messenger_type="wa",
        external_id="120363@g.us",
        name="WA Group",
        member_count=10,
    )
    assert item.id is not None
    assert item.name == "WA Group"


@pytest.mark.asyncio
async def test_upsert_update(repo: GroupInfoRepository):
    await repo.create(
        messenger_type="tg_user",
        external_id="-100999",
        name="Old Name",
        member_count=5,
    )
    updated = await repo.upsert(
        messenger_type="tg_user",
        external_id="-100999",
        name="New Name",
        member_count=15,
    )
    assert updated.name == "New Name"
    assert updated.member_count == 15


@pytest.mark.asyncio
async def test_search_by_name(repo: GroupInfoRepository):
    await repo.create(messenger_type="tg_user", external_id="-1001", name="Alpha Group")
    await repo.create(messenger_type="tg_user", external_id="-1002", name="Beta Group")
    await repo.create(messenger_type="wa", external_id="300@g.us", name="Gamma Chat")

    items, total = await repo.search(q="Group")
    assert total == 2
    assert len(items) == 2


@pytest.mark.asyncio
async def test_search_by_messenger_type(repo: GroupInfoRepository):
    await repo.create(messenger_type="tg_user", external_id="-1001", name="TG Group")
    await repo.create(messenger_type="wa", external_id="300@g.us", name="WA Group")

    items, total = await repo.search(messenger_type="wa")
    assert total == 1
    assert items[0].messenger_type == "wa"


@pytest.mark.asyncio
async def test_count_by_type(repo: GroupInfoRepository):
    await repo.create(messenger_type="tg_user", external_id="-1001", name="TG1")
    await repo.create(messenger_type="tg_user", external_id="-1002", name="TG2")
    await repo.create(messenger_type="wa", external_id="300@g.us", name="WA1")

    counts = await repo.count_by_type()
    assert counts["tg_user"] == 2
    assert counts["wa"] == 1


@pytest.mark.asyncio
async def test_list_all_keys(repo: GroupInfoRepository):
    await repo.create(messenger_type="tg_user", external_id="-1001", name="TG1")
    await repo.create(messenger_type="wa", external_id="300@g.us", name="WA1")

    keys = await repo.list_all_keys()
    assert ("tg_user", "-1001") in keys
    assert ("wa", "300@g.us") in keys
    assert len(keys) == 2

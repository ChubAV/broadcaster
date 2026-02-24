import pytest
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.auth_service import hash_password


@pytest.mark.asyncio
async def test_get_all_users(db_session):
    repo = UserRepository(db_session)
    u1 = User(email="a@test.com", password_hash=hash_password("p"), name="A")
    u2 = User(email="b@test.com", password_hash=hash_password("p"), name="B")
    db_session.add_all([u1, u2])
    await db_session.commit()

    users = await repo.get_all_users()
    assert len(users) == 2


@pytest.mark.asyncio
async def test_search_users(db_session):
    repo = UserRepository(db_session)
    u1 = User(email="alice@test.com", password_hash=hash_password("p"), name="Alice")
    u2 = User(email="bob@test.com", password_hash=hash_password("p"), name="Bob")
    db_session.add_all([u1, u2])
    await db_session.commit()

    results = await repo.search_users("alice")
    assert len(results) == 1
    assert results[0].email == "alice@test.com"

    results = await repo.search_users("bob")
    assert len(results) == 1
    assert results[0].name == "Bob"


@pytest.mark.asyncio
async def test_count_all(db_session):
    repo = UserRepository(db_session)
    u1 = User(email="a@test.com", password_hash=hash_password("p"), name="A")
    db_session.add(u1)
    await db_session.commit()

    count = await repo.count_all()
    assert count == 1

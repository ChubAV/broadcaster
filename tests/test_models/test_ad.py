import pytest
from app.models.user import User
from app.models.ad import Ad


@pytest.mark.asyncio
async def test_create_ad(db_session):
    user = User(
        email="ad@example.com",
        password_hash="hashed",
        name="Ad User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    ad = Ad(
        user_id=user.id,
        title="Summer Sale",
        text="Big discounts on all products!",
        images=["image1.jpg", "image2.jpg"],
        is_active=True,
    )
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)

    assert ad.id is not None
    assert ad.user_id == user.id
    assert ad.title == "Summer Sale"
    assert ad.text == "Big discounts on all products!"
    assert ad.images == ["image1.jpg", "image2.jpg"]
    assert ad.is_active is True
    assert ad.created_at is not None


@pytest.mark.asyncio
async def test_ad_default_values(db_session):
    user = User(
        email="ad_default@example.com",
        password_hash="hashed",
        name="Default Ad User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    ad = Ad(
        user_id=user.id,
        title="Basic Ad",
        text="Some text",
    )
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)

    assert ad.images == []
    assert ad.is_active is True


@pytest.mark.asyncio
async def test_ad_with_empty_images(db_session):
    user = User(
        email="ad_empty@example.com",
        password_hash="hashed",
        name="Empty Images User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    ad = Ad(
        user_id=user.id,
        title="No Image Ad",
        text="Text only ad",
        images=[],
    )
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)

    assert ad.images == []

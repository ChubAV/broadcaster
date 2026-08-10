import pytest

from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED
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
        status=AD_STATUS_PUBLISHED,
    )
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)

    assert ad.id is not None
    assert ad.user_id == user.id
    assert ad.title == "Summer Sale"
    assert ad.text == "Big discounts on all products!"
    assert ad.images == ["image1.jpg", "image2.jpg"]
    assert ad.status == AD_STATUS_PUBLISHED
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
    # D-02: умолчание — «опубликовано». Черновик появляется только явным
    # действием пользователя; иначе созданное объявление молча перестало бы
    # отправляться по уже существующим расписаниям.
    assert ad.status == AD_STATUS_PUBLISHED


@pytest.mark.asyncio
async def test_ad_can_be_draft(db_session):
    user = User(
        email="ad_draft@example.com",
        password_hash="hashed",
        name="Draft Ad User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    ad = Ad(
        user_id=user.id,
        title="Draft Ad",
        text="Some text",
        status=AD_STATUS_DRAFT,
    )
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)

    assert ad.status == AD_STATUS_DRAFT


@pytest.mark.asyncio
async def test_ad_has_no_legacy_activity_flag():
    """Старый булев флаг снят вместе с колонкой (ревизия 0013).

    Проверка на модели, а не грепом: атрибут, оставшийся объявленным, вернул бы
    `/api/ads` в исходное состояние, а миграция уже сняла колонку под ним.
    """
    assert not hasattr(Ad, "is_active")
    assert "is_active" not in Ad.__table__.columns


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

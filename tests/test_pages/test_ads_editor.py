"""Рендер-тесты редактора объявления — точка опоры ADS-04 и ADS-06 (D-21).

До этого файла `/ads/new` и `/ads/{id}/edit` не рендерились НИ ОДНИМ тестом
суиты: шаблонные глобалы изображений в `app/pages/common.py` вызывали
`get_settings()` в обход подмены зависимостей, поэтому страница рендерилась
только при наличии `.env` рядом с процессом. Планы 02-04 и 02-05 переделывают
именно этот экран — без рендер-теста их правки нечем удержать (T-02-03).

Эталон формы взят из `tests/test_pages/test_responsive_markup.py`: посев через
`db_session`, запрос через `authed_client`, утверждения на РЕАЛЬНЫХ строках
данных. Утверждения на один только код ответа тут бесполезны: потеря контекста
макроса даёт 200 с пустой страницей.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.models.ad import Ad
from app.models.user import User


async def _user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_ad(
    db: AsyncSession,
    title: str = "Осенний завоз",
    images: list[str] | None = None,
    user_id: int | None = None,
) -> Ad:
    if user_id is None:
        user_id = (await _user(db)).id
    ad = Ad(
        user_id=user_id,
        title=title,
        text="Полный текст объявления про осенний завоз",
        images=images or [],
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


# --- ADS-04: экран создания рендерится --------------------------------------


@pytest.mark.asyncio
async def test_ads_new_renders(authed_client: AsyncClient):
    """`GET /ads/new` отдаёт 200 и форму с полями названия и текста (D-21)."""
    response = await authed_client.get("/ads/new")

    assert response.status_code == 200
    html = response.text
    assert 'name="title"' in html
    assert 'name="text"' in html
    # Форма создания уходит на свой маршрут, а не на редактирование.
    assert 'action="/ads/new"' in html


@pytest.mark.asyncio
async def test_ads_edit_renders_own_ad(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """`GET /ads/{id}/edit` отдаёт 200 и РЕАЛЬНЫЕ данные объявления."""
    ad = await _seed_ad(db_session, title="Уникальный заголовок редактора")

    response = await authed_client.get(f"/ads/{ad.id}/edit")

    assert response.status_code == 200
    html = response.text
    assert "Уникальный заголовок редактора" in html
    assert "Полный текст объявления про осенний завоз" in html
    assert f'action="/ads/{ad.id}/edit"' in html


# --- T-02-04: владение объявлением ------------------------------------------


@pytest.mark.asyncio
async def test_ads_edit_foreign_ad_is_not_served(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Чужое объявление не открывается: редирект на список, а не 200.

    Закрепляет существующую проверку `Ad.user_id == user.id`
    (`app/pages/ads.py:151-156`) как регрессионный контракт — планы 02-04 и
    02-05 переписывают этот обработчик.
    """
    owner_id = (await _user(db_session)).id
    foreign = await _seed_ad(
        db_session, title="Чужое объявление", user_id=owner_id + 1000
    )

    response = await authed_client.get(
        f"/ads/{foreign.id}/edit", follow_redirects=False
    )

    assert response.status_code != 200
    assert response.status_code == 302
    assert response.headers["location"] == "/ads"


# --- T-02-02: базовый URL изображений берётся из настроек приложения --------


@pytest_asyncio.fixture
async def cdn_settings():
    """Настройки с узнаваемым S3-хостом, которого нет ни в одном `.env`."""
    return Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret-key",
        s3_public_url="https://cdn.bound-to-app-settings.test/bucket",
    )


@pytest_asyncio.fixture
async def cdn_client(db_session, cdn_settings):
    app = create_app(settings=cdn_settings)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: cdn_settings
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post(
            "/api/auth/register",
            json={
                "email": "testuser@test.com",
                "password": "testpass123",
                "name": "Test User",
            },
        )
        await c.post(
            "/login",
            data={"email": "testuser@test.com", "password": "testpass123"},
            follow_redirects=False,
        )
        yield c


@pytest.mark.asyncio
async def test_image_base_url_comes_from_app_settings(
    cdn_client: AsyncClient, db_session: AsyncSession
):
    """Ссылка на изображение строится из настроек ПРИЛОЖЕНИЯ, а не окружения.

    Ровно этот дефект (D-21): глобалы `get_image_url` / `s3_public_url` брали
    `get_settings()`, поэтому подмена зависимости `create_app(settings=...)` их
    не касалась, а базовый URL приезжал из `.env` рабочего каталога.
    """
    await _seed_ad(db_session, title="С картинкой", images=["u1/photo.jpg"])

    listing = await cdn_client.get("/ads")
    assert listing.status_code == 200
    assert (
        "https://cdn.bound-to-app-settings.test/bucket/u1/photo.jpg"
        in listing.text
    )


@pytest.mark.asyncio
async def test_editor_s3_public_url_global_comes_from_app_settings(
    cdn_client: AsyncClient, db_session: AsyncSession
):
    """Тот же контракт для глобала `s3_public_url()` в шаблоне редактора."""
    ad = await _seed_ad(db_session, title="С картинкой", images=["u1/photo.jpg"])

    response = await cdn_client.get(f"/ads/{ad.id}/edit")

    assert response.status_code == 200
    assert "https://cdn.bound-to-app-settings.test/bucket" in response.text

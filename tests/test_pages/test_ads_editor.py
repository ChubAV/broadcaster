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

from urllib.parse import urlencode
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.models.ad import Ad
from app.models.user import User

# Форма ключа вложения — источник правды `app/routes/uploads.py`:
# `{user_id}/{32 hex}_{имя}`. Свой ключ строится тем же способом, что в
# tests/test_pages/test_ads_image_ownership.py: значение обязано пройти
# `own_image_keys` из плана 02-02, иначе тест меряет отказ, а не поведение.
FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}
HX_HEADERS = {**FORM_HEADERS, "HX-Request": "true"}


def image_key(user_id: int, name: str = "photo.jpg") -> str:
    return f"{user_id}/{uuid4().hex}_{name}"


def form_body(
    title: str = "Заголовок",
    text: str = "Текст",
    images: list[str] | None = None,
    extra: list[tuple[str, str]] | None = None,
) -> str:
    fields: list[tuple[str, str]] = [("title", title), ("text", text)]
    fields += [("images", value) for value in images or []]
    fields += extra or []
    return urlencode(fields)


async def _ads_count(db: AsyncSession, user_id: int) -> int:
    return int(
        await db.scalar(select(func.count()).select_from(Ad).where(Ad.user_id == user_id))
        or 0
    )


async def _only_ad(db: AsyncSession, user_id: int) -> Ad:
    db.expire_all()
    return (
        await db.execute(select(Ad).where(Ad.user_id == user_id))
    ).scalars().one()


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


# --- План 02-04, ADS-04: черновик создаётся автосохранением ------------------
#
# Ключевое свойство раздела — сохранение НЕ перерисовывает форму. Проверить это
# можно только по телу ответа: страница с перерисованной формой тоже отдаёт 200,
# и пользователь узнаёт о поломке, лишь потеряв каретку на середине текста.


@pytest.mark.asyncio
async def test_ads_new_page_creates_no_row(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-03: заход на `/ads/new` не создаёт запись.

    Иначе каждое случайное открытие раздела оставляло бы в списке пустое
    объявление, и пользователь чистил бы за интерфейсом.
    """
    owner_id = (await _user(db_session)).id
    before = await _ads_count(db_session, owner_id)

    response = await authed_client.get("/ads/new")

    assert response.status_code == 200
    assert await _ads_count(db_session, owner_id) == before


@pytest.mark.asyncio
async def test_autosave_creates_draft_and_pushes_edit_url(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-03: первое автосохранение создаёт черновик и подменяет адрес."""
    owner_id = (await _user(db_session)).id

    response = await authed_client.post(
        "/ads/new",
        content=form_body(title="Черновик из автосохранения", text="Набранный текст"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    ad = await _only_ad(db_session, owner_id)
    assert ad.status == AD_STATUS_DRAFT
    assert response.headers.get("HX-Push-Url") == f"/ads/{ad.id}/edit"


@pytest.mark.asyncio
async def test_autosave_response_carries_no_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Форма при автосохранении НЕ перерисовывается.

    Любая подмена, накрывающая поле ввода, сбрасывает каретку и выделение:
    пользователь физически не сможет набрать длинный текст.
    """
    response = await authed_client.post(
        "/ads/new",
        content=form_body(),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert 'id="ad-form"' not in response.text
    assert "<form" not in response.text


@pytest.mark.asyncio
async def test_autosave_response_updates_three_blocks(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-06: один ответ обновляет предпросмотр, сводку и индикатор."""
    response = await authed_client.post(
        "/ads/new",
        content=form_body(),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    html = response.text
    assert 'id="ad-preview"' in html
    assert 'id="ad-summary"' in html
    assert 'id="autosave-indicator"' in html
    assert "hx-swap-oob" in html


@pytest.mark.asyncio
async def test_plain_post_without_htmx_redirects(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-09: базовый путь без JavaScript отвечает редиректом, а не фрагментом."""
    ad = await _seed_ad(db_session, title="Объявление без JavaScript")

    response = await authed_client.post(
        f"/ads/{ad.id}/edit",
        content=form_body(title="Правка без JavaScript", text="Текст"),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302


@pytest.mark.asyncio
async def test_repeated_autosave_updates_the_same_ad(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Повторное автосохранение обновляет первую запись, а не плодит вторую."""
    owner_id = (await _user(db_session)).id

    first = await authed_client.post(
        "/ads/new",
        content=form_body(title="Первый вариант", text="Текст"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )
    assert first.status_code == 200
    ad_id = (await _only_ad(db_session, owner_id)).id

    second = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(title="Второй вариант", text="Текст"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert second.status_code == 200
    assert await _ads_count(db_session, owner_id) == 1
    assert (await _only_ad(db_session, owner_id)).title == "Второй вариант"


@pytest.mark.asyncio
async def test_preview_renders_stored_text(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ADS-06: предпросмотр показывает записанный текст, а не пустую рамку."""
    response = await authed_client.post(
        "/ads/new",
        content=form_body(title="Заголовок", text="Уникальный текст предпросмотра"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert "Уникальный текст предпросмотра" in response.text


@pytest.mark.asyncio
async def test_preview_never_shows_rejected_attachments(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """D-10: предпросмотр рендерится из БАЗЫ, а не из тела запроса.

    Сервер отклоняет сохранение с числом вложений сверх лимита (D-13). Превью,
    собранное из формы, показало бы отклонённое — то есть пообещало бы отправку
    того, чего в базе нет.
    """
    owner_id = (await _user(db_session)).id
    kept = image_key(owner_id, "kept.jpg")
    ad = await _seed_ad(db_session, title="С вложением", images=[kept])
    ad_id = ad.id
    rejected = [
        image_key(owner_id, f"over{i}.jpg")
        for i in range(test_settings.max_images_per_ad + 1)
    ]

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(title="Слишком много", text="Текст", images=rejected),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    for value in rejected:
        assert value not in response.text
    assert "autosave--error" in response.text
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == [kept]
    assert stored.title == "С вложением"


@pytest.mark.asyncio
async def test_remove_image_drops_one_key_and_keeps_order(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ADS-05, D-12: убирание вложения снимает ровно один ключ и держит порядок.

    Именованная кнопка отправки — путь БЕЗ Alpine: она обязана работать сама по
    себе, иначе без скрипта вложение убрать нечем.
    """
    owner_id = (await _user(db_session)).id
    keys = [image_key(owner_id, f"p{i}.jpg") for i in range(3)]
    ad_id = (await _seed_ad(db_session, title="Три вложения", images=keys)).id

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(
            title="Три вложения",
            text="Текст",
            images=keys,
            extra=[("remove_image", keys[1])],
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == [keys[0], keys[2]]


@pytest.mark.asyncio
async def test_foreign_ad_is_not_autosavable(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-02-21: чужое объявление недоступно на автосохранение.

    Владение проверяется внутри запроса, а не последующим `if`, поэтому «нет
    такой записи» и «запись чужая» дают один исход.
    """
    owner_id = (await _user(db_session)).id
    foreign = await _seed_ad(
        db_session, title="Чужое объявление", user_id=owner_id + 1000
    )
    foreign_id = foreign.id

    response = await authed_client.post(
        f"/ads/{foreign_id}/edit",
        content=form_body(title="Захват", text="Захват"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code != 200
    db_session.expire_all()
    stored = (
        await db_session.execute(select(Ad).where(Ad.id == foreign_id))
    ).scalar_one()
    assert stored.title == "Чужое объявление"


@pytest.mark.asyncio
async def test_explicit_save_publishes_autosave_does_not(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-04: публикует явное «Сохранить», а не эвристика «текст непустой».

    Отдельной кнопки публикации в макете нет, поэтому состояние различается по
    признаку явной отправки. Эвристика опубликовала бы объявление, которое
    пользователь только начал набирать.
    """
    owner_id = (await _user(db_session)).id

    await authed_client.post(
        "/ads/new",
        content=form_body(title="Черновик", text="Текст"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )
    ad_id = (await _only_ad(db_session, owner_id)).id
    assert (await _only_ad(db_session, owner_id)).status == AD_STATUS_DRAFT

    await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(title="Черновик", text="Текст", extra=[("save", "1")]),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert (await _only_ad(db_session, owner_id)).status == AD_STATUS_PUBLISHED

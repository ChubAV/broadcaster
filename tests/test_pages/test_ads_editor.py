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


async def _stranger(db: AsyncSession) -> User:
    """Второй пользователь — владелец «чужого» объявления.

    Форма посева взята из tests/test_pages/test_schedule_ownership.py: чужая
    запись обязана принадлежать НАСТОЯЩЕМУ пользователю, иначе отказ мог бы
    объясняться отсутствием владельца, а не проверкой владения.
    """
    user = User(email="stranger@test.com", password_hash="x", name="Stranger")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _attr_value(html: str, anchor: str, attr: str) -> str:
    """Значение атрибута элемента, опознанного по подстроке `anchor`.

    Разбор строкой — тот же приём, что уже применяют этот файл и
    tests/test_pages/test_responsive_markup.py: новой зависимости разбора HTML
    ради одного скрытого поля не заводится. Отсутствие элемента или атрибута
    поднимает ValueError — то есть тест падает, а не молча меряет пустоту.
    """
    start = html.index(anchor)
    opened = html.index(f'{attr}="', start) + len(attr) + 2
    return html[opened : html.index('"', opened)]


def _ad_id_from(html: str) -> str:
    """Идентификатор объявления, который СЕРВЕР вернул в ответе автосохранения.

    Значение приезжает внеполосно скрытым полем `#ad-id-field` и подменяет то
    же поле внутри никогда не перерисовываемой формы. Тест обязан брать
    следующий адрес и следующий идентификатор ИЗ ОТВЕТА, а не назначать их
    рукой: назначенный рукой идентификатор проверяет замысел теста, а не
    контракт, который получает браузер (02-REVIEW.md, IN-06).
    """
    return _attr_value(html, 'id="ad-id-field"', "value")


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


# --- План 02-08, CR-01: повторное автосохранение адресуется в ту же запись ---
#
# Прежний тест этого места (`test_repeated_autosave_updates_the_same_ad`) слал
# второй запрос на `/ads/{id}/edit` — на адрес, который форма НЕ несёт и на
# который браузер не уходит: `hx-post` неизменяем, а `hx-swap="none"` гарантирует,
# что форма никогда не перерисуется. Тест утверждал переписывание адреса, которого
# никто не выполняет, и был зелёным ровно тогда, когда пользователь терял правки
# (02-REVIEW.md, IN-06). Он удалён; ниже адрес второго запроса берётся из ответа.


@pytest.mark.asyncio
async def test_repeated_autosave_posts_to_the_url_the_form_carries(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Второе автосохранение на АДРЕС ФОРМЫ обновляет первый черновик.

    Ключевое отличие от удалённого теста: адрес второго запроса не назначается,
    а сверяется с атрибутом `hx-post`, который сервер отдал в разметке формы.
    Пока эти два адреса совпадают, тест меряет то же, что делает браузер.
    """
    owner_id = (await _user(db_session)).id

    page = await authed_client.get("/ads/new")
    assert page.status_code == 200
    assert _attr_value(page.text, 'id="ad-form"', "hx-post") == "/ads/new"

    first = await authed_client.post(
        "/ads/new",
        content=form_body(title="Первый вариант", text="Текст"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )
    assert first.status_code == 200
    ad_id = _ad_id_from(first.text)
    assert ad_id, "ответ автосохранения не назвал созданную запись"

    second = await authed_client.post(
        "/ads/new",
        content=form_body(
            title="Второй вариант", text="Текст", extra=[("ad_id", ad_id)]
        ),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert second.status_code == 200
    assert await _ads_count(db_session, owner_id) == 1
    stored = await _only_ad(db_session, owner_id)
    assert stored.title == "Второй вариант"
    assert stored.status == AD_STATUS_DRAFT, "автосохранение изменило состояние"


@pytest.mark.asyncio
async def test_creation_path_keeps_text_and_attachment_in_one_ad(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ADS-05, SC-2: текст и вложение с пути СОЗДАНИЯ лежат в ОДНОМ объявлении.

    Загрузка файла поднимает событие `change`, htmx уходит на тот же `/ads/new`,
    и до этого плана вложение приезжало во ВТОРУЮ запись — набранный текст
    оставался в первой.
    """
    owner_id = (await _user(db_session)).id

    first = await authed_client.post(
        "/ads/new",
        content=form_body(title="Черновик с вложением", text="Набранный текст"),
        headers=HX_HEADERS,
        follow_redirects=False,
    )
    assert first.status_code == 200
    ad_id = _ad_id_from(first.text)
    key = image_key(owner_id, "photo.jpg")

    second = await authed_client.post(
        "/ads/new",
        content=form_body(
            title="Черновик с вложением",
            text="Набранный текст",
            images=[key],
            extra=[("ad_id", ad_id)],
        ),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert second.status_code == 200
    assert await _ads_count(db_session, owner_id) == 1
    stored = await _only_ad(db_session, owner_id)
    assert stored.text == "Набранный текст"
    assert stored.images == [key]


@pytest.mark.asyncio
async def test_body_ad_id_from_another_user_is_refused(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-02G-01: идентификатор из ТЕЛА запроса не открывает чужую запись.

    Этот план вводит в тело `/ads/new` новый идентификатор объекта, то есть
    расширяет границу доверия. Неподтверждённое владение обязано давать отказ —
    ни записи в чужую строку, ни создания нового черновика взамен.
    """
    owner_id = (await _user(db_session)).id
    # Идентификаторы снимаются СРАЗУ: каждый последующий commit сбрасывает
    # загруженные атрибуты, и обращение к ним из синхронного кода теста ушло бы
    # в ленивую подгрузку вне greenlet-а.
    stranger_id = (await _stranger(db_session)).id
    foreign_id = (
        await _seed_ad(db_session, title="Чужое объявление", user_id=stranger_id)
    ).id
    before = await _ads_count(db_session, owner_id)

    await authed_client.post(
        "/ads/new",
        content=form_body(
            title="Захват", text="Захват", extra=[("ad_id", str(foreign_id))]
        ),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    db_session.expire_all()
    stored = (
        await db_session.execute(select(Ad).where(Ad.id == foreign_id))
    ).scalar_one()
    assert stored.title == "Чужое объявление"
    assert await _ads_count(db_session, stranger_id) == 1
    assert await _ads_count(db_session, owner_id) == before


@pytest.mark.asyncio
async def test_plain_post_without_htmx_still_redirects(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-09: базовый путь БЕЗ JavaScript на `/ads/new` по-прежнему отвечает 302.

    Регрессия к задаче 2: маршрутизация тела запроса на обновление не имеет
    права превратить обычную отправку формы в фрагмент.
    """
    response = await authed_client.post(
        "/ads/new",
        content=form_body(title="Без JavaScript", text="Текст"),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302


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
async def test_preview_lists_every_attachment_in_send_order(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ADS-06, UI-SPEC E9 `zero-one-many`: предпросмотр показывает ВСЕ вложения.

    Макет рисует ровно один медиаблок, раскладка 2…10 вложений им не задана.
    Дефолт контракта — переносящаяся строка миниатюр в порядке отправки, то есть
    в порядке `Ad.images`. Порядок проверяется ПОЗИЦИЯМИ подстрок, а не целым
    блоком разметки: разметка миниатюры может измениться, порядок — нет.
    """
    owner_id = (await _user(db_session)).id
    keys = [image_key(owner_id, f"p{i}.jpg") for i in range(3)]
    ad_id = (await _seed_ad(db_session, title="Три вложения", images=keys)).id

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(title="Три вложения", text="Текст", images=keys),
        headers=HX_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 200
    html = response.text
    # index() поднимает ValueError на отсутствующем ключе: «показаны все три» и
    # «показаны в этом порядке» проверяются одним выражением.
    positions = [html.index(key) for key in keys]
    assert positions == sorted(positions), "порядок миниатюр разошёлся с Ad.images"
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == keys


@pytest.mark.asyncio
async def test_removing_an_absent_key_changes_nothing(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ADS-05: повторное «убрать вложение» на уже убранный ключ — без эффекта.

    Кнопка убирания живёт в форме автосохранения, и повторная отправка того же
    тела реальна: дебаунс мог отправить запрос дважды. Отбрасывание «лишнего»
    ключа или ошибка здесь одинаково испортили бы список.
    """
    owner_id = (await _user(db_session)).id
    keys = [image_key(owner_id, f"p{i}.jpg") for i in range(2)]
    absent = image_key(owner_id, "already-gone.jpg")
    ad_id = (await _seed_ad(db_session, title="Два вложения", images=keys)).id

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=form_body(
            title="Два вложения",
            text="Текст",
            images=keys,
            extra=[("remove_image", absent)],
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == keys


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


# --- План 02-04, Задача 3: разметка редактора --------------------------------
#
# Утверждения на РЕНДЕР, а не на исходник шаблона: контракт с обработчиком и
# порядок чтения проверяются там, где их видит браузер. Проверки исходного
# текста живут в tests/test_templates/test_ads_form_security.py и говорят о
# другом — о СПОСОБЕ сборки клиентской разметки.


@pytest.mark.asyncio
async def test_editor_has_two_column_containers(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Редактор собран на сетке раздела 8, а не на своей вёрстке."""
    ad = await _seed_ad(db_session, title="Объявление с сеткой")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert "data-editor" in html
    assert "data-editor-side" in html


@pytest.mark.asyncio
async def test_editor_form_carries_autosave_and_stays_a_real_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Автосохранение — УСИЛЕНИЕ поверх настоящей формы, а не замена ей.

    Потеря `method`/`action` не роняет страницу: она молча лишает пользователя
    без JavaScript единственного способа сохранить объявление (D-09).
    """
    ad = await _seed_ad(db_session, title="Объявление с автосохранением")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert 'id="ad-form"' in html
    assert 'method="post"' in html
    assert f'action="/ads/{ad.id}/edit"' in html
    assert f'hx-post="/ads/{ad.id}/edit"' in html
    assert "delay:2s" in html, "дебаунс автосохранения потерян"
    assert 'hx-sync="this:replace"' in html, "отмена устаревшего запроса потеряна"
    assert 'hx-swap="none"' in html, "форма стала целью подмены — каретка потеряется"


@pytest.mark.asyncio
async def test_editor_shows_only_add_tile_without_attachments(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """0 вложений — только плитка добавления, не пустая рамка (UI-SPEC E3)."""
    ad = await _seed_ad(db_session, title="Без вложений", images=[])

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert "media-tile--add" in html
    # Именно РАЗМЕТКА: имя класса встречается ещё и в узловой сборке плиток,
    # которая живёт в этом же файле и никуда не выносится.
    assert 'class="media-tile__remove"' not in html


@pytest.mark.asyncio
async def test_editor_hides_add_tile_at_the_limit(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """На лимите плитка добавления скрыта — она удобство, а не точка принуждения."""
    owner_id = (await _user(db_session)).id
    keys = [
        image_key(owner_id, f"p{i}.jpg")
        for i in range(test_settings.max_images_per_ad)
    ]
    ad = await _seed_ad(db_session, title="Полный комплект", images=keys)

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert "media-tile--add" in html, "плитка добавления удалена, а не скрыта"
    assert "media-tile--add hidden" in html or "media-tile--add\" hidden" in html


@pytest.mark.asyncio
async def test_attachment_remove_is_a_named_submit_inside_the_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Путь убирания вложения переживает отсутствие Alpine и htmx.

    Кнопка `type="button"` вместо именованной кнопки отправки лишила бы
    пользователя без скрипта единственного способа убрать вложение.
    """
    owner_id = (await _user(db_session)).id
    ad = await _seed_ad(
        db_session, title="С вложением", images=[image_key(owner_id, "p0.jpg")]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert 'name="remove_image"' in html
    assert 'aria-label="Убрать вложение"' in html
    assert 'type="submit"' in html


@pytest.mark.asyncio
async def test_editor_delete_form_degrades_without_alpine(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Удаление объявления — настоящая форма, перехват навешен на неё саму."""
    ad = await _seed_ad(db_session, title="Удаляемое объявление")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert f'action="/ads/{ad.id}/delete"' in html
    assert f"modal-open-ad-del-{ad.id}" in html
    assert 'role="dialog"' in html


@pytest.mark.asyncio
async def test_editor_markup_order_is_the_reading_order(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """На ≤900px колонки схлопываются и порядок разметки становится порядком чтения.

    Поэтому предпросмотр обязан стоять ПОСЛЕ составителя: иначе на телефоне
    пользователь читает результат раньше, чем видит, где его набирать.

    Позиции берутся по подписи РАЗДЕЛА (`card__title`), а не по слову: слово
    «Расписания» есть и в боковом меню шелла, которое стоит выше по разметке.
    """
    ad = await _seed_ad(db_session, title="Порядок разметки")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    content = html.index('card__title">Содержание<')
    schedules = html.index('card__title">Расписания<')
    preview = html.index('card__title">Предпросмотр<')

    assert content < schedules < preview


@pytest.mark.asyncio
async def test_editor_renders_preview_summary_and_indicator_anchors(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Якоря внеполосной подмены есть на первичной отрисовке.

    Без них ответ автосохранения приходит в никуда: страница остаётся живой, а
    предпросмотр молча перестаёт обновляться.
    """
    ad = await _seed_ad(db_session, title="Якоря подмены")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert 'id="ad-preview"' in html
    assert 'id="ad-summary"' in html
    assert 'id="autosave-indicator"' in html


@pytest.mark.asyncio
async def test_editor_schedules_section_is_outside_the_ad_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Секция расписаний — СОСЕД формы объявления, а не её содержимое.

    Вложенные формы браузер молча отбрасывает: в плане 02-05 кнопки карточек
    расписаний перестали бы работать и с JavaScript, и без него.
    """
    ad = await _seed_ad(db_session, title="Место под расписания")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    form_start = html.index('id="ad-form"')
    form_end = html.index("</form>", form_start)
    schedules = html.index('card__title">Расписания<')

    assert schedules > form_end, "секция расписаний оказалась внутри формы объявления"


@pytest.mark.asyncio
async def test_editor_counter_is_server_rendered(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Счётчик длины приходит с сервера и не блокирует сохранение."""
    ad = await _seed_ad(db_session, title="Счётчик")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert 'id="text-counter"' in html
    assert "4096" in html, "предел длины не отрисован"
    assert "maxlength" not in html, "счётчик не имеет права обрезать текст"

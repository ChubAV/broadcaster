"""WR-01 / T-10-04 и D-13: владение ключом вложения и серверный лимит.

Список ключей вложений приходит скрытыми полями формы и полностью управляем
клиентом. Без проверки владения объявление можно сохранить с ключом из чужого
префикса того же хранилища — и чужое изображение начнёт отдаваться в карточке,
истории и админке. Лимит числа вложений до этого плана существовал только в
браузере и обходился прямым POST.

Отказ здесь именно отказ, а не молчаливое отбрасывание значения: отбрасывание
превратило бы попытку подмены в «успешное сохранение без картинки» и скрыло бы
её от пользователя.
"""

from urllib.parse import urlencode
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.user import User

FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}


def image_key(user_id: int, name: str = "photo.jpg") -> str:
    """Ключ вложения ровно в той форме, которую выдаёт `/api/uploads/image`.

    Источник формы — `app/routes/uploads.py`: `{user_id}/{uuid4().hex}_{имя}`.
    """
    return f"{user_id}/{uuid4().hex}_{name}"


@pytest_asyncio.fixture
async def owner(db_session: AsyncSession) -> User:
    """Пользователь, под которым ходит `authed_client`."""
    result = await db_session.execute(
        select(User).where(User.email == "testuser@test.com")
    )
    return result.scalar_one()


async def _seed_ad(db_session: AsyncSession, user_id: int, images: list[str]) -> Ad:
    ad = Ad(user_id=user_id, title="Своё объявление", text="Текст", images=images)
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)
    return ad


def _form(images: list[str], title: str = "Объявление"):
    fields = [("title", title), ("text", "Текст объявления")]
    fields += [("images", value) for value in images]
    return urlencode(fields)


async def _ads_of(db_session: AsyncSession, user_id: int) -> list[Ad]:
    result = await db_session.execute(select(Ad).where(Ad.user_id == user_id))
    return list(result.scalars().all())


# --- Создание -----------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "hostile",
    [
        pytest.param("{foreign}", id="foreign-prefix"),
        pytest.param("http://evil.example.com/steal.png", id="external-url"),
        pytest.param("https://cdn.example.com/other/img.png", id="external-https"),
        pytest.param("../{own_bare}", id="traversal"),
        pytest.param("{own_bare}", id="no-prefix"),
        pytest.param("999/nothex_photo.jpg", id="malformed-token"),
    ],
)
async def test_ads_create_rejects_key_outside_owner_prefix(
    hostile, authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Ключ вне префикса владельца или не той формы — отказ, объявление не создано."""
    value = hostile.format(
        foreign=image_key(owner.id + 1000),
        own_bare=image_key(owner.id).split("/", 1)[1],
    )

    response = await authed_client.post(
        "/ads/new",
        content=_form([value]),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert await _ads_of(db_session, owner.id) == []


@pytest.mark.asyncio
async def test_ads_create_accepts_own_keys_and_preserves_order(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    keys = [image_key(owner.id, f"p{i}.jpg") for i in range(3)]

    response = await authed_client.post(
        "/ads/new",
        content=_form(keys),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    ads = await _ads_of(db_session, owner.id)
    assert len(ads) == 1
    assert ads[0].images == keys


# --- Обновление ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_ads_update_rejects_foreign_key_and_leaves_ad_untouched(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Отказ на обновлении не должен оставлять объявление частично изменённым."""
    original = [image_key(owner.id, "original.jpg")]
    ad_id = (await _seed_ad(db_session, owner.id, original)).id

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=_form([image_key(owner.id + 1000)], title="Подменённое"),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 400
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == original
    assert stored.title == "Своё объявление"


@pytest.mark.asyncio
async def test_ads_update_accepts_own_keys(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    ad_id = (
        await _seed_ad(db_session, owner.id, [image_key(owner.id, "original.jpg")])
    ).id
    replacement = [image_key(owner.id, "new.jpg")]

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=_form(replacement, title="Обновлённое"),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == replacement


# --- D-13: серверный лимит числа вложений -------------------------------------


@pytest.mark.asyncio
async def test_ads_create_rejects_more_attachments_than_limit(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, test_settings
):
    """Обход браузерного ограничения прямым POST отклоняется сервером."""
    limit = test_settings.max_images_per_ad
    keys = [image_key(owner.id, f"p{i}.jpg") for i in range(limit + 1)]

    response = await authed_client.post(
        "/ads/new",
        content=_form(keys),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert str(limit) in response.json()["detail"]
    assert await _ads_of(db_session, owner.id) == []


@pytest.mark.asyncio
async def test_ads_create_accepts_exactly_the_limit(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, test_settings
):
    """Порог — граница включительно: ровно лимит вложений сохраняется."""
    limit = test_settings.max_images_per_ad
    keys = [image_key(owner.id, f"p{i}.jpg") for i in range(limit)]

    response = await authed_client.post(
        "/ads/new",
        content=_form(keys),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    ads = await _ads_of(db_session, owner.id)
    assert ads[0].images == keys


@pytest.mark.asyncio
async def test_ads_update_rejects_more_attachments_than_limit(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, test_settings
):
    limit = test_settings.max_images_per_ad
    ad_id = (await _seed_ad(db_session, owner.id, [])).id

    response = await authed_client.post(
        f"/ads/{ad_id}/edit",
        content=_form([image_key(owner.id, f"p{i}.jpg") for i in range(limit + 1)]),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 400
    db_session.expire_all()
    stored = (await db_session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
    assert stored.images == []


# --- Лимит читается из настроек, а не из литерала ------------------------------


# --- WR-01: форма ключа сопоставляется ТОЧНО ----------------------------------
#
# Образец был заякорен `^…$` и сопоставлялся методом `match`. Якорь `$` в Python
# совпадает и НЕПОСРЕДСТВЕННО ПЕРЕД завершающим переводом строки, поэтому
# значение `"{user_id}/{32 hex}_a.png\n"` проходило проверку владения и ложилось
# в `Ad.images` дословно — оттуда оно попадает в адрес изображения, в карточку,
# в историю и в адаптеры мессенджеров. Отдельно от этого префикс нормализовался
# через `int()`, поэтому `007/…` принимался за `7/…`, то есть за ключ, которого
# маршрут загрузки выдать не мог.
#
# Ни один из двух случаев не пересекает границу арендатора сам по себе, но оба
# ломают объявленный инвариант: ключ — ровно то значение, которое загрузка
# выдала ЭТОМУ вызывающему.
#
# Проверяется на ВСЕХ ЧЕТЫРЁХ входах записи `Ad.images`. Правило одно, и
# разъехавшись, входы оставили бы дыру ровно там, где её не проверяли.

ENTRANCES = ("page-create", "page-update", "api-create", "api-update")


async def _write_images(
    entrance: str,
    authed_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    owner: User,
    values: list[str],
) -> tuple[int, list[str] | None, list[str] | None]:
    """Подать список ключей в один из четырёх входов записи ``Ad.images``.

    Возвращает тройку: код ответа, список ключей объявления ПОСЛЕ запроса
    (``None``, если объявления нет вовсе) и то, каким этот список обязан
    остаться при отказе. На входах создания отказ означает «записи не
    появилось», на входах обновления — «посеянный список не тронут».
    """
    # Идентификатор снимается СРАЗУ и дальше используется вместо живого объекта:
    # `expire_all()` ниже сбрасывает загруженные атрибуты, и обращение к
    # `owner.id` после него ушло бы в ленивую подгрузку вне greenlet-а. Красная
    # фаза, падающая по инфраструктурной причине, не отличает «мой тест
    # воспроизвёл дефект» от «сломалось что-то постороннее».
    owner_id = owner.id
    seeded = [image_key(owner_id, "seeded.jpg")]

    if entrance == "page-create":
        response = await authed_client.post(
            "/ads/new",
            content=_form(values),
            headers=FORM_HEADERS,
            follow_redirects=False,
        )
        unchanged = None
    elif entrance == "page-update":
        ad_id = (await _seed_ad(db_session, owner_id, seeded)).id
        response = await authed_client.post(
            f"/ads/{ad_id}/edit",
            content=_form(values),
            headers=FORM_HEADERS,
            follow_redirects=False,
        )
        unchanged = seeded
    elif entrance == "api-create":
        response = await authed_client.post(
            "/api/ads",
            json={"title": "Объявление", "text": "Текст", "images": values},
            headers=auth_headers,
        )
        unchanged = None
    elif entrance == "api-update":
        ad_id = (await _seed_ad(db_session, owner_id, seeded)).id
        response = await authed_client.put(
            f"/api/ads/{ad_id}",
            json={"images": values},
            headers=auth_headers,
        )
        unchanged = seeded
    else:  # pragma: no cover - защита от опечатки в параметризации
        raise AssertionError(f"неизвестный вход записи: {entrance}")

    db_session.expire_all()
    ads = await _ads_of(db_session, owner_id)
    stored = ads[0].images if ads else None
    return response.status_code, stored, unchanged


@pytest.mark.asyncio
@pytest.mark.parametrize("entrance", ENTRANCES)
async def test_key_with_trailing_newline_is_refused(
    entrance: str,
    authed_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    owner: User,
):
    """Ключ с завершающим переводом строки — не тот ключ, что выдала загрузка."""
    hostile = image_key(owner.id, "a.png") + "\n"

    code, stored, unchanged = await _write_images(
        entrance, authed_client, auth_headers, db_session, owner, [hostile]
    )

    assert code == 400
    assert stored == unchanged


@pytest.mark.asyncio
@pytest.mark.parametrize("entrance", ENTRANCES)
async def test_key_with_leading_zero_prefix_is_refused(
    entrance: str,
    authed_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    owner: User,
):
    """Префикс сравнивается как строка: `007/…` — не `7/…`."""
    hostile = "0" + image_key(owner.id, "a.png")

    code, stored, unchanged = await _write_images(
        entrance, authed_client, auth_headers, db_session, owner, [hostile]
    )

    assert code == 400
    assert stored == unchanged


@pytest.mark.asyncio
@pytest.mark.parametrize("entrance", ENTRANCES)
async def test_own_key_is_accepted_on_every_entrance(
    entrance: str,
    authed_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    owner: User,
):
    """Ужесточение формы не имеет права отказать по всему классу.

    Страж: зелен и до правки, и после. Без него отказ «на любой ключ» выглядел
    бы закрытием WR-01, хотя означал бы, что вложения перестали работать вовсе.
    """
    value = image_key(owner.id, "a.png")

    code, stored, _ = await _write_images(
        entrance, authed_client, auth_headers, db_session, owner, [value]
    )

    assert code in (200, 201, 302), code
    assert stored == [value]


@pytest.mark.asyncio
async def test_limit_comes_from_settings_not_a_literal(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Порог берётся из `settings.max_images_per_ad`.

    Проверяется поведением: при пониженной настройке отклоняется число вложений,
    которое захардкоженная десятка пропустила бы.
    """
    test_settings.max_images_per_ad = 2
    await client.post(
        "/api/auth/register",
        json={"email": "limit@test.com", "password": "testpass123", "name": "Limit"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "limit@test.com", "password": "testpass123"},
    )
    token = resp.json()["access_token"]
    result = await db_session.execute(
        select(User).where(User.email == "limit@test.com")
    )
    user = result.scalar_one()

    response = await client.post(
        "/api/ads",
        json={
            "title": "Три вложения",
            "text": "Текст",
            "images": [image_key(user.id, f"p{i}.jpg") for i in range(3)],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400

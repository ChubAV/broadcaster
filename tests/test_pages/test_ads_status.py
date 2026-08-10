"""Состояние объявления сквозным срезом: список, дашборд, JSON-API, расписания.

Файл держит две разные вещи, и обе — про один коммит трассирующей пули.

1. **Бейдж.** Черновик отличим от опубликованного в списке `/ads`, а
   нераспознанное значение падает в «Черновик» — безопасный дефолт, потому что
   черновик не отправляется (UI-SPEC E15 `error`).
2. **Живость всех восьми читателей снятого флага.** `/dashboard`, `/api/ads`,
   `/schedules/new` и `/schedules/{id}/edit` читали `Ad.is_active`. Ревизия 0013
   снимает колонку; забытый читатель падает не пустой ячейкой, а 500-й — на
   `/api/ads` ошибкой схемы Pydantic, на остальных ошибкой SQL. Утверждения на
   код ответа здесь и есть проверка того, что не забыт ни один.

   **План 02-06 снял двух читателей из этого списка.** Отдельные страницы
   `/schedules/new` и `/schedules/{id}/edit` удалены (D-14): расписание
   настраивается в редакторе объявления. Читателем состояния объявления на этом
   месте стал сам редактор `/ads/{id}/edit` — он и проверяется ниже. Тесты
   переведены на него, а не удалены: вопрос «переживает ли настройка расписаний
   снятие колонки» остался, сменилось только место, где на него отвечают.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED
from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User

DRAFT_BADGE = "Черновик"
PUBLISHED_BADGE = "Опубликовано"


async def _user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_ad(
    db: AsyncSession,
    status: str = AD_STATUS_PUBLISHED,
    title: str = "Объявление среза",
) -> Ad:
    user = await _user(db)
    ad = Ad(user_id=user.id, title=title, text="Текст объявления", images=[])
    # Присваивание после конструктора: значение бывает и нераспознанным, а
    # именованный аргумент конструктора читался бы как «так и задумано».
    ad.status = status
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


async def _seed_account(db: AsyncSession) -> MessengerAccount:
    user = await _user(db)
    account = MessengerAccount(
        user_id=user.id, type="tg_user", credentials="sess", status="active"
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def _seed_schedule(db: AsyncSession, ad: Ad) -> Schedule:
    account = await _seed_account(db)

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[],
        days_of_week=[0],
        times_of_day=["09:00"],
        timezone="UTC",
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


# --- Бейдж состояния в списке (UI-SPEC E15) -----------------------------------


@pytest.mark.asyncio
async def test_ads_list_shows_draft_badge(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _seed_ad(db_session, status=AD_STATUS_DRAFT)

    response = await authed_client.get("/ads")

    assert response.status_code == 200
    assert DRAFT_BADGE in response.text


@pytest.mark.asyncio
async def test_ads_list_shows_published_badge(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _seed_ad(db_session, status=AD_STATUS_PUBLISHED)

    response = await authed_client.get("/ads")

    assert response.status_code == 200
    assert PUBLISHED_BADGE in response.text
    assert DRAFT_BADGE not in response.text


@pytest.mark.asyncio
async def test_ads_list_unrecognised_status_falls_back_to_draft(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Значение вне словаря показывается «Черновиком», а не сырой строкой.

    Безопасный дефолт выбран стороной, которая не отправляет: показать
    «Опубликовано» на неизвестном значении значило бы пообещать пользователю
    рассылку, которой планировщик не сделает.
    """
    await _seed_ad(db_session, status="totally-unknown-status")

    response = await authed_client.get("/ads")

    assert response.status_code == 200
    assert DRAFT_BADGE in response.text
    assert "totally-unknown-status" not in response.text
    assert PUBLISHED_BADGE not in response.text


# --- Живость читателей снятого флага ------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_counts_ads(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """`/dashboard` считает объявления. Этого читателя нет в 02-CONTEXT.md."""
    await _seed_ad(db_session, status=AD_STATUS_PUBLISHED)
    await _seed_ad(db_session, status=AD_STATUS_DRAFT, title="Черновик")

    response = await authed_client.get("/dashboard")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_ads_exposes_status(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    await _seed_ad(db_session, status=AD_STATUS_DRAFT)

    response = await client.get("/api/ads", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["status"] == AD_STATUS_DRAFT


@pytest.mark.asyncio
async def test_api_ads_update_accepts_known_status(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    ad = await _seed_ad(db_session, status=AD_STATUS_PUBLISHED)

    response = await client.put(
        f"/api/ads/{ad.id}", json={"status": AD_STATUS_DRAFT}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == AD_STATUS_DRAFT


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "hostile",
    [
        pytest.param("archived", id="plausible-but-unknown"),
        pytest.param("", id="empty"),
        pytest.param("PUBLISHED", id="wrong-case"),
        pytest.param(True, id="wrong-type"),
    ],
)
async def test_api_ads_update_rejects_unknown_status(
    hostile, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    """T-02-11: произвольная строка в состояние через JSON-вход не проходит.

    `update_ad` присваивает поля напрямую из `model_dump(exclude_unset=True)`,
    поэтому единственное место, где такое значение можно остановить, — схема.
    Записанное произвольное значение не отфильтровалось бы ни как черновик, ни
    как опубликованное.
    """
    ad = await _seed_ad(db_session, status=AD_STATUS_PUBLISHED)

    response = await client.put(
        f"/api/ads/{ad.id}", json={"status": hostile}, headers=auth_headers
    )

    assert response.status_code == 422
    check = await client.get(f"/api/ads/{ad.id}", headers=auth_headers)
    assert check.json()["status"] == AD_STATUS_PUBLISHED


def test_api_literal_matches_constants():
    """Literal в схеме и AD_STATUSES не имеют права разъехаться.

    `Literal` требует константного выражения на этапе объявления класса,
    поэтому значения там выписаны заново, а не импортированы. Разъехавшись, они
    дали бы 422 на легальном значении или пропустили бы нелегальное.
    """
    from typing import get_args

    from app.constants import AD_STATUSES
    from app.routes.ads import UpdateAdRequest

    annotation = UpdateAdRequest.model_fields["status"].annotation
    literal_values = {v for arg in get_args(annotation) for v in get_args(arg)}

    assert literal_values == AD_STATUSES


@pytest.mark.asyncio
async def test_schedule_creation_reader_alive_in_the_editor(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """SC-3: путь СОЗДАНИЯ расписания переживает миграцию.

    До плана 02-06 читателем был `GET /schedules/new`; страница снята (D-14), и
    тот же вопрос теперь задаётся редактору объявления — единственному месту,
    где расписание создаётся. Утверждение не ослаблено, а усилено: проверяется
    не только код ответа, но и наличие самой формы создания, потому что живая
    страница без формы была бы ровно тем отказом, который SC-3 запрещает.
    """
    ad = await _seed_ad(db_session, status=AD_STATUS_PUBLISHED)
    # Аккаунт мессенджера — предусловие формы добавления в редакторе (D10 плана
    # 02-05): без него на её месте стоит подсказка «Сначала подключите аккаунт».
    await _seed_account(db_session)

    response = await authed_client.get(f"/ads/{ad.id}/edit", follow_redirects=False)

    assert response.status_code == 200
    assert 'action="/schedules/new"' in response.text


@pytest.mark.asyncio
async def test_schedule_editing_reader_alive_in_the_editor(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """То же для пути ИЗМЕНЕНИЯ: читателем стала карточка в редакторе.

    `GET /schedules/{id}/edit` снят; развёрнутая карточка расписания живёт в
    редакторе объявления и сохраняется на `POST /schedules/{id}/edit`.
    """
    ad = await _seed_ad(db_session, status=AD_STATUS_PUBLISHED)
    schedule = await _seed_schedule(db_session, ad)

    response = await authed_client.get(
        f"/ads/{ad.id}/edit?sched={schedule.id}", follow_redirects=False
    )

    assert response.status_code == 200
    html = response.text
    # Карточка развёрнута и несёт СВОИ данные, а не пустую разметку.
    assert f'action="/schedules/{schedule.id}/edit"' in html
    assert "09:00" in html


@pytest.mark.asyncio
async def test_editor_of_a_draft_ad_says_there_will_be_no_sends(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Черновику не обещается рассылка ТАМ, где настраивается расписание.

    До плана 02-06 то же обещание проверялось иначе: страница `/schedules/new`
    предлагала выбрать объявление, и черновики в этот список не попадали.
    Выбора объявления больше нет — расписание принадлежит тому объявлению, чей
    редактор открыт, — поэтому вопрос «не обещаем ли мы рассылку черновику»
    задаётся редактору: он обязан назвать состояние черновиком и сказать, что
    отправок не будет (D-01/D-02, UI-SPEC §Status vocabulary).
    """
    draft = await _seed_ad(db_session, status=AD_STATUS_DRAFT, title="Черновиковое")
    published = await _seed_ad(
        db_session, status=AD_STATUS_PUBLISHED, title="Опубликованное"
    )

    draft_html = (await authed_client.get(f"/ads/{draft.id}/edit")).text
    assert DRAFT_BADGE in draft_html
    assert "отправок не будет" in draft_html

    published_html = (await authed_client.get(f"/ads/{published.id}/edit")).text
    assert PUBLISHED_BADGE in published_html

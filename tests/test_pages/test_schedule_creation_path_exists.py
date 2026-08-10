"""Страховочная сетка SC-3 на всю Фазу 2.

Критерий SC-3: «ни в один момент выката пользователь не остаётся без
возможности создать расписание». Фаза переносит настройку расписаний из
отдельных страниц в редактор объявления, и переезд растянут на два плана:

* **02-05** заводит новый путь — расписание настраивается внутри
  `/ads/{id}/edit`;
* **02-06** сносит старые страницы `/schedules/new` и `/schedules/{id}/edit`.

Между этими планами сосуществуют оба пути, до 02-05 работает только старый,
после 02-06 — только новый. Поэтому тест утверждает ДИЗЪЮНКЦИЮ, а не
конкретный маршрут: он обязан быть зелёным в КАЖДОМ коммите фазы. Утверждение
на один конкретный путь превратило бы сетку в расписание работ — она краснела
бы ровно в тот момент, когда переезд идёт по плану, и её бы отключили.

Красным этот тест становится только тогда, когда создавать расписание нельзя
НИКАК — то есть ровно в той ситуации, которую SC-3 запрещает.
"""

import re

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.user import User

# Маршруты, создающие расписание. Пополняется планом 02-05, если новый путь
# уходит на собственный адрес, а не на POST /schedules/new.
SCHEDULE_CREATE_ACTIONS = ("/schedules/new",)

FORM_ACTION_RE = re.compile(r'<form\b[^>]*\baction="([^"]+)"', re.I)


async def _seed_ad(db: AsyncSession) -> Ad:
    user = (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()
    ad = Ad(
        user_id=user.id,
        title="Объявление для проверки SC-3",
        text="Текст объявления",
        images=[],
        is_active=True,
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


async def _legacy_page_available(client: AsyncClient) -> bool:
    """Старый путь: отдельная страница `/schedules/new` отвечает 200."""
    response = await client.get("/schedules/new", follow_redirects=False)
    return response.status_code == 200


async def _editor_offers_schedule_form(client: AsyncClient, ad_id: int) -> bool:
    """Новый путь: в редакторе объявления есть форма создания расписания."""
    response = await client.get(f"/ads/{ad_id}/edit", follow_redirects=False)
    if response.status_code != 200:
        return False
    actions = FORM_ACTION_RE.findall(response.text)
    return any(
        action.startswith(create_action)
        for action in actions
        for create_action in SCHEDULE_CREATE_ACTIONS
    )


@pytest.mark.asyncio
async def test_schedule_creation_path_exists(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Хотя бы один рабочий путь создания расписания доступен пользователю."""
    ad = await _seed_ad(db_session)

    legacy = await _legacy_page_available(authed_client)
    in_editor = await _editor_offers_schedule_form(authed_client, ad.id)

    assert legacy or in_editor, (
        "SC-3 нарушен: создать расписание нельзя ни через отдельную страницу "
        "/schedules/new, ни через форму в редакторе объявления. "
        "Либо план 02-05 ещё не завёл путь в редакторе, либо план 02-06 снёс "
        "старые страницы раньше него."
    )

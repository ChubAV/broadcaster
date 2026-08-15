"""Таймзона профиля доходит до расписания, созданного в редакторе объявления.

До плана 02-06 то же проверялось на отдельной странице `/schedules/new`: её
форма подставляла таймзону пользователя в выпадающий список. Страница снята
(D-14), и таймзона в карточке расписания БОЛЬШЕ НЕ ВЫБИРАЕТСЯ — по UI-SPEC это
моноширинная подпись «Время по {tz из профиля}» только для чтения.

Проверяемое обещание осталось прежним: расписание пользователя живёт в ЕГО
часовом поясе, а не в UTC. Сместилось только место, где это видно, — и место,
где значение назначается: раньше его присылала форма, теперь подставляет
сервер из профиля.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User


@pytest.mark.asyncio
async def test_schedule_created_in_the_editor_uses_the_profile_timezone(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict,
):
    # Пользователь уже создан через auth_headers
    result = await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    user = result.scalar_one()
    user.timezone = "Europe/Moscow"

    ad = Ad(user_id=user.id, title="Объявление таймзоны", text="Текст", images=[])
    account = MessengerAccount(user_id=user.id, type="tg_user", credentials="creds")
    db_session.add_all([ad, account])
    await db_session.commit()
    await db_session.refresh(ad)
    # Идентификатор снимается в локальную переменную ДО перечитывания: сессия
    # теста общая с обработчиком, и обращение к атрибуту истёкшего объекта уходит
    # в ленивую загрузку вне greenlet-контекста (приём из плана 02-05).
    ad_id = ad.id

    # Логинимся через страницу, чтобы выставить cookie
    await client.post(
        "/login",
        data={"email": "testuser@test.com", "password": "testpass123"},
        follow_redirects=False,
    )

    # Форма «+ ДОБАВИТЬ ПЕРВОЕ» из редактора: поля timezone в ней НЕТ — именно
    # поэтому умолчание обязано браться из профиля, а не из литерала.
    created = await client.post(
        "/schedules/new",
        data={"ad_id": str(ad_id), "return_to": "editor"},
        follow_redirects=False,
    )
    assert created.status_code == 302

    schedule = (
        await db_session.execute(
            select(Schedule)
            .where(Schedule.ad_id == ad_id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one()
    schedule_id, schedule_tz = schedule.id, schedule.timezone
    assert schedule_tz == "Europe/Moscow", (
        "расписание создано в чужом часовом поясе: подпись карточки обещает "
        "таймзону профиля, а рассылка ушла бы по UTC"
    )

    # Подпись в развёрнутой карточке — только для чтения и несёт ту же таймзону.
    html = (await client.get(f"/ads/{ad_id}/edit?sched={schedule_id}")).text
    assert "Время по Europe/Moscow" in html
    # Выбора таймзоны в карточке нет: ни списка, ни видимого поля.
    assert '<option value="Europe/Moscow"' not in html

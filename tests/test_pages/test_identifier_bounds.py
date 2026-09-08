"""ГРАНИЦА ВЕЛИЧИНЫ ИДЕНТИФИКАТОРА — ОДИН МАРШРУТ, ПРОВЕДЁННЫЙ НАСКВОЗЬ.

⚠️ ЧТО ЭТИ ПРАВИЛА НАБЛЮДАЮТ, А ЧТО НЕ НАБЛЮДАЮТ — НАЗВАНО ЗДЕСЬ, А НЕ
ПОДРАЗУМЕВАЕТСЯ. Отказ ставит ГРАНИЦА ПРИЛОЖЕНИЯ: величина отвергается ДО того,
как тело обработчика получило управление, и потому ДО любого обращения к
драйверу. Из этого прямо следует, что исход правил от драйвера НЕ ЗАВИСИТ —
они одинаковы на SQLite суиты и на PostgreSQL боевого стенда.

⚠️ И ИЗ ЭТОГО ЖЕ СЛЕДУЕТ, ЧЕГО ОНИ НЕ ГОВОРЯТ. Поведение БОЕВОГО драйвера на
НЕОГРАНИЧЕННОМ входе эти правила не наблюдают и наблюдать не могут: у суиты
драйвер ОДИН (`sqlite+aiosqlite:///:memory:`), величина `2147483648` проходит в
него молча, тогда как asyncpg на ней даёт `DataError`. Утверждать по зелёному
этого модуля, что боевой отказ воспроизведён, ЗАПРЕЩЕНО — это предмет окна 39
реестра `.planning/WINDOWS.md`, и оно остаётся открытым.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import AD_STATUS_PUBLISHED
from app.models.ad import Ad
from app.models.user import User

FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

# Форма ответа на негодную величину — отказ ВАЛИДАЦИИ.
VALIDATION_REFUSAL = "422"

# Величина ВЫШЕ ГРАНИЦЫ КОЛОНКИ на единицу. В SQLite она проходит молча (там
# целое шире), поэтому ДО правки этот вход давал не отказ обработчика, а
# редирект «нет такой записи» — то есть тихо становился неотличим от годного.
ABOVE_THE_COLUMN = "2147483648"

# Двадцать шесть девяток. Эта величина не влезает уже и в SQLite, и ДО правки
# роняла обработчик.
BEYOND_ANY_DRIVER = "99999999999999999999999999"


async def _seed_owner_ad(db: AsyncSession) -> Ad:
    """Посев объявления пользователя, заведённого фикстурой входа.

    Помощник ПОСЕВА, а не фикстура: модуль своих фикстур не заводит — он берёт
    `authed_client` и `db_session` из `tests/conftest.py`.
    """
    user = (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()
    ad = Ad(
        user_id=user.id,
        title="Объявление для границы",
        text="Текст объявления",
        images=[],
        status=AD_STATUS_PUBLISHED,
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


async def _delete_ad(client: AsyncClient, value: str):
    """Прямой POST мимо браузера по маршруту удаления объявления.

    ⚠️ ВЕЛИЧИНА ПОДСТАВЛЯЕТСЯ В АДРЕС ФОРМАТИРОВАНИЕМ СТРОКИ, А НЕ ПРИВЕДЕНИЕМ
    К ЦЕЛОМУ: величина в двадцать шесть знаков в приведении потеряла бы ровно то
    свойство, ради которого взята (записанное основание `_post_route_input`
    соседнего модуля).

    ⚠️ ОТВЕТ ЕСТЬ ВСЕГДА, И ЭТО ЗАМЕР, А НЕ ДОПУЩЕНИЕ. Отказ обработчика на
    величине, не влезающей в драйвер, не долетает до вызывающего исключением:
    собственная прослойка проекта (`app/middleware.py:27`) ловит его и отвечает
    `500`. Поэтому исход снимается КОДОМ ОТВЕТА, а не парой «код либо
    исключение», и защитной ветки на исключение здесь нет — ветка, которая не
    исполняется, читалась бы как исполненный инвариант.
    """
    return await client.post(
        f"/ads/{value}/delete",
        content="",
        headers=FORM_HEADERS,
        follow_redirects=False,
    )


async def _delete_outcome(client: AsyncClient, value: str) -> str:
    """СНЯТЫЙ КОД одного запроса удаления по одной величине — строкой.

    Строкой, а не числом, чтобы отображение «величина → снятый код» читалось в
    тексте отказа тем же способом, каким записана сама величина.
    """
    return str((await _delete_ad(client, value)).status_code)


@pytest.mark.asyncio
async def test_ads_delete_refuses_a_value_no_driver_can_hold_with_a_validation_refusal(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Пункт 2 `<behavior>`: величина из двадцати шести девяток даёт `422`.

    ДО правки тот же запрос давал отказ ОБРАБОТЧИКА — это наблюдается прогоном,
    а не предполагается.
    """
    await _seed_owner_ad(db_session)

    outcome = await _delete_outcome(authed_client, BEYOND_ANY_DRIVER)

    assert outcome == VALIDATION_REFUSAL, (
        "величина, не влезающая ни в один драйвер, доехала до тела обработчика "
        f"(снято → {outcome!r}; ожидалось → {VALIDATION_REFUSAL!r}). Предмет — "
        "граница ПРИЛОЖЕНИЯ: значение вне диапазона колонки обязано "
        "отвергаться ДО тела обработчика, а не ронять запрос драйвером "
        "(`CR-01` пятого круга ревизии)"
    )

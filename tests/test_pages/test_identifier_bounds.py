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

# ⚠️ ГРАНИЦА ВВОЗИТСЯ У ПРИЛОЖЕНИЯ, А НЕ ВЫПИСЫВАЕТСЯ ЛИТЕРАЛОМ. Вторая копия
# числа разошлась бы с первой молча при первой же правке колонки, и правило
# начало бы утверждать о числе, которого в приложении нет (записанное основание
# соседнего обхода — `tests/test_pages/test_editor_schedules.py`).
from app.pages.identifiers import ID_MAX

FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

# Форма ответа на негодную величину — отказ ВАЛИДАЦИИ.
VALIDATION_REFUSAL = "422"

# Форма ответа на ГОДНУЮ величину, которой в базе нет: переход. Величина внутри
# диапазона есть ЗАКОННЫЙ идентификатор, и «нет такой записи» неотличимо от
# «запись чужая» — записанное основание самого обработчика (T-02-21).
MISSING_ROW_REDIRECT = "302"

# Ровно ГРАНИЦА. Величина в диапазоне колонки лежит, и отвергать её граница
# права не имеет.
AT_THE_COLUMN = str(ID_MAX)

# Величина ВЫШЕ ГРАНИЦЫ КОЛОНКИ на единицу. В SQLite она проходит молча (там
# целое шире), поэтому ДО правки этот вход давал не отказ обработчика, а
# редирект «нет такой записи» — то есть тихо становился неотличим от годного.
ABOVE_THE_COLUMN = str(ID_MAX + 1)

# Двадцать шесть девяток. Эта величина не влезает уже и в SQLite, и ДО правки
# роняла обработчик.
BEYOND_ANY_DRIVER = "99999999999999999999999999"

# Ноль. В домен автоинкремента не входит: идентификаторы начинаются с единицы.
BELOW_THE_DOMAIN = "0"

# ⚠️ ОТОБРАЖЕНИЕ «ВЕЛИЧИНА → ОЖИДАЕМЫЙ КОД» СЛИЧАЕТСЯ ЦЕЛИКОМ, А НЕ ПО ОДНОЙ
# СТРОКЕ. Правило, останавливающееся на первой несогласной, чинилось бы по
# одной величине за круг; и оно же обязано нести ОБЕ стороны стыка — граница,
# проверенная только снаружи диапазона, зеленела бы на помощнике, отвергающем
# ВСЁ, и границей не была бы.
EXPECTED_OUTCOMES: dict[str, str] = {
    ABOVE_THE_COLUMN: VALIDATION_REFUSAL,
    BEYOND_ANY_DRIVER: VALIDATION_REFUSAL,
    AT_THE_COLUMN: MISSING_ROW_REDIRECT,
    BELOW_THE_DOMAIN: VALIDATION_REFUSAL,
}


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


@pytest.mark.asyncio
async def test_ads_delete_draws_the_column_boundary_on_both_of_its_sides(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """СКВОЗНОЕ правило одного маршрута: отображение сличается ЦЕЛИКОМ.

    Четыре величины и обе стороны стыка: `ID_MAX` годной величиной не
    отвергается, `ID_MAX + 1` отвергается. Правило, отвергающее ВСЁ, дало бы
    зелёный на трёх строках из четырёх и покраснело бы на четвёртой — именно
    поэтому строка границы стои́т в том же отображении, а не в соседнем правиле.
    """
    await _seed_owner_ad(db_session)

    seen = {
        value: await _delete_outcome(authed_client, value)
        for value in EXPECTED_OUTCOMES
    }

    disagreed = {
        value: code
        for value, code in seen.items()
        if code != EXPECTED_OUTCOMES[value]
    }
    assert not disagreed, (
        "граница величины отвечает не тем, что объявила. Несогласные строки "
        f"({len(disagreed)} из {len(EXPECTED_OUTCOMES)}): "
        + "; ".join(
            f"{value} = {code} (ожидалось {EXPECTED_OUTCOMES[value]})"
            for value, code in sorted(disagreed.items())
        )
        + f". Все снятые исходы: {sorted(seen.items())}"
    )


@pytest.mark.asyncio
async def test_ads_delete_still_removes_a_live_advert_of_its_owner(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """АНТИВАКУУМ. Без него зелёное выше не значит ничего.

    Граница, отвергающая ВСЁ, дала бы те же три отказа валидации и объявила бы
    себя границей. Здесь подаётся ЖИВАЯ величина, и объявление обязано
    исчезнуть.
    """
    ad = await _seed_owner_ad(db_session)

    outcome = await _delete_outcome(authed_client, str(ad.id))

    assert outcome not in (VALIDATION_REFUSAL,) and not outcome.startswith("5"), (
        "граница отвергла ГОДНУЮ величину — она отвергает не то, что объявила "
        f"(снято → {outcome!r} на живом идентификаторе {ad.id})"
    )

    survivor = (
        await db_session.execute(select(Ad).where(Ad.id == ad.id))
    ).scalar_one_or_none()
    assert survivor is None, (
        "живое объявление владельца НЕ УДАЛИЛОСЬ: правка границы задела то, "
        f"что обязана была пропустить (идентификатор {ad.id}, снятый код "
        f"{outcome!r})"
    )


@pytest.mark.asyncio
async def test_a_repeated_refused_request_is_indistinguishable_from_the_first(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Пункт 5 `<behavior>`: повтор отвергнутого запроса неотличим от первого.

    Граница есть ЧИСТАЯ ФУНКЦИЯ запроса: состояния между вызовами она не держит,
    и второй запрос не может получить ни другого кода, ни другого тела. Правило
    сличает и КОД, и ТЕЛО: отказ, различающийся телом, выдал бы наличие
    состояния так же верно, как различающийся кодом.
    """
    await _seed_owner_ad(db_session)

    first = await _delete_ad(authed_client, ABOVE_THE_COLUMN)
    second = await _delete_ad(authed_client, ABOVE_THE_COLUMN)

    assert (first.status_code, first.content) == (
        second.status_code,
        second.content,
    ), (
        "повтор отвергнутого запроса отличим от первого: "
        f"первый — {first.status_code} / {first.content!r}; "
        f"второй — {second.status_code} / {second.content!r}. Граница обязана "
        "быть чистой функцией запроса и состояния между вызовами не держать"
    )

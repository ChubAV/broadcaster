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

from datetime import datetime, timezone

import ast
import pathlib
import re
import uuid
from dataclasses import dataclass
from functools import lru_cache

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import AD_STATUS_PUBLISHED
from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.user import User
from app.pages.history import STATUS_OK
from tests.conftest import a_future_run_moment, seed_group

# ⚠️ ГРАНИЦА ВВОЗИТСЯ У ПРИЛОЖЕНИЯ, А НЕ ВЫПИСЫВАЕТСЯ ЛИТЕРАЛОМ. Вторая копия
# числа разошлась бы с первой молча при первой же правке колонки, и правило
# начало бы утверждать о числе, которого в приложении нет (записанное основание
# соседнего обхода — `tests/test_pages/test_editor_schedules.py`).
from app.pages.identifiers import ID_MAX

FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

# ⚠️ ПАРОЛЬ ОДИН НА ОБЕ ЛИЧНОСТИ, И ЭТО СВОЙСТВО ФИКСТУР, А НЕ ДОПУЩЕНИЕ:
# `authed_client` и `admin_client` (`tests/conftest.py`) заводят своих
# пользователей одним и тем же паролем. Вторая копия строки здесь разошлась бы
# с ними молча, и вход перестал бы удаваться ровно тогда, когда фикстуру
# поправят.
IDENTITY_PASSWORD = "testpass123"

# Почта обычной личности — та же, по которой посев ищет пользователя фикстуры.
USER_IDENTITY_EMAIL = "testuser@test.com"

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


# =============================================================================
# ЕДИНСТВЕННОСТЬ ОБЪЯВЛЕНИЯ ГРАНИЦЫ ВО ВСЁМ `app/`
#
# Правило есть МАШИННОЕ ПРИНУЖДЕНИЕ решения `promote` плана 10-24: величина
# повышена в первичное представление и объявлена ОДИН раз, а прежнее частное
# понижено до именованных псевдонимов. Ветвь `add-alongside` отвергнута с
# названным последствием — вторая копия числа в соседнем файле разошлась бы с
# первой МОЛЧА, и это ровно тот класс отказа, за который фаза получила круги
# ревизии 3, 4 и 5. Отвергнутое решение, за которым не стои́т правила, есть
# намерение, а не решение.
#
# ⚠️ ПРЕДМЕТ ПРАВИЛА — ЕДИНСТВЕННОСТЬ, А НЕ ВЕРНОСТЬ ВЕЛИЧИНЫ, И ЭТО НАЗВАНО, А
# НЕ ОБОЙДЕНО. Искомая величина берётся ВВОЗОМ у самого приложения, поэтому
# правка `ID_MAX` на неверное число правило зелёным оставит: оно скажет лишь,
# что объявление по-прежнему ОДНО. Верность величины держат основания у
# объявления (граница колонки int4) и сквозное правило маршрута выше, где
# `ID_MAX + 1` обязан отвергаться, а `ID_MAX` — нет.
# =============================================================================

APP_DIRECTORY = pathlib.Path(__file__).resolve().parents[2] / "app"

# Владелец величины. Назван ПУТЁМ, а не «каким-нибудь одним местом»: правило,
# требующее лишь единственности, зеленело бы и на объявлении, уехавшем обратно
# в страничный модуль, — то есть на откате переезда, ради которого заведено.
BOUND_OWNER = "app/pages/identifiers.py"


def _app_sources() -> dict[str, str]:
    """Пары «относительный путь → ТЕКСТ модуля» по всему дереву `app/`.

    Обход РЕКУРСИВНЫЙ: файл, положенный будущей фазой в новый подкаталог,
    обязан попасть в охват сам, а не ждать, пока кто-то вспомнит про его
    каталог (форма взята у `_read_directory`, `tests/test_pages/test_htmx_gates.py`).
    """
    root = APP_DIRECTORY.parent
    return {
        str(path.relative_to(root)): path.read_text(encoding="utf-8")
        for path in sorted(APP_DIRECTORY.glob("**/*.py"))
    }


def _bound_declarations(sources: dict[str, str], bound: int) -> list[str]:
    """Места, где ВЕЛИЧИНА границы объявлена целочисленной константой.

    ⚠️ ПРАВИЛО ЧИТАЕТ ДЕРЕВО РАЗБОРА, А НЕ СТРОКИ. Построчный поиск считал бы
    вхождение числа в КОММЕНТАРИЙ и в ДОКСТРИНГ — то есть объяснение роняло бы
    утверждение, а комментарий, повторяющий искомое, мог бы заменить собой
    пропавшее объявление. Ловушка не гипотетическая: `app/pages/schedules.py`
    несёт число прозой ровно затем, чтобы объяснить, почему копии числа там
    больше нет. Основание перенесено дословно из `_strip_comments`
    (`tests/test_pages/test_editor_schedules.py`), где та же ловушка уже стоила
    суите константы, знавшей текст документации наизусть.

    Возвращаются ВСЕ найденные места, а не первое: правило, называющее одно,
    чинилось бы по одному файлу за круг.
    """
    places: list[str] = []
    for module, text in sorted(sources.items()):
        try:
            tree = ast.parse(text)
        except SyntaxError as error:  # модуль обязан РОНЯТЬ правило, а не выпадать
            raise AssertionError(
                f"модуль {module} не разобрался в дерево ({error}) — охват, тихо "
                "потерявший файл, утверждает не то, что обещает"
            ) from error

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets, value = node.targets, node.value
            elif isinstance(node, ast.AnnAssign):
                targets, value = [node.target], node.value
            else:
                continue
            if not isinstance(value, ast.Constant):
                continue
            # `bool` — подкласс `int`, и без этой строки `True` сравнивался бы с
            # числом как число.
            if isinstance(value.value, bool) or not isinstance(value.value, int):
                continue
            if value.value != bound:
                continue
            for target in targets:
                name = getattr(target, "id", None) or ast.dump(target)
                places.append(f"{module}:{node.lineno} → {name}")
    return places


def test_the_identifier_bound_is_declared_exactly_once_in_the_whole_app():
    """Величина границы объявлена во всём `app/` РОВНО ОДИН РАЗ, и владелец назван."""
    places = _bound_declarations(_app_sources(), ID_MAX)

    # Номер строки владельца в утверждение НЕ ЗАШИТ: он есть свойство файла, а
    # не правила, и первая же вставка абзаца выше объявления красила бы прогон
    # сообщением о расползшейся границе — то есть правило начало бы врать о
    # своём предмете.
    assert len(places) == 1 and places[0].startswith(f"{BOUND_OWNER}:"), (
        f"объявлений величины границы ({ID_MAX}) во всём `app/` не одно, а "
        f"{len(places)}, либо владелец её не `{BOUND_OWNER}`. НАЙДЕНЫ ВСЕ "
        f"места: {places}. Вторая копия числа расходится с первой МОЛЧА при "
        "первой же правке колонки — ровно тот класс отказа (`запись шире "
        "дерева`), за который фаза получила круги ревизии 3, 4 и 5. Величина "
        f"объявляется в `{BOUND_OWNER}`, а потребители ввозят её оттуда"
    )


def test_control_negative_a_second_declaration_reddens_the_uniqueness_rule():
    """ЗУБЫ ПРАВИЛА ПОКАЗАНЫ, А НЕ ЗАЯВЛЕНЫ.

    Правилу подаётся ИЗМЕНЁННАЯ КОПИЯ дерева, в которой та же величина
    объявлена ВТОРОЙ раз в соседнем модуле. Копия собирается в памяти — файл
    дерева не правится ни байтом. Без наблюдённого перехода цвета правило
    неотличимо от вакуумно-зелёного (записанный опыт окна 29).
    """
    sources = _app_sources()

    honest = _bound_declarations(sources, ID_MAX)
    # Первый предохранитель: на НАСТОЯЩЕМ дереве правило зелено, иначе контроль
    # сравнивал бы подделку с уже сломанным образцом.
    assert len(honest) == 1, (
        f"на настоящем дереве правило уже красно: {honest}"
    )

    victim = "app/pages/schedules.py"
    assert victim in sources, f"модуль подделки исчез из дерева: {victim}"
    forged = dict(sources)
    forged[victim] = sources[victim] + f"\n_SECOND_COPY_OF_THE_BOUND = {ID_MAX}\n"

    broken = _bound_declarations(forged, ID_MAX)
    assert len(broken) == 2 and any(
        place.startswith(f"{victim}:") for place in broken
    ), (
        "правило НЕ ЗАМЕТИЛО второго объявления той же величины в соседнем "
        f"модуле: {broken}. Копия числа прошла бы в дерево незамеченной"
    )
    assert any(place.startswith(f"{BOUND_OWNER}:") for place in broken), (
        "подделка вытеснила из находок владельца величины — контроль "
        f"доказывал бы не то свойство, которое объявил: {broken}"
    )


def test_control_the_uniqueness_rule_does_not_read_prose():
    """ПРАВИЛО НЕ САМООТМЕНЯЕТСЯ: комментарий не есть объявление.

    В копию модуля дописывается СТРОКА КОММЕНТАРИЯ и ДОКСТРИНГ, дословно
    несущие искомое число. Находки обязаны не измениться: правило, читающее
    прозу, краснело бы на правку документации и зеленело бы на документацию,
    повторяющую искомое.
    """
    sources = _app_sources()
    honest = _bound_declarations(sources, ID_MAX)

    victim = "app/pages/schedules.py"
    forged = dict(sources)
    forged[victim] = (
        sources[victim]
        + f"\n# Прежняя копия величины была {ID_MAX}, и её здесь больше нет.\n"
        + f'\n_PROSE = """величина {ID_MAX} названа здесь прозой"""\n'
    )

    assert _bound_declarations(forged, ID_MAX) == honest, (
        "правило прочло ПРОЗУ как объявление: комментарий и докстринг, "
        "называющие число, изменили находки. Объяснение не имеет права ронять "
        f"утверждение (найдено на подделке: {_bound_declarations(forged, ID_MAX)})"
    )


# =============================================================================
# МАТРИЦА ВХОДОВ ПРОДУКТОВЫХ МОДУЛЕЙ — «ВХОД → СНЯТЫЙ КОД»
#
# ⚠️ МАТРИЦА, А НЕ ОБРАЗЕЦ, И ЭТО ЕДИНСТВЕННОЕ, ЧЕМ «ЗАКРЫТО НА ОДНОМ МАРШРУТЕ»
# НЕ ПРОЧИТАЕТСЯ КАК «ЗАКРЫТО НА ВСЕХ». План 10-24 провёл насквозь ОДИН вход
# (`POST /ads/{ad_id}/delete`), и зелёный того правила говорил ровно об одном
# входе. Пятый круг ревизии (`CR-01`) предъявил ВОСПРОИЗВЕДЁННЫЕ отказы ещё на
# пяти маршрутах: граница стояла там, куда смотрели, и молчала там, куда не
# смотрели. Правило, сличающее отображение ЦЕЛИКОМ и называющее ВСЕ несогласные
# строки, чинится одним кругом; правило, останавливающееся на первой, чинилось
# бы по одному входу за круг — ровно тот способ, которым фаза потратила круги
# ревизии 3, 4 и 5.
#
# ⚠️ ГРАНИЦА НАБЛЮДЕНИЯ ТА ЖЕ, ЧТО У ПРАВИЛ ВЫШЕ, И ПОВТОРЯЕТСЯ ЗДЕСЬ, А НЕ
# ОСТАВЛЯЕТСЯ ЧИТАТЕЛЮ: наблюдается отказ на ГРАНИЦЕ ПРИЛОЖЕНИЯ, до драйвера.
# Поведения боевого PostgreSQL на НЕОГРАНИЧЕННОМ входе матрица не наблюдает и
# наблюдать не может — предмет окна 39 реестра `.planning/WINDOWS.md`.
# =============================================================================


@dataclass(frozen=True)
class _BoundedEntry:
    """Один ЗАКРЫТЫЙ ВХОД матрицы.

    ВХОД, а не маршрут: маршрут с двумя идентификаторами даёт ДВА входа, и
    склеивание их в один есть ровно та ошибка счёта, которую соседний реестр
    расхождения заводился исправить (`tests/test_pages/test_htmx_gates.py`,
    летопись числа 0 → 7).

    Поля: `key` — человекочитаемое имя входа, по форме совпадающее с ключом
    реестра расхождения там, где вход есть вход POST-обработчика; `method` —
    способ обращения; `address` — адрес с местозаполнителем `{value}` на месте
    ИСПЫТУЕМОЙ величины и с живыми полями посева на местах ПРОЧИХ; `parameter` —
    имя испытуемого параметра; `live` — ключ посева, из которого берётся ЖИВАЯ
    величина для антивакуума.

    ⚠️ `identity` — ЛИЧНОСТЬ, ПОД КОТОРОЙ ИДЁТ ОБРАЩЕНИЕ, И ОНА ЕСТЬ ПОЛЕ ВХОДА,
    А НЕ ФИКСТУРА ПРАВИЛА. Административные входы закрыты `require_admin`, и
    обращение к ним из-под обычного пользователя упёрлось бы в проверку ПРАВ:
    исход перестал бы говорить о границе ВЕЛИЧИНЫ и начал бы говорить о правах.
    Две личности живут в ОДНОЙ матрице, а не в двух: предмет у них один —
    граница величины идентификатора, — и разведение по личности было бы
    разведением по внешнему признаку ровно так же, как разведение по способу
    передачи (записанное основание курсора постраничного вывода выше).

    ⚠️ `body` — ТЕЛО POST-ЗАПРОСА, И ОНО НЕ УКРАШЕНИЕ. Вход, у которого есть
    ОБЯЗАТЕЛЬНОЕ поле формы (снятие задачи из очереди несёт `task_id`), на
    пустом теле отвечает отказом валидации ЗА ОТСУТСТВИЕ ПОЛЯ — то есть строка
    матрицы зеленела бы, не сказав ни слова о границе идентификатора, а
    антивакуум на живой величине краснел бы по той же причине. Поле подаётся
    затем, чтобы отказ мог прийти РОВНО от границы.
    """

    key: str
    method: str
    address: str
    parameter: str
    live: str
    identity: str = "user"
    body: str = ""


BOUNDED_ENTRIES: tuple[_BoundedEntry, ...] = (
    # --- app/pages/account_groups.py: семь идентификаторов пути и курсор ---
    _BoundedEntry(
        key="app/pages/account_groups.py::GET /accounts/{account_id}/groups → адрес account_id",
        method="GET",
        address="/accounts/{value}/groups",
        parameter="account_id",
        live="account",
    ),
    _BoundedEntry(
        key="app/pages/account_groups.py::GET /accounts/{account_id}/groups/partial → адрес account_id",
        method="GET",
        address="/accounts/{value}/groups/partial",
        parameter="account_id",
        live="account",
    ),
    _BoundedEntry(
        # ⚠️ ИДЕНТИФИКАТОР, ПРИЕХАВШИЙ ПАРАМЕТРОМ ЗАПРОСА, А НЕ АДРЕСОМ. Курсор
        # уезжает операндом сравнения SQL по колонке идентификатора
        # (`Group.id > after_id`, `app/pages/account_groups.py`), то есть его
        # граница есть граница КОЛОНКИ. Разведение входов по СПОСОБУ ПЕРЕДАЧИ
        # было бы разведением по внешнему признаку.
        key="app/pages/account_groups.py::GET /accounts/{account_id}/groups/partial → запрос after_id",
        method="GET",
        address="/accounts/{account}/groups/partial?after_id={value}",
        parameter="after_id",
        live="group",
    ),
    _BoundedEntry(
        key="app/pages/account_groups.py::GET /accounts/{account_id}/groups/sync-status → адрес account_id",
        method="GET",
        address="/accounts/{value}/groups/sync-status",
        parameter="account_id",
        live="account",
    ),
    _BoundedEntry(
        key="app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/toggle → адрес account_id",
        method="POST",
        address="/accounts/{value}/groups/{group}/toggle",
        parameter="account_id",
        live="account",
    ),
    _BoundedEntry(
        key="app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/toggle → адрес group_id",
        method="POST",
        address="/accounts/{account}/groups/{value}/toggle",
        parameter="group_id",
        live="group",
    ),
    _BoundedEntry(
        key="app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/delete → адрес account_id",
        method="POST",
        address="/accounts/{value}/groups/{group}/delete",
        parameter="account_id",
        live="account",
    ),
    _BoundedEntry(
        key="app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/delete → адрес group_id",
        method="POST",
        address="/accounts/{account}/groups/{value}/delete",
        parameter="group_id",
        live="group",
    ),
    # --- app/pages/accounts.py: четыре идентификатора пути ---
    _BoundedEntry(
        key="app/pages/accounts.py::GET /accounts/{account_id}/sync-status → адрес account_id",
        method="GET",
        address="/accounts/{value}/sync-status",
        parameter="account_id",
        live="account",
    ),
    _BoundedEntry(
        key="app/pages/accounts.py::POST /accounts/{account_id}/retry-sync → адрес account_id",
        method="POST",
        address="/accounts/{value}/retry-sync",
        parameter="account_id",
        live="account",
    ),
    _BoundedEntry(
        key="app/pages/accounts.py::POST /accounts/{account_id}/sync-groups → адрес account_id",
        method="POST",
        address="/accounts/{value}/sync-groups",
        parameter="account_id",
        live="account",
    ),
    _BoundedEntry(
        key="app/pages/accounts.py::POST /accounts/{account_id}/delete → адрес account_id",
        method="POST",
        address="/accounts/{value}/delete",
        parameter="account_id",
        live="account",
    ),
    # --- app/pages/ads.py: два идентификатора пути и признак раскрытого расписания ---
    #
    # ⚠️ УДАЛЕНИЯ ОБЪЯВЛЕНИЯ ЗДЕСЬ НЕТ, И ЭТО НЕ ПРОПУСК. Оно закрыто планом
    # 10-24 и проведено насквозь СОБСТВЕННЫМИ правилами этого же модуля выше
    # (`_delete_outcome`). Вторая строка матрицы на тот же вход не добавила бы
    # ни одного наблюдения и увела бы счёт входов плана.
    _BoundedEntry(
        key="app/pages/ads.py::GET /ads/{ad_id}/edit → адрес ad_id",
        method="GET",
        address="/ads/{value}/edit",
        parameter="ad_id",
        live="ad",
    ),
    _BoundedEntry(
        # ⚠️ ВТОРОЙ ИДЕНТИФИКАТОР, ПРИЕХАВШИЙ ПАРАМЕТРОМ ЗАПРОСА. Основание, по
        # которому он закрыт, ОТЛИЧАЕТСЯ от основания курсора выше, и разница
        # названа здесь, а не сглажена: курсор ДОЕЗЖАЕТ до сравнения по колонке,
        # а этот признак — НЕ ДОЕЗЖАЕТ (он сличается с уже загруженным составом
        # расписаний в памяти, `app/pages/ads.py`, `_editor_context`). Закрыт он
        # по ОБЪЯВЛЕННОМУ предмету: параметр объявлен идентификатором
        # расписания, а идентификаторы этого проекта лежат в диапазоне колонки.
        key="app/pages/ads.py::GET /ads/{ad_id}/edit → запрос sched",
        method="GET",
        address="/ads/{ad}/edit?sched={value}",
        parameter="sched",
        live="schedule",
    ),
    _BoundedEntry(
        key="app/pages/ads.py::POST /ads/{ad_id}/edit → адрес ad_id",
        method="POST",
        address="/ads/{value}/edit",
        parameter="ad_id",
        live="ad",
    ),
    # --- app/pages/history.py: два идентификатора пути ---
    _BoundedEntry(
        key="app/pages/history.py::GET /history/{log_id} → адрес log_id",
        method="GET",
        address="/history/{value}",
        parameter="log_id",
        live="log",
    ),
    _BoundedEntry(
        key="app/pages/history.py::POST /history/{log_id}/retry → адрес log_id",
        method="POST",
        address="/history/{value}/retry",
        parameter="log_id",
        live="log",
    ),
    # --- app/pages/admin.py: одиннадцать идентификаторов пути ---
    #
    # ⚠️ САМАЯ ПРИВИЛЕГИРОВАННАЯ ПОВЕРХНОСТЬ ПРОЕКТА, И ОНА ЗАКРЫВАЕТСЯ ТОЙ ЖЕ
    # ГРАНИЦЕЙ, ЧТО И ПРОДУКТОВАЯ, А НЕ СВОЕЙ. Ревизия эти маршруты своим
    # клиентом не прогоняла — но объявление первичного ключа у них то же
    # (`app/models/user.py`, `app/models/send_log.py` — `Mapped[int]` без
    # расширенной разрядности), механизм отказа тот же, и основание, по
    # которому закрыты продуктовые входы, применимо к ним слово в слово.
    #
    # ⚠️ У ШЕСТИ ИЗМЕНЯЮЩИХ ВХОДОВ ГАРД ПРОИСХОЖДЕНИЯ СТОИ́Т В ТЕЛЕ, И НА
    # НЕГОДНОЙ ВЕЛИЧИНЕ ДО НЕГО НЕ ДОХОДИЛО. Ровно та же асимметрия по оси
    # ВЕЛИЧИНЫ, какую ревизия Фазы 6 (`CR-02`) закрыла по оси ИСТОЧНИКА:
    # приведение к целому удавалось, отказ случался позже — уже в SQLAlchemy, —
    # и порядок «сначала граница, потом права, потом источник» зависел от того,
    # что написано выше в функции. С границей на сигнатуре он не зависит.
    _BoundedEntry(
        key="app/pages/admin.py::POST /admin/workers/{account_id}/restart → адрес account_id",
        method="POST",
        address="/admin/workers/{value}/restart",
        parameter="account_id",
        live="account",
        identity="admin",
    ),
    _BoundedEntry(
        # ⚠️ ТЕЛО ПОДАЁТСЯ, И ЭТО ЗАМЕР, А НЕ ОСТОРОЖНОСТЬ: обработчик несёт
        # обязательное поле формы `task_id`, и на пустом теле отказ валидации
        # пришёл бы ЗА ОТСУТСТВИЕ ПОЛЯ — строка матрицы зеленела бы, не сказав
        # ни слова о границе идентификатора.
        key="app/pages/admin.py::POST /admin/queue/{account_id}/drop → адрес account_id",
        method="POST",
        address="/admin/queue/{value}/drop",
        parameter="account_id",
        live="account",
        identity="admin",
        body="task_id=задача-посева",
    ),
    _BoundedEntry(
        key="app/pages/admin.py::GET /admin/users/{user_id} → адрес user_id",
        method="GET",
        address="/admin/users/{value}",
        parameter="user_id",
        live="target",
        identity="admin",
    ),
    _BoundedEntry(
        key="app/pages/admin.py::GET /admin/users/{user_id}/history → адрес user_id",
        method="GET",
        address="/admin/users/{value}/history",
        parameter="user_id",
        live="target",
        identity="admin",
    ),
    _BoundedEntry(
        key="app/pages/admin.py::GET /admin/users/{user_id}/history/partial → адрес user_id",
        method="GET",
        address="/admin/users/{value}/history/partial",
        parameter="user_id",
        live="target",
        identity="admin",
    ),
    _BoundedEntry(
        # ⚠️ МАРШРУТ КАРТОЧКИ ЗАПИСИ ЖУРНАЛА ДАЁТ ДВА ВХОДА, А НЕ ОДИН, и обе
        # строки стоят рядом намеренно: склеивание маршрута с двумя
        # идентификаторами в один вход есть ровно та ошибка счёта, которую
        # соседний реестр расхождения заводился исправить.
        key="app/pages/admin.py::GET /admin/users/{user_id}/history/{log_id} → адрес user_id",
        method="GET",
        address="/admin/users/{value}/history/{target_log}",
        parameter="user_id",
        live="target",
        identity="admin",
    ),
    _BoundedEntry(
        key="app/pages/admin.py::GET /admin/users/{user_id}/history/{log_id} → адрес log_id",
        method="GET",
        address="/admin/users/{target}/history/{value}",
        parameter="log_id",
        live="target_log",
        identity="admin",
    ),
    _BoundedEntry(
        key="app/pages/admin.py::POST /admin/users/{user_id}/unlimited → адрес user_id",
        method="POST",
        address="/admin/users/{value}/unlimited",
        parameter="user_id",
        live="target",
        identity="admin",
    ),
    _BoundedEntry(
        key="app/pages/admin.py::POST /admin/users/{user_id}/impersonate → адрес user_id",
        method="POST",
        address="/admin/users/{value}/impersonate",
        parameter="user_id",
        live="target",
        identity="admin",
    ),
    _BoundedEntry(
        key="app/pages/admin.py::POST /admin/users/{user_id}/block → адрес user_id",
        method="POST",
        address="/admin/users/{value}/block",
        parameter="user_id",
        live="target",
        identity="admin",
    ),
    _BoundedEntry(
        key="app/pages/admin.py::POST /admin/users/{user_id}/delete → адрес user_id",
        method="POST",
        address="/admin/users/{value}/delete",
        parameter="user_id",
        live="target",
        identity="admin",
    ),
)


# Три величины ВНЕ диапазона колонки. Каждая взята по СВОЕМУ основанию, а не для
# числа: `ABOVE_THE_COLUMN` — соседняя граница, до правки тихо неотличимая от
# годной; `BEYOND_ANY_DRIVER` — величина, роняющая сам драйвер; `BELOW_THE_DOMAIN`
# — величина ниже домена автоинкремента.
REFUSED_VALUES: tuple[str, ...] = (
    ABOVE_THE_COLUMN,
    BEYOND_ANY_DRIVER,
    BELOW_THE_DOMAIN,
)


async def _seed_live_row_set(db: AsyncSession) -> dict[str, int]:
    """ЖИВОЙ набор строк пользователя фикстуры входа — по одной на сущность.

    Возвращается отображение «имя сущности → её идентификатор»: именно из него
    матрица берёт ЖИВЫЕ величины для антивакуума и живые поля адреса на местах
    НЕиспытуемых параметров.

    ⚠️ СОСТОЯНИЕ АККАУНТА `syncing` — ВЫБОР ВЕТКИ, А НЕ УКРАШЕНИЕ ПОСЕВА, и
    названо здесь, а не оставлено читателю. Живой запуск синхронизации
    (`POST /accounts/{id}/sync-groups`) на аккаунте в состоянии `active` пошёл бы
    в НАСТОЯЩИЙ мессенджер: суита получила бы сетевой вызов, а исход правила
    стал бы зависеть от того, чего у суиты нет. Состояние `syncing` уводит
    обработчик в ступень первую гарда повторного запуска — переход на экран
    групп, — то есть живая величина ДОЕЗЖАЕТ ДО ТЕЛА обработчика, а тело
    возвращается детерминированно. Предмет антивакуума — ДОПУЩЕНА ли живая
    величина границей, и он наблюдается полностью; что тело делает дальше —
    предмет собственных суит этих модулей, и они прогоняются отдельно.

    ⚠️ ТИП АККАУНТА `tg_user` — ТОТ ЖЕ ВЫБОР ВЕТКИ ПО ТОМУ ЖЕ ОСНОВАНИЮ: повтор
    синхронизации (`POST /accounts/{id}/retry-sync`) принимает только `wa` и
    `max` и на `tg_user` возвращает переход, не обращаясь ни к какому мосту.

    ⚠️ ЗАПИСЬ ЖУРНАЛА ПОСЕЯНА УСПЕШНОЙ по тому же основанию: повтор успешной
    отправки возвращает переход ДО обращения к брокеру очереди. Повтор
    НЕуспешной ушёл бы в `celery.send_task`, то есть к внешней системе.
    """
    user = (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()

    account = MessengerAccount(
        user_id=user.id,
        type="tg_user",
        credentials="сессия посева",
        status="syncing",
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)

    group = await seed_group(db, account.id)

    ad = Ad(
        user_id=user.id,
        title="Объявление для матрицы",
        text="Текст объявления",
        images=[],
        status=AD_STATUS_PUBLISHED,
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[group.id],
        days_of_week=[1],
        times_of_day=["10:00"],
        next_run_at=a_future_run_moment(),
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    log = SendLog(
        user_id=user.id,
        ad_id=ad.id,
        group_id=group.id,
        status=STATUS_OK,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    # ⚠️ ОТДЕЛЬНЫЙ ПОЛЬЗОВАТЕЛЬ-ЦЕЛЬ ДЛЯ АДМИНСКИХ ВХОДОВ, И ЭТО МИТИГАЦИЯ, А НЕ
    # АККУРАТНОСТЬ (T-10-29-05). Два входа админского перечня НЕОБРАТИМЫ и
    # действуют НАД ЛИЧНОСТЬЮ: удаление пользователя стирает учётную запись
    # целиком, вход под пользователем перевыписывает cookie. Прогон, подавший
    # им саму АДМИНИСТРАТИВНУЮ личность, оставил бы следующие строки матрицы
    # без личности вовсе — и покрасил бы их отказом ПРАВ, то есть дал бы ложный
    # красный о границе величины. Цель посеяна своя, и почта у неё уникальная:
    # посев зовётся ПО РАЗУ НА ВХОД, и вторая цель с той же почтой уронила бы
    # уникальность колонки.
    target = User(
        email=f"target-{uuid.uuid4().hex[:12]}@test.com",
        password_hash="ХЕШ-ЦЕЛИ-АДМИНСКИХ-ВХОДОВ",
        name="Цель админских входов",
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)

    # Запись журнала ЦЕЛИ, а не пользователя фикстуры: карточка записи
    # административного журнала сличает `log.user_id` с идентификатором из
    # адреса, и чужая запись увела бы живую величину в переход «не его запись»
    # — то есть антивакуум перестал бы наблюдать тело обработчика.
    target_log = SendLog(
        user_id=target.id,
        ad_id=ad.id,
        group_id=group.id,
        status=STATUS_OK,
    )
    db.add(target_log)
    await db.commit()
    await db.refresh(target_log)

    return {
        "account": account.id,
        "group": group.id,
        "ad": ad.id,
        "schedule": schedule.id,
        "log": log.id,
        "target": target.id,
        "target_log": target_log.id,
    }


async def _assume(client: AsyncClient, identity: str, admin_email: str) -> None:
    """Взять ЛИЧНОСТЬ, под которой пойдёт следующее обращение матрицы.

    ⚠️ ВХОД ВЫПОЛНЯЕТСЯ ЯВНО, А НЕ ЗАКАЗЫВАЕТСЯ ФИКСТУРОЙ, И ЭТО ЗАМЕР
    УСТРОЙСТВА ФИКСТУР, А НЕ ПРЕДПОЧТЕНИЕ. `authed_client` и `admin_client`
    (`tests/conftest.py`) возвращают ОДИН И ТОТ ЖЕ объект клиента: они
    различаются только тем, чью cookie оставили на нём последней. Правило,
    заказавшее обе фикстуры и положившееся на порядок их разрешения, утверждало
    бы о порядке фикстур, а не о границе; правило, заказавшее одну, гоняло бы
    половину матрицы под чужой личностью.

    ⚠️ ВХОД НУЖЕН И ПОСЛЕ КАЖДОГО ЖИВОГО ПРОГОНА ВХОДА ПОД ПОЛЬЗОВАТЕЛЕМ:
    удавшаяся имперсонация перевыписывает ту же cookie на личность цели, и
    следующая строка матрицы пошла бы уже не от администратора.
    """
    email = admin_email if identity == "admin" else USER_IDENTITY_EMAIL
    await client.post(
        "/login",
        data={"email": email, "password": IDENTITY_PASSWORD},
        follow_redirects=False,
    )


async def _entry_outcome(
    client: AsyncClient, entry: _BoundedEntry, address: str
) -> str:
    """СНЯТЫЙ КОД одного обращения по одному адресу — строкой.

    ⚠️ ВЕЛИЧИНА УЖЕ ПОДСТАВЛЕНА В АДРЕС ФОРМАТИРОВАНИЕМ СТРОКИ, А НЕ
    ПРИВЕДЕНИЕМ К ЦЕЛОМУ — по тому же основанию, что и у `_delete_ad` выше:
    величина в двадцать шесть знаков в приведении потеряла бы ровно то свойство,
    ради которого взята.
    """
    if entry.method == "POST":
        response = await client.post(
            address, content=entry.body, headers=FORM_HEADERS, follow_redirects=False
        )
    else:
        response = await client.get(address, follow_redirects=False)
    return str(response.status_code)


@pytest.mark.asyncio
async def test_every_bounded_input_refuses_a_value_outside_the_column(
    authed_client: AsyncClient,
    admin_client: AsyncClient,
    test_settings,
    db_session: AsyncSession,
):
    """КАЖДЫЙ вход матрицы отвечает отказом ВАЛИДАЦИИ на величине вне диапазона.

    Отображение сличается ЦЕЛИКОМ, и текст отказа называет ВСЕ несогласные
    строки со снятыми кодами.

    ⚠️ ОБЕ ФИКСТУРЫ ЗАКАЗАНЫ РАДИ ЗАВЕДЕНИЯ ОБЕИХ УЧЁТНЫХ ЗАПИСЕЙ, А ДЕЙСТВУЮЩАЯ
    ЛИЧНОСТЬ БЕРЁТСЯ ЯВНО (`_assume`): объект клиента у них ОДИН, и полагаться
    на порядок их разрешения значило бы утверждать о порядке фикстур.
    """
    live = await _seed_live_row_set(db_session)
    client = authed_client
    assumed: str | None = None

    disagreed: list[str] = []
    for entry in BOUNDED_ENTRIES:
        if entry.identity != assumed:
            await _assume(client, entry.identity, test_settings.admin_email)
            assumed = entry.identity
        for value in REFUSED_VALUES:
            address = entry.address.format(value=value, **live)
            code = await _entry_outcome(client, entry, address)
            if code != VALIDATION_REFUSAL:
                disagreed.append(
                    f"{entry.key} ← {value} = {code} "
                    f"(ожидалось {VALIDATION_REFUSAL}; {entry.method} {address})"
                )

    assert not disagreed, (
        "ГРАНИЦА ВЕЛИЧИНЫ ИДЕНТИФИКАТОРА СТОИ́Т НЕ НА ВСЕХ ВХОДАХ. Несогласных "
        f"строк {len(disagreed)} из "
        f"{len(BOUNDED_ENTRIES) * len(REFUSED_VALUES)}:\n  "
        + "\n  ".join(disagreed)
        + "\n\nВеличина вне диапазона колонки обязана отвергаться ДО тела "
        "обработчика на КАЖДОМ входе, а не на том, куда смотрели (`CR-01` "
        "пятого круга ревизии)"
    )


@pytest.mark.asyncio
async def test_every_bounded_input_admits_the_value_at_the_column(
    authed_client: AsyncClient,
    admin_client: AsyncClient,
    test_settings,
    db_session: AsyncSession,
):
    """СМЕЖНОСТЬ, ВТОРАЯ СТОРОНА СТЫКА — НА КАЖДОМ ВХОДЕ, А НЕ НА ОБРАЗЦЕ.

    Величина, РАВНАЯ границе, в диапазоне колонки лежит, и отвергать её граница
    права не имеет. Без этого правила помощник, отвергающий ВСЁ, дал бы зелёный
    прогон правила выше и границей не был бы.
    """
    live = await _seed_live_row_set(db_session)
    client = authed_client
    assumed: str | None = None

    disagreed: list[str] = []
    for entry in BOUNDED_ENTRIES:
        if entry.identity != assumed:
            await _assume(client, entry.identity, test_settings.admin_email)
            assumed = entry.identity
        address = entry.address.format(value=AT_THE_COLUMN, **live)
        code = await _entry_outcome(client, entry, address)
        if code == VALIDATION_REFUSAL or code.startswith("5"):
            disagreed.append(
                f"{entry.key} ← {AT_THE_COLUMN} = {code} "
                f"({entry.method} {address})"
            )

    assert not disagreed, (
        "ГРАНИЦА ОТВЕРГЛА ВЕЛИЧИНУ, ЛЕЖАЩУЮ В ДИАПАЗОНЕ КОЛОНКИ, либо уронила "
        f"на ней обработчик. Несогласных строк {len(disagreed)} из "
        f"{len(BOUNDED_ENTRIES)}:\n  " + "\n  ".join(disagreed)
    )


@pytest.mark.asyncio
async def test_every_bounded_input_still_admits_a_live_value(
    authed_client: AsyncClient,
    admin_client: AsyncClient,
    test_settings,
    db_session: AsyncSession,
):
    """АНТИВАКУУМ ПО ВСЕМУ ПЕРЕЧНЮ, А НЕ ПО ОДНОЙ СТРОКЕ.

    Правило, отвергающее ВСЁ, дало бы тот же зелёный на правилах отказа выше.
    Здесь на КАЖДЫЙ вход подаётся ЖИВАЯ посеянная величина, и её исход обязан не
    быть ни отказом валидации, ни отказом обработчика.

    ⚠️ ПОСЕВ СВЕЖИЙ НА КАЖДЫЙ ВХОД, И ЭТО НЕ ОСТОРОЖНОСТЬ. Четыре входа перечня
    НЕОБРАТИМЫ (удаление аккаунта и удаление группы), и общий посев сделал бы
    исход входов, идущих следом, зависимым от ПОРЯДКА перечня — то есть правило
    начало бы утверждать о порядке, а не о границе.
    """
    disagreed: list[str] = []
    live_values_run = 0
    client = authed_client

    for entry in BOUNDED_ENTRIES:
        # ⚠️ ЛИЧНОСТЬ БЕРЁТСЯ ЗАНОВО ПЕРЕД КАЖДЫМ ВХОДОМ, А НЕ ПРИ СМЕНЕ ГРУППЫ,
        # И ЭТО НЕ ИЗБЫТОЧНОСТЬ. Правило подаёт ЖИВЫЕ величины, а среди входов
        # есть тот, чьё УДАВШЕЕСЯ тело перевыписывает cookie на личность цели
        # (вход под пользователем). Проверка «личность та же, что была
        # заказана» здесь солгала бы: заказана — та же, действует — чужая.
        await _assume(client, entry.identity, test_settings.admin_email)
        live = await _seed_live_row_set(db_session)
        address = entry.address.format(value=live[entry.live], **live)
        code = await _entry_outcome(client, entry, address)
        live_values_run += 1
        if code == VALIDATION_REFUSAL or code.startswith("5"):
            disagreed.append(
                f"{entry.key} ← живая величина {live[entry.live]} = {code} "
                f"({entry.method} {address})"
            )

    assert live_values_run == len(BOUNDED_ENTRIES), (
        f"живых величин прогнано {live_values_run}, а входов "
        f"{len(BOUNDED_ENTRIES)} — антивакуум прогнан не по всему перечню"
    )
    assert not disagreed, (
        "ГРАНИЦА ОТВЕРГЛА ЖИВУЮ ВЕЛИЧИНУ либо уронила на ней обработчик — она "
        f"отвергает не то, что объявила. Несогласных строк {len(disagreed)} из "
        f"{len(BOUNDED_ENTRIES)}:\n  " + "\n  ".join(disagreed)
    )


@pytest.mark.asyncio
async def test_the_editor_without_the_schedule_flag_is_not_a_validation_refusal(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ПУСТОЕ значение признака раскрытого расписания остаётся ЗАКОННЫМ.

    ⚠️ БЕЗ ЭТОГО ПРАВИЛА ГРАНИЦА, ПОСТАВЛЕННАЯ НА ПРИЗНАК, БЫЛА БЫ НЕОТЛИЧИМА
    ОТ ЗАПРЕТА ОТКРЫВАТЬ РЕДАКТОР. Расписание может быть НЕ ВЫБРАНО — это
    основное состояние экрана, а не край: ссылка на редактор БЕЗ параметра
    стои́т в разметке карточки расписания (`app/templates/ads/includes/
    sched_card.html`) ровно для свёртывания открытой карточки. Граница величины
    к ОТСУТСТВИЮ значения не применяется, и правило это наблюдает, а не
    подразумевает.
    """
    live = await _seed_live_row_set(db_session)

    outcome = await _entry_outcome(
        authed_client,
        _BoundedEntry(
            key="контроль пустого признака",
            method="GET",
            address="/ads/{ad}/edit",
            parameter="sched",
            live="schedule",
        ),
        f"/ads/{live['ad']}/edit",
    )

    assert outcome != VALIDATION_REFUSAL and not outcome.startswith("5"), (
        "редактор БЕЗ признака раскрытого расписания ответил отказом валидации "
        f"либо отказом обработчика (снято → {outcome!r}). Пустое значение есть "
        "законное состояние: расписание может быть не выбрано, и граница "
        "ВЕЛИЧИНЫ к ОТСУТСТВИЮ значения не применяется"
    )


# =============================================================================
# ГЕЙТ ПОЛНОТЫ ГРАНИЦЫ ПО ВСЕМУ КАТАЛОГУ СТРАНИЧНОГО СЛОЯ
# =============================================================================
#
# ПРЕДМЕТ ЭТОГО РАЗДЕЛА — СЛЕДУЮЩИЙ ВХОД, А НЕ СЕГОДНЯШНИЕ. Матрица выше
# стережёт РОВНО ТЕ входы, которые в неё внесены руками: маршрут, добавленный
# завтра с неограниченным идентификатором, оставит её зелёной — она о нём не
# знает. Ревизия пятого круга (`CR-01`, вторая половина предписания) просит
# «widen the gate so the next unbounded input cannot appear silently»: заменить
# перечень РАЗБОРОМ КАТАЛОГА, то есть краснеть В МОМЕНТ ВВЕДЕНИЯ входа, а не
# следующим кругом верификации.
#
# ⚠️ РАЗБОР ДЕРЕВА, А НЕ СТРОК. Построчный поиск считал бы вхождение имени в
# докстринг и в комментарий — то есть объяснение роняло бы утверждение, — и
# ломался бы от переноса декоратора на вторую строку. Форма взята целиком у
# `tests/test_pages/test_origin_guard_on_destructive_routes.py`: реестр,
# собранный ЧТЕНИЕМ, объявленное число вселенной, объявленное число изъятий,
# замыкающее требование «каждый найденный», антивакуум и отрицательные контроли,
# доказывающие, что правило КРАСНЕЕТ.
#
# ⚠️ ВСТРЕЧНАЯ ОТСЫЛКА К ИНВАРИАНТУ МОДУЛЯ РАСПИСАНИЙ. Этот раздел НЕ ЗАМЕНЯЕТ
# и не поглощает правил `tests/test_pages/test_editor_schedules.py`, и предметы
# у них РАЗНЫЕ:
#   — `test_no_schedule_route_answers_with_a_handler_failure_on_an_out_of_range_identifier`
#     наблюдает ПОВЕДЕНИЕ пяти РЕАЛЬНЫХ запросов, доезжающих до отказа
#     валидации, — включая порядок в теле; статическая проверка сигнатуры этого
#     не наблюдает и наблюдать не может, она наблюдает ОБЪЯВЛЕНИЕ;
#   — `test_every_identifier_input_of_the_schedule_routes_carries_the_shared_bound`
#     стережёт ИНВАРИАНТ, объявленный шапкой ТОГО модуля («прямой POST мимо
#     браузера обязан давать отказ валидации, а не 500»), и вселенная у него —
#     один файл;
#   — правила ниже стерегут свойство ПРОЕКТА: ни один вход ни одного модуля
#     страничного слоя не появится без границы.
# Ни одно из трёх не выводится из другого, и снос любого ради «неповторения»
# заменил бы наблюдение объявлением либо инвариант модуля — свойством проекта.

CATALOGUE_DIRECTORY = APP_DIRECTORY / "pages"

# ПРИЗНАК ИДЕНТИФИКАТОРА В ИМЕНИ: `id` целиком либо хвост `_id`. `valid`, `paid`
# и прочие слова, кончающиеся теми же двумя буквами, признаком НЕ являются —
# иначе правило судило бы о параметрах, к идентификаторам отношения не имеющих.
# Выражение перенесено дословно из `_IDENTIFIER_PARAM`
# (`tests/test_pages/test_editor_schedules.py`): две копии ОДНОГО признака
# разошлись бы молча.
_IDENTIFIER_NAME_MARK = re.compile(r"(?:^id|_id)$")

# ⚠️ ВСЕЛЕННАЯ НАЗВАНА ДВУМЯ ПРИЗНАКАМИ, И ЭТО ЗАМЕР, А НЕ ОСТОРОЖНОСТЬ. Каждый
# признак ПОРОЗНЬ пропускает то, что накрывает второй:
#   — ПРИЗНАК АДРЕСА (имя параметра стои́т местозаполнителем в пути маршрута)
#     машинно чёток и не зависит от того, как параметр назвали. Но он один НЕ
#     НАКРЫЛ БЫ курсор постраничного вывода групп (`after_id`,
#     `app/pages/account_groups.py`), закрытый планом 10-28: тот приезжает
#     ПАРАМЕТРОМ ЗАПРОСА и в пути не стоит;
#   — ПРИЗНАК ИМЕНИ (окончание на `id`/`_id`) накрывает курсор. Но он один НЕ
#     НАКРЫЛ БЫ идентификатор пути, названный будущей фазой иначе, — а имя
#     параметра есть выбор автора, тогда как местозаполнитель пути есть
#     объявленный контракт маршрута.
# Ни один вход не обязан удовлетворять ОБОИМ: вселенная есть ОБЪЕДИНЕНИЕ.

# ИЗЪЯТИЕ ВЕЛИЧИН ПОСТРАНИЧНОГО ВЫВОДА — ЗАПИСЬ С ОБОСНОВАНИЕМ, А НЕ ОТСУТСТВИЕ
# В РАЗБОРЕ.
#
# ОСНОВАНИЕ ВЗЯТО У ДЕЙСТВУЮЩЕГО ГЕЙТА ДОСЛОВНО: смещение и размер порции НЕ
# ЕСТЬ идентификатор, они не уезжают операндом сравнения по колонке
# идентификатора, и отказ по ним не говорит ничего о ВЛАДЕНИИ строкой. Граница
# у них своя и по своему основанию (`le=100` у размера порции — защита от
# выдачи, а не от переполнения колонки), и требовать от них границы
# ИДЕНТИФИКАТОРА значило бы требовать неверного числа.
#
# ⚠️ ИЗЪЯТИЕ ОБЪЯВЛЕНО ЗАПИСЬЮ ИМЕННО ЗАТЕМ, ЧТОБЫ ЧИТАТЕЛЬ УЗНАЛ О НЁМ ИЗ
# ОБЪЯВЛЕНИЯ, А НЕ ИЗ РАЗБОРА. Правило, молча не смотрящее на часть параметров,
# имеет слепую зону, о которой известно только тому, кто прочёл его код.
PAGINATION_EXCLUSION_NAMES = frozenset({"offset", "limit"})

# ЛЕТОПИСЬ ЧИСЛА ИЗЪЯТЫХ ВЕЛИЧИН ПОСТРАНИЧНОГО ВЫВОДА:
#   0 → 13, Фаза 10, план 10-30, задача 1. Замер разбором каталога: по одной
#   величине у `account_groups.py`, по паре у `accounts.py`, `ads.py` и
#   `schedules.py`, три у `admin.py` и три у `history.py`. Число движется — это
#   решение о том, что добавленная величина ДЕЙСТВИТЕЛЬНО есть постраничный
#   вывод, а не идентификатор, названный коротким именем.
PAGINATION_EXCLUSION_DECLARED = 13

# ЛЕТОПИСЬ ЧИСЛА ВСЕЛЕННОЙ — ПОСТАВЛЕНО ПРОГОНОМ ПОКРАСНЕВШЕГО ПРАВИЛА:
#   0 → 35, Фаза 10, план 10-30, задача 1. ЗАВЕДОМО НЕВЕРНОЕ ЧИСЛО (`0`)
#   вписано ПЕРВЫМ, замер `35` прочитан из текста отказа. Число, вписанное по
#   итогу ЗЕЛЁНОГО прогона, равнялось бы тому, что есть, ПО ПОСТРОЕНИЮ и не
#   стерегло бы ничего.
#
#   ⚠️ ЗАМЕР СЛИЧЁН С СУММОЙ ЗАКРЫТОГО, И СЛАГАЕМЫЕ НАЗВАНЫ. Партия закрыла
#   ДВАДЦАТЬ ДЕВЯТЬ входов: 1 (план 10-24) + 17 (план 10-28) + 11 (план 10-29).
#   Один из семнадцати — признак раскрытого расписания редактора (`sched`) — во
#   вселенную НЕ ВХОДИТ: он вне обоих её признаков и живёт записью ПРИЛОЖЕНИЯ,
#   будучи закрытым. Остаётся 28. Модуль расписаний закрыт РАНЬШЕ партии, планом
#   10-12: отчёт третьего круга назвал ПЯТЬ ВХОДОВ, но считал их МАРШРУТАМИ, а
#   вселенная считает ПАРАМЕТРАМИ — тех же шести маршрутов параметров СЕМЬ
#   (`schedules_create` несёт два, `schedules_update` — три). 28 + 7 = 35.
#   Расхождения с суммой закрытого НЕТ; расходятся ЕДИНИЦЫ СЧЁТА, и обе названы.
CATALOGUE_UNIVERSE_DECLARED = 35

# ЛЕТОПИСЬ ЧИСЛА ЗАПИСЕЙ ПРИЛОЖЕНИЯ — то же основание, тот же приём:
#   0 → 10, Фаза 10, план 10-30, задача 1. Ориентир планировщика знал ОДНОГО
#   кандидата (`sched`); замер дал ДЕСЯТЬ, и расхождение названо поимённо в
#   комментарии к самому перечню. Пустое приложение тоже было бы законным — но
#   тогда ноль стоял бы здесь ЯВНО: именованный ноль стережёт появление первой
#   записи, отсутствующее объявление — нет.
CATALOGUE_APPENDIX_DECLARED = 10

# ЧИСЛО КОРНЕВЫХ ПСЕВДОНИМОВ НЕЙТРАЛЬНОГО МОДУЛЯ. Перечень узнаваемых имён
# СОБИРАЕТСЯ ЧТЕНИЕМ `app/pages/identifiers.py`, а не выписывается здесь второй
# копией: выписанный перечень разошёлся бы с модулем молча — ровно тем способом,
# каким прежде расходилась сама граница. Число объявлено затем, чтобы
# ИСЧЕЗНОВЕНИЕ псевдонима из нейтрального модуля (то есть потеря узнаваемости
# половины входов) краснело здесь, а не зеленело пустым перечнем.
BOUNDED_ALIAS_ROOTS_DECLARED = 3

# ЧИСЛО КОРНЕВЫХ POST-ПСЕВДОНИМОВ НЕЙТРАЛЬНОГО МОДУЛЯ — псевдонимов БЕЗ границы
# фреймворка (`PostIdPath`, `PostIdForm`, `OptionalPostIdForm`), заведённых
# решением D-07 Фазы 11 (план 11-02). Перечень СОБИРАЕТСЯ ЧТЕНИЕМ того же
# модуля, что и перечень ограниченных, и по той же причине: выписанная копия
# разошлась бы с модулем молча. Исчезновение псевдонима краснеет здесь, а не
# зеленеет пустым перечнем — правило «проверка первым использованием» на пустом
# перечне не стерегло бы ни одного входа.
#
# ЛЕТОПИСЬ: 0 → 3, Фаза 11, план 11-02, задача 1.
POST_ALIAS_ROOTS_DECLARED = 3

# ЕДИНСТВЕННЫЙ ПОМОЩНИК ПРОВЕРКИ ВНУТРИ ОБРАБОТЧИКА (D-07: один на проект).
# Имя стоит константой затем, чтобы разбор и текст отказа называли одно и то же.
FIRST_USE_CHECK_HELPER = "id_in_column"


@dataclass(frozen=True)
class _AppendixEntry:
    """Вход, НЕ ПОКРЫТЫЙ НИ ОДНИМ признаком вселенной, — названный поимённо.

    ⚠️ ПРИЛОЖЕНИЕ ЕСТЬ ЕДИНСТВЕННОЕ, ЧЕМ НЕПОКРЫТЫЙ ВХОД НЕ ВЫПАДАЕТ МОЛЧА.
    Правило, объявляющее полноту по двум признакам, имеет слепую зону — вход,
    не попавший ни под один. Слепая зона, о которой не объявлено, есть
    утверждение полноты, которое утверждает меньше, чем говорит (предмет
    `WR-05`).

    Поля: `key` — тот же ключ, каким вход назван замером; `reason` —
    ОБОСНОВАНИЕ, почему вход вне вселенной; `removal` — УСЛОВИЕ СНЯТИЯ записи;
    `verdict` — `"safe"` либо `"open"`; `observed` — СНЯТЫЙ исход.

    ⚠️ `verdict` РАЗВОДИТ ДВЕ РАЗНЫЕ ВЕЩИ, КОТОРЫЕ ОДНО СЛОВО «ПРИЛОЖЕНИЕ»
    СКЛЕИЛО БЫ В ОДНУ. `safe` — вход, которому граница ИДЕНТИФИКАТОРА не нужна
    по существу (величина не есть целое колонки идентификатора). `open` — вход,
    которому она НУЖНА и у которого её НЕТ: отказ обработчика на нём
    ВОСПРОИЗВЕДЁН и записан в `observed`. Запись `open` НЕ ЕСТЬ разрешение —
    она есть НАЗВАННЫЙ ДОЛГ: без неё дефект был бы не «принят», а невидим.
    """

    key: str
    reason: str
    removal: str
    verdict: str
    observed: str


# ⚠️ СОДЕРЖИМОЕ ПРИЛОЖЕНИЯ СНЯТО ЗАМЕРОМ, А НЕ ВЫВЕДЕНО ИЗ ОЖИДАНИЯ. Ориентир
# планировщика знал ОДНОГО кандидата — признак раскрытого расписания редактора.
# Замер по каталогу дал ДЕСЯТЬ, и девять из них — параметры, объявленные
# СТРОКОЙ и приводимые к целому ВНУТРИ обработчика: признак «объявлен целым»
# их не видит. ШЕСТЬ ИЗ ЭТИХ ДЕВЯТИ ДОЕЗЖАЮТ ДО СРАВНЕНИЯ ПО КОЛОНКЕ БЕЗ
# ГРАНИЦЫ, и отказ обработчика на них ВОСПРОИЗВЕДЁН (`observed`). Это находка
# настоящего плана, а не принятое решение: правка `app/` настоящему плану
# запрещена его собственным составом (`files_modified`), и запись здесь есть
# способ, которым долг назван, а не способ, которым он списан.
CATALOGUE_APPENDIX: tuple[_AppendixEntry, ...] = (
    _AppendixEntry(
        key="app/pages/ads.py::GET /ads/{ad_id}/edit → sched",
        reason=(
            "объявлен целым и ограничен ВСТРОЕННОЙ записью "
            "(`Query(None, ge=1, le=ID_MAX)`, план 10-28), но имя его на признак "
            "идентификатора не оканчивается и местозаполнителем пути не стои́т — "
            "то есть он вне ОБОИХ признаков вселенной, будучи закрытым"
        ),
        removal="переименование параметра в оканчивающийся на признак идентификатора",
        verdict="safe",
        observed="GET /ads/1/edit?sched=99999999999999999999999999 → 422",
    ),
    _AppendixEntry(
        key="app/pages/accounts.py::GET /accounts/connect/tg_user/qr-status → session_id",
        reason=(
            "величина есть ключ сессии авторизации Telegram, объявленный СТРОКОЙ "
            "и остающийся строкой: он не есть целое колонки идентификатора и "
            "операндом сравнения по ней не уезжает"
        ),
        removal="перевод ключа сессии на целочисленную колонку",
        verdict="safe",
        observed="строка остаётся строкой; сравнения по колонке идентификатора нет",
    ),
    _AppendixEntry(
        key="app/pages/admin.py::POST /queue/{account_id}/drop → task_id",
        reason=(
            "величина есть идентификатор задачи очереди Celery — строка, "
            "сравниваемая со строками очереди, а не целое колонки"
        ),
        removal="перевод идентификатора задачи на целочисленную колонку",
        verdict="safe",
        observed="строка остаётся строкой; сравнения по колонке идентификатора нет",
    ),
    _AppendixEntry(
        key="app/pages/groups.py::GET /groups; GET /groups/{deep_link:path} → deep_link",
        reason=(
            "местозаполнитель пути ЕСТЬ, но величина объявлена строкой и строкой "
            "остаётся: это непрозрачный токен приглашения, а не целое колонки"
        ),
        removal="перевод адреса на целочисленный идентификатор группы",
        verdict="safe",
        observed="GET /groups/xxxxxxxx… → 302",
    ),
    _AppendixEntry(
        key="app/pages/ads.py::POST /ads/new → ad_id",
        reason=(
            "ОБЪЯВЛЕН СТРОКОЙ (`str | None = Form(None)`) и приводится к целому "
            "ВНУТРИ обработчика (`int(ad_id)`, `app/pages/ads.py`), после чего "
            "уезжает операндом сравнения по колонке (`Ad.id == requested_id`). "
            "Признак «объявлен целым» его НЕ ВИДИТ — граница на границе "
            "приложения отсутствует"
        ),
        removal=(
            "объявление параметра ограниченным псевдонимом либо постановка "
            "границы величины до сравнения по колонке"
        ),
        verdict="open",
        observed=(
            "POST /ads/new с полем ad_id=99999999999999999999999999 → 500 "
            "(OverflowError, app/pages/ads.py:629), снято 2026-09-08"
        ),
    ),
    _AppendixEntry(
        key="app/pages/history.py::GET /history → account_id",
        reason=(
            "ОБЪЯВЛЕН СТРОКОЙ (`str | None = Query(default=None)`) и приводится "
            "к целому помощником `parse_account_id` БЕЗ границы, после чего "
            "уезжает в условие фильтра по колонке идентификатора аккаунта"
        ),
        removal="постановка границы величины в `parse_account_id` либо в сигнатуре",
        verdict="open",
        observed=(
            "GET /history?account_id=99999999999999999999999999 → 500 "
            "(OverflowError, app/pages/history.py:1057), снято 2026-09-08"
        ),
    ),
    _AppendixEntry(
        key="app/pages/history.py::GET /history/partial → account_id",
        reason="то же основание, что у `GET /history`: строка, приводимая `parse_account_id` без границы",
        removal="постановка границы величины в `parse_account_id` либо в сигнатуре",
        verdict="open",
        observed=(
            "GET /history/partial?account_id=99999999999999999999999999 → 500 "
            "(OverflowError, app/pages/history.py:586), снято 2026-09-08"
        ),
    ),
    _AppendixEntry(
        key="app/pages/history.py::GET /history/export → account_id",
        reason="то же основание: строка, приводимая `parse_account_id` без границы",
        removal="постановка границы величины в `parse_account_id` либо в сигнатуре",
        verdict="open",
        observed=(
            "GET /history/export?account_id=99999999999999999999999999 → 500, "
            "снято 2026-09-08"
        ),
    ),
    _AppendixEntry(
        key="app/pages/admin.py::GET /users/{user_id}/history → account_id",
        reason=(
            "то же основание: строка, приводимая ТЕМ ЖЕ `parse_account_id` "
            "(админка зовёт помощника через границу модуля) без границы"
        ),
        removal="постановка границы величины в `parse_account_id` либо в сигнатуре",
        verdict="open",
        observed=(
            "GET /admin/users/1/history?account_id=99999999999999999999999999 → 500, "
            "снято 2026-09-08"
        ),
    ),
    _AppendixEntry(
        key="app/pages/admin.py::GET /users/{user_id}/history/partial → account_id",
        reason="то же основание: строка, приводимая `parse_account_id` без границы",
        removal="постановка границы величины в `parse_account_id` либо в сигнатуре",
        verdict="open",
        observed=(
            "GET /admin/users/1/history/partial?account_id=99999999999999999999999999 "
            "→ 500, снято 2026-09-08"
        ),
    ),
)


# =============================================================================
# Разборщики каталога. ИСХОДНИКИ ПРИХОДЯТ ПАРАМЕТРОМ
# =============================================================================
#
# ⚠️ ПОДАЧА ИСХОДНИКОВ ПАРАМЕТРОМ ОБЯЗАТЕЛЬНА, А НЕ УДОБНА. Без неё зубы правила
# пришлось бы ЗАЯВЛЯТЬ, а боевой файл — ПРАВИТЬ ради доказательства: подмена
# живёт строкой в памяти, и разборщику подаётся она. Приём и его основание
# взяты у `destructive_route_handlers`
# (`tests/test_pages/test_origin_guard_on_destructive_routes.py`).

_HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})
_ROUTE_PLACEHOLDER = re.compile(r"\{([^}:]+)")


def _catalogue_sources() -> dict[str, str]:
    """Пары «относительный путь → ТЕКСТ модуля» по каталогу страничного слоя."""
    root = APP_DIRECTORY.parent
    return {
        str(path.relative_to(root)): path.read_text(encoding="utf-8")
        for path in sorted(CATALOGUE_DIRECTORY.glob("*.py"))
    }


def _module_level_assignments(tree: ast.AST):
    """Пары «имя → значение» модульных присваиваний. Только верхний уровень."""
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    yield target.id, node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                yield node.target.id, node.value


def _is_the_identifier_bound(node: ast.AST) -> bool:
    """Указывает ли узел на ВЕЛИЧИНУ границы идентификатора, а не на любую другую.

    Имя `ID_MAX` либо тот же литерал. Ограничение `le=100` у размера порции под
    признак НЕ ПОПАДАЕТ — иначе правило считало бы границей ЛЮБОЕ ограничение
    сверху и зеленело бы на числе, которое к колонке идентификатора отношения не
    имеет.
    """
    if isinstance(node, ast.Name):
        return node.id == "ID_MAX"
    return isinstance(node, ast.Constant) and node.value == ID_MAX


def _annotated_metadata(annotation: ast.AST) -> list[ast.AST]:
    """Метаданные `Annotated[...]` — всё, кроме первого элемента."""
    if not isinstance(annotation, ast.Subscript):
        return []
    head = annotation.value
    name = getattr(head, "id", None) or getattr(head, "attr", None)
    if name != "Annotated":
        return []
    sliced = annotation.slice
    if isinstance(sliced, ast.Tuple):
        return list(sliced.elts[1:])
    return []


def _call_declares_the_bound(node: ast.AST) -> bool:
    """Несёт ли вызов объявителя (`Path`/`Form`/`Query`) верхнюю границу колонки."""
    if not isinstance(node, ast.Call):
        return False
    return any(
        keyword.arg == "le" and _is_the_identifier_bound(keyword.value)
        for keyword in node.keywords
    )


def bounded_alias_names(app_sources: dict[str, str]) -> frozenset[str]:
    """Имена, которыми ОГРАНИЧЕННАЯ величина приезжает в сигнатуру.

    ⚠️ ПЕРЕЧЕНЬ СОБИРАЕТСЯ ЧТЕНИЕМ, А НЕ ВЫПИСЫВАЕТСЯ. Корни берутся из
    НЕЙТРАЛЬНОГО МОДУЛЯ (`app/pages/identifiers.py`) — это те его модульные
    имена, чьё объявление есть `Annotated[...]` с верхней границей колонки.
    Выписанная здесь вторая копия перечня разошлась бы с модулем МОЛЧА, а
    молчаливое расхождение границы с местом её объявления — ровно тот дефект,
    ради которого нейтральный модуль и заводился.

    ⚠️ РАЗРЕШЕНИЕ ГОНИТСЯ ДО НЕПОДВИЖНОЙ ТОЧКИ ПО ВСЕМУ `app/`, А НЕ НА ОДИН
    ШАГ. Потребитель вправе завести СВОЁ имя (`app/pages/schedules.py`:
    `ScheduleIdPath = IdPath`), а следующая фаза — имя от этого имени. Разбор,
    видящий только корни, объявил бы семь закрытых входов модуля расписаний
    неограниченными; разбор на один шаг — промолчал бы о втором звене. Ровно на
    этом сломался первый сбор плана 10-24: он был слеп к границе, приезжающей
    ИМПОРТОМ, и мерил ПУСТУЮ вселенную.
    """
    roots: set[str] = set()
    owner_tree = ast.parse(app_sources[BOUND_OWNER])
    for name, value in _module_level_assignments(owner_tree):
        if any(_call_declares_the_bound(meta) for meta in _annotated_metadata(value)):
            roots.add(name)

    known = set(roots)
    trees = {module: ast.parse(text) for module, text in sorted(app_sources.items())}
    while True:
        grown = set(known)
        for _module, tree in trees.items():
            for name, value in _module_level_assignments(tree):
                if isinstance(value, ast.Name) and value.id in known:
                    grown.add(name)
        if grown == known:
            return frozenset(known)
        known = grown


def bounded_alias_roots(app_sources: dict[str, str]) -> frozenset[str]:
    """Корневые псевдонимы НЕЙТРАЛЬНОГО модуля — без перенятых имён потребителей."""
    owner_tree = ast.parse(app_sources[BOUND_OWNER])
    return frozenset(
        name
        for name, value in _module_level_assignments(owner_tree)
        if any(_call_declares_the_bound(meta) for meta in _annotated_metadata(value))
    )


_DECLARATORS = frozenset({"Path", "Form", "Query"})


def _is_an_unbounded_declarator(node: ast.AST) -> bool:
    """Вызов объявителя (`Path`/`Form`/`Query`) БЕЗ `ge=`/`le=` — признак POST-псевдонима."""
    if not isinstance(node, ast.Call):
        return False
    name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
    if name not in _DECLARATORS:
        return False
    return not any(keyword.arg in {"ge", "le"} for keyword in node.keywords)


def post_alias_roots(app_sources: dict[str, str]) -> frozenset[str]:
    """Корневые POST-псевдонимы НЕЙТРАЛЬНОГО модуля: `Annotated[...]` с объявителем без границы.

    ⚠️ ПРИЗНАК — ОТСУТСТВИЕ ГРАНИЦЫ У ОБЪЯВИТЕЛЯ, А НЕ ИМЯ. Узнавание по префиксу
    `Post` зеленело бы на псевдониме, который кто-то назвал иначе, и краснело бы
    на ограниченном, названном «Post…» по ошибке; предмет правила — есть ли у
    величины граница фреймворка, и признак снят ровно с него.
    """
    owner_tree = ast.parse(app_sources[BOUND_OWNER])
    roots: set[str] = set()
    for name, value in _module_level_assignments(owner_tree):
        metadata = _annotated_metadata(value)
        if any(_call_declares_the_bound(meta) for meta in metadata):
            continue
        if any(_is_an_unbounded_declarator(meta) for meta in metadata):
            roots.add(name)
    return frozenset(roots)


def post_alias_names(app_sources: dict[str, str]) -> frozenset[str]:
    """POST-псевдонимы с перенятыми именами потребителей — до неподвижной точки по `app/`.

    Разрешение то же, что у `bounded_alias_names`, и по той же причине:
    потребитель вправе завести своё имя (`ScheduleIdPath = PostIdPath`), и
    разбор, видящий только корни, выронил бы его входы из вселенной.
    """
    known = set(post_alias_roots(app_sources))
    trees = {module: ast.parse(text) for module, text in sorted(app_sources.items())}
    while True:
        grown = set(known)
        for _module, tree in trees.items():
            for name, value in _module_level_assignments(tree):
                if isinstance(value, ast.Name) and value.id in known:
                    grown.add(name)
        if grown == known:
            return frozenset(known)
        known = grown


@lru_cache(maxsize=1)
def _real_post_alias_names() -> frozenset[str]:
    """POST-псевдонимы НАСТОЯЩЕГО дерева — для разборов, которым их не подали явно."""
    return post_alias_names(_app_sources())


def _names_an_alias(annotation: ast.AST | None, names: frozenset[str]) -> bool:
    """Объявлен ли параметр одним из имён — голым именем либо первым элементом `Annotated`."""
    if annotation is None:
        return False
    if isinstance(annotation, ast.Name):
        return annotation.id in names
    if isinstance(annotation, ast.Subscript):
        head = annotation.value
        if (getattr(head, "id", None) or getattr(head, "attr", None)) == "Annotated":
            sliced = annotation.slice
            first = sliced.elts[0] if isinstance(sliced, ast.Tuple) else sliced
            return isinstance(first, ast.Name) and first.id in names
    return False


def _first_use_is_checked(handler: ast.AST, name: str) -> bool:
    """Первое по ТЕКСТУ чтение имени в теле обработчика — аргумент `id_in_column`?

    ⚠️ ПОРЯДОК — ПОЗИЦИЯ В ИСХОДНИКЕ (строка, столбец), А НЕ ПОРЯДОК ОБХОДА
    `ast.walk`: тот идёт вширь и поставил бы операнд вложенного `select` позже
    вызова помощника, стоящего ниже по тексту. Чтение, которого нет вовсе,
    проверкой НЕ считается: вход без проверки есть вход без границы, даже если
    сегодня он в запрос не уходит — завтрашняя строка отправит его туда молча.

    ⚠️ НАЗВАННАЯ ГРАНИЦА ПРИЗНАКА. Позиция в тексте совпадает с порядком
    исполнения для последовательных операторов, но не для условного выражения
    (`a if id_in_column(x) else b` исполняет условие раньше, чем стоящее левее
    `a`). Форма «проверка отдельным оператором в начале тела» признаком
    принимается всегда; условное выражение, где операнд запроса стоит левее
    проверки, признак объявит нарушением — ложный красный, а не ложный зелёный.
    """
    parents: dict[int, ast.AST] = {}
    loads: list[ast.Name] = []
    for statement in getattr(handler, "body", []):
        for node in ast.walk(statement):
            for child in ast.iter_child_nodes(node):
                parents[id(child)] = node
            if (
                isinstance(node, ast.Name)
                and node.id == name
                and isinstance(node.ctx, ast.Load)
            ):
                loads.append(node)
    if not loads:
        return False
    first = min(loads, key=lambda node: (node.lineno, node.col_offset))
    parent = parents.get(id(first))
    if not isinstance(parent, ast.Call):
        return False
    callee = getattr(parent.func, "id", None) or getattr(parent.func, "attr", None)
    if callee != FIRST_USE_CHECK_HELPER:
        return False
    return any(argument is first for argument in parent.args) or any(
        keyword.value is first for keyword in parent.keywords
    )


def _route_declarations(handler: ast.AST) -> list[tuple[str, str]]:
    """Пары «метод → путь», объявленные декораторами обработчика.

    Узнаются ОБЕ формы объявления маршрута: именованный метод и общая
    (`api_route(..., methods=[...])`). Вторая от первой не отличается ничем,
    кроме видимости для наивного разборщика, — маршрут, написанный ею, выпал бы
    из обхода МОЛЧА. Имя объекта роутера НЕ ПРОВЕРЯЕТСЯ: роутер, заведённый
    будущей фазой, выпал бы из обхода по имени, а не по существу.
    """
    declarations: list[tuple[str, str]] = []
    for decorator in handler.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        func = decorator.func
        if not isinstance(func, ast.Attribute):
            continue
        if not decorator.args:
            continue
        path = decorator.args[0]
        if not (isinstance(path, ast.Constant) and isinstance(path.value, str)):
            continue
        if func.attr in _HTTP_METHODS:
            declarations.append((func.attr.upper(), path.value))
        elif func.attr == "api_route":
            for keyword in decorator.keywords:
                if keyword.arg != "methods":
                    continue
                if not isinstance(keyword.value, (ast.List, ast.Tuple, ast.Set)):
                    continue
                for element in keyword.value.elts:
                    if isinstance(element, ast.Constant) and isinstance(element.value, str):
                        declarations.append((element.value.upper(), path.value))
    return declarations


@dataclass(frozen=True)
class _CatalogueParameter:
    """Один параметр одного обработчика маршрута, снятый разбором дерева."""

    key: str
    module: str
    handler: str
    routes: tuple[str, ...]
    name: str
    annotation: str
    in_path: bool
    named_like_identifier: bool
    declared_integer: bool
    carries_the_bound: bool
    # Поля D-07 (Фаза 11, план 11-02): объявлен ли параметр POST-псевдонимом,
    # объявлены ли у обработчика ТОЛЬКО маршруты POST, и стоит ли проверка
    # первым использованием параметра в теле.
    post_alias: bool = False
    post_only: bool = False
    first_use_checked: bool = False


def _declares_an_integer(annotation: ast.AST | None, aliases: frozenset[str]) -> bool:
    """Объявлен ли параметр ЦЕЛЫМ — с учётом псевдонимов, разрешённых по дереву."""
    if annotation is None:
        return False
    if isinstance(annotation, ast.Name) and annotation.id in aliases:
        return True
    node = annotation
    if isinstance(node, ast.Subscript):
        head = node.value
        name = getattr(head, "id", None) or getattr(head, "attr", None)
        if name == "Annotated":
            sliced = node.slice
            node = sliced.elts[0] if isinstance(sliced, ast.Tuple) else sliced
    if isinstance(node, ast.Name) and node.id in aliases:
        return True
    source = ast.unparse(node)
    parts = {
        piece.strip()
        for piece in source.replace("Optional[", "").replace("]", "|").split("|")
        if piece.strip()
    }
    return "int" in parts and parts <= {"int", "None"}


def _carries_the_bound(
    annotation: ast.AST | None, default: ast.AST | None, aliases: frozenset[str]
) -> bool:
    """Несёт ли параметр границу — ПСЕВДОНИМОМ либо ВСТРОЕННОЙ записью.

    Две формы, а не одна, и это ЗАМЕР: курсор постраничного вывода групп
    (`after_id`) объявлен встроенной записью `Query(None, ge=1, le=ID_MAX)`, а
    не псевдонимом, — правило, знающее только псевдонимы, объявило бы закрытый
    вход неограниченным и было бы починено ослаблением.
    """
    if isinstance(annotation, ast.Name) and annotation.id in aliases:
        return True
    if annotation is not None:
        if any(_call_declares_the_bound(meta) for meta in _annotated_metadata(annotation)):
            return True
        inner = annotation
        if isinstance(inner, ast.Subscript):
            head = inner.value
            name = getattr(head, "id", None) or getattr(head, "attr", None)
            if name == "Annotated":
                sliced = inner.slice
                first = sliced.elts[0] if isinstance(sliced, ast.Tuple) else sliced
                if isinstance(first, ast.Name) and first.id in aliases:
                    return True
    return _call_declares_the_bound(default) if default is not None else False


def catalogue_parameters(
    sources: dict[str, str],
    aliases: frozenset[str],
    post_aliases: frozenset[str] | None = None,
) -> list[_CatalogueParameter]:
    """ВСЕ параметры ВСЕХ обработчиков маршрутов каталога — по дереву разбора.

    ⚠️ POST-ПСЕВДОНИМ ОБЪЯВЛЯЕТ ЦЕЛОЕ (D-07, план 11-02). Без этого вход,
    переведённый на псевдоним без границы фреймворка, выпал бы из вселенной в
    приложение — и число вселенной сдвинулось бы от перевода, которого оно не
    касается. Не поданный явно перечень берётся с настоящего дерева.
    """
    if post_aliases is None:
        post_aliases = _real_post_alias_names()
    integer_aliases = aliases | post_aliases
    found: list[_CatalogueParameter] = []
    for module, text in sorted(sources.items()):
        try:
            tree = ast.parse(text)
        except SyntaxError as error:  # модуль обязан РОНЯТЬ правило, а не выпадать
            raise AssertionError(
                f"модуль {module} не разобрался в дерево ({error}) — охват, тихо "
                "потерявший файл, утверждает не то, что обещает"
            ) from error

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            routes = _route_declarations(node)
            if not routes:
                continue
            placeholders: set[str] = set()
            for _method, path in routes:
                placeholders |= set(_ROUTE_PLACEHOLDER.findall(path))
            printed = tuple(f"{method} {path}" for method, path in routes)
            post_only = all(method == "POST" for method, _path in routes)

            args = node.args
            positional = list(args.posonlyargs) + list(args.args)
            defaults: dict[str, ast.AST | None] = {}
            padding = len(positional) - len(args.defaults)
            for index, argument in enumerate(positional):
                defaults[argument.arg] = (
                    args.defaults[index - padding] if index >= padding else None
                )
            for argument, default in zip(args.kwonlyargs, args.kw_defaults):
                defaults[argument.arg] = default

            for argument in positional + list(args.kwonlyargs):
                found.append(
                    _CatalogueParameter(
                        key=f"{module}::{'; '.join(printed)} → {argument.arg}",
                        module=module,
                        handler=node.name,
                        routes=printed,
                        name=argument.arg,
                        annotation=(
                            ast.unparse(argument.annotation)
                            if argument.annotation is not None
                            else ""
                        ),
                        in_path=argument.arg in placeholders,
                        named_like_identifier=bool(
                            _IDENTIFIER_NAME_MARK.search(argument.arg)
                        ),
                        declared_integer=_declares_an_integer(
                            argument.annotation, integer_aliases
                        ),
                        carries_the_bound=_carries_the_bound(
                            argument.annotation, defaults.get(argument.arg), aliases
                        ),
                        post_alias=_names_an_alias(argument.annotation, post_aliases),
                        post_only=post_only,
                        first_use_checked=_first_use_is_checked(node, argument.arg),
                    )
                )
    return found


def _is_watched(parameter: _CatalogueParameter) -> bool:
    """Попадает ли параметр ПОД НАБЛЮДЕНИЕ этого раздела вообще.

    ⚠️ НАБЛЮДАЕМОЕ МНОЖЕСТВО ШИРЕ ВСЕЛЕННОЙ НАМЕРЕННО, И ЭТО ЗАМЕР. Вселенная
    требует объявления ЦЕЛЫМ; но параметр, объявленный СТРОКОЙ и приводимый к
    целому внутри обработчика, доезжает до сравнения по колонке ровно так же —
    ЗАМЕРЕНО на шести маршрутах (см. записи `open` приложения). Если бы
    наблюдаемое множество равнялось вселенной, эти шесть не попали бы ни во
    вселенную, ни в приложение и выпали бы МОЛЧА — то есть правило объявляло бы
    полноту, имея слепую зону, и повторяло бы предмет `WR-05` на другой оси.
    """
    return (
        parameter.in_path
        or parameter.named_like_identifier
        or parameter.declared_integer
    )


def catalogue_universe(
    sources: dict[str, str],
    aliases: frozenset[str],
    post_aliases: frozenset[str] | None = None,
) -> list[_CatalogueParameter]:
    """ВСЕЛЕННАЯ: объявлен целым И (стоит в пути ЛИБО назван идентификатором)."""
    return [
        parameter
        for parameter in catalogue_parameters(sources, aliases, post_aliases)
        if parameter.declared_integer
        and (parameter.in_path or parameter.named_like_identifier)
        and parameter.name not in PAGINATION_EXCLUSION_NAMES
    ]


def catalogue_pagination(
    sources: dict[str, str], aliases: frozenset[str]
) -> list[_CatalogueParameter]:
    """ИЗЪЯТИЕ: величины постраничного вывода, объявленные целым."""
    return [
        parameter
        for parameter in catalogue_parameters(sources, aliases)
        if parameter.declared_integer and parameter.name in PAGINATION_EXCLUSION_NAMES
    ]


def catalogue_appendix(
    sources: dict[str, str], aliases: frozenset[str]
) -> list[_CatalogueParameter]:
    """ПРИЛОЖЕНИЕ: наблюдаемое минус вселенная минус изъятие."""
    universe = {parameter.key for parameter in catalogue_universe(sources, aliases)}
    pagination = {parameter.key for parameter in catalogue_pagination(sources, aliases)}
    return [
        parameter
        for parameter in catalogue_parameters(sources, aliases)
        if _is_watched(parameter)
        and parameter.key not in universe
        and parameter.key not in pagination
    ]


def unbounded_universe_entries(
    sources: dict[str, str],
    aliases: frozenset[str],
    post_aliases: frozenset[str] | None = None,
) -> list[_CatalogueParameter]:
    """Входы вселенной, НЕ несущие границы.

    ⚠️ ПОКОЛЕНИЕ (Фаза 11, план 11-02, решение D-07). Прежде предметом было
    «граница ОБЪЯВЛЕНА в сигнатуре» у КАЖДОГО входа. Для POST-входа,
    объявленного POST-псевдонимом на обработчике только с маршрутами POST,
    судьёй теперь служит `unchecked_post_identifier_entries` (проверка первым
    использованием), и этот перечень его не повторяет. Всё остальное — GET,
    POST-псевдоним на не-POST маршруте, голое `int` на POST — судится здесь
    как прежде.
    """
    return [
        parameter
        for parameter in catalogue_universe(sources, aliases, post_aliases)
        if not parameter.carries_the_bound
        and not (parameter.post_alias and parameter.post_only)
    ]


def unchecked_post_identifier_entries(
    sources: dict[str, str],
    aliases: frozenset[str],
    post_aliases: frozenset[str] | None = None,
) -> list[tuple[_CatalogueParameter, str]]:
    """POST-псевдонимы вселенной, судимые правилом «проверка первым использованием».

    Два нарушения и два текста: псевдоним без границы на маршруте не-POST
    (у GET нет формы отказа по классу действия — RESEARCH OQ4, ограниченный
    псевдоним там обязателен), и первое чтение параметра, не являющееся
    аргументом `id_in_column` (величина уходит в запрос раньше проверки —
    Landmine CONTEXT Фазы 11).
    """
    found: list[tuple[_CatalogueParameter, str]] = []
    for parameter in catalogue_universe(sources, aliases, post_aliases):
        if not parameter.post_alias:
            continue
        if not parameter.post_only:
            found.append((parameter, "POST-псевдоним без границы на маршруте не-POST"))
        elif not parameter.first_use_checked:
            found.append(
                (
                    parameter,
                    f"первое чтение параметра не есть аргумент `{FIRST_USE_CHECK_HELPER}`",
                )
            )
    return found


def assert_every_post_identifier_is_checked_before_its_first_use(
    sources: dict[str, str],
    aliases: frozenset[str],
    post_aliases: frozenset[str] | None = None,
) -> None:
    """ТЕКСТ ОТКАЗА (в): POST-вход без границы фреймворка не проверен первым использованием."""
    found = unchecked_post_identifier_entries(sources, aliases, post_aliases)
    assert found == [], (
        "POST-ВХОД СТРАНИЧНОГО СЛОЯ БЕЗ ГРАНИЦЫ ФРЕЙМВОРКА НЕ ПРОВЕРЕН ДО ПЕРВОГО "
        "ИСПОЛЬЗОВАНИЯ: "
        + "; ".join(
            f"{parameter.module} :: {' / '.join(parameter.routes)} :: "
            f"{parameter.handler}({parameter.name}: {parameter.annotation}) — {reason}"
            for parameter, reason in sorted(found, key=lambda item: item[0].key)
        )
        + f". Первое чтение параметра обязано быть аргументом `{FIRST_USE_CHECK_HELPER}` "
        f"из {BOUND_OWNER}, стоящим ДО любого запроса (D-07 Фазы 11): величина вне "
        "колонки, ушедшая операндом сравнения, роняет обработчик отказом драйвера "
        "(`500` на PostgreSQL). На маршруте не-POST объявите параметр ограниченным "
        "псевдонимом (`IdPath`/`IdForm`/`OptionalIdForm`)"
    )


# =============================================================================
# Утверждения. ВЫНЕСЕНЫ ФУНКЦИЯМИ, ЧТОБЫ ИХ МОЖНО БЫЛО ПРОГНАТЬ НА ПОДМЕНЕ
# =============================================================================


def assert_the_universe_is_declared(
    sources: dict[str, str], aliases: frozenset[str]
) -> None:
    """ТЕКСТ ОТКАЗА (б): объявленное число вселенной разошлось с замером.

    ⚠️ ДВА ТЕКСТА ОТКАЗА РАЗВЕДЕНЫ, А НЕ СЛИТЫ В ОДИН. Один текст на два
    события лгал бы в одном из них: «число разошлось» ведёт к ОБЪЯВЛЕНИЮ и к
    решению о том, что вход добавлен законно, тогда как «вход без границы»
    ведёт к СИГНАТУРЕ и к псевдониму, которым вход надо объявить. Читатель,
    получивший не тот текст, пошёл бы чинить не то место.
    """
    assert len(sources) > 0, (
        f"в каталоге {CATALOGUE_DIRECTORY} не разобрано НИ ОДНОГО модуля — "
        "правило полноты ниже зеленеет ВАКУУМОМ: утверждение «каждый найденный "
        "ограничен» истинно и для ПУСТОГО множества найденных"
    )

    universe = catalogue_universe(sources, aliases)
    assert len(universe) > 0, (
        f"по всему каталогу {CATALOGUE_DIRECTORY} не найдено НИ ОДНОГО параметра "
        "вселенной (признаки: объявлен целым И стои́т местозаполнителем пути либо "
        "оканчивается на `id`/`_id`) — разбор декораторов либо разрешение "
        "псевдонимов перестало их узнавать, и правило полноты стало вечно зелёным"
    )

    assert len(universe) == CATALOGUE_UNIVERSE_DECLARED, (
        f"параметров вселенной найдено {len(universe)}, объявлено "
        f"{CATALOGUE_UNIVERSE_DECLARED}. Найденное: "
        f"{sorted(parameter.key for parameter in universe)}. ЧИСЛО ВЫРОСЛО — в "
        "страничный слой добавлен вход того же класса, и решение о его границе "
        "обязано быть принято ЯВНО, а число исправлено вместе с ним. ЧИСЛО "
        "УПАЛО — вход снят ЛИБО перестал узнаваться разбором (переименован "
        "каталог, сменилась форма объявления маршрута, уехал псевдоним "
        "границы), и во втором случае правило полноты ниже стало зелёным, "
        "перестав стеречь"
    )

    appendix_declared = {entry.key for entry in CATALOGUE_APPENDIX}
    appendix_found = {
        parameter.key for parameter in catalogue_appendix(sources, aliases)
    }
    assert appendix_found == appendix_declared, (
        "ПРИЛОЖЕНИЕ РАЗОШЛОСЬ С ЗАМЕРОМ. Найдено и не заявлено: "
        f"{sorted(appendix_found - appendix_declared)}; заявлено и не найдено: "
        f"{sorted(appendix_declared - appendix_found)}. Вход, не покрытый ни "
        "одним признаком вселенной и не внесённый в приложение, ВЫПАЛ БЫ МОЛЧА "
        "— то есть правило объявляло бы полноту, имея слепую зону"
    )

    assert len(CATALOGUE_APPENDIX) == CATALOGUE_APPENDIX_DECLARED, (
        f"записей приложения {len(CATALOGUE_APPENDIX)}, объявлено "
        f"{CATALOGUE_APPENDIX_DECLARED}"
    )

    pagination = catalogue_pagination(sources, aliases)
    assert len(pagination) == PAGINATION_EXCLUSION_DECLARED, (
        f"величин постраничного вывода найдено {len(pagination)}, объявлено "
        f"{PAGINATION_EXCLUSION_DECLARED}: "
        f"{sorted(parameter.key for parameter in pagination)}. Изъятие есть "
        "ЗАПИСЬ С ОБОСНОВАНИЕМ, а не отсутствие в разборе: добавленная величина "
        "обязана быть ДЕЙСТВИТЕЛЬНО постраничным выводом, а не идентификатором, "
        "названным коротким именем"
    )


def assert_every_universe_entry_carries_the_bound(
    sources: dict[str, str], aliases: frozenset[str]
) -> None:
    """ТЕКСТ ОТКАЗА (а): найден вход вселенной без границы."""
    missing = unbounded_universe_entries(sources, aliases)
    assert missing == [], (
        "ВХОД СТРАНИЧНОГО СЛОЯ ОБЪЯВЛЕН ИДЕНТИФИКАТОРОМ БЕЗ ОБЩЕЙ ГРАНИЦЫ: "
        + "; ".join(
            f"{parameter.module} :: {' / '.join(parameter.routes)} :: "
            f"{parameter.handler}({parameter.name}: "
            f"{parameter.annotation or 'без объявления'})"
            for parameter in sorted(missing, key=lambda item: item.key)
        )
        + f". Объявите параметр псевдонимом нейтрального модуля {BOUND_OWNER} "
        "(`IdPath` для адреса, `IdForm` для обязательного поля формы, "
        "`OptionalIdForm` для необязательного) либо поставьте границу "
        "встроенной записью `Query(..., ge=1, le=ID_MAX)`. Величина вне "
        "диапазона колонки уезжает операндом сравнения по ней и роняет "
        "обработчик отказом драйвера — `500` там, где обязан быть отказ "
        "валидации (`CR-01`, пятый круг ревизии)"
    )


# =============================================================================
# Правила
# =============================================================================


def test_the_catalogue_universe_is_declared_by_a_number():
    """Вселенная правила полноты ОБЪЯВЛЕНА ЧИСЛОМ — вместе с изъятием и приложением.

    ⚠️ ЭТО НЕ ДУБЛИРОВАНИЕ СЛЕДУЮЩЕГО ПРАВИЛА, А ЕГО ОПОРА. «Каждый найденный
    ограничен» — утверждение, истинное и для ПУСТОГО множества найденных:
    сломайся разбор декораторов, переименуйся каталог или уедь псевдоним
    границы — и правило полноты зеленело бы навсегда, ничего не стерегя. Ровно
    так сломался первый сбор плана 10-24, слепой к границе, приезжающей
    импортом.
    """
    sources = _catalogue_sources()
    aliases = bounded_alias_names(_app_sources())
    assert_the_universe_is_declared(sources, aliases)


def test_every_identifier_parameter_of_the_catalogue_carries_the_bound():
    """КАЖДЫЙ идентификатор КАЖДОГО модуля страничного слоя несёт общую границу.

    Предмет — СЛЕДУЮЩИЙ вход, а не сегодняшние: правило краснеет В МОМЕНТ
    ВВЕДЕНИЯ неограниченного идентификатора и называет его модулем, маршрутом и
    именем параметра. Матрица входов выше о завтрашнем маршруте не знает и
    останется на нём зелёной.
    """
    sources = _catalogue_sources()
    aliases = bounded_alias_names(_app_sources())
    assert_every_universe_entry_carries_the_bound(sources, aliases)


def test_the_recognised_bound_aliases_come_from_a_single_place():
    """Перечень узнаваемых имён СОБРАН ЧТЕНИЕМ нейтрального модуля, а не выписан.

    Выписанная копия перечня разошлась бы с модулем МОЛЧА, и правило полноты
    объявило бы неограниченными входы, закрытые псевдонимом, которого оно не
    узнаёт, — то есть было бы починено ОСЛАБЛЕНИЕМ.
    """
    app_sources = _app_sources()
    roots = bounded_alias_roots(app_sources)

    assert len(roots) == BOUNDED_ALIAS_ROOTS_DECLARED, (
        f"корневых псевдонимов границы в {BOUND_OWNER} найдено {len(roots)} "
        f"({sorted(roots)}), объявлено {BOUNDED_ALIAS_ROOTS_DECLARED}. "
        "Псевдоним ИСЧЕЗ — половина входов перестала узнаваться, и правило "
        "полноты объявит их неограниченными; псевдоним ДОБАВЛЕН — это решение о "
        "новом способе передачи, а не правка числа"
    )

    resolved = bounded_alias_names(app_sources)
    assert roots <= resolved, "разрешение псевдонимов потеряло собственные корни"

    # ⚠️ ПОКОЛЕНИЕ АНТИВАКУУМА (Фаза 11, план 11-02, решение D-07). Прежде
    # перенятые имена модуля расписаний (`ScheduleIdPath`, `AdIdForm`,
    # `AccountIdForm`) разрешались ОГРАНИЧЕННЫМИ псевдонимами, и антивакуум
    # требовал, чтобы разрешение ограниченных нашло хотя бы одно перенятое имя.
    # D-07 перевёл эти имена на POST-псевдонимы, и потребителей, перенимающих
    # ОГРАНИЧЕННЫЙ псевдоним своим именем, в дереве не осталось. Предмет
    # антивакуума — слепота разбора к имени, приехавшему ИМПОРТОМ, — от этого не
    # исчез: он переехал к разрешению POST-псевдонимов, по которому те же семь
    # входов остаются во вселенной.
    post_roots = post_alias_roots(app_sources)
    post_resolved = post_alias_names(app_sources)
    inherited = (resolved - roots) | (post_resolved - post_roots)
    assert {"ScheduleIdPath", "AdIdForm", "AccountIdForm"} <= inherited, (
        f"разрешение псевдонимов не нашло перенятых имён модуля расписаний "
        f"(найдено перенятых: {sorted(inherited)}) — а `app/pages/schedules.py` "
        "заводит свои (`ScheduleIdPath`, `AdIdForm`, `AccountIdForm`). Разбор, "
        "слепой к имени, приезжающему ИМПОРТОМ, выронил бы семь входов модуля "
        "расписаний из вселенной: ровно так мерил ПУСТУЮ вселенную первый сбор "
        "плана 10-24"
    )


def test_every_post_identifier_is_checked_before_its_first_use():
    """КАЖДЫЙ POST-вход на псевдониме без границы проверен ПЕРВЫМ использованием.

    ⚠️ ПОКОЛЕНИЕ ПРЕДМЕТА (Фаза 11, план 11-02, решение D-07). Прежде правило
    полноты требовало от КАЖДОГО идентификатора «объявления в сигнатуре»: граница
    `ge=`/`le=` стояла в аннотации, и форму отказа выбирал фреймворк
    (`{"detail": …}` без заголовка перехода) — ровно расхождение с D-01,
    записанное окном 51. Для POST-входов предмет сменился на «объявление ЛИБО
    проверка первым использованием»: граница уезжает внутрь обработчика, но
    ослабнуть не вправе — проверка обязана стоять ДО того, как величина уйдёт в
    запрос. GET-входы судятся прежним правилом без изменений.

    Антивакуум — число корневых POST-псевдонимов: на пустом перечне правило
    молчало бы по построению.
    """
    app_sources = _app_sources()
    roots = post_alias_roots(app_sources)
    assert len(roots) == POST_ALIAS_ROOTS_DECLARED, (
        f"корневых POST-псевдонимов в {BOUND_OWNER} найдено {len(roots)} "
        f"({sorted(roots)}), объявлено {POST_ALIAS_ROOTS_DECLARED}. Псевдоним ИСЧЕЗ "
        "— входы на нём перестали узнаваться целыми и выпали из вселенной; "
        "псевдоним ДОБАВЛЕН — это решение о новом способе передачи, а не правка числа"
    )

    sources = _catalogue_sources()
    aliases = bounded_alias_names(app_sources)
    assert_every_post_identifier_is_checked_before_its_first_use(
        sources, aliases, post_alias_names(app_sources)
    )


def test_every_appendix_entry_is_still_outside_the_universe():
    """ЗАПИСЬ ПРИЛОЖЕНИЯ НЕ ПЕРЕЖИВЁТ СВОЕГО ОСНОВАНИЯ.

    Запись, чей вход стал покрыт признаком вселенной, есть изъятие, потерявшее
    предмет: она молча выводила бы вход из-под правила полноты. Проверяется
    также, что каждая запись `open` несёт СНЯТЫЙ исход, — иначе названный долг
    был бы неотличим от догадки.
    """
    assert CATALOGUE_APPENDIX, (
        "приложение пусто, а число его записей объявлено ненулевым — правило "
        "зеленеет вакуумом"
    )

    sources = _catalogue_sources()
    aliases = bounded_alias_names(_app_sources())
    universe = {parameter.key for parameter in catalogue_universe(sources, aliases)}

    for entry in CATALOGUE_APPENDIX:
        assert entry.key not in universe, (
            f"запись приложения {entry.key!r} ПОПАЛА ВО ВСЕЛЕННУЮ — основание "
            f"({entry.reason}) исчерпано, и запись обязана быть снята, иначе "
            "она молча выводит вход из-под правила полноты"
        )
        assert entry.verdict in {"safe", "open"}, (
            f"запись приложения {entry.key!r} несёт неизвестный вердикт "
            f"{entry.verdict!r}"
        )
        assert entry.reason and entry.removal, (
            f"запись приложения {entry.key!r} без обоснования либо без условия "
            "снятия — изъятие без основания неотличимо от пропуска"
        )
        if entry.verdict == "open":
            assert "→" in entry.observed and "500" in entry.observed, (
                f"запись приложения {entry.key!r} объявлена ОТКРЫТЫМ ДОЛГОМ, но "
                "снятого исхода не несёт: названный долг обязан стоять на "
                f"замере, а не на догадке (снято: {entry.observed!r})"
            )


# =============================================================================
# Контроли: у правил выше есть ЗУБЫ
# =============================================================================
#
# Боевые файлы НЕ ПРАВЯТСЯ ни одним контролем: подмена живёт строкой в памяти, и
# разборщику подаётся она.

_SYNTHETIC_UNBOUNDED_IDENTIFIER = '''
from fastapi import APIRouter, Request
from app.pages.identifiers import IdPath

router = APIRouter()


@router.post("/widgets/{widget_id}/delete")
async def widgets_delete(request: Request, widget_id: int):
    """Идентификатор пути БЕЗ границы — синтетический тридцатый вход."""
    return None


@router.post("/gadgets/{gadget_id}/delete")
async def gadgets_delete(request: Request, gadget_id: IdPath):
    """Соседний вход С границей: правило обязано назвать ПЕРВЫЙ, а не оба."""
    return None
'''


def test_control_a_synthetic_unbounded_identifier_reddens_the_catalogue_rule():
    """ЧТО ДОКАЗЫВАЕТ: правило КРАСНЕЕТ на неограниченном входе и НАЗЫВАЕТ его.

    ⚠️ БЕЗ ЭТОГО КОНТРОЛЯ ПРАВИЛО БЫЛО БЫ ЗЕЛЕНО ПО ПОСТРОЕНИЮ, а обнаружилось
    бы это в тот единственный день, когда оно пропустит настоящий неограниченный
    вход.
    """
    aliases = bounded_alias_names(_app_sources())
    sources = {"app/pages/widgets.py": _SYNTHETIC_UNBOUNDED_IDENTIFIER}

    universe = catalogue_universe(sources, aliases)
    assert {parameter.name for parameter in universe} == {"widget_id", "gadget_id"}, (
        "разборщик не собрал вселенную синтетического модуля: "
        f"{sorted(parameter.key for parameter in universe)} — контроль проверял "
        "бы дерево, в котором испытуемого входа нет, и доказывал бы меньше, чем "
        "утверждает"
    )

    missing = unbounded_universe_entries(sources, aliases)
    assert [parameter.name for parameter in missing] == ["widget_id"], (
        "ПРАВИЛО НЕ ЗАМЕТИЛО НЕОГРАНИЧЕННОГО ВХОДА либо назвало вместе с ним "
        f"ограниченный: {sorted(parameter.key for parameter in missing)}"
    )

    with pytest.raises(AssertionError) as complaint:
        assert_every_universe_entry_carries_the_bound(sources, aliases)

    text = str(complaint.value)
    for expected in ("app/pages/widgets.py", "POST /widgets/{widget_id}/delete", "widget_id"):
        assert expected in text, (
            f"текст отказа не называет {expected!r} — читатель, поймавший "
            "красное, не найдёт входа, о котором оно: " + text
        )
    assert "gadget_id" not in text, (
        "текст отказа назвал ОГРАНИЧЕННЫЙ соседний вход — правило чинили бы не "
        "там: " + text
    )


def test_control_an_empty_catalogue_reddens_the_universe_rule():
    """ЧТО ДОКАЗЫВАЕТ: АНТИВАКУУМ работает — пустая вселенная даёт КРАСНЫЙ.

    Утверждение «каждый найденный ограничен» истинно и для ПУСТОГО множества
    найденных. Без этого контроля переименование каталога или смена формы
    объявления маршрута дали бы ВЕЧНО ЗЕЛЁНОЕ правило, и обнаружилось бы это
    следующим отказом обработчика на бою.
    """
    aliases = bounded_alias_names(_app_sources())

    with pytest.raises(AssertionError) as no_modules:
        assert_the_universe_is_declared({}, aliases)
    assert "не разобрано НИ ОДНОГО модуля" in str(no_modules.value)

    with pytest.raises(AssertionError) as no_parameters:
        assert_the_universe_is_declared({"app/pages/empty.py": "x = 1\n"}, aliases)
    assert "не найдено НИ ОДНОГО параметра вселенной" in str(no_parameters.value)

    # И правило полноты на том же пустом наборе МОЛЧИТ — что и есть причина, по
    # которой объявленное число стои́т рядом с ним, а не вместо него.
    assert unbounded_universe_entries({}, aliases) == []


# Контроли правила «проверка первым использованием» (Фаза 11, план 11-02, D-07).

_SYNTHETIC_POST_IDENTIFIER_CHECKS = '''
from fastapi import APIRouter, Request
from sqlalchemy import select
from app.pages.identifiers import OptionalPostIdForm, PostIdPath, id_in_column

router = APIRouter()


@router.post("/widgets/{widget_id}/delete")
async def widgets_delete(request: Request, widget_id: PostIdPath):
    """Проверка НИЖЕ первого использования: величина уже ушла в запрос."""
    await session.execute(select(Widget).where(Widget.id == widget_id))
    if not id_in_column(widget_id):
        return None
    return None


@router.post("/gadgets/{gadget_id}/delete")
async def gadgets_delete(
    request: Request, gadget_id: PostIdPath, owner_id: OptionalPostIdForm = None
):
    """Проверка ПЕРВЫМ использованием у обоих входов: правило обязано промолчать."""
    if not id_in_column(gadget_id) or not id_in_column(owner_id, optional=True):
        return None
    await session.execute(
        select(Gadget).where(Gadget.id == gadget_id, Gadget.owner_id == owner_id)
    )
    return None
'''

_SYNTHETIC_POST_ALIAS_ON_A_GET_ROUTE = '''
from fastapi import APIRouter, Request
from app.pages.identifiers import PostIdPath, id_in_column

router = APIRouter()


@router.get("/widgets/{widget_id}")
async def widgets_show(request: Request, widget_id: PostIdPath):
    """POST-псевдоним на GET — даже при проверке первым использованием."""
    if not id_in_column(widget_id):
        return None
    return None
'''


def _post_aliases_for_controls() -> tuple[frozenset[str], frozenset[str]]:
    app_sources = _app_sources()
    return bounded_alias_names(app_sources), post_alias_names(app_sources)


def test_control_a_check_below_the_first_use_reddens_the_catalogue_rule():
    """ЧТО ДОКАЗЫВАЕТ: проверка НИЖЕ `select` краснеет и НАЗЫВАЕТ вход; проверка первой — нет.

    ⚠️ БЕЗ ЭТОГО КОНТРОЛЯ перенос границы внутрь обработчика мог бы ОСЛАБИТЬ
    защиту от переполнения колонки незаметно: вызов помощника присутствовал бы,
    но стоял бы после запроса, и `500` на PostgreSQL вернулся бы на зелёной суите.
    """
    aliases, post_aliases = _post_aliases_for_controls()
    sources = {"app/pages/widgets.py": _SYNTHETIC_POST_IDENTIFIER_CHECKS}

    universe = catalogue_universe(sources, aliases, post_aliases)
    assert {parameter.name for parameter in universe} == {
        "widget_id",
        "gadget_id",
        "owner_id",
    }, (
        "разборщик не узнал POST-псевдонимы целыми: "
        f"{sorted(parameter.key for parameter in universe)} — контроль проверял бы "
        "дерево, в котором испытуемых входов нет"
    )

    found = unchecked_post_identifier_entries(sources, aliases, post_aliases)
    assert [parameter.name for parameter, _reason in found] == ["widget_id"], (
        "ПРАВИЛО НЕ ЗАМЕТИЛО ПРОВЕРКИ НИЖЕ ПЕРВОГО ИСПОЛЬЗОВАНИЯ либо назвало "
        f"проверенные входы: {sorted(parameter.key for parameter, _reason in found)}"
    )
    assert unbounded_universe_entries(sources, aliases, post_aliases) == [], (
        "прежнее правило полноты судит POST-вход на POST-псевдониме повторно — "
        "у одного нарушения было бы два текста, ведущих в разные места"
    )

    with pytest.raises(AssertionError) as complaint:
        assert_every_post_identifier_is_checked_before_its_first_use(
            sources, aliases, post_aliases
        )
    text = str(complaint.value)
    for expected in (
        "app/pages/widgets.py",
        "POST /widgets/{widget_id}/delete",
        "widget_id",
        FIRST_USE_CHECK_HELPER,
    ):
        assert expected in text, f"текст отказа не называет {expected!r}: {text}"
    assert "gadget_id" not in text and "owner_id" not in text, (
        "текст отказа назвал входы, проверенные первым использованием: " + text
    )


def test_control_a_post_alias_on_a_get_route_reddens_the_catalogue_rule():
    """ЧТО ДОКАЗЫВАЕТ: псевдоним без границы допустим ТОЛЬКО на POST.

    У GET нет формы отказа по классу действия (RESEARCH OQ4), и граница там
    остаётся объявлением в сигнатуре; перевод GET-входа на POST-псевдоним снял бы
    её молча — даже при проверке первым использованием.
    """
    aliases, post_aliases = _post_aliases_for_controls()
    sources = {"app/pages/widgets.py": _SYNTHETIC_POST_ALIAS_ON_A_GET_ROUTE}

    found = unchecked_post_identifier_entries(sources, aliases, post_aliases)
    assert [parameter.name for parameter, _reason in found] == ["widget_id"], (
        "ПРАВИЛО ПРОПУСТИЛО POST-ПСЕВДОНИМ НА GET: "
        f"{sorted(parameter.key for parameter, _reason in found)}"
    )
    assert [
        parameter.name
        for parameter in unbounded_universe_entries(sources, aliases, post_aliases)
    ] == ["widget_id"], "прежнее правило полноты обязано по-прежнему видеть GET-вход без границы"

    with pytest.raises(AssertionError) as complaint:
        assert_every_post_identifier_is_checked_before_its_first_use(
            sources, aliases, post_aliases
        )
    text = str(complaint.value)
    for expected in ("app/pages/widgets.py", "GET /widgets/{widget_id}", "не-POST"):
        assert expected in text, f"текст отказа не называет {expected!r}: {text}"

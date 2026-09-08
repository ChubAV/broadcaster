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

import ast
import pathlib
import uuid
from dataclasses import dataclass

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
from tests.conftest import seed_group

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

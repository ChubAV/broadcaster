"""ГРАНИЦА ВЕЛИЧИНЫ ИДЕНТИФИКАТОРА НА JSON-ВХОДЕ РАСПИСАНИЙ (WR-02).

ПРЕДМЕТ. План закрыл на этом входе ОБЛАСТЬ ЗНАЧЕНИЙ дней и времён
(`tests/test_routes/test_schedules_api_value_domain.py`), а ВЕЛИЧИНУ
идентификаторов не закрыл ничем: `ad_id`, `account_id`, элементы `group_ids` и
путевой `schedule_id` объявлены голым `int` без верхней границы. Величина за
пределами колонки уезжает ОПЕРАНДОМ СРАВНЕНИЯ по ней:

    Ad.id == 99999999999999999999999999
        -> OverflowError: Python int too large to convert to SQLite INTEGER
    Group.id.in_([99999999999999999999999999])
        -> то же

На PostgreSQL это `DataError` вне диапазона `int32`. Итог один — HTTP 500 на
ФОРМЕННЫЙ запрос аутентифицированного пользователя, то есть ровно тот класс
`CR-01` пятого круга ревизии, ради которого и заведён `ID_MAX`.

⚠️ ПОЧЕМУ ЭТОТ ФАЙЛ ВООБЩЕ НУЖЕН, ЕСЛИ ГЕЙТ КАТАЛОГА УЖЕ ЕСТЬ. Гейт
`tests/test_pages/test_identifier_bounds.py` собирает вселенную из `app/pages/`
(`_catalogue_sources`), и `app/routes/` не входит в неё НИ ОДНИМ входом. То есть
поверхность была закрыта там, куда гейт смотрит, и открыта там, куда он не
смотрит, — повторение ровно той ошибки, которую летопись `ID_MAX`
(`app/pages/identifiers.py`) описывает как причину переезда константы: «величина
ограничивала там, куда смотрели, и молчала там, куда не смотрели».

⚠️ ГРАНИЦА ВСЕЛЕННОЙ ЭТОГО ФАЙЛА НАЗЫВАЕТСЯ ПРЯМО, А НЕ ОСТАВЛЯЕТСЯ НА ДОГАДКУ.
Вселенная — ОДИН модуль `app/routes/schedules.py`, и только он. Прочие модули
`app/routes/` (ads, accounts, groups, billing, history, uploads) НЕ ПРОВЕРЯЮТСЯ
здесь и остаются открытым вопросом: закрывать их скопом означало бы правку,
которой ревизия не предъявляла ни одного воспроизведённого исхода, а молчаливое
включение их во вселенную сделало бы этот файл ЕЩЁ ОДНИМ гейтом, который
выглядит полнее, чем он есть, — то есть той же болезнью, что он лечит. Приём
(второй гейт с ЯВНО названной границей вселенной) уже применён проектом для
админки.

⚠️ ЧЕГО ЭТИ ПРАВИЛА НЕ ГОВОРЯТ. Отказ ставит ГРАНИЦА ПРИЛОЖЕНИЯ — величина
отвергается ДО того, как тело обработчика получило управление, и потому ДО
любого обращения к драйверу. Поэтому исход правил от драйвера НЕ ЗАВИСИТ, и
поведение БОЕВОГО драйвера на НЕОГРАНИЧЕННОМ входе они не наблюдают: предмет
остаётся окном 39 реестра `.planning/WINDOWS.md`. Довод наследуется дословно у
гейта страничного слоя.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# ⚠️ ГРАНИЦА ВВОЗИТСЯ У ПРИЛОЖЕНИЯ, А НЕ ВЫПИСЫВАЕТСЯ ЛИТЕРАЛОМ. Вторая копия
# числа разошлась бы с первой молча при первой же правке колонки, и правило
# начало бы утверждать о числе, которого в приложении нет.
from app.pages.identifiers import ID_MAX
from tests.conftest import seed_group

# Форма ответа на негодную ВЕЛИЧИНУ — отказ ВАЛИДАЦИИ, а не пятисотка и не 404.
# 404 здесь был бы хуже отказа: он утверждал бы, что величина законна и просто
# не найдена, — то есть приглашал бы перебирать.
VALIDATION_REFUSAL = 422

# Величина ЗА пределами колонки. Число берётся от границы приложения `+ 1`, а не
# литералом: правка `ID_MAX` обязана тянуть за собой и предмет этих правил.
BEYOND_COLUMN = ID_MAX + 1

# Величина, которой драйвер не выдерживает ВОВСЕ (та самая из отчёта ревизии).
FAR_BEYOND_COLUMN = 99999999999999999999999999


async def _account(client: AsyncClient, auth_headers: dict) -> int:
    return (
        await client.post(
            "/api/accounts",
            json={"type": "tg_user", "credentials": "creds"},
            headers=auth_headers,
        )
    ).json()["id"]


async def _ad(client: AsyncClient, auth_headers: dict) -> int:
    return (
        await client.post(
            "/api/ads",
            json={"title": "Объявление границ", "text": "текст"},
            headers=auth_headers,
        )
    ).json()["id"]


async def _schedule(
    client: AsyncClient, auth_headers: dict, db: AsyncSession
) -> tuple[int, int, int, int]:
    """Законное расписание владельца. Возвращает (schedule, ad, account, group)."""
    ad_id = await _ad(client, auth_headers)
    account_id = await _account(client, auth_headers)
    group = await seed_group(db, account_id, name="Группа границ")
    group_id = group.id
    schedule_id = (
        await client.post(
            "/api/schedules",
            json={
                "ad_id": ad_id,
                "account_id": account_id,
                "group_ids": [group_id],
                "days_of_week": [0, 1, 2, 3, 4, 5, 6],
                "times_of_day": ["09:00"],
            },
            headers=auth_headers,
        )
    ).json()["id"]
    return schedule_id, ad_id, account_id, group_id


# ─────────────────────────────────────────────────────────────────────────────
# ТЕЛО ЗАПРОСА: ad_id, account_id, group_ids
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("oversized", [BEYOND_COLUMN, FAR_BEYOND_COLUMN])
@pytest.mark.parametrize("field", ["ad_id", "account_id"])
async def test_create_refuses_an_oversized_identifier_in_the_body(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict,
    field: str, oversized: int,
):
    """Величина вне колонки — отказ ВАЛИДАЦИИ, а не пятисотка от драйвера."""
    _, ad_id, account_id, group_id = await _schedule(client, auth_headers, db_session)
    body = {
        "ad_id": ad_id,
        "account_id": account_id,
        "group_ids": [group_id],
        "days_of_week": [0],
        "times_of_day": ["09:00"],
    }
    body[field] = oversized

    response = await client.post("/api/schedules", json=body, headers=auth_headers)

    assert response.status_code == VALIDATION_REFUSAL, (
        f"{field}={oversized} ответило {response.status_code}, а не "
        f"{VALIDATION_REFUSAL}: величина уехала операндом сравнения по колонке"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("oversized", [BEYOND_COLUMN, FAR_BEYOND_COLUMN])
async def test_create_refuses_an_oversized_identifier_inside_group_ids(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict, oversized: int,
):
    """Граница стои́т на ЭЛЕМЕНТАХ списка, а не только на скалярах.

    `Group.id.in_([...])` уносит элемент в тот же операнд сравнения, и список
    ровно поэтому не может быть закрыт границей на самом поле.
    """
    _, ad_id, account_id, group_id = await _schedule(client, auth_headers, db_session)

    response = await client.post(
        "/api/schedules",
        json={
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": [group_id, oversized],
            "days_of_week": [0],
            "times_of_day": ["09:00"],
        },
        headers=auth_headers,
    )

    assert response.status_code == VALIDATION_REFUSAL, (
        f"group_ids=[..., {oversized}] ответило {response.status_code}, а не "
        f"{VALIDATION_REFUSAL}"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("oversized", [BEYOND_COLUMN, FAR_BEYOND_COLUMN])
async def test_update_refuses_an_oversized_identifier_inside_group_ids(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict, oversized: int,
):
    """Тот же вопрос у частичного обновления — второй вход того же правила."""
    schedule_id, _, _, group_id = await _schedule(client, auth_headers, db_session)

    response = await client.put(
        f"/api/schedules/{schedule_id}",
        json={"group_ids": [group_id, oversized]},
        headers=auth_headers,
    )

    assert response.status_code == VALIDATION_REFUSAL, (
        f"патч group_ids=[..., {oversized}] ответил {response.status_code}, а не "
        f"{VALIDATION_REFUSAL}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# ИДЕНТИФИКАТОР ПУТИ: update / delete / toggle
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("oversized", [BEYOND_COLUMN, FAR_BEYOND_COLUMN])
@pytest.mark.parametrize("verb", ["put", "delete", "toggle"])
async def test_path_identifier_beyond_the_column_is_refused_by_validation(
    client: AsyncClient, auth_headers: dict, verb: str, oversized: int,
):
    """ВСЕ ТРИ маршрута с путевым идентификатором, а не один выбранный.

    Перечислены поимённо намеренно: правило, проверяющее один маршрут из трёх,
    зеленело бы при двух открытых — то самое «закрыто там, куда смотрят».
    """
    if verb == "put":
        response = await client.put(
            f"/api/schedules/{oversized}",
            json={"times_of_day": ["09:00"]},
            headers=auth_headers,
        )
    elif verb == "delete":
        response = await client.delete(
            f"/api/schedules/{oversized}", headers=auth_headers
        )
    else:
        response = await client.post(
            f"/api/schedules/{oversized}/toggle", headers=auth_headers
        )

    assert response.status_code == VALIDATION_REFUSAL, (
        f"{verb} на идентификаторе {oversized} ответил {response.status_code}, "
        f"а не {VALIDATION_REFUSAL}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# АНТИВАКУУМНЫЕ ПОЛОВИНЫ: граница не съела ЗАКОННЫЕ величины
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_a_legitimate_identifier_still_passes_validation(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    """Без этой половины правила выше зеленели бы у входа, отвергающего ВСЁ."""
    _, ad_id, account_id, group_id = await _schedule(client, auth_headers, db_session)

    response = await client.post(
        "/api/schedules",
        json={
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": [group_id],
            "days_of_week": [0],
            "times_of_day": ["09:00"],
        },
        headers=auth_headers,
    )

    assert response.status_code == 201, (
        f"законные идентификаторы отвергнуты ({response.status_code}) — граница "
        "величины закрыла обычную работу входа"
    )


@pytest.mark.asyncio
async def test_the_boundary_value_itself_is_accepted_not_refused(
    client: AsyncClient, auth_headers: dict
):
    """`ID_MAX` — ГРАНИЦА ВКЛЮЧИТЕЛЬНО, и это проверяется, а не подразумевается.

    Отказ на самом `ID_MAX` означал бы сдвиг границы на единицу: величина,
    которой строка ЗАКОННО может обладать, перестала бы приниматься. Поэтому
    ожидается 404 («такой строки нет»), а НЕ 422 («такой величины не бывает»).
    """
    response = await client.post(
        f"/api/schedules/{ID_MAX}/toggle", headers=auth_headers
    )

    assert response.status_code == 404, (
        f"величина ID_MAX={ID_MAX} получила {response.status_code} вместо 404 — "
        "граница сдвинулась на единицу и отвергает законный идентификатор"
    )


# ─────────────────────────────────────────────────────────────────────────────
# ГЕЙТ ПОЛНОТЫ: НОВЫЙ НЕОГРАНИЧЕННЫЙ ВХОД КРАСНЕЕТ САМ
# ─────────────────────────────────────────────────────────────────────────────
#
# ⚠️ ЗАЧЕМ ГЕЙТ, ЕСЛИ ВЫШЕ УЖЕ ПЕРЕЧИСЛЕНЫ ВСЕ ПЯТЬ ВХОДОВ. Правила выше
# проверяют ПОВЕДЕНИЕ пяти НАЗВАННЫХ входов и по построению молчат о шестом.
# А появление шестого — это ровно то, как дефект `WR-02` и возник: граница
# стояла там, куда смотрели, и молчала там, куда не смотрели. Перечисление без
# гейта полноты устаревает в тот день, когда в модуль добавят маршрут.

import ast  # noqa: E402 — разбор источника нужен только этому разделу
import pathlib  # noqa: E402

ROUTES_MODULE = (
    pathlib.Path(__file__).resolve().parents[2] / "app" / "routes" / "schedules.py"
)

# ⚠️ ГРАНИЦА ВСЕЛЕННОЙ ГЕЙТА — ОДИН ФАЙЛ, И ЭТО НАПИСАНО, А НЕ ВЫВЕДЕНО.
# Прочие модули `app/routes/` сюда не входят; см. шапку модуля.

# Имена, которыми в этом модуле выражена ОГРАНИЧЕННАЯ величина. Голый `int`
# среди них отсутствует намеренно — он и есть предмет отказа.
BOUNDED_NAMES = frozenset({"BoundedId", "IdPath"})


def _is_identifier_name(name: str) -> bool:
    """Похоже ли имя на идентификатор строки: `..._id` либо `..._ids`."""
    return name.endswith("_id") or name.endswith("_ids")


def _annotation_is_bounded(node: ast.AST | None) -> bool:
    """Несёт ли аннотация ограниченную величину ХОТЬ ГДЕ-ТО внутри себя.

    Разбор идёт по ИМЕНАМ дерева, а не по строке целиком: одна и та же граница
    выражается и скаляром (`IdPath`), и элементом списка
    (`list[BoundedId]`), и необязательным (`list[BoundedId] | None`).
    """
    if node is None:
        return False
    return any(
        isinstance(inner, ast.Name) and inner.id in BOUNDED_NAMES
        for inner in ast.walk(node)
    )


# ⚠️ ГЕЙТ СУДИТ О СХЕМАХ ЗАПРОСА, А НЕ ОБО ВСЕХ СХЕМАХ МОДУЛЯ, И РАЗНИЦА
# СУЩЕСТВЕННА. В поля схемы ОТВЕТА величина приезжает ИЗ БАЗЫ, а не от клиента:
# там она по построению принадлежит существующей строке, и требовать от неё
# границы значило бы проверять СОБСТВЕННОЕ значение — то есть завести отказ,
# который может сработать только на испорченной базе, и ничего не сказать о
# входе. Предикат отбора — суффикс `Request` в имени класса.
#
# ⚠️ И ИМЕННО ПОЭТОМУ ОСТАЛЬНЫЕ СХЕМЫ ПЕРЕЧИСЛЕНЫ ПОИМЁННО, А НЕ ОТБРОШЕНЫ
# МОЛЧА. Схема, добавленная завтра под именем без суффикса `Request`, выпала бы
# из вселенной гейта БЕЗ ЕДИНОГО СЛЕДА — ровно тот способ, которым `app/routes/`
# выпал из вселенной страничного гейта. Новое имя обязано покраснеть здесь и
# быть отнесено к одному из двух множеств СОЗНАТЕЛЬНО.
NON_REQUEST_SCHEMAS = frozenset({"ScheduleResponse"})


def _request_schema_names(tree: ast.AST) -> list[str]:
    return [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and any(
            isinstance(base, ast.Name) and base.id == "BaseModel" for base in node.bases
        )
    ]


def test_every_schema_of_the_module_is_classified_as_request_or_not():
    """Новая схема обязана быть отнесена к множеству СОЗНАТЕЛЬНО."""
    tree = ast.parse(ROUTES_MODULE.read_text(encoding="utf-8"))
    unclassified = [
        name
        for name in _request_schema_names(tree)
        if not name.endswith("Request") and name not in NON_REQUEST_SCHEMAS
    ]

    assert unclassified == [], (
        "схемы модуля не отнесены ни к запросам, ни к перечню не-запросов: "
        + ", ".join(sorted(unclassified))
        + ". Гейт границ величины СУДИТ только о схемах запроса, и молчаливое "
        "выпадение схемы из его вселенной есть ровно тот способ, которым "
        "`app/routes/` выпал из вселенной страничного гейта"
    )


def _unbounded_identifiers() -> list[str]:
    """Входы модуля, чья величина идентификатора ничем не ограничена."""
    tree = ast.parse(ROUTES_MODULE.read_text(encoding="utf-8"))
    offenders: list[str] = []

    for node in ast.walk(tree):
        # (а) поля схем ЗАПРОСА (схемы ответа — см. разбор у NON_REQUEST_SCHEMAS)
        if (
            isinstance(node, ast.ClassDef)
            and node.name.endswith("Request")
            and any(
                isinstance(base, ast.Name) and base.id == "BaseModel"
                for base in node.bases
            )
        ):
            for statement in node.body:
                if not isinstance(statement, ast.AnnAssign):
                    continue
                if not isinstance(statement.target, ast.Name):
                    continue
                field = statement.target.id
                if not _is_identifier_name(field):
                    continue
                if not _annotation_is_bounded(statement.annotation):
                    offenders.append(f"{node.name}.{field}")

        # (б) параметры обработчиков маршрутов
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_route = any(
                isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Attribute)
                and isinstance(dec.func.value, ast.Name)
                and dec.func.value.id == "router"
                for dec in node.decorator_list
            )
            if not is_route:
                continue
            for arg in [*node.args.args, *node.args.kwonlyargs]:
                if not _is_identifier_name(arg.arg):
                    continue
                # `user_id` приезжает ЗАВИСИМОСТЬЮ (`get_current_user_id`), а не
                # от клиента: величину назначает сервер из разобранного токена,
                # и ограничивать её значило бы проверять СВОЁ же значение.
                if arg.arg == "user_id":
                    continue
                if not _annotation_is_bounded(arg.annotation):
                    offenders.append(f"{node.name}({arg.arg})")

    return offenders


def test_every_client_supplied_identifier_of_the_module_is_bounded():
    """Ни один вход `app/routes/schedules.py` не принимает величину без границы.

    Отказ ЛОВИТ НОВОЕ, а не подтверждает старое: маршрут или поле схемы,
    добавленные завтра с голым `int`, покраснят это правило В ДЕНЬ ПОЯВЛЕНИЯ, а
    не в день, когда кто-нибудь пришлёт в них `10**26` и получит пятисотку.
    """
    offenders = _unbounded_identifiers()

    assert offenders == [], (
        "величина идентификатора не ограничена у входов: "
        + ", ".join(sorted(offenders))
        + ". Голый `int` уезжает операндом сравнения по колонке и даёт HTTP 500 "
        "(`OverflowError` на SQLite, `DataError` на PostgreSQL). Ввезите "
        "`IdPath` для идентификатора пути либо `BoundedId` для поля схемы."
    )


def test_control_negative_the_catalogue_gate_reddens_on_a_bare_int():
    """ЗУБЫ ГЕЙТА — ЗАМЕРОМ, А НЕ ЗАЯВЛЕНИЕМ.

    Гейт, зелёный по построению, создаёт уверенность вместо проверки: разборщик,
    молча не находящий НИ ОДНОГО входа, тоже вернул бы пустой список. Контроль
    подаёт разборщику доктóренный источник и требует, чтобы голый `int` был
    НАЗВАН.
    """
    doctored = ROUTES_MODULE.read_text(encoding="utf-8").replace(
        "    ad_id: BoundedId", "    ad_id: int", 1
    )
    tree = ast.parse(doctored)

    offenders = [
        f"{node.name}.{statement.target.id}"
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and any(
            isinstance(base, ast.Name) and base.id == "BaseModel" for base in node.bases
        )
        for statement in node.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and _is_identifier_name(statement.target.id)
        and not _annotation_is_bounded(statement.annotation)
    ]

    assert "CreateScheduleRequest.ad_id" in offenders, (
        "разборщик НЕ ЗАМЕТИЛ голого `int` у `CreateScheduleRequest.ad_id` — "
        f"гейт полноты зелен по построению, а не по предмету: {offenders}"
    )

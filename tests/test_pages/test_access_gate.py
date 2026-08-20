"""Гейт доступа: кого закрывает истёкший срок и кого не закрывает НИКОГДА.

ФАЙЛ ДЕРЖИТ ДВЕ ГРУППЫ, РАЗЛИЧИМЫЕ ПО `-k pages` И `-k api`, И ЭТО НЕ
ОФОРМЛЕНИЕ. Поверхностей отказа в продукте две, и устроены они по-разному:
страничная отвечает редиректом на место, где чинят (человеку нужен экран), а
JSON-API обязан отвечать кодом и телом (клиенту редирект бессмыслен). Общий
файл заводится затем, чтобы ПЕРЕЧЕНЬ закрытого нельзя было расширить на одной
поверхности, забыв про другую.

⚠️ ГРУППУ `api` ЗАПОЛНЯЕТ ПЛАН `05.1-03`, И ФАЙЛ ОБЯЗАН БЫТЬ ГОТОВ ЕЁ ПРИНЯТЬ.
Сегодня в ней стоит единственное утверждение — что JSON-поверхность гейта ещё
НЕ существует, — и оно намеренно ПАДАЕТ, как только зависимость появится: план
`05.1-03` обязан заменить его настоящими утверждениями, а не дописать их рядом.
Пустая группа молчала бы о несделанном; эта — называет его вслух.

ПОЧЕМУ ГЕЙТ ПЕРЕЧНЯ ЧИТАЕТ ИСХОДНИК, А НЕ СОБРАННОЕ ПРИЛОЖЕНИЕ. Цель —
поймать роутер, добавленный БУДУЩИМ планом БЕЗ зависимости. В объекте
приложения такой роутер выглядит совершенно обычно: у его маршрутов просто нет
одной зависимости, и отличить «забыли» от «не должно быть» там нечем. В
исходнике же решение записано явным вызовом, и множество вызовов замкнуто.
Форма взята у отрицательных утверждений `tests/test_pages/test_history_retry.py`.
"""
import ast
from pathlib import Path

import pytest
from httpx import AsyncClient

PAGES_INIT = Path(__file__).resolve().parents[2] / "app" / "pages" / "__init__.py"

EXPIRED_LOCATION = "/billing?expired=1"

# РОУТЕРЫ, КОТОРЫЕ ЗАКРЫВАЕТ ИСТЁКШИЙ ДОСТУП. Перечень выписан ЗДЕСЬ, а не
# выведен из исходника: тест, выводящий ожидание из проверяемого, согласился бы
# с любой правкой. Изменение этого множества обязано быть решением, записанным
# в двух местах сразу.
GATED_ROUTERS = {
    "ads_router",
    "accounts_router",
    "account_groups_router",
    "groups_router",
    "schedules_router",
    "history_router",
}

# РОУТЕРЫ, КОТОРЫЕ НЕ ЗАКРЫВАЮТСЯ НИКОГДА (T-05.1-03). Вход, регистрация и
# выход — иначе человек не может даже войти, чтобы заплатить; подписка и оплата —
# иначе гейт запирает продукт от единственного действия, которое его открывает;
# профиль и админка — администратор без оплаченного доступа обязан входить в
# админку; дашборд — он только читает и служит местом, куда человека приводят
# после входа со словами о том, что произошло.
OPEN_ROUTERS = {
    "auth_router",
    "dashboard_router",
    "billing_router",
    "admin_router",
    "profile_router",
}


def _included_routers() -> dict[str, bool]:
    """Каждый вызов `router.include_router(...)` → «висит ли на нём гейт».

    Разбор по синтаксическому дереву, а не грепом: греп по строке
    `Depends(require_access)` посчитал бы её и в комментарии, и в докстринге, и
    в объявлении самой зависимости, а вопрос здесь ровно один — с какими
    аргументами позван `include_router`.
    """
    tree = ast.parse(PAGES_INIT.read_text(encoding="utf-8"))
    found: dict[str, bool] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "include_router":
            continue
        if not node.args or not isinstance(node.args[0], ast.Name):
            continue

        router_name = node.args[0].id
        gated = False
        for keyword in node.keywords:
            if keyword.arg != "dependencies":
                continue
            for element in ast.walk(keyword.value):
                if (
                    isinstance(element, ast.Name)
                    and element.id == "require_access"
                ):
                    gated = True
        found[router_name] = gated

    return found


# =============================================================================
# Группа `pages` — страничная поверхность отказа
# =============================================================================


def test_pages_gate_covers_exactly_the_declared_routers():
    """Множество закрытых роутеров равно объявленному — ни шире, ни уже.

    ⚠️ РОУТЕР, ДОБАВЛЕННЫЙ БУДУЩИМ ПЛАНОМ, РОНЯЕТ ЭТОТ ТЕСТ В ЛЮБОМ СЛУЧАЕ, И В
    ЭТОМ ВЕСЬ СМЫСЛ. Он не назван ни в `GATED_ROUTERS`, ни в `OPEN_ROUTERS`,
    поэтому последнее утверждение красит его независимо от того, поставили на
    него зависимость или забыли. Автор нового роутера обязан ОТВЕТИТЬ на вопрос
    «закрывает ли его истёкший доступ» здесь, а не оставить ответ умолчанием
    сборки.
    """
    included = _included_routers()

    gated = {name for name, is_gated in included.items() if is_gated}
    open_ = {name for name, is_gated in included.items() if not is_gated}

    assert gated == GATED_ROUTERS, (
        f"перечень закрытых роутеров разошёлся с объявленным: "
        f"лишние {gated - GATED_ROUTERS}, недостающие {GATED_ROUTERS - gated}"
    )
    assert open_ == OPEN_ROUTERS, (
        f"перечень ВСЕГДА открытых роутеров разошёлся с объявленным: "
        f"лишние {open_ - OPEN_ROUTERS}, недостающие {OPEN_ROUTERS - open_}"
    )
    assert set(included) == GATED_ROUTERS | OPEN_ROUTERS, (
        "в сборку страниц включён роутер, о котором этот тест не знает — "
        "решение «закрывает ли его истёкший доступ» не принято"
    )


@pytest.mark.parametrize(
    "path",
    ["/ads", "/accounts", "/schedules", "/groups", "/history"],
)
@pytest.mark.asyncio
async def test_pages_of_value_are_closed_when_access_expired(
    expired_client: AsyncClient, path: str
):
    """Страница создания ценности отвечает 302 на место, где чинят."""
    response = await expired_client.get(path, follow_redirects=False)

    assert response.status_code == 302, (
        f"{path} ответил {response.status_code} при истёкшем доступе"
    )
    assert response.headers["location"] == EXPIRED_LOCATION, (
        f"{path} увёл на {response.headers.get('location')!r} вместо "
        f"{EXPIRED_LOCATION!r} — человек не узнал, что произошло и что делать"
    )


@pytest.mark.parametrize(
    "path",
    ["/login", "/billing", "/profile", "/dashboard"],
)
@pytest.mark.asyncio
async def test_pages_of_recovery_stay_open_when_access_expired(
    expired_client: AsyncClient, path: str
):
    """Путь к оплате, вход и профиль истёкшим доступом НЕ закрываются (T-05.1-03).

    Утверждение написано ОТ ПРОТИВНОГО — «не уведён на `?expired=1`», — а не
    «ответил 200», и это существеннее, чем кажется. Часть этих страниц имеет
    право ответить редиректом по СВОЕЙ причине (например, увести гостя на
    `/login`), и требовать от них двухсотки значило бы вписать в тест гейта
    доступа чужие правила. Единственное, чего им делать НЕЛЬЗЯ, — отправлять
    человека оплачивать доступ вместо того, что он попросил.
    """
    response = await expired_client.get(path, follow_redirects=False)

    assert response.headers.get("location") != EXPIRED_LOCATION, (
        f"{path} закрыт гейтом доступа: человек не может ни войти, ни заплатить"
    )
    assert response.status_code in (200, 302), (
        f"{path} ответил {response.status_code} при истёкшем доступе"
    )


@pytest.mark.asyncio
async def test_pages_of_value_stay_open_while_the_trial_is_live(
    authed_client: AsyncClient
):
    """Граница сверху: внутри пробного срока те же страницы ОТКРЫТЫ.

    Без этого утверждения гейт, закрывающий ВСЕХ, прошёл бы все проверки выше.
    Пробный период обещан «в полном объёме» (критерий 2), и урезанного режима в
    плоской модели нет вовсе.

    ⚠️ `/groups` ПРОВЕРЯЕТСЯ ДРУГИМ УТВЕРЖДЕНИЕМ, И ПРИЧИНА НАЗВАНА ЗДЕСЬ, ЧТОБЫ
    СЛЕДУЮЩИЙ ЧИТАТЕЛЬ НЕ «ПРИВЁЛ ЕГО В СООТВЕТСТВИЕ». Раздел снят решением
    владельца (GRP-08, план 03-07), и его адрес БЕЗУСЛОВНО уводит на
    `/accounts` — двухсотки он не отдаёт никому и никогда, ни с доступом, ни
    без. Требовать её значило бы проверять не гейт, а снятый раздел; поэтому у
    него утверждение от противного — его редирект обязан быть СВОИМ, а не
    гейтовским.
    """
    for path in ("/ads", "/accounts", "/schedules", "/history"):
        response = await authed_client.get(path, follow_redirects=False)
        assert response.status_code == 200, (
            f"{path} ответил {response.status_code} внутри пробного срока"
        )

    retired = await authed_client.get("/groups", follow_redirects=False)
    assert retired.status_code == 302
    assert retired.headers["location"] == "/accounts", (
        "снятый раздел увёл не на свой адрес — гейт вмешался в живой доступ"
    )


# =============================================================================
# Группа `api` — JSON-поверхность отказа (заполняет план 05.1-03)
# =============================================================================


def test_api_surface_of_the_gate_is_not_built_yet():
    """НАЗВАННЫЙ ДОЛГ: гейт доступа на JSON-API ещё не поставлен.

    ⚠️ ЭТОТ ТЕСТ ОБЯЗАН УПАСТЬ, КОГДА ДОЛГ БУДЕТ ЗАКРЫТ, И ЭТО ЕГО РАБОТА.
    План `05.1-03` заводит `get_current_user_id_with_access` и вешает её
    пер-роутерно на `ads`, `accounts`, `schedules`, `history`, `uploads`; в тот
    же момент это утверждение перестаёт быть верным, красит группу `api` и
    требует заменить себя настоящими утверждениями отказа (402/403 с телом-
    объяснением).

    Зачем он стоит здесь СЕЙЧАС. Пустая группа `api` молчала бы о том, что
    JSON-поверхность продукта доступом не закрыта вовсе: страницы отвечают 302,
    а те же данные достижимы через `/api/*` без единой проверки срока. Молчание
    читалось бы как «проверено и закрыто».
    """
    dependencies = (
        Path(__file__).resolve().parents[2] / "app" / "dependencies.py"
    ).read_text(encoding="utf-8")

    assert "get_current_user_id_with_access" not in dependencies, (
        "JSON-поверхность гейта появилась — замените это утверждение долга "
        "настоящими утверждениями отказа группы `api` (план 05.1-03)"
    )

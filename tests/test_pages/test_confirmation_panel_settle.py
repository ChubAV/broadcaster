"""Подмена тела после подтверждённого удаления не стирает скрытое состояние панелей.

ДЕФЕКТ (issue #51). На `/accounts` подтверждение удаления одного аккаунта
открывало панель подтверждения ДРУГОГО аккаунта, её подтверждение — третьего, и
так по кругу: «система начинает предлагать удаление всех других аккаунтов».
Разметка раздела и привязка обработчиков здесь ни при чём — каждая форма-триггер
диспетчеризует событие СВОЕЙ панели, и панель слушает только своё имя.

МЕХАНИКА. Маршрут удаления отвечает 204 + `HX-Location: /accounts` (осознанно:
изъятие `OFFSET_CURSOR_EXCEPTIONS`, докстринг `accounts_delete`), и рантайм htmx
2.0.10 подменяет `<body>` свежим документом. В этой подмене работает ОСЕДАНИЕ
атрибутов: каждому входящему узлу, чей `id` совпал с узлом уже в документе,
сначала копируются атрибуты из списка `attributesToSettle` СТАРОГО узла, а через
задержку оседания (20 мс) атрибуты возвращаются к серверным. Атрибут, которого в
серверной разметке нет, на этом возврате УДАЛЯЕТСЯ. Корень панели
(`components/modal.html`) серверного `style` не несёт: его `display: none` пишет
Alpine по `x-show="open"` при инициализации. Оседание стирает этот `style` ПОСЛЕ
инициализации, а `open` остаётся ложным и реактивно не меняется — `x-show`
повода восстановить его не получает. Итог: панели всех оставшихся аккаунтов
видимы стопкой, человек видит верхнюю, и её подтверждение необратимо удаляет
аккаунт, которого он не выбирал. Два владельца одного атрибута — Alpine и
рантайм подмены — и есть корень.

ПОЧЕМУ РЕГРЕССИЯ РАЗМЕТОЧНАЯ. Суита не исполняет ни строчки JS: httpx отдаёт
текст ответа, а не браузер с рантаймом. Поэтому утверждаются три вещи, которые
ВМЕСТЕ и составляют дефект, и одна, которая его снимает: (1) рантайм по
умолчанию осаждает `style` — прочитано из вендоренного бандла, а не выписано
словами; (2) корень панели несёт `id` и `x-show` и не несёт серверного `style` —
то есть единственный писатель `style` у него Alpine; (3) ответ подмены приносит
панели оставшихся сущностей под ТЕМИ ЖЕ `id` — это те узлы, которые оседание
сопоставляет; (4) ДЕЙСТВУЮЩИЙ список оседания документа `style` не содержит.
Первые три — предпосылки, без которых зелёный четвёртый пункт был бы вакуумом.

ЗАМЕР, А НЕ ПРИЁМКА. Прогон планировщика (jsdom 26 + вендоренные htmx 2.0.10 и
Alpine, три сущности, удаление первой) воспроизвёл дефект ровно в этой механике:
на списке аккаунтов после подтверждения открыты `acc-del-2` и `acc-del-3`, на
списке объявлений — `ad-del-2` и `ad-del-3`, трасса мутаций
`style "display: none;" -> null` в момент оседания; с ключом
`attributesToSettle` без `style` открытых панелей ноль на обеих поверхностях.
Это замер механизма, а не проверка глазами: зрительный результат в живом
браузере остаётся за владельцем.
"""
import json
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.pages.htmx import HX_LOCATION_HEADER

# Разборщик блока конфигурации и сидеры — ИМПОРТОМ, а не вторыми копиями: два
# разборщика одного атрибута разъехались бы молча (D-01, прецедент —
# tests/test_pages/test_htmx_response_contract.py).
from tests.test_pages.test_responsive_markup import _seed_account, _seed_ad
from tests.test_pages.test_shell import _htmx_config_of

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VENDORED_HTMX = PROJECT_ROOT / "app" / "static" / "js" / "htmx.min.js"

# Атрибуты, которыми владеет СОСТОЯНИЕ панели, а не сервер: ровно `style`, его
# пишет Alpine по `x-show`. `class` сюда не входит, и это разобрано, а не
# пропущено: единственная привязка класса Alpine на узле проекта —
# `components/filters.html` (`x-bind:class`), и её начальное состояние совпадает
# с серверной разметкой, поэтому возврат класса к серверному у Alpine ничего не
# стирает. Если в проекте появится `x-bind:class`, расходящийся с разметкой на
# узле с `id`, — сюда дописывается `class`, и предикат покраснеет на ключе.
PANEL_STATE_OWNED_ATTRIBUTES = ("style",)

_RUNTIME_SETTLE_DEFAULT_RE = re.compile(r"attributesToSettle:(\[[^\]]*\])")


def _runtime_settle_default() -> list[str]:
    """Умолчание `attributesToSettle`, прочитанное из ВЕНДОРЕННОГО бандла.

    Читается из артефакта, а не выписывается константой: замена рантайма на
    версию с другим умолчанием обязана менять и предпосылку теста.
    """
    match = _RUNTIME_SETTLE_DEFAULT_RE.search(VENDORED_HTMX.read_text(encoding="utf-8"))
    assert match, (
        f"{VENDORED_HTMX.relative_to(PROJECT_ROOT)}: ключа attributesToSettle в "
        "бандле нет — рантайм заменён, и предпосылка регрессии issue #51 "
        "должна быть пересобрана по новому артефакту"
    )
    return json.loads(match.group(1))


def _effective_settle_list(config: dict) -> list[str]:
    """Список оседания, с которым рантайм РЕАЛЬНО работает на документе.

    Рантайм сливает блок конфигурации поверх умолчаний: массив ключа заменяет
    умолчание целиком, отсутствующий ключ оставляет умолчание.
    """
    return config.get("attributesToSettle", _runtime_settle_default())


def _settled_panel_state(settle_list: list[str]) -> list[str]:
    """Какие атрибуты, которыми владеет состояние панели, рантайм осаждает."""
    return sorted(set(settle_list) & set(PANEL_STATE_OWNED_ATTRIBUTES))


class _PanelRootCollector(HTMLParser):
    """Открывающие теги корней панели подтверждения (`div.modal`), словарём.

    Парсер, а не регулярное выражение: в `x-data` корня стоят стрелочные
    функции, и `>` внутри значения оборвал бы совпадение по `[^>]*`.
    """

    def __init__(self) -> None:
        super().__init__()
        self.roots: list[dict[str, str | None]] = []

    def handle_starttag(self, tag, attrs):
        if tag != "div":
            return
        attributes = dict(attrs)
        if "modal" in (attributes.get("class") or "").split():
            self.roots.append(attributes)


def _panel_roots(html: str, prefix: str) -> dict[str, dict[str, str | None]]:
    """Корни панелей, чей `id` начинается с основы события, по `id`."""
    collector = _PanelRootCollector()
    collector.feed(html)
    collector.close()
    return {
        root["id"]: root
        for root in collector.roots
        if (root.get("id") or "").startswith(prefix)
    }


def _assert_panel_roots_have_alpine_owned_style(
    roots: dict[str, dict[str, str | None]], surface: str
) -> None:
    """Предпосылка: `x-show` на корне есть, серверного `style` нет."""
    for panel_id, root in roots.items():
        assert "x-show" in root, (
            f"{surface}: у корня панели {panel_id} нет x-show — состояние панели "
            "больше не пишет style, и регрессия issue #51 стала вакуумной"
        )
        assert "style" not in root, (
            f"{surface}: корень панели {panel_id} несёт серверный style "
            f"{root['style']!r} — у атрибута снова два писателя, пересобрать "
            "предпосылку регрессии issue #51"
        )


@pytest.mark.asyncio
async def test_the_swap_after_an_account_deletion_cannot_strip_the_hidden_state_of_the_other_panels(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Issue #51: подтверждение удаления аккаунта не всплывает панелями соседей.

    Порядок утверждений нарочный: предпосылки дефекта — первыми, утверждение о
    действующем списке оседания — последним, чтобы до правки тест краснел именно
    им, а не ошибкой сбора или разбора.
    """
    accounts = [await _seed_account(db_session) for _ in range(3)]
    doomed, *survivors = accounts

    # Документ, по которому рантайм СКОНФИГУРИРОВАН: полный заход без признака
    # htmx, как первый заход браузера на страницу.
    page = await authed_client.get("/accounts")
    assert page.status_code == 200
    config = _htmx_config_of(page.text, "base.html")

    runtime_default = _runtime_settle_default()
    assert "style" in runtime_default, (
        f"умолчание вендоренного рантайма {runtime_default} больше не осаждает "
        "style — предпосылка регрессии issue #51 пересобирается по артефакту"
    )

    before = _panel_roots(page.text, "acc-del-")
    assert set(before) == {f"acc-del-{account.id}" for account in accounts}, before.keys()
    _assert_panel_roots_have_alpine_owned_style(before, "/accounts")

    deleted = await authed_client.post(
        f"/accounts/{doomed.id}/delete",
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert deleted.status_code == 204, deleted.status_code
    assert deleted.headers.get(HX_LOCATION_HEADER) == "/accounts", deleted.headers

    # Ответ подмены тела: тот GET, который рантайм делает по HX-Location.
    swapped = await authed_client.get("/accounts", headers={"HX-Request": "true"})
    assert swapped.status_code == 200
    after = _panel_roots(swapped.text, "acc-del-")
    assert after, "ответ подмены не принёс ни одной панели — сценарий вакуумен"
    assert set(after) == {f"acc-del-{account.id}" for account in survivors}, after.keys()
    assert set(after) <= set(before), (
        "панели оставшихся аккаунтов пришли под НОВЫМИ id — оседанию нечего "
        "сопоставлять, сценарий не воспроизводит issue #51"
    )

    effective = _effective_settle_list(config)
    assert _settled_panel_state(effective) == [], (
        f"действующий список оседания документа {effective} (умолчание "
        f"вендоренного рантайма {runtime_default}) осаждает "
        f"{_settled_panel_state(effective)}: при подмене тела по HX-Location "
        "рантайм вернёт корням панелей серверный атрибут без style и сотрёт "
        "display: none, записанный Alpine, — панели оставшихся аккаунтов "
        "всплывут стопкой после подтверждения (issue #51)"
    )


@pytest.mark.asyncio
async def test_the_swap_after_an_ad_deletion_cannot_strip_the_hidden_state_of_the_other_panels(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Свидетель того, что механизм ОБЩИЙ, а не свойство раздела аккаунтов.

    Та же панель (`components/modal.html`), тот же ответ перехода
    (`HX-Location: /ads`), та же подмена тела — и панели оставшихся объявлений
    под прежними `id`. Замер планировщика по этой поверхности до правки: после
    подтверждения открыты `ad-del-2` и `ad-del-3`. Собственный литеральный POST,
    а не параметризация адреса: гейты пар транспорта разбирают адрес из
    исходника.
    """
    ads = [await _seed_ad(db_session, title=f"Объявление {n}") for n in range(3)]
    doomed, *survivors = ads

    page = await authed_client.get("/ads")
    assert page.status_code == 200
    config = _htmx_config_of(page.text, "base.html")

    runtime_default = _runtime_settle_default()
    assert "style" in runtime_default, (
        f"умолчание вендоренного рантайма {runtime_default} больше не осаждает "
        "style — предпосылка регрессии issue #51 пересобирается по артефакту"
    )

    before = _panel_roots(page.text, "ad-del-")
    assert set(before) == {f"ad-del-{ad.id}" for ad in ads}, before.keys()
    _assert_panel_roots_have_alpine_owned_style(before, "/ads")

    deleted = await authed_client.post(
        f"/ads/{doomed.id}/delete",
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert deleted.status_code == 204, deleted.status_code
    assert deleted.headers.get(HX_LOCATION_HEADER) == "/ads", deleted.headers

    swapped = await authed_client.get("/ads", headers={"HX-Request": "true"})
    assert swapped.status_code == 200
    after = _panel_roots(swapped.text, "ad-del-")
    assert after, "ответ подмены не принёс ни одной панели — сценарий вакуумен"
    assert set(after) == {f"ad-del-{ad.id}" for ad in survivors}, after.keys()
    assert set(after) <= set(before), (
        "панели оставшихся объявлений пришли под НОВЫМИ id — оседанию нечего "
        "сопоставлять, сценарий не воспроизводит issue #51"
    )

    effective = _effective_settle_list(config)
    assert _settled_panel_state(effective) == [], (
        f"действующий список оседания документа {effective} (умолчание "
        f"вендоренного рантайма {runtime_default}) осаждает "
        f"{_settled_panel_state(effective)}: при подмене тела по HX-Location "
        "рантайм вернёт корням панелей серверный атрибут без style и сотрёт "
        "display: none, записанный Alpine, — панели оставшихся объявлений "
        "всплывут стопкой после подтверждения (issue #51)"
    )


@pytest.mark.asyncio
async def test_control_negative_the_panel_settle_predicate_names_style_on_the_runtime_default(
    authed_client: AsyncClient,
):
    """Предикат умеет называть `style` — и называет его ровно на умолчании рантайма.

    Без этого контроля зелёный предикат сценариев неотличим от предиката, не
    умеющего называть ничего: пустое пересечение получилось бы и от сломанного
    кортежа владения, и от сломанного чтения бандла. Поданный умолчанию
    вендоренного рантайма предикат обязан вернуть `["style"]`, поданный
    действующему списку отгруженного шелла — пусто.
    """
    assert _settled_panel_state(_runtime_settle_default()) == ["style"], (
        f"предикат на умолчании рантайма {_runtime_settle_default()} не назвал "
        "style — регрессия issue #51 стала вакуумной"
    )

    response = await authed_client.get("/dashboard")
    assert response.status_code == 200
    shipped = _effective_settle_list(_htmx_config_of(response.text, "base.html"))
    assert _settled_panel_state(shipped) == [], (
        f"отгруженный список оседания {shipped} осаждает атрибуты, которыми "
        "владеет состояние панели (issue #51)"
    )

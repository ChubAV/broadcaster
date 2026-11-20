"""Проход по отрисованным экранам: идентификатор аккаунта в тексте — только там, где его поставил помощник.

Фаза 17, план 09 (PHONE-03…PHONE-06, критерий 5 роадмапа, D-03, D-04, D-06, D-17).

ЗАЧЕМ ПРОХОД. Греп-гейт 17-08 запрещает КЛАСС конструкции (литерал, оканчивающийся
на `#`, и `#` перед `{{`), но сам назвал свою границу: идентификатор без `#`
(«Акк 7311», «№7311»), подпись, собранная в Python и поданная готовой строкой, и
значение, пришедшее из базы. Этот проход судит РЕЗУЛЬТАТ, а не исходник: открывает
экран, разбирает отрисованный HTML и утверждает, что число — идентификатор аккаунта,
заведомо уникальный (`SWEEP_ACCOUNT_ID = 7311`, вне диапазона обычных 1…N других
чисел страницы) — не встречается ни в одном ТЕКСТОВОМ узле и ни в одном ТЕКСТОВОМ
атрибуте (`TEXT_ATTRIBUTES`) нигде, кроме ОБЪЯВЛЕННЫХ адресов. Он ловит любое
написание — и `#` без `#`, и Python-сборку — потому что не знает, как строка собрана.

ЧТО ПРОХОД НЕ ВИДИТ. Только то, что отрисовал: шаблоны и ветки, не попавшие в
сеянные состояния, остаются грепу-гейту 17-08 — вместе они закрывают друг друга.
Он не судит атрибуты-идентификаторы и адреса (`id=`, `href=`, `hx-get=`, `value=`,
`data-*`, `x-*`): число там — адрес, а не подпись. Он не судит содержимое
`<script>` и `<style>`: его человек не читает. CSV — не HTML и вне прохода (его
колонку «Номер» держит `test_history_export.py`).

ПОЧЕМУ ЦИФРОВЫЕ ГРАНИЦЫ. Совпадение — `(?<!\\d)<id>(?!\\d)`: идентификатор группы
`-1007311000001` (посев `seed_group` строит его из идентификатора аккаунта) — не
подпись аккаунта, а `7311` внутри длинного числа — не вхождение идентификатора.

ОБЪЯВЛЕННЫЙ АДРЕС — это элемент подписи или плоский приёмник ТОГО ЖЕ аккаунта,
а не документ, не `<main>` и не контейнер шире подписи: адрес, объявленный шире,
сделал бы проход вакуумно зелёным (T-17-26). Адреса и причина у каждого —
`DECLARED_ADDRESSES`; у уникального аккаунта на экранах пользователя адресов НЕТ
(`#id` у него не показывается вовсе, D-03).

Гейты номера (`tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`,
`tests/test_application/test_phone_single_writer_gate.py`) модуль не трогает: номер
ставится только писателем Фазы 16 через `seed_account`.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messenger_account import MessengerAccount
from app.models.user import User
from tests.account_label_support import label_texts, seed_account
from tests.conftest import seed_group
from tests.test_pages.test_account_label_admin_history import _seed_viewed_user
from tests.test_pages.test_account_label_history import _seed_log
from tests.test_pages.test_admin_panel import _fake_redis, _FakeQueuePageRedis, _queue_task
from tests.test_pages.test_editor_schedules import _seed_ad, _seed_schedule

SWEEP_ACCOUNT_ID = 7311
# Пара двойников: два `wa` без номера (D-03) — подписи совпали.
TWIN_A_ID = 7312
TWIN_B_ID = 7313

# Текстовые атрибуты: то, что человек читает, не открывая исходник.
TEXT_ATTRIBUTES = ("title", "aria-label", "alt", "placeholder")

PHONE_STORED = "+79991234567"
PHONE_SHOWN = "+7 999 123-45-67"
UNKNOWN = "Номер неизвестен"


_VOID_TAGS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
)
# Содержимое этих элементов человек не читает: проход его не судит.
_UNREAD_TAGS = frozenset({"script", "style"})


class Address:
    """Объявленный адрес: элемент, внутри которого идентификатор законен.

    `applies(tag, attrs)` — предикат одного элемента; адрес применим, если ему
    удовлетворяет сам элемент (для атрибута — его владелец) или любой из его
    открытых предков. Адрес — элемент подписи или плоский приёмник того же
    аккаунта, не контейнер шире подписи (T-17-26).

    Два рода адреса:

    * ЦЕЛЫЙ (`plains is None`) — элемент подписи или знака аккаунта: всё, что
      внутри, законно (канал, номер, `#id`).
    * ПЛОСКИЙ ПРИЁМНИК (`plains` — плоские подписи ЭТОГО аккаунта) — `<option>`,
      `<title>`, тело модалки, `title=`, сводка расписания: туда подпись
      приезжает строкой, и вхождение законно, только если ВСЕ его места лежат
      внутри такой подписи. Остаток текста вокруг подписи проход судит как
      обычный текст, поэтому приёмник не оправдывает чужой «Акк 7312».

    `kinds` — какие вхождения адрес оправдывает: `"text"` (текстовый узел) и/или
    имя атрибута; `None` — любые.
    """

    def __init__(
        self,
        name: str,
        applies,
        *,
        plains: tuple[str, ...] | None = None,
        kinds: tuple[str, ...] | None = None,
    ) -> None:
        self.name = name
        self.applies = applies
        self.plains = plains
        self.kinds = kinds


def _id_pattern(account_id: int) -> re.Pattern[str]:
    # Цифровые границы: `-1007311000001` у группы — не вхождение идентификатора.
    return re.compile(rf"(?<!\d){account_id}(?!\d)")


class _IdSweep(HTMLParser):
    """Один проход по разметке со стеком открытых элементов."""

    def __init__(self, account_id: int, declared) -> None:
        super().__init__(convert_charrefs=True)
        self.pattern = _id_pattern(account_id)
        self.declared = tuple(declared)
        self.stack: list[tuple[str, dict[str, str]]] = []
        self.found: list[str] = []

    def _covered(self, chain: list[tuple[str, dict[str, str]]], kind: str, value: str) -> bool:
        for address in self.declared:
            if address.kinds is not None and kind not in address.kinds:
                continue
            if not any(address.applies(tag, attrs) for tag, attrs in chain):
                continue
            if address.plains is None:
                return True
            # Плоский приёмник: вырезать плоские подписи — идентификатора остаться не должно.
            rest = value
            for plain in sorted(address.plains, key=len, reverse=True):
                rest = rest.replace(plain, "")
            if not self.pattern.search(rest):
                return True
        return False

    def _report(self, chain: list[tuple[str, dict[str, str]]], where: str, value: str) -> None:
        path = ">".join(tag for tag, _attrs in chain)
        self.found.append(f"{path} {where}: {value.strip()!r}")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v if v is not None else "") for k, v in attrs}
        chain = [*self.stack, (tag, a)]
        for attr in TEXT_ATTRIBUTES:
            value = a.get(attr)
            if value and self.pattern.search(value) and not self._covered(chain, attr, value):
                self._report(chain, f"@{attr}", value)
        if tag not in _VOID_TAGS:
            self.stack.append((tag, a))

    def handle_data(self, data: str) -> None:
        if not self.pattern.search(data):
            return
        if any(tag in _UNREAD_TAGS for tag, _attrs in self.stack):
            return
        if not self._covered(self.stack, "text", data):
            self._report(self.stack, "text", data)

    def handle_endtag(self, tag: str) -> None:
        # Закрыть до ближайшего одноимённого открытого элемента.
        for pos in range(len(self.stack) - 1, -1, -1):
            if self.stack[pos][0] == tag:
                del self.stack[pos:]
                break


def undeclared_id_occurrences(html: str, account_id: int, declared=()) -> list[str]:
    """Вхождения идентификатора вне объявленных адресов: «путь вид: фрагмент».

    Судятся текстовые узлы и текстовые атрибуты (`TEXT_ATTRIBUTES`); вид —
    `text` или `@<атрибут>`, путь — теги от корня разметки до элемента.
    """
    sweep = _IdSweep(account_id, declared)
    sweep.feed(html)
    sweep.close()
    return sweep.found


# Объявленные адреса: имя → причина, по которой идентификатор законен именно там.
# Каждый — элемент подписи или плоский приёмник ТОГО ЖЕ аккаунта; адреса шире подписи
# нет (T-17-26). Новый адрес — решение: сюда он попадает вместе с причиной, а не
# подавлением красного прохода.
DECLARED_ADDRESSES: dict[str, str] = {
    "label": "элемент подписи `data-account-label` аккаунта: канал, номер и `#id` двойника (D-03)",
    "id-mark": "отдельный знак `data-account-id` аккаунта: `#id` двойника и админский `#id` (D-04, D-17)",
    "option": "`<option value=<id>>` фильтра истории: тег не красится, `#id` идёт простым текстом (D-12)",
    "title": "`<title>` экрана групп аккаунта: плоская подпись, разметки в нём нет (D-12)",
    "modal-body": "тело `#acc-del-<id>-text` подтверждения удаления: плоская подпись, у двойника с `#id` (D-13)",
    "chip-title": "`title=` чипа расписания: полный текст остаётся там, где `.chip__label` обрезан многоточием",
    "schedule-summary": "сводка `.sched-card__sum` и её `title=`: подпись склеена в строку через « · » (D-12)",
    "schedule-modal": "тело `#sched-del-<id>-text` панели удаления расписания: та же склеенная строка (D-12)",
}


def declared_for(account_id: int, *, plains: tuple[str, ...] = ()) -> tuple[Address, ...]:
    """Объявленные адреса ОДНОГО аккаунта; `plains` — его плоские подписи (с `#id`)."""
    sid = str(account_id)
    flat = tuple(plains)
    by_name = {
        "label": Address("label", lambda tag, a: a.get("data-account-label") == sid),
        "id-mark": Address("id-mark", lambda tag, a: a.get("data-account-id") == sid),
        "option": Address(
            "option",
            lambda tag, a: tag == "option" and a.get("value") == sid,
            plains=flat,
            kinds=("text",),
        ),
        "title": Address("title", lambda tag, a: tag == "title", plains=flat, kinds=("text",)),
        "modal-body": Address(
            "modal-body",
            lambda tag, a: a.get("id") == f"acc-del-{sid}-text",
            plains=flat,
            kinds=("text",),
        ),
        "chip-title": Address(
            "chip-title",
            lambda tag, a: tag == "label" and "chip" in a.get("class", "").split(),
            plains=flat,
            kinds=("title",),
        ),
        "schedule-summary": Address(
            "schedule-summary",
            lambda tag, a: "sched-card__sum" in a.get("class", "").split(),
            plains=flat,
            kinds=("text", "title"),
        ),
        "schedule-modal": Address(
            "schedule-modal",
            lambda tag, a: re.fullmatch(r"sched-del-\d+-text", a.get("id", "")) is not None,
            plains=flat,
            kinds=("text",),
        ),
    }
    assert set(by_name) == set(DECLARED_ADDRESSES), "адрес без причины или причина без адреса"
    return tuple(by_name.values())


@dataclass(frozen=True)
class SweptPath:
    """Один открываемый проходом путь и место, которое он покрывает."""

    name: str  # идентификатор случая в отчёте pytest
    path: str  # шаблон пути: {subject} {ad} {sched_unique} {sched_twin} {owner}
    place: str  # места RESEARCH §1 (№1–№16), которые рисует этот путь
    status: str | None = None  # статус, присваиваемый аккаунту `subject` до открытия


# Экраны и фрагменты пользователя. «Места» — номера строк переписи RESEARCH §1
# (№1–№16); CSV — не HTML, вне прохода. Шесть мест чипов и карточек расписания
# (№6–№9) рисует один путь редактора: сводка, панель, `title=` и чип.
SWEPT_USER_CASES: tuple[SweptPath, ...] = (
    SweptPath("accounts-page", "/accounts", "1, 2"),
    SweptPath("accounts-partial", "/accounts/partial?offset=0&limit=30", "3"),
    SweptPath("sync-status-active", "/accounts/{subject}/sync-status", "4", status="active"),
    SweptPath("sync-status-syncing", "/accounts/{subject}/sync-status", "4", status="syncing"),
    SweptPath("sync-status-sync-failed", "/accounts/{subject}/sync-status", "4", status="sync_failed"),
    SweptPath("account-groups", "/accounts/{subject}/groups", "5"),
    SweptPath("editor-unique-schedule", "/ads/{ad}/edit?sched={sched_unique}", "6, 7, 8, 9"),
    SweptPath("editor-twin-schedule", "/ads/{ad}/edit?sched={sched_twin}", "6, 7, 8, 9"),
    SweptPath("history-page", "/history", "10, 11"),
    SweptPath("history-partial", "/history/partial?offset=0&limit=30", "10"),
)

# Экраны админки (идентификатор всегда виден, D-04, D-17): воркеры, очередь, карточка и история.
SWEPT_ADMIN_PATHS: tuple[SweptPath, ...] = (
    SweptPath("workers-page", "/admin/workers", "12"),
    SweptPath("workers-partial", "/admin/workers/partial", "12"),
    SweptPath("queue-page", "/admin/queue", "13, 14"),
    SweptPath("user-card", "/admin/users/{owner}", "15"),
    SweptPath("user-history-page", "/admin/users/{owner}/history", "10, 16"),
    SweptPath("user-history-partial", "/admin/users/{owner}/history/partial?offset=0&limit=30", "10"),
)


# --- Контроль: проход непуст -------------------------------------------------


def test_control_a_stray_id_in_a_text_node_is_named():
    """Посторонний идентификатор в тексте и в `title=` назван; подпись внутри адреса — нет.

    «Акк 7311» — без `#`: ровно то написание, которое греп-гейт 17-08 назвал
    своей границей. Проход обязан его назвать, иначе он вакуумно зелёный.
    """
    html = (
        '<div><span data-account-label="7311">+7 999 123-45-67</span>'
        "<p>Акк 7311</p>"
        '<b title="акк 7311">x</b></div>'
    )

    found = undeclared_id_occurrences(html, SWEEP_ACCOUNT_ID)

    assert found == ["div>p text: 'Акк 7311'", "div>b @title: 'акк 7311'"]


# --- Первый экран: «Аккаунты» ------------------------------------------------


@pytest.mark.asyncio
async def test_the_accounts_page_shows_the_unique_id_nowhere_in_text(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ТРАССЕР: у уникального аккаунта `7311` нет адреса, и в тексте `/accounts` его нет нигде."""
    owner_id = (
        await db_session.execute(select(User.id).where(User.email == "testuser@test.com"))
    ).scalar_one()
    await seed_account(
        db_session, owner_id, "tg_user", phone=PHONE_STORED, account_id=SWEEP_ACCOUNT_ID
    )

    html = (await authed_client.get("/accounts")).text

    # Проход смотрит на непустую страницу: подпись аккаунта на ней есть.
    assert label_texts(html)[str(SWEEP_ACCOUNT_ID)] == [PHONE_SHOWN]
    assert undeclared_id_occurrences(html, SWEEP_ACCOUNT_ID) == []


# --- Контроль адресов: законно только своё и только в плоской форме ---------------

PLAIN_TWIN = f"WhatsApp {UNKNOWN} #{TWIN_A_ID}"


def test_declared_addresses_are_named_with_a_reason():
    """Каждый объявленный адрес назван в `DECLARED_ADDRESSES` с причиной; лишних причин нет."""
    names = {a.name for a in declared_for(TWIN_A_ID, plains=(PLAIN_TWIN,))}

    assert len(names) >= 8, "адресов меньше объявленных планом: подпись, знак и шесть плоских приёмников"
    assert names == set(DECLARED_ADDRESSES)
    assert all(reason.strip() for reason in DECLARED_ADDRESSES.values())


def test_control_declared_addresses_make_only_their_own_text_legal():
    """Подпись, знак, `<option>`, `<title>`, тело модалки, `title=` чипа и сводки — законны.

    Каждое из этих мест — элемент подписи или плоский приёмник ТОГО ЖЕ аккаунта
    с его плоской подписью: с идентификатором внутри неё проход молчит.
    """
    html = (
        f"<html><head><title>{PLAIN_TWIN} — группы аккаунта — Broadcaster</title></head><body>"
        f'<span class="acct-label" data-account-label="{TWIN_A_ID}">'
        '<span class="acct-label__chan">WhatsApp</span> '
        f'<span class="acct-label__text">{UNKNOWN}</span> '
        f'<span class="acct-label__id" data-account-id="{TWIN_A_ID}">#{TWIN_A_ID}</span></span>'
        f'<select name="account_id"><option value="{TWIN_A_ID}">{PLAIN_TWIN}</option></select>'
        f'<p id="acc-del-{TWIN_A_ID}-text">{PLAIN_TWIN}</p>'
        f'<label class="chip" title="{PLAIN_TWIN}">x</label>'
        '<span class="sched-card__sum">'
        f'<span title="{PLAIN_TWIN} · 1 групп · Пн · 09:00">{PLAIN_TWIN} · 1 групп · Пн · 09:00</span>'
        "</span>"
        f'<div id="sched-del-5-text">{PLAIN_TWIN} · 1 групп</div>'
        "</body></html>"
    )

    declared = declared_for(TWIN_A_ID, plains=(PLAIN_TWIN,))

    assert undeclared_id_occurrences(html, TWIN_A_ID, declared) == []


def test_control_the_same_places_of_another_account_are_not_declared():
    """`<option>`, тело модалки и `title=` ЧУЖОГО аккаунта не оправдывают идентификатор этого."""
    html = (
        "<body>"
        "<p>Акк 7312</p>"
        '<b title="Акк #7312">x</b>'
        f'<select name="account_id"><option value="{TWIN_B_ID}">Акк 7312</option></select>'
        f'<p id="acc-del-{TWIN_B_ID}-text">WhatsApp {UNKNOWN} #7312</p>'
        "</body>"
    )

    found = undeclared_id_occurrences(html, TWIN_A_ID, declared_for(TWIN_A_ID, plains=(PLAIN_TWIN,)))

    assert found == [
        "body>p text: 'Акк 7312'",
        "body>b @title: 'Акк #7312'",
        "body>select>option text: 'Акк 7312'",
        f"body>p text: 'WhatsApp {UNKNOWN} #7312'",
    ]


def test_control_an_address_is_never_wider_than_the_label():
    """Адрес — подпись, а не контейнер вокруг неё: остаток текста в `<main>` и в `<title>` назван."""
    html = (
        f'<main><span data-account-label="{TWIN_A_ID}">WhatsApp {UNKNOWN} #{TWIN_A_ID}</span>'
        " и ещё 7312</main>"
        f"<title>{PLAIN_TWIN} — Акк 7312</title>"
    )

    found = undeclared_id_occurrences(html, TWIN_A_ID, declared_for(TWIN_A_ID, plains=(PLAIN_TWIN,)))

    assert found == [
        "main text: 'и ещё 7312'",
        f"title text: '{PLAIN_TWIN} — Акк 7312'",
    ]


def test_control_script_and_style_text_is_not_judged():
    """Граница названа: `<script>` и `<style>` человек не читает, проход их не судит."""
    html = "<body><script>var account = 7311;</script><style>.a-7311 {}</style><i>7311</i></body>"

    assert undeclared_id_occurrences(html, SWEEP_ACCOUNT_ID) == ["body>i text: '7311'"]


# --- Посев: мир экрана ----------------------------------------------------------


@dataclass(frozen=True)
class World:
    """Засеянный пользователь: уникальный аккаунт, пара двойников, объявление с двумя расписаниями."""

    owner: int
    unique: int
    twin_a: int
    twin_b: int
    ad: int
    sched_unique: int
    sched_twin: int


async def _owner_id(db: AsyncSession) -> int:
    return (
        await db.execute(select(User.id).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_world(db: AsyncSession, owner_id: int, *, unique_type: str = "tg_user") -> World:
    """Три аккаунта с группой и записью журнала у каждого; номер ставит только писатель."""
    unique = await seed_account(
        db, owner_id, unique_type, phone=PHONE_STORED, account_id=SWEEP_ACCOUNT_ID
    )
    twin_a = await seed_account(db, owner_id, "wa", account_id=TWIN_A_ID)
    twin_b = await seed_account(db, owner_id, "wa", account_id=TWIN_B_ID)
    groups: dict[int, int] = {}
    for account_id in (unique, twin_a, twin_b):
        group = await seed_group(db, account_id, owner_id)
        await _seed_log(db, owner_id, group.id)
        groups[account_id] = group.id
    ad = await _seed_ad(db, owner_id)
    sched_unique = await _seed_schedule(db, ad.id, unique, group_ids=[groups[unique]])
    sched_twin = await _seed_schedule(db, ad.id, twin_a, group_ids=[groups[twin_a]])
    return World(owner_id, unique, twin_a, twin_b, ad.id, sched_unique.id, sched_twin.id)


def _path(world: World, case: SweptPath, subject: int) -> str:
    return case.path.format(
        subject=subject,
        ad=world.ad,
        sched_unique=world.sched_unique,
        sched_twin=world.sched_twin,
        owner=world.owner,
    )


async def _open_user(
    client: AsyncClient, db: AsyncSession, world: World, case: SweptPath, subject: int
) -> str:
    """Открывает путь случая от лица пользователя; статус случая присваивается аккаунту до этого."""
    if case.status is not None:
        account = await db.get(MessengerAccount, subject)
        account.status = case.status
        await db.commit()
    path = _path(world, case, subject)
    response = await client.get(path)
    assert response.status_code == 200, f"{path}: {response.status_code}"
    return response.text


async def _open_admin(client: AsyncClient, world: World, case: SweptPath) -> str:
    """Открывает путь админки с двойниками Redis воркеров и очереди (как в test_admin_panel)."""
    fresh = str(int(time.time() * 1000))
    ids = (world.unique, world.twin_a, world.twin_b)
    if case.path.startswith("/admin/queue"):
        redis = _FakeQueuePageRedis({f"wa:queue:{i}": [_queue_task(f"sweep-{i}")] for i in ids})
    else:
        redis = _fake_redis([fresh, fresh, fresh], [fresh, 0] * len(ids))
    path = _path(world, case, world.unique)
    with patch("app.services.ops_state._get_redis", return_value=redis):
        response = await client.get(path)
    assert response.status_code == 200, f"{path}: {response.status_code}"
    return response.text


@pytest.mark.asyncio
async def test_control_a_planted_id_on_a_real_page_is_named(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Проход непуст и на НАСТОЯЩЕЙ разметке: подложенный в страницу «Акк 7311» назван."""
    await _seed_world(db_session, await _owner_id(db_session))
    html = (await authed_client.get("/accounts")).text

    planted = html.replace("</body>", "<p>Акк 7311</p></body>")

    assert planted != html, "в странице нет </body>: подкладывать некуда"
    assert undeclared_id_occurrences(html, SWEEP_ACCOUNT_ID) == []
    found = undeclared_id_occurrences(planted, SWEEP_ACCOUNT_ID)
    assert len(found) == 1 and found[0].endswith("body>p text: 'Акк 7311'"), found


# --- Перечни: проход не пропускает место ------------------------------------------


def test_the_sweep_covers_every_place():
    """Нижняя граница перечней: пустой перечень делал бы проход вакуумно зелёным (T-17-26)."""
    assert len(SWEPT_USER_CASES) >= 9
    assert len(SWEPT_ADMIN_PATHS) >= 6


def test_every_place_of_the_census_is_named_by_a_swept_path():
    """Все 16 мест переписи RESEARCH §1 названы хотя бы одним путём прохода."""
    named = {
        int(n) for case in (*SWEPT_USER_CASES, *SWEPT_ADMIN_PATHS) for n in re.findall(r"\d+", case.place)
    }

    assert named == set(range(1, 17)), sorted(set(range(1, 17)) - named)


# --- Проход по экранам пользователя -----------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("case", SWEPT_USER_CASES, ids=lambda c: c.name)
async def test_every_user_screen_shows_the_unique_id_nowhere_in_text(
    authed_client: AsyncClient, db_session: AsyncSession, case: SweptPath
):
    """Уникальный `7311` у недвойника не встречается ни в одном тексте экрана: адресов у него нет."""
    world = await _seed_world(db_session, await _owner_id(db_session))

    html = await _open_user(authed_client, db_session, world, case, world.unique)

    # Проход смотрит на экран с подписью аккаунта, а не в пустоту.
    assert str(SWEEP_ACCOUNT_ID) in label_texts(html), f"{case.name}: подписи аккаунта на экране нет"
    assert undeclared_id_occurrences(html, SWEEP_ACCOUNT_ID) == [], case.name


@pytest.mark.asyncio
@pytest.mark.parametrize("case", SWEPT_USER_CASES, ids=lambda c: c.name)
async def test_twins_show_their_id_only_at_declared_addresses(
    authed_client: AsyncClient, db_session: AsyncSession, case: SweptPath
):
    """Двойники `7312` и `7313`: идентификатор — подпись, `<option>`, `<title>`, тело модалки, `title=`."""
    world = await _seed_world(db_session, await _owner_id(db_session))

    html = await _open_user(authed_client, db_session, world, case, world.twin_a)

    assert str(TWIN_A_ID) in label_texts(html), f"{case.name}: подписи двойника на экране нет"
    for account_id in (TWIN_A_ID, TWIN_B_ID):
        plain = f"WhatsApp {UNKNOWN} #{account_id}"
        declared = declared_for(account_id, plains=(plain,))
        assert undeclared_id_occurrences(html, account_id, declared) == [], (
            f"{case.name}: {account_id}"
        )


# --- Проход по экранам админки ----------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("case", SWEPT_ADMIN_PATHS, ids=lambda c: c.name)
async def test_every_admin_screen_shows_the_id_only_at_declared_addresses(
    admin_client: AsyncClient, db_session: AsyncSession, case: SweptPath
):
    """Админка (D-04, D-17): идентификатор — подпись, отдельный знак и текст `<option>`; больше нигде."""
    viewed = await _seed_viewed_user(db_session)
    world = await _seed_world(db_session, viewed, unique_type="wa")

    html = await _open_admin(admin_client, world, case)

    shown = {
        SWEEP_ACCOUNT_ID: f"WhatsApp {PHONE_SHOWN} #{SWEEP_ACCOUNT_ID}",
        TWIN_A_ID: f"WhatsApp {UNKNOWN} #{TWIN_A_ID}",
        TWIN_B_ID: f"WhatsApp {UNKNOWN} #{TWIN_B_ID}",
    }
    labels = label_texts(html)
    for account_id, plain in shown.items():
        assert str(account_id) in labels, f"{case.name}: подписи {account_id} на экране нет"
        declared = declared_for(account_id, plains=(plain,))
        assert undeclared_id_occurrences(html, account_id, declared) == [], (
            f"{case.name}: {account_id}"
        )


# --- Наихудшая длина --------------------------------------------------------------


class _LabelMarkup(HTMLParser):
    """Разметка внутри каждого `data-account-label`: теги и начальные теги как написаны."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[tuple[str, int | None]] = []
        self.entries: list[tuple[str, list[str], list[str]]] = []  # (id, теги, начальные теги)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        raw = self.get_starttag_text() or ""
        a = dict(attrs)
        index: int | None = None
        if "data-account-label" in a:
            self.entries.append((a["data-account-label"] or "", [], []))
            index = len(self.entries) - 1
        for _tag, open_index in self._stack:
            if open_index is not None:
                self.entries[open_index][1].append(tag)
                self.entries[open_index][2].append(raw)
        if index is not None:
            self.entries[index][1].append(tag)
            self.entries[index][2].append(raw)
        self._stack.append((tag, index))

    def handle_endtag(self, tag: str) -> None:
        for pos in range(len(self._stack) - 1, -1, -1):
            if self._stack[pos][0] == tag:
                del self._stack[pos:]
                break


def _label_markup(html: str) -> list[tuple[str, list[str], list[str]]]:
    parser = _LabelMarkup()
    parser.feed(html)
    parser.close()
    return parser.entries


WORST_MAX_PHONE = "+88801234567"
WORST_MAX_SHOWN = "+888 01234567"
WORST_ODD_STORED = "unparsable-value"  # 16 символов, писатель такого не произведёт
WORST_MAX_A_ID = 123456
WORST_MAX_B_ID = 123457
WORST_ODD_ID = 7401


@pytest.mark.asyncio
async def test_the_worst_case_labels_render(authed_client: AsyncClient, db_session: AsyncSession):
    """D-06: самая длинная подпись — «MAX +888 01234567 #123456» у двойника и 16 символов «как есть».

    Раскладку на 320–375 px суита не измеряет (браузера нет): здесь доказано то, что
    она измеряет, — экраны отвечают 200, подписи полные, разметка подписи — только
    `<span>` без инлайн-стилей, то есть CSS-контракт не обойти разметкой.
    """
    owner_id = await _owner_id(db_session)
    max_a = await seed_account(
        db_session, owner_id, "max", phone=WORST_MAX_PHONE, account_id=WORST_MAX_A_ID
    )
    max_b = await seed_account(
        db_session, owner_id, "max", phone=WORST_MAX_PHONE, account_id=WORST_MAX_B_ID
    )
    odd = await seed_account(
        db_session, owner_id, "tg_user", stored_as_is=WORST_ODD_STORED, account_id=WORST_ODD_ID
    )
    groups = {}
    for account_id in (max_a, max_b, odd):
        group = await seed_group(db_session, account_id, owner_id)
        await _seed_log(db_session, owner_id, group.id)
        groups[account_id] = group.id
    ad = await _seed_ad(db_session, owner_id)
    schedule = await _seed_schedule(db_session, ad.id, max_a, group_ids=[groups[max_a]])

    editor = f"/ads/{ad.id}/edit?sched={schedule.id}"
    paths = [
        "/accounts",
        "/accounts/partial?offset=0&limit=30",
        *(f"/accounts/{i}/groups" for i in (max_a, max_b, odd)),
        "/history",
        "/history/partial?offset=0&limit=30",
        editor,
    ]
    pages: dict[str, str] = {}
    for path in paths:
        response = await authed_client.get(path)
        assert response.status_code == 200, f"{path}: {response.status_code}"
        pages[path] = response.text

    chips = label_texts(pages[editor])
    assert chips[str(max_a)] == [f"MAX {WORST_MAX_SHOWN} #{max_a}"]
    assert chips[str(max_b)] == [f"MAX {WORST_MAX_SHOWN} #{max_b}"]
    assert chips[str(odd)] == [f"Telegram {WORST_ODD_STORED}"]
    for path, html in pages.items():
        for label_id, tags, raws in _label_markup(html):
            assert set(tags) == {"span"}, f"{path}: подпись {label_id} несёт теги {sorted(set(tags))}"
            assert not any("style=" in raw for raw in raws), f"{path}: подпись {label_id} со style="

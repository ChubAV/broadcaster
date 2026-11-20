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
from html.parser import HTMLParser

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from tests.account_label_support import label_texts, seed_account

SWEEP_ACCOUNT_ID = 7311

# Текстовые атрибуты: то, что человек читает, не открывая исходник.
TEXT_ATTRIBUTES = ("title", "aria-label", "alt", "placeholder")

PHONE_STORED = "+79991234567"
PHONE_SHOWN = "+7 999 123-45-67"


_VOID_TAGS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
)
# Содержимое этих элементов человек не читает: проход его не судит.
_UNREAD_TAGS = frozenset({"script", "style"})


class Address:
    """Объявленный адрес: элемент, внутри которого идентификатор законен.

    `applies(tag, attrs)` — предикат одного элемента; вхождение законно, если ему
    удовлетворяет сам элемент (для атрибута — его владелец) или любой из его
    открытых предков. Адрес — элемент подписи или плоский приёмник того же
    аккаунта, не контейнер шире подписи (T-17-26).
    """

    def __init__(self, name: str, applies) -> None:
        self.name = name
        self.applies = applies


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

    def _covered(self, chain: list[tuple[str, dict[str, str]]]) -> bool:
        return any(a.applies(tag, attrs) for a in self.declared for tag, attrs in chain)

    def _report(self, chain: list[tuple[str, dict[str, str]]], where: str, value: str) -> None:
        path = ">".join(tag for tag, _attrs in chain)
        self.found.append(f"{path} {where}: {value.strip()!r}")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v if v is not None else "") for k, v in attrs}
        chain = [*self.stack, (tag, a)]
        for attr in TEXT_ATTRIBUTES:
            value = a.get(attr)
            if value and self.pattern.search(value) and not self._covered(chain):
                self._report(chain, f"@{attr}", value)
        if tag not in _VOID_TAGS:
            self.stack.append((tag, a))

    def handle_data(self, data: str) -> None:
        if not self.pattern.search(data):
            return
        if any(tag in _UNREAD_TAGS for tag, _attrs in self.stack):
            return
        if not self._covered(self.stack):
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

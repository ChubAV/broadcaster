"""Подпись аккаунта на экранах пользователя и администратора (Фаза 17, D-06).

Модуль нейтрален, как `app/services/schedule_rules.py`: чистое правило без БД
и без Jinja. На вход — строки `(id, type, phone)`, на выход — готовые подписи.
Страницы, глобалы шаблонов и загрузчик строк
(`app/application/accounts/labels.py`) зовут ЭТО правило и больше нигде его не
повторяют: второе написание разошлось бы с первым молча, и один и тот же
аккаунт читался бы на двух экранах по-разному (D-14).

СЛОВА КАНАЛА — ТОЛЬКО `MESSENGER_LABELS` (D-11): локального словаря здесь нет.
Незнакомый тип остаётся как есть, как в CSV истории.

РАЗМЕТКУ МОДУЛЬ НЕ ОТДАЁТ. Хранимый номер — недоверенная строка («как есть» у
неразбираемого, D-07), а готовая разметка из Python — это объект «доверенной
разметки» шаблонизатора, закрытый правилами `MARKUP_BUILDERS = 0` и
`UNSAFE_MARKERS`. Поэтому модуль отдаёт ДАННЫЕ (`AccountLabel`) и плоские строки (`plain`, `plain_with_id`), а
`<span data-account-label>` рисует макрос `components/account_label.html`
автоэкранированием Jinja.

ЗНАК `#` ПЕРЕД ИДЕНТИФИКАТОРОМ собирается в одном месте — функция `id_mark`.
Это единственная строковая константа модуля, оканчивающаяся на этот знак:
её вхождение вносится в реестр гейта плана 17-08 как плоская половина
помощника (D-06). Разметочная половина — макрос `account_id_mark`.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from typing import NamedTuple

from app.constants import MESSENGER_LABELS
from app.services.phone import format_phone

PHONE_UNKNOWN_TEXT = "Номер неизвестен"


class AccountRow(NamedTuple):
    """Три колонки аккаунта, из которых строится подпись (D-18)."""

    id: int
    type: str
    phone: str | None


@dataclass(frozen=True, slots=True)
class AccountLabel:
    """Готовая подпись одного аккаунта: данные, а не разметка."""

    account_id: int
    channel: str
    phone_text: str | None
    twin: bool

    @property
    def text(self) -> str:
        """Номер для показа или «Номер неизвестен»."""
        return self.phone_text if self.phone_text is not None else PHONE_UNKNOWN_TEXT

    @property
    def plain(self) -> str:
        """Плоская форма экранов пользователя: `#id` — только у двойника (D-12)."""
        base = f"{self.channel} {self.text}"
        return f"{base} {id_mark(self.account_id)}" if self.twin else base

    @property
    def plain_with_id(self) -> str:
        """Плоская форма админки: `#id` — всегда, независимо от двойников (D-17)."""
        return f"{self.channel} {self.text} {id_mark(self.account_id)}"


def id_mark(account_id: int) -> str:
    """Знак и идентификатор аккаунта — единственная сборка `#id` в Python."""
    return f"#{account_id}"


def shown_phone(stored: str | None) -> str | None:
    """Хранимый номер → текст для показа; `None` — «Номер неизвестен» (D-02, D-07).

    `None`, пустая и пробельная строка отсекаются ДО `format_phone`:
    `format_phone(None)` вернул бы `None`, а `format_phone("")` — пустую подпись.
    Это закрывает «заботу Фазы 17» из докстринга `app/services/phone.format_phone`.
    Сохранённое, но неразбираемое значение `format_phone` возвращает как есть, и
    здесь оно как есть и остаётся: спрятать его под «неизвестен» значило бы
    солгать о состоянии аккаунта.
    """
    if stored is None or not stored.strip():
        return None
    return format_phone(stored)


def _twin_key(row_type: str, shown: str | None) -> tuple[str, str | None]:
    """Ключ двойника: тип аккаунта и ГОТОВАЯ подпись (D-14).

    Тип входит в ключ: один номер законно живёт в Telegram, WhatsApp и MAX
    сразу, и такие аккаунты двойниками не считаются. Подпись берётся после
    `shown_phone`, поэтому `+79991234567` и `+7 999 123-45-67` — один ключ, а
    `None` и `""` — тоже.
    """
    return (row_type, shown)


def row_of(account: object) -> AccountRow:
    """Строка подписи из ORM-объекта или DTO с полями `id`, `type`, `phone`."""
    return AccountRow(account.id, account.type, account.phone)  # type: ignore[attr-defined]


def label_of(subject: AccountRow, rows: Iterable[AccountRow]) -> AccountLabel:
    """Подпись одного аккаунта среди `rows` — тот же результат, что у `build_labels`.

    Двойник — строка с ИНЫМ `id` и тем же ключом; `rows` может содержать сам
    `subject` или не содержать его. Без соседей (`rows` пуст) двойника нет —
    так подпись админки считает один объект (`phone_label`).
    """
    shown = shown_phone(subject.phone)
    key = _twin_key(subject.type, shown)
    twin = any(
        other.id != subject.id and _twin_key(other.type, shown_phone(other.phone)) == key
        for other in rows
    )
    return AccountLabel(subject.id, MESSENGER_LABELS.get(subject.type, subject.type), shown, twin)


def build_labels(rows: Iterable[AccountRow]) -> dict[int, AccountLabel]:
    """Подписи ВСЕХ аккаунтов одного пользователя: двойник — совпала готовая подпись."""
    drafts = [(row.id, row.type, shown_phone(row.phone)) for row in rows]
    counts = Counter(_twin_key(type_, shown) for _id, type_, shown in drafts)
    return {
        account_id: AccountLabel(
            account_id,
            MESSENGER_LABELS.get(type_, type_),
            shown,
            counts[_twin_key(type_, shown)] > 1,
        )
        for account_id, type_, shown in drafts
    }


def labels_for(accounts: Iterable[object]) -> dict[int, AccountLabel]:
    """Подписи по списку ORM-объектов или DTO — глобал `phone_labels` шаблонов."""
    return build_labels(row_of(account) for account in accounts)

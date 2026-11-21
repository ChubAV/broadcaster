"""Общий для тестов Фазы 17 посев аккаунта и разбор подписей по адресу (D-06).

ЗАЧЕМ ОДИН МОДУЛЬ. Каждый тестовый файл проекта держит свою копию
`_seed_account`, и номер в них не ставится вовсе. Фазе 17 нужны аккаунты С
номером на двенадцати экранах: пятая копия посева расходилась бы с остальными
молча, поэтому посев и разбор живут здесь, а файлы Фазы 17 ввозят их так же,
как `seed_group` из `tests/conftest.py`:

    from tests.account_label_support import seed_account, label_texts

АДРЕС, А НЕ ПОДСТРОКА. Подпись аккаунта находится по атрибуту
`data-account-label="<id>"`, а не вхождением `"#1" in html`: подстрока `#1`
входит в `#10`, а вхождение слова «Номер неизвестен» у соседнего аккаунта
засчитало бы подпись не тому элементу. Разбор — `html.parser` стандартной
библиотеки со счётчиком вложенности, чтобы полный текст элемента включал его
потомков (канал, номер, `#id` двойника) и не выходил за его границы.

НОМЕР СТАВИТ ТОЛЬКО ПИСАТЕЛЬ ФАЗЫ 16. Конструктор и присваивание атрибуту
отказывают (`PhoneWriteOutsideWriter`), и это правильно: гейты единственного
писателя краснят запись мимо `app/application/accounts/phone.py`. Ручной номер
(Фаза 18, `manual_phone=`) ставит тот же единственный писатель — `set_manual_phone`,
тот же, которым пользуется форма; признак `phone_is_manual` он выставляет сам. «Как есть»
(значение, которое писатель не произвёл бы) ставит только тест и только внутри
`writer_scope()` — он моделирует писателя с ошибкой, а не обходит защиту
(шапка `app/models/phone_guard.py`).
"""

from __future__ import annotations

from html.parser import HTMLParser

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.accounts.phone import PhoneWrite, fill_reported_phone, set_manual_phone
from app.models.messenger_account import MessengerAccount
from app.models.phone_guard import writer_scope

# Текст пометки у номера, указанного вручную (Фаза 18, D-10): тесты сверяют его
# одной константой, а не литералом в каждом файле.
MANUAL_MARK = "указан вручную"

# Элементы без закрывающего тега: счётчик вложенности их не открывает.
_VOID = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
)


async def seed_account(
    session: AsyncSession,
    user_id: int,
    type_: str = "tg_user",
    *,
    phone: str | None = None,
    manual_phone: str | None = None,
    stored_as_is: str | None = None,
    status: str = "active",
    account_id: int | None = None,
) -> int:
    """Аккаунт пользователя; возвращает его id (объект после `commit` устаревает).

    `phone` — номер от автоисточника, записанный писателем Фазы 16 (разбор и
    приведение к E.164 делает он). `manual_phone` — ввод человека («как в форме»):
    его нормализует и пишет `set_manual_phone`, он же ставит `phone_is_manual`
    (Фаза 18). `stored_as_is` — значение, которое писатель не произвёл бы
    (неразбираемое), записывается внутри `writer_scope()`.
    """
    account = MessengerAccount(user_id=user_id, type=type_, credentials="creds", status=status)
    if account_id is not None:
        account.id = account_id
    session.add(account)
    await session.commit()
    new_id = account.id
    if phone is not None:
        written = await fill_reported_phone(session, new_id, phone)
        assert written is PhoneWrite.WRITTEN, f"писатель не записал номер {phone!r}: {written}"
        await session.commit()
    if manual_phone is not None:
        saved = await set_manual_phone(session, new_id, manual_phone)
        assert saved is not None, f"писатель не сохранил ручной номер {manual_phone!r}"
        await session.commit()
    if stored_as_is is not None:
        row = await session.get(MessengerAccount, new_id)
        with writer_scope():
            row.phone = stored_as_is
            await session.flush()
        await session.commit()
    return new_id


def _collapse(text: str) -> str:
    return " ".join(text.split())


class _Tracker(HTMLParser):
    """Один проход: тексты элементов с заданным атрибутом, заголовок, option, id."""

    def __init__(self, attr: str | None = None) -> None:
        super().__init__(convert_charrefs=True)
        self.attr = attr
        # Стек открытых элементов: (тег, индекс записи или None).
        self._stack: list[tuple[str, int | None]] = []
        # Записи в порядке открытия: [значение атрибута, куски текста, приглушён ли текст].
        self.entries: list[list] = []
        self.by_id: dict[str, list[str]] = {}
        self._id_slots: list[tuple[str, int]] = []
        self.title: list[str] = []
        self._in_title = False
        self._select: str | None = None
        self._option_value: str | None = None
        self._option_text: list[str] = []
        self.options: dict[str, dict[str, str]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v if v is not None else "") for k, v in attrs}
        entry_index: int | None = None
        if self.attr is not None and self.attr in a:
            self.entries.append([a[self.attr], [], False])
            entry_index = len(self.entries) - 1
        # Внутренний `acct-label__text`: приглушён ли он.
        classes = a.get("class", "").split()
        if "acct-label__text" in classes:
            for _t, idx in self._stack:
                if idx is not None:
                    self.entries[idx][2] = "mono--muted" in classes
        if "id" in a:
            self.by_id[a["id"]] = []
            if tag not in _VOID:
                self._id_slots.append((a["id"], len(self._stack)))
        if tag == "title":
            self._in_title = True
        if tag == "select" and "name" in a:
            self._select = a["name"]
            self.options.setdefault(self._select, {})
        if tag == "option" and self._select is not None:
            self._option_value = a.get("value", "")
            self._option_text = []
        if tag not in _VOID:
            self._stack.append((tag, entry_index))

    def handle_data(self, data: str) -> None:
        for _t, idx in self._stack:
            if idx is not None:
                self.entries[idx][1].append(data)
        for element_id, depth in self._id_slots:
            if depth < len(self._stack):
                self.by_id[element_id].append(data)
        if self._in_title:
            self.title.append(data)
        if self._option_value is not None:
            self._option_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag == "select":
            self._select = None
        if tag == "option" and self._option_value is not None and self._select is not None:
            self.options[self._select][self._option_value] = _collapse("".join(self._option_text))
            self._option_value = None
        # Закрыть до ближайшего одноимённого открытого элемента.
        for pos in range(len(self._stack) - 1, -1, -1):
            if self._stack[pos][0] == tag:
                del self._stack[pos:]
                break
        self._id_slots = [(i, d) for i, d in self._id_slots if d < len(self._stack)]


def _texts(html: str, attr: str) -> dict[str, list[str]]:
    parser = _Tracker(attr)
    parser.feed(html)
    parser.close()
    found: dict[str, list[str]] = {}
    for value, chunks, _muted in parser.entries:
        found.setdefault(value, []).append(_collapse("".join(chunks)))
    return found


def label_texts(html: str) -> dict[str, list[str]]:
    """Значение `data-account-label` → полные тексты каждого такого элемента (порядок документа)."""
    return _texts(html, "data-account-label")


def id_mark_texts(html: str) -> dict[str, list[str]]:
    """То же для `data-account-id`: знак и идентификатор двойника (или админа)."""
    return _texts(html, "data-account-id")


def muted_label_ids(html: str) -> set[str]:
    """Идентификаторы подписей, у которых внутренний `acct-label__text` приглушён."""
    parser = _Tracker("data-account-label")
    parser.feed(html)
    parser.close()
    return {value for value, _chunks, muted in parser.entries if muted}


def element_text(html: str, element_id: str) -> str | None:
    """Полный текст элемента с `id=…` (пробелы схлопнуты); нет элемента — `None`."""
    parser = _Tracker()
    parser.feed(html)
    parser.close()
    chunks = parser.by_id.get(element_id)
    return None if chunks is None else _collapse("".join(chunks))


def option_texts(html: str, select_name: str) -> dict[str, str]:
    """`value` → текст `<option>` в `<select name=…>`."""
    parser = _Tracker()
    parser.feed(html)
    parser.close()
    return dict(parser.options.get(select_name, {}))


def title_text(html: str) -> str:
    """Текст `<title>` страницы (пробелы схлопнуты)."""
    parser = _Tracker()
    parser.feed(html)
    parser.close()
    return _collapse("".join(parser.title))

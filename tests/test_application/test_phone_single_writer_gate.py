"""Гейт единственного писателя номера (D-13, PHONE-02).

ЗАЧЕМ. Правило, ради которого существует признак «указан вручную», одно: номер,
который пользователь ввёл сам, автоматический источник не затирает (D-07). Модуль
`app/application/accounts/phone.py` держит его условной записью — одним оператором
UPDATE «записать, если номера нет и он не ручной». Но правило держится, только пока
писатель ОДИН. Мастер подключения Фазы 19, скрипт дозаполнения Фазы 20 или форма
Фазы 18 со своей записью в колонку обходят модуль разом и возвращают пару
«прочитать — проверить в Python — записать», в промежуток которой ручной номер
затирается (тест гонки `tests/test_application/test_account_phone_race.py`). Ни
один тест модуля-писателя такого обхода не заметит: обход живёт в другом файле.
Поэтому этот гейт краснит суиту на любой записи номера вне модуля-писателя.

ВСЕЛЕННАЯ — `app/**/*.py` и `scripts/**/*.py`, ОБХОДОМ каталогов, а не перечнем:
модуль, добавленный следующей фазой, попадает под гейт сам. Вне вселенной, и это
решение, а не забывчивость:
- `alembic/` — ревизия описывает схему, а не пишет номер аккаунта;
- `tests/` — тесты сеют строки напрямую, это их работа;
- `max_worker/` — пишет `phone` в `SessionState` воркера (`max_worker/main.py`,
  `self.phone`, `state.phone`), то есть в память процесса, а не в базу.

ПОЧЕМУ РАЗБОР `ast`, А НЕ ПОИСК СТРОКИ. В `app/pages/accounts.py` три законных
вызова с `phone=`: `render(..., phone=...)`, `_max_step_markup(..., phone=...)` и
`messenger.start_session(phone=...)` — номер из формы MAX уходит в разметку и в
воркер, а не в колонку. Наивный предикат «любой `phone=`» покраснел бы на всех трёх
(замер разведки), и автор следующего плана снял бы гейт как шумный. Предикат судит
только формы, которые действительно пишут в колонку.

ВИДЫ ЗАПИСИ, КОТОРЫЕ ГЕЙТ ЛОВИТ (восемь). Пишущий вызов опознаётся по имени,
названному литералом, где бы оно ни стояло: последнее звено вызываемого
(`stmt.values(…)`); строка вызываемого `getattr(obj, "bulk_update_mappings")(…)`;
ссылка на пишущий API, поданная другому вызову вместе с его аргументами, —
`session.run_sync(Session.bulk_update_mappings, M, rows)` (и `fn=`),
`functools.partial(s.bulk_update_mappings, M)(rows)`, `asyncio.to_thread(…)`,
`loop.run_in_executor(None, …)`: судится вызов этого API с аргументами после
ссылки (и аргументами применения у `partial(…)(…)`); строка в
`operator.methodcaller("bulk_update_mappings", …)`. У `AsyncSession` нет `bulk_*`
вовсе, поэтому `run_sync` — естественный путь асинхронного скрипта к ним (план
16-17, ревью WR-10).
1. присваивание атрибуту `phone` / `phone_is_manual` (`=`, `+=`, аннотированное);
2. именованный аргумент `phone` / `phone_is_manual` в вызове `values(...)`,
   `update(...)`, `insert(...)`, `MessengerAccount(...)` или псевдонима модели,
   заведённого в том же модуле (`from … import MessengerAccount as Account`,
   `Model = MessengerAccount`) — в том числе распаковкой литерала:
   `values(**{"phone": x})`, `MessengerAccount(**{…})`, `values(**({…} | base))`;
3. ключ литерального отображения — строка `"phone"` / `"phone_is_manual"`, атрибут
   `MessengerAccount.phone`, индекс `table.c["phone"]` или `getattr(X, "phone")` —
   в позиционном аргументе `values(...)` и
   устаревшего `Query.update({...})`. Отображение — `{…}` (и `{**{…}, …}`) или
   вызов `dict(phone=…)` (и `dict({…})`, `dict(**{…})`, `dict([("phone", …)])`),
   взятое из литерального контейнера по грамматике `_literal_mappings`: список,
   кортеж, набор, comprehension и генератор (`values([{…} for …])`), обёртка
   `list(…)`, слияние `{…} | base`, склейка `+`, условное выражение, `*` и `:=`;
4. запись атрибута по имени в обход присваивания: `setattr(obj, "phone", …)`,
   `set_committed_value(obj, "phone_is_manual", …)`, `set_attribute(obj, "phone",
   …)`, `object.__setattr__(obj, "phone", …)` и `obj.__setattr__("phone", …)`;
5. сырой SQL в строковой константе, НЕ являющейся докстрингом, и в склейке `+`
   строковых констант — по механизму записи (`RAW_SQL_PHONE_WRITE`):
   (а) присваивание колонки номера в `SET` до `WHERE`, имя в кавычках или без;
   (б) строчный конструктор `SET (…, phone, …) =`; (в) голова пишущего оператора
   перед таблицей аккаунтов — `INSERT [OR …] INTO`, `REPLACE INTO`, `UPSERT INTO`,
   `MERGE INTO`, таблица в кавычках или без и с префиксом схемы; (г) загрузка —
   `COPY <таблица аккаунтов> … FROM` и `LOAD DATA … INTO TABLE <таблица
   аккаунтов>` (`COPY … TO` — выгрузка, чтение). Кавычки идентификатора — `"…"`,
   `` `…` `` и `[…]`: SQLite принимает все три. Сюда же
   COPY asyncpg в обход SQLAlchemy — `copy_records_to_table("messenger_accounts",
   …)` / `copy_to_table`. Голое слово `phone_is_manual` в строке не судится — на нём
   покраснела бы константа условия CHECK модели (`MANUAL_REQUIRES_PHONE`).
   Летопись: до плана 16-12 вид звучал «`UPDATE … SET … phone… =` либо `INSERT
   INTO messenger_accounts`», и шаблон требовал голые идентификаторы — кавычки,
   префикс схемы, `INSERT OR REPLACE`, `MERGE` и склейка проходили (ревью WR-08).
6. ключ номера в строках `execute` / `bulk_update_mappings` /
   `bulk_insert_mappings` / Alembic `op.bulk_insert` — словарь или `dict(...)`,
   поданный позиционно или аргументом `params=` / `mappings=` / `parameters=`
   (так называется аргумент строк у `Connection.execute`), прямо или в
   литеральном контейнере той же грамматики, что в виде 3 (comprehension строк из
   пар «аккаунт — номер» включительно): executemany по первичному ключу,
   естественная форма скрипта дозаполнения Фазы 20 (ревью WR-01, WR-08);
7. upsert пишет колонку при конфликте: ключ номера в литеральном отображении
   `set_` у `on_conflict_do_update` (ревью WR-01); у MySQL
   `on_duplicate_key_update` — именованный аргумент номера, `**{…}`, позиционное
   отображение и позиционный перечень пар `[("phone", …)]` (план 16-12);
8. колонка номера, названная ПОЗИЦИЕЙ: пара `(MessengerAccount.phone, x)` /
   `("phone_is_manual", x)` / `(table.c["phone"], x)` в `ordered_values(...)` (и
   `ordered_values(*[…])`) и имя колонки номера в перечне `from_select([…,
   "phone"], select)` (план 16-12, ревью WR-08).
Перечень пар (виды 3, 7, 8: `dict([…])`, `on_duplicate_key_update([…])`,
`ordered_values(*[…])`) разбирается той же грамматикой контейнера, что
отображения, — список, кортеж, `*`, comprehension, `+`, условное выражение.

ЦЕНА СТРОГОСТИ ВТОРОГО И ТРЕТЬЕГО ВИДОВ. Имя `update` берётся по последнему звену
вызова, поэтому `some_dict.update(phone=x)` и `some_dict.update({"phone": x})` тоже
покраснеют, хотя в колонку не пишут. Это осознанно: отличить `dict.update` от
`sqlalchemy.update` и `Query.update` по исходнику без типов нельзя, а ложное
срабатывание здесь снимается переименованием ключа, тогда как пропущенный второй
писатель снимается только потерей ручного номера у пользователя. Псевдоним модели
разрешается по всему модулю, без учёта областей видимости: имя, однажды связанное
с `MessengerAccount`, считается моделью в любой функции того же файла.

ЦЕНА СТРОГОСТИ ШЕСТОГО ВИДА — та же по природе. `execute` судится по ключам строк,
а не по первому аргументу: иначе `stmt = update(MessengerAccount);
session.execute(stmt, rows)` прошёл бы. Поэтому параметр привязки `:phone` в
словаре у `execute` для ЧТЕНИЯ — `execute(text("… WHERE phone = :phone"),
{"phone": p})` — тоже краснеет; снимается переименованием параметра (`:number`).

ГРАНИЦА ПРЕДИКАТА — через механизм, а не через «всё». Ловится всякая запись, в
которой колонка номера — или таблица аккаунтов во вставке, загрузке и слиянии —
названа литералом в самом пишущем вызове, в его аргументе-контейнере (грамматика
`_literal_mappings`) или в строковой константе SQL (и в склейке `+` констант).
Вне охвата, каждая форма с причиной, по которой синтаксическому предикату она
недостижима:
(1) значение, пришедшее в пишущий вызов ИМЕНЕМ или результатом другого вызова, —
    переменная, параметр, `build_rows()`, `values(**fields)`, `{k: v for …}` с
    вычисленными ключами: поток данных предикат не прослеживает, даже когда
    литерал стоит строкой выше в том же файле;
(2) имя колонки или SQL, вычисленные во время исполнения, — `setattr(obj, name,
    …)`, f-строка с колонкой в подстановке, `.format(col)`, склейка с переменной;
(3) вставка позиционным кортежем значений без имён колонок —
    `insert(MessengerAccount).values((…))`: колонку по исходнику не назвать,
    порядок колонок живёт в модели;
(4) пишущий API без имени или под псевдонимом из другого модуля —
    `type(account)(phone=…)`, псевдоним модели, заведённый в чужом файле: без
    типов он неотличим от законного `render(…, phone=…)`;
(5) НЕ запись в колонку — `account.__dict__["phone"] = …`, `vars(account)[…] = …`:
    обход инструментовки ORM, оператора UPDATE не порождает и в базу не уходит.
Такие формы в коде записи номера сами по себе повод для ревью. Форма, которая
под механизм подпадает, но предикатом не ловится, — слепота предиката, а не
граница средства: повод дописать строку `LITERAL_FORM_CASES` и предикат.

Летопись границы. До плана 16-09 граница называлась словами «значение, собранное
во время исполнения», но пять литеральных форм (executemany по первичному ключу,
`dict(...)`, `**{…}`, `set_` при конфликте, `bulk_*_mappings`) проходили молча,
хотя видны в исходнике (ревью WR-01, 2026-10-08). До плана 16-12 абзац
заканчивался заявлением «Всё, что видно литералом в исходнике, ловится», и оно
было неверно дважды: ревью WR-01 (2026-10-08) нашло пять литеральных форм, ревью
WR-08 (2026-10-09) — ещё девять (`parameters=`, comprehension и генератор строк,
`values([…for…])`, кавычки у колонки и у таблицы, префикс схемы, `ordered_values`,
`object.__setattr__`). План 16-12 чинит их и формы тех же семейств, найденные
перебором, и заменяет заявление «всё» заявлением через механизм.

РЕЕСТР ИСКЛЮЧЕНИЙ `PHONE_WRITER_EXCEPTIONS` — поимённо, с причиной, и в нём ровно
модуль-писатель. Второй исключённый модуль есть второй писатель, поэтому
расширение реестра — решение владельца, а не правка ради зелени; состав реестра
закреплён отдельным правилом. Исключение снимает все виды, кроме первого, и
НИКОГДА не снимает вид 1: писатель пишет только операторами UPDATE и зеркалит значение
`set_committed_value`, а присваивание атрибуту сделало бы объект грязным, и ORM
выдала бы на коммите второй, безусловный UPDATE мимо условной записи. Это строже
буквы D-13 и проверяется контролем над исходником писателя с подложенным
присваиванием.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import re
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Каталоги вселенной гейта. Множество файлов ВЫВОДИТСЯ их обходом.
WRITER_TREES = ("app", "scripts")

# Единственный законный писатель номера (D-12, D-13).
PHONE_WRITER_MODULE = "app/application/accounts/phone.py"

# Колонки номера в `messenger_accounts` (ревизия 0023).
PHONE_COLUMNS = frozenset({"phone", "phone_is_manual"})

# Вызовы, именованный аргумент которых пишет колонку: Core-операторы и конструктор
# модели. Имя берётся по последнему звену (`func.id` или `func.attr`). Псевдонимы
# модели, заведённые в том же модуле, добавляются к набору при разборе исходника
# (`_module_model_aliases`).
WRITE_CALL_NAMES = frozenset({"values", "update", "insert", "MessengerAccount"})

# Имя модели аккаунта: его псевдонимы в модуле — тоже пишущие вызовы.
MODEL_NAME = "MessengerAccount"

# Вызовы, пишущие атрибут по имени из второго позиционного аргумента. `__setattr__`
# (`object.__setattr__(account, "phone", x)`) и `set_attribute`
# (`sqlalchemy.orm.attributes.set_attribute`) добавлены планом 16-12 (ревью WR-08);
# у `__setattr__` судится и ПЕРВЫЙ позиционный аргумент — форма вызова через объект
# `account.__setattr__("phone", x)`, где имени атрибута предшествует только он сам.
NAMED_ATTRIBUTE_WRITERS = frozenset(
    {"setattr", "set_committed_value", "__setattr__", "set_attribute"}
)

# Вызовы, называющие колонку ПОЗИЦИЕЙ, а не именованным аргументом или ключом
# словаря: `ordered_values((колонка, значение), …)` и `from_select([имена колонок],
# select)` (план 16-12, ревью WR-08).
POSITIONAL_COLUMN_CALL_NAMES = frozenset({"ordered_values", "from_select"})

# Вызовы, чьи позиционные аргументы несут строки для executemany: словарь или
# список словарей по первичному ключу (ревью WR-01). Судятся ключи строк, а не
# первый аргумент: `stmt = update(...); session.execute(stmt, rows)` иначе прошёл бы.
#
# `bulk_insert` — Alembic `op.bulk_insert(table, rows)`: строки вставки стоят вторым
# позиционным аргументом, который правило и так обходит (план 16-12).
ROW_MAPPING_CALL_NAMES = frozenset(
    {"execute", "bulk_update_mappings", "bulk_insert_mappings", "bulk_insert"}
)

# Именованные аргументы тех же вызовов, несущие строки: `execute(stmt, params=…)`,
# `bulk_update_mappings(mapper, mappings=…)` — та же литеральная форма, что позиционно.
# У `Connection.execute` / `AsyncConnection.execute` в SQLAlchemy 2.0.46 аргумент
# строк называется `parameters` (замер верификатора через `inspect.signature`), у
# `Session.execute` — `params`. До плана 16-12 имени `parameters` в наборе не было,
# и естественная форма скрипта дозаполнения на соединении проходила (ревью WR-08).
ROW_MAPPING_KEYWORDS = frozenset({"params", "mappings", "parameters"})

# Именованный параметр ССЫЛКИ на функцию: `fn` у `AsyncSession.run_sync` /
# `AsyncConnection.run_sync` — `(self, fn, *arg, **kw)`, замер `inspect.signature`,
# SQLAlchemy 2.0.46. У `asyncio.to_thread` и `functools.partial` ссылка
# позиционно-только (`partial(func=…)` и `to_thread(func=…)` падают `TypeError`,
# замер 2026-10-12), у `loop.run_in_executor` именованных аргументов нет вовсе
# (план 16-17, ревью WR-10).
REFERENCE_KEYWORDS = frozenset({"fn"})

# Обёртки литерального контейнера: `list(<генератор словарей>)` и подобные с ОДНИМ
# позиционным аргументом и без именованных — разбираются по этому аргументу.
LITERAL_CONTAINER_WRAPPERS = frozenset({"list", "tuple", "set", "iter"})

# Upsert: именованный аргумент `set_` у `on_conflict_do_update` пишет колонки при
# конфликте (ревью WR-01). MySQL `on_duplicate_key_update` (план 16-12) несёт
# колонки именованными аргументами, позиционным отображением или перечнем пар; диалекта
# в проекте нет, но форма литеральна, и оставить её в границе значило бы назвать
# достижимую форму недостижимой.
UPSERT_CALL_NAMES = frozenset({"on_conflict_do_update", "on_duplicate_key_update"})

# Кавычки идентификатора SQL: двойные (стандарт, PostgreSQL), обратные (MySQL) и
# квадратные скобки (SQL Server); SQLite, на которой гоняется суита, принимает все три.
_SQL_QUOTE = r'["`\[\]]?'

# Таблица аккаунтов в SQL: в кавычках или без, с необязательным префиксом схемы
# (`public.messenger_accounts`, `"public"."messenger_accounts"`).
_ACCOUNTS_TABLE_SQL = (
    r"(?:" + _SQL_QUOTE + r"\w+" + _SQL_QUOTE + r"\s*\.\s*)?"
    + _SQL_QUOTE + r"messenger_accounts\b" + _SQL_QUOTE
)

# Пишущий SQL — по МЕХАНИЗМУ записи, четырьмя альтернативами (без учёта регистра):
# (а) присваивание колонки номера в `SET` до `WHERE` (фильтр по номеру записью не
#     является) — имя `phone` / `phone_is_manual` в кавычках или без;
# (б) строчный конструктор `SET (…, phone, …) = (…)`;
# (в) голова пишущего оператора перед таблицей аккаунтов — `INSERT [OR <конфликт>]
#     INTO`, `INSERT IGNORE INTO`, `REPLACE INTO`, `UPSERT INTO`, `MERGE INTO`;
# (г) загрузка в таблицу аккаунтов — `COPY <таблица> [(колонки)] FROM` и MySQL
#     `LOAD DATA … INTO TABLE <таблица>`; `COPY … TO` — выгрузка, то есть чтение, и
#     не судится.
# Летопись: до плана 16-12 шаблон требовал голое `phone =` и голую
# `messenger_accounts` после `INSERT INTO`, и кавычки у идентификатора, префикс
# схемы, `INSERT OR REPLACE`, `REPLACE` / `MERGE INTO`, `COPY … FROM` и строчный
# конструктор проводили запись мимо гейта (ревью WR-08, 2026-10-09).
RAW_SQL_PHONE_WRITE = re.compile(
    r"\bupdate\b[\s\S]*?\bset\b(?:(?!\bwhere\b)[\s\S])*?\bphone(?:_is_manual)?\b"
    + _SQL_QUOTE
    + r"\s*="
    + r"|\bupdate\b[\s\S]*?\bset\s*\([^)]*\bphone(?:_is_manual)?\b[^)]*\)\s*="
    + r"|\b(?:insert\s+(?:or\s+\w+\s+|ignore\s+)?|replace\s+|upsert\s+|merge\s+)into\s+"
    + _ACCOUNTS_TABLE_SQL
    + r"|\bcopy\s+"
    + _ACCOUNTS_TABLE_SQL
    + r"\s*(?:\([^)]*\)\s*)?from\b"
    + r"|\bload\s+data\b[\s\S]*?\binto\s+table\s+"
    + _ACCOUNTS_TABLE_SQL,
    re.IGNORECASE,
)

# COPY asyncpg в обход SQLAlchemy: `conn.copy_records_to_table("messenger_accounts",
# records=…)` / `copy_to_table(…)` загружают строки в таблицу, названную первым
# позиционным аргументом или аргументом `table_name` (план 16-12).
ROW_COPY_CALL_NAMES = frozenset({"copy_records_to_table", "copy_to_table"})
_ACCOUNTS_TABLE_NAME = re.compile(r'(?:"?\w+"?\.)?"?messenger_accounts"?')

KIND_ASSIGNMENT = "присваивание"
KIND_KEYWORD = "именованный аргумент"
KIND_DICT_KEY = "ключ словаря values"
KIND_SETATTR = "запись атрибута по имени"
KIND_RAW_SQL = "сырой SQL"
KIND_ROW_MAPPING = "ключ словаря строк"
KIND_UPSERT_SET = "set_ при конфликте"
KIND_POSITIONAL_COLUMN = "колонка позицией"

# Не вид находки, а пометка строк `JUDGED_PARAMETERS` о параметре ССЫЛКИ: у них вид
# находки — вид API, названного ссылкой (`run_sync(Session.bulk_update_mappings, …)`
# даёт вид строк `bulk_update_mappings`).
KIND_BY_REFERENCE = "вид API по ссылке"


class JudgedParameter(NamedTuple):
    """Судимый параметр судимого API: где он стоит и под каким именем.

    `api` — путь для правила-сторожа (`importlib` + `getattr` по звеньям); `call` —
    последнее звено вызова в исходнике; `signature_index` — индекс в
    `inspect.signature(api).parameters` (у методов `self` — индекс 0);
    `call_index` — позиция в записи вызова, как её пишет код
    (`session.execute(stmt, rows)` — `rows` на позиции 1); `kind` — вид находки.
    """

    api: str
    call: str
    parameter: str
    signature_index: int
    call_index: int
    kind: str


# Классы сессии и соединения в путях таблицы ниже.
_SESSION = "sqlalchemy.orm.Session"
_ASYNC_SESSION = "sqlalchemy.ext.asyncio.AsyncSession"
_CONNECTION = "sqlalchemy.engine.Connection"
_ASYNC_CONNECTION = "sqlalchemy.ext.asyncio.AsyncConnection"

# Перебор сигнатур судимых API (план 16-17, ревью WR-10): замер `inspect.signature`
# 2026-10-12 на установленных SQLAlchemy 2.0.46, Alembic 1.18.4, asyncpg 0.31.0 и
# builtins. Каждый параметр здесь судится при ЛЮБОМ литеральном связывании —
# позицией, именем, `**{"имя": …}` и `*[…]`; таблицу сверяет с установленными
# сигнатурами правило-сторож, а правило-матрица — каждую строку с каждой формой.
# Подъём библиотеки, сменивший имя или позицию параметра, краснит сторож, а не
# оставляет гейт слепым молча (пин версий отложен владельцем — IN-02).
#
# `setattr(obj, name, value, /)` и `object.__setattr__(self, name, value, /)` —
# позиционно-только: `setattr(account, name="phone", value=x)` падает `TypeError:
# setattr() takes no keyword arguments` и ничего не пишет. Гейт судит и такую форму —
# по цене строгости: вызов, который не исполнится, законной формой не является.
#
# API без именованного позиционного параметра — у них именованной формы нет, и они
# судятся, как прежде (каждый позиционный аргумент, `*[…]`, именованные колонки,
# `**{…}`): `Update.values` / `Insert.values` — `(self, *args, **kwargs)`;
# `Update.ordered_values` — `(self, *args)`; MySQL `Insert.on_duplicate_key_update` —
# `(self, *args, **kw)`; конструктор модели — `**kwargs`. У `AsyncSession` нет
# `bulk_*` вовсе — к ним ведёт только `run_sync`, поэтому две последние строки —
# главная ось асинхронного проекта.
JUDGED_PARAMETERS: tuple[JudgedParameter, ...] = (
    JudgedParameter("sqlalchemy.orm.Query.update", "update", "values", 1, 0, KIND_DICT_KEY),
    JudgedParameter(
        "sqlalchemy.orm.attributes.set_attribute", "set_attribute", "key", 1, 1, KIND_SETATTR
    ),
    JudgedParameter(
        "sqlalchemy.orm.attributes.set_committed_value",
        "set_committed_value",
        "key",
        1,
        1,
        KIND_SETATTR,
    ),
    JudgedParameter("builtins.setattr", "setattr", "name", 1, 1, KIND_SETATTR),
    JudgedParameter("builtins.object.__setattr__", "__setattr__", "name", 1, 1, KIND_SETATTR),
    JudgedParameter(
        "sqlalchemy.sql.dml.Insert.from_select",
        "from_select",
        "names",
        1,
        0,
        KIND_POSITIONAL_COLUMN,
    ),
    JudgedParameter(
        "sqlalchemy.dialects.postgresql.dml.Insert.on_conflict_do_update",
        "on_conflict_do_update",
        "set_",
        4,
        3,
        KIND_UPSERT_SET,
    ),
    JudgedParameter(
        "sqlalchemy.dialects.sqlite.dml.Insert.on_conflict_do_update",
        "on_conflict_do_update",
        "set_",
        3,
        2,
        KIND_UPSERT_SET,
    ),
    # Исполняющие вызовы: у `Session` / `AsyncSession` параметр строк — `params`, у
    # `Connection` / `AsyncConnection` — `parameters`; до плана 16-17 судился один
    # `execute`, а `scalar(s)` / `stream*` / `exec_driver_sql` — нет (ревью WR-10).
    JudgedParameter(f"{_SESSION}.execute", "execute", "params", 2, 1, KIND_ROW_MAPPING),
    JudgedParameter(f"{_ASYNC_SESSION}.execute", "execute", "params", 2, 1, KIND_ROW_MAPPING),
    JudgedParameter(f"{_CONNECTION}.execute", "execute", "parameters", 2, 1, KIND_ROW_MAPPING),
    JudgedParameter(
        f"{_ASYNC_CONNECTION}.execute", "execute", "parameters", 2, 1, KIND_ROW_MAPPING
    ),
    JudgedParameter(f"{_SESSION}.scalar", "scalar", "params", 2, 1, KIND_ROW_MAPPING),
    JudgedParameter(f"{_ASYNC_SESSION}.scalar", "scalar", "params", 2, 1, KIND_ROW_MAPPING),
    JudgedParameter(f"{_CONNECTION}.scalar", "scalar", "parameters", 2, 1, KIND_ROW_MAPPING),
    JudgedParameter(
        f"{_ASYNC_CONNECTION}.scalar", "scalar", "parameters", 2, 1, KIND_ROW_MAPPING
    ),
    JudgedParameter(f"{_SESSION}.scalars", "scalars", "params", 2, 1, KIND_ROW_MAPPING),
    JudgedParameter(f"{_ASYNC_SESSION}.scalars", "scalars", "params", 2, 1, KIND_ROW_MAPPING),
    JudgedParameter(f"{_CONNECTION}.scalars", "scalars", "parameters", 2, 1, KIND_ROW_MAPPING),
    JudgedParameter(
        f"{_ASYNC_CONNECTION}.scalars", "scalars", "parameters", 2, 1, KIND_ROW_MAPPING
    ),
    JudgedParameter(f"{_ASYNC_SESSION}.stream", "stream", "params", 2, 1, KIND_ROW_MAPPING),
    JudgedParameter(
        f"{_ASYNC_CONNECTION}.stream", "stream", "parameters", 2, 1, KIND_ROW_MAPPING
    ),
    JudgedParameter(
        f"{_ASYNC_SESSION}.stream_scalars", "stream_scalars", "params", 2, 1, KIND_ROW_MAPPING
    ),
    JudgedParameter(
        f"{_ASYNC_CONNECTION}.stream_scalars",
        "stream_scalars",
        "parameters",
        2,
        1,
        KIND_ROW_MAPPING,
    ),
    JudgedParameter(
        f"{_CONNECTION}.exec_driver_sql", "exec_driver_sql", "parameters", 2, 1, KIND_ROW_MAPPING
    ),
    JudgedParameter(
        f"{_ASYNC_CONNECTION}.exec_driver_sql",
        "exec_driver_sql",
        "parameters",
        2,
        1,
        KIND_ROW_MAPPING,
    ),
    JudgedParameter(
        f"{_SESSION}.bulk_update_mappings",
        "bulk_update_mappings",
        "mappings",
        2,
        1,
        KIND_ROW_MAPPING,
    ),
    JudgedParameter(
        f"{_SESSION}.bulk_insert_mappings",
        "bulk_insert_mappings",
        "mappings",
        2,
        1,
        KIND_ROW_MAPPING,
    ),
    JudgedParameter(
        "alembic.operations.Operations.bulk_insert", "bulk_insert", "rows", 2, 1, KIND_ROW_MAPPING
    ),
    JudgedParameter(
        "asyncpg.connection.Connection.copy_records_to_table",
        "copy_records_to_table",
        "table_name",
        1,
        0,
        KIND_RAW_SQL,
    ),
    JudgedParameter(
        "asyncpg.connection.Connection.copy_to_table",
        "copy_to_table",
        "table_name",
        1,
        0,
        KIND_RAW_SQL,
    ),
    JudgedParameter(f"{_ASYNC_SESSION}.run_sync", "run_sync", "fn", 1, 0, KIND_BY_REFERENCE),
    JudgedParameter(
        f"{_ASYNC_CONNECTION}.run_sync", "run_sync", "fn", 1, 0, KIND_BY_REFERENCE
    ),
)

# Строки таблицы, чей параметр позиционно-только (сноска выше).
POSITIONAL_ONLY_APIS = frozenset({"builtins.setattr", "builtins.object.__setattr__"})

# Реестр исключений: путь → причина. РОВНО ОДНА ЗАПИСЬ; см. шапку модуля.
PHONE_WRITER_EXCEPTIONS: dict[str, str] = {
    PHONE_WRITER_MODULE: (
        "единственный писатель номера (D-12, D-13): условные UPDATE автоисточника, "
        "запись и очистка ручного номера, зеркало set_committed_value"
    ),
}

# Виды, которые исключение реестра НЕ снимает никогда.
NEVER_EXEMPT_KINDS = frozenset({KIND_ASSIGNMENT})


def writer_sources(root: Path) -> list[Path]:
    """Все исходники вселенной гейта под `root` — ОБХОДОМ, а не перечнем.

    Параметр `root`, а не жёсткий путь, затем, чтобы обход можно было натравить на
    синтетическое дерево в `tmp_path` и доказать, что подложенный файл им находится.
    """
    found: list[Path] = []
    for tree in WRITER_TREES:
        base = root / tree
        if base.is_dir():
            found.extend(base.rglob("*.py"))
    return sorted(found)


def phone_write_offences(source: str, path: str) -> list[str]:
    """Записи номера в исходнике — строками «`путь:строка` — вид — предмет».

    Чистая функция над текстом: исключения реестра здесь НЕ применяются, поэтому ею
    же доказывается, что в самом модуле-писателе запись видна.
    """
    return [_format(path, write) for write in _phone_writes(source, path)]


def judged_offences(source: str, path: str) -> list[str]:
    """Находки, которые гейт судит: предикат плюс исключения реестра.

    В пути из реестра отбрасываются все виды, кроме присваивания; присваивание
    (вид 1) судится везде.
    """
    exempt = path in PHONE_WRITER_EXCEPTIONS
    return [
        _format(path, write)
        for write in _phone_writes(source, path)
        if not exempt or write[2] in NEVER_EXEMPT_KINDS
    ]


def _format(path: str, write: tuple[int, int, str, str]) -> str:
    line, _column, kind, subject = write
    return f"{path}:{line} — {kind} — {subject}"


def _phone_writes(source: str, path: str) -> list[tuple[int, int, str, str]]:
    """Записи номера видов шапки: (строка, столбец, вид, предмет), по порядку в файле."""
    tree = ast.parse(source, filename=path)
    docstrings = _docstring_nodes(tree)
    # Звенья склейки строк внутри более длинной склейки: судится только внешняя.
    inner_concatenations = {
        id(child)
        for node in ast.walk(tree)
        if _is_concatenation(node) and _folded_string(node) is not None
        for child in (node.left, node.right)
        if _is_concatenation(child)
    }
    # Пишущие вызовы этого исходника: общий набор плюс псевдонимы модели в модуле.
    write_names = WRITE_CALL_NAMES | _module_model_aliases(tree)
    # Имена, которые судятся у ссылки: всякий пишущий API, который судит `_judge_call`.
    judged_names = _judged_call_names(write_names)
    # Вызовы, чей результат тут же вызывается (`partial(ref, …)(…)`): ссылка в них
    # судится один раз — у применения, с аргументами обоих вызовов.
    applied = {
        id(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Call)
    }
    found: list[tuple[int, int, str, str]] = []

    def record(node: ast.AST, kind: str, subject: str) -> None:
        found.append((node.lineno, node.col_offset, kind, subject))

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                for attribute in _assigned_attributes(target):
                    record(attribute, KIND_ASSIGNMENT, ast.unparse(attribute))
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            for attribute in _assigned_attributes(node.target):
                record(attribute, KIND_ASSIGNMENT, ast.unparse(attribute))
        elif isinstance(node, ast.Call):
            name = _call_name(node)
            if name is not None:
                _judge_call(node, name, write_names, record)
            # `methodcaller("…", …)` судится у себя: его применение подаёт объект,
            # а не аргументы API.
            if id(node) not in applied or name == "methodcaller":
                for synthetic, referenced in _referenced_calls(node, judged_names):
                    _judge_call(synthetic, referenced, write_names, record)
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
            and RAW_SQL_PHONE_WRITE.search(node.value)
        ):
            snippet = " ".join(node.value.split())[:60]
            record(node, KIND_RAW_SQL, f"«{snippet}»")
        elif (
            _is_concatenation(node)
            and id(node) not in inner_concatenations
            and (folded := _folded_string(node)) is not None
            # Если константа склейки совпала сама, находка у неё уже есть.
            and not any(
                RAW_SQL_PHONE_WRITE.search(part.value)
                for part in ast.walk(node)
                if isinstance(part, ast.Constant)
            )
            and RAW_SQL_PHONE_WRITE.search(folded)
        ):
            snippet = " ".join(folded.split())[:60]
            record(node, KIND_RAW_SQL, f"«{snippet}»")

    return sorted(found)


def _judge_call(
    node: ast.Call,
    name: str,
    write_names: frozenset[str],
    record: Callable[[ast.AST, str, str], None],
) -> None:
    """Ветки видов 2–8 у одного вызова с именем `name`.

    Имя передаётся, а не берётся из узла, затем, чтобы тем же веткам подать и
    «синтетический» вызов API, названного ссылкой (`run_sync(Session.
    bulk_update_mappings, …)`) или строкой (`methodcaller("…", …)`).
    """
    if name in write_names:
        for keyword in node.keywords:
            if keyword.arg in PHONE_COLUMNS:
                record(keyword, KIND_KEYWORD, f"{name}({keyword.arg}=…)")
            elif keyword.arg is None:
                # `values(**{"phone": x})`, `MessengerAccount(**dict(phone=x))`
                for mapping in _literal_mappings(keyword.value):
                    for key, column in _mapping_phone_keys(mapping):
                        text = _mapping_key_text(key, column)
                        record(key, KIND_KEYWORD, f"{name}(**{text})")
    if name in ("values", "update"):
        # `update({...})` — устаревший `Query.update({"phone": x})`.
        for key, column in _values_dict_keys(node):
            record(key, KIND_DICT_KEY, f"{name}({_mapping_key_text(key, column)})")
    if name in POSITIONAL_COLUMN_CALL_NAMES:
        for column_node, column in _positional_phone_columns(node):
            subject = (
                f"ordered_values(({column}, …))"
                if name == "ordered_values"
                else f"from_select([{column!r}, …])"
            )
            record(column_node, KIND_POSITIONAL_COLUMN, subject)
    if name in ROW_MAPPING_CALL_NAMES:
        arguments = list(node.args) + [
            keyword.value
            for keyword in node.keywords
            if keyword.arg in ROW_MAPPING_KEYWORDS
        ]
        for argument in arguments:
            # Скобки — когда строки лежат в контейнере или comprehension,
            # а не голым отображением.
            rows = not (isinstance(argument, ast.Dict) or _is_dict_call(argument))
            for mapping in _literal_mappings(argument):
                for key, column in _mapping_phone_keys(mapping):
                    text = _mapping_key_text(key, column)
                    subject = f"{name}([{text}])" if rows else f"{name}({text})"
                    record(key, KIND_ROW_MAPPING, subject)
    if name in UPSERT_CALL_NAMES and name == "on_conflict_do_update":
        for keyword in node.keywords:
            if keyword.arg != "set_":
                continue
            for mapping in _literal_mappings(keyword.value):
                for key, column in _mapping_phone_keys(mapping):
                    text = _mapping_key_text(key, column)
                    record(key, KIND_UPSERT_SET, f"{name}(set_={text})")
    elif name in UPSERT_CALL_NAMES:
        # MySQL `on_duplicate_key_update`: именованные аргументы, `**{…}`,
        # позиционное отображение и позиционный перечень пар.
        for keyword in node.keywords:
            if keyword.arg in PHONE_COLUMNS:
                record(keyword, KIND_UPSERT_SET, f"{name}({keyword.arg}=…)")
            elif keyword.arg is None:
                for mapping in _literal_mappings(keyword.value):
                    for key, column in _mapping_phone_keys(mapping):
                        text = _mapping_key_text(key, column)
                        record(key, KIND_UPSERT_SET, f"{name}(**{text})")
        for argument in node.args:
            for mapping in _literal_mappings(argument):
                for key, column in _mapping_phone_keys(mapping):
                    text = _mapping_key_text(key, column)
                    record(key, KIND_UPSERT_SET, f"{name}({text})")
            for key, column in _phone_pairs(argument):
                record(key, KIND_UPSERT_SET, f"{name}([({column!r}, …)])")
    if name in NAMED_ATTRIBUTE_WRITERS:
        # Имя атрибута — второй позиционный аргумент; у `__setattr__` ещё и
        # первый (`account.__setattr__("phone", x)`).
        positions = (0, 1) if name == "__setattr__" else (1,)
        for position in positions:
            if position >= len(node.args):
                break
            attribute = node.args[position]
            if isinstance(attribute, ast.Constant) and attribute.value in PHONE_COLUMNS:
                shown = (
                    f"{name}({attribute.value!r}, …)"
                    if position == 0
                    else f"{name}(…, {attribute.value!r}, …)"
                )
                record(node, KIND_SETATTR, shown)
                break
    if name in ROW_COPY_CALL_NAMES:
        table = node.args[0] if node.args else next(
            (k.value for k in node.keywords if k.arg == "table_name"), None
        )
        if (
            isinstance(table, ast.Constant)
            and isinstance(table.value, str)
            and _ACCOUNTS_TABLE_NAME.fullmatch(table.value)
        ):
            record(node, KIND_RAW_SQL, f"{name}({table.value!r}, …)")


def _judged_call_names(write_names: frozenset[str]) -> frozenset[str]:
    """Имена пишущих API, которые судит `_judge_call`, — их и опознаёт ссылка."""
    return (
        write_names
        | NAMED_ATTRIBUTE_WRITERS
        | POSITIONAL_COLUMN_CALL_NAMES
        | ROW_MAPPING_CALL_NAMES
        | UPSERT_CALL_NAMES
        | ROW_COPY_CALL_NAMES
    )


def _getattr_literal(node: ast.AST) -> str | None:
    """Строка в `getattr(<что угодно>, "<строка>")`, иначе `None`."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and isinstance(node.args[1].value, str)
    ):
        return node.args[1].value
    return None


def _reference_name(node: ast.AST) -> str | None:
    """Имя ССЫЛКИ на функцию: `Name.id`, `Attribute.attr` или строка `getattr(…, "…")`.

    Ссылка — функция, поданная другому вызову без вызова: `run_sync(Session.
    bulk_update_mappings, …)`, `partial(set_attribute, …)`. У прочих узлов — `None`.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return _getattr_literal(node)


def _synthetic_call(
    origin: ast.Call, func: ast.expr, args: list[ast.expr], keywords: list[ast.keyword]
) -> ast.Call:
    """Вызов `func(*args, **keywords)` на месте `origin`: строка находки — настоящая."""
    return ast.copy_location(ast.Call(func=func, args=args, keywords=keywords), origin)


def _referenced_calls(
    call: ast.Call, judged_names: frozenset[str]
) -> list[tuple[ast.Call, str]]:
    """Вызовы пишущего API, названного в `call` ссылкой или строкой: (вызов, имя API).

    - `operator.methodcaller("<имя>", …)` — вызов `<имя>` с аргументами после строки;
    - ссылка на судимый API среди позиционных аргументов (или в `fn=`, параметре
      ссылки `run_sync`) — вызов этого API с позиционными аргументами ПОСЛЕ ссылки
      и именованными аргументами `call`, кроме `fn`: `run_sync`, `to_thread`,
      `run_in_executor`, `partial` подают их функции именно так;
    - `partial(ref, …)(…)` — к ним добавляются аргументы применения; судится у
      применения (`call` с `func`-вызовом), а у самого `partial` — нет.
    Вызов, имя которого само судимо, судится напрямую и ссылкой не разбирается.
    """
    name = _call_name(call)
    if name == "methodcaller":
        head = call.args[0] if call.args else None
        if (
            isinstance(head, ast.Constant)
            and isinstance(head.value, str)
            and head.value in judged_names
        ):
            func = ast.copy_location(ast.Name(id=head.value, ctx=ast.Load()), head)
            return [
                (_synthetic_call(call, func, list(call.args[1:]), list(call.keywords)), head.value)
            ]
        return []
    if name in judged_names or name == "getattr":
        return []
    source, outer_args, outer_keywords = call, [], []
    if isinstance(call.func, ast.Call) and _call_name(call.func) not in (
        "getattr",
        "methodcaller",
    ):
        # `partial(ref, …)(…)`: ссылка — в применяемом вызове, хвост — у применения.
        if _call_name(call.func) in judged_names:
            return []
        source, outer_args, outer_keywords = call.func, list(call.args), list(call.keywords)
    positional = list(source.args)
    for index, argument in enumerate(positional):
        referenced = _reference_name(argument)
        if referenced in judged_names:
            keywords = [k for k in source.keywords if k.arg not in REFERENCE_KEYWORDS]
            return [
                (
                    _synthetic_call(
                        call, argument, positional[index + 1 :] + outer_args,
                        keywords + outer_keywords,
                    ),
                    referenced,
                )
            ]
    for keyword in source.keywords:
        if keyword.arg in REFERENCE_KEYWORDS:
            referenced = _reference_name(keyword.value)
            if referenced in judged_names:
                keywords = [k for k in source.keywords if k is not keyword]
                return [
                    (
                        _synthetic_call(
                            call, keyword.value, positional + outer_args,
                            keywords + outer_keywords,
                        ),
                        referenced,
                    )
                ]
    return []


def _is_concatenation(node: ast.AST) -> bool:
    return isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)


def _folded_string(node: ast.AST) -> str | None:
    """Строка, если узел — строковая константа или склейка `+` из одних строковых констант.

    Иначе `None`: переменная, f-строка, `.format(…)` в склейке — SQL, собранный во
    время исполнения, лежит за объявленной границей предиката.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if _is_concatenation(node):
        left = _folded_string(node.left)
        right = _folded_string(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Узлы-докстринги модуля, классов и функций: прозу о SQL гейт не судит."""
    found: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ) and node.body:
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                found.add(id(first.value))
    return found


def _values_dict_keys(call: ast.Call) -> list[tuple[ast.AST, str]]:
    """Ключи номера в позиционных отображениях `values(...)` / `update(...)`.

    Отображение — `{...}` или `dict(...)` в литеральном контейнере грамматики
    `_literal_mappings`; список — многострочная вставка; у `update` — устаревший
    `Query.update({"phone": x})`.
    """
    return [
        found
        for argument in call.args
        for mapping in _literal_mappings(argument)
        for found in _mapping_phone_keys(mapping)
    ]


def _literal_mappings(node: ast.expr) -> list[ast.expr]:
    """Литеральные отображения в узле — по ГРАММАТИКЕ литерального контейнера.

    Грамматика (план 16-12, ревью WR-08):
    - `{…}` и вызов `dict(...)` — само отображение, а с ним отображения, вложенные
      в него: `{**{…}, …}`, `dict({…})`, `dict(**{…})`;
    - `rows := …` — по присваиваемому значению;
    - `[…]`, `(…)`, `{…, …}` (список, кортеж, набор) — рекурсивно по элементам;
    - `[… for …]`, `(… for …)`, `{… for …}` — рекурсивно по элементу comprehension:
      ключ `"phone"` в его словаре стоит литералом в исходнике, хотя строк много;
    - `a | b`, `a + b` (слияние словарей, склейка списков) — по обеим сторонам;
    - `a if c else b` — по обеим ветвям;
    - `*rows` — по распаковываемому значению;
    - `list(…)`, `tuple(…)`, `set(…)`, `iter(…)` ровно с одним позиционным аргументом
      и без именованных (`LITERAL_CONTAINER_WRAPPERS`) — по этому аргументу.

    Граница грамматики: всё прочее — имя, атрибут, вызов другого имени, `{k: v for …}`
    с вычисленными ключами — пустой список. Это значения, пришедшие в пишущий вызов
    именем или результатом другого вызова: поток данных предикат не прослеживает.
    """
    if isinstance(node, ast.Dict):
        # `{**{"phone": x}, …}` — отображение внутри отображения.
        return [node] + [
            mapping
            for key, value in zip(node.keys, node.values)
            if key is None
            for mapping in _literal_mappings(value)
        ]
    if _is_dict_call(node):
        # `dict({"phone": x})`, `dict(**{"phone": x})` — отображение-аргумент.
        nested = list(node.args) + [k.value for k in node.keywords if k.arg is None]
        return [node] + [
            mapping for argument in nested for mapping in _literal_mappings(argument)
        ]
    if isinstance(node, ast.NamedExpr):
        return _literal_mappings(node.value)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return [mapping for item in node.elts for mapping in _literal_mappings(item)]
    if isinstance(node, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
        return _literal_mappings(node.elt)
    if isinstance(node, ast.BinOp):
        return _literal_mappings(node.left) + _literal_mappings(node.right)
    if isinstance(node, ast.IfExp):
        return _literal_mappings(node.body) + _literal_mappings(node.orelse)
    if isinstance(node, ast.Starred):
        return _literal_mappings(node.value)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in LITERAL_CONTAINER_WRAPPERS
        and len(node.args) == 1
        and not node.keywords
    ):
        return _literal_mappings(node.args[0])
    return []


def _is_dict_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "dict"
    )


def _mapping_phone_keys(mapping: ast.expr) -> list[tuple[ast.AST, str]]:
    """Ключи номера в литеральном отображении: (узел для строки находки, колонка).

    У `{...}` — строковая константа или атрибут (`MessengerAccount.phone`) из
    `PHONE_COLUMNS`; у `dict(...)` — именованный аргумент из `PHONE_COLUMNS`.
    """
    found: list[tuple[ast.AST, str]] = []
    if isinstance(mapping, ast.Dict):
        for key in mapping.keys:
            if key is not None and (column := _phone_column(key)) is not None:
                found.append((key, column))
    elif _is_dict_call(mapping):
        for keyword in mapping.keywords:
            if keyword.arg in PHONE_COLUMNS:
                found.append((keyword, keyword.arg))
        # `dict([("phone", x)])` — перечень пар.
        for argument in mapping.args:
            found.extend(_phone_pairs(argument))
    return found


def _phone_column(node: ast.AST) -> str | None:
    """Колонка номера, названная узлом литералом.

    Строка `"phone"`, атрибут `X.phone`, индекс `table.c["phone"]` и
    `getattr(X, "phone")` с именем-константой.
    """
    if isinstance(node, ast.Constant) and node.value in PHONE_COLUMNS:
        return node.value
    if isinstance(node, ast.Attribute) and node.attr in PHONE_COLUMNS:
        return node.attr
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.slice, ast.Constant)
        and node.slice.value in PHONE_COLUMNS
    ):
        return node.slice.value
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value in PHONE_COLUMNS
    ):
        return node.args[1].value
    return None


def _pair_candidates(node: ast.AST) -> list[ast.AST]:
    """Элементы литерального перечня пар — по той же грамматике контейнера.

    Список, кортеж, набор (с `*`-распаковкой внутри), comprehension и генератор (их
    элемент), `+` / `|`, условное выражение, `:=` и обёртки `list(…)` и подобные.
    """
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        found: list[ast.AST] = []
        for item in node.elts:
            if isinstance(item, ast.Starred):
                found.extend(_pair_candidates(item.value))
            else:
                found.append(item)
        return found
    if isinstance(node, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
        return [node.elt]
    if isinstance(node, ast.BinOp):
        return _pair_candidates(node.left) + _pair_candidates(node.right)
    if isinstance(node, ast.IfExp):
        return _pair_candidates(node.body) + _pair_candidates(node.orelse)
    if isinstance(node, ast.NamedExpr):
        return _pair_candidates(node.value)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in LITERAL_CONTAINER_WRAPPERS
        and len(node.args) == 1
        and not node.keywords
    ):
        return _pair_candidates(node.args[0])
    return []


def _phone_pairs_among(candidates: list[ast.AST]) -> list[tuple[ast.AST, str]]:
    """Пары `(колонка номера, значение)` среди кандидатов: первый элемент — колонка."""
    found: list[tuple[ast.AST, str]] = []
    for pair in candidates:
        if isinstance(pair, (ast.Tuple, ast.List)) and pair.elts:
            column = _phone_column(pair.elts[0])
            if column is not None:
                found.append((pair.elts[0], column))
    return found


def _phone_pairs(node: ast.AST) -> list[tuple[ast.AST, str]]:
    """Пары `(колонка номера, значение)` в литеральном перечне пар `[(…, …), …]`."""
    return _phone_pairs_among(_pair_candidates(node))


def _positional_phone_columns(call: ast.Call) -> list[tuple[ast.AST, str]]:
    """Колонки номера, названные ПОЗИЦИЕЙ: (узел для строки находки, колонка).

    У `ordered_values` — каждый позиционный аргумент-пара, чей первый элемент —
    колонка номера; у `from_select` — элементы первого позиционного аргумента
    (или `names=`), являющиеся колонкой номера.
    """
    name = _call_name(call)
    if name == "ordered_values":
        # Каждый позиционный аргумент — пара; `*pairs` — перечень пар.
        candidates: list[ast.AST] = []
        for argument in call.args:
            if isinstance(argument, ast.Starred):
                candidates.extend(_pair_candidates(argument.value))
            else:
                candidates.append(argument)
        return _phone_pairs_among(candidates)
    if name == "from_select":
        names = call.args[0] if call.args else next(
            (k.value for k in call.keywords if k.arg == "names"), None
        )
        if isinstance(names, (ast.List, ast.Tuple)):
            return [
                (item, column)
                for item in names.elts
                if (column := _phone_column(item)) is not None
            ]
    return []


def _module_model_aliases(tree: ast.AST) -> frozenset[str]:
    """Псевдонимы модели аккаунта в ТОМ ЖЕ модуле.

    `from … import MessengerAccount as X` и присваивание `X = MessengerAccount` (и
    цепочкой `Y = X`). Область видимости плоская — весь модуль, без учёта функций и
    классов; псевдоним, заведённый в другом модуле, — поток данных между модулями,
    и это названная граница предиката.
    """
    known = {MODEL_NAME}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == MODEL_NAME and alias.asname:
                    known.add(alias.asname)
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets, value = node.targets, node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets, value = [node.target], node.value
            else:
                continue
            if isinstance(value, ast.Name) and value.id in known:
                for target in targets:
                    if isinstance(target, ast.Name) and target.id not in known:
                        known.add(target.id)
                        changed = True
    return frozenset(known - {MODEL_NAME})


def _mapping_key_text(key: ast.AST, column: str) -> str:
    """Ключ номера в предмете находки: `{'phone': …}`, `{X.phone: …}`, `dict(phone=…)`."""
    if isinstance(key, ast.keyword):
        return f"dict({column}=…)"
    if isinstance(key, (ast.Attribute, ast.Subscript, ast.Call)):
        return f"{{{ast.unparse(key)}: …}}"
    return f"{{{column!r}: …}}"


def _assigned_attributes(target: ast.AST) -> list[ast.Attribute]:
    """Атрибуты номера среди целей присваивания, включая распаковку кортежа.

    Цель-имя (`phone: Mapped[...] = mapped_column(...)` в теле класса модели) не
    судится: это объявление колонки, а не запись в неё.
    """
    if isinstance(target, ast.Attribute):
        return [target] if target.attr in PHONE_COLUMNS else []
    if isinstance(target, (ast.Tuple, ast.List)):
        return [item for element in target.elts for item in _assigned_attributes(element)]
    if isinstance(target, ast.Starred):
        return _assigned_attributes(target.value)
    return []


def _call_name(call: ast.Call) -> str | None:
    """Имя вызова, названное литералом.

    Последнее звено вызываемого: `update(...)` → `update`, `stmt.values(...)` →
    `values`; строка вызываемого `getattr(<что угодно>, "<строка>")(…)` →
    `<строка>` (ревью WR-10: `getattr(session, "bulk_update_mappings")(…)`).
    """
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return _getattr_literal(call.func)


def tree_offences(root: Path) -> tuple[list[Path], list[str]]:
    """Обход дерева и судимые находки по каждому файлу, писатель включительно."""
    sources = writer_sources(root)
    offences: list[str] = []
    for file in sources:
        relative = file.relative_to(root).as_posix()
        offences.extend(judged_offences(file.read_text(encoding="utf-8"), relative))
    return sources, offences


def _plant(root: Path, relative: str, source: str) -> Path:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return target


def test_a_planted_phone_write_outside_the_writer_reddens_the_gate(tmp_path):
    """ТРАСЕР: присваивание номера в файле, о котором гейт не знал, краснит его.

    Без этого контроля живое правило зелено и при пустом обходе, и при предикате,
    не находящем ничего, — то есть проверяло бы ничто.
    """
    _plant(
        tmp_path,
        "app/pages/planted.py",
        "def save(account, x):\n"
        "    account.phone = '+79991234567'\n",
    )

    sources, offences = tree_offences(tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in sources] == [
        "app/pages/planted.py"
    ], "обход синтетического дерева не нашёл подложенный файл"
    assert offences, (
        "подложенная запись номера не найдена: присваивание `account.phone` в "
        "app/pages/planted.py гейт пропустил"
    )
    assert any(
        offence.startswith(f"app/pages/planted.py:2 — {KIND_ASSIGNMENT}")
        for offence in offences
    ), f"находка не называет файл, строку и вид: {offences}"


def test_a_planted_bulk_update_by_primary_key_reddens_the_gate(tmp_path):
    """ТРАСЕР WR-01: executemany по первичному ключу в синтетическом `scripts/`.

    ORM bulk UPDATE списком словарей — естественная форма скрипта дозаполнения
    Фазы 20, то есть ровно тот второй писатель, ради которого гейт существует (D-13).
    Подложенный файл находится тем же обходом, что и живое дерево.
    """
    _plant(
        tmp_path,
        "scripts/backfill_planted.py",
        "async def backfill(session, p):\n"
        '    await session.execute(update(MessengerAccount), [{"id": 1, "phone": p}])\n',
    )

    sources, offences = tree_offences(tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in sources] == [
        "scripts/backfill_planted.py"
    ], "обход синтетического дерева не нашёл подложенный файл в `scripts/`"
    found = [
        offence
        for offence in offences
        if offence.startswith(f"scripts/backfill_planted.py:2 — {KIND_ROW_MAPPING} — ")
    ]
    assert found, (
        "executemany по первичному ключу не найден: "
        "`session.execute(update(MessengerAccount), [{'phone': p}])` в "
        f"scripts/backfill_planted.py гейт пропустил: {offences}"
    )
    assert all("execute" in offence and "phone" in offence for offence in found), (
        f"предмет находки не называет вызов `execute` и колонку `phone`: {found}"
    )


def test_a_planted_backfill_with_parameters_and_a_comprehension_reddens_the_gate(
    tmp_path,
):
    """ТРАСЕР WR-08: строки executemany в comprehension под `parameters=`.

    У `Connection.execute` / `AsyncConnection.execute` аргумент строк называется
    `parameters`, а список словарей, собранный comprehension из пар «аккаунт —
    номер», — естественная форма скрипта дозаполнения Фазы 20 (D-13). Ключ
    `"phone"` стоит литералом прямо в аргументе пишущего вызова. Подложенный файл
    находится тем же обходом `writer_sources(root)`, что и живое дерево.
    """
    _plant(
        tmp_path,
        "scripts/backfill_planted_rows.py",
        "async def backfill(conn, rows):\n"
        "    await conn.execute(update(MessengerAccount), "
        'parameters=[{"id": a.id, "phone": n} for a, n in rows])\n',
    )

    sources, offences = tree_offences(tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in sources] == [
        "scripts/backfill_planted_rows.py"
    ], "обход синтетического дерева не нашёл подложенный файл в `scripts/`"
    found = [
        offence
        for offence in offences
        if offence.startswith(
            f"scripts/backfill_planted_rows.py:2 — {KIND_ROW_MAPPING} — "
        )
    ]
    assert found, (
        "строки executemany в comprehension под parameters= не найдены: "
        "`conn.execute(update(MessengerAccount), parameters=[{'phone': n} for …])` "
        f"в scripts/backfill_planted_rows.py гейт пропустил: {offences}"
    )
    assert all("execute" in offence and "phone" in offence for offence in found), (
        f"предмет находки не называет вызов `execute` и колонку `phone`: {found}"
    )


def test_a_planted_backfill_through_run_sync_reddens_the_gate(tmp_path):
    """ТРАСЕР WR-10: строки `bulk_update_mappings`, поданные через `run_sync`.

    У `AsyncSession` нет `bulk_*` вовсе (замер `inspect.signature`, SQLAlchemy
    2.0.46): синхронный bulk-API асинхронный код достаёт только через
    `run_sync(Session.bulk_update_mappings, …)`. Проект асинхронный целиком,
    поэтому скрипт дозаполнения Фазы 20 вероятнее всего пойдёт именно так — и
    обойдёт условную запись, если гейт опознаёт пишущий API лишь по имени самого
    вызова (D-13). Подложенный файл находится тем же обходом, что и живое дерево.
    """
    _plant(
        tmp_path,
        "scripts/backfill_run_sync.py",
        "async def backfill(session, rows):\n"
        "    await session.run_sync(Session.bulk_update_mappings, MessengerAccount, "
        '[{"id": a.id, "phone": n} for a, n in rows])\n',
    )

    sources, offences = tree_offences(tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in sources] == [
        "scripts/backfill_run_sync.py"
    ], "обход синтетического дерева не нашёл подложенный файл в `scripts/`"
    found = [
        offence
        for offence in offences
        if offence.startswith(f"scripts/backfill_run_sync.py:2 — {KIND_ROW_MAPPING} — ")
    ]
    assert found, (
        "строки bulk_update_mappings, поданные через run_sync, не найдены: "
        "`session.run_sync(Session.bulk_update_mappings, MessengerAccount, "
        "[{'phone': n} for …])` в scripts/backfill_run_sync.py гейт пропустил: "
        f"{offences}"
    )
    assert all(
        "bulk_update_mappings" in offence and "phone" in offence for offence in found
    ), f"предмет находки не называет `bulk_update_mappings` и колонку `phone`: {found}"


ASSIGNMENT_CASES = [
    pytest.param("account.phone = x\n", "account.phone", id="assign-phone"),
    pytest.param(
        "account.phone_is_manual = True\n",
        "account.phone_is_manual",
        id="assign-phone-is-manual",
    ),
    pytest.param("obj.phone += x\n", "obj.phone", id="augassign-phone"),
    pytest.param("acc.phone: str = x\n", "acc.phone", id="annassign-phone"),
]


@pytest.mark.parametrize(("source", "subject"), ASSIGNMENT_CASES)
def test_an_assignment_to_a_phone_attribute_is_a_write(source, subject):
    offences = phone_write_offences(source, "app/x.py")

    assert offences == [f"app/x.py:1 — {KIND_ASSIGNMENT} — {subject}"], (
        f"присваивание `{subject}` гейт не нашёл: {offences}"
    )


KEYWORD_CASES = [
    pytest.param(
        "stmt = update(MessengerAccount).where(MessengerAccount.id == 1).values(phone=x)\n",
        ["values(phone=…)"],
        id="update-values-phone",
    ),
    pytest.param(
        "stmt = insert(MessengerAccount).values(phone_is_manual=True)\n",
        ["values(phone_is_manual=…)"],
        id="insert-values-phone-is-manual",
    ),
    pytest.param(
        "account = MessengerAccount(user_id=1, phone=x)\n",
        ["MessengerAccount(phone=…)"],
        id="model-constructor-phone",
    ),
    pytest.param(
        "stmt = stmt.values(phone=None, phone_is_manual=False)\n",
        ["values(phone=…)", "values(phone_is_manual=…)"],
        id="values-both-columns",
    ),
]


@pytest.mark.parametrize(("source", "subjects"), KEYWORD_CASES)
def test_a_phone_keyword_in_a_write_call_is_a_write(source, subjects):
    offences = phone_write_offences(source, "app/x.py")

    assert offences == [
        f"app/x.py:1 — {KIND_KEYWORD} — {subject}" for subject in subjects
    ], f"именованный аргумент номера в пишущем вызове гейт не нашёл: {offences}"


def test_no_phone_write_outside_the_writer_in_the_live_tree():
    """Живое дерево: ни одной записи номера вне модуля-писателя.

    Антивакуум в том же правиле: обход видит больше пятидесяти файлов, видит сам
    модуль-писатель, и предикат без исключения находит в нём настоящую запись —
    иначе ноль находок ничего бы не значил.
    """
    sources, offences = tree_offences(PROJECT_ROOT)
    walked = {path.relative_to(PROJECT_ROOT).as_posix() for path in sources}
    writer_source = (PROJECT_ROOT / PHONE_WRITER_MODULE).read_text(encoding="utf-8")
    writer_writes = [
        offence
        for offence in phone_write_offences(writer_source, PHONE_WRITER_MODULE)
        if f" — {KIND_KEYWORD} — " in offence
    ]

    assert len(sources) > 50, (
        f"обход `app/` и `scripts/` дал {len(sources)} файлов — гейт проверяет "
        "почти ничто, и его зелень ничего не значит"
    )
    assert PHONE_WRITER_MODULE in walked, (
        f"обход ({len(sources)} файлов) не видит модуль-писатель {PHONE_WRITER_MODULE}"
    )
    assert len(writer_writes) >= 1, (
        f"предикат без исключения нашёл в модуле-писателе {len(writer_writes)} "
        f"записей второго вида при {len(sources)} обойдённых файлах — он слеп к "
        "настоящей условной записи, и ноль находок на дереве ничего не значит"
    )
    assert offences == [], (
        f"запись номера вне {PHONE_WRITER_MODULE} (обойдено {len(sources)} файлов, "
        f"в модуле-писателе без исключения {len(writer_writes)} записей) — второй "
        "писатель обходит условную запись, и ручной номер снова затирается (D-13):\n"
        + "\n".join(f"  {offence}" for offence in offences)
    )


def test_a_raw_sql_phone_write_reddens_the_gate(tmp_path):
    """Сырой UPDATE в строковой константе синтетического `app/` краснит гейт."""
    _plant(
        tmp_path,
        "app/x.py",
        'SQL = "UPDATE messenger_accounts SET phone = :p WHERE id = :id"\n',
    )

    sources, offences = tree_offences(tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in sources] == [
        "app/x.py"
    ], "обход синтетического дерева не нашёл подложенный файл"
    assert any(
        offence.startswith(f"app/x.py:1 — {KIND_RAW_SQL} — ") for offence in offences
    ), f"сырой SQL с номером не найден: {offences}"


def test_a_raw_sql_write_with_quoted_identifiers_reddens_the_gate(tmp_path):
    """Вставка в таблицу аккаунтов с кавычками и префиксом схемы краснит гейт (WR-08).

    До плана 16-12 шаблон требовал голое `phone =` и голую `messenger_accounts`, и
    кавычки у идентификатора или префикс схемы проводили запись мимо гейта.
    """
    _plant(
        tmp_path,
        "app/planted_sql.py",
        "SQL = 'INSERT INTO \"public\".\"messenger_accounts\" "
        "(user_id, \"phone\") VALUES (1, :p)'\n",
    )

    sources, offences = tree_offences(tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in sources] == [
        "app/planted_sql.py"
    ], "обход синтетического дерева не нашёл подложенный файл"
    assert any(
        offence.startswith(f"app/planted_sql.py:1 — {KIND_RAW_SQL} — ")
        for offence in offences
    ), f"сырой SQL с кавычками и схемой не найден: {offences}"


DICT_KEY_CASES = [
    pytest.param(
        'stmt = update(MessengerAccount).values({"phone": x})\n',
        "values({'phone': …})",
        id="values-dict-string-key",
    ),
    pytest.param(
        "stmt = update(MessengerAccount).values({MessengerAccount.phone: x})\n",
        "values({MessengerAccount.phone: …})",
        id="values-dict-column-key",
    ),
    pytest.param(
        'stmt = stmt.values({"phone_is_manual": True})\n',
        "values({'phone_is_manual': …})",
        id="values-dict-phone-is-manual",
    ),
]


@pytest.mark.parametrize(("source", "subject"), DICT_KEY_CASES)
def test_a_phone_key_in_a_values_dict_is_a_write(source, subject):
    offences = phone_write_offences(source, "app/x.py")

    assert offences == [f"app/x.py:1 — {KIND_DICT_KEY} — {subject}"], (
        f"ключ номера в словаре `values(...)` гейт не нашёл: {offences}"
    )


SETATTR_CASES = [
    pytest.param(
        'setattr(account, "phone", x)\n',
        "setattr(…, 'phone', …)",
        id="setattr-phone",
    ),
    pytest.param(
        'set_committed_value(account, "phone_is_manual", True)\n',
        "set_committed_value(…, 'phone_is_manual', …)",
        id="set-committed-value-phone-is-manual",
    ),
]


@pytest.mark.parametrize(("source", "subject"), SETATTR_CASES)
def test_a_phone_attribute_written_by_name_is_a_write(source, subject):
    offences = phone_write_offences(source, "app/x.py")

    assert offences == [f"app/x.py:1 — {KIND_SETATTR} — {subject}"], (
        f"запись атрибута номера по имени гейт не нашёл: {offences}"
    )


RAW_SQL_CASES = [
    pytest.param(
        'stmt = text("update messenger_accounts set phone_is_manual = true")\n',
        id="text-update-lowercase",
    ),
    pytest.param(
        "SQL = \"INSERT INTO messenger_accounts (user_id, phone) "
        "VALUES (1, '+79991234567')\"\n",
        id="insert-into-messenger-accounts",
    ),
]


@pytest.mark.parametrize("source", RAW_SQL_CASES)
def test_a_raw_sql_phone_write_in_a_string_constant_is_a_write(source):
    offences = phone_write_offences(source, "app/x.py")

    assert len(offences) == 1 and offences[0].startswith(
        f"app/x.py:1 — {KIND_RAW_SQL} — "
    ), f"сырой SQL с номером в строковой константе гейт не нашёл: {offences}"


def test_an_upsert_set_of_a_phone_column_is_a_write():
    """`set_` у `on_conflict_do_update` пишет колонку при конфликте — это запись (WR-01)."""
    source = (
        "stmt = insert(MessengerAccount).values(user_id=1).on_conflict_do_update("
        'index_elements=["id"], set_={"phone": x})\n'
    )

    offences = phone_write_offences(source, "app/x.py")
    upserts = [offence for offence in offences if f" — {KIND_UPSERT_SET} — " in offence]

    assert upserts, f"set_ при конфликте с номером не найден: {offences}"
    assert len(offences) == 1 and offences[0].startswith(
        f"app/x.py:1 — {KIND_UPSERT_SET} — "
    ), f"upsert дал не ровно одну находку вида «{KIND_UPSERT_SET}»: {offences}"
    assert "on_conflict_do_update" in offences[0] and "phone" in offences[0], (
        f"предмет находки не называет `on_conflict_do_update` и `phone`: {offences}"
    )


def test_an_ordered_values_pair_of_a_phone_column_is_a_write():
    """Пара `(колонка, значение)` в `ordered_values` пишет колонку — это запись (WR-08).

    Колонка названа позицией в кортеже, а не именованным аргументом или ключом
    словаря, поэтому до плана 16-12 ни один вид её не видел.
    """
    source = "stmt = update(MessengerAccount).ordered_values((MessengerAccount.phone, x))\n"

    offences = phone_write_offences(source, "app/x.py")
    positional = [
        offence for offence in offences if f" — {KIND_POSITIONAL_COLUMN} — " in offence
    ]

    assert positional, f"пара ordered_values с колонкой номера не найдена: {offences}"
    assert len(offences) == 1, (
        f"`ordered_values` дал не ровно одну находку вида «{KIND_POSITIONAL_COLUMN}»: "
        f"{offences}"
    )
    assert "ordered_values" in offences[0] and "phone" in offences[0], (
        f"предмет находки не называет `ordered_values` и `phone`: {offences}"
    )


def test_a_query_update_with_values_as_a_keyword_is_a_write():
    """`Query.update(values={"phone": x})` пишет колонку — именем, а не позицией (WR-10).

    Сигнатура `Query.update(self, values, synchronize_session, update_args)`
    (SQLAlchemy 2.0.46): `values` — обычный позиционно-именованный параметр, и
    именованная форма пишет так же, как позиционная (замер верификатора на SQLite в
    памяти). До плана 16-17 судилась только позиционная.
    """
    source = 'session.query(MessengerAccount).filter_by(id=i).update(values={"phone": x})\n'

    offences = phone_write_offences(source, "app/x.py")

    assert offences, f"Query.update(values=…) с ключом номера не найден: {offences}"
    assert len(offences) == 1 and offences[0].startswith(f"app/x.py:1 — {KIND_DICT_KEY} — "), (
        f"Query.update(values=…) дал не ровно одну находку вида «{KIND_DICT_KEY}»: {offences}"
    )
    assert "update" in offences[0] and "phone" in offences[0], (
        f"предмет находки не называет `update` и колонку `phone`: {offences}"
    )


def _resolve_api(path: str) -> object:
    """Объект по пути: самый длинный ввозимый модуль, затем `getattr` по звеньям."""
    parts = path.split(".")
    for cut in range(len(parts), 0, -1):
        try:
            found: object = importlib.import_module(".".join(parts[:cut]))
        except ImportError:
            continue
        for part in parts[cut:]:
            found = getattr(found, part)
        return found
    raise ImportError(f"ни один префикс пути {path} не ввозится")


def test_the_judged_parameters_name_the_installed_signatures():
    """Таблица `JUDGED_PARAMETERS` совпадает с установленными сигнатурами.

    Для каждой строки параметр с именем `parameter` стоит на индексе
    `signature_index` в `inspect.signature(api)`, и позиционно-только он ровно у
    `setattr` и `object.__setattr__`. Подъём SQLAlchemy / Alembic / asyncpg,
    переименовавший или переставивший параметр, краснит это правило, а не оставляет
    предикат молча слепым к новой форме.
    """
    mismatches: list[str] = []
    for row in JUDGED_PARAMETERS:
        try:
            api = _resolve_api(row.api)
            parameters = list(inspect.signature(api).parameters.values())
        except (ImportError, AttributeError, TypeError, ValueError) as error:
            mismatches.append(f"{row.api}: сигнатура не снимается ({error!r})")
            continue
        if row.signature_index >= len(parameters):
            mismatches.append(
                f"{row.api}: индекса {row.signature_index} нет, параметры "
                f"{[p.name for p in parameters]}"
            )
            continue
        parameter = parameters[row.signature_index]
        if parameter.name != row.parameter:
            mismatches.append(
                f"{row.api}: на индексе {row.signature_index} стоит «{parameter.name}», "
                f"а не «{row.parameter}»"
            )
        positional_only = parameter.kind is inspect.Parameter.POSITIONAL_ONLY
        expected_only = row.api in POSITIONAL_ONLY_APIS
        if positional_only != expected_only:
            expected = "POSITIONAL_ONLY" if expected_only else "не POSITIONAL_ONLY"
            mismatches.append(
                f"{row.api}: «{parameter.name}» — {parameter.kind.name}, таблица "
                f"ждёт {expected}"
            )

    assert len(JUDGED_PARAMETERS) >= 33, (
        f"в таблице {len(JUDGED_PARAMETERS)} строк вместо 33 — перебор сигнатур неполон"
    )
    assert not mismatches, (
        "таблица судимых параметров разошлась с установленными сигнатурами — "
        "предикат судит не те позиции или имена:\n"
        + "\n".join(f"  {mismatch}" for mismatch in mismatches)
    )


# Образец значения судимого параметра — по виду строки таблицы.
BINDING_SAMPLES = {
    KIND_DICT_KEY: '{"phone": x}',
    KIND_SETATTR: '"phone"',
    KIND_POSITIONAL_COLUMN: '["user_id", "phone"]',
    KIND_UPSERT_SET: '{"phone": x}',
    KIND_ROW_MAPPING: '[{"id": 1, "phone": p}]',
    KIND_RAW_SQL: '"messenger_accounts"',
}

# Обязательные хвосты вызова: у COPY asyncpg `records` / `source` — только именем.
BINDING_TAILS = {
    "copy_records_to_table": ["records=rows"],
    "copy_to_table": ["source=src"],
}

# Как вызов пишется в исходнике: функции модуля — без получателя, прочее — методом.
BINDING_RECEIVERS = {
    "setattr": "",
    "set_attribute": "",
    "set_committed_value": "",
    "__setattr__": "object.",
}

BINDING_FORMS = ("positional", "keyword", "double-star", "starred")


def _binding_source(row: JudgedParameter, form: str) -> str:
    """Вызов API строки с судимым параметром, связанным формой `form`."""
    value = BINDING_SAMPLES[row.kind]
    fillers = [f"a{index}" for index in range(row.call_index)]
    if form == "positional":
        arguments = [*fillers, value]
    elif form == "keyword":
        arguments = [*fillers, f"{row.parameter}={value}"]
    elif form == "double-star":
        arguments = [*fillers, f'**{{"{row.parameter}": {value}}}']
    else:
        arguments = ["*[" + ", ".join([*fillers, value]) + "]"]
    receiver = BINDING_RECEIVERS.get(row.call, "obj.")
    arguments += BINDING_TAILS.get(row.call, [])
    return f"{receiver}{row.call}({', '.join(arguments)})\n"


BINDING_CASES = [
    pytest.param(row, form, id=f"{row.api}-{form}")
    for row in JUDGED_PARAMETERS
    if row.parameter not in REFERENCE_KEYWORDS
    for form in BINDING_FORMS
]


@pytest.mark.parametrize(("row", "form"), BINDING_CASES)
def test_every_literal_binding_of_a_judged_parameter_is_judged(row, form):
    """Каждая литеральная форма связывания судимого параметра — ровно одна находка.

    Строка таблицы × форма: позицией (`call_index` после заполнителей), именем
    (`parameter=…`), `**{"parameter": …}` и `*[заполнители…, значение]`. Две строки
    ссылки `run_sync` здесь не участвуют: их предмет называет API по ссылке, а не
    `run_sync`, и все четыре формы связывания `fn` закреплены поимённо строками
    `LITERAL_FORM_CASES`. Формы позиционно-только параметров (`setattr(…, name=…)`)
    при исполнении падают `TypeError` и ничего не пишут — гейт судит их по цене
    строгости, поэтому правило называется «is_judged», а не «is_a_write».
    """
    source = _binding_source(row, form)

    offences = phone_write_offences(source, "app/x.py")

    assert len(offences) == 1, (
        f"`{source.strip()}` — {form}-связывание `{row.parameter}` у {row.api} — дало "
        f"{len(offences)} находок вместо одной: {offences}"
    )
    _location, found_kind, subject = offences[0].split(" — ", 2)
    assert found_kind == row.kind, (
        f"`{source.strip()}`: вид «{found_kind}», ожидался «{row.kind}»: {offences}"
    )
    assert row.call in subject, (
        f"`{source.strip()}`: предмет находки не называет `{row.call}`: {offences}"
    )


# Литеральные формы записи из ревью WR-01: (исходник, вид, имя вызова, колонка).
# Каждая видна в исходнике, а до плана 16-09 проходила гейт молча.
LITERAL_FORM_CASES = [
    pytest.param(
        "async def f(session, p):\n"
        '    await session.execute(update(MessengerAccount), [{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "execute",
        "phone",
        id="orm-bulk-update-by-pk",
    ),
    pytest.param(
        "stmt = update(MessengerAccount).values(dict(phone=x))\n",
        KIND_DICT_KEY,
        "values",
        "phone",
        id="values-dict-call",
    ),
    pytest.param(
        'stmt = update(MessengerAccount).values(**{"phone": x})\n',
        KIND_KEYWORD,
        "values",
        "phone",
        id="values-double-star-dict",
    ),
    pytest.param(
        "stmt = insert(MessengerAccount).values(user_id=1).on_conflict_do_update("
        'index_elements=["id"], set_={"phone": x})\n',
        KIND_UPSERT_SET,
        "on_conflict_do_update",
        "phone",
        id="upsert-set-dict",
    ),
    pytest.param(
        "stmt = insert(MessengerAccount).values(user_id=1).on_conflict_do_update("
        'index_elements=["id"], set_=dict(phone_is_manual=True))\n',
        KIND_UPSERT_SET,
        "on_conflict_do_update",
        "phone_is_manual",
        id="upsert-set-dict-call",
    ),
    pytest.param(
        'session.bulk_update_mappings(MessengerAccount, [{"id": 1, "phone_is_manual": True}])\n',
        KIND_ROW_MAPPING,
        "bulk_update_mappings",
        "phone_is_manual",
        id="bulk-update-mappings",
    ),
    pytest.param(
        "session.bulk_insert_mappings(MessengerAccount, [dict(user_id=1, phone=p)])\n",
        KIND_ROW_MAPPING,
        "bulk_insert_mappings",
        "phone",
        id="bulk-insert-mappings",
    ),
    pytest.param(
        'account = MessengerAccount(**{"phone": x})\n',
        KIND_KEYWORD,
        "MessengerAccount",
        "phone",
        id="model-constructor-double-star",
    ),
    pytest.param(
        "async def f(session, stmt, p):\n"
        '    await session.execute(stmt, params=[{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "execute",
        "phone",
        id="execute-params-keyword",
    ),
    # Ревью WR-08 (2026-10-09) и перебор планирования 16-12: строки executemany и
    # отображения `values` в литеральном контейнере — comprehension, генератор,
    # обёртка `list(…)`, условное выражение, слияние `|`, аргумент `parameters=`.
    pytest.param(
        "async def f(conn, p):\n"
        "    await conn.execute(update(MessengerAccount), "
        'parameters=[{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "execute",
        "phone",
        id="conn-execute-parameters",
    ),
    pytest.param(
        "async def f(s, rows):\n"
        "    await s.execute(update(MessengerAccount), "
        '[{"id": a.id, "phone": n} for a, n in rows])\n',
        KIND_ROW_MAPPING,
        "execute",
        "phone",
        id="execute-list-comprehension",
    ),
    pytest.param(
        "async def f(s, rows):\n"
        "    await s.execute(update(MessengerAccount), "
        '({"id": a.id, "phone": n} for a, n in rows))\n',
        KIND_ROW_MAPPING,
        "execute",
        "phone",
        id="execute-generator-expression",
    ),
    pytest.param(
        # Синтаксически литеральна; во время исполнения набор словарей упал бы
        # (словарь не хешируется), но гэп 3 называет `SetComp` прямо.
        "async def f(s, rows):\n"
        "    await s.execute(update(MessengerAccount), "
        "{dict(id=a, phone=n) for a, n in rows})\n",
        KIND_ROW_MAPPING,
        "execute",
        "phone",
        id="execute-set-comprehension-of-dict-calls",
    ),
    pytest.param(
        "async def f(s, rows):\n"
        "    await s.execute(update(MessengerAccount), "
        "[dict(id=a, phone=n) for a, n in rows])\n",
        KIND_ROW_MAPPING,
        "execute",
        "phone",
        id="execute-comprehension-of-dict-calls",
    ),
    pytest.param(
        "async def f(s, rows):\n"
        "    await s.execute(update(MessengerAccount), "
        'list({"id": a, "phone": n} for a, n in rows))\n',
        KIND_ROW_MAPPING,
        "execute",
        "phone",
        id="execute-list-wrapped-generator",
    ),
    pytest.param(
        "async def f(s, p, c):\n"
        "    await s.execute(update(MessengerAccount), "
        '[{"id": 1, "phone": p}] if c else [])\n',
        KIND_ROW_MAPPING,
        "execute",
        "phone",
        id="execute-conditional-rows",
    ),
    pytest.param(
        'op.bulk_insert(accounts_table, [{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "bulk_insert",
        "phone",
        id="alembic-bulk-insert",
    ),
    pytest.param(
        "stmt = insert(MessengerAccount).values("
        '[{"user_id": u, "phone": n} for u, n in rows])\n',
        KIND_DICT_KEY,
        "values",
        "phone",
        id="insert-values-list-comprehension",
    ),
    pytest.param(
        'stmt = update(MessengerAccount).values({"phone": x} | base)\n',
        KIND_DICT_KEY,
        "values",
        "phone",
        id="values-merged-dict",
    ),
    pytest.param(
        'stmt = update(MessengerAccount).values(**({"phone": x} | base))\n',
        KIND_KEYWORD,
        "values",
        "phone",
        id="values-double-star-merged-dict",
    ),
    # Сырой SQL (WR-08 и перебор планирования 16-12): поле «вызов» — ключевое слово
    # SQL, поле «колонка» — таблица; оба стоят в первых 60 символах предмета.
    pytest.param(
        "SQL = 'UPDATE messenger_accounts SET \"phone\" = :p WHERE id = :id'\n",
        KIND_RAW_SQL,
        "UPDATE",
        "messenger_accounts",
        id="raw-sql-quoted-column",
    ),
    pytest.param(
        "SQL = 'INSERT INTO \"messenger_accounts\" (user_id, phone) VALUES (1, :p)'\n",
        KIND_RAW_SQL,
        "INSERT",
        "messenger_accounts",
        id="raw-sql-quoted-table",
    ),
    pytest.param(
        'SQL = "INSERT INTO public.messenger_accounts (user_id, phone) VALUES (1, :p)"\n',
        KIND_RAW_SQL,
        "INSERT",
        "messenger_accounts",
        id="raw-sql-schema-qualified",
    ),
    pytest.param(
        "SQL = 'UPDATE \"public\".\"messenger_accounts\" SET \"phone_is_manual\" = true'\n",
        KIND_RAW_SQL,
        "UPDATE",
        "messenger_accounts",
        id="raw-sql-quoted-schema-update",
    ),
    pytest.param(
        'SQL = "INSERT OR REPLACE INTO messenger_accounts (id, phone) VALUES (:i, :p)"\n',
        KIND_RAW_SQL,
        "REPLACE",
        "messenger_accounts",
        id="raw-sql-insert-or-replace",
    ),
    pytest.param(
        'SQL = "REPLACE INTO messenger_accounts (id, phone) VALUES (:i, :p)"\n',
        KIND_RAW_SQL,
        "REPLACE",
        "messenger_accounts",
        id="raw-sql-replace-into",
    ),
    pytest.param(
        'SQL = "MERGE INTO messenger_accounts AS t USING src AS s ON t.id = s.id '
        'WHEN MATCHED THEN UPDATE SET phone = s.phone"\n',
        KIND_RAW_SQL,
        "MERGE",
        "messenger_accounts",
        id="raw-sql-merge-into",
    ),
    pytest.param(
        # Ветка вставки слияния: колонка номера стоит в перечне `INSERT (…)`, а не
        # в `SET`, поэтому её ловит только голова `MERGE INTO <таблица аккаунтов>`.
        'SQL = "MERGE INTO messenger_accounts AS t USING src AS s ON t.id = s.id '
        'WHEN NOT MATCHED THEN INSERT (id, phone) VALUES (s.id, s.phone)"\n',
        KIND_RAW_SQL,
        "MERGE",
        "messenger_accounts",
        id="raw-sql-merge-insert-branch",
    ),
    pytest.param(
        'SQL = "COPY messenger_accounts (id, phone) FROM STDIN"\n',
        KIND_RAW_SQL,
        "COPY",
        "messenger_accounts",
        id="raw-sql-copy-from",
    ),
    pytest.param(
        'SQL = "UPDATE messenger_accounts SET (phone, phone_is_manual) = (:p, true) '
        'WHERE id = :i"\n',
        KIND_RAW_SQL,
        "SET",
        "messenger_accounts",
        id="raw-sql-row-constructor-set",
    ),
    pytest.param(
        'SQL = "UPDATE messenger_accounts " + "SET phone = :p WHERE id = :i"\n',
        KIND_RAW_SQL,
        "UPDATE",
        "messenger_accounts",
        id="raw-sql-concatenated-literals",
    ),
    pytest.param(
        "async def f(conn, rows):\n"
        '    await conn.copy_records_to_table("messenger_accounts", '
        'records=rows, columns=["id", "phone"])\n',
        KIND_RAW_SQL,
        "copy_records_to_table",
        "messenger_accounts",
        id="asyncpg-copy-records",
    ),
    # Колонка позицией, запись по имени, устаревший `Query.update`, MySQL upsert,
    # псевдоним модели в том же модуле (WR-08 и перебор планирования 16-12).
    pytest.param(
        "stmt = update(MessengerAccount).ordered_values((MessengerAccount.phone, x))\n",
        KIND_POSITIONAL_COLUMN,
        "ordered_values",
        "phone",
        id="ordered-values",
    ),
    pytest.param(
        'stmt = update(MessengerAccount).ordered_values(("phone_is_manual", True))\n',
        KIND_POSITIONAL_COLUMN,
        "ordered_values",
        "phone_is_manual",
        id="ordered-values-string-key",
    ),
    pytest.param(
        'stmt = insert(MessengerAccount).from_select(["user_id", "phone"], sel)\n',
        KIND_POSITIONAL_COLUMN,
        "from_select",
        "phone",
        id="from-select-names",
    ),
    pytest.param(
        'object.__setattr__(account, "phone", x)\n',
        KIND_SETATTR,
        "__setattr__",
        "phone",
        id="object-setattr-dunder",
    ),
    pytest.param(
        'account.__setattr__("phone_is_manual", True)\n',
        KIND_SETATTR,
        "__setattr__",
        "phone_is_manual",
        id="bound-dunder-setattr",
    ),
    pytest.param(
        'set_attribute(account, "phone", x)\n',
        KIND_SETATTR,
        "set_attribute",
        "phone",
        id="set-attribute",
    ),
    pytest.param(
        'session.query(MessengerAccount).filter_by(id=1).update({"phone": x})\n',
        KIND_DICT_KEY,
        "update",
        "phone",
        id="legacy-query-update-dict",
    ),
    pytest.param(
        "session.query(MessengerAccount).filter(MessengerAccount.id == 1).update("
        "{MessengerAccount.phone: x}, synchronize_session=False)\n",
        KIND_DICT_KEY,
        "update",
        "phone",
        id="legacy-query-update-column-key",
    ),
    pytest.param(
        "stmt = insert(MessengerAccount).values(user_id=1).on_duplicate_key_update(phone=x)\n",
        KIND_UPSERT_SET,
        "on_duplicate_key_update",
        "phone",
        id="mysql-upsert-keyword",
    ),
    pytest.param(
        "stmt = insert(MessengerAccount).values(user_id=1).on_duplicate_key_update("
        '{"phone": x})\n',
        KIND_UPSERT_SET,
        "on_duplicate_key_update",
        "phone",
        id="mysql-upsert-dict",
    ),
    pytest.param(
        "stmt = insert(MessengerAccount).values(user_id=1).on_duplicate_key_update("
        '[("phone_is_manual", True)])\n',
        KIND_UPSERT_SET,
        "on_duplicate_key_update",
        "phone_is_manual",
        id="mysql-upsert-pairs",
    ),
    pytest.param(
        "from app.models.messenger_account import MessengerAccount as Account\n"
        "account = Account(user_id=1, phone=x)\n",
        KIND_KEYWORD,
        "Account",
        "phone",
        id="model-import-alias",
    ),
    pytest.param(
        "Model = MessengerAccount\naccount = Model(phone=x)\n",
        KIND_KEYWORD,
        "Model",
        "phone",
        id="model-assignment-alias",
    ),
    # Отображения внутри отображения (отклонение исполнения 16-12, Rule 2): ключ номера
    # стоит литералом в аргументе пишущего вызова, только вложен на уровень глубже.
    pytest.param(
        'stmt = update(MessengerAccount).values({**{"phone": x}, "id": 1})\n',
        KIND_DICT_KEY,
        "values",
        "phone",
        id="values-dict-display-spread",
    ),
    pytest.param(
        'stmt = update(MessengerAccount).values(dict(**{"phone": x}))\n',
        KIND_DICT_KEY,
        "values",
        "phone",
        id="values-dict-call-spread",
    ),
    pytest.param(
        'stmt = update(MessengerAccount).values(dict({"phone": x}, id=1))\n',
        KIND_DICT_KEY,
        "values",
        "phone",
        id="values-dict-call-positional-dict",
    ),
    pytest.param(
        'stmt = update(MessengerAccount).values(dict([("phone", x)]))\n',
        KIND_DICT_KEY,
        "values",
        "phone",
        id="values-dict-call-pairs",
    ),
    pytest.param(
        "async def f(s, p):\n"
        "    await s.execute(update(MessengerAccount), "
        'rows := [{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "execute",
        "phone",
        id="execute-walrus-rows",
    ),
    # Самопроверка исполнителя 16-12 после задачи 3 (отклонение, Rule 2): формы,
    # подпадающие под механизм шапки, которые предикат задачи 3 ещё не ловил.
    pytest.param(
        "stmt = update(MessengerAccount).ordered_values(*[(MessengerAccount.phone, x)])\n",
        KIND_POSITIONAL_COLUMN,
        "ordered_values",
        "phone",
        id="ordered-values-starred-pairs",
    ),
    pytest.param(
        "stmt = insert(MessengerAccount).on_duplicate_key_update("
        '[("phone", v) for v in xs])\n',
        KIND_UPSERT_SET,
        "on_duplicate_key_update",
        "phone",
        id="mysql-upsert-pairs-comprehension",
    ),
    pytest.param(
        'stmt = stmt.values(dict([("phone", v) for v in xs]))\n',
        KIND_DICT_KEY,
        "values",
        "phone",
        id="values-dict-call-pairs-comprehension",
    ),
    pytest.param(
        'stmt = update(accounts).values({accounts.c["phone"]: x})\n',
        KIND_DICT_KEY,
        "values",
        "phone",
        id="values-table-c-subscript-key",
    ),
    pytest.param(
        'stmt = update(accounts).ordered_values((accounts.c["phone"], x))\n',
        KIND_POSITIONAL_COLUMN,
        "ordered_values",
        "phone",
        id="ordered-values-table-c-subscript",
    ),
    pytest.param(
        'stmt = update(MessengerAccount).values({getattr(MessengerAccount, "phone"): x})\n',
        KIND_DICT_KEY,
        "values",
        "phone",
        id="values-getattr-column-key",
    ),
    pytest.param(
        "SQL = 'UPDATE messenger_accounts SET `phone` = :p WHERE id = :i'\n",
        KIND_RAW_SQL,
        "UPDATE",
        "messenger_accounts",
        id="raw-sql-backtick-column",
    ),
    pytest.param(
        "SQL = 'INSERT INTO `messenger_accounts` (id, phone) VALUES (:i, :p)'\n",
        KIND_RAW_SQL,
        "INSERT",
        "messenger_accounts",
        id="raw-sql-backtick-table",
    ),
    pytest.param(
        "SQL = 'INSERT INTO [messenger_accounts] (id, phone) VALUES (:i, :p)'\n",
        KIND_RAW_SQL,
        "INSERT",
        "messenger_accounts",
        id="raw-sql-bracket-table",
    ),
    pytest.param(
        "SQL = \"LOAD DATA INFILE 'x.csv' INTO TABLE messenger_accounts\"\n",
        KIND_RAW_SQL,
        "LOAD",
        "messenger_accounts",
        id="raw-sql-load-data",
    ),
    # Ревью WR-10 (2026-10-10) и план 16-17, задача 1: пишущий API, названный
    # литералом не последним звеном вызываемого, — ссылкой, поданной другому вызову
    # вместе с аргументами (`run_sync`, `partial(…)(…)`, `to_thread`,
    # `run_in_executor`), строкой в `getattr(obj, "…")(…)` и в `methodcaller("…", …)`.
    pytest.param(
        "async def f(session, p):\n"
        "    await session.run_sync(Session.bulk_update_mappings, MessengerAccount, "
        '[{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "bulk_update_mappings",
        "phone",
        id="run-sync-bulk-update-mappings",
    ),
    pytest.param(
        "async def f(session, p):\n"
        "    await session.run_sync(fn=Session.bulk_update_mappings, "
        'mapper=MessengerAccount, mappings=[{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "bulk_update_mappings",
        "phone",
        id="run-sync-keyword-fn",
    ),
    pytest.param(
        "async def f(conn, p):\n"
        "    await conn.run_sync(Connection.execute, update(MessengerAccount), "
        '[{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "execute",
        "phone",
        id="conn-run-sync-execute",
    ),
    pytest.param(
        "functools.partial(session.bulk_update_mappings, MessengerAccount)("
        '[{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "bulk_update_mappings",
        "phone",
        id="partial-bulk-update-applied",
    ),
    pytest.param(
        "async def f(s, p):\n"
        "    await asyncio.to_thread(s.bulk_update_mappings, MessengerAccount, "
        '[{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "bulk_update_mappings",
        "phone",
        id="to-thread-bulk-update",
    ),
    pytest.param(
        "async def f(loop, s, p):\n"
        "    await loop.run_in_executor(None, s.bulk_update_mappings, MessengerAccount, "
        '[{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "bulk_update_mappings",
        "phone",
        id="run-in-executor-bulk-update",
    ),
    pytest.param(
        'getattr(session, "bulk_update_mappings")(MessengerAccount, '
        '[{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "bulk_update_mappings",
        "phone",
        id="getattr-callee-bulk-update",
    ),
    pytest.param(
        'operator.methodcaller("bulk_update_mappings", MessengerAccount, '
        '[{"id": 1, "phone": p}])(session)\n',
        KIND_ROW_MAPPING,
        "bulk_update_mappings",
        "phone",
        id="methodcaller-bulk-update",
    ),
    pytest.param(
        'functools.partial(set_attribute, account, "phone")(x)\n',
        KIND_SETATTR,
        "set_attribute",
        "phone",
        id="partial-set-attribute-applied",
    ),
    pytest.param(
        "async def f(loop, a, x):\n"
        '    await loop.run_in_executor(None, setattr, a, "phone", x)\n',
        KIND_SETATTR,
        "setattr",
        "phone",
        id="run-in-executor-setattr",
    ),
    pytest.param(
        'stmt = getattr(update(MessengerAccount), "values")(phone=x)\n',
        KIND_KEYWORD,
        "values",
        "phone",
        id="getattr-callee-values-keyword",
    ),
    # План 16-17, задача 2: судимый параметр при любом литеральном связывании
    # (`JUDGED_PARAMETERS`), `{"phone": v for …}` с постоянным ключом и исполняющие
    # вызовы с параметром строк, как у `execute` (ревью WR-10, формы 1, 2, 3, 5).
    pytest.param(
        'session.query(MessengerAccount).filter_by(id=i).update(values={"phone": x})\n',
        KIND_DICT_KEY,
        "update",
        "phone",
        id="query-update-values-keyword",
    ),
    pytest.param(
        'set_attribute(account, key="phone", value=x)\n',
        KIND_SETATTR,
        "set_attribute",
        "phone",
        id="set-attribute-key-keyword",
    ),
    pytest.param(
        'set_committed_value(account, key="phone", value=x)\n',
        KIND_SETATTR,
        "set_committed_value",
        "phone",
        id="set-committed-value-key-keyword",
    ),
    pytest.param(
        'stmt = update(MessengerAccount).values(**{"phone": n for n in [x]})\n',
        KIND_KEYWORD,
        "values",
        "phone",
        id="values-double-star-dictcomp-constant-key",
    ),
    pytest.param(
        "async def f(s, ns):\n"
        '    await s.execute(update(MessengerAccount), [{"phone": n for n in ns}])\n',
        KIND_ROW_MAPPING,
        "execute",
        "phone",
        id="rows-dictcomp-constant-key",
    ),
    pytest.param(
        "async def f(s, p):\n"
        "    await s.scalars(insert(MessengerAccount).returning(MessengerAccount.id), "
        '[{"user_id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "scalars",
        "phone",
        id="scalars-insert-returning-rows",
    ),
    pytest.param(
        "async def f(s, p):\n"
        "    await s.scalar(insert(MessengerAccount).returning(MessengerAccount.id), "
        '{"user_id": 1, "phone": p})\n',
        KIND_ROW_MAPPING,
        "scalar",
        "phone",
        id="scalar-insert-returning-row",
    ),
    pytest.param(
        "async def f(s, p):\n"
        '    await s.stream(insert(MessengerAccount), [{"user_id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "stream",
        "phone",
        id="stream-insert-rows",
    ),
    pytest.param(
        'c.exec_driver_sql(sql, [{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "exec_driver_sql",
        "phone",
        id="exec-driver-sql-rows",
    ),
    pytest.param(
        'op.bulk_insert(accounts_table, rows=[{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "bulk_insert",
        "phone",
        id="alembic-bulk-insert-rows-keyword",
    ),
    pytest.param(
        "stmt = insert(MessengerAccount).values(user_id=1).on_conflict_do_update("
        'None, ["id"], None, {"phone": x})\n',
        KIND_UPSERT_SET,
        "on_conflict_do_update",
        "phone",
        id="upsert-set-positional-pg",
    ),
    pytest.param(
        "stmt = insert(MessengerAccount).values(user_id=1).on_conflict_do_update("
        '["id"], None, {"phone": x})\n',
        KIND_UPSERT_SET,
        "on_conflict_do_update",
        "phone",
        id="upsert-set-positional-sqlite",
    ),
    pytest.param(
        "async def f(session, p):\n"
        '    await session.run_sync(**{"fn": Session.bulk_update_mappings}, '
        'mapper=MessengerAccount, mappings=[{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "bulk_update_mappings",
        "phone",
        id="run-sync-double-star-fn",
    ),
    pytest.param(
        "async def f(session, p):\n"
        "    await session.run_sync(*[Session.bulk_update_mappings, MessengerAccount, "
        '[{"id": 1, "phone": p}]])\n',
        KIND_ROW_MAPPING,
        "bulk_update_mappings",
        "phone",
        id="run-sync-starred-reference",
    ),
]


@pytest.mark.parametrize(("source", "kind", "call", "column"), LITERAL_FORM_CASES)
def test_a_literal_write_form_is_a_write(source, kind, call, column):
    offences = phone_write_offences(source, "app/x.py")

    assert len(offences) == 1, (
        f"литеральная форма записи `{call}(… {column} …)` дала {len(offences)} "
        f"находок вместо одной: {offences}"
    )
    _location, found_kind, subject = offences[0].split(" — ", 2)
    assert found_kind == kind, f"вид находки «{found_kind}», ожидался «{kind}»: {offences}"
    assert call in subject and column in subject, (
        f"предмет находки не называет вызов `{call}` и колонку `{column}`: {offences}"
    )


LEGITIMATE_CASES = [
    pytest.param(
        'return render(request, "x.html", phone=phone)\n', id="render-phone-kwarg"
    ),
    pytest.param(
        "async def f(client, phone):\n    await client.start_session(phone=phone)\n",
        id="start-session-phone-kwarg",
    ),
    pytest.param(
        '_max_step_markup(request, step="phone", phone=phone)\n',
        id="max-step-markup-phone-kwarg",
    ),
    pytest.param(
        "class MessengerAccount(Base):\n"
        "    phone: Mapped[str | None] = mapped_column(String(16), nullable=True)\n"
        "    phone_is_manual: Mapped[bool] = mapped_column(Boolean, default=False)\n",
        id="model-column-declaration",
    ),
    pytest.param(
        'MANUAL_REQUIRES_PHONE = "NOT (phone_is_manual AND phone IS NULL)"\n',
        id="check-condition-constant",
    ),
    pytest.param(
        "def fill(session):\n"
        '    """Пишет одним оператором UPDATE messenger_accounts SET phone = :p."""\n',
        id="docstring-with-update-set-phone",
    ),
    pytest.param(
        '"""Модуль: INSERT INTO messenger_accounts делает мастер."""\n',
        id="module-docstring-with-insert",
    ),
    pytest.param(
        "number = account.phone\n"
        "stmt = select(MessengerAccount).where(MessengerAccount.phone.is_(None))\n",
        id="read-and-filter-by-phone",
    ),
    pytest.param(
        'logger.info("account_connected", phone_set=account.phone is not None)\n',
        id="phone-set-flag-in-log",
    ),
    pytest.param(
        'SQL = "UPDATE groups SET title = :t WHERE phone = :p"\n',
        id="update-filtering-by-phone-in-where",
    ),
    pytest.param(
        'templates.TemplateResponse("accounts/connect_max.html", '
        '{"request": request, "phone": submitted})\n',
        id="templates-response-context-phone",
    ),
    pytest.param(
        "async def f(session):\n"
        "    await session.execute(\n"
        "        select(MessengerAccount).where(MessengerAccount.phone.is_(None))\n"
        "    )\n",
        id="execute-select-filter-by-phone",
    ),
    pytest.param(
        'render(request, "x.html", **{"phone": phone})\n',
        id="render-double-star-phone",
    ),
    pytest.param(
        "stmt = insert(Group).values(title=t).on_conflict_do_update(\n"
        '    index_elements=["id"], set_={"title": t}\n'
        ")\n",
        id="upsert-set-other-columns",
    ),
    pytest.param(
        'session.bulk_update_mappings(Group, [{"id": 1, "title": t}])\n',
        id="bulk-update-mappings-other-columns",
    ),
    pytest.param(
        "async def f(session):\n"
        "    await session.execute(\n"
        '        update(MessengerAccount), [{"id": 1, "status": "active"}]\n'
        "    )\n",
        id="execute-rows-without-phone",
    ),
    pytest.param(
        "async def f(s, rows):\n"
        "    await s.execute(update(MessengerAccount), "
        '[{"id": a, "status": st} for a, st in rows])\n',
        id="execute-comprehension-rows-without-phone",
    ),
    pytest.param(
        "SQL = 'SELECT id FROM messenger_accounts WHERE \"phone\" = :p'\n",
        id="select-where-quoted-phone",
    ),
    pytest.param(
        "SQL = 'UPDATE groups SET title = :t WHERE \"phone\" = :p'\n",
        id="update-other-table-where-quoted-phone",
    ),
    pytest.param(
        'SQL = "UPDATE groups SET title = \'phone\' WHERE id = 1"\n',
        id="update-set-string-mentioning-phone",
    ),
    pytest.param(
        'SQL = "COPY messenger_accounts (id, phone) TO STDOUT"\n',
        id="copy-to-stdout-is-a-read",
    ),
    pytest.param(
        'SQL = "INSERT INTO groups (title) SELECT phone FROM messenger_accounts"\n',
        id="insert-into-another-table-selecting-phone",
    ),
    pytest.param(
        'SQL = "UPDATE groups " + "SET title = :t"\n',
        id="concatenation-without-phone",
    ),
    pytest.param(
        "async def f(conn, rows):\n"
        '    await conn.copy_records_to_table("groups", records=rows, columns=["phone"])\n',
        id="asyncpg-copy-into-another-table",
    ),
    pytest.param(
        "stmt = update(Group).ordered_values((Group.title, t))\n",
        id="ordered-values-other-column",
    ),
    pytest.param(
        'stmt = insert(Group).from_select(["title"], sel)\n',
        id="from-select-other-columns",
    ),
    pytest.param(
        'context.update({"title": t})\n',
        id="dict-update-other-keys",
    ),
    pytest.param(
        "from app.models.group import Group as G\ng = G(phone=x)\n",
        id="alias-of-another-model-with-phone-kwarg",
    ),
    pytest.param(
        'object.__setattr__(account, "status", x)\n',
        id="dunder-setattr-other-attribute",
    ),
    pytest.param(
        "SQL = 'SELECT id FROM `messenger_accounts` WHERE `phone` = :p'\n",
        id="select-backtick-where-phone",
    ),
    pytest.param(
        "SQL = \"LOAD DATA INFILE 'x.csv' INTO TABLE groups\"\n",
        id="load-data-into-another-table",
    ),
    pytest.param(
        'stmt = update(groups).values({groups.c["title"]: t})\n',
        id="table-c-subscript-other-column",
    ),
    pytest.param(
        'stmt = select(accounts).where(accounts.c["phone"] == p)\n',
        id="where-table-c-subscript-phone",
    ),
    # План 16-17, задача 1: ссылки на функции, которые не пишут номер. Первая —
    # живая форма `app/services/image_upload.py` (`to_thread(prepare_upload, …)`).
    pytest.param(
        "async def f(content):\n"
        "    return await asyncio.to_thread(prepare_upload, content)\n",
        id="to-thread-other-function",
    ),
    pytest.param(
        "async def f(conn):\n    await conn.run_sync(Base.metadata.create_all)\n",
        id="run-sync-create-all",
    ),
    pytest.param(
        "async def f(s, t):\n"
        "    await s.run_sync(Session.bulk_update_mappings, Group, "
        '[{"id": 1, "title": t}])\n',
        id="run-sync-bulk-other-columns",
    ),
    pytest.param(
        'view = functools.partial(render, request, "x.html", phone=phone)\n',
        id="partial-render-phone-kwarg",
    ),
    pytest.param(
        'getattr(session, "add")(account)\n',
        id="getattr-other-method",
    ),
    pytest.param(
        'operator.methodcaller("bulk_update_mappings", Group, '
        '[{"id": 1, "title": t}])(session)\n',
        id="methodcaller-other-columns",
    ),
    # План 16-17, задача 2: исполняющий вызов без строк и запись чужого атрибута.
    pytest.param(
        "async def f(s):\n"
        "    return await s.scalars(\n"
        "        select(MessengerAccount).where(MessengerAccount.phone.is_(None))\n"
        "    )\n",
        id="scalars-select-without-rows",
    ),
    pytest.param(
        'set_attribute(account, key="status", value=x)\n',
        id="set-attribute-keyword-other-attribute",
    ),
]


@pytest.mark.parametrize("source", LEGITIMATE_CASES)
def test_a_legitimate_phone_mention_is_not_a_write(source):
    offences = phone_write_offences(source, "app/x.py")

    assert offences == [], (
        f"законное упоминание номера гейт счёл записью — шум снимет гейт: {offences}"
    )


def test_the_walk_leaves_max_worker_alembic_and_tests_outside(tmp_path):
    """`max_worker/`, `alembic/` и `tests/` вне вселенной: их записи не судятся."""
    planted_write = "def f(state):\n    state.phone = '+79991234567'\n"
    _plant(tmp_path, "max_worker/main.py", planted_write)
    _plant(tmp_path, "tests/x.py", planted_write)
    _plant(tmp_path, "alembic/versions/x.py", planted_write)
    _plant(tmp_path, "app/pages/clean.py", 'render(request, "x.html", phone=phone)\n')

    sources, offences = tree_offences(tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in sources] == [
        "app/pages/clean.py"
    ], "обход вышел за `app/` и `scripts/` или не нашёл файл вселенной"
    assert offences == [], f"законный вызов в `app/` дал находку: {offences}"


def test_the_exception_registry_names_only_the_writer_module():
    """Реестр — ровно модуль-писатель с причиной; его записи не судятся, кроме присваивания.

    Второй исключённый модуль есть второй писатель: расширение реестра — решение
    владельца, а не правка ради зелени.
    """
    assert list(PHONE_WRITER_EXCEPTIONS) == [PHONE_WRITER_MODULE], (
        f"реестр исключений — не ровно модуль-писатель: {sorted(PHONE_WRITER_EXCEPTIONS)}"
    )
    assert PHONE_WRITER_EXCEPTIONS[PHONE_WRITER_MODULE].strip(), (
        "исключение модуля-писателя записано без причины"
    )
    writer_path = PROJECT_ROOT / PHONE_WRITER_MODULE
    assert writer_path.is_file(), f"исключён несуществующий файл {PHONE_WRITER_MODULE}"

    writer_source = writer_path.read_text(encoding="utf-8")
    raw = phone_write_offences(writer_source, PHONE_WRITER_MODULE)
    raw_kinds = {offence.split(" — ")[1] for offence in raw}

    assert {KIND_KEYWORD, KIND_SETATTR} <= raw_kinds, (
        f"в модуле-писателе предикат без исключения видит виды {sorted(raw_kinds)} — "
        "условный UPDATE и зеркало set_committed_value обязаны быть видны"
    )
    assert judged_offences(writer_source, PHONE_WRITER_MODULE) == [], (
        "записи модуля-писателя, кроме присваивания, судятся, хотя он в реестре"
    )


def test_control_an_assignment_inside_the_writer_module_still_reddens():
    """Присваивание атрибуту номера исключением не покрывается — даже в писателе.

    Писатель пишет только операторами UPDATE и зеркалит `set_committed_value`;
    присваивание сделало бы объект грязным, и ORM выдала бы на коммите второй,
    безусловный UPDATE мимо условной записи.
    """
    sneaked = "    account.phone = '+79990000000'"
    source = (
        (PROJECT_ROOT / PHONE_WRITER_MODULE).read_text(encoding="utf-8")
        + "\n\ndef _sneak(account):\n"
        + sneaked
        + "\n"
    )
    line = source.splitlines().index(sneaked) + 1

    assert judged_offences(source, PHONE_WRITER_MODULE) == [
        f"{PHONE_WRITER_MODULE}:{line} — {KIND_ASSIGNMENT} — account.phone"
    ], "присваивание номера в модуле-писателе прикрыто исключением"

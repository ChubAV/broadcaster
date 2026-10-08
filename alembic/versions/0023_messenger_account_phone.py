"""Номер аккаунта: место в схеме для номера в E.164 и признака «указан вручную»

ЗАЧЕМ. Веха v2.2 «Номера аккаунтов» показывает рядом с аккаунтом его номер,
чтобы человек различал два аккаунта одного мессенджера. Номер читают писатель
(план 16-05), подпись Фазы 17, форма Фазы 18, захват Фазы 19 и дозаполнение
Фазы 20 — и у всех них должно быть одно место, куда номер ложится. Эта ревизия
заводит это место и больше ничего.

ДВЕ КОЛОНКИ.

    `phone` — `String(16)`, NULL. Номер хранится в E.164: `+` и до 15 цифр
    (предел E.164, D-14), отсюда длина 16. NULL означает «номер неизвестен» и
    обязан отличаться от пустой строки — пустая строка была бы «номером»,
    которого нет, и прошла бы мимо любого `IS NULL`.

    `phone_is_manual` — `Boolean`, NOT NULL, умолчание `false` на стороне базы.
    Признак «номер указал пользователь»: автоисточник его не затирает (D-07).
    Умолчание стоит в схеме, а не только в модели, потому что именно оно
    заполняет признак у всех существующих строк при накате.

⚠️ УНИКАЛЬНОСТИ ПО НОМЕРУ НЕТ, И ЭТО РЕШЕНИЕ, А НЕ НЕДОСМОТР (D-02). Один SIM
законно даёт аккаунт Telegram, WhatsApp и MAX одновременно, а Telegram при
пересканировании QR создаёт НОВУЮ строку для того же номера. Уникальный индекс
по номеру запретил бы ровно эти законные состояния.

⚠️ ДАННЫХ РЕВИЗИЯ НЕ ПРАВИТ — НИ ОДНОЙ СТРОКИ (D-01). После наката у КАЖДОГО
существующего аккаунта номер «неизвестен»: `phone IS NULL`,
`phone_is_manual = false`. В том числе у MAX, чей введённый при подключении
номер уже лежит в `credentials`: переносит его дозаполнение Фазы 20 через
модуль-писатель (`app/application/accounts/phone.py`, D-13), а не ревизия.
Ревизия, угадывающая номер из JSON учётных данных, стала бы вторым писателем
колонки в обход правила «пишет один модуль» — и её решение нельзя было бы
откатить: откат снимает колонку, а не знание о том, откуда взялось значение.

«РУЧНОЙ БЕЗ НОМЕРА» НЕВОЗМОЖЕН — В СХЕМЕ (D-03). Именованное ограничение
`ck_messenger_accounts_manual_requires_phone` с условием
`NOT (phone_is_manual AND phone IS NULL)` запрещает ровно одну пару из четырёх:
признак «указан вручную» при неизвестном номере. Такая строка была бы мертва
навсегда и молча — автоисточник не вправе писать поверх ручного (D-07), а
показывать нечего. Прикладная проверка писателя делает состояние
НЕДОСТИЖИМЫМ ЧЕРЕЗ ПРИЛОЖЕНИЕ, а не НЕВОЗМОЖНЫМ (довод `0021`/`0022`): прямой
psql, ручной UPDATE и любой второй писатель обходят её разом. Запрет держится с
обеих сторон UPDATE, поэтому очистка номера меняет обе колонки одним
оператором.

ДАННЫЕ ПЕРЕД СОЗДАНИЕМ ОГРАНИЧЕНИЯ НЕ ПРАВЯТСЯ — И ЭТО НЕ ПРОПУСК. Колонки
новые: в момент создания ограничения у каждой строки `phone IS NULL` и
`phone_is_manual = false`, то есть законная пара «неизвестен». Нарушителей
нет по построению, зачистки, как у `0022`, не требуется.

BATCH_ALTER_TABLE НА SQLITE И ПОЧЕМУ `copy_from`. На PostgreSQL колонки
добавляются обычным `ALTER TABLE ... ADD COLUMN`, без пересоздания. На SQLite
batch-режим ПЕРЕСОЗДАЁТ таблицу и переносит строки, а отражение SQLite в
SQLAlchemy не переносит `ON DELETE` вовсе — это ИЗМЕРЕНО на ревизии `0022`
(её шапка): пересозданная по отражению таблица теряла правила внешних ключей
без единого предупреждения. Здесь потеря означала бы `user_id` без
`ON DELETE CASCADE`: удаление пользователя оставляло бы сиротские аккаунты.
Поэтому состав таблицы на момент `0022` выписан ЯВНО (`_accounts`) и передаётся
в `copy_from`. Правила детей (`groups.account_id` — CASCADE,
`schedules.account_id` — SET NULL) живут в ДЕТЯХ и пересозданием родителя не
затрагиваются; их сохранность закреплена тестом ревизии, а не надеждой.

⚠️ ГРАНИЦА: ВЕТКА POSTGRESQL ТЕСТАМИ НЕ ИСПОЛНЯЛАСЬ (A1 разведки фазы 16).
Тестового PostgreSQL в окружении нет, а на хосте работают боевые контейнеры,
трогать которые нельзя; тесты ревизий проекта идут по SQLite, как и у `0022`.
Что `server_default=sa.false()` рендерится в `DEFAULT false` и что таблица на
PG не пересоздаётся — допущение, которое проверяет деплой-гейт владельца
(D-26, R-08-06), а не суита.

⚠️ ВЫКАТ — ТОЛЬКО ВМЕСТЕ С ОЧЕРЕДЬЮ `0020…0023` (D-01: one-way, D-26,
R-08-06). Ревизия создана, но не накачена ни на одну базу; накат — действие
владельца, а не автора ревизии.

Литералы имени таблицы, колонок и их типов выписаны ЗДЕСЬ и НЕ импортированы
из `app.models` — правило ревизий `0013`/`0014`/`0017`/`0018`/`0020`/`0021`/
`0022`: ревизия описывает схему на СВОЙ момент времени, и правка модели задним
числом не имеет права изменить смысл давно выполненного шага.

Revision ID: 0023
Revises: 0022
"""
from alembic import op
import sqlalchemy as sa

revision = "0023"
down_revision = "0022"

TABLE = "messenger_accounts"
CONSTRAINT_NAME = "ck_messenger_accounts_manual_requires_phone"

# Условие выписано ОДНОЙ формулировкой. Дословно то же стоит в
# `app/models/messenger_account.py` (MANUAL_REQUIRES_PHONE); совпадение сверяет
# тест, потому что импортировать модель сюда нельзя.
CONDITION = "NOT (phone_is_manual AND phone IS NULL)"


def _new_columns() -> list[sa.Column]:
    """Две колонки этой ревизии — одним описанием для обеих веток диалекта."""
    return [
        sa.Column("phone", sa.String(length=16), nullable=True),
        sa.Column(
            "phone_is_manual",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    ]


def _accounts(*, with_new: bool, with_constraint: bool) -> sa.Table:
    """Состав таблицы, выписанный ЯВНО — для `copy_from` на SQLite.

    Собран по ревизиям, а не по сегодняшней модели: `0001_initial_schema.py`
    (семь колонок, внешний ключ на `users` с `ON DELETE CASCADE`) и
    `0014_sync_result_and_group_missing.py` (`last_synced_at`,
    `last_sync_result`). Ревизии `0012` и `0022` таблицу лишь называют
    внешним ключом `schedules` и её колонок не меняют. Ровно это и есть схема
    на момент `0022`. Индексов у таблицы нет и не было — `0001` не заводит их.

    `with_new=True, with_constraint=True` описывает её же ПОСЛЕ этой ревизии —
    состав нужен обратному проходу, которому иначе нечего снимать: отражение
    SQLite не показывает CHECK-ограничения вовсе.
    """
    args = [
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("credentials", sa.Text(), nullable=False),
        sa.Column("session_data", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="disconnected",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_result", sa.Text(), nullable=True),
    ]
    if with_new:
        args.extend(_new_columns())
    if with_constraint:
        args.append(sa.CheckConstraint(CONDITION, name=CONSTRAINT_NAME))
    return sa.Table(TABLE, sa.MetaData(), *args)


def upgrade():
    connection = op.get_bind()

    if connection.dialect.name == "postgresql":
        for column in _new_columns():
            op.add_column(TABLE, column)
        op.create_check_constraint(CONSTRAINT_NAME, TABLE, CONDITION)
    else:
        # SQLite: таблица пересоздаётся целиком. Состав передаётся ЯВНО — см.
        # абзац про `copy_from` в шапке: на отражении терялись правила ON DELETE.
        with op.batch_alter_table(
            TABLE, copy_from=_accounts(with_new=False, with_constraint=False)
        ) as batch_op:
            for column in _new_columns():
                batch_op.add_column(column)
            batch_op.create_check_constraint(CONSTRAINT_NAME, CONDITION)


def downgrade():
    # Откат снимает ограничение и ровно две колонки этой ревизии — и больше
    # ничего (D-01). Сначала ограничение: оно называет обе колонки. Значения
    # номеров, если они успели появиться, теряются вместе с колонкой:
    # притворяться, что откат их сохраняет, нечем.
    connection = op.get_bind()

    if connection.dialect.name == "postgresql":
        op.drop_constraint(CONSTRAINT_NAME, TABLE, type_="check")
        op.drop_column(TABLE, "phone_is_manual")
        op.drop_column(TABLE, "phone")
    else:
        with op.batch_alter_table(
            TABLE, copy_from=_accounts(with_new=True, with_constraint=True)
        ) as batch_op:
            batch_op.drop_constraint(CONSTRAINT_NAME, type_="check")
            batch_op.drop_column("phone_is_manual")
            batch_op.drop_column("phone")

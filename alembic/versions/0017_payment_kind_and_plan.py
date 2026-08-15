"""Предмет покупки и тариф на платеже

ЗАЧЕМ. До этой ревизии таблица `payments` умела описывать ровно одну покупку —
пакет сообщений, — и предмет покупки был не записан нигде: он ВЫВОДИЛСЯ из того,
что `messages_count` заполнен. С появлением подписки (BILL-05) такой вывод
перестаёт работать: у платежа за тариф сообщений не покупается вовсе. Колонка
`kind` делает предмет покупки явным и в своей базе, и — через `metadata` ЮKassa —
в кабинете магазина, где иначе два разных предмета неразличимы (T-05-08).

`messages_count` СНИМАЕТ NOT NULL. Ноль вместо NULL здесь был бы неправдой:
он читается как «куплено ноль сообщений», тогда как у подписки сообщений не
покупается. Ревизия при этом не теряет ни одной строки — ограничение
ослабляется, а не ужесточается.

BACKFILL ИДЁТ SERVER_DEFAULT'ОМ, отдельного UPDATE нет и не должно быть.
`ADD COLUMN ... NOT NULL DEFAULT 'package'` проставляет значение всем
существующим строкам самим определением колонки, и это ровно верное значение:
до этой ревизии в таблице физически не могло быть ни одного платежа за подписку.
Отдельный UPDATE делал бы ту же работу вторым проходом по таблице.

BATCH_ALTER_TABLE — не стилистика. SQLite не умеет `ALTER COLUMN` вообще, а вся
тестовая суита проекта идёт на SQLite; `op.alter_column` там падает. Batch-режим
пересоздаёт таблицу на SQLite и разворачивается в обычный ALTER на PostgreSQL,
поэтому один и тот же код ревизии применим на обоих диалектах.

Downgrade симметричен: две колонки снимаются, NOT NULL возвращается. Он теряет
данные ровно там, где иначе не может: строки подписок, у которых
`messages_count` NULL, обратному NOT NULL противоречат — поэтому откат делается
на базе, где платежей за подписку ещё нет (D-15). Выкат `0017` на боевую базу,
где она встаёт пятой в очереди невыкаченных ревизий, решается отдельно (план 05-06).

Revision ID: 0017
Revises: 0016
"""
from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"

# Литералы 'package' и 'subscription' выписаны ЗДЕСЬ, а не импортированы из
# app.models / app.constants: ревизия обязана описывать схему на СВОЙ момент
# времени (правило ревизии 0013, повторённое в 0014). Импорт связал бы уже
# применённую миграцию с текущим кодом, и переименование константы задним
# числом изменило бы смысл давно выполненного шага.
KIND_DEFAULT = "package"


def upgrade():
    op.add_column(
        "payments",
        sa.Column(
            "kind",
            sa.String(length=50),
            nullable=False,
            server_default=KIND_DEFAULT,
        ),
    )
    op.add_column(
        "payments",
        sa.Column("plan", sa.String(length=50), nullable=True),
    )
    with op.batch_alter_table("payments") as batch_op:
        batch_op.alter_column(
            "messages_count", existing_type=sa.Integer(), nullable=True
        )


def downgrade():
    with op.batch_alter_table("payments") as batch_op:
        batch_op.alter_column(
            "messages_count", existing_type=sa.Integer(), nullable=False
        )
    op.drop_column("payments", "plan")
    op.drop_column("payments", "kind")

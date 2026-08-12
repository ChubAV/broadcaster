"""Одна строка на одну группу мессенджера внутри аккаунта

Ревизия закрывает гонку двойного нажатия «Синхронизировать всё» на уровне
СХЕМЫ. Прикладной guard `status == "syncing"` её не закрывал: страничный
обработчик синхронизации выполняется синхронно и статус `syncing` не занимает
вовсе — его ставят только фоновые пути. Два одновременных POST-а читали
одинаковый состав существующих групп, оба делали INSERT для одного и того же
`group_external_id`, и в таблице появлялись две строки на одну группу
мессенджера: обе видны на экране, обе выбираемы в расписаниях, а выбор обеих
означал две отправки в один и тот же чат.

ПОЧЕМУ РЕВИЗИЯ УДАЛЯЕТ СТРОКИ (единственное исключение из правила «синк не
удаляет данные пользователя», D-11). Ограничение невозможно наложить на
таблицу, в которой дубли уже есть, а дубль — это не данные пользователя, а
след дефекта: две строки описывают ОДНУ группу мессенджера. Правила слияния
выбраны так, чтобы не потерять ни одного пользовательского решения:

- выживает строка с НАИМЕНЬШИМ id. Она появилась первой, и именно на неё
  ссылаются расписания, созданные до появления дубля (`schedules.group_ids`
  хранится JSON-ом, и переписать эти ссылки ревизия не может);
- выживает ВЫКЛЮЧЕННОСТЬ: если хотя бы одна из строк группы была выключена,
  выключенной остаётся и выжившая. Направление выбрано в сторону
  НЕотправки — ошибка «не отправили в чат, куда хотели» исправляется одним
  нажатием тумблера, а ошибка «отправили в чат, который выключили» уже
  необратима;
- выживает САМАЯ РАННЯЯ пометка пропажи: подпись «не найдена с …» обязана
  говорить, когда группа исчезла, а не когда о ней вспомнили последний раз
  (то же правило, что и в `apply_group_resync`).

Ограничение создаётся через `batch_alter_table`: на SQLite (тестовая суита)
именованное UNIQUE-ограничение иначе не добавляется — диалект не поддерживает
`ALTER TABLE ... ADD CONSTRAINT`. На PostgreSQL batch-режим сводится к обычному
`ALTER TABLE`.

Downgrade снимает ровно это ограничение. Удалённые дубли он, разумеется, не
воскрешает — и не должен: их существование и было дефектом.

Revision ID: 0015
Revises: 0014
"""
from alembic import op
import sqlalchemy as sa

revision = "0015"
down_revision = "0014"

CONSTRAINT_NAME = "uq_groups_account_external"

# Схлопывание дублей выписано голым SQL и без импорта из app.models: ревизия
# обязана описывать схему на СВОЙ момент времени (правило ревизий 0013 и 0014).
# Оператор совместим и со SQLite, и с PostgreSQL: коррелированные подзапросы по
# той же таблице поддерживают оба диалекта.

# 1. Выключенность переносится на выжившую строку — до удаления дублей.
_MERGE_IS_ACTIVE = sa.text(
    """
    UPDATE groups SET is_active = 0
    WHERE id IN (
        SELECT MIN(g.id) FROM groups AS g
        GROUP BY g.account_id, g.group_external_id
        HAVING COUNT(*) > 1 AND MIN(g.is_active) = 0
    )
    """
)

# 2. Самая ранняя пометка пропажи — туда же. Строки, где пометки нет ни у
#    одной из копий, оператор не трогает: MIN по одним NULL даёт NULL, и
#    условие IS NOT NULL их отсекает.
_MERGE_MISSING_SINCE = sa.text(
    """
    UPDATE groups SET missing_since = (
        SELECT MIN(d.missing_since) FROM groups AS d
        WHERE d.account_id = groups.account_id
          AND d.group_external_id = groups.group_external_id
    )
    WHERE id IN (
        SELECT MIN(g.id) FROM groups AS g
        GROUP BY g.account_id, g.group_external_id
        HAVING COUNT(*) > 1
    )
    AND (
        SELECT MIN(d.missing_since) FROM groups AS d
        WHERE d.account_id = groups.account_id
          AND d.group_external_id = groups.group_external_id
    ) IS NOT NULL
    """
)

# 3. И только теперь — снятие лишних строк.
_DROP_DUPLICATES = sa.text(
    """
    DELETE FROM groups
    WHERE id NOT IN (
        SELECT MIN(g.id) FROM groups AS g
        GROUP BY g.account_id, g.group_external_id
    )
    """
)


def upgrade():
    connection = op.get_bind()
    connection.execute(_MERGE_IS_ACTIVE)
    connection.execute(_MERGE_MISSING_SINCE)
    connection.execute(_DROP_DUPLICATES)

    with op.batch_alter_table("groups") as batch_op:
        batch_op.create_unique_constraint(
            CONSTRAINT_NAME, ["account_id", "group_external_id"]
        )


def downgrade():
    with op.batch_alter_table("groups") as batch_op:
        batch_op.drop_constraint(CONSTRAINT_NAME, type_="unique")

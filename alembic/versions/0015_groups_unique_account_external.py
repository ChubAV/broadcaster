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
  ссылаются расписания, созданные до появления дубля. Расписания, созданные
  или отредактированные ПОСЛЕ появления дубля, могли выбрать и строку с
  бОльшим id — обе были видны на экране и обе выбирались, — поэтому ссылки на
  удаляемые строки ревизия ПЕРЕПИСЫВАЕТ на выжившую (`_remap_schedule_group_ids`
  ниже) ДО удаления. Иначе в `schedules.group_ids` осталась бы висячая ссылка,
  а висячая ссылка ведёт себя молча: WA/MAX получают адресата `null`, а
  Telegram — журнальную запись «Missing ad, group, or account». Ровно этот
  инвариант держит и маршрут удаления группы
  (`app/pages/account_groups.py`: «оставленный в `Schedule.group_ids`
  идентификатор удалённой строки не роняет отправку, он делает её тихо
  неполной»);
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
import json

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
#
# `is_active` — колонка типа Boolean, и на PostgreSQL это НАСТОЯЩИЙ boolean, а
# не 0/1, как на SQLite. Поэтому здесь нельзя ни `MIN(g.is_active)` (агрегата
# `min(boolean)` в PostgreSQL просто нет — запрос падает), ни `SET is_active = 0`
# (целочисленный литерал в boolean-колонку PostgreSQL не принимает). Тестовая
# суита идёт по SQLite и оба этих дефекта пропускает, а боевая база —
# PostgreSQL, и ревизия оборвалась бы прямо на деплое. Отсюда `CASE` вместо
# агрегата по boolean и ключевое слово `false` вместо нуля: оба понимают и
# SQLite, и PostgreSQL.
_MERGE_IS_ACTIVE = sa.text(
    """
    UPDATE groups SET is_active = false
    WHERE id IN (
        SELECT MIN(g.id) FROM groups AS g
        GROUP BY g.account_id, g.group_external_id
        HAVING COUNT(*) > 1
           AND MIN(CASE WHEN g.is_active THEN 1 ELSE 0 END) = 0
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

# 3. Соответствие «удаляемая строка -> выжившая» для переписывания ссылок.
_DUPLICATE_MAP = sa.text(
    """
    SELECT d.id AS dead, s.keep AS keep
    FROM groups AS d
    JOIN (
        SELECT account_id, group_external_id, MIN(id) AS keep
        FROM groups
        GROUP BY account_id, group_external_id
        HAVING COUNT(*) > 1
    ) AS s
      ON s.account_id = d.account_id
     AND s.group_external_id = d.group_external_id
    WHERE d.id <> s.keep
    """
)

_SELECT_SCHEDULE_GROUP_IDS = sa.text(
    "SELECT id, group_ids FROM schedules WHERE group_ids IS NOT NULL"
)

# Параметр объявлен типом JSON, а не голой строкой: сериализацию берёт на себя
# диалект. На SQLite колонка — TEXT и значение уходит строкой, на PostgreSQL —
# настоящий `json`, куда текстовый литерал без приведения типа не принимается.
_UPDATE_SCHEDULE_GROUP_IDS = sa.text(
    "UPDATE schedules SET group_ids = :group_ids WHERE id = :schedule_id"
).bindparams(
    sa.bindparam("group_ids", type_=sa.JSON()),
    sa.bindparam("schedule_id", type_=sa.Integer()),
)


def _remap_schedule_group_ids(connection) -> None:
    """Переводит ссылки расписаний с удаляемых дублей на выжившую строку.

    Вызывается ДО `_DROP_DUPLICATES`: после удаления соответствие уже не
    построить, а оставленный в JSON идентификатор несуществующей строки не
    роняет отправку — он делает её ТИХО неполной (см. докстринг модуля).

    `schedules.group_ids` — JSON-список, и агрегата по его элементам нет ни в
    одном из двух диалектов, поэтому перевод идёт построчно на стороне Python.
    Порядок сохраняется, а дубликаты, возникшие ПОСЛЕ перевода (расписание
    выбрало обе строки одной группы), схлопываются: иначе одна группа получила
    бы два сообщения — ровно тот дефект, ради устранения которого ревизия и
    написана.

    Элементы, не являющиеся целыми, проходят насквозь: значение колонки пишет
    только наш код, но ревизия не имеет права упасть на мусоре в чужой базе.
    """
    mapping = {row.dead: row.keep for row in connection.execute(_DUPLICATE_MAP)}
    if not mapping:
        return

    for row in connection.execute(_SELECT_SCHEDULE_GROUP_IDS).fetchall():
        raw = row.group_ids
        # На SQLite колонка отдаётся строкой, на PostgreSQL asyncpg-кодек
        # SQLAlchemy уже вернул список — принимаются оба вида.
        if isinstance(raw, (str, bytes)):
            try:
                ids = json.loads(raw)
            except (TypeError, ValueError):
                continue
        else:
            ids = raw
        if not isinstance(ids, list):
            continue

        moved: list = []
        seen: set = set()
        for group_id in ids:
            new_id = mapping.get(group_id, group_id) if isinstance(group_id, int) else group_id
            if isinstance(new_id, int):
                if new_id in seen:
                    continue
                seen.add(new_id)
            moved.append(new_id)

        if moved != ids:
            connection.execute(
                _UPDATE_SCHEDULE_GROUP_IDS,
                {"group_ids": moved, "schedule_id": row.id},
            )


# 4. И только теперь — снятие лишних строк.
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
    _remap_schedule_group_ids(connection)
    connection.execute(_DROP_DUPLICATES)

    with op.batch_alter_table("groups") as batch_op:
        batch_op.create_unique_constraint(
            CONSTRAINT_NAME, ["account_id", "group_external_id"]
        )


def downgrade():
    with op.batch_alter_table("groups") as batch_op:
        batch_op.drop_constraint(CONSTRAINT_NAME, type_="unique")

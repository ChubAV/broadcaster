# SendLog: убрать FK, добавить снапшоты

**Дата:** 2026-02-25

## Проблема

При удалении объявлений, групп, аккаунтов или расписаний вся история отправки (SendLog) каскадно удаляется из-за `ondelete="CASCADE"` на всех FK.

## Решение

**Hard delete сущностей + SendLog без FK со снапшотами.**

### 1. Модель SendLog — убираем все ForeignKey

Столбцы `schedule_id`, `ad_id`, `group_id` становятся обычными `Integer` (nullable) без ссылочной целостности. Добавляем поля-снапшоты:

| Поле | Тип | Описание |
|------|-----|----------|
| `ad_title` | `String(255), nullable` | Название объявления |
| `ad_text` | `Text, nullable` | Текст объявления |
| `ad_images` | `JSON, nullable` | Картинки объявления |
| `group_name` | `String(255), nullable` | Название группы |
| `account_name` | `String(255), nullable` | Название аккаунта |
| `messenger_type` | `String(20), nullable` | Тип мессенджера |

### 2. Создание SendLog (use_cases.py)

При создании записи заполняем все снапшоты из загруженных сущностей:
```python
SendLog(
    schedule_id=schedule_id,
    ad_id=ad_id,
    group_id=group_id,
    ad_title=ad.title,
    ad_text=ad.text,
    ad_images=ad.images,
    group_name=group.name,
    account_name=account.name,
    messenger_type=account.messenger_type,
    status=...,
    error_message=...,
)
```

### 3. Отображение истории

- `app/pages/history.py` — данные берутся напрямую из SendLog, без JOIN
- `app/routes/history.py` — API возвращает снапшоты, поля `*_id` nullable
- Fallback для старых записей без снапшотов: "—"

### 4. Каскады между сущностями

Каскады Account→Group, Account→Schedule, Ad→Schedule — остаются как есть. SendLog не затрагивается при удалении.

### 5. Миграция Alembic

- Удалить 3 FK constraint
- Сделать `schedule_id`, `ad_id`, `group_id` nullable
- Добавить 6 новых столбцов
- Data migration: заполнить снапшоты для существующих записей через UPDATE...FROM

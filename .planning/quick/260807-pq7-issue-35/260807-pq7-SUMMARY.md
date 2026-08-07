---
quick_id: 260807-pq7
slug: issue-35
status: complete
date: 2026-08-07
description: "issue 35: при удалении аккаунта мессенджера расписания не удаляются, а переходят в статус приостановлено"
plan: 260807-pq7-PLAN.md
tasks_total: 3
tasks_completed: 3
commits:
  - e834263
  - bacdc94
  - b4757b3
  - 454cd08
  - 845457d
  - 95babd3
---

# Quick Task 260807-pq7 — Summary

**Issue #35:** «При удалении аккаунта любого из мессанджеров расписание не должно
удаляться оно должно оставаться и переходить в статус приостановлено».

## Что было не так

`Schedule.account_id` был `ForeignKey("messenger_accounts.id", ondelete="CASCADE")`
и `NOT NULL`. Любое удаление messenger-аккаунта уничтожало все его расписания.

Мест удаления аккаунта оказалось **четыре**, а не два:

| # | Место | Контекст |
|---|-------|----------|
| 1 | `app/routes/accounts.py:65` | JSON API `DELETE /accounts/{id}` |
| 2 | `app/application/accounts/use_cases.py:82` | use case, вызывается из `app/pages/accounts.py:834` |
| 3 | `app/pages/accounts.py:361` | WA connect — очистка «залипших» `connecting`/`sync_failed` аккаунтов |
| 4 | `app/pages/accounts.py:508` | MAX connect — тот же цикл |

Сайты 3 и 4 тоже молча уничтожали расписания при повторном подключении.

## Решение

**Статус «приостановлено» не изобретался** — в проекте он уже есть: это
`is_active = False` + `next_run_at = None` (ровно то, что пишет `/schedules/{id}/toggle`).
Шаблоны уже рендерят это как «Пауза» с кнопкой возобновления.

Выбран вариант «жёсткое удаление аккаунта + nullable FK + `ON DELETE SET NULL`
+ явная отвязка на уровне приложения». Мягкое удаление аккаунта отвергнуто:
`MessengerAccount.status` — это словарь состояния подключения
(`disconnected`/`connecting`/`active`/`syncing`/`sync_failed`), который читают
worker-диспетчер и оба container manager'а; плюс мягкое удаление сохранило бы
`credentials`/`session_data` (живые сессии Telegram/WA/MAX) аккаунта, который
пользователь попросил удалить.

### Задача 1 — сохранение и пауза расписаний

- `app/models/schedule.py` — `account_id` стал `int | None`, `nullable=True`,
  `ondelete="SET NULL"`.
- `alembic/versions/0012_schedules_account_id_nullable_set_null.py` — новая
  миграция: снятие `NOT NULL` + пересоздание FK с `SET NULL` (шаг FK
  выполняется только на PostgreSQL). `downgrade()` рабочий, но **разрушающий**:
  отвязанные строки (`account_id IS NULL`) невозможно привязать обратно, поэтому
  они удаляются ради восстановления `NOT NULL` — это задокументировано в самой
  миграции.
- `detach_schedules_from_account()` в `app/application/accounts/use_cases.py` —
  bulk `UPDATE ... SET is_active=false, next_run_at=NULL, account_id=NULL`,
  без коммита (транзакцией владеет вызывающая сторона, чтобы отвязка и удаление
  аккаунта были атомарны). Подключён во всех четырёх местах удаления.

Почему нужен явный UPDATE, а не только FK: `Schedule.account` — однонаправленный
`relationship(..., lazy="raise")` без backref, SQLAlchemy сам ничего не занулит;
а тесты идут на `sqlite+aiosqlite` с выключенным `PRAGMA foreign_keys`, где
DB-level `SET NULL` вообще не сработает. FK остаётся страховкой для прямых
SQL-удалений.

### Задача 2 — видимость отвязанных расписаний

`app/pages/schedules.py:57` и `:93` использовали **INNER JOIN** на
`MessengerAccount` — отвязанное расписание не упало бы с 500, а просто **исчезло
бы из списка**, что хуже. Заменено на `isouter=True`.
`ScheduleResponse.account_id` в `app/routes/schedules.py` стал `int | None`
(`CreateScheduleRequest.account_id` остался обязательным).
Шаблоны править не пришлось: `app/templates/includes/messenger_icon.html` уже
имеет `{% else %}`-ветку.

### Задача 3 — запрет возобновления отвязанного расписания

Без этого пользователь мог нажать «Возобновить», расписание становилось активным,
получало `next_run_at` и дальше молча перепланировалось, ничего не отправляя.
Оба toggle-пути (`app/routes/schedules.py:161`, `app/pages/schedules.py:341`)
теперь отказывают именно в направлении «возобновить», пока `account_id IS NULL`.
Постановка на паузу активного расписания не блокируется.

Путь восстановления: форма редактирования расписания
(`app/pages/schedules.py:315`) позволяет привязать новый аккаунт, после чего
расписание возобновляется штатно.

## Worker

Изменений не потребовалось: `collect_due_schedules` выбирает только
`is_active == True` и уже содержит защиту `if not ad or not account`.

## Тесты

Добавлено 17 тестов (TDD: сначала падающие, затем фикс):

- `tests/test_application/test_account_deletion_schedules.py` — расписание
  переживает удаление аккаунта, приходит в `is_active=False` / `next_run_at=None`
  / `account_id=None`; покрыты все четыре места удаления; отдельный тест
  проверяет, что расписание **другого** аккаунта не задето (T-pq7-01).
- `tests/test_pages/test_schedules_detached_account.py` — отвязанное расписание
  видно в списке, в partial и открывается на редактирование.
- `tests/test_routes/test_schedules_toggle_detached.py` — возобновление
  отвязанного расписания отклоняется (400 / без изменения состояния), пауза
  активного работает.

**Результат прогона:** на чистом дереве HEAD — `389 passed, 0 failed`
(полный `pytest tests/`).

> Примечание: прогон в рабочем каталоге разработчика даёт 26 падений, ни одно
> из которых не относится к issue #35. Разбивка (проверена экспериментально):
>
> - **25 падений + 2 ошибки** (`test_config_s3`, `test_e2e`, `test_groups_bulk`,
>   `test_sync_groups`, `test_tg_user_auth`, `test_uploads`, `test_wa_sync_status`)
>   вызваны локальным файлом **`.env`** (gitignored), который `Settings`
>   подхватывает в тестах: например `test_s3_settings_defaults` ожидает
>   `s3_endpoint_url == ""`, а получает прод-значение из `.env`. Воспроизведено
>   на чистом `HEAD` без единого изменения — достаточно симлинка на `.env`.
>   Это инфраструктурный дефект тестов (нужен `env_file=None` или
>   `monkeypatch`-изоляция в `conftest.py`), а не регрессия.
> - **1 падение** — `test_whatsapp_routing::TestEnsureWaContainer::test_returns_existing_endpoint`,
>   вызвано незакоммиченной правкой `app/messengers/whatsapp.py` (тест патчит
>   только `get_wa_endpoint`, а новый контракт `ensure_wa_container` вызывает
>   ещё `get_container_endpoint` и `wait_for_container_ready` — тест реально
>   поднимает Docker-контейнер и падает по таймауту). К issue #35 отношения не
>   имеет.
>
> На чистом `HEAD` без `.env` — `389 passed, 0 failed`.

## Развёртывание

Требуется `just upgrade` (alembic `0011` → `0012`) перед деплоем кода.

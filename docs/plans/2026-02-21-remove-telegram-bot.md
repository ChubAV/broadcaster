# Remove Telegram Bot Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove all Telegram Bot API (`tg_bot`) support from the project, keeping only Telegram Userbot (`tg_user`) and WhatsApp (`wa`).

**Architecture:** Delete the bot adapter, its template, and tests. Remove all `tg_bot` branches from worker factory, routes, and UI templates. Update all tests that used `tg_bot` as a convenient account type to use `tg_user` instead. Create an Alembic data migration to delete existing `tg_bot` records. Remove `aiogram` dependency.

**Tech Stack:** Python, FastAPI, SQLAlchemy, Alembic, Jinja2, pytest

---

### Task 1: Delete Telegram Bot files

**Files:**
- Delete: `app/messengers/telegram_bot.py`
- Delete: `app/templates/accounts/connect_tg_bot.html`
- Delete: `tests/test_messengers/test_telegram_bot.py`

**Step 1: Delete the three files**

```bash
rm app/messengers/telegram_bot.py
rm app/templates/accounts/connect_tg_bot.html
rm tests/test_messengers/test_telegram_bot.py
```

**Step 2: Commit**

```bash
git add -u app/messengers/telegram_bot.py app/templates/accounts/connect_tg_bot.html tests/test_messengers/test_telegram_bot.py
git commit -m "chore: delete telegram bot adapter, template, and tests"
```

---

### Task 2: Remove tg_bot from worker factory

**Files:**
- Modify: `app/worker/tasks.py`

**Step 1: Edit app/worker/tasks.py**

Remove the import on line 14:
```python
from app.messengers.telegram_bot import TelegramBotMessenger
```

In the `get_messenger()` function, remove the `tg_bot` branch (lines 24-25):
```python
    if account.type == "tg_bot":
        return TelegramBotMessenger(token=account.credentials)
    elif account.type == "tg_user":
```

Change the remaining `elif account.type == "tg_user":` to `if account.type == "tg_user":` since it's now the first branch.

Result should be:
```python
def get_messenger(account: MessengerAccount):
    """Factory: create messenger adapter based on account type."""
    if account.type == "tg_user":
        from app.config import Settings
        settings = Settings()
        return TelegramUserMessenger(
            session_string=account.credentials,
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
        )
    elif account.type == "wa":
        from app.config import Settings
        settings = Settings()
        return WhatsAppMessenger(bridge_url=settings.wa_bridge_url, session_id=str(account.id))
    else:
        raise ValueError(f"Unknown account type: {account.type}")
```

**Step 2: Commit**

```bash
git add app/worker/tasks.py
git commit -m "refactor: remove tg_bot from messenger factory"
```

---

### Task 3: Remove tg_bot routes from pages.py

**Files:**
- Modify: `app/routes/pages.py`

**Step 1: Edit app/routes/pages.py**

Remove the two route functions (lines 373-406):
- `accounts_connect_tg_bot_page` (GET /accounts/connect/tg_bot)
- `accounts_connect_tg_bot_submit` (POST /accounts/connect/tg_bot)

**Step 2: Commit**

```bash
git add app/routes/pages.py
git commit -m "refactor: remove tg_bot connection routes"
```

---

### Task 4: Update UI templates

**Files:**
- Modify: `app/templates/accounts/list.html`
- Modify: `app/templates/schedules/form.html`
- Modify: `app/templates/groups/list.html`

**Step 1: Edit app/templates/accounts/list.html**

Remove the "Подключить TG бота" button (line 7):
```html
        <a href="/accounts/connect/tg_bot" class="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500">Подключить TG бота</a>
```

Remove the `tg_bot` condition from the type display (line 30). Change:
```html
                    {% if account.type == 'tg_bot' %}Telegram бот
                    {% elif account.type == 'tg_user' %}Telegram аккаунт
```
To:
```html
                    {% if account.type == 'tg_user' %}Telegram аккаунт
```

**Step 2: Edit app/templates/schedules/form.html**

On line 30, change:
```
                    #{{ account.id }} - {% if account.type == 'tg_bot' %}Telegram бот{% elif account.type == 'tg_user' %}Telegram аккаунт{% elif account.type == 'wa' %}WhatsApp{% else %}{{ account.type }}{% endif %} ({{ account.status }})
```
To:
```
                    #{{ account.id }} - {% if account.type == 'tg_user' %}Telegram аккаунт{% elif account.type == 'wa' %}WhatsApp{% else %}{{ account.type }}{% endif %} ({{ account.status }})
```

**Step 3: Edit app/templates/groups/list.html**

On lines 45-46, change:
```html
                    {% if group.messenger_type == 'tg_bot' %}Telegram бот
                    {% elif group.messenger_type == 'tg_user' %}Telegram аккаунт
```
To:
```html
                    {% if group.messenger_type == 'tg_user' %}Telegram аккаунт
```

**Step 4: Commit**

```bash
git add app/templates/accounts/list.html app/templates/schedules/form.html app/templates/groups/list.html
git commit -m "refactor: remove tg_bot references from UI templates"
```

---

### Task 5: Update comments in models and routes

**Files:**
- Modify: `app/models/messenger_account.py:16`
- Modify: `app/routes/accounts.py:15`

**Step 1: Edit comments**

In `app/models/messenger_account.py` line 16, change:
```python
    type: Mapped[str] = mapped_column(String(20))  # tg_bot, tg_user, wa
```
To:
```python
    type: Mapped[str] = mapped_column(String(20))  # tg_user, wa
```

In `app/routes/accounts.py` line 15, change:
```python
    type: str  # tg_bot, tg_user, wa
```
To:
```python
    type: str  # tg_user, wa
```

**Step 2: Commit**

```bash
git add app/models/messenger_account.py app/routes/accounts.py
git commit -m "docs: update type comments to remove tg_bot"
```

---

### Task 6: Update tests — replace tg_bot with tg_user

Many tests use `tg_bot` as a convenient account type for creating test data. These need to be changed to `tg_user`. The tests don't actually exercise the bot adapter — they mock `get_messenger` — so changing the type string is sufficient.

**Files:**
- Modify: `tests/test_worker/test_tasks.py`
- Modify: `tests/test_routes/test_accounts.py`
- Modify: `tests/test_routes/test_groups.py`
- Modify: `tests/test_routes/test_schedules.py`
- Modify: `tests/test_routes/test_history.py`
- Modify: `tests/test_routes/test_limits.py`
- Modify: `tests/test_routes/test_sync_groups.py`
- Modify: `tests/test_models/test_messenger_account.py`
- Modify: `tests/test_models/test_group.py`
- Modify: `tests/test_models/test_schedule.py`
- Modify: `tests/test_models/test_send_log.py`
- Modify: `tests/test_e2e.py`

**Step 1: Update tests/test_worker/test_tasks.py**

In `create_test_data` (line 37), change `type="tg_bot"` to `type="tg_user"`.

Delete the `test_get_messenger_tg_bot` test function entirely (lines 64-70):
```python
@pytest.mark.asyncio
async def test_get_messenger_tg_bot():
    account = MessengerAccount(type="tg_bot", credentials="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
                               user_id=1, status="active")
    m = get_messenger(account)
    from app.messengers.telegram_bot import TelegramBotMessenger
    assert isinstance(m, TelegramBotMessenger)
```

**Step 2: Update tests/test_routes/test_accounts.py**

Replace all `"tg_bot"` with `"tg_user"` in the file:
- Line 7: `"type": "tg_bot"` → `"type": "tg_user"`
- Line 12: `assert data["type"] == "tg_bot"` → `assert data["type"] == "tg_user"`
- Line 24: `"type": "tg_bot"` → `"type": "tg_user"`
- Line 36: `assert data[0]["type"] == "tg_bot"` → `assert data[0]["type"] == "tg_user"`
- Line 63: `"type": "tg_bot"` → `"type": "tg_user"`

**Step 3: Update tests/test_routes/test_groups.py**

In the `create_account` helper and all test functions, replace `"tg_bot"` with `"tg_user"`:
- Lines 7, 19, 27, 40, 46, 71, 102, 122: all `"tg_bot"` → `"tg_user"`

**Step 4: Update tests/test_routes/test_schedules.py**

In `setup_ad_and_account` (line 13), change `"tg_bot"` to `"tg_user"`.

**Step 5: Update tests/test_routes/test_history.py**

In `setup_dependencies` (lines 18, 25), change `"tg_bot"` to `"tg_user"`.

**Step 6: Update tests/test_routes/test_limits.py**

Line 25: change `"tg_bot"` to `"tg_user"`.

**Step 7: Update tests/test_routes/test_sync_groups.py**

Delete the entire `test_sync_groups_wrong_account_type_redirects` test (lines 272-299). This test specifically validated that tg_bot accounts are rejected for group sync, which is no longer relevant.

**Step 8: Update tests/test_models/test_messenger_account.py**

Lines 19, 30: change `"tg_bot"` to `"tg_user"`.

**Step 9: Update tests/test_models/test_group.py**

Lines 20, 30, 42: change `"tg_bot"` to `"tg_user"`.

**Step 10: Update tests/test_models/test_schedule.py**

Lines 23, 78: change `"tg_bot"` to `"tg_user"`.

**Step 11: Update tests/test_models/test_send_log.py**

Lines 24, 43, 96, 115: change `"tg_bot"` to `"tg_user"`.

**Step 12: Update tests/test_e2e.py**

Line 77: change `"tg_bot"` to `"tg_user"`.

**Step 13: Run all tests**

```bash
uv run pytest tests/ -v
```

Expected: ALL PASS. No references to `tg_bot` remain.

**Step 14: Commit**

```bash
git add tests/
git commit -m "test: replace tg_bot with tg_user in all tests"
```

---

### Task 7: Remove aiogram dependency

**Files:**
- Modify: `pyproject.toml`

**Step 1: Remove aiogram**

```bash
uv remove aiogram
```

**Step 2: Run tests to verify nothing breaks**

```bash
uv run pytest tests/ -v
```

Expected: ALL PASS.

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: remove aiogram dependency"
```

---

### Task 8: Create Alembic data migration

**Files:**
- Create: `alembic/versions/XXXX_remove_tg_bot_accounts.py`

**Step 1: Create data-only migration**

```bash
uv run alembic revision -m "remove tg_bot accounts"
```

**Step 2: Edit the generated migration file**

```python
"""remove tg_bot accounts

Revision ID: <auto>
"""
from alembic import op

# revision identifiers
revision = "<auto>"
down_revision = "<auto>"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DELETE FROM messenger_accounts WHERE type = 'tg_bot'")


def downgrade() -> None:
    pass  # Cannot restore deleted data
```

**Step 3: Commit**

```bash
git add alembic/
git commit -m "migration: delete existing tg_bot accounts from database"
```

---

### Task 9: Final verification

**Step 1: Grep for any remaining tg_bot references**

```bash
grep -r "tg_bot" --include="*.py" --include="*.html" app/ tests/
```

Expected: No matches.

**Step 2: Grep for aiogram references**

```bash
grep -r "aiogram" --include="*.py" app/ tests/
```

Expected: No matches.

**Step 3: Run full test suite**

```bash
uv run pytest tests/ -v
```

Expected: ALL PASS.

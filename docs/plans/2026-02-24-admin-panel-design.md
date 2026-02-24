# Admin Panel Design

## Context

Broadcaster needs an admin who can manage user tariffs, view statistics, block/delete users. Currently there are no admin features, no roles, and no way to assign plans (all users are on "free").

## Decisions

- **Admin identification**: Single superadmin via `ADMIN_EMAIL` env var (compared at runtime, no DB migration for roles)
- **Scope**: Full management — tariffs, stats, block/delete users, view user data
- **UI**: Menu item visible only to admin, pages at `/admin/*`, same Tailwind+HTMX style

## Architecture

### Config

Add `admin_email: str = ""` to `app/config.py` Settings.

### Auth/Dependency

New `require_admin(request, db, settings)` dependency:
- Extracts user from cookie/token
- Compares `user.email == settings.admin_email`
- Raises `ForbiddenError` if not admin

### User Model Change

Add `is_blocked: bool = False` field. Alembic migration. Check in auth flow — blocked users cannot log in.

### Routes (`app/pages/admin.py`)

| Route | Method | Description |
|-------|--------|-------------|
| `/admin` | GET | Dashboard: user count, accounts, sends today |
| `/admin/users` | GET | Users table with search |
| `/admin/users/{id}` | GET | User detail card |
| `/admin/users/{id}/plan` | POST | Set tariff plan + expiration |
| `/admin/users/{id}/block` | POST | Toggle block/unblock |
| `/admin/users/{id}/delete` | POST | Delete user |

### Templates (`app/templates/admin/`)

- `dashboard.html` — stat cards (users, accounts, sends today, active subscriptions)
- `users.html` — table: email, name, plan, registered, status
- `user_detail.html` — info + plan form (select + expires_at) + block/delete buttons + user's objects (accounts, ads, groups)

### Navigation

`base.html` — add "Admin" menu item, visible only when `is_admin` is true in template context.

### Repository

Extend `UserRepository`: `get_all_users()`, `search_users(query)`.
Add `set_user_plan(user_id, plan, expires_at)` to billing service or subscription repo.

### Blocked User Enforcement

In `get_current_user_id` dependency or `get_user_from_cookie`: if user `is_blocked`, raise 403 / redirect to login with error message.

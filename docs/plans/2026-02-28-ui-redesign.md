# UI Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete rewrite of all 41 Jinja2 templates with Linear-inspired light minimalist design, sidebar navigation on desktop, bottom tab bar on mobile.

**Architecture:** Server-rendered Jinja2 templates with Tailwind CSS (CDN v3), HTMX for dynamic content, Alpine.js for client-side state. No backend changes needed — only templates are rewritten. All template variables, HTMX endpoints, and form actions remain identical.

**Tech Stack:** Tailwind CSS v3 (CDN), HTMX 1.9.10, Alpine.js 3.13.3, Inter font, Heroicons (inline SVG)

---

## Design System Reference

### Colors
- Page bg: `bg-gray-50` (#f9fafb)
- Cards/sidebar: `bg-white`
- Text: `text-gray-900` (primary), `text-gray-600` (secondary), `text-gray-400` (muted)
- Accent: `indigo-600` (buttons/links), `indigo-50` (hover bg)
- Borders: `border-gray-200`
- Status: green (`emerald-700`/`emerald-50`), red (`red-700`/`red-50`), amber (`amber-700`/`amber-50`), gray (`gray-600`/`gray-100`)

### Typography
- Page title: `text-lg font-semibold text-gray-900`
- Section: `text-xs font-medium text-gray-500 uppercase tracking-wider`
- Body: `text-sm text-gray-700`
- Meta: `text-xs text-gray-500`

### Components
- Primary btn: `bg-indigo-600 text-white rounded-lg px-3.5 py-2 text-sm font-medium hover:bg-indigo-700 transition-colors`
- Secondary btn: `bg-white border border-gray-300 text-gray-700 rounded-lg px-3.5 py-2 text-sm font-medium hover:bg-gray-50 transition-colors`
- Ghost btn: `text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg px-2 py-1.5 text-sm transition-colors`
- Danger btn: `text-red-600 hover:bg-red-50 rounded-lg px-2 py-1.5 text-sm transition-colors`
- Card: `bg-white rounded-lg border border-gray-200`
- Input: `w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none transition-colors`
- Badge: `inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium`
- Table row hover: `hover:bg-gray-50 transition-colors`

---

## Task 1: Base Template — Sidebar Layout

**Files:**
- Rewrite: `app/templates/base.html`

**What to build:**

The base template defines the entire app shell. Desktop gets a fixed sidebar (240px) on the left. Mobile gets a thin top header + fixed bottom tab bar.

**Step 1: Rewrite `app/templates/base.html`**

Structure:
```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="theme-color" content="#4f46e5">
  <title>{% block title %}Broadcaster{% endblock %}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
        }
      }
    }
  </script>
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.3/dist/cdn.min.js"></script>
  <style>[x-cloak]{display:none!important}</style>
</head>
<body class="font-sans bg-gray-50 text-gray-900 antialiased">
  {% block body %}

  <!-- MOBILE: Top header (lg:hidden) -->
  <header class="lg:hidden fixed top-0 inset-x-0 z-40 bg-white border-b border-gray-200 h-14" x-data="{ menuOpen: false }">
    <div class="flex items-center justify-between h-full px-4">
      <!-- Hamburger (opens slide-over for secondary nav) -->
      <button @click="menuOpen = true" class="p-2 -ml-2 text-gray-500 hover:text-gray-700">
        {% from "includes/icons.html" import icon_menu %}
        {{ icon_menu('h-6 w-6') }}
      </button>
      <a href="/dashboard" class="text-base font-semibold text-gray-900">Broadcaster</a>
      <!-- User avatar -->
      <a href="/profile" class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-sm font-medium text-indigo-700">
        {{ user.name[0]|upper if user and user.name else '?' }}
      </a>
    </div>

    <!-- Mobile slide-over menu (for secondary nav items) -->
    <div x-show="menuOpen" x-cloak class="fixed inset-0 z-50" @click.self="menuOpen = false">
      <div class="fixed inset-0 bg-black/20" x-show="menuOpen" x-transition:enter="transition-opacity duration-200" x-transition:leave="transition-opacity duration-200"></div>
      <div class="fixed inset-y-0 left-0 w-72 bg-white shadow-xl" x-show="menuOpen" x-transition:enter="transition-transform duration-200" x-transition:enter-start="-translate-x-full" x-transition:enter-end="translate-x-0" x-transition:leave="transition-transform duration-200" x-transition:leave-start="translate-x-0" x-transition:leave-end="-translate-x-full">
        <div class="flex items-center justify-between h-14 px-4 border-b border-gray-200">
          <span class="text-base font-semibold text-gray-900">Broadcaster</span>
          <button @click="menuOpen = false" class="p-2 text-gray-400 hover:text-gray-600">
            {% from "includes/icons.html" import icon_close %}
            {{ icon_close('h-5 w-5') }}
          </button>
        </div>
        <nav class="px-3 py-4 space-y-1">
          <!-- All nav items in slide-over -->
          <a href="/dashboard" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium {{ 'bg-gray-100 text-gray-900' if active_page == 'dashboard' else 'text-gray-600 hover:bg-gray-50 hover:text-gray-900' }}">Панель</a>
          <a href="/ads" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium {{ 'bg-gray-100 text-gray-900' if active_page == 'ads' else 'text-gray-600 hover:bg-gray-50 hover:text-gray-900' }}">Объявления</a>
          <a href="/accounts" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium {{ 'bg-gray-100 text-gray-900' if active_page == 'accounts' else 'text-gray-600 hover:bg-gray-50 hover:text-gray-900' }}">Аккаунты</a>
          <a href="/groups" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium {{ 'bg-gray-100 text-gray-900' if active_page == 'groups' else 'text-gray-600 hover:bg-gray-50 hover:text-gray-900' }}">Группы</a>
          <a href="/schedules" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium {{ 'bg-gray-100 text-gray-900' if active_page == 'schedules' else 'text-gray-600 hover:bg-gray-50 hover:text-gray-900' }}">Расписания</a>
          <a href="/history" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium {{ 'bg-gray-100 text-gray-900' if active_page == 'history' else 'text-gray-600 hover:bg-gray-50 hover:text-gray-900' }}">История</a>
          <a href="/billing" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium {{ 'bg-gray-100 text-gray-900' if active_page == 'billing' else 'text-gray-600 hover:bg-gray-50 hover:text-gray-900' }}">Тарифы</a>
          {% if is_admin %}
          <a href="/admin" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium {{ 'bg-gray-100 text-gray-900' if active_page == 'admin' else 'text-gray-600 hover:bg-gray-50 hover:text-gray-900' }}">Админ</a>
          {% endif %}
          <div class="border-t border-gray-200 my-3"></div>
          <a href="/profile" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50">Профиль</a>
          <a href="/logout" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50">Выйти</a>
        </nav>
      </div>
    </div>
  </header>

  <!-- MOBILE: Bottom tab bar (lg:hidden) -->
  <nav class="lg:hidden fixed bottom-0 inset-x-0 z-40 bg-white border-t border-gray-200">
    <div class="flex items-center justify-around h-14">
      <a href="/dashboard" class="flex flex-col items-center justify-center flex-1 h-full text-xs {{ 'text-indigo-600 font-medium' if active_page == 'dashboard' else 'text-gray-500' }}">
        <!-- Dashboard icon SVG inline -->
        <svg class="h-5 w-5 mb-0.5" ...>...</svg>
        <span>Панель</span>
      </a>
      <a href="/ads" class="...">Объявл.</a>
      <a href="/groups" class="...">Группы</a>
      <a href="/schedules" class="...">Распис.</a>
      <a href="/history" class="...">История</a>
    </div>
  </nav>

  <!-- DESKTOP: Fixed sidebar (hidden on mobile) -->
  <aside class="hidden lg:flex lg:flex-col lg:fixed lg:inset-y-0 lg:left-0 lg:w-60 lg:bg-white lg:border-r lg:border-gray-200 lg:z-30">
    <!-- Logo -->
    <div class="flex items-center h-14 px-5 border-b border-gray-200 shrink-0">
      <a href="/dashboard" class="text-base font-semibold text-gray-900">Broadcaster</a>
    </div>
    <!-- Nav links -->
    <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
      <!-- Each link: icon + label, active state with bg-gray-100 -->
      <a href="/dashboard" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium {{ 'bg-gray-100 text-gray-900' if active_page == 'dashboard' else 'text-gray-600 hover:bg-gray-50 hover:text-gray-900' }} transition-colors">
        <!-- SVG icon inline -->
        Панель
      </a>
      <!-- repeat for: Объявления, Аккаунты, Группы, Расписания, История, Тарифы, [Админ] -->
    </nav>
    <!-- User section at bottom -->
    <div class="border-t border-gray-200 px-3 py-3 shrink-0">
      <div class="flex items-center gap-3 px-3 py-2">
        <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-sm font-medium text-indigo-700">
          {{ user.name[0]|upper if user and user.name else '?' }}
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-gray-900 truncate">{{ user.name }}</p>
        </div>
      </div>
      <a href="/profile" class="flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors">Профиль</a>
      <a href="/logout" class="flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm text-red-600 hover:bg-red-50 transition-colors">Выйти</a>
    </div>
  </aside>

  <!-- Main content area -->
  <main class="lg:ml-60 pt-14 pb-16 lg:pt-0 lg:pb-0 min-h-screen">
    <div class="px-4 py-5 lg:px-8 lg:py-6">
      {% block content %}{% endblock %}
    </div>
  </main>

  {% endblock %}
</body>
</html>
```

Key details:
- `pt-14` on mobile for fixed header (h-14), `pb-16` for bottom bar
- `lg:ml-60` pushes content right on desktop (sidebar width)
- `lg:pt-0 lg:pb-0` removes mobile padding on desktop
- Sidebar nav icons should be simple outline SVGs (Heroicons) — 7 nav items + conditional Admin
- Bottom tab bar: 5 items (Dashboard, Ads, Groups, Schedules, History)
- Slide-over menu: all nav items + Profile + Logout
- Remove old Tailwind custom theme (primary-*, surface-*) — use standard gray/indigo

**Step 2: Verify base renders**

Run: `just run` and open browser. Every page should show sidebar on desktop, bottom bar on mobile.

**Step 3: Commit**
```bash
git add app/templates/base.html
git commit -m "feat: redesign base template with sidebar layout"
```

---

## Task 2: Shared Includes — Icons & Messenger Icon

**Files:**
- Rewrite: `app/templates/includes/icons.html`
- Rewrite: `app/templates/includes/messenger_icon.html`

**Step 1: Rewrite `app/templates/includes/icons.html`**

Keep all existing macros with same signatures. Update default sizes where needed. Add any new nav icons needed by the sidebar (home, megaphone, users, folder, calendar, clock, credit-card, shield). All icons remain Heroicons outline style 24x24 viewBox.

New macros to add:
- `icon_home(size='h-5 w-5')` — for Dashboard nav
- `icon_megaphone(size='h-5 w-5')` — for Ads nav
- `icon_user_group(size='h-5 w-5')` — for Accounts nav
- `icon_folder(size='h-5 w-5')` — for Groups nav
- `icon_calendar(size='h-5 w-5')` — for Schedules nav
- `icon_clock(size='h-5 w-5')` — for History nav
- `icon_credit_card(size='h-5 w-5')` — for Billing nav
- `icon_shield(size='h-5 w-5')` — for Admin nav
- `icon_user(size='h-5 w-5')` — for Profile nav
- `icon_logout(size='h-5 w-5')` — for Logout
- `icon_plus(size='h-5 w-5')` — for Create buttons
- `icon_search(size='h-5 w-5')` — for Search inputs
- `icon_chevron_right(size='h-4 w-4')` — for breadcrumbs/links

**Step 2: Rewrite `app/templates/includes/messenger_icon.html`**

Keep same `messenger_icon(messenger_type, size, title, show_label)` macro signature. Update styling to match new design system colors.

**Step 3: Verify icons render**

Run: `just run`, check sidebar icons and any page using messenger icons.

**Step 4: Commit**
```bash
git add app/templates/includes/
git commit -m "feat: update icon macros for new design system"
```

---

## Task 3: Auth Pages — Login & Register

**Files:**
- Rewrite: `app/templates/auth/login.html`
- Rewrite: `app/templates/auth/register.html`

**What to build:**

Auth pages override `{% block body %}` (not `content`) — they don't show sidebar/nav. Centered card on gray-50 background.

**Step 1: Rewrite `app/templates/auth/login.html`**

Layout:
```
┌─────────────────────────────────┐
│         bg-gray-50              │
│                                 │
│    ┌───────────────────────┐    │
│    │  Broadcaster (logo)   │    │
│    │                       │    │
│    │  Вход в аккаунт       │    │
│    │                       │    │
│    │  [Email           ]   │    │
│    │  [Password        ]   │    │
│    │                       │    │
│    │  [    Войти       ]   │    │
│    │                       │    │
│    │  Нет аккаунта?        │    │
│    │  Зарегистрироваться   │    │
│    └───────────────────────┘    │
│                                 │
└─────────────────────────────────┘
```

Key details:
- `{% block body %}` — NO sidebar, NO bottom bar
- Centered: `min-h-screen flex items-center justify-center bg-gray-50`
- Card: `bg-white rounded-xl border border-gray-200 p-8 w-full max-w-sm`
- Error message: `bg-red-50 text-red-700 text-sm rounded-lg px-4 py-3`
- Form action: POST `/login` with fields `email`, `password`
- Link to `/register`

**Step 2: Rewrite `app/templates/auth/register.html`**

Same layout, add `name` field. Form action POST `/register`. Link to `/login`.

**Step 3: Verify**

Open `/login` and `/register` in browser. Check mobile rendering.

**Step 4: Commit**
```bash
git add app/templates/auth/
git commit -m "feat: redesign auth pages with centered card layout"
```

---

## Task 4: Dashboard Page

**Files:**
- Rewrite: `app/templates/dashboard.html`
- Rewrite: `app/templates/dashboard/includes/recent_send_card.html`

**Step 1: Rewrite `app/templates/dashboard.html`**

Layout:
```
Page title: "Панель управления"

4 stat cards (grid-cols-2 lg:grid-cols-4, gap-4):
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ 12       │ │ 5        │ │ 48       │ │ 156      │
│ Объявл.  │ │ Аккаунты │ │ Группы   │ │ Отправл. │
└──────────┘ └──────────┘ └──────────┘ └──────────┘

Section: "Последние отправки"
Table with compact rows (or empty state)
```

Context variables used:
- `stats.active_ads`, `stats.active_accounts`, `stats.active_groups`, `stats.sent_today`
- `recent_sends` — list of SendLog dicts

Stat card: `bg-white rounded-lg border border-gray-200 p-5`
- Number: `text-2xl font-semibold text-gray-900`
- Label: `text-sm text-gray-500 mt-1`

**Step 2: Rewrite `app/templates/dashboard/includes/recent_send_card.html`**

Compact table row for each send log:
- Time: `text-xs text-gray-500` — `{{ format_datetime_for_user(log.sent_at, user, '%H:%M') }}`
- Ad title: `text-sm text-gray-900 font-medium truncate`
- Group: `text-sm text-gray-500`
- Messenger icon (small)
- Status badge: `ok` → green pill, `fail` → red pill, `account_disconnected` → amber pill
- Uses `{% from "includes/messenger_icon.html" import messenger_icon %}`

**Step 3: Verify, Step 4: Commit**
```bash
git add app/templates/dashboard.html app/templates/dashboard/
git commit -m "feat: redesign dashboard with stat cards and send log table"
```

---

## Task 5: Ads Pages

**Files:**
- Rewrite: `app/templates/ads/list.html`
- Rewrite: `app/templates/ads/includes/ad_card.html`
- Rewrite: `app/templates/ads/form.html`
- Rewrite: `app/templates/ads/partial_cards.html`
- Rewrite: `app/templates/ads/partial_rows.html`

**Step 1: Rewrite `app/templates/ads/list.html`**

Layout:
```
Header row: "Объявления" (left) + [+ Создать] button (right)

List of ad items (vertical stack, gap-3):
┌──────────────────────────────────────────────┐
│ [img]  Title                    Active  Edit▸│
│        Preview text...          12 sends     │
├──────────────────────────────────────────────┤
│ [img]  Title                    Paused  Edit▸│
│        Preview text...          5 sends      │
└──────────────────────────────────────────────┘

HTMX infinite scroll at bottom
```

Context: `ads`, `has_next`, `next_offset`
- Header: `flex items-center justify-between mb-6`
- Title: `text-lg font-semibold text-gray-900`
- Create button: Primary btn, links to `/ads/new`
- Ad items: `bg-white rounded-lg border border-gray-200` with `divide-y divide-gray-100`
- HTMX loader: `<div hx-get="/ads/partial?offset={{ next_offset }}&limit=30&layout=cards" hx-trigger="revealed" hx-swap="outerHTML">` (if `has_next`)

**Step 2: Rewrite `app/templates/ads/includes/ad_card.html`**

Each ad item is a horizontal row in the card container:
- Left: thumbnail image (48x48 rounded-lg, or placeholder bg-gray-100)
- Center: title (font-medium text-gray-900) + text preview (text-gray-500 truncate) + meta (sends count, schedules count)
- Right: status badge + action buttons (edit, delete)

If ad has images, show first image as thumbnail. Alpine.js carousel is removed for list view — only show on detail/form.

Variables: `ad.id`, `ad.title`, `ad.text`, `ad.images`, `ad.is_active`, `ad.created_at`, `ad.sends_count`, `ad.schedules_count`

Delete: `<form method="post" action="/ads/{{ ad.id }}/delete" onsubmit="return confirm('Удалить объявление?')"><button type="submit" class="danger btn">delete icon</button></form>`

**Step 3: Rewrite `app/templates/ads/form.html`**

Centered form, `max-w-2xl mx-auto`:
```
Title: "Создать объявление" or "Редактировать объявление"

┌────────────────────────────────────────┐
│ Заголовок                              │
│ [________________________]             │
│                                        │
│ Текст                                  │
│ [________________________]             │
│ [________________________]             │
│ [________________________]             │
│                                        │
│ Изображения                            │
│ ┌─────────────────────────────────┐    │
│ │  Drop zone / Click to upload    │    │
│ └─────────────────────────────────┘    │
│ [img1] [img2] [img3]                   │
│                                        │
│ ☐ Активно (edit mode only)             │
│                                        │
│ [Отмена]                    [Сохранить]│
└────────────────────────────────────────┘
```

Form actions:
- Create: POST `/ads/new`
- Edit: POST `/ads/{{ ad.id }}/edit`
- Cancel: link to `/ads`

Image upload JS: keep existing logic, just update styling:
- Upload endpoint: `/api/uploads/image` (POST FormData)
- Uses `IMAGE_BASE_URL` for S3 URLs
- Max 10 images
- Drag-and-drop zone with dashed border
- Image previews in grid with remove buttons

IMPORTANT: Keep all existing JavaScript for image management — only update HTML/CSS classes.

Fields: `title` (required), `text` (textarea, required), `images` (hidden inputs), `is_active` (checkbox, edit only)

**Step 4: Rewrite `app/templates/ads/partial_cards.html`**

```html
{% from "ads/includes/ad_card.html" import ad_card %}
{% for ad in ads %}
{{ ad_card(ad, user) }}
{% endfor %}
{% if has_next %}
<div hx-get="/ads/partial?offset={{ next_offset }}&limit=30&layout=cards" hx-trigger="revealed" hx-swap="outerHTML"></div>
{% endif %}
```

**Step 5: Rewrite `app/templates/ads/partial_rows.html`**

Same structure but for `layout=rows` (table rows format).

**Step 6: Verify, Step 7: Commit**
```bash
git add app/templates/ads/
git commit -m "feat: redesign ads pages with clean card list and form"
```

---

## Task 6: Accounts Pages

**Files:**
- Rewrite: `app/templates/accounts/list.html`
- Rewrite: `app/templates/accounts/partial_cards.html`
- Rewrite: `app/templates/accounts/partial_rows.html`
- Rewrite: `app/templates/accounts/partials/sync_status_card.html`
- Rewrite: `app/templates/accounts/partials/sync_status_row.html`
- Rewrite: `app/templates/accounts/connect_tg_user.html`
- Rewrite: `app/templates/accounts/connect_wa.html`

**Step 1: Rewrite `app/templates/accounts/list.html`**

Layout:
```
Header: "Аккаунты" + [Подключить TG] [Подключить WA] buttons

Account cards (grid-cols-1 sm:grid-cols-2 lg:grid-cols-3, gap-4):
┌──────────────────────┐
│ 📱 Telegram          │
│ account_name         │
│ ● Активен            │
│                      │
│ Групп: 12            │
│ Расписаний: 3        │
│ Отправлено: 89%      │
│                      │
│ [Удалить]            │
└──────────────────────┘
```

Context: `accounts`, `account_stats`, `has_next`, `next_offset`

Each account card: `bg-white rounded-lg border border-gray-200 p-5`
- Messenger icon + type label at top
- Status badge below name
- Stats section: groups_count, schedules_count, success rate (send_success/send_attempts)
- Last sent timestamp
- Delete button (danger ghost)

Account states:
- `status == 'active'`: green badge "Активен"
- `status == 'syncing'`: amber badge "Синхронизация..." + spinner, HTMX poll `every 5s`
- `status == 'sync_failed'`: red badge "Ошибка синхронизации" + retry button
- `status == 'connecting'`: amber badge "Подключение..."
- `status == 'disconnected'`: gray badge "Отключён"

HTMX infinite scroll endpoint: `/accounts/partial?offset=...&limit=30&layout=cards`

**Step 2: Rewrite sync status partials**

`sync_status_card.html` — full card replacement for HTMX polling:
- If `status == 'syncing'`: show spinner + "Синхронизация..." + `hx-get="/accounts/{{ account_id }}/sync-status?layout=cards" hx-trigger="every 5s" hx-swap="outerHTML"`
- If `status == 'active'`: show full stats card (no more polling)
- If `status == 'sync_failed'`: show error + retry button

`sync_status_row.html` — same but for table row layout

**Step 3: Rewrite `app/templates/accounts/connect_tg_user.html`**

Centered card with state machine sections:

Sections (managed by vanilla JS, shown/hidden):
1. `start-section`: "Подключение Telegram" + [Начать] button
2. `qr-section`: QR code image + status text + [Обновить QR] button + polling
3. `2fa-section`: 2FA password input + [Подтвердить] button
4. `success-section`: checkmark + "Подключено!" + [К аккаунтам] link

IMPORTANT: Keep ALL existing JavaScript logic for API calls. Only update HTML structure and CSS classes.

API endpoints (keep as-is):
- POST `/accounts/connect/tg_user/start-qr`
- GET `/accounts/connect/tg_user/qr-status?session_id={id}`
- POST `/accounts/connect/tg_user/refresh-qr`
- POST `/accounts/connect/tg_user/verify-2fa`
- POST `/accounts/connect/tg_user/complete`

**Step 4: Rewrite `app/templates/accounts/connect_wa.html`**

Centered card:
- QR code display (if `qr_code` provided)
- HTMX polling: `hx-get="/accounts/connect/wa/status" hx-trigger="every 3s" hx-swap="innerHTML"` on status container
- Success state
- Error display

Keep existing HTMX patterns.

**Step 5: Rewrite partial_cards.html and partial_rows.html**

HTMX infinite scroll partials for accounts list.

**Step 6: Verify, Step 7: Commit**
```bash
git add app/templates/accounts/
git commit -m "feat: redesign accounts pages with card grid layout"
```

---

## Task 7: Groups Page

**Files:**
- Rewrite: `app/templates/groups/list.html`
- Rewrite: `app/templates/groups/partial_cards.html`
- Rewrite: `app/templates/groups/partial_rows.html`

**Step 1: Rewrite `app/templates/groups/list.html`**

Layout:
```
Header: "Группы" + sync buttons per account (secondary btns)

Filter bar (inline on desktop, collapsible on mobile):
┌──────────────────────────────────────────────────┐
│ [Account ▼] [Messenger ▼] [Status ▼] [Search__] │
└──────────────────────────────────────────────────┘

Bulk actions (shown when items selected):
┌──────────────────────────────────────────────────┐
│ ☐ Выбрать все    [Деактивировать] [Удалить]      │
└──────────────────────────────────────────────────┘

Group list (table-like rows on desktop, cards on mobile):
┌──────────────────────────────────────────────────┐
│ ☐  Group Name         📱TG   Active   3 sched ▸ │
│ ☐  Another Group      📱WA   Active   1 sched ▸ │
│ ☐  Error Group        📱TG   Error    0 sched ▸ │
└──────────────────────────────────────────────────┘
```

Context: `groups`, `group_stats`, `accounts_by_id`, `tg_user_accounts`, `wa_accounts`, `all_accounts`, `has_next`, `next_offset`, filter params

Filter form: GET `/groups` with params `account_id`, `messenger_type`, `is_active`, `search`
- Alpine.js: `filterOpen` state for mobile toggle
- Each filter: select or text input with gray-300 border
- Filter button on mobile: icon_filter

Sync buttons: one POST form per account type
- `<form method="post" action="/accounts/{{ acc.id }}/sync-groups">` for each TG/WA account
- Secondary buttons

Bulk actions:
- Keep existing JavaScript: `selectAllGroups()`, `submitBulkGroups(action)`
- Form POST `/groups/bulk` with `action` and `group_ids[]`

Each group row:
- Checkbox (left)
- Group name (font-medium)
- Messenger icon (small)
- Status badge (active/paused/error)
- Stats: schedules_count, send success rate, last_sent_at
- Error message if `group.last_error`
- Action buttons: pause/play toggle, delete

HTMX infinite scroll: preserves filter params in URL

**Step 2: Rewrite partial_cards.html and partial_rows.html**

Partials with same variables + HTMX loader.

**Step 3: Verify, Step 4: Commit**
```bash
git add app/templates/groups/
git commit -m "feat: redesign groups page with filters and bulk actions"
```

---

## Task 8: Schedules Pages

**Files:**
- Rewrite: `app/templates/schedules/list.html`
- Rewrite: `app/templates/schedules/form.html`
- Rewrite: `app/templates/schedules/partial_cards.html`
- Rewrite: `app/templates/schedules/partial_rows.html`

**Step 1: Rewrite `app/templates/schedules/list.html`**

Layout:
```
Header: "Расписания" + [+ Создать] button

Schedule cards (max-w-3xl mx-auto, gap-3):
┌────────────────────────────────────────────┐
│ Ad Title                          Active   │
│ 📱 Telegram · 5 групп                     │
│ Пн Вт Ср Чт Пт · 09:00, 14:00, 18:00     │
│ Следующий запуск: 28.02 09:00 (MSK)       │
│                                            │
│ [Пауза]  [Редактировать]  [Удалить]       │
└────────────────────────────────────────────┘
```

Context: `schedules` (list of dicts with `schedule`, `ad_title`, `messenger_type`, `next_run_local`, `tz_label`), `has_next`, `next_offset`

Day names map: `{0: 'Пн', 1: 'Вт', 2: 'Ср', 3: 'Чт', 4: 'Пт', 5: 'Сб', 6: 'Вс'}`

Each schedule card:
- Top: ad_title (font-medium) + status badge
- Middle: messenger icon + group count + days + times
- Bottom: next_run_local display + action buttons
- Actions: pause/resume toggle (POST), edit (link), delete (POST with confirm)

**Step 2: Rewrite `app/templates/schedules/form.html`**

Centered form, `max-w-2xl mx-auto`:
```
Title: "Создать расписание" or "Редактировать расписание"

┌────────────────────────────────────────┐
│ Объявление                             │
│ [Select ad ▼            ]              │
│                                        │
│ Аккаунт                               │
│ [Select account ▼       ]              │
│                                        │
│ Группы                                 │
│ [Выбрать все] [Снять все]              │
│ ┌──────────────────────────────┐       │
│ │ ☐ Group 1                   │       │
│ │ ☐ Group 2                   │       │
│ │ ☐ Group 3 (filtered by acc) │       │
│ └──────────────────────────────┘       │
│                                        │
│ Дни недели                             │
│ [Все] [Снять]                          │
│ ☐Пн ☐Вт ☐Ср ☐Чт ☐Пт ☐Сб ☐Вс        │
│                                        │
│ Время отправки                         │
│ [09:00] [×]                            │
│ [14:00] [×]                            │
│ [+ Добавить время]                     │
│                                        │
│ Часовой пояс                           │
│ [Select timezone ▼      ]              │
│                                        │
│ [Отмена]                    [Сохранить]│
└────────────────────────────────────────┘
```

Context: `schedule` (or None), `ads`, `accounts`, `groups`, `timezone_choices`, `default_timezone`

Form actions:
- Create: POST `/schedules/new`
- Edit: POST `/schedules/{{ schedule.id }}/edit`

IMPORTANT: Keep ALL existing JavaScript:
- `filterGroupsByAccount()` — shows/hides groups based on selected account
- `selectAllGroups()`, `deselectAllGroups()`
- `selectAllDays()`, `deselectAllDays()`
- `addTimeInput()` — dynamic time field addition
- Event listeners on `account_id` change

Groups container: `max-h-60 overflow-y-auto border border-gray-200 rounded-lg p-3`
- Each group: checkbox with `data-account-id` and `data-messenger-type` attributes
- Only show groups matching selected account

Days: inline flex of 7 checkboxes with labels

Times: dynamic list of time inputs + add button + remove button per item

**Step 3: Rewrite partial_cards.html and partial_rows.html**

**Step 4: Verify, Step 5: Commit**
```bash
git add app/templates/schedules/
git commit -m "feat: redesign schedules pages with clean form and card list"
```

---

## Task 9: History Pages

**Files:**
- Rewrite: `app/templates/history/list.html`
- Rewrite: `app/templates/history/includes/history_card.html`
- Rewrite: `app/templates/history/detail.html`
- Rewrite: `app/templates/history/partial_cards.html`
- Rewrite: `app/templates/history/partial_rows.html`

**Step 1: Rewrite `app/templates/history/list.html`**

Layout:
```
Header: "История отправок"

Filter bar (inline desktop, collapsible mobile):
[Status ▼] [Messenger ▼] [Account ▼] [Period ▼]

History items (list):
┌────────────────────────────────────────────┐
│ 14:30 28.02  Ad Title                  ✓   │
│              → Group Name  📱TG            │
├────────────────────────────────────────────┤
│ 14:25 28.02  Ad Title                  ✗   │
│              → Group Name  📱WA   error... │
└────────────────────────────────────────────┘

HTMX infinite scroll
```

Context: `logs`, `all_accounts`, filter params, `has_next`, `next_offset`

Filter form: GET `/history` with `status`, `messenger`, `account_id`, `period`
- Status: Все / Успешные / Ошибки
- Messenger: Все / Telegram / WhatsApp
- Account: Все / per-account options
- Period: 7 дней / 30 дней / Все

Alpine.js: `filterOpen` for mobile

HTMX infinite scroll: `/history/partial?offset=...&layout=cards&status=...&messenger=...&account_id=...&period=...`

**Step 2: Rewrite `app/templates/history/includes/history_card.html`**

Each history item as a compact row in a bordered container:
- Timestamp (left, gray-500)
- Ad title (font-medium) + arrow + group name
- Messenger icon (small)
- Status: green check or red X badge
- Error message line (if fail, text-red-600 text-xs)
- Link to detail: `/history/{{ log.id }}`

Remove Avito-style image carousel from list view — keep it simple. Images shown only on detail page.

**Step 3: Rewrite `app/templates/history/detail.html`**

```
← Назад к истории

┌────────────────────────────────────────────┐
│ Детали отправки                            │
│                                            │
│ Статус:      ● Успешно / ✗ Ошибка          │
│ Время:       28.02.2026, 14:30             │
│ Мессенджер:  📱 Telegram                   │
│ ID задачи:   abc-123                       │
│ Группа:      Group Name                    │
│ Ошибка:      error text (if any)           │
│                                            │
│ ──────────────────────────────             │
│                                            │
│ Объявление                                 │
│ Title                                      │
│ Text content...                            │
│                                            │
│ [img1] [img2] [img3]  (image grid)         │
└────────────────────────────────────────────┘
```

Context: `log`, `group`

Back link: `/history`
Detail card: key-value pairs in grid layout
Ad section: title + text + image grid (if images)

**Step 4: Rewrite partial_cards.html and partial_rows.html**

**Step 5: Verify, Step 6: Commit**
```bash
git add app/templates/history/
git commit -m "feat: redesign history pages with compact list and detail view"
```

---

## Task 10: Billing Page

**Files:**
- Rewrite: `app/templates/billing/plans.html`

**Step 1: Rewrite `app/templates/billing/plans.html`**

Layout:
```
Header: "Тарифы"

Current plan section:
┌────────────────────────────────────────────┐
│ Текущий тариф: Free                       │
│                                            │
│ Объявления    ████████░░  8/10             │
│ Группы        ██░░░░░░░░  12/100           │
│ Отправок/день ████░░░░░░  40/100           │
└────────────────────────────────────────────┘

Available plans (grid-cols-1 md:grid-cols-3):
┌─────────┐  ┌─────────┐  ┌─────────┐
│  Free   │  │  Basic  │  │   Pro   │
│         │  │         │  │         │
│ 10 ads  │  │ 50 ads  │  │ ∞ ads   │
│ 100 grp │  │ 500 grp │  │ ∞ grps  │
│ 100/day │  │ 500/day │  │ ∞/day   │
│         │  │         │  │         │
│[Current]│  │ [-----] │  │ [-----] │
└─────────┘  └─────────┘  └─────────┘
```

Context: `plan`, `limits`, `usage`, `all_plans`

Progress bars: `bg-gray-200 rounded-full h-2` + inner `bg-indigo-600 rounded-full h-2`
- Calculate percentage: `min(usage.X / limits.X * 100, 100)`
- Show count: `{{ usage.X }} / {{ limits.X }}`

Plan cards: `bg-white rounded-lg border border-gray-200 p-6`
- Current plan: `border-indigo-600 ring-1 ring-indigo-600`
- Plan name at top (font-semibold)
- Feature list below
- "Текущий" badge or empty space

**Step 2: Verify, Step 3: Commit**
```bash
git add app/templates/billing/
git commit -m "feat: redesign billing page with progress bars and plan cards"
```

---

## Task 11: Profile Page

**Files:**
- Rewrite: `app/templates/profile.html`

**Step 1: Rewrite `app/templates/profile.html`**

Layout:
```
Header: "Профиль"

┌────────────────────────────────────────────┐
│ Часовой пояс                               │
│ [Select timezone ▼                    ]    │
│                                            │
│ [Сохранить]                                │
└────────────────────────────────────────────┘
```

Context: `timezone_choices`, `error`

Form: POST `/profile` with `timezone` select
- Centered card, `max-w-lg mx-auto`
- Error message if `error`

**Step 2: Verify, Step 3: Commit**
```bash
git add app/templates/profile.html
git commit -m "feat: redesign profile page"
```

---

## Task 12: Admin Pages

**Files:**
- Rewrite: `app/templates/admin/dashboard.html`
- Rewrite: `app/templates/admin/users.html`
- Rewrite: `app/templates/admin/user_detail.html`
- Rewrite: `app/templates/admin/user_history.html`
- Rewrite: `app/templates/admin/user_history_detail.html`
- Rewrite: `app/templates/admin/history_partial_cards.html`

**Step 1: Rewrite `app/templates/admin/dashboard.html`**

Same pattern as dashboard.html:
- Stat cards: `total_users`, `total_accounts`, `active_accounts`, `sends_today`
- Link to user management: `/admin/users`

**Step 2: Rewrite `app/templates/admin/users.html`**

```
Header: "Пользователи" + Search input

┌────────────────────────────────────────────┐
│ User Name        user@email.com   Free   ▸│
│ User Name 2      user2@email.com  Pro    ▸│
└────────────────────────────────────────────┘
```

Context: `users` (list of dicts with `user`, `plan`), `search_query`

Search form: GET `/admin/users?q=...`
User rows: name, email, plan badge, link to detail

**Step 3: Rewrite `app/templates/admin/user_detail.html`**

Sections:
1. User info (name, email, created_at, status)
2. Usage stats (ads_count, groups_count, sends)
3. Accounts list
4. Plan management form
5. Admin actions (block/unblock, delete)

Context: `target_user`, `plan`, `usage`, `accounts`, `ads_count`, `groups_count`, `active_sub`, `all_plans`

Forms:
- POST `/admin/users/{{ target_user.id }}/plan` — plan select + expires_days
- POST `/admin/users/{{ target_user.id }}/block` — toggle block
- POST `/admin/users/{{ target_user.id }}/delete` — delete with confirm

**Step 4: Rewrite `app/templates/admin/user_history.html`**

Same as history/list.html but:
- Back link to `/admin/users/{{ target_user.id }}`
- Detail links go to `/admin/users/{{ target_user.id }}/history/{{ log.id }}`
- HTMX endpoint: `/admin/users/{{ target_user.id }}/history/partial?...`

Context: `target_user`, `logs`, filter params, `detail_base_path`

**Step 5: Rewrite `app/templates/admin/user_history_detail.html`**

Same as history/detail.html but with admin back link.

**Step 6: Rewrite `app/templates/admin/history_partial_cards.html`**

HTMX partial for admin user history pagination.

**Step 7: Verify, Step 8: Commit**
```bash
git add app/templates/admin/
git commit -m "feat: redesign admin pages with user management UI"
```

---

## Task 13: Run Full Test Suite

**Step 1: Run tests**

```bash
just test
```

Expected: all tests pass (templates don't break Python logic, only HTML output changes)

**Step 2: Manual verification checklist**

Run `just run` and check each page:
- [ ] Login/Register pages render
- [ ] Dashboard shows stats and recent sends
- [ ] Sidebar visible on desktop, bottom bar on mobile
- [ ] Ads list with create/edit/delete
- [ ] Accounts list with connect/sync flows
- [ ] Groups list with filters and bulk actions
- [ ] Schedules list and form
- [ ] History list with filters and detail page
- [ ] Billing page with progress bars
- [ ] Profile page
- [ ] Admin pages (if admin user)
- [ ] Mobile views for all pages
- [ ] HTMX infinite scroll works
- [ ] HTMX polling works (account sync status)

**Step 3: Final commit**
```bash
git add -A
git commit -m "feat: complete UI redesign - Linear-inspired minimalist design"
```

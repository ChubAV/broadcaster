# UI Redesign Design Document

**Date:** 2026-02-28
**Approach:** Full rewrite of all Jinja2 templates
**Reference:** Linear (clean minimalist)

## Stack (unchanged)
- Tailwind CSS v3 (CDN)
- HTMX 1.9+ (CDN)
- Alpine.js 3.13+ (CDN)
- Inter font (Google Fonts)
- Heroicons (inline SVG)

## Layout

### Desktop (lg+): Fixed sidebar
- Sidebar: 240px, fixed left, white bg, `border-r border-gray-200`
- Logo at top, nav links with outline icons (filled when active)
- User section at bottom: avatar + name + logout
- Active link: `bg-gray-100 text-gray-900 font-medium`
- Content area: `ml-60`, padding `px-8 py-6`, bg `#fafafa`

### Mobile (<lg): Bottom tab bar + minimal header
- Header: hamburger (left), logo (center), avatar (right)
- Bottom bar: 5 tabs (Dashboard, Ads, Groups, Schedules, History), fixed, 56px, `border-t`
- Hamburger opens slide-over menu for: Accounts, Billing, Profile, Admin
- Content: full width, padding `px-4 py-4`

## Design Tokens

### Colors
- Page bg: `#fafafa`
- Card/sidebar bg: `#ffffff`
- Text primary: `#1a1a1a`
- Text secondary: `#6b7280`
- Text muted: `#9ca3af`
- Accent: Indigo `#4f46e5` (actions), `#eef2ff` (light bg)
- Border primary: `#e5e7eb`
- Border light: `#f3f4f6`

### Status badges
- Active/Success: `#059669` on `#ecfdf5`
- Error/Failed: `#dc2626` on `#fef2f2`
- Warning/Syncing: `#d97706` on `#fffbeb`
- Neutral/Paused: `#6b7280` on `#f3f4f6`

### Typography (Inter)
- Page title: `text-lg font-semibold text-gray-900`
- Section header: `text-sm font-medium text-gray-500 uppercase tracking-wide`
- Body: `text-sm text-gray-700`
- Meta: `text-xs text-gray-500`

### Components
- **Buttons**:
  - Primary: `bg-indigo-600 text-white rounded-lg px-3 py-2 text-sm font-medium hover:bg-indigo-700`
  - Secondary: `border border-gray-300 text-gray-700 rounded-lg px-3 py-2 text-sm`
  - Ghost: `text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg px-3 py-2 text-sm`
  - Danger: `text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg px-3 py-2 text-sm`
- **Cards**: `bg-white rounded-lg border border-gray-200` (no shadows, Linear-style)
- **Inputs**: `border border-gray-300 rounded-lg text-sm px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500`
- **Badges**: `rounded-full px-2 py-0.5 text-xs font-medium`
- **Tables/Lists**: border-separated rows, hover `bg-gray-50`

## Page Designs

### Dashboard
- 4 stat cards in a row (2x2 on mobile)
- "Recent sends" as compact table rows
- Clean, data-focused

### List pages (Ads, Groups, Accounts, Schedules, History)
- Page title + action button (top right)
- Inline filters (collapsible on mobile)
- Table rows on desktop, cards on mobile
- Infinite scroll via HTMX (preserved)
- Empty states with CTA

### Form pages (Ads, Schedules)
- Centered form, `max-w-2xl`
- Grouped fields with subtle separators
- Primary + Ghost buttons at bottom

### Detail pages (History detail, Account connect)
- Clean card layout, centered content

### Admin pages
- Same design system, admin-specific content
- User table, user detail, user history

### Auth pages (Login, Register)
- Centered card on plain background
- Clean form with indigo accents

## HTMX patterns (preserved)
- Infinite scroll: `hx-trigger="revealed"` with `hx-swap="outerHTML"`
- Polling: `hx-trigger="every 5s"` for sync status
- Layout param: `layout=cards` (mobile) or `layout=rows` (desktop)

## Alpine.js patterns (preserved)
- Mobile menu toggle
- Filter panel toggle
- Image carousels
- User dropdown
- Bulk selection (groups)

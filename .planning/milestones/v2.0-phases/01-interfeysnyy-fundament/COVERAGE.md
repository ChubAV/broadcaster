# Phase 1 — API Coverage Declaration

**Detector result:** `detected: true` — single signal, verb `(surface)` + noun `sdk`, matched inside
this snippet from `01-CONTEXT.md`:

> **D-19:** «Воркер онлайн» в индикаторе шапки (D-09) читается из **БД — `MessengerAccount.status`**,
> не из состояния Docker-контейнера.

**Verdict: false positive.** The only match is the phrase «Docker SDK» appearing inside a decision that
**forbids** calling that SDK. D-19 exists precisely to keep an SDK out of the request path.

## No external API integration

**No external API integration: фаза заменяет слой представления работающего приложения — ни одного нового
роута, клиента, ключа или исходящего вызова к стороннему сервису она не добавляет.**

Confirmed by re-reading the phase scope, not by preference:

| Would-be signal | Actual scope in Phase 1 |
|-----------------|-------------------------|
| Docker SDK (`list_worker_containers()`) | **Explicitly prohibited** by D-19 for page rendering. The worker indicator reads `MessengerAccount.status` from PostgreSQL — an in-process SQLAlchemy query, not an API call. `01-RESEARCH.md` Pitfall 3 documents why. |
| npm / package installs | Prohibited by D-02 (no frontend build step, no `package.json` in the main app). No Python dependency added either. |
| htmx 1.9.10, Alpine 3.13.3 | **Vendored as static files** into `app/static/js/` (D-05). One-time `curl` during execution; no runtime integration, no SDK, no client. After this phase the app calls **zero** external CDNs — the phase *removes* three outbound dependencies (`cdn.tailwindcss.com`, `fonts.googleapis.com`, `unpkg.com`). |
| Fonts | Extracted from the already-committed `new_broadcaster_design.html` manifest and self-hosted (D-04). No Google Fonts request remains. |
| Telegram / WhatsApp / MAX protocols | Out of scope by ROADMAP hard boundary: «Протоколы отправки Telegram, WhatsApp и MAX не затрагиваются». |
| Billing / S3 / Redis | Existing internal services, already integrated, read through existing service functions (`billing_service.get_balance_info`, `billing_cache`). No surface change. |

There is no external API capability surface to enumerate, so no capability matrix is produced. This
declaration is the seal-time artifact in its place.

**Net direction of this phase is the opposite of integration:** it eliminates every third-party runtime
dependency the application currently has.

---

*Generated at plan time, Phase 1 — Интерфейсный фундамент.*

# Codebase Concerns

**Analysis Date:** 2026-08-03

## Tech Debt

**Oversized orchestration modules:**
- Issue: Worker dispatch and server-rendered account/auth flows are concentrated in very large modules (up to ~29k lines), making changes difficult to isolate.
- Files: `app/worker/tasks.py`, `app/pages/accounts.py`, `app/pages/auth.py`
- Impact: High regression risk and difficult review/testing of unrelated behavior.
- Fix approach: Split by task/use-case (send, retry, cleanup, lifecycle) and extract shared validation/response helpers with focused tests.

**Duplicated container managers:**
- Issue: WhatsApp and MAX managers duplicate Docker lifecycle code and swallow `NotFound`/cleanup failures.
- Files: `app/services/wa_container_manager.py`, `app/services/max_container_manager.py`
- Impact: Bug fixes and resource policy changes can diverge between messenger types.
- Fix approach: Introduce a typed container-manager abstraction and centralize lifecycle, timeout, and logging behavior.

## Known Bugs

**Blocking polling in async-capable service path:**
- Symptoms: Container readiness waits use synchronous HTTP and sleep calls.
- Files: `app/services/wa_container_manager.py`, `app/services/max_container_manager.py`
- Trigger: Starting or reconnecting a worker from an async request/task.
- Workaround: Run lifecycle operations in a dedicated thread/worker; migrate polling to `httpx.AsyncClient` and `asyncio.sleep`.

## Security Considerations

**Docker socket exposure:**
- Risk: Web and default Celery containers mount `/var/run/docker.sock`, granting effective host-level Docker control if the app is compromised.
- Files: `docker-compose.yml`, `docker-compose.prod.yml`, `app/services/wa_container_manager.py`
- Current mitigation: Containers are labeled and namespaced, but the socket is unrestricted.
- Recommendations: Isolate a narrowly privileged container-manager service or use a restricted Docker API proxy; never expose the socket to request-serving code.

**Upload validation trusts MIME metadata:**
- Risk: Image uploads only check `UploadFile.content_type`; arbitrary files can be stored with an image MIME type and attacker-controlled filename.
- Files: `app/routes/uploads.py`, `app/services/s3.py`
- Current mitigation: 5 MB configured size limit and per-user key prefix.
- Recommendations: Decode magic bytes with an image library, normalize extension/name, enforce image dimensions, and return non-public object URLs where possible.

**Cookie authentication lacks explicit CSRF protection:**
- Risk: Browser state-changing routes accept an `access_token` cookie; SameSite=Lax does not cover all cross-site navigation/API cases.
- Files: `app/pages/auth.py`, `app/dependencies.py`, `app/routes/*.py`
- Current mitigation: `httponly` and `samesite="lax"` cookie attributes.
- Recommendations: Add CSRF tokens for form/API mutations and set `secure=True` in production.

## Performance Bottlenecks

**Unbounded result materialization:**
- Problem: Many page handlers load complete query result sets with `.scalars().all()` before rendering.
- Files: `app/pages/groups.py`, `app/pages/accounts.py`, `app/pages/history.py`, `app/pages/admin.py`
- Cause: Pagination is inconsistent and large account/group/history tables can consume memory and DB time.
- Improvement path: Enforce limit/offset or cursor pagination at repository boundaries and add indexes for user/time filters.

**Periodic metrics query load:**
- Problem: A background loop executes several aggregate queries every 30 seconds in every web process.
- Files: `app/main.py`, `app/metrics.py`
- Cause: No leader election or centralized metrics worker; horizontal web scaling multiplies DB load.
- Improvement path: Move aggregation to one scheduled worker or use Prometheus database/exporter metrics with caching.

## Fragile Areas

**Broad exception swallowing:**
- Files: `app/worker/tasks.py`, `app/messengers/telegram_user.py`, `app/messengers/whatsapp.py`, `app/middleware.py`
- Why fragile: Generic `except Exception` blocks and bare `pass` can hide partial sends, leaked sessions, or failed cleanup.
- Safe modification: Catch known exception classes, preserve task retry semantics, and emit structured failure state for each account/message.

**Messenger session lifecycle:**
- Files: `app/messengers/telegram_user.py`, `app/messengers/telegram_pool.py`, `app/messengers/whatsapp.py`
- Why fragile: Multiple adapters independently manage connect/disconnect and fallback behavior, with cleanup errors ignored.
- Safe modification: Define a single lifecycle contract and test disconnect/reconnect, auth expiry, and cancellation paths.

## Dependencies at Risk

**Legacy bridge alongside dynamic workers:**
- Risk: Two WhatsApp implementations increase operational and security surface and can drift in protocol behavior.
- Files: `wa_bridge/`, `wa_worker/`, `app/messengers/whatsapp.py`
- Impact: Fixes may be applied to one integration while production routes another.
- Migration plan: Declare one supported implementation, move remaining accounts through it, then archive the unused bridge.

## Test Coverage Gaps

**Infrastructure and failure paths:**
- What's not tested: Docker lifecycle, S3 upload validation, messenger reconnects, and Celery retry/idempotency behavior.
- Files: `app/services/wa_container_manager.py`, `app/services/s3.py`, `app/worker/tasks.py`, `app/messengers/`
- Risk: Production-only failures can strand containers, duplicate messages, or lose schedules.
- Priority: High

---

*Concerns audit: 2026-08-03*

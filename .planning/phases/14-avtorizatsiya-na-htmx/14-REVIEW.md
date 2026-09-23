---
phase: 14-avtorizatsiya-na-htmx
reviewed: 2026-09-22T00:00:00Z
depth: standard
files_reviewed: 31
files_reviewed_list:
  - app/pages/auth.py
  - app/pages/htmx.py
  - app/static/css/app.css
  - app/templates/auth/forgot_password.html
  - app/templates/auth/forgot_password_reset.html
  - app/templates/auth/forgot_password_verify.html
  - app/templates/auth/includes/forgot_password_reset_step.html
  - app/templates/auth/includes/forgot_password_step.html
  - app/templates/auth/includes/forgot_password_verify_step.html
  - app/templates/auth/includes/login_step.html
  - app/templates/auth/includes/register_complete_step.html
  - app/templates/auth/includes/register_step.html
  - app/templates/auth/includes/register_verify_step.html
  - app/templates/auth/includes/step_response.html
  - app/templates/auth/login.html
  - app/templates/auth/register.html
  - app/templates/auth/register_complete.html
  - app/templates/auth/register_verify.html
  - app/templates/auth_base.html
  - app/templates/base.html
  - tests/test_pages/test_auth_transport.py
  - tests/test_pages/test_blocked_user.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_htmx_post_pairs.py
  - tests/test_pages/test_htmx_response_layer.py
  - tests/test_pages/test_hx_location_destinations.py
  - tests/test_pages/test_impersonation.py
  - tests/test_pages/test_notices_channel.py
  - tests/test_pages/test_password_reset.py
  - tests/test_pages/test_registration.py
  - tests/test_templates/test_htmx_markup_gates.py
findings:
  critical: 2
  warning: 7
  info: 3
  total: 12
status: issues_found
---

# Phase 14: Code Review Report

**Reviewed:** 2026-09-22
**Depth:** standard
**Files Reviewed:** 31
**Status:** issues_found

## Summary

I traced every security property the phase claims against the source rather than
against the prose, and the transport-level claims hold up:

* the password is never echoed — `_screen_builders` (`app/pages/auth.py:211`) raises
  on a `password` context key, and no handler passes one;
* a failed login answers 422 on both transports with no `Set-Cookie`, and the
  order `password → blocked → cookie` is intact (`app/pages/auth.py:257-275`);
* echo is escaped: `templates.env.autoescape` is `True` (verified at runtime) and
  neither `|safe` nor `Markup(` appears anywhere under `app/templates/auth/` or
  `app/templates/components/`;
* the step token rides only a hidden field — `respond_screen` emits no navigation
  header, and every `redirect_internal` target is an ASCII literal local path
  through `_local_path`;
* `<title>` as the first top-level node is correct against the *vendored* runtime:
  `app/static/js/htmx.min.js` function `P` (makeFragment) does
  `var o=r.querySelector("title"); if(o&&o.parentNode===r){o.remove();r.title=o.innerText}`
  — the direct-child requirement in `step_response.html` is a measured fact, and
  the node is stripped before the swap;
* `HX-Location` / `HX-Redirect` are both read before `Bn(n)` (the `responseHandling`
  lookup) in the same file, so 204 does not suppress them;
* the impersonation return refuses cross-origin with a bare 403 before any token
  read (`app/pages/auth.py:691`) and the four recovery steps carry
  `Depends(forbid_when_impersonating)`.

The defects are elsewhere. Two are security controls that are *absent* from this
module while being present in every sibling page module, and one of those the new
test suite actively encodes as expected behaviour. The rest are correctness-
adjacent quality problems the phase carried forward unchanged across four
copy-pasted handler bodies.

Two findings (CR-01, CR-02) predate this phase; I report them because the review
scope is `app/pages/auth.py` as it stands, they are provable in the file, and the
3605-test suite cannot see either — it asserts one of them as correct.

## Critical Issues

### CR-01: Ten state-changing auth POST routes carry no cross-origin guard

**File:** `app/pages/auth.py:234, 285, 373, 454, 542, 784, 879, 960, 1051` (vs. `app/pages/auth.py:691`)
**Issue:**
`stop_impersonation` is the only handler in this module that calls
`is_same_origin(request)`. Every other converted route — `/login`,
`/register/send-code`, `/register/verify`, `/register/resend-code`,
`/register/complete`, `/forgot-password/send-code`, `/forgot-password/verify`,
`/forgot-password/resend-code`, `/forgot-password/reset` — accepts a cross-site
POST unconditionally.

This is not a stylistic gap. The project's own control, documented at
`app/pages/common.py:716-745`, states the requirement verbatim:

> ASVS L1 (V4.2.2) требует защиты изменяющих состояние запросов от межсайтовой
> подделки.

and the guard is applied to nine other page-layer mutating handlers
(`app/pages/admin.py` ×6, `app/pages/ads.py` ×2, `app/pages/accounts.py`,
`app/pages/account_groups.py`, `app/pages/schedules.py`, `app/pages/history.py`,
`app/pages/billing.py`). Auth is the one module left out.

Two concrete consequences, both reachable from a plain attacker-controlled page:

1. **Login CSRF.** A cross-site form POST to `/login` with the attacker's
   credentials returns `302`/`204` *with* `Set-Cookie: access_token=…`. `SameSite=Lax`
   restricts *sending* a cookie, not *setting* one, so the victim's browser stores
   the attacker's session and subsequent top-level navigations run under it. The
   victim then performs work (creates ads, connects messenger accounts, uploads
   files) inside an account the attacker controls and can read.
2. **Unsolicited mail from the product's domain.** `/register/send-code` and
   `/forgot-password/send-code` insert a row and dispatch an email for an
   attacker-chosen address. The `CODE_RESEND_COOLDOWN_SECONDS` limit is per
   address, so a single hostile page can fan out across an arbitrary address list
   at one message per address per minute.

The suite cannot catch this: `is_same_origin` deliberately passes requests that
send neither `Sec-Fetch-Site` nor `Origin` (documented at `app/pages/common.py:737-744`),
and httpx sends neither.

**Fix:** apply the same guard the rest of the page layer applies, at the boundary
`ORIGIN_CHECK_BOUNDARY` describes (`app/pages/common.py:702`) — first statement of
the handler, before any token read or DB access:

```python
@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not is_same_origin(request):
        return Response(status_code=403)
    ...
```

If a bare 403 on these nine is to remain an accepted exception rather than a
control, it needs the same treatment `stop_impersonation` got: an owner decision
and an `OWN_RESPONSE_EXITS` record. Today it is neither guarded nor declared.

### CR-02: A verified password-reset token is replayable and self-renewing

**File:** `app/pages/auth.py:1075-1115`, `app/pages/auth.py:1094-1103`, `app/services/auth_service.py:143-150`
**Issue:**
`forgot_password_reset` validates the token, finds the user, hashes the new
password and commits. It never touches the `EmailVerificationCode` row and never
invalidates the token. `code_record.verified_at`, written by
`forgot_password_verify` at `app/pages/auth.py:950`, is never read by the reset
handler — the "one code, one use" property exists in the data model and is not
enforced.

Three compounding effects:

1. **Replay.** The same verified token resets the password again and again for
   its whole 30-minute TTL (`expires_minutes=30` default,
   `app/services/auth_service.py:145`). The new suite proves this: in
   `tests/test_pages/test_auth_transport.py:1717-1745` one `token` is minted once
   and POSTed twice — 302 then 204 — and both are asserted to succeed.
2. **Indefinite renewal.** The short-password branch mints a *fresh* verified
   token on every rejection:

   ```python
   if len(password) < 6:
       verified_token = create_verification_token(
           email, settings.secret_key, verified=True, purpose="password_reset"
       )
   ```

   Anyone holding a token that is about to expire posts a 5-character password,
   gets a 422 whose body contains a new 30-minute token, and repeats. The reset
   capability never times out. `register_complete` has the identical pattern at
   `app/pages/auth.py:588-598`.
3. **No session invalidation.** After `user.password_hash = hash_password(password)`
   the previously issued JWTs remain valid until their own expiry — "change your
   password" does not evict an attacker who already has a session.

Taken together: a reset token that leaks once (shoulder-surfed form, shared
device with the page still open, browser history/bfcache of the POST response,
an extension reading the DOM) becomes a permanent account-takeover primitive
rather than a ten-minute one.

**Fix:** make the reset consume the code record, and make the token single-use by
binding it to that record.

```python
    code_record = (
        await db.execute(
            select(EmailVerificationCode)
            .where(
                EmailVerificationCode.email == email,
                EmailVerificationCode.purpose == "password_reset",
                EmailVerificationCode.verified_at.is_not(None),
                EmailVerificationCode.consumed_at.is_(None),   # new column
                EmailVerificationCode.expires_at > now,
            )
            .order_by(EmailVerificationCode.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if code_record is None:
        # тот же экран начала восстановления, что и у устаревшей ссылки
        ...

    user.password_hash = hash_password(password)
    code_record.consumed_at = now
    await db.commit()
```

and stop re-minting on the validation failure — echo back the token that arrived
instead of issuing a new one:

```python
    if len(password) < 6:
        page, fragment = _screen_builders(
            request, "forgot_password_reset", email=email, token=token, error=...
        )
```

Session invalidation on password change (a `password_changed_at` claim checked in
`decode_access_token`) is the third half of the fix and belongs in the same change.

## Warnings

### WR-01: `register_verify` and `register_resend_code` skip the `purpose` check their siblings enforce

**File:** `app/pages/auth.py:393-398`, `app/pages/auth.py:473-478`
**Issue:** four of the six token-consuming handlers validate the claim:

| handler | check |
|---|---|
| `register_complete` (573) | `payload.get("purpose") != "email_verification"` |
| `forgot_password_verify` (901) | `payload.get("purpose") != "password_reset"` |
| `forgot_password_resend_code` (982) | `payload.get("purpose") != "password_reset"` |
| `forgot_password_reset` (1076) | `payload.get("purpose") != "password_reset"` |
| **`register_verify` (393)** | **`if not payload:` only** |
| **`register_resend_code` (473)** | **`if not payload:` only** |

`decode_verification_token` accepts either purpose (`app/services/auth_service.py:157`),
so a `password_reset` token is a valid input to both registration handlers. Feeding
one to `/register/resend-code` makes the app generate a *registration* code and
send a "confirm your email" message to an address the holder is only supposed to
be able to reset — a token-type confusion that gets a cross-flow email sent. Two
handlers validating and two not, in the same file, is exactly the asymmetry that
survives review by looking intentional.

**Fix:**

```python
    payload = decode_verification_token(token, settings.secret_key)
    if not payload or payload.get("purpose") != "email_verification":
        page, fragment = _screen_builders(
            request, "register", error="Ссылка устарела. Начните регистрацию заново."
        )
        return await respond_screen(request, page=page, fragment=fragment)
```

### WR-02: The page and fragment render paths do NOT share a template context — D-06's "nowhere to diverge" is only half true

**File:** `app/pages/auth.py:182-226`
**Issue:** `_page` renders through `templates.TemplateResponse(entry.page, {"request": request, **context})`;
`_fragment` renders through `_screen_markup`, i.e.
`templates.env.get_template(...).render(screen_title=…, screen_template=…, **context)`.
The *markup* is shared; the *context* is not. Measured on this tree:

```
>>> templates.env.from_string('[{{ request }}]').render()
'[]'                                  # fragment path: request is silently Undefined
>>> templates.env.from_string("{{ url_for('static', path='/x') }}").render()
KeyError: 'request'                   # fragment path: Starlette's url_for explodes
```

Today no step template reads `request` or calls `url_for`, so the divergence is
latent — but it is exactly the class of drift the "one included template" decision
was taken to make impossible, and nothing in the suite or the markup gates checks
it. A future `{% if request.query_params… %}` renders one way on the degraded path
and another on the htmx path, silently; a future `url_for` 500s on the htmx path
only. The `components/alert.html` header already warns about this by hand
("макрос НЕ читает request из контекста") — hand-warnings are what this codebase
replaces with gates everywhere else.

**Fix:** give the fragment the same context the page gets, so the two paths
cannot differ:

```python
    async def _fragment():
        entry = AUTH_SCREENS[screen]
        return templates.TemplateResponse(
            AUTH_STEP_RESPONSE_TEMPLATE,
            {
                "request": request,
                "screen_title": entry.title,
                "screen_template": entry.step,
                **context,
            },
        )
```

(or, if the bare-env render is deliberate, add a gate asserting that no template
reachable from `AUTH_SCREENS[*].step` contains `request` or `url_for`).

### WR-03: The status-code split between "address known" and "address unknown" turns user enumeration into a machine-readable oracle

**File:** `app/pages/auth.py:810-818` vs `app/pages/auth.py:832-841/872-876`, and `app/pages/auth.py:306-311` vs `app/pages/auth.py:364-368`
**Issue:** the *texts* are unchanged (D-15), but the *codes* are new. An
unregistered address now gets `422` from `/forgot-password/send-code` and a
registered one gets `200`; on `/register/send-code` the polarity is inverted
(`422` = taken, `200` = free). Before the phase both answered `200` and an
enumerator had to parse Russian HTML; now a single unauthenticated request per
address yields a one-bit answer from the status line alone — no body parsing, no
locale dependency, trivially parallelised. Combined with CR-01 (no origin guard)
the oracle is also reachable cross-site.

I am not asking for the texts to change (that is a product decision the phase
correctly refused to make). I am flagging that the transport change made an
existing weakness materially cheaper to exploit, and that this was not weighed.

**Fix:** either answer both outcomes with the same screen change + generic text
("Если такой адрес зарегистрирован, код отправлен"), or — if the explicit text is
a deliberate product choice — record it as a named acceptance next to
`BLOCKED_LOGIN_ERROR` (`app/pages/auth.py:61-72`), which is the module's own form
for "this disclosure is intentional and here is who pays".

### WR-04: A failed email send is swallowed and reported to the user as success

**File:** `app/pages/auth.py:346-361`, `512-527`, `855-870`, `1023-1038`
**Issue:** all four code-sending handlers wrap the SMTP call in
`except Exception as e: logger.error(...)` and then fall through to
`respond_screen(...)` — the user is moved to the code screen and told a code was
sent. If `settings.smtp_host` is empty the branch logs `smtp_not_configured` and
does the same. Either way the person now sits on a code screen with no code, and
`CODE_RESEND_COOLDOWN_SECONDS` blocks their retry for a minute because the row
*was* written before the send was attempted.

This is a real dead-end for the user, and it is invisible to the suite (which
never configures SMTP, so every test takes the `smtp_not_configured` branch and
asserts the success screen).

**Fix:** treat a send failure as a field error on the same screen and do not leave
a cooldown row behind:

```python
    try:
        if not settings.smtp_host:
            raise RuntimeError("smtp_not_configured")
        await send_verification_email(...)
    except Exception as e:
        logger.error("verification_email_send_failed", email=email, error=str(e))
        await db.delete(verification)
        await db.commit()
        page, fragment = _screen_builders(
            request, "register", email=email,
            error="Не удалось отправить код. Попробуйте ещё раз.",
        )
        return await respond_field_error(request, page=page, fragment=fragment)
```

### WR-05: Four copy-pasted code-issuing bodies, including a 118-character cooldown expression

**File:** `app/pages/auth.py:313-368`, `481-537`, `820-876`, `991-1048`
**Issue:** `register_send_code`, `register_resend_code`, `forgot_password_send_code`
and `forgot_password_resend_code` each contain the same five steps written out
longhand: latest-code query, cooldown comparison, `secrets.randbelow` loop,
`EmailVerificationCode(...)` insert + commit, SMTP send inside a bare
`except Exception`, token mint. The cooldown line is copied verbatim four times:

```python
if last_code and (now - last_code.created_at.replace(tzinfo=timezone.utc)).total_seconds() < CODE_RESEND_COOLDOWN_SECONDS:
```

The copies have already drifted in a small way — the registration pair chains
`.where(...).where(...)` while the recovery pair uses a single `.where(a, b)` —
which is the first symptom of the class of divergence the module's own
`_session_cookie_attrs` docstring (`app/pages/auth.py:78-85`) argues against at
length for cookies. Every one of WR-04's four occurrences, and every future change
to the cooldown, the code alphabet, or the TTL, has to be made four times.

**Fix:** extract the shared body, parameterised on purpose and mailer:

```python
async def _issue_code(
    db: AsyncSession, settings: Settings, email: str, *, purpose: str, send
) -> bool:
    """Выдать код, если минута между кодами прошла. False — кода не выдано."""
    ...
```

and let the four handlers keep only their screen decisions.

### WR-06: Minimum password length is a magic `6` in five places

**File:** `app/pages/auth.py:588`, `app/pages/auth.py:1094`, `app/templates/auth/includes/register_complete_step.html:40`, `app/templates/auth/includes/forgot_password_reset_step.html:35`, plus the literal in `"Пароль должен быть не менее 6 символов"` (auth.py:596, 1101)
**Issue:** the module declares `CODE_LENGTH`, `CODE_TTL_MINUTES`, `CODE_MAX_ATTEMPTS`
and `CODE_RESEND_COOLDOWN_SECONDS` as named constants twenty lines earlier and
then hard-codes the password policy in two handlers, two `minlength=` attributes
and two message strings. Raising the minimum requires finding all six; missing the
`minlength=` pair makes the client and the server disagree, which surfaces as a
422 the user cannot explain.

**Fix:**

```python
PASSWORD_MIN_LENGTH = 6
SHORT_PASSWORD_ERROR = f"Пароль должен быть не менее {PASSWORD_MIN_LENGTH} символов"
```

and pass `minlength=PASSWORD_MIN_LENGTH` into the two `field(...)` calls from the
handler context rather than writing it in the templates.

### WR-07: A new test asserts token replay as correct behaviour without naming it

**File:** `tests/test_pages/test_auth_transport.py:1705-1752`
**Issue:** `test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice`
mints one verified reset token (line 1717) and POSTs `/forgot-password/reset` with
it twice — once bare (expects 302) and once over htmx (expects 204). Both are
asserted to succeed. The test's stated subject is transport, but its effect is to
pin CR-02's replay window open: the day someone makes reset tokens single-use,
this test reddens on the *second* POST and the failure will read as "the htmx
transport broke", not "replay is now refused". A reviewer chasing that failure
will be pointed at `redirect_internal`, which is innocent.

**Fix:** mint a token per transport, the way the sibling tests already do for
per-transport addresses (`test_a_short_new_password_answers_422_without_echo_on_both_transports`
takes a fresh token per iteration at line 1501):

```python
    for headers, expected in (({}, 302), (HTMX_HEADERS, 204)):
        token = _verified_reset_token(email, test_settings.secret_key)
        ...
```

so the test measures transport only, and replay stays measurable by whichever rule
owns it.

## Info

### IN-01: `_respond_by_transport` silently drops every header the builder set

**File:** `app/pages/htmx.py:1010-1021`
**Issue:** the exit reads `built.body` and discards `built` entirely, so any
`Set-Cookie`, `HX-Push-Url` or `Cache-Control` a builder attaches vanishes with no
error. This is deliberate and argued for at `app/pages/htmx.py:943-948`, and the
mirror-image boundary in `_glue_notice` (`app/pages/htmx.py:665-700`) is guarded by
an explicit "the next builder must re-read this paragraph" note. Here there is no
such note and no runtime check — the loss is only findable by reading prose in a
different function.

**Fix:** either copy non-`content-*` headers onto the fresh response, or raise
when the builder produced any header the exit is about to throw away, so the loss
is loud:

```python
    extra = set(built.headers) - {"content-type", "content-length"}
    if extra:
        raise ValueError(f"сборщик экрана навесил заголовки, которые выход теряет: {sorted(extra)}")
```

### IN-02: `_screen_builders`' password guard matches only the exact key `"password"`

**File:** `app/pages/auth.py:211-215`
**Issue:** the refusal is `if "password" in context`. A future context key named
`new_password`, `password_confirm` or `old_password` passes the guard and reaches
the template. The guard is the module's single line of defence for D-04 and is
worth making total.

**Fix:** `if any("password" in key for key in context):`

### IN-03: `created_at.replace(tzinfo=timezone.utc)` is a no-op that reads like a conversion

**File:** `app/pages/auth.py:323, 491, 832, 1003`
**Issue:** `EmailVerificationCode.created_at` is `DateTime(timezone=True)`
(`app/models/email_verification.py:21-23`) and the project runs on asyncpg, which
returns `timestamptz` already UTC-aware — so `.replace(tzinfo=timezone.utc)` changes
nothing today. It would, however, *overwrite* rather than convert under any driver
or column change that returns a non-UTC aware value, silently shifting the cooldown
by the offset (a positive offset makes the branch permanently true and blocks code
sending outright). The tests run on SQLite, which returns naive datetimes, so
neither the current no-op nor the future breakage is observable from the suite.

**Fix:** `.astimezone(timezone.utc)` expresses the intent and is correct for both
aware and, with an explicit guard, naive inputs.

---

_Reviewed: 2026-09-22_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

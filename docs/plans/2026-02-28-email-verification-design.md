# Email Verification at Registration — Design

## Problem

Registration currently creates accounts without any email verification. Users can register with any email address, including invalid or non-owned ones.

## Solution

Add email verification via a 6-digit code **before** account creation. The registration flow becomes a 3-step process.

## User Flow

### Step 1 — Enter Email (`/register`)

- Page shows only an email input and "Send Code" button
- POST `/register/send-code`:
  - Validate email format
  - Check email not already registered
  - Generate 6-digit code, save to DB with 10-min TTL
  - Send code via SMTP (Celery background task)
  - Return signed JWT token containing email
  - Redirect to Step 2

### Step 2 — Enter Code (`/register/verify`)

- Page shows code input (6 digits) and "Verify" button
- "Resend code" button (rate-limited: 1 per 60 seconds)
- POST `/register/verify`:
  - Validate JWT token (extract email)
  - Check code against DB
  - Max 5 attempts, then code is invalidated
  - On success: mark code as verified, issue new JWT with `verified=true`
  - Redirect to Step 3

### Step 3 — Complete Profile (`/register/complete`)

- Page shows name and password fields
- POST `/register/complete`:
  - Validate JWT token (must have `verified=true` and email)
  - Create user account
  - Set auth cookie, redirect to dashboard

## Data Model

### New Table: `email_verification_codes`

| Column | Type | Description |
|--------|------|-------------|
| id | int, PK | Auto-increment |
| email | varchar(255), indexed | Email being verified |
| code | varchar(6) | 6-digit verification code |
| attempts | int, default 0 | Failed verification attempts |
| verified_at | datetime, nullable | When code was successfully verified |
| expires_at | datetime | Code expiration (created_at + 10 min) |
| created_at | datetime | When code was generated |

## Security

- **Brute-force protection:** Max 5 code entry attempts per code
- **Code expiry:** 10 minutes TTL
- **Rate limiting:** Max 1 code send per email per 60 seconds (enforced by checking last created_at in DB)
- **Token-based flow:** Signed JWT carries email between steps (no hidden form fields)
- **Code storage:** Plain text (6-digit code with 10-min TTL and 5 attempts doesn't need hashing)

## Email Sending

### New Settings (in `Settings`)

- `smtp_host: str = ""`
- `smtp_port: int = 587`
- `smtp_user: str = ""`
- `smtp_password: str = ""`
- `smtp_from: str = ""`
- `smtp_use_tls: bool = True`

### New Service: `app/services/email_service.py`

- Uses `aiosmtplib` for async SMTP
- Single function: `send_verification_email(to_email, code)`
- Plain text email body

### New Celery Task

- `send_verification_email_task(email, code)` — sends email in background

## Files Changed

### New Files
- `app/models/email_verification.py` — EmailVerificationCode model
- `app/services/email_service.py` — SMTP email sending
- `app/templates/auth/register_email.html` — Step 1: email input
- `app/templates/auth/register_verify.html` — Step 2: code input
- `app/templates/auth/register_complete.html` — Step 3: name + password

### Modified Files
- `app/config.py` — Add SMTP settings
- `app/pages/auth.py` — Add new registration step routes
- `app/routes/auth.py` — Update REST API registration
- `app/worker/tasks.py` — Add email sending task
- `app/templates/auth/register.html` — Replace with email-only form (Step 1)

### Migration
- Alembic migration for `email_verification_codes` table

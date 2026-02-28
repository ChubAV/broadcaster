from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models.user import User
from app.services.auth_service import decode_access_token
from app.services.s3 import get_image_url

_templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))

# Register get_image_url as Jinja2 global so templates can use {{ get_image_url(key) }}
def _resolve_image_url(key: str) -> str:
    """Return key as-is if it's already a full URL, else build S3 URL."""
    if not key:
        return ""
    if key.startswith("http://") or key.startswith("https://"):
        return key
    return get_image_url(key, get_settings().s3_public_url)


templates.env.globals["get_image_url"] = lambda key: get_image_url(key, get_settings().s3_public_url)
templates.env.globals["resolve_image_url"] = _resolve_image_url
templates.env.globals["s3_public_url"] = lambda: get_settings().s3_public_url


def _get_timezone_for_user(user: User | None) -> ZoneInfo:
    """Return ZoneInfo for user's timezone or UTC as fallback."""
    tz_name = "UTC"
    if user and getattr(user, "timezone", None):
        try:
            tz_name = user.timezone
            return ZoneInfo(tz_name)
        except Exception:
            tz_name = "UTC"
    return ZoneInfo(tz_name)


def format_datetime_for_user(
    value: datetime | None,
    user: User | None,
    fmt: str = "%Y-%m-%d %H:%M",
) -> str:
    """Format datetime in user's timezone for display."""
    if value is None:
        return ""
    # Если дата без tzinfo — считаем, что она в UTC
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    tz = _get_timezone_for_user(user)
    local = value.astimezone(tz)
    return local.strftime(fmt)


templates.env.globals["format_datetime_for_user"] = format_datetime_for_user


async def get_user_from_cookie(
    request: Request, db: AsyncSession, settings: Settings
) -> User | None:
    """Read JWT from httpOnly cookie and return the User, or None."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token, settings.secret_key)
    if not payload:
        return None
    user = await db.get(User, payload["sub"])
    if user and user.is_blocked:
        return None
    return user


def check_is_admin(user: User | None, settings: Settings) -> bool:
    """Check if user is admin."""
    if not user or not settings.admin_email:
        return False
    return user.email == settings.admin_email

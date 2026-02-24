from pathlib import Path

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
templates.env.globals["get_image_url"] = lambda key: get_image_url(key, get_settings().s3_public_url)
templates.env.globals["s3_public_url"] = lambda: get_settings().s3_public_url


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

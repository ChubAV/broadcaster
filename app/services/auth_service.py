from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, secret_key: str, expires_minutes: int = 1440) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> dict | None:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        payload["sub"] = int(payload["sub"])
        return payload
    except (JWTError, KeyError, ValueError):
        return None


def create_verification_token(
    email: str, secret_key: str, verified: bool = False,
    expires_minutes: int = 30, purpose: str = "email_verification"
) -> str:
    """Create a JWT token for email verification or password reset flow."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"email": email, "verified": verified, "exp": expire, "purpose": purpose}
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_verification_token(token: str, secret_key: str) -> dict | None:
    """Decode a verification JWT token. Returns None if invalid."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        if payload.get("purpose") not in ("email_verification", "password_reset"):
            return None
        return payload
    except (JWTError, KeyError, ValueError):
        return None

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

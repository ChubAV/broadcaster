from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_settings
from app.config import Settings
from app.repositories.user import UserRepository
from app.services.auth_service import hash_password, verify_password, create_access_token, decode_verification_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    verification_token: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    # If SMTP is configured, require verified token
    if settings.smtp_host and not data.verification_token:
        raise HTTPException(status_code=400, detail="Email verification required")
    if data.verification_token:
        payload = decode_verification_token(data.verification_token, settings.secret_key)
        if not payload or not payload.get("verified") or payload.get("email") != data.email:
            raise HTTPException(status_code=400, detail="Invalid verification token")

    repo = UserRepository(db)
    existing = await repo.get_by_email(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await repo.create(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
    )
    return UserResponse(id=user.id, email=user.email, name=user.name)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db), settings: Settings = Depends(get_settings)):
    repo = UserRepository(db)
    user = await repo.get_by_email(data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is blocked")
    token = create_access_token(user.id, settings.secret_key, settings.access_token_expire_minutes)
    return TokenResponse(access_token=token)

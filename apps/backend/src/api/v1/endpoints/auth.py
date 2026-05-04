from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.user import UserModel, UserRole
from src.services.auth_service import AuthService, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, SECRET_KEY, ALGORITHM
from src.services.redis_service import (
    record_failed_login,
    is_account_locked,
    reset_failed_login,
    blacklist_token,
    is_token_revoked,
)
from pydantic import BaseModel, EmailStr, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from jose import jwt, JWTError
import structlog

logger = structlog.get_logger()
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    # SECURITY: role is NOT accepted from clients — assigned server-side only.
    # Prevents privilege escalation (H-06).

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        # DT-08: NIST SP 800-63B minimum requirements for a SaMD system
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    expires_in: int
    refresh_token: str
    full_name: str


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
async def register(
    request: Request, user_in: UserCreate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserModel).where(UserModel.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User already registered")

    hashed_password = AuthService.get_password_hash(user_in.password)
    user = UserModel(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        role=UserRole.PHYSICIAN.value,  # H-06: always server-side, never from client
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"message": "User created", "id": user.id}


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    # SEC-01: check account lockout before any DB query
    if await is_account_locked(form_data.username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to too many failed attempts. Try again in 15 minutes.",
        )

    result = await db.execute(
        select(UserModel).where(UserModel.email == form_data.username)
    )
    user = result.scalars().first()

    if not user or not AuthService.verify_password(
        form_data.password, user.hashed_password
    ):
        # SEC-01: record failure regardless of whether user exists (prevents enumeration)
        count = await record_failed_login(form_data.username)
        logger.warning("login_failed", email=form_data.username, attempt=count)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Successful login — reset lockout counter
    await reset_failed_login(form_data.username)

    try:
        user_name = user.full_name
    except Exception:
        user_name = "Usuario"

    # SEC-02: tokens now carry jti for revocation
    access_token, _access_jti = AuthService.create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    refresh_token, _refresh_jti = AuthService.create_refresh_token(
        data={"sub": user.email}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,
        "full_name": user_name,
    }


@router.post("/refresh", response_model=TokenRefreshResponse)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request, body: TokenRefresh, db: AsyncSession = Depends(get_db)
):
    payload = AuthService.decode_refresh_token(body.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # SEC-02: reject blacklisted refresh tokens
    old_jti = payload.get("jti")
    if old_jti and await is_token_revoked(old_jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    email = payload.get("sub")
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # SEC-02: rotate — blacklist old refresh token, issue new pair
    if old_jti:
        await blacklist_token(old_jti, ttl_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    new_access_token, _new_jti = AuthService.create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    new_refresh_token, _new_refresh_jti = AuthService.create_refresh_token(
        data={"sub": user.email}
    )
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest,
    token: str = Depends(oauth2_scheme),
):
    """
    SEC-02: Invalidates both the current access token and refresh token.
    Client should discard tokens locally after calling this endpoint.
    """
    # Blacklist access token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            from datetime import datetime, timezone
            ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
            await blacklist_token(jti, ttl_seconds=ttl)
    except JWTError:
        pass  # already expired — no need to blacklist

    # Blacklist refresh token
    refresh_payload = AuthService.decode_refresh_token(body.refresh_token)
    if refresh_payload:
        refresh_jti = refresh_payload.get("jti")
        if refresh_jti:
            await blacklist_token(
                refresh_jti, ttl_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 86400
            )

    logger.info("user_logged_out")

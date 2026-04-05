from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.user import UserModel, UserRole
from src.services.auth_service import AuthService
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.PHYSICIAN


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    expires_in: int
    refresh_token: str


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


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
        role=user_in.role.value,
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
    result = await db.execute(
        select(UserModel).where(UserModel.email == form_data.username)
    )
    user = result.scalars().first()

    if not user or not AuthService.verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = AuthService.create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    refresh_token = AuthService.create_refresh_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "expires_in": AuthService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,
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

    email = payload.get("sub")
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    new_access_token = AuthService.create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": AuthService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }

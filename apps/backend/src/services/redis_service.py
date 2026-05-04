"""
Redis Security Service — Integrum V2
Handles:
  - Account lockout: per-account failed login tracking (SEC-01)
  - JWT blacklist: jti-based token revocation for access + refresh tokens (SEC-02)
"""
from src.config import settings
import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger()

REDIS_URL = settings.REDIS_URL

# Lockout config (overridable via env)
MAX_FAILED_ATTEMPTS = settings.MAX_FAILED_LOGIN_ATTEMPTS
LOCKOUT_SECONDS = settings.ACCOUNT_LOCKOUT_SECONDS


def _get_redis() -> aioredis.Redis:
    """Lazy singleton — avoids connection at import time (important for tests)."""
    return aioredis.from_url(REDIS_URL, decode_responses=True)


# ─── Account Lockout ──────────────────────────────────────────────────────────

async def record_failed_login(email: str) -> int:
    """
    Increments failed login counter for the given account.
    Returns the new count. Counter TTL resets on each failure.
    """
    key = f"auth:failed:{email.lower()}"
    async with _get_redis() as r:
        count = await r.incr(key)
        await r.expire(key, LOCKOUT_SECONDS)
        if count >= MAX_FAILED_ATTEMPTS:
            await r.set(f"auth:locked:{email.lower()}", "1", ex=LOCKOUT_SECONDS)
            logger.warning("account_locked", email=email, attempts=count)
        return count


async def is_account_locked(email: str) -> bool:
    """Returns True if the account is currently locked."""
    async with _get_redis() as r:
        return bool(await r.exists(f"auth:locked:{email.lower()}"))


async def reset_failed_login(email: str) -> None:
    """Clears lockout state after a successful login."""
    async with _get_redis() as r:
        await r.delete(f"auth:failed:{email.lower()}")
        await r.delete(f"auth:locked:{email.lower()}")


# ─── JWT Token Blacklist ───────────────────────────────────────────────────────

async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """
    Adds a token jti to the blacklist with a TTL matching token expiry.
    After TTL expires, the key is auto-deleted (token would be expired anyway).
    """
    async with _get_redis() as r:
        await r.set(f"auth:blacklist:{jti}", "1", ex=ttl_seconds)
    logger.info("token_revoked", jti=jti)


async def is_token_revoked(jti: str) -> bool:
    """Returns True if the token jti is in the blacklist."""
    async with _get_redis() as r:
        return bool(await r.exists(f"auth:blacklist:{jti}"))

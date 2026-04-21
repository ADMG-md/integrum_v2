from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.api import api_router
from src.logging_config import setup_logging, logger
from src.database import engine
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

__version__ = "0.2.1" # Semantic versioning (Fixing Hardcode)

# Initialize SaMD Structured Logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", message="Integrum V2 API starting")
    yield
    logger.info("shutdown", message="Disposing database connection pool")
    await engine.dispose()
    logger.info("shutdown", message="Integrum V2 API stopped")


# Hardening: Rate Limiter (Prevent DDoS on clinical engines)
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Integrum V2 API",
    description="Core Clinical Engine (SaMD Class B) - Hardened Version",
    version=__version__,
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Hardening: CORS Restricted (Synced with environment)
import os
from dotenv import load_dotenv

load_dotenv()

raw_origins = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://0.0.0.0:3000"
)
ALLOWED_ORIGINS = [origin.strip() for origin in raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


# Hardening: HTTP Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    start_time = time.time()
    response: Response = await call_next(request)
    process_time = time.time() - start_time

    # Security Headers (OWASP Recommendations)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; frame-ancestors 'none';"
    )
    response.headers["X-Process-Time"] = str(process_time)

    # Sanitization of logs: Don't log full Authorization headers
    logger.info(
        "request_processed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time,
    )

    return response


app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
@limiter.limit("5/minute")
async def health_check(request: Request):
    try:
        from src.database import SessionLocal
        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "ok", "version": __version__, "db": "connected", "mode": "hardened"}
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return {"status": "degraded", "version": __version__, "db": "error", "error": str(e)}, 503


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

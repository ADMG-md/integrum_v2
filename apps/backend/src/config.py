from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Centralized configuration management for Integrum V2.
    Using pydantic-settings ensures fail-fast behavior if required env vars are missing
    or improperly formatted, meeting SaMD Class B configuration safety requirements (H-05).
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Environment
    ENVIRONMENT: str = Field(default="production", description="Runtime environment (development, staging, production)")
    
    # Security / Auth
    SECRET_KEY: str = Field(default="", description="JWT Secret Key. Must be set in production.")
    ALGORITHM: str = Field(default="HS256", description="JWT Algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration")
    
    # Rate Limiting & Account Security
    MAX_FAILED_LOGIN_ATTEMPTS: int = Field(default=5)
    ACCOUNT_LOCKOUT_SECONDS: int = Field(default=900)  # 15 min
    
    # Vault / Encryption
    VAULT_MASTER_KEY: str = Field(default="", description="Fernet key for Field-Level Encryption")
    ALLOW_DEV_VAULT_KEY: bool = Field(default=False, description="Allow ephemeral vault key generation in dev")

    # Infrastructure
    DATABASE_URL: str = Field(default="postgresql+asyncpg://integrum_user:integrum_password@localhost:5432/integrum_v2")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # CORS
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_env(cls, v: str) -> str:
        return v.lower()

    def validate_production_safety(self):
        """Called at startup to ensure no development settings leak to production."""
        if self.ENVIRONMENT != "development":
            if not self.SECRET_KEY:
                raise RuntimeError("CRITICAL: SECRET_KEY environment variable is NOT SET in production/staging.")
            if not self.VAULT_MASTER_KEY and not self.ALLOW_DEV_VAULT_KEY:
                raise RuntimeError("CRITICAL: VAULT_MASTER_KEY is NOT SET in production/staging.")
            
            # Warn if dev overrides are present in production
            if self.ALLOW_DEV_VAULT_KEY:
                logger.warning("SECURITY WARNING: ALLOW_DEV_VAULT_KEY=true is active in a non-development environment!")

settings = Settings()
settings.validate_production_safety()

"""
SQLAlchemy custom type for automatic field-level encryption.

Encapsulates Fernet encryption so that SQLAlchemy models do not need to
import vault_service directly, preserving Clean Architecture boundaries.
"""

from sqlalchemy import TypeDecorator, String
from cryptography.fernet import Fernet, InvalidToken
import os
import structlog

logger = structlog.get_logger()


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy TypeDecorator that transparently encrypts/decrypts string values.

    Usage:
        full_name: Mapped[str] = mapped_column(EncryptedString(1024))

    The column behaves like a normal String column from the model's perspective.
    Encryption happens on write, decryption on read.
    """

    impl = String
    cache_ok = True

    _cipher = None

    @classmethod
    def _get_cipher(cls) -> Fernet:
        if cls._cipher is None:
            key = os.getenv("VAULT_MASTER_KEY", "").encode()
            if not key:
                raise RuntimeError("VAULT_MASTER_KEY environment variable is not set")
            cls._cipher = Fernet(key)
        return cls._cipher

    def process_bind_param(self, value, dialect):
        """Encrypt value before writing to database."""
        if value is None:
            return None
        return self._get_cipher().encrypt(value.encode()).decode()

    def process_result_value(self, value, dialect):
        """Decrypt value after reading from database."""
        if value is None:
            return None
        try:
            return self._get_cipher().decrypt(value.encode()).decode()
        except InvalidToken:
            # Graceful fallback for legacy unencrypted data
            logger.warning("encrypted_string.decrypt_failed", value_preview=value[:20])
            return value
        except Exception as e:
            logger.error("encrypted_string.decrypt_error", error=str(e))
            return value

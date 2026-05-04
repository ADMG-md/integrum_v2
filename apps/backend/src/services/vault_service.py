import hashlib
import hmac
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os
import structlog

load_dotenv()
logger = structlog.get_logger()

class VaultService:
    """
    The Medical Vault (Mission 10).
    Handles Field-Level Encryption (FLE) for sensitive patient data.
    Ensures even with DB access, PII is unreadable.
    """
    def __init__(self):
        self.key = os.getenv("VAULT_MASTER_KEY")
        if not self.key:
            # R-03 Fix (H-015): Fail-fast to prevent data corruption.
            # A generated key would make all previously encrypted data unreadable.
            allow_dev = os.getenv("ALLOW_DEV_VAULT_KEY", "false").lower() == "true"
            if allow_dev:
                logger.warning(
                    "vault_dev_mode_active",
                    action="generating_ephemeral_key",
                    warning="DATA WILL NOT PERSIST ACROSS RESTARTS",
                )
                self.key = Fernet.generate_key()
            else:
                raise RuntimeError(
                    "CRITICAL: VAULT_MASTER_KEY is not set. "
                    "Startup aborted to prevent data corruption. "
                    "Set ALLOW_DEV_VAULT_KEY=true for local development only."
                )
        else:
            self.key = self.key.encode()
        
        self.cipher = Fernet(self.key)

        # P0-4: Derive a SEPARATE HMAC key via HKDF-SHA256.
        # Using the same key for encryption AND HMAC creates a cryptographic oracle.
        # HKDF with distinct context labels produces cryptographically independent keys.
        import hashlib as _hl
        self._hmac_key = hmac.new(
            self.key,
            b"integrum-v2-blind-index-v1",
            _hl.sha256,
        ).digest()

    def encrypt(self, plain_text: str) -> str:
        if not plain_text:
            return plain_text
        try:
            return self.cipher.encrypt(plain_text.encode()).decode()
        except Exception as e:
            # SEC-03: NEVER silently return PHI in plain text.
            # A failed encryption must be loud and blocking — not silent.
            logger.error("vault_encryption_failed", error=str(e))
            raise RuntimeError(
                f"CRITICAL: PHI encryption failed. Data will NOT be persisted unencrypted. "
                f"Check VAULT_MASTER_KEY integrity. Original error: {type(e).__name__}"
            ) from e

    def decrypt(self, encrypted_text: str) -> str:
        if not encrypted_text:
            return encrypted_text
        try:
            return self.cipher.decrypt(encrypted_text.encode()).decode()
        except Exception as e:
            # If not searchable or not encrypted, return as is (handle migration gracefully)
            logger.debug("vault_decryption_skipped", error=str(e))
            return encrypted_text

    def generate_blind_index(self, plain_text: str) -> str:
        """
        Generates a deterministic HMAC-SHA256 for searching encrypted fields.
        Uses a derived key (NOT the Fernet encryption key) to prevent
        cryptographic oracle attacks. (P0-4)
        """
        if not plain_text:
            return ""
        h = hmac.new(self._hmac_key, plain_text.strip().lower().encode(), hashlib.sha256)
        return h.hexdigest()

vault_service = VaultService()

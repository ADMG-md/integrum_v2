from sqlalchemy import String, ForeignKey, DateTime, Boolean, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
import uuid
from datetime import datetime
from typing import Optional


def _get_vault():
    from src.services.vault_service import vault_service

    return vault_service


class PatientConsent(Base):
    """
    Mission 12: Legal & Clinical Governance.
    Stores informed consent records for SaMD processing.
    """

    __tablename__ = "patient_consents"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    patient_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("patients.id"), nullable=False, index=True
    )
    encounter_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey("encounters.id"), nullable=True, index=True
    )

    consent_type: Mapped[str] = mapped_column(String(100), default="SAMD_ANALYSIS_V1")
    is_granted: Mapped[bool] = mapped_column(Boolean, default=False)

    _signature_image_data: Mapped[Optional[str]] = mapped_column(
        "signature_image", String(2048), nullable=True
    )
    _signer_ip_encrypted: Mapped[Optional[str]] = mapped_column(
        "signer_ip", String(1024), nullable=True
    )

    terms_version: Mapped[str] = mapped_column(String(50), default="2026.03.14-ES")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @property
    def signer_ip(self) -> Optional[str]:
        return (
            _get_vault().decrypt(self._signer_ip_encrypted)
            if self._signer_ip_encrypted
            else None
        )

    @signer_ip.setter
    def signer_ip(self, value: Optional[str]):
        if value:
            self._signer_ip_encrypted = _get_vault().encrypt(value)

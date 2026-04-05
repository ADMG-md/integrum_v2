from sqlalchemy import String, ForeignKey, JSON, Float, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database import Base
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.audit import AdjudicationLog


def _get_vault():
    from src.services.vault_service import vault_service

    return vault_service


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(
        String(255), nullable=False, default="default-clinic", index=True
    )

    _external_id_encrypted: Mapped[str] = mapped_column(
        "external_id", String(1024), unique=True, index=True
    )
    external_id_hash: Mapped[Optional[str]] = mapped_column(
        String(64), index=True, nullable=True
    )

    _full_name_encrypted: Mapped[str] = mapped_column("full_name", String(1024))
    _dob_encrypted: Mapped[Optional[str]] = mapped_column(
        "date_of_birth", String(1024), nullable=True
    )
    _gender_encrypted: Mapped[Optional[str]] = mapped_column(
        "gender", String(1024), nullable=True
    )
    _email_encrypted: Mapped[Optional[str]] = mapped_column(
        "email", String(1024), nullable=True
    )
    _phone_encrypted: Mapped[Optional[str]] = mapped_column(
        "phone", String(1024), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    encounters: Mapped[List["EncounterModel"]] = relationship(
        "EncounterModel", back_populates="patient"
    )

    @property
    def full_name(self) -> str:
        return _get_vault().decrypt(self._full_name_encrypted)

    @full_name.setter
    def full_name(self, value: str):
        self._full_name_encrypted = _get_vault().encrypt(value)

    @property
    def external_id(self) -> str:
        return _get_vault().decrypt(self._external_id_encrypted)

    @external_id.setter
    def external_id(self, value: str):
        self._external_id_encrypted = _get_vault().encrypt(value)
        self.external_id_hash = _get_vault().generate_blind_index(value)

    @property
    def date_of_birth(self) -> Optional[str]:
        return (
            _get_vault().decrypt(self._dob_encrypted) if self._dob_encrypted else None
        )

    @date_of_birth.setter
    def date_of_birth(self, value: Optional[str]):
        if value:
            self._dob_encrypted = _get_vault().encrypt(value)

    @property
    def gender(self) -> Optional[str]:
        return (
            _get_vault().decrypt(self._gender_encrypted)
            if self._gender_encrypted
            else None
        )

    @gender.setter
    def gender(self, value: Optional[str]):
        if value:
            self._gender_encrypted = _get_vault().encrypt(value)

    @property
    def email(self) -> Optional[str]:
        return (
            _get_vault().decrypt(self._email_encrypted)
            if self._email_encrypted
            else None
        )

    @email.setter
    def email(self, value: Optional[str]):
        if value:
            self._email_encrypted = _get_vault().encrypt(value)

    @property
    def phone(self) -> Optional[str]:
        return (
            _get_vault().decrypt(self._phone_encrypted)
            if self._phone_encrypted
            else None
        )

    @phone.setter
    def phone(self, value: Optional[str]):
        if value:
            self._phone_encrypted = _get_vault().encrypt(value)


class EncounterModel(Base):
    __tablename__ = "encounters"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(
        String(255), nullable=False, default="default-clinic", index=True
    )
    patient_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("patients.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    phenotype_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    ai_narrative: Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)
    clinical_notes: Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)
    plan_of_action: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    physician_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    agreement_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    reason_for_visit: Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)
    personal_history: Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)
    family_history: Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="encounters")
    observations: Mapped[List["ObservationModel"]] = relationship(
        "ObservationModel", back_populates="encounter", cascade="all, delete-orphan"
    )
    conditions: Mapped[List["EncounterConditionModel"]] = relationship(
        "EncounterConditionModel",
        back_populates="encounter",
        cascade="all, delete-orphan",
    )
    adjudication_logs: Mapped[List["AdjudicationLog"]] = relationship(
        "AdjudicationLog", back_populates="encounter", cascade="all, delete-orphan"
    )


class ObservationModel(Base):
    __tablename__ = "observations"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    encounter_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("encounters.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(100), index=True)
    value: Mapped[str] = mapped_column(String(500))
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="Clinical")
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    encounter: Mapped["EncounterModel"] = relationship(
        "EncounterModel", back_populates="observations"
    )


class EncounterConditionModel(Base):
    """Associates a diagnostic code with a specific encounter."""

    __tablename__ = "encounter_conditions"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    encounter_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("encounters.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(255))
    system: Mapped[str] = mapped_column(String(50), default="CIE-10")

    encounter: Mapped["EncounterModel"] = relationship(
        "EncounterModel", back_populates="conditions"
    )

import enum
from sqlalchemy import (
    String,
    Text,
    DateTime,
    JSON,
    Float,
    ForeignKey,
    Boolean,
    func,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.encounter import EncounterModel


class DecisionType(str, enum.Enum):
    AGREEMENT = "AGREEMENT"
    OVERRIDE = "OVERRIDE"


class ReasonCode(str, enum.Enum):
    AGREE_INSIGHT = "AGREE_INSIGHT"
    OVERRIDE_CLINICAL_INTUITION = "OVERRIDE_CLINICAL_INTUITION"
    OVERRIDE_ECONOMIC_BARRIER = "OVERRIDE_ECONOMIC_BARRIER"
    OVERRIDE_MISSING_CONTEXT = "OVERRIDE_MISSING_CONTEXT"
    OVERRIDE_PATIENT_REFUSAL = "OVERRIDE_PATIENT_REFUSAL"


class AdjudicationLog(Base):
    """
    SaMD Audit Trail (IEC 62304 / ISO 13485).
    Stores every clinical decision made by the internal motors.
    """

    __tablename__ = "adjudication_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    encounter_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("encounters.id"), index=True
    )
    engine_name: Mapped[str] = mapped_column(String(100), index=True)
    engine_version_hash: Mapped[str] = mapped_column(
        String(64)
    )  # Hash of the engine code

    calculated_value: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    evidence: Mapped[Dict[str, Any]] = mapped_column(
        JSON
    )  # Serialized list of evidence

    # Traceability
    requirement_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("clinical_traceability.id"), nullable=True
    )

    # Audit Meta
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Physician Feedback (Mission 5 extension)
    is_overridden: Mapped[bool] = mapped_column(Boolean, default=False)
    physician_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    physician_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Hardening: Cryptographic Hash
    integrity_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Relationships
    encounter: Mapped["EncounterModel"] = relationship(
        "EncounterModel", back_populates="adjudication_logs"
    )


class DecisionAuditLog(Base):
    """
    Human-AI Interaction Audit (MinCiencias Compliance).
    Tracks whether a physician agreed or overrode specific AI insights.
    """

    __tablename__ = "decision_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    encounter_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("encounters.id"), index=True
    )
    engine_name: Mapped[str] = mapped_column(String(100), index=True)
    engine_version_hash: Mapped[str] = mapped_column(String(64))

    decision_type: Mapped[DecisionType] = mapped_column(
        SQLEnum(DecisionType), nullable=False
    )
    reason_code: Mapped[ReasonCode] = mapped_column(SQLEnum(ReasonCode), nullable=False)

    physician_id: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    encounter: Mapped["EncounterModel"] = relationship("EncounterModel")


class ClinicalRequirement(Base):
    """
    Maps engine logic to clinical papers (Traceability).
    """

    __tablename__ = "clinical_traceability"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # e.g., 'CORE-001'
    source_title: Mapped[str] = mapped_column(String(255))
    source_doi: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    logic_digest: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

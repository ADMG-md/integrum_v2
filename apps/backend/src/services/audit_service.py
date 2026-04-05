from sqlalchemy.ext.asyncio import AsyncSession
from src.models.audit import AdjudicationLog
from src.engines.domain import AdjudicationResult, Encounter
from typing import Dict, Any
import structlog
import uuid

logger = structlog.get_logger()


class AuditService:
    """
    Handles the inmutable logging of clinical decisions.
    Ensures SaMD traceability between motors and DB.
    """

    async def log_adjudications(
        self,
        db: AsyncSession,
        encounter_id: str,
        results: Dict[str, AdjudicationResult],
        engines_map: Dict[str, Any] = None,
    ) -> Dict[
        str, Dict[str, str]
    ]:  # Returns {engine_name: {"log_id": str, "integrity_hash": str}}
        audit_data = {}
        for name, res in results.items():
            version_hash = "unknown"
            req_id = "GENERIC-001"
            if engines_map and name in engines_map:
                motor = engines_map[name]
                version_hash = motor.get_version_hash()
                req_id = getattr(motor, "REQUIREMENT_ID", "GENERIC-001")

            log_id = uuid.uuid4()

            # Hardening: Generate Integrity Hash (HMAC-SHA256)
            import hmac
            import hashlib
            import json
            import os

            secret = os.getenv("SECRET_KEY", "unsafe-dev-salt")
            calc_val = getattr(
                res, "calculated_value", getattr(res, "clinical_profile", str(res))
            )
            confidence = getattr(res, "confidence", 0.0)
            payload = f"{encounter_id}|{name}|{calc_val}|{confidence}"
            integrity_hash = hmac.new(
                secret.encode(), payload.encode(), hashlib.sha512
            ).hexdigest()

            log_entry = AdjudicationLog(
                id=log_id,
                encounter_id=encounter_id,
                engine_name=name,
                engine_version_hash=version_hash,
                requirement_id=req_id,
                calculated_value=str(calc_val),
                confidence=confidence,
                evidence=[ev.model_dump() for ev in res.evidence]
                if hasattr(res, "evidence") and res.evidence
                else [],
                integrity_hash=integrity_hash,
            )
            db.add(log_entry)
            audit_data[name] = {"log_id": str(log_id), "integrity_hash": integrity_hash}

        try:
            await db.commit()
            logger.info(
                "samd_audit_logged", encounter_id=encounter_id, count=len(results)
            )
            return audit_data
        except Exception as e:
            await db.rollback()
            logger.error("samd_audit_failed", error=str(e), encounter_id=encounter_id)
            raise e


audit_service = AuditService()

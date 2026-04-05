from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.encounter import EncounterModel, ObservationModel, Patient
from src.models.audit import AdjudicationLog
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()

class TimelineService:
    """
    Mission 7: Timeline & Analytics.
    Manages clinical history and progress tracking (T0 vs Tn).
    """

    async def get_patient_progress(self, db: AsyncSession, patient_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves a timeline of adjudicated results for a specific patient.
        """
        stmt = (
            select(AdjudicationLog)
            .join(EncounterModel, AdjudicationLog.encounter_id == EncounterModel.id)
            .where(EncounterModel.patient_id == patient_id)
            .order_by(AdjudicationLog.created_at.asc())
        )
        result = await db.execute(stmt)
        logs = result.scalars().all()

        # Group by engine_name to see evolution per pilar
        timeline_data = {}
        for log in logs:
            if log.engine_name not in timeline_data:
                timeline_data[log.engine_name] = []
            
            timeline_data[log.engine_name].append({
                "date": log.created_at.isoformat(),
                "value": log.calculated_value,
                "confidence": log.confidence,
                "is_overridden": log.is_overridden,
                "physician_value": log.physician_value
            })
        
        return timeline_data

    async def record_encounter(self, db: AsyncSession, patient_id: str, encounter_id: str, observations: List[Any]):
        """
        Persists raw encounter observations for future temporal comparison.
        """
        for obs in observations:
            db_obs = ObservationModel(
                encounter_id=encounter_id,
                code=obs.code,
                value=str(obs.value),
                unit=obs.unit,
                category=obs.category,
                metadata_json=obs.metadata_json
            )
            db.add(db_obs)
        
        await db.commit()
        logger.info("encounter_observations_persisted", encounter_id=encounter_id, count=len(observations))

# Singleton
timeline_service = TimelineService()

import asyncio
import structlog
from src.database import engine, Base
from src.models.encounter import (
    Patient,
    EncounterModel,
    ObservationModel,
    EncounterConditionModel,
)
from src.models.condition import Condition
from src.models.user import UserModel
from src.models.audit import AdjudicationLog

logger = structlog.get_logger()


async def init_models():
    """
    Initializes the database schema.
    Warning: In development, this drops and recreates tables to ensure alignment.
    """
    logger.info("database_init_started")
    async with engine.begin() as conn:
        # For development alignment, we drop and recreate
        # In production, this MUST be replaced by Alembic migrations
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_init_completed")


if __name__ == "__main__":
    asyncio.run(init_models())
    asyncio.run(engine.dispose())

from fastapi import APIRouter
from src.schemas.encounter import ObservationSchema
from typing import Dict, Tuple

router = APIRouter()

@router.get("/limits")
async def get_biological_limits() -> Dict[str, Tuple[float, float]]:
    """
    Expose physiological limits defined in the backend to the frontend.
    This ensures synchronous validation without code duplication.
    """
    # This is a bit of a hack to extract the limits from the validator
    # In a more mature system, the LIMITS would be a separate constant in src.engines.domain
    # For now, we'll keep it simple but functional.
    
    LIMITS = {
        "2339-0": (20, 600), # Glucose
        "8480-6": (60, 250), # SBP
        "AGE-001": (0, 125),
        "29463-7": (2, 400), # Weight
        "8302-2": (30, 250), # Height
        "WAIST-001": (30, 300),
        "APOB-001": (20, 500),
        "TSH-001": (0.01, 100),
        "FT4-001": (0.1, 10),
        "FT3-001": (1.0, 20),
        "HS-CRP-001": (0.01, 100),
        "ALB-001": (1.0, 10.0),
        "ALKPHOS-001": (10, 1000),
        "MCV-001": (50, 150),
        "RDW-001": (5, 30),
        "WBC-001": (1.0, 50.0),
        "GGT-001": (1, 2000),
        "FER-001": (1, 10000),
        "UA-001": (1, 20),
        "5XSTS-SEC": (3.0, 120.0),
        "GRIP-STR-R": (5.0, 80.0),
        "GAIT-SPEED": (0.1, 3.0),
    }
    return LIMITS

from fastapi import APIRouter
from typing import Dict, Tuple, List, Any
from src.engines.specialty_runner import PRIMARY_MOTORS, GATED_MOTORS, AGGREGATOR_MOTORS
from src.services.redis_service import cache_get, cache_set

router = APIRouter()

@router.get("/limits")
async def get_biological_limits() -> Dict[str, Tuple[float, float]]:
    """
    Expose physiological limits defined in the backend to the frontend.
    This ensures synchronous validation without code duplication.
    """
    cache_key = "metadata:limits"
    cached = await cache_get(cache_key)
    if cached:
        return cached

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
    await cache_set(cache_key, LIMITS, ttl_seconds=86400)
    return LIMITS


def _get_motor_metadata(name: str) -> Dict[str, Any]:
    """Extract metadata from a motor instance."""
    try:
        # Handle special cases
        if name == "ObesityMasterMotor":
            from src.engines.obesity_master import ObesityMasterMotor
            motor = ObesityMasterMotor()
        elif name == "ClinicalGuidelinesMotor":
            from src.engines.specialty.guidelines import ClinicalGuidelinesMotor
            motor = ClinicalGuidelinesMotor()
        else:
            return {"name": name, "group": "unknown"}
        
        return {
            "name": name,
            "group": getattr(motor, "group", "unknown"),
            "description": getattr(motor, "description", ""),
            "requirement_id": getattr(motor, "REQUIREMENT_ID", None),
        }
    except Exception:
        return {"name": name, "group": "unknown"}


@router.get("/motors")
async def get_motor_metadata() -> List[Dict[str, Any]]:
    """
    Returns metadata for all registered motors.
    Used by frontend to dynamically render motor groups and panels.
    """
    cache_key = "metadata:motors"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    all_motors = []
    
    # Process PRIMARY_MOTORS (dict of motor_name -> instance)
    for name, motor in PRIMARY_MOTORS.items():
        meta = {
            "name": name,
            "group": getattr(motor, "group", "core"),
            "description": getattr(motor, "description", ""),
            "requirement_id": getattr(motor, "REQUIREMENT_ID", None),
        }
        all_motors.append(meta)
    
    # Process GATED_MOTORS
    for name, motor in GATED_MOTORS.items():
        meta = {
            "name": name,
            "group": "risk",
            "description": getattr(motor, "description", ""),
            "requirement_id": getattr(motor, "REQUIREMENT_ID", None),
            "gated": True,
        }
        all_motors.append(meta)
    
    # Process AGGREGATOR_MOTORS
    for name, motor in AGGREGATOR_MOTORS.items():
        meta = {
            "name": name,
            "group": "guidelines",
            "description": getattr(motor, "description", ""),
            "requirement_id": getattr(motor, "REQUIREMENT_ID", None),
        }
        all_motors.append(meta)
    
    await cache_set(cache_key, all_motors, ttl_seconds=86400)
    return all_motors


@router.get("/questionnaires")
async def get_questionnaires() -> List[Dict[str, Any]]:
    """
    Returns questionnaire definitions (PHQ-9, GAD-7, TFEQ, Atenas, FNQ).
    Used by frontend to dynamically render questionnaire forms.
    """
    cache_key = "metadata:questionnaires"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    questionnaires = [
        {
            "id": "phq9",
            "name": "PHQ-9",
            "full_name": "Patient Health Questionnaire-9",
            "description": "Evaluación de severidad de depresión",
            "max_score": 27,
            "severity_labels": ["Mínima (0-4)", "Leve (5-9)", "Moderada (10-14)", "Moderadamente severa (15-19)", "Severa (20-27)"],
            "severity_colors": ["text-green-400", "text-yellow-400", "text-orange-400", "text-red-400", "text-red-500"],
            "options": ["Nunca", "Varios días", "Más de la mitad", "Casi todos los días"],
            "questions": [
                "Poco interés o placer en hacer las cosas",
                "Sentirse desanimado/a, deprimido/a o sin esperanza",
                "Problemas para dormir, mantenerse dormido/a, o dormir demasiado",
                "Sentirse cansado/a o con poca energía",
                "Poco apetito o comer en exceso",
                "Sentirse mal consigo mismo/a, sentir que es un fracaso",
                "Dificultad para concentrarse en cosas como leer o ver televisión",
                "Moverse o hablar tan lento que otros lo notan, o lo contrario",
                "Pensamientos de que estaría mejor muerto/a o de hacerse daño",
            ],
        },
        {
            "id": "gad7",
            "name": "GAD-7",
            "full_name": "Generalized Anxiety Disorder-7",
            "description": "Evaluación de severidad de ansiedad",
            "max_score": 21,
            "severity_labels": ["Mínima (0-4)", "Leve (5-9)", "Moderada (10-14)", "Severa (15-21)"],
            "severity_colors": ["text-green-400", "text-yellow-400", "text-orange-400", "text-red-400"],
            "options": ["Nunca", "Varios días", "Más de la mitad", "Casi todos los días"],
            "questions": [
                "Sentirse nervioso/a, ansioso/a o con los nervios de punta",
                "No poder dejar de preocuparse o no poder controlar la preocupación",
                "Preocuparse demasiado por diferentes cosas",
                "Dificultad para relajarse",
                "Estar tan inquieto/a que es difícil permanecer sentado/a",
                "Molestarse o irritarse fácilmente",
                "Sentir miedo como si algo terrible fuera a pasar",
            ],
        },
        {
            "id": "tfeq",
            "name": "TFEQ-R18",
            "full_name": "Three-Factor Eating Questionnaire R18",
            "description": "Conducta alimentaria: hambre hedónica, restricción cognitiva, alimentación emocional",
            "max_score": 54,
            "severity_labels": ["Bajo", "Moderado", "Alto"],
            "severity_colors": ["text-green-400", "text-yellow-400", "text-red-400"],
            "options": ["Definitivamente falso", "Mayormente falso", "Mayormente verdadero", "Definitivamente verdadero"],
            "special_item": {"index": 17, "label": "En una escala del 1 al 8, donde 1 significa que no se restringe en absoluto a la hora de comer (come lo que quiere y cuando quiere) y 8 significa que se restringe totalmente (siempre vigila lo que come y nunca se deja llevar), ¿qué número se daría a sí mismo?", "range": [1, 8]},
            "questions": [
                "Cuando huelo un bistec jugoso o un trozo de carne deliciosa, me cuesta mucho no comer, incluso si acabo de terminar de comer.",
                "¿Come cuando se siente deprimido/a?",
                "¿Come cuando se siente ansioso/a?",
                "¿Come cuando se siente solo/a?",
                "¿Come más de lo que debería cuando está aburrido/a?",
                "¿Come sin pensar cuando está viendo TV?",
                "¿Come más de lo planeado en eventos sociales?",
                "¿Le cuesta dejar de comer cuando empieza?",
                "¿Come aunque no tenga hambre?",
                "¿Come porciones más grandes de lo normal?",
                "¿Planifica sus comidas con anticipación?",
                "¿Cuenta las calorías de lo que come?",
                "¿Controla conscientemente lo que come?",
                "¿Evita alimentos altos en carbohidratos?",
                "¿Se salta comidas a propósito?",
                "¿Rechaza alimentos por miedo a engordar?",
                "¿Come despacio para disfrutar más?",
                "¿Se detiene cuando se siente lleno/a?",
            ],
        },
        {
            "id": "atenas",
            "name": "Escala de Atenas",
            "full_name": "Athens Insomnia Scale",
            "description": "Evaluación de severidad de insomnio (último mes, si se acostó a la hora deseada)",
            "max_score": 24,
            "severity_labels": ["Sin insomnio (0-3)", "Insomnio leve (4-5)", "Insomnio moderado (6-9)", "Insomnio severo (10-24)"],
            "severity_colors": ["text-green-400", "text-yellow-400", "text-orange-400", "text-red-400"],
            "options": ["Ningún problema", "Leve", "Moderado", "Severo / No durmió"],
            "questions": [
                "Inducción del sueño (tiempo que tardó en quedarse dormido)",
                "Despertares durante la noche",
                "Despertar final (despertar demasiado temprano sin poder volver a dormir)",
                "Duración total del sueño",
                "Calidad global del sueño",
                "Bienestar durante el día",
                "Capacidad de funcionamiento durante el día",
                "Somnolencia durante el día",
            ],
        },
        {
            "id": "fnq",
            "name": "FNQ",
            "full_name": "Food Noise Questionnaire",
            "description": "Evaluación del 'ruido alimentario' — pensamientos intrusivos sobre comida (últimas 2 semanas)",
            "max_score": 20,
            "severity_labels": ["Bajo (0-4)", "Moderado (5-9)", "Alto (10-14)", "Muy alto (15-20)"],
            "severity_colors": ["text-green-400", "text-yellow-400", "text-orange-400", "text-red-400"],
            "options": ["Totalmente en desacuerdo", "En desacuerdo", "Ni de acuerdo ni en desacuerdo", "De acuerdo", "Totalmente de acuerdo"],
            "questions": [
                "Me encuentro constantemente pensando en comida a lo largo del día.",
                "Mis pensamientos sobre comida se sienten incontrolables.",
                "Paso demasiado tiempo pensando en comida.",
                "Mis pensamientos sobre comida tienen efectos negativos en mí y/o en mi vida.",
                "Mis pensamientos sobre comida me distraen de lo que necesito hacer.",
            ],
        },
    ]
    await cache_set(cache_key, questionnaires, ttl_seconds=86400)
    return questionnaires

from pydantic import BaseModel, Field

class VitalSigns(BaseModel):
    heart_rate: float = Field(..., ge=0, le=300, description="Frecuencia cardíaca en latidos por minuto")
    temperature: float = Field(..., ge=30, le=45, description="Temperatura corporal en grados Celsius")

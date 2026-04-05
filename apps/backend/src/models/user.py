from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
import enum
import uuid
from src.database import Base


def _get_vault():
    from src.services.vault_service import vault_service

    return vault_service


class UserRole(str, enum.Enum):
    SUPERADMIN = "superadmin"
    ADMINSTAFF = "adminstaff"
    PHYSICIAN = "physician"
    NUTRITION_PHYSICIAN = "nutrition_physician"
    PSYCHOLOGIST = "psychologist"
    AUDITOR = "auditor"
    MEDICAL_DIRECTOR = "medical_director"
    EPS_MANAGER = "eps_manager"
    PATIENT = "patient"


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    _full_name_encrypted = Column("full_name", String(1024))

    tenant_id = Column(
        String(255), nullable=False, default="default-clinic", index=True
    )

    role = Column(String, default=UserRole.PHYSICIAN)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    last_login = Column(DateTime, nullable=True)

    @property
    def full_name(self):
        return _get_vault().decrypt(self._full_name_encrypted)

    @full_name.setter
    def full_name(self, value):
        self._full_name_encrypted = _get_vault().encrypt(value)

import asyncio
import os
import sys

# Add the project root to PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.database import DATABASE_URL, Base
from src.models.user import UserModel, UserRole
from src.models.audit import AdjudicationLog, ClinicalRequirement
from src.models.encounter import EncounterModel, Patient
from src.models.tenant import Tenant
from src.models.consent import PatientConsent
from src.services.auth_service import AuthService


async def init_prod_db():
    print("[Mission 11] Initializing Security Layer DB Suite...")
    engine = create_async_engine(DATABASE_URL, echo=False)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # NEW-02 fix: NEVER drop_all — it destroys all data in production.
    # For schema migrations, use Alembic. This script is ONLY for initial dev seeding.
    if os.getenv("ENVIRONMENT", "production").lower() != "development":
        raise RuntimeError(
            "CRITICAL: init_security_db.py must NOT run in production. "
            "Use Alembic migrations for schema changes."
        )

    async with engine.begin() as conn:
        # create_all is idempotent — safe to run multiple times (tables already existing are skipped)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Create Suite of Users for Multi-Role Testing

        # 1. Superadmin
        admin = UserModel(
            email="admin@integrum.ai",
            hashed_password=AuthService.get_password_hash("admin123"),
            full_name="Integrum Super Admin",
            role=UserRole.SUPERADMIN.value,
        )
        session.add(admin)

        # 2. Specialist Physician
        doctor = UserModel(
            email="doctor@integrum.ai",
            hashed_password=AuthService.get_password_hash("doctor123"),
            full_name="Dr. Precision (Endocrino)",
            role=UserRole.PHYSICIAN.value,
        )
        session.add(doctor)

        # 3. Patient
        patient = UserModel(
            email="paciente@ejemplo.com",
            hashed_password=AuthService.get_password_hash("paciente123"),
            full_name="Juan Paciente",
            role=UserRole.PATIENT.value,
        )
        session.add(patient)

        # 4. Auditor
        auditor = UserModel(
            email="auditor@regulatorio.gov",
            hashed_password=AuthService.get_password_hash("auditor123"),
            full_name="Auditor SaMD",
            role=UserRole.AUDITOR.value,
        )
        session.add(auditor)

        # 5. EPS Manager
        eps = UserModel(
            email="gerente@eps.com",
            hashed_password=AuthService.get_password_hash("gerente123"),
            full_name="Gerente Salud",
            role=UserRole.EPS_MANAGER.value,
        )
        session.add(eps)

        # Mission 10 & 12: Add default patients
        # Note: The 'external_id' setter now automatically calculates the blind index hash
        p1 = Patient(
            date_of_birth="1985-05-12",
            gender="female",
            email="elena@mail.com",
            phone="+57 321 0000001",
        )
        p1.external_id = "PAT-001"
        p1.full_name = "Elena Ramos"
        session.add(p1)

        p2 = Patient(
            date_of_birth="1978-11-20",
            gender="male",
            email="carlos@mail.com",
            phone="+57 321 0000002",
        )
        p2.external_id = "PAT-002"
        p2.full_name = "Carlos Ruiz"
        session.add(p2)

        p3 = Patient(
            date_of_birth="1992-03-15",
            gender="female",
            email="sofia@mail.com",
            phone="+57 321 0000003",
        )
        p3.external_id = "PAT-003"
        p3.full_name = "Sofía Méndez"
        session.add(p3)

        # Mission 12: Clinical Traceability Matrix (The "Citations")
        r1 = ClinicalRequirement(
            id="ACOSTA-2015",
            source_title="Acosta et al. | Selection of antiobesity medications based on phenotypes",
            source_doi="10.1038/oby.2014.248",
            logic_digest="Categorización fenotípica basada en saciedad (Hungry Brain), saciación (Hungry Gut), gasto energético (Slow Burn) y hambre emocional.",
        )
        session.add(r1)

        r2 = ClinicalRequirement(
            id="EOSS-2009",
            source_title="Sharma & Kushner | A proposed clinical staging system for obesity (EOSS)",
            source_doi="10.1038/ijo.2009.2",
            logic_digest="Clasificación de severidad (Estadios 0-4) basada en el impacto funcional y de salud sistémica, no solo en el IMC.",
        )
        session.add(r2)

        r3 = ClinicalRequirement(
            id="LEVINE-2018",
            source_title="Levine et al. | An epigenetic biomarker of aging (PhenoAge)",
            source_doi="10.18632/aging.101414",
            logic_digest="Cálculo de edad biológica basado en 9 biomarcadores metabólicos e inflamatorios más edad cronológica.",
        )
        session.add(r3)

        # 6. Médico Nutriólogo
        nutri = UserModel(
            email="nutri@integrum.ai",
            hashed_password=AuthService.get_password_hash("nutri123"),
            full_name="Dr. Metabol (Médico Nutriólogo)",
            role=UserRole.NUTRITION_PHYSICIAN.value,
        )
        session.add(nutri)

        await session.flush()

        # Mission 12: Legal Consents for default patients
        for p in [p1, p2, p3]:
            session.add(
                PatientConsent(
                    patient_id=p.id,
                    is_granted=True,
                    terms_version="2026.03.14-ES",
                    consent_type="SAMD_ANALYSIS_V1",
                )
            )

        await session.commit()
        print(
            "Created default security suite: admin, doctor, nutri, patient, auditor, eps_manager + 3 patients"
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_prod_db())
    print("Database initialization complete, connections disposed.")

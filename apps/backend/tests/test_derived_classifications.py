import pytest
from sqlalchemy import select
from src.database import SessionLocal, engine, Base
from src.models.encounter import Patient, EncounterModel, DerivedClassification, AxisType
from src.schemas.encounter import EncounterCreate, ObservationSchema, BiometricsSchema
from src.services.encounter_orchestrator import process_encounter
from src.models.user import UserModel, UserRole

@pytest.mark.anyio
async def test_derived_classifications_population():
    # 1. Setup DB tables
    import sqlalchemy as sa
    async with engine.begin() as conn:
        await conn.execute(sa.text("DROP TABLE IF EXISTS derived_classifications CASCADE"))
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        tenant_id = "test-tenant-derived"
        patient_id = "PAT-DERIVED-001"
        external_id = "1234567"
        
        stmt = select(Patient).where(Patient.id == patient_id)
        res = await db.execute(stmt)
        patient = res.scalar_one_or_none()
        
        if not patient:
            patient = Patient(
                id=patient_id,
                tenant_id=tenant_id,
            )
            patient.external_id = external_id
            patient.full_name = "John Doe"
            patient.date_of_birth = "1980-01-01"
            patient.gender = "female"
            db.add(patient)
            await db.flush()
            
            from src.models.consent import PatientConsent
            consent = PatientConsent(
                patient_id=patient_id,
                is_granted=True
            )
            db.add(consent)
            await db.commit()

        # Seed clinical_traceability dynamically to prevent FK violations
        from src.engines.specialty_runner import create_runner
        from src.models.audit import ClinicalRequirement
        
        runner = create_runner()
        req_ids = {"GENERIC-001", "LEVINE-2018", "ACOSTA-2021"}
        for motor in runner.get_all_motors():
            req_id = getattr(motor, "REQUIREMENT_ID", None)
            if req_id:
                req_ids.add(req_id)
                
        for req_id in req_ids:
            stmt = select(ClinicalRequirement).where(ClinicalRequirement.id == req_id)
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                db.add(ClinicalRequirement(
                    id=req_id,
                    source_title=f"Auto-seeded {req_id}",
                    logic_digest=f"Traceability path for {req_id}"
                ))
        await db.commit()

        # Create dummy user
        user = UserModel(
            id="usr-physician",
            email="physician@example.com",
            hashed_password="...",
            role=UserRole.PHYSICIAN,
            tenant_id=tenant_id
        )

        # 2. Process an encounter with valid data to trigger motors
        payload = EncounterCreate(
            patient_id=patient_id,
            reason_for_visit="Checkup",
            biometrics=BiometricsSchema(
                weight_kg=100.0,
                height_cm=180.0,
                waist_cm=105.0,
                systolic_bp=130,
                diastolic_bp=80
            ),
            observations=[
                ObservationSchema(code="BUFFET-KCAL", value=950.0),
            ]
        )

        result = await process_encounter(db, payload, user)
        enc_id = result["encounter_id"]

        # 3. Query DerivedClassification to verify it populated
        stmt_clf = select(DerivedClassification).where(DerivedClassification.encounter_id == enc_id)
        res_clf = await db.execute(stmt_clf)
        classifications = res_clf.scalars().all()

        assert len(classifications) > 0, "No classifications were derived!"
        
        # Check specific mapped axes
        axes = [c.axis for c in classifications]
        assert AxisType.A in axes, "Axis A (Acosta) was not populated"
        assert AxisType.E in axes, "Axis E (EOSS) was not populated"

        acosta_clf = next(c for c in classifications if c.axis == AxisType.A)
        assert acosta_clf.code == "A1", f"Acosta code should be A1, got {acosta_clf.code}"
        assert "A1 - Ingesta-Dominante" in acosta_clf.label
        assert acosta_clf.source_engine == "ATaxonomyMotor"
        assert acosta_clf.rule_version_semantic == "A_taxonomy_v0.1"

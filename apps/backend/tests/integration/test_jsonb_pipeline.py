import pytest
from sqlalchemy import select
from src.database import SessionLocal, engine, Base
from src.models.encounter import Patient, EncounterModel, DerivedClassification, AxisType
from src.schemas.encounter import EncounterCreate, ObservationSchema, BiometricsSchema
from src.domain.models import MetabolicPanelSchema, ClinicalHistory
from src.services.encounter_orchestrator import process_encounter
from src.models.user import UserModel, UserRole

@pytest.mark.anyio
async def test_jsonb_pipeline_persistence_and_retrieval():
    # Dispose pool to prevent loop mismatch
    await engine.dispose()
    
    # 1. Setup DB tables
    import sqlalchemy as sa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        tenant_id = "test-tenant-jsonb"
        patient_id = "PAT-JSONB-001"
        external_id = "7654321"
        
        stmt = select(Patient).where(Patient.id == patient_id)
        res = await db.execute(stmt)
        patient = res.scalar_one_or_none()
        
        if not patient:
            patient = Patient(
                id=patient_id,
                tenant_id=tenant_id,
            )
            patient.external_id = external_id
            patient.full_name = "Jane Doe"
            patient.date_of_birth = "1990-01-01"
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

        # Seed clinical_traceability dynamically
        from src.engines.specialty_runner import create_runner
        from src.models.audit import ClinicalRequirement
        
        runner = create_runner()
        req_ids = {"GENERIC-001", "LEVINE-2018", "ACOSTA-2021", "CD-CORE-001"}
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
            id="usr-physician-jsonb",
            email="physician-jsonb@example.com",
            hashed_password="...",
            role=UserRole.PHYSICIAN,
            tenant_id=tenant_id
        )

        # 2. Process an encounter with metabolic panel and history
        metabolic_payload = MetabolicPanelSchema(
            glucose_mg_dl=95.0,
            creatinine_mg_dl=0.8,
            hba1c_percent=5.4,
            ldl_mg_dl=120.0,
            total_cholesterol_mg_dl=200.0,
            triglycerides_mg_dl=150.0,
            hdl_mg_dl=50.0
        )
        
        history_payload = ClinicalHistory(
            has_type2_diabetes=False,
            has_hypertension=True,
            pregnancy_status="unknown"
        )

        payload = EncounterCreate(
            patient_id=patient_id,
            reason_for_visit="Annual Checkup",
            biometrics=BiometricsSchema(
                weight_kg=70.0,
                height_cm=165.0,
                waist_cm=80.0,
                systolic_bp=120,
                diastolic_bp=80
            ),
            metabolic=metabolic_payload,
            history=history_payload,
            observations=[]
        )

        result = await process_encounter(db, payload, user)
        enc_id = result["encounter_id"]

        # 3. Query the DB directly to check the JSONB columns
        stmt_enc = select(EncounterModel).where(EncounterModel.id == enc_id)
        res_enc = await db.execute(stmt_enc)
        db_encounter = res_enc.scalar_one()

        assert db_encounter.metabolic_panel_payload is not None
        assert db_encounter.metabolic_panel_payload["glucose_mg_dl"] == 95.0
        assert db_encounter.metabolic_panel_payload["ldl_mg_dl"] == 120.0
        assert db_encounter.clinical_history_payload is not None
        assert db_encounter.clinical_history_payload["has_hypertension"] is True
        assert db_encounter.clinical_history_payload["has_type2_diabetes"] is False

        # 4. Verify API response output (resembles retrieve details logic)
        from src.api.v1.endpoints.encounter import get_encounter
        api_response = await get_encounter(enc_id, db, user)
        
        assert "metabolic_panel_payload" in api_response
        assert api_response["metabolic_panel_payload"]["glucose_mg_dl"] == 95.0
        assert "clinical_history_payload" in api_response
        assert api_response["clinical_history_payload"]["has_hypertension"] is True


@pytest.mark.anyio
async def test_pregnancy_safety_gates():
    # Dispose pool to prevent loop mismatch
    await engine.dispose()
    
    # 1. Setup DB tables
    import sqlalchemy as sa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        tenant_id = "test-tenant-preg"
        patient_id = "PAT-PREG-001"
        external_id = "9998887"
        
        stmt = select(Patient).where(Patient.id == patient_id)
        res = await db.execute(stmt)
        patient = res.scalar_one_or_none()
        
        if not patient:
            patient = Patient(
                id=patient_id,
                tenant_id=tenant_id,
            )
            patient.external_id = external_id
            patient.full_name = "Alice Smith"
            patient.date_of_birth = "1995-05-05"
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

        # Seed clinical requirements dynamically to prevent FK violations
        from src.engines.specialty_runner import create_runner
        from src.models.audit import ClinicalRequirement
        
        runner = create_runner()
        req_ids = {"GENERIC-001", "LEVINE-2018", "ACOSTA-2021", "CD-CORE-001"}
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
            id="usr-physician-preg",
            email="physician-preg@example.com",
            hashed_password="...",
            role=UserRole.PHYSICIAN,
            tenant_id=tenant_id
        )

        # 2. Process an encounter for a pregnant patient with conditions that would normally trigger AOM/Statins
        metabolic_payload = MetabolicPanelSchema(
            glucose_mg_dl=130.0,
            creatinine_mg_dl=0.9,
            ldl_mg_dl=180.0,
            total_cholesterol_mg_dl=260.0,
            triglycerides_mg_dl=150.0,
            hdl_mg_dl=40.0
        )
        
        history_payload = ClinicalHistory(
            has_type2_diabetes=True,
            has_hypertension=True,
            pregnancy_status="pregnant" # Blocker
        )

        payload = EncounterCreate(
            patient_id=patient_id,
            reason_for_visit="Pregnancy Follow-up",
            biometrics=BiometricsSchema(
                weight_kg=75.0,
                height_cm=160.0,
                waist_cm=90.0,
                systolic_bp=140,
                diastolic_bp=90
            ),
            metabolic=metabolic_payload,
            history=history_payload,
            observations=[]
        )

        result = await process_encounter(db, payload, user)
        results = result["results"]

        # 3. Assert that CVDReclassifierMotor and SGLT2iBenefitMotor did not run (suppressed by safety gate)
        assert "CVDReclassifierMotor" not in results
        assert "SGLT2iBenefitMotor" not in results

import asyncio
from src.database import SessionLocal
from src.models.audit import ClinicalRequirement
from sqlalchemy import select

async def seed_traceability():
    requirements = [
        {"id": "ACOSTA-2015", "source_title": "Acosta et al. 2015 / 2021 Adaptation", "source_doi": "10.1002/oby.23120", "logic_digest": "Metabolic Phenotyping based on physiological triggers."},
        {"id": "EOSS-2009", "source_title": "Edmonton Obesity Staging System", "source_doi": "10.1503/cmaj.081177", "logic_digest": "Staging based on end-organ damage and clinical risk."},
        {"id": "HTN-SEC-2024", "source_title": "Hypertension Secondary Screening", "source_doi": "N/A", "logic_digest": "Screening for secondary causes of hypertension."},
        {"id": "LEVINE-PHENOAGE-2018", "source_title": "Levine Phenotypic Age", "source_doi": "10.18632/aging.101414", "logic_digest": "Biological age calculation using biochemical markers."},
        {"id": "KLEIBER-1961", "source_title": "Kleiber's Law (The Fire of Life)", "source_doi": "N/A", "logic_digest": "Allometric scaling for BMR and drug dosing."},
        {"id": "AROSE-2024-CVD-RISK", "source_title": "AROSE CVD Risk / Lancet 2024", "source_doi": "N/A", "logic_digest": "Precision CVD risk assessment using WHtR."},
        {"id": "JAMA-MARKOV-METS", "source_title": "JAMA Markov MetS Simulation", "source_doi": "10.1001/jamanetworkopen.2024", "logic_digest": "Disease progression modeling via Markov states."},
        {"id": "SAFE-IP-OSA", "source_title": "Safe-IP Protocol for OSA", "source_doi": "N/A", "logic_digest": "Pathophysiology-based sleep apnea risk assessment."},
        {"id": "GENERIC-001", "source_title": "Generic Clinical Observation", "source_doi": "N/A", "logic_digest": "Standardized capture of non-engine-specific clinical data."}
    ]
    
    async with SessionLocal() as db:
        for req in requirements:
            stmt = select(ClinicalRequirement).where(ClinicalRequirement.id == req["id"])
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                db.add(ClinicalRequirement(**req))
        
        await db.commit()
        print("✅ Clinical Traceability seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_traceability())

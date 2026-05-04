"""
Drug Interaction Motor — checks medication safety against conditions, renal function,
and drug-drug interactions using a static in-memory knowledge base.

REQUIREMENT_ID: DRUG-INTERACTION
SOURCE: FDA Labels, Lexicomp, Micromedex (extracted 2026-04-03)
"""

from src.engines.specialty.drug_knowledge import (
    MEDICATIONS,
    INTERACTIONS,
    CONTRAINDICATIONS,
    RENAL_DOSING,
    MED_NAME_TO_ID,
    ID_TO_MED_NAME,
)
from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
    safe_float,
)
from typing import Tuple, List, Dict, Any, Optional

# ============================================================
# Fuzzy medication name matching (Spanish/English variants)

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel
# ============================================================

_SYNONYM_MAP: Dict[str, str] = {
    "semaglutida": "semaglutide",
    "tirzepatida": "tirzepatide",
    "metformina": "metformin",
    "empagliflozina": "empagliflozin",
    "insulina_glargina": "insulin_glargine",
    "insulina_glargine": "insulin_glargine",
    "atorvastatina": "atorvastatin",
    "naltrexona": "naltrexone",
    "liraglutida": "liraglutide",
    "dulaglutida": "dulaglutide",
    "dapagliflozina": "dapagliflozin",
    "canagliflozina": "canagliflozin",
    "enalapril": "enalapril",
    "lisinopril": "lisinopril",
    "losartan": "losartan",
    "amlodipino": "amlodipine",
    "amlodipine": "amlodipine",
    "furosemida": "furosemide",
    "hydrochlorothiazide": "hydrochlorothiazide",
    "hidroclorotiazida": "hydrochlorothiazide",
    "omeprazol": "omeprazole",
    "omeprazole": "omeprazole",
    "sertralina": "sertraline",
    "sertraline": "sertraline",
    "fluoxetina": "fluoxetine",
    "fluoxetine": "fluoxetine",
    "citalopram": "citalopram",
    "escitalopram": "escitalopram",
    "amiodarona": "amiodarone",
    "amiodarone": "amiodarone",
    "azitromicina": "azithromycin",
    "azithromycin": "azithromycin",
    "levofloxacino": "levofloxacin",
    "levofloxacin": "levofloxacin",
    "ondansetron": "ondansetron",
    "ondansetrón": "ondansetron",
    "tramadol": "tramadol",
    "gabapentina": "gabapentin",
    "gabapentin": "gabapentin",
    "pregabalina": "pregabalin",
    "pregabalin": "pregabalin",
    "topiramato": "topiramate",
    "topiramate": "topiramate",
    "warfarina": "warfarin",
    "warfarin": "warfarin",
    "apixaban": "apixaban",
    "rivaroxaban": "rivaroxaban",
    "clopidogrel": "clopidogrel",
    "aspirina": "aspirin",
    "aspirin": "aspirin",
    "ibuprofeno": "ibuprofen",
    "ibuprofen": "ibuprofen",
    "naproxeno": "naproxen",
    "naproxen": "naproxen",
    "diclofenaco": "diclofenac",
    "diclofenac": "diclofenac",
    "prednisona": "prednisone",
    "prednisone": "prednisone",
    "dexametasona": "dexamethasone",
    "dexamethasone": "dexamethasone",
    "levothyroxine": "levothyroxine",
    "levotiroxina": "levothyroxine",
    "carbamazepina": "carbamazepine",
    "carbamazepine": "carbamazepine",
    "valproato": "valproate",
    "valproic_acid": "valproic_acid",
    "ácido_valproico": "valproic_acid",
    "lamotrigina": "lamotrigine",
    "lamotrigine": "lamotrigine",
    "quetiapina": "quetiapine",
    "quetiapine": "quetiapine",
    "olanzapina": "olanzapine",
    "olanzapine": "olanzapine",
    "risperidona": "risperidone",
    "risperidone": "risperidone",
    "aripiprazol": "aripiprazole",
    "aripiprazole": "aripiprazole",
    "metoprolol": "metoprolol",
    "carvedilol": "carvedilol",
    "propranolol": "propranolol",
    "espironolactona": "spironolactone",
    "spironolactone": "spironolactone",
    "clonidina": "clonidine",
    "clonidine": "clonidine",
    "sildenafilo": "sildenafil",
    "sildenafil": "sildenafil",
    "tadalafilo": "tadalafil",
    "tadalafil": "tadalafil",
    "finasterida": "finasteride",
    "finasteride": "finasteride",
    "testosterona": "testosterone",
    "testosterone": "testosterone",
    "estrógeno": "estrogen",
    "estrogen": "estrogen",
    "progesterona": "progesterone",
    "progesterone": "progesterone",
    "medroxiprogesterona": "medroxyprogesterone",
    "medroxyprogesterone": "medroxyprogesterone",
    "drospirenona": "drospirenone",
    "drospirenone": "drospirenone",
    "etinilestradiol": "ethinyl_estradiol",
    "ethinyl_estradiol": "ethinyl_estradiol",
    "levonorgestrel": "levonorgestrel",
    "noretindrona": "norethindrone",
    "norethindrone": "norethindrone",
}


def _normalize_med_name(raw: str) -> str:
    return raw.lower().strip().replace(" ", "_").replace("-", "_")


def _match_medication(raw_name: str) -> Optional[str]:
    """Match a medication name (Spanish/English) to a canonical key in MEDICATIONS."""
    normalized = _normalize_med_name(raw_name)

    if normalized in MEDICATIONS:
        return normalized

    if normalized in _SYNONYM_MAP:
        canonical = _SYNONYM_MAP[normalized]
        if canonical in MEDICATIONS:
            return canonical

    for key in MEDICATIONS:
        if key in normalized or normalized in key:
            return key

    for synonym, canonical in _SYNONYM_MAP.items():
        if synonym in normalized or normalized in synonym:
            if canonical in MEDICATIONS:
                return canonical

    return None


# ============================================================
# Motor
# ============================================================


class DrugInteractionMotor(BaseClinicalMotor):
    """
    Drug Interaction & Safety Motor.

    Checks all current medications against:
    1. Drug-drug interactions (severity, mechanism, management)
    2. Contraindications by condition (ICD-10)
    3. Renal dose adjustments (eGFR-based)
    4. Pregnancy safety (teratogenic medications)
    5. QT prolongation aggregation
    6. Obesity-inducing medications audit

    Uses a static in-memory knowledge base (drug_knowledge.py).
    No I/O, no database, no network — pure deterministic function.

    REQUIREMENT_ID: DRUG-INTERACTION
    """

    REQUIREMENT_ID = "DRUG-INTERACTION"
    ENGINE_NAME = "DrugInteractionMotor"
    ENGINE_VERSION = "2.0.0"

    def get_version_hash(self) -> str:
        return f"{self.ENGINE_NAME}-v{self.ENGINE_VERSION}"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        if not encounter.medications:
            return False, "No medications to evaluate."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        critical_alerts: List[str] = []
        major_alerts: List[str] = []
        moderate_alerts: List[str] = []
        actions: List[ActionItem] = []
        evidence: List[ClinicalEvidence] = []
        qt_meds: List[str] = []
        obesity_meds: List[str] = []

        condition_codes = {c.code for c in encounter.conditions}
        if encounter.history:
            if encounter.history.has_type2_diabetes:
                condition_codes.add("E11")
            if encounter.history.has_hypertension:
                condition_codes.add("I10")

        matched_meds: List[Tuple[str, Dict[str, Any]]] = []
        for med in encounter.medications:
            canonical = _match_medication(med.name)
            if canonical:
                matched_meds.append((canonical, MEDICATIONS[canonical]))
            dose = getattr(med, "dose_amount", "") or ""
            freq = getattr(med, "frequency", "") or ""
            evidence.append(
                ClinicalEvidence(
                    type="Medication",
                    code=med.code or "CUSTOM",
                    value=med.name,
                    display=f"{med.name} {dose} {freq}".strip(),
                )
            )

        med_ids = [MEDICATIONS[name]["id"] for name, _ in matched_meds]

        # 1. Drug-Drug Interactions
        for i, (name_a, data_a) in enumerate(matched_meds):
            id_a = data_a["id"]
            for j in range(i + 1, len(matched_meds)):
                name_b = matched_meds[j][0]
                id_b = matched_meds[j][1]["id"]
                pair = (min(id_a, id_b), max(id_a, id_b))
                if pair in INTERACTIONS:
                    inter = INTERACTIONS[pair]
                    severity = inter["severity"]
                    msg = (
                        f"{name_a} + {name_b}: {inter['effect']} "
                        f"[{inter['mechanism']}] — {inter['management']}"
                    )
                    if severity == "critical":
                        critical_alerts.append(msg)
                    elif severity == "major":
                        major_alerts.append(msg)
                    else:
                        moderate_alerts.append(msg)
                    actions.append(
                        ActionItem(
                            category="diagnostic",
                            priority="high"
                            if severity in ("critical", "major")
                            else "medium",
                            task=f"Revisar interacción {name_a} + {name_b}",
                            rationale=inter["management"],
                        )
                    )

        # 2. Contraindications by Condition
        for cond_code in condition_codes:
            if cond_code in CONTRAINDICATIONS:
                for contra in CONTRAINDICATIONS[cond_code]:
                    if contra["med_id"] in med_ids:
                        med_name = ID_TO_MED_NAME.get(
                            contra["med_id"], f"med_id_{contra['med_id']}"
                        )
                        severity = contra["severity"]
                        msg = (
                            f"CONTRAINDICACIÓN: {med_name} en {cond_code} — "
                            f"{contra['rationale']}. Alternativa: {contra['alt']}"
                        )
                        if severity == "absolute":
                            critical_alerts.append(msg)
                        else:
                            major_alerts.append(msg)
                        actions.append(
                            ActionItem(
                                category="diagnostic",
                                priority="high",
                                task=f"Evaluar suspensión de {med_name} ({cond_code})",
                                rationale=contra["rationale"],
                            )
                        )

        # 3. Renal Dosing
        egfr_obs = encounter.get_observation("EGFR-001")
        egfr = safe_float(egfr_obs.value) if egfr_obs else None

        if egfr is not None:
            for name, data in matched_meds:
                med_id = data["id"]
                if med_id in RENAL_DOSING:
                    for adj in RENAL_DOSING[med_id]:
                        if adj["min"] <= egfr < adj["max"]:
                            msg = (
                                f"Ajuste renal {name}: eGFR={egfr:.0f} mL/min — "
                                f"{adj['adjustment']}. {adj['notes']}"
                            )
                            if "contraindicated" in adj["adjustment"].lower():
                                critical_alerts.append(msg)
                            else:
                                moderate_alerts.append(msg)
                            actions.append(
                                ActionItem(
                                    category="pharmacological",
                                    priority="high"
                                    if "contraindicated" in adj["adjustment"].lower()
                                    else "medium",
                                    task=f"Ajustar dosis de {name} (eGFR={egfr:.0f})",
                                    rationale=adj["adjustment"],
                                )
                            )
                            break

        # 4. Pregnancy Safety
        pregnancy_status = encounter.metadata.get("pregnancy_status") if encounter.metadata else None
        if pregnancy_status == "positive":
            for name, data in matched_meds:
                if data.get("teratogenic"):
                    preg_cat = data.get("preg_cat", "unknown")
                    msg = (
                        f"RIESGO TERATOGÉNICO: {name} — Categoría {preg_cat}. "
                        f"Consultar obstetra antes de continuar."
                    )
                    if preg_cat in ("X", "D"):
                        critical_alerts.append(msg)
                    else:
                        major_alerts.append(msg)
                    actions.append(
                        ActionItem(
                            category="pharmacological",
                            priority="high",
                            task=f"Evaluar riesgo/beneficio de {name} en embarazo",
                            rationale=f"Categoría embarazo: {preg_cat}",
                        )
                    )

        # 5. QT Prolongation Aggregation
        for name, data in matched_meds:
            if data.get("qt_risk") in ("high", "moderate"):
                qt_meds.append(name)

        if len(qt_meds) >= 2:
            msg = f"Riesgo QT prolongado (agregación): {', '.join(qt_meds)}"
            major_alerts.append(msg)
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="high",
                    task="Obtener ECG basal y monitoreo QTc",
                    rationale=f"{len(qt_meds)} fármacos con riesgo QT",
                )
            )

        # 6. Obesity-Inducing Medications Audit
        for name, data in matched_meds:
            if data.get("weight_effect") == "gain":
                avg_change = data.get("avg_loss", 0)
                obesity_meds.append(f"{name} (+{abs(avg_change)}kg promedio)")

        if obesity_meds:
            moderate_alerts.append(
                f"Medicamentos obesogénicos: {'; '.join(obesity_meds)}"
            )
            actions.append(
                ActionItem(
                    category="lifestyle",
                    priority="medium",
                    task="Evaluar alternativas no obesogénicas para medicamentos actuales",
                    rationale=f"Medicamentos que aumentan peso: {'; '.join(obesity_meds)}",
                )
            )

        # Classification
        n_critical = len(critical_alerts)
        n_major = len(major_alerts)
        n_moderate = len(moderate_alerts)

        if n_critical > 0:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"{n_critical} alerta(s) CRÍTICA(S) de seguridad farmacológica"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.PROXY_MARKER]
        elif n_major > 0:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"{n_major} interacción(es) MAYOR(ES) detectada(s)"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.PROXY_MARKER]
        elif n_moderate > 0:
            estado = "PROBABLE_WARNING"
            verdict = f"{n_moderate} interacción(es) MODERADA(S) detectada(s)"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.PROXY_MARKER]
        else:
            estado = "INDETERMINATE_LOCKED"
            verdict = "No evaluable — base de datos limitada"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.PROXY_MARKER]
            explanation = (
                "La combinación de medicamentos no se encuentra en la base de datos "
                "embebida. Consultar base de datos completa (Lexicomp/Micromedex) antes "
                "de prescribir. Esta evaluación NO garantiza ausencia de interacciones."
            )

        all_findings = critical_alerts + major_alerts + moderate_alerts
        if all_findings:
            explanation = "; ".join(all_findings)
        else:
            explanation = verdict

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=evidence,
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            dato_faltante="Base de datos de interacciones: cobertura limitada. No sustituye Lexicomp ni Micromedex."
            if estado == "INDETERMINATE_LOCKED"
            else None,
            explanation=explanation,
            action_checklist=actions,
            metadata={
                "critical_alerts": critical_alerts,
                "major_alerts": major_alerts,
                "moderate_alerts": moderate_alerts,
                "qt_meds": qt_meds,
                "obesity_meds": obesity_meds,
                "n_medications_evaluated": len(matched_meds),
                "db_coverage": "limited",
            },
        )

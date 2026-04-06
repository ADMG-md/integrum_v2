"""
Drug Interaction Motor — checks medication safety against conditions, renal function,
and drug-drug interactions using embedded SQLite database.
"""

import sqlite3
import os
from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
    safe_float,
)
from typing import Tuple, List, Dict, Any

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..",
    "data",
    "drug_interactions.db",
)


def _get_db() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        sql_path = DB_PATH.replace(".db", ".sql")
        if os.path.exists(sql_path):
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            conn = sqlite3.connect(DB_PATH)
            with open(sql_path) as f:
                conn.executescript(f.read())
            conn.commit()
            return conn
        raise FileNotFoundError(f"Drug interaction database not found at {DB_PATH}")
    return sqlite3.connect(DB_PATH)


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

    Uses embedded SQLite database for portability.
    Database initialized from drug_interactions.sql on first run.

    REQUIREMENT_ID: DRUG-INTERACTION
    """

    REQUIREMENT_ID = "DRUG-INTERACTION"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        if not encounter.medications:
            return False, "No medications to evaluate."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        conn = _get_db()
        cursor = conn.cursor()

        findings: List[str] = []
        actions: List[ActionItem] = []
        evidence: List[ClinicalEvidence] = []
        critical_alerts: List[str] = []
        major_alerts: List[str] = []
        moderate_alerts: List[str] = []

        # Build medication name lookup
        med_names = []
        for med in encounter.medications:
            name = med.name.lower().replace(" ", "_")
            med_names.append(name)

        # 1. Drug-Drug Interactions
        if len(med_names) >= 2:
            placeholders = ",".join(["?"] * len(med_names))
            cursor.execute(
                f"""
                SELECT m1.generic_name, m2.generic_name, di.severity, di.mechanism,
                       di.clinical_effect, di.management, di.evidence_level
                FROM drug_interactions di
                JOIN medications m1 ON di.drug_a_id = m1.id
                JOIN medications m2 ON di.drug_b_id = m2.id
                WHERE m1.generic_name IN ({placeholders})
                  AND m2.generic_name IN ({placeholders})
                  AND m1.generic_name != m2.generic_name
            """,
                med_names + med_names,
            )

            for row in cursor.fetchall():
                (
                    drug_a,
                    drug_b,
                    severity,
                    mechanism,
                    effect,
                    management,
                    evidence_level,
                ) = row
                alert = f"{drug_a} + {drug_b}: {effect} ({severity})"
                if severity == "contraindicated":
                    critical_alerts.append(alert)
                    actions.append(
                        ActionItem(
                            category="pharmacological",
                            priority="critical",
                            task=f"CONTRAINDICADO: {drug_a} + {drug_b}",
                            rationale=f"{mechanism}. {effect}. Manejo: {management}",
                        )
                    )
                elif severity == "major":
                    major_alerts.append(alert)
                    actions.append(
                        ActionItem(
                            category="pharmacological",
                            priority="high",
                            task=f"Interacción mayor: {drug_a} + {drug_b}",
                            rationale=f"{mechanism}. {effect}. Manejo: {management}",
                        )
                    )
                elif severity == "moderate":
                    moderate_alerts.append(alert)

        # 2. Contraindications by condition
        h = encounter.history
        if h:
            condition_codes = []
            for cond in encounter.conditions:
                condition_codes.append(cond.code)

            if condition_codes:
                placeholders = ",".join(["?"] * len(condition_codes))
                cursor.execute(
                    f"""
                    SELECT m.generic_name, c.condition_name, c.severity, c.rationale,
                           c.alternative_medications
                    FROM contraindications c
                    JOIN medications m ON c.medication_id = m.id
                    WHERE c.condition_code IN ({placeholders})
                """,
                    condition_codes,
                )

                for row in cursor.fetchall():
                    med_name, cond_name, severity, rationale, alternatives = row
                    if med_name.lower() in [n.lower() for n in med_names]:
                        if severity == "absolute":
                            critical_alerts.append(
                                f"{med_name} contraindicado en {cond_name}"
                            )
                            actions.append(
                                ActionItem(
                                    category="pharmacological",
                                    priority="critical",
                                    task=f"SUSPENDER {med_name} — contraindicado en {cond_name}",
                                    rationale=f"{rationale}. Alternativas: {alternatives or 'Consultar farmacología'}",
                                )
                            )
                        elif severity == "relative":
                            major_alerts.append(
                                f"{med_name} con precaución en {cond_name}"
                            )

        # 3. Renal dose adjustments
        egfr = encounter.egfr_ckd_epi
        if egfr and med_names:
            placeholders = ",".join(["?"] * len(med_names))
            cursor.execute(
                f"""
                SELECT m.generic_name, rd.dose_adjustment, rd.monitoring, rd.notes
                FROM renal_dosing rd
                JOIN medications m ON rd.medication_id = m.id
                WHERE m.generic_name IN ({placeholders})
                  AND ? BETWEEN rd.egfr_min AND rd.egfr_max
            """,
                med_names + [egfr],
            )

            for row in cursor.fetchall():
                med_name, adjustment, monitoring, notes = row
                if med_name.lower() in [n.lower() for n in med_names]:
                    if "contraindicated" in adjustment.lower():
                        critical_alerts.append(
                            f"{med_name} contraindicado (eGFR {egfr})"
                        )
                        actions.append(
                            ActionItem(
                                category="pharmacological",
                                priority="critical",
                                task=f"SUSPENDER {med_name} — eGFR {egfr}",
                                rationale=f"Ajuste: {adjustment}. {notes or ''}",
                            )
                        )
                    else:
                        major_alerts.append(f"{med_name}: ajustar dosis (eGFR {egfr})")
                        actions.append(
                            ActionItem(
                                category="pharmacological",
                                priority="high",
                                task=f"Ajustar dosis de {med_name}: {adjustment}",
                                rationale=f"eGFR: {egfr}. {notes or ''}. Monitoreo: {monitoring or 'Según protocolo'}",
                            )
                        )

        # 4. Pregnancy safety
        pregnancy = getattr(h, "pregnancy_status", "unknown") if h else "unknown"
        if pregnancy == "pregnant" and med_names:
            placeholders = ",".join(["?"] * len(med_names))
            cursor.execute(
                f"""
                SELECT m.generic_name, m.pregnancy_category
                FROM medications m
                WHERE m.generic_name IN ({placeholders})
                  AND m.is_teratogenic = 1
            """,
                med_names,
            )

            for row in cursor.fetchall():
                med_name, category = row
                if med_name.lower() in [n.lower() for n in med_names]:
                    critical_alerts.append(
                        f"{med_name} teratogénico (categoría {category}) — EMBARAZO"
                    )
                    actions.append(
                        ActionItem(
                            category="pharmacological",
                            priority="critical",
                            task=f"SUSPENDER {med_name} — embarazo (categoría {category})",
                            rationale="Medicamento teratogénico contraindicado en embarazo.",
                        )
                    )

        # 4b. Suicide risk gate for bupropion-containing medications
        # FDA Black Box Warning: suicidality in young adults
        bupropion_meds = [
            m
            for m in med_names
            if "bupropion" in m.lower() or "naltrexone_bupropion" in m.lower()
        ]
        if bupropion_meds:
            phq9_item_9 = None
            if h and hasattr(h, "phq9_item_9_score"):
                phq9_item_9 = h.phq9_item_9_score
            if phq9_item_9 is not None and phq9_item_9 > 0:
                for med_name in bupropion_meds:
                    critical_alerts.append(
                        f"{med_name} CONTRAINDICADO: PHQ-9 Item 9 = {phq9_item_9} (riesgo suicida)"
                    )
                    actions.append(
                        ActionItem(
                            category="pharmacological",
                            priority="critical",
                            task=f"CONTRAINDICADO: {med_name} — riesgo suicida detectado (PHQ-9 Item 9 = {phq9_item_9})",
                            rationale="FDA Black Box Warning: bupropion aumenta riesgo de suicidio en adultos jóvenes. Requiere revisión clínica.",
                        )
                    )

        # 5. QT prolongation aggregation
        qt_meds = []
        if med_names:
            placeholders = ",".join(["?"] * len(med_names))
            cursor.execute(
                f"""
                SELECT m.generic_name, m.qt_prolongation_risk
                FROM medications m
                WHERE m.generic_name IN ({placeholders})
                  AND m.qt_prolongation_risk IN ('moderate', 'high')
            """,
                med_names,
            )

            for row in cursor.fetchall():
                med_name, risk = row
                qt_meds.append(f"{med_name} ({risk})")

            if len(qt_meds) >= 2:
                major_alerts.append(f"Riesgo QT prolongado: {', '.join(qt_meds)}")
                actions.append(
                    ActionItem(
                        category="diagnostic",
                        priority="high",
                        task="Obtener ECG — múltiples medicamentos con riesgo QT",
                        rationale=f"Medicamentos: {', '.join(qt_meds)}. Riesgo de Torsades de Pointes.",
                    )
                )

        # 6. Obesity-inducing medications audit
        obesity_meds = []
        if med_names:
            placeholders = ",".join(["?"] * len(med_names))
            cursor.execute(
                f"""
                SELECT m.generic_name, m.weight_effect, m.avg_weight_change_kg
                FROM medications m
                WHERE m.generic_name IN ({placeholders})
                  AND m.is_obesity_inducing = 1
            """,
                med_names,
            )

            for row in cursor.fetchall():
                med_name, effect, weight_change = row
                obesity_meds.append(f"{med_name} (+{weight_change}kg promedio)")

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

        # Build evidence
        for med in encounter.medications:
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

        # Classification
        n_critical = len(critical_alerts)
        n_major = len(major_alerts)
        n_moderate = len(moderate_alerts)

        if n_critical > 0:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"{n_critical} alerta(s) CRÍTICA(S) de seguridad farmacológica"
            confidence = 0.95
        elif n_major > 0:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"{n_major} interacción(es) MAYOR(ES) detectada(s)"
            confidence = 0.90
        elif n_moderate > 0:
            estado = "PROBABLE_WARNING"
            verdict = f"{n_moderate} interacción(es) MODERADA(S) detectada(s)"
            confidence = 0.85
        else:
            estado = "INDETERMINATE_LOCKED"
            verdict = "No evaluable — base de datos limitada"
            confidence = 0.30
            explanation = (
                "La combinación de medicamentos no se encuentra en la base de datos "
                "embebida. Consultar base de datos completa (Lexicomp/Micromedex) antes "
                "de prescribir. Esta evaluación NO garantiza ausencia de interacciones."
            )

        all_findings = critical_alerts + major_alerts + moderate_alerts
        if all_findings:
            explanation = "; ".join(all_findings)

        conn.close()

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=evidence,
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            dato_faltante="Base de datos de interacciones: cobertura limitada a 53 fármacos. No sustituye Lexicomp ni Micromedex."
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
                "n_medications_evaluated": len(med_names),
                "db_coverage": "limited",
            },
        )

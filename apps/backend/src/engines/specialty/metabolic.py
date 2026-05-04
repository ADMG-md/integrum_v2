"""
Metabolic Precision Motor - Insulin Resistance & Beta-Cell Function

Evidence:
- Ahlqvist et al., 2018. Lancet Diabetes Endocrinol 6(5): 361-369. (SIDD/SIRD clusters)
- Matthews et al., 1985. Diabetologia 28: 412-419. (HOMA-IR)
- Vasques et al., 2011. Diabetes Care 34(11): 2432-2434. (TyG index)
- Bello-Chavolla et al., 2018. J Clin Endocrinol Metab 103(11): 4108-4116. (METS-IR)
- ADA Standards of Care, 2024. Diabetes Care 47(Suppl 1). (HbA1c, glucose thresholds)
- WHO Obesity Classification, 2000. (BMI thresholds)
- SMI thresholds: Baumgartner et al., 1998. Am J Epidemiol 147(8): 755-763.
- FIB-4: Sterling et al., 2006. Hepatology 43(6): 1290-1298.

REQUIREMENT_ID: METABOLIC-PRECISION
"""
from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel
from typing import Tuple
import math

# === Clinical Thresholds (with citations) ===
# Obesity phenotyping (WHO, 2000)
BMI_OBESE_THRESHOLD: float = 30.0
BMI_NORMAL_UPPER: float = 25.0

# Inflammatory adiposopathy (Pearson et al., 2003 + HOMA-IR consensus)
CRP_INFLAMMATORY_FLOOR: float = 1.0
CRP_PROTECTIVE_CEILING: float = 0.5
HOMA_IR_RESISTANCE_FLOOR: float = 2.5
HOMA_IR_SENSITIVE_CEILING: float = 2.0

# Visceral adiposity (TOFI/MUNW phenotype)
VISCERAL_FAT_TOFI_THRESHOLD: float = 10.0

# Sarcopenia (Baumgartner et al., 1998)
SMI_MALE_THRESHOLD: float = 7.0
SMI_FEMALE_THRESHOLD: float = 5.4

# Diabetes diagnosis (ADA Standards of Care, 2024)
HBA1C_DIABETES_THRESHOLD: float = 6.5
FASTING_GLUCOSE_DIABETES_THRESHOLD: float = 126.0

# Beta-cell function (Matthews et al., 1985)
HOMA_B_DYSFUNCTION_THRESHOLD: float = 50.0
HOMA_B_HYPERFUNCTION_THRESHOLD: float = 150.0

# Insulin resistance indices
METS_IR_RESISTANCE_THRESHOLD: float = 35.0  # Bello-Chavolla et al., 2018
TYG_RESISTANCE_THRESHOLD: float = 4.5        # Vasques et al., 2011

# Ahlqvist clusters (Ahlqvist et al., 2018)
C_PEPTIDE_SIDD_THRESHOLD: float = 0.6
C_PEPTIDE_SIRD_THRESHOLD: float = 1.1
HOMA_IR_SIRD_THRESHOLD: float = 3.5
HOMA_IR_PRE_SIRD_THRESHOLD: float = 3.0

# Hepatic steatosis/fibrosis (Sterling et al., 2006)
FIB4_ELEVATED_THRESHOLD: float = 1.30


class MetabolicPrecisionMotor(BaseClinicalMotor):
    """
    Evaluates insulin resistance and beta-cell function (Mets-IR, TyG).

    Evidence:
    - Ahlqvist et al., 2018. Lancet Diabetes Endocrinol 6(5): 361-369.
    - Matthews et al., 1985. Diabetologia 28: 412-419.
    - Vasques et al., 2011. Diabetes Care 34(11): 2432-2434.
    - Bello-Chavolla et al., 2018. J Clin Endocrinol Metab 103(11): 4108-4116.

    REQUIREMENT_ID: METABOLIC-PRECISION
    """

    REQUIREMENT_ID = "METABOLIC-PRECISION"
    CODES = {
        "GLUCOSE": "2339-0",
        "TRIGLYCERIDES": "2571-8",
        "HDL": "2085-9",
        "BMI": "39156-5",
        "INSULIN": "20448-7",
        "C_PEPTIDE": "C-PEP-001",
        "HBA1C": "4548-4",
        "GADA": "GADA-001",
        "AST": "29230-0",
        "ALT": "22538-3",
        "PLATELETS": "PLT-001",
        "AGE": "AGE-001",
        "CRP": "30522-7",
        "VISCERAL_FAT": "BIA-VISCERAL",
        "SMI": "SMI-001"
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        if not (
            encounter.get_observation(self.CODES["GLUCOSE"])
            or encounter.get_observation(self.CODES["HBA1C"])
            or encounter.bmi
        ):
            return False, "Insufficient data for metabolic precision audit"
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        glucose = encounter.get_observation(self.CODES["GLUCOSE"])
        hba1c = encounter.get_observation(self.CODES["HBA1C"])
        trig = encounter.get_observation(self.CODES["TRIGLYCERIDES"])
        hdl = encounter.get_observation(self.CODES["HDL"])
        bmi = encounter.bmi
        insulin = encounter.get_observation(self.CODES["INSULIN"])
        c_peptide = encounter.get_observation(self.CODES["C_PEPTIDE"])
        gada = encounter.get_observation(self.CODES["GADA"])
        age = encounter.get_observation(self.CODES["AGE"])
        crp = encounter.get_observation(self.CODES["CRP"])
        visceral = encounter.get_observation(self.CODES["VISCERAL_FAT"])
        smi = encounter.get_observation(self.CODES["SMI"])
        
        findings = []
        evidence = []
        explanation = "Visión 360: Estado del Tejido Adiposo y Metabolismo. "
        dato_faltante = None
        
        # 1. Fenotipado de Obesidad y Disfunción de Tejido Adiposo (WHO, 2000)
        if bmi:
            homa_ir = encounter.homa_ir
            
            if bmi >= BMI_OBESE_THRESHOLD:
                if crp and crp.value > CRP_INFLAMMATORY_FLOOR and homa_ir and homa_ir > HOMA_IR_RESISTANCE_FLOOR:
                    findings.append("Adiposopatía Inflamatoria (Sick Fat)")
                    explanation += "Disfunción de tejido adiposo detectada (Pro-inflamatorio). "
                elif crp and crp.value < CRP_PROTECTIVE_CEILING and homa_ir and homa_ir < HOMA_IR_SENSITIVE_CEILING:
                    findings.append("Hiperplasia Adiposa Protegida (MHO Transicional)")
                    explanation += "Expansión de grasa saludable (Limitada en el tiempo). "
            
            if bmi < BMI_NORMAL_UPPER and visceral and visceral.value > VISCERAL_FAT_TOFI_THRESHOLD:
                findings.append("Disfunción de Expansión (TOFI/MUNW)")
                explanation += "Grasa visceral excesiva en peso formalmente normal. Riesgo oculto. "

        # 2. Fragilidad Metabólica (Sarcopenia) (Baumgartner et al., 1998)
        is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]
        smi_threshold = SMI_MALE_THRESHOLD if is_male else SMI_FEMALE_THRESHOLD
        if smi and smi.value < smi_threshold:
            findings.append("Obesidad Sarcopénica (Fragilidad)")
            evidence.append(ClinicalEvidence(type="Observation", code="SMI", value=smi.value, display="SMI", threshold="Bajo"))

        # 3. Índices de Resistencia y Clústeres (Ahlqvist et al., 2018 + ADA Standards)
        homa_ir = encounter.homa_ir
        homa_b = encounter.homa_b
        mets_ir = encounter.mets_ir
        is_diabetic = (hba1c and hba1c.value >= HBA1C_DIABETES_THRESHOLD) or (glucose and glucose.value >= FASTING_GLUCOSE_DIABETES_THRESHOLD)
        
        if homa_b:
            evidence.append(ClinicalEvidence(type="Calculation", code="HOMA-B", value=round(homa_b, 1), display="Función Beta-%"))
            if homa_b < HOMA_B_DYSFUNCTION_THRESHOLD:
                findings.append("Disfunción Beta-Celular Primaria (Baja Reserva)")
            elif homa_b > HOMA_B_HYPERFUNCTION_THRESHOLD and not is_diabetic:
                findings.append("Hiperfunción Pancreática Compensatoria")

        if mets_ir:
            evidence.append(ClinicalEvidence(type="Calculation", code="METS-IR", value=round(mets_ir, 2), display="Index METS-IR"))
            if mets_ir > METS_IR_RESISTANCE_THRESHOLD:
                findings.append("Resistencia a la Insulina (METS-IR > 35)")

        if glucose and trig:
            tyg = encounter.tyg_index
            if tyg and tyg > TYG_RESISTANCE_THRESHOLD:
                findings.append("Resistencia a la Insulina (Reserva TyG elevada)")

        if is_diabetic:
            # Alpha Cluster Isolation (Ahlqvist et al., 2018)
            if gada and gada.value in [True, "Positivo", "Positive"]:
                findings.append("Deficiencia de Insulina Autoinmune (SAID)")
            elif c_peptide:
                try:
                    c_val = float(c_peptide.value)
                    evidence.append(ClinicalEvidence(type="Observation", code="C-PEPTIDE", value=c_val, display="Péptido C"))
                    if c_val < C_PEPTIDE_SIDD_THRESHOLD:
                        findings.append("Deficiencia de Insulina Severa (SIDD)")
                        explanation += "Función beta-celular críticamente baja. "
                    elif c_val > C_PEPTIDE_SIRD_THRESHOLD:
                        findings.append("Resistencia a la Insulina Severa (SIRD)")
                        explanation += "Fenotipo de alta secreción con resistencia marcada. "
                except (ValueError, TypeError):
                    pass
            elif homa_ir:
                if homa_ir > HOMA_IR_SIRD_THRESHOLD and bmi and bmi > BMI_OBESE_THRESHOLD:
                    findings.append("Resistencia a la Insulina Severa (SIRD)")
                elif homa_ir < HOMA_IR_SENSITIVE_CEILING:
                    findings.append("Deficiencia de Insulina Severa (SIDD)")
                    dato_faltante = "Péptido C (Requerido para fenotipado de precisión SIDD/SIRD)"
            else:
                findings.append("Diabetes No Tipificada")
                dato_faltante = "Péptido C + GADA (Indicados para tipificación de precisión de diabetes)"
        
        elif homa_ir and homa_ir > HOMA_IR_PRE_SIRD_THRESHOLD:
             findings.append("Resistencia a la Insulina de Alto Grado (Estado Pre-SIRD)")
             explanation += "Marcada insulino-resistencia sin clúster diabético franco aún. Alta prioridad de intervención. "

        # 4. Grasa Ectópica (FIB-4) (Sterling et al., 2006)
        ast = encounter.get_observation(self.CODES["AST"])
        alt = encounter.get_observation(self.CODES["ALT"])
        plt = encounter.get_observation(self.CODES["PLATELETS"])
        
        if all([age, ast, alt, plt]) and alt.value > 0:
            fib4 = (age.value * ast.value) / (plt.value * math.sqrt(alt.value))
            if fib4 > FIB4_ELEVATED_THRESHOLD:
                findings.append(f"Fenotipo de Grasa Ectópica (FIB-4: {fib4:.2f})")
                evidence.append(ClinicalEvidence(type="Calculation", code="FIB-4", value=round(fib4, 2), display="FIB-4", threshold=f">{FIB4_ELEVATED_THRESHOLD}"))

        return AdjudicationResult(
            calculated_value=" | ".join(findings) if findings else "Metabólicamente Estable",
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.VALIDATED_BIOMARKER],
            evidence=evidence,
            explanation=explanation.strip(),
            dato_faltante=dato_faltante,
            estado_ui="CONFIRMED_ACTIVE" if findings else "PROBABLE_WARNING"
        )

from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple
import math

class MetabolicPrecisionMotor(BaseClinicalMotor):
    """
    Evaluates insulin resistance and beta-cell function (Mets-IR, TyG).
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
        if not encounter.get_observation(self.CODES["GLUCOSE"]) and \
           not encounter.get_observation(self.CODES["HBA1C"]) and \
           not encounter.bmi:
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
        
        # 1. Fenotipado de Obesidad y Disfunción de Tejido Adiposo
        if bmi:
            homa_ir = encounter.homa_ir
            
            if bmi >= 30:
                if crp and crp.value > 1.0 and homa_ir and homa_ir > 2.5:
                    findings.append("Adiposopatía Inflamatoria (Sick Fat)")
                    explanation += "Disfunción de tejido adiposo detectada (Pro-inflamatorio). "
                elif crp and crp.value < 0.5 and homa_ir and homa_ir < 2.0:
                    findings.append("Hiperplasia Adiposa Protegida (MHO Transicional)")
                    explanation += "Expansión de grasa saludable (Limitada en el tiempo). "
            
            if bmi < 25 and visceral and visceral.value > 10:
                findings.append("Disfunción de Expansión (TOFI/MUNW)")
                explanation += "Grasa visceral excesiva en peso formalmente normal. Riesgo oculto. "

        # 2. Fragilidad Metabólica (Sarcopenia)
        is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]
        smi_threshold = 7.0 if is_male else 5.4
        if smi and smi.value < smi_threshold:
            findings.append("Obesidad Sarcopénica (Fragilidad)")
            evidence.append(ClinicalEvidence(type="Observation", code="SMI", value=smi.value, display="SMI", threshold="Bajo"))

        # 3. Índices de Resistencia y Clústeres (Ahlqvist + IR de Grado)
        homa_ir = encounter.homa_ir
        homa_b = encounter.homa_b
        mets_ir = encounter.mets_ir
        is_diabetic = (hba1c and hba1c.value >= 6.5) or (glucose and glucose.value >= 126)
        
        if homa_b:
            evidence.append(ClinicalEvidence(type="Calculation", code="HOMA-B", value=round(homa_b, 1), display="Función Beta-%"))
            if homa_b < 50:
                findings.append("Disfunción Beta-Celular Primaria (Baja Reserva)")
            elif homa_b > 150 and not is_diabetic:
                findings.append("Hiperfunción Pancreática Compensatoria")

        if mets_ir:
            evidence.append(ClinicalEvidence(type="Calculation", code="METS-IR", value=round(mets_ir, 2), display="Index METS-IR"))
            if mets_ir > 35:
                findings.append("Resistencia a la Insulina (METS-IR > 35)")

        if glucose and trig:
            tyg = encounter.tyg_index
            if tyg and tyg > 4.5:
                findings.append("Resistencia a la Insulina (Reserva TyG elevada)")

        if is_diabetic:
            # Alpha Cluster Isolation
            if gada and gada.value in [True, "Positivo", "Positive"]:
                findings.append("Deficiencia de Insulina Autoinmune (SAID)")
            elif c_peptide:
                try:
                    c_val = float(c_peptide.value)
                    evidence.append(ClinicalEvidence(type="Observation", code="C-PEPTIDE", value=c_val, display="Péptido C"))
                    if c_val < 0.6:
                        findings.append("Deficiencia de Insulina Severa (SIDD)")
                        explanation += "Función beta-celular críticamente baja. "
                    elif c_val > 1.1:
                        findings.append("Resistencia a la Insulina Severa (SIRD)")
                        explanation += "Fenotipo de alta secreción con resistencia marcada. "
                except (ValueError, TypeError):
                    pass
            elif homa_ir:
                if homa_ir > 3.5 and bmi and bmi > 30:
                    findings.append("Resistencia a la Insulina Severa (SIRD)")
                elif homa_ir < 2.0:
                    findings.append("Deficiencia de Insulina Severa (SIDD)")
                    dato_faltante = "Péptido C (Requerido para fenotipado de precisión SIDD/SIRD)"
            else:
                findings.append("Diabetes No Tipificada")
                dato_faltante = "Péptido C + GADA (Indicados para tipificación de precisión de diabetes)"
        
        elif homa_ir and homa_ir > 3.0:
             findings.append("Resistencia a la Insulina de Alto Grado (Estado Pre-SIRD)")
             explanation += "Marcada insulino-resistencia sin clúster diabético franco aún. Alta prioridad de intervención. "

        # 4. Grasa Ectópica (FIB-4)
        ast = encounter.get_observation(self.CODES["AST"])
        alt = encounter.get_observation(self.CODES["ALT"])
        plt = encounter.get_observation(self.CODES["PLATELETS"])
        
        if all([age, ast, alt, plt]) and alt.value > 0:
            fib4 = (age.value * ast.value) / (plt.value * math.sqrt(alt.value))
            if fib4 > 1.30:
                findings.append(f"Fenotipo de Grasa Ectópica (FIB-4: {fib4:.2f})")
                evidence.append(ClinicalEvidence(type="Calculation", code="FIB-4", value=round(fib4, 2), display="FIB-4", threshold=">1.30"))

        return AdjudicationResult(
            calculated_value=" | ".join(findings) if findings else "Metabólicamente Estable",
            confidence=0.9,
            evidence=evidence,
            explanation=explanation.strip(),
            dato_faltante=dato_faltante,
            estado_ui="CONFIRMED_ACTIVE" if findings else "PROBABLE_WARNING"
        )

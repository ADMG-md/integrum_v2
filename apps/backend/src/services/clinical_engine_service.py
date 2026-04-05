from src.engines.domain import Encounter, Observation
from typing import List, Optional
import math

class ClinicalIntelligenceBridge:
    """
    Research-Grade Clinical Data Flow Enrichment.
    Ensures the 'Structured Dataset' is normalized and enriched with primary indices 
    before SaMD Engine execution.
    """
    
    # LOINC Codes
    WEIGHT = "29463-7"
    HEIGHT = "8302-2"
    GLUCOSE = "2339-0"
    INSULIN = "20448-7"
    TRIGLYCERIDES = "2571-8"
    HDL = "2085-9"
    WAIST = "WAIST-001"
    
    # Derived Codes
    BMI = "CALC-BMI"
    WHTR = "CALC-WHTR"
    HOMA_IR = "CALC-HOMA-IR"
    TYG = "CALC-TYG"
    VAI = "CALC-VAI"
    FIB4 = "CALC-FIB4"
    
    # Lab Codes
    AST = "29230-0"
    ALT = "22538-3"
    PLT = "PLT-001"
    AGE = "AGE-001"

    def enrich(self, encounter: Encounter) -> Encounter:
        """
        Main enrichment entry point.
        """
        # 1. Calculate Indices
        self._inject_bmi(encounter)
        self._inject_whtr(encounter)
        self._inject_homa(encounter)
        self._inject_tyg(encounter)
        self._inject_vai(encounter)
        self._inject_fib4(encounter)
        
        return encounter

    def _inject_whtr(self, encounter: Encounter):
        w = encounter.get_observation(self.WAIST)
        h = encounter.get_observation(self.HEIGHT)
        if w and h and h.value > 0:
            whtr = float(w.value) / float(h.value)
            encounter.observations.append(Observation(
                code=self.WHTR,
                value=round(whtr, 3),
                unit="Ratio",
                category="Clinical",
                metadata={"source": "2025-standard-auto-calculated"}
            ))

    def _inject_bmi(self, encounter: Encounter):
        w = encounter.get_observation(self.WEIGHT)
        h = encounter.get_observation(self.HEIGHT)
        if w and h and h.value > 0:
            bmi = float(w.value) / ((float(h.value)/100)**2)
            encounter.observations.append(Observation(
                code=self.BMI,
                value=round(bmi, 2),
                unit="kg/m2",
                category="Clinical",
                metadata={"source": "auto-calculated"}
            ))

    def _inject_homa(self, encounter: Encounter):
        glu = encounter.get_observation(self.GLUCOSE)
        ins = encounter.get_observation(self.INSULIN)
        if glu and ins:
            homa = (float(glu.value) * float(ins.value)) / 405
            encounter.observations.append(Observation(
                code=self.HOMA_IR,
                value=round(homa, 2),
                unit="Score",
                category="Clinical",
                metadata={"source": "auto-calculated"}
            ))

    def _inject_tyg(self, encounter: Encounter):
        glu = encounter.get_observation(self.GLUCOSE)
        tg = encounter.get_observation(self.TRIGLYCERIDES)
        if glu and tg:
            try:
                product = float(tg.value) * float(glu.value)
                if product > 0:
                    tyg = math.log(product / 2)
                    encounter.observations.append(Observation(
                        code=self.TYG,
                        value=round(tyg, 2),
                        unit="Score",
                        category="Clinical",
                        metadata={"source": "auto-calculated"}
                    ))
            except (ValueError, ZeroDivisionError):
                pass

    def _inject_vai(self, encounter: Encounter):
        # Visceral Adiposity Index (VAI)
        # Men: (WC / (39.68 + (1.88 * BMI))) * (TG / 1.03) * (1.31 / HDL)
        # Women: (WC / (36.58 + (1.89 * BMI))) * (TG / 0.81) * (1.52 / HDL)
        tg = encounter.get_observation(self.TRIGLYCERIDES)
        hdl = encounter.get_observation(self.HDL)
        waist = encounter.get_observation(self.WAIST)
        bmi = encounter.get_observation(self.BMI)
        gender = encounter.metadata.get("gender", "male").lower()
        
        if all([tg, hdl, waist, bmi]) and hdl.value > 0:
            try:
                if gender == "male":
                    vai = (waist.value / (39.68 + (1.88 * bmi.value))) * (tg.value / 1.03) * (1.31 / hdl.value)
                else:
                    vai = (waist.value / (36.58 + (1.89 * bmi.value))) * (tg.value / 0.81) * (1.52 / hdl.value)
                
                encounter.observations.append(Observation(
                    code=self.VAI,
                    value=round(vai, 2),
                    unit="Score",
                    category="Clinical",
                    metadata={"source": "auto-calculated-precision"}
                ))
            except:
                pass

    def _inject_fib4(self, encounter: Encounter):
        # FIB-4 = (Age * AST) / (PLT * sqrt(ALT))
        ast = encounter.get_observation(self.AST)
        alt = encounter.get_observation(self.ALT)
        plt = encounter.get_observation(self.PLT)
        age = encounter.get_observation(self.AGE)
        
        if all([ast, alt, plt, age]) and alt.value > 0 and plt.value > 0:
            try:
                fib4 = (age.value * ast.value) / (plt.value * math.sqrt(alt.value))
                encounter.observations.append(Observation(
                    code=self.FIB4,
                    value=round(fib4, 2),
                    unit="Score",
                    category="Clinical",
                    metadata={"source": "auto-calculated-liver-risk"}
                ))
            except:
                pass

clinical_bridge = ClinicalIntelligenceBridge()

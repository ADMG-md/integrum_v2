"""
Clinical Calculators — Value Objects for computed clinical indices.

Each calculator is a pure function encapsulated in a value object.
Encounter composes these instead of implementing calculations directly.

This eliminates the God Class anti-pattern in Encounter (586 lines → ~250 lines).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.models import Encounter


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ============================================================
# Renal Function
# ============================================================


@dataclass(frozen=True)
class RenalFunction:
    """CKD-EPI 2021 race-free eGFR + UACR."""

    egfr_ckd_epi: Optional[float]
    uacr: Optional[float]

    @classmethod
    def from_encounter(cls, enc: Encounter) -> RenalFunction:
        creat = enc.metabolic_panel.creatinine_mg_dl
        age_obs = enc.get_observation("AGE-001")
        age = _safe_float(age_obs.value) if age_obs else None

        egfr = None
        if creat and age and age > 0:
            is_male = enc.metadata.get("sex", "").lower() in ("male", "m")
            kappa = 0.9 if is_male else 0.7
            alpha = -0.302 if is_male else -0.241
            sex_factor = 1.012 if not is_male else 1.0
            ratio = creat / kappa
            egfr = round(
                142
                * min(ratio, 1) ** alpha
                * max(ratio, 1) ** -1.200
                * (0.9938**age)
                * sex_factor,
                1,
            )

        uacr = None
        uacr_obs = enc.get_observation("UACR-001")
        if uacr_obs:
            uacr = _safe_float(uacr_obs.value)
        else:
            alb_obs = enc.get_observation("UALB-001")
            ucr_obs = enc.get_observation("UCREAT-001")
            if alb_obs and ucr_obs:
                alb = _safe_float(alb_obs.value)
                ucr = _safe_float(ucr_obs.value)
                if alb and ucr and ucr > 0:
                    uacr = round((alb / ucr) * 1000, 1)

        return cls(egfr_ckd_epi=egfr, uacr=uacr)


# ============================================================
# Lipid Profile
# ============================================================


@dataclass(frozen=True)
class LipidProfile:
    """Atherogenic indices and lipid risk markers."""

    remnant_cholesterol: Optional[float]
    aip: Optional[float]
    castelli_index_i: Optional[float]
    castelli_index_ii: Optional[float]
    apob_apoa1_ratio: Optional[float]
    non_hdl_cholesterol: Optional[float]

    @classmethod
    def from_encounter(cls, enc: Encounter) -> LipidProfile:
        cp = enc.cardio_panel
        tc = cp.total_cholesterol_mg_dl
        hdl = cp.hdl_mg_dl
        ldl = cp.ldl_mg_dl
        tg = cp.triglycerides_mg_dl
        apob = cp.apob_mg_dl
        apoa1 = cp.apoa1_mg_dl

        remnant = round(tc - hdl - ldl, 1) if all([tc, hdl, ldl]) else None
        aip = round(math.log10(tg / hdl), 3) if tg and hdl and hdl > 0 else None
        ci = round(tc / hdl, 2) if tc and hdl and hdl > 0 else None
        cii = round(ldl / hdl, 2) if ldl and hdl and hdl > 0 else None
        apo_ratio = round(apob / apoa1, 3) if apob and apoa1 and apoa1 > 0 else None
        non_hdl = round(tc - hdl, 1) if tc and hdl else None

        return cls(
            remnant_cholesterol=remnant,
            aip=aip,
            castelli_index_i=ci,
            castelli_index_ii=cii,
            apob_apoa1_ratio=apo_ratio,
            non_hdl_cholesterol=non_hdl,
        )


# ============================================================
# Metabolic Indices
# ============================================================


@dataclass(frozen=True)
class MetabolicIndices:
    """Insulin resistance and metabolic syndrome indices."""

    homa_ir: Optional[float]
    homa_b: Optional[float]
    tyg_index: Optional[float]
    tyg_bmi: Optional[float]
    mets_ir: Optional[float]

    @classmethod
    def from_encounter(cls, enc: Encounter) -> MetabolicIndices:
        glu = enc.glucose_mg_dl
        ins = enc.metabolic_panel.insulin_mu_u_ml
        tg = enc.cardio_panel.triglycerides_mg_dl
        hdl = enc.cardio_panel.hdl_mg_dl
        bmi = enc.bmi

        homa_ir = (glu * ins) / 405 if glu and ins and glu > 0 else None
        homa_b = (360 * ins) / (glu - 63) if glu and ins and glu > 63 else None
        tyg = math.log((tg * glu) / 2.0) if glu and tg and glu > 0 and tg > 0 else None
        tyg_bmi = round(tyg * bmi, 2) if tyg and bmi else None

        mets_ir = None
        if all([glu, tg, hdl, bmi]) and glu > 0 and tg > 0 and hdl > 0:
            mets_ir = (math.log((2 * glu) + tg) * bmi) / math.log(hdl)

        return cls(
            homa_ir=homa_ir,
            homa_b=homa_b,
            tyg_index=tyg,
            tyg_bmi=tyg_bmi,
            mets_ir=mets_ir,
        )


# ============================================================
# Anthropometry
# ============================================================


@dataclass(frozen=True)
class AnthropometricData:
    """Body composition and anthropometric ratios."""

    bmi: Optional[float]
    waist_to_height: Optional[float]
    waist_to_hip: Optional[float]
    body_roundness_index: Optional[float]
    fat_free_mass: Optional[float]
    ideal_body_weight: Optional[float]

    @classmethod
    def from_encounter(cls, enc: Encounter) -> AnthropometricData:
        w_obs = enc.get_observation("29463-7") or enc.get_observation("W-001")
        h_obs = enc.get_observation("8302-2") or enc.get_observation("H-001")
        waist_obs = enc.get_observation("WAIST-001")
        hip_obs = enc.get_observation("HIP-001")

        w = _safe_float(w_obs.value) if w_obs else None
        h = _safe_float(h_obs.value) if h_obs else None
        waist = _safe_float(waist_obs.value) if waist_obs else None
        hip = _safe_float(hip_obs.value) if hip_obs else None

        bmi = w / ((h / 100) ** 2) if w and h and h > 0 else None
        wht = waist / h if waist and h and h > 0 else None
        whr = waist / hip if waist and hip and hip > 0 else None

        bri = None
        if waist and h and h > 0:
            # P0-2: Body Roundness Index — Thomas DM et al, J Obes 2010;2010:301895
            # Formula: BRI = 364.2 - 365.5 × sqrt(1 - (waist_m/(2π))^2 / (height_m/2)^2)
            # waist in cm → m; height in cm → m
            waist_m = waist / 100.0
            height_m = h / 100.0
            _term = (waist_m / (2 * math.pi)) ** 2 / (height_m / 2) ** 2
            if _term < 1.0:  # geometrically valid (waist < height/π ≈ physiological)
                bri = round(364.2 - 365.5 * math.sqrt(1.0 - _term), 2)
            else:
                bri = None  # physiologically impossible input

        ffm = None
        ffm_obs = enc.get_observation("BIA-FFM-KG")
        if ffm_obs:
            ffm = _safe_float(ffm_obs.value)
        else:
            mm_obs = enc.get_observation("MMA-001") or enc.get_observation("MUSCLE-KG")
            if mm_obs:
                mm = _safe_float(mm_obs.value)
                if mm is not None:
                    ffm = mm * 1.15

        ibw = None
        if h and h > 0:
            h_in = h / 2.54
            is_male = enc.metadata.get("sex", "").lower() in ("male", "m")
            ibw = round(
                max(
                    50.0 + 2.3 * (h_in - 60) if is_male else 45.5 + 2.3 * (h_in - 60),
                    30,
                ),
                1,
            )

        return cls(
            bmi=bmi,
            waist_to_height=wht,
            waist_to_hip=whr,
            body_roundness_index=bri,
            fat_free_mass=ffm,
            ideal_body_weight=ibw,
        )


# ============================================================
# Hemodynamics
# ============================================================


@dataclass(frozen=True)
class Hemodynamics:
    """Blood pressure derived metrics."""

    pulse_pressure: Optional[float]
    mean_arterial_pressure: Optional[float]

    @classmethod
    def from_encounter(cls, enc: Encounter) -> Hemodynamics:
        sbp_obs = enc.get_observation("8480-6")
        dbp_obs = enc.get_observation("8462-4")
        sbp = _safe_float(sbp_obs.value) if sbp_obs else None
        dbp = _safe_float(dbp_obs.value) if dbp_obs else None

        pp = round(sbp - dbp, 1) if sbp and dbp else None
        map_val = round(dbp + (sbp - dbp) / 3, 1) if sbp and dbp else None

        return cls(pulse_pressure=pp, mean_arterial_pressure=map_val)


# ============================================================
# Clinical Context
# ============================================================


@dataclass(frozen=True)
class ClinicalContext:
    """Trauma and clinical history derived metrics."""

    ace_score: Optional[int]

    @classmethod
    def from_encounter(cls, enc: Encounter) -> ClinicalContext:
        ace = None
        if enc.history and enc.history.trauma:
            ace = enc.history.trauma.ace_score
        return cls(ace_score=ace)


# ============================================================
# Proxy Values (simple pass-throughs)
# ============================================================


@dataclass(frozen=True)
class ProxyValues:
    """Direct access to commonly needed values."""

    glucose_mg_dl: Optional[float]
    creatinine_mg_dl: Optional[float]
    hba1c: Optional[float]
    uric_acid: Optional[float]

    @classmethod
    def from_encounter(cls, enc: Encounter) -> ProxyValues:
        ua_obs = enc.get_observation("UA-001")
        uric_acid = (
            _safe_float(ua_obs.value) if ua_obs else enc.metabolic_panel.uric_acid_mg_dl
        )

        return cls(
            glucose_mg_dl=enc.metabolic_panel.glucose_mg_dl,
            creatinine_mg_dl=enc.metabolic_panel.creatinine_mg_dl,
            hba1c=enc.metabolic_panel.hba1c_percent,
            uric_acid=uric_acid,
        )

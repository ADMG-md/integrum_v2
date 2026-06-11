import math
from typing import Tuple, Dict, Any, Optional

def calculate_tyg_bmi(tg_mg_dl: float, glu_mg_dl: float, bmi: float) -> Tuple[float, float]:
    """
    Calculates TyG index and TyG-BMI index.
    TyG = ln(TG [mg/dL] * Glu [mg/dL] / 2)
    TyG-BMI = TyG * BMI
    Returns (tyg_index, tyg_bmi_index).
    """
    tyg = math.log(tg_mg_dl * glu_mg_dl / 2)
    tyg_bmi = round(tyg * bmi, 2)
    return tyg, tyg_bmi

def calculate_fli(tg_mg_dl: float, bmi: float, ggt_u_l: float, waist_cm: float) -> float:
    """
    Fatty Liver Index (FLI) — Bedogni et al., 2006.
    """
    linear = (
        0.953 * math.log(tg_mg_dl)
        + 0.139 * bmi
        + 0.718 * math.log(ggt_u_l)
        + 0.053 * waist_cm
        - 15.745
    )
    fli = (math.exp(linear) / (1 + math.exp(linear))) * 100
    return round(fli, 1)

def calculate_vai(wc_cm: float, bmi: float, tg_mg_dl: float, hdl_mg_dl: float, is_male: bool) -> float:
    """
    Visceral Adiposity Index (VAI) — Amato et al., 2010.
    """
    if is_male:
        vai = (wc_cm / (39.68 + 1.88 * bmi)) * (tg_mg_dl / 1.03) * (1.31 / hdl_mg_dl)
    else:
        vai = (wc_cm / (36.58 + 1.89 * bmi)) * (tg_mg_dl / 0.81) * (1.52 / hdl_mg_dl)
    return round(vai, 2)

def calculate_kleiber_bmr(weight_kg: float) -> float:
    """
    Kleiber’s law BMR approximation.
    """
    return round(70.0 * (weight_kg ** 0.75))

def calculate_free_testosterone_vermeulen(total_t_ng_dl: float, shbg_nmol_l: float, albumin_g_dl: float = 4.3) -> Tuple[float, float]:
    """
    Free Testosterone Calculator — Vermeulen Method (1999).
    Returns (free_t_pg_ml, bioavailable_t_ng_dl)
    """
    total_t_nmol = total_t_ng_dl * 0.0347
    albumin_mol = (albumin_g_dl * 10) / 69000

    ka_shbg = 1.0e9
    ka_alb = 3.6e4

    b = 1 + ka_shbg * shbg_nmol_l + ka_alb * albumin_mol - ka_shbg * total_t_nmol
    c = -ka_shbg * total_t_nmol

    free_t_nmol = (-b + math.sqrt(b * b - 4 * ka_shbg * c)) / (2 * ka_shbg)
    free_t_pg_ml = free_t_nmol * 288.4

    bioavailable_nmol = free_t_nmol * (1 + ka_alb * albumin_mol)
    bioavailable_t_ng_dl = bioavailable_nmol * 28.84

    return free_t_pg_ml, bioavailable_t_ng_dl

def calculate_kfre(egfr: float, uacr: float, age: float, is_male: bool) -> Tuple[float, float]:
    """
    Kidney Failure Risk Equation (KFRE) — 4-variable model (Tangri 2016).
    Returns (risk_2y_percent, risk_5y_percent).
    """
    age_term = 0.0299 * (age - 60) if age > 60 else 0
    egfr_term = -0.584 * math.log(max(egfr, 5))
    uacr_term = 0.417 * math.log(max(uacr, 1))
    sex_term = 0.399 if is_male else 0

    linear_predictor = age_term + egfr_term + uacr_term + sex_term

    s2 = 0.9793
    s5 = 0.9415

    risk_2y = 1 - (s2 ** math.exp(linear_predictor))
    risk_5y = 1 - (s5 ** math.exp(linear_predictor))

    return round(min(risk_2y * 100, 100), 1), round(min(risk_5y * 100, 100), 1)

def calculate_apob_ratio(apob_mg_dl: float, apoa1_mg_dl: float) -> float:
    """
    ApoB/ApoA1 Ratio.
    """
    return round(apob_mg_dl / apoa1_mg_dl, 3)

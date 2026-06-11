from src.engines.calculators import (
    calculate_tyg_bmi,
    calculate_fli,
    calculate_vai,
    calculate_kleiber_bmr,
    calculate_free_testosterone_vermeulen,
    calculate_kfre,
    calculate_apob_ratio
)
import math

def test_calculate_tyg_bmi():
    # TG 150, Glu 100, BMI 30
    # TyG = ln(150 * 100 / 2) = ln(7500) ≈ 8.9226
    # TyG-BMI = 8.9226 * 30 ≈ 267.68
    tyg, tygbmi = calculate_tyg_bmi(150, 100, 30)
    assert math.isclose(tyg, 8.9226, rel_tol=1e-3)
    assert tygbmi == 267.68

def test_calculate_fli():
    # TG 150, BMI 30, GGT 40, Waist 100
    fli = calculate_fli(150, 30, 40, 100)
    # Just asserting it returns a float without crashing
    assert isinstance(fli, float)

def test_calculate_vai():
    # Male, WC 100, BMI 30, TG 150, HDL 40
    vai_m = calculate_vai(100, 30, 150, 40, is_male=True)
    assert isinstance(vai_m, float)
    # Female
    vai_f = calculate_vai(100, 30, 150, 40, is_male=False)
    assert isinstance(vai_f, float)

def test_calculate_kleiber_bmr():
    bmr = calculate_kleiber_bmr(70)
    assert bmr == round(70 * (70 ** 0.75))

def test_calculate_free_testosterone():
    free, bio = calculate_free_testosterone_vermeulen(500, 30, 4.3)
    assert isinstance(free, float)
    assert isinstance(bio, float)

def test_calculate_kfre():
    risk2, risk5 = calculate_kfre(egfr=45, uacr=300, age=65, is_male=True)
    assert isinstance(risk2, float)
    assert isinstance(risk5, float)

def test_calculate_apob_ratio():
    ratio = calculate_apob_ratio(100, 50)
    assert ratio == 2.0

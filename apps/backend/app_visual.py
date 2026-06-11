import streamlit as st
import uuid
import sys
import os
from datetime import datetime, date, timedelta

# Ensure pythonpath includes the apps/backend directory to resolve src.* imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.domain.models import (
    Encounter,
    DemographicsSchema,
    MetabolicPanelSchema,
    Condition,
    Observation,
    MedicationStatement,
    ClinicalHistory,
    DrugEntry,
    LongitudinalEncounterEntry
)
from src.engines.specialty_runner import create_runner
from src.domain.models import AdjudicationResult

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Integrum V2 — CDSS Cardiometabólico",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN STYLING ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e9ecef;
        margin-bottom: 15px;
    }
    .engine-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 8px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .status-confirmed { background-color: #d1fae5; color: #065f46; }
    .status-warning { background-color: #fef3c7; color: #92400e; }
    .status-locked { background-color: #f1f5f9; color: #475569; }
    .status-error { background-color: #fee2e2; color: #991b1b; }
    .card-footer {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 10px;
        border-top: 1px dashed #e2e8f0;
        padding-top: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- TITLE ---
st.title("🩺 Integrum V2 — CDSS Cardiometabólico (SaMD Clase B)")
st.markdown("### Demo Operativa Interactiva de Motores de Precisión Clínicos")

# --- SIDEBAR - PATIENT ENCOUNTER INPUTS ---
st.sidebar.header("👤 Demografía del Paciente")
age = st.sidebar.number_input("Edad (años)", min_value=18, max_value=120, value=48)
gender = st.sidebar.selectbox("Género", ["female", "male", "other"], index=0)

# --- BIOMETRICS SECTION ---
st.sidebar.header("📏 Biometría y Signos Vitales")
weight = st.sidebar.number_input("Peso (kg)", min_value=30.0, max_value=300.0, value=98.5, step=0.5)
height = st.sidebar.number_input("Talla (cm)", min_value=100, max_value=250, value=160, step=1)
waist = st.sidebar.number_input("Perímetro Abdominal (cm)", min_value=40, max_value=200, value=108, step=1)
neck = st.sidebar.number_input("Circunferencia de Cuello (cm)", min_value=20, max_value=80, value=42, step=1)
systolic = st.sidebar.number_input("Presión Sistólica (mmHg)", min_value=70, max_value=250, value=135)
diastolic = st.sidebar.number_input("Presión Diastólica (mmHg)", min_value=40, max_value=150, value=85)

# --- METABOLIC PANEL ---
st.sidebar.header("🧪 Laboratorio (Panel Metabólico)")
glucose = st.sidebar.number_input("Glucosa en Ayunas (mg/dL)", min_value=40.0, max_value=500.0, value=118.0)
hba1c = st.sidebar.number_input("Hemoglobina Glicosilada - HbA1c (%)", min_value=3.0, max_value=18.0, value=6.2)
insulin = st.sidebar.number_input("Insulina en Ayunas (µIU/mL)", min_value=0.5, max_value=200.0, value=18.0)
triglycerides = st.sidebar.number_input("Triglicéridos (mg/dL)", min_value=30.0, max_value=1200.0, value=185.0)
hdl = st.sidebar.number_input("Colesterol HDL (mg/dL)", min_value=5.0, max_value=150.0, value=38.0)
ldl = st.sidebar.number_input("Colesterol LDL (mg/dL)", min_value=20.0, max_value=400.0, value=165.0)
creatinine = st.sidebar.number_input("Creatinina Sérica (mg/dL)", min_value=0.2, max_value=10.0, value=0.9)
albumin_g = st.sidebar.number_input("Albúmina Sérica (g/dL)", min_value=2.0, max_value=6.0, value=4.1)
hscrp = st.sidebar.number_input("PCR Ultrasensible - hs-CRP (mg/L)", min_value=0.0, max_value=50.0, value=3.2)
vitd = st.sidebar.number_input("Vitamina D (ng/mL)", min_value=5.0, max_value=150.0, value=22.0)
testo = st.sidebar.number_input("Testosterona Total (ng/dL)", min_value=10.0, max_value=1500.0, value=350.0)

# --- CLINICAL HISTORY ---
st.sidebar.header("📜 Antecedentes y Comorbilidades")
has_obesity = st.sidebar.checkbox("Obesidad (Diagnóstico formal)", value=True)
has_t2d = st.sidebar.checkbox("Diabetes Mellitus Tipo 2", value=False)
has_htn = st.sidebar.checkbox("Hipertensión Arterial", value=True)
has_dyslipidemia = st.sidebar.checkbox("Dislipidemia", value=True)
has_nafld = st.sidebar.checkbox("Hígado Graso (NAFLD/MASLD)", value=True)
has_hf = st.sidebar.checkbox("Insuficiencia Cardíaca", value=False)
has_mtc = st.sidebar.checkbox("Historia de Cáncer Medular de Tiroides", value=False)
has_men2 = st.sidebar.checkbox("Historia de MEN2", value=False)

# --- PSYCHOMETRICS & LIFESTYLE ---
st.sidebar.header("🧠 Psicosocial y Estilo de Vida")
tfeq_uncontrolled = st.sidebar.slider("TFEQ - Ingesta Descontrolada", 1.0, 4.0, 3.2, 0.1)
tfeq_emotional = st.sidebar.slider("TFEQ - Hambre Emocional", 1.0, 4.0, 2.8, 0.1)
ais_insomnia = st.sidebar.slider("AIS - Score de Insomnio (Athens)", 0, 24, 8)
phq9_item_9 = st.sidebar.selectbox("PHQ-9 - Ítem 9 (Riesgo Suicida)", [0, 1, 2, 3], index=0)
exercise_min = st.sidebar.number_input("Ejercicio Físico (min/semana)", min_value=0, max_value=1000, value=60)
sleep_hours = st.sidebar.number_input("Horas de Sueño (promedio/noche)", min_value=2.0, max_value=14.0, value=5.5, step=0.5)

# --- LOGICAL LONGITUDINAL SIMULATION ---
st.sidebar.header("📈 Simulación Longitudinal (C-State)")
use_longitudinal = st.sidebar.checkbox("Simular Encuentros Previos (Eje C)", value=True)
prev_weight_28d = st.sidebar.number_input("Peso hace 28 días (kg)", min_value=30.0, max_value=300.0, value=100.0)
prev_ffm_28d = st.sidebar.number_input("Masa Magra (FFM) hace 28 días (kg)", min_value=20.0, max_value=200.0, value=61.0)
current_ffm = st.sidebar.number_input("Masa Magra (FFM) actual (kg)", min_value=20.0, max_value=200.0, value=59.5)

# --- ACTIONS PANEL ---
st.sidebar.markdown("---")
run_analysis = st.sidebar.button("⚙️ EJECUTAR ADJUDICACIÓN CLÍNICA", use_container_width=True)

# --- ENCOUNTER DATA CONVERSION & COMPUTATION ---
# Create default objects
demographics = DemographicsSchema(age_years=age, gender=gender)

# Build metabolic panel safely
try:
    metabolic_panel = MetabolicPanelSchema(
        glucose_mg_dl=glucose,
        creatinine_mg_dl=creatinine,
        hba1c_percent=hba1c,
        insulin_mu_u_ml=insulin,
        total_cholesterol_mg_dl=ldl + hdl + (triglycerides / 5), # Friedewald estimation fallback
        triglycerides_mg_dl=triglycerides,
        hdl_mg_dl=hdl,
        ldl_mg_dl=ldl,
        vldl_mg_dl=triglycerides / 5,
        ast_u_l=25.0,
        alt_u_l=35.0,
        ggt_u_l=45.0,
        uric_acid_mg_dl=6.2,
        platelets_k_u_l=220.0,
        albumin_g_dl=albumin_g,
        ferritin_ng_ml=150.0,
        hs_crp_mg_l=hscrp,
        vitamin_d_ng_ml=vitd,
        testosterone_total_ng_dl=testo
    )
except Exception as e:
    st.error(f"Error de Coherencia Metabólica: {str(e)}")
    metabolic_panel = MetabolicPanelSchema()

# Create conditions list
conditions = []
if has_obesity:
    conditions.append(Condition(code="E66.9", title="Obesidad no especificada", system="CIE-10"))
if has_t2d:
    conditions.append(Condition(code="E11.9", title="Diabetes mellitus tipo 2 sin complicaciones", system="CIE-10"))
if has_htn:
    conditions.append(Condition(code="I10", title="Hipertensión esencial (primaria)", system="CIE-10"))
if has_dyslipidemia:
    conditions.append(Condition(code="E78.5", title="Dislipidemia no especificada", system="CIE-10"))
if has_nafld:
    conditions.append(Condition(code="K76.0", title="Hígado graso no alcohólico", system="CIE-10"))

# Create observations list
observations = [
    Observation(code="29463-7", value=weight, unit="kg"),
    Observation(code="8302-2", value=height, unit="cm"),
    Observation(code="WAIST-001", value=waist, unit="cm"),
    Observation(code="NECK-001", value=neck, unit="cm"),
    Observation(code="8480-6", value=systolic, unit="mmHg"),
    Observation(code="8462-4", value=diastolic, unit="mmHg"),
    Observation(code="TFEQ-UNCONTROLLED", value=tfeq_uncontrolled, category="Psychometry"),
    Observation(code="TFEQ-EMOTIONAL", value=tfeq_emotional, category="Psychometry"),
    Observation(code="AIS-001", value=ais_insomnia, category="Psychometry"),
    Observation(code="LIFE-EXERCISE", value=exercise_min, unit="min/week", category="Lifestyle"),
    Observation(code="LIFE-SLEEP", value=sleep_hours, unit="hours", category="Lifestyle"),
    Observation(code="BIA-MUSCLE-KG", value=current_ffm, unit="kg"),
]

# Create ClinicalHistory
clinical_history = ClinicalHistory(
    has_type2_diabetes=has_t2d,
    has_prediabetes=(not has_t2d and 5.7 <= hba1c < 6.5),
    has_hypertension=has_htn,
    has_dyslipidemia=has_dyslipidemia,
    has_nafld=has_nafld,
    has_heart_failure=has_hf,
    has_history_medullary_thyroid_carcinoma=has_mtc,
    has_history_men2=has_men2,
    phq9_item_9_score=phq9_item_9,
    pregnancy_status="unknown"
)

# Longitudinal encounters
longitudinal_encs = []
if use_longitudinal:
    # Baseline encounter (28 days ago)
    longitudinal_encs.append(LongitudinalEncounterEntry(
        encounter_id="sim-prev-01",
        encounter_date=datetime.now() - timedelta(days=28),
        weight_kg=prev_weight_28d,
        ffm_kg=prev_ffm_28d
    ))
    # Current encounter
    longitudinal_encs.append(LongitudinalEncounterEntry(
        encounter_id="sim-current",
        encounter_date=datetime.now(),
        weight_kg=weight,
        ffm_kg=current_ffm
    ))

# Assemble aggregate root Encounter
encounter = Encounter(
    id=str(uuid.uuid4()),
    demographics=demographics,
    metabolic_panel=metabolic_panel,
    conditions=conditions,
    observations=observations,
    history=clinical_history,
    longitudinal_encounters=longitudinal_encs
)

# --- CALCULATE & DISPLAY CORE CARDIOMETABOLIC INDICES ---
st.markdown("### 📊 Índices Computados (SSOT Domain Calculators)")
cols = st.columns(6)

with cols[0]:
    bmi_val = encounter.bmi
    st.metric("IMC (Índice Masa Corporal)", f"{bmi_val:.2f}" if bmi_val else "N/A", "kg/m²")
with cols[1]:
    egfr_val = encounter.egfr_ckd_epi
    st.metric("eGFR (Filttrado Glomerular)", f"{egfr_val:.1f}" if egfr_val else "N/A", "mL/min/1.73m²")
with cols[2]:
    homa_val = encounter.homa_ir
    st.metric("HOMA-IR (Resist. Insulina)", f"{homa_val:.2f}" if homa_val else "N/A")
with cols[3]:
    tyg_val = encounter.tyg_index
    st.metric("Índice TyG (Triglicéridos/Gluc)", f"{tyg_val:.2f}" if tyg_val else "N/A")
with cols[4]:
    mets_val = encounter.mets_ir
    st.metric("METS-IR (Sensib. Insulina)", f"{mets_val:.1f}" if mets_val else "N/A")
with cols[5]:
    pp_val = encounter.pulse_pressure
    st.metric("Presión de Pulso", f"{pp_val:.1f}" if pp_val else "N/A", "mmHg")

st.markdown("---")

# --- PIPELINE ADJUDICATION LOGIC ---
if run_analysis:
    st.markdown("### 🔬 Resultados de Adjudicación de Motores")
    
    with st.spinner("Procesando encuentro a través del runner de especialidades paralelizado..."):
        try:
            # Execute primary clinical engines in parallel
            runner = create_runner()
            results = runner.run_all(encounter)
            
            # Execute downstream Core Clinical Decisions
            from src.engines.domain import DecisionContext
            from src.engines.core_decisions import CoreClinicalDecisionEngine
            
            ctx = DecisionContext()
            
            # Map Axis outputs to context
            if "ATaxonomyMotor" in results:
                a_res = results["ATaxonomyMotor"]
                ctx.axis_a_code = a_res.metadata.get("code")
                a_label = str(a_res.calculated_value)
                ctx.is_slow_burn = ctx.axis_a_code == "A3" or "Lenta" in a_label
                ctx.has_sarcopenic_risk = "Sarcopenia" in a_label
                
            if "BDomainScoresMotor" in results:
                b_res = results["BDomainScoresMotor"]
                b_domains = b_res.metadata.get("domain_scores", [])
                for ds in b_domains:
                    code = ds.get("code")
                    comp = ds.get("completeness_status")
                    if code == "B_UNCONTROLLED" and comp == "complete":
                        ctx.has_uncontrolled_eating = True
                    elif code == "B_EMOTIONAL" and comp == "complete":
                        ctx.has_emotional_eating = True
                    elif code == "B_AFFECT" and comp == "partial":
                        ctx.has_affective_traits = True
                    elif code == "B_SLEEP" and comp == "complete":
                        ctx.has_clinical_insomnia = True
                        
            if "CStateMachineMotor" in results:
                c_res = results["CStateMachineMotor"]
                ctx.axis_c_code = "C2" if "C2" in str(c_res.calculated_value) else "C0"
                c_label = str(c_res.calculated_value)
                ctx.has_suboptimal_c = "C2" in c_label or "NON_RESPONDER" in c_label or "SUBOPTIMAL" in c_label
            
            # Gated medical history inputs
            ctx.has_advanced_ckd = (egfr_val is not None and egfr_val < 30)
            ctx.has_malnutrition_risk = False
            ctx.has_active_behavioral_referral = False
            
            core_engine = CoreClinicalDecisionEngine()
            core_result = core_engine.compute_from_context(encounter, ctx)
            results["CoreClinicalDecisions"] = core_result
            
        except Exception as e:
            st.error(f"Falla crítica en la pipeline de motores: {str(e)}")
            st.exception(e)
            results = {}

    if results:
        # Create Layout Tabs
        tab_actions, tab_axes, tab_pharma, tab_nutrition, tab_all = st.tabs([
            "📋 Acciones y Alertas de Seguridad",
            "🌐 Ejes de Diagnóstico (A-B-C-E)",
            "💊 Farmacoterapia de Precisión",
            "🥗 Nutrición de Precisión",
            "🗂️ Todos los Motores ({})".format(len(results))
        ])

        # --- TAB 1: ACTIONS & ALERTS ---
        with tab_actions:
            st.subheader("💡 Plan de Acción y Alertas del CDSS")
            
            # Safety checks and alerts first
            critical_alerts = []
            standard_alerts = []
            
            # Aggregate checklists and omissions
            checklist_items = []
            for name, res in results.items():
                if res and isinstance(res, AdjudicationResult):
                    if res.action_checklist:
                        for item in res.action_checklist:
                            checklist_items.append((name, item))
                    if res.critical_omissions:
                        for gap in res.critical_omissions:
                            critical_alerts.append(gap)
            
            # Display Critical Omissions (Red Alerts)
            if critical_alerts:
                st.error("⚠️ **ALERTAS DE SEGURIDAD CRÍTICAS / CONTRAINDICACIONES:**")
                for alert in critical_alerts:
                    st.markdown(f"""
                        <div style="background-color: #fee2e2; border-left: 5px solid #ef4444; padding: 15px; border-radius: 6px; margin-bottom: 10px;">
                            <strong style="color: #991b1b;">[{alert.drug_class}] - {alert.gap_type} (Severidad: {alert.severity.upper()})</strong><br>
                            <span style="color: #7f1d1d;">{alert.clinical_rationale}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No se detectaron contraindicaciones absolutas o brechas de seguridad críticas.")

            # Display Action Checklist by priority
            if checklist_items:
                st.markdown("#### Lista de Tareas Sugeridas para el Profesional")
                
                # Sort by priority
                priority_map = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                sorted_items = sorted(checklist_items, key=lambda x: priority_map.get(x[1].priority, 99))
                
                for origin_motor, item in sorted_items:
                    color = "#ef4444" if item.priority == "critical" else ("#f59e0b" if item.priority == "high" else ("#3b82f6" if item.priority == "medium" else "#10b981"))
                    st.markdown(f"""
                        <div style="background-color: white; border-left: 4px solid {color}; padding: 12px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 8px; border: 1px solid #e2e8f0;">
                            <strong>{item.task}</strong> <span style="font-size:0.75rem; background-color:#f1f5f9; padding:2px 6px; border-radius:4px; margin-left:8px;">{item.category.upper()}</span> 
                            <span style="color:{color}; font-size:0.75rem; font-weight:700;">[{item.priority.upper()}]</span><br>
                            <span style="font-size:0.85rem; color:#475569;">Rationale: {item.rationale}</span><br>
                            <span style="font-size:0.75rem; color:#94a3b8;">Origen: {origin_motor}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No se generaron tareas específicas en el checklist.")

        # --- TAB 2: CLINICAL AXES (A-B-C-E) ---
        with tab_axes:
            st.subheader("🌐 Estructuración de Ejes Clínicos (Taxonomía CDSS)")
            
            col_a, col_b = st.columns(2)
            col_c, col_e = st.columns(2)
            
            with col_a:
                st.markdown("#### Eje A: Fenotipo Fisiopatológico")
                if "ATaxonomyMotor" in results:
                    r = results["ATaxonomyMotor"]
                    st.info(f"**Clasificación:** {r.calculated_value}\n\n*Evidencia:* {r.explanation}")
                else:
                    st.warning("Motor de Taxonomía A3 no disponible.")

            with col_b:
                st.markdown("#### Eje B: Conducta y Estilo de Vida")
                if "BDomainScoresMotor" in results:
                    r = results["BDomainScoresMotor"]
                    scores = r.metadata.get("domain_scores", [])
                    for score in scores:
                        comp = score.get("completeness_status")
                        color = "green" if comp == "complete" else ("orange" if comp == "partial" else "gray")
                        st.markdown(f"- **{score.get('label')}:** :{color}[{comp.upper()}] (Score: {score.get('raw_score')})")
                else:
                    st.warning("Motor de Dominios B no disponible.")

            with col_c:
                st.markdown("#### Eje C: Trayectoria Longitudinal")
                if "CStateMachineMotor" in results:
                    r = results["CStateMachineMotor"]
                    st.info(f"**Estado de Adherencia:** {r.calculated_value}\n\n*Nota:* {r.metadata.get('label')}\n\n*Acción:* {r.metadata.get('suggested_action')}")
                else:
                    st.warning("Motor de Estado C no disponible.")

            with col_e:
                st.markdown("#### Eje E: Estadio EOSS (Comorbilidad)")
                if "EOSSStagingMotor" in results:
                    r = results["EOSSStagingMotor"]
                    st.info(f"**Estadio EOSS:** {r.calculated_value}\n\n*Explicación:* {r.explanation}")
                else:
                    st.warning("Motor EOSS Staging no disponible.")

        # --- TAB 3: PHARMACOTHERAPY OF PRECISION ---
        with tab_axes:
            pass # Tab placeholder handled by streamlit tabs list order mapping
            
        with tab_pharma:
            st.subheader("💊 Decisiones Farmacológicas de Precisión")
            
            # Display Core decisions related to pharmacology
            if "CoreClinicalDecisions" in results:
                core_res = results["CoreClinicalDecisions"]
                recs = core_res.metadata.get("recommendations", [])
                pharma_recs = [r for r in recs if r.get("domain") == "pharmacotherapy"]
                
                if pharma_recs:
                    st.markdown("#### Recomendación de Iniciación Terapéutica")
                    for rec in pharma_recs:
                        badge_color = "status-confirmed" if rec.get("status") == "active" else "status-locked"
                        st.markdown(f"""
                            <div class="metric-card">
                                <span class="status-badge {badge_color}">{rec.get('status').upper()}</span>
                                <div class="engine-header">{rec.get('recommendation_code')}</div>
                                <p><strong>Base Clínica:</strong> {rec.get('human_readable_basis')}</p>
                                <div class="card-footer">Requisito ID: {rec.get('requirement_id')} | Disparado por: {', '.join(rec.get('depends_on', []))}</div>
                            </div>
                        """, unsafe_allow_html=True)
            
            # Display Pharma Precision specific motor
            if "PharmaPrecisionMotor" in results:
                r = results["PharmaPrecisionMotor"]
                st.markdown("#### Adjudicación de Beneficio Orgánico y Seguridad")
                st.write(f"**Conclusión:** {r.explanation}")
                
                if r.evidence:
                    st.markdown("**Evidencia de Beneficio Cardiometabólico:**")
                    for ev in r.evidence:
                        st.markdown(f"- **{ev.display}:** {ev.value} (Umbral: {ev.threshold or 'N/A'})")

        # --- TAB 4: PRECISION NUTRITION ---
        with tab_nutrition:
            st.subheader("🥗 Terapia Nutricional y Proteica Personalizada")
            
            # Display Core decisions related to nutrition
            if "CoreClinicalDecisions" in results:
                core_res = results["CoreClinicalDecisions"]
                recs = core_res.metadata.get("recommendations", [])
                nut_recs = [r for r in recs if r.get("domain") in ["nutrition", "protein"]]
                
                if nut_recs:
                    st.markdown("#### Prescripción de Macronutrientes y Calórica")
                    nut_cols = st.columns(len(nut_recs))
                    for i, rec in enumerate(nut_recs):
                        with nut_cols[i]:
                            badge_color = "status-confirmed" if rec.get("status") == "active" else "status-locked"
                            st.markdown(f"""
                                <div class="metric-card">
                                    <span class="status-badge {badge_color}">{rec.get('status').upper()}</span>
                                    <div class="engine-header">{rec.get('recommendation_code')}</div>
                                    <p>{rec.get('human_readable_basis')}</p>
                                    <div class="card-footer">Déficit/Target: {rec.get('audit_payload', {}).get('caloric_deficit_target_kcal', 'N/A') or rec.get('audit_payload', {}).get('protein_target_g_kg', 'N/A')}</div>
                                </div>
                            """, unsafe_allow_html=True)

            # Display Precision Nutrition specific motor
            if "PrecisionNutritionMotor" in results:
                r = results["PrecisionNutritionMotor"]
                st.markdown("#### Fenotipo Dietario Acosta & Triadas Aterogénicas")
                st.info(f"**Perfil Dietario Sugerido:** {r.calculated_value}\n\n*Racional:* {r.explanation}")
                
                if r.metadata.get("phenotypes"):
                    st.markdown("**Fenotipos Detectados:**")
                    st.write(", ".join(r.metadata["phenotypes"]))

        # --- TAB 5: ALL MOTORS DETAILS ---
        with tab_all:
            st.subheader("🗂️ Registro Detallado de Motores Clínicos")
            
            # Search filter for motors
            search_query = st.text_input("Filtrar motores por nombre", "")
            
            for name, res in results.items():
                if search_query and search_query.lower() not in name.lower():
                    continue
                    
                if not isinstance(res, AdjudicationResult):
                    continue
                
                # Check status color
                status = res.estado_ui
                badge_class = "status-confirmed"
                if status == "PROBABLE_WARNING":
                    badge_class = "status-warning"
                elif status == "INDETERMINATE_LOCKED":
                    badge_class = "status-locked"
                elif "Error" in res.calculated_value:
                    badge_class = "status-error"

                with st.expander(f"{name} — {res.calculated_value}", expanded=False):
                    st.markdown(f"""
                        <span class="status-badge {badge_class}">{status}</span>
                        <p><strong>Resultado Calculado:</strong> {res.calculated_value}</p>
                        <p><strong>Narrativa Técnica:</strong> {res.explanation}</p>
                        <p><strong>Confianza del Nivel de Evidencia (GRADE):</strong> {res.confidence:.2f}</p>
                    """, unsafe_allow_html=True)
                    
                    if res.evidence:
                        st.markdown("**Evidencia Evaluada:**")
                        for ev in res.evidence:
                            st.write(f"- {ev.type} | Code: `{ev.code}` | Value: `{ev.value}` | Display: *{ev.display}*")
                            
                    st.markdown(f"<div class='card-footer'>Requisito ID: {res.requirement_id or 'N/A'} | Hash de Integridad: {res.log_id or 'UNKNOWN'}</div>", unsafe_allow_html=True)
else:
    st.info("👈 Configura los parámetros del paciente en el panel lateral y haz clic en **EJECUTAR ADJUDICACIÓN CLÍNICA**.")

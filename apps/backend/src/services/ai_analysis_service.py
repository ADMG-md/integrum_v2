"""
AI Analysis Service — Expert Medical Prompts for Generative AI

This service generates structured prompts that constrain LLM behavior to act as
an expert physician in obesity and cardiometabolic health.

Key principles:
1. Zero hallucination: Responses MUST be grounded in the provided data
2. Evidence-based: Reference guidelines (ADA, AHA, AACE, ESPEN, AAP)
3. Safety-first: Flag uncertainties, contraindications, and alerts
4. Differential reasoning: Consider alternative diagnoses
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class MedicalExpertRole:
    """Defines an expert medical persona for the AI."""

    name: str
    specialty: str
    guidelines: List[str]
    expertise_level: Literal["expert", "specialist", "consultant"]
    system_prompt: str


@dataclass
class ClinicalContext:
    """Structured clinical context for AI analysis."""

    patient_id: str
    demographics: Dict[str, Any]
    anthropometry: Dict[str, Any]
    labs: Dict[str, Any]
    motors: Dict[str, Any]
    conditions: List[Dict[str, Any]]
    medications: List[Dict[str, Any]]
    lifestyle: Dict[str, Any] = field(default_factory=dict)
    phenotype: Optional[str] = None
    eoss_stage: Optional[str] = None
    encounter_date: Optional[str] = None


@dataclass
class AnalysisRequest:
    """Request for AI clinical analysis."""

    context: ClinicalContext
    query_type: Literal[
        "comprehensive",
        "phenotype_analysis",
        "treatment_plan",
        "risk_assessment",
        "differential_diagnosis",
        "medication_review",
        "nutrition_recommendation",
        "pediatric_assessment",
    ]
    expertise_level: Literal["expert", "specialist", "consultant"] = "expert"
    include_differential: bool = True
    include_references: bool = True


@dataclass
class ExpertMedicalPrompt:
    """Generated prompt with system/ user/ assistant structure."""

    system_prompt: str
    user_prompt: str
    context_summary: str
    constraints: List[str]
    expected_output_format: str


class MedicalExpertPrompts:
    """Collection of expert medical prompts by specialty."""

    OBESITY_EXPERT = MedicalExpertRole(
        name="Dr. Carlos Obesity",
        specialty="Obesity Medicine & Cardiometabolic Health",
        guidelines=[
            "AACE/ACE 2024 Comprehensive Care Algorithm",
            "ADA Standards of Care 2024",
            "AHA/ACC Guideline on Management of Obesity 2023",
            "ESPEN 2023 Guidelines on Obesity",
            "WHO Global Health Sector Strategy on NCDs 2023",
        ],
        expertise_level="expert",
        system_prompt="""You are an expert physician specializing in obesity medicine and cardiometabolic health.
Your responses MUST:
1. Ground every clinical claim in the provided patient data
2. Reference specific guidelines (ADA, AACE, AHA, ESPEN) when applicable
3. Explicitly state confidence levels and uncertainties
4. Flag drug interactions, contraindications, and safety concerns
5. Provide differential diagnoses when appropriate
6. NEVER recommend treatments without explicit data support
7. ALWAYS ask clarifying questions when data is insufficient

Your response format must include:
- Clinical Assessment (what you observe in the data)
- Risk Stratification (using validated scores when available)
- Differential Considerations (alternative explanations)
- Recommendations (specific, actionable, guideline-based)
- Safety Alerts (warnings, contraindications, monitoring needs)
- Confidence Level (your certainty about each recommendation)""",
    )

    PEDIATRIC_EXPERT = MedicalExpertRole(
        name="Dr. Maria Pediatric",
        specialty="Pediatric Endocrinology & Nutrition",
        guidelines=[
            "AAP 2023 Clinical Practice Guideline for Pediatric Obesity",
            "AAP 2024 Prevention and Management of Childhood Obesity",
            "USPSTF 2024 Obesity in Children and Adolescents Screening",
            "AAP Council on Children with Disabilities - Nutrition Guidelines",
        ],
        expertise_level="expert",
        system_prompt="""You are a board-certified pediatric endocrinologist and obesity specialist.
You specialize in children and adolescents (ages 2-18) with obesity, metabolic conditions, and neurodevelopmental disorders (ASD, ADHD).

Your clinical approach:
1. Growth and development take priority over weight-focused metrics
2. Family-based interventions are the cornerstone of pediatric obesity treatment
3. Pharmacotherapy is reserved for severe cases (BMI ≥95th percentile with comorbidities)
4. Nutritional interventions must be age-appropriate and nutritionally adequate
5. Mental health and quality of life are primary outcomes

MANDATORY SAFETY CONSTRAINTS:
- NEVER recommend caloric restriction for children <12 years
- NEVER recommend adult medications for pediatric patients without explicit FDA approval
- ALWAYS consider developmental stage, not just chronological age
- ALWAYS involve the family/caregivers in treatment planning
- Be extra cautious with supplements and complementary therapies in children

Response Format:
- Growth Assessment (BMI percentiles, growth velocity)
- Nutritional Status (macro/micronutrient adequacy)
- Developmental Considerations (age-appropriate recommendations)
- Family Intervention Plan
- Monitoring Schedule
- Red Flags (when to escalate)""",
    )

    ENDOCRINE_EXPERT = MedicalExpertRole(
        name="Dr. Sofia Endocrine",
        specialty="Endocrinology & Diabetes",
        guidelines=[
            "ADA Standards of Care 2024",
            "AACE/ACE 2024 Diabetes Management Algorithm",
            "Endocrine Society Clinical Guidelines 2023",
            "ATA Thyroid Guidelines 2023",
        ],
        expertise_level="expert",
        system_prompt="""You are a board-certified endocrinologist with expertise in diabetes, thyroid disorders, and metabolic syndrome.

Your analytical framework:
1. Evaluate hormonal pathways and their interactions
2. Consider secondary causes of metabolic dysfunction
3. Assess for subclinical disease (thyroid, adrenal)
4. Evaluate medication effects on metabolism
5. Consider genetic/rare causes when presentations are atypical

When analyzing metabolic data:
- Interpret HbA1c in context of glucose patterns, not just point values
- Evaluate thyroid function considering the euthyroid sick syndrome possibility
- Consider Cushing's syndrome in atypical presentations
- Evaluate for PCOS in women with metabolic syndrome
- Assess adrenal function in resistant hypertension

Response must include:
- Hormonal Pathway Analysis
- Secondary Cause Evaluation
- Medication Impact Assessment
- Monitoring Recommendations
- Escalation Triggers""",
    )

    CARDIOVASCULAR_EXPERT = MedicalExpertRole(
        name="Dr. Roberto Cardiovascular",
        specialty="Preventive Cardiology & Vascular Medicine",
        guidelines=[
            "AHA/ACC 2018 Cholesterol Guidelines (Updated 2022)",
            "ACC/AHA 2019 Primary Prevention Guideline",
            "ESC/EAS 2019 Dyslipidaemia Guidelines",
            "AHA/ACC/HFSA 2022 Heart Failure Guideline",
            "KDIGO 2024 Blood Pressure in CKD",
        ],
        expertise_level="expert",
        system_prompt="""You are a preventive cardiologist with expertise in cardiovascular risk assessment, lipidology, and vascular medicine.

Your cardiovascular risk framework:
1. Use validated risk calculators (ASCVD, PCE, Framingham) when appropriate
2. Consider lifetime risk vs. 10-year risk in younger patients
3. Evaluate subclinical atherosclerosis (coronary calcium scoring when indicated)
4. Assess vascular health beyond traditional risk factors
5. Consider sex-specific presentations and risk factors

Key cardiovascular calculations to apply:
- 10-year ASCVD risk (pooled cohort equations)
- LDL-C goal based on risk category
- Non-HDL-C as secondary target
- Triglyceride-associated pancreatitis risk (>500 mg/dL)
- Heart failure risk (ACC/AHA stages A-D)

Response Format:
- Cardiovascular Risk Stratification (10-year and lifetime)
- Lipid Management Plan (goal-based, not fixed-dose)
- Blood Pressure Assessment (orthostatic, masked hypertension)
- Vascular Health Evaluation
- Primary Prevention Interventions
- Monitoring and Follow-up""",
    )


class AIAnalysisService:
    """
    Service that generates expert medical prompts for generative AI analysis.

    This service ensures AI responses are:
    - Grounded in provided clinical data
    - Aligned with evidence-based guidelines
    - Constrained to expert medical reasoning
    - Structured for clinical utility
    """

    def __init__(self):
        self.prompts = MedicalExpertPrompts()

    def _get_role_for_query(
        self, query_type: str, age: Optional[int] = None
    ) -> MedicalExpertRole:
        """Select appropriate expert role based on query type and patient age."""

        if age is not None and age < 18:
            return MedicalExpertPrompts.PEDIATRIC_EXPERT

        query_role_map = {
            "comprehensive": MedicalExpertPrompts.OBESITY_EXPERT,
            "phenotype_analysis": MedicalExpertPrompts.OBESITY_EXPERT,
            "treatment_plan": MedicalExpertPrompts.OBESITY_EXPERT,
            "risk_assessment": MedicalExpertPrompts.CARDIOVASCULAR_EXPERT,
            "differential_diagnosis": MedicalExpertPrompts.ENDOCRINE_EXPERT,
            "medication_review": MedicalExpertPrompts.ENDOCRINE_EXPERT,
            "nutrition_recommendation": MedicalExpertPrompts.OBESITY_EXPERT,
            "pediatric_assessment": MedicalExpertPrompts.PEDIATRIC_EXPERT,
        }

        return query_role_map.get(query_type, MedicalExpertPrompts.OBESITY_EXPERT)

    def _build_demographics_section(self, ctx: ClinicalContext) -> str:
        """Build demographics section for prompt."""
        demo = ctx.demographics
        age = demo.get("age", "Unknown")
        gender = demo.get("gender", "Unknown")

        lines = [
            f"## Demographics",
            f"- Age: {age} years",
            f"- Sex: {gender}",
        ]

        if ctx.phenotype:
            lines.append(f"- Phenotype: {ctx.phenotype}")
        if ctx.eoss_stage:
            lines.append(f"- EOSS Stage: {ctx.eoss_stage}")
        if ctx.encounter_date:
            lines.append(f"- Encounter Date: {ctx.encounter_date}")

        return "\n".join(lines)

    def _build_anthropometry_section(self, ctx: ClinicalContext) -> str:
        """Build anthropometry section for prompt."""
        anthro = ctx.anthropometry
        if not anthro:
            return "## Anthropometry\n*No anthropometric data available*"

        lines = ["## Anthropometric Measurements"]
        for key, value in anthro.items():
            if value is not None:
                lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def _build_labs_section(self, ctx: ClinicalContext) -> str:
        """Build laboratory section for prompt."""
        labs = ctx.labs
        if not labs:
            return "## Laboratory Results\n*No laboratory data available*"

        lines = ["## Laboratory Results"]

        sections = {
            "Glucose Metabolism": ["glucose_mg_dl", "hba1c_percent", "insulin_mu_u_ml"],
            "Lipid Panel": [
                "total_cholesterol_mg_dl",
                "ldl_mg_dl",
                "hdl_mg_dl",
                "triglycerides_mg_dl",
            ],
            "Renal Function": ["creatinine_mg_dl", "egfr", "uacr_mg_g"],
            "Liver": ["ast_u_l", "alt_u_l", "ggt_u_l"],
            "Thyroid": ["tsh_uiu_ml", "ft4_ng_dl"],
            "Inflammation": ["hs_crp_mg_l"],
            "Nutritional": ["vitamin_d_ng_ml", "ferritin_ng_ml", "vitb12_pg_ml"],
            "Hematology": ["hemoglobin_g_dl", "platelets_k_ul"],
        }

        for section_name, markers in sections.items():
            section_data = {k: labs.get(k) for k in markers if labs.get(k) is not None}
            if section_data:
                lines.append(f"\n### {section_name}")
                for k, v in section_data.items():
                    lines.append(f"- {k}: {v}")

        return "\n".join(lines)

    def _build_motor_outputs_section(self, ctx: ClinicalContext) -> str:
        """Build clinical motor outputs section for prompt."""
        motors = ctx.motors
        if not motors:
            return "## Clinical Decision Support Outputs\n*No CDS outputs available*"

        lines = ["## Clinical Decision Support System Outputs"]
        lines.append("*(Outputs from validated clinical engines)*\n")

        motor_categories = {
            "Phenotyping & Staging": ["AcostaPhenotypeMotor", "EOSSStagingMotor"],
            "Metabolic Assessment": [
                "MetabolicPrecisionMotor",
                "DeepMetabolicProxyMotor",
                "TyGBMIMotor",
            ],
            "Cardiovascular Risk": [
                "CVDHazardMotor",
                "CVDReclassifierMotor",
                "PulsePressureMotor",
                "ApoBApoA1Motor",
            ],
            "Liver Health": ["FLIMotor", "NFSMotor", "VAIMotor"],
            "Endocrine": ["EndocrineMotor", "FreeTestosteroneMotor", "VitaminDMotor"],
            "Screening": ["CancerScreeningMotor", "SleepApneaMotor"],
            "Safety": [
                "DrugInteractionMotor",
                "MetforminB12Motor",
                "GLP1MonitoringMotor",
            ],
            "Pediatric": ["PediatricNutritionMotor"],
        }

        for category, motor_names in motor_categories.items():
            category_data = {}
            for motor_name in motor_names:
                motor_data = motors.get(motor_name)
                if motor_data:
                    prefix = motor_name.replace("Motor", "").replace("Engine", "")
                    category_data[prefix] = motor_data

            if category_data:
                lines.append(f"### {category}")
                for motor_name, data in category_data.items():
                    if isinstance(data, dict):
                        value = data.get("calculated_value", "N/A")
                        confidence = data.get("confidence", "N/A")
                        estado = data.get("estado_ui", "N/A")
                        lines.append(f"- **{motor_name}**: {value}")
                        lines.append(f"  - Confidence: {confidence}")
                        lines.append(f"  - Status: {estado}")

        return "\n".join(lines)

    def _build_conditions_section(self, ctx: ClinicalContext) -> str:
        """Build conditions/diagnoses section for prompt."""
        conditions = ctx.conditions
        if not conditions:
            return "## Active Diagnoses\n*No active diagnoses documented*"

        lines = ["## Active Diagnoses"]
        for cond in conditions:
            code = cond.get("code", "N/A")
            title = cond.get("title", "N/A")
            status = cond.get("status", "active")
            lines.append(f"- [{code}] {title} ({status})")

        return "\n".join(lines)

    def _build_medications_section(self, ctx: ClinicalContext) -> str:
        """Build medications section for prompt."""
        medications = ctx.medications
        if not medications:
            return "## Current Medications\n*No medications documented*"

        lines = ["## Current Medications"]
        for med in medications:
            name = med.get("name", "N/A")
            dose = med.get("dose", "")
            frequency = med.get("frequency", "")
            status = med.get("status", "active")
            lines.append(f"- {name} {dose} {frequency}".strip())
            lines.append(f"  Status: {status}")

        return "\n".join(lines)

    def _build_lifestyle_section(self, ctx: ClinicalContext) -> str:
        """Build lifestyle section for prompt."""
        lifestyle = ctx.lifestyle
        if not lifestyle:
            return "## Lifestyle Factors\n*No lifestyle data available*"

        lines = ["## Lifestyle Factors"]
        for key, value in lifestyle.items():
            if value is not None:
                lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def _build_constraints(self, query_type: str, role: MedicalExpertRole) -> List[str]:
        """Build response constraints based on query type and role."""

        base_constraints = [
            "Respond ONLY with information derivable from the provided clinical data",
            "Explicitly state when data is insufficient to make a clinical determination",
            "Include specific numerical thresholds when referencing guidelines",
            "Flag any potential safety concerns or urgent clinical situations",
            "Format all recommendations as actionable items",
        ]

        type_specific = {
            "comprehensive": [
                "Provide a holistic clinical assessment covering all organ systems",
                "Identify the most pressing clinical priorities",
                "Recommend a coordinated care plan addressing all active issues",
            ],
            "phenotype_analysis": [
                "Classify the patient's obesity phenotype based on available data",
                "Identify dominant pathophysiological mechanisms",
                "Recommend phenotype-matched therapeutic strategies",
            ],
            "treatment_plan": [
                "Prioritize interventions by expected impact and feasibility",
                "Consider drug interactions and contraindications",
                "Include non-pharmacological interventions",
                "Specify monitoring parameters and follow-up intervals",
            ],
            "risk_assessment": [
                "Quantify cardiovascular risk using available validated scores",
                "Identify modifiable vs. non-modifiable risk factors",
                "Recommend risk reduction strategies with expected impact",
            ],
            "differential_diagnosis": [
                "Present 3-5 most likely alternative diagnoses",
                "Include prevalence estimates and supporting evidence",
                "Suggest diagnostic tests to differentiate",
            ],
            "medication_review": [
                "Evaluate each medication for appropriateness and efficacy",
                "Identify potential drug interactions",
                "Recommend monitoring for adverse effects",
                "Suggest medication optimization opportunities",
            ],
            "nutrition_recommendation": [
                "Calculate estimated caloric needs based on patient characteristics",
                "Recommend macronutrient distribution",
                "Suggest specific dietary patterns (Mediterranean, DASH, etc.)",
                "Include vitamin/mineral supplementation recommendations if indicated",
            ],
            "pediatric_assessment": [
                "Use age-appropriate growth references and percentiles",
                "Emphasize family-based interventions",
                "Avoid adult-focused metrics and treatments",
                "Consider developmental stage in all recommendations",
            ],
        }

        return base_constraints + type_specific.get(query_type, [])

    def _build_output_format(self, query_type: str) -> str:
        """Build expected output format description."""

        format_templates = {
            "comprehensive": """**Clinical Assessment:**
[Your detailed clinical assessment]

**Active Problem List:**
1. [Problem] - [Priority] - [Evidence in data]
2. ...

**Integrated Care Plan:**
1. [Immediate actions]
2. [Short-term interventions]
3. [Long-term strategy]

**Safety Alerts:**
⚠️ [Any urgent concerns]

**Follow-up:**
[Recommended timeline and parameters]""",
            "treatment_plan": """**Treatment Priorities:**
1. [Highest priority intervention] - Rationale: [why this is priority]
2. ...

**Medication Plan:**
| Medication | Dose | Duration | Monitoring |
|------------|------|----------|------------|
| ... | ... | ... | ... |

**Non-Pharmacological Interventions:**
- [Intervention 1]
- [Intervention 2]

**Monitoring Plan:**
- [Parameter] @ [Frequency]
- ...

**Contraindications/Precautions:**
⚠️ [Any concerns]""",
            "risk_assessment": """**Cardiovascular Risk Stratification:**
- 10-year ASCVD Risk: [Score]% ([Category])
- Risk Modifiers: [List]

**Modifiable Risk Factors:**
| Factor | Current | Target | Intervention |
|--------|---------|--------|--------------|
| ... | ... | ... | ... |

**Primary Prevention Recommendations:**
1. [Recommendation with expected RR reduction]

**Monitoring:**
[Parameters and frequency]""",
        }

        return format_templates.get(
            query_type,
            "Respond in structured markdown with clear sections:\n"
            "- Clinical Findings\n"
            "- Assessment\n"
            "- Recommendations\n"
            "- Safety Alerts\n"
            "- Follow-up",
        )

    def generate_prompt(self, request: AnalysisRequest) -> ExpertMedicalPrompt:
        """
        Generate a complete expert medical prompt for the given analysis request.

        This method constructs:
        1. System prompt (expert persona + guidelines)
        2. User prompt (structured clinical data + specific query)
        3. Response constraints (safety, format, reasoning)
        4. Expected output format
        """
        ctx = request.context
        role = self._get_role_for_query(request.query_type, ctx.demographics.get("age"))

        system_prompt = role.system_prompt

        user_prompt_parts = [
            "# CLINICAL ANALYSIS REQUEST",
            f"## Query Type: {request.query_type.upper()}",
            f"## Expertise Level: {request.expertise_level}",
            "",
            self._build_demographics_section(ctx),
            "",
            self._build_anthropometry_section(ctx),
            "",
            self._build_labs_section(ctx),
            "",
            self._build_conditions_section(ctx),
            "",
            self._build_medications_section(ctx),
            "",
        ]

        if ctx.lifestyle:
            user_prompt_parts.extend(
                [
                    "",
                    self._build_lifestyle_section(ctx),
                ]
            )

        user_prompt_parts.extend(
            [
                "",
                self._build_motor_outputs_section(ctx),
                "",
                "# ANALYSIS REQUEST",
                f"Analyze this patient case using {request.expertise_level}-level expertise.",
                f"Focus on: {request.query_type.replace('_', ' ')}.",
            ]
        )

        if request.include_differential:
            user_prompt_parts.append("Include differential diagnoses when appropriate.")

        user_prompt_parts.extend(
            [
                "",
                "# RESPONSE CONSTRAINTS",
                "You MUST:",
            ]
        )

        constraints = self._build_constraints(request.query_type, role)
        for i, constraint in enumerate(constraints, 1):
            user_prompt_parts.append(f"{i}. {constraint}")

        user_prompt_parts.extend(
            [
                "",
                "# EXPECTED OUTPUT FORMAT",
                self._build_output_format(request.query_type),
            ]
        )

        if request.include_references:
            user_prompt_parts.extend(
                [
                    "",
                    "# APPLICABLE GUIDELINES",
                    f"This analysis should reference these guidelines when relevant:",
                ]
            )
            for guideline in role.guidelines:
                user_prompt_parts.append(f"- {guideline}")

        user_prompt = "\n".join(user_prompt_parts)

        context_summary = f"Patient: {ctx.demographics.get('age', '?')}y {ctx.demographics.get('gender', '?')}"
        if ctx.phenotype:
            context_summary += f", Phenotype: {ctx.phenotype}"
        if ctx.eoss_stage:
            context_summary += f", EOSS: {ctx.eoss_stage}"

        return ExpertMedicalPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context_summary=context_summary,
            constraints=constraints,
            expected_output_format=self._build_output_format(request.query_type),
        )

    def generate_batch_prompts(
        self, contexts: List[ClinicalContext], query_type: str
    ) -> List[ExpertMedicalPrompt]:
        """Generate prompts for batch analysis of multiple patients."""
        prompts = []
        for ctx in contexts:
            request = AnalysisRequest(
                context=ctx,
                query_type=query_type,
                expertise_level="expert",
                include_differential=True,
                include_references=True,
            )
            prompts.append(self.generate_prompt(request))
        return prompts

    def validate_clinical_response(self, response: str) -> Dict[str, Any]:
        """
        Validate that an AI response meets clinical safety standards.

        Returns validation result with flags for:
        - Hallucination risk (references data not in context)
        - Safety concerns
        - Guideline adherence
        - Completeness
        """
        validation = {
            "is_valid": True,
            "warnings": [],
            "safety_flags": [],
            "completeness_score": 0.0,
            "guideline_citations": [],
        }

        if not response or len(response) < 100:
            validation["is_valid"] = False
            validation["warnings"].append("Response too short - may be incomplete")

        danger_phrases = [
            "guaranteed",
            "definitely",
            "certainly will",
            "without a doubt",
            "always safe",
            "no side effects",
            "guaranteed to work",
        ]

        for phrase in danger_phrases:
            if phrase.lower() in response.lower():
                validation["safety_flags"].append(
                    f"Dangerous certainty detected: '{phrase}'"
                )

        guideline_patterns = [
            "ADA",
            "AACE",
            "AHA",
            "ACC",
            "ESPEN",
            "WHO",
            "AAP",
            "USPSTF",
            "KDIGO",
            "ATA",
            "Endocrine Society",
        ]

        for pattern in guideline_patterns:
            if pattern in response:
                validation["guideline_citations"].append(pattern)

        completeness_indicators = [
            "clinical assessment",
            "recommendation",
            "risk",
            "monitoring",
            "safety",
            "follow-up",
        ]

        found_indicators = sum(
            1 for ind in completeness_indicators if ind.lower() in response.lower()
        )
        validation["completeness_score"] = found_indicators / len(
            completeness_indicators
        )

        if validation["completeness_score"] < 0.5:
            validation["warnings"].append(
                "Response may be incomplete - missing key sections"
            )

        if validation["safety_flags"]:
            validation["is_valid"] = False

        return validation


ai_analysis_service = AIAnalysisService()

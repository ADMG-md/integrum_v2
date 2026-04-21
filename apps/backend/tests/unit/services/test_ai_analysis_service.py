"""
Tests for AI Analysis Service - Expert Medical Prompts

Validates:
1. Clinical context building
2. Prompt generation for different query types
3. Role selection based on patient age
4. Response validation
5. Safety constraints enforcement
"""

import pytest
from src.services.ai_analysis_service import (
    AIAnalysisService,
    ClinicalContext,
    AnalysisRequest,
    MedicalExpertPrompts,
)


@pytest.fixture
def service():
    return AIAnalysisService()


@pytest.fixture
def sample_context():
    """Sample clinical context for testing."""
    return ClinicalContext(
        patient_id="test-patient-001",
        demographics={"age": 55, "gender": "male"},
        anthropometry={
            "weight_kg": 110,
            "height_cm": 175,
            "waist_cm": 115,
        },
        labs={
            "glucose_mg_dl": 115,
            "hba1c_percent": 6.2,
            "ldl_mg_dl": 145,
            "hdl_mg_dl": 38,
            "triglycerides_mg_dl": 220,
        },
        motors={
            "AcostaPhenotypeMotor": {
                "calculated_value": "PHENOTYPE_B",
                "confidence": 0.85,
                "estado_ui": "CONFIRMED",
            },
            "EOSSStagingMotor": {
                "calculated_value": "Stage 2",
                "confidence": 0.90,
                "estado_ui": "CONFIRMED",
            },
            "CVDHazardMotor": {
                "calculated_value": "15.2% 10-year ASCVD risk",
                "confidence": 0.88,
                "estado_ui": "PROBABLE_RECOMMENDATION",
            },
        },
        conditions=[
            {"code": "E11.9", "title": "Type 2 Diabetes Mellitus"},
            {"code": "I10", "title": "Essential Hypertension"},
        ],
        medications=[
            {"name": "Metformin", "dose": "1000mg", "status": "active"},
            {"name": "Lisinopril", "dose": "20mg", "status": "active"},
        ],
        phenotype="PHENOTYPE_B",
        eoss_stage="Stage 2",
        encounter_date="2026-04-13",
    )


@pytest.fixture
def pediatric_context():
    """Sample pediatric clinical context for testing."""
    return ClinicalContext(
        patient_id="test-pediatric-001",
        demographics={"age": 12, "gender": "female"},
        anthropometry={
            "weight_kg": 55,
            "height_cm": 150,
            "waist_cm": 80,
        },
        labs={
            "glucose_mg_dl": 95,
            "hba1c_percent": 5.4,
            "total_cholesterol_mg_dl": 170,
        },
        motors={
            "PediatricNutritionMotor": {
                "calculated_value": "Pediatric Nutrition: obesity",
                "confidence": 0.85,
                "estado_ui": "PROBABLE_RECOMMENDATION",
            },
        },
        conditions=[
            {"code": "E66.9", "title": "Obesity"},
            {"code": "F90.9", "title": "ADHD"},
        ],
        medications=[],
        encounter_date="2026-04-13",
    )


class TestRoleSelection:
    """Test expert role selection based on query type and patient age."""

    def test_adult_gets_obesity_expert(self, service, sample_context):
        """T-AI-ROLE-01: Adult patient gets obesity expert role."""
        role = service._get_role_for_query("comprehensive", age=55)
        assert role.name == "Dr. Carlos Obesity"
        assert "obesity" in role.specialty.lower()

    def test_pediatric_gets_pediatric_expert(self, service, pediatric_context):
        """T-AI-ROLE-02: Pediatric patient gets pediatric expert role."""
        role = service._get_role_for_query("comprehensive", age=12)
        assert role.name == "Dr. Maria Pediatric"
        assert "pediatric" in role.specialty.lower()

    def test_risk_assessment_gets_cardio_expert(self, service, sample_context):
        """T-AI-ROLE-03: Risk assessment query gets cardiovascular expert."""
        role = service._get_role_for_query("risk_assessment", age=55)
        assert role.name == "Dr. Roberto Cardiovascular"

    def test_differential_diagnosis_gets_endocrine_expert(
        self, service, sample_context
    ):
        """T-AI-ROLE-04: Differential diagnosis gets endocrine expert."""
        role = service._get_role_for_query("differential_diagnosis", age=55)
        assert role.name == "Dr. Sofia Endocrine"


class TestPromptGeneration:
    """Test prompt generation for different analysis types."""

    def test_comprehensive_prompt_structure(self, service, sample_context):
        """T-AI-PROMPT-01: Comprehensive prompt has all required sections."""
        request = AnalysisRequest(
            context=sample_context,
            query_type="comprehensive",
            expertise_level="expert",
        )
        prompt = service.generate_prompt(request)

        assert hasattr(prompt, "system_prompt")
        assert hasattr(prompt, "user_prompt")
        assert len(prompt.system_prompt) > 100
        assert len(prompt.user_prompt) > 100

    def test_prompt_includes_demographics(self, service, sample_context):
        """T-AI-PROMPT-02: Prompt includes patient demographics."""
        request = AnalysisRequest(
            context=sample_context,
            query_type="comprehensive",
        )
        prompt = service.generate_prompt(request)

        assert "55" in prompt.user_prompt
        assert "male" in prompt.user_prompt.lower()
        assert "Demographics" in prompt.user_prompt

    def test_prompt_includes_labs(self, service, sample_context):
        """T-AI-PROMPT-03: Prompt includes laboratory data."""
        request = AnalysisRequest(
            context=sample_context,
            query_type="comprehensive",
        )
        prompt = service.generate_prompt(request)

        assert "Glucose Metabolism" in prompt.user_prompt
        assert "115" in prompt.user_prompt
        assert "hba1c" in prompt.user_prompt.lower()

    def test_prompt_includes_motor_outputs(self, service, sample_context):
        """T-AI-PROMPT-04: Prompt includes CDS motor outputs."""
        request = AnalysisRequest(
            context=sample_context,
            query_type="comprehensive",
        )
        prompt = service.generate_prompt(request)

        assert "Clinical Decision Support" in prompt.user_prompt
        assert "PHENOTYPE_B" in prompt.user_prompt
        assert "Stage 2" in prompt.user_prompt

    def test_prompt_includes_constraints(self, service, sample_context):
        """T-AI-PROMPT-05: Prompt includes response constraints."""
        request = AnalysisRequest(
            context=sample_context,
            query_type="comprehensive",
        )
        prompt = service.generate_prompt(request)

        assert len(prompt.constraints) > 0
        assert any("data" in c.lower() for c in prompt.constraints)

    def test_pediatric_prompt_has_safety_warnings(self, service, pediatric_context):
        """T-AI-PROMPT-06: Pediatric prompts include safety constraints."""
        request = AnalysisRequest(
            context=pediatric_context,
            query_type="pediatric_assessment",
        )
        prompt = service.generate_prompt(request)

        assert (
            "pediatric" in prompt.system_prompt.lower()
            or "child" in prompt.system_prompt.lower()
        )
        assert "NEVER" in prompt.system_prompt or "never" in prompt.system_prompt


class TestContextBuilding:
    """Test clinical context building methods."""

    def test_demographics_section(self, service, sample_context):
        """T-AI-CTX-01: Demographics section is properly formatted."""
        section = service._build_demographics_section(sample_context)

        assert "Demographics" in section
        assert "55" in section
        assert "male" in section.lower()
        assert "PHENOTYPE_B" in section

    def test_labs_section(self, service, sample_context):
        """T-AI-CTX-02: Labs section groups by category."""
        section = service._build_labs_section(sample_context)

        assert "Laboratory Results" in section
        assert "Glucose Metabolism" in section
        assert "Lipid Panel" in section

    def test_conditions_section(self, service, sample_context):
        """T-AI-CTX-03: Conditions section lists all diagnoses."""
        section = service._build_conditions_section(sample_context)

        assert "Active Diagnoses" in section
        assert "E11.9" in section
        assert "Diabetes" in section
        assert "I10" in section

    def test_medications_section(self, service, sample_context):
        """T-AI-CTX-04: Medications section lists all meds."""
        section = service._build_medications_section(sample_context)

        assert "Medications" in section
        assert "Metformin" in section
        assert "Lisinopril" in section


class TestResponseValidation:
    """Test AI response validation for safety and quality."""

    def test_valid_response_passes(self, service):
        """T-AI-VAL-01: Valid clinical response passes validation."""
        response = """
        Clinical Assessment:
        Based on the provided data, this patient has obesity with metabolic complications.
        
        Recommendations:
        1. Continue current medications
        2. Consider intensifying lifestyle intervention
        3. Monitor HbA1c quarterly
        
        Safety considerations: No acute safety concerns identified.
        
        Follow-up: 3 months
        """
        validation = service.validate_clinical_response(response)

        assert validation["is_valid"] is True

    def test_certainty_phrase_fails(self, service):
        """T-AI-VAL-02: Response with dangerous certainty phrases fails."""
        response = """
        This medication is definitely safe and guaranteed to work without any side effects.
        """
        validation = service.validate_clinical_response(response)

        assert validation["is_valid"] is False
        assert len(validation["safety_flags"]) > 0

    def test_short_response_fails(self, service):
        """T-AI-VAL-03: Too-short response fails validation."""
        response = "The patient has diabetes."
        validation = service.validate_clinical_response(response)

        assert validation["is_valid"] is False
        assert any("short" in w.lower() for w in validation["warnings"])

    def test_incomplete_response_fails(self, service):
        """T-AI-VAL-04: Response missing key sections fails."""
        response = """
        The patient has high blood pressure.
        """
        validation = service.validate_clinical_response(response)

        assert validation["completeness_score"] < 0.5

    def test_guideline_citations_detected(self, service):
        """T-AI-VAL-05: Guideline citations are detected."""
        response = """
        According to ADA Standards of Care 2024, the target HbA1c should be <7%.
        The AHA/ACC guidelines recommend statin therapy for this risk level.
        """
        validation = service.validate_clinical_response(response)

        assert "ADA" in validation["guideline_citations"]
        assert "AHA" in validation["guideline_citations"]


class TestBatchPrompts:
    """Test batch prompt generation."""

    def test_batch_generates_multiple_prompts(self, service, sample_context):
        """T-AI-BATCH-01: Batch generates prompts for all contexts."""
        contexts = [sample_context, sample_context]
        prompts = service.generate_batch_prompts(contexts, "comprehensive")

        assert len(prompts) == 2
        assert all(hasattr(p, "system_prompt") for p in prompts)


class TestExpertRoles:
    """Test expert role definitions."""

    def test_obesity_expert_has_guidelines(self):
        """T-AI-EXP-01: Obesity expert references major guidelines."""
        role = MedicalExpertPrompts.OBESITY_EXPERT

        assert "ADA" in " ".join(role.guidelines)
        assert "AACE" in " ".join(role.guidelines)
        assert "ESPEN" in " ".join(role.guidelines)

    def test_pediatric_expert_includes_safety(self):
        """T-AI-EXP-02: Pediatric expert includes safety constraints."""
        role = MedicalExpertPrompts.PEDIATRIC_EXPERT

        assert "NEVER" in role.system_prompt
        assert "family" in role.system_prompt.lower()

    def test_cardio_expert_has_risk_calculators(self):
        """T-AI-EXP-03: Cardiovascular expert mentions risk calculators."""
        role = MedicalExpertPrompts.CARDIOVASCULAR_EXPERT

        assert "ASCVD" in role.system_prompt or "risk" in role.system_prompt.lower()

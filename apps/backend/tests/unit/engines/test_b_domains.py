import pytest
from src.engines.specialty.b_domains import BDomainScoresMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import DemographicsSchema, MetabolicPanelSchema
from src.models.encounter import CompletenessStatus

@pytest.fixture
def motor():
    return BDomainScoresMotor()

def _make_encounter(observations=None):
    return Encounter(
        id="test-enc",
        demographics=DemographicsSchema(age_years=45, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=observations or [],
    )

def test_b_domains_all_missing(motor):
    enc = _make_encounter()
    result = motor.compute(enc)
    domains = result.metadata["domain_scores"]
    assert len(domains) == 6
    for ds in domains:
        assert ds["completeness_status"] == CompletenessStatus.INDETERMINATE.value
        assert ds["label"] == "Unknown"

def test_b_domains_phq9_moderate(motor):
    enc = _make_encounter(observations=[Observation(code="PHQ9-SCORE", value="12")])
    result = motor.compute(enc)
    domains = result.metadata["domain_scores"]
    
    affect_domain = next(d for d in domains if d["code"] == "B_AFFECT")
    assert affect_domain["mapped_code"] == "moderate"
    assert affect_domain["completeness_status"] == CompletenessStatus.COMPLETE.value

def test_b_domains_anxiety_indeterminate(motor):
    enc = _make_encounter(observations=[Observation(code="PHQ9-SCORE", value="12")])
    result = motor.compute(enc)
    domains = result.metadata["domain_scores"]
    
    anxiety_domain = next(d for d in domains if d["code"] == "B_ANXIETY")
    assert anxiety_domain["mapped_code"] == "unknown"
    assert anxiety_domain["completeness_status"] == CompletenessStatus.INDETERMINATE.value

def test_b_domains_tfeq_emotional(motor):
    enc = _make_encounter(observations=[Observation(code="TFEQ-EMOTIONAL", value="3.1")])
    result = motor.compute(enc)
    domains = result.metadata["domain_scores"]
    
    emotional = next(d for d in domains if d["code"] == "B_EMOTIONAL")
    assert emotional["mapped_code"] == "elevated"
    assert emotional["completeness_status"] == CompletenessStatus.COMPLETE.value

def test_b_domains_all_present(motor):
    enc = _make_encounter(observations=[
        Observation(code="PHQ9-SCORE", value="1"),
        Observation(code="GAD-7", value="1"),
        Observation(code="TFEQ-UNCONTROLLED", value="1"),
        Observation(code="TFEQ-EMOTIONAL", value="1"),
        Observation(code="TFEQ-COGNITIVE", value="1"),
        Observation(code="AIS-001", value="1"),
    ])
    result = motor.compute(enc)
    domains = result.metadata["domain_scores"]
    assert len(domains) == 6
    assert all(d["completeness_status"] == CompletenessStatus.COMPLETE.value for d in domains)

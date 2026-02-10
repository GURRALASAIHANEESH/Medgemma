"""
Integration tests for AI components in the complete pipeline.
Tests end-to-end flow with JSON output validation.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from pregnancy_bridge.modules.symptom_intake import SymptomIntake
from pregnancy_bridge.modules.symptom_risk_engine import SymptomRiskEngine
from pregnancy_bridge.modules.medgemma_bridge import explain_context
from pregnancy_bridge.modules.missing_data_recommender import recommend_next_actions_with_deterministic


@pytest.fixture
def output_dir(tmp_path):
    """Create temporary output directory for test runs."""
    output_dir = tmp_path / "outputs" / "validation"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def demo_case_preeclampsia():
    """Demo case: Preeclampsia with neurological symptoms."""
    return {
        "case_id": "test_preeclampsia_001",
        "visits": [
            {
                "date": "2026-01-10",
                "gestational_age": 32,
                "weight": 68.5,
                "bp": {"systolic": 128, "diastolic": 84},
                "hemoglobin": 11.2,
                "proteinuria": "nil",
                "fundal_height": 30,
                "fetal_heart_rate": 142
            },
            {
                "date": "2026-02-04",
                "gestational_age": 36,
                "weight": 72.0,
                "bp": {"systolic": 142, "diastolic": 92},
                "hemoglobin": 10.8,
                "proteinuria": "+1",
                "fundal_height": 34,
                "fetal_heart_rate": 148
            }
        ],
        "current_symptoms": {
            "symptoms": {
                "headache": True,
                "blurred_vision": True,
                "facial_edema": False,
                "pedal_edema": True,
                "dizziness": False,
                "breathlessness": False,
                "reduced_fetal_movement": False,
                "abdominal_pain": False,
                "nausea_vomiting": False
            }
        }
    }


@pytest.fixture
def demo_case_severe_anemia():
    """Demo case: Severe anemia with breathlessness."""
    return {
        "case_id": "test_anemia_001",
        "visits": [
            {
                "date": "2026-01-15",
                "gestational_age": 28,
                "weight": 62.0,
                "bp": {"systolic": 118, "diastolic": 76},
                "hemoglobin": 9.5,
                "proteinuria": "nil",
                "fundal_height": 26,
                "fetal_heart_rate": 140
            },
            {
                "date": "2026-02-05",
                "gestational_age": 31,
                "weight": 63.5,
                "bp": {"systolic": 120, "diastolic": 78},
                "hemoglobin": 7.8,
                "proteinuria": "nil",
                "fundal_height": 29,
                "fetal_heart_rate": 145
            }
        ],
        "current_symptoms": {
            "symptoms": {
                "headache": False,
                "blurred_vision": False,
                "facial_edema": False,
                "pedal_edema": False,
                "dizziness": True,
                "breathlessness": True,
                "reduced_fetal_movement": False,
                "abdominal_pain": False,
                "nausea_vomiting": False
            }
        }
    }


@pytest.fixture
def demo_case_low_risk():
    """Demo case: Low risk, normal progression."""
    return {
        "case_id": "test_low_risk_001",
        "visits": [
            {
                "date": "2026-01-20",
                "gestational_age": 24,
                "weight": 60.0,
                "bp": {"systolic": 115, "diastolic": 72},
                "hemoglobin": 11.5,
                "proteinuria": "nil",
                "fundal_height": 23,
                "fetal_heart_rate": 142
            },
            {
                "date": "2026-02-06",
                "gestational_age": 27,
                "weight": 62.0,
                "bp": {"systolic": 118, "diastolic": 74},
                "hemoglobin": 11.3,
                "proteinuria": "nil",
                "fundal_height": 26,
                "fetal_heart_rate": 145
            }
        ],
        "current_symptoms": {
            "symptoms": {
                "headache": False,
                "blurred_vision": False,
                "facial_edema": False,
                "pedal_edema": False,
                "dizziness": False,
                "breathlessness": False,
                "reduced_fetal_movement": False,
                "abdominal_pain": False,
                "nausea_vomiting": False
            }
        }
    }


@pytest.fixture
def demo_case_severe_htn():
    """Demo case: Severe hypertension."""
    return {
        "case_id": "test_severe_htn_001",
        "visits": [
            {
                "date": "2026-01-25",
                "gestational_age": 34,
                "weight": 70.0,
                "bp": {"systolic": 138, "diastolic": 88},
                "hemoglobin": 11.0,
                "proteinuria": "nil",
                "fundal_height": 32,
                "fetal_heart_rate": 140
            },
            {
                "date": "2026-02-07",
                "gestational_age": 36,
                "weight": 72.0,
                "bp": {"systolic": 168, "diastolic": 108},
                "hemoglobin": 10.8,
                "proteinuria": "+2",
                "fundal_height": 34,
                "fetal_heart_rate": 148
            }
        ],
        "current_symptoms": {
            "symptoms": {
                "headache": True,
                "blurred_vision": False,
                "facial_edema": True,
                "pedal_edema": True,
                "dizziness": False,
                "breathlessness": False,
                "reduced_fetal_movement": False,
                "abdominal_pain": False,
                "nausea_vomiting": False
            }
        }
    }


def run_pipeline_for_case(case_data, output_dir):
    """
    Run complete pipeline for a test case.
    
    Returns:
        Dict with pipeline outputs and Path to output file
    """
    # Step 1: Process symptoms
    intake = SymptomIntake()
    is_valid, error = intake.validate_symptoms(case_data["current_symptoms"])
    assert is_valid, f"Symptom validation failed: {error}"
    
    symptom_record = intake.capture_symptoms(
        case_data["current_symptoms"],
        visit_id=f"V{len(case_data['visits']):03d}"
    )
    
    # Attach symptoms to latest visit
    case_data["visits"][-1]["symptoms"] = symptom_record
    
    # Step 2: Run risk engine
    engine = SymptomRiskEngine(log_assessments=False)
    risk_assessment = engine.evaluate_visit(case_data["visits"], symptom_record)
    
    # Step 3: Generate evidence summary
    evidence_summary = []
    for component, data in risk_assessment["component_risks"].items():
        if data["reason"]:
            evidence_summary.append(f"{component}: {data['reason']}")
    
    if risk_assessment.get("trigger_reason"):
        evidence_summary.append(risk_assessment["trigger_reason"])
    
    # Step 4: AI Context Interpreter
    explanation_result = explain_context(
        evidence_summary=evidence_summary,
        rule_reason=risk_assessment["trigger_reason"],
        risk_category=risk_assessment["risk_category"],
        symptoms=symptom_record.get("raw_symptoms", {}),
        lab_age_days=5  # Simulated
    )
    
    # Step 5: AI Recommender - USE THE CORRECT FUNCTION
    available_tests = ["CBC", "UrineDip", "BP_machine", "LFT"]
    context = {
        "lab_age_days": 5,
        "distance_to_facility_km": 5
    }
    
    latest_values = {
        "bp_systolic": case_data["visits"][-1]["bp"]["systolic"],
        "bp_diastolic": case_data["visits"][-1]["bp"]["diastolic"],
        "hemoglobin": case_data["visits"][-1].get("hemoglobin"),
        "proteinuria": case_data["visits"][-1].get("proteinuria")
    }
    
    recommendations = recommend_next_actions_with_deterministic(
        evidence_summary=evidence_summary,
        available_tests=available_tests,
        context=context,
        risk_category=risk_assessment["risk_category"],
        latest_values=latest_values
    )
    
    # Step 6: Build output JSON
    output = {
        "case_id": case_data["case_id"],
        "provenance": {
            "timestamp_utc": datetime.utcnow().isoformat() + "Z",
            "risk_authority": "rule_engine",
            "explanation_source": explanation_result["explanation_source"],
            "model_snapshot": explanation_result.get("model_snapshot"),
            "recommendation_source": recommendations[0].get("source") if recommendations else None,
            "system_version": "1.0.0",
            "pipeline": "integration_test"
        },
        "input_case": {
            "visits": case_data["visits"],
            "symptom_record": symptom_record
        },
        "rule_result": {
            "risk_category": risk_assessment["risk_category"],
            "referral_required": risk_assessment["referral_required"],
            "trigger_reason": risk_assessment["trigger_reason"],
            "trigger_visit": risk_assessment.get("trigger_visit"),
            "component_risks": risk_assessment["component_risks"]
        },
        "evidence_summary": evidence_summary,
        "ai_outputs": {
            "explanation": explanation_result,
            "recommendations": recommendations
        }
    }
    
    # Step 7: Save JSON
    output_file = output_dir / f"{case_data['case_id']}_full.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    return output, output_file


def test_preeclampsia_case_integration(demo_case_preeclampsia, output_dir):
    """Test preeclampsia case end-to-end."""
    output, output_file = run_pipeline_for_case(demo_case_preeclampsia, output_dir)
    
    # Assertions
    assert output_file.exists(), f"Output file not created: {output_file}"
    assert output["rule_result"]["risk_category"] == "HIGH"
    assert output["rule_result"]["referral_required"] is True
    assert output["provenance"]["risk_authority"] == "rule_engine"
    assert "explanation" in output["ai_outputs"]
    assert "recommendations" in output["ai_outputs"]
    assert len(output["ai_outputs"]["recommendations"]) > 0
    
    # Validate explanation structure
    explanation = output["ai_outputs"]["explanation"]
    assert "explanation_text" in explanation
    assert "explanation_qc_pass" in explanation
    assert "explanation_source" in explanation
    assert isinstance(explanation["explanation_qc_pass"], bool)
    
    print(f"\n✅ Preeclampsia case: {output['case_id']}")
    print(f"   Risk: {output['rule_result']['risk_category']}")
    print(f"   Explanation QC: {explanation['explanation_qc_pass']}")
    print(f"   Recommendations: {len(output['ai_outputs']['recommendations'])}")


def test_json_structure_valid(demo_case_preeclampsia, output_dir):
    """Test that JSON output has valid structure."""
    output, output_file = run_pipeline_for_case(demo_case_preeclampsia, output_dir)
    
    # Validate JSON can be loaded
    with open(output_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    
    assert loaded["case_id"] == demo_case_preeclampsia["case_id"]
    assert "provenance" in loaded
    assert "rule_result" in loaded
    assert "ai_outputs" in loaded
    
    print(f"\n✅ JSON structure valid for: {output['case_id']}")


def test_severe_anemia_case(demo_case_severe_anemia, output_dir):
    """Test severe anemia case end-to-end."""
    output, output_file = run_pipeline_for_case(demo_case_severe_anemia, output_dir)
    
    assert output_file.exists()
    assert output["rule_result"]["risk_category"] in ["MODERATE", "HIGH"]
    assert len(output["ai_outputs"]["recommendations"]) > 0
    
    print(f"\n✅ Severe anemia case: {output['case_id']}")
    print(f"   Risk: {output['rule_result']['risk_category']}")
    print(f"   QC: {output['ai_outputs']['explanation']['explanation_qc_pass']}")


def test_low_risk_case(demo_case_low_risk, output_dir):
    """Test low risk case end-to-end."""
    output, output_file = run_pipeline_for_case(demo_case_low_risk, output_dir)
    
    assert output_file.exists()
    assert output["rule_result"]["risk_category"] == "LOW"
    
    print(f"\n✅ Low risk case: {output['case_id']}")
    print(f"   Risk: {output['rule_result']['risk_category']}")
    print(f"   QC: {output['ai_outputs']['explanation']['explanation_qc_pass']}")


def test_severe_htn_case(demo_case_severe_htn, output_dir):
    """Test severe hypertension case end-to-end."""
    output, output_file = run_pipeline_for_case(demo_case_severe_htn, output_dir)
    
    assert output_file.exists()
    assert output["rule_result"]["risk_category"] == "HIGH"
    assert output["rule_result"]["referral_required"] is True
    
    # Should have urgent recommendations
    urgent_recs = [r for r in output["ai_outputs"]["recommendations"] if r["priority"] == "urgent"]
    assert len(urgent_recs) > 0
    
    print(f"\n✅ Severe HTN case: {output['case_id']}")
    print(f"   Risk: {output['rule_result']['risk_category']}")
    print(f"   Urgent recommendations: {len(urgent_recs)}")
    print(f"   QC: {output['ai_outputs']['explanation']['explanation_qc_pass']}")

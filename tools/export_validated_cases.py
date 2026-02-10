"""
Export validated integration test cases to JSON files.
"""

import json
from pathlib import Path


def get_validated_cases():
    """Return the 5 validated test cases."""
    cases = []
    
    # Case 1: Preeclampsia
    cases.append({
        "case_id": "case_001",
        "type": "preeclampsia_validated",
        "seed": 9001,
        "patient": {"age": 28, "gravida": 2, "para": 1},
        "visits": [
            {
                "visit_id": "v1",
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
                "visit_id": "v2",
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
        },
        "missing_labs": False,
        "language": "en",
        "expected_keywords_for_QC": [
            "proteinuria: +1",
            "BP: 142/92",
            "blurred_vision",
            "headache"
        ],
        "notes": "Validated integration test case - preeclampsia"
    })
    
    # Case 2: Severe Anemia
    cases.append({
        "case_id": "case_002",
        "type": "severe_anemia_validated",
        "seed": 9002,
        "patient": {"age": 25, "gravida": 1, "para": 0},
        "visits": [
            {
                "visit_id": "v1",
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
                "visit_id": "v2",
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
        },
        "missing_labs": False,
        "language": "en",
        "expected_keywords_for_QC": [
            "hemoglobin: 7.8",
            "Hb 7.8",
            "breathlessness",
            "anemia"
        ],
        "notes": "Validated integration test case - severe anemia"
    })
    
    # Case 3: Low Risk
    cases.append({
        "case_id": "case_003",
        "type": "low_risk_validated",
        "seed": 9003,
        "patient": {"age": 26, "gravida": 1, "para": 0},
        "visits": [
            {
                "visit_id": "v1",
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
                "visit_id": "v2",
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
        },
        "missing_labs": False,
        "language": "en",
        "expected_keywords_for_QC": [
            "hemoglobin: 11.3",
            "proteinuria: nil",
            "normal"
        ],
        "notes": "Validated integration test case - low risk"
    })
    
    # Case 4: Severe HTN
    cases.append({
        "case_id": "case_004",
        "type": "severe_htn_validated",
        "seed": 9004,
        "patient": {"age": 32, "gravida": 3, "para": 2},
        "visits": [
            {
                "visit_id": "v1",
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
                "visit_id": "v2",
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
        },
        "missing_labs": False,
        "language": "en",
        "expected_keywords_for_QC": [
            "BP: 168/108",
            "proteinuria: +2",
            "severe hypertension",
            "headache"
        ],
        "notes": "Validated integration test case - severe hypertension"
    })
    
    # Case 5: Moderate Risk (for diversity)
    cases.append({
        "case_id": "case_005",
        "type": "moderate_risk_validated",
        "seed": 9005,
        "patient": {"age": 29, "gravida": 2, "para": 1},
        "visits": [
            {
                "visit_id": "v1",
                "date": "2026-01-18",
                "gestational_age": 26,
                "weight": 64.0,
                "bp": {"systolic": 125, "diastolic": 80},
                "hemoglobin": 10.5,
                "proteinuria": "trace",
                "fundal_height": 24,
                "fetal_heart_rate": 142
            },
            {
                "visit_id": "v2",
                "date": "2026-02-03",
                "gestational_age": 29,
                "weight": 66.0,
                "bp": {"systolic": 138, "diastolic": 88},
                "hemoglobin": 10.2,
                "proteinuria": "+1",
                "fundal_height": 27,
                "fetal_heart_rate": 144
            }
        ],
        "current_symptoms": {
            "symptoms": {
                "headache": False,
                "blurred_vision": False,
                "facial_edema": False,
                "pedal_edema": True,
                "dizziness": False,
                "breathlessness": False,
                "reduced_fetal_movement": False,
                "abdominal_pain": False,
                "nausea_vomiting": False
            }
        },
        "missing_labs": False,
        "language": "en",
        "expected_keywords_for_QC": [
            "BP: 138/88",
            "proteinuria: +1",
            "hemoglobin: 10.2"
        ],
        "notes": "Validated integration test case - moderate risk"
    })
    
    return cases


def main():
    """Export validated cases to JSON files."""
    output_dir = Path("tests/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("Exporting Validated Test Cases")
    print("=" * 80)
    
    cases = get_validated_cases()
    
    for case in cases:
        output_file = output_dir / f"{case['case_id']}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(case, f, indent=2, ensure_ascii=False)
        print(f"✓ Exported {case['case_id']}: {case['type']}")
    
    print(f"\n✓ Exported {len(cases)} validated cases to {output_dir}")
    print("\nNext: Run synthetic case generator for case_006 onwards")


if __name__ == "__main__":
    main()

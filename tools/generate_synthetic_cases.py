"""
Synthetic Test Case Generator for PregnancyBridge
Generates realistic maternal health cases with controlled variation.
"""

import json
import random
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import csv


def set_seed(seed: int):
    """Set random seed for reproducibility."""
    random.seed(seed)


def generate_hellp_preeclampsia_case(case_id: str, seed: int) -> Dict[str, Any]:
    """Generate HELLP/evolving preeclampsia case."""
    random.seed(seed)
    
    base_date = datetime(2025, 10, 1) + timedelta(days=random.randint(0, 60))
    
    # Progressive deterioration
    visit1 = {
        "visit_id": "v1",
        "date": base_date.strftime("%Y-%m-%d"),
        "gestational_age": 28 + random.randint(0, 4),
        "weight": 62.0 + random.uniform(0, 8),
        "bp": {"systolic": 125 + random.randint(0, 10), "diastolic": 80 + random.randint(0, 5)},
        "hemoglobin": 10.5 + random.uniform(0, 1.5),
        "proteinuria": random.choice(["nil", "trace"]),
        "platelets_k_ul": 180 + random.randint(0, 50),
        "fundal_height": 26 + random.randint(0, 2),
        "fetal_heart_rate": 140 + random.randint(-5, 5)
    }
    
    visit2 = {
        "visit_id": "v2",
        "date": (base_date + timedelta(days=14 + random.randint(0, 7))).strftime("%Y-%m-%d"),
        "gestational_age": visit1["gestational_age"] + 2,
        "weight": visit1["weight"] + random.uniform(0.5, 2),
        "bp": {"systolic": 140 + random.randint(0, 10), "diastolic": 90 + random.randint(0, 5)},
        "hemoglobin": visit1["hemoglobin"] - random.uniform(0.2, 0.8),
        "proteinuria": random.choice(["+1", "+2"]),
        "platelets_k_ul": visit1["platelets_k_ul"] - random.randint(30, 80),
        "fundal_height": visit1["fundal_height"] + 2,
        "fetal_heart_rate": 142 + random.randint(-5, 5)
    }
    
    symptoms = {
        "symptoms": {
            "headache": random.choice([True, False]),
            "blurred_vision": random.choice([True, False]),
            "facial_edema": True,
            "pedal_edema": True,
            "dizziness": False,
            "breathlessness": False,
            "reduced_fetal_movement": False,
            "abdominal_pain": random.choice([True, False]),
            "nausea_vomiting": False
        }
    }
    
    expected_keywords = [
        f"proteinuria: {visit2['proteinuria']}",
        f"platelets: {visit2['platelets_k_ul']}",
        f"BP: {visit2['bp']['systolic']}/{visit2['bp']['diastolic']}"
    ]
    
    return {
        "case_id": case_id,
        "type": "hellp_preeclampsia",
        "seed": seed,
        "patient": {"age": 24 + random.randint(0, 15), "gravida": random.randint(1, 3), "para": random.randint(0, 2)},
        "visits": [visit1, visit2],
        "current_symptoms": symptoms,
        "missing_labs": False,
        "language": "en",
        "expected_keywords_for_QC": expected_keywords,
        "notes": f"generator: v1.2, seed={seed}"
    }


def generate_platelet_decline_case(case_id: str, seed: int, missing_latest: bool = False) -> Dict[str, Any]:
    """Generate platelet decline case."""
    random.seed(seed)
    
    base_date = datetime(2025, 9, 15) + timedelta(days=random.randint(0, 60))
    
    visit1 = {
        "visit_id": "v1",
        "date": base_date.strftime("%Y-%m-%d"),
        "gestational_age": 30 + random.randint(0, 4),
        "weight": 65.0 + random.uniform(0, 8),
        "bp": {"systolic": 120 + random.randint(0, 15), "diastolic": 78 + random.randint(0, 8)},
        "hemoglobin": 10.8 + random.uniform(0, 1.0),
        "proteinuria": random.choice(["nil", "trace", "+1"]),
        "platelets_k_ul": 170 + random.randint(0, 40),
        "fundal_height": 28 + random.randint(0, 2),
        "fetal_heart_rate": 142 + random.randint(-5, 5)
    }
    
    visit2_platelet = visit1["platelets_k_ul"] - random.randint(50, 90) if not missing_latest else None
    
    visit2 = {
        "visit_id": "v2",
        "date": (base_date + timedelta(days=14 + random.randint(0, 7))).strftime("%Y-%m-%d"),
        "gestational_age": visit1["gestational_age"] + 2,
        "weight": visit1["weight"] + random.uniform(0.5, 2),
        "bp": {"systolic": 132 + random.randint(0, 15), "diastolic": 84 + random.randint(0, 8)},
        "hemoglobin": visit1["hemoglobin"] - random.uniform(0.1, 0.5),
        "proteinuria": random.choice(["+1", "+2"]),
        "fundal_height": visit1["fundal_height"] + 2,
        "fetal_heart_rate": 144 + random.randint(-5, 5)
    }
    
    if visit2_platelet is not None:
        visit2["platelets_k_ul"] = visit2_platelet
    
    symptoms = {
        "symptoms": {
            "headache": random.choice([True, False]),
            "blurred_vision": False,
            "facial_edema": False,
            "pedal_edema": random.choice([True, False]),
            "dizziness": False,
            "breathlessness": False,
            "reduced_fetal_movement": False,
            "abdominal_pain": random.choice([True, False]),
            "nausea_vomiting": False
        }
    }
    
    expected_keywords = [
        f"platelets: {visit1['platelets_k_ul']}" if missing_latest else f"platelets: {visit2_platelet}",
        f"proteinuria: {visit2['proteinuria']}"
    ]
    
    return {
        "case_id": case_id,
        "type": "platelet_decline",
        "seed": seed,
        "patient": {"age": 26 + random.randint(0, 12), "gravida": random.randint(1, 4), "para": random.randint(0, 3)},
        "visits": [visit1, visit2],
        "current_symptoms": symptoms,
        "missing_labs": missing_latest,
        "language": "en",
        "expected_keywords_for_QC": expected_keywords,
        "notes": f"generator: v1.2, seed={seed}, missing_latest={missing_latest}"
    }


def generate_anemia_case(case_id: str, seed: int, severity: str = "moderate") -> Dict[str, Any]:
    """Generate anemia progression case."""
    random.seed(seed)
    
    base_date = datetime(2025, 10, 10) + timedelta(days=random.randint(0, 60))
    
    hb_start = 9.5 + random.uniform(0, 1.5) if severity == "moderate" else 7.5 + random.uniform(0, 1.0)
    hb_end = hb_start - random.uniform(0.5, 1.5)
    
    visit1 = {
        "visit_id": "v1",
        "date": base_date.strftime("%Y-%m-%d"),
        "gestational_age": 26 + random.randint(0, 6),
        "weight": 60.0 + random.uniform(0, 8),
        "bp": {"systolic": 115 + random.randint(0, 10), "diastolic": 72 + random.randint(0, 8)},
        "hemoglobin": hb_start,
        "proteinuria": "nil",
        "fundal_height": 24 + random.randint(0, 2),
        "fetal_heart_rate": 140 + random.randint(-5, 5)
    }
    
    visit2 = {
        "visit_id": "v2",
        "date": (base_date + timedelta(days=21 + random.randint(0, 7))).strftime("%Y-%m-%d"),
        "gestational_age": visit1["gestational_age"] + 3,
        "weight": visit1["weight"] + random.uniform(0.5, 2),
        "bp": {"systolic": 118 + random.randint(0, 10), "diastolic": 74 + random.randint(0, 8)},
        "hemoglobin": hb_end,
        "proteinuria": "nil",
        "fundal_height": visit1["fundal_height"] + 3,
        "fetal_heart_rate": 142 + random.randint(-5, 5)
    }
    
    symptoms = {
        "symptoms": {
            "headache": False,
            "blurred_vision": False,
            "facial_edema": False,
            "pedal_edema": random.choice([True, False]),
            "dizziness": True if severity == "severe" else random.choice([True, False]),
            "breathlessness": True if severity == "severe" else random.choice([True, False]),
            "reduced_fetal_movement": False,
            "abdominal_pain": False,
            "nausea_vomiting": False
        }
    }
    
    expected_keywords = [
        f"hemoglobin: {hb_end:.1f}",
        f"Hb {hb_end:.1f}"
    ]
    
    return {
        "case_id": case_id,
        "type": f"anemia_{severity}",
        "seed": seed,
        "patient": {"age": 22 + random.randint(0, 15), "gravida": random.randint(1, 3), "para": random.randint(0, 2)},
        "visits": [visit1, visit2],
        "current_symptoms": symptoms,
        "missing_labs": False,
        "language": "en",
        "expected_keywords_for_QC": expected_keywords,
        "notes": f"generator: v1.2, seed={seed}, severity={severity}"
    }


def generate_severe_htn_case(case_id: str, seed: int) -> Dict[str, Any]:
    """Generate severe hypertension case."""
    random.seed(seed)
    
    base_date = datetime(2025, 11, 1) + timedelta(days=random.randint(0, 60))
    
    visit1 = {
        "visit_id": "v1",
        "date": base_date.strftime("%Y-%m-%d"),
        "gestational_age": 32 + random.randint(0, 4),
        "weight": 68.0 + random.uniform(0, 8),
        "bp": {"systolic": 130 + random.randint(0, 10), "diastolic": 85 + random.randint(0, 5)},
        "hemoglobin": 10.5 + random.uniform(0, 1.0),
        "proteinuria": random.choice(["nil", "trace"]),
        "fundal_height": 30 + random.randint(0, 2),
        "fetal_heart_rate": 140 + random.randint(-5, 5)
    }
    
    visit2 = {
        "visit_id": "v2",
        "date": (base_date + timedelta(days=7 + random.randint(0, 7))).strftime("%Y-%m-%d"),
        "gestational_age": visit1["gestational_age"] + 1,
        "weight": visit1["weight"] + random.uniform(0.5, 2),
        "bp": {"systolic": 165 + random.randint(0, 10), "diastolic": 110 + random.randint(0, 5)},
        "hemoglobin": visit1["hemoglobin"] - random.uniform(0.1, 0.3),
        "proteinuria": random.choice(["+1", "+2", "+3"]),
        "fundal_height": visit1["fundal_height"] + 1,
        "fetal_heart_rate": 142 + random.randint(-5, 5)
    }
    
    symptoms = {
        "symptoms": {
            "headache": True,
            "blurred_vision": random.choice([True, False]),
            "facial_edema": True,
            "pedal_edema": True,
            "dizziness": random.choice([True, False]),
            "breathlessness": False,
            "reduced_fetal_movement": False,
            "abdominal_pain": False,
            "nausea_vomiting": False
        }
    }
    
    expected_keywords = [
        f"BP: {visit2['bp']['systolic']}/{visit2['bp']['diastolic']}",
        f"proteinuria: {visit2['proteinuria']}"
    ]
    
    return {
        "case_id": case_id,
        "type": "severe_htn",
        "seed": seed,
        "patient": {"age": 28 + random.randint(0, 12), "gravida": random.randint(1, 4), "para": random.randint(0, 3)},
        "visits": [visit1, visit2],
        "current_symptoms": symptoms,
        "missing_labs": False,
        "language": "en",
        "expected_keywords_for_QC": expected_keywords,
        "notes": f"generator: v1.2, seed={seed}"
    }


def generate_low_risk_case(case_id: str, seed: int) -> Dict[str, Any]:
    """Generate low-risk normal case."""
    random.seed(seed)
    
    base_date = datetime(2025, 10, 20) + timedelta(days=random.randint(0, 60))
    
    visit1 = {
        "visit_id": "v1",
        "date": base_date.strftime("%Y-%m-%d"),
        "gestational_age": 20 + random.randint(0, 8),
        "weight": 58.0 + random.uniform(0, 8),
        "bp": {"systolic": 110 + random.randint(0, 10), "diastolic": 70 + random.randint(0, 8)},
        "hemoglobin": 11.0 + random.uniform(0, 1.5),
        "proteinuria": "nil",
        "fundal_height": 18 + random.randint(0, 2),
        "fetal_heart_rate": 140 + random.randint(-5, 5)
    }
    
    visit2 = {
        "visit_id": "v2",
        "date": (base_date + timedelta(days=28 + random.randint(0, 7))).strftime("%Y-%m-%d"),
        "gestational_age": visit1["gestational_age"] + 4,
        "weight": visit1["weight"] + random.uniform(1, 3),
        "bp": {"systolic": 115 + random.randint(0, 8), "diastolic": 72 + random.randint(0, 6)},
        "hemoglobin": visit1["hemoglobin"] - random.uniform(0, 0.5),
        "proteinuria": "nil",
        "fundal_height": visit1["fundal_height"] + 4,
        "fetal_heart_rate": 142 + random.randint(-5, 5)
    }
    
    symptoms = {
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
    
    expected_keywords = [
        f"hemoglobin: {visit2['hemoglobin']:.1f}",
        "proteinuria: nil"
    ]
    
    return {
        "case_id": case_id,
        "type": "low_risk",
        "seed": seed,
        "patient": {"age": 24 + random.randint(0, 10), "gravida": random.randint(1, 2), "para": random.randint(0, 1)},
        "visits": [visit1, visit2],
        "current_symptoms": symptoms,
        "missing_labs": False,
        "language": "en",
        "expected_keywords_for_QC": expected_keywords,
        "notes": f"generator: v1.2, seed={seed}"
    }


def generate_edge_case(case_id: str, seed: int, edge_type: str) -> Dict[str, Any]:
    """Generate edge/noisy case."""
    random.seed(seed)
    
    # Start with a base case
    if edge_type == "ocr_noise":
        case = generate_platelet_decline_case(case_id, seed)
        case["visits"][1]["notes"] = "Platlt: 95 x10^3/uL (OCR noise)"
        case["type"] = "edge_ocr_noise"
    elif edge_type == "bilingual":
        case = generate_hellp_preeclampsia_case(case_id, seed)
        case["visits"][1]["notes"] = "सिरदर्द और धुंधली दृष्टि (headache and blurred vision)"
        case["language"] = "hi"
        case["type"] = "edge_bilingual"
    else:
        case = generate_anemia_case(case_id, seed, "moderate")
        case["visits"][1]["notes"] = "Late visit - patient delayed due to transport"
        case["type"] = "edge_late_visit"
    
    return case


def main():
    """Main generator function."""
    parser = argparse.ArgumentParser(description="Generate synthetic test cases")
    parser.add_argument("--seed", type=int, default=1234, help="Base random seed")
    parser.add_argument("--n", type=int, default=45, help="Number of cases to generate")
    parser.add_argument("--out", type=str, required=True, help="Output directory")
    args = parser.parse_args()
    
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {args.n} synthetic cases...")
    print(f"Output directory: {output_dir}")
    print(f"Base seed: {args.seed}")
    
    cases = []
    manifest_rows = []
    
    case_num = 6  # Start from case_006 (001-005 are validated cases)
    
    # Distribution
    distributions = [
        ("hellp_preeclampsia", 10),
        ("platelet_decline", 5),
        ("platelet_decline_missing", 3),
        ("anemia_moderate", 5),
        ("anemia_severe", 3),
        ("severe_htn", 6),
        ("low_risk", 6),
        ("edge_ocr_noise", 2),
        ("edge_bilingual", 2),
        ("edge_late_visit", 3)
    ]
    
    for case_type, count in distributions:
        for i in range(count):
            case_id = f"case_{case_num:03d}"
            seed = args.seed + case_num
            
            if case_type == "hellp_preeclampsia":
                case = generate_hellp_preeclampsia_case(case_id, seed)
            elif case_type == "platelet_decline":
                case = generate_platelet_decline_case(case_id, seed, missing_latest=False)
            elif case_type == "platelet_decline_missing":
                case = generate_platelet_decline_case(case_id, seed, missing_latest=True)
            elif case_type == "anemia_moderate":
                case = generate_anemia_case(case_id, seed, "moderate")
            elif case_type == "anemia_severe":
                case = generate_anemia_case(case_id, seed, "severe")
            elif case_type == "severe_htn":
                case = generate_severe_htn_case(case_id, seed)
            elif case_type == "low_risk":
                case = generate_low_risk_case(case_id, seed)
            elif case_type.startswith("edge_"):
                edge_type = case_type.replace("edge_", "")
                case = generate_edge_case(case_id, seed, edge_type)
            
            # Save case
            output_file = output_dir / f"{case_id}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(case, f, indent=2, ensure_ascii=False)
            
            cases.append(case)
            manifest_rows.append({
                "case_id": case_id,
                "type": case["type"],
                "seed": seed,
                "notes": case["notes"]
            })
            
            print(f"  ✓ Generated {case_id}: {case['type']}")
            case_num += 1
    
    # Write manifest
    manifest_file = output_dir / "manifest.csv"
    with open(manifest_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "type", "seed", "notes"])
        writer.writeheader()
        writer.writerows(manifest_rows)
    
    print(f"\n✓ Generated {len(cases)} cases")
    print(f"✓ Manifest saved to {manifest_file}")
    print(f"\nNext: Copy validated cases (case_001-case_005.json) to {output_dir}")


if __name__ == "__main__":
    main()

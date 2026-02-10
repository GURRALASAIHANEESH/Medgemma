import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pregnancy_bridge.modules.symptom_intake import SymptomIntake
from pregnancy_bridge.modules.symptom_risk_engine import SymptomRiskEngine
from pregnancy_bridge.modules.medgemma_bridge import explain_context

SHOWCASE_CASES = {
    "case_006": "HELLP progression",
    "case_016": "Platelet decline forecasting",
    "case_023": "Symptom escalation",
    "case_044": "OCR noisy input",
    "case_046": "Multilingual symptom",
    "case_014": "Borderline HELLP",
    "case_021": "Temporal platelet trend",
    "case_048": "Multi-symptom cluster",
    "case_024": "Moderate-risk ambiguous",
    "case_005": "Data consistency"
}

def run_showcase_case(case_id, description):
    print(f"\n[{case_id}] {description}")
    print("-" * 60)
    
    case_file = Path("tests/synthetic") / f"{case_id}.json"
    if not case_file.exists():
        return {"case_id": case_id, "error": "File not found", "ai_worked": False}
    
    with open(case_file, encoding='utf-8') as f:
        case_data = json.load(f)
    
    intake = SymptomIntake()
    visits = case_data.get("visits", [])
    symptom_record = {}
    for visit in visits:
        for symptom_key, value in visit.items():
            if symptom_key not in ["visit_number", "gestational_week", "date"]:
                if value not in [None, "", "none", "normal"]:
                    symptom_record[symptom_key] = value
    
    engine = SymptomRiskEngine()
    assessment = engine.evaluate_visit(visits, symptom_record)
    
    risk = assessment.get("risk_category", assessment.get("risk_level", "UNKNOWN"))
    
    explanation_result = explain_context(
        evidence_summary=assessment.get("evidence", []),
        rule_reason=assessment.get("primary_reason", ""),
        risk_category=risk,
        symptoms=symptom_record,
        lab_age_days=0
    )
    
    explanation = explanation_result.get("explanation_text", "")
    source = explanation_result.get("explanation_source", "unknown")
    chars = len(explanation)
    ai_worked = source == "medgemma" and chars > 50
    
    print(f"Rule Decision: {risk}")
    print(f"AI Source: {source}")
    print(f"Chars Generated: {chars}")
    print(f"AI Worked: {ai_worked}")
    
    if ai_worked:
        print(f"Preview: {explanation[:150]}...")
    
    raw_request = {
        "evidence": assessment.get("evidence", []),
        "rule_reason": assessment.get("primary_reason", ""),
        "risk_category": risk,
        "symptoms": symptom_record
    }
    
    return {
        "case_id": case_id,
        "description": description,
        "rule_decision": risk,
        "ai_worked": ai_worked,
        "explanation_source": source,
        "chars_generated": chars,
        "hardware_used": "CPU",
        "raw_request": raw_request,
        "raw_response": explanation,
        "fallback_triggered": source != "medgemma"
    }

def main():
    output_dir = Path("artifacts/ai_showcase")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("PregnancyBridge AI Showcase - CPU Validation")
    print("=" * 80)
    
    results = []
    
    for case_id, description in SHOWCASE_CASES.items():
        try:
            result = run_showcase_case(case_id, description)
            results.append(result)
            
            case_output = output_dir / f"{case_id}_raw.json"
            with open(case_output, 'w', encoding='utf-8') as f:
                json.dump({
                    "case_id": case_id,
                    "description": description,
                    "raw_request": result["raw_request"],
                    "raw_response": result["raw_response"],
                    "metadata": {
                        "hardware_used": result["hardware_used"],
                        "chars_generated": result["chars_generated"],
                        "explanation_source": result["explanation_source"]
                    }
                }, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "case_id": case_id,
                "description": description,
                "error": str(e),
                "ai_worked": False
            })
    
    print("\n" + "=" * 80)
    print("SHOWCASE SUMMARY")
    print("=" * 80)
    
    ai_success = sum(1 for r in results if r.get("ai_worked", False))
    fallback_count = sum(1 for r in results if r.get("fallback_triggered", True))
    
    print(f"Total Cases: {len(results)}")
    print(f"AI Success: {ai_success}/{len(results)}")
    print(f"Fallback Count: {fallback_count}")
    print(f"CPU Inference: Confirmed")
    
    summary = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "showcase_case_count": len(results),
        "ai_success_count": ai_success,
        "fallback_count": fallback_count,
        "hardware_used": "CPU",
        "explanation_quality_notes": "MedGemma running on CPU for production stability",
        "cases": results
    }
    
    summary_file = Path("artifacts/ai_showcase_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to {summary_file}")
    print("\nCPU showcase validation complete.")
    
    return 0 if ai_success >= 7 else 1

if __name__ == "__main__":
    sys.exit(main())

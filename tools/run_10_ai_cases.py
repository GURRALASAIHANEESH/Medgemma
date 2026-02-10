import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pregnancy_bridge.modules.symptom_intake import SymptomIntake
from pregnancy_bridge.modules.symptom_risk_engine import SymptomRiskEngine
from pregnancy_bridge.modules.medgemma_bridge import explain_context

SELECTED_CASES = [
    "case_001", "case_006", "case_016", "case_024", "case_029",
    "case_032", "case_038", "case_044", "case_046", "case_048"
]

def run_case(case_file):
    print(f"\nProcessing {case_file.stem}...")
    
    with open(case_file) as f:
        case_data = json.load(f)
    
    intake = SymptomIntake()
    symptom_record = intake.extract_symptoms_from_case(case_data)
    
    engine = SymptomRiskEngine()
    assessment = engine.evaluate_visit(case_data.get("visits", []), symptom_record)
    
    explanation_result = explain_context(
        evidence=assessment.get("evidence", []),
        rule_reason=assessment.get("primary_reason", ""),
        risk_level=assessment["risk_level"],
        symptoms=symptom_record
    )
    
    explanation_source = explanation_result.get("explanation_source", "unknown")
    chars_generated = len(explanation_result.get("explanation", ""))
    ai_worked = explanation_source == "medgemma" and chars_generated > 50
    
    print(f"  Rule: {assessment['risk_level']}")
    print(f"  Source: {explanation_source}")
    print(f"  Chars: {chars_generated}")
    print(f"  Hardware: {explanation_result.get('hardware_used', 'unknown')}")
    print(f"  AI worked: {ai_worked}")
    
    return {
        "case_id": case_file.stem,
        "rule_decision": assessment["risk_level"],
        "ai_worked": ai_worked,
        "explanation_source": explanation_source,
        "chars_generated": chars_generated,
        "hardware_used": explanation_result.get("hardware_used", "unknown"),
        "inference_time_ms": explanation_result.get("inference_time_ms", 0)
    }

def main():
    cases_dir = Path("tests/synthetic")
    results = []
    
    print("=" * 80)
    print("Running 10 AI-validated cases with GPU")
    print("=" * 80)
    
    for case_id in SELECTED_CASES:
        case_file = cases_dir / f"{case_id}.json"
        if not case_file.exists():
            print(f"WARNING: {case_file} not found")
            continue
        
        try:
            result = run_case(case_file)
            results.append(result)
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"case_id": case_id, "error": str(e), "ai_worked": False})
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    ai_success = sum(1 for r in results if r.get("ai_worked", False))
    print(f"\nAI Success: {ai_success}/10")
    print(f"GPU Used: {sum(1 for r in results if r.get('hardware_used') == 'CUDA')}/10")
    
    output_file = Path("artifacts/10_ai_case_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_cases": len(results),
            "ai_success_count": ai_success,
            "results": results
        }, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    
    if ai_success >= 8:
        print("\nSTATUS: SUCCESS - Proceed with hybrid submission")
        return 0
    else:
        print("\nSTATUS: FAIL - Fall back to Option 1")
        return 1

if __name__ == "__main__":
    sys.exit(main())

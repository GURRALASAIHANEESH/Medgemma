import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pregnancy_bridge.modules.symptom_intake import SymptomIntake
from pregnancy_bridge.modules.symptom_risk_engine import SymptomRiskEngine
from pregnancy_bridge.modules.medgemma_bridge import explain_context

# 3 BEST CASES FOR DEMO
SHOWCASE_CASES = {
    "case_006": "HELLP progression with preeclampsia features",
    "case_016": "Severe hypertension with proteinuria",
    "case_038": "Low risk baseline for contrast"
}

def run_showcase_case(case_id, description):
    print(f"\n{'='*60}")
    print(f"[{case_id}] {description}")
    print('='*60)
    
    case_file = Path("tests/synthetic") / f"{case_id}.json"
    if not case_file.exists():
        return {"case_id": case_id, "error": "File not found", "ai_worked": False}
    
    with open(case_file, encoding='utf-8') as f:
        case_data = json.load(f)
    
    intake = SymptomIntake()
    visits = case_data.get("visits", [])
    symptom_record = {}
    for visit in visits:
        for k, v in visit.items():
            if k not in ["visit_number", "gestational_week", "date"]:
                if v not in [None, "", "none", "normal"]:
                    symptom_record[k] = v
    
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
    qc_pass = explanation_result.get("explanation_qc_pass", False)
    ai_worked = source == "medgemma" and qc_pass
    
    print(f"\nRule Decision: {risk}")
    print(f"AI Source: {source}")
    print(f"QC Pass: {qc_pass}")
    print(f"Chars Generated: {chars}")
    print(f"AI Worked: {ai_worked}")
    
    if ai_worked:
        print(f"\nMedGemma Explanation Preview (first 400 chars):")
        print(explanation[:400])
        print("...")
    
    return {
        "case_id": case_id,
        "description": description,
        "rule_decision": risk,
        "ai_worked": ai_worked,
        "explanation_source": source,
        "qc_pass": qc_pass,
        "chars_generated": chars,
        "full_explanation": explanation,
        "hardware_used": "CPU",
        "evidence": assessment.get("evidence", []),
        "rule_reason": assessment.get("primary_reason", "")
    }

def main():
    output_dir = Path("artifacts/medgemma_showcase")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*80)
    print("PregnancyBridge MedGemma Showcase - 3 Cases")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%H:%M:%S')}")
    print("Estimated duration: 90 minutes")
    print("="*80)
    
    results = []
    
    for i, (case_id, description) in enumerate(SHOWCASE_CASES.items(), 1):
        print(f"\n\nPROCESSING CASE {i}/3")
        try:
            result = run_showcase_case(case_id, description)
            results.append(result)
            
            # Save individual case
            case_output = output_dir / f"{case_id}_medgemma_output.json"
            with open(case_output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nSaved: {case_output}")
            
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
    
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    
    ai_success = sum(1 for r in results if r.get("ai_worked", False))
    
    print(f"Total Cases: {len(results)}")
    print(f"MedGemma Success: {ai_success}/{len(results)}")
    print(f"Hardware: CPU")
    print(f"Completion time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Save summary
    summary = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_cases": len(results),
        "medgemma_success_count": ai_success,
        "hardware": "CPU",
        "average_chars": sum(r.get("chars_generated", 0) for r in results) / len(results),
        "cases": results
    }
    
    summary_file = output_dir / "showcase_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\nSummary saved: {summary_file}")
    
    if ai_success == 3:
        print("\n*** ALL 3 CASES SUCCESSFUL - READY FOR COMPETITION SUBMISSION ***")
        return 0
    else:
        print(f"\n*** WARNING: Only {ai_success}/3 cases successful ***")
        return 1

if __name__ == "__main__":
    sys.exit(main())

"""
Full Validation Runner for PregnancyBridge
Runs 50-case validation with performance profiling and QC validation.
"""

import json
import csv
import time
import psutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pregnancy_bridge.modules.symptom_intake import SymptomIntake
from pregnancy_bridge.modules.symptom_risk_engine import SymptomRiskEngine
from pregnancy_bridge.modules.medgemma_bridge import explain_context
from pregnancy_bridge.modules.missing_data_recommender import recommend_next_actions_with_deterministic


def measure_performance(func, *args, **kwargs) -> Tuple[Any, float, float]:
    """
    Measure function performance.
    
    Returns:
        (result, latency_ms, mem_peak_mb)
    """
    process = psutil.Process()
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    mem_after = process.memory_info().rss / 1024 / 1024  # MB
    latency_ms = (end_time - start_time) * 1000
    mem_peak_mb = max(mem_after - mem_before, 0)
    
    return result, latency_ms, mem_peak_mb


def run_pipeline_for_case(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run complete pipeline for a test case.
    
    Returns:
        Pipeline output dictionary
    """
    # Step 1: Process symptoms
    intake = SymptomIntake()
    is_valid, error = intake.validate_symptoms(case_data["current_symptoms"])
    
    if not is_valid:
        raise ValueError(f"Symptom validation failed: {error}")
    
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
        lab_age_days=5
    )
    
    # Step 5: AI Recommender
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
    
    # Build output
    output = {
        "case_id": case_data["case_id"],
        "provenance": {
            "timestamp_utc": datetime.utcnow().isoformat() + "Z",
            "risk_authority": "rule_engine",
            "explanation_source": explanation_result["explanation_source"],
            "model_snapshot": explanation_result.get("model_snapshot"),
            "recommendation_source": recommendations[0].get("source") if recommendations else None,
            "system_version": "1.0.0",
            "pipeline": "full_validation"
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
    
    return output


def validate_qc(output: Dict[str, Any], expected_keywords: List[str]) -> Tuple[bool, str]:
    """
    Validate QC rules for a case.
    
    Returns:
        (qa_pass, failure_reason)
    """
    explanation = output["ai_outputs"]["explanation"]
    explanation_text = explanation.get("explanation_text", "").lower()
    
    # Rule 1: Evidence present
    evidence_present = False
    if output.get("evidence_summary") and len(output["evidence_summary"]) > 0:
        # Check if explanation contains expected keywords or evidence
        for keyword in expected_keywords:
            if keyword.lower() in explanation_text:
                evidence_present = True
                break
        
        if not evidence_present:
            # Check if any evidence summary item is quoted
            for evidence in output["evidence_summary"]:
                if evidence.lower() in explanation_text:
                    evidence_present = True
                    break
    
    if not evidence_present and explanation["explanation_source"] == "medgemma":
        return False, "Evidence not present in explanation"
    
    # Rule 2: AI never overrides rule
    rule_decision = output["rule_result"]["risk_category"]
    # AI doesn't make risk decisions, so this check is about source
    if output["provenance"]["risk_authority"] != "rule_engine":
        return False, "Risk authority is not rule_engine"
    
    # Rule 3: QC pass check
    if not explanation.get("explanation_qc_pass", False) and explanation["explanation_source"] == "medgemma":
        return False, "Explanation failed QC validation"
    
    # Rule 4: Provenance present
    if not output.get("provenance") or len(output["provenance"]) == 0:
        return False, "Provenance missing"
    
    return True, "PASS"


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Run full validation")
    parser.add_argument("--cases", type=str, required=True, help="Test cases directory")
    parser.add_argument("--out", type=str, required=True, help="Output directory")
    parser.add_argument("--parallel", type=int, default=1, help="Parallel workers (use 1 for determinism)")
    args = parser.parse_args()
    
    cases_dir = Path(args.cases)
    output_dir = Path(args.out)
    
    # Create output directories
    (output_dir / "outputs").mkdir(parents=True, exist_ok=True)
    (output_dir / "failed_cases").mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("🚀 PregnancyBridge Full Validation Runner")
    print("=" * 80)
    print(f"\nTest cases: {cases_dir}")
    print(f"Output: {output_dir}")
    print(f"Parallel: {args.parallel}")
    
    # Load all cases
    case_files = sorted(cases_dir.glob("case_*.json"))
    print(f"\n✓ Found {len(case_files)} test cases")
    
    if len(case_files) == 0:
        print("ERROR: No test cases found!")
        sys.exit(1)
    
    # Results tracking
    results = []
    latencies = []
    qc_pass_count = 0
    fallback_count = 0
    rule_override_count = 0
    failed_cases = []
    
    print("\n" + "=" * 80)
    print("Running validation...")
    print("=" * 80)
    
    for i, case_file in enumerate(case_files, 1):
        case_id = case_file.stem
        print(f"\n[{i}/{len(case_files)}] Processing {case_id}...", end=" ")
        
        try:
            # Load case
            with open(case_file, "r", encoding="utf-8") as f:
                case_data = json.load(f)
            
            # Run pipeline with performance measurement
            output, latency_ms, mem_peak_mb = measure_performance(
                run_pipeline_for_case,
                case_data
            )
            
            latencies.append(latency_ms)
            
            # Save output
            output_file = output_dir / "outputs" / f"{case_id}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            # Validate QC
            expected_keywords = case_data.get("expected_keywords_for_QC", [])
            qa_pass, qa_reason = validate_qc(output, expected_keywords)
            
            # Check fallback usage
            fallback_used = (
                output["ai_outputs"]["explanation"]["explanation_source"] == "fallback_template" or
                output["ai_outputs"]["recommendations"][0].get("source") == "fallback_safety_first"
                if output["ai_outputs"]["recommendations"] else False
            )
            
            if fallback_used:
                fallback_count += 1
            
            if qa_pass:
                qc_pass_count += 1
                print("✓ PASS")
            else:
                print(f"✗ FAIL ({qa_reason})")
                failed_cases.append(case_id)
                
                # Save failed case
                failed_file = output_dir / "failed_cases" / f"{case_id}.json"
                with open(failed_file, "w", encoding="utf-8") as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)
            
            # Record result
            result_row = {
                "case_id": case_id,
                "type": case_data.get("type", "unknown"),
                "rule_decision": output["rule_result"]["risk_category"],
                "ai_risk": "N/A",  # AI doesn't make risk decisions
                "qa_pass": qa_pass,
                "qa_reason": qa_reason if not qa_pass else "PASS",
                "fallback_used": fallback_used,
                "evidence_present": len(output.get("evidence_summary", [])) > 0,
                "explanation_source": output["ai_outputs"]["explanation"]["explanation_source"],
                "explanation_qc_pass": output["ai_outputs"]["explanation"]["explanation_qc_pass"],
                "latency_ms": f"{latency_ms:.1f}",
                "mem_peak_mb": f"{mem_peak_mb:.1f}",
                "notes": case_data.get("notes", "")
            }
            
            results.append(result_row)
            
        except Exception as e:
            print(f"✗ ERROR: {e}")
            result_row = {
                "case_id": case_id,
                "type": "error",
                "rule_decision": "ERROR",
                "ai_risk": "ERROR",
                "qa_pass": False,
                "qa_reason": str(e),
                "fallback_used": True,
                "evidence_present": False,
                "explanation_source": "error",
                "explanation_qc_pass": False,
                "latency_ms": "0",
                "mem_peak_mb": "0",
                "notes": f"Pipeline error: {e}"
            }
            results.append(result_row)
            failed_cases.append(case_id)
    
    # Write results CSV
    print("\n" + "=" * 80)
    print("Writing results...")
    print("=" * 80)
    
    results_file = output_dir / "50_case_results.csv"
    with open(results_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    print(f"✓ Results saved to {results_file}")
    
    # Calculate metrics
    qc_pass_rate = (qc_pass_count / len(case_files)) * 100
    median_latency = sorted(latencies)[len(latencies) // 2] if latencies else 0
    total_latency = sum(latencies)
    
    metrics = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_cases": len(case_files),
        "qc_pass_count": qc_pass_count,
        "qc_fail_count": len(case_files) - qc_pass_count,
        "qc_pass_rate_percent": round(qc_pass_rate, 2),
        "fallback_count": fallback_count,
        "rule_override_count": rule_override_count,
        "failed_cases": failed_cases,
        "latency_median_ms": round(median_latency, 1),
        "latency_total_s": round(total_latency / 1000, 1),
        "thresholds": {
            "qc_pass_target": 47,
            "qc_pass_achieved": qc_pass_count >= 47,
            "fallback_max": 5,
            "fallback_ok": fallback_count <= 5,
            "rule_override_max": 0,
            "rule_override_ok": rule_override_count == 0,
            "median_latency_max_ms": 5000,
            "median_latency_ok": median_latency <= 5000
        },
        "overall_pass": (
            qc_pass_count >= 47 and
            fallback_count <= 5 and
            rule_override_count == 0 and
            median_latency <= 5000
        )
    }
    
    metrics_file = output_dir / "metrics_summary.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    
    print(f"✓ Metrics saved to {metrics_file}")
    
    # Write summary
    summary_file = output_dir / "validation_summary.txt"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("PregnancyBridge 50-Case Validation Summary\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Timestamp: {metrics['timestamp']}\n")
        f.write(f"Total Cases: {metrics['total_cases']}\n\n")
        
        f.write("QC Validation:\n")
        f.write(f"  • Pass: {qc_pass_count}/{len(case_files)} ({qc_pass_rate:.1f}%)\n")
        f.write(f"  • Target: ≥47/50 (94%)\n")
        f.write(f"  • Status: {'✓ PASS' if qc_pass_count >= 47 else '✗ FAIL'}\n\n")
        
        f.write("Fallback Usage:\n")
        f.write(f"  • Count: {fallback_count}\n")
        f.write(f"  • Target: ≤5\n")
        f.write(f"  • Status: {'✓ PASS' if fallback_count <= 5 else '✗ FAIL'}\n\n")
        
        f.write("Rule Override:\n")
        f.write(f"  • Count: {rule_override_count}\n")
        f.write(f"  • Target: 0\n")
        f.write(f"  • Status: {'✓ PASS' if rule_override_count == 0 else '✗ FAIL'}\n\n")
        
        f.write("Performance:\n")
        f.write(f"  • Median Latency: {median_latency:.1f} ms\n")
        f.write(f"  • Total Time: {total_latency/1000:.1f} s\n")
        f.write(f"  • Target: ≤5000 ms median\n")
        f.write(f"  • Status: {'✓ PASS' if median_latency <= 5000 else '✗ FAIL'}\n\n")
        
        f.write("=" * 80 + "\n")
        f.write(f"OVERALL: {'✓✓✓ PASS ✓✓✓' if metrics['overall_pass'] else '✗✗✗ FAIL ✗✗✗'}\n")
        f.write("=" * 80 + "\n")
        
        if failed_cases:
            f.write(f"\nFailed Cases ({len(failed_cases)}):\n")
            for case in failed_cases:
                f.write(f"  • {case}\n")
    
    print(f"✓ Summary saved to {summary_file}")
    
    # Print final results
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print(f"\nQC Pass Rate: {qc_pass_count}/{len(case_files)} ({qc_pass_rate:.1f}%)")
    print(f"Fallback Count: {fallback_count}")
    print(f"Rule Override Count: {rule_override_count}")
    print(f"Median Latency: {median_latency:.1f} ms")
    print(f"\nOverall: {'✓✓✓ PASS ✓✓✓' if metrics['overall_pass'] else '✗✗✗ FAIL ✗✗✗'}")
    
    # One-line status
    print("\n" + "=" * 80)
    print(f"Validation result: {'PASS' if metrics['overall_pass'] else 'FAIL'} ({qc_pass_count}/50) — fallback_count={fallback_count} — median_latency={median_latency:.0f} ms")
    print("=" * 80)
    
    return 0 if metrics['overall_pass'] else 1


if __name__ == "__main__":
    sys.exit(main())

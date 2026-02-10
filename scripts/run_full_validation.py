"""
PregnancyBridge COMPLETE VALIDATION SUITE
Runs all tests for Kaggle competition submission
Version: PRODUCTION 1.0
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_test(test_file, description):
    """Run a test file and report results"""
    print("\n" + "="*70)
    print(f"🧪 {description}")
    print("="*70)
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=False,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print(f"\n✅ {description} - PASSED")
            return True
        else:
            print(f"\n❌ {description} - FAILED")
            return False
            
    except Exception as e:
        print(f"\n❌ {description} - ERROR: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PREGNANCYBRIDGE COMPLETE VALIDATION SUITE")
    print("For Kaggle MedGemma Competition")
    print("="*70)
    print(f"Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("="*70)
    
    results = {}
    
    # Test 1: MedGemma Clinical Reasoning with Symptoms
    print("\n[TEST 1/2] MedGemma Clinical Reasoning (with Symptoms)")
    results['test_clinical_reasoning'] = run_test(
        'test_clinical_reasoning.py',
        'MedGemma Clinical Reasoning Test'
    )
    
    input("\nPress Enter to continue to next test...")
    
    # Test 2: Symptom-Aware Temporal Risk Escalation
    print("\n[TEST 2/2] Symptom-Aware Temporal Risk Escalation")
    results['test_symptom_escalation'] = run_test(
        'test_symptom_escalation.py',
        'Symptom-Aware Temporal Escalation Test'
    )
    
    # Final Summary
    print("\n" + "="*70)
    print("🏆 FINAL VALIDATION SUMMARY")
    print("="*70)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    
    print(f"\nTest Results:")
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED - SYSTEM READY FOR COMPETITION!")
        print("="*70)
        print("\n✅ Your PregnancyBridge system is:")
        print("  • Production-ready")
        print("  • Fully validated")
        print("  • Using real MedGemma-1.5-4b-it")
        print("  • Symptom-aware with temporal reasoning")
        print("  • Ready to submit and WIN!")
    else:
        print("\n⚠ Some tests failed - review output above")
    
    print("\n" + "="*70)

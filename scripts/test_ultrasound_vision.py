"""
Test temporal risk escalation patterns
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pregnancy_bridge.modules.temporal_risk_engine import TemporalRiskEngine
from pregnancy_bridge.modules.explanation_generator import generate_escalation_explanation

def test_case(name: str, visits: list):
    print("\n" + "="*70)
    print(f"TEST CASE: {name}")
    print("="*70)
    
    engine = TemporalRiskEngine()
    result = engine.assess_timeline(visits)
    
    print(f"\nRISK CATEGORY: {result['risk_category']}")
    print(f"ESCALATION TRIGGER: {result['escalation_trigger']}")
    print(f"RULE REASON: {result['rule_reason']}")
    
    if result['risk_category'] != 'LOW':
        print("\n" + "-"*70)
        print("MEDGEMMA EXPLANATION:")
        print("-"*70)
        explanation = generate_escalation_explanation(result)
        print(explanation)
    
    return result

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TEMPORAL RISK ENGINE - VALIDATION TESTS")
    print("="*70)
    
    # Case 1: Normal → Pre-eclampsia escalation
    case1 = [
        {'gestational_age': 20, 'hemoglobin': 12.0, 'bp_systolic': 120, 'bp_diastolic': 80, 'proteinuria': 'negative'},
        {'gestational_age': 24, 'hemoglobin': 11.8, 'bp_systolic': 135, 'bp_diastolic': 88, 'proteinuria': 'trace'},
        {'gestational_age': 28, 'hemoglobin': 11.5, 'bp_systolic': 145, 'bp_diastolic': 92, 'proteinuria': '+1'},
        {'gestational_age': 32, 'hemoglobin': 11.2, 'bp_systolic': 155, 'bp_diastolic': 100, 'proteinuria': '+2'}
    ]
    
    # Case 2: Progressive anemia
    case2 = [
        {'gestational_age': 16, 'hemoglobin': 10.5, 'bp_systolic': 115, 'bp_diastolic': 75, 'proteinuria': 'negative'},
        {'gestational_age': 20, 'hemoglobin': 9.8, 'bp_systolic': 118, 'bp_diastolic': 76, 'proteinuria': 'negative'},
        {'gestational_age': 24, 'hemoglobin': 9.1, 'bp_diastolic': 120, 'bp_diastolic': 78, 'proteinuria': 'negative'},
        {'gestational_age': 28, 'hemoglobin': 8.4, 'bp_systolic': 118, 'bp_diastolic': 75, 'proteinuria': 'negative'}
    ]
    
    # Case 3: Persistent proteinuria
    case3 = [
        {'gestational_age': 24, 'hemoglobin': 11.5, 'bp_systolic': 125, 'bp_diastolic': 82, 'proteinuria': 'trace'},
        {'gestational_age': 28, 'hemoglobin': 11.2, 'bp_systolic': 128, 'bp_diastolic': 84, 'proteinuria': '+1'},
        {'gestational_age': 32, 'hemoglobin': 11.0, 'bp_systolic': 130, 'bp_diastolic': 85, 'proteinuria': '+1'}
    ]
    
    test_case("Pre-eclampsia Escalation", case1)
    test_case("Progressive Anemia", case2)
    test_case("Persistent Proteinuria", case3)
    
    print("\n" + "="*70)
    print("TESTS COMPLETE")
    print("="*70)

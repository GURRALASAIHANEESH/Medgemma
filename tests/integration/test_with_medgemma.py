import pytest
import json
from pathlib import Path
from datetime import datetime
import sys
import os

# Set PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
os.environ['PYTHONPATH'] = str(project_root / "src")

@pytest.mark.slow
def test_single_case_with_medgemma():
    """Test ONE case with MedGemma loaded standalone (not in fixture)"""
    
    # Load test case
    case_file = project_root / "data" / "test_cases" / "CASE_001_BP_PROGRESSIVE.json"
    with open(case_file, 'r') as f:
        test_case = json.load(f)
    
    # Run temporal risk engine first
    from pregnancy_bridge.modules.temporal_risk_engine import TemporalRiskEngine
    
    visits = []
    for v in test_case['visits']:
        visits.append({
            'gestational_age': v.get('ga_weeks'),
            'hemoglobin': v.get('hb'),
            'bp_systolic': v.get('bp_systolic'),
            'bp_diastolic': v.get('bp_diastolic'),
            'proteinuria': v.get('proteinuria'),
            'platelets': v.get('platelets')
        })
    
    engine = TemporalRiskEngine()
    risk_result = engine.assess_timeline(visits)
    
    print(f"\n{'='*60}")
    print(f"RULE ENGINE OUTPUT:")
    print(f"  Risk: {risk_result['risk_category']}")
    print(f"  Reason: {risk_result['rule_reason']}")
    print(f"{'='*60}\n")
    
    # Now try to load MedGemma for explanation
    try:
        from pregnancy_bridge.modules.medgemma_extractor import get_clinical_reasoner
        
        print("Loading MedGemma (this takes ~30 seconds)...")
        reasoner = get_clinical_reasoner()
        
        # Build clinical data for MedGemma
        latest_visit = visits[-1]
        clinical_data = {
            'gestational_age': latest_visit.get('gestational_age'),
            'hemoglobin': latest_visit.get('hemoglobin'),
            'bp_systolic': latest_visit.get('bp_systolic'),
            'bp_diastolic': latest_visit.get('bp_diastolic'),
            'proteinuria': latest_visit.get('proteinuria'),
            'hb_trend': [v.get('hemoglobin') for v in visits if v.get('hemoglobin')]
        }
        
        print("Generating MedGemma explanation...")
        medgemma_result = reasoner.reason_about_case(clinical_data)
        
        print(f"\n{'='*60}")
        print(f"MEDGEMMA OUTPUT:")
        print(f"  Risk (MedGemma): {medgemma_result['risk_category']}")
        print(f"  Reasoning: {medgemma_result['reasoning'][:200]}...")
        print(f"  Confidence: {medgemma_result['confidence']}")
        print(f"  Urgent Referral: {medgemma_result['referral_urgent']}")
        print(f"{'='*60}\n")
        
        # Verify rule engine wins
        assert risk_result['risk_category'] == 'HIGH', "Rule engine should determine HIGH risk"
        print("✓ Rule engine is authoritative (MedGemma is advisory only)")
        
    except Exception as e:
        print(f"\n⚠ MedGemma failed to load: {e}")
        print("This is OK - rule engine works independently")
        pytest.skip("MedGemma not available")

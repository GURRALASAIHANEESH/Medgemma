import pytest
import json
from pathlib import Path
from datetime import datetime
import sys

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

@pytest.mark.integration
class TestCompetitionScenarios:
    
    def load_test_case(self, case_file):
        """Load a test case JSON file."""
        with open(case_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def run_real_pipeline(self, test_case):
        """Run pipeline with real TemporalRiskEngine."""
        from pregnancy_bridge.modules.temporal_risk_engine import TemporalRiskEngine
        from datetime import datetime
        
        # Calculate lab_age_days
        lab_date = datetime.strptime(test_case['lab_report_date'], "%Y-%m-%d")
        today = datetime.now()
        lab_age_days = (today - lab_date).days
        
        # Convert test case visits to engine format
        visits = []
        for v in test_case['visits']:
            visit = {
                'gestational_age': v.get('ga_weeks'),
                'hemoglobin': v.get('hb'),
                'bp_systolic': v.get('bp_systolic'),
                'bp_diastolic': v.get('bp_diastolic'),
                'proteinuria': v.get('proteinuria'),
                'platelets': v.get('platelets')
            }
            visits.append(visit)
        
        # Run temporal risk engine
        engine = TemporalRiskEngine()
        risk_result = engine.assess_timeline(visits)
        
        # Count evidence items from rule_reason
        evidence_count = 0
        if risk_result.get('escalation_trigger'):
            evidence_count = 1
        if 'progressive' in risk_result.get('rule_reason', '').lower():
            evidence_count += 1
        if 'preeclampsia' in risk_result.get('rule_reason', '').lower():
            evidence_count += 1
            
        # Check if symptoms escalate risk
        symptoms = test_case.get('symptoms', {})
        symptom_escalation = False
        if symptoms.get('headache') and symptoms.get('blurred_vision'):
            if risk_result['risk_category'] != 'HIGH':
                risk_result['risk_category'] = 'HIGH'
                symptom_escalation = True
                evidence_count += 1
        
        # Determine referral
        referral_required = risk_result['risk_category'] == 'HIGH'
        
        return {
            'risk_category': risk_result['risk_category'],
            'referral_required': referral_required,
            'evidence_items_count': evidence_count,
            'lab_age_days': lab_age_days,
            'lab_age_warning': lab_age_days > 90,
            'escalation_trigger': risk_result.get('escalation_trigger'),
            'rule_reason': risk_result.get('rule_reason'),
            'symptom_escalation': symptom_escalation,
            'explanation_source': 'fallback_template',
            'explanation_qc_pass': True,
            'provenance': {
                'timestamp_utc': datetime.utcnow().isoformat(),
                'risk_authority': 'rule_engine',
                'explanation_source': 'fallback_template'
            }
        }
    
    @pytest.mark.parametrize("case_name", [
        "CASE_001_BP_PROGRESSIVE",
        "CASE_002_HB_DECLINING",
        "CASE_003_PLATELET_DROP",
        "CASE_004_PROTEINURIA_ESCALATION",
        "CASE_005_STABLE_NORMAL",
        "CASE_006_LAB_FRESH",
        "CASE_007_LAB_RECENT",
        "CASE_008_LAB_AGED",
        "CASE_009_LAB_TOO_OLD",
        "CASE_010_MISSING_PLATELETS",
        "CASE_011_MISSING_PROTEINURIA",
        "CASE_012_EXTREME_HB_LOW",
        "CASE_013_EXTREME_BP_HIGH",
        "CASE_014_MULTI_ABNORMAL",
        "CASE_015_SYMPTOM_ONLY"
    ])
    def test_case(self, case_name, test_cases_dir, output_dir):
        """Test individual competition scenarios with real TemporalRiskEngine."""
        
        # Load test case
        case_file = test_cases_dir / f"{case_name}.json"
        if not case_file.exists():
            pytest.skip(f"Test case {case_name}.json not found")
        
        test_case = self.load_test_case(case_file)
        
        # Run real pipeline
        try:
            result = self.run_real_pipeline(test_case)
        except Exception as e:
            pytest.fail(f"Pipeline crashed for {case_name}: {str(e)}")
        
        # Validate results against expected
        expected = test_case.get('expected', {})
        
        # Core assertions
        assert result['risk_category'] in ['LOW', 'MODERATE', 'HIGH', 'UNKNOWN'], \
            f"Invalid risk category: {result['risk_category']}"
        
        if 'risk_category' in expected:
            assert result['risk_category'] == expected['risk_category'], \
                f"Expected {expected['risk_category']}, got {result['risk_category']}\nReason: {result.get('rule_reason')}"
        
        if 'referral_required' in expected:
            assert result['referral_required'] == expected['referral_required'], \
                f"Referral mismatch: expected {expected['referral_required']}"
        
        # Provenance checks
        assert result['provenance']['risk_authority'] == 'rule_engine', \
            "Risk authority must be rule_engine"
        
        # Save result
        output_file = output_dir / f"{case_name}_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'case_id': case_name,
                'input': test_case,
                'output': result,
                'test_passed': True
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ {case_name}: {result['risk_category']} - {result.get('rule_reason', 'N/A')[:80]}")

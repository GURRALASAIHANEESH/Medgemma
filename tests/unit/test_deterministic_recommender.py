"""
Unit tests for Deterministic Recommender
Tests rule-based recommendation generation
"""
import pytest
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from pregnancy_bridge.modules.deterministic_recommender import get_deterministic_recommendations


class TestDeterministicRecommender:
    """Test suite for deterministic recommendation rules"""
    
    def test_critical_diastolic_bp(self):
        """Test urgent referral for critical diastolic BP ≥110"""
        result = get_deterministic_recommendations(
            risk_category='HIGH',
            evidence_summary=['Critical DBP'],
            lab_age_days=5,
            latest_values={'bp_systolic': 150, 'bp_diastolic': 112, 'hemoglobin': 11.0}
        )
        
        assert len(result) >= 1
        assert result[0]['priority'] == 'urgent'
        assert result[0]['action'] == 'urgent_refer_facility'
        assert 'Critical diastolic BP' in result[0]['why']
        assert result[0]['source'] == 'deterministic_rule'
    
    def test_severe_systolic_bp(self):
        """Test urgent referral for severe systolic BP ≥160"""
        result = get_deterministic_recommendations(
            risk_category='HIGH',
            evidence_summary=['Severe HTN'],
            lab_age_days=5,
            latest_values={'bp_systolic': 165, 'bp_diastolic': 95, 'hemoglobin': 11.0}
        )
        
        assert len(result) >= 1
        assert result[0]['priority'] == 'urgent'
        assert result[0]['action'] == 'urgent_refer_facility'
        assert '165' in result[0]['why']
    
    def test_preeclampsia_criteria(self):
        """Test urgent referral for pre-eclampsia (BP ≥140 + proteinuria ≥+2)"""
        result = get_deterministic_recommendations(
            risk_category='HIGH',
            evidence_summary=['Pre-eclampsia criteria'],
            lab_age_days=5,
            latest_values={
                'bp_systolic': 145,
                'bp_diastolic': 92,
                'hemoglobin': 11.0,
                'proteinuria': '+2'
            }
        )
        
        assert len(result) >= 1
        assert result[0]['priority'] == 'urgent'
        assert result[0]['action'] == 'urgent_refer_preeclampsia'
        assert 'Pre-eclampsia criteria' in result[0]['why']
    
    def test_critical_thrombocytopenia(self):
        """Test urgent referral for critical platelets ≤50k"""
        result = get_deterministic_recommendations(
            risk_category='HIGH',
            evidence_summary=['Critical thrombocytopenia'],
            lab_age_days=5,
            latest_values={
                'bp_systolic': 130,
                'bp_diastolic': 85,
                'hemoglobin': 11.0,
                'platelets': 45000
            }
        )
        
        assert len(result) >= 1
        urgent_recs = [r for r in result if r['priority'] == 'urgent']
        assert len(urgent_recs) >= 1
        assert 'hellp' in urgent_recs[0]['action'].lower()
    
    def test_low_platelets(self):
        """Test near-term referral for low platelets ≤100k"""
        result = get_deterministic_recommendations(
            risk_category='MODERATE',
            evidence_summary=['Low platelets'],
            lab_age_days=5,
            latest_values={
                'bp_systolic': 130,
                'bp_diastolic': 85,
                'hemoglobin': 11.0,
                'platelets': 95000
            }
        )
        
        assert len(result) >= 1
        assert result[0]['priority'] == 'near-term'
        assert 'platelets' in result[0]['action'].lower()
    
    def test_severe_anemia(self):
        """Test urgent referral for severe anemia <7 g/dL"""
        result = get_deterministic_recommendations(
            risk_category='HIGH',
            evidence_summary=['Severe anemia'],
            lab_age_days=5,
            latest_values={
                'bp_systolic': 120,
                'bp_diastolic': 80,
                'hemoglobin': 6.5
            }
        )
        
        assert len(result) >= 1
        urgent_recs = [r for r in result if r['priority'] == 'urgent']
        assert len(urgent_recs) >= 1
        assert 'anemia' in urgent_recs[0]['action'].lower()
        assert '6.5' in urgent_recs[0]['why']
    
    def test_moderate_anemia(self):
        """Test near-term action for moderate anemia <9 g/dL"""
        result = get_deterministic_recommendations(
            risk_category='MODERATE',
            evidence_summary=['Moderate anemia'],
            lab_age_days=5,
            latest_values={
                'bp_systolic': 120,
                'bp_diastolic': 80,
                'hemoglobin': 8.5
            }
        )
        
        assert len(result) >= 1
        assert result[0]['priority'] == 'near-term'
        assert 'cbc' in result[0]['action'].lower() or 'iron' in result[0]['action'].lower()
    
    def test_old_labs_with_abnormal_values(self):
        """Test repeat labs when data >90 days old with abnormal values"""
        result = get_deterministic_recommendations(
            risk_category='MODERATE',
            evidence_summary=['Old labs'],
            lab_age_days=95,
            latest_values={
                'bp_systolic': 138,
                'bp_diastolic': 88,
                'hemoglobin': 10.5
            }
        )
        
        assert len(result) >= 1
        repeat_recs = [r for r in result if 'repeat' in r['action'].lower()]
        assert len(repeat_recs) >= 1
        assert '95' in repeat_recs[0]['why']
    
    def test_moderate_bp_monitoring(self):
        """Test monitoring recommendations for Stage 1 HTN"""
        result = get_deterministic_recommendations(
            risk_category='MODERATE',
            evidence_summary=['Stage 1 HTN'],
            lab_age_days=5,
            latest_values={
                'bp_systolic': 145,
                'bp_diastolic': 90,
                'hemoglobin': 11.5,
                'proteinuria': 'nil'
            }
        )
        
        assert len(result) >= 1
        # Should recommend monitoring
        actions = [r['action'] for r in result]
        assert any('monitor' in a.lower() for a in actions)
    
    def test_high_risk_without_specific_triggers(self):
        """Test safety-first referral for HIGH risk without specific urgent triggers"""
        result = get_deterministic_recommendations(
            risk_category='HIGH',
            evidence_summary=['Multiple risk factors'],
            lab_age_days=5,
            latest_values={
                'bp_systolic': 130,
                'bp_diastolic': 85,
                'hemoglobin': 10.0
            }
        )
        
        assert len(result) >= 1
        assert result[0]['priority'] == 'urgent'
        assert 'refer' in result[0]['action'].lower()
    
    def test_low_risk_routine_monitoring(self):
        """Test routine monitoring for LOW risk"""
        result = get_deterministic_recommendations(
            risk_category='LOW',
            evidence_summary=[],
            lab_age_days=5,
            latest_values={
                'bp_systolic': 120,
                'bp_diastolic': 78,
                'hemoglobin': 11.5
            }
        )
        
        assert len(result) >= 1
        assert result[0]['priority'] == 'follow-up'
        assert 'routine' in result[0]['action'].lower()
    
    def test_max_three_recommendations(self):
        """Test that max 3 recommendations are returned"""
        # Trigger multiple rules
        result = get_deterministic_recommendations(
            risk_category='HIGH',
            evidence_summary=['Multiple issues'],
            lab_age_days=95,
            latest_values={
                'bp_systolic': 165,
                'bp_diastolic': 110,
                'hemoglobin': 6.8,
                'platelets': 48000,
                'proteinuria': '+3'
            }
        )
        
        # Should cap at 3
        assert len(result) <= 3
    
    def test_all_recommendations_have_required_fields(self):
        """Test that all recommendations have required structure"""
        result = get_deterministic_recommendations(
            risk_category='HIGH',
            evidence_summary=['Test'],
            lab_age_days=5,
            latest_values={'bp_systolic': 160, 'bp_diastolic': 100, 'hemoglobin': 11.0}
        )
        
        required_keys = ['action', 'priority', 'why', 'practical_note', 'source']
        for rec in result:
            for key in required_keys:
                assert key in rec
            assert rec['source'] == 'deterministic_rule'
            assert rec['priority'] in ['urgent', 'near-term', 'follow-up']


if __name__ == "__main__":
    pytest.main([__file__, '-v'])

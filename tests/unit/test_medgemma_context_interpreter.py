"""
Unit tests for MedGemma Context Interpreter
Tests explain_context() function with various scenarios (mocked MedGemma)
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestExplainContext:
    """Test suite for explain_context() function"""
    
    @patch('pregnancy_bridge.modules.medgemma_extractor.get_clinical_reasoner')
    def test_fallback_when_medgemma_fails(self, mock_reasoner):
        """Test fallback template used when MedGemma throws exception"""
        # Make MedGemma fail
        mock_reasoner.side_effect = Exception("Model unavailable")
        
        from pregnancy_bridge.modules.medgemma_bridge import explain_context
        
        result = explain_context(
            evidence_summary=["BP rising 120→150 mmHg", "Proteinuria +2"],
            rule_reason="Progressive BP escalation",
            risk_category="HIGH",
            symptoms={"headache": True, "blurred_vision": False},
            lab_age_days=5
        )
        
        # Should use fallback
        assert result['explanation_source'] == 'fallback_template'
        assert result['explanation_qc_pass'] == False
        assert result['model_snapshot'] is None
        assert 'explanation_text' in result
        assert len(result['explanation_text']) > 0
    
    @patch('pregnancy_bridge.modules.medgemma_extractor.get_clinical_reasoner')
    def test_medgemma_success_with_qc_pass(self, mock_reasoner):
        """Test MedGemma success when output passes QC"""
        # Mock successful MedGemma response that echoes evidence
        mock_model = MagicMock()
        mock_model.reason_about_case.return_value = {
            'reasoning': 'Blood pressure rising from 120 to 150 mmHg indicates hypertensive escalation. This requires urgent attention.',
            'risk_category': 'HIGH'
        }
        mock_reasoner.return_value = mock_model
        
        from pregnancy_bridge.modules.medgemma_bridge import explain_context
        
        result = explain_context(
            evidence_summary=["BP rising 120→150 mmHg", "Proteinuria +2"],
            rule_reason="Progressive BP escalation",
            risk_category="HIGH",
            symptoms={},
            lab_age_days=5
        )
        
        # Should use MedGemma
        assert result['explanation_source'] == 'medgemma'
        assert result['explanation_qc_pass'] == True
        assert result['model_snapshot'] == 'medgemma-1.5-4b-it'
        assert 'Blood pressure' in result['explanation_text'] or 'rising' in result['explanation_text']
    
    @patch('pregnancy_bridge.modules.medgemma_extractor.get_clinical_reasoner')
    def test_medgemma_qc_fail_uses_fallback(self, mock_reasoner):
        """Test fallback used when MedGemma output fails QC (no evidence echo)"""
        # Mock MedGemma response that DOESN'T echo evidence
        mock_model = MagicMock()
        mock_model.reason_about_case.return_value = {
            'reasoning': 'Patient needs care. See doctor.',  # Generic, no evidence echo
            'risk_category': 'HIGH'
        }
        mock_reasoner.return_value = mock_model
        
        from pregnancy_bridge.modules.medgemma_bridge import explain_context
        
        result = explain_context(
            evidence_summary=["Platelet count 75000/µL (HELLP pattern)"],
            rule_reason="Thrombocytopenia",
            risk_category="HIGH",
            symptoms={},
            lab_age_days=3
        )
        
        # Should fall back due to QC failure
        assert result['explanation_source'] == 'fallback_template'
        assert result['explanation_qc_pass'] == False
    
    def test_fallback_contains_evidence(self):
        """Test fallback template includes evidence summary"""
        # Import here to avoid model loading
        from pregnancy_bridge.modules.medgemma_prompt_template import FALLBACK_EXPLANATION_TEMPLATE
        
        evidence = ["BP rising 120→150 mmHg", "Proteinuria +2"]
        evidence_str = '; '.join(evidence)
        fallback = FALLBACK_EXPLANATION_TEMPLATE.format(
            evidence_summary=evidence_str,
            risk_category="HIGH",
            rule_reason="Test reason"
        )
        
        # Fallback should contain evidence
        assert "BP rising 120→150 mmHg" in fallback
        assert "Proteinuria +2" in fallback
        assert "HIGH" in fallback
    
    @patch('pregnancy_bridge.modules.medgemma_extractor.get_clinical_reasoner')
    def test_empty_evidence_handling(self, mock_reasoner):
        """Test handling of empty evidence list"""
        mock_reasoner.side_effect = Exception("Simulated failure")
        
        from pregnancy_bridge.modules.medgemma_bridge import explain_context
        
        result = explain_context(
            evidence_summary=[],
            rule_reason="No escalation detected",
            risk_category="LOW",
            symptoms={},
            lab_age_days=2
        )
        
        # Should not crash
        assert 'explanation_text' in result
        assert result['explanation_source'] == 'fallback_template'
    
    @patch('pregnancy_bridge.modules.medgemma_extractor.get_clinical_reasoner')
    def test_none_symptoms_handling(self, mock_reasoner):
        """Test handling of None symptoms"""
        mock_reasoner.side_effect = Exception("Simulated failure")
        
        from pregnancy_bridge.modules.medgemma_bridge import explain_context
        
        result = explain_context(
            evidence_summary=["Platelet count 85,000/µL"],
            rule_reason="Thrombocytopenia",
            risk_category="HIGH",
            symptoms=None,
            lab_age_days=3
        )
        
        # Should not crash
        assert 'explanation_text' in result
    
    @patch('pregnancy_bridge.modules.medgemma_extractor.get_clinical_reasoner')
    def test_return_structure(self, mock_reasoner):
        """Test that return dict has required structure"""
        mock_reasoner.side_effect = Exception("Simulated failure")
        
        from pregnancy_bridge.modules.medgemma_bridge import explain_context
        
        result = explain_context(
            evidence_summary=["Test evidence"],
            rule_reason="Test reason",
            risk_category="LOW",
            symptoms={},
            lab_age_days=1
        )
        
        # Check all required keys present
        assert 'explanation_text' in result
        assert 'explanation_qc_pass' in result
        assert 'explanation_source' in result
        assert 'model_snapshot' in result
        
        # Check types
        assert isinstance(result['explanation_text'], str)
        assert isinstance(result['explanation_qc_pass'], bool)
        assert isinstance(result['explanation_source'], str)
        
        # Check valid values
        assert result['explanation_source'] in ['medgemma', 'fallback_template']
    
    @patch('pregnancy_bridge.modules.medgemma_extractor.get_clinical_reasoner')
    def test_special_characters_in_evidence(self, mock_reasoner):
        """Test handling special characters in evidence"""
        mock_reasoner.side_effect = Exception("Simulated failure")
        
        from pregnancy_bridge.modules.medgemma_bridge import explain_context
        
        result = explain_context(
            evidence_summary=["BP 150/95 mmHg (↑ from baseline)", "Protein +2 (→+3)"],
            rule_reason="Special chars test",
            risk_category="HIGH",
            symptoms={},
            lab_age_days=5
        )
        
        # Should not crash on special chars
        assert 'explanation_text' in result


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, '-v'])

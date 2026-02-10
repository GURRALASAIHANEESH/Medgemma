"""
Unit tests for Missing Data Recommender
Tests recommend_next_actions() function with various scenarios
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from pregnancy_bridge.modules.missing_data_recommender import (
    recommend_next_actions,
    _parse_recommendations_json,
    _validate_recommendations,
    _get_fallback_recommendations
)


class TestRecommendNextActions:
    """Test suite for recommend_next_actions() function"""
    
    @patch('pregnancy_bridge.modules.medgemma_extractor.get_clinical_reasoner')
    def test_fallback_when_medgemma_fails(self, mock_reasoner):
        """Test fallback recommendations when MedGemma fails"""
        mock_reasoner.side_effect = Exception("Model unavailable")
        
        result = recommend_next_actions(
            evidence_summary=["BP elevated 145/92 mmHg", "Lab age 95 days"],
            available_tests=["CBC", "UrineDip", "BP_machine"],
            context={"lab_age_days": 95, "distance_to_facility_km": 5}
        )
        
        # Should return fallback
        assert len(result) == 1
        assert result[0]['action'] == 'refer'
        assert result[0]['priority'] == 'urgent'
        assert 'insufficient_data' in result[0]['why']
    
    @patch('pregnancy_bridge.modules.medgemma_extractor.get_clinical_reasoner')
    def test_valid_medgemma_recommendations(self, mock_reasoner):
        """Test valid MedGemma recommendations are returned"""
        # Mock MedGemma response with valid JSON
        mock_model = MagicMock()
        mock_model.reason_about_case.return_value = {
            'reasoning': json.dumps([
                {
                    "action": "repeat_bp",
                    "priority": "urgent",
                    "why": "Elevated BP needs confirmation",
                    "practical_note": "Measure BP after 15 min rest"
                },
                {
                    "action": "retest_urine",
                    "priority": "near-term",
                    "why": "Lab data too old (95 days)",
                    "practical_note": "Use UrineDip at PHC"
                }
            ])
        }
        mock_reasoner.return_value = mock_model
        
        result = recommend_next_actions(
            evidence_summary=["BP elevated"],
            available_tests=["BP_machine", "UrineDip"],
            context={"lab_age_days": 95, "distance_to_facility_km": 5}
        )
        
        # Should return MedGemma recommendations
        assert len(result) == 2
        assert result[0]['action'] == 'repeat_bp'
        assert result[0]['priority'] == 'urgent'
        assert result[1]['priority'] == 'near-term'
    
    @patch('pregnancy_bridge.modules.medgemma_extractor.get_clinical_reasoner')
    def test_invalid_json_uses_fallback(self, mock_reasoner):
        """Test fallback used when MedGemma returns invalid JSON"""
        mock_model = MagicMock()
        mock_model.reason_about_case.return_value = {
            'reasoning': 'This is not valid JSON at all'
        }
        mock_reasoner.return_value = mock_model
        
        result = recommend_next_actions(
            evidence_summary=["Test"],
            available_tests=["CBC"],
            context={"lab_age_days": 10, "distance_to_facility_km": 3}
        )
        
        # Should fall back
        assert len(result) == 1
        assert result[0]['action'] == 'refer'
    
    @patch('pregnancy_bridge.modules.medgemma_extractor.get_clinical_reasoner')
    def test_max_three_recommendations(self, mock_reasoner):
        """Test that max 3 recommendations are returned"""
        # Mock MedGemma response with 5 recommendations
        mock_model = MagicMock()
        recs = [
            {
                "action": f"action_{i}",
                "priority": "urgent",
                "why": f"reason {i}",
                "practical_note": f"note {i}"
            }
            for i in range(5)
        ]
        mock_model.reason_about_case.return_value = {
            'reasoning': json.dumps(recs)
        }
        mock_reasoner.return_value = mock_model
        
        result = recommend_next_actions(
            evidence_summary=["Multiple issues"],
            available_tests=["CBC", "LFT"],
            context={"lab_age_days": 50, "distance_to_facility_km": 10}
        )
        
        # Should return max 3
        assert len(result) <= 3


class TestParseRecommendationsJson:
    """Test suite for _parse_recommendations_json()"""
    
    def test_parse_valid_json_array(self):
        """Test parsing valid JSON array"""
        text = json.dumps([
            {"action": "refer", "priority": "urgent", "why": "test"}
        ])
        result = _parse_recommendations_json(text)
        
        assert result is not None
        assert len(result) == 1
        assert result[0]['action'] == 'refer'
    
    def test_parse_json_embedded_in_text(self):
        """Test parsing JSON embedded in text"""
        text = """Here are the recommendations:
        [
            {"action": "monitor", "priority": "follow-up", "why": "stable"}
        ]
        Additional notes follow."""
        
        result = _parse_recommendations_json(text)
        
        assert result is not None
        assert len(result) == 1
    
    def test_parse_invalid_json_returns_none(self):
        """Test that invalid JSON returns None"""
        text = "Not JSON at all"
        result = _parse_recommendations_json(text)
        
        assert result is None
    
    def test_parse_non_array_json_returns_none(self):
        """Test that non-array JSON returns None"""
        text = json.dumps({"action": "refer"})  # Object, not array
        result = _parse_recommendations_json(text)
        
        assert result is None


class TestValidateRecommendations:
    """Test suite for _validate_recommendations()"""
    
    def test_valid_recommendations_pass(self):
        """Test valid recommendations pass validation"""
        recs = [
            {
                "action": "refer",
                "priority": "urgent",
                "why": "Critical condition",
                "practical_note": "Call ambulance"
            }
        ]
        
        assert _validate_recommendations(recs) == True
    
    def test_missing_required_key_fails(self):
        """Test recommendations missing required key fail"""
        recs = [
            {
                "action": "refer",
                "priority": "urgent"
                # Missing 'why'
            }
        ]
        
        assert _validate_recommendations(recs) == False
    
    def test_invalid_priority_fails(self):
        """Test recommendations with invalid priority fail"""
        recs = [
            {
                "action": "refer",
                "priority": "super-urgent",  # Invalid
                "why": "test"
            }
        ]
        
        assert _validate_recommendations(recs) == False
    
    def test_non_string_values_fail(self):
        """Test recommendations with non-string values fail"""
        recs = [
            {
                "action": "refer",
                "priority": "urgent",
                "why": 123  # Should be string
            }
        ]
        
        assert _validate_recommendations(recs) == False
    
    def test_empty_list_fails(self):
        """Test empty list fails validation"""
        assert _validate_recommendations([]) == False
    
    def test_non_list_fails(self):
        """Test non-list input fails validation"""
        assert _validate_recommendations("not a list") == False
    
    def test_multiple_valid_recommendations_pass(self):
        """Test multiple valid recommendations pass"""
        recs = [
            {
                "action": "refer",
                "priority": "urgent",
                "why": "Critical"
            },
            {
                "action": "monitor",
                "priority": "follow-up",
                "why": "Stable"
            }
        ]
        
        assert _validate_recommendations(recs) == True


class TestGetFallbackRecommendations:
    """Test suite for _get_fallback_recommendations()"""
    
    def test_fallback_structure(self):
        """Test fallback has correct structure"""
        result = _get_fallback_recommendations()
        
        assert len(result) == 1
        assert 'action' in result[0]
        assert 'priority' in result[0]
        assert 'why' in result[0]
        assert 'practical_note' in result[0]
    
    def test_fallback_is_safety_first(self):
        """Test fallback is safety-first (refer urgent)"""
        result = _get_fallback_recommendations()
        
        assert result[0]['action'] == 'refer'
        assert result[0]['priority'] == 'urgent'
        assert 'insufficient_data' in result[0]['why']


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, '-v'])

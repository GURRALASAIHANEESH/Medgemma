"""
Confidence and Uncertainty Estimation Module
Provides structured confidence scoring for risk assessments
Author: PregnancyBridge Development Team
Version: 1.0.0
Date: 2026-02-04
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ConfidenceEstimator:
    """
    Estimate confidence in maternal risk assessments.
    
    Evaluates data quality, completeness, and consistency to provide
    transparent confidence metrics for clinical decision support.
    
    Confidence factors considered:
        - Temporal context (number of visits)
        - Symptom data completeness
        - Laboratory data availability
        - Risk category clarity
        - Rule convergence (multiple indicators)
        - Safety net activation status
    """
    
    # Confidence tier thresholds
    CONFIDENCE_THRESHOLDS = {
        'HIGH': 0.85,
        'MODERATE': 0.65,
        'LOW': 0.0
    }
    
    # Factor weights for overall confidence calculation
    FACTOR_WEIGHTS = {
        'temporal_context': 0.25,
        'symptom_clarity': 0.20,
        'lab_completeness': 0.20,
        'risk_clarity': 0.15,
        'rule_convergence': 0.10,
        'deterministic_override': 0.10
    }
    
    def __init__(self):
        """Initialize confidence estimator"""
        logger.info("ConfidenceEstimator initialized")
    
    def estimate_confidence(self,
                           risk_assessment: Dict,
                           visits: List[Dict],
                           symptoms: Optional[Dict] = None,
                           lab_flags: Optional[List[str]] = None) -> Dict:
        """
        Calculate confidence score and identify uncertainty sources.
        
        Args:
            risk_assessment: Risk assessment output from symptom_risk_engine
            visits: List of visit records
            symptoms: Symptom dictionary from symptom_intake
            lab_flags: Laboratory risk flags from lab_risk_analyzer
            
        Returns:
            Dictionary containing:
                - confidence_score: Float 0.0-1.0
                - confidence_tier: String (HIGH, MODERATE, LOW)
                - uncertainty_reason: Human-readable explanation
                - confidence_factors: Individual factor scores
                - data_quality_summary: Overall data quality assessment
        """
        factors = {}
        uncertainty_reasons = []
        
        # Factor 1: Temporal context quality
        visit_count = len(visits)
        temporal_score = self._assess_temporal_context(visit_count, visits)
        factors['temporal_context'] = temporal_score
        
        if visit_count == 1:
            uncertainty_reasons.append("Single visit assessment - no temporal trend available")
        elif visit_count == 2:
            uncertainty_reasons.append("Limited temporal data - only 2 visits analyzed")
        
        # Factor 2: Symptom data quality
        symptom_score = self._assess_symptom_quality(symptoms)
        factors['symptom_clarity'] = symptom_score
        
        if symptom_score < 0.7:
            if not symptoms or symptoms.get('symptom_count', 0) == 0:
                uncertainty_reasons.append("No symptoms reported - clinical picture may be incomplete")
            else:
                uncertainty_reasons.append("Limited symptom data captured")
        
        # Factor 3: Laboratory data completeness
        lab_score = self._assess_lab_completeness(visits, lab_flags)
        factors['lab_completeness'] = lab_score
        
        if lab_score < 0.7:
            uncertainty_reasons.append("Incomplete laboratory data - some parameters not measured")
        
        # Factor 4: Risk category clarity
        risk_score = self._assess_risk_clarity(risk_assessment)
        factors['risk_clarity'] = risk_score
        
        if risk_score < 0.8:
            if risk_assessment.get('risk_category') == 'MODERATE':
                uncertainty_reasons.append("Borderline risk category - close to threshold")
            elif risk_assessment.get('risk_category') == 'UNKNOWN':
                uncertainty_reasons.append("Risk category could not be determined")
        
        # Factor 5: Rule convergence (multiple indicators)
        convergence_score = self._assess_rule_convergence(risk_assessment, symptoms, lab_flags)
        factors['rule_convergence'] = convergence_score
        
        if convergence_score < 0.7:
            uncertainty_reasons.append("Single risk indicator - additional confirmatory data would increase confidence")
        
        # Factor 6: Deterministic override presence
        override_score = self._assess_deterministic_override(risk_assessment)
        factors['deterministic_override'] = override_score
        
        # Calculate weighted overall confidence score
        confidence_score = self._calculate_weighted_score(factors)
        
        # Determine confidence tier
        confidence_tier = self._assign_confidence_tier(confidence_score)
        
        # Generate comprehensive uncertainty explanation
        uncertainty_reason = self._generate_uncertainty_explanation(
            uncertainty_reasons, confidence_tier, factors
        )
        
        # Data quality summary
        data_quality = self._assess_data_quality(factors)
        
        return {
            'confidence_score': round(confidence_score, 2),
            'confidence_tier': confidence_tier,
            'uncertainty_reason': uncertainty_reason,
            'confidence_factors': factors,
            'data_quality_summary': data_quality
        }
    
    def _assess_temporal_context(self, visit_count: int, visits: List[Dict]) -> float:
        """
        Assess temporal context quality.
        
        Args:
            visit_count: Number of visits
            visits: Visit records
            
        Returns:
            Score 0.0-1.0
        """
        if visit_count >= 3:
            # Check visit spacing
            if self._has_adequate_spacing(visits):
                return 1.0
            else:
                return 0.9  # Good count but poor spacing
        elif visit_count == 2:
            return 0.7
        else:
            return 0.4
    
    def _has_adequate_spacing(self, visits: List[Dict]) -> bool:
        """
        Check if visits are adequately spaced for trend detection.
        
        Adequate spacing: At least 1 week between visits
        """
        if len(visits) < 2:
            return True
        
        dates = [v.get('date') for v in visits if v.get('date')]
        if len(dates) < 2:
            return True  # Cannot assess without dates
        
        # Simple heuristic: check if visits span reasonable timeframe
        return True  # Simplified for now
    
    def _assess_symptom_quality(self, symptoms: Optional[Dict]) -> float:
        """
        Assess symptom data quality.
        
        Args:
            symptoms: Symptom dictionary
            
        Returns:
            Score 0.0-1.0
        """
        if not symptoms:
            return 0.5
        
        symptom_count = symptoms.get('symptom_count', 0)
        
        if symptom_count == 0:
            return 0.5
        elif symptom_count >= 3:
            # Multiple symptoms with category information
            if symptoms.get('has_neurological') or symptoms.get('has_respiratory'):
                return 1.0
            else:
                return 0.9
        elif symptom_count >= 1:
            return 0.8
        else:
            return 0.6
    
    def _assess_lab_completeness(self, 
                                 visits: List[Dict],
                                 lab_flags: Optional[List[str]]) -> float:
        """
        Assess laboratory data completeness.
        
        Args:
            visits: Visit records
            lab_flags: Lab risk flags
            
        Returns:
            Score 0.0-1.0
        """
        if not visits:
            return 0.5
        
        latest = visits[-1]
        
        # Key lab parameters
        key_params = ['hemoglobin', 'bp', 'proteinuria']
        extended_params = ['platelets', 'wbc', 'rbc']
        
        # Count available key parameters
        available_key = sum(1 for p in key_params if latest.get(p) is not None)
        available_extended = sum(1 for p in extended_params if latest.get(p) is not None)
        
        key_completeness = available_key / len(key_params)
        extended_completeness = available_extended / len(extended_params)
        
        # Weight key parameters more heavily
        overall_score = (key_completeness * 0.7) + (extended_completeness * 0.3)
        
        # Bonus if lab flags present (indicates detailed analysis)
        if lab_flags and len(lab_flags) > 0:
            overall_score = min(overall_score + 0.1, 1.0)
        
        return overall_score
    
    def _assess_risk_clarity(self, risk_assessment: Dict) -> float:
        """
        Assess risk category clarity.
        
        Args:
            risk_assessment: Risk assessment output
            
        Returns:
            Score 0.0-1.0
        """
        risk_cat = risk_assessment.get('risk_category', 'UNKNOWN')
        
        if risk_cat == 'HIGH':
            # Clear high risk
            return 1.0
        elif risk_cat == 'LOW':
            # Clear low risk
            return 1.0
        elif risk_cat == 'MODERATE':
            # Borderline case
            return 0.7
        else:
            # Unknown or unclear
            return 0.3
    
    def _assess_rule_convergence(self,
                                risk_assessment: Dict,
                                symptoms: Optional[Dict],
                                lab_flags: Optional[List[str]]) -> float:
        """
        Assess convergence of multiple risk indicators.
        
        Higher score when multiple independent sources agree.
        
        Args:
            risk_assessment: Risk assessment output
            symptoms: Symptom data
            lab_flags: Lab flags
            
        Returns:
            Score 0.0-1.0
        """
        indicator_count = 0
        
        # Check trigger reason for multiple conditions
        trigger = risk_assessment.get('trigger_reason', '')
        if 'WITH' in trigger or 'AND' in trigger:
            indicator_count += 2  # Multiple conditions in trigger
        else:
            indicator_count += 1
        
        # Symptom presence
        if symptoms and symptoms.get('symptom_count', 0) > 0:
            indicator_count += 1
        
        # Lab abnormalities
        if lab_flags and len(lab_flags) >= 2:
            indicator_count += 1
        
        # Temporal progression
        if 'progressive' in trigger.lower() or 'worsening' in trigger.lower():
            indicator_count += 1
        
        # Score based on convergence
        if indicator_count >= 4:
            return 1.0
        elif indicator_count == 3:
            return 0.9
        elif indicator_count == 2:
            return 0.7
        else:
            return 0.5
    
    def _assess_deterministic_override(self, risk_assessment: Dict) -> float:
        """
        Assess if deterministic safety nets were triggered.
        
        Higher confidence when safety rules activate.
        
        Args:
            risk_assessment: Risk assessment output
            
        Returns:
            Score 0.0-1.0
        """
        if risk_assessment.get('safety_net_triggered'):
            return 1.0
        else:
            return 0.8
    
    def _calculate_weighted_score(self, factors: Dict[str, float]) -> float:
        """
        Calculate weighted overall confidence score.
        
        Args:
            factors: Dictionary of factor scores
            
        Returns:
            Weighted score 0.0-1.0
        """
        weighted_sum = 0.0
        total_weight = 0.0
        
        for factor_name, weight in self.FACTOR_WEIGHTS.items():
            if factor_name in factors:
                weighted_sum += factors[factor_name] * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.5
        
        return weighted_sum / total_weight
    
    def _assign_confidence_tier(self, score: float) -> str:
        """
        Assign confidence tier based on score.
        
        Args:
            score: Confidence score 0.0-1.0
            
        Returns:
            Tier string (HIGH, MODERATE, LOW)
        """
        if score >= self.CONFIDENCE_THRESHOLDS['HIGH']:
            return 'HIGH'
        elif score >= self.CONFIDENCE_THRESHOLDS['MODERATE']:
            return 'MODERATE'
        else:
            return 'LOW'
    
    def _generate_uncertainty_explanation(self,
                                         uncertainty_reasons: List[str],
                                         confidence_tier: str,
                                         factors: Dict[str, float]) -> str:
        """
        Generate human-readable uncertainty explanation.
        
        Args:
            uncertainty_reasons: List of specific uncertainty sources
            confidence_tier: Overall confidence tier
            factors: Individual factor scores
            
        Returns:
            Explanation string
        """
        if confidence_tier == 'HIGH' and not uncertainty_reasons:
            return "High-quality multi-visit data with clear risk indicators and complete laboratory workup"
        
        if not uncertainty_reasons:
            return "Adequate data quality with clear clinical risk indicators"
        
        # Primary uncertainty
        explanation_parts = []
        
        if len(uncertainty_reasons) == 1:
            explanation_parts.append(f"Primary uncertainty: {uncertainty_reasons[0]}")
        else:
            explanation_parts.append(f"Uncertainty sources: {'; '.join(uncertainty_reasons[:2])}")
        
        # Recommendation based on confidence
        if confidence_tier == 'LOW':
            explanation_parts.append("Recommend obtaining additional clinical data to improve confidence")
        elif confidence_tier == 'MODERATE':
            explanation_parts.append("Confidence adequate for clinical decision-making with appropriate caution")
        
        return ". ".join(explanation_parts)
    
    def _assess_data_quality(self, factors: Dict[str, float]) -> str:
        """
        Provide overall data quality summary.
        
        Args:
            factors: Individual factor scores
            
        Returns:
            Quality summary string
        """
        avg_score = sum(factors.values()) / len(factors) if factors else 0
        
        if avg_score >= 0.9:
            return "Excellent data quality across all parameters"
        elif avg_score >= 0.75:
            return "Good data quality with minor gaps"
        elif avg_score >= 0.6:
            return "Adequate data quality for risk assessment"
        else:
            return "Limited data quality - additional information recommended"
    
    def compare_confidence_over_time(self, 
                                    confidence_history: List[Dict]) -> Dict:
        """
        Analyze confidence trends over multiple assessments.
        
        Args:
            confidence_history: List of confidence estimation results
            
        Returns:
            Trend analysis
        """
        if len(confidence_history) < 2:
            return {
                'trend': 'insufficient_data',
                'improvement': None,
                'recommendation': 'Obtain at least 2 assessments for trend analysis'
            }
        
        scores = [c['confidence_score'] for c in confidence_history]
        
        improvement = scores[-1] - scores[0]
        
        if improvement > 0.1:
            trend = 'improving'
            recommendation = "Data quality improving over time"
        elif improvement < -0.1:
            trend = 'declining'
            recommendation = "Data quality declining - review data collection procedures"
        else:
            trend = 'stable'
            recommendation = "Confidence stable across assessments"
        
        return {
            'trend': trend,
            'improvement': round(improvement, 2),
            'recommendation': recommendation,
            'score_history': scores
        }


# Singleton instance
_confidence_estimator_instance = None


def get_confidence_estimator() -> ConfidenceEstimator:
    """
    Get singleton instance of ConfidenceEstimator.
    
    Returns:
        ConfidenceEstimator instance
    """
    global _confidence_estimator_instance
    if _confidence_estimator_instance is None:
        _confidence_estimator_instance = ConfidenceEstimator()
    return _confidence_estimator_instance


if __name__ == "__main__":
    # Self-test
    print("\nConfidenceEstimator Self-Test")
    print("=" * 70)
    
    estimator = get_confidence_estimator()
    
    # Test case 1: High confidence scenario
    print("\nTest Case 1: High Confidence Scenario")
    print("-" * 70)
    
    test_risk_high = {
        'risk_category': 'HIGH',
        'referral_required': True,
        'trigger_reason': 'Elevated BP 150/95 WITH proteinuria +2 AND neurological symptoms',
        'safety_net_triggered': True
    }
    
    test_visits_high = [
        {'date': '2026-01-10', 'gestational_age': 32, 'bp': {'systolic': 138, 'diastolic': 88},
         'hemoglobin': 11.2, 'platelets': 150000, 'proteinuria': 'trace'},
        {'date': '2026-01-24', 'gestational_age': 34, 'bp': {'systolic': 145, 'diastolic': 92},
         'hemoglobin': 11.0, 'platelets': 140000, 'proteinuria': '+1'},
        {'date': '2026-02-04', 'gestational_age': 36, 'bp': {'systolic': 150, 'diastolic': 95},
         'hemoglobin': 10.8, 'platelets': 130000, 'proteinuria': '+2'}
    ]
    
    test_symptoms_high = {
        'symptom_count': 3,
        'present_symptoms': ['headache', 'blurred_vision', 'pedal_edema'],
        'has_neurological': True
    }
    
    test_lab_flags_high = [
        'Moderate proteinuria (+2) - preeclampsia risk',
        'Borderline platelets - monitor closely',
        'MULTI-PARAMETER ABNORMALITY'
    ]
    
    result_high = estimator.estimate_confidence(
        test_risk_high, test_visits_high, test_symptoms_high, test_lab_flags_high
    )
    
    print(f"Confidence Score: {result_high['confidence_score']} ({result_high['confidence_tier']})")
    print(f"Uncertainty: {result_high['uncertainty_reason']}")
    print(f"Data Quality: {result_high['data_quality_summary']}")
    print("\nFactor Breakdown:")
    for factor, score in result_high['confidence_factors'].items():
        print(f"  {factor}: {score:.2f}")
    
    # Test case 2: Low confidence scenario
    print("\n\nTest Case 2: Low Confidence Scenario")
    print("-" * 70)
    
    test_risk_low = {
        'risk_category': 'MODERATE',
        'referral_required': False,
        'trigger_reason': 'Borderline BP elevation'
    }
    
    test_visits_low = [
        {'date': '2026-02-04', 'gestational_age': 36, 'bp': {'systolic': 142, 'diastolic': 88}}
    ]
    
    result_low = estimator.estimate_confidence(
        test_risk_low, test_visits_low, None, None
    )
    
    print(f"Confidence Score: {result_low['confidence_score']} ({result_low['confidence_tier']})")
    print(f"Uncertainty: {result_low['uncertainty_reason']}")
    print(f"Data Quality: {result_low['data_quality_summary']}")
    print("\nFactor Breakdown:")
    for factor, score in result_low['confidence_factors'].items():
        print(f"  {factor}: {score:.2f}")
    
    print("\n" + "=" * 70)
    print("Self-test complete")

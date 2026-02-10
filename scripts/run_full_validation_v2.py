"""
Full Validation Suite v2
Comprehensive testing for production requirements
Author: PregnancyBridge Development Team
Version: 2.0.0
Date: 2026-02-04
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from competition_pipeline_v2 import CompetitionPipelineV2
import json
import logging
from datetime import datetime
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationSuiteV2:
    """
    Production validation test suite.
    
    Tests required by competition specification:
    1. Recent lab test (≤7 days) - no warnings
    2. Old lab test (45-75 days) - warning + confidence penalty
    3. Too-old test (>90 days) - retest recommendation
    4. Provenance test - explanation source tracking
    5. Translation parity - no English in translations
    """
    
    def __init__(self):
        """Initialize validation suite."""
        logger.info("=" * 70)
        logger.info("PregnancyBridge Validation Suite v2.0")
        logger.info("=" * 70)
        
        self.pipeline = CompetitionPipelineV2(use_medgemma=False)  # Faster without MedGemma
        self.test_results = []
        
    def run_all_tests(self) -> Dict:
        """
        Run all validation tests.
        
        Returns:
            Complete test results dictionary
        """
        logger.info("\n" + "=" * 70)
        logger.info("Starting Validation Tests")
        logger.info("=" * 70)
        
        # Test 1: Recent lab (7 days)
        logger.info("\n>>> TEST 1: Recent Lab (7 days)")
        test1_result = self.test_recent_lab()
        self.test_results.append(test1_result)
        self._print_test_result(1, test1_result)
        
        # Test 2: Old lab (60 days)
        logger.info("\n>>> TEST 2: Old Lab (60 days)")
        test2_result = self.test_old_lab()
        self.test_results.append(test2_result)
        self._print_test_result(2, test2_result)
        
        # Test 3: Too-old lab (100 days)
        logger.info("\n>>> TEST 3: Too-Old Lab (100 days)")
        test3_result = self.test_too_old_lab()
        self.test_results.append(test3_result)
        self._print_test_result(3, test3_result)
        
        # Test 4: Provenance tracking
        logger.info("\n>>> TEST 4: Provenance Tracking")
        test4_result = self.test_provenance()
        self.test_results.append(test4_result)
        self._print_test_result(4, test4_result)
        
        # Test 5: Translation parity
        logger.info("\n>>> TEST 5: Translation Parity")
        test5_result = self.test_translation_parity()
        self.test_results.append(test5_result)
        self._print_test_result(5, test5_result)
        
        # Test 6: Schema v2 compliance
        logger.info("\n>>> TEST 6: Schema v2 Compliance")
        test6_result = self.test_schema_compliance()
        self.test_results.append(test6_result)
        self._print_test_result(6, test6_result)
        
        # Test 7: Evidence summary generation
        logger.info("\n>>> TEST 7: Evidence Summary")
        test7_result = self.test_evidence_summary()
        self.test_results.append(test7_result)
        self._print_test_result(7, test7_result)
        
        # Test 8: Confidence penalty on old labs
        logger.info("\n>>> TEST 8: Confidence Penalty")
        test8_result = self.test_confidence_penalty()
        self.test_results.append(test8_result)
        self._print_test_result(8, test8_result)
        
        # Compile summary
        summary = self._compile_summary()
        
        logger.info("\n" + "=" * 70)
        logger.info("Validation Complete")
        logger.info("=" * 70)
        logger.info(f"Tests passed: {summary['passed']}/{summary['total']}")
        logger.info(f"Tests failed: {summary['failed']}/{summary['total']}")
        
        if summary['failed'] == 0:
            logger.info("✓ ALL TESTS PASSED - System ready for competition")
        else:
            logger.error(f"✗ {summary['failed']} TEST(S) FAILED - Review issues")
        
        return summary
    
    def test_recent_lab(self) -> Dict:
        """
        Test 1: Recent lab (≤7 days) should have no warnings.
        """
        test_case = self._create_test_case(lab_age_days=5)
        
        result = self.pipeline.process_case(
            case_id='TEST_RECENT_LAB',
            visits=test_case['visits'],
            symptoms=test_case['symptoms'],
            lab_report_date='2026-01-30',
            reference_date='2026-02-04'
        )
        
        # Assertions
        assertions = []
        
        # Lab age should be 5 days
        assertions.append({
            'check': 'lab_age_days == 5',
            'expected': 5,
            'actual': result['lab_age_days'],
            'passed': result['lab_age_days'] == 5
        })
        
        # No lab age warning
        assertions.append({
            'check': 'lab_age_warning is None',
            'expected': None,
            'actual': result['lab_age_warning'],
            'passed': result['lab_age_warning'] is None
        })
        
        # Confidence not penalized
        assertions.append({
            'check': 'confidence_score >= 0.70',
            'expected': '>=0.70',
            'actual': result['confidence_score'],
            'passed': result['confidence_score'] >= 0.70
        })
        
        # Lab freshness factor should be high
        lab_freshness = result['confidence_factors'].get('lab_age_freshness', 0)
        assertions.append({
            'check': 'lab_age_freshness >= 0.90',
            'expected': '>=0.90',
            'actual': lab_freshness,
            'passed': lab_freshness >= 0.90
        })
        
        all_passed = all(a['passed'] for a in assertions)
        
        return {
            'test_name': 'Recent Lab Test (≤7 days)',
            'test_id': 'TEST_1_RECENT_LAB',
            'passed': all_passed,
            'assertions': assertions,
            'output': result
        }
    
    def test_old_lab(self) -> Dict:
        """
        Test 2: Old lab (45-75 days) should trigger warning.
        """
        test_case = self._create_test_case(lab_age_days=60)
        
        result = self.pipeline.process_case(
            case_id='TEST_OLD_LAB',
            visits=test_case['visits'],
            symptoms=test_case['symptoms'],
            lab_report_date='2025-12-06',
            reference_date='2026-02-04'
        )
        
        # Assertions
        assertions = []
        
        # Lab age should be 60 days
        assertions.append({
            'check': 'lab_age_days == 60',
            'expected': 60,
            'actual': result['lab_age_days'],
            'passed': result['lab_age_days'] == 60
        })
        
        # Should have old_but_usable warning
        assertions.append({
            'check': 'lab_age_warning == "old_but_usable"',
            'expected': 'old_but_usable',
            'actual': result['lab_age_warning'],
            'passed': result['lab_age_warning'] == 'old_but_usable'
        })
        
        # Confidence should be penalized
        lab_freshness = result['confidence_factors'].get('lab_age_freshness', 1.0)
        assertions.append({
            'check': 'lab_age_freshness < 0.70',
            'expected': '<0.70',
            'actual': lab_freshness,
            'passed': lab_freshness < 0.70
        })
        
        # Uncertainty reason should mention lab age
        uncertainty = result.get('uncertainty_reason', '').lower()
        assertions.append({
            'check': '"lab" in uncertainty_reason',
            'expected': 'contains "lab"',
            'actual': uncertainty[:50],
            'passed': 'lab' in uncertainty
        })
        
        # ASHA explanation should have lab warning note
        asha_text = result.get('asha_explanation', '')
        assertions.append({
            'check': 'Lab warning in ASHA text',
            'expected': 'contains warning',
            'actual': 'Lab report is' in asha_text or 'month old' in asha_text,
            'passed': 'Lab report' in asha_text or 'month old' in asha_text or 'old' in asha_text.lower()
        })
        
        all_passed = all(a['passed'] for a in assertions)
        
        return {
            'test_name': 'Old Lab Test (45-75 days)',
            'test_id': 'TEST_2_OLD_LAB',
            'passed': all_passed,
            'assertions': assertions,
            'output': result
        }
    
    def test_too_old_lab(self) -> Dict:
        """
        Test 3: Too-old lab (>90 days) should recommend retest.
        """
        test_case = self._create_test_case(lab_age_days=100)
        
        result = self.pipeline.process_case(
            case_id='TEST_TOO_OLD_LAB',
            visits=test_case['visits'],
            symptoms=test_case['symptoms'],
            lab_report_date='2025-10-27',
            reference_date='2026-02-04'
        )
        
        # Assertions
        assertions = []
        
        # Lab age should be 100 days
        assertions.append({
            'check': 'lab_age_days == 100',
            'expected': 100,
            'actual': result['lab_age_days'],
            'passed': result['lab_age_days'] == 100
        })
        
        # Should have too_old_recommend_repeat warning
        assertions.append({
            'check': 'lab_age_warning == "too_old_recommend_repeat"',
            'expected': 'too_old_recommend_repeat',
            'actual': result['lab_age_warning'],
            'passed': result['lab_age_warning'] == 'too_old_recommend_repeat'
        })
        
        # Lab freshness should be very low
        lab_freshness = result['confidence_factors'].get('lab_age_freshness', 1.0)
        assertions.append({
            'check': 'lab_age_freshness <= 0.30',
            'expected': '<=0.30',
            'actual': lab_freshness,
            'passed': lab_freshness <= 0.30
        })
        
        # Uncertainty should mention very old lab
        uncertainty = result.get('uncertainty_reason', '').lower()
        assertions.append({
            'check': 'Mentions >90 days',
            'expected': 'contains "90" or "very old"',
            'actual': uncertainty[:60],
            'passed': '90' in uncertainty or 'very old' in uncertainty or 'too old' in uncertainty
        })
        
        all_passed = all(a['passed'] for a in assertions)
        
        return {
            'test_name': 'Too-Old Lab Test (>90 days)',
            'test_id': 'TEST_3_TOO_OLD_LAB',
            'passed': all_passed,
            'assertions': assertions,
            'output': result
        }
    
    def test_provenance(self) -> Dict:
        """
        Test 4: Provenance tracking verification.
        """
        test_case = self._create_test_case(lab_age_days=10)
        
        result = self.pipeline.process_case(
            case_id='TEST_PROVENANCE',
            visits=test_case['visits'],
            symptoms=test_case['symptoms'],
            lab_report_date='2026-01-25',
            lab_report_image='test_lab.jpg',
            anc_card_image='test_anc.jpg',
            reference_date='2026-02-04'
        )
        
        # Assertions
        assertions = []
        provenance = result.get('provenance', {})
        input_sources = result.get('input_sources', {})
        
        # Risk authority must be rule_engine
        assertions.append({
            'check': 'risk_authority == "rule_engine"',
            'expected': 'rule_engine',
            'actual': provenance.get('risk_authority'),
            'passed': provenance.get('risk_authority') == 'rule_engine'
        })
        
        # Explanation source must be valid
        valid_sources = ['medgemma', 'fallback_template']
        assertions.append({
            'check': 'explanation_source in valid_sources',
            'expected': 'medgemma or fallback_template',
            'actual': provenance.get('explanation_source'),
            'passed': provenance.get('explanation_source') in valid_sources
        })
        
        # Timestamp must exist
        assertions.append({
            'check': 'timestamp_utc exists',
            'expected': 'ISO timestamp',
            'actual': provenance.get('timestamp_utc', 'MISSING')[:20],
            'passed': 'timestamp_utc' in provenance and provenance['timestamp_utc'] is not None
        })
        
        # Explanation generated flag
        assertions.append({
            'check': 'explanation_generated is bool',
            'expected': 'True or False',
            'actual': provenance.get('explanation_generated'),
            'passed': isinstance(provenance.get('explanation_generated'), bool)
        })
        
        # Input sources populated
        assertions.append({
            'check': 'input_sources has lab_report_image',
            'expected': 'test_lab.jpg',
            'actual': input_sources.get('lab_report_image'),
            'passed': input_sources.get('lab_report_image') == 'test_lab.jpg'
        })
        
        assertions.append({
            'check': 'input_sources has lab_report_date',
            'expected': '2026-01-25',
            'actual': input_sources.get('lab_report_date'),
            'passed': input_sources.get('lab_report_date') == '2026-01-25'
        })
        
        all_passed = all(a['passed'] for a in assertions)
        
        return {
            'test_name': 'Provenance Tracking',
            'test_id': 'TEST_4_PROVENANCE',
            'passed': all_passed,
            'assertions': assertions,
            'output': result
        }
    
    def test_translation_parity(self) -> Dict:
        """
        Test 5: Translation parity - no English in target languages.
        """
        test_case = self._create_test_case(lab_age_days=10)
        
        result = self.pipeline.process_case(
            case_id='TEST_TRANSLATION',
            visits=test_case['visits'],
            symptoms=test_case['symptoms'],
            lab_report_date='2026-01-25',
            reference_date='2026-02-04'
        )
        
        # Assertions
        assertions = []
        translations = result.get('translations', {})
        
        hindi = translations.get('hindi', '')
        telugu = translations.get('telugu', '')
        
        # Check for common English words (should not appear)
        english_markers = ['blood', 'pressure', 'hospital', 'doctor', 'mother', 'baby', 'urgent', 'test']
        
        hindi_has_english = any(marker in hindi.lower() for marker in english_markers)
        telugu_has_english = any(marker in telugu.lower() for marker in english_markers)
        
        assertions.append({
            'check': 'Hindi translation has no English',
            'expected': 'No English markers',
            'actual': f"Contains English: {hindi_has_english}",
            'passed': not hindi_has_english
        })
        
        assertions.append({
            'check': 'Telugu translation has no English',
            'expected': 'No English markers',
            'actual': f"Contains English: {telugu_has_english}",
            'passed': not telugu_has_english
        })
        
        # Hindi should use Devanagari script
        hindi_has_devanagari = any('\u0900' <= c <= '\u097F' for c in hindi)
        assertions.append({
            'check': 'Hindi uses Devanagari script',
            'expected': 'Contains Devanagari',
            'actual': f"Has Devanagari: {hindi_has_devanagari}",
            'passed': hindi_has_devanagari
        })
        
        # Telugu should use Telugu script
        telugu_has_telugu_script = any('\u0C00' <= c <= '\u0C7F' for c in telugu)
        assertions.append({
            'check': 'Telugu uses Telugu script',
            'expected': 'Contains Telugu script',
            'actual': f"Has Telugu script: {telugu_has_telugu_script}",
            'passed': telugu_has_telugu_script
        })
        
        # Translation fallback flag
        assertions.append({
            'check': 'translation_fallback_flag is False',
            'expected': False,
            'actual': translations.get('translation_fallback_flag'),
            'passed': translations.get('translation_fallback_flag') == False
        })
        
        all_passed = all(a['passed'] for a in assertions)
        
        return {
            'test_name': 'Translation Parity',
            'test_id': 'TEST_5_TRANSLATION',
            'passed': all_passed,
            'assertions': assertions,
            'output': result
        }
    
    def test_schema_compliance(self) -> Dict:
        """
        Test 6: Schema v2 compliance.
        """
        test_case = self._create_test_case(lab_age_days=15)
        
        result = self.pipeline.process_case(
            case_id='TEST_SCHEMA',
            visits=test_case['visits'],
            symptoms=test_case['symptoms'],
            lab_report_date='2026-01-20',
            reference_date='2026-02-04'
        )
        
        # Required top-level fields
        required_fields = [
            'case_id', 'input_sources', 'provenance', 'risk_category',
            'referral_required', 'trigger_reason', 'evidence_items',
            'confidence_score', 'uncertainty_reason', 'clinical_explanation',
            'asha_explanation', 'translations'
        ]
        
        assertions = []
        
        for field in required_fields:
            assertions.append({
                'check': f'Field "{field}" exists',
                'expected': 'Present',
                'actual': 'Present' if field in result else 'MISSING',
                'passed': field in result
            })
        
        # Check types
        assertions.append({
            'check': 'evidence_items is list',
            'expected': 'list',
            'actual': type(result.get('evidence_items')).__name__,
            'passed': isinstance(result.get('evidence_items'), list)
        })
        
        assertions.append({
            'check': 'confidence_score is number',
            'expected': 'float',
            'actual': type(result.get('confidence_score')).__name__,
            'passed': isinstance(result.get('confidence_score'), (int, float))
        })
        
        assertions.append({
            'check': 'translations is dict',
            'expected': 'dict',
            'actual': type(result.get('translations')).__name__,
            'passed': isinstance(result.get('translations'), dict)
        })
        
        all_passed = all(a['passed'] for a in assertions)
        
        return {
            'test_name': 'Schema v2 Compliance',
            'test_id': 'TEST_6_SCHEMA',
            'passed': all_passed,
            'assertions': assertions,
            'output': result
        }
    
    def test_evidence_summary(self) -> Dict:
        """
        Test 7: Evidence summary generation.
        """
        test_case = self._create_test_case(lab_age_days=10)
        
        result = self.pipeline.process_case(
            case_id='TEST_EVIDENCE',
            visits=test_case['visits'],
            symptoms=test_case['symptoms'],
            lab_report_date='2026-01-25',
            reference_date='2026-02-04'
        )
        
        assertions = []
        
        evidence_summary = result.get('evidence_summary', [])
        evidence_items = result.get('evidence_items', [])
        
        # Evidence summary should be non-empty
        assertions.append({
            'check': 'evidence_summary exists and not empty',
            'expected': 'List with items',
            'actual': f"{len(evidence_summary)} items",
            'passed': len(evidence_summary) > 0
        })
        
        # Evidence items should be non-empty
        assertions.append({
            'check': 'evidence_items exists and not empty',
            'expected': 'List with items',
            'actual': f"{len(evidence_items)} items",
            'passed': len(evidence_items) > 0
        })
        
        # Evidence summary should have ≤3 items
        assertions.append({
            'check': 'evidence_summary has ≤3 items',
            'expected': '≤3',
            'actual': len(evidence_summary),
            'passed': len(evidence_summary) <= 3
        })
        
        # Evidence items should have proper structure
        if evidence_items:
            first_item = evidence_items[0]
            assertions.append({
                'check': 'evidence_item has "type" field',
                'expected': 'Present',
                'actual': 'type' in first_item,
                'passed': 'type' in first_item
            })
            
            assertions.append({
                'check': 'evidence_item has "name" field',
                'expected': 'Present',
                'actual': 'name' in first_item,
                'passed': 'name' in first_item
            })
        
        all_passed = all(a['passed'] for a in assertions)
        
        return {
            'test_name': 'Evidence Summary Generation',
            'test_id': 'TEST_7_EVIDENCE',
            'passed': all_passed,
            'assertions': assertions,
            'output': result
        }
    
    def test_confidence_penalty(self) -> Dict:
        """
        Test 8: Confidence penalty on old labs.
        """
        # Test with fresh lab
        test_case_fresh = self._create_test_case(lab_age_days=5)
        result_fresh = self.pipeline.process_case(
            case_id='TEST_CONFIDENCE_FRESH',
            visits=test_case_fresh['visits'],
            symptoms=test_case_fresh['symptoms'],
            lab_report_date='2026-01-30',
            reference_date='2026-02-04'
        )
        
        # Test with old lab
        test_case_old = self._create_test_case(lab_age_days=100)
        result_old = self.pipeline.process_case(
            case_id='TEST_CONFIDENCE_OLD',
            visits=test_case_old['visits'],
            symptoms=test_case_old['symptoms'],
            lab_report_date='2025-10-27',
            reference_date='2026-02-04'
        )
        
        assertions = []
        
        conf_fresh = result_fresh['confidence_score']
        conf_old = result_old['confidence_score']
        
        freshness_fresh = result_fresh['confidence_factors']['lab_age_freshness']
        freshness_old = result_old['confidence_factors']['lab_age_freshness']
        
        # Fresh lab should have higher confidence
        assertions.append({
            'check': 'Fresh lab confidence > Old lab confidence',
            'expected': 'Fresh > Old',
            'actual': f"Fresh={conf_fresh}, Old={conf_old}",
            'passed': conf_fresh > conf_old
        })
        
        # Fresh lab freshness should be higher
        assertions.append({
            'check': 'Fresh lab freshness factor > Old lab',
            'expected': 'Fresh > Old',
            'actual': f"Fresh={freshness_fresh}, Old={freshness_old}",
            'passed': freshness_fresh > freshness_old
        })
        
        # Old lab freshness should be ≤0.30
        assertions.append({
            'check': 'Old lab freshness ≤0.30',
            'expected': '≤0.30',
            'actual': freshness_old,
            'passed': freshness_old <= 0.30
        })
        
        all_passed = all(a['passed'] for a in assertions)
        
        return {
            'test_name': 'Confidence Penalty on Old Labs',
            'test_id': 'TEST_8_CONFIDENCE_PENALTY',
            'passed': all_passed,
            'assertions': assertions,
            'output': {'fresh': result_fresh, 'old': result_old}
        }
    
    def _create_test_case(self, lab_age_days: int) -> Dict:
        """
        Create standardized test case.
        
        Args:
            lab_age_days: Age of lab for this test
            
        Returns:
            Test case dictionary with visits and symptoms
        """
        visits = [
            {
                'date': '2026-01-10',
                'gestational_age': 32,
                'bp': {'systolic': 128, 'diastolic': 84},
                'hemoglobin': 11.2,
                'platelets': 180000,
                'proteinuria': 'trace',
                'wbc': 8500
            },
            {
                'date': '2026-02-04',
                'gestational_age': 36,
                'bp': {'systolic': 150, 'diastolic': 96},
                'hemoglobin': 10.5,
                'platelets': 85000,
                'proteinuria': '+2',
                'wbc': 16500
            }
        ]
        
        symptoms = {
            'symptom_count': 2,
            'present_symptoms': ['headache', 'blurred_vision'],
            'has_neurological': True,
            'categories': {'neurological': ['headache', 'blurred_vision']}
        }
        
        return {'visits': visits, 'symptoms': symptoms}
    
    def _print_test_result(self, test_num: int, result: Dict):
        """Print formatted test result."""
        status = "✓ PASS" if result['passed'] else "✗ FAIL"
        logger.info(f"Test {test_num}: {result['test_name']} - {status}")
        
        if not result['passed']:
            logger.error("Failed assertions:")
            for assertion in result['assertions']:
                if not assertion['passed']:
                    logger.error(f"  - {assertion['check']}")
                    logger.error(f"    Expected: {assertion['expected']}")
                    logger.error(f"    Actual: {assertion['actual']}")
    
    def _compile_summary(self) -> Dict:
        """Compile validation summary."""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        
        summary = {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': round((passed / total) * 100, 1) if total > 0 else 0,
            'timestamp': datetime.now().isoformat(),
            'test_results': self.test_results
        }
        
        return summary
    
    def save_results(self, filename: str):
        """Save test results to JSON file."""
        summary = self._compile_summary()
        
        output_path = Path(filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Results saved: {output_path.absolute()}")


# Main execution
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("PregnancyBridge Validation Suite v2.0")
    print("Running comprehensive production tests...")
    print("=" * 70)
    
    suite = ValidationSuiteV2()
    summary = suite.run_all_tests()
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_filename = f'validation_results_v2_{timestamp}.json'
    suite.save_results(results_filename)
    
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Total tests: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass rate: {summary['pass_rate']}%")
    print("=" * 70)
    
    if summary['failed'] == 0:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("System is READY for competition submission")
    else:
        print(f"\n✗✗✗ {summary['failed']} TEST(S) FAILED ✗✗✗")
        print("Review failed tests before submission")
    
    print("\n" + "=" * 70)

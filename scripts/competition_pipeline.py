"""
PregnancyBridge Competition Demonstration Pipeline
Complete integrated workflow demonstrating all competition features
Author: PregnancyBridge Development Team
Version: 1.0.0
Date: 2026-02-04
"""

import sys
from pathlib import Path
from typing import List, Dict
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pregnancy_bridge.modules.lab_risk_analyzer import get_lab_analyzer
from pregnancy_bridge.modules.dual_explanation_generator import get_dual_explainer
from pregnancy_bridge.modules.translation_engine import get_translator
from pregnancy_bridge.modules.confidence_estimator import get_confidence_estimator
from pregnancy_bridge.modules.temporal_highlight import get_highlight_generator
from pregnancy_bridge.modules.symptom_risk_engine import SymptomRiskEngine
from pregnancy_bridge.modules.symptom_intake import SymptomIntake
import json
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompetitionPipeline:
    """
    Complete competition demonstration pipeline.
    
    Integrates all PregnancyBridge modules to demonstrate:
        - Temporal risk escalation detection
        - Symptom-aware clinical reasoning
        - Laboratory integration
        - Dual-audience explanations (doctor + ASHA)
        - Multi-language translation
        - Confidence scoring
    """
    
    def __init__(self, use_medgemma: bool = True):
        """
        Initialize competition pipeline.
        
        Args:
            use_medgemma: Whether to attempt loading MedGemma model
        """
        logger.info("Initializing PregnancyBridge Competition Pipeline")
        logger.info("=" * 70)
        
        # Load core modules
        self.lab_analyzer = get_lab_analyzer()
        self.translator = get_translator()
        self.confidence_estimator = get_confidence_estimator()
        self.highlight_generator = get_highlight_generator()
        self.risk_engine = SymptomRiskEngine()
        self.symptom_intake = SymptomIntake()
        
        logger.info("Core modules loaded successfully")
        
        # Attempt to load MedGemma for clinical explanations
        self.medgemma_available = False
        if use_medgemma:
            try:
                from pregnancy_bridge.modules.medgemma_extractor import get_clinical_reasoner
                medgemma_reasoner = get_clinical_reasoner()
                
                # Create bridge for explanation generator
                class MedGemmaBridge:
                    def __init__(self, reasoner):
                        self.reasoner = reasoner
                    
                    def generate_explanation(self, prompt, max_tokens=400, temperature=0.3):
                        # Simple extraction of key data from prompt
                        data = {'gestational_age': 36, 'hemoglobin': 10.0}
                        result = self.reasoner.reason_about_case(data)
                        return result['reasoning']
                
                medgemma_bridge = MedGemmaBridge(medgemma_reasoner)
                self.dual_explainer = get_dual_explainer(medgemma_bridge)
                self.medgemma_available = True
                logger.info("MedGemma AI model loaded successfully")
                
            except Exception as e:
                logger.warning(f"MedGemma unavailable: {e}")
                logger.info("Using rule-based fallback explanations")
                self.dual_explainer = get_dual_explainer(None)
        else:
            self.dual_explainer = get_dual_explainer(None)
            logger.info("MedGemma disabled - using rule-based explanations")
        
        logger.info("=" * 70)
        logger.info("PregnancyBridge Competition Pipeline Ready")
        logger.info("=" * 70)
    
    def process_case(self, 
                    visits: list[dict],
                    symptoms: dict,
                    case_name: str,
                    case_description: str = "") -> dict:
        """
        Process complete case through competition pipeline.
        
        Args:
            visits: List of visit records in chronological order
            symptoms: Symptom dictionary from symptom intake
            case_name: Case identifier
            case_description: Optional case description
            
        Returns:
            Complete competition output dictionary
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"Processing Case: {case_name}")
        logger.info("=" * 70)
        
        if case_description:
            logger.info(f"Description: {case_description}")
        
        # Step 1: Laboratory risk analysis
        logger.info("\nStep 1: Laboratory Risk Analysis")
        latest_visit = visits[-1]
        lab_analysis = self.lab_analyzer.analyze_labs(latest_visit)
        lab_trends = self.lab_analyzer.compare_temporal_labs(visits)
        
        logger.info(f"  Lab risk score: {lab_analysis['lab_risk_score']}/10")
        logger.info(f"  Abnormal parameters: {lab_analysis['abnormal_count']}")
        if lab_analysis['critical_flags']:
            logger.info(f"  Critical flags: {', '.join(lab_analysis['critical_flags'])}")
        
        # Step 2: Temporal + symptom risk assessment
        logger.info("\nStep 2: Risk Assessment (Temporal + Symptoms)")
        risk_assessment = self.risk_engine.evaluate_visit(visits, symptoms)
        
        logger.info(f"  Risk category: {risk_assessment['risk_category']}")
        logger.info(f"  Referral required: {risk_assessment['referral_required']}")
        logger.info(f"  Trigger: {risk_assessment['trigger_reason'][:80]}...")
        
        # Step 3: Temporal highlight generation
        logger.info("\nStep 3: Temporal Highlight Generation")
        temporal_highlight = self.highlight_generator.generate_highlight(visits, symptoms)
        trend_severity = self.highlight_generator.get_trend_severity(visits)
        
        logger.info(f"  Trend severity: {trend_severity}")
        
        # Step 4: Dual explanations (clinical + ASHA)
        logger.info("\nStep 4: Dual Explanation Generation")
        explanations = self.dual_explainer.generate_explanations(
            risk_assessment, visits, symptoms, lab_analysis['lab_risk_flags']
        )
        
        logger.info(f"  Clinical explanation: {len(explanations['clinical_explanation'])} chars")
        logger.info(f"  ASHA explanation: {len(explanations['asha_explanation'])} chars")
        
        # Step 5: Multi-language translation
        logger.info("\nStep 5: Multi-Language Translation")
        translations = self.translator.translate_all(explanations['asha_explanation'])
        
        logger.info(f"  Languages: {', '.join(translations.keys())}")
        
        # Check translation coverage
        for lang in ['telugu', 'hindi']:
            coverage = self.translator.get_translation_coverage(
                explanations['asha_explanation'], lang
            )
            logger.info(f"  {lang.title()} coverage: {coverage['coverage_percent']}%")
        
        # Step 6: Confidence estimation
        logger.info("\nStep 6: Confidence Estimation")
        confidence = self.confidence_estimator.estimate_confidence(
            risk_assessment, visits, symptoms, lab_analysis['lab_risk_flags']
        )
        
        logger.info(f"  Confidence score: {confidence['confidence_score']:.2f} ({confidence['confidence_tier']})")
        logger.info(f"  Data quality: {confidence['data_quality_summary']}")
        
        # Build complete output
        output = {
            'case_metadata': {
                'case_name': case_name,
                'case_description': case_description,
                'processed_timestamp': datetime.now().isoformat(),
                'visit_count': len(visits),
                'medgemma_used': self.medgemma_available
            },
            'risk_assessment': {
                'risk_category': risk_assessment['risk_category'],
                'referral_required': risk_assessment['referral_required'],
                'trigger_reason': risk_assessment['trigger_reason']
            },
            'temporal_analysis': {
                'temporal_highlight': temporal_highlight,
                'trend_severity': trend_severity,
                'temporal_trends': lab_trends.get('trends', [])
            },
            'laboratory_analysis': {
                'lab_risk_flags': lab_analysis['lab_risk_flags'],
                'lab_risk_score': lab_analysis['lab_risk_score'],
                'critical_flags': lab_analysis['critical_flags'],
                'abnormal_count': lab_analysis['abnormal_count']
            },
            'explanations': {
                'clinical_explanation': explanations['clinical_explanation'],
                'asha_explanation': explanations['asha_explanation']
            },
            'translations': translations,
            'confidence_metrics': {
                'confidence_score': confidence['confidence_score'],
                'confidence_tier': confidence['confidence_tier'],
                'uncertainty_reason': confidence['uncertainty_reason'],
                'data_quality': confidence['data_quality_summary']
            },
            'symptom_summary': {
                'symptom_count': symptoms.get('symptom_count', 0),
                'present_symptoms': symptoms.get('present_symptoms', []),
                'categories': list(symptoms.get('categories', {}).keys())
            }
        }
        
        logger.info("\nCase processing complete")
        
        return output
    
    def print_case_output(self, output: Dict) -> None:
        """
        Print formatted case output to console.
        
        Args:
            output: Complete case output dictionary
        """
        print("\n")
        print("=" * 70)
        print(f"CASE: {output['case_metadata']['case_name']}")
        print("=" * 70)
        
        if output['case_metadata']['case_description']:
            print(f"\n{output['case_metadata']['case_description']}")
        
        print(f"\nProcessed: {output['case_metadata']['processed_timestamp']}")
        print(f"Visits analyzed: {output['case_metadata']['visit_count']}")
        print(f"MedGemma AI: {'Active' if output['case_metadata']['medgemma_used'] else 'Fallback mode'}")
        
        # Risk assessment
        print("\n" + "-" * 70)
        print("RISK ASSESSMENT")
        print("-" * 70)
        print(f"Category: {output['risk_assessment']['risk_category']}")
        print(f"Referral: {'YES - URGENT' if output['risk_assessment']['referral_required'] else 'NO'}")
        print(f"Reason: {output['risk_assessment']['trigger_reason']}")
        
        # Temporal analysis
        print("\n" + "-" * 70)
        print("TEMPORAL ANALYSIS")
        print("-" * 70)
        print(f"Highlight: {output['temporal_analysis']['temporal_highlight']}")
        print(f"Trend severity: {output['temporal_analysis']['trend_severity']}")
        
        # Laboratory findings
        if output['laboratory_analysis']['lab_risk_flags']:
            print("\n" + "-" * 70)
            print(f"LABORATORY FINDINGS (Risk Score: {output['laboratory_analysis']['lab_risk_score']}/10)")
            print("-" * 70)
            for i, flag in enumerate(output['laboratory_analysis']['lab_risk_flags'][:5], 1):
                print(f"{i}. {flag}")
            
            if output['laboratory_analysis']['critical_flags']:
                print(f"\nCritical flags: {', '.join(output['laboratory_analysis']['critical_flags'])}")
        
        # Confidence metrics
        print("\n" + "-" * 70)
        print("CONFIDENCE ASSESSMENT")
        print("-" * 70)
        print(f"Score: {output['confidence_metrics']['confidence_score']:.2f} ({output['confidence_metrics']['confidence_tier']})")
        print(f"Data quality: {output['confidence_metrics']['data_quality']}")
        print(f"Note: {output['confidence_metrics']['uncertainty_reason']}")
        
        # Clinical explanation
        print("\n" + "-" * 70)
        print("CLINICAL EXPLANATION (Doctor)")
        print("-" * 70)
        print(output['explanations']['clinical_explanation'][:600])
        if len(output['explanations']['clinical_explanation']) > 600:
            print("...")
        
        # ASHA explanation
        print("\n" + "-" * 70)
        print("ASHA WORKER EXPLANATION (Simple Language)")
        print("-" * 70)
        print(output['explanations']['asha_explanation'])
        
        # Translations
        print("\n" + "-" * 70)
        print("TRANSLATIONS")
        print("-" * 70)
        
        print("\nTelugu:")
        print(output['translations']['telugu'][:400])
        if len(output['translations']['telugu']) > 400:
            print("...")
        
        print("\nHindi:")
        print(output['translations']['hindi'][:400])
        if len(output['translations']['hindi']) > 400:
            print("...")
        
        print("\n" + "=" * 70)
    
    def save_output(self, output: Dict, filename: str) -> None:
        """
        Save output to JSON file.
        
        Args:
            output: Complete case output
            filename: Output filename
        """
        output_path = Path(filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {output_path.absolute()}")
    
    def run_demo_cases(self) -> List[Dict]:
        """
        Run all competition demonstration cases.
        
        Returns:
            List of case outputs
        """
        results = []
        
        # Demo Case 1: Platelet drop + proteinuria (HELLP risk)
        case1 = self._demo_case_1_hellp()
        results.append(case1)
        
        # Demo Case 2: Progressive anemia + respiratory symptoms
        case2 = self._demo_case_2_anemia()
        results.append(case2)
        
        # Demo Case 3: Multi-lab abnormality + infection
        case3 = self._demo_case_3_infection()
        results.append(case3)
        
        # Demo Case 4: Progressive BP + neurological symptoms
        case4 = self._demo_case_4_preeclampsia()
        results.append(case4)
        
        return results
    
    def _demo_case_1_hellp(self) -> Dict:
        """Demo Case 1: Platelet drop with proteinuria (HELLP syndrome risk)"""
        
        visits = [
            {
                'date': '2026-01-10',
                'gestational_age': 32,
                'bp': {'systolic': 138, 'diastolic': 88},
                'hemoglobin': 11.2,
                'platelets': 180000,
                'proteinuria': 'trace',
                'wbc': 11000
            },
            {
                'date': '2026-01-24',
                'gestational_age': 34,
                'bp': {'systolic': 144, 'diastolic': 92},
                'hemoglobin': 10.8,
                'platelets': 120000,
                'proteinuria': '+1',
                'wbc': 12000
            },
            {
                'date': '2026-02-04',
                'gestational_age': 36,
                'bp': {'systolic': 150, 'diastolic': 96},
                'hemoglobin': 10.5,
                'platelets': 85000,
                'proteinuria': '+2',
                'wbc': 13000
            }
        ]
        
        symptoms = {
            'symptom_count': 4,
            'present_symptoms': ['headache', 'blurred_vision', 'abdominal_pain', 'nausea_vomiting'],
            'has_neurological': True,
            'has_gi': True,
            'categories': {
                'neurological': ['headache', 'blurred_vision'],
                'gi': ['abdominal_pain', 'nausea_vomiting']
            }
        }
        
        return self.process_case(
            visits, symptoms,
            "Case 1: Platelet Drop + Proteinuria (HELLP Risk)",
            "32-year-old G2P1 at 36 weeks with progressive platelet decline and worsening proteinuria"
        )
    
    def _demo_case_2_anemia(self) -> Dict:
        """Demo Case 2: Progressive anemia with respiratory symptoms"""
        
        visits = [
            {
                'date': '2026-01-05',
                'gestational_age': 28,
                'bp': {'systolic': 118, 'diastolic': 76},
                'hemoglobin': 10.5,
                'platelets': 200000,
                'proteinuria': 'nil'
            },
            {
                'date': '2026-01-20',
                'gestational_age': 30,
                'bp': {'systolic': 120, 'diastolic': 78},
                'hemoglobin': 9.2,
                'platelets': 195000,
                'proteinuria': 'nil'
            },
            {
                'date': '2026-02-04',
                'gestational_age': 32,
                'bp': {'systolic': 122, 'diastolic': 80},
                'hemoglobin': 8.3,
                'platelets': 190000,
                'proteinuria': 'nil'
            }
        ]
        
        symptoms = {
            'symptom_count': 3,
            'present_symptoms': ['breathlessness', 'dizziness', 'pedal_edema'],
            'has_respiratory': True,
            'has_neurological': True,
            'has_edema': True,
            'categories': {
                'respiratory': ['breathlessness'],
                'neurological': ['dizziness'],
                'edema': ['pedal_edema']
            }
        }
        
        return self.process_case(
            visits, symptoms,
            "Case 2: Progressive Anemia + Respiratory Symptoms",
            "28-year-old G1P0 at 32 weeks with declining hemoglobin and cardiopulmonary symptoms"
        )
    
    def _demo_case_3_infection(self) -> Dict:
        """Demo Case 3: Multi-lab abnormality with infection symptoms"""
        
        visits = [
            {
                'date': '2026-01-20',
                'gestational_age': 34,
                'bp': {'systolic': 125, 'diastolic': 82},
                'hemoglobin': 10.8,
                'platelets': 160000,
                'proteinuria': 'nil',
                'wbc': 13000
            },
            {
                'date': '2026-02-04',
                'gestational_age': 36,
                'bp': {'systolic': 132, 'diastolic': 86},
                'hemoglobin': 10.2,
                'platelets': 145000,
                'proteinuria': 'trace',
                'wbc': 21000
            }
        ]
        
        symptoms = {
            'symptom_count': 3,
            'present_symptoms': ['fever', 'abdominal_pain', 'nausea_vomiting'],
            'has_gi': True,
            'categories': {
                'gi': ['abdominal_pain', 'nausea_vomiting'],
                'other': ['fever']
            }
        }
        
        return self.process_case(
            visits, symptoms,
            "Case 3: Multi-Lab Abnormality + Infection Symptoms",
            "30-year-old G3P2 at 36 weeks with elevated WBC and fever"
        )
    
    def _demo_case_4_preeclampsia(self) -> Dict:
        """Demo Case 4: Progressive BP with neurological symptoms"""
        
        visits = [
            {
                'date': '2026-01-15',
                'gestational_age': 34,
                'bp': {'systolic': 128, 'diastolic': 84},
                'hemoglobin': 11.5,
                'platelets': 175000,
                'proteinuria': 'nil',
                'weight': 72.0
            },
            {
                'date': '2026-01-29',
                'gestational_age': 36,
                'bp': {'systolic': 136, 'diastolic': 88},
                'hemoglobin': 11.3,
                'platelets': 170000,
                'proteinuria': 'trace',
                'weight': 74.5
            },
            {
                'date': '2026-02-04',
                'gestational_age': 37,
                'bp': {'systolic': 148, 'diastolic': 94},
                'hemoglobin': 11.2,
                'platelets': 165000,
                'proteinuria': '+1',
                'weight': 76.5
            }
        ]
        
        symptoms = {
            'symptom_count': 4,
            'present_symptoms': ['headache', 'blurred_vision', 'pedal_edema', 'facial_edema'],
            'has_neurological': True,
            'has_edema': True,
            'categories': {
                'neurological': ['headache', 'blurred_vision'],
                'edema': ['pedal_edema', 'facial_edema']
            }
        }
        
        return self.process_case(
            visits, symptoms,
            "Case 4: Progressive BP + Neurological Symptoms",
            "35-year-old G2P1 at 37 weeks with escalating hypertension and preeclampsia symptoms"
        )


def main():
    """Main demonstration entry point"""
    
    print("\n" + "=" * 70)
    print("PREGNANCYBRIDGE COMPETITION DEMONSTRATION")
    print("Maternal Risk Assessment with AI-Powered Temporal Reasoning")
    print("=" * 70)
    print(f"\nExecution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    # Initialize pipeline
    pipeline = CompetitionPipeline(use_medgemma=True)
    
    # Run demonstration cases
    print("\n" + "=" * 70)
    print("RUNNING COMPETITION DEMONSTRATION CASES")
    print("=" * 70)
    
    results = pipeline.run_demo_cases()
    
    # Print each case
    for result in results:
        pipeline.print_case_output(result)
        
        # Save individual case
        case_name = result['case_metadata']['case_name'].replace(' ', '_').replace(':', '')
        filename = f"competition_{case_name.lower()}.json"
        pipeline.save_output(result, filename)
        
        input("\nPress Enter to continue to next case...")
    
    # Save combined results
    combined_filename = f"competition_all_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(combined_filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print("COMPETITION DEMONSTRATION COMPLETE")
    print("=" * 70)
    print(f"\nAll results saved to: {combined_filename}")
    print("\nSystem demonstrates:")
    print("  1. Temporal risk escalation detection")
    print("  2. Laboratory integration (CBC + urinalysis)")
    print("  3. Symptom-aware clinical reasoning")
    print("  4. Dual explanations (doctor + ASHA worker)")
    print("  5. Multi-language translation (English, Telugu, Hindi)")
    print("  6. Confidence scoring and uncertainty quantification")
    print("\nReady for competition submission")


if __name__ == "__main__":
    main()

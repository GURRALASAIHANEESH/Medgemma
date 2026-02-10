"""
PregnancyBridge Competition Pipeline v2
Production-grade pipeline with full auditability and provenance tracking
Author: PregnancyBridge Development Team
Version: 2.0.0
Date: 2026-02-04
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pregnancy_bridge.modules.lab_risk_analyzer import get_lab_analyzer
from pregnancy_bridge.modules.evidence_linker import get_evidence_linker
from pregnancy_bridge.modules.asha_phrase_composer import get_asha_composer
from pregnancy_bridge.modules.provenance_tracker import get_provenance_tracker
from pregnancy_bridge.modules.confidence_estimator_v2 import get_confidence_estimator_v2
from pregnancy_bridge.modules.temporal_highlight import get_highlight_generator
from pregnancy_bridge.modules.symptom_risk_engine import SymptomRiskEngine
from pregnancy_bridge.modules.medgemma_prompt_template import get_prompt_template

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompetitionPipelineV2:
    """
    Production-grade competition pipeline with full auditability.
    
    Version 2 enhancements:
    - Lab age tracking and warnings
    - Evidence linking with temporal deltas
    - Provenance tracking for audit trail
    - Controlled phrase ASHA translations (95%+ coverage)
    - Structured MedGemma prompting
    - Schema v2 compliant output
    
    Requirements met:
    - (A) Output provenance and metadata ✓
    - (B) Lab age policy enforcement ✓
    - (C) Evidence linking layer ✓
    - (D) Dual explanations with templates ✓
    - (E) Controlled phrase library ✓
    - (F) Confidence with lab age penalty ✓
    """
    
    def __init__(self, use_medgemma: bool = True):
        """
        Initialize competition pipeline v2.
        
        Args:
            use_medgemma: Whether to attempt loading MedGemma model
        """
        logger.info("=" * 70)
        logger.info("PregnancyBridge Competition Pipeline v2.0")
        logger.info("=" * 70)
        
        # Load core modules
        self.lab_analyzer = get_lab_analyzer()
        self.evidence_linker = get_evidence_linker()
        self.asha_composer = get_asha_composer()
        self.provenance_tracker = get_provenance_tracker()
        self.confidence_estimator = get_confidence_estimator_v2()
        self.highlight_generator = get_highlight_generator()
        self.risk_engine = SymptomRiskEngine()
        self.prompt_template = get_prompt_template()
        
        logger.info("✓ Core modules loaded")
        
        # Attempt to load MedGemma
        self.medgemma_available = False
        self.model_snapshot_id = None
        
        if use_medgemma:
            try:
                from pregnancy_bridge.modules.medgemma_extractor import get_clinical_reasoner
                self.medgemma_reasoner = get_clinical_reasoner()
                self.medgemma_available = True
                
                # Extract model snapshot ID
                model_path = "D:\\medgemma_clean\\models--google--medgemma-1.5-4b-it"
                self.model_snapshot_id = self.provenance_tracker.get_model_snapshot_info(model_path)
                
                logger.info(f"✓ MedGemma loaded (snapshot: {self.model_snapshot_id[:20] if self.model_snapshot_id else 'unknown'}...)")
                
            except Exception as e:
                logger.warning(f"MedGemma unavailable: {e}")
                logger.info("Using fallback explanations")
                self.medgemma_available = False
        else:
            logger.info("MedGemma disabled by configuration")
        
        logger.info("=" * 70)
        logger.info("Pipeline ready")
        logger.info("=" * 70)
    
    def process_case(self,
                    case_id: str,
                    visits: List[Dict],
                    symptoms: Dict,
                    lab_report_date: Optional[str] = None,
                    lab_report_image: Optional[str] = None,
                    anc_card_image: Optional[str] = None,
                    reference_date: Optional[str] = None) -> Dict:
        """
        Process complete case through pipeline v2.
        
        Args:
            case_id: Unique case identifier
            visits: List of visit records (chronological order)
            symptoms: Symptom dictionary
            lab_report_date: Lab report date (YYYY-MM-DD format)
            lab_report_image: Path to lab report image (optional)
            anc_card_image: Path to ANC card image (optional)
            reference_date: Reference date for lab age (defaults to today)
            
        Returns:
            Complete output conforming to schema v2
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"Processing Case: {case_id}")
        logger.info("=" * 70)
        
        # Step 1: Compute lab age
        logger.info("Step 1: Lab Age Computation")
        lab_age_days = None
        lab_age_warning = None
        
        if lab_report_date:
            lab_age_days = self.evidence_linker.compute_lab_age(lab_report_date, reference_date)
            lab_age_warning = self.evidence_linker.get_lab_age_warning(lab_age_days)
            
            logger.info(f"  Lab date: {lab_report_date}")
            logger.info(f"  Lab age: {lab_age_days} days")
            if lab_age_warning:
                logger.warning(f"  Warning: {lab_age_warning}")
        else:
            logger.warning("  Lab report date not provided")
        
        # Step 2: Laboratory risk analysis
        logger.info("")
        logger.info("Step 2: Laboratory Risk Analysis")
        latest_visit = visits[-1]
        lab_analysis = self.lab_analyzer.analyze_labs(latest_visit)
        
        logger.info(f"  Lab risk score: {lab_analysis['lab_risk_score']}/10")
        logger.info(f"  Abnormal parameters: {lab_analysis['abnormal_count']}")
        
        # Step 3: Build evidence items
        logger.info("")
        logger.info("Step 3: Evidence Linking")
        evidence_items = self.evidence_linker.build_evidence_items(
            visits, symptoms, lab_age_days
        )
        
        evidence_summary = self.evidence_linker.generate_evidence_summary(
            evidence_items, visits
        )
        
        logger.info(f"  Evidence items: {len(evidence_items)}")
        logger.info(f"  Evidence summary: {len(evidence_summary)} line(s)")
        for line in evidence_summary:
            logger.info(f"    - {line}")
        
        # Step 4: Risk assessment
        logger.info("")
        logger.info("Step 4: Risk Assessment")
        risk_assessment = self.risk_engine.evaluate_visit(visits, symptoms)
        
        logger.info(f"  Risk: {risk_assessment['risk_category']}")
        logger.info(f"  Referral: {risk_assessment['referral_required']}")
        logger.info(f"  Trigger: {risk_assessment['trigger_reason'][:60]}...")
        
        # Step 5: Temporal highlight
        logger.info("")
        logger.info("Step 5: Temporal Highlight")
        temporal_highlight = self.highlight_generator.generate_highlight(visits, symptoms)
        logger.info(f"  Highlight: {temporal_highlight[:80]}...")
        
        # Step 6: Clinical explanation (MedGemma or fallback)
        logger.info("")
        logger.info("Step 6: Clinical Explanation Generation")
        
        clinical_explanation = ""
        explanation_source = "fallback_template"
        explanation_generated = False
        
        if self.medgemma_available and risk_assessment['risk_category'] in ['HIGH', 'MODERATE']:
            try:
                # Generate structured prompt
                prompt = self.prompt_template.generate_clinical_explanation_prompt(
                    risk_category=risk_assessment['risk_category'],
                    trigger_reason=risk_assessment['trigger_reason'],
                    evidence_summary=evidence_summary,
                    visits=visits,
                    symptoms=symptoms
                )
                
                # Validate prompt
                validation = self.prompt_template.validate_prompt_constraints(prompt)
                if not validation['valid']:
                    logger.warning(f"Prompt validation issues: {validation['issues']}")
                
                # Call MedGemma
                result = self.medgemma_reasoner.reason_about_case({'prompt': prompt})
                clinical_explanation = result.get('reasoning', '')
                
                if clinical_explanation:
                    explanation_source = "medgemma"
                    explanation_generated = True
                    logger.info(f"  MedGemma explanation: {len(clinical_explanation)} chars")
                else:
                    logger.warning("  MedGemma returned empty explanation")
                    
            except Exception as e:
                logger.error(f"  MedGemma generation failed: {e}")
        
        # Fallback if MedGemma unavailable or failed
        if not clinical_explanation:
            clinical_explanation = self._generate_clinical_fallback(
                risk_assessment, evidence_summary, visits, symptoms, lab_analysis['lab_risk_flags']
            )
            explanation_source = "fallback_template"
            explanation_generated = True
            logger.info(f"  Fallback explanation: {len(clinical_explanation)} chars")
        
        # Step 7: ASHA explanation (phrase-based)
        logger.info("")
        logger.info("Step 7: ASHA Explanation (Controlled Phrases)")
        
        asha_explanation_en = self.asha_composer.compose_asha_explanation(
            risk_category=risk_assessment['risk_category'],
            evidence_summary=evidence_summary,
            lab_age_warning=lab_age_warning
        )
        
        logger.info(f"  ASHA (EN): {len(asha_explanation_en)} chars")
        
        # Step 8: Translation
        logger.info("")
        logger.info("Step 8: Multi-Language Translation")
        
        translations = self.asha_composer.translate_all(asha_explanation_en)
        
        logger.info(f"  Hindi: {len(translations['hindi'])} chars")
        logger.info(f"  Telugu: {len(translations['telugu'])} chars")
        logger.info(f"  Fallback flag: {translations['translation_fallback_flag']}")
        
        # Step 9: Confidence estimation
        logger.info("")
        logger.info("Step 9: Confidence Estimation")
        
        confidence_result = self.confidence_estimator.estimate_confidence(
            risk_assessment=risk_assessment,
            visits=visits,
            symptoms=symptoms,
            lab_flags=lab_analysis['lab_risk_flags'],
            lab_age_days=lab_age_days,
            evidence_items=evidence_items
        )
        
        logger.info(f"  Score: {confidence_result['confidence_score']} ({confidence_result['confidence_tier']})")
        logger.info(f"  Uncertainty: {confidence_result['uncertainty_reason'][:60]}...")
        
        # Step 10: Provenance tracking
        logger.info("")
        logger.info("Step 10: Provenance Tracking")
        
        input_sources = self.provenance_tracker.create_input_sources_record(
            anc_card_image=anc_card_image,
            lab_report_image=lab_report_image,
            lab_report_date=lab_report_date
        )
        
        provenance = self.provenance_tracker.create_provenance_record(
            explanation_source=explanation_source,
            explanation_generated=explanation_generated,
            model_snapshot_id=self.model_snapshot_id,
            lab_report_image_path=lab_report_image
        )
        
        logger.info(f"  Source: {provenance['explanation_source']}")
        logger.info(f"  Generated: {provenance['explanation_generated']}")
        
        # Build schema v2 compliant output
        output = {
            'case_id': case_id,
            'input_sources': input_sources,
            'lab_age_days': lab_age_days,
            'lab_age_warning': lab_age_warning,
            'provenance': provenance,
            'risk_category': risk_assessment['risk_category'],
            'referral_required': risk_assessment['referral_required'],
            'trigger_reason': risk_assessment['trigger_reason'],
            'evidence_items': evidence_items,
            'evidence_summary': evidence_summary,
            'temporal_highlight': temporal_highlight,
            'confidence_score': confidence_result['confidence_score'],
            'confidence_tier': confidence_result['confidence_tier'],
            'uncertainty_reason': confidence_result['uncertainty_reason'],
            'confidence_factors': confidence_result['confidence_factors'],
            'clinical_explanation': clinical_explanation,
            'asha_explanation': asha_explanation_en,
            'translations': translations,
            'laboratory_analysis': {
                'lab_risk_flags': lab_analysis['lab_risk_flags'],
                'lab_risk_score': lab_analysis['lab_risk_score'],
                'critical_flags': lab_analysis['critical_flags']
            }
        }
        
        logger.info("")
        logger.info("✓ Case processing complete")
        
        return output
    
    def _generate_clinical_fallback(self,
                                   risk_assessment: Dict,
                                   evidence_summary: List[str],
                                   visits: List[Dict],
                                   symptoms: Optional[Dict],
                                   lab_flags: List[str]) -> str:
        """
        Generate rule-based clinical explanation (fallback).
        
        Args:
            risk_assessment: Risk assessment output
            evidence_summary: Evidence summary lines
            visits: Visit records
            symptoms: Symptom data
            lab_flags: Lab risk flags
            
        Returns:
            Clinical explanation string
        """
        sections = []
        
        sections.append(f"Risk Category: {risk_assessment['risk_category']}")
        sections.append(f"Trigger: {risk_assessment['trigger_reason']}")
        sections.append("")
        
        sections.append("Evidence-based escalation:")
        for i, evidence in enumerate(evidence_summary, 1):
            sections.append(f"{i}. {evidence}")
        sections.append("")
        
        if lab_flags:
            sections.append("Laboratory findings:")
            for flag in lab_flags[:3]:
                sections.append(f"- {flag}")
            sections.append("")
        
        sections.append(f"Clinical reasoning: The combination of laboratory trends and clinical symptoms supports {risk_assessment['risk_category']} risk classification.")
        
        if risk_assessment['referral_required']:
            sections.append("Recommendation: Urgent referral to higher-level facility for comprehensive evaluation and management.")
        
        return "\n".join(sections)
    
    def save_output(self, output: Dict, filename: str):
        """Save output to JSON file."""
        output_path = Path(filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Saved: {output_path.absolute()}")


# Self-test with demo case
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("CompetitionPipelineV2 Self-Test")
    print("=" * 70)
    
    pipeline = CompetitionPipelineV2(use_medgemma=True)
    
    # Demo case: Recent lab (15 days old)
    test_visits = [
        {
            'date': '2026-01-05',
            'gestational_age': 32,
            'bp': {'systolic': 128, 'diastolic': 84},
            'hemoglobin': 11.2,
            'platelets': 180000,
            'proteinuria': 'trace'
        },
        {
            'date': '2026-01-20',
            'gestational_age': 34,
            'bp': {'systolic': 145, 'diastolic': 92},
            'hemoglobin': 10.5,
            'platelets': 110000,
            'proteinuria': '+2'
        }
    ]
    
    test_symptoms = {
        'symptom_count': 2,
        'present_symptoms': ['headache', 'blurred_vision'],
        'has_neurological': True,
        'categories': {'neurological': ['headache', 'blurred_vision']}
    }
    
    result = pipeline.process_case(
        case_id='DEMO_001',
        visits=test_visits,
        symptoms=test_symptoms,
        lab_report_date='2026-01-20',
        lab_report_image='demo_lab.jpg',
        reference_date='2026-02-04'
    )
    
    # Save output
    pipeline.save_output(result, 'pipeline_v2_demo_output.json')
    
    # Print key fields
    print("\n" + "=" * 70)
    print("Demo Output Summary")
    print("=" * 70)
    print(f"Case ID: {result['case_id']}")
    print(f"Lab age: {result['lab_age_days']} days ({result['lab_age_warning'] or 'No warning'})")
    print(f"Risk: {result['risk_category']}")
    print(f"Confidence: {result['confidence_score']} ({result['confidence_tier']})")
    print(f"Explanation source: {result['provenance']['explanation_source']}")
    print(f"Evidence items: {len(result['evidence_items'])}")
    print(f"Translation fallback: {result['translations']['translation_fallback_flag']}")
    
    print("\n" + "=" * 70)
    print("✓ Self-test complete")
    print("=" * 70)

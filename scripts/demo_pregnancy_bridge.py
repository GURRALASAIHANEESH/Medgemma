"""
PregnancyBridge End-to-End Demonstration Pipeline
Complete offline maternal risk escalation system with symptoms
Author: PregnancyBridge Development Team
Version: 1.0.0

Pipeline Flow:
ANC Card Image → OCR Extraction → Visit Timeline → Symptom Intake →
Risk Escalation Detection → MedGemma Explanation → Referral Summary
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add modules to path
sys.path.append(str(Path(__file__).parent))

from pregnancy_bridge.modules.symptom_intake import SymptomIntake
from pregnancy_bridge.modules.symptom_risk_engine import SymptomRiskEngine
from pregnancy_bridge.modules.explanation_generator import ClinicalExplanationGenerator, FallbackExplanationGenerator

# Try to import existing modules
try:
    from pregnancy_bridge.modules.clinical_parser import ClinicalParser
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False
    print("[Warning: ClinicalParser not available]")

try:
    from pregnancy_bridge.modules.medgemma_bridge import MedGemmaBridge
    MEDGEMMA_AVAILABLE = True
except ImportError:
    MEDGEMMA_AVAILABLE = False
    print("[Warning: MedGemma bridge not available - using fallback]")


def print_header(title: str, width: int = 70):
    """Print formatted section header"""
    print("\n" + "=" * width)
    print(f" {title}")
    print("=" * width)


def print_step(step_num: int, title: str):
    """Print pipeline step header"""
    print(f"\n[STEP {step_num}: {title}]")
    print("-" * 70)


def demo_pipeline(use_simulated_data: bool = True):
    """
    Complete PregnancyBridge pipeline demonstration.
    
    Args:
        use_simulated_data: If True, uses simulated visit data
                           If False, attempts to use real OCR extraction
    
    Returns:
        Tuple of (visits, risk_assessment, symptom_record, explanation)
    """
    
    print_header("PREGNANCYBRIDGE - OFFLINE MATERNAL EARLY WARNING SYSTEM")
    print("Symptom-Aware Temporal Risk Escalation Pipeline")
    print(f"Demo Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("\nSystem Characteristics:")
    print("  • Fully offline (no cloud dependencies)")
    print("  • Deterministic safety rules")
    print("  • Temporal trend detection")
    print("  • Symptom-aware escalation")
    print("  • Explainable AI reasoning")
    
    # ========================================================================
    # STEP 1: ANC Card OCR Extraction (Simulated)
    # ========================================================================
    print_step(1, "ANC Card OCR Extraction")
    
    if use_simulated_data:
        print("Processing simulated historical ANC card data...")
        print("(In production: OCR extracts from physical ANC card images)")
        
        # Simulated extracted visit data
        extracted_visits = [
            {
                'date': '2026-01-10',
                'gestational_age': 32,
                'weight': 68.5,
                'bp': {'systolic': 128, 'diastolic': 84},
                'hemoglobin': 11.2,
                'proteinuria': 'nil',
                'fundal_height': 30,
                'fetal_heart_rate': 142
            },
            {
                'date': '2026-01-24',
                'gestational_age': 34,
                'weight': 70.2,
                'bp': {'systolic': 136, 'diastolic': 88},
                'hemoglobin': 11.0,
                'proteinuria': 'nil',
                'fundal_height': 32,
                'fetal_heart_rate': 145
            },
            {
                'date': '2026-02-04',
                'gestational_age': 36,
                'weight': 72.0,
                'bp': {'systolic': 142, 'diastolic': 92},
                'hemoglobin': 10.8,
                'proteinuria': '+1',
                'fundal_height': 34,
                'fetal_heart_rate': 148
            }
        ]
        
        print(f"✓ Successfully extracted {len(extracted_visits)} visits from ANC cards")
        
    else:
        print("[Real OCR extraction not implemented in this demo]")
        print("[Would process: images/anc_card_001.jpg → structured data]")
        extracted_visits = []
    
    # ========================================================================
    # STEP 2: Temporal Visit Timeline Reconstruction
    # ========================================================================
    print_step(2, "Temporal Visit Timeline Reconstruction")
    
    if extracted_visits:
        print("Reconstructing longitudinal patient timeline...\n")
        
        for i, visit in enumerate(extracted_visits, 1):
            bp_str = f"{visit['bp']['systolic']}/{visit['bp']['diastolic']}"
            print(f"Visit {i} ({visit['date']}, {visit['gestational_age']} weeks):")
            print(f"  • Blood Pressure: {bp_str} mmHg")
            print(f"  • Hemoglobin: {visit['hemoglobin']} g/dL")
            print(f"  • Proteinuria: {visit['proteinuria']}")
            print(f"  • Weight: {visit['weight']} kg")
            print(f"  • Fundal Height: {visit['fundal_height']} cm")
        
        print(f"\n✓ Timeline spans {len(extracted_visits)} visits over " +
              f"{(datetime.fromisoformat(extracted_visits[-1]['date']) - datetime.fromisoformat(extracted_visits[0]['date'])).days} days")
    
    # ========================================================================
    # STEP 3: Structured Symptom Intake
    # ========================================================================
    print_step(3, "Structured Symptom Intake - Current Visit")
    
    print("Healthcare worker enters patient-reported symptoms...")
    print("(Structured input - NO free text, NO NLP required)\n")
    
    # Current visit symptom input
    current_symptoms_input = {
        'symptoms': {
            'headache': True,
            'blurred_vision': True,
            'facial_edema': False,
            'pedal_edema': True,
            'dizziness': False,
            'breathlessness': False,
            'reduced_fetal_movement': False,
            'abdominal_pain': False,
            'nausea_vomiting': False
        }
    }
    
    print("Symptom Input:")
    for symptom, present in current_symptoms_input['symptoms'].items():
        status = "✓ YES" if present else "  No"
        print(f"  {status}  {symptom.replace('_', ' ').title()}")
    
    # Validate and capture symptoms
    intake = SymptomIntake()
    is_valid, error = intake.validate_symptoms(current_symptoms_input)
    
    if not is_valid:
        print(f"\n✗ Symptom validation failed: {error}")
        return None, None, None, None
    
    symptom_record = intake.capture_symptoms(current_symptoms_input, visit_id='V003')
    
    print(f"\n✓ Symptoms captured successfully")
    print(f"  • Total symptoms: {symptom_record['symptom_count']}")
    print(f"  • Present: {', '.join(symptom_record['present_symptoms'])}")
    print(f"  • Categories affected: {symptom_record['category_count']}")
    
    # Categorization
    print("\nClinical Categorization:")
    for category, symptoms in symptom_record['categories'].items():
        if symptoms:
            print(f"  • {category.capitalize()}: {', '.join(symptoms)}")
    
    # Attach symptoms to latest visit
    extracted_visits[-1]['symptoms'] = symptom_record
    
    # ========================================================================
    # STEP 4: Temporal Risk Escalation Engine
    # ========================================================================
    print_step(4, "Temporal Risk Escalation Detection")
    
    print("Analyzing visit trends + symptom combinations...")
    print("Applying evidence-based escalation rules (MEOWS + ACOG guidelines)\n")
    
    engine = SymptomRiskEngine(log_assessments=True)
    risk_assessment = engine.evaluate_visit(extracted_visits, symptom_record)
    
    # Display component risks
    print("Component Risk Analysis:")
    for component, data in risk_assessment['component_risks'].items():
        risk_level = data['risk']
        reason = data['reason'] if data['reason'] else "Normal"
        print(f"  • {component.replace('_', ' ').title()}: {risk_level}")
        if data['reason']:
            print(f"    → {reason}")
    
    # Display final assessment
    print("\n" + "=" * 70)
    print("FINAL RISK ASSESSMENT")
    print("=" * 70)
    print(f"Risk Category: {risk_assessment['risk_category']}")
    print(f"Referral Required: {'YES' if risk_assessment['referral_required'] else 'NO'}")
    print(f"Trigger Visit: Visit {risk_assessment['trigger_visit'] + 1 if risk_assessment['trigger_visit'] is not None else 'N/A'}")
    print(f"\nEscalation Reason:")
    print(f"  {risk_assessment['trigger_reason']}")
    print("=" * 70)
    
    # ========================================================================
    # STEP 4B: AI Context Interpreter & Missing Data Recommender
    # ========================================================================
    print_step("4B", "AI Context Interpreter & Missing Data Recommender")
    print("Generating AI-powered explanations and recommendations...\n")
    
    # Import AI modules
    try:
        from pregnancy_bridge.modules.medgemma_bridge import explain_context
        from pregnancy_bridge.modules.missing_data_recommender import recommend_next_actions
        AI_MODULES_AVAILABLE = True
    except ImportError as e:
        print(f"✗ AI modules not available: {e}")
        AI_MODULES_AVAILABLE = False
    
    if AI_MODULES_AVAILABLE:
        # Prepare evidence summary from risk assessment
        evidence_summary = []
        for component, data in risk_assessment['component_risks'].items():
            if data['reason']:
                evidence_summary.append(f"{component}: {data['reason']}")
        
        # Add trigger reason
        if risk_assessment.get('trigger_reason'):
            evidence_summary.append(risk_assessment['trigger_reason'])
        
        # Calculate lab age (assuming latest visit is today)
        lab_age_days = 5  # Simulated - in production, calculate from visit dates
        
        # Get symptoms dict
        symptoms_dict = symptom_record.get('symptoms', {}) if symptom_record else {}
        
        # 1. Generate AI explanation
        print("Generating context-aware explanation...")
        try:
            ai_explanation = explain_context(
                evidence_summary=evidence_summary,
                rule_reason=risk_assessment['trigger_reason'],
                risk_category=risk_assessment['risk_category'],
                symptoms=symptoms_dict,
                lab_age_days=lab_age_days
            )
            
            print(f"✓ Explanation generated (source: {ai_explanation['explanation_source']})")
            print(f"  QC Pass: {ai_explanation['explanation_qc_pass']}")
            print(f"\nAI Explanation:")
            print(f"  {ai_explanation['explanation_text'][:200]}...")
            
        except Exception as e:
            print(f"✗ AI explanation failed: {e}")
            ai_explanation = None
        
        # 2. Generate recommendations
        print("\nGenerating field-safe recommendations...")
        
        try:
            from pregnancy_bridge.modules.missing_data_recommender import recommend_next_actions_with_deterministic
            
            # Prepare inputs for deterministic fallback
            latest_visit = extracted_visits[-1]
            latest_values = {
                'bp_systolic': latest_visit['bp']['systolic'],
                'bp_diastolic': latest_visit['bp']['diastolic'],
                'hemoglobin': latest_visit['hemoglobin'],
                'proteinuria': latest_visit['proteinuria']
            }
            
            available_tests = ['CBC', 'UrineDip', 'BP_machine', 'LFT']
            context = {
                'lab_age_days': lab_age_days,
                'distance_to_facility_km': 5  # Simulated
            }
            
            # Use production-ready version with deterministic fallback
            ai_recommendations = recommend_next_actions_with_deterministic(
                evidence_summary=evidence_summary,
                available_tests=available_tests,
                context=context,
                risk_category=risk_assessment['risk_category'],
                latest_values=latest_values
            )
            
            print(f"✓ Generated {len(ai_recommendations)} recommendations")
            print(f"  Source: {ai_recommendations[0].get('source', 'unknown')}")
            print("\nRecommendations:")
            for i, rec in enumerate(ai_recommendations, 1):
                print(f"  {i}. [{rec['priority'].upper()}] {rec['action']}")
                print(f"     Why: {rec['why']}")
                if 'practical_note' in rec:
                    print(f"     Note: {rec['practical_note']}")
            
        except Exception as e:
            print(f"✗ Recommendations generation failed: {e}")
            ai_recommendations = None
        
    else:
        ai_explanation = None
        ai_recommendations = None
        print("⚠ AI modules not available - skipping AI integration")
    
    print("\n" + "-" * 70)
    
    # ========================================================================
    # STEP 5: MedGemma Clinical Reasoning
    # ========================================================================
    print_step(5, "MedGemma Clinical Explanation Generation")
    
    print("Generating explainable clinical justification...")
    print("(MedGemma provides reasoning - does NOT change risk classification)\n")
    
    # Initialize explanation generator
    if MEDGEMMA_AVAILABLE:
        try:
            medgemma = MedGemmaBridge()
            explainer = ClinicalExplanationGenerator(medgemma)
            print("✓ MedGemma model loaded successfully")
            use_ai_explanation = True
        except Exception as e:
            print(f"✗ MedGemma initialization failed: {e}")
            print("✓ Using rule-based fallback explanation")
            explainer = FallbackExplanationGenerator()
            use_ai_explanation = False
    else:
        explainer = FallbackExplanationGenerator()
        use_ai_explanation = False
        print("✓ Using rule-based explanation (MedGemma not available)")
    
    # Generate explanation
    print("\n" + "-" * 70)
    print("CLINICAL EXPLANATION")
    print("-" * 70 + "\n")
    
    try:
        explanation = explainer.generate_escalation_explanation(
            extracted_visits,
            risk_assessment,
            symptom_record
        )
        print(explanation)
    except Exception as e:
        print(f"[Explanation generation error: {e}]")
        explanation = f"Rule-based escalation: {risk_assessment['trigger_reason']}"
    
    print("\n" + "-" * 70)
    
    # ========================================================================
    # STEP 6: Referral Summary Generation
    # ========================================================================
    print_step(6, "Referral Summary for Higher Facility")
    
    if risk_assessment['referral_required']:
        print("Generating structured referral document...\n")
        
        referral_summary = generate_referral_summary(
            extracted_visits,
            risk_assessment,
            symptom_record,
            explanation
        )
        
        print(referral_summary)
        
        # Save to file
        referral_filename = f"referral_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(referral_filename, 'w', encoding='utf-8') as f:
                f.write(referral_summary)
            print(f"\n✓ Referral summary saved to: {referral_filename}")
        except Exception as e:
            print(f"\n✗ Failed to save referral summary: {e}")
    else:
        print("No referral required - Continue routine antenatal care")
        print("Next scheduled visit as per protocol")
    
    # ========================================================================
    # PIPELINE SUMMARY
    # ========================================================================
    print("\n" + "=" * 70)
    print("PIPELINE DEMONSTRATION COMPLETE")
    print("=" * 70)
    
    print("\nSystem Validation:")
    print("  ✓ Fully offline (no cloud dependencies)")
    print("  ✓ Deterministic safety rules (authoritative)")
    print("  ✓ Temporal reasoning (detects escalation patterns)")
    print("  ✓ Symptom-aware (clinical context integration)")
    print(f"  ✓ Explainable ({'AI-powered' if use_ai_explanation else 'rule-based'} reasoning)")
    print("  ✓ Human-in-the-loop (supports clinical decision-making)")
    
    print("\nClinical Impact:")
    print(f"  • Risk detected: {risk_assessment['risk_category']}")
    print(f"  • Referral triggered: {'YES' if risk_assessment['referral_required'] else 'NO'}")
    print(f"  • Visits analyzed: {len(extracted_visits)}")
    print(f"  • Symptoms integrated: {symptom_record['symptom_count']}")
    
    print("\nPregnancyBridge successfully demonstrates:")
    print("  'Maternal risk is missed because it unfolds across time and symptoms.'")
    print("  'This system detects that escalation safely and explainably.'")
    
    # ========================================================================
    # Save AI outputs to JSON for competition submission
    # ========================================================================
    from datetime import datetime as dt
    import json
    from pathlib import Path
    
    # Create output directory
    output_dir = Path("outputs/validation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate case ID
    case_id = f"demo_{dt.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Build complete output with AI results
    complete_output = {
        'case_id': case_id,
        'provenance': {
            'timestamp_utc': dt.utcnow().isoformat() + 'Z',
            'risk_authority': 'rule_engine',
            'explanation_source': ai_explanation['explanation_source'] if ai_explanation else 'none',
            'model_snapshot': ai_explanation.get('model_snapshot') if ai_explanation else None,
            'recommendation_source': ai_recommendations[0].get('source') if ai_recommendations else 'none',
            'system_version': '1.0.0',
            'pipeline': 'demo_pregnancy_bridge'
        },
        'input_case': {
            'visits': extracted_visits,
            'symptom_record': symptom_record
        },
        'rule_result': {
            'risk_category': risk_assessment['risk_category'],
            'referral_required': risk_assessment['referral_required'],
            'trigger_reason': risk_assessment['trigger_reason'],
            'trigger_visit': risk_assessment['trigger_visit'],
            'component_risks': risk_assessment['component_risks']
        },
        'evidence_summary': evidence_summary if 'evidence_summary' in locals() else [],
        'ai_outputs': {
            'explanation': ai_explanation if ai_explanation else None,
            'recommendations': ai_recommendations if ai_recommendations else []
        }
    }
    
    # Save to JSON file
    output_file = output_dir / f"{case_id}_full.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(complete_output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ AI outputs saved to: {output_file}")
    
    return complete_output


def generate_referral_summary(visits: List[Dict],
                               assessment: Dict,
                               symptoms: Dict,
                               explanation: str) -> str:
    """
    Generate comprehensive referral summary document.
    
    Args:
        visits: Visit timeline
        assessment: Risk assessment from engine
        symptoms: Symptom record
        explanation: Clinical explanation from MedGemma
        
    Returns:
        Formatted referral summary string
    """
    
    # Header
    summary = []
    summary.append("╔" + "═" * 68 + "╗")
    summary.append("║" + "MATERNAL REFERRAL SUMMARY".center(68) + "║")
    summary.append("║" + "PregnancyBridge Early Warning System".center(68) + "║")
    summary.append("╚" + "═" * 68 + "╝")
    summary.append("")
    
    # Status
    summary.append("REFERRAL STATUS: URGENT - HIGH RISK PREGNANCY")
    summary.append("")
    summary.append(f"Risk Category: {assessment['risk_category']}")
    summary.append(f"Escalation Reason: {assessment['trigger_reason']}")
    summary.append(f"Assessment Date: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}")
    summary.append("")
    
    # Patient Information
    latest_visit = visits[-1]
    summary.append("=" * 70)
    summary.append("PATIENT INFORMATION")
    summary.append("=" * 70)
    summary.append(f"Current Gestational Age: {latest_visit.get('gestational_age', '?')} weeks")
    summary.append(f"Current Weight: {latest_visit.get('weight', '?')} kg")
    summary.append(f"Total ANC Visits: {len(visits)}")
    summary.append("")
    
    # Visit Timeline
    summary.append("=" * 70)
    summary.append("VISIT TIMELINE")
    summary.append("=" * 70)
    
    for i, visit in enumerate(visits, 1):
        bp = visit['bp']
        summary.append(f"\nVisit {i} ({visit['date']}, {visit['gestational_age']} weeks):")
        summary.append(f"  Blood Pressure: {bp['systolic']}/{bp['diastolic']} mmHg")
        summary.append(f"  Hemoglobin: {visit['hemoglobin']} g/dL")
        summary.append(f"  Proteinuria: {visit['proteinuria']}")
        summary.append(f"  Weight: {visit.get('weight', 'N/A')} kg")
        
        if 'symptoms' in visit and visit['symptoms']['symptom_count'] > 0:
            symptom_list = ', '.join(visit['symptoms']['present_symptoms'])
            summary.append(f"  Symptoms: {symptom_list}")
    
    summary.append("")
    
    # Current Symptoms
    summary.append("=" * 70)
    summary.append("CURRENT SYMPTOMS")
    summary.append("=" * 70)
    
    if symptoms['symptom_count'] > 0:
        for category, items in symptoms['categories'].items():
            if items:
                summary.append(f"• {category.capitalize()}: {', '.join(items)}")
    else:
        summary.append("No symptoms reported")
    
    summary.append("")
    
    # Clinical Explanation
    summary.append("=" * 70)
    summary.append("CLINICAL REASONING")
    summary.append("=" * 70)
    summary.append(explanation)
    summary.append("")
    
    # Recommended Actions
    summary.append("=" * 70)
    summary.append("RECOMMENDED IMMEDIATE ACTIONS")
    summary.append("=" * 70)
    
    actions = [
        "• Immediate obstetric evaluation by specialist",
        "• Blood pressure monitoring every 15-30 minutes",
        "• Complete metabolic panel (LFT, RFT, CBC)",
        "• Urine protein quantification (24-hour or spot PCR)",
        "• Fetal monitoring (NST and biophysical profile)",
        "• Assess for signs of severe preeclampsia/eclampsia"
    ]
    
    if 'preeclampsia' in assessment['trigger_reason'].lower():
        actions.append("• Consider magnesium sulfate prophylaxis")
        actions.append("• Prepare for potential expedited delivery")
    
    if 'anemia' in assessment['trigger_reason'].lower():
        actions.append("• Consider blood transfusion if Hb <7 g/dL")
        actions.append("• Iron studies and peripheral smear")
    
    summary.extend(actions)
    summary.append("")
    
    # Facility Requirements
    summary.append("=" * 70)
    summary.append("REFERRAL FACILITY REQUIREMENTS")
    summary.append("=" * 70)
    summary.append("• 24/7 obstetric specialist availability")
    summary.append("• NICU capability for preterm neonates")
    summary.append("• Eclampsia management protocol")
    summary.append("• Blood bank and transfusion services")
    summary.append("• Operating theater for emergency C-section")
    summary.append("")
    
    # Footer
    summary.append("=" * 70)
    summary.append(f"Generated by: PregnancyBridge Offline Maternal EWS v1.0")
    summary.append(f"Timestamp: {datetime.now().isoformat()}")
    summary.append(f"System: Deterministic rule-based + AI explanation")
    summary.append("=" * 70)
    
    return "\n".join(summary)


def interactive_demo():
    """
    Interactive demo mode with user prompts.
    """
    print("\n" + "=" * 70)
    print("PREGNANCYBRIDGE INTERACTIVE DEMONSTRATION")
    print("=" * 70 + "\n")
    
    print("This demo will walk through the complete pipeline:")
    print("  1. ANC card OCR extraction (simulated)")
    print("  2. Temporal visit timeline reconstruction")
    print("  3. Structured symptom intake")
    print("  4. Risk escalation detection")
    print("  5. MedGemma clinical explanation")
    print("  6. Referral summary generation")
    
    input("\nPress Enter to begin demonstration...")
    
    try:
        result = demo_pipeline(use_simulated_data=True)
        
        # Extract components from result dictionary
        visits = result.get('visits')
        assessment = result.get('risk_assessment')
        symptoms = result.get('symptom_record')
        explanation = result.get('explanation')
        
        print("\n" + "=" * 70)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("=" * 70)
        
        # Offer to view detailed results
        print("\nWould you like to:")
        print("  1. View detailed component risks")
        print("  2. Export results to JSON")
        print("  3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1' and assessment:
            print("\n" + "=" * 70)
            print("DETAILED COMPONENT RISKS")
            print("=" * 70)
            for component, data in assessment['component_risks'].items():
                print(f"\n{component.replace('_', ' ').title()}:")
                print(f"  Risk Level: {data['risk']}")
                print(f"  Reason: {data['reason'] or 'Normal'}")
                print(f"  Trigger Visit: {data['visit']}")
        
        elif choice == '2' and assessment:
            filename = f"demo_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output = {
                'timestamp': datetime.now().isoformat(),
                'risk_category': assessment['risk_category'],
                'referral_required': assessment['referral_required'],
                'trigger_reason': assessment['trigger_reason'],
                'symptom_count': symptoms['symptom_count'] if symptoms else 0,
                'visit_count': len(visits) if visits else 0
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            print(f"\n✓ Results exported to: {filename}")
        
        print("\nThank you for using PregnancyBridge!")
        
    except KeyboardInterrupt:
        print("\n\n[Demo interrupted by user]")
    except Exception as e:
        print(f"\n\n[ERROR: Demo failed - {e}]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_demo()
    else:
        print("\nRunning automated demonstration...")
        result = demo_pipeline(use_simulated_data=True)
        
        if result:
            print(f"\n[Demo completed: {result['rule_result']['risk_category']} risk detected]")
            print(f"[JSON output: {result['case_id']}_full.json]")
        else:
            print("\n[Demo failed to complete]")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pregnancy_bridge.modules.ocr_utils import perform_ocr
from pregnancy_bridge.modules.clinical_parser import extract_clinical_fields
from pregnancy_bridge.modules.risk_engine import assess_risk
from pregnancy_bridge.modules.history_manager import load_patient_history, save_patient_visit, summarize_trends
from pregnancy_bridge.modules.summary_writer import (
    generate_referral_summary,
    save_summary_to_file,
    save_clinical_record_json
)
from pregnancy_bridge.modules.medgemma_bridge import extract_clinical_data_medgemma, extract_symptoms_medgemma
from pregnancy_bridge.modules.medgemma_extractor import extract_with_fallback


def process_anc_record(
    image_path: str,
    symptoms: dict = None,
    patient_id: str = None
):
    if symptoms is None:
        symptoms = {}
    
    print("\n" + "="*70)
    print("  PregnancyBridge - Processing Pipeline with History")
    print("="*70)
    
    print("\n[1/6] Performing OCR extraction...")
    text = perform_ocr(image_path)
    
    if not text:
        print("ERROR: OCR extraction failed")
        return None, None, None
    
    print(f"Extracted {len(text)} characters")
    
    print("\n[2/6] Extracting clinical fields...")
    fields = extract_clinical_fields(text)
    
    extracted_count = sum(1 for v in fields.values() if v is not None)
    print(f"Extracted {extracted_count} clinical parameters")
    
    if patient_id is None:
        patient_id = fields.get('patient_id', 'UNKNOWN')
    
    print(f"\n[3/6] Loading patient history (ID: {patient_id})...")
    history = load_patient_history(patient_id)
    
    if history:
        print(f"Found {len(history)} previous visits")
    else:
        print("No previous history found - first visit")
    
    print("\n[4/6] Analyzing longitudinal trends...")
    trend_summary = summarize_trends(history, fields)
    
    if trend_summary['trend_summary']:
        print(f"Detected {len(trend_summary['trend_summary'])} critical trends")
        for trend in trend_summary['trend_summary']:
            print(f"  - {trend}")
    else:
        print("No significant trends detected")
    
    print("\n[5/6] Assessing clinical risk...")
    assessment = assess_risk(fields, symptoms, trend_summary)
    print(f"Risk Level: {assessment['risk_level'].upper()} (Score: {assessment['risk_score']})")
    
    print("\n[6/6] Saving visit data to history...")
    save_patient_visit(patient_id, fields)
    print(f"Visit saved for patient {patient_id}")
    
    return fields, assessment, trend_summary


def process_anc_record_medgemma(image_path: str, patient_id: str = None):
    """
    Process ANC record using MedGemma vision-language model for direct extraction.
    This bypasses OCR and uses the model's native document understanding.
    """
    print("\n" + "="*70)
    print("  PregnancyBridge - MedGemma Vision Processing Pipeline")
    print("="*70)
    
    print("\n[1/6] MedGemma document extraction...")
    raw_data = extract_with_fallback(image_path)
    
    # Convert to clinical data format
    clinical_data = extract_clinical_data_medgemma(image_path)
    symptoms = extract_symptoms_medgemma(raw_data)
    
    extracted_count = sum(1 for v in clinical_data.values() if v is not None)
    print(f"Extracted {extracted_count} clinical parameters")
    
    if patient_id is None:
        patient_id = clinical_data.get('patient_id', 'UNKNOWN')
    
    print(f"\n[2/6] Loading patient history (ID: {patient_id})...")
    history = load_patient_history(patient_id)
    
    if history:
        print(f"Found {len(history)} previous visits")
    else:
        print("No previous history found - first visit")
    
    print("\n[3/6] Analyzing longitudinal trends...")
    trend_summary = summarize_trends(history, clinical_data)
    
    if trend_summary['trend_summary']:
        print(f"Detected {len(trend_summary['trend_summary'])} critical trends")
        for trend in trend_summary['trend_summary']:
            print(f"  - {trend}")
    else:
        print("No significant trends detected")
    
    print("\n[4/6] Assessing clinical risk...")
    assessment = assess_risk(clinical_data, symptoms, trend_summary)
    print(f"Risk Level: {assessment['risk_level'].upper()} (Score: {assessment['risk_score']})")
    
    print("\n[5/6] Generating clinical summary...")
    summary = generate_referral_summary(
        clinical_data,
        assessment,
        trend_summary['trend_summary'],
        symptoms
    )
    
    print("\n[6/6] Saving visit data to history...")
    save_patient_visit(patient_id, clinical_data)
    print(f"Visit saved for patient {patient_id}")
    
    print("\n" + "="*70)
    print(summary)
    print("="*70)
    
    return clinical_data, assessment, trend_summary


def main():
    print("\n" + "█"*70)
    print("  TEST: Complete Workflow with Trend-Based Risk Escalation")
    print("█"*70)
    
    patient_id = "PAC001"
    
    manual_data = {
        'patient_name': 'Ana Betz',
        'patient_id': patient_id,
        'age': '25y10m26d',
        'date': '2026-01-18',
        'hemoglobin': 9.2,
        'bp_systolic': 155,
        'bp_diastolic': 98,
        'gestational_age': 34,
        'proteinuria': '3+',
        'weight': 70.5,
        'fundal_height': 31,
        'edema': True
    }
    
    symptoms = {
        "headache": True,
        "visual_changes": True,
        "nausea": False,
        "swelling": True,
        "abdominal_pain": True
    }
    
    print(f"\n[Loading history for patient {patient_id}...]")
    history = load_patient_history(patient_id)
    
    if history:
        print(f"Loaded {len(history)} previous visits:")
        for i, visit in enumerate(history[-3:], 1):
            hb = visit.get('hemoglobin', 'N/A')
            bp_sys = visit.get('bp_systolic', 'N/A')
            bp_dia = visit.get('bp_diastolic', 'N/A')
            protein = visit.get('proteinuria', 'N/A')
            date = visit.get('visit_date', 'N/A')
            print(f"  Visit {i} ({date}): Hb {hb}, BP {bp_sys}/{bp_dia}, Protein {protein}")
    
    print("\n[Analyzing current visit with trend detection...]")
    trend_summary = summarize_trends(history, manual_data)
    
    if trend_summary['trend_summary']:
        print(f"\nTrends detected:")
        for trend in trend_summary['trend_summary']:
            print(f"  ! {trend}")
    
    print("\n[Performing risk assessment with trend escalation...]")
    assessment = assess_risk(manual_data, symptoms, trend_summary)
    
    summary = generate_referral_summary(
        manual_data,
        assessment,
        trend_summary['trend_summary'],
        symptoms
    )
    
    print("\n" + "="*70)
    print(summary)
    print("="*70)
    
    summary_path = save_summary_to_file(summary, manual_data['patient_name'])
    print(f"\nSummary saved: {summary_path}")
    
    json_path = save_clinical_record_json(manual_data, assessment)
    print(f"JSON record saved: {json_path}")
    
    save_patient_visit(patient_id, manual_data)
    print(f"History updated for patient: {patient_id}")
    
    print("\n" + "="*70)
    print("  Pipeline Complete")
    print("="*70)


def test_trend_escalation():
    print("\n\n" + "█"*70)
    print("  TEST: Dangerous Trend Detection (Hb Drop + BP Surge)")
    print("█"*70)
    
    patient_id = "PAC002"
    
    # Simulate 3 progressive visits showing deterioration
    visits = [
        {
            'date': '2026-01-01',
            'hemoglobin': 11.5,
            'bp_systolic': 130,
            'bp_diastolic': 80,
            'gestational_age': 28,
            'proteinuria': 'negative'
        },
        {
            'date': '2026-01-08',
            'hemoglobin': 10.2,
            'bp_systolic': 140,
            'bp_diastolic': 88,
            'gestational_age': 30,
            'proteinuria': 'trace'
        },
        {
            'date': '2026-01-15',
            'hemoglobin': 8.8,
            'bp_systolic': 152,
            'bp_diastolic': 94,
            'gestational_age': 32,
            'proteinuria': '2+'
        }
    ]
    
    from pregnancy_bridge.modules.history_manager import save_patient_visit, load_patient_history, summarize_trends
    
    # Save first two visits
    for visit in visits[:2]:
        visit['patient_id'] = patient_id
        save_patient_visit(patient_id, visit)
    
    # Process third visit with trend analysis
    current_visit = visits[2]
    current_visit['patient_id'] = patient_id
    
    history = load_patient_history(patient_id)
    print(f"\nLoaded {len(history)} previous visits")
    
    trend_summary = summarize_trends(history, current_visit)
    
    print("\n[TRENDS DETECTED]:")
    for trend in trend_summary['trend_summary']:
        print(f"  ! {trend}")
    
    symptoms = {"headache": True, "visual_changes": False, "swelling": True}
    
    assessment = assess_risk(current_visit, symptoms, trend_summary)
    
    print(f"\n[RISK ASSESSMENT]:")
    print(f"Risk Level: {assessment['risk_level'].upper()} (Score: {assessment['risk_score']})")
    print(f"\nKey Risk Factors:")
    for factor in assessment['risk_factors'][:5]:
        print(f"  * {factor}")


if __name__ == "__main__":
    main()
    test_trend_escalation()

from competition_pipeline_v2 import CompetitionPipelineV2
import json

# Initialize pipeline
pipeline = CompetitionPipelineV2(use_medgemma=True)

# YOUR REAL DATA - EDIT THIS
visits = [
    {
        'date': '2026-01-15',
        'gestational_age': 32,
        'bp': {'systolic': 130, 'diastolic': 85},
        'hemoglobin': 11.5,
        'platelets': 175000,
        'proteinuria': 'trace',
        'wbc': 9000
    },
    {
        'date': '2026-02-01',
        'gestational_age': 35,
        'bp': {'systolic': 145, 'diastolic': 95},
        'hemoglobin': 10.8,
        'platelets': 95000,
        'proteinuria': '+2',
        'wbc': 15000
    }
]

symptoms = {
    'symptom_count': 3,
    'present_symptoms': ['headache', 'blurred_vision', 'epigastric_pain']
}

# Process
result = pipeline.process_case(
    case_id='REAL_TEST_001',
    visits=visits,
    symptoms=symptoms,
    lab_report_date='2026-02-01',  # CHANGE THIS to your lab date
    lab_report_image='test_real_data/lab_report.jpg',  # Your file
    anc_card_image='test_real_data/anc_card.jpg',
    reference_date='2026-02-04'
)

# Save output
with open('REAL_RESULT.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# Print results
print("\n" + "="*70)
print("REAL WORLD TEST RESULT")
print("="*70)
print(f"Case ID: {result['case_id']}")
print(f"Risk: {result['risk_category']}")
print(f"Referral needed: {result['referral_required']}")
print(f"Lab age: {result['lab_age_days']} days")
print(f"Lab warning: {result['lab_age_warning']}")
print(f"Confidence: {result['confidence_score']}")
print(f"\nTrigger reason: {result['trigger_reason']}")
print(f"\nEvidence summary:")
for i, evidence in enumerate(result['evidence_summary'], 1):
    print(f"  {i}. {evidence}")

print(f"\nClinical explanation:")
print(result['clinical_explanation'][:300] + "...")

print(f"\nASHA explanation (English):")
print(result['asha_explanation'][:300] + "...")

print(f"\nASHA explanation (Hindi):")
print(result['translations']['hindi'][:200] + "...")

print(f"\nASHA explanation (Telugu):")
print(result['translations']['telugu'][:200] + "...")

print("\n✓ Full output saved to: REAL_RESULT.json")
print("="*70)

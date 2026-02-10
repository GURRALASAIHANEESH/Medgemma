"""
SIMPLE IMAGE TEST - NO COMPLEX IMPORTS
Just OCR + Manual entry + Pipeline v2
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# YOUR IMAGE
IMAGE_PATH = r"D:\MedGemma\data\images\test1.png"

print("\n" + "="*70)
print("SIMPLE IMAGE PROCESSOR")
print("="*70)

# Try OCR
try:
    from pregnancy_bridge.modules.ocr_utils import perform_ocr
    print(f"\n1. Trying OCR on: {IMAGE_PATH}")
    ocr_text = perform_ocr(IMAGE_PATH)
    print(f"   Extracted: {len(ocr_text)} chars")
    print(f"   Text: {ocr_text[:300]}")
except Exception as e:
    print(f"   OCR failed: {e}")
    ocr_text = ""

# Manual entry
print("\n2. ENTER DATA MANUALLY:")
print("-" * 70)

visit = {}

# BP
bp_sys = input("BP Systolic (e.g., 140): ").strip()
bp_dia = input("BP Diastolic (e.g., 90): ").strip()
if bp_sys and bp_dia:
    visit['bp'] = {'systolic': int(bp_sys), 'diastolic': int(bp_dia)}

# Hemoglobin
hb = input("Hemoglobin (e.g., 10.5): ").strip()
if hb:
    visit['hemoglobin'] = float(hb)

# Platelets
plt = input("Platelets (e.g., 150000): ").strip()
if plt:
    visit['platelets'] = int(plt)

# Proteinuria
protein = input("Proteinuria (nil/trace/+1/+2/+3): ").strip()
if protein:
    visit['proteinuria'] = protein

# WBC
wbc = input("WBC (e.g., 8000 or press Enter): ").strip()
if wbc:
    visit['wbc'] = int(wbc)

# Gestational age
ga = input("Gestational Age (e.g., 32): ").strip()
if ga:
    visit['gestational_age'] = int(ga)

print("\n3. SYMPTOMS:")
print("Examples: headache, blurred_vision, breathlessness, epigastric_pain")
symptom_input = input("Enter symptoms (comma-separated): ").strip()

if symptom_input:
    symptom_list = [s.strip() for s in symptom_input.split(',')]
    symptoms = {
        'symptom_count': len(symptom_list),
        'present_symptoms': symptom_list
    }
else:
    symptoms = {'symptom_count': 0, 'present_symptoms': []}

# Lab date
lab_date = input("Lab date (YYYY-MM-DD or Enter for today): ").strip()
if not lab_date:
    from datetime import datetime
    lab_date = datetime.now().strftime('%Y-%m-%d')

print("\n4. PROCESSING...")
print("-" * 70)

# Use pipeline v2
from competition_pipeline_v2 import CompetitionPipelineV2
import json

pipeline = CompetitionPipelineV2(use_medgemma=True)

result = pipeline.process_case(
    case_id='SIMPLE_IMAGE_001',
    visits=[visit],
    symptoms=symptoms,
    lab_report_date=lab_date,
    lab_report_image=IMAGE_PATH,
    anc_card_image=IMAGE_PATH
)

# Save
with open('SIMPLE_RESULT.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# Print
print("\n" + "="*70)
print("FINAL RESULT")
print("="*70)
print(f"Risk: {result['risk_category']}")
print(f"Referral: {result['referral_required']}")
print(f"Lab age: {result['lab_age_days']} days")
print(f"Confidence: {result['confidence_score']}")
print(f"\nTrigger: {result['trigger_reason']}")
print(f"\nEvidence:")
for ev in result['evidence_summary']:
    print(f"  - {ev}")
print(f"\nASHA (English): {result['asha_explanation'][:150]}...")
print(f"\nASHA (Hindi): {result['translations']['hindi'][:100]}...")
print(f"\n✓ Saved to: SIMPLE_RESULT.json")
print("="*70)

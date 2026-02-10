import sys
sys.path.insert(0, 'src')
from pathlib import Path
import json
from pregnancy_bridge.modules.symptom_intake import SymptomIntake
from pregnancy_bridge.modules.symptom_risk_engine import SymptomRiskEngine
from pregnancy_bridge.modules.medgemma_bridge import explain_context

print("Testing MedGemma with relaxed QC...")
print("=" * 60)

case_file = Path('tests/synthetic/case_006.json')
with open(case_file) as f:
    case_data = json.load(f)

intake = SymptomIntake()
visits = case_data.get('visits', [])
symptom_record = {}
for visit in visits:
    for k, v in visit.items():
        if k not in ['visit_number', 'gestational_week', 'date']:
            if v not in [None, '', 'none', 'normal']:
                symptom_record[k] = v

engine = SymptomRiskEngine()
assessment = engine.evaluate_visit(visits, symptom_record)
risk = assessment.get('risk_category', assessment.get('risk_level', 'UNKNOWN'))

result = explain_context(
    evidence_summary=assessment.get('evidence', []),
    rule_reason=assessment.get('primary_reason', ''),
    risk_category=risk,
    symptoms=symptom_record,
    lab_age_days=0
)

print(f"\nRESULTS:")
print(f"Source: {result.get('explanation_source')}")
print(f"QC Pass: {result.get('explanation_qc_pass')}")
print(f"Length: {len(result.get('explanation_text', ''))} chars")
print(f"\nPreview (first 300 chars):")
print(result.get('explanation_text', '')[:300])
print("\n" + "=" * 60)

if result.get('explanation_source') == 'medgemma':
    print("SUCCESS - MedGemma working!")
else:
    print("FAIL - Still using fallback")

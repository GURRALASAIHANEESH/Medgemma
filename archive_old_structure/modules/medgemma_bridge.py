from typing import Dict
from modules.medgemma_extractor import extract_with_fallback
import logging

logger = logging.getLogger(__name__)


def extract_clinical_data_medgemma(image_path: str) -> Dict:
    raw_data = extract_with_fallback(image_path)
    
    clinical_data = {
        'patient_name': raw_data.get('patient_name'),
        'patient_id': None,
        'age': raw_data.get('age'),
        'date': raw_data.get('visit_date'),
        'hemoglobin': raw_data.get('hemoglobin'),
        'bp_systolic': None,
        'bp_diastolic': None,
        'gestational_age': raw_data.get('gestational_age_weeks'),
        'proteinuria': raw_data.get('proteinuria'),
        'weight': None,
        'fundal_height': raw_data.get('fundal_height_cm'),
        'edema': raw_data.get('edema') == 'present' if raw_data.get('edema') else None
    }
    
    bp = raw_data.get('blood_pressure')
    if bp and '/' in bp:
        parts = bp.split('/')
        try:
            clinical_data['bp_systolic'] = int(parts[0])
            clinical_data['bp_diastolic'] = int(parts[1])
        except ValueError:
            pass
    
    return clinical_data


def extract_symptoms_medgemma(raw_data: Dict) -> Dict[str, bool]:
    return {
        'headache': raw_data.get('headache', False),
        'visual_changes': raw_data.get('visual_disturbance', False),
        'nausea': raw_data.get('nausea', False),
        'bleeding': raw_data.get('bleeding', False),
        'swelling': raw_data.get('edema') == 'present' if raw_data.get('edema') else False
    }

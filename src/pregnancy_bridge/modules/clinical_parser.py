import re
from typing import Dict, Optional


def extract_clinical_fields(ocr_text: str) -> Dict[str, Optional[str]]:
    fields = {}
    lines = ocr_text.split('\n')
    
    fields['patient_name'] = _extract_patient_name(ocr_text)
    fields['patient_id'] = _extract_patient_id(ocr_text)
    fields['age'] = _extract_age(ocr_text)
    fields['date'] = _extract_date(ocr_text)
    fields['hemoglobin'] = _extract_hemoglobin(lines)
    fields['bp_systolic'], fields['bp_diastolic'] = _extract_blood_pressure(ocr_text)
    fields['gestational_age'] = _extract_gestational_age(ocr_text)
    fields['proteinuria'] = _extract_proteinuria(ocr_text)
    fields['weight'] = _extract_weight(ocr_text)
    fields['fundal_height'] = _extract_fundal_height(ocr_text)
    fields['edema'] = _extract_edema(ocr_text)
    
    return fields


def _extract_patient_name(text: str) -> Optional[str]:
    match = re.search(r'Name\s+([A-Za-z\s]+?)(?:Patient|Date|\n)', text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_patient_id(text: str) -> Optional[str]:
    match = re.search(r'Patient\s*ID[\s:]*([A-Z0-9]+)', text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_age(text: str) -> Optional[str]:
    match = re.search(r'Age[\s:]+(\d+y.*?)\s+Sex', text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_date(text: str) -> Optional[str]:
    match = re.search(r'Date[\s:]+(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_hemoglobin(lines: list) -> Optional[float]:
    for line in lines:
        if 'hemoglobin' not in line.lower():
            continue
        
        numbers = re.findall(r'\b(\d{1,2}(?:\.\d)?)\b', line)
        valid_results = [float(num) for num in numbers if 4 <= float(num) <= 18]
        
        if valid_results:
            return valid_results[0]
    
    return None


def _extract_blood_pressure(text: str) -> tuple[Optional[int], Optional[int]]:
    match = re.search(r'(BP|B\.P|Blood Pressure)[\s:]*([0-9]{2,3}\s*/\s*[0-9]{2,3})', text, re.IGNORECASE)
    if not match:
        return None, None
    
    bp_string = match.group(2).replace(" ", "")
    parts = bp_string.split("/")
    
    if len(parts) != 2:
        return None, None
    
    try:
        systolic = int(parts[0])
        diastolic = int(parts[1])
        
        if 70 <= systolic <= 200 and 40 <= diastolic <= 140:
            return systolic, diastolic
    except ValueError:
        pass
    
    return None, None


def _extract_gestational_age(text: str) -> Optional[int]:
    match = re.search(r'(GA|Gestational Age)[\s:]*([0-9]{1,2})\s*(weeks|wks)?', text, re.IGNORECASE)
    if not match:
        return None
    
    try:
        ga = int(match.group(2))
        return ga if 4 <= ga <= 42 else None
    except ValueError:
        return None


def _extract_proteinuria(text: str) -> Optional[str]:
    patterns = [
        r'Protein(?:uria)?[\s:]*(\d\+|\+{1,4}|negative|trace|nil)',
        r'Urine\s*Protein[\s:]*(\d\+|\+{1,4}|negative|trace|nil)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    
    return None


def _extract_weight(text: str) -> Optional[float]:
    match = re.search(r'Weight[\s:]*([0-9]{2,3}(?:\.\d)?)\s*kg', text, re.IGNORECASE)
    if not match:
        return None
    
    try:
        weight = float(match.group(1))
        return weight if 30 <= weight <= 150 else None
    except ValueError:
        return None


def _extract_fundal_height(text: str) -> Optional[int]:
    match = re.search(r'(Fundal Height|FH)[\s:]*([0-9]{2})\s*cm', text, re.IGNORECASE)
    if not match:
        return None
    
    try:
        fh = int(match.group(2))
        return fh if 10 <= fh <= 45 else None
    except ValueError:
        return None


def _extract_edema(text: str) -> Optional[bool]:
    patterns = [
        (r'Edema[\s:]*(\+{1,4}|present|yes)', True),
        (r'Swelling[\s:]*(\+{1,4}|present|yes)', True),
        (r'Edema[\s:]*(absent|no|nil)', False)
    ]
    
    for pattern, value in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return value
    
    return None

import os
import sys
from pathlib import Path
from PIL import Image
import pytesseract
import re
import json
from datetime import datetime

def extract_text_from_image(image_path):
    """Extract text using OCR"""
    print("Extracting text with OCR...")
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text

def parse_lab_values(text):
    """Parse lab values - improved for actual lab report format"""
    results = {}
    
    # Split into lines for better parsing
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Pattern: Test Name followed by numeric value
        # Examples: "Hemoglobin Fr 110-160" or "REC 33 3.5550"
        
        # Hemoglobin variants
        if re.search(r'hemoglobin|hb\s', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['hemoglobin'] = match.group(1)
        
        # RBC (Red Blood Cells)
        if re.search(r'\bREC\b|\bRBC\b', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d+)', line)
            if match:
                results['rbc'] = match.group(1)
        
        # Hematocrit (HCT/Her)
        if re.search(r'\bHer\b|\bHCT\b|\bhematocrit\b', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['hematocrit'] = match.group(1)
        
        # MCV
        if re.search(r'\bMcv\b|\bMCV\b', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['mcv'] = match.group(1)
        
        # MCH
        if re.search(r'\bMcH\b(?!c)|\bMCH\b(?!C)', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['mch'] = match.group(1)
        
        # MCHC
        if re.search(r'\bMcHc\b|\bMCHC\b', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['mchc'] = match.group(1)
        
        # RDW-CV
        if re.search(r'RDW.CV|RDW-CV', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['rdw_cv'] = match.group(1)
        
        # RDW-SD
        if re.search(r'RDW.?SD|RDWSD', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['rdw_sd'] = match.group(1)
        
        # WBC (White Blood Cells)
        if re.search(r'\bwee\b|\bWBC\b', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['wbc'] = match.group(1)
        
        # Neutrophils %
        if re.search(r'NEU%|neutrophil', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['neutrophils_percent'] = match.group(1)
        
        # Lymphocytes %
        if re.search(r'Lyme%|lymph%|lymphocyte', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['lymphocytes_percent'] = match.group(1)
        
        # Monocytes %
        if re.search(r'mony%|mono%|monocyte', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['monocytes_percent'] = match.group(1)
        
        # Eosinophils %
        if re.search(r'E0s%|EOS%|eosinophil', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['eosinophils_percent'] = match.group(1)
        
        # Basophils %
        if re.search(r'BAS%|basophil', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['basophils_percent'] = match.group(1)
        
        # Platelets
        if re.search(r'\bpur\b|\bPLT\b|\bplatelet', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['platelets'] = match.group(1)
        
        # ESR
        if re.search(r'\bESR\b', line, re.IGNORECASE):
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                results['esr'] = match.group(1)
    
    return results

def extract_patient_info(text):
    """Extract patient metadata"""
    info = {}
    
    # Patient Name
    name_match = re.search(r'Name\s+([A-Za-z\s]+)\s+Patient', text, re.IGNORECASE)
    if name_match:
        info['patient_name'] = name_match.group(1).strip()
    
    # Patient ID
    id_match = re.search(r'Patient ID\s+([A-Z0-9]+)', text, re.IGNORECASE)
    if id_match:
        info['patient_id'] = id_match.group(1)
    
    # Date
    date_match = re.search(r'Date\s+(\d{4}-\d{2}-\d{2})', text)
    if date_match:
        info['test_date'] = date_match.group(1)
    
    # Age
    age_match = re.search(r'Age\s+(\d+y\d+m\d+d|\d+)', text, re.IGNORECASE)
    if age_match:
        info['age'] = age_match.group(1)
    
    # Sex
    sex_match = re.search(r'Sex[.:\s]+([A-Za-z]+)', text, re.IGNORECASE)
    if sex_match:
        info['sex'] = sex_match.group(1)
    
    # Doctor
    doctor_match = re.search(r'Doctor\s+([A-Za-z\s]+)\s+', text, re.IGNORECASE)
    if doctor_match:
        info['doctor'] = doctor_match.group(1).strip()
    
    return info

def process_lab_report(image_path, patient_id=None):
    """Process a lab report image"""
    print(f"\n{'='*60}")
    print(f"Processing: {Path(image_path).name}")
    print(f"{'='*60}\n")
    
    # Extract text
    raw_text = extract_text_from_image(image_path)
    print(f"\nExtracted OCR Text:\n{'-'*60}")
    print(raw_text)
    print(f"{'-'*60}\n")
    
    # Extract patient info
    patient_info = extract_patient_info(raw_text)
    
    # Parse lab values
    print("Parsing lab values...")
    lab_values = parse_lab_values(raw_text)
    
    # Create result
    result = {
        'patient_info': patient_info,
        'image_path': str(image_path),
        'timestamp': datetime.now().isoformat(),
        'raw_ocr_text': raw_text,
        'extracted_values': lab_values
    }
    
    # Print patient info
    if patient_info:
        print("\n" + "="*60)
        print("PATIENT INFORMATION")
        print("="*60)
        for key, value in patient_info.items():
            print(f"  {key.replace('_', ' ').title():.<30} {value}")
    
    # Print results
    print("\n" + "="*60)
    print("EXTRACTED LAB VALUES")
    print("="*60)
    for key, value in lab_values.items():
        print(f"  {key.replace('_', ' ').upper():.<30} {value}")
    
    if not lab_values:
        print("  ⚠ No standard lab values detected")
    
    print(f"\n{'='*60}")
    print(f"Total values extracted: {len(lab_values)}")
    print(f"{'='*60}")
    
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: python test_image_extraction.py <image_path> [patient_id]")
        print("\nExample:")
        print("  python test_image_extraction.py D:\\MedGemma\\images\\test_card.png PATIENT001")
        sys.exit(1)
    
    image_path = sys.argv[1]
    patient_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(image_path).exists():
        print(f"❌ Error: Image not found: {image_path}")
        sys.exit(1)
    
    # Process image
    result = process_lab_report(image_path, patient_id)
    
    # Save results
    output_file = Path("D:/MedGemma") / (Path(image_path).stem + "_results.json")
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")

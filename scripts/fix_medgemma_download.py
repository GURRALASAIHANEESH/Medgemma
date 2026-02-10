"""
STEP 1 VALIDATION: Sanity test before clinical cases
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pregnancy_bridge.modules.medgemma_extractor import get_clinical_reasoner

print("="*70)
print("MEDGEMMA SANITY TEST - PLAIN TEXT INFERENCE")
print("="*70)

reasoner = get_clinical_reasoner()

# Simple medical explanation test
prompt = "Explain hemoglobin in pregnancy in simple medical terms."

print(f"\nPrompt: {prompt}\n")

inputs = reasoner.tokenizer(
    prompt,
    return_tensors="pt",
    truncation=True,
    max_length=1024
)

inputs = {k: v.to(reasoner.model.device) for k, v in inputs.items()}

print("Generating...")
import torch
with torch.no_grad():
    outputs = reasoner.model.generate(
        **inputs,
        max_new_tokens=120,
        do_sample=False,
        temperature=None,
        pad_token_id=reasoner.tokenizer.pad_token_id,
        eos_token_id=reasoner.tokenizer.eos_token_id
    )

response = reasoner.tokenizer.decode(
    outputs[0][inputs['input_ids'].shape[1]:],
    skip_special_tokens=True
)

print("\n" + "="*70)
print("OUTPUT:")
print("="*70)
print(response)
print("="*70)

# Check for success
has_unicode_garbage = any(ord(c) > 127 for c in response[:100])
has_medical_terms = any(term in response.lower() for term in 
                       ['hemoglobin', 'blood', 'oxygen', 'pregnancy', 'anemia', 'iron'])

print(f"\nUnicode garbage detected: {has_unicode_garbage}")
print(f"Medical terms present: {has_medical_terms}")

if not has_unicode_garbage and has_medical_terms:
    print("\n✓ SANITY TEST PASSED - Proceed to clinical tests")
else:
    print("\n✗ SANITY TEST FAILED - DO NOT PROCEED")

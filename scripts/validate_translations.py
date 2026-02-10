"""
ASHA Translation Validation Script
Checks for English leaks, phrase coverage, and translation quality
"""
import json
import re
from pathlib import Path
from typing import Dict, List

# English word pattern (rough heuristic)
ENGLISH_WORD_PATTERN = re.compile(r'\b[a-zA-Z]{3,}\b')

def load_phrase_library(path: Path) -> Dict:
    """Load ASHA phrase library"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def detect_english_leaks(text: str, language: str) -> List[str]:
    """Detect English words in non-English text (simple heuristic)"""
    if language == 'en':
        return []
    
    # Find potential English words
    matches = ENGLISH_WORD_PATTERN.findall(text)
    
    # Filter out medical terms that are acceptable in both languages
    acceptable_terms = {
        'BP', 'Hb', 'mmHg', 'g/dL', 'ANC', 'PHC', 'ASHA',
        'OK', 'Dr', 'mm', 'cm', 'kg', 'GA'
    }
    
    leaks = [w for w in matches if w not in acceptable_terms]
    return leaks

def validate_phrase_library(lib_path: Path) -> Dict:
    """Validate ASHA phrase library for completeness"""
    library = load_phrase_library(lib_path)
    
    results = {
        'total_phrases': 0,
        'languages': {},
        'missing_translations': [],
        'english_leaks': []
    }
    
    # Get phrases array from library
    phrases = library.get('phrases', [])
    
    for phrase_obj in phrases:
        results['total_phrases'] += 1
        phrase_id = phrase_obj.get('id', 'unknown')
        
        # Check all languages present
        for lang in ['en', 'hi', 'te']:
            if lang not in results['languages']:
                results['languages'][lang] = {'present': 0, 'missing': 0}
            
            if lang in phrase_obj and phrase_obj[lang]:
                results['languages'][lang]['present'] += 1
                
                # Check for English leaks in non-English
                if lang != 'en':
                    leaks = detect_english_leaks(phrase_obj[lang], lang)
                    if leaks:
                        results['english_leaks'].append({
                            'phrase_id': phrase_id,
                            'language': lang,
                            'text': phrase_obj[lang],
                            'leaked_words': leaks
                        })
            else:
                results['languages'][lang]['missing'] += 1
                results['missing_translations'].append({
                    'phrase_id': phrase_id,
                    'language': lang
                })
    
    # Calculate coverage percentages
    for lang in results['languages']:
        total = results['total_phrases']
        present = results['languages'][lang]['present']
        results['languages'][lang]['coverage_percent'] = (present / total * 100) if total > 0 else 0
    
    return results

def generate_validation_report(results: Dict, output_path: Path):
    """Generate CSV validation report"""
    import csv
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Summary section
        writer.writerow(['ASHA Phrase Library Validation Report'])
        writer.writerow(['Total Phrases', results['total_phrases']])
        writer.writerow([])
        
        # Language coverage
        writer.writerow(['Language', 'Phrases Present', 'Missing', 'Coverage %'])
        for lang, data in results['languages'].items():
            writer.writerow([
                lang.upper(),
                data['present'],
                data['missing'],
                f"{data['coverage_percent']:.1f}%"
            ])
        writer.writerow([])
        
        # Missing translations
        writer.writerow(['Missing Translations'])
        writer.writerow(['Phrase ID', 'Language'])
        for item in results['missing_translations']:
            writer.writerow([item['phrase_id'], item['language'].upper()])
        writer.writerow([])
        
        # English leaks
        writer.writerow(['English Leaks Detected'])
        writer.writerow(['Phrase ID', 'Language', 'Leaked Words', 'Full Text'])
        for item in results['english_leaks']:
            writer.writerow([
                item['phrase_id'],
                item['language'].upper(),
                ', '.join(item['leaked_words']),
                item['text'][:100]  # Truncate for readability
            ])
    
    print(f"✓ Validation report saved to {output_path}")

def main():
    project_root = Path(__file__).parent.parent
    lib_path = project_root / "data" / "i18n" / "asha_phrase_library.json"
    output_path = project_root / "data" / "i18n" / "asha_phrase_validation_report.csv"
    
    if not lib_path.exists():
        print(f"✗ Phrase library not found at {lib_path}")
        return
    
    print("Running ASHA phrase library validation...")
    results = validate_phrase_library(lib_path)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"ASHA Phrase Library Validation Summary")
    print(f"{'='*60}")
    print(f"Total phrases: {results['total_phrases']}")
    print(f"\nLanguage Coverage:")
    for lang, data in results['languages'].items():
        status = "✓" if data['coverage_percent'] >= 95 else "⚠"
        print(f"  {status} {lang.upper()}: {data['coverage_percent']:.1f}% ({data['present']}/{results['total_phrases']})")
    
    print(f"\nMissing translations: {len(results['missing_translations'])}")
    print(f"English leaks detected: {len(results['english_leaks'])}")
    
    # Generate report
    generate_validation_report(results, output_path)
    
    # Pass/Fail determination
    min_coverage = 95.0
    all_pass = all(
        data['coverage_percent'] >= min_coverage 
        for data in results['languages'].values()
    )
    
    if all_pass and len(results['english_leaks']) == 0:
        print(f"\n✓ PASS: All languages have ≥{min_coverage}% coverage and no English leaks")
    else:
        print(f"\n⚠ WARNING: Coverage below {min_coverage}% or English leaks detected")
        print(f"   Review {output_path} for details")

if __name__ == "__main__":
    main()

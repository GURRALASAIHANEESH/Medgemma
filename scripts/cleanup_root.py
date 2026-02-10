"""
Root Directory Cleanup Script
Moves remaining loose files to proper locations
Author: PregnancyBridge Team
Date: 2026-02-05
"""

import shutil
from pathlib import Path

REPO_ROOT = Path(r"D:\MedGemma")

def cleanup_root(dry_run=True):
    """Move loose files from root to proper locations."""
    
    moves = []
    
    # Files to move to outputs/validation/
    validation_files = [
        "competition_all_cases_20260204_115609.json",
        "competition_case_1_platelet_drop_+_proteinuria_(hellp_risk).json",
        "competition_case_2_progressive_anemia_+_respiratory_symptoms.json",
        "competition_case_3_multi-lab_abnormality_+_infection_symptoms.json",
        "competition_case_4_progressive_bp_+_neurological_symptoms.json",
        "REAL_RESULT.json",
        "SIMPLE_RESULT.json",
        "test_card_results.json",
        "test_results_20260204_102613.json",
        "test_results_20260204_105328.json",
        "validation_results_v2_20260205_090558.json",
    ]
    
    # Files to move to scripts/ (already exist, but remove from root)
    script_files = [
        "competition_pipeline.py",
        "competition_pipeline_v2.py",
        "config_medgemma.py",
        "demo_pregnancy_bridge.py",
        "fix_medgemma_download.py",
        "ocr_test.py",
        "process_image_now.py",
        "quickload.py",
        "run_full_validation.py",
        "run_full_validation_v2.py",
        "test_clinical_reasoning.py",
        "test_real_world.py",
        "test_symptom_escalation.py",
        "test_ultrasound_vision.py",
    ]
    
    # Files to DELETE (duplicates or temp)
    files_to_delete = [
        "Filest1.json",
        "Filest2.json",
        "Filest3.json",
    ]
    
    # Files to keep at root (documentation/config)
    keep_at_root = [
        "requirements.txt",
        "README.md",
        "LICENSE",
        "refactor_report.json",
        "import_updates_report.txt",
    ]
    
    print("="*70)
    print("Root Directory Cleanup")
    print("="*70)
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print("="*70)
    
    # Move validation files
    print("\n1. Moving validation files to outputs/validation/")
    for filename in validation_files:
        src = REPO_ROOT / filename
        dst = REPO_ROOT / "outputs" / "validation" / filename
        
        if src.exists():
            if dst.exists():
                print(f"  ✓ {filename} (already in outputs/validation/)")
                if not dry_run:
                    src.unlink()  # Delete duplicate at root
                moves.append(('delete_duplicate', src))
            else:
                print(f"  → {filename} → outputs/validation/")
                if not dry_run:
                    shutil.move(src, dst)
                moves.append(('move', src, dst))
    
    # Remove duplicate scripts (already copied to scripts/)
    print("\n2. Removing duplicate script files (originals in scripts/)")
    for filename in script_files:
        src = REPO_ROOT / filename
        dst = REPO_ROOT / "scripts" / filename
        
        if src.exists() and dst.exists():
            print(f"  ✗ {filename} (duplicate, keeping scripts/ version)")
            if not dry_run:
                src.unlink()
            moves.append(('delete_duplicate', src))
    
    # Delete temp/test files
    print("\n3. Deleting temporary files")
    for filename in files_to_delete:
        src = REPO_ROOT / filename
        if src.exists():
            print(f"  ✗ {filename} (temporary file)")
            if not dry_run:
                src.unlink()
            moves.append(('delete', src))
    
    # Move old folders to archive
    print("\n4. Archiving old folders")
    old_folders = ["modules", "summaries", "test", "images", "test_real_data"]
    archive_dir = REPO_ROOT / "archive_old_structure"
    
    if not dry_run:
        archive_dir.mkdir(exist_ok=True)
    
    for folder in old_folders:
        src = REPO_ROOT / folder
        dst = archive_dir / folder
        
        if src.exists() and src.is_dir():
            print(f"  → {folder}/ → archive_old_structure/{folder}/")
            if not dry_run:
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.move(src, dst)
            moves.append(('archive', src, dst))
    
    # Summary
    print("\n" + "="*70)
    print("CLEANUP SUMMARY")
    print("="*70)
    print(f"Files moved to outputs/: {len([m for m in moves if m[0] == 'move'])}")
    print(f"Duplicates removed: {len([m for m in moves if m[0] == 'delete_duplicate'])}")
    print(f"Temp files deleted: {len([m for m in moves if m[0] == 'delete'])}")
    print(f"Folders archived: {len([m for m in moves if m[0] == 'archive'])}")
    print("="*70)
    
    if dry_run:
        print("\n[DRY RUN] No changes made. Run with --execute to apply.")
    else:
        print("\n✓ Cleanup complete!")
        print("\nFinal root directory should contain:")
        print("  - README.md")
        print("  - requirements.txt")
        print("  - LICENSE")
        print("  - refactor_report.json")
        print("  - import_updates_report.txt")
        print("  - src/, data/, tests/, scripts/, outputs/, docs/, schemas/")
        print("  - model_offload/, venv/, __pycache__/")
    
    return moves


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up root directory")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    parser.add_argument('--execute', action='store_true', help='Execute the cleanup')
    
    args = parser.parse_args()
    
    if not args.execute:
        args.dry_run = True
    
    cleanup_root(dry_run=args.dry_run)


if __name__ == "__main__":
    main()

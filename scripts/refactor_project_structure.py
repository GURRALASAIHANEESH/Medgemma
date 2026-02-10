"""
PregnancyBridge Project Structure Refactoring Script
Author: PregnancyBridge Team
Date: 2026-02-05
Version: 1.0.0
"""

import os
import shutil
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Base paths
REPO_ROOT = Path(r"D:\MedGemma")
BACKUP_ROOT = Path(r"D:\MedGemma_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))

class RefactorManager:
    """Manages the refactoring process with dry-run support."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.moves_log = []
        self.errors_log = []
        
    def log_move(self, src: Path, dst: Path):
        """Log a file move operation."""
        self.moves_log.append({
            'source': str(src),
            'destination': str(dst),
            'timestamp': datetime.now().isoformat()
        })
        
    def log_error(self, operation: str, error: str):
        """Log an error."""
        self.errors_log.append({
            'operation': operation,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
    
    def create_backup(self):
        """Step 1: Create complete backup of current repository."""
        print("\n" + "="*70)
        print("STEP 1: Creating Backup")
        print("="*70)
        
        if self.dry_run:
            print(f"[DRY RUN] Would create backup at: {BACKUP_ROOT}")
            return
        
        try:
            print(f"Creating backup at: {BACKUP_ROOT}")
            shutil.copytree(REPO_ROOT, BACKUP_ROOT, 
                          ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git', 'venv', 'node_modules'))
            print(f"✓ Backup created successfully")
            
            # Create zip archive
            backup_zip = f"{BACKUP_ROOT}.zip"
            shutil.make_archive(str(BACKUP_ROOT), 'zip', BACKUP_ROOT)
            print(f"✓ Backup archived to: {backup_zip}")
            
        except Exception as e:
            self.log_error("create_backup", str(e))
            print(f"✗ Backup failed: {e}")
            raise
    
    def create_target_structure(self):
        """Step 2: Create target directory structure."""
        print("\n" + "="*70)
        print("STEP 2: Creating Target Structure")
        print("="*70)
        
        target_dirs = [
            "src/pregnancy_bridge",
            "src/pregnancy_bridge/modules",
            "src/pregnancy_bridge/config",
            "data/i18n",
            "data/patient_history",
            "data/lab_reports",
            "data/images",
            "tests/unit",
            "tests/integration",
            "scripts",
            "outputs/summaries",
            "outputs/validation",
            "docs",
            "schemas",
            "src/pregnancy_bridge/deprecated"
        ]
        
        for dir_path in target_dirs:
            full_path = REPO_ROOT / dir_path
            if self.dry_run:
                print(f"[DRY RUN] Would create: {full_path}")
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"✓ Created: {dir_path}")
                
                # Create __init__.py for Python packages
                if 'src/' in dir_path and not dir_path.endswith('config'):
                    init_file = full_path / "__init__.py"
                    if not init_file.exists():
                        init_file.write_text('"""PregnancyBridge package."""\n')
    
    def move_modules(self):
        """Step 3: Move module files to src/pregnancy_bridge/modules/."""
        print("\n" + "="*70)
        print("STEP 3: Moving Module Files")
        print("="*70)
        
        modules_src = REPO_ROOT / "modules"
        modules_dst = REPO_ROOT / "src" / "pregnancy_bridge" / "modules"
        deprecated_dst = REPO_ROOT / "src" / "pregnancy_bridge" / "deprecated"
        
        if not modules_src.exists():
            print(f"✗ Source modules directory not found: {modules_src}")
            return
        
        # List all .py files
        module_files = list(modules_src.glob("*.py"))
        
        for src_file in module_files:
            # Handle version conflicts
            if 'v1' in src_file.stem and (modules_src / f"{src_file.stem.replace('_v1', '_v2')}.py").exists():
                # Move v1 to deprecated
                dst_file = deprecated_dst / src_file.name
                print(f"  → {src_file.name} → deprecated/ (superseded by v2)")
            else:
                dst_file = modules_dst / src_file.name
                print(f"  → {src_file.name}")
            
            if not self.dry_run:
                shutil.copy2(src_file, dst_file)
            
            self.log_move(src_file, dst_file)
        
        print(f"✓ Moved {len(module_files)} module files")
    
    def move_data_files(self):
        """Step 4: Reorganize data files."""
        print("\n" + "="*70)
        print("STEP 4: Moving Data Files")
        print("="*70)
        
        # Move asha_phrase_library.json
        src = REPO_ROOT / "data" / "asha_phrase_library.json"
        dst = REPO_ROOT / "data" / "i18n" / "asha_phrase_library.json"
        if src.exists():
            print(f"  → {src.relative_to(REPO_ROOT)} → {dst.relative_to(REPO_ROOT)}")
            if not self.dry_run:
                shutil.copy2(src, dst)
            self.log_move(src, dst)
        
        # Move record_*.json files
        for record_file in (REPO_ROOT / "data").glob("record_*.json"):
            dst = REPO_ROOT / "data" / "patient_history" / record_file.name
            print(f"  → {record_file.relative_to(REPO_ROOT)} → {dst.relative_to(REPO_ROOT)}")
            if not self.dry_run:
                if not dst.exists():  # Don't overwrite existing
                    shutil.copy2(record_file, dst)
            self.log_move(record_file, dst)
        
        # Move sample_records.json
        src = REPO_ROOT / "data" / "sample_records.json"
        dst = REPO_ROOT / "data" / "patient_history" / "sample_records.json"
        if src.exists():
            print(f"  → {src.relative_to(REPO_ROOT)} → {dst.relative_to(REPO_ROOT)}")
            if not self.dry_run:
                if not dst.exists():
                    shutil.copy2(src, dst)
            self.log_move(src, dst)
    
    def move_images(self):
        """Step 5: Consolidate image files."""
        print("\n" + "="*70)
        print("STEP 5: Moving Image Files")
        print("="*70)
        
        # Move from images/
        images_src = REPO_ROOT / "images"
        images_dst = REPO_ROOT / "data" / "images"
        
        if images_src.exists():
            for img_file in images_src.glob("*.*"):
                dst = images_dst / img_file.name
                print(f"  → images/{img_file.name} → data/images/{img_file.name}")
                if not self.dry_run:
                    shutil.copy2(img_file, dst)
                self.log_move(img_file, dst)
        
        # Move from test_real_data/
        test_data_src = REPO_ROOT / "test_real_data"
        if test_data_src.exists():
            for img_file in test_data_src.glob("*.*"):
                dst = images_dst / img_file.name
                print(f"  → test_real_data/{img_file.name} → data/images/{img_file.name}")
                if not self.dry_run:
                    if not dst.exists():  # Don't overwrite
                        shutil.copy2(img_file, dst)
                self.log_move(img_file, dst)
    
    def move_tests(self):
        """Step 6: Organize test files."""
        print("\n" + "="*70)
        print("STEP 6: Moving Test Files")
        print("="*70)
        
        test_files = [
            ("test_clinical_reasoning.py", "tests/integration/test_clinical_reasoning.py"),
            ("test_symptom_escalation.py", "tests/integration/test_symptom_escalation.py"),
            ("test_real_world.py", "tests/integration/test_real_world.py"),
            ("ocr_test.py", "tests/integration/test_ocr.py"),
            ("test/test_medgemma_extraction.py", "tests/integration/test_medgemma_extraction.py"),
            ("test/test_model.py", "tests/integration/test_model.py"),
        ]
        
        for src_rel, dst_rel in test_files:
            src = REPO_ROOT / src_rel
            dst = REPO_ROOT / dst_rel
            if src.exists():
                print(f"  → {src_rel} → {dst_rel}")
                if not self.dry_run:
                    shutil.copy2(src, dst)
                self.log_move(src, dst)
    
    def move_scripts(self):
        """Step 7: Move scripts to scripts/ folder."""
        print("\n" + "="*70)
        print("STEP 7: Moving Script Files")
        print("="*70)
        
        # Scripts to move (already in scripts/ - just document)
        script_files = [
            "competition_pipeline.py",
            "competition_pipeline_v2.py",
            "demo_pregnancy_bridge.py",
            "run_full_validation.py",
            "run_full_validation_v2.py",
            "quickload.py",
            "fix_medgemma_download.py",
            "config_medgemma.py",
            "test_ultrasound_vision.py",
            "process_image_now.py",
            "test_real_world.py",
            "SIMPLE_IMAGE_TEST.py"
        ]
        
        for script_name in script_files:
            src = REPO_ROOT / script_name
            dst = REPO_ROOT / "scripts" / script_name
            if src.exists() and not dst.exists():
                print(f"  → {script_name} → scripts/{script_name}")
                if not self.dry_run:
                    shutil.copy2(src, dst)
                self.log_move(src, dst)
    
    def move_outputs(self):
        """Step 8: Move output files."""
        print("\n" + "="*70)
        print("STEP 8: Moving Output Files")
        print("="*70)
        
        # Move JSON results to outputs/validation/
        for json_file in REPO_ROOT.glob("*RESULT*.json"):
            dst = REPO_ROOT / "outputs" / "validation" / json_file.name
            print(f"  → {json_file.name} → outputs/validation/{json_file.name}")
            if not self.dry_run:
                shutil.copy2(json_file, dst)
            self.log_move(json_file, dst)
        
        # Move test results
        for json_file in REPO_ROOT.glob("test_results_*.json"):
            dst = REPO_ROOT / "outputs" / "validation" / json_file.name
            print(f"  → {json_file.name} → outputs/validation/{json_file.name}")
            if not self.dry_run:
                shutil.copy2(json_file, dst)
            self.log_move(json_file, dst)
        
        # Move competition case JSONs
        for json_file in REPO_ROOT.glob("competition_*.json"):
            dst = REPO_ROOT / "outputs" / "validation" / json_file.name
            print(f"  → {json_file.name} → outputs/validation/{json_file.name}")
            if not self.dry_run:
                shutil.copy2(json_file, dst)
            self.log_move(json_file, dst)
        
        # Move summaries
        summaries_src = REPO_ROOT / "summaries"
        summaries_dst = REPO_ROOT / "outputs" / "summaries"
        if summaries_src.exists():
            for txt_file in summaries_src.glob("*.txt"):
                dst = summaries_dst / txt_file.name
                print(f"  → summaries/{txt_file.name} → outputs/summaries/{txt_file.name}")
                if not self.dry_run:
                    shutil.copy2(txt_file, dst)
                self.log_move(txt_file, dst)
    
    def move_config(self):
        """Step 9: Move config files."""
        print("\n" + "="*70)
        print("STEP 9: Moving Config Files")
        print("="*70)
        
        src = REPO_ROOT / "config_medgemma.py"
        dst = REPO_ROOT / "src" / "pregnancy_bridge" / "config" / "config_medgemma.py"
        if src.exists():
            print(f"  → config_medgemma.py → src/pregnancy_bridge/config/config_medgemma.py")
            if not self.dry_run:
                shutil.copy2(src, dst)
            self.log_move(src, dst)
    
    def create_deprecated_readme(self):
        """Create README in deprecated folder."""
        if self.dry_run:
            return
        
        readme_path = REPO_ROOT / "src" / "pregnancy_bridge" / "deprecated" / "README.md"
        content = """# Deprecated Modules

This folder contains deprecated versions of modules that have been superseded by newer versions.

## Files

- `confidence_estimator_v1.py` - Superseded by `confidence_estimator_v2.py`
  - v2 adds lab age penalty and improved temporal reasoning
  - v1 kept for reference only

**Do not import or use these modules in production code.**
"""
        readme_path.write_text(content)
        print("✓ Created deprecated/README.md")
    
    def generate_report(self):
        """Generate refactor report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'moves_count': len(self.moves_log),
            'errors_count': len(self.errors_log),
            'moves': self.moves_log,
            'errors': self.errors_log
        }
        
        report_file = REPO_ROOT / "refactor_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✓ Report saved to: {report_file}")
        return report


def main():
    """Main refactor execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Refactor PregnancyBridge project structure")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--execute', action='store_true', help='Execute the refactoring')
    
    args = parser.parse_args()
    
    if not args.execute:
        args.dry_run = True
    
    print("="*70)
    print("PregnancyBridge Project Structure Refactoring")
    print("="*70)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'EXECUTE'}")
    print(f"Repository: {REPO_ROOT}")
    print("="*70)
    
    manager = RefactorManager(dry_run=args.dry_run)
    
    try:
        manager.create_backup()
        manager.create_target_structure()
        manager.move_modules()
        manager.move_data_files()
        manager.move_images()
        manager.move_tests()
        manager.move_scripts()
        manager.move_outputs()
        manager.move_config()
        manager.create_deprecated_readme()
        
        report = manager.generate_report()
        
        print("\n" + "="*70)
        print("REFACTORING SUMMARY")
        print("="*70)
        print(f"Files moved: {report['moves_count']}")
        print(f"Errors: {report['errors_count']}")
        print("="*70)
        
        if not args.dry_run:
            print("\n✓ Refactoring completed successfully!")
            print("\nNext steps:")
            print("1. Review refactor_report.json")
            print("2. Update imports in scripts")
            print("3. Run validation tests")
        
    except Exception as e:
        print(f"\n✗ Refactoring failed: {e}")
        raise


if __name__ == "__main__":
    main()

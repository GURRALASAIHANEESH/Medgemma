"""
Import Path Updater for PregnancyBridge Refactoring
Automatically updates import statements in all Python files
Author: PregnancyBridge Team
Date: 2026-02-05
"""

import re
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(r"D:\MedGemma")

class ImportUpdater:
    """Updates import statements to use new package structure."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.files_updated = []
        self.changes_made = []
        
    def update_single_script(self, script_path: Path) -> int:
        """Update imports in a single script file."""
        if not script_path.exists():
            return 0
        
        content = script_path.read_text(encoding='utf-8')
        original_content = content
        changes = 0
        
        # Pattern 1: from modules.xxx import yyy
        # Replace with: from pregnancy_bridge.modules.xxx import yyy
        pattern1 = r'from modules\.(\w+) import'
        replacement1 = r'from pregnancy_bridge.modules.\1 import'
        content, count1 = re.subn(pattern1, replacement1, content)
        changes += count1
        
        # Pattern 2: import modules.xxx
        # Replace with: import pregnancy_bridge.modules.xxx
        pattern2 = r'import modules\.(\w+)'
        replacement2 = r'import pregnancy_bridge.modules.\1'
        content, count2 = re.subn(pattern2, replacement2, content)
        changes += count2
        
        # Pattern 3: sys.path.insert with modules path - update to include src
        if 'sys.path.insert' in content:
            # Check if we need to add src path
            if 'src' not in content or 'pregnancy_bridge' not in content:
                # Find sys.path.insert lines and add src path
                lines = content.split('\n')
                new_lines = []
                path_added = False
                
                for i, line in enumerate(lines):
                    new_lines.append(line)
                    # Add src path after first sys.path.insert
                    if 'sys.path.insert' in line and not path_added and 'src' not in line:
                        indent = len(line) - len(line.lstrip())
                        new_line = ' ' * indent + "sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))"
                        new_lines.append(new_line)
                        changes += 1
                        path_added = True
                
                content = '\n'.join(new_lines)
        
        # Save if changes were made
        if changes > 0 and content != original_content:
            if not self.dry_run:
                script_path.write_text(content, encoding='utf-8')
            
            self.files_updated.append(str(script_path.relative_to(REPO_ROOT)))
            self.changes_made.append({
                'file': str(script_path.relative_to(REPO_ROOT)),
                'changes': changes
            })
            
            print(f"  ✓ {script_path.name}: {changes} import(s) updated")
        
        return changes
    
    def update_all_scripts(self):
        """Update imports in all script files."""
        print("\n" + "="*70)
        print("Updating Script Imports")
        print("="*70)
        
        scripts_dir = REPO_ROOT / "scripts"
        total_changes = 0
        files_processed = 0
        
        for script_file in scripts_dir.glob("*.py"):
            if script_file.name in ['refactor_project_structure.py', 'update_imports.py']:
                continue  # Skip utility scripts
            
            changes = self.update_single_script(script_file)
            total_changes += changes
            files_processed += 1
        
        print(f"\n✓ Processed {files_processed} scripts, {total_changes} changes total")
    
    def update_module_imports(self):
        """Update imports within module files."""
        print("\n" + "="*70)
        print("Updating Module Imports")
        print("="*70)
        
        modules_dir = REPO_ROOT / "src" / "pregnancy_bridge" / "modules"
        
        if not modules_dir.exists():
            print(f"✗ Modules directory not found: {modules_dir}")
            return
        
        total_changes = 0
        files_processed = 0
        
        for module_file in modules_dir.glob("*.py"):
            if module_file.name == '__init__.py':
                continue
            
            content = module_file.read_text(encoding='utf-8')
            original_content = content
            changes = 0
            
            # Pattern: from modules.xxx import yyy
            # Replace with: from pregnancy_bridge.modules.xxx import yyy
            pattern = r'from modules\.(\w+) import'
            replacement = r'from pregnancy_bridge.modules.\1 import'
            content, count = re.subn(pattern, replacement, content)
            changes += count
            
            # Pattern: import modules.xxx as yyy
            pattern2 = r'import modules\.(\w+)'
            replacement2 = r'import pregnancy_bridge.modules.\1'
            content, count2 = re.subn(pattern2, replacement2, content)
            changes += count2
            
            if changes > 0 and content != original_content:
                if not self.dry_run:
                    module_file.write_text(content, encoding='utf-8')
                
                print(f"  ✓ {module_file.name}: {changes} import(s) updated")
                total_changes += changes
                files_processed += 1
                self.files_updated.append(str(module_file.relative_to(REPO_ROOT)))
        
        print(f"\n✓ Processed {files_processed} modules, {total_changes} changes")
    
    def update_test_imports(self):
        """Update imports in test files."""
        print("\n" + "="*70)
        print("Updating Test Imports")
        print("="*70)
        
        tests_dir = REPO_ROOT / "tests" / "integration"
        
        if not tests_dir.exists():
            print(f"✗ Tests directory not found: {tests_dir}")
            return
        
        total_changes = 0
        files_processed = 0
        
        for test_file in tests_dir.glob("*.py"):
            changes = self.update_single_script(test_file)
            total_changes += changes
            if changes > 0:
                files_processed += 1
        
        print(f"\n✓ Processed {files_processed} test files, {total_changes} changes")
    
    def update_data_paths(self):
        """Update hardcoded data paths."""
        print("\n" + "="*70)
        print("Updating Data Paths")
        print("="*70)
        
        changes_made = 0
        
        # Update asha_phrase_composer.py to use new path
        composer_path = REPO_ROOT / "src" / "pregnancy_bridge" / "modules" / "asha_phrase_composer.py"
        if composer_path.exists():
            content = composer_path.read_text(encoding='utf-8')
            original = content
            
            # Old path pattern
            content = content.replace('data/asha_phrase_library.json', 'data/i18n/asha_phrase_library.json')
            
            if content != original:
                if not self.dry_run:
                    composer_path.write_text(content, encoding='utf-8')
                
                print(f"  ✓ Updated asha_phrase_composer.py data path")
                changes_made += 1
        
        # Update any other files with old data paths
        for py_file in (REPO_ROOT / "src").rglob("*.py"):
            content = py_file.read_text(encoding='utf-8')
            original = content
            
            # Check for old paths
            content = content.replace('data/asha_phrase_library.json', 'data/i18n/asha_phrase_library.json')
            
            if content != original:
                if not self.dry_run:
                    py_file.write_text(content, encoding='utf-8')
                
                print(f"  ✓ Updated {py_file.name}")
                changes_made += 1
        
        print(f"\n✓ Updated {changes_made} data paths")
    
    def generate_report(self):
        """Generate import update report."""
        report_path = REPO_ROOT / "import_updates_report.txt"
        
        report_lines = [
            "="*70,
            "Import Update Report",
            "="*70,
            f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}",
            f"Files Updated: {len(self.files_updated)}",
            "",
            "Changes Made:",
            "-"*70
        ]
        
        for change in self.changes_made:
            report_lines.append(f"  {change['file']}: {change['changes']} changes")
        
        if not self.changes_made:
            report_lines.append("  No changes needed")
        
        report_lines.extend([
            "",
            "="*70,
            "Updated Files:",
            "-"*70
        ])
        
        for file in self.files_updated:
            report_lines.append(f"  - {file}")
        
        if not self.files_updated:
            report_lines.append("  No files updated")
        
        report_content = '\n'.join(report_lines)
        
        if not self.dry_run:
            report_path.write_text(report_content)
            print(f"\n✓ Report saved to: {report_path}")
        else:
            print("\n[DRY RUN] Report not saved")


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Update import paths after refactoring")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed')
    parser.add_argument('--execute', action='store_true', help='Execute the updates')
    
    args = parser.parse_args()
    
    if not args.execute:
        args.dry_run = True
    
    print("="*70)
    print("PregnancyBridge Import Path Updater")
    print("="*70)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'EXECUTE'}")
    print("="*70)
    
    updater = ImportUpdater(dry_run=args.dry_run)
    
    updater.update_all_scripts()
    updater.update_module_imports()
    updater.update_test_imports()
    updater.update_data_paths()
    updater.generate_report()
    
    print("\n" + "="*70)
    print("Import Update Complete")
    print("="*70)


if __name__ == "__main__":
    main()

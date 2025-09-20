#!/usr/bin/env python3
"""
Fix all hardcoded sys.path modifications in test files
Replace with proper package imports
"""

import os
import re
from pathlib import Path


def fix_test_file(file_path: Path):
    """Remove hardcoded sys.path modifications from a test file"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Remove sys.path.append lines
    content = re.sub(
        r'^import sys\n.*sys\.path\.append.*\n', 
        '', 
        content, 
        flags=re.MULTILINE
    )
    
    content = re.sub(
        r'^sys\.path\.append.*\n', 
        '', 
        content, 
        flags=re.MULTILINE
    )
    
    # Add proper import for local API if needed
    if 'from api.main import' in content and 'import sys' not in content:
        # Add the import at the top after other imports
        lines = content.split('\n')
        import_index = 0
        
        # Find where to insert the import
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i + 1
            elif line.strip() == '' and import_index > 0:
                break
        
        # Insert the comment about running from project root
        lines.insert(import_index, "# Note: Run this test from the custom-trading directory")
        content = '\n'.join(lines)
    
    # Only write if content changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed: {file_path}")
        return True
    
    return False


def main():
    """Fix all test files in the tests directory"""
    
    tests_dir = Path(__file__).parent.parent / "tests"
    
    if not tests_dir.exists():
        print(f"Tests directory not found: {tests_dir}")
        return
    
    fixed_count = 0
    
    for test_file in tests_dir.glob("test_*.py"):
        if fix_test_file(test_file):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} test files")
    print("\nAll test files now use proper imports!")
    print("Run tests from the custom-trading directory:")
    print("  cd custom-trading")
    print("  python -m pytest tests/")


if __name__ == "__main__":
    main()
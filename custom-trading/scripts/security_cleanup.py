#!/usr/bin/env python3
"""
SECURITY CLEANUP SCRIPT
Remove hardcoded credentials from all test files and documentation
"""

import os
import re
from pathlib import Path


# Sensitive data patterns to remove
SENSITIVE_PATTERNS = {
    'degiro_username': r'bastiheye',
    'degiro_password': r'!c3c6kdG5j6NFB7R',
    'totp_secret': r'5ADDODASZT7CHKD273VFMJMJZNAUHVBH',
    'int_account': r'31043411',
    'api_key': r'pjFJKB-iEd3_HOLchTcxglzV1yn27QncyzDQAhOhf1Y',
}

# Replacement mappings
REPLACEMENTS = {
    'bastiheye': 'os.getenv("DEGIRO_USERNAME")',
    '"!c3c6kdG5j6NFB7R"': 'os.getenv("DEGIRO_PASSWORD")',
    '"5ADDODASZT7CHKD273VFMJMJZNAUHVBH"': 'os.getenv("DEGIRO_TOTP_SECRET")',
    '31043411': 'int(os.getenv("DEGIRO_INT_ACCOUNT", 0))',
    'pjFJKB-iEd3_HOLchTcxglzV1yn27QncyzDQAhOhf1Y': 'os.getenv("TRADING_API_KEY")',
}


def clean_file(file_path: Path) -> bool:
    """Clean a single file of hardcoded credentials"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = False
        
        # Apply replacements
        for old_value, new_value in REPLACEMENTS.items():
            if old_value in content:
                content = content.replace(f'"{old_value}"', new_value)
                content = content.replace(f"'{old_value}'", new_value)
                content = content.replace(old_value, new_value)
                changes_made = True
        
        # Ensure os import is present if we added os.getenv calls
        if 'os.getenv(' in content and 'import os' not in content:
            lines = content.split('\\n')
            # Find insertion point after existing imports
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_index = i + 1
                elif line.strip() == '' and insert_index > 0:
                    break
            
            lines.insert(insert_index, 'import os')
            content = '\\n'.join(lines)
            changes_made = True
        
        # Write back if changes were made
        if changes_made:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error cleaning {file_path}: {e}")
        return False


def main():
    """Clean all files in the project"""
    print("🔐 SECURITY CLEANUP - Removing Hardcoded Credentials")
    print("=" * 55)
    
    project_root = Path(__file__).parent.parent
    files_cleaned = 0
    
    # Files to clean
    patterns_to_check = [
        "tests/test_*.py",
        "docs/*.md",
        "api/*.py",
        "*.py"
    ]
    
    all_files = set()
    for pattern in patterns_to_check:
        all_files.update(project_root.glob(pattern))
    
    print(f"📁 Scanning {len(all_files)} files for security issues...")
    
    for file_path in sorted(all_files):
        if file_path.name == __file__.split('/')[-1]:  # Skip this script
            continue
            
        if clean_file(file_path):
            print(f"🔧 Cleaned: {file_path.relative_to(project_root)}")
            files_cleaned += 1
    
    print(f"\\n📊 Summary:")
    print(f"   🔧 Files cleaned: {files_cleaned}")
    print(f"   🛡️  Credentials removed from code")
    print(f"   ✅ Environment variable usage enforced")
    
    if files_cleaned > 0:
        print(f"\\n⚠️  IMPORTANT NEXT STEPS:")
        print(f"   1. Set environment variables in your shell:")
        print(f"      export DEGIRO_USERNAME='your_username'")
        print(f"      export DEGIRO_PASSWORD='your_password'")
        print(f"      export DEGIRO_TOTP_SECRET='your_totp_secret'")
        print(f"      export DEGIRO_INT_ACCOUNT='your_account_id'")
        print(f"      export TRADING_API_KEY='your_api_key'")
        print(f"   2. Update config/.env file with your credentials")
        print(f"   3. Verify tests still work with environment variables")
        print(f"   4. Commit these security fixes")
    else:
        print(f"\\n✅ No hardcoded credentials found!")
    
    return files_cleaned


if __name__ == "__main__":
    main()
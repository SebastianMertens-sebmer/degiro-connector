#!/usr/bin/env python3
"""Script to fix Python 3.10+ union syntax to be compatible with Python 3.9"""

import os
import re
import glob

# Get all Python files in src/degiro_connector
files_to_fix = []
for root, dirs, files in os.walk("src/degiro_connector"):
    for file in files:
        if file.endswith(".py"):
            files_to_fix.append(os.path.join(root, file))

print(f"Found {len(files_to_fix)} Python files to check")

# Pattern to match union syntax like "dict | None", "int | str", etc.
union_pattern = re.compile(r'([a-zA-Z_][a-zA-Z0-9_\[\]]*)\s*\|\s*([a-zA-Z_][a-zA-Z0-9_\[\]]*)')

fixed_count = 0
for file_path in files_to_fix:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Add Optional import if not present and we have union with None
        if '| None' in content and 'from typing import' not in content and 'import typing' not in content:
            # Find the import section and add Optional
            import_lines = []
            other_lines = []
            in_imports = True
            
            for line in content.split('\n'):
                if in_imports and (line.startswith('import ') or line.startswith('from ') or line.strip() == ''):
                    import_lines.append(line)
                else:
                    in_imports = False
                    other_lines.append(line)
            
            # Add Optional import
            if 'from typing import' in '\n'.join(import_lines):
                # Find the typing import and add Optional
                for i, line in enumerate(import_lines):
                    if line.startswith('from typing import'):
                        if 'Optional' not in line:
                            import_lines[i] = line.rstrip() + ', Optional'
                        break
            else:
                # Add new typing import
                import_lines.insert(-1, 'from typing import Optional')
            
            content = '\n'.join(import_lines + other_lines)
        
        # Replace union syntax with Optional/Union
        def replace_union(match):
            left, right = match.groups()
            if right == 'None':
                return f'Optional[{left}]'
            else:
                return f'Union[{left}, {right}]'
        
        new_content = union_pattern.sub(replace_union, content)
        
        # If we used Union, make sure it's imported
        if 'Union[' in new_content and 'Union' not in content:
            if 'from typing import' in new_content:
                new_content = re.sub(
                    r'from typing import ([^,\n]+(?:, [^,\n]+)*)',
                    lambda m: f"from typing import {m.group(1)}, Union" if 'Union' not in m.group(1) else m.group(0),
                    new_content
                )
            else:
                new_content = re.sub(
                    r'(from typing import [^\n]+)',
                    r'\1, Union',
                    new_content
                )
        
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed: {file_path}")
            fixed_count += 1
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

print(f"Fixed {fixed_count} files")
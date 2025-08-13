from typing import Any
#!/usr/bin/env python3
"""
Automatic typing import fixer
Finds and fixes missing typing imports in all Python files
"""

import os
import re
from pathlib import Path

def fix_typing_imports():
    """Find and fix all typing import issues"""
    fixed_files = []
    
    # Common typing imports that might be missing
    typing_patterns = {
        'Any': r'-> Any|: Any',
        'Dict': r'-> Dict\[|: Dict\[',
        'List': r'-> List\[|: List\[',
        'Set': r'-> Set\[|: Set\[',
        'Tuple': r'-> Tuple\[|: Tuple\[',
        'Optional': r'-> Optional\[|: Optional\[',
        'Union': r'-> Union\[|: Union\[',
        'Callable': r'-> Callable\[|: Callable\['
    }
    
    # Search all Python files
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', '.venv', 'dist']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Find missing typing imports
                    missing_imports = []
                    
                    for typing_name, pattern in typing_patterns.items():
                        if re.search(pattern, content):
                            # Check if it's already imported
                            import_pattern = f'from typing import.*{typing_name}'
                            if not re.search(import_pattern, content):
                                missing_imports.append(typing_name)
                    
                    if missing_imports:
                        # Fix the imports
                        fixed_content = fix_imports_in_content(content, missing_imports)
                        
                        if fixed_content != content:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(fixed_content)
                            
                            fixed_files.append({
                                'file': str(file_path),
                                'added_imports': missing_imports
                            })
                
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    return fixed_files

def fix_imports_in_content(content: str, missing_imports: list) -> str:
    """Fix typing imports in file content"""
    lines = content.split('\n')
    
    # Find the typing import line
    typing_import_line = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('from typing import'):
            typing_import_line = i
            break
    
    if typing_import_line >= 0:
        # Add missing imports to existing line
        current_line = lines[typing_import_line]
        
        # Extract current imports
        import_match = re.match(r'from typing import (.+)', current_line)
        if import_match:
            current_imports = [imp.strip() for imp in import_match.group(1).split(',')]
            
            # Add missing imports
            for missing in missing_imports:
                if missing not in current_imports:
                    current_imports.append(missing)
            
            # Reconstruct the import line
            new_import_line = f"from typing import {', '.join(sorted(current_imports))}"
            lines[typing_import_line] = new_import_line
    
    else:
        # Add new typing import line
        # Find a good place to insert it (after other imports)
        insert_line = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                insert_line = i + 1
            elif line.strip() == '' or line.strip().startswith('"""') or line.strip().startswith('#'):
                continue
            else:
                break
        
        new_import_line = f"from typing import {', '.join(sorted(missing_imports))}"
        lines.insert(insert_line, new_import_line)
    
    return '\n'.join(lines)

def main():
    """Main function"""
    print("🔧 Fixing typing import issues...")
    print()
    
    fixed_files = fix_typing_imports()
    
    if not fixed_files:
        print("✅ No typing import issues found!")
        return True
    
    print(f"Fixed typing imports in {len(fixed_files)} files:")
    print()
    
    for fix in fixed_files:
        print(f"📁 {fix['file']}")
        print(f"   Added: {', '.join(fix['added_imports'])}")
        print()
    
    print("🎉 All typing imports fixed!")
    print()
    print("✅ Try launching the game now:")
    print("   python main.py")
    
    return True

if __name__ == "__main__":
    success = main()
    
    import sys
    sys.exit(0 if success else 1)
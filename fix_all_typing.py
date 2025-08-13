from typing import Any
#!/usr/bin/env python3
"""
Script to find and fix all typing import issues
"""

import os
import re
from pathlib import Path

def find_typing_issues():
    """Find all files with potential typing issues"""
    issues = []
    
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
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if file uses typing annotations
                    for typing_name, pattern in typing_patterns.items():
                        if re.search(pattern, content):
                            # Check if it's imported
                            import_pattern = f'from typing import.*{typing_name}'
                            if not re.search(import_pattern, content):
                                issues.append({
                                    'file': file_path,
                                    'missing_import': typing_name,
                                    'pattern_found': pattern
                                })
                
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return issues

def main():
    """Main function"""
    print("Scanning for typing import issues...")
    
    issues = find_typing_issues()
    
    if not issues:
        print("✅ No typing import issues found!")
        return True
    
    print(f"Found {len(issues)} potential typing issues:")
    
    for issue in issues:
        print(f"  📁 {issue['file']}")
        print(f"     Missing: {issue['missing_import']}")
        print(f"     Pattern: {issue['pattern_found']}")
        print()
    
    return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("🎉 All typing imports look good!")
    else:
        print("⚠️  Found some potential issues. Check the files above.")
        print("💡 Most common fix: Add missing imports to 'from typing import ...' line")
    
    import sys
    sys.exit(0 if success else 1)
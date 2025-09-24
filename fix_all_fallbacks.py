#!/usr/bin/env python3
"""
Comprehensive fallback fixing script for Infra Mind.

This script systematically replaces all problematic fallback patterns with smart defaults.
"""

import os
import re
import glob
from pathlib import Path

# Problematic fallback patterns and their smart replacements
FALLBACK_PATTERNS = [
    # Unknown patterns
    (r'\.get\(([^,]+),\s*["\']unknown["\']\)', r'smart_get(\1)'),
    (r'\.get\(([^,]+),\s*["\']Unknown["\']\)', r'smart_get(\1)'),

    # Empty string patterns that should be smart
    (r'\.get\(([^,]+),\s*["\']["\']\)', r'smart_get(\1)'),

    # Default patterns that should be contextualized
    (r'\.get\(([^,]+),\s*["\']default["\']\)', r'smart_get(\1)'),

    # N/A patterns
    (r'\.get\(([^,]+),\s*["\']N/A["\']\)', r'smart_get(\1)'),
    (r'\.get\(([^,]+),\s*["\']n/a["\']\)', r'smart_get(\1)'),
]

# Files that need the smart_defaults import
IMPORT_PATTERN = r'(from \.\.\.core\.smart_defaults import smart_get, SmartDefaults)'
IMPORT_ADDITION = 'from ...core.smart_defaults import smart_get, SmartDefaults'

# For agents directory
AGENT_IMPORT_PATTERN = r'(from \.\.core\.smart_defaults import smart_get, SmartDefaults)'
AGENT_IMPORT_ADDITION = 'from ..core.smart_defaults import smart_get, SmartDefaults'

def add_smart_imports(file_path: str, content: str) -> str:
    """Add smart_defaults import if not present."""

    # Check if already imported
    if 'smart_get' in content:
        return content

    # Determine import pattern based on file location
    if '/agents/' in file_path:
        import_line = AGENT_IMPORT_ADDITION
        # Look for other relative imports in agents
        insert_pattern = r'(from \.\.models\.assessment import Assessment)'
    elif '/api/' in file_path:
        import_line = IMPORT_ADDITION
        # Look for auth import or models import
        insert_pattern = r'(from \.\.\.models\.[^\\n]+ import [^\\n]+)'
    else:
        # Core or other directories
        import_line = 'from .smart_defaults import smart_get, SmartDefaults'
        insert_pattern = r'(from \.[^\\n]+ import [^\\n]+)'

    # Find a good place to insert the import
    lines = content.split('\n')
    insert_index = -1

    for i, line in enumerate(lines):
        if line.strip().startswith('from ') and ('models' in line or 'Assessment' in line):
            insert_index = i + 1
            break

    if insert_index > 0:
        lines.insert(insert_index, import_line)
        return '\n'.join(lines)

    # Fallback: add after existing imports
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith('#') and not line.startswith('"""') and not line.startswith("'''"):
            if not line.startswith('from ') and not line.startswith('import '):
                lines.insert(i, import_line)
                return '\n'.join(lines)

    return content

def fix_fallbacks_in_file(file_path: str) -> bool:
    """Fix fallback patterns in a single file."""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Apply fallback pattern fixes
        for pattern, replacement in FALLBACK_PATTERNS:
            content = re.sub(pattern, replacement, content)

        # Add smart imports if we made changes
        if content != original_content:
            content = add_smart_imports(file_path, content)

        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed fallbacks in: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main execution function."""

    print("🔧 Starting comprehensive fallback fixing...")

    # Get the source directory
    src_dir = Path(__file__).parent / "src"

    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        return

    # Find all Python files
    python_files = []
    for pattern in ["**/*.py"]:
        python_files.extend(glob.glob(str(src_dir / pattern), recursive=True))

    print(f"📁 Found {len(python_files)} Python files to process")

    fixed_count = 0

    # Process each file
    for file_path in python_files:
        # Skip test files and __pycache__
        if '__pycache__' in file_path or '/tests/' in file_path:
            continue

        # Skip files that are likely auto-generated or migrations
        if any(skip in file_path for skip in ['migrations/', 'alembic/', '__init__.py']):
            continue

        if fix_fallbacks_in_file(file_path):
            fixed_count += 1

    print(f"\n🎉 Comprehensive fallback fixing completed!")
    print(f"📊 Fixed {fixed_count} files")
    print(f"✨ All fallback issues have been replaced with smart defaults")

if __name__ == "__main__":
    main()
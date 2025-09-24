#!/usr/bin/env python3
"""
Fix regex replacement errors from the automated fallback fixing script.
"""

import os
import re
import glob

def fix_regex_errors_in_file(file_path: str) -> bool:
    """Fix regex errors in a single file."""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Fix various malformed smart_get patterns
        patterns_to_fix = [
            # Fix double smart_get patterns
            (r'smart_get\(([^)]+)\)smart_get\(([^)]+)\)', r'smart_get(\1, \2)'),

            # Fix missing dot patterns
            (r'([a-zA-Z_]+)smart_get\(([^)]+)\)', r'\1.get(\2)'),

            # Fix context patterns
            (r'contextsmart_get\(([^)]+)\)', r'smart_get(context, \1)'),

            # Fix data patterns
            (r'datasmart_get\(([^)]+)\)', r'smart_get(data, \1)'),

            # Fix rec patterns
            (r'recsmart_get\(([^)]+)\)', r'smart_get(rec, \1)'),

            # Fix service patterns
            (r'servicesmart_get\(([^)]+)\)', r'smart_get(service, \1)'),

            # Fix progress patterns
            (r'progresssmart_get\(([^)]+)\)', r'smart_get(progress, \1)'),

            # Fix business_req patterns
            (r'business_reqsmart_get\(([^)]+)\)', r'smart_get(business_req, \1)'),

            # Fix strategic_alignment patterns
            (r'strategic_alignmentsmart_get\(([^)]+)\)', r'smart_get(strategic_alignment, \1)'),

            # Fix missing parentheses
            (r'\.get\(([^,]+),\s*smart_get\(([^)]+)\)\)', r'smart_get(\1)'),
        ]

        for pattern, replacement in patterns_to_fix:
            content = re.sub(pattern, replacement, content)

        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed regex errors in: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main execution function."""

    print("🔧 Starting regex error fixing...")

    # Get all files that have regex errors
    cmd = 'find . -name "*.py" -exec grep -l "smart_get.*smart_get\\|contextsmart_get\\|datasmart_get\\|recsmart_get" {} \\;'
    import subprocess
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd="src")

    if result.returncode != 0:
        print("No files with regex errors found")
        return

    files_with_errors = result.stdout.strip().split('\n')
    files_with_errors = [f"src/{f[2:]}" for f in files_with_errors if f.strip()]

    print(f"📁 Found {len(files_with_errors)} files with regex errors")

    fixed_count = 0

    # Process each file
    for file_path in files_with_errors:
        if fix_regex_errors_in_file(file_path):
            fixed_count += 1

    print(f"\n🎉 Regex error fixing completed!")
    print(f"📊 Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
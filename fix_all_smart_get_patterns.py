#!/usr/bin/env python3
"""
Fix all smart_get pattern errors across the codebase.
"""

import os
import re
import glob

def fix_smart_get_patterns_in_file(file_path: str) -> bool:
    """Fix smart_get pattern errors in a single file."""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Fix all patterns of missing dot operators before smart_get/get
        patterns_to_fix = [
            # Fix variable followed directly by smart_get (no dot)
            (r'([a-zA-Z_][a-zA-Z0-9_]*)smart_get\(([^)]+)\)', r'\1.get(\2)'),

            # Fix specific patterns found in the codebase
            (r'appsmart_get\(([^)]+)\)', r'app.get(\1)'),
            (r'login_infosmart_get\(([^)]+)\)', r'login_info.get(\1)'),
            (r'report_docsmart_get\(([^)]+)\)', r'report_doc.get(\1)'),
            (r'kwargssmart_get\(([^)]+)\)', r'kwargs.get(\1)'),
            (r'headerssmart_get\(([^)]+)\)', r'headers.get(\1)'),
            (r'redis_clientsmart_get\(([^)]+)\)', r'redis_client.get(\1)'),
            (r'reportsmart_get\(([^)]+)\)', r'report.get(\1)'),
            (r'resultsmart_get\(([^)]+)\)', r'result.get(\1)'),
            (r'recovery_resultsmart_get\(([^)]+)\)', r'recovery_result.get(\1)'),
            (r'itemsmart_get\(([^)]+)\)', r'item.get(\1)'),
            (r'imgsmart_get\(([^)]+)\)', r'img.get(\1)'),
            (r'servicesmart_get\(([^)]+)\)', r'service.get(\1)'),
            (r'configsmart_get\(([^)]+)\)', r'config.get(\1)'),
            (r'id_infosmart_get\(([^)]+)\)', r'id_info.get(\1)'),
            (r'data_validationsmart_get\(([^)]+)\)', r'data_validation.get(\1)'),
            (r'existing_resultsmart_get\(([^)]+)\)', r'existing_result.get(\1)'),

            # Fix patterns where .get() is followed by smart_get
            (r'\.get\([^)]+\)smart_get\(([^)]+)\)', r'.get(\1)'),

            # Fix double smart_get patterns
            (r'smart_get\(([^)]+)\)smart_get\(([^)]+)\)', r'.get(\1).get(\2)'),

            # Fix missing parentheses after get
            (r'\.get\(([^,)]+),\s*smart_get\(([^)]+)\)\)', r'.get(\1)'),
        ]

        for pattern, replacement in patterns_to_fix:
            content = re.sub(pattern, replacement, content)

        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed smart_get patterns in: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main execution function."""

    print("🔧 Starting smart_get pattern fixing...")

    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    print(f"📁 Found {len(python_files)} Python files")

    fixed_count = 0

    # Process each file
    for file_path in python_files:
        if fix_smart_get_patterns_in_file(file_path):
            fixed_count += 1

    print(f"\n🎉 Smart_get pattern fixing completed!")
    print(f"📊 Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script to integrate PromptSanitizer into all remaining agents.
Automates the security hardening process.
"""

import os
import re
from pathlib import Path

# Agents to integrate (excluding cto_agent which is already done)
AGENTS_TO_INTEGRATE = [
    "cloud_engineer_agent.py",
    "research_agent.py",
    "compliance_agent.py",
    "mlops_agent.py",
    "infrastructure_agent.py",
    "ai_consultant_agent.py",
    "report_generator_agent.py",
    "chatbot_agent.py",
    "web_research_agent.py",
    "simulation_agent.py"
]

AGENTS_DIR = Path("src/infra_mind/agents")

def add_import(content: str) -> tuple[str, bool]:
    """Add sanitizer import if not already present."""
    import_line = "from ..llm.prompt_sanitizer import PromptSanitizer"

    if import_line in content:
        return content, False

    # Find the last import statement
    import_pattern = r'(from \.\.(?:models|core)\.[\w_]+ import [\w, ]+)'
    matches = list(re.finditer(import_pattern, content))

    if matches:
        last_import = matches[-1]
        insert_pos = last_import.end()
        new_content = (
            content[:insert_pos] +
            f"\n{import_line}" +
            content[insert_pos:]
        )
        return new_content, True

    return content, False

def add_initialization(content: str) -> tuple[str, bool]:
    """Add sanitizer initialization in __init__ if not present."""
    init_code = """
        # Initialize prompt sanitizer for security
        self.prompt_sanitizer = PromptSanitizer(security_level="balanced")
"""

    if "self.prompt_sanitizer" in content:
        return content, False

    # Find super().__init__(config) and add sanitizer after it
    pattern = r'(super\(\).__init__\(config\))\s*\n'
    match = re.search(pattern, content)

    if match:
        insert_pos = match.end()
        new_content = (
            content[:insert_pos] +
            init_code +
            content[insert_pos:]
        )
        return new_content, True

    return content, False

def integrate_agent(agent_file: Path) -> dict:
    """Integrate sanitizer into a single agent file."""
    print(f"\n{'='*60}")
    print(f"Integrating: {agent_file.name}")
    print('='*60)

    with open(agent_file, 'r') as f:
        original_content = f.read()

    content = original_content
    changes_made = []

    # Step 1: Add import
    content, import_added = add_import(content)
    if import_added:
        changes_made.append("✅ Added PromptSanitizer import")
        print("✅ Added PromptSanitizer import")
    else:
        print("⏭️  Import already present")

    # Step 2: Add initialization
    content, init_added = add_initialization(content)
    if init_added:
        changes_made.append("✅ Added sanitizer initialization in __init__")
        print("✅ Added sanitizer initialization in __init__")
    else:
        print("⏭️  Initialization already present")

    # Write back if changes were made
    if changes_made:
        with open(agent_file, 'w') as f:
            f.write(content)
        print(f"\n✅ {agent_file.name} updated successfully")
        return {"status": "updated", "changes": changes_made}
    else:
        print(f"\n⏭️  {agent_file.name} already integrated")
        return {"status": "skipped", "changes": []}

def main():
    """Main integration function."""
    print("\n" + "="*60)
    print(" Prompt Sanitizer Integration Script")
    print(" Securing all AI agents against prompt injection")
    print("="*60)

    results = {}

    for agent_name in AGENTS_TO_INTEGRATE:
        agent_file = AGENTS_DIR / agent_name

        if not agent_file.exists():
            print(f"\n⚠️  {agent_name} not found, skipping...")
            results[agent_name] = {"status": "not_found", "changes": []}
            continue

        try:
            result = integrate_agent(agent_file)
            results[agent_name] = result
        except Exception as e:
            print(f"\n❌ Error integrating {agent_name}: {e}")
            results[agent_name] = {"status": "error", "error": str(e)}

    # Summary
    print("\n" + "="*60)
    print(" Integration Summary")
    print("="*60)

    updated = sum(1 for r in results.values() if r["status"] == "updated")
    skipped = sum(1 for r in results.values() if r["status"] == "skipped")
    errors = sum(1 for r in results.values() if r["status"] == "error")
    not_found = sum(1 for r in results.values() if r["status"] == "not_found")

    print(f"\n✅ Updated: {updated}")
    print(f"⏭️  Already integrated: {skipped}")
    print(f"❌ Errors: {errors}")
    print(f"⚠️  Not found: {not_found}")
    print(f"\n📊 Total agents processed: {len(results)}")

    if updated > 0:
        print(f"\n🎉 Successfully integrated sanitizer into {updated} agents!")
        print("\n⚠️  IMPORTANT NEXT STEPS:")
        print("   1. Review the changes in each agent file")
        print("   2. Add sanitization calls where user data is used in prompts")
        print("   3. Run tests: pytest tests/ -v")
        print("   4. Deploy to staging for testing")

    return results

if __name__ == "__main__":
    main()

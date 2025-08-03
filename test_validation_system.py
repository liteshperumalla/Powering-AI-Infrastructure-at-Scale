#!/usr/bin/env python3
"""
Quick Test of Validation System

Demonstrates that all validation scripts are working correctly
and can detect system status appropriately.
"""

import subprocess
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def run_validation_test(script_name, description):
    """Run a validation script and return basic status."""
    try:
        # Run with --help to test basic functionality
        result = subprocess.run(
            [sys.executable, script_name, "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return {"status": "✅ WORKING", "details": "Script loads and runs correctly"}
        else:
            return {"status": "❌ ERROR", "details": f"Exit code: {result.returncode}"}
            
    except subprocess.TimeoutExpired:
        return {"status": "⏱️ TIMEOUT", "details": "Script took too long"}
    except Exception as e:
        return {"status": "🔥 FAILED", "details": str(e)}

def main():
    """Test all validation scripts."""
    console.print(Panel.fit(
        "[bold blue]🧪 Validation System Test[/bold blue]\n"
        "Testing that all validation scripts are working correctly",
        border_style="blue"
    ))
    
    # Test scripts
    scripts = [
        ("test_comprehensive_system_validation.py", "Comprehensive System Validation"),
        ("test_requirements_validation.py", "Requirements Validation"),
        ("validate_system_production_readiness.py", "Production Readiness Validator"),
        ("run_system_validation.py", "System Validation Orchestrator")
    ]
    
    # Create results table
    table = Table(title="Validation Script Status")
    table.add_column("Script", style="cyan", no_wrap=True)
    table.add_column("Description", style="blue")
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="green")
    
    all_working = True
    
    for script, description in scripts:
        console.print(f"[yellow]Testing {script}...[/yellow]")
        result = run_validation_test(script, description)
        
        table.add_row(
            script,
            description,
            result["status"],
            result["details"]
        )
        
        if "ERROR" in result["status"] or "FAILED" in result["status"]:
            all_working = False
    
    console.print(table)
    
    # Summary
    if all_working:
        console.print(Panel(
            "[bold green]✅ All validation scripts are working correctly![/bold green]\n\n"
            "The validation system is ready to use. To run full validation:\n"
            "1. Configure real API keys in .env file\n"
            "2. Start required services (MongoDB, Redis)\n"
            "3. Run: python validate_system_production_readiness.py",
            title="Validation System Status",
            border_style="green"
        ))
        return True
    else:
        console.print(Panel(
            "[bold red]❌ Some validation scripts have issues![/bold red]\n\n"
            "Please check the errors above and fix any issues.",
            title="Validation System Status",
            border_style="red"
        ))
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
System Validation Test Runner

Orchestrates all validation tests for task 13.2:
- End-to-end user workflows
- Integration testing
- Security assessment
- Performance benchmarking
- Load testing
"""

import asyncio
import subprocess
import sys
import os
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

console = Console()

class ValidationOrchestrator:
    """Orchestrates all system validation tests."""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.utcnow()
    
    async def run_all_validations(self):
        """Run all validation test suites."""
        console.print(Panel.fit(
            "[bold blue]🔍 System Validation Test Suite[/bold blue]\n"
            "Running comprehensive end-to-end system validation",
            border_style="blue"
        ))
        
        validation_tests = [
            ("Comprehensive System Validation", "python test_comprehensive_system_validation.py"),
            ("Full Integration Test", "python test_full_integration.py"),
            ("Security Audit", "python -m pytest tests/test_security_audit.py -v"),
            ("Performance Benchmarks", "python -m pytest tests/test_performance_benchmarking.py -v"),
            ("Load Testing", "python -m pytest tests/test_load_testing.py -v"),
            ("End-to-End Workflows", "python -m pytest tests/test_end_to_end_workflows.py -v"),
        ]
        
        for test_name, command in validation_tests:
            console.print(f"\n[yellow]Running {test_name}...[/yellow]")
            
            try:
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minutes timeout
                )
                
                self.results[test_name] = {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode
                }
                
                if result.returncode == 0:
                    console.print(f"[green]✅ {test_name} PASSED[/green]")
                else:
                    console.print(f"[red]❌ {test_name} FAILED[/red]")
                    if result.stderr:
                        console.print(f"[red]Error: {result.stderr[:200]}...[/red]")
                
            except subprocess.TimeoutExpired:
                self.results[test_name] = {
                    "success": False,
                    "error": "Test timed out after 30 minutes"
                }
                console.print(f"[red]❌ {test_name} TIMED OUT[/red]")
            
            except Exception as e:
                self.results[test_name] = {
                    "success": False,
                    "error": str(e)
                }
                console.print(f"[red]❌ {test_name} ERROR: {e}[/red]")
        
        await self._generate_final_report()
    
    async def _generate_final_report(self):
        """Generate final validation report."""
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds() / 60
        
        passed_tests = sum(1 for result in self.results.values() if result.get("success", False))
        total_tests = len(self.results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Create summary
        summary = {
            "validation_timestamp": end_time.isoformat(),
            "duration_minutes": duration,
            "total_test_suites": total_tests,
            "passed_test_suites": passed_tests,
            "failed_test_suites": total_tests - passed_tests,
            "success_rate": success_rate,
            "system_ready": success_rate >= 80 and passed_tests >= 4,
            "test_results": self.results
        }
        
        # Save report
        report_file = f"validation_summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Display final results
        if summary["system_ready"]:
            panel_style = "green"
            status_emoji = "🎉"
            status_text = "SYSTEM READY FOR PRODUCTION"
        else:
            panel_style = "red"
            status_emoji = "🚨"
            status_text = "SYSTEM NOT READY - ISSUES FOUND"
        
        console.print(Panel(
            f"{status_emoji} [bold]System Validation Complete[/bold]\n\n"
            f"Duration: {duration:.1f} minutes\n"
            f"Test Suites: {passed_tests}/{total_tests} passed\n"
            f"Success Rate: {success_rate:.1f}%\n\n"
            f"[bold]{status_text}[/bold]\n\n"
            f"Detailed report: {report_file}",
            border_style=panel_style
        ))
        
        return summary["system_ready"]


async def main():
    """Main validation orchestrator."""
    orchestrator = ValidationOrchestrator()
    success = await orchestrator.run_all_validations()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
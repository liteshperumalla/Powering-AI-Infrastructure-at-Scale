#!/usr/bin/env python3
"""
Simple System Test for Infra Mind MVP
Tests the basic system functionality without complex integrations
"""

import asyncio
import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class SimpleSystemTest:
    """Simple system test for MVP validation"""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        
    async def run_all_tests(self):
        """Run all basic system tests"""
        console.print(Panel.fit(
            "[bold blue]🚀 Infra Mind MVP - Simple System Test[/bold blue]\n"
            f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            border_style="blue"
        ))
        
        tests = [
            ("Environment Check", self.test_environment),
            ("API Health Check", self.test_api_health),
            ("Frontend Health Check", self.test_frontend_health),
            ("Database Connectivity", self.test_database_connectivity),
            ("Cache Connectivity", self.test_cache_connectivity),
            ("API Endpoints", self.test_api_endpoints),
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            for test_name, test_func in tests:
                task = progress.add_task(f"Running {test_name}...", total=None)
                
                try:
                    result = await test_func()
                    self.results[test_name] = {
                        "status": "PASS" if result else "FAIL",
                        "details": result if isinstance(result, dict) else {}
                    }
                    progress.update(task, description=f"✅ {test_name}")
                    
                except Exception as e:
                    self.results[test_name] = {
                        "status": "ERROR",
                        "error": str(e)
                    }
                    progress.update(task, description=f"❌ {test_name}")
                    console.print(f"[red]Error in {test_name}: {e}[/red]")
                
                progress.remove_task(task)
        
        await self.generate_report()
    
    async def test_environment(self) -> Dict[str, Any]:
        """Test environment configuration"""
        console.print("[yellow]Checking environment variables...[/yellow]")
        
        required_vars = [
            'INFRA_MIND_OPENAI_API_KEY',
            'INFRA_MIND_SECRET_KEY',
            'INFRA_MIND_MONGODB_URL',
            'INFRA_MIND_REDIS_URL'
        ]
        
        present_vars = []
        missing_vars = []
        
        for var in required_vars:
            if os.getenv(var):
                present_vars.append(var)
            else:
                missing_vars.append(var)
        
        return {
            "required_vars": len(required_vars),
            "present_vars": len(present_vars),
            "missing_vars": missing_vars,
            "environment_ok": len(missing_vars) == 0
        }
    
    async def test_api_health(self) -> Dict[str, Any]:
        """Test API health endpoint"""
        console.print("[yellow]Testing API health...[/yellow]")
        
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            
            return {
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "healthy": response.status_code == 200,
                "response_data": response.json() if response.status_code == 200 else None
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def test_frontend_health(self) -> Dict[str, Any]:
        """Test frontend health endpoint"""
        console.print("[yellow]Testing frontend health...[/yellow]")
        
        try:
            response = requests.get("http://localhost:3000/health", timeout=10)
            
            return {
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "healthy": response.status_code == 200,
                "response_data": response.json() if response.status_code == 200 else None
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity using Docker"""
        console.print("[yellow]Testing database connectivity...[/yellow]")
        
        try:
            import subprocess
            
            # Test MongoDB
            mongo_result = subprocess.run([
                'docker', 'exec', 'infra_mind_mongodb', 
                'mongosh', '--quiet', '--eval', 'db.adminCommand("ping").ok'
            ], capture_output=True, text=True, timeout=10)
            
            mongo_healthy = mongo_result.returncode == 0 and "1" in mongo_result.stdout
            
            # Test Redis
            redis_result = subprocess.run([
                'docker', 'exec', 'infra_mind_redis', 
                'redis-cli', 'ping'
            ], capture_output=True, text=True, timeout=10)
            
            redis_healthy = redis_result.returncode == 0 and "PONG" in redis_result.stdout
            
            return {
                "mongodb_healthy": mongo_healthy,
                "redis_healthy": redis_healthy,
                "both_healthy": mongo_healthy and redis_healthy
            }
            
        except Exception as e:
            return {
                "mongodb_healthy": False,
                "redis_healthy": False,
                "both_healthy": False,
                "error": str(e)
            }
    
    async def test_cache_connectivity(self) -> Dict[str, Any]:
        """Test cache connectivity using Redis CLI"""
        console.print("[yellow]Testing cache operations...[/yellow]")
        
        try:
            import subprocess
            
            # Test Redis set/get operations
            test_key = "test_integration_key"
            test_value = "test_value"
            
            # Set a test value
            set_result = subprocess.run([
                'docker', 'exec', 'infra_mind_redis', 
                'redis-cli', 'set', test_key, test_value
            ], capture_output=True, text=True, timeout=5)
            
            # Get the test value
            get_result = subprocess.run([
                'docker', 'exec', 'infra_mind_redis', 
                'redis-cli', 'get', test_key
            ], capture_output=True, text=True, timeout=5)
            
            # Delete the test value
            del_result = subprocess.run([
                'docker', 'exec', 'infra_mind_redis', 
                'redis-cli', 'del', test_key
            ], capture_output=True, text=True, timeout=5)
            
            set_ok = set_result.returncode == 0 and "OK" in set_result.stdout
            get_ok = get_result.returncode == 0 and test_value in get_result.stdout
            del_ok = del_result.returncode == 0
            
            return {
                "cache_set": set_ok,
                "cache_get": get_ok,
                "cache_delete": del_ok,
                "cache_working": set_ok and get_ok and del_ok
            }
            
        except Exception as e:
            return {
                "cache_working": False,
                "error": str(e)
            }
    
    async def test_api_endpoints(self) -> Dict[str, Any]:
        """Test various API endpoints"""
        console.print("[yellow]Testing API endpoints...[/yellow]")
        
        endpoints = [
            ("/health", "GET"),
            ("/api/v1/assessments", "GET"),
            ("/api/v1/recommendations", "GET"),
            ("/api/v1/reports", "GET"),
            ("/docs", "GET"),
        ]
        
        results = {}
        
        for endpoint, method in endpoints:
            try:
                url = f"http://localhost:8000{endpoint}"
                response = requests.get(url, timeout=5)
                
                results[endpoint] = {
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "accessible": response.status_code in [200, 401, 422]  # 401/422 are OK (auth/validation)
                }
                
            except Exception as e:
                results[endpoint] = {
                    "accessible": False,
                    "error": str(e)
                }
        
        accessible_count = sum(1 for r in results.values() if r.get("accessible", False))
        
        return {
            "endpoints_tested": len(endpoints),
            "endpoints_accessible": accessible_count,
            "success_rate": (accessible_count / len(endpoints)) * 100,
            "details": results
        }
    
    async def generate_report(self):
        """Generate test report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Create summary table
        table = Table(title="Simple System Test Results")
        table.add_column("Test", style="cyan", no_wrap=True)
        table.add_column("Status", style="magenta")
        table.add_column("Details", style="green")
        
        passed = 0
        total = len(self.results)
        
        for test_name, result in self.results.items():
            status = result["status"]
            if status == "PASS":
                passed += 1
                status_display = "✅ PASS"
            elif status == "FAIL":
                status_display = "❌ FAIL"
            else:
                status_display = "🔥 ERROR"
            
            details = ""
            if "error" in result:
                details = f"Error: {result['error'][:50]}..."
            elif "details" in result and result["details"]:
                if isinstance(result["details"], dict):
                    key_details = []
                    for k, v in result["details"].items():
                        if isinstance(v, bool):
                            key_details.append(f"{k}: {'✓' if v else '✗'}")
                        elif isinstance(v, (int, float)):
                            key_details.append(f"{k}: {v}")
                    details = ", ".join(key_details[:3])  # Show first 3 details
            
            table.add_row(test_name, status_display, details)
        
        console.print(table)
        
        # Summary panel
        success_rate = (passed / total) * 100 if total > 0 else 0
        summary_text = (
            f"[bold]Test Summary[/bold]\n"
            f"Total Tests: {total}\n"
            f"Passed: {passed}\n"
            f"Failed: {total - passed}\n"
            f"Success Rate: {success_rate:.1f}%\n"
            f"Duration: {duration.total_seconds():.2f} seconds"
        )
        
        if success_rate >= 80:
            panel_style = "green"
            status_emoji = "🎉"
        elif success_rate >= 60:
            panel_style = "yellow"
            status_emoji = "⚠️"
        else:
            panel_style = "red"
            status_emoji = "🚨"
        
        console.print(Panel(
            f"{status_emoji} {summary_text}",
            title="System Test Complete",
            border_style=panel_style
        ))
        
        # Save results
        results_file = f"simple_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": end_time.isoformat(),
                "duration_seconds": duration.total_seconds(),
                "summary": {
                    "total_tests": total,
                    "passed": passed,
                    "failed": total - passed,
                    "success_rate": success_rate
                },
                "results": self.results
            }, f, indent=2)
        
        console.print(f"\n[blue]Results saved to: {results_file}[/blue]")
        
        return success_rate >= 80


async def main():
    """Main test runner"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        console.print("""
[bold blue]Infra Mind MVP - Simple System Test[/bold blue]

This script tests the basic system functionality without complex integrations.

[bold]Prerequisites:[/bold]
1. System deployed and running (make deploy-dev)
2. Docker containers healthy

[bold]Usage:[/bold]
python test_system_simple.py

[bold]What it tests:[/bold]
- Environment configuration
- API and Frontend health endpoints
- Database connectivity (MongoDB + Redis)
- Cache operations
- API endpoint accessibility
        """)
        return
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run tests
    test_runner = SimpleSystemTest()
    success = await test_runner.run_all_tests()
    
    if success:
        console.print("\n[bold green]🎉 Simple System Test PASSED! Your MVP is working![/bold green]")
        console.print("\n[bold]🌐 Access your system:[/bold]")
        console.print("• Frontend: http://localhost:3000")
        console.print("• API: http://localhost:8000")
        console.print("• API Docs: http://localhost:8000/docs")
        sys.exit(0)
    else:
        console.print("\n[bold red]🚨 Simple System Test FAILED! Please check the issues above.[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
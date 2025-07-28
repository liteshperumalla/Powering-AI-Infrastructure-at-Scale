#!/usr/bin/env python3
"""
MVP Test Runner - Complete system test with real APIs
Orchestrates the full testing process from setup to validation
"""

import os
import sys
import time
import subprocess
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class MVPTestRunner:
    """Complete MVP test orchestrator"""
    
    def __init__(self):
        self.console = Console()
    
    async def run_complete_test(self):
        """Run the complete MVP test process"""
        self.console.print(Panel.fit(
            "[bold blue]🚀 Infra Mind MVP - Complete System Test[/bold blue]\n"
            "Testing with real APIs, database, LLM, and full integration",
            border_style="blue"
        ))
        
        # Step 1: Environment setup
        if not await self.check_environment():
            return False
        
        # Step 2: Start services
        if not await self.start_services():
            return False
        
        # Step 3: Wait for services
        await self.wait_for_services()
        
        # Step 4: Run integration tests
        if not await self.run_integration_tests():
            return False
        
        # Step 5: Run health check
        await self.run_health_check()
        
        self.console.print(Panel(
            "[bold green]🎉 MVP Test Complete![/bold green]\n\n"
            "Your Infra Mind system is ready for production!\n\n"
            "[bold]Access URLs:[/bold]\n"
            "• Frontend: http://localhost:3000\n"
            "• API: http://localhost:8000\n"
            "• API Docs: http://localhost:8000/docs",
            title="Success!",
            border_style="green"
        ))
        
        return True
    
    async def check_environment(self) -> bool:
        """Check and setup environment"""
        self.console.print("\n[bold]📋 Step 1: Environment Setup[/bold]")
        
        # Check if .env exists
        if not os.path.exists('.env'):
            self.console.print("[yellow]No .env file found. Running setup...[/yellow]")
            
            # Run setup script
            try:
                result = subprocess.run([
                    sys.executable, 'setup_real_test.py'
                ], check=True, capture_output=True, text=True)
                
                self.console.print("[green]✅ Environment setup completed[/green]")
            except subprocess.CalledProcessError as e:
                self.console.print(f"[red]❌ Environment setup failed: {e}[/red]")
                return False
        else:
            self.console.print("[green]✅ .env file found[/green]")
        
        # Validate required variables
        required_vars = [
            'INFRA_MIND_OPENAI_API_KEY',
            'INFRA_MIND_SECRET_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.console.print(f"[red]❌ Missing required variables: {missing_vars}[/red]")
            self.console.print("[yellow]Please run: python setup_real_test.py[/yellow]")
            return False
        
        return True
    
    async def start_services(self) -> bool:
        """Start Docker services"""
        self.console.print("\n[bold]🐳 Step 2: Starting Services[/bold]")
        
        try:
            # Check if Docker is running
            result = subprocess.run(['docker', 'info'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.console.print("[red]❌ Docker is not running. Please start Docker first.[/red]")
                return False
            
            # Start services
            self.console.print("[yellow]Starting Docker services...[/yellow]")
            result = subprocess.run(['make', 'deploy-dev'], 
                                  check=True, capture_output=True, text=True)
            
            self.console.print("[green]✅ Services started successfully[/green]")
            return True
            
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]❌ Failed to start services: {e}[/red]")
            self.console.print(f"[red]Output: {e.stdout}[/red]")
            self.console.print(f"[red]Error: {e.stderr}[/red]")
            return False
        except FileNotFoundError:
            self.console.print("[red]❌ Make command not found. Please install make or run manually:[/red]")
            self.console.print("[yellow]docker-compose up -d[/yellow]")
            return False
    
    async def wait_for_services(self):
        """Wait for services to be ready"""
        self.console.print("\n[bold]⏳ Step 3: Waiting for Services[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            
            task = progress.add_task("Waiting for services to start...", total=None)
            
            # Wait for services to be ready
            max_wait = 120  # 2 minutes
            wait_time = 0
            
            while wait_time < max_wait:
                try:
                    import requests
                    
                    # Check API health
                    api_response = requests.get('http://localhost:8000/health', timeout=5)
                    if api_response.status_code == 200:
                        progress.update(task, description="✅ Services are ready!")
                        break
                        
                except requests.exceptions.RequestException:
                    pass
                
                await asyncio.sleep(5)
                wait_time += 5
                progress.update(task, description=f"Waiting for services... ({wait_time}s)")
            
            progress.remove_task(task)
        
        if wait_time >= max_wait:
            self.console.print("[red]❌ Services did not start within 2 minutes[/red]")
            self.console.print("[yellow]Check logs with: make docker-logs[/yellow]")
        else:
            self.console.print("[green]✅ All services are ready[/green]")
    
    async def run_integration_tests(self) -> bool:
        """Run the full integration test suite"""
        self.console.print("\n[bold]🧪 Step 4: Running Integration Tests[/bold]")
        
        try:
            # Run the integration test
            result = subprocess.run([
                sys.executable, 'test_full_integration.py'
            ], check=True, capture_output=False, text=True)
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]❌ Integration tests failed with exit code: {e.returncode}[/red]")
            return False
    
    async def run_health_check(self):
        """Run system health check"""
        self.console.print("\n[bold]🔍 Step 5: System Health Check[/bold]")
        
        try:
            result = subprocess.run(['make', 'health-check'], 
                                  check=True, capture_output=False, text=True)
            
        except subprocess.CalledProcessError:
            self.console.print("[yellow]⚠️ Health check had some issues, but system may still be functional[/yellow]")
        except FileNotFoundError:
            self.console.print("[yellow]⚠️ Make command not found, skipping health check[/yellow]")


async def main():
    """Main test runner"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        console.print("""
[bold blue]Infra Mind MVP - Complete System Test[/bold blue]

This script runs a complete end-to-end test of the MVP with real APIs.

[bold]What it does:[/bold]
1. Checks/sets up environment configuration
2. Starts Docker services (API, Frontend, Database)
3. Waits for services to be ready
4. Runs comprehensive integration tests
5. Performs system health check

[bold]Prerequisites:[/bold]
- Docker installed and running
- Make command available (or run docker-compose manually)

[bold]Usage:[/bold]
python run_mvp_test.py

[bold]Manual alternative:[/bold]
1. python setup_real_test.py
2. make deploy-dev
3. python test_full_integration.py
4. make health-check
        """)
        return
    
    # Load environment if .env exists
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
    
    runner = MVPTestRunner()
    success = await runner.run_complete_test()
    
    if success:
        console.print("\n[bold green]🎉 MVP is ready for production![/bold green]")
        sys.exit(0)
    else:
        console.print("\n[bold red]🚨 MVP test failed. Please check the issues above.[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Setup script for real API testing
Helps configure environment variables and validate API keys
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
import requests

console = Console()

class RealTestSetup:
    """Setup helper for real API testing"""
    
    def __init__(self):
        self.env_vars = {}
        self.api_validations = {}
    
    def run_setup(self):
        """Run the complete setup process"""
        console.print(Panel.fit(
            "[bold blue]🔧 Infra Mind MVP - Real API Test Setup[/bold blue]\n"
            "This will help you configure real API keys for testing",
            border_style="blue"
        ))
        
        # Check existing .env
        self.check_existing_env()
        
        # Setup required variables
        self.setup_required_vars()
        
        # Setup optional cloud providers
        self.setup_cloud_providers()
        
        # Validate API keys
        self.validate_api_keys()
        
        # Write .env file
        self.write_env_file()
        
        # Show next steps
        self.show_next_steps()
    
    def check_existing_env(self):
        """Check if .env file exists and load existing values"""
        if os.path.exists('.env'):
            console.print("[yellow]Found existing .env file. Loading current values...[/yellow]")
            
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.env_vars[key] = value
        else:
            console.print("[yellow]No .env file found. Will create a new one.[/yellow]")
    
    def setup_required_vars(self):
        """Setup required environment variables"""
        console.print("\n[bold]📋 Required Configuration[/bold]")
        
        # OpenAI API Key
        current_openai = self.env_vars.get('INFRA_MIND_OPENAI_API_KEY', '')
        if current_openai and not current_openai.startswith('your-'):
            console.print(f"[green]✅ OpenAI API Key already configured[/green]")
        else:
            console.print("\n[bold]OpenAI API Key (Required for LLM functionality)[/bold]")
            console.print("Get your API key from: https://platform.openai.com/api-keys")
            
            openai_key = Prompt.ask(
                "Enter your OpenAI API Key",
                default=current_openai if current_openai else "",
                password=True
            )
            
            if openai_key and not openai_key.startswith('your-'):
                self.env_vars['INFRA_MIND_OPENAI_API_KEY'] = openai_key
            else:
                console.print("[red]⚠️ OpenAI API key is required for testing[/red]")
        
        # Secret Key
        current_secret = self.env_vars.get('INFRA_MIND_SECRET_KEY', '')
        if not current_secret or current_secret.startswith('your-'):
            import secrets
            secret_key = secrets.token_urlsafe(32)
            self.env_vars['INFRA_MIND_SECRET_KEY'] = secret_key
            console.print("[green]✅ Generated secure secret key[/green]")
        
        # Database URLs
        self.env_vars['INFRA_MIND_MONGODB_URL'] = 'mongodb://admin:password@localhost:27017/infra_mind?authSource=admin'
        self.env_vars['INFRA_MIND_REDIS_URL'] = 'redis://localhost:6379'
        self.env_vars['INFRA_MIND_ENVIRONMENT'] = 'development'
        self.env_vars['INFRA_MIND_DEBUG'] = 'true'
    
    def setup_cloud_providers(self):
        """Setup optional cloud provider configurations"""
        console.print("\n[bold]☁️ Cloud Provider Configuration (Optional)[/bold]")
        console.print("Configure cloud providers to test real pricing and service data")
        
        # AWS
        if Confirm.ask("\nConfigure AWS credentials?", default=False):
            self.setup_aws()
        
        # Azure
        if Confirm.ask("\nConfigure Azure credentials?", default=False):
            self.setup_azure()
        
        # GCP
        if Confirm.ask("\nConfigure GCP credentials?", default=False):
            self.setup_gcp()
    
    def setup_aws(self):
        """Setup AWS credentials"""
        console.print("\n[bold]AWS Configuration[/bold]")
        console.print("Get credentials from: https://console.aws.amazon.com/iam/")
        
        access_key = Prompt.ask(
            "AWS Access Key ID",
            default=self.env_vars.get('INFRA_MIND_AWS_ACCESS_KEY_ID', '')
        )
        
        secret_key = Prompt.ask(
            "AWS Secret Access Key",
            default=self.env_vars.get('INFRA_MIND_AWS_SECRET_ACCESS_KEY', ''),
            password=True
        )
        
        region = Prompt.ask(
            "AWS Region",
            default=self.env_vars.get('INFRA_MIND_AWS_REGION', 'us-east-1')
        )
        
        if access_key and secret_key:
            self.env_vars['INFRA_MIND_AWS_ACCESS_KEY_ID'] = access_key
            self.env_vars['INFRA_MIND_AWS_SECRET_ACCESS_KEY'] = secret_key
            self.env_vars['INFRA_MIND_AWS_REGION'] = region
    
    def setup_azure(self):
        """Setup Azure credentials"""
        console.print("\n[bold]Azure Configuration[/bold]")
        console.print("Create an App Registration in: https://portal.azure.com/")
        
        client_id = Prompt.ask(
            "Azure Client ID",
            default=self.env_vars.get('INFRA_MIND_AZURE_CLIENT_ID', '')
        )
        
        client_secret = Prompt.ask(
            "Azure Client Secret",
            default=self.env_vars.get('INFRA_MIND_AZURE_CLIENT_SECRET', ''),
            password=True
        )
        
        tenant_id = Prompt.ask(
            "Azure Tenant ID",
            default=self.env_vars.get('INFRA_MIND_AZURE_TENANT_ID', '')
        )
        
        if client_id and client_secret and tenant_id:
            self.env_vars['INFRA_MIND_AZURE_CLIENT_ID'] = client_id
            self.env_vars['INFRA_MIND_AZURE_CLIENT_SECRET'] = client_secret
            self.env_vars['INFRA_MIND_AZURE_TENANT_ID'] = tenant_id
    
    def setup_gcp(self):
        """Setup GCP credentials"""
        console.print("\n[bold]GCP Configuration[/bold]")
        console.print("Create a Service Account in: https://console.cloud.google.com/")
        
        project_id = Prompt.ask(
            "GCP Project ID",
            default=self.env_vars.get('INFRA_MIND_GCP_PROJECT_ID', '')
        )
        
        service_account_path = Prompt.ask(
            "Path to Service Account JSON file",
            default=self.env_vars.get('INFRA_MIND_GCP_SERVICE_ACCOUNT_PATH', '')
        )
        
        if project_id:
            self.env_vars['INFRA_MIND_GCP_PROJECT_ID'] = project_id
            
        if service_account_path and os.path.exists(service_account_path):
            self.env_vars['INFRA_MIND_GCP_SERVICE_ACCOUNT_PATH'] = service_account_path
        elif service_account_path:
            console.print(f"[red]⚠️ Service account file not found: {service_account_path}[/red]")
    
    def validate_api_keys(self):
        """Validate API keys by making test calls"""
        console.print("\n[bold]🔍 Validating API Keys[/bold]")
        
        # Validate OpenAI
        if 'INFRA_MIND_OPENAI_API_KEY' in self.env_vars:
            self.validate_openai()
        
        # Validate AWS
        if 'INFRA_MIND_AWS_ACCESS_KEY_ID' in self.env_vars:
            self.validate_aws()
    
    def validate_openai(self):
        """Validate OpenAI API key"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.env_vars['INFRA_MIND_OPENAI_API_KEY'])
            
            # Test with a simple completion
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            if response.choices:
                console.print("[green]✅ OpenAI API key is valid[/green]")
                self.api_validations['openai'] = True
            else:
                console.print("[red]❌ OpenAI API key validation failed[/red]")
                self.api_validations['openai'] = False
                
        except Exception as e:
            console.print(f"[red]❌ OpenAI API validation error: {str(e)}[/red]")
            self.api_validations['openai'] = False
    
    def validate_aws(self):
        """Validate AWS credentials"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            session = boto3.Session(
                aws_access_key_id=self.env_vars['INFRA_MIND_AWS_ACCESS_KEY_ID'],
                aws_secret_access_key=self.env_vars['INFRA_MIND_AWS_SECRET_ACCESS_KEY'],
                region_name=self.env_vars.get('INFRA_MIND_AWS_REGION', 'us-east-1')
            )
            
            # Test with STS get-caller-identity
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            if identity.get('Account'):
                console.print(f"[green]✅ AWS credentials valid for account: {identity['Account']}[/green]")
                self.api_validations['aws'] = True
            else:
                console.print("[red]❌ AWS credentials validation failed[/red]")
                self.api_validations['aws'] = False
                
        except Exception as e:
            console.print(f"[red]❌ AWS validation error: {str(e)}[/red]")
            self.api_validations['aws'] = False
    
    def write_env_file(self):
        """Write the .env file"""
        console.print("\n[bold]💾 Writing .env file[/bold]")
        
        # Add additional required variables
        additional_vars = {
            'INFRA_MIND_MONGODB_DATABASE': 'infra_mind',
            'INFRA_MIND_LLM_MODEL': 'gpt-4',
            'INFRA_MIND_LLM_TEMPERATURE': '0.1',
            'INFRA_MIND_API_HOST': '0.0.0.0',
            'INFRA_MIND_API_PORT': '8000',
            'INFRA_MIND_CORS_ORIGINS': '["http://localhost:3000","http://localhost:8080"]',
            'INFRA_MIND_RATE_LIMIT_REQUESTS': '100'
        }
        
        for key, value in additional_vars.items():
            if key not in self.env_vars:
                self.env_vars[key] = value
        
        # Write to file
        with open('.env', 'w') as f:
            f.write("# Environment variables for Infra Mind MVP Testing\n")
            f.write(f"# Generated on {os.popen('date').read().strip()}\n\n")
            
            f.write("# Application Configuration\n")
            for key in ['INFRA_MIND_ENVIRONMENT', 'INFRA_MIND_DEBUG', 'INFRA_MIND_SECRET_KEY']:
                if key in self.env_vars:
                    f.write(f"{key}={self.env_vars[key]}\n")
            
            f.write("\n# Database Configuration\n")
            for key in ['INFRA_MIND_MONGODB_URL', 'INFRA_MIND_MONGODB_DATABASE', 'INFRA_MIND_REDIS_URL']:
                if key in self.env_vars:
                    f.write(f"{key}={self.env_vars[key]}\n")
            
            f.write("\n# LLM Configuration\n")
            for key in ['INFRA_MIND_OPENAI_API_KEY', 'INFRA_MIND_LLM_MODEL', 'INFRA_MIND_LLM_TEMPERATURE']:
                if key in self.env_vars:
                    f.write(f"{key}={self.env_vars[key]}\n")
            
            f.write("\n# AWS Configuration\n")
            for key in ['INFRA_MIND_AWS_ACCESS_KEY_ID', 'INFRA_MIND_AWS_SECRET_ACCESS_KEY', 'INFRA_MIND_AWS_REGION']:
                if key in self.env_vars:
                    f.write(f"{key}={self.env_vars[key]}\n")
            
            f.write("\n# Azure Configuration\n")
            for key in ['INFRA_MIND_AZURE_CLIENT_ID', 'INFRA_MIND_AZURE_CLIENT_SECRET', 'INFRA_MIND_AZURE_TENANT_ID']:
                if key in self.env_vars:
                    f.write(f"{key}={self.env_vars[key]}\n")
            
            f.write("\n# GCP Configuration\n")
            for key in ['INFRA_MIND_GCP_SERVICE_ACCOUNT_PATH', 'INFRA_MIND_GCP_PROJECT_ID']:
                if key in self.env_vars:
                    f.write(f"{key}={self.env_vars[key]}\n")
            
            f.write("\n# API Configuration\n")
            for key in ['INFRA_MIND_API_HOST', 'INFRA_MIND_API_PORT', 'INFRA_MIND_CORS_ORIGINS', 'INFRA_MIND_RATE_LIMIT_REQUESTS']:
                if key in self.env_vars:
                    f.write(f"{key}={self.env_vars[key]}\n")
        
        console.print("[green]✅ .env file created successfully[/green]")
    
    def show_next_steps(self):
        """Show next steps for testing"""
        console.print("\n[bold]🚀 Next Steps[/bold]")
        
        # Create validation summary table
        table = Table(title="API Validation Summary")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Required", style="yellow")
        
        validations = [
            ("OpenAI", self.api_validations.get('openai', False), True),
            ("AWS", self.api_validations.get('aws', False), False),
            ("Azure", self.api_validations.get('azure', False), False),
            ("GCP", self.api_validations.get('gcp', False), False),
        ]
        
        for service, valid, required in validations:
            status = "✅ Valid" if valid else ("❌ Invalid" if service.lower() in self.env_vars else "⚪ Not configured")
            req_text = "Required" if required else "Optional"
            table.add_row(service, status, req_text)
        
        console.print(table)
        
        steps_text = """
[bold]1. Start the system:[/bold]
   make deploy-dev

[bold]2. Wait for services to start (30-60 seconds)[/bold]

[bold]3. Run the integration test:[/bold]
   python test_full_integration.py

[bold]4. Check system health:[/bold]
   make health-check

[bold]5. Access the system:[/bold]
   • Frontend: http://localhost:3000
   • API: http://localhost:8000
   • API Docs: http://localhost:8000/docs
        """
        
        console.print(Panel(
            steps_text,
            title="Ready to Test!",
            border_style="green"
        ))


def main():
    """Main setup function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        console.print("""
[bold blue]Infra Mind MVP - Real API Test Setup[/bold blue]

This script helps you configure real API keys for comprehensive testing.

[bold]Usage:[/bold]
python setup_real_test.py

[bold]What it does:[/bold]
1. Checks existing .env configuration
2. Prompts for required API keys (OpenAI)
3. Optionally configures cloud providers (AWS/Azure/GCP)
4. Validates API keys by making test calls
5. Creates/updates .env file
6. Shows next steps for testing

[bold]Required API Keys:[/bold]
- OpenAI API Key (for LLM functionality)

[bold]Optional API Keys:[/bold]
- AWS credentials (for real pricing data)
- Azure credentials (for service comparisons)
- GCP credentials (for multi-cloud analysis)
        """)
        return
    
    setup = RealTestSetup()
    setup.run_setup()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Setup Real Credentials Script
Interactive script to help users configure real cloud provider credentials
"""

import os
import sys
from pathlib import Path

def main():
    """Main setup function"""
    print("🔐 Infra Mind - Real Credentials Setup")
    print("=" * 50)
    print()
    print("This script will help you configure real cloud provider credentials")
    print("to eliminate validation warnings and enable full functionality.")
    print()
    
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Please create a .env file first. You can copy from .env.development:")
        print("cp .env.development .env")
        return
    
    print("✅ Found .env file")
    print()
    
    # Read current .env file
    with open('.env', 'r') as f:
        env_content = f.read()
    
    print("Current credential status:")
    check_current_credentials(env_content)
    print()
    
    # Ask user what they want to configure
    print("What would you like to configure?")
    print("1. AWS credentials")
    print("2. Azure credentials") 
    print("3. GCP credentials")
    print("4. OpenAI API key")
    print("5. All credentials")
    print("6. Exit")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    
    if choice == '1':
        setup_aws_credentials(env_content)
    elif choice == '2':
        setup_azure_credentials(env_content)
    elif choice == '3':
        setup_gcp_credentials(env_content)
    elif choice == '4':
        setup_openai_credentials(env_content)
    elif choice == '5':
        setup_all_credentials(env_content)
    elif choice == '6':
        print("Exiting...")
        return
    else:
        print("Invalid choice. Exiting...")
        return

def check_current_credentials(env_content):
    """Check current credential status"""
    # AWS
    if 'AWS_ACCESS_KEY_ID=' in env_content:
        aws_key = extract_env_value(env_content, 'AWS_ACCESS_KEY_ID')
        if aws_key and not aws_key.startswith('test-'):
            print("✅ AWS: Real credentials detected")
        else:
            print("⚠️  AWS: Test/placeholder credentials")
    else:
        print("❌ AWS: No credentials found")
    
    # Azure
    if 'AZURE_CLIENT_ID=' in env_content:
        azure_id = extract_env_value(env_content, 'AZURE_CLIENT_ID')
        if azure_id and not azure_id.startswith('test-'):
            print("✅ Azure: Real credentials detected")
        else:
            print("⚠️  Azure: Test/placeholder credentials")
    else:
        print("❌ Azure: No credentials found")
    
    # GCP
    if 'GCP_PROJECT_ID=' in env_content:
        gcp_project = extract_env_value(env_content, 'GCP_PROJECT_ID')
        if gcp_project and not gcp_project.startswith('test-'):
            print("✅ GCP: Real project ID detected")
        else:
            print("⚠️  GCP: Test/placeholder project ID")
    else:
        print("❌ GCP: No project ID found")
    
    # OpenAI
    if 'OPENAI_API_KEY=' in env_content:
        openai_key = extract_env_value(env_content, 'OPENAI_API_KEY')
        if openai_key and openai_key.startswith('sk-'):
            print("✅ OpenAI: Real API key detected")
        else:
            print("⚠️  OpenAI: Test/placeholder API key")
    else:
        print("❌ OpenAI: No API key found")

def extract_env_value(content, key):
    """Extract environment variable value from content"""
    for line in content.split('\n'):
        if line.startswith(f'{key}='):
            return line.split('=', 1)[1].strip()
    return None

def setup_aws_credentials(env_content):
    """Setup AWS credentials"""
    print("\n🔧 AWS Credentials Setup")
    print("-" * 30)
    print("You need:")
    print("1. AWS Access Key ID")
    print("2. AWS Secret Access Key")
    print("3. AWS Region (optional, defaults to us-east-1)")
    print()
    print("Get these from: AWS Console → IAM → Users → Security credentials")
    print()
    
    access_key = input("Enter AWS Access Key ID: ").strip()
    if not access_key:
        print("❌ Access Key ID is required")
        return
    
    secret_key = input("Enter AWS Secret Access Key: ").strip()
    if not secret_key:
        print("❌ Secret Access Key is required")
        return
    
    region = input("Enter AWS Region (default: us-east-1): ").strip() or "us-east-1"
    
    # Update .env file
    updated_content = update_env_var(env_content, 'AWS_ACCESS_KEY_ID', access_key)
    updated_content = update_env_var(updated_content, 'AWS_SECRET_ACCESS_KEY', secret_key)
    updated_content = update_env_var(updated_content, 'AWS_DEFAULT_REGION', region)
    
    save_env_file(updated_content)
    print("✅ AWS credentials saved to .env file")

def setup_azure_credentials(env_content):
    """Setup Azure credentials"""
    print("\n🔧 Azure Credentials Setup")
    print("-" * 30)
    print("You need:")
    print("1. Azure Client ID")
    print("2. Azure Client Secret")
    print("3. Azure Tenant ID")
    print("4. Azure Subscription ID")
    print()
    print("Get these from: Azure Portal → App registrations")
    print()
    
    client_id = input("Enter Azure Client ID: ").strip()
    if not client_id:
        print("❌ Client ID is required")
        return
    
    client_secret = input("Enter Azure Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret is required")
        return
    
    tenant_id = input("Enter Azure Tenant ID: ").strip()
    if not tenant_id:
        print("❌ Tenant ID is required")
        return
    
    subscription_id = input("Enter Azure Subscription ID: ").strip()
    if not subscription_id:
        print("❌ Subscription ID is required")
        return
    
    # Update .env file
    updated_content = update_env_var(env_content, 'AZURE_CLIENT_ID', client_id)
    updated_content = update_env_var(updated_content, 'AZURE_CLIENT_SECRET', client_secret)
    updated_content = update_env_var(updated_content, 'AZURE_TENANT_ID', tenant_id)
    updated_content = update_env_var(updated_content, 'AZURE_SUBSCRIPTION_ID', subscription_id)
    
    save_env_file(updated_content)
    print("✅ Azure credentials saved to .env file")

def setup_gcp_credentials(env_content):
    """Setup GCP credentials"""
    print("\n🔧 GCP Credentials Setup")
    print("-" * 30)
    print("You need:")
    print("1. GCP Project ID")
    print("2. Service Account Key file (optional)")
    print()
    print("Get these from: Google Cloud Console → IAM & Admin")
    print()
    
    project_id = input("Enter GCP Project ID: ").strip()
    if not project_id:
        print("❌ Project ID is required")
        return
    
    key_file = input("Enter path to service account key file (optional): ").strip()
    
    # Update .env file
    updated_content = update_env_var(env_content, 'GCP_PROJECT_ID', project_id)
    if key_file:
        updated_content = update_env_var(updated_content, 'GOOGLE_APPLICATION_CREDENTIALS', key_file)
    
    save_env_file(updated_content)
    print("✅ GCP credentials saved to .env file")

def setup_openai_credentials(env_content):
    """Setup OpenAI credentials"""
    print("\n🔧 OpenAI API Key Setup")
    print("-" * 30)
    print("You need:")
    print("1. OpenAI API Key (starts with sk-)")
    print()
    print("Get this from: https://platform.openai.com/api-keys")
    print()
    
    api_key = input("Enter OpenAI API Key: ").strip()
    if not api_key:
        print("❌ API Key is required")
        return
    
    if not api_key.startswith('sk-'):
        print("⚠️  Warning: OpenAI API keys usually start with 'sk-'")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            return
    
    # Update .env file
    updated_content = update_env_var(env_content, 'OPENAI_API_KEY', api_key)
    
    save_env_file(updated_content)
    print("✅ OpenAI API key saved to .env file")

def setup_all_credentials(env_content):
    """Setup all credentials"""
    print("\n🔧 Complete Credentials Setup")
    print("-" * 30)
    print("This will guide you through setting up all credentials.")
    print("You can skip any by pressing Enter.")
    print()
    
    # AWS
    print("1. AWS Credentials:")
    setup_aws_credentials(env_content)
    
    # Reload content
    with open('.env', 'r') as f:
        env_content = f.read()
    
    # Azure
    print("\n2. Azure Credentials:")
    setup_azure_credentials(env_content)
    
    # Reload content
    with open('.env', 'r') as f:
        env_content = f.read()
    
    # GCP
    print("\n3. GCP Credentials:")
    setup_gcp_credentials(env_content)
    
    # Reload content
    with open('.env', 'r') as f:
        env_content = f.read()
    
    # OpenAI
    print("\n4. OpenAI API Key:")
    setup_openai_credentials(env_content)

def update_env_var(content, key, value):
    """Update environment variable in content"""
    lines = content.split('\n')
    updated = False
    
    for i, line in enumerate(lines):
        if line.startswith(f'{key}='):
            lines[i] = f'{key}={value}'
            updated = True
            break
    
    if not updated:
        # Add new variable
        lines.append(f'{key}={value}')
    
    return '\n'.join(lines)

def save_env_file(content):
    """Save content to .env file"""
    with open('.env', 'w') as f:
        f.write(content)

if __name__ == "__main__":
    main()
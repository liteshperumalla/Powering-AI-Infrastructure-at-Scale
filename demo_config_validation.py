#!/usr/bin/env python3
"""
Demonstration of the production-ready configuration and secrets management system.
This script shows how the system handles different environments and validates configuration.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infra_mind.core.config import get_settings, validate_production_config, setup_logging
from infra_mind.core.secrets import secrets_manager, validate_production_secrets, setup_development_secrets
from infra_mind.core.env_loader import env_loader, get_environment


def demonstrate_configuration_system():
    """Demonstrate the configuration system capabilities."""
    print("🚀 Infra Mind Configuration & Secrets Management Demo")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    
    # 1. Environment Detection
    print("1️⃣  ENVIRONMENT DETECTION")
    print("-" * 30)
    current_env = get_environment()
    print(f"   Current Environment: {current_env.value}")
    print(f"   Environment Source: {os.getenv('INFRA_MIND_ENVIRONMENT', 'default (development)')}")
    
    # 2. Configuration Sources
    print("\n2️⃣  CONFIGURATION SOURCES")
    print("-" * 30)
    
    # Load configuration
    config = env_loader.load_configuration()
    status = env_loader.get_configuration_status()
    
    print(f"   Project Root: {status['project_root']}")
    print(f"   Configuration Sources Found: {len(status['sources'])}")
    
    for source in status['sources']:
        status_icon = "✅" if source['loaded'] else "❌"
        error_msg = f" (Error: {source['error']})" if source['error'] else ""
        print(f"   {status_icon} {source['name']} - Priority: {source['priority']}{error_msg}")
        if source['path']:
            exists = "✓" if Path(source['path']).exists() else "✗"
            print(f"      Path: {source['path']} [{exists}]")
    
    print(f"   Total Config Items Loaded: {status['total_config_items']}")
    
    # 3. Settings Validation
    print("\n3️⃣  SETTINGS VALIDATION")
    print("-" * 30)
    
    settings = get_settings()
    print(f"   ✅ Settings Instance Created")
    print(f"   Environment: {settings.environment}")
    print(f"   Debug Mode: {settings.debug}")
    print(f"   API Port: {settings.api_port}")
    print(f"   Database: {settings.mongodb_database}")
    
    # 4. Secrets Management
    print("\n4️⃣  SECRETS MANAGEMENT")
    print("-" * 30)
    
    # Setup development secrets for demo
    if current_env.value == "development":
        setup_development_secrets()
        print("   ✅ Development secrets initialized")
    
    # Check secrets health
    health = secrets_manager.health_check()
    print(f"   Secrets Manager Health: {'✅ Healthy' if health['healthy'] else '❌ Issues'}")
    
    for backend, status in health['backends'].items():
        status_icon = "✅" if status['healthy'] else "❌"
        print(f"   {status_icon} {backend.title()} Backend")
        if not status['healthy']:
            print(f"      Error: {status.get('error', 'Unknown')}")
    
    # 5. Configuration Validation
    print("\n5️⃣  CONFIGURATION VALIDATION")
    print("-" * 30)
    
    validation = validate_production_config()
    if validation['valid']:
        print("   ✅ Configuration is valid")
    else:
        print(f"   ⚠️  Configuration has issues:")
        print(f"      Errors: {len(validation['errors'])}")
        print(f"      Warnings: {len(validation['warnings'])}")
        
        if validation['errors']:
            print("      Critical Errors:")
            for error in validation['errors'][:3]:  # Show first 3
                print(f"        - {error}")
        
        if validation['warnings']:
            print("      Warnings:")
            for warning in validation['warnings'][:3]:  # Show first 3
                print(f"        - {warning}")
    
    # 6. Secrets Validation
    print("\n6️⃣  SECRETS VALIDATION")
    print("-" * 30)
    
    secret_validation = validate_production_secrets()
    print(f"   Total Required Secrets: {secret_validation['total_secrets']}")
    print(f"   Valid Secrets: {secret_validation['valid_secrets']}")
    print(f"   Missing Secrets: {len(secret_validation['missing_secrets'])}")
    
    if secret_validation['missing_secrets']:
        print("   Missing Secrets:")
        for secret in secret_validation['missing_secrets'][:5]:  # Show first 5
            print(f"     - {secret}")
    
    # 7. Cloud Provider Configuration
    print("\n7️⃣  CLOUD PROVIDER CONFIGURATION")
    print("-" * 30)
    
    aws_creds = settings.get_aws_credentials()
    azure_creds = settings.get_azure_credentials()
    gcp_creds = settings.get_gcp_credentials()
    
    aws_configured = bool(aws_creds['access_key_id'])
    azure_configured = bool(azure_creds['client_id'])
    gcp_configured = bool(gcp_creds['project_id'])
    
    print(f"   AWS: {'✅ Configured' if aws_configured else '⚠️  Not configured'}")
    print(f"   Azure: {'✅ Configured' if azure_configured else '⚠️  Not configured'}")
    print(f"   GCP: {'✅ Configured' if gcp_configured else '⚠️  Not configured'}")
    
    # 8. Production Readiness Check
    print("\n8️⃣  PRODUCTION READINESS")
    print("-" * 30)
    
    if current_env.value == "production":
        prod_validation = validate_production_config()
        if prod_validation['valid']:
            print("   ✅ Ready for production deployment")
        else:
            print("   ❌ Not ready for production")
            print(f"      Issues to resolve: {len(prod_validation['errors'])}")
    else:
        print(f"   ℹ️  Currently in {current_env.value} environment")
        print("   💡 To test production validation:")
        print("      export INFRA_MIND_ENVIRONMENT=production")
    
    # 9. Configuration Export (Safe)
    print("\n9️⃣  CONFIGURATION SUMMARY")
    print("-" * 30)
    
    export = env_loader.export_configuration(include_secrets=False)
    config_items = export['configuration']
    
    print(f"   Environment: {export['environment']}")
    print(f"   Configuration Items: {len(config_items)}")
    print("   Sample Configuration:")
    
    # Show some safe config items
    safe_items = {k: v for k, v in config_items.items() 
                  if not any(sensitive in k.lower() 
                           for sensitive in ['password', 'secret', 'key', 'token'])}
    
    for key, value in list(safe_items.items())[:5]:
        print(f"     {key}: {value}")
    
    if len(safe_items) > 5:
        print(f"     ... and {len(safe_items) - 5} more items")
    
    print("\n" + "=" * 60)
    print("🎉 Configuration System Demo Complete!")
    
    return {
        'environment': current_env.value,
        'config_sources': len(status.get('sources', [])),
        'config_items': status.get('total_config_items', 0),
        'secrets_healthy': health['healthy'],
        'config_valid': validation['valid'],
        'aws_configured': aws_configured,
        'azure_configured': azure_configured,
        'gcp_configured': gcp_configured
    }


def show_production_setup_guide():
    """Show guide for production setup."""
    print("\n📋 PRODUCTION SETUP GUIDE")
    print("=" * 40)
    print("To set up for production:")
    print()
    print("1. Generate secrets template:")
    print("   ./scripts/setup-secrets.sh template")
    print()
    print("2. Copy and configure production environment:")
    print("   cp .env.secrets.template .env.production")
    print("   # Edit .env.production with real values")
    print()
    print("3. Set production environment:")
    print("   export INFRA_MIND_ENVIRONMENT=production")
    print()
    print("4. Validate configuration:")
    print("   python scripts/validate-config.py")
    print()
    print("5. Setup secrets for deployment:")
    print("   ./scripts/setup-secrets.sh k8s    # For Kubernetes")
    print("   ./scripts/setup-secrets.sh docker # For Docker")


if __name__ == "__main__":
    try:
        print("Starting configuration system demonstration...")
        result = demonstrate_configuration_system()
        
        print(f"\n📊 DEMO RESULTS:")
        print(f"   Environment: {result['environment']}")
        print(f"   Config Sources: {result['config_sources']}")
        print(f"   Config Items: {result['config_items']}")
        print(f"   Secrets Healthy: {result['secrets_healthy']}")
        print(f"   Config Valid: {result['config_valid']}")
        print(f"   Cloud Providers: AWS={result['aws_configured']}, Azure={result['azure_configured']}, GCP={result['gcp_configured']}")
        
        if result['environment'] != 'production':
            show_production_setup_guide()
        
        print("\n✅ Demo completed successfully!")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
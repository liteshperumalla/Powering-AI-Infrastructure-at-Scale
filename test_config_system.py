#!/usr/bin/env python3
"""
Test script to demonstrate the production-ready configuration system.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infra_mind.core.config import get_settings, validate_production_config, setup_logging
from infra_mind.core.secrets import secrets_manager, validate_production_secrets
from infra_mind.core.env_loader import env_loader, get_environment


def test_configuration_system():
    """Test the configuration system."""
    print("🧪 Testing Infra Mind Configuration System")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    # Test environment detection
    print(f"📍 Environment: {get_environment().value}")
    
    # Test settings loading
    settings = get_settings()
    print(f"🔧 Settings loaded successfully")
    print(f"   - Environment: {settings.environment}")
    print(f"   - Debug mode: {settings.debug}")
    print(f"   - API port: {settings.api_port}")
    
    # Test environment loader
    env_status = env_loader.get_configuration_status()
    print(f"📁 Configuration sources: {len(env_status['sources'])}")
    for source in env_status['sources']:
        status = "✓" if source['loaded'] else "❌"
        print(f"   {status} {source['name']} (priority: {source['priority']})")
    
    # Test secrets manager
    print(f"🔐 Secrets manager health check:")
    health = secrets_manager.health_check()
    if health['healthy']:
        print("   ✓ All backends healthy")
        for backend, status in health['backends'].items():
            print(f"     - {backend}: {'✓' if status['healthy'] else '❌'}")
    else:
        print("   ❌ Some backends have issues")
    
    # Test configuration validation
    print(f"✅ Configuration validation:")
    validation = validate_production_config()
    if validation['valid']:
        print("   ✓ Configuration is valid")
    else:
        print(f"   ⚠️  {len(validation['errors'])} errors, {len(validation['warnings'])} warnings")
    
    # Test secrets validation
    print(f"🔑 Secrets validation:")
    secret_validation = validate_production_secrets()
    print(f"   - Total secrets: {secret_validation['total_secrets']}")
    print(f"   - Valid secrets: {secret_validation['valid_secrets']}")
    print(f"   - Missing secrets: {len(secret_validation['missing_secrets'])}")
    
    # Test specific configuration access
    print(f"🎯 Configuration access test:")
    print(f"   - MongoDB URL configured: {bool(settings.get_database_url())}")
    print(f"   - Redis URL configured: {bool(settings.get_redis_url())}")
    print(f"   - OpenAI key configured: {bool(settings.get_openai_api_key())}")
    
    # Test cloud credentials
    print(f"☁️  Cloud credentials test:")
    aws_creds = settings.get_aws_credentials()
    azure_creds = settings.get_azure_credentials()
    gcp_creds = settings.get_gcp_credentials()
    
    print(f"   - AWS: {'✓' if aws_creds['access_key_id'] else '❌'}")
    print(f"   - Azure: {'✓' if azure_creds['client_id'] else '❌'}")
    print(f"   - GCP: {'✓' if gcp_creds['project_id'] else '❌'}")
    
    print("\n🎉 Configuration system test completed!")
    
    return {
        'settings_loaded': True,
        'environment': settings.environment,
        'secrets_healthy': health['healthy'],
        'config_valid': validation['valid']
    }


if __name__ == "__main__":
    try:
        result = test_configuration_system()
        print(f"\n📊 Test Results: {result}")
        
        if result['config_valid'] and result['secrets_healthy']:
            print("✅ All systems operational!")
            sys.exit(0)
        else:
            print("⚠️  Some issues detected - check configuration")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
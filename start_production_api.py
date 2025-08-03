#!/usr/bin/env python3
"""
Production API startup script for Infra Mind.
"""

import os
import sys
import subprocess
from pathlib import Path

# Set production environment variables
os.environ.update({
    'INFRA_MIND_ENVIRONMENT': 'production',
    'INFRA_MIND_DEBUG': 'false',
    'INFRA_MIND_SECRET_KEY': 'demo-production-secret-key-32-chars-long',
    'INFRA_MIND_MONGODB_URL': 'mongodb://admin:secure-mongo-password-123@localhost:27017/infra_mind?authSource=admin',
    'INFRA_MIND_REDIS_URL': 'redis://:secure-redis-password-123@localhost:6379/0',
    'INFRA_MIND_API_HOST': '0.0.0.0',
    'INFRA_MIND_API_PORT': '8000',
    'INFRA_MIND_LOG_LEVEL': 'info',
    'INFRA_MIND_CORS_ORIGINS': '["http://localhost:3000","https://localhost:3000"]',
    'INFRA_MIND_OPENAI_API_KEY': 'demo-openai-key-placeholder',
    'INFRA_MIND_AWS_ACCESS_KEY_ID': 'demo-aws-access-key',
    'INFRA_MIND_AWS_SECRET_ACCESS_KEY': 'demo-aws-secret-key',
    'INFRA_MIND_AWS_REGION': 'us-east-1',
    'INFRA_MIND_AZURE_CLIENT_ID': 'demo-azure-client-id',
    'INFRA_MIND_AZURE_CLIENT_SECRET': 'demo-azure-client-secret',
    'INFRA_MIND_AZURE_TENANT_ID': 'demo-azure-tenant-id',
    'INFRA_MIND_GCP_PROJECT_ID': 'demo-gcp-project',
    'INFRA_MIND_RATE_LIMIT_REQUESTS': '1000',
})

def main():
    print("🚀 Starting Infra Mind API in Production Mode")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("api/app.py").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Add project paths to Python path
    project_root = Path.cwd()
    src_path = project_root / "src"
    
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    print(f"📍 Environment: {os.environ.get('INFRA_MIND_ENVIRONMENT')}")
    print(f"🔧 Debug Mode: {os.environ.get('INFRA_MIND_DEBUG')}")
    print(f"🌐 Host: {os.environ.get('INFRA_MIND_API_HOST')}")
    print(f"🔌 Port: {os.environ.get('INFRA_MIND_API_PORT')}")
    print(f"📊 Log Level: {os.environ.get('INFRA_MIND_LOG_LEVEL')}")
    print()
    
    try:
        # Start the production server with optimized settings
        cmd = [
            sys.executable, "-m", "uvicorn",
            "api.app:app",
            "--host", os.environ.get('INFRA_MIND_API_HOST', '0.0.0.0'),
            "--port", os.environ.get('INFRA_MIND_API_PORT', '8000'),
            "--workers", "4",  # Production workers
            "--log-level", os.environ.get('INFRA_MIND_LOG_LEVEL', 'info').lower(),
            "--access-log",
            "--use-colors",
            "--loop", "uvloop",  # High-performance event loop
            "--http", "httptools",  # High-performance HTTP parser
        ]
        
        print(f"🔄 Running command: {' '.join(cmd)}")
        print("=" * 60)
        print("🌟 Production API Server Starting...")
        print(f"📚 API Documentation: http://localhost:{os.environ.get('INFRA_MIND_API_PORT', '8000')}/docs")
        print(f"❤️  Health Check: http://localhost:{os.environ.get('INFRA_MIND_API_PORT', '8000')}/health")
        print("=" * 60)
        
        # Start the server
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Production server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to start production server: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
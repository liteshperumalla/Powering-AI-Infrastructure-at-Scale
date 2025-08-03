#!/usr/bin/env python3
"""
Startup script for Infra Mind API Gateway.

This script provides an easy way to start the API server with proper configuration.
"""

import sys
import os
import subprocess
from pathlib import Path

# Load development environment variables
from load_env import load_development_env
load_development_env()

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'loguru',
        'motor',
        'beanie'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True


def check_environment():
    """Check environment configuration."""
    print("\n🔧 Checking environment...")
    
    # Check if we're in the right directory
    if not Path("api/app.py").exists():
        print("❌ Please run this script from the project root directory")
        return False
    
    # Check Python path
    project_root = Path.cwd()
    src_path = project_root / "src"
    
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        print(f"   ✅ Added {src_path} to Python path")
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"   ✅ Added {project_root} to Python path")
    
    print("✅ Environment configured")
    return True


def test_api_import():
    """Test if the API can be imported successfully."""
    print("\n🧪 Testing API import...")
    
    try:
        from api.app import app
        print("   ✅ FastAPI app imported successfully")
        print(f"   ✅ App title: {app.title}")
        print(f"   ✅ App version: {app.version}")
        print(f"   ✅ Number of routes: {len(app.routes)}")
        return True
    except Exception as e:
        print(f"   ❌ Failed to import API: {e}")
        return False


def start_server(host="0.0.0.0", port=8000, reload=True):
    """Start the API server using uvicorn."""
    print(f"\n🚀 Starting Infra Mind API Gateway...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Reload: {reload}")
    print(f"   Docs: http://localhost:{port}/docs")
    print(f"   Health: http://localhost:{port}/health")
    
    try:
        # Use uvicorn to start the server
        cmd = [
            sys.executable, "-m", "uvicorn",
            "api.app:app",
            "--host", host,
            "--port", str(port),
            "--log-level", "info"
        ]
        
        if reload:
            cmd.append("--reload")
        
        print(f"\n🔄 Running command: {' '.join(cmd)}")
        print("=" * 60)
        
        # Start the server
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to start server: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False
    
    return True


def main():
    """Main startup function."""
    print("🌟 Infra Mind API Gateway Startup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Test API import
    if not test_api_import():
        sys.exit(1)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Start Infra Mind API Gateway")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    
    args = parser.parse_args()
    
    # Start the server
    success = start_server(
        host=args.host,
        port=args.port,
        reload=not args.no_reload
    )
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
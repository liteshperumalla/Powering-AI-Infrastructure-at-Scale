#!/usr/bin/env python3
"""
Production Frontend startup script for Infra Mind.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🌐 Starting Infra Mind Frontend in Production Mode")
    print("=" * 60)
    
    # Change to frontend directory
    frontend_dir = Path("frontend-react")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        sys.exit(1)
    
    os.chdir(frontend_dir)
    
    # Set production environment variables
    env = os.environ.copy()
    env.update({
        'NODE_ENV': 'production',
        'NEXT_PUBLIC_API_URL': 'http://localhost:8000',
        'NEXT_PUBLIC_WS_URL': 'ws://localhost:8000',
        'NEXT_TELEMETRY_DISABLED': '1',
        'PORT': '3000',
    })
    
    print(f"📍 Environment: {env.get('NODE_ENV')}")
    print(f"🔗 API URL: {env.get('NEXT_PUBLIC_API_URL')}")
    print(f"🔌 Port: {env.get('PORT')}")
    print()
    
    try:
        # First, build the production version
        print("🔨 Building production frontend...")
        build_cmd = ["npm", "run", "build"]
        subprocess.run(build_cmd, env=env, check=True)
        
        print("✅ Build completed successfully!")
        print()
        
        # Start the production server
        print("🚀 Starting production frontend server...")
        start_cmd = ["npm", "run", "start"]
        
        print(f"🔄 Running command: {' '.join(start_cmd)}")
        print("=" * 60)
        print("🌟 Production Frontend Server Starting...")
        print(f"🌐 Frontend URL: http://localhost:{env.get('PORT', '3000')}")
        print("=" * 60)
        
        # Start the server
        subprocess.run(start_cmd, env=env, check=True)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Production frontend stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to start production frontend: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
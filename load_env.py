#!/usr/bin/env python3
"""
Environment loader for Infra Mind development.
Loads environment variables from .env.development file.
"""

import os
from pathlib import Path

def load_development_env():
    """Load development environment variables."""
    env_file = Path(__file__).parent / '.env.development'
    
    if not env_file.exists():
        print(f"Warning: {env_file} not found")
        return
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"\'')
                os.environ[key] = value
    
    print("✅ Development environment variables loaded")

if __name__ == "__main__":
    load_development_env()
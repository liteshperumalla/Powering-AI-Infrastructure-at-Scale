#!/usr/bin/env python3
"""
Create a demo user for testing the application.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.infra_mind.core.database import init_database
from src.infra_mind.models.user import User
from src.infra_mind.core.auth import hash_password


async def create_demo_user():
    """Create a demo user for testing."""
    try:
        # Initialize database connection
        await init_database()
        print("✅ Database connection initialized")
        
        # Check if demo user already exists
        existing_user = await User.find_one({"email": "demo@infraMind.com"})
        if existing_user:
            print("✅ Demo user already exists")
            print(f"   Email: demo@infraMind.com")
            print(f"   Name: {existing_user.full_name}")
            return
        
        # Create demo user
        demo_user = User(
            email="demo@infraMind.com",
            full_name="Demo User",
            hashed_password=hash_password("demo123456"),
            is_active=True,
            role="user",
            created_at=datetime.utcnow(),
            last_login=None
        )
        
        await demo_user.save()
        print("✅ Demo user created successfully!")
        print(f"   Email: demo@infraMind.com")
        print(f"   Password: demo123456")
        print(f"   Name: Demo User")
        
    except Exception as e:
        print(f"❌ Error creating demo user: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(create_demo_user())
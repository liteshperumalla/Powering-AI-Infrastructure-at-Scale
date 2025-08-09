#!/usr/bin/env python3
"""
Create a test user using proper Pydantic/Beanie models.
"""

import os
import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def create_test_user():
    """Create a test user using the proper User model."""
    
    print("🔧 Creating test user with Pydantic/Beanie models...")
    
    try:
        # Initialize the database connection and models
        from infra_mind.core.database import init_database
        from infra_mind.models.user import User
        
        # Initialize database - this sets up the connection and document models
        await init_database()
        
        # Check if user already exists
        existing_user = await User.find_one(User.email == "liteshperumalla@gmail.com")
        if existing_user:
            print("🔄 Deleting existing test user...")
            await existing_user.delete()
        
        # Create new test user using the proper model method
        test_user = await User.create_user(
            email="liteshperumalla@gmail.com",
            password="Litesh@#12345",
            full_name="Litesh Perumalla",
            company_name="AI Infrastructure Solutions",
            job_title="Infrastructure Engineer",
            role="user"
        )
        
        print(f"✅ Test user created successfully!")
        print(f"   User ID: {test_user.id}")
        print(f"   Email: liteshperumalla@gmail.com")
        print(f"   Password: Litesh@#12345")
        print(f"   Full Name: {test_user.full_name}")
        print(f"   Company: {test_user.company_name}")
        
        # Test authentication
        auth_user = await User.authenticate("liteshperumalla@gmail.com", "Litesh@#12345")
        if auth_user:
            print("✅ Authentication test passed!")
        else:
            print("❌ Authentication test failed!")
        
        return test_user
        
    except Exception as e:
        print(f"❌ Failed to create test user: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

async def main():
    """Main function."""
    print("🚀 Proper Test User Creation Script")
    print("=" * 40)
    
    try:
        user = await create_test_user()
        print("\n🎉 Success! You can now log in with:")
        print("   Email: liteshperumalla@gmail.com")
        print("   Password: Litesh@#12345")
        print("\nUse these credentials to test the frontend sign-in!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
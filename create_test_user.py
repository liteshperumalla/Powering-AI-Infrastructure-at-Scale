#!/usr/bin/env python3
"""
Create a test user for testing authenticated chat features.
"""

import os
import asyncio
import uuid
from datetime import datetime, timezone
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Database configuration
MONGODB_URL = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")

async def hash_password(password: str) -> str:
    """Proper bcrypt password hashing to match the backend."""
    # Use bcrypt with 12 rounds to match backend settings
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

async def create_test_user():
    """Create a test user in the database."""
    
    print("🔧 Creating test user for chat testing...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.infra_mind
    
    try:
        # Delete existing test user if it exists
        existing_user = await db.users.find_one({"email": "liteshperumalla@gmail.com"})
        if existing_user:
            print("🔄 Deleting existing test user...")
            await db.users.delete_one({"email": "liteshperumalla@gmail.com"})
        
        # Create test user document
        user_id = str(uuid.uuid4())
        hashed_password = await hash_password("Litesh@#12345")
        
        user_doc = {
            "_id": user_id,
            "email": "liteshperumalla@gmail.com",
            "hashed_password": hashed_password,
            "full_name": "Litesh Perumalla",
            "company_name": "AI Infrastructure Solutions",
            "role": "user",
            "is_active": True,
            "preferences": {
                "notifications_enabled": True,
                "default_context": "general_inquiry"
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Insert user
        result = await db.users.insert_one(user_doc)
        print(f"✅ Test user created successfully!")
        print(f"   User ID: {result.inserted_id}")
        print(f"   Email: liteshperumalla@gmail.com")
        print(f"   Password: Litesh@#12345")
        
        return user_doc
        
    except Exception as e:
        print(f"❌ Failed to create test user: {str(e)}")
        raise
    finally:
        client.close()

async def main():
    """Main function."""
    print("🚀 Test User Creation Script")
    print("=" * 40)
    
    try:
        user = await create_test_user()
        print("\n🎉 Success! You can now log in with:")
        print("   Email: liteshperumalla@gmail.com")
        print("   Password: Litesh@#12345")
        print("\nUse these credentials to test:")
        print("• Start conversations")
        print("• Chat settings")
        print("• End chat functionality")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
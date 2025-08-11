#!/usr/bin/env python3
"""
Create a proper test user for API testing with correct Pydantic ObjectId format.
"""

import os
import asyncio
from datetime import datetime, timezone
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Database configuration
MONGODB_URL = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://localhost:27017/infra_mind")

async def hash_password(password: str) -> str:
    """Proper bcrypt password hashing to match the backend."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

async def create_api_test_user():
    """Create a test user with proper ObjectId format."""
    print("🚀 API Test User Creation")
    print("=" * 40)
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client.infra_mind
        users_collection = db.users
        
        # Test email and password
        test_email = "api_test@example.com"
        test_password = "test123"
        
        print(f"🔧 Creating test user: {test_email}")
        
        # Delete existing test user if exists
        await users_collection.delete_many({"email": test_email})
        print("🔄 Deleted any existing test user")
        
        # Create new user with proper MongoDB ObjectId
        user_id = ObjectId()
        hashed_password = await hash_password(test_password)
        
        user_doc = {
            "_id": user_id,
            "email": test_email,
            "hashed_password": hashed_password,
            "full_name": "API Test User",
            "company_name": "Test Company",
            "role": "admin",
            "is_active": True,
            "is_verified": True,
            "preferences": {
                "notifications_enabled": True,
                "default_context": "general_inquiry"
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Insert the user
        result = await users_collection.insert_one(user_doc)
        
        if result.inserted_id:
            print("✅ API test user created successfully!")
            print(f"   User ID: {user_id}")
            print(f"   Email: {test_email}")
            print(f"   Password: {test_password}")
            print("")
            print("🎉 Success! You can now use these credentials for API testing:")
            print(f"   Email: {test_email}")
            print(f"   Password: {test_password}")
        else:
            print("❌ Failed to create test user")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(create_api_test_user())
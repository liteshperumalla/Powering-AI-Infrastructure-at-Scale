#!/usr/bin/env python3
"""
Create test users for the Infra Mind application.
This script creates several test users with different roles for easy login testing.
"""

import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import bcrypt

# Import our models
import sys
sys.path.append('src')

from src.infra_mind.models.user import User
from src.infra_mind.models.assessment import Assessment
from src.infra_mind.models.recommendation import Recommendation
from src.infra_mind.models.report import Report
from src.infra_mind.core.config import get_settings

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

async def create_test_users():
    """Create test users in the database."""
    
    # Get database settings
    settings = get_settings()
    
    # Connect to MongoDB
    mongodb_url = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
    print(f"Connecting to MongoDB: {mongodb_url}")
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client.get_database("infra_mind")
    
    # Initialize Beanie
    await init_beanie(
        database=db,
        document_models=[
            User,
            Assessment,
            Recommendation,
            Report
        ]
    )
    
    # Test users to create
    test_users = [
        {
            "email": "admin@example.com",
            "password": "admin123",
            "full_name": "Admin User",
            "role": "admin",
            "company": "Infra Mind Corp",
            "is_active": True,
            "is_verified": True
        },
        {
            "email": "test@example.com", 
            "password": "testpass123",
            "full_name": "Test User",
            "role": "user",
            "company": "Test Company",
            "is_active": True,
            "is_verified": True
        },
        {
            "email": "demo@infra-mind.com",
            "password": "demo123",
            "full_name": "Demo User",
            "role": "user", 
            "company": "Demo Corp",
            "is_active": True,
            "is_verified": True
        },
        {
            "email": "user@test.com",
            "password": "password123",
            "full_name": "John Smith",
            "role": "user",
            "company": "Tech Solutions Inc",
            "is_active": True,
            "is_verified": True
        }
    ]
    
    print("Creating test users...")
    
    for user_data in test_users:
        try:
            # Check if user already exists
            existing_user = await User.find_one({"email": user_data["email"]})
            
            if existing_user:
                print(f"✓ User {user_data['email']} already exists, skipping...")
                continue
            
            # Hash the password
            hashed_password = hash_password(user_data["password"])
            
            # Create new user
            new_user = User(
                email=user_data["email"],
                hashed_password=hashed_password,
                full_name=user_data["full_name"],
                role=user_data["role"],
                company=user_data.get("company"),
                is_active=user_data["is_active"],
                is_verified=user_data["is_verified"],
                created_at=datetime.utcnow(),
                last_login=None,
                preferences={}
            )
            
            # Save user to database
            await new_user.insert()
            
            print(f"✅ Created user: {user_data['email']} (password: {user_data['password']})")
            
        except Exception as e:
            print(f"❌ Failed to create user {user_data['email']}: {str(e)}")
    
    print("\n" + "="*60)
    print("TEST USERS CREATED - USE THESE CREDENTIALS TO LOGIN:")
    print("="*60)
    
    for user_data in test_users:
        print(f"📧 Email: {user_data['email']}")
        print(f"🔒 Password: {user_data['password']}")  
        print(f"👤 Name: {user_data['full_name']}")
        print(f"🏢 Role: {user_data['role']}")
        print("-" * 40)
    
    print("="*60)
    
    # Close database connection
    client.close()
    print("✅ Test user creation completed!")

if __name__ == "__main__":
    asyncio.run(create_test_users())